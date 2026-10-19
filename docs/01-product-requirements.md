# 01 — Product Requirements Document (PRD)

**Project:** AI Governance Layer (AGL)
**Status:** Draft v0.1 — options exploration
**Date:** 2026-10-19
**Owner:** TBD (CISO / Head of Engineering)
**Related:** [02 Technical Requirements](02-technical-requirements.md) · [03 App Flows](03-app-flows.md) · [04 Design Brief](04-design-brief.md) · [05 Backend Schema](05-backend-schema.md) · [06 Implementation Plan](06-implementation-plan.md) · [Decision Log](decision-log.md)

---

## 1. Problem statement

The company is ISO/IEC 27001 certified and wants to use AI (coding assistants, LLM APIs, agentic tools) across engineering and adjacent teams without:

- breaking the Information Security Management System (ISMS) or putting the certificate at risk,
- moving personal or confidential data outside EU jurisdiction or outside controlled processors,
- losing the ability to prove *who asked what, when, with which model, at what cost*,
- letting spend run uncontrolled,
- letting AI-produced changes reach production without the same (or stronger) controls as human changes,
- letting any AI tool, agent or vendor touch production systems or production data.

Today there is no single enforcement point. Developers can install any assistant, paste any snippet, and bill any card. This PRD defines a product-shaped answer: a governance layer that sits between people/tools and models, plus a set of SDLC rules that sit between AI output and production.

## 2. Vision

> Every AI interaction in the company goes through one controlled door. The door knows who you are, which model you may use, how much you may spend, what you may not send, and writes an unalterable record of what happened. Nothing on the other side of the door can reach production.

## 3. Goals

| # | Goal | Measure of success |
|---|------|--------------------|
| G1 | Single enforcement point for all LLM traffic | ≥ 95 % of AI calls (by token volume) routed via the gateway within 6 months of go-live; direct vendor keys revoked |
| G2 | EU data sovereignty | 100 % of approved models hosted in EU regions by EU-established or contractually bound processors; DPIA + Art. 28 DPA on file per vendor |
| G3 | Immutable audit trail | Every request/response metadata record written once to WORM storage, hash-chained, retention ≥ legal requirement; zero successful tamper in audit tests |
| G4 | Budget control | Hard caps per team/project enforced in real time; no month closes > 100 % of approved envelope without a logged exception |
| G5 | Controlled merge and deploy | 100 % of PRs with AI-assisted changes carry the `ai-assisted` marker; 0 merges without an independent human approval; 0 deploys triggered by a non-human identity |
| G6 | Production isolation | 0 AI identities with any production IAM role; 0 network paths from AI tooling to production VPCs; dev/test datasets 100 % synthetic or masked |
| G7 | ISO 27001 alignment | Controls mapped to Annex A (2022); internal audit finds no major nonconformity in the AI scope |

## 4. Non-goals (v1)

- Building or fine-tuning our own foundation models.
- Governing AI features *inside our products* for customers (that is a product-level DPIA and a separate stream; the gateway may later serve it).
- Replacing existing SIEM, IAM, or CI/CD platforms. AGL integrates with them.
- Blocking all US-headquartered vendors on principle. The criterion is *where data is processed and under which contract*, not the vendor's passport (see Decision D-02).
- Training-data licensing or copyright indemnity analysis beyond requiring vendor indemnification clauses in procurement.

## 5. Stakeholders and personas

| Persona | Needs | Pain today |
|---------|-------|------------|
| **Developer (Dana)** | Fast assistant in IDE/CLI; clear rules; no surprise blocks | Unsure what is allowed; fear of pasting the wrong thing |
| **Tech Lead (Teo)** | See team spend; approve exceptions; trust that AI PRs are reviewed | No visibility; cannot tell AI code from human code |
| **CISO / ISMS owner (Ines)** | Evidence for auditors; control over vendors and data flows; incident traceability | Shadow AI; no logs; vendor sprawl |
| **DPO (Pawel)** | Lawful basis, transfer mechanism, retention, DSAR capability | Cannot answer "did personal data go to a model?" |
| **FinOps / Finance (Mira)** | Predictable spend; cost allocation to cost centres | Dozens of credit-card subscriptions |
| **Platform / SRE (Sven)** | Guarantee prod isolation; operate the gateway with low toil | Fear that an agent will run `kubectl` against prod |
| **Internal auditor (Ola)** | Sample evidence quickly; verify immutability | Nothing to sample |
| **Procurement / Legal (Lena)** | Standard vendor assessment; DPA, SCCs, exit terms | Ad-hoc vendor onboarding |

