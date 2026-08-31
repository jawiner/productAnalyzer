// Public endpoint: customer-initiated cancellation via confirmation code.
// Business staff cancel through the authenticated dashboard API instead
// (direct table update under RLS), not this function.
//
// POST body: { confirmation_code, reason? }
import { serviceClient } from '../_shared/supabaseClient.ts';
import { CORS_HEADERS, jsonResponse, errorResponse } from '../_shared/cors.ts';
import { notifyBookingEvent } from '../_shared/notify.ts';

Deno.serve(async (req) => {
  if (req.method === 'OPTIONS') return new Response(null, { headers: CORS_HEADERS });

  try {
    const { confirmation_code, reason } = await req.json();
    if (!confirmation_code) return errorResponse('confirmation_code is required');

    const supabase = serviceClient();

    const { data: appointment } = await supabase
      .from('appointments')
      .select('id, business_id, starts_at, status, service_id, customer_id')
      .eq('confirmation_code', confirmation_code)
      .maybeSingle();

    if (!appointment) return errorResponse('Appointment not found', 404);
    if (appointment.status === 'cancelled') return errorResponse('Appointment is already cancelled', 409);

    const { data: settings } = await supabase
      .from('business_settings')
      .select('allow_cancellation, cancellation_notice_minutes')
      .eq('business_id', appointment.business_id)
      .single();

    if (!settings?.allow_cancellation) return errorResponse('This business does not allow self-service cancellation', 403);

    const noticeMs = settings.cancellation_notice_minutes * 60 * 1000;
    const startsAt = new Date(appointment.starts_at).getTime();
    if (startsAt - Date.now() < noticeMs) {
      return errorResponse('Too close to the appointment time to cancel online. Please contact the business directly.', 409);
    }

    const { error } = await supabase
      .from('appointments')
      .update({ status: 'cancelled', cancelled_at: new Date().toISOString(), cancellation_reason: reason ?? null })
      .eq('id', appointment.id);
    if (error) return errorResponse('Could not cancel the appointment', 500);

    await supabase.from('audit_logs').insert({
      business_id: appointment.business_id,
      action: 'appointment_cancelled',
      entity_type: 'appointment',
      entity_id: appointment.id,
      metadata: { source: 'widget', reason: reason ?? null },
    });

    const [{ data: business }, { data: service }, { data: customer }] = await Promise.all([
      supabase.from('businesses').select('name').eq('id', appointment.business_id).single(),
      supabase.from('services').select('name').eq('id', appointment.service_id).single(),
      supabase.from('customers').select('full_name, phone').eq('id', appointment.customer_id).single(),
    ]);

    if (business && service && customer) {
      const whenText = new Date(appointment.starts_at).toLocaleString('en-US', {
        weekday: 'short',
        month: 'short',
        day: 'numeric',
        hour: 'numeric',
        minute: '2-digit',
      });
      await notifyBookingEvent(supabase, {
        businessId: appointment.business_id,
        appointmentId: appointment.id,
        eventType: 'cancellation',
        customerPhone: customer.phone,
        customerMessage: `${business.name}: your ${service.name} appointment on ${whenText} has been cancelled.`,
        businessMessage: `${business.name}: ${customer.full_name} cancelled their ${service.name} appointment on ${whenText}.`,
      });
    }

    return jsonResponse({ status: 'cancelled' });
  } catch (err) {
    return errorResponse(err instanceof Error ? err.message : 'Unexpected error', 500);
  }
});
