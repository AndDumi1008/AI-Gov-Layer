# 11 — Audit: current state against the AI Guardrails MVP brief

**Brief:** *AI Adoption Plan* of 28 September 2026 and the MVP Definition of Done of 4–5 October 2026 (healthcare client, ISO 27001; replica built by Discovery XD on synthetic material, demonstrated to the client's product owner, then transferred into the client's own accounts).
**Audited state:** this repository and `parcel-app` at `main` on 2026-10-21, the Tier 1 stack on SERVER, the preview backend on SERVER.
**Method:** each requirement scored **Met / Partial / Missing** against observable evidence (a file, a scenario in `demo/run-scenarios.sh`, a live check), with the gap named. Where the brief's wording is stricter than what we built, the stricter reading is used. Nothing here is weighted by effort; the ranking at the end is.

## 0. Framing differences that colour every line

| Brief says | Our build assumes | Consequence |
|------------|-------------------|-------------|
| Healthcare client; patient data exists in production | Logistics demo with personal data of senders/recipients | The same mechanisms apply, but special-category data raises the floor: anything production-derived is RESTRICTED, never masked-for-AI without a DPIA. Our masked-dataset path needs a DPO sign-off step before it is used for health data. |
| Replica in Discovery XD's environment, transferred **as-is** into the client's cloud and source control | A Windows PC on a tailnet with Docker Desktop, GitHub.com personal account, local JWT issuer | Shape transfers (Compose, policies, workflows, rulesets); substrate does not. The brief implies a cloud footprint with organisation policies, region controls and provider audit logs. None of that exists in the replica. |
| One encrypted connection bundle per developer | Managed settings file + CA certificate + dev token, installed by hand with sudo | Three artefacts and two manual steps instead of one bundle and a passphrase. |
| Canaries fired on demand from a prompt, through a vendor-neutral tool | `demo/run-scenarios.sh` from a shell; chat slash commands for gateway queries | The suite exists; the "from a prompt" trigger does not. |
| Evidence reconciled against the cloud provider's and SCM's own logs | Our own hash-chained store is the only record | Strong tamper evidence, no independent corroboration. |

## 1. Guardrails

| # | Guardrail | Score | What exists (evidence) | Gap against the brief |
|---|-----------|-------|------------------------|-----------------------|
| G1 | Production data isolation | **Partial** | Repository quarantine gate with dual sign-off (S19–S23); dataset catalog refuses `prod-derived` mounts (S21); sandbox image with no credentials and egress to the gateway only (sandbox tests); org-policy deny and network separation **designed** (docs/02 §4.4, F-14) | No production environment exists yet (parcel production stack not built), so "no route, role or shared resource" is untested; the quarterly isolation probe (F-14) is not implemented; **no path for approved aggregate statistics out of production** is designed at all |
| G2 | European processing region | **Partial, with one open violation** | Registry refuses an approved non-EU endpoint (S14, schema check); CONFIDENTIAL rerouted to the self-hosted tier (S4); egress proxy allows one host (S25); every audit event records the registry region and residency class | The external tier is the **US Anthropic endpoint under a 72-hour exception** (registry status `evaluating`); the brief says every other region is denied, not excepted. No EU-region provider (Bedrock/Vertex EU) is configured. "Every call proves where it was processed" is satisfied only by our own registry field, not by a provider-attested region |
| G3 | Code leakage prevention | **Partial** | One path: gateway with managed Claude Code settings, DLP block/redact (S2, S3), no prompt content stored anywhere (D-09; content store not built), local model inherent zero retention | The Claude desktop app bypasses the gateway (PD-35/PD-38) and is only forbidden by policy text (docs/10); vendor zero-retention is a registry flag, not contractually verified; sandbox exists only as a PoC image, no orchestrator |
| G4 | Vulnerability avoidance | **Partial** | Secret scanning on every change in both repositories (CI `secrets`, gitleaks over history); dependency allowlist and SCA (Trivy) in the example workflows | SCA and the dependency allowlist are **not active** on either repository (no dependency manifests yet); no SBOM produced for anything that runs |
| G5 | Production code exposure limitation | **Partial** | Only registered repositories are usable (`REPO_UNKNOWN`, quarantine); rulesets: PR only, no bypass actors, bot approvals not counted, signed commits; delegated agent tokens scoped to feature branches; CODEOWNERS on policy and workflow paths | Required approvals are **0** (single human account, PD-39), so "the AI never approves its own work" rests on the absence of an AI identity rather than on an enforced review; "cannot change the gates" is a CODEOWNERS file pointing at the same one account |
| G6 | Traceability | **Partial (strong on one half)** | Hash-chained, Object-Locked, metadata-only audit store with anchors; verifier detects a single edited event (S10–S12); merge and deploy events designed (TRD §5–6) | **No reconciliation** against GitHub's audit log or any provider log; CI evidence job exists only in the example workflows and the gateway has no OIDC verifier for it; merge/deploy events are not in the chain for the two real repositories |
| G7 | Spend | **Partial** | Hard caps per org and team with reserve/settle (S8), dual-controlled top-ups (S9), budget visible to the developer (headers, CLI, chat), per-identity envelopes supported by the schema | Per **run** quota and per **developer-month** quota are not populated (team/org only); no infrastructure-spend bound or alert; no monthly reconciliation against the provider invoice (F-15 designed) |
| G8 | No retention, no training | **Partial** | Registry fields `training_opt_out`, `zero_retention`; the direct Anthropic entry is honestly recorded as `zero_retention = false`; self-hosted tier inherently retains nothing; DLP as the technical check | No contract or configuration evidence from any provider; the one external provider in use does **not** satisfy the guardrail |
| G9 | Provider and tool change control | **Met in design, Partial in operation** | Registry with dual approval enforced by a database constraint; evaluating status with time-boxed exception; tool allowlist and deny patterns in policy (`action` rules); managed-settings deny list; MCP allowlist designed | Registry changes are made with SQL, not through a reviewed admin API; MCP allowlist not implemented |
| CS | Content security scanning (added after external review) | **Missing** | DLP scans prompts for secrets and personal data | No malware or content scan of uploaded or generated artefacts, and therefore no negative test of such a scanner |

