import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { supabase } from '@/lib/supabaseClient';
import { useAuth } from '@/lib/AuthContext';

export function useEmployees() {
  const { businessId } = useAuth();
  return useQuery({
    queryKey: ['employees', businessId],
    enabled: !!businessId,
    queryFn: async () => {
      const { data, error } = await supabase
        .from('employees')
        .select('*')
        .eq('business_id', businessId)
        .order('sort_order', { ascending: true });
      if (error) throw error;
      return data;
    },
  });
}

export function useEmployee(id) {
  const { businessId } = useAuth();
  return useQuery({
    queryKey: ['employee', id],
    enabled: !!id && !!businessId,
    queryFn: async () => {
      const [{ data: employee, error: e1 }, { data: services, error: e2 }, { data: hours, error: e3 }, { data: holidays, error: e4 }] =
        await Promise.all([
          supabase.from('employees').select('*').eq('id', id).single(),
          supabase.from('employee_services').select('service_id').eq('employee_id', id),
          supabase.from('working_hours').select('*').eq('employee_id', id).order('weekday').order('start_time'),
          supabase.from('holidays').select('*').eq('employee_id', id).order('starts_on'),
        ]);
      if (e1) throw e1;
      if (e2) throw e2;
      if (e3) throw e3;
      if (e4) throw e4;
      return { employee, serviceIds: (services || []).map((s) => s.service_id), hours: hours || [], holidays: holidays || [] };
    },
  });
}

export function useSaveEmployee() {
  const { businessId } = useAuth();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (employee) => {
      const payload = { ...employee, business_id: businessId };
      const { data, error } = await supabase.from('employees').upsert(payload).select().single();
      if (error) throw error;
      return data;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ['employees', businessId] }),
  });
}

export function useDeleteEmployee() {
  const { businessId } = useAuth();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id) => {
      const { error } = await supabase.from('employees').delete().eq('id', id);
      if (error) throw error;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ['employees', businessId] }),
  });
}

export function useSetEmployeeServices() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({ employeeId, serviceIds }) => {
      const { error: delErr } = await supabase.from('employee_services').delete().eq('employee_id', employeeId);
      if (delErr) throw delErr;
      if (serviceIds.length > 0) {
        const rows = serviceIds.map((service_id) => ({ employee_id: employeeId, service_id }));
        const { error: insErr } = await supabase.from('employee_services').insert(rows);
        if (insErr) throw insErr;
      }
    },
    onSuccess: (_data, vars) => qc.invalidateQueries({ queryKey: ['employee', vars.employeeId] }),
  });
}

export function useSaveWorkingHours() {
  const qc = useQueryClient();
  return useMutation({
    // rows: full replacement set for this employee/business scope
    mutationFn: async ({ businessId, employeeId, rows }) => {
      let delQuery = supabase.from('working_hours').delete().eq('business_id', businessId);
      delQuery = employeeId ? delQuery.eq('employee_id', employeeId) : delQuery.is('employee_id', null);
      const { error: delErr } = await delQuery;
      if (delErr) throw delErr;
      if (rows.length > 0) {
        const payload = rows.map((r) => ({ ...r, business_id: businessId, employee_id: employeeId ?? null }));
        const { error: insErr } = await supabase.from('working_hours').insert(payload);
        if (insErr) throw insErr;
      }
    },
    onSuccess: (_data, vars) => {
      if (vars.employeeId) qc.invalidateQueries({ queryKey: ['employee', vars.employeeId] });
      qc.invalidateQueries({ queryKey: ['business_hours', vars.businessId] });
    },
  });
}

export function useSaveHolidays() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({ businessId, employeeId, rows }) => {
      let delQuery = supabase.from('holidays').delete().eq('business_id', businessId);
      delQuery = employeeId ? delQuery.eq('employee_id', employeeId) : delQuery.is('employee_id', null);
      const { error: delErr } = await delQuery;
      if (delErr) throw delErr;
      if (rows.length > 0) {
        const payload = rows.map((r) => ({ ...r, business_id: businessId, employee_id: employeeId ?? null }));
        const { error: insErr } = await supabase.from('holidays').insert(payload);
        if (insErr) throw insErr;
      }
    },
    onSuccess: (_data, vars) => {
      if (vars.employeeId) qc.invalidateQueries({ queryKey: ['employee', vars.employeeId] });
      qc.invalidateQueries({ queryKey: ['business_holidays', vars.businessId] });
    },
  });
}
