# 08 — Delivery Pipeline: from local AI-assisted code to a released production

**Project:** AI Governance Layer (AGL)
**Status:** Draft v0.1
**Date:** 2026-10-19
**Related:** [02 TRD §5–6](02-technical-requirements.md) · [03 App Flows F-06, F-07](03-app-flows.md) · [07 PoC](07-poc-requirements.md) · example files in [`pipeline/`](../pipeline/)

---

## 1. The path in one picture

```mermaid
flowchart LR
  L[Laptop<br/>developer + Claude Code<br/>no prod credentials] -->|signed commits<br/>AI-Assisted trailer| PR[Pull request]
  PR --> G1[Gate 1 · PR checks<br/>env-var scan · secrets · lint · compile · tests<br/>run on the MERGE COMMIT of main + PR]
  G1 --> G2[Gate 2 · Merge candidate<br/>build once · sign · SBOM · provenance<br/>deploy preview = main + PR<br/>smoke + compatibility tests]
  G2 --> H1{Human review<br/>≠ author}
  H1 -->|approve| MQ[Merge queue<br/>re-runs Gate 1 on final merge]
  MQ --> MAIN[(main)]
  MAIN --> STG[Staging<br/>auto-promote same digest]
  STG --> H2{Human release approval<br/>protected environment}
  H2 -->|approve| GO[GitOps commit<br/>digest bump]
  GO --> ADM{Admission<br/>signature + provenance}
  ADM --> PROD[(Production)]
  G1 & G2 & MQ & H2 & ADM --> AUD[(Audit chain)]
  classDef prod fill:#fdd,stroke:#c00; class PROD prod
```

Two humans, two places: one approves the change (PR), one approves the release (environment). They may be the same person for small teams, but never the author.

## 2. Stage by stage

### Stage 0 — On the laptop

| What | Rule |
|------|------|
| AI tooling | Claude Code or similar is allowed locally. Model calls go through the AGL gateway (base URL in managed settings), so DLP, budget, residency and audit apply to prompts |
| Credentials | No standing production credentials on the machine. Cloud access is SSO with short-lived tokens for non-prod only. Production is reached only through the privileged access system, never from a shell where an agent runs |
| Commits | Signed by the developer (SSH/GPG/gitsign). AI-assisted commits carry the trailer `AI-Assisted: claude-code` |
| Pre-commit | gitleaks and the env-var check run locally as a convenience, not as the control; the control is CI |
| Data | Local dev uses the masked dataset from the catalog; `.env` is git-ignored; `.env.example` lists every variable with a placeholder |

Nothing on the laptop is trusted by the pipeline. Everything is re-checked in CI.

### Stage 1 — Gate 1: PR checks (automatic, required status checks)

Runs on the **merge commit** (`refs/pull/N/merge`), which is what GitHub's `pull_request` event checks out: the result of merging the PR into the current `main`. That is the "tested against the current version" guarantee. If `main` moves, the check is stale and the ruleset requires it to re-run (strict status checks / "require branches to be up to date").

| Check | Fails when | Tool in the example |
|-------|-----------|---------------------|
| `env-vars` | A variable is read in code but not declared in `.env.example`; a `.env` file is committed; a secret-looking literal is assigned in code; a secret has a default value in code | `pipeline/scripts/check-env-vars.sh` |
| `secrets` | Any credential pattern in the diff or history of the branch | gitleaks |
| `lint` | Linter errors (warnings allowed but reported) | `make lint` |
| `compile` | Build/type-check fails | `make build` |
| `test` | Unit and integration tests fail; coverage drops below the repo threshold | `make test` |
| `ai-label` | Commits carry the AI trailer but the PR lacks the `ai-assisted` label (auto-added), or the PR template checklist is unticked | labeler step |
| `dependencies` | New dependency not in the private registry allowlist, known vulnerability above threshold, disallowed licence | SCA (Trivy/Grype/OSV) + allowlist |
| `iac-policy` | Terraform/Kubernetes manifests violate OPA/conftest rules (e.g. a sandbox pod with secrets, a prod route from non-prod) | conftest |

### Stage 2 — Gate 2: Merge candidate (automatic)

Purpose: prove that **main + this PR is a working system before any human spends review time on it**, and produce the exact artifact that will later ship.

1. Build the container image once from the merge commit. Tag with the merge commit SHA; record the digest.
2. Generate SBOM, sign with cosign (keyless, CI OIDC identity), attach SLSA provenance.
3. Apply database migrations against a fresh copy of the **current** schema (masked snapshot), forward only; fail if a migration is not backward compatible with the running version (expand/contract rule).
4. Deploy an ephemeral preview environment `pr-N` from the digest, with masked data and non-prod configuration.
5. Run smoke and end-to-end tests against the preview. Run the **previous** release's API contract tests against the new server (N-1 compatibility).
6. Post a comment on the PR with the preview URL, test summary, SBOM diff, image digest.
7. Tear down the preview when the PR closes.

### Stage 3 — Human review of the change

Ruleset on `main`: no direct push, signed commits, linear history, required checks from Gates 1 and 2, at least one approval from a human who is not the author, CODEOWNERS approval for sensitive paths, dismiss stale approvals on new commits, bot approvals do not count, merge only via merge queue.

