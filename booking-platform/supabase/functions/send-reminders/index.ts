// Cron-triggered (via pg_cron + pg_net, see migration 0002): finds
// appointments across ALL businesses that are due for a reminder — i.e.
// starting within that business's own reminder_hours_before window, not
// yet reminded, not cancelled — sends the customer an SMS, and stamps
// reminder_sent_at so it's never sent twice even if the cron job overlaps
// itself (each row update is a single atomic UPDATE ... WHERE
// reminder_sent_at is null, so a double-run can't double-send).
//
// Not a public/widget-facing function. Deployed with verify_jwt: false
// (like the other public functions, so pg_net's plain HTTP call can reach
// it without a Supabase auth JWT), but gated by a shared secret header
// instead — CRON_SECRET, set via `supabase secrets set CRON_SECRET=...`
// and echoed in the migration's cron.schedule() call. Requests without a
// matching header are rejected before touching the database.
import { serviceClient } from '../_shared/supabaseClient.ts';
import { jsonResponse, errorResponse } from '../_shared/cors.ts';
import { notify } from '../_shared/notify.ts';

Deno.serve(async (req) => {
  const cronSecret = Deno.env.get('CRON_SECRET');
  if (cronSecret && req.headers.get('x-cron-secret') !== cronSecret) {
    return errorResponse('Unauthorized', 401);
  }

  try {
    const supabase = serviceClient();
    const now = new Date();

    // Businesses with SMS reminders enabled (business_settings) and their
    // configured reminder window (notification_settings) — two separate
    // tables, joined here since they're both business-level 1:1 settings.
    const { data: smsEnabledRows } = await supabase
      .from('business_settings')
      .select('business_id')
      .eq('sms_enabled', true);

    if (!smsEnabledRows || smsEnabledRows.length === 0) {
      return jsonResponse({ processed: 0 });
    }

    const { data: notificationSettingsRows } = await supabase
      .from('notification_settings')
      .select('business_id, reminder_hours_before')
      .in('business_id', smsEnabledRows.map((r) => r.business_id));

    let processed = 0;
    let failed = 0;

    for (const settings of notificationSettingsRows ?? []) {
      const windowEnd = new Date(now.getTime() + settings.reminder_hours_before * 60 * 60 * 1000);

      const { data: dueAppointments } = await supabase
        .from('appointments')
        .select('id, business_id, service_id, customer_id, starts_at')
        .eq('business_id', settings.business_id)
        .in('status', ['pending', 'confirmed'])
        .is('reminder_sent_at', null)
        .lte('starts_at', windowEnd.toISOString())
        .gt('starts_at', now.toISOString());

      for (const appt of dueAppointments ?? []) {
        // Atomically claim this appointment's reminder slot — if two cron
        // invocations overlap, only one UPDATE affects a row (still
        // reminder_sent_at is null), so at most one of them proceeds to send.
        const { data: claimed } = await supabase
          .from('appointments')
          .update({ reminder_sent_at: new Date().toISOString() })
          .eq('id', appt.id)
          .is('reminder_sent_at', null)
          .select('id')
          .maybeSingle();

        if (!claimed) continue; // another invocation already claimed it

        const [{ data: business }, { data: service }, { data: customer }] = await Promise.all([
          supabase.from('businesses').select('name').eq('id', appt.business_id).single(),
          supabase.from('services').select('name').eq('id', appt.service_id).single(),
          supabase.from('customers').select('full_name, phone').eq('id', appt.customer_id).single(),
        ]);
        if (!business || !service || !customer) continue;

        const whenText = new Date(appt.starts_at).toLocaleString('en-US', {
          weekday: 'short',
          month: 'short',
          day: 'numeric',
          hour: 'numeric',
          minute: '2-digit',
        });

        const result = await notify(supabase, {
          businessId: appt.business_id,
          appointmentId: appt.id,
          recipientRole: 'customer',
          recipient: customer.phone,
          eventType: 'reminder',
          message: `${business.name}: reminder — your ${service.name} appointment is on ${whenText}.`,
        });

        if (result.ok) processed++;
        else failed++;
      }
    }

    return jsonResponse({ processed, failed });
  } catch (err) {
    return errorResponse(err instanceof Error ? err.message : 'Unexpected error', 500);
  }
});
