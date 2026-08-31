// Lightweight client-side heuristic for de-emphasizing calendar dates that
// definitely have zero availability (closed weekday, holiday, or beyond the
// max advance-booking window). This mirrors `dateCouldHaveAvailability` from
// packages/availability/src/index.js (which is CommonJS and not consumable
// from a browser ESM bundle, so the logic is ported here rather than
// imported). It is a HINT only — it looks at working_hours/holidays, not
// blocked_times or existing appointments, so it can say "maybe available"
// for a date that turns out to have zero slots. get-availability is always
// the authoritative source; this only decides which calendar cells to gray
// out before the user picks a date.
const MINUTE_MS = 60 * 1000;

function isHoliday(date, holidays) {
  return holidays.some((h) => date >= h.starts_on && date <= h.ends_on);
}

export function dateCouldHaveAvailability({ date, now, maxBookingDaysAhead, workingHours, holidays }) {
  if (isHoliday(date, holidays)) return false;
  const maxDate = new Date(now.getTime() + maxBookingDaysAhead * 24 * 60 * MINUTE_MS);
  const dateStart = new Date(`${date}T00:00:00.000Z`);
  if (dateStart > maxDate) return false;
  const weekday = new Date(`${date}T00:00:00Z`).getUTCDay();
  return workingHours.some((wh) => wh.weekday === weekday);
}
