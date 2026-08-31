import { createClient } from '@supabase/supabase-js';

// The widget is always customer-facing and unauthenticated — it only ever
// uses the anon key, and never establishes a Supabase auth session. All
// writes (create/cancel/reschedule booking) go through edge functions
// using the service role server-side; the widget never reads or writes
// customers/appointments tables directly (RLS has no anon policy on those).
export const supabase = createClient(
  import.meta.env.VITE_SUPABASE_URL,
  import.meta.env.VITE_SUPABASE_ANON_KEY,
  { auth: { persistSession: false } }
);