The reviewer sees the preview, the checks and the AI-assisted checklist. Approval is the first human-in-the-loop point.

### Stage 4 — Merge queue → main

The queue builds the final merge result (other PRs may have landed since Gate 2) and re-runs Gate 1. On success it merges. The `merge_event` with reviewers, check results and artifact digest goes to the audit chain.

### Stage 5 — Release preparation (automatic)

- The same digest that passed Gate 2 is promoted, never rebuilt. If the merge queue produced a different merge commit, Gate 2 is rerun by the queue and the new digest is the candidate.
- Staging is updated automatically by a GitOps commit (digest bump) made by the CI identity.
- Release notes are drafted from PR titles and labels; `ai-assisted` PRs are listed separately so the release approver sees the share.
- A release candidate record is written: version, digest, provenance, SBOM, test evidence, staging soak result.

### Stage 6 — Human release approval

Production is a **protected environment** with required reviewers (humans from the service-owning team; CI identity and bots are not eligible). The approver sees the release candidate record and the staging soak. Approval is the second human-in-the-loop point. The approval, approver and digest go to the audit chain as `deploy_event`.

### Stage 7 — Production rollout

- The release workflow commits the digest bump to the production GitOps repository. The GitOps controller is the only writer to production clusters.
- Admission control verifies signature and provenance from the allowed CI identity before a pod starts.
- Progressive rollout (canary or blue/green) with automatic rollback to the previous digest on SLO breach. Rollback is a pre-approved runbook and is logged.
- No AI identity, bot or workflow can approve the environment or write to production directly; the only path is the human-approved GitOps commit.

## 3. "Tested against the current version": what it actually means

| Risk | Control |
|------|---------|
| PR passes on its own branch but breaks when merged | Checks run on the merge commit; ruleset requires branches up to date; merge queue re-runs on the final merge |
| Schema change breaks the running version during rollout | Migrations must be expand/contract: new version runs against old schema and new schema; migration dry-run against masked snapshot of the current schema |
| API change breaks existing clients | Previous release's contract tests run against the new server in the preview |
| Config drift between preview and production | Same image digest, same Helm/Kustomize base, environment-specific values only; env-var check guarantees every variable is declared |
| Works on one PR, fails with another landed meanwhile | Merge queue serialises; Gate 1 reruns on the queue's merge result |

## 4. Env-var and secret checks, precisely

The `env-vars` check enforces four rules:

1. **Declared or it does not exist.** Every variable read in code (`process.env.X`, `os.environ["X"]`, `os.Getenv("X")`, `${X}` in manifests, `env.X` in workflows) must appear in `.env.example` or in the config schema file. Prevents a variable that exists only on one developer's machine.
2. **No `.env` in the repository.** The file is ignored; its presence in the tree fails the check.
3. **No secrets with defaults.** A variable whose name matches `*_SECRET|*_TOKEN|*_PASSWORD|*_KEY|*_DSN` must not have a fallback value in code (`|| "..."`, `.get("X", "...")`). A missing secret must fail loudly at startup, not silently use a default.
4. **No production identifiers in code.** Hostnames, bucket names, account IDs tagged as production in the inventory must not appear in source or fixtures.

Secrets scanning (gitleaks) runs separately on the full branch history so a secret committed and then removed is still caught.

## 5. What the laptop change means for the governance claims

Allowing local Claude Code shifts enforcement from the sandbox to two places:

- **The gateway** still governs every model call (residency, DLP, budget, audit), because the CLI's base URL is set by managed settings and direct vendor endpoints are blocked at egress.
- **The pipeline** governs everything the agent produces, because nothing reaches `main` or production except through Gates 1–2, a human reviewer and a human release approver.

What the laptop does **not** give you is a delegated agent identity or a step cap, so two conditions must hold on the machine: no production credentials, and the masked dataset only. Those are enforced by the privileged access system and by the dataset catalog, not by the agent configuration. The sandbox orchestrator from the TRD remains the path for long-running or autonomous agent sessions.

## 6. Example files

Everything in [`pipeline/`](../pipeline/) is stack-agnostic: it calls `make lint`, `make build`, `make test` so each repository supplies its own targets.

| File | Purpose |
|------|---------|
| `.github/workflows/pr-checks.yml` | Gate 1 |
| `.github/workflows/merge-candidate.yml` | Gate 2: build once, sign, preview, compatibility tests |
| `.github/workflows/release.yml` | Staging auto-promote, production behind environment approval, GitOps commit |
| `scripts/check-env-vars.sh` | Env-var rules 1–3 |
| `.github/CODEOWNERS` | Sensitive paths |
| `.github/pull_request_template.md` | AI-assisted checklist |
| `rulesets/main.json` | Branch ruleset for `main` to import via the GitHub API |
| `admission/kyverno-verify-images.yaml` | Production admission policy bound to the merge-queue signature |

Action references are pinned to commit SHAs (via `ratchet`). Security hardening applied to the examples is recorded in the Problem & Decision Register as PD-10 to PD-13 and PD-17.
