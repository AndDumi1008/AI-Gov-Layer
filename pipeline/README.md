# pipeline/ — example delivery pipeline files

Companion to [docs/08-delivery-pipeline.md](../docs/08-delivery-pipeline.md). Two release variants: **container/GitOps** (`merge-candidate.yml`, `release.yml`, `admission/`) and **PaaS** for the parcel app on self-hosted Supabase + Vercel (`merge-candidate-paas.yml`, `release-paas.yml`, see docs/07 §10.6). Stack-agnostic: workflows call `make lint`, `make build`, `make test`, `make db-*`, `make preview-up`, `make e2e`, `make contract-tests`, `make staging-soak`; each repository supplies those targets.

| Path | Role |
|------|------|
| `.github/workflows/pr-checks.yml` | Gate 1: env-vars, secrets, lint, compile, test, dependencies, iac-policy, ai-label. Runs on the merge commit and in the merge queue |
| `.github/workflows/merge-candidate.yml` | Gate 2: build once, SBOM, cosign sign, provenance, migrations on current schema, preview env (main + PR), smoke/e2e, N-1 contract tests, audit evidence |
| `.github/workflows/merge-candidate-paas.yml` | Gate 2 for the Supabase + Vercel app: `vercel build` once → prebuilt artifact hashed and (merge queue only) cosign-signed as a blob; preview Supabase stack reset + migrations + expand/contract; Vercel preview deployment; e2e; N-1; audit evidence |
| `.github/workflows/release-paas.yml` | Release for the Supabase + Vercel app: finds the merge-queue run for main's commit, downloads its artifact, verifies the blob signature by workflow/trigger/SHA and refuses preview markers; staging migrate + alias + soak; release candidate record with migration checksums; production behind human approval on the `server-release` runner (checksum compare, `supabase db push`, functions, `vercel --prod`); frontend rollback via dispatch |
| `.github/workflows/release.yml` | Verify signature, staging auto-promote + soak, release candidate record, production behind human environment approval, GitOps commit, audit event |
| `scripts/check-env-vars.sh` | Env-var rules (declared-or-nonexistent, no `.env`, no secret defaults, placeholders only in `.env.example`) |
| `.github/CODEOWNERS` | Second human for sensitive paths |
| `.github/pull_request_template.md` | Continuity + AI-assisted checklist (ticked boxes are enforced by the `ai-label` check) |
| `admission/kyverno-verify-images.yaml` | Production admission: only images signed by `merge-candidate.yml` on a `merge_group` run, with SLSA provenance, are admitted (PD-10) |
| `rulesets/main.json` | Branch ruleset for `main`: signatures, linear history, 1+ human review, code owners, strict status checks, merge queue. Import with `gh api repos/{owner}/{repo}/rulesets --input rulesets/main.json` |

Not included, configured in the GitHub UI or via Terraform:

- `production` environment: **required reviewers = humans only**, deployment branch policy `main`, and the GitHub App credentials (`GITOPS_APP_ID`, `GITOPS_APP_PRIVATE_KEY`) as **environment secrets** so they exist only after approval (PD-12).
- `staging` environment: no reviewers; its own App credentials as environment secrets.
- `preview` environment: no reviewers; cloud credentials scoped to the preview cluster/namespace only; the cloud OIDC trust policy requires the `environment:preview` claim (PD-11).
- Repository setting "allow GitHub Actions to approve pull requests" = **off**.
- The `gitops` repository: branch protection allowing the GitHub App to push only digest bumps under `envs/*/kustomization.yaml` (PD-12).
- Public repositories (PD-20): set "Fork pull request workflows → Require approval for all outside collaborators". `runs-on` sends fork PRs to `ubuntu-latest` and preview jobs are skipped for forks, so nothing from a fork executes on the self-hosted runner.
- Ephemeral runners for PR-triggered workflows (PD-11); location per PD-16. PaaS production jobs read `AGL_RELEASE_RUNNER` (`server-release`), the only runner with a route into `prod-net`.
- PaaS variant: `preview` environment secrets `PREVIEW_DB_URL`, `VERCEL_TOKEN`; `staging`: `STAGING_DB_URL`, `VERCEL_TOKEN`; `production`: `PROD_DB_URL`, `VERCEL_TOKEN`; repository variables `VERCEL_ORG_ID`, `VERCEL_PROJECT_ID`. Vercel's Git integration is disabled for production. Make targets: `preview-db-reset`, `db-compat-check`, `functions-deploy`, `e2e`, `contract-tests`, `staging-soak`. `runs-on` reads the repository variable `AGL_RUNNER` (set to `server` for the PoC's self-hosted runner on SERVER) and falls back to `ubuntu-latest`.
- The AGL audit API verifies GitHub OIDC tokens (issuer, repository, workflow, ref) on `POST /events` (PD-13).

Security properties of the workflows as written:

- PR-triggered jobs run with a read-only token; only `ai-label` (no PR code executed) and `preview` (environment-scoped) have write permissions.
- A release signature exists only for `merge_group` runs; PR builds carry a preview attestation the release and the cluster never accept.
- The release derives the digest from main's commit and verifies the certificate's repository, workflow, trigger and SHA; there is no digest input.
- All `uses:` references are pinned to commit SHAs by `ratchet` (the trailing `# ratchet:owner/action@vN` comment lets `ratchet update` refresh them).
