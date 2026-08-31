// Public endpoint: look up the minimal, non-sensitive context a customer
// needs to manage their own booking (cancel or reschedule) by confirmation
// code — since there is no anon read policy on `appointments` (by design,
// to avoid exposing other customers' bookings), the widget cannot query it
// directly. This function is the one narrow, purpose-built exception,
// returning only what's needed to render the manage-booking UI: which
// business/service/employee the appointment is for (so the reschedule flow
// can call get-availability), its current time and status, and the
// relevant booking-settings flags.
//
// POST body: { confirmation_code }
import { serviceClient } from '../_shared/supabaseClient.ts';
import { CORS_HEADERS, jsonResponse, errorResponse } from '../_shared/cors.ts';

Deno.serve(async (req) => {
  if (req.method === 'OPTIONS') return new Response(null, { headers: CORS_HEADERS });

  try {
    const { confirmation_code } = await req.json();
    if (!confirmation_code) return errorResponse('confirmation_code is required');

    const supabase = serviceClient();

    const { data: appointment } = await supabase
      .from('appointments')
      .select('business_id, service_id, employee_id, starts_at, ends_at, status')
      .eq('confirmation_code', confirmation_code)
      .maybeSingle();

    if (!appointment) return errorResponse('Appointment not found', 404);

    const [{ data: business }, { data: settings }, { data: service }, { data: employee }] = await Promise.all([
      supabase.from('businesses').select('id, name').eq('id', appointment.business_id).single(),
      supabase
        .from('business_settings')
        .select('allow_cancellation, allow_rescheduling, cancellation_notice_minutes, minimum_notice_minutes, max_booking_days_ahead, slot_interval_minutes')
        .eq('business_id', appointment.business_id)
        .single(),
      supabase.from('services').select('id, name, duration_minutes, price').eq('id', appointment.service_id).single(),
      appointment.employee_id
        ? supabase.from('employees').select('id, name').eq('id', appointment.employee_id).single()
        : Promise.resolve({ data: null }),
    ]);

    return jsonResponse({
      business: business ? { id: business.id, name: business.name } : null,
      settings,
      service,
      employee,
      appointment: {
        starts_at: appointment.starts_at,
        ends_at: appointment.ends_at,
        status: appointment.status,
      },
    });
  } catch (err) {
    return errorResponse(err instanceof Error ? err.message : 'Unexpected error', 500);
  }
});
