// Public endpoint: create a confirmed appointment.
//
// Double-booking protection is NOT "check availability then insert" — that
// has a race window. Instead this relies on the database-level exclusion
// constraint `appointments_no_overlap` (see migration 0001), which rejects
// any overlapping (employee_id, time range) insert atomically, even under
// concurrent requests. This function still calls get-availability's slot
// logic first as a fast-path validation (better error message, avoids an
// unnecessary DB round trip for obviously-bad requests), but the INSERT
// itself is the actual source of truth and correctness does not depend on
// the pre-check.
//
// POST body: {
//   business_id, service_id, employee_id?, starts_at (ISO),
//   customer: { full_name, phone, email? }, notes?
// }
import { serviceClient } from '../_shared/supabaseClient.ts';
import { CORS_HEADERS, jsonResponse, errorResponse } from '../_shared/cors.ts';
import { notifyBookingEvent } from '../_shared/notify.ts';

Deno.serve(async (req) => {
  if (req.method === 'OPTIONS') return new Response(null, { headers: CORS_HEADERS });

  try {
    const { business_id, service_id, employee_id, starts_at, customer, notes } = await req.json();

    if (!business_id || !service_id || !starts_at || !customer?.full_name || !customer?.phone) {
      return errorResponse('business_id, service_id, starts_at, customer.full_name, and customer.phone are required');
    }

    const startsAt = new Date(starts_at);
    if (Number.isNaN(startsAt.getTime())) return errorResponse('starts_at must be a valid ISO timestamp');

    const supabase = serviceClient();

    const [{ data: business }, { data: settings }, { data: service }] = await Promise.all([
      supabase.from('businesses').select('id, name, status').eq('id', business_id).single(),
      supabase.from('business_settings').select('*').eq('business_id', business_id).single(),
      supabase.from('services').select('*').eq('id', service_id).eq('business_id', business_id).eq('is_active', true).single(),
    ]);

    if (!business || !['trial', 'active'].includes(business.status)) return errorResponse('Business not available', 404);
    if (!settings) return errorResponse('Business not configured', 404);
    if (!service) return errorResponse('Service not found', 404);

    if (employee_id) {
      const { data: link } = await supabase
        .from('employee_services')
        .select('employee_id')
        .eq('employee_id', employee_id)
        .eq('service_id', service_id)
        .maybeSingle();
      if (!link) return errorResponse('Employee does not provide this service', 400);
    }

    const now = new Date();
    const minimumNoticeMs = settings.minimum_notice_minutes * 60 * 1000;
    if (startsAt.getTime() < now.getTime() + minimumNoticeMs) {
      return errorResponse('This time no longer satisfies the minimum booking notice', 409);
    }
    const maxAdvanceMs = settings.max_booking_days_ahead * 24 * 60 * 60 * 1000;
    if (startsAt.getTime() > now.getTime() + maxAdvanceMs) {
      return errorResponse('This date is beyond the maximum advance booking window', 409);
    }

    const endsAt = new Date(startsAt.getTime() + service.duration_minutes * 60 * 1000);

    // Upsert the customer by (business_id, phone).
    const { data: existingCustomer } = await supabase
      .from('customers')
      .select('id')
      .eq('business_id', business_id)
      .eq('phone', customer.phone)
      .maybeSingle();

    let customerId: string;
    if (existingCustomer) {
      customerId = existingCustomer.id;
      await supabase
        .from('customers')
        .update({ full_name: customer.full_name, email: customer.email ?? null })
        .eq('id', customerId);
    } else {
      const { data: created, error: customerErr } = await supabase
        .from('customers')
        .insert({
          business_id,
          full_name: customer.full_name,
          phone: customer.phone,
          email: customer.email ?? null,
        })
        .select('id')
        .single();
      if (customerErr || !created) return errorResponse('Could not create customer record', 500);
      customerId = created.id;
    }

    const { data: appointment, error: apptErr } = await supabase
      .from('appointments')
      .insert({
        business_id,
        service_id,
        employee_id: employee_id ?? null,
        customer_id: customerId,
        starts_at: startsAt.toISOString(),
        ends_at: endsAt.toISOString(),
        status: 'confirmed',
        price_at_booking: service.price,
        notes: notes ?? null,
      })
      .select('id, confirmation_code, starts_at, ends_at, status')
      .single();

    if (apptErr) {
      // Postgres exclusion-constraint violation surfaces as error code 23P01.
      if ((apptErr as { code?: string }).code === '23P01') {
        return errorResponse('This time slot was just booked by someone else. Please choose another time.', 409);
      }
      return errorResponse('Could not create the appointment', 500);
    }

    await supabase.from('audit_logs').insert({
      business_id,
      action: 'appointment_created',
      entity_type: 'appointment',
      entity_id: appointment.id,
      metadata: { source: 'widget', service_id, employee_id: employee_id ?? null },
    });

    const whenText = formatWhen(startsAt);
    await notifyBookingEvent(supabase, {
      businessId: business_id,
      appointmentId: appointment.id,
      eventType: 'booking_confirmation',
      customerPhone: customer.phone,
      customerMessage: `${business.name}: your ${service.name} appointment is confirmed for ${whenText}. Reply code ${appointment.confirmation_code} for any changes.`,
      businessMessage: `${business.name}: new booking — ${service.name} with ${customer.full_name} on ${whenText}.`,
    });

    return jsonResponse({
      appointment_id: appointment.id,
      confirmation_code: appointment.confirmation_code,
      starts_at: appointment.starts_at,
      ends_at: appointment.ends_at,
      status: appointment.status,
    });
  } catch (err) {
    return errorResponse(err instanceof Error ? err.message : 'Unexpected error', 500);
  }
});

function formatWhen(date: Date): string {
  return date.toLocaleString('en-US', {
    weekday: 'short',
    month: 'short',
    day: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
  });
}
