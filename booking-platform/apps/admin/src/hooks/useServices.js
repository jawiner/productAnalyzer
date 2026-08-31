import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { supabase } from '@/lib/supabaseClient';
import { useAuth } from '@/lib/AuthContext';

export function useServices() {
  const { businessId } = useAuth();
  return useQuery({
    queryKey: ['services', businessId],
    enabled: !!businessId,
    queryFn: async () => {
      const { data, error } = await supabase
        .from('services')
        .select('*')
        .eq('business_id', businessId)
        .order('sort_order', { ascending: true });
      if (error) throw error;
      return data;
    },
  });
}

export function useSaveService() {
  const { businessId } = useAuth();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (service) => {
      const payload = { ...service, business_id: businessId };
      const { data, error } = await supabase.from('services').upsert(payload).select().single();
      if (error) throw error;
      return data;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ['services', businessId] }),
  });
}

export function useDeleteService() {
  const { businessId } = useAuth();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id) => {
      const { error } = await supabase.from('services').delete().eq('id', id);
      if (error) throw error;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ['services', businessId] }),
  });
}
