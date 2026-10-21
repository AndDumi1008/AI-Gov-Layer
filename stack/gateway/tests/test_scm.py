import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from app import scm

def rec(mc, **kw):
    base = {"merge_commit": mc, "head_sha": "h" + mc, "author": "a", "merged_by": "b", "merged_at": "t", "base_ref": "main",
            "required_checks": {"ci": "success"}, "gates_green": True, "gates_red": [], "gates_not_reported": [], "approvals": ["b"], "labels": [], "post_merge_run": {"id": 1, "conclusion": "success", "name": "ci"}, "pr": 1,
            "record_version": scm.RECORD_VERSION}
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
    r = scm.compare({}, [rec("x", gates_green=False, gates_red=["ci"], required_checks={"ci": "failure"}), rec("y", author="a", merged_by="a"),
                         rec("z", gates_green=False, gates_not_reported=["ticket"], required_checks={"ci": "success", "ticket": None})])
    assert [g["merge_commit"] for g in r["gates_not_green"]] == ["x"]
    assert [g["merge_commit"] for g in r["gates_not_reported"]] == ["z"]
    assert [s["merge_commit"] for s in r["self_merged"]] == ["y"]

def test_old_record_version_is_reimported_not_mismatched():
    old = rec("m1"); old.pop("gates_red"); old.pop("gates_not_reported"); old.pop("record_version")   # stored by the v1 collector
    r = scm.compare({"m1": old}, [rec("m1")])
    assert r["upgrades"] == ["m1"] and [x["merge_commit"] for x in r["imports"]] == ["m1"] and r["mismatches"] == []

def test_completed_post_merge_run_is_an_upgrade_not_a_mismatch():
    pending = rec("m1", post_merge_run={"id": 7, "conclusion": "", "name": "ci"})
    final = rec("m1", post_merge_run={"id": 7, "conclusion": "success", "name": "ci"})
    r = scm.compare({"m1": pending}, [final])
    assert r["upgrades"] == ["m1"] and r["mismatches"] == []
    other = rec("m1", post_merge_run={"id": 7, "conclusion": "success", "name": "ci"}, merged_by="z")
    assert scm.compare({"m1": pending}, [other])["mismatches"][0]["kind"] == "changed"
