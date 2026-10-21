"""Feature catalog (PD-51): what client product questions are answered from must be well formed, must not trip
the gateway's own DLP, and every check it cites as proof must exist in the scenario suite."""
import os, pathlib, re, sys
import pytest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from app import catalog, dlp

ROOT = pathlib.Path(__file__).resolve().parents[3]
CATALOG = ROOT / "stack" / "catalog" / "features.json"
SUITE = ROOT / "demo" / "run-scenarios.sh"

@pytest.fixture(scope="module")
def cat():
    if not CATALOG.exists():
        pytest.skip("catalog not in this build context (container run); CI checks it from the checkout")
    return catalog.load(str(CATALOG))

def test_shape(cat):
    ids = [f["id"] for f in cat["features"]]
    assert len(ids) == len(set(ids))
    for f in cat["features"]:
        assert f["status"] in cat["statuses"], f["id"]
        assert f["name"] and f["what"], f["id"]
        if f["status"] == "partial":
            assert f.get("note"), f"{f['id']}: a partial feature states its limit"

def test_active_features_cite_proof_that_exists(cat):
    if not SUITE.exists():
        pytest.skip("scenario suite not in this build context")
    text = SUITE.read_text()
    checks = set(re.findall(r"\bcheck(?:_absent)? (S\d+[a-z]?)\b", text))
    # looped checks: `for h in a:host b:host; do ... check "S25${h%%:*}"` yields S25a, S25b
    for loop, base in re.findall(r"for h in ([a-z]:\S+(?: [a-z]:\S+)*);.*?\n.*?check \"(S\d+)\$\{h%%:\*\}\"", text, re.S):
        checks |= {base + item.split(":")[0] for item in loop.split()}
    for f in cat["features"]:
        if f["status"] == "active":
            assert f["evidence"], f"{f['id']}: active without proof"
        for e in f["evidence"]:
            if re.fullmatch(r"S\d+[a-z]?", e):
                assert e in checks, f"{f['id']}: cites {e}, which the suite does not check"

def test_prompt_built_from_catalog_passes_dlp(cat):
    # otherwise every product question would be blocked by the catalog itself
    s = dlp.scan(catalog.system_prompt(cat, {"run_id": "run-x", "result": "pass", "checks": {"passed": 1, "failed": 0}, "finished_at": "2026-10-21T00:00:00Z"})).summary()
    assert s["secrets"] == 0 and s["pii"] == 0
