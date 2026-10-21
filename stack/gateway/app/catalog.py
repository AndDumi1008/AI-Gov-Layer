"""Client product questions (owner decision 2026-10-21, PD-51): "is this feature active?", "can we already do this?".

Answers come from the feature catalog, a file reviewed in the repository and hashed into every run's
config_snapshot, plus the result of the latest verification run. The model sees nothing else: no code, no
repository context, no production state, so the "AI never touches production" rule holds for clients too."""
import json, os
from . import db, runs

PATH = os.path.join(runs.CONFIG_ROOT, "catalog", "features.json")

class CatalogUnavailable(Exception):
    pass

def load(path: str = PATH) -> dict:
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError) as e:
        raise CatalogUnavailable(f"feature catalog unavailable: {e}") from e

def last_run() -> dict | None:
    row = db.one("select ts, body from audit_event where type='run_finished' order by seq desc limit 1")
    if not row:
        return None
    b = row["body"]
    return {"run_id": b.get("run_id"), "result": b.get("result"), "checks": b.get("checks"), "finished_at": row["ts"].isoformat()}

def system_prompt(cat: dict, run: dict | None) -> str:
    verified = (f"Latest verification run: {run['run_id']}, result {run['result'] or 'not reported'}, finished {run['finished_at']}"
                + (f", checks {json.dumps(run['checks'])}" if run.get("checks") else "") + ".") if run else "No verification run has been recorded yet."
    return ("You answer questions from the client's product team about what the AI Governance Layer can do today.\n"
            "Answer only from the catalog below. Give the feature id and its status; for 'active', name the checks that prove it; "
            "for 'partial', state the limit; for 'planned' or 'out_of_scope', say plainly that it is not available today.\n"
            "If the catalog does not cover the question, say so and suggest asking the delivery team. Never guess, never describe "
            "source code, and never claim to see production systems or data.\n"
            f"{verified}\n\nCATALOG\n{json.dumps(cat, ensure_ascii=False, separators=(',', ':'))}")
