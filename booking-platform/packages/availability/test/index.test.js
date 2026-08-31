const { test } = require('node:test');
const assert = require('node:assert/strict');
const { getAvailableSlots, dateCouldHaveAvailability } = require('../src/index');

// Sunday 2026-08-30... let's use a known Sunday: 2026-08-30 is a Sunday.
const SUNDAY = '2026-08-30';
const MONDAY = '2026-08-31';

const baseWorkingHours = [
  { weekday: 0, start_time: '09:00', end_time: '17:00' }, // Sunday
  { weekday: 1, start_time: '09:00', end_time: '13:00' }, // Monday split shift part 1
  { weekday: 1, start_time: '16:00', end_time: '20:00' }, // Monday split shift part 2
];

function baseParams(overrides = {}) {
  return {
    date: SUNDAY,
    serviceDurationMinutes: 30,
    slotIntervalMinutes: 30,
    minimumNoticeMinutes: 0,
    maxBookingDaysAhead: 60,
    now: new Date('2026-08-25T00:00:00Z'),
    workingHours: baseWorkingHours,
    holidays: [],
    blockedTimes: [],
    existingAppointments: [],
    ...overrides,
  };
}

test('produces slots across the full working window at the configured interval', () => {
  const slots = getAvailableSlots(baseParams());
  assert.equal(slots.length, 16); // 09:00..16:30 every 30 min = 16 slots for an 8h window with 30min service
  assert.equal(slots[0].startsAt, new Date(Date.UTC(2026, 7, 30, 9, 0)).toISOString());
});

test('returns empty for a closed weekday', () => {
  const slots = getAvailableSlots(baseParams({ date: '2026-09-01' })); // Tuesday, not in workingHours
  assert.deepEqual(slots, []);
});

test('handles split shifts on the same day (two windows)', () => {
  const slots = getAvailableSlots(baseParams({ date: MONDAY }));
  const hours = slots.map((s) => new Date(s.startsAt).getUTCHours());
  assert.ok(hours.every((h) => (h >= 9 && h < 13) || (h >= 16 && h < 20)));
  assert.ok(!hours.includes(13));
  assert.ok(!hours.includes(14));
});

test('excludes slots overlapping an existing appointment', () => {
  const slots = getAvailableSlots(
    baseParams({
      existingAppointments: [
        { starts_at: new Date(Date.UTC(2026, 7, 30, 9, 0)).toISOString(), ends_at: new Date(Date.UTC(2026, 7, 30, 10, 0)).toISOString() },
      ],
    })
  );
  const hours = slots.map((s) => new Date(s.startsAt).getUTCHours() + new Date(s.startsAt).getUTCMinutes() / 60);
  assert.ok(!hours.includes(9));
  assert.ok(!hours.includes(9.5));
  assert.ok(hours.includes(10));
});

test('excludes slots overlapping a blocked time (e.g. lunch)', () => {
  const slots = getAvailableSlots(
    baseParams({
      blockedTimes: [
        { starts_at: new Date(Date.UTC(2026, 7, 30, 13, 0)).toISOString(), ends_at: new Date(Date.UTC(2026, 7, 30, 14, 0)).toISOString() },
      ],
    })
  );
  const hours = slots.map((s) => new Date(s.startsAt).getUTCHours());
  assert.ok(!hours.includes(13));
  assert.ok(!hours.includes(13.5));
});

test('returns empty on a holiday date', () => {
  const slots = getAvailableSlots(
    baseParams({ holidays: [{ starts_on: SUNDAY, ends_on: SUNDAY }] })
  );
  assert.deepEqual(slots, []);
});

test('respects minimum notice — slots before the notice window are excluded', () => {
  const slots = getAvailableSlots(
    baseParams({
      now: new Date(Date.UTC(2026, 7, 30, 8, 0)), // same-day, 8:00 UTC
      minimumNoticeMinutes: 180, // 3 hours -> earliest allowed 11:00
    })
  );
  const hours = slots.map((s) => new Date(s.startsAt).getUTCHours());
  assert.ok(!hours.includes(9));
  assert.ok(!hours.includes(10));
  assert.ok(hours.includes(11));
});

test('respects maximum advance booking window', () => {
  const slots = getAvailableSlots(
    baseParams({
      now: new Date('2026-08-25T00:00:00Z'),
      maxBookingDaysAhead: 3, // Sunday 2026-08-30 is 5 days out -> nothing bookable
    })
  );
  assert.deepEqual(slots, []);
});

test('does not offer a slot whose duration would run past the working window close', () => {
  const slots = getAvailableSlots(baseParams({ serviceDurationMinutes: 45, slotIntervalMinutes: 30 }));
  const lastSlot = slots[slots.length - 1];
  const lastEndHour = new Date(lastSlot.endsAt).getUTCHours() + new Date(lastSlot.endsAt).getUTCMinutes() / 60;
  assert.ok(lastEndHour <= 17);
});

test('dateCouldHaveAvailability returns false for a holiday and true for an open weekday', () => {
  const params = {
    now: new Date('2026-08-25T00:00:00Z'),
    maxBookingDaysAhead: 60,
    workingHours: baseWorkingHours,
    holidays: [{ starts_on: SUNDAY, ends_on: SUNDAY }],
  };
  assert.equal(dateCouldHaveAvailability({ ...params, date: SUNDAY }), false);
  assert.equal(dateCouldHaveAvailability({ ...params, date: MONDAY }), true);
});
