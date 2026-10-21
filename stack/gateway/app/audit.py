"""Immutable audit chain: hash-chained events → append-only Postgres hot copy + WORM segments in MinIO + daily anchor."""
import json, hashlib, threading, time, uuid, datetime as dt
import boto3
from botocore.config import Config as BotoConfig
from . import config, db

def canon(o) -> str:
    return json.dumps(o, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str)

def sha256(s: str) -> str:
    return "sha256:" + hashlib.sha256(s.encode()).hexdigest()

def event_hash(ev: dict) -> str:
    body = {k: v for k, v in ev.items() if k != "hash"}
    return sha256(canon(body) + ev["prev_hash"])

def _s3(url, user, pw):
    return boto3.client("s3", endpoint_url=url, aws_access_key_id=user, aws_secret_access_key=pw,
                        region_name="eu-poc", config=BotoConfig(signature_version="s3v4", retries={"max_attempts": 2}, proxies={}))

class Chain:
    def __init__(self):
        self.lock = threading.Lock()
        self.open: list[dict] = []
        self.open_started = time.time()
        self.s3 = _s3(config.MINIO_URL, config.MINIO_USER, config.MINIO_PASSWORD)
        self.anchor_s3 = _s3(config.ANCHOR_URL, config.ANCHOR_USER, config.ANCHOR_PASSWORD)

    def _last_hash(self) -> str:
        row = db.one("select hash from audit_event order by seq desc limit 1")
        return row["hash"] if row else "sha256:" + "0" * 64

    def append(self, type_: str, body: dict, actor_identity_id=None, team_id=None, model_endpoint_id=None, outcome=None, reasons=None, cost_eur=None) -> dict:
        with self.lock:
            from .runs import current_run   # run correlation id from the x-agl-run header, if any
            run_id = body.get("run_id") or current_run.get()
            ev = {"event_id": str(uuid.uuid4()), "ts": dt.datetime.now(dt.timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z"),
                  "type": type_, "schema_version": 1, **({"run_id": run_id} if run_id else {}), **body, "prev_hash": self._last_hash()}
            ev["hash"] = event_hash(ev)
            seg_id = self.open[0]["_segment_id"] if self.open else str(uuid.uuid4())
            db.run("""insert into audit_event (event_id, ts, type, actor_identity_id, team_id, model_endpoint_id, outcome, reasons, cost_eur, segment_id, prev_hash, hash, body)
                      values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                   (ev["event_id"], ev["ts"], type_, actor_identity_id, team_id, model_endpoint_id, outcome, reasons, cost_eur, seg_id, ev["prev_hash"], ev["hash"], json.dumps(ev)))
            stored = dict(ev); stored["_segment_id"] = seg_id
            self.open.append(stored)
            if len(self.open) >= config.SEGMENT_MAX_EVENTS:
                self._flush_locked()
            return ev

    def flush(self) -> dict | None:
        with self.lock:
            return self._flush_locked()

    def _flush_locked(self):
        if not self.open:
            return None
        events = [{k: v for k, v in e.items() if not k.startswith("_")} for e in self.open]
        seg_id = self.open[0]["_segment_id"]
        first, last = events[0], events[-1]
        day = dt.datetime.now(dt.timezone.utc)
        key = f"segments/{day:%Y/%m/%d}/{seg_id}.jsonl"
        payload = "\n".join(canon(e) for e in events) + "\n"
        retain = day + dt.timedelta(days=config.AUDIT_RETENTION_DAYS)
        self.s3.put_object(Bucket=config.AUDIT_BUCKET, Key=key, Body=payload.encode(), ContentType="application/x-ndjson",
                           ObjectLockMode="COMPLIANCE", ObjectLockRetainUntilDate=retain)
        uri = f"s3://{config.AUDIT_BUCKET}/{key}"
        db.run("""insert into audit_segment (id, started_at, closed_at, object_uri, first_event, last_event, event_count, first_hash, last_hash, object_lock_until)
                  values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
               (seg_id, first["ts"], last["ts"], uri, first["event_id"], last["event_id"], len(events), first["hash"], last["hash"], retain))
        self.open = []
        self.open_started = time.time()
        return {"segment_id": seg_id, "object_uri": uri, "events": len(events), "last_hash": last["hash"]}

    def maybe_flush(self):
        if self.open and time.time() - self.open_started >= config.SEGMENT_MAX_SECONDS:
            self.flush()

    def anchor(self, date: dt.date | None = None) -> dict:
        self.flush()
        now = dt.datetime.now(dt.timezone.utc)
        date = date or now.date()
        segs = db.all_("select id, object_uri, last_hash from audit_segment where closed_at::date = %s and closed_at <= %s order by closed_at", (date, now))
        root = sha256("".join(s["last_hash"] for s in segs)) if segs else sha256("")
        doc = {"anchor_date": date.isoformat(), "anchored_through": now.isoformat(), "root_hash": root,
               "segments": [{"uri": s["object_uri"], "last_hash": s["last_hash"]} for s in segs], "created_at": now.isoformat()}
        key = f"anchors/{date.isoformat()}/{uuid.uuid4().hex[:8]}.json"
        retain = dt.datetime.now(dt.timezone.utc) + dt.timedelta(days=config.AUDIT_RETENTION_DAYS)
        self.anchor_s3.put_object(Bucket=config.ANCHOR_BUCKET, Key=key, Body=canon(doc).encode(), ContentType="application/json",
                                  ObjectLockMode="COMPLIANCE", ObjectLockRetainUntilDate=retain)
        uri = f"s3://{config.ANCHOR_BUCKET}/{key}"
        db.run("""insert into audit_anchor (id, anchor_date, anchored_through, root_hash, external_uri, signed_by) values (%s,%s,%s,%s,%s,%s)""",
               (str(uuid.uuid4()), date, now, root, uri, "poc-no-hsm"))
        return {"anchor_date": date.isoformat(), "anchored_through": now.isoformat(), "root_hash": root, "segments": len(segs), "external_uri": uri}

    def _read_locked(self, key: str) -> tuple[str, bool]:
        """Object Lock protects versions, not the key: a plain delete only adds a delete marker.
        Read the newest real version regardless, and report whether a delete was attempted."""
        vers = self.s3.list_object_versions(Bucket=config.AUDIT_BUCKET, Prefix=key)
        markers = [m for m in vers.get("DeleteMarkers", []) if m["Key"] == key]
        real = sorted([v for v in vers.get("Versions", []) if v["Key"] == key], key=lambda v: v["LastModified"], reverse=True)
        if not real:
            raise FileNotFoundError(f"no locked version for {key}")
        body = self.s3.get_object(Bucket=config.AUDIT_BUCKET, Key=key, VersionId=real[0]["VersionId"])["Body"].read().decode()
        return body, bool(markers)

    def verify(self, simulate_tamper: bool = False) -> dict:
        """Re-hash every event from the WORM segments (+ open events), check links, compare with hot copy and anchors."""
        self.flush()
        segs = db.all_("select id, object_uri, first_hash, last_hash, event_count from audit_segment order by started_at")
        events, seg_results = [], []
        for s in segs:
            key = s["object_uri"].split(f"s3://{config.AUDIT_BUCKET}/", 1)[1]
            body, delete_marker = self._read_locked(key)
            evs = [json.loads(l) for l in body.splitlines() if l.strip()]
            seg_results.append({"segment_id": str(s["id"]), "uri": s["object_uri"], "events": len(evs),
                                "last_hash_matches_db": bool(evs) and evs[-1]["hash"] == s["last_hash"],
                                "delete_attempted": delete_marker})
            events.extend(evs)
        tampered_at = None
        if simulate_tamper and len(events) >= 2:
            idx = min(3, len(events) - 1)
            events[idx] = dict(events[idx]); events[idx]["type"] = events[idx]["type"] + "_EDITED"
            tampered_at = events[idx]["event_id"]
        prev = "sha256:" + "0" * 64
        broken = []
        for i, e in enumerate(events):
            ok_prev = e["prev_hash"] == prev
            ok_hash = event_hash(e) == e["hash"]
            if not (ok_prev and ok_hash):
                broken.append({"index": i, "event_id": e["event_id"], "prev_link_ok": ok_prev, "content_hash_ok": ok_hash})
            prev = e["hash"]
        hot = db.all_("select event_id, hash from audit_event order by seq")
        hot_map = {r["event_id"] if isinstance(r["event_id"], str) else str(r["event_id"]): r["hash"] for r in hot}
        hot_mismatch = [e["event_id"] for e in events if hot_map.get(e["event_id"]) != e["hash"]]
        anchors = db.all_("select anchor_date, anchored_through, root_hash from audit_anchor order by anchored_through")
        anchor_results = []
        for a in anchors:
            day_segs = db.all_("select last_hash from audit_segment where closed_at::date=%s and closed_at <= %s order by closed_at", (a["anchor_date"], a["anchored_through"]))
            root = sha256("".join(s["last_hash"] for s in day_segs))
            anchor_results.append({"date": a["anchor_date"].isoformat(), "through": a["anchored_through"].isoformat(), "segments": len(day_segs), "matches": root == a["root_hash"]})
        result = "pass" if not broken and not hot_mismatch and all(x["matches"] for x in anchor_results) else "fail"
        db.run("insert into chain_verification (range_start, range_end, result, details) values (%s,%s,%s,%s)",
               (events[0]["ts"] if events else dt.datetime.now(dt.timezone.utc), events[-1]["ts"] if events else dt.datetime.now(dt.timezone.utc), result,
                json.dumps({"events": len(events), "broken": broken[:10], "hot_mismatch": len(hot_mismatch), "anchors": anchor_results, "simulated_tamper": tampered_at})))
        return {"result": result, "events_verified": len(events), "segments": seg_results, "broken_links": broken, "hot_copy_mismatches": len(hot_mismatch),
                "anchors": anchor_results, "simulated_tamper_event": tampered_at, "head_hash": events[-1]["hash"] if events else None}

chain: Chain | None = None

def start():
    global chain
    chain = Chain()
    def loop():
        while True:
            time.sleep(5)
            try:
                chain.maybe_flush()
            except Exception as e:  # noqa
                print("audit flush error:", e)
    threading.Thread(target=loop, daemon=True).start()
