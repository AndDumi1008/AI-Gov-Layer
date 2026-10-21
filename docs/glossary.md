# Glossary

| Term | Meaning in these documents |
|------|----------------------------|
| **AGL** | AI Governance Layer — the gateway, policy engine, ledger, registry, audit store, console and the SDLC rules described here |
| **Agent / agentic tool** | An AI tool that executes actions (runs commands, edits files, calls APIs) rather than only suggesting text |
| **Anchor** | Daily root hash of audit segments stored in an independent location and timestamped, used to prove the chain was not rewritten |
| **Annex A** | Control catalogue of ISO/IEC 27001:2022 |
| **Break-glass** | Time-boxed, dual-approved exception to a control, fully logged |
| **CASB** | Cloud Access Security Broker — controls SaaS usage from corporate devices |
| **Classification ceiling** | Highest data classification a model endpoint may receive |
| **Content store** | Separate encrypted store for prompt/response bodies and agent commands with output; mandatory, 30 days, erasable (D-12) |
| **Client account** | Identity with the `client` role: asks product questions only, answered from the feature catalog (D-13) |
| **Feature catalog** | `stack/catalog/features.json`: what the platform does today, with status and the checks that prove it; the only source for client answers |
| **Delegated identity** | Short-lived identity for an agent run acting on behalf of a human, scoped to a sandbox |
| **DLP** | Data Loss Prevention — detection of secrets, personal data and identifiers in prompts |
| **DPA** | Data Processing Agreement under GDPR Art. 28 |
| **DPIA** | Data Protection Impact Assessment under GDPR Art. 35 |
| **DSAR** | Data Subject Access Request |
| **Envelope** | A budget amount for a scope (org, cost centre, team, project, identity) and period |
| **Fail closed** | When a governance dependency is unavailable, requests are rejected |
| **GitOps** | Deployment model where a controller continuously reconciles production to a Git-declared state |
| **GPAI** | General-Purpose AI model, a category in the EU AI Act |
| **Hash chain** | Each event's hash includes the previous event's hash, so altering one event invalidates all later ones |
| **ISMS** | Information Security Management System |
| **Object Lock (compliance mode)** | Object storage setting that prevents deletion or overwrite by anyone until a retention date |
| **OPA / Rego** | Open Policy Agent and its policy language |
| **Policy bundle** | Signed, versioned set of policy rules loaded by the policy engine |
| **Provenance / SLSA** | Attestation describing how and by whom an artifact was built |
| **Registry** | Allowlist of model endpoints with status, region, ceiling, contract references |
| **Reserve / settle** | Two-phase budget accounting: estimate at request start, correct at completion |
| **Residency** | Where data is processed and stored, and under which legal entity |
| **RFC 3161** | Trusted timestamping protocol |
| **RFC 8785 (JCS)** | JSON canonicalisation scheme used before hashing |
| **Sandbox** | Ephemeral, network-restricted environment for agentic tools with no production credentials |
| **SCIM** | Protocol for syncing users and groups from the identity provider |
| **SCP** | AWS Service Control Policy (equivalents: Azure Policy, GCP Organization Policy) |
| **SoA** | Statement of Applicability (ISO 27001) |
| **TIA** | Transfer Impact Assessment for international data transfers |
| **WORM** | Write Once Read Many storage |
| **Zero retention** | Provider contractually does not store prompts/responses beyond the request |
