# 04 — Design Brief

**Project:** AI Governance Layer (AGL) — Admin Console and developer touchpoints
**Status:** Draft v0.1
**Date:** 2026-10-19
**Related:** [01 PRD](01-product-requirements.md) · [03 App Flows](03-app-flows.md)

---

## 1. What we are designing

AGL is mostly invisible infrastructure. The parts people *see* are:

1. **In-tool feedback** — the messages a developer gets inside the IDE/CLI when something is warned or blocked.
2. **Admin Console** — a web application for team leads, security, DPO, finance and auditors.
3. **PR surface** — labels, checklists and status checks inside the Git hosting UI.
4. **Notifications** — budget thresholds, DLP alerts, exception approvals in chat/email.

The brief covers tone, principles, information architecture, key screens and accessibility. Visual identity follows the company's existing internal design system; this brief defines what is specific to AGL.

## 2. Audiences and their one job

| Audience | Comes to AGL to… | Frequency |
|----------|------------------|-----------|
| Developer | understand why a request was blocked and fix it fast | rare, under stress |
| Team lead | see spend and approve things | weekly |
| Security admin | manage registry/policy, investigate | daily |
| DPO | answer "did personal data go where?" | monthly / on request |
| Finance | close the month, allocate cost | monthly |
| Auditor | sample and verify evidence | quarterly / annually |

## 3. Design principles

1. **Explain, don't scold.** Every block states *what type* of issue, *why it matters in one line*, and *what to do next*. Never show the matched secret or personal data.
2. **Evidence first.** Every number on a dashboard links to the immutable events behind it. Auditors should never ask "where does this come from?".
3. **Boring by default.** Governance UI should feel like a well-kept ledger: dense, calm, predictable. No gamification, no AI-themed decoration.
4. **Fast path for the common case.** A top-up approval or a false-positive flag is two clicks.
5. **Separation of duties visible.** Where two approvals are needed, the UI shows both slots and who may fill them.
6. **Residency visible.** Region and provider are always shown next to a model name. Non-EU is never an option in a dropdown; it does not exist in the UI.
7. **Accessible.** WCAG 2.2 AA; keyboard-complete; no colour-only status.

## 4. Tone of voice

- Plain, direct, neutral. Second person for the developer ("Your request was blocked because…").
- Reason codes shown as short labels (`SECRET_DETECTED`) *and* human text. The code is for search and support; the text is for the person.
- No blame language ("violation", "offender"). Use "blocked", "not sent", "needs approval".

**Example in-band messages**

| Situation | Message |
|-----------|---------|
| Secret | **Blocked — a credential pattern (AWS access key) was found in your prompt.** Remove it or replace it with a placeholder such as `<AWS_KEY>`. If this key is real, rotate it now: <runbook link>. Ref `SECRET_DETECTED` · event `evt_…` |
| Personal data | **Blocked — personal data was found in your prompt (2 email addresses, 1 phone number), so nothing was sent.** Remove it or use a placeholder such as `<EMAIL>`; your own address and test domains (example.com, *.test) are fine. Ref `PII_DETECTED` |
| Client scope | **Client accounts can ask product questions only.** Ask what the platform does today, or list everything with `/features`. Ref `CLIENT_SCOPE` |
| Stored | Chip on every answer: **prompt stored 30d** (content store; reading it takes two people, and every read is logged). |
| Store down | **Blocked — the prompt could not be stored, so it was not sent.** Ref `GOVERNANCE_UNAVAILABLE` |
| Ceiling | **Blocked — this repository is classified CONFIDENTIAL; model `gpt-x (Azure, Sweden Central)` is approved up to INTERNAL.** Use `mistral-y (EU, zero-retention)` or ask security about the classification. Ref `CLASSIFICATION_CEILING` |
| Budget | **Blocked — your team's October AI budget is used up (€4,000 / €4,000).** Your team lead can request a top-up: <link>. Ref `BUDGET_EXHAUSTED` |
| Budget warning | **Note: your team has used 85 % of this month's AI budget.** |
| Governance down | **Blocked — the AI governance service is unavailable, so requests are paused for safety.** Status: <link>. Ref `GOVERNANCE_UNAVAILABLE` |

## 5. Information architecture — Admin Console

```
AGL Console
├── Overview            (today: requests, spend vs envelope, blocks, provider health)
├── Spend
│   ├── By cost centre / team / project / person
│   ├── By model / provider
│   ├── Budgets & envelopes (edit, thresholds)
│   └── Top-up requests (queue, approve/reject)
├── Usage
│   ├── Requests explorer (filter, drill to event)
│   └── Agent sessions (sandbox runs, actions)
├── Decisions
│   ├── Blocks (by reason code, trend) and DLP exemptions (own address, test data)
│   └── False-positive flags (queue)
├── Models & Vendors
│   ├── Registry (status, region, ceiling, review date)
│   ├── Vendor assessments
│   └── SaaS-embedded AI inventory
├── Policy
│   ├── Active bundle (digest, since)
│   ├── Change history (links to Git)
│   └── Replay / impact preview
├── Exceptions
│   ├── Open / approve
│   └── History
├── Audit
│   ├── Event search (hot copy)
│   ├── Chain verification (run, history)
│   └── Evidence export
├── Change governance
│   ├── Merges (ai-assisted share, review stats)
│   ├── Deployments (approver, artifact, provenance)
│   └── Isolation tests
└── Settings
    ├── Roles & access
    ├── Notifications
    └── Retention
```

