# 09 — Problem & Decision Register

**Project:** AI Governance Layer (AGL)
**Status:** Living document. Started 2026-10-19.
**Related:** [Decision Log](decision-log.md) (architecture decisions D-xx) · all numbered documents

---

## How this register works

Every problem found in review, every gap discovered while building, and every decision that is not a pure architecture choice gets an entry here. An entry is written when the problem is found, not when it is solved, and it is updated until its status is `closed`.

| Field | What goes there |
|-------|-----------------|
| **Problem** | What is wrong or undecided, who found it, how it was found |
| **Why it matters** | The concrete failure or exposure if left alone |
| **Fixes considered** | Each option, one line each |
| **Thought process** | How the options were weighed; what was ruled out and why |
| **Decision** | The option taken, or "open" with the owner and date needed |
| **Pros / Cons** | Of the chosen option, honestly |
| **Applied in** | Which document, file or configuration carries the change, or "not yet" |
| **Status** | `open` · `decided` · `applied` · `verified` · `closed` · `rejected` |

Statuses mean: *decided* = agreed but nothing changed yet; *applied* = documents or files changed; *verified* = a test or check proved it; *closed* = verified and no follow-up. When a decision becomes architectural, it also gets a D-xx entry in the Decision Log and the two link to each other.

IDs are `PD-xx`, chronological.

## Index

