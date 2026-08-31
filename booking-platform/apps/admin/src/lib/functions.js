// Thin wrapper for calling booking edge functions, mirroring
// apps/widget/src/lib/functions.js. The admin app uses the public ones
// only for get-availability (to help staff pick a valid slot when creating
// a manual appointment) — everything else goes through direct
// authenticated table access under RLS, EXCEPT send-broadcast, which must
// be an edge function since it fans out server-side to every customer's
// phone number using the Twilio secret (never exposed to the browser).
import { supabase } from '@/lib/supabaseClient';

const BASE = `${import.meta.env.VITE_SUPABASE_URL}/functions/v1`;
const ANON_KEY = import.meta.env.VITE_SUPABASE_ANON_KEY;

async function callFn(name, body, { authenticated = false } = {}) {
  const headers = { 'Content-Type': 'application/json', apikey: ANON_KEY };

  if (authenticated) {
    const {
      data: { session },
    } = await supabase.auth.getSession();
    if (!session) {
      const err = new Error('Not authenticated');
      err.status = 401;
      throw err;
    }
    headers.Authorization = `Bearer ${session.access_token}`;
  }

  let res;
  try {
    res = await fetch(`${BASE}/${name}`, {
      method: 'POST',
      headers,
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
  sendBroadcast: (payload) => callFn('send-broadcast', payload, { authenticated: true }),
};
