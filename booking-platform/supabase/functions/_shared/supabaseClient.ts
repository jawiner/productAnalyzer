import { createClient } from 'npm:@supabase/supabase-js@2';

// Service-role client — bypasses RLS. Only ever used inside edge functions,
// never shipped to the browser. Public/anon-facing functions (get-availability,
// create-booking, cancel-booking, reschedule-booking) rely on this client plus
// their own explicit business_id/tenant checks, since RLS can't protect
// server-side logic that must read/write across those boundaries by design
// (e.g. checking availability requires reading other customers' appointment
// times without exposing them).
export function serviceClient() {
  return createClient(
    Deno.env.get('SUPABASE_URL')!,
    Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!
  );
}
