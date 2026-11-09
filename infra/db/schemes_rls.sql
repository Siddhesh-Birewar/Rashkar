-- Government Schemes — Supabase Row Level Security policies.
--
-- Apply in the Supabase SQL editor (or via `psql` against your Supabase database).
-- These are also applied automatically by Alembic migration 009_government_schemes
-- when the target database has the Supabase `auth` schema.
--
-- Design:
--   * Public/anonymous read is restricted to ACTIVE + VERIFIED schemes only.
--   * All writes (INSERT / UPDATE / DELETE) are restricted to the service_role,
--     which is used by the FastAPI backend and administrative tooling.
--   * The FastAPI backend connects directly as the `postgres` superuser and is
--     therefore unaffected by these policies (RLS does not bind table owners /
--     superusers unless FORCE ROW LEVEL SECURITY is set).

alter table public.government_schemes enable row level security;

-- Read policy: expose only active, verified schemes to public readers.
drop policy if exists "schemes_public_read" on public.government_schemes;
create policy "schemes_public_read" on public.government_schemes
  for select
  using (status = 'ACTIVE' and verification_status = 'VERIFIED');

-- Admin policy: service_role can read and write every record.
drop policy if exists "schemes_admin_manage" on public.government_schemes;
create policy "schemes_admin_manage" on public.government_schemes
  for all
  using (auth.jwt() ->> 'role' = 'service_role')
  with check (auth.jwt() ->> 'role' = 'service_role');
