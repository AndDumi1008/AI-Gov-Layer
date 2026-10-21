import os, sys, tempfile, pathlib
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

def test_digests_and_drift(monkeypatch):
    from app import runs
    root = tempfile.mkdtemp()
    (pathlib.Path(root) / "policy").mkdir(); (pathlib.Path(root) / "proxy").mkdir()
    (pathlib.Path(root) / "policy" / "a.rego").write_text("package a")
    (pathlib.Path(root) / "proxy" / "squid.conf").write_text("http_access deny all")
    monkeypatch.setattr(runs, "CONFIG_ROOT", root)
    d1 = runs.compute_digests()
    assert d1["policy_bundle"]["files"] == 1 and d1["egress_allowlist"]["digest"].startswith("sha256:")
    assert d1["workflow_templates"]["missing"] is True
    (pathlib.Path(root) / "policy" / "a.rego").write_text("package a\nallow := true")
    d2 = runs.compute_digests()
    changes = runs.drift({"digests": d1, "images": {"agl-gateway:latest": "sha256:old"}}, {**d2, "_images": {"agl-gateway:latest": "sha256:new"}})
    items = {c["item"] for c in changes}
    assert items == {"policy_bundle", "image:agl-gateway:latest"}
    assert runs.drift(None, d2) == []