## 6. Scope of "AI" covered

| Category | Examples | In scope v1 |
|----------|----------|-------------|
| IDE / CLI coding assistants | Copilot-style completions, chat, agentic CLIs (e.g. Claude Code, Codex CLI, Cursor agent mode) | Yes |
| Direct LLM API use by internal tools | scripts, internal bots, RAG over internal docs | Yes |
| SaaS products with embedded AI | ticketing, docs, CRM "AI summarise" features | Partially: inventory + vendor assessment; traffic cannot be proxied |
| Autonomous agents acting on infrastructure | agents with cloud/K8s/DB credentials | Yes — **prohibited** in production; sandboxed in dev |
| Model training / fine-tuning | — | No (non-goal) |
| Browser chat UIs (consumer ChatGPT, Gemini, etc.) | — | Yes — **blocked** at network/DLP level unless through gateway-brokered enterprise tier |

## 7. User stories

### 7.1 Developer

- **US-01** As a developer I can use an approved coding assistant from my IDE with company SSO, without managing API keys.
- **US-02** As a developer I see which models are approved for which data classification, and the tool refuses or warns before I send something classified higher than allowed.
- **US-03** As a developer I am told clearly when a request is blocked (secret detected, PII detected, budget exhausted) and what to do about it.
- **US-04** As a developer I can mark a PR as AI-assisted in one click (or it is detected automatically), and the review requirements are shown in the PR.

### 7.2 Tech lead / budget owner

- **US-10** As a tech lead I see my team's spend in near real time, by person, tool and model, against the envelope.
- **US-11** As a tech lead I receive alerts at 50/80/100 % of envelope and can request a top-up with justification.
- **US-12** As a tech lead I can approve a time-boxed exception (e.g. a higher-cost model for an incident) which is logged.

### 7.3 Security / compliance

- **US-20** As CISO I can produce, for any date range, an immutable list of every AI request: identity, team, model, provider, region, token counts, classification outcome, policy decisions.
- **US-21** As CISO I can prove that no AI identity holds production credentials and that no network route exists from AI tooling to production.
- **US-22** As DPO I can query whether personal data was detected in prompts and what was done (redacted/blocked), and fulfil a DSAR or erasure request against the *content* store while the *audit* store stays immutable.
- **US-23** As an auditor I can verify the hash chain of the audit log for a sample period and confirm WORM retention settings.
- **US-24** As CISO I can onboard or decommission a model/provider through a defined workflow with a vendor assessment, DPA, region check and risk acceptance.

### 7.4 Platform / SRE

- **US-30** As SRE I deploy the gateway as a highly available service in an EU region with no single vendor lock-in for the policy engine.
- **US-31** As SRE I can see that every production deployment originated from a signed artifact built by CI from a merged PR with human approval.
- **US-32** As SRE I can run agentic AI tools in an ephemeral, network-isolated sandbox that has synthetic data and no production secrets.

