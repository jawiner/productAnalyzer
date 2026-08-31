// Public endpoint: customer-initiated reschedule via confirmation code.
// Relies on the same exclusion constraints as create-booking for atomic
// double-booking protection on the new slot.
//
// POST body: { confirmation_code, new_starts_at (ISO) }
import { serviceClient } from '../_shared/supabaseClient.ts';
import { CORS_HEADERS, jsonResponse, errorResponse } from '../_shared/cors.ts';
import { notifyBookingEvent } from '../_shared/notify.ts';

Deno.serve(async (req) => {
  if (req.method === 'OPTIONS') return new Response(null, { headers: CORS_HEADERS });

  try {
    const { confirmation_code, new_starts_at } = await req.json();
    if (!confirmation_code || !new_starts_at) return errorResponse('confirmation_code and new_starts_at are required');

    const newStartsAt = new Date(new_starts_at);
    if (Number.isNaN(newStartsAt.getTime())) return errorResponse('new_starts_at must be a valid ISO timestamp');

    const supabase = serviceClient();

    const { data: appointment } = await supabase
      .from('appointments')
      .select('id, business_id, service_id, employee_id, status, customer_id')
      .eq('confirmation_code', confirmation_code)
      .maybeSingle();

    if (!appointment) return errorResponse('Appointment not found', 404);
    if (appointment.status === 'cancelled') return errorResponse('Cannot reschedule a cancelled appointment', 409);

    const [{ data: settings }, { data: service }] = await Promise.all([
      supabase.from('business_settings').select('allow_rescheduling, minimum_notice_minutes, max_booking_days_ahead').eq('business_id', appointment.business_id).single(),
      supabase.from('services').select('duration_minutes').eq('id', appointment.service_id).single(),
    ]);

    if (!settings?.allow_rescheduling) return errorResponse('This business does not allow self-service rescheduling', 403);
    if (!service) return errorResponse('Service not found', 404);

    const now = new Date();
    if (newStartsAt.getTime() < now.getTime() + settings.minimum_notice_minutes * 60 * 1000) {
      return errorResponse('New time does not satisfy the minimum booking notice', 409);
    }
    if (newStartsAt.getTime() > now.getTime() + settings.max_booking_days_ahead * 24 * 60 * 60 * 1000) {
      return errorResponse('New date is beyond the maximum advance booking window', 409);
    }

    const newEndsAt = new Date(newStartsAt.getTime() + service.duration_minutes * 60 * 1000);

    const { error } = await supabase
      .from('appointments')
      // reminder_sent_at resets to null: the new time is a different
      // reminder window, so it must become eligible for send-reminders again.
      .update({ starts_at: newStartsAt.toISOString(), ends_at: newEndsAt.toISOString(), status: 'confirmed', reminder_sent_at: null })
      .eq('id', appointment.id);

    if (error) {
      if ((error as { code?: string }).code === '23P01') {
        return errorResponse('That new time was just booked by someone else. Please choose another time.', 409);
      }
      return errorResponse('Could not reschedule the appointment', 500);
    }

    await supabase.from('audit_logs').insert({
      business_id: appointment.business_id,
      action: 'appointment_rescheduled',
      entity_type: 'appointment',
      entity_id: appointment.id,
      metadata: { source: 'widget', new_starts_at: newStartsAt.toISOString() },
    });

    const [{ data: business }, { data: customer }] = await Promise.all([
      supabase.from('businesses').select('name').eq('id', appointment.business_id).single(),
      supabase.from('customers').select('full_name, phone').eq('id', appointment.customer_id).single(),
    ]);

    if (business && customer) {
      const whenText = newStartsAt.toLocaleString('en-US', {
        weekday: 'short',
        month: 'short',
        day: 'numeric',
        hour: 'numeric',
        minute: '2-digit',
      });
      await notifyBookingEvent(supabase, {
        businessId: appointment.business_id,
        appointmentId: appointment.id,
        eventType: 'reschedule',
        customerPhone: customer.phone,
        customerMessage: `${business.name}: your appointment has been rescheduled to ${whenText}.`,
        businessMessage: `${business.name}: ${customer.full_name} rescheduled their appointment to ${whenText}.`,
      });
    }

    return jsonResponse({ status: 'confirmed', starts_at: newStartsAt.toISOString(), ends_at: newEndsAt.toISOString() });
  } catch (err) {
    return errorResponse(err instanceof Error ? err.message : 'Unexpected error', 500);
  }
});
