// Public endpoint: compute bookable slots for a service (+ optional employee)
// on a given date. This is the authoritative availability calculation —
// the widget must never compute slots itself from raw data, only display
// what this function returns.
//
// POST body: { business_id, service_id, employee_id?, date }
import { serviceClient } from '../_shared/supabaseClient.ts';
import { CORS_HEADERS, jsonResponse, errorResponse } from '../_shared/cors.ts';
import { getAvailableSlots } from '../_shared/availability.ts';

Deno.serve(async (req) => {
  if (req.method === 'OPTIONS') return new Response(null, { headers: CORS_HEADERS });

  try {
    const { business_id, service_id, employee_id, date } = await req.json();
    if (!business_id || !service_id || !date) {
      return errorResponse('business_id, service_id, and date are required');
    }
    if (!/^\d{4}-\d{2}-\d{2}$/.test(date)) {
      return errorResponse('date must be YYYY-MM-DD');
    }

    const supabase = serviceClient();

    const [{ data: business }, { data: settings }, { data: service }] = await Promise.all([
      supabase.from('businesses').select('id, status').eq('id', business_id).single(),
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

    const dayStart = `${date}T00:00:00.000Z`;
    const dayEnd = `${date}T23:59:59.999Z`;

    // Fetch both employee-specific and business-level default hours, then
    // prefer the employee's own rows if any exist for this weekday, falling
    // back to the business default otherwise (handled after the query).
    const workingHoursQuery = supabase
      .from('working_hours')
      .select('weekday, start_time, end_time, employee_id')
      .eq('business_id', business_id)
      .or(employee_id ? `employee_id.is.null,employee_id.eq.${employee_id}` : 'employee_id.is.null');

    const holidaysQuery = supabase
      .from('holidays')
      .select('starts_on, ends_on')
      .eq('business_id', business_id)
      .lte('starts_on', date)
      .gte('ends_on', date)
      .or(employee_id ? `employee_id.is.null,employee_id.eq.${employee_id}` : 'employee_id.is.null');

    const blockedTimesQuery = supabase
      .from('blocked_times')
      .select('starts_at, ends_at')
      .eq('business_id', business_id)
      .lt('starts_at', dayEnd)
      .gt('ends_at', dayStart)
      .or(employee_id ? `employee_id.is.null,employee_id.eq.${employee_id}` : 'employee_id.is.null');

    // When no employee is specified, the business has no per-employee
    // capacity split for this booking — treat the business itself as a
    // single resource, so any existing appointment for this service (by
    // any employee) blocks that slot too.
    let appointmentsQuery = supabase
      .from('appointments')
      .select('starts_at, ends_at')
      .eq('business_id', business_id)
      .neq('status', 'cancelled')
      .lt('starts_at', dayEnd)
      .gt('ends_at', dayStart);
    appointmentsQuery = employee_id
      ? appointmentsQuery.eq('employee_id', employee_id)
      : appointmentsQuery.eq('service_id', service_id);

    const [{ data: workingHours }, { data: holidays }, { data: blockedTimes }, { data: existingAppointments }] = await Promise.all([
      workingHoursQuery,
      holidaysQuery,
      blockedTimesQuery,
      appointmentsQuery,
    ]);

    const allHours = workingHours ?? [];
    const employeeHours = employee_id ? allHours.filter((h) => h.employee_id === employee_id) : [];
    const businessHours = allHours.filter((h) => h.employee_id === null);
    const effectiveHours = employeeHours.length > 0 ? employeeHours : businessHours;

    const slots = getAvailableSlots({
      date,
      serviceDurationMinutes: service.duration_minutes,
      slotIntervalMinutes: settings.slot_interval_minutes,
      minimumNoticeMinutes: settings.minimum_notice_minutes,
      maxBookingDaysAhead: settings.max_booking_days_ahead,
      now: new Date(),
      workingHours: effectiveHours,
      holidays: holidays ?? [],
      blockedTimes: blockedTimes ?? [],
      existingAppointments: existingAppointments ?? [],
    });

    return jsonResponse({ slots });
  } catch (err) {
    return errorResponse(err instanceof Error ? err.message : 'Unexpected error', 500);
  }
});
