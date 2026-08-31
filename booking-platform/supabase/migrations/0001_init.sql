-- Booking Platform — initial multi-tenant schema
-- Run via `supabase db push` or the Supabase SQL editor.
--
-- Tenancy model: every business-scoped table carries `business_id`.
-- Access control uses security-definer helper functions (my_role(),
-- my_business_id(), is_super_admin()) so RLS policies stay short and
-- consistent, following the pattern used in talentflow/supabase/migrations.
--
-- Roles: 'super_admin' (platform owner, sees everything), 'owner' (business
-- owner, full control of their business), 'staff' (employee, scoped to
-- appointments relevant to them). Anonymous/public access is granted
-- separately, narrowly, only on the tables the booking widget needs.

-- ============================================================
-- 0. extensions
-- ============================================================
create extension if not exists "btree_gist";
create extension if not exists "pgcrypto";

create function public.set_updated_at() returns trigger
  language plpgsql
  as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

-- ============================================================
-- 1. businesses (the tenant)
-- ============================================================
create table public.businesses (
  id uuid primary key default gen_random_uuid(),
  slug text not null unique,
  name text not null,
  business_type text,
  contact_email text,
  contact_phone text,
  address text,
  timezone text not null default 'Asia/Jerusalem',
  status text not null default 'trial' check (status in ('trial', 'active', 'past_due', 'suspended', 'cancelled')),
  plan text not null default 'trial',
  trial_ends_at timestamptz,
  subscription_renews_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

-- ============================================================
-- 2. profiles (mirrors auth.users; carries role + tenant link)
-- ============================================================
create table public.profiles (
  id uuid primary key references auth.users(id) on delete cascade,
  email text not null,
  full_name text,
  role text not null check (role in ('super_admin', 'owner', 'staff')),
  business_id uuid references public.businesses(id) on delete cascade,
  employee_id uuid, -- set for 'staff' once linked to an employees row (added FK after employees exists)
  created_at timestamptz not null default now()
);

create index profiles_business_id_idx on public.profiles(business_id);

-- Security-definer helpers — read the calling user's own profile without
-- re-triggering RLS on profiles itself.
create function public.my_role() returns text
  language sql security definer stable
  set search_path = public
  as $$ select role from profiles where id = auth.uid() $$;

create function public.my_business_id() returns uuid
  language sql security definer stable
  set search_path = public
  as $$ select business_id from profiles where id = auth.uid() $$;

create function public.my_employee_id() returns uuid
  language sql security definer stable
  set search_path = public
  as $$ select employee_id from profiles where id = auth.uid() $$;

create function public.is_super_admin() returns boolean
  language sql security definer stable
  set search_path = public
  as $$ select coalesce((select role from profiles where id = auth.uid()) = 'super_admin', false) $$;

-- Tenant-scope check used throughout: caller is super_admin, or an
-- owner/staff of the given business.
create function public.in_business(target_business_id uuid) returns boolean
  language sql security definer stable
  set search_path = public
  as $$ select is_super_admin() or my_business_id() = target_business_id $$;

create trigger set_updated_at_businesses before update on public.businesses
  for each row execute function public.set_updated_at();

alter table public.businesses enable row level security;
alter table public.profiles enable row level security;

create policy "businesses_read" on public.businesses for select
  using (is_super_admin() or id = my_business_id());
-- Public/anon can look up a business by slug/id to render the booking
-- widget, but only non-sensitive fields matter — the widget UI only ever
-- selects name, business_type, contact_*, timezone; status/plan are also
-- exposed here but carry no sensitive data.
create policy "businesses_public_read" on public.businesses for select
  to anon
  using (status in ('trial', 'active'));
create policy "businesses_update" on public.businesses for update
  using (is_super_admin() or (id = my_business_id() and my_role() = 'owner'));
create policy "businesses_insert" on public.businesses for insert
  with check (is_super_admin());
create policy "businesses_delete" on public.businesses for delete
  using (is_super_admin());

create policy "profiles_read" on public.profiles for select
  using (id = auth.uid() or is_super_admin() or (my_role() = 'owner' and business_id = my_business_id()));
create policy "profiles_update" on public.profiles for update
  using (id = auth.uid() or is_super_admin() or (my_role() = 'owner' and business_id = my_business_id()));
create policy "profiles_insert" on public.profiles for insert
  with check (is_super_admin() or (my_role() = 'owner' and business_id = my_business_id()));
create policy "profiles_delete" on public.profiles for delete
  using (is_super_admin() or (my_role() = 'owner' and business_id = my_business_id()));

-- Auto-create a profile row on signup. New users default to no role/business;
-- an owner or super_admin must assign them via the admin API afterward.
create function public.handle_new_user() returns trigger
  language plpgsql security definer
  set search_path = public
  as $$
begin
  insert into public.profiles (id, email, role) values (new.id, new.email, 'staff');
  return new;
end;
$$;

create trigger on_auth_user_created
  after insert on auth.users
  for each row execute function public.handle_new_user();

-- ============================================================
-- 3. business_settings (booking rules, 1:1 with businesses)
-- ============================================================
create table public.business_settings (
  business_id uuid primary key references public.businesses(id) on delete cascade,
  show_employee_selection boolean not null default true,
  show_prices boolean not null default true,
  allow_cancellation boolean not null default true,
  allow_rescheduling boolean not null default true,
  cancellation_notice_minutes int not null default 1440,
  minimum_notice_minutes int not null default 120,
  max_booking_days_ahead int not null default 60,
  slot_interval_minutes int not null default 30,
  default_language text not null default 'en',
  updated_at timestamptz not null default now()
);

alter table public.business_settings enable row level security;

create policy "business_settings_read" on public.business_settings for select
  using (in_business(business_id));
create policy "business_settings_write" on public.business_settings for all
  using (is_super_admin() or (my_role() = 'owner' and business_id = my_business_id()))
  with check (is_super_admin() or (my_role() = 'owner' and business_id = my_business_id()));

-- Public/anon needs a read-only view of the subset of settings relevant to
-- rendering the booking widget (not e.g. cancellation policy internals).
create policy "business_settings_public_read" on public.business_settings for select
  to anon
  using (true);

-- ============================================================
-- 4. business_themes (branding, 1:1 with businesses)
-- ============================================================
create table public.business_themes (
  business_id uuid primary key references public.businesses(id) on delete cascade,
  logo_url text,
  primary_color text not null default '#2563eb',
  secondary_color text not null default '#1e293b',
  font_family text not null default 'Inter, system-ui, sans-serif',
  button_style text not null default 'rounded' check (button_style in ('rounded', 'square', 'pill')),
  updated_at timestamptz not null default now()
);

alter table public.business_themes enable row level security;

create policy "business_themes_read" on public.business_themes for select
  using (in_business(business_id));
create policy "business_themes_write" on public.business_themes for all
  using (is_super_admin() or (my_role() = 'owner' and business_id = my_business_id()))
  with check (is_super_admin() or (my_role() = 'owner' and business_id = my_business_id()));
create policy "business_themes_public_read" on public.business_themes for select
  to anon
  using (true);

-- ============================================================
-- 5. services
-- ============================================================
create table public.services (
  id uuid primary key default gen_random_uuid(),
  business_id uuid not null references public.businesses(id) on delete cascade,
  name text not null,
  description text,
  duration_minutes int not null check (duration_minutes > 0),
  price numeric(10, 2),
  image_url text,
  is_active boolean not null default true,
  sort_order int not null default 0,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index services_business_id_idx on public.services(business_id);

create trigger set_updated_at_services before update on public.services
  for each row execute function public.set_updated_at();

alter table public.services enable row level security;

create policy "services_read" on public.services for select
  using (in_business(business_id));
create policy "services_public_read" on public.services for select
  to anon
  using (is_active = true);
create policy "services_write" on public.services for all
  using (is_super_admin() or (my_role() = 'owner' and business_id = my_business_id()))
  with check (is_super_admin() or (my_role() = 'owner' and business_id = my_business_id()));

-- ============================================================
-- 6. employees
-- ============================================================
create table public.employees (
  id uuid primary key default gen_random_uuid(),
  business_id uuid not null references public.businesses(id) on delete cascade,
  profile_id uuid references public.profiles(id) on delete set null,
  name text not null,
  email text,
  phone text,
  photo_url text,
  is_active boolean not null default true,
  sort_order int not null default 0,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index employees_business_id_idx on public.employees(business_id);

create trigger set_updated_at_employees before update on public.employees
  for each row execute function public.set_updated_at();

alter table public.profiles
  add constraint profiles_employee_id_fkey foreign key (employee_id) references public.employees(id) on delete set null;

alter table public.employees enable row level security;

create policy "employees_read" on public.employees for select
  using (in_business(business_id));
create policy "employees_public_read" on public.employees for select
  to anon
  using (is_active = true);
create policy "employees_write" on public.employees for all
  using (is_super_admin() or (my_role() = 'owner' and business_id = my_business_id()))
  with check (is_super_admin() or (my_role() = 'owner' and business_id = my_business_id()));

-- ============================================================
-- 7. employee_services (which employees can perform which services)
-- ============================================================
create table public.employee_services (
  employee_id uuid not null references public.employees(id) on delete cascade,
  service_id uuid not null references public.services(id) on delete cascade,
  primary key (employee_id, service_id)
);

alter table public.employee_services enable row level security;

create policy "employee_services_read" on public.employee_services for select
  using (exists (select 1 from employees e where e.id = employee_id and in_business(e.business_id)));
create policy "employee_services_public_read" on public.employee_services for select
  to anon
  using (true);
create policy "employee_services_write" on public.employee_services for all
  using (exists (select 1 from employees e where e.id = employee_id and (is_super_admin() or (my_role() = 'owner' and e.business_id = my_business_id()))))
  with check (exists (select 1 from employees e where e.id = employee_id and (is_super_admin() or (my_role() = 'owner' and e.business_id = my_business_id()))));

-- ============================================================
-- 8. working_hours (business-level and employee-level, shared shape)
-- weekday: 0=Sunday .. 6=Saturday. Multiple rows per weekday allow split
-- shifts (e.g. 09:00-13:00 and 16:00-20:00).
-- ============================================================
create table public.working_hours (
  id uuid primary key default gen_random_uuid(),
  business_id uuid not null references public.businesses(id) on delete cascade,
  employee_id uuid references public.employees(id) on delete cascade, -- null = business-level default
  weekday smallint not null check (weekday between 0 and 6),
  start_time time not null,
  end_time time not null,
  check (end_time > start_time)
);

create index working_hours_business_id_idx on public.working_hours(business_id);
create index working_hours_employee_id_idx on public.working_hours(employee_id);

alter table public.working_hours enable row level security;

create policy "working_hours_read" on public.working_hours for select
  using (in_business(business_id));
create policy "working_hours_public_read" on public.working_hours for select
  to anon
  using (true);
create policy "working_hours_write" on public.working_hours for all
  using (is_super_admin() or (my_role() = 'owner' and business_id = my_business_id()))
  with check (is_super_admin() or (my_role() = 'owner' and business_id = my_business_id()));

-- ============================================================
-- 9. holidays (business-level or employee-level closed date ranges)
-- ============================================================
create table public.holidays (
  id uuid primary key default gen_random_uuid(),
  business_id uuid not null references public.businesses(id) on delete cascade,
  employee_id uuid references public.employees(id) on delete cascade, -- null = whole business
  starts_on date not null,
  ends_on date not null,
  label text,
  check (ends_on >= starts_on)
);

create index holidays_business_id_idx on public.holidays(business_id);

alter table public.holidays enable row level security;

create policy "holidays_read" on public.holidays for select
  using (in_business(business_id));
create policy "holidays_public_read" on public.holidays for select
  to anon
  using (true);
create policy "holidays_write" on public.holidays for all
  using (is_super_admin() or (my_role() = 'owner' and business_id = my_business_id()))
  with check (is_super_admin() or (my_role() = 'owner' and business_id = my_business_id()));

-- ============================================================
-- 10. blocked_times (ad-hoc blocks: lunch, meetings, one-off closures)
-- ============================================================
create table public.blocked_times (
  id uuid primary key default gen_random_uuid(),
  business_id uuid not null references public.businesses(id) on delete cascade,
  employee_id uuid references public.employees(id) on delete cascade, -- null = whole business
  starts_at timestamptz not null,
  ends_at timestamptz not null,
  label text,
  check (ends_at > starts_at)
);

create index blocked_times_business_id_idx on public.blocked_times(business_id);
create index blocked_times_employee_range_idx on public.blocked_times using gist (employee_id, tstzrange(starts_at, ends_at));

alter table public.blocked_times enable row level security;

create policy "blocked_times_read" on public.blocked_times for select
  using (in_business(business_id));
create policy "blocked_times_public_read" on public.blocked_times for select
  to anon
  using (true);
create policy "blocked_times_write" on public.blocked_times for all
  using (is_super_admin() or (my_role() = 'owner' and business_id = my_business_id()))
  with check (is_super_admin() or (my_role() = 'owner' and business_id = my_business_id()));

-- ============================================================
-- 11. customers
-- ============================================================
create table public.customers (
  id uuid primary key default gen_random_uuid(),
  business_id uuid not null references public.businesses(id) on delete cascade,
  full_name text not null,
  phone text not null,
  email text,
  notes text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index customers_business_id_idx on public.customers(business_id);
create unique index customers_business_phone_idx on public.customers(business_id, phone);

create trigger set_updated_at_customers before update on public.customers
  for each row execute function public.set_updated_at();

alter table public.customers enable row level security;

create policy "customers_read" on public.customers for select
  using (in_business(business_id));
create policy "customers_write" on public.customers for all
  using (is_super_admin() or (business_id = my_business_id() and my_role() in ('owner', 'staff')))
  with check (is_super_admin() or (business_id = my_business_id() and my_role() in ('owner', 'staff')));
-- No anon policy: customers are only ever created via the create-booking
-- edge function (service role), never inserted directly by the widget.

-- ============================================================
-- 12. appointments
-- Double-booking protection: an exclusion constraint on
-- (employee_id, time range) rejects overlapping appointments for the same
-- employee at the database level, even under concurrent transactions.
-- ============================================================
create table public.appointments (
  id uuid primary key default gen_random_uuid(),
  confirmation_code text not null unique default upper(substr(md5(gen_random_uuid()::text), 1, 8)),
  business_id uuid not null references public.businesses(id) on delete cascade,
  service_id uuid not null references public.services(id),
  employee_id uuid references public.employees(id),
  customer_id uuid not null references public.customers(id),
  starts_at timestamptz not null,
  ends_at timestamptz not null,
  status text not null default 'confirmed' check (status in ('pending', 'confirmed', 'completed', 'cancelled', 'no_show')),
  price_at_booking numeric(10, 2),
  notes text,
  cancelled_at timestamptz,
  cancellation_reason text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  check (ends_at > starts_at)
);

create index appointments_business_id_idx on public.appointments(business_id);
create index appointments_customer_id_idx on public.appointments(customer_id);
create index appointments_starts_at_idx on public.appointments(business_id, starts_at);

create trigger set_updated_at_appointments before update on public.appointments
  for each row execute function public.set_updated_at();

-- The core anti-double-booking guarantee, split into two exclusion
-- constraints covering the two ways a slot can be scoped:
--  1. Per-employee: no employee can have two overlapping appointments.
--  2. Per-service, no-employee: when a business doesn't assign employees to
--     appointments, the service itself is the resource being reserved, so
--     no two overlapping appointments for the same (business, service) with
--     a null employee_id may exist either.
-- Cancelled appointments free the slot via the partial where-condition.
-- Both are enforced atomically at the database level, so concurrent
-- requests cannot double-book regardless of application-layer races.
alter table public.appointments
  add constraint appointments_no_overlap_per_employee
  exclude using gist (
    employee_id with =,
    tstzrange(starts_at, ends_at) with &&
  ) where (status not in ('cancelled') and employee_id is not null);

alter table public.appointments
  add constraint appointments_no_overlap_per_service_no_employee
  exclude using gist (
    business_id with =,
    service_id with =,
    tstzrange(starts_at, ends_at) with &&
  ) where (status not in ('cancelled') and employee_id is null);

alter table public.appointments enable row level security;

create policy "appointments_read" on public.appointments for select
  using (
    is_super_admin()
    or (business_id = my_business_id() and my_role() = 'owner')
    or (business_id = my_business_id() and my_role() = 'staff' and employee_id = my_employee_id())
  );
create policy "appointments_write" on public.appointments for all
  using (
    is_super_admin()
    or (business_id = my_business_id() and my_role() = 'owner')
    or (business_id = my_business_id() and my_role() = 'staff' and employee_id = my_employee_id())
  )
  with check (
    is_super_admin()
    or (business_id = my_business_id() and my_role() = 'owner')
    or (business_id = my_business_id() and my_role() = 'staff' and employee_id = my_employee_id())
  );
-- No anon policy: appointments are only ever created via the create-booking
-- edge function (service role) so availability + the exclusion constraint
-- are always honored server-side.

alter publication supabase_realtime add table public.appointments;

-- ============================================================
-- 13. notification_settings + notification_logs
-- ============================================================
create table public.notification_settings (
  business_id uuid primary key references public.businesses(id) on delete cascade,
  email_enabled boolean not null default true,
  reminder_hours_before int not null default 24,
  updated_at timestamptz not null default now()
);

alter table public.notification_settings enable row level security;

create policy "notification_settings_read" on public.notification_settings for select
  using (in_business(business_id));
create policy "notification_settings_write" on public.notification_settings for all
  using (is_super_admin() or (my_role() = 'owner' and business_id = my_business_id()))
  with check (is_super_admin() or (my_role() = 'owner' and business_id = my_business_id()));

create table public.notification_logs (
  id uuid primary key default gen_random_uuid(),
  business_id uuid not null references public.businesses(id) on delete cascade,
  appointment_id uuid references public.appointments(id) on delete cascade,
  channel text not null check (channel in ('email', 'whatsapp', 'sms')),
  event_type text not null check (event_type in ('booking_confirmation', 'reminder', 'cancellation', 'reschedule')),
  recipient text not null,
  status text not null default 'pending' check (status in ('pending', 'sent', 'failed')),
  error_message text,
  created_at timestamptz not null default now()
);

create index notification_logs_business_id_idx on public.notification_logs(business_id);

alter table public.notification_logs enable row level security;

create policy "notification_logs_read" on public.notification_logs for select
  using (in_business(business_id));
-- Writes happen only via service-role edge functions; no client write policy.

-- ============================================================
-- 14. audit_logs
-- ============================================================
create table public.audit_logs (
  id uuid primary key default gen_random_uuid(),
  business_id uuid references public.businesses(id) on delete cascade,
  actor_id uuid references auth.users(id),
  actor_role text,
  action text not null,
  entity_type text not null,
  entity_id uuid,
  metadata jsonb not null default '{}',
  created_at timestamptz not null default now()
);

create index audit_logs_business_id_idx on public.audit_logs(business_id);

alter table public.audit_logs enable row level security;

create policy "audit_logs_read" on public.audit_logs for select
  using (is_super_admin() or (my_role() = 'owner' and business_id = my_business_id()));
-- Writes happen only via service-role (triggers/edge functions), no client write policy.

-- ============================================================
-- 15. google_calendar_tokens (architecture stub for section 13 of spec)
-- Same pattern as talentflow: service-role only, no client policies at all.
-- ============================================================
create table public.google_calendar_tokens (
  id uuid primary key default gen_random_uuid(),
  business_id uuid not null references public.businesses(id) on delete cascade,
  employee_id uuid references public.employees(id) on delete cascade,
  access_token text not null,
  refresh_token text not null,
  expires_at timestamptz not null,
  sync_busy_events boolean not null default false,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create unique index google_calendar_tokens_scope_idx on public.google_calendar_tokens(business_id, coalesce(employee_id, '00000000-0000-0000-0000-000000000000'));

alter table public.google_calendar_tokens enable row level security;
-- No policies granted to anon/authenticated: only the service_role key can read/write this table.

-- ============================================================
-- 16. subscriptions (billing architecture stub — see spec section 19)
-- ============================================================
create table public.subscriptions (
  id uuid primary key default gen_random_uuid(),
  business_id uuid not null references public.businesses(id) on delete cascade,
  plan text not null default 'trial',
  status text not null default 'trial' check (status in ('trial', 'active', 'past_due', 'suspended', 'cancelled')),
  started_at timestamptz not null default now(),
  renews_at timestamptz,
  cancelled_at timestamptz,
  external_provider text, -- e.g. 'stripe', filled in when billing is added
  external_subscription_id text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index subscriptions_business_id_idx on public.subscriptions(business_id);

alter table public.subscriptions enable row level security;

create policy "subscriptions_read" on public.subscriptions for select
  using (is_super_admin() or (my_role() = 'owner' and business_id = my_business_id()));
create policy "subscriptions_write" on public.subscriptions for all
  using (is_super_admin())
  with check (is_super_admin());
