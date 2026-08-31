import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { supabase } from '@/lib/supabaseClient';
import { useAuth } from '@/lib/AuthContext';

const APPT_SELECT = '*, customers(id, full_name, phone, email), services(id, name, duration_minutes, price), employees(id, name)';

// Appointments in [startIso, endIso) for the calendar/dashboard. RLS already
// scopes staff to their own employee_id — no need to filter client-side.
export function useAppointmentsRange(startIso, endIso) {
  const { businessId } = useAuth();
  return useQuery({
    queryKey: ['appointments', businessId, startIso, endIso],
    enabled: !!businessId && !!startIso && !!endIso,
    queryFn: async () => {
      const { data, error } = await supabase
        .from('appointments')
        .select(APPT_SELECT)
        .eq('business_id', businessId)
        .lt('starts_at', endIso)
        .gte('starts_at', startIso)
        .order('starts_at', { ascending: true });
      if (error) throw error;
      return data;
    },
  });
}

export function useAppointment(id) {
  return useQuery({
    queryKey: ['appointment', id],
    enabled: !!id,
    queryFn: async () => {
      const { data, error } = await supabase.from('appointments').select(APPT_SELECT).eq('id', id).single();
      if (error) throw error;
      return data;
    },
  });
}

function invalidateAppointments(qc, businessId) {
  qc.invalidateQueries({ queryKey: ['appointments', businessId] });
  qc.invalidateQueries({ queryKey: ['appointment'] });
}

export function useCreateAppointment() {
  const { businessId } = useAuth();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (appt) => {
      const payload = { ...appt, business_id: businessId };
      const { data, error } = await supabase.from('appointments').insert(payload).select().single();
      if (error) throw error;
      return data;
    },
    onSuccess: () => invalidateAppointments(qc, businessId),
  });
}

export function useUpdateAppointment() {
  const { businessId } = useAuth();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, ...patch }) => {
      const { data, error } = await supabase.from('appointments').update(patch).eq('id', id).select().single();
      if (error) throw error;
      return data;
    },
    onSuccess: () => invalidateAppointments(qc, businessId),
  });
}

export function useCancelAppointment() {
  const { businessId } = useAuth();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, reason }) => {
      const { data, error } = await supabase
        .from('appointments')
        .update({ status: 'cancelled', cancelled_at: new Date().toISOString(), cancellation_reason: reason || null })
        .eq('id', id)
        .select()
        .single();
      if (error) throw error;
      return data;
    },
    onSuccess: () => invalidateAppointments(qc, businessId),
  });
}
