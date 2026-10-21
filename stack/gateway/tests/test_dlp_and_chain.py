import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from app import dlp
from app.audit import canon, event_hash

def test_secret_detected():
    r = dlp.scan("here is AKIAABCDEFGHIJKLMNOP and a password = supersecretvalue123")
    assert r.summary()["secrets"] >= 2

def test_pii_detected_counts_types_not_values():
    text = "Contact ana.popescu@example.ro or +40 721 334 512, IBAN RO49AAAA1B31007593840000."
    r = dlp.scan(text)
    assert r.summary()["pii"] == 3
    assert "example.ro" not in str(r.summary())

def test_own_address_is_exempt_and_counted():
    r = dlp.scan("reply to Dana@Example.test and ana.popescu@example.ro", own_values=("dana@example.test",))
    s = r.summary()
    assert s["pii"] == 1 and s["exempt"]["own_identity"] == 1

def test_reserved_test_domains_are_exempt():
    r = dlp.scan("qa@example.com ops@billing.test x@sub.example.org a@b.invalid")
    s = r.summary()
    assert s["pii"] == 0 and s["exempt"]["test_data"] == 4

def test_lookalike_domains_are_not_test_data():
    # example.ro, example.de and notexample.com are ordinary domains somebody can own
    r = dlp.scan("ana@example.ro jonas@example.de bob@notexample.com eve@example.com.evil.ro")
    assert r.summary()["pii"] == 4 and r.summary()["exempt"]["test_data"] == 0

def test_phone_and_iban_are_never_test_data():
    r = dlp.scan("+40 721 334 512 RO49AAAA1B31007593840000")
    assert r.summary()["pii"] == 2 and r.summary()["exempt"] == {"own_identity": 0, "test_data": 0}

def test_hash_chain_detects_edit():
    e1 = {"event_id": "1", "ts": "t", "type": "a", "prev_hash": "sha256:" + "0"*64}
    e1["hash"] = event_hash(e1)
    e2 = {"event_id": "2", "ts": "t", "type": "b", "prev_hash": e1["hash"]}
    e2["hash"] = event_hash(e2)
    assert event_hash(e2) == e2["hash"]
    e1["type"] = "edited"
    assert event_hash(e1) != e1["hash"]
    assert canon({"b": 1, "a": [2, 3]}) == '{"a":[2,3],"b":1}'
