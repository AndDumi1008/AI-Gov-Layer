"""Canaries executed by the gateway itself (DoD: "prove each guardrail with canaries: a deliberate violation that
must be blocked, a clean input that must pass, and the evidence recorded for both"; issue #14).

Each canary runs a NEGATIVE probe (must be refused) and a POSITIVE probe (must pass) and appends one
`canary_result` event carrying both observations verbatim, tagged with the canary id as the check id, so the
scoreboard shows it like any other check. Request-path canaries call the gateway's own public surface over
loopback with the caller's token; store-level canaries use the gateway's own connections, so the refusal they
record is the one the gateway itself meets (its database role cannot delete audit rows; the WORM bucket refuses
even its root credentials)."""
import socket, json, httpx
from . import db, audit, config, runs

LOOP = "http://127.0.0.1:8000"

def _ask(token: str, text: str, check: str, **headers) -> tuple[int, dict, dict]:
    h = {"authorization": "Bearer " + token, "x-agl-check": check, "x-agl-client": "canary"}
    if runs.current_run.get(): h["x-agl-run"] = runs.current_run.get()
    h.update({k.replace("_", "-"): v for k, v in headers.items() if v})
    r = httpx.post(f"{LOOP}/v1/chat/completions", json={"model": config.LOCAL_ALIAS, "max_tokens": 32, "messages": [{"role": "user", "content": text}]}, headers=h, timeout=120, trust_env=False)
    agl = {k: v for k, v in r.headers.items() if k.lower().startswith("x-agl")}
    try: body = r.json()
    except Exception: body = {}
    return r.status_code, agl, body

def c_secret(tok):
    s1, h1, b1 = _ask(tok, "Why does AKIAABCDEFGHIJKLMNOP return 403?", "C-SECRET", x_agl_classification="INTERNAL")
    s2, h2, _ = _ask(tok, "Reply with the word ok.", "C-SECRET", x_agl_classification="INTERNAL")
    neg = {"action": "prompt containing an AWS access key pattern", "observed": f"HTTP {s1} {h1.get('x-agl-reasons')}", "refused": s1 == 403 and "SECRET_DETECTED" in (h1.get("x-agl-reasons") or "")}
    pos = {"action": "clean prompt", "observed": f"HTTP {s2} {h2.get('x-agl-decision')}", "passed": s2 == 200}
    return neg, pos

def c_restricted(tok):
    s1, h1, _ = _ask(tok, "Here is the production customer table.", "C-RESTRICTED", x_agl_classification="RESTRICTED")
    s2, h2, _ = _ask(tok, "Reply with the word ok.", "C-RESTRICTED", x_agl_classification="INTERNAL")
    return ({"action": "RESTRICTED prompt", "observed": f"HTTP {s1} {h1.get('x-agl-reasons')}", "refused": s1 == 403 and "RESTRICTED_DATA" in (h1.get("x-agl-reasons") or "")},
            {"action": "INTERNAL prompt", "observed": f"HTTP {s2} {h2.get('x-agl-decision')}", "passed": s2 == 200})

def c_quarantine(tok):
    q = db.one("select full_name from repository where ai_exposure = 'quarantined' and classification <> 'RESTRICTED' order by full_name limit 1")
    a = db.one("select full_name from repository where ai_exposure = 'allowed' order by full_name limit 1")
    if not q or not a:
        return ({"action": "request for a quarantined repository", "observed": "no quarantined and allowed pair in the registry", "refused": None},
                {"action": "request for an allowed repository", "observed": "skipped", "passed": None})
    s1, h1, _ = _ask(tok, "Explain this module.", "C-QUARANTINE", x_agl_repo=q["full_name"])
    s2, h2, _ = _ask(tok, "Explain this module.", "C-QUARANTINE", x_agl_repo=a["full_name"])
    return ({"action": f"request with repository context {q['full_name']} (quarantined)", "observed": f"HTTP {s1} {h1.get('x-agl-reasons')}", "refused": s1 == 403 and "REPO_QUARANTINED" in (h1.get("x-agl-reasons") or "")},
            {"action": f"request with repository context {a['full_name']} (allowed)", "observed": f"HTTP {s2} {h2.get('x-agl-decision')}", "passed": s2 == 200})

def c_non_eu(tok):
    try:
        db.run("insert into model_endpoint (model_id, alias, base_url, region, region_country, residency, status, classification_ceiling, secret_ref) select id, 'canary-us', 'https://x', 'us-east-1', 'US', 'EU_REGION_HYPERSCALER', 'approved', 'INTERNAL', 'none' from model limit 1")
        neg = {"action": "register an approved endpoint in us-east-1 as the gateway", "observed": "INSERTED (must not happen)", "refused": False}
        db.run("delete from model_endpoint where alias = 'canary-us'")
    except Exception as e:
        neg = {"action": "register an approved endpoint in us-east-1 as the gateway", "observed": type(e).__name__ + ": " + str(e).splitlines()[0][:160], "refused": True}
    rows = db.all_("select alias, region_country, residency from model_endpoint where status in ('approved','restricted')")
    ok = bool(rows) and all(r["residency"] != "NON_EU_EVALUATING" for r in rows)
    return neg, {"action": "list usable endpoints", "observed": ", ".join(f"{r['alias']}@{r['region_country']}" for r in rows), "passed": ok}

