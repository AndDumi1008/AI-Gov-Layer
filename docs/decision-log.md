# Decision Log

Architecture and governance decisions for the AI Governance Layer. Format follows a light ADR: context, decision, consequences, status. Decisions are referenced from the other documents as `D-xx`.

| ID | Title | Status | Date |
|----|-------|--------|------|
| D-01 | One gateway as the sole enforcement point | Proposed | 2026-10-19 |
| D-02 | Residency is judged per vendor contract and processing location, not nationality; default US endpoints excluded | Proposed | 2026-10-19 |
| D-03 | Self-hosted OSS gateway preferred over managed gateway SaaS | Proposed | 2026-10-19 |
| D-04 | Immutability via Object Lock + hash chain + external anchor + RFC 3161 | Proposed | 2026-10-19 |
| D-05 | Fail closed everywhere | **Accepted** (owner, 2026-10-21) | 2026-10-19 |
| D-06 | Gateway implementation chosen by Phase 1 spike; policy and ledger kept external | Proposed | 2026-10-19 |
| D-07 | Block reasons returned in-band to the developer | Proposed (amended 2026-10-21: nothing is redacted, D-11) | 2026-10-19 |
| D-08 | AI is an untrusted contributor: humans commit, humans approve, humans deploy | Proposed | 2026-10-19 |
| D-09 | Audit store holds no prompt content; content store is separate and erasable | **Accepted, amended** (owner, 2026-10-21: the content store is mandatory, D-12) | 2026-10-19 |
| D-10 | Unlabelled repositories default to CONFIDENTIAL | Proposed (amended 2026-10-21: content is stored for every class, D-12) | 2026-10-19 |
| D-11 | Personal data in prompts is blocked, not redacted; the caller's own address and reserved test domains are exempt and counted | **Accepted** (owner) | 2026-10-21 |
| D-12 | Every prompt and answer, and every agent command with its output, is stored: encrypted, 30 days, erasable | **Accepted** (owner) | 2026-10-21 |
| D-13 | Engineers use AI for coding; client accounts ask product questions, answered from a reviewed feature catalog | **Accepted** (owner) | 2026-10-21 |
| D-14 | Source code is data under the EU-only rule: Git hosting and CI runners must be EU-resident | **Accepted** (owner) | 2026-10-21 |

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
**Owner, 2026-10-21.** "No governance, no tool": accepted as written, with no low-risk bypass. Since D-12 the content store is one of those dependencies: a prompt that cannot be stored is not sent.
**Consequences.** HA and alerting are mandatory; developers see a clear "governance unavailable" message; status page needed. The PoC runs one gateway on one server, so production needs at least two instances before go-live.

## D-06 — Gateway chosen by spike; policy and ledger external

**Context.** Several OSS gateways are viable; the landscape moves fast.
**Decision.** Two-week spike in Phase 1 against TRD T-GW-01..10. Regardless of choice, policy lives in OPA/Rego bundles and budgets in the AGL ledger, so the gateway is replaceable (NFR-09).
**Consequences.** Slight duplication (gateways have built-in budgets we will not rely on); long-term portability.

## D-07 — In-band explanations

**Context.** Silent blocks drive developers to bypass controls.
**Decision.** Every block returns a reason code, one-line explanation, remediation and event id in the API response; the console can expand it. For DLP blocks it also returns the finding types and counts, never the values. (There is no redact outcome since D-11.)
**Consequences.** Message catalogue maintained with the policy bundle; messages never include matched sensitive values.

## D-08 — AI is an untrusted contributor

**Context.** ISO 27001 A.8.30 (outsourced development) and A.8.32 (change management) already model external contributors.
**Decision.** AI may propose code; only humans commit (signed), only humans distinct from the author approve, only humans approve production deployment, and only the GitOps controller writes to production using signed, provenance-attested artifacts. AI identities have no production IAM and no network path.
**Consequences.** Some friction for small changes; strong auditability; aligns with existing ISMS language.

## D-09 — No prompt content in the audit store

**Context.** Immutable storage and GDPR erasure conflict if personal data is in the immutable record.
**Decision.** Audit events carry hashes of prompt/response and DLP finding types/counts only. Full content goes, when policy allows, to a separate encrypted store with short retention and erasure.
**Owner, 2026-10-21.** Prompts and the resulting actions are to be stored. The separation stays (content never enters the immutable store, so erasure never touches the chain); what changes is that the content store is mandatory for every request that reaches a model, see D-12.
**Consequences.** ~~Investigations may lack content for high classifications by design.~~ Superseded by D-12: investigations have content for 30 days, for every classification.

