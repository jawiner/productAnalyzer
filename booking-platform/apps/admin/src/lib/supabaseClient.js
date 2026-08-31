import { createClient } from '@supabase/supabase-js';

// Unlike the widget, the admin app is fully authenticated — owners/staff
// sign in with Supabase Auth (email/password) and every table read/write
// goes through RLS as that user, using the anon key + their session JWT
// (never the service role key, which must never ship to a browser bundle).
export const supabase = createClient(
  import.meta.env.VITE_SUPABASE_URL,
  import.meta.env.VITE_SUPABASE_ANON_KEY,
  { auth: { persistSession: true, autoRefreshToken: true } }
);
