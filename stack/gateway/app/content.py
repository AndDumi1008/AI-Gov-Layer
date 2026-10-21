"""Content store (owner decision 2026-10-21, PD-50): the prompt and answer of every request that reached a model,
and every command an agent asked to run with its output. Kept apart from the audit store, which holds only
fingerprints (D-09), so erasing content never touches the hash chain; each record carries the fingerprint its audit
event holds, so a stored body can be checked against the immutable record.

Bodies are AES-256-GCM encrypted with a per-team key derived from AGL_CONTENT_KEY (HKDF-SHA256); the event id is
bound as associated data, so a body cannot be moved to another event. Retention is AGL_CONTENT_RETENTION_DAYS (30);
expired and erased records keep their row and fingerprints with the bodies set to null.
Reading takes two people: one asks with a reason, a different person approves, the asker reads for 24 hours.
Without a key every model request fails closed: no prompt reaches a model unless it can be stored."""
import base64, binascii, os, threading, time, uuid
from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from . import config, db

KEY_VERSION = "v1"

class ContentUnavailable(Exception):
    pass

def _master() -> bytes | None:
    try:
        k = base64.b64decode(config.CONTENT_KEY or "", validate=True)
    except (binascii.Error, ValueError):
        return None
    return k if len(k) == 32 else None

def ready() -> bool:
    return _master() is not None

def key_id(team_id: str | None) -> str:
    return f"hkdf:{team_id or 'org'}:{KEY_VERSION}"

def _key(team_id: str | None) -> bytes:
    m = _master()
    if not m:
        raise ContentUnavailable("content store key not configured (AGL_CONTENT_KEY: 32 random bytes, base64)")
    return HKDF(algorithm=hashes.SHA256(), length=32, salt=None, info=f"agl-content:{key_id(team_id)}".encode()).derive(m)

def seal(team_id: str | None, event_id: str, text: str | None) -> bytes | None:
    if text is None:
        return None
    nonce = os.urandom(12)
    return nonce + AESGCM(_key(team_id)).encrypt(nonce, text.encode(), str(event_id).encode())

def unseal(team_id: str | None, event_id: str, blob) -> str | None:
    if blob is None:
        return None
    blob = bytes(blob)
    try:
        return AESGCM(_key(team_id)).decrypt(blob[:12], blob[12:], str(event_id).encode()).decode()
    except InvalidTag as e:
        raise ContentUnavailable("a stored body does not decrypt with the current key (key changed, or the body was moved)") from e

def store(kind: str, event_id: str, identity_id: str, team_id: str | None, prompt: str, prompt_sha256: str,
          response: str | None = None, response_sha256: str | None = None) -> str:
    try:
        rid = str(uuid.uuid4())
        db.run("""insert into content_record (id, event_id, kind, identity_id, team_id, key_id, prompt_cipher, response_cipher,
                                              prompt_sha256, response_sha256, expires_at)
                  values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s, now() + make_interval(days => %s))""",
               (rid, event_id, kind, identity_id, team_id, key_id(team_id), seal(team_id, event_id, prompt), seal(team_id, event_id, response),
                prompt_sha256, response_sha256, config.CONTENT_RETENTION_DAYS))
        return rid
    except ContentUnavailable:
        raise
    except Exception as e:  # noqa: any write failure is a governance failure
        raise ContentUnavailable(f"content store write failed: {str(e)[:160]}") from e

def add_response(event_id: str, identity_id: str, team_id: str | None, response: str, response_sha256: str) -> int:
    """An agent command's output arrives after it ran; it fills the empty response of that command's own record."""
    rows = db.all_("""update content_record set response_cipher=%s, response_sha256=%s
                      where event_id=%s and identity_id=%s and kind='agent_action' and response_cipher is null and erased_at is null returning id""",
                   (seal(team_id, event_id, response), response_sha256, event_id, identity_id))
    return len(rows)

def read(event_id: str) -> list:
    rows = db.all_("""select c.*, i.subject from content_record c left join identity i on i.id=c.identity_id
                      where c.event_id=%s order by c.created_at""", (event_id,))
    out = []
    for r in rows:
        team = str(r["team_id"]) if r["team_id"] else None
        out.append({"record_id": str(r["id"]), "event_id": str(r["event_id"]), "kind": r["kind"], "subject": r["subject"],
                    "created_at": r["created_at"].isoformat(), "expires_at": r["expires_at"].isoformat(),
                    "erased_at": r["erased_at"].isoformat() if r["erased_at"] else None,
                    "prompt": unseal(team, str(r["event_id"]), r["prompt_cipher"]), "response": unseal(team, str(r["event_id"]), r["response_cipher"]),
                    "prompt_sha256": r["prompt_sha256"], "response_sha256": r["response_sha256"]})
    return out

