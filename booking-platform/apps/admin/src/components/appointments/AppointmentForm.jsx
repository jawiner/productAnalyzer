import { useEffect, useMemo, useState } from 'react';
import { format } from 'date-fns';
import { Dialog, DialogContent } from '@/components/ui/Dialog';
import Button from '@/components/ui/Button';
import Input from '@/components/ui/Input';
import Select from '@/components/ui/Select';
import Textarea from '@/components/ui/Textarea';
import { Field } from '@/components/ui/Field';
import { useServices } from '@/hooks/useServices';
import { useEmployees } from '@/hooks/useEmployees';
import { useCustomers, useSaveCustomer } from '@/hooks/useCustomers';
import { useCreateAppointment, useUpdateAppointment } from '@/hooks/useAppointments';
import { useAuth } from '@/lib/AuthContext';
import { bookingApi } from '@/lib/functions';
import useT from '@/i18n/LanguageContext';

const emptyCustomer = { full_name: '', phone: '', email: '' };

/**
 * Handles both "new appointment" and "reschedule existing" flows.
 * initial: null for create, or an appointment row (with nested customers/
 * services/employees) to reschedule — reschedule only changes date/time and
 * optionally employee, keeping the same service/customer.
 */
export default function AppointmentForm({ open, onOpenChange, initial, defaultDate }) {
  const t = useT();
  const { businessId } = useAuth();
  const isReschedule = !!initial;

  const { data: services } = useServices();
  const { data: employees } = useEmployees();
  const { data: customers } = useCustomers('');
  const createAppt = useCreateAppointment();
  const updateAppt = useUpdateAppointment();
  const saveCustomer = useSaveCustomer();

  const [serviceId, setServiceId] = useState('');
  const [employeeId, setEmployeeId] = useState('');
  const [customerMode, setCustomerMode] = useState('existing');
  const [customerId, setCustomerId] = useState('');
  const [newCustomer, setNewCustomer] = useState(emptyCustomer);
  const [date, setDate] = useState('');
  const [useOverride, setUseOverride] = useState(false);
  const [slots, setSlots] = useState([]);
  const [slotsLoading, setSlotsLoading] = useState(false);
  const [selectedSlot, setSelectedSlot] = useState('');
  const [manualStart, setManualStart] = useState('');
  const [manualDuration, setManualDuration] = useState(30);
  const [notes, setNotes] = useState('');
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!open) return;
    if (isReschedule) {
      setServiceId(initial.service_id);
      setEmployeeId(initial.employee_id || '');
      setCustomerMode('existing');
      setCustomerId(initial.customer_id);
      setDate(format(new Date(initial.starts_at), 'yyyy-MM-dd'));
      setNotes(initial.notes || '');
      setManualDuration(Math.round((new Date(initial.ends_at) - new Date(initial.starts_at)) / 60000));
    } else {
      setServiceId('');
      setEmployeeId('');
      setCustomerMode('existing');
      setCustomerId('');
      setNewCustomer(emptyCustomer);
      setDate(defaultDate ? format(defaultDate, 'yyyy-MM-dd') : format(new Date(), 'yyyy-MM-dd'));
      setNotes('');
      setManualDuration(30);
    }
    setUseOverride(false);
    setSelectedSlot('');
    setManualStart('');
    setError(null);
  }, [open, initial, defaultDate, isReschedule]);

  const selectedService = useMemo(() => services?.find((s) => s.id === serviceId), [services, serviceId]);
  const eligibleEmployees = employees || [];

  useEffect(() => {
    if (!open || !serviceId || !date || useOverride) {
      setSlots([]);
      return;
    }
    let cancelled = false;
    setSlotsLoading(true);
    bookingApi
      .getAvailability({ business_id: businessId, service_id: serviceId, employee_id: employeeId || undefined, date })
      .then((res) => {
        if (!cancelled) setSlots(res.slots || []);
      })
      .catch(() => {
        if (!cancelled) setSlots([]);
      })
      .finally(() => {
        if (!cancelled) setSlotsLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [open, serviceId, employeeId, date, useOverride, businessId]);

  const durationMinutes = isReschedule ? manualDuration : selectedService?.duration_minutes || 30;

  const buildTimeRange = () => {
    if (useOverride) {
      if (!manualStart) return null;
      const starts = new Date(`${date}T${manualStart}:00`);
      const ends = new Date(starts.getTime() + durationMinutes * 60000);
      return { starts_at: starts.toISOString(), ends_at: ends.toISOString() };
    }
    if (!selectedSlot) return null;
    const starts = new Date(selectedSlot);
    const ends = new Date(starts.getTime() + durationMinutes * 60000);
    return { starts_at: starts.toISOString(), ends_at: ends.toISOString() };
  };

  const onSubmit = async (e) => {
    e.preventDefault();
    setError(null);

    const range = buildTimeRange();
    if (!range) {
      setError(t('appt.pickSlot'));
      return;
    }

    try {
      if (isReschedule) {
        await updateAppt.mutateAsync({ id: initial.id, employee_id: employeeId || null, ...range });
      } else {
        let finalCustomerId = customerId;
        if (customerMode === 'new') {
          if (!newCustomer.full_name || !newCustomer.phone) {
            setError(t('errors.saveFailed'));
            return;
          }
          const saved = await saveCustomer.mutateAsync(newCustomer);
          finalCustomerId = saved.id;
        }
        if (!finalCustomerId || !serviceId) {
          setError(t('errors.saveFailed'));
          return;
        }
        await createAppt.mutateAsync({
          customer_id: finalCustomerId,
          service_id: serviceId,
          employee_id: employeeId || null,
          status: 'confirmed',
          price_at_booking: selectedService?.price ?? null,
          notes: notes || null,
          ...range,
        });
      }
      onOpenChange(false);
    } catch (err) {
      const msg = String(err.message || '');
      if (msg.toLowerCase().includes('exclude') || msg.toLowerCase().includes('overlap') || err.code === '23P01') {
        setError(t('errors.conflict'));
      } else {
        setError(t('errors.saveFailed'));
      }
    }
  };

  const pending = createAppt.isPending || updateAppt.isPending || saveCustomer.isPending;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent title={isReschedule ? t('appt.editTitle') : t('appt.newTitle')}>
        <form onSubmit={onSubmit} className="flex flex-col gap-4">
          {!isReschedule && (
            <>
              <Field id="customerMode" label={t('appt.selectCustomer')}>
                <div className="flex gap-2">
                  <Button
                    type="button"
                    size="sm"
                    variant={customerMode === 'existing' ? 'primary' : 'outline'}
                    onClick={() => setCustomerMode('existing')}
                  >
                    {t('appt.existingCustomer')}
                  </Button>
                  <Button type="button" size="sm" variant={customerMode === 'new' ? 'primary' : 'outline'} onClick={() => setCustomerMode('new')}>
                    {t('appt.newCustomer')}
                  </Button>
                </div>
              </Field>

              {customerMode === 'existing' ? (
                <Field id="customerId" label={t('appt.customer')}>
                  <Select id="customerId" value={customerId} onChange={(e) => setCustomerId(e.target.value)} required>
                    <option value="">—</option>
                    {(customers || []).map((c) => (
                      <option key={c.id} value={c.id}>
                        {c.full_name} ({c.phone})
                      </option>
                    ))}
                  </Select>
                </Field>
              ) : (
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                  <Field id="newName" label={t('common.name')}>
                    <Input
                      id="newName"
                      value={newCustomer.full_name}
                      onChange={(e) => setNewCustomer({ ...newCustomer, full_name: e.target.value })}
                      required
                    />
                  </Field>
                  <Field id="newPhone" label={t('common.phone')}>
                    <Input
                      id="newPhone"
                      value={newCustomer.phone}
                      onChange={(e) => setNewCustomer({ ...newCustomer, phone: e.target.value })}
                      required
                    />
                  </Field>
                  <Field id="newEmail" label={`${t('common.email')} (${t('common.optional')})`}>
                    <Input
                      id="newEmail"
                      type="email"
                      value={newCustomer.email}
                      onChange={(e) => setNewCustomer({ ...newCustomer, email: e.target.value })}
                    />
                  </Field>
                </div>
              )}

              <Field id="serviceId" label={t('appt.service')}>
                <Select id="serviceId" value={serviceId} onChange={(e) => setServiceId(e.target.value)} required>
                  <option value="">—</option>
                  {(services || [])
                    .filter((s) => s.is_active)
                    .map((s) => (
                      <option key={s.id} value={s.id}>
                        {s.name} ({s.duration_minutes} min)
                      </option>
                    ))}
                </Select>
              </Field>
            </>
          )}

          <Field id="employeeId" label={`${t('appt.employee')} (${t('common.optional')})`}>
            <Select id="employeeId" value={employeeId} onChange={(e) => setEmployeeId(e.target.value)}>
              <option value="">{t('appt.unassigned')}</option>
              {eligibleEmployees
                .filter((e) => e.is_active)
                .map((e) => (
                  <option key={e.id} value={e.id}>
                    {e.name}
                  </option>
                ))}
            </Select>
          </Field>

          {isReschedule && (
            <Field id="manualDuration" label={t('appt.manualDuration')}>
              <Input
                id="manualDuration"
                type="number"
                min={5}
                step={5}
                value={manualDuration}
                onChange={(e) => setManualDuration(Number(e.target.value))}
              />
            </Field>
          )}

          <Field id="date" label={t('common.date')}>
            <Input id="date" type="date" value={date} onChange={(e) => setDate(e.target.value)} required />
          </Field>

          <label className="flex items-center gap-2 text-sm text-surface-foreground">
            <input type="checkbox" checked={useOverride} onChange={(e) => setUseOverride(e.target.checked)} />
            {t('appt.overrideSlot')}
          </label>

          {useOverride ? (
            <Field id="manualStart" label={t('appt.manualStart')}>
              <Input id="manualStart" type="time" value={manualStart} onChange={(e) => setManualStart(e.target.value)} required />
            </Field>
          ) : (
            <Field id="slots" label={t('appt.availableSlots')}>
              {slotsLoading ? (
                <p className="text-sm text-muted-foreground">{t('common.loading')}</p>
              ) : slots.length === 0 ? (
                <p className="text-sm text-muted-foreground">{t('appt.noSlotsForDay')}</p>
              ) : (
                <div className="flex flex-wrap gap-2 max-h-40 overflow-y-auto">
                  {slots.map((s) => (
                    <Button
                      key={s}
                      type="button"
                      size="sm"
                      variant={selectedSlot === s ? 'primary' : 'outline'}
                      onClick={() => setSelectedSlot(s)}
                    >
                      {new Date(s).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </Button>
                  ))}
                </div>
              )}
            </Field>
          )}

          {!isReschedule && (
            <Field id="notes" label={`${t('appt.notes')} (${t('common.optional')})`}>
              <Textarea id="notes" value={notes} onChange={(e) => setNotes(e.target.value)} rows={2} />
            </Field>
          )}

          {error && (
            <p role="alert" className="text-sm text-destructive">
              {error}
            </p>
          )}

          <div className="flex gap-2 pt-2">
            <Button type="submit" disabled={pending}>
              {pending ? t('common.saving') : t('common.save')}
            </Button>
            <Button type="button" variant="ghost" onClick={() => onOpenChange(false)}>
              {t('common.cancel')}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}
