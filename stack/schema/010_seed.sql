-- Demo seed: synthetic organisation, two teams, models, envelopes, repositories, datasets.
-- Nobody here is real. Amounts are small so the budget scenarios trigger quickly.

insert into org (id, name) values ('00000000-0000-0000-0000-000000000001', 'Shortandsweet Logistics (demo)');
insert into cost_centre (id, org_id, code, name) values
  ('00000000-0000-0000-0000-000000000011', '00000000-0000-0000-0000-000000000001', 'CC-204', 'Engineering');
insert into team (id, cost_centre_id, idp_group, name) values
  ('00000000-0000-0000-0000-000000000021', '00000000-0000-0000-0000-000000000011', 'ai-users-logistics-core', 'logistics-core'),
  ('00000000-0000-0000-0000-000000000022', '00000000-0000-0000-0000-000000000011', 'ai-users-payments', 'payments');

insert into identity (id, kind, subject, display_name, email, team_id, training_completed_at) values
  ('00000000-0000-0000-0000-000000000101', 'human', 'dana', 'Dana (developer)', 'dana@example.test', '00000000-0000-0000-0000-000000000021', now()),
  ('00000000-0000-0000-0000-000000000102', 'human', 'teo',  'Teo (team lead)',   'teo@example.test',  '00000000-0000-0000-0000-000000000021', now()),
  ('00000000-0000-0000-0000-000000000103', 'human', 'mira', 'Mira (finance)',    'mira@example.test', null, now()),
  ('00000000-0000-0000-0000-000000000104', 'human', 'ines', 'Ines (CISO)',       'ines@example.test', null, now()),
  ('00000000-0000-0000-0000-000000000105', 'human', 'pawel','Pawel (DPO)',       'pawel@example.test', null, now()),
  ('00000000-0000-0000-0000-000000000106', 'human', 'sven', 'Sven (SRE)',        'sven@example.test', '00000000-0000-0000-0000-000000000022', now()),
  ('00000000-0000-0000-0000-000000000107', 'human', 'newbie','Newbie (no training yet)', 'newbie@example.test', '00000000-0000-0000-0000-000000000022', null);

insert into identity_role (identity_id, role, scope_team) values
  ('00000000-0000-0000-0000-000000000101', 'developer', '00000000-0000-0000-0000-000000000021'),
  ('00000000-0000-0000-0000-000000000102', 'team_lead', '00000000-0000-0000-0000-000000000021'),
  ('00000000-0000-0000-0000-000000000102', 'developer', '00000000-0000-0000-0000-000000000021'),
  ('00000000-0000-0000-0000-000000000103', 'budget_owner', null),
  ('00000000-0000-0000-0000-000000000103', 'finance', null),
  ('00000000-0000-0000-0000-000000000104', 'security_admin', null),
  ('00000000-0000-0000-0000-000000000105', 'dpo', null),
  ('00000000-0000-0000-0000-000000000106', 'developer', '00000000-0000-0000-0000-000000000022'),
  ('00000000-0000-0000-0000-000000000106', 'platform_admin', null),
  ('00000000-0000-0000-0000-000000000107', 'developer', '00000000-0000-0000-0000-000000000022');

-- Providers and models
insert into provider (id, name, legal_entity, entity_country, parent_country, training_opt_out, zero_retention, next_review_at) values
  ('00000000-0000-0000-0000-000000000201', 'Self-hosted (SERVER)', 'Shortandsweet Logistics (demo)', 'RO', null, true, true, '2027-04-01'),
  ('00000000-0000-0000-0000-000000000202', 'Anthropic (direct API, evaluating)', 'Anthropic PBC', 'US', 'US', true, false, '2026-11-19');

insert into model (id, provider_id, name, version) values
  ('00000000-0000-0000-0000-000000000301', '00000000-0000-0000-0000-000000000201', 'local-coder', 'q4'),
  ('00000000-0000-0000-0000-000000000302', '00000000-0000-0000-0000-000000000202', 'claude', 'latest');

-- Endpoints. base_url is overridden by the gateway from env for the PoC (see config);
-- the registry row carries status, ceiling and residency, which are what policy reads.
insert into model_endpoint (id, model_id, alias, base_url, region, region_country, residency, status, classification_ceiling, cost_tier,
                            approved_by_security, approved_by_dpo, approved_at, next_review_at, secret_ref) values
  ('00000000-0000-0000-0000-000000000401', '00000000-0000-0000-0000-000000000301', 'code-local', 'http://ollama:11434', 'server-cluj', 'RO', 'EU_SELF_HOSTED', 'approved', 'CONFIDENTIAL', 1,
   '00000000-0000-0000-0000-000000000104', '00000000-0000-0000-0000-000000000105', now(), '2027-04-01', 'none'),
  ('00000000-0000-0000-0000-000000000402', '00000000-0000-0000-0000-000000000302', 'code-default', 'https://api.anthropic.com', 'us-east-1', 'US', 'NON_EU_EVALUATING', 'evaluating', 'INTERNAL', 3,
   null, null, null, '2026-11-19', 'env:ANTHROPIC_API_KEY');

