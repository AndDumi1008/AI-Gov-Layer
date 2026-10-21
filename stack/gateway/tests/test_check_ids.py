"""Scenario ids are unique: the scoreboard groups events and results by id, and checks.json is the export of report.py's MAP."""
import ast, collections, json, pathlib, re
import pytest

ROOT = pathlib.Path(__file__).resolve().parents[3]
SUITE = ROOT / "demo" / "run-scenarios.sh"
REPORT = ROOT / "demo" / "report.py"
CHECKS = pathlib.Path(__file__).resolve().parent.parent / "app" / "static" / "checks.json"

def _need_demo():
    if not SUITE.exists() or not REPORT.exists():
        pytest.skip("demo/ not in this build context (container run); CI checks it from the checkout")

def _dupes(ids):
    return [i for i, n in collections.Counter(ids).items() if n > 1]

def _map_node():
    tree = ast.parse(REPORT.read_text())
    return next(n.value for n in tree.body if isinstance(n, ast.Assign) and any(getattr(t, "id", None) == "MAP" for t in n.targets))

def test_suite_ids_are_unique():
    _need_demo()
    text = SUITE.read_text()
    assert not _dupes(re.findall(r"^say \"(S\d+[a-z]?)\b", text, re.M)), "two scenarios share a say id (their events merge)"
    assert not _dupes(re.findall(r"\bcheck (S\d+[a-z]*)\b", text)), "two checks share an id (their results merge)"

def test_report_map_has_no_duplicate_keys():
    _need_demo()
    keys = [k.value for k in _map_node().keys]
    assert not _dupes(keys)

def test_every_suite_check_is_in_the_map():
    _need_demo()
    keys = {k.value for k in _map_node().keys}
    assert set(re.findall(r"\bcheck (S\d+[a-z]*)\b", SUITE.read_text())) <= keys

def test_checks_json_is_the_map_export():
    _need_demo()
    m = ast.literal_eval(_map_node())
    assert CHECKS.read_text() == json.dumps({k: {"proof": p, "title": t, "annex": a} for k, (p, t, a) in m.items()}, indent=1, ensure_ascii=False)
