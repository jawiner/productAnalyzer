-- Minimal stand-in for Supabase's auth.users table + auth.uid(), so the
-- multi-tenant migration (which references auth.users via FK and auth.uid()
-- inside RLS helper functions) applies cleanly on plain Postgres for local
-- testing purposes only. Never used against a real Supabase project (which
-- already provides the real auth schema).
create schema if not exists auth;

create table if not exists auth.users (
  id uuid primary key default gen_random_uuid(),
  email text
);

create or replace function auth.uid() returns uuid
  language sql stable
  as $$ select null::uuid $$;

do $$
begin
  if not exists (select 1 from pg_roles where rolname = 'anon') then
    create role anon nologin;
  end if;
  if not exists (select 1 from pg_roles where rolname = 'authenticated') then
    create role authenticated nologin;
  end if;
end
$$;