## D-10 — Default classification CONFIDENTIAL

**Context.** Unlabelled repositories are the norm at start.
**Decision.** Until a repository carries a classification manifest, treat it as CONFIDENTIAL (EU zero-retention/self-hosted models only; content logging off until 2026-10-21, now stored like every class, D-12).
**Consequences.** Incentive for teams to classify; initial restriction of model choice for unlabelled repos.

## D-11 — Personal data is blocked, not redacted

**Context.** The PoC redacted personal data into placeholders and restored it in the answer. The owner was asked whether to block, mask or warn when someone sends personal data or secrets.
**Decision (owner, 2026-10-21).** Block. A prompt carrying somebody's email address, phone number or IBAN is refused before any model is called, like a secret. Two kinds of match are exempt and counted in the event, never silently: the caller's own registered address (developer tools such as Claude Code put it in their system prompt), and addresses on domains reserved for examples and tests (example.com/.net/.org, *.test, *.example, *.invalid, *.localhost).
**Consequences.** More friction than redaction; a false positive now stops work, so the false-positive path (F-05) matters more. Nothing is rewritten on the way to the model, so the model sees exactly what was audited and stored. If a tool's system prompt carries an address other than the identity's registered one, every call from it is blocked until the two match. Register PD-49.

## D-12 — Prompts, answers and agent actions are stored

**Context.** D-09 kept content out of the audit store and made a content store optional, off for CONFIDENTIAL. The owner was asked whether logging should keep the prompts or only who asked and what the AI did.
**Decision (owner, 2026-10-21).** Both: prompts and the resulting actions. Every request that reaches a model is stored with its answer, and every command an agent asks to run is stored with its output, for every classification, in the separate content store: AES-256-GCM with a per-team key, bound to its audit event, 30 days, then the bodies are removed and the row with its fingerprints stays. Reading takes two people (owner, 2026-10-21): security or the DPO asks with a reason, a different person (security, DPO or team lead) approves, and only the asker may then read, for 24 hours; request, approval and read are audit events. The DPO erases per person or per request. Blocked requests are not stored: they hold the very data that blocked them. A request whose content cannot be stored is not sent (D-05).
**Consequences.** Investigations and access requests have content. Storing every engineer's prompts is processing of employee data: the AUP (docs/10) is the prior notice, and the DPO confirms the legal basis and the retention; the owner accepted 30 days (2026-10-21); Romanian employee-monitoring rules (Law 190/2018 art. 5) cap such retention at 30 days, which this matches. Losing the content key makes stored bodies unreadable. Register PD-50.

## D-13 — Who uses it: engineers for coding, clients for product questions

**Context.** The owner was asked whether the tool is for engineers only or also for other people.
**Decision (owner, 2026-10-21).** Engineers, for coding. In addition the client can ask specific questions about what already exists ("do we have this feature active?", "can we already do this?"). Client accounts carry the `client` role; they ask through `/agl/ask` (chat or `agl product-ask`), where the gateway builds the prompt from the feature catalog (`stack/catalog/features.json`, reviewed in the repository and hashed into each run's configuration snapshot) plus the result of the latest verification run. Policy refuses any other request from a client (`CLIENT_SCOPE`).
**Owner, 2026-10-21.** There is no client at the moment: this is a PoC. The client account (`carla`) is a demo persona that shows the capability, and the catalog describes the PoC itself.
**Consequences.** "Is it active?" is answered from the catalog and the evidence suite, not from production, so D-08 holds. The catalog has to be kept honest; a unit test fails when it cites a check the suite does not run. Register PD-51.

## D-14 — Source code is data under the EU-only rule

**Context.** PD-43 applied "EU only, no exception" to model inference and left Git hosting, CI runners and other services open. The owner was asked whether code must stay in the EU or only production data.
**Decision (owner, 2026-10-21).** Both code and data. Repositories and the CI runners that build them must be EU-resident: an EU-resident Git host (GitHub Enterprise Cloud with EU data residency, or GitLab/Gitea self-hosted in the EU) and EU self-hosted ephemeral runners. For now the host is GitHub (owner, 2026-10-21).
**Consequences.** PD-16 and PD-09 are decided, not yet applied. For the PoC the repository stays on GitHub.com with GitHub-hosted runners (owner, 2026-10-21: "for now GitHub"); it holds synthetic code only. The EU-resident host and runners apply when real code is involved.