-- Price list (EUR per 1M tokens). Local model priced at 0 marginal; external at list-like values.
insert into price (model_endpoint_id, effective_from, input_per_1m_eur, output_per_1m_eur, cached_input_per_1m_eur, source) values
  ('00000000-0000-0000-0000-000000000401', '2026-01-01', 0, 0, 0, 'internal'),
  ('00000000-0000-0000-0000-000000000402', '2026-01-01', 2.80, 14.00, 0.28, 'list price (approx.)');

-- Exception that allows the evaluating external endpoint for 72 h (F-09 model_enable), two approvers.
insert into exception (id, type, scope, justification, requested_by, approver_1, approver_2, approved_at, starts_at, ends_at, status) values
  ('00000000-0000-0000-0000-000000000501', 'model_enable', '{"model_alias":"code-default","ceiling":"INTERNAL"}',
   'PoC: evaluate the external endpoint for INTERNAL data only, while a Bedrock/Vertex EU region is arranged. Reviewed by security and DPO.',
   '00000000-0000-0000-0000-000000000106', '00000000-0000-0000-0000-000000000104', '00000000-0000-0000-0000-000000000105', now(), now(), now() + interval '72 hours', 'approved');

-- Budgets for the current month: org total, two teams. Small numbers so S8/S24 trigger in a demo.
insert into budget_envelope (id, scope, scope_id, period_start, period_end, amount_eur, soft_pct, owner_identity) values
  ('00000000-0000-0000-0000-000000000601', 'org',  '00000000-0000-0000-0000-000000000001', date_trunc('month', now())::date, (date_trunc('month', now()) + interval '1 month - 1 day')::date, 2.00, '{50,80}', '00000000-0000-0000-0000-000000000103'),
  ('00000000-0000-0000-0000-000000000602', 'team', '00000000-0000-0000-0000-000000000021', date_trunc('month', now())::date, (date_trunc('month', now()) + interval '1 month - 1 day')::date, 1.00, '{50,80}', '00000000-0000-0000-0000-000000000102'),
  ('00000000-0000-0000-0000-000000000603', 'team', '00000000-0000-0000-0000-000000000022', date_trunc('month', now())::date, (date_trunc('month', now()) + interval '1 month - 1 day')::date, 0.01, '{50,80}', '00000000-0000-0000-0000-000000000103');

-- Repositories: one cleared, one quarantined, one RESTRICTED.
insert into repository (id, scm_host, full_name, team_id, classification, ai_exposure) values
  ('00000000-0000-0000-0000-000000000701', 'github.com', 'shortandsweet/booking-svc', '00000000-0000-0000-0000-000000000021', 'INTERNAL', 'quarantined'),
  ('00000000-0000-0000-0000-000000000702', 'github.com', 'shortandsweet/app-x',       '00000000-0000-0000-0000-000000000021', 'INTERNAL', 'quarantined'),
  ('00000000-0000-0000-0000-000000000703', 'github.com', 'shortandsweet/payments-db', '00000000-0000-0000-0000-000000000022', 'RESTRICTED', 'quarantined');

-- booking-svc: gate fully satisfied and signed off → allowed. app-x: gate incomplete (G2 open).
insert into repository_ai_gate (repository_id, classification_set, no_prod_data, no_prod_secrets, no_prod_connectivity, dpia_or_risk_ref, approver_security, approver_owner, approved_at, evidence) values
  ('00000000-0000-0000-0000-000000000701', true, true, true, true, 'RISK-2026-014', '00000000-0000-0000-0000-000000000104', '00000000-0000-0000-0000-000000000102', now(), '{"secret_scan":"evidence/booking-svc-gitleaks.json","probe":"evidence/booking-svc-probe.txt"}'),
  ('00000000-0000-0000-0000-000000000702', true, false, true, true, null, null, null, null, '{}');
update repository set ai_exposure = 'allowed' where id = '00000000-0000-0000-0000-000000000701';

insert into dataset (name, origin, masking_report_ref, repository_id) values
  ('booking-masked-2026-10', 'masked', 'evidence/mask-report-2026-10.json', '00000000-0000-0000-0000-000000000701'),
  ('booking-synthetic-small', 'synthetic', null, '00000000-0000-0000-0000-000000000701'),
  ('prod-dump-2026-10-18', 'prod-derived', null, '00000000-0000-0000-0000-000000000703');
