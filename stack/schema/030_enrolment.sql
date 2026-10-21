-- One-time enrolment codes carried inside a developer's encrypted connection bundle (DoD; issue #12).
-- The gateway stores only the SHA-256 of the code; `agl enroll` exchanges the code for a token once.
create table if not exists enrolment_code (
  id           uuid primary key default gen_random_uuid(),
  code_hash    text not null unique,
  identity_id  uuid not null references identity(id),
  issued_by    uuid not null references identity(id),
  issued_at    timestamptz not null default now(),
  expires_at   timestamptz not null,
  used_at      timestamptz,
  used_from    text
);
grant select, insert, update on enrolment_code to agl_gateway;
