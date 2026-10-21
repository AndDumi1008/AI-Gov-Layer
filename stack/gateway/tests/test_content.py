"""Content store (PD-50): bodies sealed per team and bound to their event; no key means no service."""
import base64, os, sys
import pytest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from app import config, content

KEY = base64.b64encode(bytes(range(32))).decode()

@pytest.fixture
def key(monkeypatch):
    monkeypatch.setattr(config, "CONTENT_KEY", KEY)

def test_roundtrip(key):
    blob = content.seal("team-a", "ev-1", "Write a function that parses an ISO date.")
    assert b"ISO date" not in blob
    assert content.unseal("team-a", "ev-1", blob) == "Write a function that parses an ISO date."

def test_body_cannot_move_to_another_event(key):
    blob = content.seal("team-a", "ev-1", "secret plan")
    with pytest.raises(content.ContentUnavailable):
        content.unseal("team-a", "ev-2", blob)

def test_teams_have_separate_keys(key):
    blob = content.seal("team-a", "ev-1", "x")
    with pytest.raises(content.ContentUnavailable):
        content.unseal("team-b", "ev-1", blob)
    assert content.key_id("team-a") != content.key_id("team-b") and content.key_id(None) == "hkdf:org:v1"

@pytest.mark.parametrize("bad", [None, "", "not base64!", base64.b64encode(b"short").decode()])
def test_no_usable_key_is_not_ready(monkeypatch, bad):
    monkeypatch.setattr(config, "CONTENT_KEY", bad)
    assert not content.ready()
    with pytest.raises(content.ContentUnavailable):
        content.seal("team-a", "ev-1", "x")

def test_the_key_has_no_default():
    src = open(os.path.join(os.path.dirname(__file__), "..", "app", "config.py")).read()
    assert 'os.environ.get("AGL_CONTENT_KEY")' in src
