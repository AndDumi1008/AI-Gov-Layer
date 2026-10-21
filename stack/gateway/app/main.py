"""AI Governance Layer — PoC gateway. One door for model calls: identity → registry → DLP → budget → policy → audit → route."""
import json, uuid, hashlib, re, datetime as dt
from decimal import Decimal
from fastapi import FastAPI, Request, Header, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse, FileResponse, RedirectResponse
import os as _os
from . import config, db, auth, dlp, policy, ledger, audit, formats, providers, runs, scm, canaries

app = FastAPI(title="AGL gateway", version="0.1.0")

@app.middleware("http")
async def _run_correlation(request: Request, call_next):
    """Every event written while handling a request carries the run id from `x-agl-run`, if the caller sent one."""
    token = runs.current_run.set(request.headers.get("x-agl-run") or None)
    ctoken = runs.current_check.set(request.headers.get("x-agl-check") or None)
    try:
        return await call_next(request)
    finally:
        runs.current_run.reset(token); runs.current_check.reset(ctoken)

MESSAGES = {
    "SECRET_DETECTED": ("A credential pattern was found in your prompt. Remove it or replace it with a placeholder. If the key is real, rotate it now.", 403),
    "RESTRICTED_DATA": ("This request is classified RESTRICTED (production data, secrets, special-category personal data). Nothing RESTRICTED is ever sent to an AI model.", 403),
    "REPO_QUARANTINED": ("This repository is quarantined from AI until its gate items are satisfied and signed off (agl repo show <name>).", 403),
    "CLASSIFICATION_CEILING": ("The requested model is not approved for this data classification. Use a model with a higher ceiling (agl models).", 403),
    "MODEL_NOT_APPROVED": ("The requested model is not in the approved registry.", 404),
    "NON_EU_ENDPOINT": ("The requested model is processed outside the EU. Only EU-resident endpoints may be used, and no exception can change that.", 403),
    "BUDGET_EXHAUSTED": ("The AI budget for this period is used up. A team lead can request a top-up: agl topup request <amount> \"<justification>\".", 402),
    "NO_TEAM_BUDGET": ("No budget envelope exists for your team; requests are blocked until a budget owner sets one.", 402),
    "IDENTITY_SUSPENDED": ("Your AI access is suspended. Contact security.", 403),
    "TRAINING_REQUIRED": ("Complete the AI literacy module before using AI tools (AI Act Art. 4).", 403),
    "DELEGATION_EXPIRED": ("The sandbox token has expired or was revoked. Start a new session.", 401),
    "LOCAL_MODEL_UNAVAILABLE": ("CONFIDENTIAL data may only go to the self-hosted tier, which is not available right now.", 503),
    "PRODUCTION_CALLER": ("Requests from production workloads are not permitted.", 403),
    "GOVERNANCE_UNAVAILABLE": ("The AI governance service is unavailable, so requests are paused for safety (fail closed).", 503),
    "BACKEND_ERROR": ("The model backend returned an error.", 502),
}

# ---------- lifecycle
@app.on_event("startup")
def _startup():
    db.open_pool()
    audit.start()          # also recovers hot-copy events that never reached a WORM segment (PD-47)

@app.on_event("shutdown")
def _shutdown():
    """Flush the open segment so a restart never leaves events only in the hot copy (PD-47)."""
    try:
        if audit.chain:
            r = audit.chain.flush()
            print("audit: flushed on shutdown:", r)
    except Exception as e:  # noqa
        print("audit: flush on shutdown failed:", e)

@app.get("/healthz")
def healthz():
    try:
        db.one("select 1")
        return {"ok": True}
    except Exception as e:  # noqa
        return JSONResponse({"ok": False, "error": str(e)}, status_code=503)

@app.get("/.well-known/jwks.json")
def jwks():
    return auth.jwks()

# ---------- identity
class AuthError(Exception):
    def __init__(self, code, msg, status=401):
        self.code, self.msg, self.status = code, msg, status

def identity_from_request(authorization: str | None, x_api_key: str | None = None) -> dict:
    # Clients may send two credentials (Claude Code adds the user's own Anthropic login as a bearer token even
    # when ANTHROPIC_API_KEY is set). Use whichever header carries a JWT issued for the gateway.
    candidates = []
    if authorization and authorization.lower().startswith("bearer "):
        candidates.append(authorization.split(" ", 1)[1].strip())
    if x_api_key:
        candidates.append(x_api_key.strip())
    token = next((c for c in candidates if c.count(".") == 2), candidates[0] if candidates else None)
    if not token:
        raise AuthError("NO_TOKEN", "Missing bearer token. Use `agl login` (PoC) or your IdP token.")
    try:
        claims = auth.verify(token)
    except Exception as e:  # noqa
        raise AuthError("INVALID_TOKEN", f"Token rejected: {e}")
    sub = claims["act"]["sub"] if claims.get("kind") == "agent" else claims["sub"]
    row = db.one("""select i.*, t.name as team_name, cc.code as cost_centre from identity i
                    left join team t on t.id = i.team_id left join cost_centre cc on cc.id = t.cost_centre_id where i.subject=%s""", (sub,))
    if not row:
        raise AuthError("UNKNOWN_IDENTITY", f"No identity for subject '{sub}'.", 403)
    ident = {"id": str(row["id"]), "subject": row["subject"], "kind": claims.get("kind", "human"), "status": row["status"],
             "team_id": str(row["team_id"]) if row["team_id"] else None, "team": row["team_name"], "cost_centre": row["cost_centre"],
             "training_completed": row["training_completed_at"] is not None, "display_name": row["display_name"],
             "claims": claims, "delegation_valid": True}
    if claims.get("kind") == "agent":
        d = db.one("select * from delegated_identity where id=%s", (claims.get("delegation_id"),))
        ident["delegation_valid"] = bool(d) and d["revoked_at"] is None and d["expires_at"] > dt.datetime.now(dt.timezone.utc)
        ident["sandbox_id"] = claims.get("sandbox"); ident["repo"] = claims.get("repo"); ident["tool"] = claims.get("tool")
    return ident