## 2. Acceptance conditions (definition of done)

| Condition | Score | Evidence | Gap |
|-----------|-------|----------|-----|
| One-command start from the bundle alone: connect, fetch sample code, run the task set and the canary suite, succeed only if every canary passes | **Partial** | `make bootstrap && make demo` on a laptop; `make demo-server` from the Mac; exit code is non-zero on any failed check | No encrypted bundle; no "fetch sample code through the controlled path" step; no task set (retrofit requirements, regenerate docs, statistics question) |
| Walking skeleton first, kept green | **Met** | Scenario suite green since the first SERVER run; CI on both repositories green on every PR | — |
| Evidence completeness, matched to provider audit logs (principal, commit, pipeline, model, inference region) | **Missing** | Events carry principal, model, registry region; merge events designed | No match against GitHub or provider logs; commit and pipeline identifiers are not in the chain for real repositories; a missing or stale record does not fail a run |
| Configuration digests recorded per run and shown on the scoreboard | **Missing** | `policy_bundle` and `policy_activation` tables exist; `bundle_digest` is a field on events | The gateway does not compute or record digests of policies, allowlists, workflow templates or image versions; the report shows none |
| Scoreboard rendered only from reconciled evidence, linking to each record | **Partial** | `demo/report.py` renders pass/fail per scenario with the proof and Annex A control, plus the chain verification result | Rendered from the scenario log, not from the evidence store; no links to records; no reconciliation |
| Repeatable from cold from another enrolled machine with only the bundle and its passphrase; dependencies from private mirrors | **Partial** | Second machine needs Tailscale enrolment, the CA trust, a dev token and the repository; all scripted | No bundle; images and packages come from public registries (Docker Hub, GHCR, PyPI); the sandbox's package mirror is designed, not deployed |
| No content outside its place: scans of logs, evidence stores, CI traces and disks after a session | **Partial** | No prompt content is stored by design; DLP findings are types and counts only | No post-session scan is performed; CI traces live on GitHub.com for public repositories (acceptable only because everything is synthetic) |
| A control is evidence only once observed failing: recorded negative observation per control | **Partial** | Negative observations exist and are recorded in `evidence/` for: secrets (S3), RESTRICTED (S6), DBA edit/delete (S10), WORM delete (S11), chain tamper (S12), governance down (S13), non-EU registry (S14), quarantine (S19–S23), egress (S25); sandbox `kill` and egress denials | No negative observation for: SCA, aggregate-statistics path, budget alerts, infrastructure spend, content scanning, provider-log reconciliation (the controls do not exist yet) |

## 3. Working rules set by the owner

| Rule | Score | Observation |
|------|-------|-------------|
| Nothing goes live, is destroyed or incurs spend without explicit, recorded approval stating the expected cost; the owner performs the go-live action personally | **Partial** | The owner merged every PR, pushed the application repository and installed the client settings personally. Spend approvals were not recorded with an expected cost; SERVER actions (compose up, password generation) were performed by the assistant on request without a recorded approval |
| Secrets, MFA codes and security settings handled by the owner only | **Partial** | The Anthropic key was typed by the owner and never seen by the assistant; firewall and ACLs applied by the owner. Database, MinIO and JWT secrets were **generated by the assistant** and copied to SERVER (PD-38). Rotation is open |
| Test-first development | **Missing as a practice** | Tests exist and are green (policy, gateway, schema, RLS, API, scenarios) but were written with or after the code, not first |
| Secret scanning on every change | **Met** | gitleaks in CI on both repositories, full history, allowlist reviewed |
| Every change traceable to a ticket | **Missing** | No ticket system; PRs reference the register, not tickets |
| Independent review of each plan, briefed to dissent | **Missing** | Single human account; plans were reviewed by the author and the assistant only. The register's PD entries are the nearest thing to dissent on record |
| Decisions numbered with rationale; deviations recorded as such | **Met** | D-01..D-10, PD-01..PD-40 with problem, options, decision, pros and cons, status |

