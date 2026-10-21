# Demo runbook — AI Governance Layer PoC

Audience: the people who decide whether AI can be adopted under the ISMS (CISO, DPO, engineering lead, finance). 45 minutes: 10 of context, 25 of live proof, 10 of questions. Everything shown is live on SERVER; nothing is a slide of a thing that might work.

## Before the room

| Check | Command / place |
|-------|-----------------|
| Docker Desktop running on SERVER | Windows session; `docker --context server ps` from the Mac shows 9 running containers (`minio-init` exits after creating the buckets) |
| Gateway healthy over TLS | `curl https://gateway.shortandsweet.home.ro:8443/healthz` → `{"ok":true}` |
| Fresh token for Claude Code | `agl login --as dana`, copy `evidence/managed-settings.json` to the system path (sudo) |
| Reset the control plane (logged) | `make demo-server-reset` the evening before, or `agl demo-reset` as sven/ines live, to show that the reset is itself an audit event |
| Open browser tabs | The two interactive pages (Parcel Data Journey, Code to Production Journey). There is no MinIO web console in this build; Object Lock is shown live with `make demo-worm` |
| Chat tab | `https://chat.shortandsweet.home.ro:8443`: the same door with a face; use it for acts 2–4 if the audience is not terminal-minded. It shows who is connected and the verdict chips per answer |
| Terminal font large | the audience reads the headers `X-AGL-Decision`, `X-AGL-Model`, `X-AGL-Rerouted` |

Set once in the demo terminal:

```bash
export AGL_URL=https://gateway.shortandsweet.home.ro:8443 AGL_CA_FILE=$PWD/evidence/agl-root.crt
alias agl='python3 stack/cli/agl'
agl login --as dana
```

## Act 0 — context (10 min)

Open the Parcel Data Journey page. One parcel, two people's data, nine stages. Walk the role selector: courier sees a relay number for one day, sorter sees no names, the AI model sees placeholders, the auditor sees hashes. Stop on the ledger: "every event is hashed with the previous one; try to edit one". Click the tamper button, run verify. This is the mental model for everything that follows.

State the four proofs out loud; they are the agenda:

1. A repository is not exposed to AI until we are certain, and it closes again by itself.
2. A total budget cannot be exceeded.
3. Nothing leaves the EU; CONFIDENTIAL never leaves our hardware.
4. The record is immutable.

## Act 1 — the door (5 min)

```bash
agl whoami                       # identity from the IdP stand-in, team, roles, budget state
agl models                       # code-local (self-hosted, EU) approved; code-default revoked (PD-43)
agl ask "Write a function that parses an ISO date." -c INTERNAL -r shortandsweet/booking-svc
```

Point at the headers: `X-AGL-Decision: allow`, `X-AGL-Model: code-local`, `X-AGL-Cost-EUR`, `X-AGL-Event`. Then:

```bash
agl why <event id>               # the full event: who, which model, region, residency class, decision, policy reasons, prompt hash only
```

Say: the prompt text is not in the record. That is deliberate (D-09): the immutable store holds no personal data, so GDPR erasure never conflicts with immutability.

## Act 2 — privacy and leakage (5 min)

```bash
agl ask "Email ana.popescu@example.ro and jonas.weber@example.de about the parcel." -c INTERNAL
```
`X-AGL-Decision: redact`, `PII_REDACTED`. The model received `[EMAIL_1]`, `[EMAIL_2]`; the answer came back with the real addresses restored inside the gateway.

```bash
agl ask "Why does AKIAABCDEFGHIJKLMNOP fail with 403?" -c INTERNAL
```
Blocked, `SECRET_DETECTED`, with the remediation text a developer sees. Nothing was forwarded.

Then the real tool, no CLI: in a second terminal with the managed settings installed, run Claude Code and paste the same key into a prompt. Same block, from the same gateway. The audience sees the control applies to the tool they will actually use.

## Act 3 — EU only (5 min)

```bash
agl ask "Review this payment reconciliation logic." -c CONFIDENTIAL
```
`X-AGL-Rerouted: code-local`: the request asked for the external model and was answered by Qwen on the GTX 1070 in this building. Cost 0.

```bash
agl ask "Here is the production customer table." -c RESTRICTED --model code-local
```
Blocked, `RESTRICTED_DATA`: not even the local model.

Show the registry refusing a non-EU approved endpoint (S14) on the screen from the evidence report, or live with `docker --context server compose … exec postgres psql` if the audience is technical. Then the network proof: from inside the gateway container, `https://api.openai.com` is refused by the egress proxy. Say: policy says no, the registry says no, and the network says no; three independent layers.

## Act 4 — quarantine (5 min)

