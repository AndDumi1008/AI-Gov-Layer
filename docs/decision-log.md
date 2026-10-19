# Decision Log

Architecture and governance decisions for the AI Governance Layer. Format follows a light ADR: context, decision, consequences, status. Decisions are referenced from the other documents as `D-xx`.

| ID | Title | Status | Date |
|----|-------|--------|------|
| D-01 | One gateway as the sole enforcement point | Proposed | 2026-10-19 |
| D-02 | Residency is judged per vendor contract and processing location, not nationality; default US endpoints excluded | Proposed | 2026-10-19 |
| D-03 | Self-hosted OSS gateway preferred over managed gateway SaaS | Proposed | 2026-10-19 |
| D-04 | Immutability via Object Lock + hash chain + external anchor + RFC 3161 | Proposed | 2026-10-19 |
| D-05 | Fail closed everywhere | Proposed | 2026-10-19 |
| D-06 | Gateway implementation chosen by Phase 1 spike; policy and ledger kept external | Proposed | 2026-10-19 |
| D-07 | Block/redact reasons returned in-band to the developer | Proposed | 2026-10-19 |
| D-08 | AI is an untrusted contributor: humans commit, humans approve, humans deploy | Proposed | 2026-10-19 |
| D-09 | Audit store holds no prompt content; content store is separate and erasable | Proposed | 2026-10-19 |
| D-10 | Unlabelled repositories default to CONFIDENTIAL | Proposed | 2026-10-19 |

---

## D-01 — One gateway as the sole enforcement point

**Context.** Controls spread across vendor consoles cannot give a unified log, budget or policy. ISO 27001 A.5.14 and A.8.12 want a defined channel.
**Decision.** All LLM traffic from company devices and non-prod workloads goes through the AGL gateway; other AI endpoints are blocked at egress. Tools that cannot use a custom endpoint are treated as SaaS-embedded AI with their own assessment.
**Consequences.** Gateway becomes critical infrastructure (HA, EU, fail closed). Some tools may need replacement. Clear single place for auditors.

## D-02 — Residency judged per contract and processing location

**Context.** Several frontier models are offered in EU regions by US-parented hyperscalers and also directly by US vendors. EU-native providers exist with competitive coding models. Legal exposure (e.g. extraterritorial access laws) is a Transfer Impact Assessment matter, not a blanket rule.
**Decision.** A model endpoint is eligible only if (a) processing and storage are contractually pinned to EU/EEA regions, (b) an Art. 28 DPA with EU processing terms exists, (c) training on our data is excluded and retention terms are known, (d) a TIA documents any residual non-EU access with supplementary measures. Default US endpoints without these guarantees are excluded. Vendors are re-evaluated individually.
**Consequences.** Two-provider strategy (hyperscaler EU + EU-native). Registry carries contract references and review dates. Legal workload per vendor.

## D-03 — Self-hosted OSS gateway preferred

**Context.** Managed gateway SaaS products are quick but add another processor whose log location and sub-processors must be assessed; some are not EU-resident.
**Decision.** Run an OSS gateway on EU infrastructure under our control. Reconsider only if operations prove too costly.
**Consequences.** Platform team owns a service; we keep full control of logs and keys.

## D-04 — Immutability mechanism

**Context.** Auditors need tamper-evident and tamper-resistant records; GDPR needs erasability of personal content; blockchain is overkill.
**Decision.** Events are hash-chained (RFC 8785 canonical JSON, SHA-256), written in segments to object storage with Object Lock in compliance mode in an EU region, with a daily root hash anchored to a second independent store and timestamped via RFC 3161. A Postgres hot copy is append-only but is not the source of truth.
**Consequences.** Cheap, standard, verifiable. Retention is fixed at write time; legal must set it. Content is kept out of this store (D-09).

## D-05 — Fail closed

**Context.** If policy, budget or audit components are down, allowing traffic would create unlogged, unmetered, unpoliced requests.
**Decision.** The gateway rejects requests when any governance dependency is unavailable, for all classifications.
**Consequences.** HA and alerting are mandatory; developers see a clear "governance unavailable" message; status page needed.

## D-06 — Gateway chosen by spike; policy and ledger external

**Context.** Several OSS gateways are viable; the landscape moves fast.
**Decision.** Two-week spike in Phase 1 against TRD T-GW-01..10. Regardless of choice, policy lives in OPA/Rego bundles and budgets in the AGL ledger, so the gateway is replaceable (NFR-09).
**Consequences.** Slight duplication (gateways have built-in budgets we will not rely on); long-term portability.

## D-07 — In-band explanations

**Context.** Silent blocks drive developers to bypass controls.
**Decision.** Every block/redact returns a reason code, one-line explanation, remediation and event id in the API response; the console can expand it.
**Consequences.** Message catalogue maintained with the policy bundle; messages never include matched sensitive values.

## D-08 — AI is an untrusted contributor

**Context.** ISO 27001 A.8.30 (outsourced development) and A.8.32 (change management) already model external contributors.
**Decision.** AI may propose code; only humans commit (signed), only humans distinct from the author approve, only humans approve production deployment, and only the GitOps controller writes to production using signed, provenance-attested artifacts. AI identities have no production IAM and no network path.
**Consequences.** Some friction for small changes; strong auditability; aligns with existing ISMS language.

## D-09 — No prompt content in the audit store

**Context.** Immutable storage and GDPR erasure conflict if personal data is in the immutable record.
**Decision.** Audit events carry hashes of prompt/response and DLP finding types/counts only. Full content goes, when policy allows, to a separate encrypted store with short retention and erasure.
**Consequences.** Investigations may lack content for high classifications by design; this is accepted.

## D-10 — Default classification CONFIDENTIAL

**Context.** Unlabelled repositories are the norm at start.
**Decision.** Until a repository carries a classification manifest, treat it as CONFIDENTIAL (EU zero-retention/self-hosted models only, content logging off).
**Consequences.** Incentive for teams to classify; initial restriction of model choice for unlabelled repos.