# ---- two-person read (T-CNT-04): one person asks with a reason, a different person approves, the asker reads
ACCESS_HOURS = 24

class AccessRefused(Exception):
    def __init__(self, code: str, msg: str, status: int = 403):
        super().__init__(msg); self.code, self.status = code, status

def stored(event_id: str) -> bool:
    return bool(db.one("select 1 from content_record where event_id=%s", (event_id,)))

def request_access(event_id: str, requested_by: str, reason: str) -> dict:
    row = db.one("""insert into content_access_request (event_id, requested_by, reason) values (%s,%s,%s)
                    returning id, status""", (event_id, requested_by, reason))
    return {"request_id": str(row["id"]), "status": row["status"]}

def approve_access(request_id: str, approver: str) -> dict:
    r = db.one("select * from content_access_request where id=%s", (request_id,))
    if not r:
        raise AccessRefused("NOT_FOUND", "no such access request", 404)
    if r["status"] != "open":
        raise AccessRefused("ACCESS_NOT_OPEN", f"access request is {r['status']}", 409)
    if str(r["requested_by"]) == approver:
        raise AccessRefused("APPROVER_MUST_DIFFER", "a second person must approve: the approver must differ from the requester", 409)
    row = db.one("""update content_access_request set status='approved', approved_by=%s, approved_at=now(),
                    expires_at=now() + make_interval(hours => %s) where id=%s and status='open' returning expires_at, event_id, requested_by""",
                 (approver, ACCESS_HOURS, request_id))
    return {"request_id": request_id, "status": "approved", "event_id": str(row["event_id"]), "requested_by": str(row["requested_by"]),
            "expires_at": row["expires_at"].isoformat()}

def approved_access(request_id: str, event_id: str, reader: str) -> dict:
    r = db.one("""select a.*, ri.subject as requester, ai.subject as approver from content_access_request a
                  join identity ri on ri.id=a.requested_by left join identity ai on ai.id=a.approved_by where a.id=%s""", (request_id,))
    if not r or str(r["event_id"]) != event_id or str(r["requested_by"]) != reader:
        raise AccessRefused("ACCESS_NOT_APPROVED", "no access request of yours for this event; ask first (agl content request)")
    if r["status"] != "approved":
        raise AccessRefused("ACCESS_NOT_APPROVED", "your access request has not been approved by a second person yet")
    if r["expires_at"] <= db.one("select now() as t")["t"]:
        raise AccessRefused("ACCESS_EXPIRED", f"the approval expired after {ACCESS_HOURS} h; ask again")
    return {"request_id": request_id, "requester": r["requester"], "approver": r["approver"], "reason": r["reason"]}

def erasable(event_id: str | None = None, identity_id: str | None = None) -> int:
    return db.one("""select count(*) as n from content_record where erased_at is null
                     and ((%s::uuid is not null and event_id=%s::uuid) or (%s::uuid is not null and identity_id=%s::uuid))""",
                  (event_id, event_id, identity_id, identity_id))["n"]

def erase(erasure_event_id: str, by_identity_id: str, event_id: str | None = None, identity_id: str | None = None) -> int:
    rows = db.all_("""update content_record set prompt_cipher=null, response_cipher=null, erased_at=now(), erased_by=%s, erasure_event_id=%s
                      where erased_at is null and ((%s::uuid is not null and event_id=%s::uuid) or (%s::uuid is not null and identity_id=%s::uuid))
                      returning id""", (by_identity_id, erasure_event_id, event_id, event_id, identity_id, identity_id))
    return len(rows)

def purge_expired() -> int:
    return len(db.all_("""update content_record set prompt_cipher=null, response_cipher=null, erased_at=now()
                          where expires_at <= now() and erased_at is null returning id"""))

def start(append_event) -> None:
    """Retention: every five minutes, expired bodies are removed and the count is written to the audit chain."""
    def loop():
        while True:
            time.sleep(300)
            try:
                n = purge_expired()
                if n:
                    append_event("content_expired", {"records": n, "retention_days": config.CONTENT_RETENTION_DAYS}, outcome="erased")
            except Exception as e:  # noqa
                print("content purge error:", e)
    threading.Thread(target=loop, daemon=True).start()