## 4. Score summary

| Area | Met | Partial | Missing |
|------|-----|---------|---------|
| Guardrails (10 incl. content security) | 0 | 9 | 1 |
| Acceptance conditions (8) | 1 | 5 | 2 |
| Working rules (7) | 2 | 2 | 3 |

Reading: the **mechanisms** the brief asks for are largely present and have been observed failing on demand; what is missing is the **independent corroboration and packaging** the definition of done is built around (bundle, reconciliation, digests, mirrors, scoreboard from evidence), the production side of isolation, an EU-resident external provider, and the owner's process hygiene (tickets, independent review, recorded cost approvals).

## 5. Ranked gaps, by weight in the brief and cost to close

| Rank | Gap | Guardrail / condition | Why first | Rough effort |
|------|-----|-----------------------|-----------|--------------|
| 1 | External tier on a US endpoint under exception | G2, G8 (both Highest/High) | Contradicts the two "Highest" guardrails; the exception is a demo convenience, not an argument the client's PO can accept | Small: register Bedrock or Vertex EU endpoint, revoke the exception. Needs an AWS/GCP account (owner) |
| 2 | Evidence reconciliation and completeness | G6, DoD | The DoD's central idea; our chain proves integrity but not completeness | Medium: GitHub audit-log export + Actions run metadata matched to merge/deploy events; gateway OIDC verifier; "missing record fails the run" |
| 3 | Configuration digests on every run | DoD | Cheap and demonstrable; makes drift visible | Small: hash policy bundle, allowlists, workflow files, image digests at run start; store in an event; show on the scoreboard |
| 4 | Scoreboard from the evidence store, with record links | DoD | Turns the report into evidence rather than a log summary | Small–medium: render from `audit_event` + verification rows; link to `/agl/events/<id>` |
| 5 | Production environment and the isolation probe | G1 | Highest guardrail, currently untestable | Medium: parcel production stack on `prod-net`; `server-release` runner; F-14 probes as a scheduled job with recorded failures |
| 6 | Aggregate-statistics export path | G1 | Named explicitly in the brief, absent in the design | Medium: an approved, reviewed export job producing k-anonymised aggregates into a catalog entry; DPO sign-off; negative test (row-level export refused) |
| 7 | Connection bundle and cold start from a second machine | DoD | The first thing the PO will try | Medium: one encrypted archive (settings, CA, token request, enrolment script) with a passphrase; a second enrolled machine in the test |
| 8 | Private mirrors | DoD, G3 | Supply-chain and offline repeatability | Medium: registry mirror and package mirrors on SERVER; sandbox and CI pointed at them |
| 9 | Task set and canaries from a prompt | DoD | The demo the brief describes | Small–medium: three defined tasks over the sample repository; `/canary` command in the chat and CLI that runs the suite through the gateway and links the evidence |
| 10 | SCA active, SBOM, content scanning with negative test | G4, CS | Straightforward once dependencies exist | Small: enable Trivy and the allowlist on `parcel-app`; ClamAV or equivalent on uploads/artefacts with an EICAR negative test |
| 11 | Per-run and per-developer-month quotas; infra spend alert | G7 | Schema supports it | Small: identity envelopes populated; per-session cap in the sandbox token; a SERVER resource alert |
| 12 | Working rules: tickets, independent dissenting review, recorded cost approvals, secret handling by owner | Owner's rules | Not technical, but the PO will ask | Process: GitHub Issues as the ticket system with the PR template requiring an issue; a second reviewer account or an external reviewer for plans; an approval record template with expected cost; rotate the secrets the assistant generated |
| 13 | Desktop-app bypass | G3 | Policy-only control today | Procedural until the vendor offers routing; keep in the AUP and the vendor assessment |

## 6. What already positions well

- Immutable, metadata-only evidence with on-demand tamper detection and Object Lock refusals, observed live (G6 first half).
- One controlled path with DLP block and redaction, verified with the real developer tool, and a chat that explains every verdict (G3 first half).
- Repository quarantine as data with dual sign-off and automatic re-closing (G1, G5).
- Hard budgets with dual-controlled top-ups, visible to the developer (G7 core).
- Registry that cannot hold an approved non-EU endpoint, and a self-hosted tier for CONFIDENTIAL (G2 core).
- A problem-and-decision register that already reads like the dissent the brief asks for (working rule 5), including an entry against the build process itself (PD-38).

## 7. Recommendation

Take gaps 1–4 first: they change what the demo proves without new infrastructure. Then 5–7, which make the replica look like what the client will receive. Items 9–11 fit around them. Item 12 starts now, because it is cheapest when adopted before the next change rather than retrofitted: open an issue per gap in this list, reference it from each PR, and record each go-live approval with the expected cost in the register.