def roles_of(identity_id: str) -> set:
    return {r["role"] for r in db.all_("select role from identity_role where identity_id=%s", (identity_id,))}

def require_role(ident: dict, *roles: str):
    have = roles_of(ident["id"])
    if not have.intersection(roles):
        raise HTTPException(403, {"code": "FORBIDDEN", "message": f"needs one of roles {list(roles)}"})

# ---------- helpers
def endpoint_by_alias(alias: str) -> dict | None:
    return db.one("""select e.*, m.name as model_name, m.version as model_version, p.name as provider_name
                     from model_endpoint e join model m on m.id=e.model_id join provider p on p.id=m.provider_id where e.alias=%s""", (alias,))

def resolve_alias(requested: str) -> str:
    """Map client model names onto registry aliases. Claude Code sends real model names; they land on the default alias."""
    if endpoint_by_alias(requested):
        return requested
    return config.DEFAULT_ALIAS

def active_exceptions() -> list:
    rows = db.all_("select id, type, scope from exception where status='approved' and now() between starts_at and ends_at")
    return [{"id": str(r["id"]), "type": r["type"], "scope": r["scope"]} for r in rows]

RANK = {"PUBLIC": 0, "INTERNAL": 1, "CONFIDENTIAL": 2, "RESTRICTED": 3}

def effective_classification(header: str | None, repo: dict | None) -> tuple[str, str]:
    h = (header or "").upper()
    if h and h not in RANK:
        raise HTTPException(400, {"code": "BAD_CLASSIFICATION", "message": f"x-agl-classification must be one of {list(RANK)}"})
    if repo:
        rc = repo["classification"]
        eff = rc if not h or RANK[rc] >= RANK[h] else h
        return eff, "repo_manifest" if eff == rc else "header"
    return (h or "INTERNAL"), ("header" if h else "default")

def fingerprint(s: str) -> str:
    return "sha256:" + hashlib.sha256(s.encode()).hexdigest()

def err(surface: str, code: str, event_id: str | None, extra: dict | None = None, message: str | None = None):
    msg, status = MESSAGES.get(code, ("Request blocked by policy.", 403))
    body = formats.error_body(surface, status, code, message or msg, event_id, extra)
    headers = {"X-AGL-Decision": "block", "X-AGL-Reasons": code}
    if event_id:
        headers["X-AGL-Event"] = event_id
    return JSONResponse(body, status_code=status, headers=headers)

