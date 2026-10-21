import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from app import scm

def rec(mc, **kw):
    base = {"merge_commit": mc, "head_sha": "h" + mc, "author": "a", "merged_by": "b", "merged_at": "t", "base_ref": "main",
            "required_checks": {"ci": "success"}, "gates_green": True, "approvals": ["b"], "labels": [], "post_merge_run": {"id": 1, "conclusion": "success", "name": "ci"}, "pr": 1}
    base.update(kw); return base

def test_import_match_change_missing():
    existing = {"m1": rec("m1"), "m2": rec("m2"), "gone": rec("gone")}
    incoming = [rec("m1"), rec("m2", merged_by="c"), rec("new")]
    r = scm.compare(existing, incoming)
    assert [x["merge_commit"] for x in r["imports"]] == ["new"]
    assert r["matches"] == ["m1"]
    kinds = {(m["kind"], m["merge_commit"]) for m in r["mismatches"]}
    assert kinds == {("changed", "m2"), ("missing_in_scm", "gone")}
    assert r["mismatches"][0]["diff"]["merged_by"] == {"chain": "b", "scm": "c"}

def test_gates_and_self_merge_flags():
    r = scm.compare({}, [rec("x", gates_green=False, required_checks={"ci": "failure"}), rec("y", author="a", merged_by="a")])
    assert [g["merge_commit"] for g in r["gates_not_green"]] == ["x"]
    assert [s["merge_commit"] for s in r["self_merged"]] == ["y"]
