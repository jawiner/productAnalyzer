-- Per-business monthly SMS quota. A business that hits its cap simply
-- stops receiving further SMS until the next calendar month — bookings
-- themselves are never blocked, only the notification side effect is
-- skipped (and logged as such, so it's visible rather than silently lost).

alter table public.notification_settings
  add column sms_monthly_quota int not null default 100 check (sms_monthly_quota >= 0);

-- notification_logs already has a 'status' check constraint of
-- ('pending', 'sent', 'failed') — widen it to include 'skipped' for the
-- quota-exceeded case, distinct from 'failed' (a real send attempt that
-- errored) so the two are never conflated in the admin UI.
alter table public.notification_logs drop constraint notification_logs_status_check;
alter table public.notification_logs
  add constraint notification_logs_status_check check (status in ('pending', 'sent', 'failed', 'skipped'));

-- Fast count of this-calendar-month SMS sent (status='sent' only — skipped
-- and failed attempts don't consume quota) per business, used by the
-- notify() helper before every send and by the admin dashboard usage
-- display.
create index notification_logs_business_channel_created_idx
  on public.notification_logs(business_id, channel, created_at)
  where status = 'sent';
