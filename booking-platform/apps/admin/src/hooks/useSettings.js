import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { supabase } from '@/lib/supabaseClient';
import { useAuth } from '@/lib/AuthContext';

export function useBusinessSettings() {
  const { businessId } = useAuth();
  return useQuery({
    queryKey: ['business_settings', businessId],
    enabled: !!businessId,
    queryFn: async () => {
      const { data, error } = await supabase.from('business_settings').select('*').eq('business_id', businessId).single();
      if (error) throw error;
      return data;
    },
  });
}

export function useSaveBusinessSettings() {
  const { businessId } = useAuth();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (settings) => {
      const { data, error } = await supabase
        .from('business_settings')
        .upsert({ ...settings, business_id: businessId })
        .select()
        .single();
      if (error) throw error;
      return data;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ['business_settings', businessId] }),
  });
}

export function useNotificationSettings() {
  const { businessId } = useAuth();
  return useQuery({
    queryKey: ['notification_settings', businessId],
    enabled: !!businessId,
    queryFn: async () => {
      const { data, error } = await supabase.from('notification_settings').select('*').eq('business_id', businessId).single();
      if (error) throw error;
      return data;
    },
  });
}

export function useSaveNotificationSettings() {
  const { businessId } = useAuth();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (settings) => {
      const { data, error } = await supabase
        .from('notification_settings')
        .upsert({ ...settings, business_id: businessId })
        .select()
        .single();
      if (error) throw error;
      return data;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ['notification_settings', businessId] }),
  });
}

export function useSmsUsageThisMonth() {
  const { businessId } = useAuth();
  return useQuery({
    queryKey: ['sms_usage_this_month', businessId],
    enabled: !!businessId,
    queryFn: async () => {
      const monthStart = new Date();
      monthStart.setUTCDate(1);
      monthStart.setUTCHours(0, 0, 0, 0);
      const { count, error } = await supabase
        .from('notification_logs')
        .select('id', { count: 'exact', head: true })
        .eq('business_id', businessId)
        .eq('channel', 'sms')
        .eq('status', 'sent')
        .gte('created_at', monthStart.toISOString());
      if (error) throw error;
      return count ?? 0;
    },
  });
}

export function useBusinessTheme() {
  const { businessId } = useAuth();
  return useQuery({
    queryKey: ['business_theme', businessId],
    enabled: !!businessId,
    queryFn: async () => {
      const { data, error } = await supabase.from('business_themes').select('*').eq('business_id', businessId).single();
      if (error) throw error;
      return data;
    },
  });
}

export function useSaveBusinessTheme() {
  const { businessId } = useAuth();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (theme) => {
      const { data, error } = await supabase
        .from('business_themes')
        .upsert({ ...theme, business_id: businessId })
        .select()
        .single();
      if (error) throw error;
      return data;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ['business_theme', businessId] }),
  });
}

export function useBusinessHours() {
  const { businessId } = useAuth();
  return useQuery({
    queryKey: ['business_hours', businessId],
    enabled: !!businessId,
    queryFn: async () => {
      const { data, error } = await supabase
        .from('working_hours')
        .select('*')
        .eq('business_id', businessId)
        .is('employee_id', null)
        .order('weekday')
        .order('start_time');
      if (error) throw error;
      return data;
    },
  });
}

export function useBusinessHolidays() {
  const { businessId } = useAuth();
  return useQuery({
    queryKey: ['business_holidays', businessId],
    enabled: !!businessId,
    queryFn: async () => {
      const { data, error } = await supabase
        .from('holidays')
        .select('*')
        .eq('business_id', businessId)
        .is('employee_id', null)
        .order('starts_on');
      if (error) throw error;
      return data;
    },
  });
}

export function useBusinessBlockedTimes() {
  const { businessId } = useAuth();
  return useQuery({
    queryKey: ['business_blocked_times', businessId],
    enabled: !!businessId,
    queryFn: async () => {
      const { data, error } = await supabase
        .from('blocked_times')
        .select('*')
        .eq('business_id', businessId)
        .is('employee_id', null)
        .order('starts_at');
      if (error) throw error;
      return data;
    },
  });
}

export function useSaveBlockedTimes() {
  const { businessId } = useAuth();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (rows) => {
      let delQuery = supabase.from('blocked_times').delete().eq('business_id', businessId).is('employee_id', null);
      const { error: delErr } = await delQuery;
      if (delErr) throw delErr;
      if (rows.length > 0) {
        const payload = rows.map((r) => ({ ...r, business_id: businessId, employee_id: null }));
        const { error: insErr } = await supabase.from('blocked_times').insert(payload);
        if (insErr) throw insErr;
      }
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ['business_blocked_times', businessId] }),
  });
}