def c_audit_delete(tok):
    try:
        db.run("delete from audit_event where seq = (select min(seq) from audit_event)")
        neg = {"action": "delete the oldest audit event with the gateway's database role", "observed": "DELETED (must not happen)", "refused": False}
    except Exception as e:
        neg = {"action": "delete the oldest audit event with the gateway's database role", "observed": type(e).__name__ + ": " + str(e).splitlines()[0][:160], "refused": True}
    n = db.one("select count(*) as n from audit_event")["n"]
    return neg, {"action": "read the audit hot copy", "observed": f"{n} events readable", "passed": n > 0}

def c_worm(tok):
    seg = db.one("select object_uri from audit_segment order by started_at limit 1")
    if not seg:
        return ({"action": "delete a WORM segment", "observed": "no segment yet", "refused": None}, {"action": "", "observed": "skipped", "passed": None})
    key = seg["object_uri"].split(f"s3://{config.AUDIT_BUCKET}/", 1)[1]
    try:
        vers = audit.chain.s3.list_object_versions(Bucket=config.AUDIT_BUCKET, Prefix=key).get("Versions", [])
        vid = next(v["VersionId"] for v in vers if v["Key"] == key)
        audit.chain.s3.delete_object(Bucket=config.AUDIT_BUCKET, Key=key, VersionId=vid)
        neg = {"action": f"delete locked version of {key} with the store's root credentials", "observed": "DELETED (must not happen)", "refused": False}
    except Exception as e:
        neg = {"action": f"delete locked version of {key} with the store's root credentials", "observed": str(e)[:160], "refused": "WORM" in str(e) or "retention" in str(e).lower() or "Lock" in str(e)}
    body = audit.chain.s3.get_object(Bucket=config.AUDIT_BUCKET, Key=key)["Body"].read()
    return neg, {"action": "read the same segment", "observed": f"{len(body)} bytes readable", "passed": len(body) > 0}

def c_tamper(tok):
    bad = audit.chain.verify(simulate_tamper=True)
    good = audit.chain.verify()
    return ({"action": "verify the chain with one event edited in a copy", "observed": f"result {bad['result']}, broken links {len(bad['broken_links'])}", "refused": bad["result"] == "fail" and len(bad["broken_links"]) >= 1},
            {"action": "verify the chain as stored", "observed": f"result {good['result']}, {good['events_verified']} events", "passed": good["result"] == "pass"})

def c_egress(tok):
    def probe(host, port):
        try:
            s = socket.create_connection((host, port), timeout=4); s.close(); return "connected"
        except Exception as e:
            return type(e).__name__
    neg_obs = probe("one.one.one.one", 443)   # any host outside the stack: there must be no route at all
    pos_obs = probe(config.LOCAL_BACKEND_URL.split("://", 1)[1].split("/")[0].split(":")[0], int(config.LOCAL_BACKEND_URL.rsplit(":", 1)[1].split("/")[0]))
    return ({"action": "TCP connect from the gateway to a public host (one.one.one.one:443)", "observed": neg_obs, "refused": neg_obs != "connected"},
            {"action": f"TCP connect from the gateway to the self-hosted model backend", "observed": pos_obs, "passed": pos_obs == "connected"})

CANARIES = {
    "C-SECRET":     ("G3 code leakage / DLP", "A credential pattern is blocked; a clean prompt passes", c_secret),
    "C-RESTRICTED": ("G1 production data", "RESTRICTED never reaches a model; INTERNAL does", c_restricted),
    "C-QUARANTINE": ("G1/G5 quarantine", "A quarantined repository is refused; an allowed one passes", c_quarantine),
    "C-NON-EU":     ("G2 EU only", "The gateway cannot register an approved non-EU endpoint; only EU endpoints are usable", c_non_eu),
    "C-AUDIT-DEL":  ("G6 immutability", "The gateway's own role cannot delete audit rows; the hot copy stays readable", c_audit_delete),
    "C-WORM":       ("G6 immutability", "Root credentials cannot delete a locked segment; it stays readable", c_worm),
    "C-TAMPER":     ("G6 immutability", "An edited event breaks verification; the stored chain verifies", c_tamper),
    "C-EGRESS":     ("G2 EU only / G3", "No route from the gateway to a non-EU host; the self-hosted backend is reachable", c_egress),
}

def run(ids: list | None, token: str, actor_id: str, subject: str) -> dict:
    results = []
    for cid, (proof, desc, fn) in CANARIES.items():
        if ids and cid not in ids: continue
        t = runs.current_check.set(cid)
        try:
            neg, pos = fn(token)
            res = "pass" if neg.get("refused") and pos.get("passed") else ("skipped" if neg.get("refused") is None else "fail")
            ev = audit.chain.append("canary_result", {"check": cid, "canary": cid, "proof": proof, "description": desc, "result": res, "negative": neg, "positive": pos, "run_by": subject},
                                    actor_identity_id=actor_id, outcome=res)
            results.append({"id": cid, "proof": proof, "description": desc, "result": res, "negative": neg, "positive": pos, "event_id": ev["event_id"]})
        except Exception as e:
            ev = audit.chain.append("canary_result", {"check": cid, "canary": cid, "proof": proof, "result": "error", "error": str(e)[:200], "run_by": subject}, actor_identity_id=actor_id, outcome="error")
            results.append({"id": cid, "proof": proof, "description": desc, "result": "error", "error": str(e)[:200], "event_id": ev["event_id"]})
        finally:
            runs.current_check.reset(t)
    overall = "pass" if results and all(r["result"] in ("pass", "skipped") for r in results) else "fail"
    return {"result": overall, "canaries": results}