```bash
agl repo show shortandsweet/app-x          # quarantined; gate G2 "no_prod_data" open
agl ask "Fix the bug in app-x" -r shortandsweet/app-x      # REPO_QUARANTINED, lists the open item
agl sandbox new shortandsweet/app-x --no-docker            # refused
agl sandbox new shortandsweet/booking-svc --dataset prod-dump-2026-10-18 --no-docker   # PROD_DATA_FORBIDDEN
```
Now clear the gate as two people:

```bash
AGL_TOKEN_FILE=/tmp/t-ines agl login --as ines; AGL_TOKEN_FILE=/tmp/t-teo agl login --as teo
AGL_TOKEN_FILE=/tmp/t-ines agl repo gate shortandsweet/app-x no_prod_data true
AGL_TOKEN_FILE=/tmp/t-ines agl repo gate shortandsweet/app-x dpia_or_risk_ref RISK-2026-021
AGL_TOKEN_FILE=/tmp/t-ines agl repo approve shortandsweet/app-x      # security sign-off
AGL_TOKEN_FILE=/tmp/t-teo  agl repo approve shortandsweet/app-x      # owner sign-off → allowed
agl ask "Fix the bug in app-x" -r shortandsweet/app-x               # allow
AGL_TOKEN_FILE=/tmp/t-ines agl repo gate shortandsweet/app-x no_prod_data false   # requarantined: true
```
Say: the certainties are data, evaluated on every request. Nobody has to remember to close the door.

## Act 5 — budget (3 min)

```bash
AGL_TOKEN_FILE=/tmp/t-sven agl login --as sven      # team payments, envelope 0.01 EUR
for i in 1 2 3 4 5 6; do AGL_TOKEN_FILE=/tmp/t-sven agl ask "Summarise parcel handling rules, iteration $i." -c INTERNAL | grep -E 'Warning|BUDGET' ; done
```
Warning header at 80 %, then `BUDGET_EXHAUSTED`. Top-up by a team lead, approved by finance; show the self-approval refusal first:

```bash
AGL_TOKEN_FILE=/tmp/t-mira agl login --as mira
AGL_TOKEN_FILE=/tmp/t-mira agl topup request 0.50 "self-approval test" --scope org
AGL_TOKEN_FILE=/tmp/t-mira agl topup approve <id>          # refused: approver must differ
```

## Act 6 — immutable (5 min)

```bash
AGL_TOKEN_FILE=/tmp/t-ines agl audit flush; AGL_TOKEN_FILE=/tmp/t-ines agl audit anchor
```
```bash
make demo-worm        # bucket lock config, newest segments, retention COMPLIANCE, versions, delete attempt → "WORM protected", anchors in the second store
```
DBA attempt (S10): `docker --context server exec agl-postgres-1 psql -U postgres -c "delete from audit_event where seq=1"` → "append-only".

```bash
AGL_TOKEN_FILE=/tmp/t-ines agl audit verify                     # pass, N events, anchors match
AGL_TOKEN_FILE=/tmp/t-ines agl audit verify --simulate-tamper   # fail at one event, every later link flagged
```
Close with the reset: `AGL_TOKEN_FILE=/tmp/t-ines agl demo-reset` and then `agl events --limit 1` as ines: the reset is the newest event in the chain. Nothing that happened in the room can be made to un-happen.

## Act 7 — the pipeline (3 min, pages only)

Open the Code to Production Journey. Walk steps 5 to 11 and one detour (rollback). Say plainly: this half is designed and the workflow files exist and lint, but it is not deployed in this PoC; it is Tier 2.

## Questions you will get, and the honest answers

| Question | Answer |
|----------|--------|
| Is any call processed outside the EU? | No. The owner closed the US exception (PD-43): every call runs on the self-hosted tier on SERVER. The registry cannot hold a usable non-EU endpoint (S14, S28), policy refuses one whatever the exceptions (S27), and the egress proxy has no allowed host (S25). An EU-region provider (Bedrock/Vertex EU) is a transfer-time item for the client's own accounts (PD-41). |
| Is the local model good enough? | For CONFIDENTIAL work it is the only option by policy. Quality is a procurement question: a bigger card buys a bigger model. The PoC shows the mechanism, not the final model. |
| Who can turn these controls off? | Policy and registry changes need two approvers and are themselves audit events. Nobody can edit or delete the audit record, including the people who run the system. |
| What does it cost? | Metered to the cent per team and model; one Claude Code turn is about €0.03 at list price. The budget caps are real limits. |
| What is not done? | Merge/deploy governance (Tier 2), IdP integration (tokens are hand-minted and expire in 8 h), high availability, Presidio-grade PII detection, and the 30-day retention on SERVER would be 24 months in production. |
| What leaves the building? | No prompt goes to any model outside SERVER. The code goes to GitHub (see PD-43 for what that means for EU only). Logs never leave. |

## After the room

`make demo-server` produces `evidence/run-<ts>/report.html`: one page with every scenario, the proof it belongs to, the Annex A control, and the chain verification. Attach it to the decision record together with docs/09 (the problem and decision register), which is the honest account of what went wrong and what was decided.