## 8. Functional requirements

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-01 | All LLM traffic from company devices and workloads is routed through the AI Gateway; direct vendor endpoints are blocked at egress (proxy/DNS/firewall) | Must |
| FR-02 | Gateway authenticates callers via corporate IdP (OIDC) for humans and workload identity for services; no shared static keys | Must |
| FR-03 | Model registry: allowlist of (provider, model, region, data-classification ceiling, cost tier, status) | Must |
| FR-04 | Policy engine evaluates every request: identity → team → allowed models → classification → DLP → budget → route | Must |
| FR-05 | DLP: detect secrets, credentials, personal data, customer identifiers, and configured keywords in prompts; actions: allow / redact / block, per classification | Must |
| FR-06 | Budget ledger: per org / team / project / identity envelopes, hard and soft limits, real-time decrement, alerts, exception workflow | Must |
| FR-07 | Immutable audit log: one record per request and per policy decision, written to append-only storage with hash chain and WORM retention | Must |
| FR-08 | Content store (prompt/response bodies) separate from audit store; encrypted; configurable retention; erasable for GDPR; disabled by default for high classifications | Must |
| FR-09 | SDLC controls: PR labelling of AI-assisted changes, mandatory independent human review, signed commits, CI gates (SAST, secrets, dependencies, licenses, tests), policy-as-code | Must |
| FR-10 | Deploy controls: production deploys only from signed, provenance-attested artifacts, via GitOps, with human approval in a protected environment; no AI identity may trigger or approve | Must |
| FR-11 | Production isolation: AI identities denied all production IAM; AI tooling networks have no route to production; prod data never copied to AI-reachable environments without masking | Must |
| FR-12 | Admin console: dashboards for spend, usage, policy decisions, audit search, model registry, exception management | Should |
| FR-13 | Developer feedback: human-readable block/redact reasons returned in-band to the tool | Should |
| FR-14 | Vendor lifecycle: onboarding checklist (DPIA, DPA/SCC, region, retention, sub-processors, exit), periodic review, offboarding | Must |
| FR-15 | Break-glass: time-boxed, dual-approved, fully logged exceptions (e.g. temporarily enable a model) | Should |
| FR-16 | Inventory of SaaS-embedded AI features with vendor assessment status | Should |
| FR-17 | Export of audit evidence (CSV/JSON + chain verification report) for auditors | Must |

## 9. Non-functional requirements

| ID | Requirement |
|----|-------------|
| NFR-01 | **Residency:** gateway, policy engine, logs, content store, dashboards all deployed in EU regions; backups in EU |
| NFR-02 | **Availability:** gateway ≥ 99.9 % monthly; degraded mode = fail closed for high classifications, fail open to *cached allowlist* for low classifications is **not** permitted (decision D-05: fail closed everywhere) |
| NFR-03 | **Latency overhead:** p95 added by gateway ≤ 150 ms excluding model time |
| NFR-04 | **Scalability:** 500 concurrent developers, 50 M tokens/day initial, 10× headroom |
| NFR-05 | **Integrity:** audit records SHA-256 hash-chained; daily anchor published to a second independent store; WORM retention ≥ 24 months (configurable per legal advice) |
| NFR-06 | **Confidentiality:** TLS 1.2+ in transit, AES-256 at rest, customer-managed keys in EU KMS; content store keys separable from audit store keys |
| NFR-07 | **Access control:** RBAC with least privilege; admin actions themselves logged to the immutable store |
| NFR-08 | **Observability:** metrics, traces, structured logs to the existing SIEM; alerting on policy-engine errors, provider errors, budget thresholds |
| NFR-09 | **Portability:** policy expressed in a vendor-neutral language (e.g. Rego/OPA or Cedar); gateway replaceable without rewriting policy |
| NFR-10 | **Auditability:** every configuration change version-controlled and reviewed (policy-as-code in Git) |

## 10. Regulatory and standards context

| Framework | Relevance | How AGL responds |
|-----------|-----------|------------------|
| **ISO/IEC 27001:2022** (Annex A) | Existing certificate; AI must fit the ISMS | Control mapping in TRD §12; AGL becomes an asset and a set of controls in the Statement of Applicability |
| **ISO/IEC 42001:2023** (AI management system) | Optional future certification; good structure for AI policy, roles, impact assessment | Adopt its clause structure for the AI policy; do not certify in v1 |
| **GDPR** | Personal data in prompts; processors; international transfers | DLP, DPIA per use case, Art. 28 DPAs, EU processing, transfer impact assessment where any non-EU access is possible |
| **EU AI Act** (Reg. 2024/1689) | Most internal coding use = minimal risk; GPAI transparency obligations fall on providers; Art. 4 AI literacy obligation applies to deployers | Training programme (Art. 4), inventory of use cases with risk classification, vendor obligations in contracts |
| **NIS2** (if in scope) | Supply-chain security, incident reporting | Vendor assessments, logging, incident flow |
| **DORA** (if financial sector) | ICT third-party risk | Register of information for AI providers |
| **Data Act / Data Governance Act** | Cloud switching, data portability | Exit clauses, export formats |

Legal review required: confirm which of NIS2/DORA apply; confirm retention periods; confirm transfer mechanism status for each vendor at contract time (adequacy decisions and frameworks change — do not hardcode assumptions).

## 11. Options overview (summary; detail in TRD §4)

