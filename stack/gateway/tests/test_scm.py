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

def run(id_, conclusion):
    return {"id": id_, "conclusion": conclusion, "name": "ci"}

def test_post_merge_run_still_running_at_import_is_completed_not_mismatched():
    # gh reports conclusion "" while a run is in progress; the same run finishing later is a completion (#7)
    r = scm.compare({"m1": rec("m1", post_merge_run=run(7, ""))}, [rec("m1", post_merge_run=run(7, "success"))])
    assert r["mismatches"] == [] and r["completions"] == ["m1"] and [x["merge_commit"] for x in r["imports"]] == ["m1"]

def test_post_merge_run_not_yet_listed_at_import_is_completed():
    r = scm.compare({"m1": rec("m1", post_merge_run=None)}, [rec("m1", post_merge_run=run(7, "success"))])
    assert r["mismatches"] == [] and r["completions"] == ["m1"]

def test_still_running_on_both_sides_is_a_match():
    r = scm.compare({"m1": rec("m1", post_merge_run=run(7, ""))}, [rec("m1", post_merge_run=run(7, ""))])
    assert r["matches"] == ["m1"] and r["completions"] == [] and r["imports"] == []

def test_changed_final_conclusion_or_other_run_is_still_a_mismatch():
    # a recorded outcome that changes (a re-run after failure) or a different run is evidence, not completion
    r = scm.compare({"m1": rec("m1", post_merge_run=run(7, "failure"))}, [rec("m1", post_merge_run=run(7, "success"))])
    assert [m["kind"] for m in r["mismatches"]] == ["changed"] and r["completions"] == []
    r = scm.compare({"m1": rec("m1", post_merge_run=run(7, ""))}, [rec("m1", post_merge_run=run(8, "success"))])
    assert [m["kind"] for m in r["mismatches"]] == ["changed"] and r["completions"] == []

def test_completion_does_not_hide_another_change():
    r = scm.compare({"m1": rec("m1", post_merge_run=run(7, ""))}, [rec("m1", post_merge_run=run(7, "success"), merged_by="c")])
    assert [m["kind"] for m in r["mismatches"]] == ["changed"] and r["completions"] == [] and r["imports"] == []

def test_old_record_version_is_reimported_not_mismatched():
    old = rec("m1"); old.pop("gates_red"); old.pop("gates_not_reported"); old.pop("record_version")   # stored by the v1 collector
    r = scm.compare({"m1": old}, [rec("m1")])
    assert r["upgrades"] == ["m1"] and [x["merge_commit"] for x in r["imports"]] == ["m1"] and r["mismatches"] == []
