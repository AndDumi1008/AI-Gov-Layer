# AI Governance Layer (AGL) — Documentation set

**Purpose:** define how an ISO/IEC 27001-certified company can adopt AI (coding assistants, LLM APIs, agentic tools) with EU data sovereignty, immutable audit records, budget control, governed code merge and deployment, and a hard guarantee that AI never touches production systems or production data.

**Status:** Draft v0.1, options exploration (2026-10-19). More details from the business will refine these; see open questions in the PRD.

## Documents

| # | Document | What it answers |
|---|----------|-----------------|
| 01 | [Product Requirements](01-product-requirements.md) | Why, for whom, what must be true, options at a glance, open questions |
| 02 | [Technical Requirements](02-technical-requirements.md) | Architecture, component requirements, options analysis, SDLC and deploy rules, isolation, ISO 27001 Annex A mapping, threat model |
| 03 | [App Flows](03-app-flows.md) | Step-by-step flows F-01..F-15: requests, sandboxes, budgets, DLP, PRs, deploys, onboarding, exceptions, audit, GDPR, incidents |
| 04 | [Design Brief](04-design-brief.md) | Admin console IA, in-tool messages, PR surface, notifications, accessibility |
| 05 | [Backend Schema](05-backend-schema.md) | Three-store layout, PostgreSQL DDL, audit event envelope, append-only enforcement, retention |
| 06 | [Implementation Plan](06-implementation-plan.md) | Phases 0–5, deliverables, acceptance, RACI, risks, cost envelope, definition of done |
| 07 | [PoC Requirements](07-poc-requirements.md) | Prerequisites, functional requirements P-01..P-17, demo scenarios S1..S18, stand-ins, deliverables |
| 08 | [Delivery Pipeline](08-delivery-pipeline.md) | Local AI-assisted code → PR gates on the merge commit → signed merge candidate with preview → human review → human release approval → GitOps. Example files in [`pipeline/`](../pipeline/) |
| 10 | [AI Acceptable Use Policy](10-ai-acceptable-use-policy.md) | Draft ISMS policy: permitted and forbidden use, roles, exceptions; includes the desktop-app line from PD-38 |
| 09 | [Problem & Decision Register](09-problem-decision-register.md) | Every problem found and decision taken: problem, fixes considered, thought process, decision, pros and cons, status |
| — | [Decision Log](decision-log.md) | D-01..D-10 with context and consequences |
| — | [Glossary](glossary.md) | Terms |
| demo | [Code to Production Journey](demo/code-to-production.html) | Interactive walkthrough: twelve steps with detours (CI failure, changes requested, rollback, hotfix, incident), AI does/cannot per step, enforcement table, command simulator. Published at https://claude.ai/artifact/T4uHMFfa9N6Za9aCXUDjzC |
| demo | [Parcel Data Journey](demo/parcel-data-journey.html) | Interactive walkthrough: one parcel end to end, PII per role and per AI call, hash-chained ledger with tamper test. Published at https://claude.ai/artifact/23GD8uvnVNNwdzkkcqc83L |

## The model in one paragraph

Every AI call goes through one EU-hosted gateway that knows the caller (SSO), the team, the approved models (registry with region and contract references), the data classification, what must not be sent (DLP), and how much may be spent (ledger with hard caps). Each call is written once to a hash-chained, WORM-protected audit store that holds no prompt text. AI may suggest code, but humans commit, humans review, humans approve production deploys, and only a GitOps controller writes to production, admitting only signed, provenance-attested artifacts. AI identities have no production permissions and no network path to production, and that is tested every quarter.

## Contributing under Gate 1

Changes reach `main` only through a pull request that passes the seven checks in `.github/workflows/ci.yml`; AI-assisted commits carry a `Co-Authored-By`/`AI-Assisted` trailer, get the `ai-assisted` label automatically and need the checklist in the PR template ticked. See docs/08 §5.1.

## Run the PoC (Tier 1)

```
make bootstrap    # stack/ with the mock model; .env from .env.example
make demo         # 28 scenario checks → evidence/
make test         # policy + gateway unit tests
```

Stack layout and seeded identities: [stack/README.md](../stack/README.md). Pipeline examples: [pipeline/](../pipeline/). SERVER deployment kit: [deploy/server/](../deploy/server/).

## How to read

- Start with the PRD §11 options overview and the Decision Log.
- Engineers: TRD §2 (components), §5–7 (SDLC, deploy, sandboxes), then the schema.
- Security / ISMS: TRD §11–12 (sovereignty, Annex A mapping), App Flows F-08..F-14.
- Management: PRD §3 goals, Implementation Plan §1 and §12.

## Conventions

- Requirement IDs: `FR-xx`, `NFR-xx` (PRD), `T-<comp>-xx`, `SDLC-xx`, `DEP-xx` (TRD), flows `F-xx`, decisions `D-xx`.
- Diagrams are Mermaid; render in any Mermaid-capable viewer.
- Dates are ISO 8601; money is EUR.