# ---------- the door
def handle(surface: str, body: dict, authorization, x_api_key, x_agl_classification, x_agl_repo, x_agl_client):
    try:
        ident = identity_from_request(authorization, x_api_key)
    except AuthError as e:
        return err(surface, e.code, None, message=e.msg) if e.code in MESSAGES else JSONResponse(formats.error_body(surface, e.status, e.code, e.msg, None), status_code=e.status)

    req = formats.parse_openai(body) if surface == "openai" else formats.parse_anthropic(body)
    request_id = str(uuid.uuid4())
    repo = None
    repo_name = x_agl_repo or ident.get("repo")
    if repo_name:
        repo = db.one("select id, full_name, classification, ai_exposure from repository where full_name=%s", (repo_name,))
        if not repo:
            return JSONResponse(formats.error_body(surface, 404, "REPO_UNKNOWN", f"repository '{repo_name}' is not registered", None), status_code=404)
    try:
        classification, cls_source = effective_classification(x_agl_classification, repo)
    except HTTPException as e:
        return JSONResponse(formats.error_body(surface, 400, e.detail["code"], e.detail["message"], None), status_code=400)

    alias = resolve_alias(req["model"])
    ep = endpoint_by_alias(alias)
    local_ep = endpoint_by_alias(config.LOCAL_ALIAS)
    text = formats.all_text(req)
    scan = dlp.scan(text)
    client_type = x_agl_client or ("agent" if ident["kind"] == "agent" else "cli")

    try:
        budget = ledger.state(ident["team_id"])
        exceptions = active_exceptions()
        pin = {
            "identity": {"sub": ident["subject"], "kind": ident["kind"], "status": ident["status"], "training_completed": ident["training_completed"], "delegation_valid": ident["delegation_valid"]},
            "classification": classification,
            "model": {"alias": ep["alias"], "status": ep["status"], "ceiling": ep["classification_ceiling"], "residency": ep["residency"]} if ep else {"alias": alias, "status": "unknown", "ceiling": "PUBLIC", "residency": "none"},
            "local_model": {"alias": local_ep["alias"], "status": local_ep["status"], "ceiling": local_ep["classification_ceiling"], "residency": local_ep["residency"]} if local_ep else None,
            "dlp": scan.summary(), "budget": budget, "exceptions": exceptions,
            "client": {"type": client_type, "environment": "dev"},
        }
        if repo:
            pin["repo"] = {"name": repo["full_name"], "classification": repo["classification"], "ai_exposure": repo["ai_exposure"]}
        decision = policy.decide(pin)
    except policy.GovernanceUnavailable as e:
        return err(surface, "GOVERNANCE_UNAVAILABLE", None, {"detail": str(e)})
    except Exception as e:  # DB down etc. → fail closed
        return err(surface, "GOVERNANCE_UNAVAILABLE", None, {"detail": str(e)[:200]})

    target = local_ep if decision["outcome"] == "reroute" else ep
    actor = {"identity_id": ident["id"], "subject": ident["subject"], "kind": ident["kind"], "team_id": ident["team_id"], "team": ident["team"],
             "cost_centre": ident["cost_centre"], "client_type": client_type, "sandbox_id": ident.get("sandbox_id"), "tool": ident.get("tool")}
    model_doc = {"requested": req["model"], "alias": target["alias"] if target else alias, "status": target["status"] if target else "unknown",
                 "provider": target["provider_name"] if target else None, "region": target["region"] if target else None, "residency": target["residency"] if target else None,
                 "rerouted_from": ep["alias"] if decision["outcome"] == "reroute" and ep else None}
    try:
        ev = audit.chain.append("request", {
            "request_id": request_id, "surface": surface, "actor": actor, "model": model_doc,
            "classification": {"declared": x_agl_classification, "effective": classification, "source": cls_source, "repo": repo["full_name"] if repo else None},
            "dlp": scan.summary(), "decision": {k: decision[k] for k in ("outcome", "reasons", "reroute_to", "exception_id", "obligations")},
            "budget": {k: ({"pct": v["pct"]} if v else None) for k, v in budget.items()}, "fingerprints": {"prompt_sha256": fingerprint(text)}},
            actor_identity_id=ident["id"], team_id=ident["team_id"], model_endpoint_id=str(target["id"]) if target else None,
            outcome=decision["outcome"], reasons=decision["reasons"])
    except Exception as e:  # audit write failed → fail closed
        return err(surface, "GOVERNANCE_UNAVAILABLE", None, {"detail": f"audit unavailable: {str(e)[:120]}"})

    if decision["outcome"] == "block":
        code = "NON_EU_ENDPOINT" if "NON_EU_ENDPOINT" in decision["reasons"] else next((r for r in decision["reasons"] if r in MESSAGES), decision["reasons"][0] if decision["reasons"] else "BLOCKED")
        extra = {"reasons": decision["reasons"], "classification": classification}
        if code == "REPO_QUARANTINED" and repo:
            g = db.one("select * from repository_ai_gate where repository_id=%s", (repo["id"],))
            if g:
                extra["open_gate_items"] = [k for k in ("classification_set", "no_prod_data", "no_prod_secrets", "no_prod_connectivity") if not g[k]] + (["dual_signoff"] if not (g["approver_security"] and g["approver_owner"]) else [])
        if code == "CLASSIFICATION_CEILING":
            extra["allowed_models"] = [r["alias"] for r in db.all_("select alias from model_endpoint where status in ('approved','restricted') and classification_ceiling::text >= %s", (classification,))]
        return err(surface, code, ev["event_id"], extra)

    # redaction (PII) — reversible inside this request only
    mapping: dict = {}
    redacted = formats.apply_text(req, lambda s: dlp.redact(s, mapping)[0]) if decision.get("redact") else req

    # budget reserve → call → settle
    price = ledger.price_for(str(target["id"]))
    est = ledger.cost(price, max(1, len(text) // 4), redacted["max_tokens"])
    rid = ledger.reserve(budget, est, request_id, ident["id"], str(target["id"]))
    try:
        out = providers.call(target, req, redacted)
    except providers.BackendError as e:
        ledger.release(budget, rid, est, request_id, ident["id"], str(target["id"]))
        audit.chain.append("completion", {"request_id": request_id, "actor": actor, "model": model_doc, "error": str(e)[:300], "usage": None},
                           actor_identity_id=ident["id"], team_id=ident["team_id"], model_endpoint_id=str(target["id"]), outcome="error")
        return err(surface, "BACKEND_ERROR", ev["event_id"], {"detail": str(e)[:300]})
    actual = ledger.cost(price, out["input_tokens"], out["output_tokens"], out.get("cached_tokens", 0))
    ledger.settle(budget, rid, est, actual, request_id, ident["id"], str(target["id"]), out["input_tokens"], out["output_tokens"], out.get("cached_tokens", 0))
    final_text = dlp.restore(out["text"], mapping) if mapping else out["text"]
    audit.chain.append("completion", {
        "request_id": request_id, "actor": actor, "model": {**model_doc, "backend_model": out.get("model")},
        "usage": {"input_tokens": out["input_tokens"], "output_tokens": out["output_tokens"], "cached_tokens": out.get("cached_tokens", 0),
                  "cost_eur": float(round(actual, 6)), "reservation_id": rid, "provider_request_id": out.get("provider_request_id")},
        "redactions_restored": len(mapping), "fingerprints": {"prompt_sha256": fingerprint(text), "response_sha256": fingerprint(final_text)}},
        actor_identity_id=ident["id"], team_id=ident["team_id"], model_endpoint_id=str(target["id"]), outcome="completed", cost_eur=actual)

    usage = {"input_tokens": out["input_tokens"], "output_tokens": out["output_tokens"]}
    model_label = f"agl/{target['alias']}"
    resp = formats.render_openai(req, final_text, usage, model_label) if surface == "openai" else formats.render_anthropic(req, final_text, usage, model_label)
    headers = {"X-AGL-Event": ev["event_id"], "X-AGL-Decision": decision["outcome"], "X-AGL-Reasons": ",".join(decision["reasons"]), "X-AGL-Model": target["alias"],
               "X-AGL-Cost-EUR": f"{actual:.6f}"}
    if decision["outcome"] == "reroute":
        headers["X-AGL-Rerouted"] = target["alias"]
    if budget.get("team") and budget["team"]["pct"] >= 80:
        headers["X-AGL-Warning"] = f"team budget {budget['team']['pct']:.0f}% used"
    if req["stream"]:
        gen = formats.sse_openai(resp) if surface == "openai" else formats.sse_anthropic(resp)
        return StreamingResponse(gen, media_type="text/event-stream", headers=headers)
    return JSONResponse(resp, headers=headers)

@app.post("/v1/chat/completions")
async def openai_chat(request: Request, authorization: str | None = Header(None), x_api_key: str | None = Header(None),
                      x_agl_classification: str | None = Header(None), x_agl_repo: str | None = Header(None), x_agl_client: str | None = Header(None)):
    return handle("openai", await request.json(), authorization, x_api_key, x_agl_classification, x_agl_repo, x_agl_client)

@app.post("/v1/messages")
async def anthropic_messages(request: Request, authorization: str | None = Header(None), x_api_key: str | None = Header(None),
                             x_agl_classification: str | None = Header(None), x_agl_repo: str | None = Header(None), x_agl_client: str | None = Header(None)):
    return handle("anthropic", await request.json(), authorization, x_api_key, x_agl_classification, x_agl_repo, x_agl_client)

@app.get("/v1/models")
def list_models(authorization: str | None = Header(None)):
    identity_from_request(authorization)
    rows = db.all_("select alias from model_endpoint where status in ('approved','restricted','evaluating')")
    return {"object": "list", "data": [{"id": r["alias"], "object": "model", "owned_by": "agl"} for r in rows]}

# ---------- web chat (static page served by the gateway; same origin, so it reads the X-AGL-* headers)
_STATIC = _os.path.join(_os.path.dirname(__file__), "static")

@app.get("/chat")
def chat_page():
    return FileResponse(_os.path.join(_STATIC, "chat.html"), media_type="text/html")

@app.get("/")
def root():
    return RedirectResponse("/chat")

@app.get("/agl/dev/users")
def dev_users():
    if not config.DEV_ISSUER:
        raise HTTPException(404)
    rows = db.all_("select subject, display_name from identity where kind='human' and status='active' order by subject")
    return {"users": rows}

# ---------- dev issuer (PoC stand-in for the IdP)
@app.post("/agl/dev/mint")
async def dev_mint(request: Request):
    if not config.DEV_ISSUER:
        raise HTTPException(404)
    body = await request.json()
    user = body.get("user")
    if not db.one("select 1 from identity where subject=%s", (user,)):
        raise HTTPException(404, {"code": "UNKNOWN_IDENTITY", "message": f"no seeded identity '{user}'"})
    return {"token": auth.mint(user), "expires_in_hours": config.TOKEN_TTL_HOURS}

# ---------- CLI/admin API
def _ident(authorization):
    try:
        return identity_from_request(authorization)
    except AuthError as e:
        raise HTTPException(e.status, {"code": e.code, "message": e.msg})

@app.get("/agl/whoami")
def whoami(authorization: str | None = Header(None)):
    i = _ident(authorization)
    return {"subject": i["subject"], "display_name": i["display_name"], "kind": i["kind"], "team": i["team"], "cost_centre": i["cost_centre"],
            "roles": sorted(roles_of(i["id"])), "training_completed": i["training_completed"], "budget": ledger.state(i["team_id"]), "sandbox": i.get("sandbox_id")}

@app.get("/agl/models")
def models(authorization: str | None = Header(None)):
    _ident(authorization)
    rows = db.all_("""select e.alias, e.status, e.region, e.region_country, e.residency, e.classification_ceiling, e.cost_tier, p.name as provider, e.next_review_at
                      from model_endpoint e join model m on m.id=e.model_id join provider p on p.id=m.provider_id order by e.cost_tier""")
    exc = active_exceptions()
    for r in rows:
        r["active_exception"] = next((x["id"] for x in exc if x["type"] == "model_enable" and x["scope"].get("model_alias") == r["alias"]), None)
    return {"models": rows}

@app.get("/agl/budget")
def budget(authorization: str | None = Header(None)):
    i = _ident(authorization)
    return ledger.state(i["team_id"])

@app.get("/agl/events")
def events(authorization: str | None = Header(None), limit: int = 20, type: str | None = None):
    i = _ident(authorization)
    roles = roles_of(i["id"])
    if roles & {"security_admin", "auditor", "dpo", "platform_admin"}:
        rows = db.all_("select seq, event_id, ts, type, outcome, reasons, cost_eur, hash from audit_event where (%s::text is null or type=%s) order by seq desc limit %s", (type, type, limit))
    else:
        rows = db.all_("select seq, event_id, ts, type, outcome, reasons, cost_eur, hash from audit_event where actor_identity_id=%s and (%s::text is null or type=%s) order by seq desc limit %s", (i["id"], type, type, limit))
    return {"events": rows}

@app.get("/agl/events/{event_id}")
def event(event_id: str, authorization: str | None = Header(None)):
    i = _ident(authorization)
    row = db.one("select seq, body from audit_event where event_id=%s", (event_id,))
    if not row:
        raise HTTPException(404, {"code": "NOT_FOUND", "message": "no such event"})
    body = row["body"]
    if not (roles_of(i["id"]) & {"security_admin", "auditor", "dpo", "platform_admin"}) and body.get("actor", {}).get("identity_id") != i["id"]:
        raise HTTPException(403, {"code": "FORBIDDEN", "message": "not your event"})
    reasons = body.get("decision", {}).get("reasons", [])
    return {"seq": row["seq"], "event": body, "explanations": {r: MESSAGES[r][0] for r in reasons if r in MESSAGES}}

@app.post("/agl/topup")
async def topup(request: Request, authorization: str | None = Header(None)):
    i = _ident(authorization)
    require_role(i, "team_lead", "budget_owner")
    b = await request.json()
    st = ledger.state(i["team_id"])
    scope = b.get("scope", "team")
    env_id = (st.get(scope) or {}).get("envelope_id")
    if not env_id:
        raise HTTPException(404, {"code": "NO_ENVELOPE", "message": f"no open {scope} envelope"})
    t = ledger.request_topup(env_id, i["id"], Decimal(str(b["amount_eur"])), b["justification"])
    audit.chain.append("budget_topup_requested", {"topup_id": t["id"], "scope": scope, "envelope_id": env_id, "amount_eur": float(b["amount_eur"]), "requested_by": i["subject"]},
                       actor_identity_id=i["id"], team_id=i["team_id"], outcome="open")
    return t

@app.post("/agl/topup/{topup_id}/approve")
async def topup_approve(topup_id: str, request: Request, authorization: str | None = Header(None)):
    i = _ident(authorization)
    require_role(i, "budget_owner", "finance")
    b = await request.json() if await request.body() else {}
    try:
        r = ledger.approve_topup(topup_id, i["id"], b.get("note", ""))
    except ValueError as e:
        raise HTTPException(409, {"code": "TOPUP_REJECTED", "message": str(e)})
    audit.chain.append("budget_exception", {"topup_id": topup_id, "approved_by": i["subject"], "credit_eur": r["credit_eur"]}, actor_identity_id=i["id"], outcome="approved")
    return r

@app.get("/agl/repo/{owner}/{name}")
def repo_show(owner: str, name: str, authorization: str | None = Header(None)):
    _ident(authorization)
    full = f"{owner}/{name}"
    r = db.one("select r.*, g.* from repository r left join repository_ai_gate g on g.repository_id=r.id where r.full_name=%s", (full,))
    if not r:
        raise HTTPException(404, {"code": "REPO_UNKNOWN", "message": full})
    ds = db.all_("select name, origin, mountable from dataset where repository_id=%s", (r["repository_id"] or r["id"],))
    return {"repository": full, "classification": r["classification"], "ai_exposure": r["ai_exposure"],
            "gate": {k: r.get(k) for k in ("classification_set", "no_prod_data", "no_prod_secrets", "no_prod_connectivity", "dpia_or_risk_ref", "approver_security", "approver_owner", "approved_at")},
            "datasets": ds}

@app.post("/agl/repo/{owner}/{name}/gate")
async def repo_gate(owner: str, name: str, request: Request, authorization: str | None = Header(None)):
    """Flip gate items (G1–G5). Any false item re-quarantines the repository (S23)."""
    i = _ident(authorization)
    require_role(i, "security_admin", "platform_admin")
    full = f"{owner}/{name}"
    r = db.one("select id, ai_exposure from repository where full_name=%s", (full,))
    if not r:
        raise HTTPException(404, {"code": "REPO_UNKNOWN", "message": full})
    b = await request.json()
    allowed = {"classification_set", "no_prod_data", "no_prod_secrets", "no_prod_connectivity", "dpia_or_risk_ref"}
    sets = {k: v for k, v in b.items() if k in allowed}
    if not sets:
        raise HTTPException(400, {"code": "BAD_REQUEST", "message": f"keys: {sorted(allowed)}"})
    db.run("insert into repository_ai_gate (repository_id) values (%s) on conflict do nothing", (r["id"],))
    for k, v in sets.items():
        db.run(f"update repository_ai_gate set {k}=%s, updated_at=now() where repository_id=%s", (v, r["id"]))
    g = db.one("select * from repository_ai_gate where repository_id=%s", (r["id"],))
    requarantined = False
    if not all(g[k] for k in ("classification_set", "no_prod_data", "no_prod_secrets", "no_prod_connectivity")) and r["ai_exposure"] == "allowed":
        db.run("update repository set ai_exposure='quarantined' where id=%s", (r["id"],)); requarantined = True
    audit.chain.append("repo_gate_change", {"repository": full, "changes": sets, "by": i["subject"], "requarantined": requarantined}, actor_identity_id=i["id"], outcome="updated")
    return {"repository": full, "gate": {k: g[k] for k in sets}, "requarantined": requarantined}

@app.post("/agl/repo/{owner}/{name}/approve")
def repo_approve(owner: str, name: str, authorization: str | None = Header(None)):
    """Dual sign-off: a security_admin fills approver_security, a team_lead/platform_admin fills approver_owner. Both present + gate true → allowed."""
    i = _ident(authorization)
    roles = roles_of(i["id"])
    full = f"{owner}/{name}"
    r = db.one("select id from repository where full_name=%s", (full,))
    if not r:
        raise HTTPException(404, {"code": "REPO_UNKNOWN", "message": full})
    db.run("insert into repository_ai_gate (repository_id) values (%s) on conflict do nothing", (r["id"],))
    if "security_admin" in roles:
        db.run("update repository_ai_gate set approver_security=%s, updated_at=now() where repository_id=%s", (i["id"], r["id"]))
    elif roles & {"team_lead", "platform_admin"}:
        db.run("update repository_ai_gate set approver_owner=%s, updated_at=now() where repository_id=%s", (i["id"], r["id"]))
    else:
        raise HTTPException(403, {"code": "FORBIDDEN", "message": "security_admin or team_lead/platform_admin"})
    g = db.one("select * from repository_ai_gate where repository_id=%s", (r["id"],))
    allowed_now = False
    if g["approver_security"] and g["approver_owner"] and g["approver_security"] != g["approver_owner"] and all(g[k] for k in ("classification_set", "no_prod_data", "no_prod_secrets", "no_prod_connectivity")):
        try:
            db.run("update repository_ai_gate set approved_at=now() where repository_id=%s", (r["id"],))
            db.run("update repository set ai_exposure='allowed' where id=%s", (r["id"],)); allowed_now = True
        except Exception as e:  # trigger refused
            raise HTTPException(409, {"code": "GATE_NOT_SATISFIED", "message": str(e)[:200]})
    audit.chain.append("repo_gate_change", {"repository": full, "signoff_by": i["subject"], "allowed": allowed_now,
                       "approvers": {"security": str(g["approver_security"]) if g["approver_security"] else None, "owner": str(g["approver_owner"]) if g["approver_owner"] else None}},
                       actor_identity_id=i["id"], outcome="allowed" if allowed_now else "pending")
    return {"repository": full, "ai_exposure": "allowed" if allowed_now else "quarantined", "approvers": {"security": bool(g["approver_security"]), "owner": bool(g["approver_owner"])}}

# ---------- sandboxes and agent actions
@app.post("/agl/sandbox/new")
async def sandbox_new(request: Request, authorization: str | None = Header(None)):
    i = _ident(authorization)
    b = await request.json()
    full, dataset, tool = b.get("repo"), b.get("dataset"), b.get("tool", "claude-code")
    r = db.one("select * from repository where full_name=%s", (full,))
    if not r:
        raise HTTPException(404, {"code": "REPO_UNKNOWN", "message": full})
    if r["ai_exposure"] != "allowed" or not r["ai_sandbox_allowed"]:
        ev = audit.chain.append("sandbox_refused", {"repository": full, "reason": "REPO_QUARANTINED", "by": i["subject"]}, actor_identity_id=i["id"], outcome="refused", reasons=["REPO_QUARANTINED"])
        raise HTTPException(403, {"code": "REPO_QUARANTINED", "message": MESSAGES["REPO_QUARANTINED"][0], "event_id": ev["event_id"]})
    mount = None
    if dataset:
        d = db.one("select * from dataset where name=%s", (dataset,))
        if not d or not d["mountable"]:
            ev = audit.chain.append("sandbox_refused", {"repository": full, "dataset": dataset, "reason": "PROD_DATA_FORBIDDEN", "by": i["subject"]}, actor_identity_id=i["id"], outcome="refused", reasons=["PROD_DATA_FORBIDDEN"])
            raise HTTPException(403, {"code": "PROD_DATA_FORBIDDEN", "message": "only synthetic or masked datasets can be mounted into a sandbox", "event_id": ev["event_id"]})
        mount = {"name": d["name"], "origin": d["origin"]}
    sandbox_id = "sbx-" + uuid.uuid4().hex[:8]
    scopes = ["gateway", "repo:read", "repo:push:feature/*"]
    row = db.one("""insert into delegated_identity (principal_id, tool, sandbox_id, repository_id, scopes, expires_at)
                    values (%s,%s,%s,%s,%s, now() + interval '8 hours') returning id, expires_at""", (i["id"], tool, sandbox_id, r["id"], scopes))
    token = auth.mint(f"agent:{tool}", kind="agent", act={"sub": i["subject"]}, sandbox=sandbox_id, repo=full, tool=tool, scopes=scopes, delegation_id=str(row["id"]))
    ev = audit.chain.append("sandbox_created", {"sandbox_id": sandbox_id, "repository": full, "tool": tool, "principal": i["subject"], "dataset": mount, "scopes": scopes,
                            "expires_at": row["expires_at"].isoformat(), "delegation_id": str(row["id"])}, actor_identity_id=i["id"], team_id=i["team_id"], outcome="created")
    return {"sandbox_id": sandbox_id, "token": token, "repository": full, "dataset": mount, "expires_at": row["expires_at"].isoformat(), "event_id": ev["event_id"]}

@app.post("/agl/sandbox/action")
async def sandbox_action(request: Request, authorization: str | None = Header(None)):
    i = _ident(authorization)
    b = await request.json()
    cmd = b.get("command", "")
    try:
        a = policy.action({"command": cmd, "identity": {"sub": i["subject"], "kind": i["kind"]}, "sandbox": i.get("sandbox_id"), "repo": i.get("repo")})
    except policy.GovernanceUnavailable as e:
        raise HTTPException(503, {"code": "GOVERNANCE_UNAVAILABLE", "message": str(e)})
    ev_type = {"allow": "agent_action_requested", "deny": "agent_action_denied", "require_human": "agent_action_requested"}[a["outcome"]]
    ev = audit.chain.append(ev_type, {"sandbox_id": i.get("sandbox_id"), "principal": i["subject"], "tool": i.get("tool"), "command_sha256": fingerprint(cmd),
                            "command_preview": cmd[:120], "decision": a}, actor_identity_id=i["id"], team_id=i["team_id"], outcome=a["outcome"], reasons=a["reasons"])
    return {"outcome": a["outcome"], "reasons": a["reasons"], "event_id": ev["event_id"]}

@app.post("/agl/sandbox/action/result")
async def sandbox_action_result(request: Request, authorization: str | None = Header(None)):
    i = _ident(authorization)
    b = await request.json()
    ev = audit.chain.append("agent_action_executed", {"sandbox_id": i.get("sandbox_id"), "requested_event_id": b.get("event_id"), "exit_code": b.get("exit_code")},
                            actor_identity_id=i["id"], team_id=i["team_id"], outcome="executed")
    return {"event_id": ev["event_id"]}

@app.post("/agl/sandbox/{sandbox_id}/destroyed")
def sandbox_destroyed(sandbox_id: str, authorization: str | None = Header(None)):
    i = _ident(authorization)
    db.run("update delegated_identity set revoked_at=now() where sandbox_id=%s and revoked_at is null", (sandbox_id,))
    ev = audit.chain.append("sandbox_destroyed", {"sandbox_id": sandbox_id, "by": i["subject"]}, actor_identity_id=i["id"], outcome="destroyed")
    return {"event_id": ev["event_id"]}

# ---------- demo reset (PoC only: available while the dev issuer is on)
@app.post("/agl/admin/demo-reset")
def demo_reset(authorization: str | None = Header(None)):
    """Return the CONTROL PLANE to the seeded demo state: budgets, top-ups, app-x gate, sandboxes.
    The audit chain is untouched by design; the reset itself is appended to it."""
    if not config.DEV_ISSUER:
        raise HTTPException(404)
    i = _ident(authorization); require_role(i, "platform_admin", "security_admin")
    db.run("delete from budget_ledger")
    db.run("delete from topup_request")
    db.run("update delegated_identity set revoked_at = now() where revoked_at is null")
    db.run("""update repository_ai_gate set no_prod_data=false, dpia_or_risk_ref=null, approver_security=null, approver_owner=null, approved_at=null, updated_at=now()
              where repository_id = (select id from repository where full_name='shortandsweet/app-x')""")
    db.run("update repository set ai_exposure='quarantined' where full_name='shortandsweet/app-x'")
    # exceptions are not touched: the US endpoint's model_enable exception was closed for good (PD-43)
    ev = audit.chain.append("admin_action", {"action": "demo_reset", "by": i["subject"],
                            "scope": ["budget_ledger", "topup_request", "delegated_identity", "repository_ai_gate:app-x"],
                            "note": "control plane reset to seed state; audit chain not modified"}, actor_identity_id=i["id"], outcome="reset")
    return {"reset": True, "event_id": ev["event_id"], "audit_events_total": db.one("select count(*) as n from audit_event")["n"]}

# ---------- SCM reconciliation (G6; issue #7)
@app.post("/agl/scm/reconcile")
async def scm_reconcile(request: Request, authorization: str | None = Header(None)):
    """The collector (agl reconcile) submits GitHub-derived merge records for one repository; the gateway
    imports new ones as scm_merge events, flags changed or vanished ones, checks the gates, appends reconcile_result."""
    i = _ident(authorization); require_role(i, "security_admin", "auditor", "platform_admin")
    b = await request.json()
    repo, records = b.get("repo"), b.get("records") or []
    if not repo or not isinstance(records, list):
        raise HTTPException(400, {"code": "BAD_REQUEST", "message": "repo and records[] required"})
    for r in records:
        if not r.get("merge_commit"):
            raise HTTPException(400, {"code": "BAD_REQUEST", "message": "every record needs merge_commit"})
    return scm.reconcile(repo, records, i["subject"], i["id"])

@app.get("/agl/scm/records")
def scm_records(repo: str, authorization: str | None = Header(None)):
    i = _ident(authorization); require_role(i, "security_admin", "auditor", "platform_admin", "dpo")
    return {"repo": repo, "records": list(scm.existing_records(repo).values())}

# ---------- canaries executed by the gateway (DoD; issue #14)
@app.get("/agl/canaries")
def canaries_list(authorization: str | None = Header(None)):
    _ident(authorization)
    return {"canaries": [{"id": k, "proof": v[0], "description": v[1]} for k, v in canaries.CANARIES.items()]}

@app.post("/agl/canary/run")
async def canaries_run(request: Request, authorization: str | None = Header(None)):
    i = _ident(authorization); require_role(i, "security_admin", "auditor", "platform_admin", "developer", "team_lead")
    b = await request.json() if await request.body() else {}
    tok = authorization.split(" ", 1)[1].strip()
    import anyio
    return await anyio.to_thread.run_sync(lambda: canaries.run(b.get("ids"), tok, i["id"], i["subject"]))

# ---------- scoreboard, rendered only from the chain (DoD; issue #9)
@app.get("/agl/scoreboard/{run_id}")
def scoreboard_json(run_id: str, authorization: str | None = Header(None)):
    _ident(authorization)
    evs = db.all_("select seq, event_id, ts, type, outcome, reasons, body from audit_event where body->>'run_id' = %s order by seq", (run_id,))
    if not evs:
        raise HTTPException(404, {"code": "NOT_FOUND", "message": "no events for this run"})
    snap = next((e["body"] for e in evs if e["type"] == "config_snapshot"), None)
    fin = next((e["body"] for e in reversed(evs) if e["type"] == "run_finished"), None)
    by_check: dict = {}
    for e in evs:
        c = e["body"].get("check")
        if c:
            by_check.setdefault(c, []).append({"seq": e["seq"], "event_id": str(e["event_id"]), "type": e["type"], "outcome": e["outcome"], "reasons": e["reasons"] or []})
    results = {r["id"]: r for r in ((fin or {}).get("checks") or {}).get("results", [])}
    checks = []
    for cid in sorted(set(by_check) | set(results), key=lambda x: (int(re.sub(r"\D", "", x) or 0), x)):
        checks.append({"id": cid, "result": results.get(cid, {}).get("result", "no result recorded"), "expect": results.get(cid, {}).get("expect"),
                       "events": by_check.get(cid, [])})
    verifs = [{"event_id": str(e["event_id"]), "seq": e["seq"], **{k: e["body"].get(k) for k in ("result", "events_verified", "segments", "broken_links", "hot_copy_mismatches", "anchors_matching", "anchors", "simulated_tamper")}} for e in evs if e["type"] == "chain_verified"]
    recon = [{"event_id": str(e["event_id"]), "seq": e["seq"], **{k: e["body"].get(k) for k in ("repo", "result", "imported", "matched", "mismatches", "gates_not_green", "gates_not_reported", "self_merged")}} for e in evs if e["type"] == "reconcile_result"]
    return {"run_id": run_id, "rendered_from_events": len(evs), "first_seq": evs[0]["seq"], "last_seq": evs[-1]["seq"],
            "snapshot": {"event_id": next((str(e["event_id"]) for e in evs if e["type"] == "config_snapshot"), None), "digests": (snap or {}).get("digests"), "images": (snap or {}).get("images"),
                         "drift": (snap or {}).get("drift_from_previous"), "previous": (snap or {}).get("previous_snapshot"), "label": (snap or {}).get("label")},
            "finished": {"event_id": next((str(e["event_id"]) for e in reversed(evs) if e["type"] == "run_finished"), None), "result": (fin or {}).get("result"),
                         "passed": ((fin or {}).get("checks") or {}).get("passed"), "failed": ((fin or {}).get("checks") or {}).get("failed")} if fin else None,
            "checks": checks, "chain_verifications": verifs, "reconciliations": recon,
            "unattributed_events": sum(1 for e in evs if not e["body"].get("check") and e["type"] not in ("config_snapshot", "run_finished"))}

@app.get("/agl/runs")
def runs_list(authorization: str | None = Header(None), limit: int = 20):
    _ident(authorization)
    return {"runs": db.all_("select body->>'run_id' as run_id, body->>'label' as label, ts, event_id from audit_event where type='config_snapshot' order by seq desc limit %s", (limit,))}

@app.get("/scoreboard")
def scoreboard_page():
    return FileResponse(_os.path.join(_STATIC, "scoreboard.html"), media_type="text/html")

@app.get("/scoreboard/{run_id}")
def scoreboard_page_run(run_id: str):
    return FileResponse(_os.path.join(_STATIC, "scoreboard.html"), media_type="text/html")

@app.get("/agl/checks")
def checks_map():
    return FileResponse(_os.path.join(_STATIC, "checks.json"), media_type="application/json")

# ---------- runs and configuration digests (DoD; issue #8)
@app.post("/agl/run/start")
async def run_start(request: Request, authorization: str | None = Header(None)):
    """Open a run: record the digests of the configuration in force (policy bundle, egress allowlist, workflow
    templates, compose file) plus client-reported image digests, and the drift from the previous snapshot."""
    i = _ident(authorization)
    b = await request.json() if await request.body() else {}
    run_id = runs.new_run_id()
    digests = runs.compute_digests()
    images = b.get("images") or {}
    prev = runs.previous_snapshot()
    changes = runs.drift(prev, {**digests, "_images": images})
    ev = audit.chain.append("config_snapshot", {"run_id": run_id, "label": b.get("label"), "started_by": i["subject"],
                            "digests": digests, "images": images, "images_source": "client-reported (docker image inspect)" if images else None,
                            "drift_from_previous": changes, "previous_snapshot": prev.get("event_id") if prev else None},
                            actor_identity_id=i["id"], outcome="opened")
    return {"run_id": run_id, "event_id": ev["event_id"], "digests": digests, "images": images, "drift": changes, "previous_snapshot": prev.get("event_id") if prev else None}

@app.post("/agl/run/{run_id}/finish")
async def run_finish(run_id: str, request: Request, authorization: str | None = Header(None)):
    i = _ident(authorization)
    b = await request.json() if await request.body() else {}
    summary = runs.summarise(run_id)
    ev = audit.chain.append("run_finished", {"run_id": run_id, "finished_by": i["subject"], "result": b.get("result"), "checks": b.get("checks"), "summary": summary},
                            actor_identity_id=i["id"], outcome=b.get("result") or "finished")
    return {"run_id": run_id, "event_id": ev["event_id"], "summary": summary}

@app.get("/agl/run/{run_id}")
def run_show(run_id: str, authorization: str | None = Header(None)):
    _ident(authorization)
    snap = db.one("select body from audit_event where type='config_snapshot' and body->>'run_id'=%s", (run_id,))
    fin = db.one("select body from audit_event where type='run_finished' and body->>'run_id'=%s order by seq desc limit 1", (run_id,))
    events = db.all_("select seq, event_id, ts, type, outcome, reasons from audit_event where body->>'run_id'=%s order by seq", (run_id,))
    if not snap:
        raise HTTPException(404, {"code": "NOT_FOUND", "message": "no such run"})
    return {"run_id": run_id, "snapshot": snap["body"], "finished": fin["body"] if fin else None, "events": events}

# ---------- audit operations
@app.post("/agl/audit/flush")
def audit_flush(authorization: str | None = Header(None)):
    i = _ident(authorization); require_role(i, "security_admin", "platform_admin", "auditor")
    return audit.chain.flush() or {"flushed": 0}

@app.post("/agl/audit/anchor")
def audit_anchor(authorization: str | None = Header(None)):
    i = _ident(authorization); require_role(i, "security_admin", "platform_admin", "auditor")
    return audit.chain.anchor()

@app.get("/agl/audit/verify")
def audit_verify(authorization: str | None = Header(None), simulate_tamper: bool = False):
    i = _ident(authorization); require_role(i, "security_admin", "platform_admin", "auditor", "dpo")
    return audit.chain.verify(simulate_tamper=simulate_tamper)

@app.get("/agl/repos")
def repos(authorization: str | None = Header(None)):
    _ident(authorization)
    return {"repositories": db.all_("""select r.full_name, r.classification, r.ai_exposure, r.ai_sandbox_allowed, t.name as team,
                                        g.approver_security is not null as signed_security, g.approver_owner is not null as signed_owner,
                                        array_remove(array[case when not coalesce(g.classification_set,false) then 'classification_set' end,
                                                           case when not coalesce(g.no_prod_data,false) then 'no_prod_data' end,
                                                           case when not coalesce(g.no_prod_secrets,false) then 'no_prod_secrets' end,
                                                           case when not coalesce(g.no_prod_connectivity,false) then 'no_prod_connectivity' end], null) as open_items
                                 from repository r left join team t on t.id=r.team_id left join repository_ai_gate g on g.repository_id=r.id order by r.full_name""")}

@app.get("/agl/datasets")
def datasets(authorization: str | None = Header(None)):
    _ident(authorization)
    return {"datasets": db.all_("select d.name, d.origin, d.mountable, r.full_name as repository from dataset d left join repository r on r.id=d.repository_id order by d.name")}
