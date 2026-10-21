#!/usr/bin/env bash
# Runs the Tier 1 scenarios (docs/07 §5) against a running stack and writes evidence/.
# Requires: python3, docker, psql (for S10/S14), the stack up via stack/bootstrap.sh.
set -uo pipefail
cd "$(dirname "$0")/.."
export AGL_URL="${AGL_URL:-http://127.0.0.1:4000}"
ENV_FILE="${AGL_ENV_FILE:-stack/.env}"     # SERVER runs (also set AGL_CA_FILE=evidence/agl-root.crt for the Python CLI): point at a copy of SERVER's stack/.env; set DOCKER_CONTEXT=server too
AGL="python3 stack/cli/agl"
EV=evidence/run-$(date -u +%Y%m%dT%H%M%SZ); mkdir -p "$EV"
# Open a run: records configuration digests (and drift) as the first event; every later event carries the run id.
AGL_TOKEN_FILE="$EV/.tok-ines" $AGL login --as ines >/dev/null 2>&1
export AGL_RUN=$(AGL_TOKEN_FILE="$EV/.tok-ines" $AGL run start --label "scenario suite $EV" 2>"$EV/run-start.err") || { echo "could not open a run (gateway down?)"; cat "$EV/run-start.err"; exit 1; }
echo "run $AGL_RUN ($(cat "$EV/run-start.err" | sed 's/^# //'))"
LOG="$EV/scenarios.log"; : > "$LOG"
pass=0; fail=0
BIND_IP=$(grep -E '^BIND_IP=' "$ENV_FILE" | cut -d= -f2); BIND_IP=${BIND_IP:-127.0.0.1}
PSQL="docker compose -f stack/docker-compose.yml exec -T postgres psql -U postgres"

say(){ echo -e "\n== $*" | tee -a "$LOG"; export AGL_CHECK=$(echo "$1" | grep -oE "^S[0-9]+[ab]?" ); }
RESULTS="[]"
check(){ # check <name> <expected-substring> <actual>
  if echo "$3" | grep -qi -- "$2"; then echo "   PASS $1" | tee -a "$LOG"; pass=$((pass+1)); res=pass; else echo "   FAIL $1 (expected '$2')" | tee -a "$LOG"; echo "$3" | head -20 | tee -a "$LOG"; fail=$((fail+1)); res=fail; fi
  RESULTS=$(python3 -c "import json,sys;r=json.loads(sys.argv[1]);r.append({'id':sys.argv[2],'result':sys.argv[3],'expect':sys.argv[4][:80]});print(json.dumps(r))" "$RESULTS" "$1" "$res" "$2")
}
as(){ # as <user> <cmd...>  → run CLI as user (separate token files)
  local u="$1"; shift; AGL_TOKEN_FILE="$EV/.tok-$u" $AGL login --as "$u" >/dev/null 2>&1; AGL_TOKEN_FILE="$EV/.tok-$u" $AGL "$@" 2>&1
}

say "S1  normal INTERNAL prompt → allow"
r=$(as dana ask "Write a function that parses an ISO date." -c INTERNAL -r shortandsweet/booking-svc); echo "$r" >> "$LOG"; check S1 '"X-AGL-Decision": "allow"' "$r"
EV1=$(echo "$r" | grep -o '"X-AGL-Event": "[^"]*"' | cut -d'"' -f4)

