import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from app import dlp
from app.audit import canon, event_hash

def test_secret_detected():
    r = dlp.scan("here is AKIAABCDEFGHIJKLMNOP and a password = supersecretvalue123")
    assert r.summary()["secrets"] >= 2

def test_pii_redact_restore_roundtrip():
    text = "Contact ana.popescu@example.ro or +40 721 334 512, IBAN RO49AAAA1B31007593840000."
    r = dlp.scan(text)
    assert r.summary()["pii"] == 3
    red, mapping = dlp.redact(text)
    assert "example.ro" not in red and "[EMAIL_1]" in red and "[PHONE_1]" in red and "[IBAN_1]" in red
    assert dlp.restore(red, mapping) == text

def test_same_value_same_placeholder_across_messages():
    m = {}
    a, m = dlp.redact("mail ana.popescu@example.ro", m)
    b, m = dlp.redact("again ana.popescu@example.ro and jonas@example.de", m)
    assert a == "mail [EMAIL_1]" and b == "again [EMAIL_1] and [EMAIL_2]"

def test_hash_chain_detects_edit():
    e1 = {"event_id": "1", "ts": "t", "type": "a", "prev_hash": "sha256:" + "0"*64}
    e1["hash"] = event_hash(e1)
    e2 = {"event_id": "2", "ts": "t", "type": "b", "prev_hash": e1["hash"]}
    e2["hash"] = event_hash(e2)
    assert event_hash(e2) == e2["hash"]
    e1["type"] = "edited"
    assert event_hash(e1) != e1["hash"]
    assert canon({"b": 1, "a": [2, 3]}) == '{"a":[2,3],"b":1}'
