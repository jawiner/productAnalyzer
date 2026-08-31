import { useQuery } from '@tanstack/react-query';
import { bookingApi } from '@/lib/functions';

// get-availability is the sole source of truth for bookable slots — this
// hook is a thin cache wrapper, it never computes slots itself.
export function useAvailability({ businessId, serviceId, employeeId, date }) {
  return useQuery({
    queryKey: ['booking-widget', 'availability', businessId, serviceId, employeeId || 'any', date],
    enabled: Boolean(businessId && serviceId && date),
    staleTime: 15_000,
    retry: 1,
    queryFn: async () => {
      const res = await bookingApi.getAvailability({
        business_id: businessId,
        service_id: serviceId,
        employee_id: employeeId || undefined,
        date,
      });
      return res.slots || [];
    },
  });
}