say "S2  two emails in prompt → redact, model saw placeholders"
r=$(as dana ask "Email ana.popescu@example.ro and jonas.weber@example.de about the parcel." -c INTERNAL); echo "$r" >> "$LOG"; check S2a 'PII_REDACTED' "$r"
BACKEND=$(grep -E '^AGL_LOCAL_BACKEND_URL=' "$ENV_FILE" | cut -d= -f2); BACKEND=${BACKEND:-http://mock-model:8000}
if echo "$BACKEND" | grep -q mock-model && docker ps --format '{{.Names}}' 2>/dev/null | grep -q '^agl-mock-model-1$'; then
  seen=$(docker exec agl-mock-model-1 python3 -c "import urllib.request,json;print(json.load(urllib.request.urlopen('http://localhost:8000/debug/last'))['prompt'])" 2>/dev/null || echo "n/a")
  echo "model saw: $seen" >> "$LOG"; check S2b '\[EMAIL_1\]' "$seen"
else
  echo "   SKIP S2b (model backend is '$BACKEND' / mock not local: the model-side view is only inspectable on the mock; the redaction itself is proven by S2a and the response headers)" | tee -a "$LOG"
fi

say "S3  AWS key in prompt → block SECRET_DETECTED"
r=$(as dana ask "Why does AKIAABCDEFGHIJKLMNOP fail with 403?" -c INTERNAL); echo "$r" >> "$LOG"; check S3 'SECRET_DETECTED' "$r"

say "S4  CONFIDENTIAL with the model name Claude Code sends → served by code-local, nothing leaves the EU"
r=$(as dana ask "Review this payment reconciliation logic." -c CONFIDENTIAL --model claude-sonnet-4-5); echo "$r" >> "$LOG"; check S4a '"X-AGL-Model": "code-local"' "$r"; check S4b '"model": "agl/code-local"' "$r"

say "S5  CONFIDENTIAL directly to code-local → allow"
r=$(as dana ask "Review this payment reconciliation logic." -c CONFIDENTIAL --model code-local); echo "$r" >> "$LOG"; check S5 '"X-AGL-Decision": "allow"' "$r"

say "S6  RESTRICTED → block RESTRICTED_DATA"
r=$(as dana ask "Here is the production customer table." -c RESTRICTED --model code-local); echo "$r" >> "$LOG"; check S6 'RESTRICTED_DATA' "$r"

say "S7  unknown model alias → falls back to default alias (documented) / unapproved alias blocked"
r=$(as dana ask "hello" --model totally-unknown-model -c INTERNAL); echo "$r" >> "$LOG"; check S7 'X-AGL-Model' "$r"

say "S8  team 'payments' envelope is tiny (0.01 EUR) → warning then BUDGET_EXHAUSTED"
last=""; for i in $(seq 1 30); do last=$(as sven ask "Generate a 200-word summary of parcel handling rules, iteration $i. $(printf 'x%.0s' $(seq 1 1500))" -c INTERNAL); echo "$last" | grep -q BUDGET_EXHAUSTED && break; done
echo "$last" >> "$LOG"; check S8 'BUDGET_EXHAUSTED' "$last"

say "S9  team lead requests top-up, budget owner approves (≠ requester) → requests succeed"
# sven is a developer in payments; teo is lead of logistics-core. For payments, mira (budget_owner) requests? Must differ from approver → use teo as requester of his own team is not payments.
# PoC simplification: mira requests for team scope via her own team (none) → use org scope request by teo, approve by mira.
r=$(as teo topup request 1.00 "Incident work on parcel routing needs more AI calls today; approved by budget owner." --scope org); echo "$r" >> "$LOG"
TID=$(echo "$r" | grep -o '"id": "[^"]*"' | head -1 | cut -d'"' -f4)
r2=$(as mira topup approve "$TID" --note "ok for today"); echo "$r2" >> "$LOG"; check S9a '"status": "approved"' "$r2"
r3=$(as mira topup request 0.50 "self-approval test: must be refused when approver equals requester." --scope org); TID2=$(echo "$r3" | grep -o '"id": "[^"]*"' | head -1 | cut -d'"' -f4)
r4=$(as mira topup approve "$TID2" 2>&1); echo "$r4" >> "$LOG"; check S9b 'approver must differ' "$r4"

say "S10 DBA tries UPDATE/DELETE on audit_event → refused by trigger"
r=$($PSQL -c "delete from audit_event where seq = 1;" 2>&1); echo "$r" >> "$LOG"; check S10a 'append-only' "$r"
r=$($PSQL -c "update audit_event set outcome='allow' where seq = 1;" 2>&1); echo "$r" >> "$LOG"; check S10b 'append-only' "$r"

say "S11 flush + anchor, then try to delete a locked object in MinIO → refused by Object Lock"
r=$(as ines audit flush); echo "$r" >> "$LOG"; r=$(as ines audit anchor); echo "$r" >> "$LOG"
MCRUN="docker run --rm --network agl_agl-net --entrypoint sh bitnamilegacy/minio-client@sha256:00dcc4e58ada0df45bb7d9ee435af98295f96c27c3c68292ce78ec700a87b511 -c"
MCALIAS="mc alias set a http://minio:9000 $(grep -E '^MINIO_ROOT_USER=' "$ENV_FILE"|cut -d= -f2) $(grep -E '^MINIO_ROOT_PASSWORD=' "$ENV_FILE"|cut -d= -f2) >/dev/null"
OBJ=$($MCRUN "$MCALIAS && mc ls --recursive a/agl-audit/segments | awk '{print \$NF}' | head -1" 2>/dev/null)
r=$($MCRUN "$MCALIAS && echo 'plain rm (adds a delete marker only; data stays, verifier reads versions):' && mc rm a/agl-audit/segments/$OBJ 2>&1; echo 'rm of the locked versions:' && mc rm --versions --force a/agl-audit/segments/$OBJ 2>&1; echo 'retention:' && mc retention info a/agl-audit/segments/$OBJ 2>&1 | grep Mode; echo 'real versions still present:' && mc ls --versions a/agl-audit/segments/$OBJ | grep -vc DEL" 2>&1); echo "$r" >> "$LOG"
check S11 'WORM protected' "$r"

say "S12 verify chain (pass) and verify with a simulated edit (fail from that event on)"
r=$(as ines audit verify); echo "$r" >> "$LOG"; check S12a '"result": "pass"' "$r"
r=$(as ines audit verify --simulate-tamper); echo "$r" >> "$LOG"; check S12b '"result": "fail"' "$r"

say "S13 stop OPA → GOVERNANCE_UNAVAILABLE; start → allow again"
docker compose -f stack/docker-compose.yml stop opa >/dev/null 2>&1
r=$(as dana ask "hello" -c INTERNAL); echo "$r" >> "$LOG"; check S13a 'GOVERNANCE_UNAVAILABLE' "$r"
docker compose -f stack/docker-compose.yml start opa >/dev/null 2>&1; sleep 2
r=$(as dana ask "hello again" -c INTERNAL); echo "$r" >> "$LOG"; check S13b '"X-AGL-Decision": "allow"' "$r"

say "S14 register an approved endpoint in a non-EU region → rejected by schema"
r=$($PSQL -c "insert into model_endpoint(model_id,alias,base_url,region,region_country,residency,status,classification_ceiling,secret_ref) select id,'us-direct','https://x','us-east-1','US','EU_REGION_HYPERSCALER','approved','INTERNAL','none' from model limit 1;" 2>&1); echo "$r" >> "$LOG"; check S14 'violates check constraint' "$r"

say "S27 ask for the revoked US endpoint by name → block NON_EU_ENDPOINT, no exception applies"
r=$(as dana ask "hello" --model code-default -c INTERNAL); echo "$r" >> "$LOG"; check S27 'NON_EU_ENDPOINT' "$r"

say "S28 register a non-EU endpoint as evaluating (the old exception path) → rejected by schema"
r=$($PSQL -c "insert into model_endpoint(model_id,alias,base_url,region,region_country,residency,status,classification_ceiling,secret_ref) select id,'us-eval','https://x','us-east-1','US','NON_EU_EVALUATING','evaluating','INTERNAL','none' from model limit 1;" 2>&1); echo "$r" >> "$LOG"; check S28 'violates check constraint' "$r"

say "S19 prompt with quarantined repo context → REPO_QUARANTINED (lists open gate items)"
r=$(as dana ask "Fix the bug in app-x" -r shortandsweet/app-x); echo "$r" >> "$LOG"; check S19 'REPO_QUARANTINED' "$r"

say "S20 sandbox for quarantined repo → refused"
r=$(as dana sandbox new shortandsweet/app-x --no-docker); echo "$r" >> "$LOG"; check S20 'REPO_QUARANTINED' "$r"

say "S21 mount a prod-derived dataset → PROD_DATA_FORBIDDEN"
r=$(as dana sandbox new shortandsweet/booking-svc --dataset prod-dump-2026-10-18 --no-docker); echo "$r" >> "$LOG"; check S21 'PROD_DATA_FORBIDDEN' "$r"

say "S22 clear gate G2 for app-x, security + owner sign off → allowed; S19 now passes"
r=$(as ines repo gate shortandsweet/app-x no_prod_data true); echo "$r" >> "$LOG"
r=$(as ines repo gate shortandsweet/app-x dpia_or_risk_ref RISK-2026-021); echo "$r" >> "$LOG"
r=$(as ines repo approve shortandsweet/app-x); echo "$r" >> "$LOG"
r=$(as teo repo approve shortandsweet/app-x); echo "$r" >> "$LOG"; check S22a '"ai_exposure": "allowed"' "$r"
r=$(as dana ask "Fix the bug in app-x" -r shortandsweet/app-x); echo "$r" >> "$LOG"; check S22b '"X-AGL-Decision": "allow"' "$r"

say "S23 a prod-derived dataset gets attached / gate item flips false → back to quarantined"
r=$(as ines repo gate shortandsweet/app-x no_prod_data false); echo "$r" >> "$LOG"; check S23a '"requarantined": true' "$r"
r=$(as dana ask "Fix the bug in app-x" -r shortandsweet/app-x); echo "$r" >> "$LOG"; check S23b 'REPO_QUARANTINED' "$r"

say "S25 from inside the gateway network, call non-EU hosts (incl. the formerly allowed api.anthropic.com) → egress refused"
for h in a:api.openai.com b:api.anthropic.com; do
r=$(docker exec agl-gateway-1 python3 -c "
import httpx
try:
    r=httpx.get('https://${h#*:}/v1/models',timeout=8); print('HTTP',r.status_code)
except Exception as e: print('REFUSED',type(e).__name__,str(e)[:120])" 2>&1); echo "$r" >> "$LOG"; check "S25${h%%:*}" 'REFUSED\|HTTP 403' "$r"
done

say "S27 reconcile the chain against GitHub's own records (merges, gates, approvals, post-merge runs) — G6"
r=$(as ines reconcile AndDumi1008/AI-Gov-Layer AndDumi1008/parcel-app 2>&1); echo "$r" >> "$LOG"; check S27 'AI-Gov-Layer: pass' "$r"; check S27b 'parcel-app: pass' "$r"
echo "$r" > "$EV/reconcile.txt"

say "S29 gateway-executed canaries: a violation refused and a clean input passed per guardrail, both observations in the chain"
r=$(as ines canary run 2>&1); echo "$r" >> "$LOG"; check S29 "== canaries: pass" "$r"

say "S26 policy replay: 1000 synthetic decisions, count any non-EU route"
# static policy test on the engine in use; the bind mount must be a path on THAT host (SERVER run: AGL_POLICY_PATH=D:/Projects/AI-Gov-Layer/stack/policy)
r=$(docker run --rm -v "${AGL_POLICY_PATH:-$PWD/stack/policy}:/policy:ro" openpolicyagent/opa:1.4.2-static test /policy 2>&1 | tail -1); echo "$r" >> "$LOG"; check S26 'PASS' "$r"

say "S29 stop the self-hosted model → BACKEND_ERROR, no fallback to any other model"
SVC=$(echo "$BACKEND" | grep -q ollama && echo ollama || echo mock-model)
docker compose -f stack/docker-compose.yml stop "$SVC" >/dev/null 2>&1; sleep 2
r=$(as dana ask "hello while the model is down" --model claude-sonnet-4-5 -c INTERNAL); echo "$r" >> "$LOG"; check S29 'BACKEND_ERROR' "$r"
docker compose -f stack/docker-compose.yml start "$SVC" >/dev/null 2>&1; sleep 3

echo -e "\n== $pass passed, $fail failed. Evidence in $EV" | tee -a "$LOG"
RESULT=$([ $fail -eq 0 ] && echo pass || echo fail)
unset AGL_CHECK
CHECKS_JSON=$(python3 -c 'import json,sys;print(json.dumps({"passed":int(sys.argv[1]),"failed":int(sys.argv[2]),"results":json.loads(sys.argv[3])}))' "$pass" "$fail" "$RESULTS")
AGL_TOKEN_FILE="$EV/.tok-ines" $AGL run finish "$AGL_RUN" --result "$RESULT" --checks "$CHECKS_JSON" > "$EV/run-finished.json" 2>/dev/null
AGL_TOKEN_FILE="$EV/.tok-ines" $AGL run show "$AGL_RUN" > "$EV/run.json" 2>/dev/null
as ines events --limit 5 > "$EV/last-events.json" 2>/dev/null; as ines audit verify > "$EV/chain-verification.json" 2>/dev/null
[ $fail -eq 0 ]
