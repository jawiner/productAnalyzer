// Thin wrapper for calling the public edge functions, mirroring the pattern
// in talentflow/src/lib/googleCalendar.js — except the widget never has a
// Supabase auth session (customers are never authenticated), so we send
// only the anon apikey header, no Authorization bearer.
const BASE = `${import.meta.env.VITE_SUPABASE_URL}/functions/v1`;
const ANON_KEY = import.meta.env.VITE_SUPABASE_ANON_KEY;

async function callFn(name, body) {
  let res;
  try {
    res = await fetch(`${BASE}/${name}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        apikey: ANON_KEY,
      },
      body: JSON.stringify(body ?? {}),
    });
  } catch {
    const err = new Error('network_error');
    err.isNetworkError = true;
    throw err;
  }

  let data = {};
  try {
    data = await res.json();
  } catch {
    // non-JSON error body, fall through with empty data
  }

  if (!res.ok) {
    const err = new Error(data.error || 'request_failed');
    err.status = res.status;
    err.isConflict = res.status === 409;
    throw err;
  }
  return data;
}

export const bookingApi = {
  getAvailability: (payload) => callFn('get-availability', payload),
  createBooking: (payload) => callFn('create-booking', payload),
  cancelBooking: (payload) => callFn('cancel-booking', payload),
  rescheduleBooking: (payload) => callFn('reschedule-booking', payload),
  getBookingLookup: (payload) => callFn('get-booking-lookup', payload),
};
