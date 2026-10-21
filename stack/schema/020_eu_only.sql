-- EU only, no exception (owner decision PD-43, issue #19). Runs after the seed on a fresh database and,
-- unchanged, on a live one (psql -v ON_ERROR_STOP=1 -f 020_eu_only.sql). Idempotent, one transaction.
-- SQL cannot append to the hash chain; the registry_change event is an open item in PD-43.
begin;

-- 1. Close the 72-hour exception that let the US endpoint be used. Kept as a row: audit events reference it.
--    On a fresh database the seed recreates that exception first, so the history matches SERVER's.
update exception
   set status = 'closed', ends_at = least(ends_at, now()), post_review_at = now(),
       post_review_note = 'Closed by owner decision PD-43 (#19): no processing outside the EU, no exception. On a fresh database this row is replayed seed history.'
 where type = 'model_enable' and scope->>'model_alias' = 'code-default' and status = 'approved';

-- 2. Revoke every endpoint outside the EU/EEA. Rows stay for the audit trail; 'revoked' is never usable.
update model_endpoint set status = 'revoked'
 where status <> 'revoked'
   and (residency = 'NON_EU_EVALUATING'
        or region_country not in ('AT','BE','BG','HR','CY','CZ','DK','EE','FI','FR','DE','GR','HU','IE','IT','LV','LT','LU','MT','NL','PL','PT','RO','SK','SI','ES','SE','NO','IS','LI','CH'));

-- 3. From now on a non-EU endpoint can exist only as revoked history; 'evaluating' no longer opens a door.
alter table model_endpoint drop constraint if exists model_endpoint_region_country_check;
alter table model_endpoint add constraint model_endpoint_region_country_check check (
  status = 'revoked'
  or (residency <> 'NON_EU_EVALUATING'
      and region_country in ('AT','BE','BG','HR','CY','CZ','DK','EE','FI','FR','DE','GR','HU','IE','IT','LV','LT','LU','MT','NL','PL','PT','RO','SK','SI','ES','SE','NO','IS','LI','CH'))
);

-- 4. The self-hosted tier now carries all work, so it gets an internal chargeback rate; at 0 EUR the budget
--    guardrail (G7) would bound nothing. Placeholder set by the owner until finance fixes it (PD-43).
update price set effective_to = current_date
 where model_endpoint_id = (select id from model_endpoint where alias = 'code-local')
   and effective_to is null and input_per_1m_eur = 0 and output_per_1m_eur = 0 and effective_from < current_date;
insert into price (model_endpoint_id, effective_from, input_per_1m_eur, output_per_1m_eur, cached_input_per_1m_eur, source)
select id, current_date, 1.00, 5.00, 0, 'internal chargeback, placeholder (PD-43)'
  from model_endpoint e
 where alias = 'code-local'
   and not exists (select 1 from price p where p.model_endpoint_id = e.id and p.effective_to is null);

commit;
