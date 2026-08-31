// Authenticated endpoint: business owner sends an SMS announcement to
// every customer of their business (closures, price changes, etc).
//
// Unlike the other booking functions, this one is NOT public — it must be
// called with the caller's own Supabase session JWT (Authorization: Bearer
// <access_token>), and verify_jwt is left ON for this function (see
// deploy command) so an invalid/missing JWT is rejected before this code
// even runs. On top of that, this function independently re-derives the
// caller's role/business_id from their own profiles row via a
// request-scoped client — never trusts a business_id passed in the
// request body — so a customer or a different business's owner can never
// broadcast into another business's customer list, even if they guessed
// or forged a business_id in the payload.
//
// POST body: { message }
import { createClient } from 'npm:@supabase/supabase-js@2';
import { serviceClient } from '../_shared/supabaseClient.ts';
import { CORS_HEADERS, jsonResponse, errorResponse } from '../_shared/cors.ts';
import { sendSms } from '../_shared/sms.ts';

Deno.serve(async (req) => {
  if (req.method === 'OPTIONS') return new Response(null, { headers: CORS_HEADERS });

  try {
    const authHeader = req.headers.get('Authorization') || '';
    const jwt = authHeader.replace('Bearer ', '');
    if (!jwt) return errorResponse('Not authenticated', 401);

    // Request-scoped client, authenticated as the caller — used only to
    // verify who they are and look up their own profile under RLS.
    const callerClient = createClient(
      Deno.env.get('SUPABASE_URL')!,
      Deno.env.get('SUPABASE_ANON_KEY')!,
      { global: { headers: { Authorization: authHeader } } }
    );

    const { data: userData, error: userErr } = await callerClient.auth.getUser(jwt);
    if (userErr || !userData.user) return errorResponse('Not authenticated', 401);

    const { data: profile } = await callerClient
      .from('profiles')
      .select('role, business_id')
      .eq('id', userData.user.id)
      .single();

    if (!profile || profile.role !== 'owner' || !profile.business_id) {
      return errorResponse('Only a business owner can send a broadcast', 403);
    }

    const businessId = profile.business_id;

    const { message } = await req.json();
    if (!message || typeof message !== 'string' || !message.trim()) {
      return errorResponse('message is required');
    }
    if (message.length > 1500) {
      return errorResponse('message is too long (max 1500 characters)');
    }

    const supabase = serviceClient();

    const [{ data: business }, { data: settings }, { data: notificationSettings }] = await Promise.all([
      supabase.from('businesses').select('name').eq('id', businessId).single(),
      supabase.from('business_settings').select('sms_enabled').eq('business_id', businessId).single(),
      supabase.from('notification_settings').select('sms_monthly_quota').eq('business_id', businessId).single(),
    ]);

    if (!settings?.sms_enabled) return errorResponse('SMS notifications are not enabled for this business', 403);

    const { data: customers } = await supabase
      .from('customers')
      .select('id, phone')
      .eq('business_id', businessId);

    if (!customers || customers.length === 0) {
      return jsonResponse({ sent: 0, skipped: 0, failed: 0, total: 0 });
    }

    const monthStart = new Date();
    monthStart.setUTCDate(1);
    monthStart.setUTCHours(0, 0, 0, 0);

    const { count: usedThisMonth } = await supabase
      .from('notification_logs')
      .select('id', { count: 'exact', head: true })
      .eq('business_id', businessId)
      .eq('channel', 'sms')
      .eq('status', 'sent')
      .gte('created_at', monthStart.toISOString());

    const quota = notificationSettings?.sms_monthly_quota ?? 0;
    let remaining = Math.max(0, quota - (usedThisMonth ?? 0));

    const fullMessage = `${business?.name ?? 'Announcement'}: ${message.trim()}`;

    let sent = 0;
    let failed = 0;
    let skipped = 0;

    for (const customer of customers) {
      if (remaining <= 0) {
        skipped++;
        await supabase.from('notification_logs').insert({
          business_id: businessId,
          appointment_id: null,
          channel: 'sms',
          event_type: 'broadcast',
          recipient_role: 'customer',
          recipient: customer.phone,
          status: 'skipped',
          error_message: 'Monthly SMS quota exceeded',
        });
        continue;
      }

      const result = await sendSms(customer.phone, fullMessage);
      remaining--;

      if (result.ok) sent++;
      else failed++;

      await supabase.from('notification_logs').insert({
        business_id: businessId,
        appointment_id: null,
        channel: 'sms',
        event_type: 'broadcast',
        recipient_role: 'customer',
        recipient: customer.phone,
        status: result.ok ? 'sent' : 'failed',
        error_message: result.error ?? null,
      });
    }

    await supabase.from('audit_logs').insert({
      business_id: businessId,
      actor_id: userData.user.id,
      actor_role: 'owner',
      action: 'broadcast_sms_sent',
      entity_type: 'business',
      entity_id: businessId,
      metadata: { total: customers.length, sent, failed, skipped, message: fullMessage },
    });

    return jsonResponse({ sent, failed, skipped, total: customers.length });
  } catch (err) {
    return errorResponse(err instanceof Error ? err.message : 'Unexpected error', 500);
  }
});
