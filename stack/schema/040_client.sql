-- Client product questions (owner decision 2026-10-21, PD-51): a 'client' role, and a seeded client user in a team
-- with its own small envelope. Runs on a fresh database after the seed and, unchanged, on a live one. Idempotent.
-- ADD VALUE cannot share a transaction with statements that use the new value, so it runs on its own first.
alter type role_name add value if not exists 'client';

begin;
insert into team (id, cost_centre_id, idp_group, name) values
  ('00000000-0000-0000-0000-000000000023', '00000000-0000-0000-0000-000000000011', 'ai-users-client-product', 'client-product')
on conflict do nothing;

insert into identity (id, kind, subject, display_name, email, team_id, training_completed_at) values
  ('00000000-0000-0000-0000-000000000108', 'human', 'carla', 'Carla (client PO)', 'carla@example.test', '00000000-0000-0000-0000-000000000023', now())
on conflict do nothing;

insert into identity_role (identity_id, role, scope_team) values
  ('00000000-0000-0000-0000-000000000108', 'client', '00000000-0000-0000-0000-000000000023')
on conflict do nothing;

-- One question costs about 0.005 EUR at the placeholder chargeback (the catalog is sent with it); 0.50 EUR is ~100 questions.
insert into budget_envelope (id, scope, scope_id, period_start, period_end, amount_eur, soft_pct, owner_identity) values
  ('00000000-0000-0000-0000-000000000604', 'team', '00000000-0000-0000-0000-000000000023', date_trunc('month', now())::date,
   (date_trunc('month', now()) + interval '1 month - 1 day')::date, 0.50, '{50,80}', '00000000-0000-0000-0000-000000000103')
on conflict do nothing;
commit;
