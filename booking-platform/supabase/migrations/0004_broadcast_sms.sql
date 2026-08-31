-- Business-owner broadcast SMS: send an announcement to every customer of
-- a business (e.g. "closed for travel Sept 1-5", "prices updating Oct 1").
-- Reuses the existing notification_logs table + SMS quota mechanism —
-- a broadcast burns the same monthly quota as transactional SMS, since
-- it's the same Twilio spend.

alter table public.notification_logs drop constraint notification_logs_event_type_check;
alter table public.notification_logs
  add constraint notification_logs_event_type_check
  check (event_type in ('booking_confirmation', 'reminder', 'cancellation', 'reschedule', 'broadcast'));

-- appointment_id is already nullable (a broadcast isn't tied to one
-- appointment), no schema change needed there.
