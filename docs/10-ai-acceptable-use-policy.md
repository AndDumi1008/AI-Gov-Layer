# 10 — AI Acceptable Use Policy (draft for the ISMS)

**Status:** Draft v0.1 for CISO and DPO review · 2026-10-20
**Applies to:** every employee, contractor and system that sends data to, or acts on output from, an AI model on behalf of the company.
**Structure:** follows ISO/IEC 42001 clause headings so it can later become the AI policy of an AI management system. Control references are to ISO/IEC 27001:2022 Annex A (see docs/02 §12).

---

## 1. Purpose and scope

AI tools are allowed and encouraged for software development and internal work, under the controls of the AI Governance Layer (AGL). This policy says what is permitted, what is forbidden, and who decides exceptions. It covers coding assistants, chat tools, API use by internal software, agentic tools, and AI features embedded in third-party software.

## 2. Principles

1. **One door.** Every model call from a company device or workload goes through the AGL gateway. Tools that cannot use it are treated as third-party AI features and need a vendor assessment before use (A.5.19, A.5.23).
2. **Data stays in the EU.** Only registry-approved, EU-resident endpoints are reachable. CONFIDENTIAL material is processed on self-hosted models only. RESTRICTED material is never sent to any model (A.5.12, A.5.14).
3. **The record is immutable.** Every request and decision is logged to an append-only, hash-chained store without prompt text. Nobody can edit or delete it (A.5.33, A.8.15).
4. **AI is an untrusted contributor.** AI may propose code and text; only humans commit, review, approve and release. AI identities hold no production credentials and have no network route to production (A.8.30, A.8.31, A.8.32).
5. **Two people where it matters.** Model approval, repository exposure, budget top-ups and exceptions require two distinct approvers.

## 3. Permitted use

- Writing, explaining, reviewing and testing code in repositories whose AI exposure is `allowed`, through the gateway.
- Drafting documents, summaries and messages with INTERNAL information.
- Agentic tools inside the sandbox, with the delegated identity the sandbox issues, on synthetic or masked data.
- Terminal `claude` and other CLIs configured by the managed settings, which point them at the gateway.

## 4. Forbidden use

- Sending RESTRICTED data (production data, secrets, keys, special-category personal data) to any model, by any route.
- Using a personal or consumer AI account for company work, or an AI tool that bypasses the gateway. **This includes AI desktop applications that keep their own login and send requests directly to the vendor; today the Claude desktop app is one of them (register PD-35, PD-38).** Such applications may be used only on synthetic material until they can be routed through the gateway or are assessed and approved as a third-party AI feature.
- Running an AI agent in a shell that holds production credentials, cloud sessions or SSH keys to production or build hosts (PD-07).
- Pasting credentials or personal data of customers or colleagues into a prompt. The gateway blocks and redacts, but the attempt is logged and repeated attempts are followed up.
- Committing, approving or releasing on behalf of an AI, or letting an AI identity do so.
- Disabling, bypassing or weakening a gateway control, a CI check, a branch rule or an audit mechanism.

## 5. Roles

| Role | Responsibility |
|------|----------------|
| Every user | Complete AI literacy training before first use (EU AI Act Art. 4); follow this policy; report suspected leaks. |
| Team lead | Request budget top-ups; sign off repository exposure as owner; ensure PR reviews are real. |
| Security admin | Model registry and policy changes (dual approval); gate items; incident handling. |
| DPO | Data protection assessments; approve model exposure of personal data; erasure requests. |
| Budget owner / finance | Approve top-ups (never own requests); monthly reconciliation. |
| Platform | Operate the gateway, sandboxes and pipelines; isolation tests. |

## 6. Exceptions

Exceptions are time-boxed (72 hours maximum), dual-approved, logged with an identifier that appears on every request made under them, and reviewed afterwards. No exception can enable processing outside the EU (PD-43); the one that allowed the US endpoint during evaluation is closed.

## 7. Monitoring and consequences

Use is metered and logged per identity. The audit store is reviewed by sampling and on incidents. Blocked secrets create a security ticket. Breaches of section 4 are handled under the existing disciplinary and incident procedures; repeated DLP blocks trigger training refresh.

## 8. Review

Annually, on a change of vendor terms, on a new regulation, and after any incident involving AI. Owner: CISO. Register of decisions: docs/09.