Role-based visibility: developers see only their own requests and their team's budget status; team leads see their team; security/DPO/auditor see all with read-only for auditors; finance sees Spend only.

## 6. Key screens

### 6.1 Overview (team lead / security)

- Top strip: spend this period vs envelope (bar with 50/80/100 % marks), requests today, blocks today, provider health (EU regions only).
- Middle: spend by team (table, sortable) and by model.
- Right: open approvals (top-ups, exceptions) with one-click approve where the viewer is an eligible approver.
- Footer: "Last audit chain verification: passed, 2026-10-18 02:00 UTC" with link.

### 6.2 Request event detail

- Header: event id, timestamp, actor (user, team, client type), model tuple with region badge.
- Decision block: outcome, reason codes with explanations, policy bundle digest, obligations.
- DLP block: types and counts only; explicit note "matched values are never stored".
- Budget block: reservation/settlement, running utilisation.
- Integrity block: `prev_hash`, `hash`, segment, anchor status.
- Content: link appears only if content was logged *and* viewer holds both required roles; access is logged and the user is told so before opening.

### 6.3 Model registry entry

- Status chip; region badge (flag + region name); classification ceiling; retention terms; sub-processors list; DPA/DPIA/TIA document links; approval pair (names, dates); next review date; price tier; usage sparkline.
- Actions: propose change (opens dual-approval flow), deprecate, revoke (confirmation states impact: N active users).

### 6.4 Top-up request

- Form: amount, justification (min 50 chars), expiry (defaults to period end). Shows current utilisation and forecast to period end.
- Approver view: requester, team, history of previous top-ups this year, approve/reject with comment.

### 6.5 Chain verification

- Pick range → run → table of segments with hash, anchor match, timestamp authority match, result. Download report (PDF/JSON). Failures highlighted and linked to incident creation.

### 6.6 PR surface (Git hosting)

- Label `ai-assisted` (colour from design system "info", never red).
- PR template section "AI-assisted change checklist" rendered when label present.
- Status checks named clearly: `agl/ai-label`, `agl/dependency-allowlist`, `agl/provenance`.
- Review requirement banner: "This PR needs 1 human approval (2 for security paths). Bot approvals do not count."

## 7. Developer experience outside the console

- **CLI:** `agl whoami` (identity, team, budget left), `agl models` (approved models with region and ceiling), `agl why <event_id>` (explain a decision), `agl sandbox new <repo>`.
- **IDE plugin status bar:** model name + region badge + budget % ; click opens explain panel for the last decision.
- **Docs:** one page "What can I send to AI?" with the classification table and 10 examples.

## 8. Notifications

| Event | Channel | Recipient | Content |
|-------|---------|-----------|---------|
| Budget 50/80/100 % | Team chat | Team | Utilisation, link to spend |
| Top-up requested | Chat DM + email | Approvers | Summary + approve link |
| Secret detected | Security channel + ticket | Security on-call | Type, identity, repo context (no value) |
| Exception requested/approved/expired | Chat | Approvers, requester | Scope, duration |
| Registry change | Security channel | Security, DPO | Diff summary |
| Chain verification failed | Page | Security on-call | Segment, range |
| Isolation test failed | Page | Platform + security on-call | Which probe succeeded |

Digest option for non-urgent items to avoid noise.

## 9. Accessibility and inclusion

- WCAG 2.2 AA; focus order and skip links; all tables keyboard-navigable; status conveyed with icon + text + colour.
- Region badges include text (not just flags).
- Timestamps shown in UTC with local time on hover; ISO 8601.
- Reason codes have a glossary page; every code links to it.
- Language: English v1; strings externalised for later localisation.

## 10. Visual direction

- Use the corporate internal design system tokens; AGL adds only: region badge component, status chips for registry states, hash/digest monospace display with copy button, utilisation bar with threshold ticks.
- Dense data tables with sticky headers; monospace for ids, digests, codes.
- Dark and light themes from the design system; charts use colour-blind-safe palette with direct labels.
- No illustrations of robots or brains.

## 11. Content and empty states

- Empty budgets page: "No envelope set for this team. Requests will be blocked until a budget owner sets one." + CTA.
- Empty registry: "No models approved. Follow the onboarding flow (F-08)." + CTA.
- Verification never run: "Chain verification has not been run. Run now." (and a scheduled nightly job is expected; show if missing).

## 12. Out of scope for design v1

- Mobile layouts (responsive down to tablet only).
- Customisable dashboards.
- Localisation.
