import { useQuery } from '@tanstack/react-query';
import { supabase } from '@/lib/supabaseClient';

// Reads the anon-readable tables the widget needs to render the booking
// flow. All of these have `to anon` RLS policies in migration 0001 —
// businesses (status in trial/active), business_settings, business_themes,
// services (is_active), employees (is_active), employee_services,
// working_hours, holidays, blocked_times.
export function useBusinessData(businessId) {
  return useQuery({
    queryKey: ['booking-widget', 'business-data', businessId],
    enabled: Boolean(businessId),
    staleTime: 60_000,
    retry: 1,
    queryFn: async () => {
      const [businessRes, settingsRes, themeRes, servicesRes, employeesRes, employeeServicesRes, workingHoursRes, holidaysRes] =
        await Promise.all([
          supabase.from('businesses').select('id, name, timezone, status, address, contact_email, contact_phone').eq('id', businessId).maybeSingle(),
          supabase.from('business_settings').select('*').eq('business_id', businessId).maybeSingle(),
          supabase.from('business_themes').select('*').eq('business_id', businessId).maybeSingle(),
          supabase.from('services').select('*').eq('business_id', businessId).eq('is_active', true).order('sort_order'),
          supabase.from('employees').select('*').eq('business_id', businessId).eq('is_active', true).order('sort_order'),
          supabase.from('employee_services').select('employee_id, service_id'),
          supabase.from('working_hours').select('id, weekday, start_time, end_time, employee_id').eq('business_id', businessId),
          supabase.from('holidays').select('starts_on, ends_on, employee_id').eq('business_id', businessId),
        ]);

      if (businessRes.error) throw businessRes.error;
      if (!businessRes.data || !['trial', 'active'].includes(businessRes.data.status)) {
        const err = new Error('business_not_found');
        err.isBusinessNotFound = true;
        throw err;
      }
      if (settingsRes.error) throw settingsRes.error;
      if (!settingsRes.data) {
        const err = new Error('business_not_configured');
        err.isBusinessNotFound = true;
        throw err;
      }

      return {
        business: businessRes.data,
        settings: settingsRes.data,
        theme: themeRes.data || null,
        services: servicesRes.data || [],
        employees: employeesRes.data || [],
        employeeServices: employeeServicesRes.data || [],
        workingHours: workingHoursRes.data || [],
        holidays: holidaysRes.data || [],
      };
    },
  });
}
