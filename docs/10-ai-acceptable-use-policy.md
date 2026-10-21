# 10 — AI Acceptable Use Policy (draft for the ISMS)

**Status:** Draft v0.2 for CISO and DPO review · 2026-10-21 (owner decisions: personal data blocked, prompts stored, client questions; PD-49 to PD-51)
**Applies to:** every employee, contractor and system that sends data to, or acts on output from, an AI model on behalf of the company.
**Structure:** follows ISO/IEC 42001 clause headings so it can later become the AI policy of an AI management system. Control references are to ISO/IEC 27001:2022 Annex A (see docs/02 §12).

---

## 1. Purpose and scope

AI tools are allowed and encouraged for software development and internal work, under the controls of the AI Governance Layer (AGL). This policy says what is permitted, what is forbidden, and who decides exceptions. It covers coding assistants, chat tools, API use by internal software, agentic tools, and AI features embedded in third-party software. Engineers use AI for coding; client accounts may ask product questions about what the platform does (§3).

## 2. Principles

1. **One door.** Every model call from a company device or workload goes through the AGL gateway. Tools that cannot use it are treated as third-party AI features and need a vendor assessment before use (A.5.19, A.5.23).
2. **Data stays in the EU.** Only registry-approved, EU-resident endpoints are reachable. CONFIDENTIAL material is processed on self-hosted models only. RESTRICTED material is never sent to any model. Source code counts as data under this rule: repositories and the CI runners that build them must be EU-resident too (PD-09, PD-16) (A.5.12, A.5.14).
3. **The record is immutable.** Every request and decision is logged to an append-only, hash-chained store without prompt text. Nobody can edit or delete it (A.5.33, A.8.15).
4. **Prompts are kept, for a limited time.** The prompt and answer of every request that reaches a model, and every command an AI agent asks to run with its output, are kept in a separate encrypted store for 30 days, then removed automatically. Reading one takes two people: security or the DPO asks, stating why, and a different person approves; each step is itself recorded. The DPO can erase them earlier, per person or per request. This policy is the prior notice to staff that this is collected; the DPO documents the legal basis (A.5.34, A.8.10, A.8.15).
5. **No governance, no tool.** If the gateway, the policy engine, the audit store or the prompt store is unavailable, AI requests stop; nothing falls back to an unrecorded path (D-05).
6. **AI is an untrusted contributor.** AI may propose code and text; only humans commit, review, approve and release. AI identities hold no production credentials and have no network route to production (A.8.30, A.8.31, A.8.32).
7. **Two people where it matters.** Model approval, repository exposure, budget top-ups and exceptions require two distinct approvers.

## 3. Permitted use

- Writing, explaining, reviewing and testing code in repositories whose AI exposure is `allowed`, through the gateway.
- Drafting documents, summaries and messages with INTERNAL information.
- Agentic tools inside the sandbox, with the delegated identity the sandbox issues, on synthetic or masked data.
- Terminal `claude` and other CLIs configured by the managed settings, which point them at the gateway.
- Client accounts: product questions ("is this feature active?", "can we already do this?") in the chat or with `agl product-ask`. Answers come from the reviewed feature catalog, never from code or production; clients cannot send free prompts, code or repository context (PD-51).

## 4. Forbidden use

- Sending RESTRICTED data (production data, secrets, keys, special-category personal data) to any model, by any route.
- Using a personal or consumer AI account for company work, or an AI tool that bypasses the gateway. **This includes AI desktop applications that keep their own login and send requests directly to the vendor; today the Claude desktop app is one of them (register PD-35, PD-38).** Such applications may be used only on synthetic material until they can be routed through the gateway or are assessed and approved as a third-party AI feature.
- Running an AI agent in a shell that holds production credentials, cloud sessions or SSH keys to production or build hosts (PD-07).
- Pasting credentials or personal data of customers or colleagues into a prompt. The gateway blocks the request before anything is sent (only your own registered address and addresses on reserved test domains such as example.com or *.test are allowed); the attempt is logged as a type and count, and repeated attempts are followed up. Use placeholders or test data instead (PD-49).
- Committing, approving or releasing on behalf of an AI, or letting an AI identity do so.
- Disabling, bypassing or weakening a gateway control, a CI check, a branch rule or an audit mechanism.

## 5. Roles

| Role | Responsibility |
|------|----------------|
| Every user | Complete AI literacy training before first use (EU AI Act Art. 4); follow this policy; report suspected leaks. |
| Team lead | Request budget top-ups; sign off repository exposure as owner; ensure PR reviews are real. |
| Security admin | Model registry and policy changes (dual approval); gate items; incident handling; asks to read a stored prompt only for an investigation, stating the reason; approves others' requests. |
| DPO | Data protection assessments; approve model exposure of personal data; erasure of stored prompts (per person or per request); asks to read or approves reading stored prompts for access requests. |
| Client account | Product questions only, through the chat or `agl product-ask`. |
| Budget owner / finance | Approve top-ups (never own requests); monthly reconciliation. |
| Platform | Operate the gateway, sandboxes and pipelines; isolation tests. |

## 6. Exceptions

Exceptions are time-boxed (72 hours maximum), dual-approved, logged with an identifier that appears on every request made under them, and reviewed afterwards. No exception can enable processing outside the EU (PD-43); the one that allowed the US endpoint during evaluation is closed.

## 7. Monitoring and consequences

Use is metered and logged per identity. Prompts, answers and agent commands are kept for 30 days as described in §2 and are read only for investigations and access requests, never for performance assessment. The audit store is reviewed by sampling and on incidents. Blocked secrets create a security ticket. Breaches of section 4 are handled under the existing disciplinary and incident procedures; repeated DLP blocks trigger training refresh.

## 8. Review

Annually, on a change of vendor terms, on a new regulation, and after any incident involving AI. Owner: CISO. Register of decisions: docs/09.
