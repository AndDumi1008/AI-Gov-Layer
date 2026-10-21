-- Content store in use (owner decision 2026-10-21, PD-50): the prompt and answer of every request that reached a
-- model, and every agent command with its output. Runs after the seed on a fresh database and, unchanged, on a live
-- one (psql -v ON_ERROR_STOP=1 -f 030_content_store.sql). Idempotent, one transaction. Reads need two people (4).
begin;

-- 1. What a record holds and whose it is: erasure is by request or by person (F-11).
alter table content_record add column if not exists kind text not null default 'completion';
alter table content_record drop constraint if exists content_record_kind_check;
alter table content_record add constraint content_record_kind_check check (kind in ('completion', 'agent_action'));
alter table content_record add column if not exists identity_id uuid references identity(id);
alter table content_record alter column team_id drop not null;          -- identities without a team use the org key
create index if not exists content_record_event_idx on content_record (event_id);
create index if not exists content_record_identity_idx on content_record (identity_id, created_at);

-- 2. Bodies can be removed (erasure, expiry) but never rewritten, and an erased record stays erased. The row and its
--    fingerprints remain as the proof that something was stored and then removed.
create or replace function content_record_guard() returns trigger language plpgsql as $$
begin
  if new.event_id is distinct from old.event_id or new.prompt_sha256 is distinct from old.prompt_sha256
     or new.identity_id is distinct from old.identity_id or new.kind is distinct from old.kind then
    raise exception 'content_record: event link, owner and fingerprint are fixed';
  end if;
  if new.prompt_cipher is not null and new.prompt_cipher is distinct from old.prompt_cipher then
    raise exception 'content_record: a stored prompt can be erased, not rewritten';
  end if;
  if old.response_cipher is not null and new.response_cipher is not null and new.response_cipher is distinct from old.response_cipher then
    raise exception 'content_record: a stored response can be erased, not rewritten';
  end if;
  if old.erased_at is not null and (new.erased_at is null or new.prompt_cipher is not null or new.response_cipher is not null) then
    raise exception 'content_record: an erased record stays erased';
  end if;
  return new;
end $$;
drop trigger if exists content_record_guard on content_record;
create trigger content_record_guard before update on content_record for each row execute function content_record_guard();

-- 3. The gateway writes, adds an agent's output, erases and expires. It never deletes a row.
grant insert, update on content_record to agl_gateway;
revoke delete, truncate on content_record from agl_gateway;

-- 4. Reading a stored body takes two people (owner decision 2026-10-21, T-CNT-04): one asks, with a reason; a
--    different person approves; only the asker can then read, for 24 hours. Every step is an audit event too.
create table if not exists content_access_request (
  id            uuid primary key default gen_random_uuid(),
  event_id      uuid not null,
  requested_by  uuid not null references identity(id),
  reason        text not null check (length(reason) >= 10),
  requested_at  timestamptz not null default now(),
  status        text not null default 'open' check (status in ('open', 'approved')),
  approved_by   uuid references identity(id),
  approved_at   timestamptz,
  expires_at    timestamptz,
  check (approved_by is null or approved_by <> requested_by),
  check ((status = 'approved') = (approved_by is not null and approved_at is not null and expires_at is not null))
);
create index if not exists content_access_request_event_idx on content_access_request (event_id);
grant select, insert, update on content_access_request to agl_gateway;
revoke delete, truncate on content_access_request from agl_gateway;

commit;
