"""Budget ledger: envelopes per org/team, reserve → settle (or release), top-ups with dual control."""
import uuid
from decimal import Decimal
from . import db

ORG_ID = "00000000-0000-0000-0000-000000000001"

def price_for(endpoint_id: str) -> dict:
    row = db.one("""select input_per_1m_eur, output_per_1m_eur, coalesce(cached_input_per_1m_eur,0) as cached_input_per_1m_eur
                    from price where model_endpoint_id=%s and effective_from<=current_date and (effective_to is null or effective_to>current_date)
                    order by effective_from desc limit 1""", (endpoint_id,))
    return row or {"input_per_1m_eur": Decimal(0), "output_per_1m_eur": Decimal(0), "cached_input_per_1m_eur": Decimal(0)}

def cost(price: dict, input_tokens: int, output_tokens: int, cached: int = 0) -> Decimal:
    return (Decimal(input_tokens) * price["input_per_1m_eur"] + Decimal(output_tokens) * price["output_per_1m_eur"]
            + Decimal(cached) * price["cached_input_per_1m_eur"]) / Decimal(1_000_000)

def state(team_id: str | None) -> dict:
    out = {"org": None, "team": None}
    org = db.one("select * from budget_state('org', %s)", (ORG_ID,))
    if org:
        out["org"] = {"envelope_id": str(org["envelope_id"]), "amount_eur": float(org["amount_eur"]), "consumed_eur": float(org["consumed_eur"]), "pct": float(org["pct"]), "soft_pct": org["soft_pct"]}
    if team_id:
        t = db.one("select * from budget_state('team', %s)", (team_id,))
        if t:
            out["team"] = {"envelope_id": str(t["envelope_id"]), "amount_eur": float(t["amount_eur"]), "consumed_eur": float(t["consumed_eur"]), "pct": float(t["pct"]), "soft_pct": t["soft_pct"]}
    return out

def reserve(st: dict, est: Decimal, request_id: str, identity_id: str, endpoint_id: str) -> str:
    rid = str(uuid.uuid4())
    for scope in ("org", "team"):
        if st.get(scope):
            db.run("""insert into budget_ledger (envelope_id, kind, amount_eur, request_id, reservation_id, identity_id, model_endpoint_id)
                      values (%s,'reserve',%s,%s,%s,%s,%s)""", (st[scope]["envelope_id"], est, request_id, rid, identity_id, endpoint_id))
    return rid

def settle(st: dict, rid: str, est: Decimal, actual: Decimal, request_id: str, identity_id: str, endpoint_id: str, it: int, ot: int, ct: int = 0):
    delta = actual - est
    for scope in ("org", "team"):
        if st.get(scope):
            db.run("""insert into budget_ledger (envelope_id, kind, amount_eur, request_id, reservation_id, identity_id, model_endpoint_id, input_tokens, output_tokens, cached_tokens)
                      values (%s,'settle',%s,%s,%s,%s,%s,%s,%s,%s)""", (st[scope]["envelope_id"], delta, request_id, rid, identity_id, endpoint_id, it, ot, ct))

def release(st: dict, rid: str, est: Decimal, request_id: str, identity_id: str, endpoint_id: str):
    for scope in ("org", "team"):
        if st.get(scope):
            db.run("""insert into budget_ledger (envelope_id, kind, amount_eur, request_id, reservation_id, identity_id, model_endpoint_id)
                      values (%s,'release',%s,%s,%s,%s,%s)""", (st[scope]["envelope_id"], -est, request_id, rid, identity_id, endpoint_id))

def request_topup(envelope_id: str, requested_by: str, amount: Decimal, justification: str) -> dict:
    row = db.one("""insert into topup_request (envelope_id, requested_by, amount_eur, justification, expires_at)
                    values (%s,%s,%s,%s, now() + interval '7 days') returning id, status""", (envelope_id, requested_by, amount, justification))
    return {"id": str(row["id"]), "status": row["status"]}

def approve_topup(topup_id: str, approver: str, note: str) -> dict:
    t = db.one("select * from topup_request where id=%s", (topup_id,))
    if not t:
        raise ValueError("top-up not found")
    if t["status"] != "open":
        raise ValueError(f"top-up is {t['status']}")
    if str(t["requested_by"]) == approver:
        raise ValueError("approver must differ from requester")
    db.run("update topup_request set status='approved', decided_by=%s, decided_at=now(), decision_note=%s where id=%s", (approver, note, topup_id))
    db.run("insert into budget_ledger (envelope_id, kind, amount_eur, identity_id) values (%s,'adjustment',%s,%s)", (t["envelope_id"], -t["amount_eur"], approver))
    return {"id": topup_id, "status": "approved", "credit_eur": float(t["amount_eur"])}
