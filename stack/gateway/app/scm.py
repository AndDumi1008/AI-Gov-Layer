"""Reconciliation of the audit chain against the source-control system's own records (G6, DoD "evidence
completeness"; issue #7).

The gateway cannot reach GitHub (internal network) and GitHub-hosted runners cannot reach the gateway, so a
collector (`agl reconcile`, run by a security admin from a machine on the tailnet) fetches GitHub's records and
submits them here. The gateway is the judge: it compares each submitted merge with what the chain already holds,
imports what is new as `scm_merge` events, flags what changed or disappeared, checks that every required gate
was green on the merge commit, and appends a `reconcile_result` event. Any mismatch or red gate = fail.

Only metadata travels: repository, PR number, commit shas, actors, timestamps, check names and conclusions."""
import json
from . import db, audit

# Fields of a merge record that must stay identical between GitHub and the chain.
RECORD_VERSION = 2   # bump when COMPARED gains fields; older stored records are re-imported, not mismatched
COMPARED = ("merge_commit", "head_sha", "author", "merged_by", "merged_at", "base_ref", "required_checks", "gates_green", "gates_red", "gates_not_reported", "approvals", "labels", "post_merge_run")

def fingerprint(rec: dict) -> dict:
    return {k: rec.get(k) for k in COMPARED}

def existing_records(repo: str) -> dict:
    rows = db.all_("select body from audit_event where type = 'scm_merge' and body->>'repo' = %s order by seq", (repo,))
    out = {}
    for r in rows:
        out[r["body"]["merge_commit"]] = r["body"]   # last write wins; records are append-only so re-imports are explicit
    return out

def compare(existing: dict, incoming: list) -> dict:
    """Pure: decide imports, matches and mismatches. `existing` maps merge_commit → stored body; `incoming` are
    GitHub-derived records with at least the COMPARED fields and `pr`."""
    seen = set()
    imports, matches, mismatches, upgrades = [], [], [], []
    for rec in incoming:
        mc = rec["merge_commit"]; seen.add(mc)
        if mc not in existing:
            imports.append(rec); continue
        if int(existing[mc].get("record_version") or 1) < RECORD_VERSION:
            upgrades.append(rec); imports.append(rec); continue   # stored by an older collector: superseded, not mismatched
        a, b = fingerprint(existing[mc]), fingerprint(rec)
        if a == b:
            matches.append(mc)
        else:
            diff = {k: {"chain": a[k], "scm": b[k]} for k in COMPARED if a[k] != b[k]}
            mismatches.append({"kind": "changed", "merge_commit": mc, "pr": rec.get("pr"), "diff": diff})
    for mc, body in existing.items():
        if mc not in seen:
            mismatches.append({"kind": "missing_in_scm", "merge_commit": mc, "pr": body.get("pr")})
    # A required check that REPORTED failure fails the reconciliation. One that never reported (the check did not
    # exist when the PR merged, or the job did not run) is listed, not failed: a control cannot have been observed
    # before it existed; the register records when each check was introduced.
    red = [{"merge_commit": r["merge_commit"], "pr": r.get("pr"), "gates_red": r.get("gates_red"), "required_checks": r.get("required_checks")} for r in incoming if r.get("gates_red")]
    not_reported = [{"merge_commit": r["merge_commit"], "pr": r.get("pr"), "gates_not_reported": r.get("gates_not_reported")} for r in incoming if r.get("gates_not_reported")]
    self_merged = [{"merge_commit": r["merge_commit"], "pr": r.get("pr")} for r in incoming if r.get("author") and r.get("author") == r.get("merged_by")]
    return {"imports": imports, "upgrades": [u["merge_commit"] for u in upgrades], "matches": matches, "mismatches": mismatches, "gates_not_green": red, "gates_not_reported": not_reported, "self_merged": self_merged}

def reconcile(repo: str, incoming: list, submitted_by: str, actor_id: str) -> dict:
    """Import new records, append the result event, return the verdict."""
    existing_prev = existing_records(repo)
    res = compare(existing_prev, incoming)
    imported_ids = []
    for rec in res["imports"]:
        ev = audit.chain.append("scm_merge", {"repo": repo, "source": "github", "collected_by": submitted_by, "record_version": RECORD_VERSION,
                                              "supersedes": existing_prev.get(rec["merge_commit"], {}).get("event_id") if rec["merge_commit"] in res["upgrades"] else None,
                                              **{k: rec.get(k) for k in COMPARED}, "pr": rec.get("pr"), "title": rec.get("title")},
                                actor_identity_id=actor_id, outcome="imported")
        imported_ids.append(ev["event_id"])
    result = "pass" if not res["mismatches"] and not res["gates_not_green"] else "fail"
    ev = audit.chain.append("reconcile_result", {"repo": repo, "source": "github", "collected_by": submitted_by, "result": result,
                            "imported": len(imported_ids), "upgraded": len(res["upgrades"]), "matched": len(res["matches"]), "mismatches": res["mismatches"], "gates_not_green": res["gates_not_green"],
                            "gates_not_reported": res["gates_not_reported"], "self_merged": len(res["self_merged"]), "note": "self-merge is permitted while required approvals = 0 (PD-39); counted, not failed"},
                            actor_identity_id=actor_id, outcome=result)
    return {"repo": repo, "result": result, "imported": len(imported_ids), "upgraded": len(res["upgrades"]), "matched": len(res["matches"]), "mismatches": res["mismatches"],
            "gates_not_green": res["gates_not_green"], "gates_not_reported": res["gates_not_reported"], "self_merged": len(res["self_merged"]), "event_id": ev["event_id"]}
