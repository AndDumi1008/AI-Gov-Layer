"""EU only, no exception (PD-43, issue #19): the gateway has no route to a non-EU provider."""
import os, pathlib, re, sys
import pytest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from app import config, providers

APP = pathlib.Path(__file__).resolve().parent.parent / "app"
SQUID = pathlib.Path(__file__).resolve().parents[2] / "proxy" / "squid.conf"

def test_default_alias_is_the_self_hosted_tier():
    assert config.DEFAULT_ALIAS == config.LOCAL_ALIAS

def test_no_backend_for_any_other_alias():
    with pytest.raises(providers.BackendError):
        providers.call({"alias": "code-default"}, {}, {"messages": [], "max_tokens": 16})

def test_local_backend_down_fails_closed(monkeypatch):
    # no fallback: an unreachable self-hosted tier is a BackendError (502, reservation released), never another model
    monkeypatch.setattr(config, "LOCAL_BACKEND_URL", "http://127.0.0.1:9")
    with pytest.raises(providers.BackendError):
        providers.call({"alias": config.LOCAL_ALIAS}, {}, {"messages": [{"role": "user", "content": "hi"}], "max_tokens": 16})

def test_no_external_provider_in_the_code():
    for f in APP.glob("*.py"):
        assert not re.search(r"api\.anthropic\.com|api\.openai\.com|EXTERNAL_BACKEND", f.read_text()), f.name

def test_egress_allowlist_is_empty():
    if not SQUID.exists():
        pytest.skip("proxy config not in this build context (container run); CI checks it from the checkout")
    assert not re.search(r"^\s*acl\s+allowed_dst\b", SQUID.read_text(), re.M)
