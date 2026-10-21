"""Runs and configuration digests (DoD: "each run records cryptographic digests of the policies, allowlists,
gate templates and image versions in force"). A run is a correlation id carried by every event it produces
(header `x-agl-run`); `config_snapshot` is its first event and `run_finished` its last.

The gateway hashes files from read-only mounts under CONFIG_ROOT (policy bundle, egress allowlist, workflow
templates, compose file, feature catalog). Image digests cannot be read from inside a container without a Docker socket, so the
CLI collects them from the engine and sends them with the start request; they are recorded as client-reported."""
import os, hashlib, uuid, json
from contextvars import ContextVar
from . import db

CONFIG_ROOT = os.environ.get("AGL_CONFIG_ROOT", "/config")
# label → relative path (file or directory) under CONFIG_ROOT
CONFIG_PATHS = {
    "policy_bundle": "policy",
    "egress_allowlist": "proxy/squid.conf",
    "workflow_templates": "workflows",
    "compose": "docker-compose.yml",
    "feature_catalog": "catalog",   # what client product questions are answered from (PD-51)
}

current_run: ContextVar[str | None] = ContextVar("agl_run", default=None)
current_check: ContextVar[str | None] = ContextVar("agl_check", default=None)   # x-agl-check: which canary/check produced the event

def _sha256_path(path: str) -> tuple[str, int]:
    """Digest of a file, or of a directory as the sorted list of (relative name, file digest)."""
    h = hashlib.sha256()
    if os.path.isdir(path):
        n = 0
        for root, dirs, files in os.walk(path):
            dirs.sort()
            for f in sorted(files):
                p = os.path.join(root, f); rel = os.path.relpath(p, path)
                fh = hashlib.sha256(open(p, "rb").read()).hexdigest()
                h.update(f"{rel}\0{fh}\n".encode()); n += 1
        return "sha256:" + h.hexdigest(), n
    with open(path, "rb") as fh:
        h.update(fh.read())
    return "sha256:" + h.hexdigest(), 1

def compute_digests() -> dict:
    out = {}
    for label, rel in CONFIG_PATHS.items():
        p = os.path.join(CONFIG_ROOT, rel)
        if os.path.exists(p):
            d, n = _sha256_path(p); out[label] = {"digest": d, "files": n, "path": rel}
        else:
            out[label] = {"digest": None, "files": 0, "path": rel, "missing": True}
    return out

def previous_snapshot() -> dict | None:
    row = db.one("select body from audit_event where type = 'config_snapshot' order by seq desc limit 1")
    return row["body"] if row else None

def drift(prev: dict | None, now: dict) -> list:
    if not prev:
        return []
    changed = []
    for label, cur in now.items():
        before = (prev.get("digests") or {}).get(label, {}).get("digest")
        if before != cur.get("digest"):
            changed.append({"item": label, "before": before, "after": cur.get("digest")})
    for name, dig in (now.get("_images") or {}).items():
        if (prev.get("images") or {}).get(name) not in (None, dig):
            changed.append({"item": f"image:{name}", "before": prev["images"][name], "after": dig})
    return changed

def new_run_id() -> str:
    return "run-" + uuid.uuid4().hex[:12]

def summarise(run_id: str) -> dict:
    rows = db.all_("""select type, outcome, count(*) as n from audit_event where body->>'run_id' = %s group by type, outcome order by type, outcome""", (run_id,))
    first = db.one("select min(ts) as a, max(ts) as b, count(*) as n from audit_event where body->>'run_id' = %s", (run_id,))
    return {"run_id": run_id, "events": first["n"], "first": first["a"].isoformat() if first["a"] else None, "last": first["b"].isoformat() if first["b"] else None,
            "by_type": [{"type": r["type"], "outcome": r["outcome"], "n": r["n"]} for r in rows]}