| ID | Title | Status | Found |
|----|-------|--------|-------|
| PD-01 | Default classification for unlabelled repositories | applied | 2026-10-19 |
| PD-02 | DDL forward reference and missing extension in the schema | verified | 2026-10-19 |
| PD-03 | PoC must prove a repository can be fully quarantined from AI | verified | 2026-10-19 |
| PD-04 | Customer-facing AI chat about parcel status | decided | 2026-10-19 |
| PD-05 | Developers fixing bugs with AI without production data, zero vendor trust | decided (layer 3 open) | 2026-10-19 |
| PD-06 | Auditing AI decisions: what to record and how to link it | decided | 2026-10-19 |
| PD-07 | Agents on laptops inherit the operator's privileges | decided | 2026-10-19 |
| PD-08 | Model weights are a supply chain | decided | 2026-10-19 |
| PD-09 | The agent's output is also a data exit | open | 2026-10-19 |
| PD-10 | Images signed before review; release accepts any signed digest | verified | 2026-10-19 |
| PD-11 | CI executes untrusted PR code with privileges | applied | 2026-10-19 |
| PD-12 | Long-lived GitOps tokens as repository secrets | applied | 2026-10-19 |
| PD-13 | Audit evidence endpoint has no authentication in the example | applied | 2026-10-19 |
| PD-14 | Squash merge drops the AI-Assisted trailer | open | 2026-10-19 |
| PD-15 | `ai-label` check trusts the author | decided | 2026-10-19 |
| PD-16 | CI runner location versus EU residency | open | 2026-10-19 |
| PD-17 | Actions pinned to tags rather than commit SHAs | verified | 2026-10-19 |
| PD-18 | Git hosting for the PoC: GitHub.com with a self-hosted runner on SERVER | applied | 2026-10-19 |
| PD-19 | Demo application on self-hosted Supabase (SERVER) with Vercel frontend; release path without GitOps/kind | applied | 2026-10-19 |
| PD-20 | GitHub at zero cost: public repositories in a free organisation, fork PRs kept off the self-hosted runner | applied | 2026-10-19 |
| PD-21 | Frontend hosting: Docker on SERVER first, Vercel as optional variant | decided | 2026-10-19 |
| PD-22 | SERVER is Windows 10 Pro with Docker Desktop (WSL 2) and a GTX 1070 | decided | 2026-10-19 |
| PD-23 | Schema: `identity_role` primary key cannot hold org-wide roles; non-EU endpoints allowed only while `evaluating` | verified | 2026-10-19 |
| PD-24 | MinIO public images no longer pullable; Bitnami legacy build used, pinned by digest | applied | 2026-10-19 |
| PD-25 | Docker cannot publish ports from an internal network; Caddy becomes the only entry point | verified | 2026-10-19 |
| PD-26 | Object Lock protects versions, not keys: a plain delete adds a delete marker | verified | 2026-10-19 |
| PD-27 | Gateway design for the PoC: own FastAPI service, non-streaming backends, synthesized SSE | decided | 2026-10-19 |
| PD-28 | One anchor per day is wrong: anchors need a cut-off and a day may hold several | verified | 2026-10-19 |
| PD-29 | The in-stack model server cannot pull weights; weights are side-loaded by an explicit job | verified | 2026-10-19 |
| PD-30 | Gateway database password was a fixed string in the migration and the example env | verified | 2026-10-20 |
| PD-31 | Driving Docker on a Windows host from SSH: cmd.exe splitting, credential helper, WSL bash shadowing | verified | 2026-10-20 |
| PD-32 | Port 443 on SERVER belongs to Tailscale Serve; Caddy moved to 8443 | applied | 2026-10-20 |
| PD-33 | Python and Node ignore the macOS keychain; CA file passed explicitly | verified | 2026-10-20 |
| PD-34 | Firewall and ACL must list the real ports (22, 53, 4000, 8443); the first versions blocked the tailnet | verified | 2026-10-20 |
| PD-35 | Claude Code through the gateway: env token wins over stored login, except when launched inside the desktop app | verified | 2026-10-20 |
| PD-36 | No MinIO web console in current builds; Object Lock shown with the mc client | applied | 2026-10-20 |
| PD-37 | Top-ups counted as negative consumption produced negative utilisation; now they enlarge the envelope | verified | 2026-10-20 |
| PD-38 | The PoC was built by an ungoverned agent session with full operator privileges | open | 2026-10-20 |
| PD-39 | Gate 1 turned on for this repository first; one human account limits what can be required | applied | 2026-10-20 |
| PD-40 | parcel-app backend: PostgreSQL + PostgREST (Supabase core) per environment instead of the full self-host bundle | applied | 2026-10-20 |
| PD-41 | No cloud account or spend in the PoC: an EU-region external model endpoint is out of scope; US-endpoint exception decision deferred (issue #19) | decided | 2026-10-21 |
| PD-42 | GitHub Issues is the ticket system; every PR must reference an issue, enforced by the `ticket` check | applied | 2026-10-21 |
| PD-43 | EU only, no exception: the US endpoint is revoked, all model work runs on the self-hosted tier (issue #19) | decided; applied in repo, not on SERVER | 2026-10-21 |
| PD-44 | Vercel removed: the parcel frontend runs only on SERVER, a static export in one web container per environment (issue #22) | applied | 2026-10-21 |
| PD-45 | Parcel frontend hosting: read-only web container plus an SSH forced-command deploy account per environment; Caddy routes (issue #25) | applied | 2026-10-21 |
| PD-47 | Gateway restarts lost unflushed audit events from WORM (hot copy kept them); flush on shutdown and recovery at startup | verified | 2026-10-21 |
| PD-46 | Sandboxes shared the governance network: could reach Postgres, MinIO, OPA and the egress proxy; now on a dedicated internal network with the gateway only (issue #26) | verified | 2026-10-21 |

---

## PD-01 — Default classification for unlabelled repositories

**Problem.** Most repositories will have no `.classification` manifest at the start. Found while writing the TRD classification scheme.
**Why it matters.** If unlabelled means PUBLIC or INTERNAL, confidential code goes to the widest set of models on day one.
**Fixes considered.** (a) Default INTERNAL, classify later. (b) Default CONFIDENTIAL. (c) Block AI entirely until classified.
**Thought process.** (a) is convenient and wrong in the direction that hurts. (c) stalls adoption and pushes people to shadow AI. (b) restricts model choice to EU zero-retention or self-hosted and turns classification into something teams want to do.
**Decision.** (b). Also recorded as D-10.
**Pros.** Safe by default; creates an incentive. **Cons.** Unlabelled repos cannot use the cheapest models; self-hosted tier may be needed earlier than planned.
**Applied in.** TRD §8, schema `repository.classification default 'CONFIDENTIAL'`, Decision Log D-10.
**Status.** applied.

## PD-02 — DDL forward reference and missing extension

**Problem.** `delegated_identity` referenced `repository` before it was created; the `price` exclusion constraint needed `btree_gist`. Found by loading the DDL into PostgreSQL 16.
**Why it matters.** A schema document that does not load is not a schema document.
**Fixes considered.** Reorder tables; or add the foreign key after `repository` exists. Add the extension.
**Thought process.** Reordering breaks the document's narrative (identity before repositories). An `alter table` after the dependency keeps both.
**Decision.** `alter table ... add constraint` after `repository`; `create extension btree_gist` at the top.
**Pros.** Document reads in logical order and loads. **Cons.** One constraint lives away from its table.
**Applied in.** Schema §3.1–3.2. Verified by a clean load (29 tables, later 31) and by constraint tests (append-only trigger, dual approval, non-EU region, quarantine guard all reject bad rows).
**Status.** verified.

## PD-03 — PoC must prove a repository can be fully quarantined

**Problem.** The business requirement arrived mid-draft: an application repository must not be exposed to AI at all (no code, no DB, nothing from production) until defined certainties are met; total budget must hold; nothing leaves the EU; records must be immutable.
**Why it matters.** The first PoC draft treated quarantine as a classification level; the requirement is a gate with evidence and sign-off, which classification alone does not express.
**Fixes considered.** (a) Use RESTRICTED classification as "quarantined". (b) Add an explicit `ai_exposure` state with a gate checklist evaluated on every request.
**Thought process.** (a) conflates "this data is secret" with "this repo has not yet been cleared". A repo can be INTERNAL and still uncleared. (b) makes the certainties data, so a missing item re-closes the door automatically.
**Decision.** (b): `repository.ai_exposure`, `repository_ai_gate` with G1–G6, trigger that refuses `allowed` unless the gate holds, `dataset.mountable` false for anything prod-derived. PoC document restructured around four proofs PR-1..PR-4 with scenarios S19–S26.
**Pros.** Gate is enforceable in the database and in policy; evidence is attached to the gate row. **Cons.** More control-plane state to keep accurate; gate items G2–G4 need automated feeders or they rot.
**Applied in.** PoC §1.1, schema §3.2. Trigger verified in PostgreSQL.
**Status.** verified.

## PD-04 — Customer-facing AI chat about parcel status

**Problem.** A customer could ask an AI assistant about their parcel. Raised as a what-if.
**Why it matters.** Customer messages contain personal data; the assistant could be talked into another customer's parcel; the model vendor would see customer data.
**Fixes considered.** (a) Give the model a tool that queries the tracking database with the customer's token. (b) The backend resolves identity and parcels deterministically and hands the model a de-identified status object; the model only writes language; the backend fills names after.
**Thought process.** (a) puts authorization in the prompt, where injection lives. (b) keeps authorization in code, removes personal data from the model path, and makes the choice of model a cost and residency question rather than a trust question.
**Decision.** (b), plus DLP on inbound customer messages, content store with short retention and erasure, per-service budget and per-customer rate limits, AI Act transparency notice, human handoff.
**Pros.** No PII reaches any model; injection cannot cross customers. **Cons.** Less flexible answers; backend templating work; some questions must go to a human.
**Applied in.** Discussion only; not yet in the documents. Candidate for document 10 (customer AI surface).
**Status.** decided.

## PD-05 — Developers fixing bugs with AI without production data, zero vendor trust

**Problem.** Teams need to update code, read audit logs and fix bugs with AI help, but no production data may leave the infrastructure and no vendor contract is trusted for personal data.
**Why it matters.** Debugging is where production data leaks into prompts.
**Fixes considered.** Layer 1: telemetry contains no personal data by design (pseudonymous IDs, redaction in the log pipeline). Layer 2: masked, production-shaped replica for reproduction. Layer 3: read-only, no-egress analysis enclave with a self-hosted model inside the production boundary, used only by on-call humans under exception.
**Thought process.** Layers 1 and 2 cover most bugs and keep the "AI never touches production" rule intact. Layer 3 bends it from "never reads" to "never acts, never exports" and therefore needs explicit risk acceptance. Open-weight models run on our own hardware involve no data exchange with the model's author, which answers the "no handshake" concern.
**Decision.** Layers 1 and 2 adopted. Layer 3 is an option requiring risk acceptance and a dual-approved exception per use; not adopted by default. Registry: only `EU_SELF_HOSTED` for CONFIDENTIAL, nothing for RESTRICTED.
**Pros.** Most work needs no bend; vendor trust removed from the PII path. **Cons.** GPU cost; open weights lag frontier quality; layer 3, if adopted, is a standing exception that auditors will ask about.
**Applied in.** Discussion; TRD §4.4 partially. Candidate for document 10.
**Status.** decided (layer 3 open; owner CISO).

## PD-06 — Auditing AI decisions

**Problem.** How to track what an AI decided and prevent it from acting on its own judgment. Raised as a question.
**Why it matters.** Without a per-action record, an incident cannot be traced to a session, and denied attempts (the most informative events) are lost.
**Fixes considered.** Record the model's reasoning; or record inputs, outputs and actions with a session link.
**Thought process.** Reasoning text is not a reliable account of why a system acted. Inputs, outputs and tool calls are. Every tool call becomes two events (requested; executed or denied) evaluated by the same policy engine that judges prompts, so the record of what was attempted is produced by the component that prevents it.
**Decision.** Add `agent_action_requested` / `agent_action_executed` / `agent_action_denied` events with session ID and delegated identity; record model name and version on every event; sample sessions for human review. Containment in six layers (nothing to kill, explicit tools, policy gate per action, OS limits, no production path, caps and kill switch).
**Pros.** Full trace from incident to session; denied attempts visible. **Cons.** Event volume; the pre-tool hook depends on the agent CLI supporting it, which becomes a procurement requirement.
**Applied in.** Discussion. Schema change pending (event types, session link).
**Status.** decided.

## PD-07 — Agents on laptops inherit the operator's privileges

**Problem.** Every enforcement row assumed the agent runs in a sandbox. Nothing forced that. An agent CLI on a laptop is the developer; if the developer has production credentials in the shell, so does the agent. Found by re-reading the enforcement table after being asked what was missing.
**Why it matters.** "No AI identity holds production permissions" becomes true and useless. Org policies keyed on an `agent=true` tag never fire.
**Fixes considered.** (a) Forbid local agent use entirely. (b) Allow local use, but remove standing production credentials from workstations (privileged access management with just-in-time sessions on a jump host without agent tooling), set the gateway as the only model endpoint via managed settings, and treat the pipeline as the enforcement point for everything the agent produces.
**Thought process.** (a) is unenforceable in practice and drives shadow use. (b) accepts that the laptop is untrusted and makes the two things that matter (credentials, data) unavailable there. The business confirmed local Claude Code is acceptable.
**Decision.** (b). Privileged access management for humans becomes a prerequisite of the isolation claim, moved into Phase 0/3 scope.
**Pros.** Developer experience preserved; one fewer system to force people into. **Cons.** No delegated identity and no step cap on the laptop; long-running autonomous sessions must still use the sandbox orchestrator.
**Applied in.** Document 08 §0 and §5. Implementation plan not yet updated with the PAM prerequisite.
**Status.** decided.

## PD-08 — Model weights are a supply chain

**Problem.** Self-hosting removes the vendor contract but introduces trust in a weights file. Found while answering PD-05.
**Why it matters.** A tampered or malicious model file executes inside the most trusted tier.
**Fixes considered.** Pin versions; verify hashes and signatures at download; accept only `safetensors`; scan and quarantine before approval; record the weight digest in the registry.
**Decision.** All of the above; weight digest becomes a registry field so events are attributable to a specific binary.
**Pros.** Cheap; standard. **Cons.** Signature availability varies by publisher; some models only ship in formats that must be converted.
**Applied in.** Not yet (registry field and F-08 step to add).
**Status.** decided.

## PD-09 — The agent's output is also a data exit

**Problem.** All controls govern what goes into a model. The agent also writes commits, PR text, fixtures and CI logs, which land in the Git host and runners, possibly outside the EU, without touching the gateway.
**Why it matters.** A fixture with real customer data or a pasted log in a PR comment leaves the region silently.
**Fixes considered.** DLP on the push path (pre-receive hook or CI check on the diff and PR body); DLP on CI log output; residency assessment of the Git host and runners like any model vendor; EU self-hosted runners.
**Thought process.** The pipeline already has a secrets scan; extending it to personal-data patterns on diffs and PR bodies is small. The runner and host location is a business decision (see PD-16).
**Decision.** Open. Owner: security + platform. Needed before Phase 2 exit.
**Status.** open.

## PD-10 — Images signed before review; release accepts any signed digest

**Problem.** In the example pipeline, Gate 2 signs the image on every PR; the release workflow and the admission policy only check that the certificate identity is the merge-candidate workflow. A digest built from an unreviewed PR is therefore releasable via the `workflow_dispatch` input. Found in a self-review of the pipeline examples.
**Why it matters.** The human release approval sees a digest, not its origin; the "only reviewed code ships" claim fails.
**Fixes considered.** (a) Sign only on main / merge-group runs. (b) Keep signing on PRs for preview, but verify the source ref in the certificate (Sigstore embeds it) and derive the release digest from the main commit instead of accepting it as input. (c) Separate attestation types for preview vs release.
**Thought process.** (a) loses "the digest that passed Gate 2 is the one that ships" unless the merge queue rebuilds, which it does; acceptable. (b) keeps build-once and adds a precise check. (c) is a complement to either.
**Decision.** (b) + (c): verify `source_repository_ref` is `refs/heads/main` or a merge-group ref, both in release and in cluster admission; remove the free-form digest input; preview images get an unprivileged attestation.
**Pros.** Build once preserved; precise provenance check. **Cons.** Admission policy becomes more specific and must be kept in sync with the workflow file name and ref patterns.
**Applied in.** `merge-candidate.yml` (release signature only on `merge_group`; preview attestation on PRs), `release.yml` (digest derived from main's SHA; `cosign verify` checks repository, workflow ref under `gh-readonly-queue/main`, trigger `merge_group`, SHA; no digest input), `admission/kyverno-verify-images.yaml`. actionlint passes.
**Status.** verified (static). Not yet exercised against a live repository.

## PD-11 — CI executes untrusted PR code with privileges

**Problem.** `make build` runs whatever the PR's Makefile says, in jobs that hold a write-capable `GITHUB_TOKEN`, an OIDC token and preview deployment credentials. Found in the same self-review.
**Why it matters.** Code executes before review with credentials in hand; an AI-suggested change is enough.
**Fixes considered.** Read-only tokens on PR-triggered jobs; preview deploy in a separate job bound to a `preview` environment whose credentials reach only the preview namespace; OIDC trust policies restricted by ref and environment claims; ephemeral runners.
**Decision.** All four.
**Pros.** Standard hardening; no functional loss. **Cons.** More jobs and environments to manage; preview credentials need their own rotation.
**Applied in.** `pr-checks.yml` and `merge-candidate.yml`: top-level `contents: read`; per-job permissions; `preview` job bound to the `preview` environment with `id-token: write` scoped by environment claim; README lists the OIDC trust-policy and ephemeral-runner requirements.
**Status.** applied.

## PD-12 — Long-lived GitOps tokens as repository secrets

**Problem.** `GITOPS_TOKEN_PROD` as a repository secret is reachable by any workflow on main.
**Why it matters.** Anyone who lands a workflow change on main can push to the production GitOps repository without the environment approval.
**Fixes considered.** Environment secret of `production` (only materialises after approval); GitHub App installation token with short life; branch protection on the GitOps repository limiting that identity to digest bumps under its own path.
**Decision.** All three.
**Pros.** Secret only exists post-approval. **Cons.** GitHub App setup and a second protected repository to maintain.
**Applied in.** `release.yml`: `actions/create-github-app-token` mints a short-lived token from `GITOPS_APP_ID` / `GITOPS_APP_PRIVATE_KEY` held as environment secrets of `staging` and `production`; README documents the GitOps repository protection.
**Status.** applied.

## PD-13 — Audit evidence endpoint has no authentication in the example

**Problem.** CI posts merge and deploy events to the audit store with a bare `curl`.
**Why it matters.** A hash chain proves order and integrity, not authenticity of the source; anyone could forge a deploy event.
**Decision.** CI presents its OIDC token; the gateway verifies issuer, repository and workflow claims and stamps them into the event.
**Pros.** Keyless, matches cosign. **Cons.** The audit API must validate GitHub's OIDC, one more dependency.
**Applied in.** `merge-candidate.yml` evidence job and `release.yml` production job request an OIDC token (`audience=agl-audit`) and send it as `Authorization: Bearer`; jobs carry `id-token: write`. The audit API side is a Phase 1 deliverable.
**Status.** applied.

## PD-14 — Squash merge drops the AI-Assisted trailer

**Problem.** The ruleset uses squash in the merge queue; the squash commit loses individual commit messages and signatures.
**Why it matters.** The marker survives on the PR label and the merge event, but main's history no longer shows it.
**Fixes considered.** Merge commits (keep original signed commits; history not linear). Rebase (re-signs commits with GitHub's key; original signatures lost). Squash with the trailer preserved in the squash body.
**Thought process.** Trade-off between a linear history and preserving the developers' own signatures. The audit chain is the system of record either way.
**Decision.** Open. Owner: engineering lead.
**Status.** open.

## PD-15 — `ai-label` check trusts the author

**Problem.** Detection is based on a commit trailer the author controls.
**Why it matters.** Unlabelled AI-assisted PRs escape the stronger review requirement.
**Fixes considered.** Cross-check with gateway telemetry (agent-type calls by this identity on this repository and branch during the PR's lifetime); treat a mismatch as a failed check with a human override.
**Decision.** Add the telemetry cross-check as a required check once the gateway exposes a query API.
**Pros.** Label becomes evidence-backed. **Cons.** Correlation is by identity and repo, not by diff; false positives when a developer used the agent for an unrelated task.
**Applied in.** TRD SDLC-02 mentions it; workflow does not implement it.
**Status.** decided.

## PD-16 — CI runner location versus EU residency

**Problem.** GitHub-hosted runners run outside the EU; Gate 2 builds and the preview deploy run there with source code and masked data.
**Why it matters.** Whether source code leaving the region violates the residency rule is a business decision not yet taken.
**Fixes considered.** Accept for code and masked data, forbid for anything higher; or EU self-hosted ephemeral runners for all workflows.
**Decision.** Open. Owner: CISO with legal. Needed in Phase 0.
**Status.** open.

## PD-17 — Actions pinned to tags rather than commit SHAs

**Problem.** Example workflows use `@v4`-style tags.
**Why it matters.** A moved tag changes the code that runs in the pipeline.
**Decision.** Pin to commit SHAs with `ratchet`, keeping the `# ratchet:` comment so `ratchet update` can refresh them. Trivy tag corrected from a non-existent `0.28.0` to `v0.35.0`; conftest to `v0.4.0`.
**Applied in.** All three workflows; 30 references pinned; actionlint passes.
**Status.** verified.

## PD-18 — Git hosting for the PoC

**Problem.** The PoC needs a git host and CI. Two machines are available (SERVER with Docker, a Mac), connected over Tailscale, with DNS under `shortandsweet.home.ro`.
**Why it matters.** The Tier 2 proofs (S15–S18) depend on rulesets, a merge queue and a human-only environment approval. The residency proof depends on where code and builds run.
**Fixes considered.** (a) Forgejo on SERVER with a Forgejo runner and registry. (b) GitHub.com for the repository with a self-hosted ephemeral runner on SERVER joined to the tailnet. (c) GitHub.com with GitHub-hosted runners only.
**Thought process.** (a) keeps everything on owned hardware but has no environment-approval gate, so S18 would be emulated with a protected branch, weakening the demo of the second human-in-the-loop point. (c) runs builds and previews off SERVER, so previews cannot reach SERVER's services and the "stays on our hardware" story is lost. (b) keeps the `pipeline/` files exact and keeps builds and previews on SERVER, at the cost of source code and PR metadata living on GitHub.com (the PD-16 trade-off, accepted for a PoC with synthetic code).
**Decision.** (b). Private repository; ephemeral `actions/runner` container with a Docker-in-Docker sidecar on `ci-net`, not on `agl-net`; `runs-on` driven by the repository variable `AGL_RUNNER`.
**Pros.** Exact workflows, real environment approvals, builds on owned hardware. **Cons.** Self-hosted runner executes PR code on SERVER, so the PD-11 conditions (ephemeral, DinD, read-only token, private repo) are mandatory; code leaves SERVER to GitHub.
**Applied in.** PoC §10.5 (git decision table, bring-up step 8); workflows `runs-on: ${{ vars.AGL_RUNNER || 'ubuntu-latest' }}`; pipeline README. actionlint passes.
**Status.** applied.

## PD-19 — Demo application on Supabase + Vercel; release path without a cluster

**Problem.** The PoC needed a real application to govern, not only a gateway. Proposal: the parcel app with a self-hosted Supabase backend on SERVER and a Next.js frontend deployed by Vercel.
**Why it matters.** With a real backend the data proofs (per-role views, quarantine, masked previews) run against real tables and row-level security instead of a static page, and the release path has a real production database to protect.
**Fixes considered.** (a) Keep the kind + Kyverno + Argo CD path and containerise the app. (b) Replace the cluster path: production release = apply migrations to the production Supabase and deploy the prebuilt frontend to Vercel, both inside the human-approved `production` job; previews = Vercel preview deployments against a preview Supabase stack with masked data on SERVER. (c) Supabase cloud (EU region) instead of self-hosted.
**Thought process.** (a) adds a cluster nobody needs for this app and hides the point. (b) keeps every control (two human gates, build once, signed artifact, env-scoped credentials) and maps onto what the team would actually run. (c) is a legitimate production option (EU region, managed) but loses the "production is on our hardware" proof for the PoC; keep as a Phase 1 option. Vercel is a US platform: the frontend bundle and build logs go there, the browser on the Mac reaches the private backend over the tailnet, so no backend data touches Vercel. Recorded as a PD-16-class trade-off.
**Decision.** (b). Three Supabase stacks on SERVER (`preview`, `staging`, `production`) on separate Docker networks; production reachable only through Caddy and only by the browser on the tailnet and the dedicated release runner; the image signature check is replaced by a signed, digest-pinned prebuilt frontend artifact and a migration checksum recorded in the release candidate; kind/Kyverno/Argo CD removed from the PoC scope.
**Pros.** Real app, real RLS, real previews, simpler stack. **Cons.** Frontend code and build logs on Vercel; a release runner with a route to the production network must exist and is the most sensitive component on SERVER; Supabase self-hosting is a sizeable Compose stack per environment (memory).
**Applied in.** PoC §10.6; `pipeline/.github/workflows/merge-candidate-paas.yml` and `release-paas.yml` (prebuilt artifact hashed and blob-signed in merge-queue runs only; release finds the merge-queue run for main's SHA, verifies the bundle by workflow, trigger and SHA, refuses preview markers; production job on the `server-release` runner compares migration checksums before `supabase db push`; frontend rollback by dispatch). Actions pinned by ratchet; linted with actionlint. Not yet run against a live repository.
**Status.** applied.

## PD-20 — GitHub plan for private demo repositories

**Problem.** The pipeline relies on rulesets, environments with required reviewers and a merge queue. The repositories must be private because a self-hosted runner serves them (PD-11). On GitHub those features are free only for public repositories.
**Why it matters.** On a Free personal account the human-approval gate (S18) and the merge-queue signature design (PD-10) do not exist for private repositories.
**Fixes considered.** (a) Organisation on the Team plan. (b) Personal account on Pro: rulesets and environments yes, merge queue no; sign on the push-to-main run instead. (c) Public repository with GitHub-hosted runners only: free, but previews cannot reach SERVER.
**Thought process.** (a) costs two seats and keeps the design exact. (b) weakens "final merge result retested". (c) breaks the on-premises preview and the residency story.
**Decision (revised the same day).** The constraint is zero cost, so neither paid option applies. (d) **Public repositories in a free organisation**: rulesets, environments and merge queue are free there. The self-hosted-runner exposure that made us want private repositories is closed differently: fork pull requests require maintainer approval before any workflow runs, `runs-on` routes fork PRs to GitHub-hosted runners, preview jobs are skipped for forks, and fork runs get no secrets or write tokens by default. The repositories contain synthetic data and documentation only.
**Pros.** €0; the pipeline files work exactly as written. **Cons.** Everything in the repositories is readable by anyone; the PD-11 condition "private repository" is replaced by four settings that must all stay in place.
**Applied in.** PoC §10.5 and §10.7; workflows `pr-checks.yml`, `merge-candidate.yml`, `merge-candidate-paas.yml` (fork-aware `runs-on`, fork-skip on preview jobs). actionlint passes.
**Status.** applied.

## PD-21 — Frontend hosting for the parcel app

**Problem.** The frontend can be deployed by Vercel or run in Docker on SERVER. The request was to use external tools only when necessary.
**Fixes considered.** (a) Vercel for all environments. (b) Docker on SERVER behind Caddy, one container per environment, promoted by digest. (c) Both, from the same prebuilt artifact.
**Thought process.** (b) needs no account, keeps every byte on SERVER, and the artifact promotion mirrors the container variant already written. Vercel adds a realistic PaaS step but is not needed for any proof. The PaaS workflows already exist, so (c) is a configuration switch later.
**Decision.** (b) first; Vercel variant kept dormant in the repository.
**Pros.** Zero external dependencies for Tier 2 beyond GitHub. **Cons.** One less "real PaaS" demonstration until switched on.
**Applied in.** PoC §10.7.
**Status.** decided.

## PD-22 — SERVER is Windows 10 Pro with Docker Desktop and a GTX 1070

**Problem.** The stack was designed for a Linux Docker host. SERVER runs Windows 10 Pro; containers run in the WSL 2 backend of Docker Desktop.
**Why it matters.** Control over SSH, binding to the Tailscale interface, GPU passthrough and memory limits behave differently.
**Fixes considered.** Install Linux on SERVER; or adapt: OpenSSH Server on Windows + Docker context over SSH, Windows Firewall scoped to the Tailscale range, `.wslconfig` memory, CUDA on WSL for Ollama, all files in the WSL filesystem.
**Thought process.** Reinstalling is a day of the user's time for little PoC benefit; the adaptations are small and documented. `internal` networks and the egress proxy work unchanged inside the VM, so the network proofs hold.
**Decision.** Adapt. A 7–8 B Q4 model on the 1070 is the real local tier; nothing larger.
**Pros.** No OS change. **Cons.** Docker Desktop licensing for commercial use must be checked; the firewall, not Docker, is the binding control.
**Applied in.** PoC §10.7.
**Status.** decided.

## PD-23 — Schema fixes found by loading the seed

**Problem.** (a) `identity_role (identity_id, role, scope_team)` as primary key makes `scope_team` NOT NULL, so org-wide roles (security admin, DPO, finance) cannot be stored. (b) The Anthropic direct endpoint needed for the PoC cannot be inserted at all because the region check demands an EU country, yet PoC §10.5 decided to use it under an exception. Found when the seed file failed to load.
**Fixes considered.** Sentinel team id for org-wide roles; or drop the composite key and use a unique index on `coalesce(scope_team, zero-uuid)`. For regions: fake an EU region (rejected: misrepresents residency); allow non-EU rows only while `status = 'evaluating'`, so they can never become approved, and add residency class `NON_EU_EVALUATING`.
**Decision.** Unique index with coalesce; region check `EU list OR status = 'evaluating'`; new residency value. Both in `stack/schema/002_poc.sql`; the policy allows an evaluating model only under an active `model_enable` exception and records `exception_id` on every event.
**Pros.** Honest registry: non-EU is visible as such and time-boxed. **Cons.** Document 05 and the migration now differ until the document is updated (note added there).
**Applied in.** `002_poc.sql`, policy `agl.rego`, S14 (approved non-EU still rejected). Verified by load and by scenario.
**Status.** verified.

## PD-24 — MinIO images unavailable

**Problem.** `minio/minio` on Docker Hub and `quay.io/minio/minio` both refuse anonymous pulls (401 / "repository does not exist"). Found at first `compose up`.
**Fixes considered.** Bitnami legacy MinIO images (`bitnamilegacy/minio`, `bitnamilegacy/minio-client`), Zenko CloudServer, LocalStack, RustFS. All probed; all but Zenko and LocalStack untested for Object Lock semantics.
**Decision.** Bitnami legacy MinIO, pinned by digest, with `mc` from the matching client image. Object Lock in COMPLIANCE mode confirmed working (S11). Production uses the cloud provider's object storage anyway (docs/07 §7).
**Pros.** Same API and tooling as planned. **Cons.** "Legacy" means no further updates; acceptable for a PoC, must not be the production choice.
**Status.** applied.

## PD-25 — Internal networks cannot publish ports

**Problem.** Services on the `internal: true` network (gateway, postgres, minio, opa) had `ports:` entries that Docker silently did not bind; the gateway was unreachable from the host.
**Thought process.** Docker's rule is a feature: anything reachable from outside must sit on a non-internal network. Putting the gateway on such a network would give it a direct route to the internet and bypass the egress proxy. So the only non-internal services are Caddy (entry) and the egress proxy (exit).
**Decision.** Remove all port publishing from internal services; Caddy is always on, publishes 443 (TLS, hostnames) and 4000 (plain HTTP → gateway, local/CLI use); `psql` for the DBA scenario runs through `docker compose exec`; MinIO consoles only via Caddy hostnames on the tailnet.
**Pros.** The network diagram in docs/07 §10 is now literally enforced by Docker. **Cons.** Local debugging goes through Caddy or `compose exec`.
**Applied in.** `stack/docker-compose.yml`, `caddy/Caddyfile`, `demo/run-scenarios.sh`. Verified: health through Caddy, S25 egress refused.
**Status.** verified.

## PD-26 — Object Lock protects versions, not keys

**Problem.** `mc rm <object>` on a locked, versioned bucket succeeds by writing a delete marker; a later plain `GET` returns `NoSuchKey`, so the first verifier run crashed. Found by S11 followed by S12.
**Thought process.** The data was never gone: the locked version is intact and `mc rm --versions --force` fails with "WORM protected". The verifier must read the newest real version explicitly, and a delete marker on an audit segment is itself evidence of a tampering attempt worth reporting.
**Decision.** Verifier reads via `list_object_versions` + `get_object(VersionId=…)` and reports `delete_attempted` per segment; S11 deletes versions and expects "WORM protected"; documentation states that delete markers are expected noise and that retention is what matters.
**Pros.** Verifier is robust and more informative. **Cons.** A WORM bucket can accumulate delete markers; the console must not mistake them for data loss.
**Applied in.** `gateway/app/audit.py`, `demo/run-scenarios.sh`. Verified: S12 passes after a delete attempt and reports it.
**Status.** verified.

## PD-27 — Gateway implementation for the PoC

**Problem.** D-06 left the gateway to a spike. The PoC needed deterministic behaviour (reserve/settle, hash chain, reroute by classification, quarantine, in-band reason codes) that an off-the-shelf gateway would need callbacks for.
**Decision.** A small FastAPI gateway (~1,000 lines across modules) exposing both the OpenAI and Anthropic surfaces, calling backends non-streaming and synthesizing SSE for streaming clients so redaction can be reversed on the complete response. LiteLLM or Envoy AI Gateway remain candidates for Phase 1 behind the same policy and ledger.
**Pros.** Every control is explicit and testable; Claude Code works through `ANTHROPIC_BASE_URL`. **Cons.** Streaming latency is the backend's full response time; no tool-use passthrough yet; one instance (no HA) in the PoC.
**Applied in.** `stack/gateway/`. Verified: 28/28 scenarios locally, streaming on `/v1/messages` with redaction.
**Status.** decided.

## PD-28 — Daily anchor semantics

**Problem.** `audit_anchor` was unique per date and the root hash covered "all segments closed that day". Running the anchor twice in a day kept the first root (insert ignored) while more segments closed, so verification failed with no tampering at all. Found on the second scenario run against the same stack.
**Thought process.** An anchor is a statement "as of time T, the chain's segments up to T hash to R". Without T it cannot be re-verified once more segments exist. The production design (RFC 3161 timestamp) carries T implicitly; the schema did not.
**Decision.** `audit_anchor.anchored_through timestamptz`, several anchors per day allowed; the anchor document and the verifier both use `closed_at <= anchored_through`. Nightly anchoring stays the norm; ad-hoc anchors (before an audit export, after an incident) are now harmless.
**Pros.** Verifiable at any later time; evidence exports can anchor on demand. **Cons.** One more column and a dropped uniqueness constraint relative to document 05 (noted in §9 there).
**Applied in.** `002_poc.sql`, `gateway/app/audit.py`. Verified: two consecutive scenario runs on one stack both pass S12.
**Status.** verified.

## PD-29 — Model weights enter through an explicit job

**Problem.** `ollama pull` inside the stack fails: the Ollama container is on the internal network and cannot resolve or reach the model registry. Found when enabling the `model` profile locally.
**Thought process.** This is the network design working. It also matches PD-08: weights are a supply chain and should not be fetched from inside the most trusted tier on demand. A one-off container that shares only the model volume (not the network) performs the pull; the operator sees what was fetched and can record the digest in the registry before approving the endpoint.
**Decision.** `deploy/server/pull-model.sh` (one-off container with its own server process, shared `agl_ollama-models` volume). No egress allowlist entry for model registries. Registry `model.version` is to carry the weight digest (field exists; filling it is a Phase 1 task).
**Pros.** Weights provenance is a visible step; the stack's network stays closed. **Cons.** Manual step per model update.
**Applied in.** `deploy/server/pull-model.sh`, docs/07 §9.1. Verified: CONFIDENTIAL request answered by Qwen via `code-local` after side-loading.
**Status.** verified.

## PD-30 — A fixed database password in the repository

**Problem.** `002_poc.sql` created the gateway role with the literal password `agl_gateway_dev`, and `.env.example` carried the same value. Found by running our own `check-env-vars.sh` on this repository before the first push: rule 4 flagged a secret-like variable with a non-placeholder value.
**Why it matters.** Every deployment, including SERVER, would share a password that is public in the repository. The network isolation would be the only thing protecting the database.
**Fixes considered.** Keep it and rely on the internal network (rejected); set the password in the migration from an environment variable (SQL cannot read the environment); a shell init script in the PostgreSQL image entrypoint that alters the role's password from `AGL_GATEWAY_DB_PASSWORD`.
**Decision.** `003_gateway_password.sh` sets the password at first initialisation and refuses placeholder values; `bootstrap.sh` refuses to start with any `changeme` password unless explicitly allowed for a throw-away laptop; `.env.example` holds placeholders only; the gateway's default connection string has no password. The repository's own `.gitleaks.toml` allowlists the synthetic test patterns so the secrets check stays meaningful.
**Pros.** No credential in git; the pipeline's own rule caught it, which is the point of having the rule. **Cons.** First-time setup needs a real value in `.env` before anything starts.
**Applied in.** `stack/schema/002_poc.sql`, `003_gateway_password.sh`, `stack/.env.example`, `stack/bootstrap.sh`, `gateway/app/config.py`, `.gitleaks.toml`. Verified: fresh stack starts with the environment password; suite passes.
**Status.** verified.

## PD-31 — Driving Docker on a Windows host from SSH

**Problem.** Three separate traps, found one after another while bringing the stack up on SERVER from the Mac. (a) SSH's remote shell on Windows is `cmd.exe`, which splits a command on `&&` and `|` before Git Bash sees it, so pieces of each command ran in cmd. (b) The Docker CLI calls `docker-credential-desktop.exe` whenever it is on the PATH, and that helper needs the interactive logon session; pulls fail from SSH with "A specified logon session does not exist". (c) `bash` resolves to `C:\Windows\System32\bash.exe`, the WSL launcher, unless Git's directories come first on the PATH.
**Decision.** `deploy/server/agl-ssh.sh`: the command is base64-encoded and passed inside one double-quoted argument; PATH puts Git first and excludes Docker's `resources/bin`; a `docker` shim in `D:\agl-docker-config\bin` execs `docker.exe` by full path; `DOCKER_CONFIG` points to a plain `{}` config. Public images only, which is all the stack needs.
**Pros.** Everything is driven from the Mac; no interactive session needed except to start Docker Desktop itself. **Cons.** Docker Desktop still has to be started by hand in the Windows session, and the wrapper is Windows-specific.
**Status.** verified (bootstrap, model side-load, image build and the suite all ran through it).

## PD-32 — Port 443 belongs to Tailscale Serve

**Problem.** Caddy could not bind `100.109.138.14:443`: `tailscaled` holds it for a Tailscale Serve configuration belonging to another project on SERVER.
**Decision.** Leave the other project alone. Caddy's host port is parametrised (`AGL_HTTPS_PORT`), 8443 on SERVER; the gateway URL is `https://gateway.shortandsweet.home.ro:8443`. 443 can be reclaimed later by setting the variable if Serve is ever reset.
**Status.** applied.

## PD-33 — Client trust stores

**Problem.** After the Caddy root was trusted in the macOS System keychain, `curl` verified the gateway, but the Python CLI did not (every scenario failed with "no token" because the login call was rejected), and Node-based Claude Code would not either. Python and Node ship their own CA bundles.
**Decision.** CLI honours `AGL_CA_FILE`; Claude Code gets `NODE_EXTRA_CA_CERTS` in the managed settings; the suite documents both. In production the gateway certificate comes from a CA the organisation already distributes, which removes this step.
**Status.** verified.

## PD-34 — Firewall and ACL port lists

**Problem.** The first firewall script added Block rules that Windows applied to Tailscale peers (they count as "Internet"), and the first ACL allowed only a `tag:dev` source, hiding the server from the untagged Mac; after Caddy moved to 8443 and 4000 was needed for the CLI, both lists had to change again.
**Decision.** Allow-only firewall rules scoped to `100.64.0.0/10` for 22, 53, 4000, 8443; ACL from `autogroup:member` to `tag:server` on the same ports; `tests` omitted because their source cannot be an autogroup.
**Status.** verified (ports reachable from the Mac, nothing else).

## PD-35 — Claude Code through the gateway

**Problem.** The first end-to-end test of Claude Code against the gateway failed with "Token rejected": a header capture showed Claude Code sending the desktop app's own OAuth token instead of the gateway JWT given in the environment. The test had been launched from inside a Claude desktop session, whose `CLAUDE_CODE_*` variables make nested runs reuse the host's login.
**Thought process.** With a scrubbed environment (plain terminal conditions) `ANTHROPIC_AUTH_TOKEN` is sent as the bearer token even though a Keychain login exists, so the managed settings work as designed for a developer's terminal. The gateway also now accepts the JWT from either `Authorization` or `x-api-key`, so the `ANTHROPIC_API_KEY` form works too.
**Decision.** Managed settings carry `ANTHROPIC_BASE_URL`, `ANTHROPIC_AUTH_TOKEN`, `NODE_EXTRA_CA_CERTS` and `ANTHROPIC_MODEL=claude-sonnet-4-5` (the gateway maps unknown model names to `code-default`; a real model name avoids Claude Code's catalog warning). Observed on the first call: Claude Code's system prompt includes the user's email, which the gateway redacted (`PII_REDACTED`); cost per Claude Code turn is ~€0.03 at list price because of the large system prompt, which the budget ledger now meters.
**Pros.** Developers keep Claude Code as is; one settings file routes it. **Cons.** The 8 h dev token must be refreshed until the IdP integration replaces the dev issuer; nested launches inside the desktop app bypass the setting.
**Status.** verified.

## PD-36 — No MinIO web console

**Problem.** The runbook pointed at `https://minio.shortandsweet.home.ro:8443` for the Object Lock view; it returned 502. MinIO listens on 9000 only: the embedded console was removed from community builds in 2025 and the Bitnami legacy image follows.
**Fixes considered.** A third-party S3 browser container (another component to assess); or show the store with the `mc` client.
**Decision.** `demo/show-worm.sh` (`make demo-worm`): lock configuration, newest segments, retention mode and expiry, versions, a refused delete of all versions, and the anchors in the second store. The Caddy hostnames for the consoles were removed. In production the cloud provider's console or an internal dashboard replaces this.
**Status.** applied (verified on SERVER).

## PD-37 — Budget utilisation after a top-up

**Problem.** The web chat showed the org budget at "-49 %" after the demo's €1 top-up on a €2 envelope: `budget_state` summed adjustments (stored as negative lines) into consumption.
**Decision.** A top-up enlarges the envelope: `amount_eur` = envelope minus the (negative) adjustments, `consumed_eur` = reservations plus settlements, `pct` = consumed / effective envelope. Policy thresholds use `pct` and need no change.
**Status.** verified (function replaced live on SERVER; whoami shows a positive utilisation).

## PD-38 — The sessions that built this PoC were not governed by it

**Problem.** Every document, file and deployment step in this repository was produced by Claude Code running inside the Claude desktop app, signed in with the owner's Anthropic account. Those sessions did not pass through the gateway: the desktop app sends its own OAuth token directly to Anthropic's API (observed in PD-35), so the managed settings do not apply to it. No DLP, classification, budget metering or audit event covered them. The sessions also ran with the operator's full privileges: SSH key to SERVER, Docker engine there, git push to GitHub, sudo commands handed to the operator. The only control was the desktop app's per-command permission prompt, which the operator used.
**Why it matters.** This is the PD-07 case in practice, inside the project that documents it. SERVER's `.env` (passwords, but not the Anthropic key, which was never printed), tailnet addresses and the Windows user name went to Anthropic under a consumer agreement. For a PoC on synthetic data with an informed operator this is acceptable; for a real repository it is exactly what the rules forbid.
**Fixes considered.** (a) Route desktop-app sessions through the gateway: not possible today, the app keeps its own login; terminal `claude` is governed via managed settings. (b) Build inside the SERVER sandbox with a delegated identity, where SSH keys, Docker and push to main do not exist. (c) Accept and record for the PoC phase; require (b) or a governed terminal session from Tier 2 onward.
**Decision.** (c) now; (b) for any work touching a non-synthetic repository. Rotate the SERVER `.env` passwords before the stack holds anything but demo data. Add "desktop-app sessions bypass the gateway" to the AI Acceptable Use Policy draft and to the vendor assessment of the desktop app.
**Pros.** Honest record; the register can be shown to an auditor as written by the process it describes. **Cons.** The PoC's own provenance does not meet the PoC's own bar.
**Applied in.** This entry; the AUP line is in docs/10 §4 (draft). Password rotation stays open until the stack holds anything but demo data.
**Status.** open (owner: CISO; rotation before real data).

## PD-39 — This repository governs its own changes first

**Problem.** Tier 2 was scoped around a separate parcel application, which needs an organisation, a second account, Supabase stacks and a runner on SERVER before anything can be shown. Meanwhile this repository, whose every commit is AI-assisted (PD-38), had no checks at all and was pushed to directly.
**Fixes considered.** Wait for the full Tier 2 scope; or turn Gate 1 on here with GitHub-hosted runners, since none of this repository's checks need SERVER.
**Decision.** Gate 1 on this repository now: `ci.yml`, PR template, CODEOWNERS, `main` ruleset with required status checks, pull requests only, no bypass actors. The first PR through it passed and was merged by a human. Limits accepted for now: required approvals = 0 and no signature requirement, because there is a single human account and an unsigned history; a required review would block every change. When the second account exists: approvals = 1, code-owner review, signed commits, merge queue, and the `ai-label` check gains the gateway telemetry cross-check (PD-15).
**Pros.** The pipeline documents are now exercised by a real repository every day; the AI-assisted label and checklist apply to the project's own work. **Cons.** The human-review gate is not yet enforceable here; the merge-queue signature design is unexercised until an application repository exists.
**Applied in.** `.github/` in this repository; docs/08 §5.1; README.
**Status.** applied.

## PD-40 — parcel-app backend: Supabase's core rather than the full bundle

**Problem.** §10.6 planned three Supabase self-host stacks on SERVER. The official bundle is twelve services per environment (Kong, GoTrue, PostgREST, Realtime, Storage, Studio, meta, analytics, vector, pooler, functions, Postgres) and its download into this session was declined; for the proofs we need only the data API with row-level security.
**Fixes considered.** Full bundle per environment; Supabase cloud in an EU region (loses "production on our hardware"); PostgreSQL + PostgREST per environment with a JWT-minting stand-in for Auth.
**Decision.** PostgreSQL 16 + PostgREST per environment. Migrations are Supabase-format; the RLS helpers read `request.jwt.claims` exactly as under Supabase; JWTs carry `role`, `sub`, `app_metadata.role`. `tests/api_test.sh` proves the role views through HTTP (11 checks). Full Supabase stays a later configuration change.
**Pros.** Two containers instead of twelve; every control is visible; nothing downloaded that was not reviewed. **Cons.** No Auth, Storage or Studio in the PoC; the frontend will mint sessions through the stand-in until Auth is added.
**Found on the way.** The masking script cut the customer account link (fixed: `actor_id` kept); the customer tracking view needed a column-level grant on `stop`, which the SQL test had hidden because `count(*)` let the planner prune the subquery (fixed, test extended); PostgREST answers 403 for a role without a grant and 401 only without a token.
**Applied in.** `parcel-app` PR 1; this repository: Caddy route `preview-api.<domain>` and docs/07 §10.6.
**Status.** applied.

## PD-41 — No money in the PoC: the EU-region external endpoint is out of scope

**Problem.** The audit (docs/11, gap 1) ranks the US Anthropic endpoint under exception as the first thing to fix for guardrails G2 and G8. Closing it needs an EU-region provider endpoint (Bedrock or Vertex AI in an EU region), which needs a cloud account and incurs spend.
**Decision (owner, 2026-10-21).** The PoC runs with no cloud account and no money. The EU-region endpoint is therefore out of scope for the replica and becomes a transfer-time item for the client's own accounts. Whether to keep the US exception for demos or revoke it and run INTERNAL work on the self-hosted tier only is deferred; tracked as issue #19, assigned to the owner, to be decided before the demo runbook is finalised. Decided the same day in PD-43: revoked, no exception.
**Pros.** Honest scope; the registry already proves the mechanism (an approved non-EU endpoint cannot exist). **Cons.** The two Highest guardrails cannot be shown fully closed in the replica; the demo Q&A must say so.
**Status.** decided.

## PD-42 — GitHub Issues as the ticket system

**Problem.** The brief's working rule "every change traceable to a ticket" scored Missing in docs/11.
**Decision (owner, 2026-10-21).** GitHub Issues on both repositories. One issue per ranked gap (#6–#18) and one decision issue (#19). A `ticket` job in both CI workflows fails a PR whose title or description does not reference an issue (`#n` or `owner/repo#n`), and the rulesets require it. The PR template carries a `Ticket:` line.
**Pros.** Zero cost; the reference is enforced, not requested. **Cons.** A reference is not a justification; review still has to check that the PR does what the issue says.
**Status.** applied.

## PD-43 — EU only, no exception: the US endpoint is revoked

**Problem.** Issue #19 (from PD-41): keep or revoke the 72-hour `model_enable` exception that let the replica send INTERNAL work to the provider's US endpoint. It contradicted G2 and G8 (docs/11 gap 1), and `demo-reset` renewed it on every reset, so in practice it never expired.
**Fixes considered.** (a) Keep it for demos and disclose it in Q&A. (b) Revoke it and run all model work on the self-hosted tier. (c) Revoke it and add a declared EU stand-in tier (the mock on SERVER) so that reroute, ceiling and exception paths keep end-to-end scenarios.
**Thought process.** (a) asks the client's PO to accept the very thing the highest guardrail forbids. (c) keeps better demo coverage but adds a tier that exists only to be shown. (b) is the honest floor; (c) can be added later if the owner wants it.
**Decision (owner, 2026-10-21).** (b): "No exception. Everything must stay in the EU." Applied as: the exception closed and every non-EU endpoint revoked (`stack/schema/020_eu_only.sql`); the schema admits a non-EU endpoint only as `revoked`; policy blocks `NON_EU_ENDPOINT` before status or exceptions are read, and no exception applies to a non-EU endpoint; the gateway has no external adapter and its default alias is `code-local`; the egress allowlist is empty and the proxy is detached from `egress-net`; `demo-reset` no longer touches exceptions; the self-hosted tier carries a placeholder internal chargeback (1.00 / 5.00 EUR per 1M input/output tokens), because at 0 EUR the budget guardrail would bound nothing; Claude Code's managed settings disable non-essential traffic. New checks: S4b (the response names `agl/code-local`), and the negatives S25b, S27, S28 and S29 (self-hosted model stopped → `BACKEND_ERROR`, no fallback); the CI schema job checks the registry side. S29 found that an unreachable backend raised an unhandled error (500, budget reservation left open); it is now a `BackendError` (502, reservation released).
**Pros.** G2's open violation is gone and three independent layers refuse it (schema, policy, network). No external spend. G8 holds for every call (the self-hosted tier retains nothing).
**Cons.** Claude Code through the gateway now runs on the 7B local model, which is much weaker. Reroute, `CLASSIFICATION_CEILING` and the `model_enable` path are covered by OPA unit tests only, with no end-to-end scenario (option c would restore that). S4 is now close to S5: it proves the default path, not a reroute. The chargeback rate is a placeholder, not a measured cost.
**Scope (open, asked of the owner).** Applied to governed model inference. Still outside the EU or under US jurisdiction: GitHub.com and GitHub-hosted runners (PD-39), Tailscale coordination, public image and package registries (gap 8, #13), the Claude desktop app (PD-38), and the AI assistant used to build this PoC. `eu_residency` means processing location: `EU_REGION_HYPERSCALER` providers have US parents, which a jurisdiction reading of "EU only" would exclude (provider `parent_country` is not yet a policy input). Vercel is no longer used (owner, 2026-10-21); the PaaS pipeline examples and docs/07 §10.6 still describe it and need their own change.
**Open.** (1) The revocation is SQL, so the hash chain has no `registry_change` event for it (the G9 gap); a gateway admin path that appends one should run on SERVER together with the migration. (2) Look back, recorded 2026-10-21 after applying the migration on SERVER: **44 completions** went to the US endpoint between 2026-10-20 11:03 UTC and 2026-10-21 14:44 UTC, total €0.1855 at list price, all on synthetic prompts (scenario suite, chat tests, Claude Code probes). The provider row says `zero_retention = false`; a deletion request is the owner's call (no real data was involved). (3) Owner: remove `ANTHROPIC_API_KEY` from SERVER's `stack/.env` and revoke the key in the provider console. (4) Owner: apply on SERVER (020 migration, rebuild `gateway` and `egress-proxy`, `make demo-server`). (5) docs/07 §10.5 says a Mac firewall or exit-node rule blocks the provider host; nothing in the repository sets one.
**Applied in.** Branch `policy/eu-only` (issue #19).
**Status.** applied on SERVER 2026-10-21: migration `020_eu_only.sql` run on the live database (exception `closed`, `code-default` → `revoked`, chargeback price active), Anthropic key removed from `stack/.env` by the owner, stack rebuilt from `main` with the proxy detached from `egress-net`. Open: (1) the `registry_change` event for the revocation. (3) Deletion request: not applicable, owner decision 2026-10-21 on issue #19 (synthetic prompts only; the procedure is exercised at transfer with the client's provider).

## PD-44 — Vercel removed: the parcel frontend runs only on SERVER

**Problem.** PD-19 put the parcel frontend on Vercel; PD-21 moved it to Docker on SERVER first but kept the Vercel workflows as a dormant variant. On 2026-10-21 the owner stated that Vercel is no longer used, and PD-43 requires everything to stay in the EU. Issue #22.
**Why it matters.** Vercel is a US platform that would receive the frontend source, the bundle and the build logs. A dormant variant is still a documented one-switch path out of the EU, and the PaaS workflows had no other deploy target.
**Fixes considered.** (a) Static export built once, one static web container per environment on SERVER behind Caddy, deployed with `make web-deploy` and rolled back with `make web-rollback`. (b) A Node container image built once and promoted by digest through a registry on SERVER. (c) Keep Vercel dormant.
**Thought process.** (c) contradicts PD-43 and the owner's statement. (b) adds a registry service to run (GHCR is outside the EU) for no proof that (a) lacks. (a) keeps the docs/08 invariants: one build, one hash, a release signature only from the merge queue, the same digest promoted to preview, staging and production; the backend URL lives in a per-environment `config.json` outside the bundle.
**Decision (owner, 2026-10-21).** (a). Each web container serves its environment's web volume read-only (`current/` → `releases/<digest>/`, plus `config.json`). Write access is the environment secret `WEB_DEPLOY_KEY`, an SSH key whose forced command runs only `web-deploy` and `web-rollback` for that environment, so the frontend has the same two factors as the database URLs: an environment secret and a runner that can route there. The Vercel frontend of PD-19 and the dormant variant of PD-21 are superseded; those entries stay as history.
**Pros.** No hosting account outside SERVER and no deploy token held by a third party; a rollback is a pointer switch to a digest that was already verified. **Cons.** One preview at a time, as the preview backend already was; concurrent PRs overwrite each other's preview and are serialised by hand. The prebuilt artifact still passes through GitHub Actions artifact storage, like the source code (PD-16, PD-18). The web containers, their Caddy routes, the `WEB_DEPLOY_KEY` endpoint and the `web-build` / `web-deploy` / `web-rollback` targets do not exist yet; they come with the frontend in `parcel-app`.
**Applied in.** `pipeline/.github/workflows/merge-candidate-paas.yml` and `release-paas.yml` (Vercel CLI and `VERCEL_*` secrets and variables replaced by `make web-build`, `web-deploy`, `web-rollback` with `WEB_DEPLOY_KEY`; the rollback audit event now carries the digest); `pipeline/README.md`; PoC §10.3 Tier 2 table, §10.6, §10.7; `.gitignore` here and in `parcel-app` (`.vercel/` removed). actionlint passes.
**Status.** applied.

## PD-45 — Parcel frontend hosting: an SSH forced command is the only writer

**Problem.** PD-44 named `make web-deploy`, `make web-rollback` and the secret `WEB_DEPLOY_KEY`, but nothing implemented them. Issue #25; the owner asked for the containers, the deploy service, the make targets and the Caddy routes, tested with a placeholder page, nothing on SERVER.
**Fixes considered.** (a) Mount each environment's web volume into the runner containers. (b) An HTTP upload endpoint with a bearer token. (c) A `web-deploy` container per environment: sshd with one ed25519 key and a forced command that can only deploy, roll back or report, on the stack network.
**Thought process.** (a) gives every job on the `server` runner, PR code included, write access to staging without any secret, losing the environment scoping PD-11 and PD-12 rely on. (b) is custom code in the most sensitive path. (c) is standard tooling, keeps the key an environment secret, and the network still lets only `server-release` reach production.
**Decision.** (c). Before extracting, the forced command checks the received artifact against the digest and refuses links, absolute or `../` member paths, and artifacts without `index.html`. It unpacks into `releases/<hex>/`, writes `config.json` (an https backend URL only) and switches `current` with one rename; `previous` keeps the last release for rollback. One lock serialises deploys. The client pins the host key under the alias `web-deploy-<env>` and refuses an environment with no pinned key. The web container is Caddy on a read-only root filesystem with the volume mounted read-only.
**Found on the way.** The AGL managed settings on the owner's Mac (`deploy/server/managed-settings.json`) deny `docker` and `curl` to Claude Code, so the session that wrote the container test could not run it, and did not route around the rule. The test runs as the `web-test` job in parcel-app CI and as `make web-test` for a human. Busybox `mv` and `tar` differ from GNU on replacing a symlink and on stripping member names, so the deploy image installs GNU coreutils, tar and findutils.
**Pros.** Each key opens one environment and can do three things; nothing is published on a port; the refusals are tested, not assumed. **Cons.** A key per environment for the owner to create and rotate; the image is built from Alpine 3.20 packages pulled at build time; rollback toggles between the last two releases only.
**Applied in.** `parcel-app` (`deploy/web/`, compose services `web` and `web-deploy`, `scripts/web-remote.sh`, make targets, `tests/web_test.sh`, CI job `web-test`); this repository: Caddy routes `preview.parcel`, `staging.parcel` and `parcel.<domain>` (`caddy validate` passes), PoC §10.6.
**Status.** applied.

---

## PD-46 — Sandboxes shared the governance network

**Problem.** Probing from a live sandbox on SERVER (the owner asked why parcel-app is quarantined; the sandbox is the G4 evidence) showed the sandbox could open TCP connections to `postgres:5432`, `minio:9000`, `opa:8181` and `egress-proxy:3128`, because `agl sandbox new` started it on `agl_agl-net`. The design (docs/02 §7, docs/07 §10.1) says a sandbox reaches the gateway and the package mirror only. Through the proxy, a developer's own API key would have bypassed DLP, budget and audit while the proxy still had a way out (before PD-43). Issue #26. (Numbered PD-45 in PR #27; renumbered after a merge collision with the frontend entry.)
**Negative observation (before, 2026-10-21):**
```
gateway:8000 REACHABLE · postgres:5432 REACHABLE · minio:9000 REACHABLE · opa:8181 REACHABLE · egress-proxy:3128 REACHABLE
parcel-preview-api-1:3000 blocked · 100.109.138.14:4000 blocked · 1.1.1.1:443 blocked
```
**Decision.** A dedicated `internal` network `agl_sandbox-net`; the gateway is attached to it as a second network with its service alias; sandboxes start there. Nothing else joins it. The package mirror (gap 8, #13) will be the second member when it exists.
**Positive observation (after, same day, same probe):**
```
gateway:8000 REACHABLE · everything else blocked (name resolution fails: the services do not exist on that network)
```
**Pros.** The G4 property holds at the network layer, not only by the absence of credentials; the probe is a reusable isolation test. **Cons.** A manual `docker network connect` loses the service alias and a hand-made network lacks compose's labels, so only `compose up` from `main` makes it permanent (done on SERVER 2026-10-21).
**Applied in.** `stack/docker-compose.yml`, `stack/cli/agl`. Verified on SERVER after `compose up` from `main`.
**Status.** verified.

## PD-47 — A gateway restart left events out of the WORM store

**Problem.** The first scenario run with run correlation failed S12a: the verifier found a broken link at one event (content intact, `prev_hash` not matching the previous WORM event). Cause: the gateway was rebuilt several times that day; events still in the open in-memory segment were in the hot copy (Postgres) but never written to MinIO. Three events (seq 210–212) existed only in the hot copy.
**Negative observation (2026-10-21):** `verify` → `result: fail`, `broken_links: [{index: 209, prev_link_ok: false, content_hash_ok: true}]`; `select count(*) from audit_event e where not exists (select 1 from audit_segment s where s.id = e.segment_id)` → 3.
**Decision.** Two changes: the gateway flushes the open segment on shutdown (uvicorn shutdown hook), and at startup it re-emits any hot-copy events without a segment, in chain order, as WORM segments, then appends an `audit_recovery` event naming them. The hot copy is not the source of truth, but it is a durable buffer, so nothing is lost as long as Postgres survives; the production design adds a write-ahead to the object store before acknowledging the request.
**Positive observation:** after the rebuild with the fix, orphan count 0, `verify` passes over the full chain, and the recovery event is itself in the chain.
**Pros.** Restarts no longer create gaps; the gap that existed is closed with a recorded explanation rather than silently. **Cons.** Between an event's insert and the next flush, a hard crash of both the gateway and Postgres would lose it; the write-ahead above is the Phase 1 answer.
**Applied in.** `stack/gateway/app/audit.py`, `main.py` (PR #32).
**Status.** verified.

## Template for new entries

```
## PD-xx — Title

**Problem.**
**Why it matters.**
**Fixes considered.**
**Thought process.**
**Decision.**
**Pros.** **Cons.**
**Applied in.**
**Status.**
```
