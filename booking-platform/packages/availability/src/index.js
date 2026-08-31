// Pure availability engine — no I/O, no Supabase client. Given the raw
// configuration rows (working hours, holidays, blocked times, existing
// appointments) for a business/employee/service/date, computes the list of
// bookable start times. Deterministic and independently testable.
//
// This is the single source of truth for slot logic. The `get-availability`
// edge function is a thin wrapper that fetches rows from Postgres and calls
// this module — so server and any local preview UI stay in perfect sync by
// construction, not by convention.

/**
 * @typedef {{ weekday: number, start_time: string, end_time: string }} WorkingHourRow
 * @typedef {{ starts_on: string, ends_on: string }} HolidayRow
 * @typedef {{ starts_at: string, ends_at: string }} BlockedTimeRow
 * @typedef {{ starts_at: string, ends_at: string }} AppointmentRow
 */

const MINUTE_MS = 60 * 1000;

function timeToMinutes(t) {
  const [h, m] = t.split(':').map(Number);
  return h * 60 + m;
}

function dateAtMinutes(dateStr, minutes) {
  // dateStr: 'YYYY-MM-DD'. Builds a Date representing that local wall-clock
  // time; caller is responsible for treating all inputs as the business's
  // timezone (see getAvailableSlots' `now` / date handling notes below).
  const [y, mo, d] = dateStr.split('-').map(Number);
  const dt = new Date(Date.UTC(y, mo - 1, d, 0, 0, 0));
  dt.setUTCMinutes(dt.getUTCMinutes() + minutes);
  return dt;
}

function rangesOverlap(aStart, aEnd, bStart, bEnd) {
  return aStart < bEnd && bStart < aEnd;
}

/**
 * Compute available start times for a single date.
 *
 * All date/time inputs and outputs are treated as UTC instants that already
 * represent the business's local wall-clock time (i.e. the caller is
 * responsible for timezone conversion before calling in, and after calling
 * out — this module does no timezone math itself, only interval arithmetic).
 *
 * @param {object} params
 * @param {string} params.date 'YYYY-MM-DD' — the calendar date being queried
 * @param {number} params.serviceDurationMinutes
 * @param {number} params.slotIntervalMinutes
 * @param {number} params.minimumNoticeMinutes
 * @param {number} params.maxBookingDaysAhead
 * @param {Date} params.now current instant, for minimum-notice / max-advance checks
 * @param {WorkingHourRow[]} params.workingHours rows already filtered to the right business/employee scope
 * @param {HolidayRow[]} params.holidays rows already filtered to the right scope
 * @param {BlockedTimeRow[]} params.blockedTimes rows already filtered to the right scope
 * @param {AppointmentRow[]} params.existingAppointments non-cancelled appointments for the relevant employee (or business, if no employee)
 * @returns {{ startsAt: string, endsAt: string }[]} available slots, ISO strings, sorted ascending
 */
function getAvailableSlots({
  date,
  serviceDurationMinutes,
  slotIntervalMinutes,
  minimumNoticeMinutes,
  maxBookingDaysAhead,
  now,
  workingHours,
  holidays,
  blockedTimes,
  existingAppointments,
}) {
  if (isHoliday(date, holidays)) return [];

  const maxDate = new Date(now.getTime() + maxBookingDaysAhead * 24 * 60 * MINUTE_MS);
  const dateStart = dateAtMinutes(date, 0);
  if (dateStart > maxDate) return [];

  const weekday = new Date(`${date}T00:00:00Z`).getUTCDay();
  const dayWindows = workingHours.filter((wh) => wh.weekday === weekday);
  if (dayWindows.length === 0) return [];

  const earliestAllowed = new Date(now.getTime() + minimumNoticeMinutes * MINUTE_MS);

  const busyRanges = [
    ...blockedTimes.map((b) => [new Date(b.starts_at), new Date(b.ends_at)]),
    ...existingAppointments.map((a) => [new Date(a.starts_at), new Date(a.ends_at)]),
  ];

  const slots = [];

  for (const window of dayWindows) {
    const windowStartMin = timeToMinutes(window.start_time);
    const windowEndMin = timeToMinutes(window.end_time);

    for (let slotStartMin = windowStartMin; slotStartMin + serviceDurationMinutes <= windowEndMin; slotStartMin += slotIntervalMinutes) {
      const slotStart = dateAtMinutes(date, slotStartMin);
      const slotEnd = dateAtMinutes(date, slotStartMin + serviceDurationMinutes);

      if (slotStart < earliestAllowed) continue;
      if (slotStart > maxDate) continue;

      const conflicts = busyRanges.some(([bStart, bEnd]) => rangesOverlap(slotStart, slotEnd, bStart, bEnd));
      if (conflicts) continue;

      slots.push({ startsAt: slotStart.toISOString(), endsAt: slotEnd.toISOString() });
    }
  }

  return slots;
}

function isHoliday(date, holidays) {
  return holidays.some((h) => date >= h.starts_on && date <= h.ends_on);
}

/**
 * Whether a date could possibly contain any available slot, without
 * computing full slot details — used to gray out calendar dates cheaply.
 * Callers should still treat this as a hint; getAvailableSlots is
 * authoritative.
 */
function dateCouldHaveAvailability({ date, now, maxBookingDaysAhead, workingHours, holidays }) {
  if (isHoliday(date, holidays)) return false;
  const maxDate = new Date(now.getTime() + maxBookingDaysAhead * 24 * 60 * MINUTE_MS);
  const dateStart = dateAtMinutes(date, 0);
  if (dateStart > maxDate) return false;
  const weekday = new Date(`${date}T00:00:00Z`).getUTCDay();
  return workingHours.some((wh) => wh.weekday === weekday);
}

module.exports = { getAvailableSlots, dateCouldHaveAvailability };
