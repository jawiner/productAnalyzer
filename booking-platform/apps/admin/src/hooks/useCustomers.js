import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { supabase } from '@/lib/supabaseClient';
import { useAuth } from '@/lib/AuthContext';

export function useCustomers(search) {
  const { businessId } = useAuth();
  return useQuery({
    queryKey: ['customers', businessId, search],
    enabled: !!businessId,
    queryFn: async () => {
      let query = supabase.from('customers').select('*').eq('business_id', businessId).order('full_name', { ascending: true });
      if (search && search.trim()) {
        const term = search.trim();
        query = query.or(`full_name.ilike.%${term}%,phone.ilike.%${term}%`);
      }
      const { data, error } = await query;
      if (error) throw error;
      return data;
    },
  });
}

export function useCustomerCount() {
  const { businessId } = useAuth();
  return useQuery({
    queryKey: ['customers_count', businessId],
    enabled: !!businessId,
    queryFn: async () => {
      const { count, error } = await supabase
        .from('customers')
        .select('id', { count: 'exact', head: true })
        .eq('business_id', businessId);
      if (error) throw error;
      return count ?? 0;
    },
  });
}

export function useCustomer(id) {
  return useQuery({
    queryKey: ['customer', id],
    enabled: !!id,
    queryFn: async () => {
      const { data, error } = await supabase.from('customers').select('*').eq('id', id).single();
      if (error) throw error;
      return data;
    },
  });
}

export function useCustomerAppointments(id) {
  return useQuery({
    queryKey: ['customer-appointments', id],
    enabled: !!id,
    queryFn: async () => {
      const { data, error } = await supabase
        .from('appointments')
        .select('*, services(id, name), employees(id, name)')
        .eq('customer_id', id)
        .order('starts_at', { ascending: false });
      if (error) throw error;
      return data;
    },
  });
}

export function useSaveCustomer() {
  const { businessId } = useAuth();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (customer) => {
      const payload = { ...customer, business_id: businessId };
      const { data, error } = await supabase.from('customers').upsert(payload).select().single();
      if (error) throw error;
      return data;
    },
    onSuccess: (data) => {
      qc.invalidateQueries({ queryKey: ['customers', businessId] });
      qc.invalidateQueries({ queryKey: ['customer', data.id] });
    },
  });
}
