// Notification dispatch + logging, shared by every edge function that
// creates/changes an appointment. Always writes a notification_logs row
// (audit trail, visible to the business owner in the admin dashboard)
// regardless of whether sending succeeds — a 'failed' row with an
// error_message is itself useful signal, not just a side effect to hide.
import type { SupabaseClient } from 'npm:@supabase/supabase-js@2';
import { sendSms } from './sms.ts';

// Monthly SMS quota check — counts this-calendar-month 'sent' rows against
// notification_settings.sms_monthly_quota. This is a count-then-insert
// check, not an atomic constraint (unlike the appointments double-booking
// guard): under heavy concurrent sends the count could overshoot the quota
// by a handful of messages before the cap takes effect. That's an
// acceptable tradeoff here — a modest cost overrun, not a correctness bug
// like a double-booked appointment — and keeps this simple rather than
// requiring a Postgres-side atomic counter for what is fundamentally a
// soft cost-control cap, not a hard business invariant.
async function isOverQuota(supabase: SupabaseClient, businessId: string): Promise<boolean> {
  const { data: settings } = await supabase
    .from('notification_settings')
    .select('sms_monthly_quota')
    .eq('business_id', businessId)
    .single();

  if (!settings) return false;

  const monthStart = new Date();
  monthStart.setUTCDate(1);
  monthStart.setUTCHours(0, 0, 0, 0);

  const { count } = await supabase
    .from('notification_logs')
    .select('id', { count: 'exact', head: true })
    .eq('business_id', businessId)
    .eq('channel', 'sms')
    .eq('status', 'sent')
    .gte('created_at', monthStart.toISOString());

  return (count ?? 0) >= settings.sms_monthly_quota;
}

export async function notify(
  supabase: SupabaseClient,
  params: {
    businessId: string;
    appointmentId: string | null;
    recipientRole: 'customer' | 'business';
    recipient: string;
    eventType: 'booking_confirmation' | 'reminder' | 'cancellation' | 'reschedule';
    message: string;
  }
) {
  const { businessId, appointmentId, recipientRole, recipient, eventType, message } = params;

  if (await isOverQuota(supabase, businessId)) {
    await supabase.from('notification_logs').insert({
      business_id: businessId,
      appointment_id: appointmentId,
      channel: 'sms',
      event_type: eventType,
      recipient_role: recipientRole,
      recipient,
      status: 'skipped',
      error_message: 'Monthly SMS quota exceeded',
    });
    return { ok: false, error: 'Monthly SMS quota exceeded' };
  }

  const result = await sendSms(recipient, message);

  await supabase.from('notification_logs').insert({
    business_id: businessId,
    appointment_id: appointmentId,
    channel: 'sms',
    event_type: eventType,
    recipient_role: recipientRole,
    recipient,
    status: result.ok ? 'sent' : 'failed',
    error_message: result.error ?? null,
  });

  return result;
}

// Sends both the customer-facing and business-facing SMS for a booking
// event, respecting business_settings.sms_enabled /
// notify_business_on_new_booking. Never throws — a notification failure
// must never fail the booking operation itself.
export async function notifyBookingEvent(
  supabase: SupabaseClient,
  params: {
    businessId: string;
    appointmentId: string;
    eventType: 'booking_confirmation' | 'cancellation' | 'reschedule';
    customerPhone: string;
    customerMessage: string;
    businessMessage: string;
  }
) {
  try {
    const { data: settings } = await supabase
      .from('business_settings')
      .select('sms_enabled, notify_business_on_new_booking, business_notification_phone')
      .eq('business_id', params.businessId)
      .single();

    if (!settings?.sms_enabled) return;

    await notify(supabase, {
      businessId: params.businessId,
      appointmentId: params.appointmentId,
      recipientRole: 'customer',
      recipient: params.customerPhone,
      eventType: params.eventType,
      message: params.customerMessage,
    });

    if (settings.notify_business_on_new_booking && settings.business_notification_phone) {
      await notify(supabase, {
        businessId: params.businessId,
        appointmentId: params.appointmentId,
        recipientRole: 'business',
        recipient: settings.business_notification_phone,
        eventType: params.eventType,
        message: params.businessMessage,
      });
    }
  } catch {
    // Swallow — notification failures must never surface as booking failures.
  }
}
