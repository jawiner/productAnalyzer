-- SMS notifications: customer reminders + business new-booking alerts.
--
-- Adds SMS-specific settings, a recipient_role column on notification_logs
-- (so logs distinguish "sent to the customer" vs "sent to the business"),
-- and a reminder_sent_at marker on appointments so the reminder cron job
-- can find "due, not yet reminded" appointments without double-sending.

alter table public.business_settings
  add column sms_enabled boolean not null default false,
  add column notify_business_on_new_booking boolean not null default true,
  add column business_notification_phone text;

alter table public.notification_logs
  add column recipient_role text not null default 'customer' check (recipient_role in ('customer', 'business'));

alter table public.appointments
  add column reminder_sent_at timestamptz;

-- Reminder cron needs to efficiently find "starts soon, not yet reminded,
-- not cancelled" appointments across all businesses.
create index appointments_reminder_due_idx on public.appointments(starts_at)
  where status in ('pending', 'confirmed') and reminder_sent_at is null;

-- ============================================================
-- Scheduled reminder dispatch: pg_cron calls the send-reminders edge
-- function every 15 minutes. That function finds appointments due for a
-- reminder (per each business's own reminder_hours_before setting) and
-- sends SMS via Twilio, then stamps reminder_sent_at so it's never sent
-- twice. The cron job itself does no Twilio/business logic — it only
-- triggers the function, keeping that logic in one place (testable,
-- same pattern as every other public edge function).
--
-- The project URL is not a secret (it's public/derivable from the project
-- ref) so it's inlined directly below — replace the ref if this migration
-- is ever reused for a different project. The service role key IS a
-- secret; rather than storing it a second time in the database (Vault),
-- this job authenticates with send-reminders' own anon-key + a shared
-- header check inside that function instead — see send-reminders/index.ts,
-- which validates a X-Cron-Secret header against the CRON_SECRET edge
-- function secret (set via `supabase secrets set CRON_SECRET=...`,
-- alongside the Twilio secrets) rather than requiring the full service
-- role JWT to reach the function over the network.
-- ============================================================
create extension if not exists pg_cron with schema extensions;
create extension if not exists pg_net with schema extensions;

-- current_setting('app.cron_secret', true) reads a database-level GUC set
-- separately (see docs/CLIENT_SETUP_GUIDE — one-time
-- `ALTER DATABASE postgres SET app.cron_secret = '...'` run via the SQL
-- editor, matching the CRON_SECRET edge function secret). Left unset
-- (null) is fine — send-reminders treats a missing CRON_SECRET as "no
-- check configured" rather than failing closed, so this ships working
-- with the check simply inactive until both sides are set.
select
  cron.schedule(
    'send-appointment-reminders',
    '*/15 * * * *',
    $$
    select net.http_post(
      url := 'https://etsinvmbwgvyosmvwlhc.supabase.co/functions/v1/send-reminders',
      headers := jsonb_build_object(
        'Content-Type', 'application/json',
        'x-cron-secret', coalesce(current_setting('app.cron_secret', true), '')
      ),
      body := '{}'::jsonb
    );
    $$
  )
where not exists (select 1 from cron.job where jobname = 'send-appointment-reminders');
