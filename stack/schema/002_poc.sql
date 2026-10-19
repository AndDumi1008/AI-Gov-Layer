-- PoC additions on top of 001_core.sql (see docs/07 §10).

-- 1. Ordering for the hash chain: a monotonic sequence on the hot copy.
alter table audit_event add column seq bigint generated always as identity;
create unique index on audit_event (seq);

-- 2. Non-EU endpoints may exist only while 'evaluating' (used under a logged exception);
--    they can never become approved/restricted (see docs/07 §10.5 residency note).
alter type residency_class add value if not exists 'NON_EU_EVALUATING';
alter table model_endpoint drop constraint model_endpoint_region_country_check;
alter table model_endpoint add constraint model_endpoint_region_country_check check (
  region_country in ('AT','BE','BG','HR','CY','CZ','DK','EE','FI','FR','DE','GR','HU','IE','IT','LV','LT','LU','MT','NL','PL','PT','RO','SK','SI','ES','SE','NO','IS','LI','CH')
  or status = 'evaluating'
);

-- 2b. Org-wide roles have scope_team = null, which a composite primary key cannot hold (found by the seed; register PD-23).
alter table identity_role drop constraint identity_role_pkey;
alter table identity_role alter column scope_team drop not null;
create unique index identity_role_uniq on identity_role (identity_id, role, coalesce(scope_team, '00000000-0000-0000-0000-000000000000'::uuid));

-- 2c. Anchors carry a cut-off: an anchor covers the segments closed up to anchored_through, and a day
--     may hold several anchors (PD-28). The unique(anchor_date) from 001 is dropped.
alter table audit_anchor drop constraint audit_anchor_anchor_date_key;
alter table audit_anchor add column anchored_through timestamptz not null default now();

-- 3. Budget utilisation as a function (the materialized view in 001 is for dashboards).
create or replace function budget_state(p_scope envelope_scope, p_scope_id uuid, p_at timestamptz default now())
returns table (envelope_id uuid, amount_eur numeric, consumed_eur numeric, pct numeric, soft_pct smallint[])
language sql stable as $$
  select e.id, e.amount_eur,
         coalesce(sum(l.amount_eur) filter (where l.kind in ('reserve','settle','adjustment')),0) as consumed_eur,
         case when e.amount_eur = 0 then 100
              else round(100 * coalesce(sum(l.amount_eur) filter (where l.kind in ('reserve','settle','adjustment')),0) / e.amount_eur, 2) end as pct,
         e.soft_pct
  from budget_envelope e left join budget_ledger l on l.envelope_id = e.id
  where e.scope = p_scope and e.scope_id = p_scope_id and e.status = 'open'
    and p_at::date between e.period_start and e.period_end
  group by e.id
$$;

-- 4. Roles used by the gateway (passwords set by bootstrap; defaults for local dev).
do $$ begin
  if not exists (select 1 from pg_roles where rolname = 'agl_gateway') then
    create role agl_gateway login password 'agl_gateway_dev';
  end if;
end $$;
grant usage on schema public to agl_gateway;
grant select on all tables in schema public to agl_gateway;
grant insert on budget_ledger, topup_request, audit_event, audit_segment, audit_anchor, chain_verification, delegated_identity, identity, exception, repository_ai_gate to agl_gateway;
grant update on topup_request, exception, repository, repository_ai_gate, identity, delegated_identity to agl_gateway;
grant usage, select on all sequences in schema public to agl_gateway;
revoke update, delete, truncate on audit_event, audit_segment, audit_anchor from agl_gateway;