### 11.1 Where models run

| Option | Residency | Model quality | Cost | Ops burden | Lock-in | Verdict |
|--------|-----------|---------------|------|------------|---------|---------|
| A. EU-region hyperscaler managed models (Azure OpenAI EU, AWS Bedrock EU, Google Vertex EU) | EU region; US parent; need contractual guarantees on support access and no cross-region processing | High | Medium | Low | Medium | **Primary** for frontier models, subject to TIA |
| B. EU-native provider APIs (e.g. Mistral, Aleph Alpha) | EU-established | Good–high | Medium | Low | Low–medium | **Primary/secondary**; strong sovereignty story |
| C. Self-hosted open-weight models on EU IaaS / on-prem (vLLM, TGI) | Full control | Medium–good | High fixed, low marginal | High | Low | **Secondary**; for high-classification data and for independence |
| D. Direct US vendor APIs (default endpoints) | Not guaranteed EU | High | Medium | Low | Medium | **Excluded** unless vendor offers contractual EU-only processing + zero retention; re-evaluate per vendor |
| E. Consumer / unmanaged tools | None | — | Hidden | — | — | **Blocked** |

### 11.2 Enforcement point

| Option | Notes | Verdict |
|--------|-------|---------|
| Self-hosted open-source AI gateway (LiteLLM, Envoy AI Gateway, Kong AI Gateway OSS) + OPA | Full residency, full control, moderate ops | **Recommended** |
| Managed gateway SaaS (Portkey, Cloudflare AI Gateway, vendor-native gateways) | Fast; residency and log location must be verified; another processor | Fallback / not preferred |
| Per-vendor enterprise consoles only (e.g. Copilot Enterprise policies) | No cross-vendor view, no unified budget/log | Insufficient alone |

### 11.3 Immutability mechanism

| Option | Notes |
|--------|-------|
| Object storage with Object Lock / immutable blob (compliance mode), EU region, + SHA-256 hash chain + daily anchor | **Recommended**; cheap, auditable, standard |
| Append-only database with revoked UPDATE/DELETE + periodic export to WORM | Good for query; use as *hot* index, not as source of truth |
| Blockchain / public anchoring | Over-engineering for v1; a daily anchor to a second provider gives equivalent assurance for auditors |

## 12. Success metrics (12 months)

- Shadow AI: direct vendor domains blocked; < 1 % of AI traffic bypassing gateway (measured at egress).
- 100 % of AI-related vendor contracts with DPA + EU processing clause.
- Audit: hash-chain verification passes on 100 % of sampled days.
- Budget: ≤ 2 budget overrun exceptions per quarter, all logged.
- SDLC: 0 production incidents attributed to unreviewed AI code.
- Isolation: quarterly automated test proves 0 prod reachability from AI sandboxes.
- Developer satisfaction ≥ 4/5 on "the AI tooling is usable and the rules are clear".

## 13. Assumptions

- Corporate IdP (Entra ID / Okta / Keycloak) exists and supports OIDC and SCIM groups.
- Source control is GitHub Enterprise or GitLab with branch protection and environments.
- Cloud footprint has separate accounts/subscriptions/projects per environment (prod vs non-prod). If not, that becomes a prerequisite (Implementation Plan Phase 0).
- A SIEM exists for log ingestion.
- Legal/DPO capacity exists to run DPIAs and vendor assessments.

## 14. Open questions

| # | Question | Owner | Needed by |
|---|----------|-------|-----------|
| Q1 | Which sector regulations apply (NIS2, DORA, sector-specific)? | Legal | Phase 0 |
| Q2 | Required retention for audit records (24 vs 60+ months)? | Legal/DPO | Phase 0 |
| Q3 | Is a self-hosted model tier required in v1 for high-classification data, or is it enough to block such data from AI entirely? | CISO | Phase 1 |
| Q4 | Budget granularity: per team only, or per person as well? | Finance/Eng | Phase 1 |
| Q5 | GitHub or GitLab (affects CI gate implementation)? | Eng | Phase 0 |
| Q6 | Do we allow any agentic tool with write access to dev clusters, or read-only + PR-only? | Platform/CISO | Phase 2 |
| Q7 | Do we need DSAR capability over prompt *content*, or do we avoid storing content for most classes? | DPO | Phase 1 |
