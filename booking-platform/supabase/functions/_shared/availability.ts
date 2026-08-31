// Deno/TypeScript port of packages/availability/src/index.js.
//
// KEEP IN SYNC: this is a straight port so the edge function's availability
// logic matches the tested Node package byte-for-byte in behavior. If you
// change the algorithm, change it in packages/availability/src/index.js
// first (where the test suite lives), then mirror the change here.
// `packages/availability/scripts/check-drift.js` diffs the two function
// bodies structurally and fails CI if they've drifted.

export interface WorkingHourRow {
  weekday: number;
  start_time: string;
  end_time: string;
}
export interface HolidayRow {
  starts_on: string;
  ends_on: string;
}
export interface BlockedTimeRow {
  starts_at: string;
  ends_at: string;
}
export interface AppointmentRow {
  starts_at: string;
  ends_at: string;
}
export interface Slot {
  startsAt: string;
  endsAt: string;
}

const MINUTE_MS = 60 * 1000;

function timeToMinutes(t: string): number {
  const [h, m] = t.split(':').map(Number);
  return h * 60 + m;
}

function dateAtMinutes(dateStr: string, minutes: number): Date {
  const [y, mo, d] = dateStr.split('-').map(Number);
  const dt = new Date(Date.UTC(y, mo - 1, d, 0, 0, 0));
  dt.setUTCMinutes(dt.getUTCMinutes() + minutes);
  return dt;
}

function rangesOverlap(aStart: Date, aEnd: Date, bStart: Date, bEnd: Date): boolean {
  return aStart < bEnd && bStart < aEnd;
}

function isHoliday(date: string, holidays: HolidayRow[]): boolean {
  return holidays.some((h) => date >= h.starts_on && date <= h.ends_on);
}

export function getAvailableSlots(params: {
  date: string;
  serviceDurationMinutes: number;
  slotIntervalMinutes: number;
  minimumNoticeMinutes: number;
  maxBookingDaysAhead: number;
  now: Date;
  workingHours: WorkingHourRow[];
  holidays: HolidayRow[];
  blockedTimes: BlockedTimeRow[];
  existingAppointments: AppointmentRow[];
}): Slot[] {
  const {
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
  } = params;

  if (isHoliday(date, holidays)) return [];

  const maxDate = new Date(now.getTime() + maxBookingDaysAhead * 24 * 60 * MINUTE_MS);
  const dateStart = dateAtMinutes(date, 0);
  if (dateStart > maxDate) return [];

  const weekday = new Date(`${date}T00:00:00Z`).getUTCDay();
  const dayWindows = workingHours.filter((wh) => wh.weekday === weekday);
  if (dayWindows.length === 0) return [];

  const earliestAllowed = new Date(now.getTime() + minimumNoticeMinutes * MINUTE_MS);

  const busyRanges: [Date, Date][] = [
    ...blockedTimes.map((b): [Date, Date] => [new Date(b.starts_at), new Date(b.ends_at)]),
    ...existingAppointments.map((a): [Date, Date] => [new Date(a.starts_at), new Date(a.ends_at)]),
  ];

  const slots: Slot[] = [];

  for (const window of dayWindows) {
    const windowStartMin = timeToMinutes(window.start_time);
    const windowEndMin = timeToMinutes(window.end_time);

    for (
      let slotStartMin = windowStartMin;
      slotStartMin + serviceDurationMinutes <= windowEndMin;
      slotStartMin += slotIntervalMinutes
    ) {
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
