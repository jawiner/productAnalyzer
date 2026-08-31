import { useEffect, useState } from 'react';
import * as Tabs from '@radix-ui/react-tabs';
import { Plus, Trash2 } from 'lucide-react';
import { Dialog, DialogContent } from '@/components/ui/Dialog';
import Button from '@/components/ui/Button';
import Input from '@/components/ui/Input';
import Select from '@/components/ui/Select';
import { Field } from '@/components/ui/Field';
import { LoadingBlock } from '@/components/ui/StateBlock';
import { cn } from '@/lib/utils';
import { useAuth } from '@/lib/AuthContext';
import { useServices } from '@/hooks/useServices';
import {
  useEmployee,
  useSaveEmployee,
  useSetEmployeeServices,
  useSaveWorkingHours,
  useSaveHolidays,
} from '@/hooks/useEmployees';
import useT from '@/i18n/LanguageContext';

const emptyDetails = { name: '', email: '', phone: '', photo_url: '', is_active: true, sort_order: 0 };

export default function EmployeeForm({ open, onOpenChange, employeeId }) {
  const t = useT();
  const { businessId } = useAuth();
  const isEdit = !!employeeId;

  const { data: services } = useServices();
  const { data: existing, isLoading: loadingExisting } = useEmployee(employeeId);
  const saveEmployee = useSaveEmployee();
  const setServices = useSetEmployeeServices();
  const saveHours = useSaveWorkingHours();
  const saveHolidays = useSaveHolidays();

  const [tab, setTab] = useState('details');
  const [details, setDetails] = useState(emptyDetails);
  const [serviceIds, setServiceIds] = useState([]);
  const [hours, setHours] = useState([]);
  const [timeOff, setTimeOff] = useState([]);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!open) return;
    setTab('details');
    setError(null);
    if (isEdit && existing) {
      setDetails({
        name: existing.employee.name,
        email: existing.employee.email || '',
        phone: existing.employee.phone || '',
        photo_url: existing.employee.photo_url || '',
        is_active: existing.employee.is_active,
        sort_order: existing.employee.sort_order,
      });
      setServiceIds(existing.serviceIds);
      setHours(existing.hours.map((h) => ({ weekday: h.weekday, start_time: h.start_time.slice(0, 5), end_time: h.end_time.slice(0, 5) })));
      setTimeOff(existing.holidays.map((h) => ({ starts_on: h.starts_on, ends_on: h.ends_on, label: h.label || '' })));
    } else if (!isEdit) {
      setDetails(emptyDetails);
      setServiceIds([]);
      setHours([]);
      setTimeOff([]);
    }
  }, [open, isEdit, existing]);

  const toggleService = (id) => {
    setServiceIds((prev) => (prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]));
  };

  const addHourRow = () => setHours((prev) => [...prev, { weekday: 0, start_time: '09:00', end_time: '17:00' }]);
  const updateHourRow = (idx, patch) => setHours((prev) => prev.map((r, i) => (i === idx ? { ...r, ...patch } : r)));
  const removeHourRow = (idx) => setHours((prev) => prev.filter((_, i) => i !== idx));

  const addTimeOffRow = () => setTimeOff((prev) => [...prev, { starts_on: '', ends_on: '', label: '' }]);
  const updateTimeOffRow = (idx, patch) => setTimeOff((prev) => prev.map((r, i) => (i === idx ? { ...r, ...patch } : r)));
  const removeTimeOffRow = (idx) => setTimeOff((prev) => prev.filter((_, i) => i !== idx));

  const onSave = async () => {
    setError(null);
    if (!details.name) {
      setError(t('errors.saveFailed'));
      setTab('details');
      return;
    }
    try {
      const saved = await saveEmployee.mutateAsync({
        id: employeeId,
        ...details,
        sort_order: Number(details.sort_order) || 0,
      });
      const targetId = saved.id;
      await setServices.mutateAsync({ employeeId: targetId, serviceIds });
      await saveHours.mutateAsync({
        businessId,
        employeeId: targetId,
        rows: hours.map((h) => ({ weekday: Number(h.weekday), start_time: `${h.start_time}:00`, end_time: `${h.end_time}:00` })),
      });
      await saveHolidays.mutateAsync({
        businessId,
        employeeId: targetId,
        rows: timeOff.filter((r) => r.starts_on && r.ends_on).map((r) => ({ starts_on: r.starts_on, ends_on: r.ends_on, label: r.label || null })),
      });
      onOpenChange(false);
    } catch (err) {
      setError(t('errors.saveFailed'));
    }
  };

  const pending = saveEmployee.isPending || setServices.isPending || saveHours.isPending || saveHolidays.isPending;
  const weekdayNames = t('employees.weekdays');

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent title={isEdit ? t('employees.edit') : t('employees.add')} className="max-w-2xl">
        {isEdit && loadingExisting ? (
          <LoadingBlock />
        ) : (
          <Tabs.Root value={tab} onValueChange={setTab}>
            <Tabs.List className="flex gap-1 border-b border-border mb-4">
              {['details', 'services', 'hours', 'timeoff'].map((key) => (
                <Tabs.Trigger
                  key={key}
                  value={key}
                  className={cn(
                    'px-3 py-2 text-sm border-b-2 -mb-px',
                    tab === key ? 'border-primary text-surface-foreground font-medium' : 'border-transparent text-muted-foreground'
                  )}
                >
                  {key === 'details' && t('common.name')}
                  {key === 'services' && t('employees.services')}
                  {key === 'hours' && t('employees.workingHours')}
                  {key === 'timeoff' && t('employees.timeOff')}
                </Tabs.Trigger>
              ))}
            </Tabs.List>

            <Tabs.Content value="details" className="flex flex-col gap-4">
              <Field id="emp-name" label={t('employees.name')}>
                <Input id="emp-name" value={details.name} onChange={(e) => setDetails({ ...details, name: e.target.value })} required />
              </Field>
              <div className="grid grid-cols-2 gap-3">
                <Field id="emp-email" label={`${t('employees.email')} (${t('common.optional')})`}>
                  <Input id="emp-email" type="email" value={details.email} onChange={(e) => setDetails({ ...details, email: e.target.value })} />
                </Field>
                <Field id="emp-phone" label={`${t('employees.phone')} (${t('common.optional')})`}>
                  <Input id="emp-phone" value={details.phone} onChange={(e) => setDetails({ ...details, phone: e.target.value })} />
                </Field>
              </div>
              <Field id="emp-photo" label={`${t('employees.photoUrl')} (${t('common.optional')})`}>
                <Input id="emp-photo" value={details.photo_url} onChange={(e) => setDetails({ ...details, photo_url: e.target.value })} />
              </Field>
              <label className="flex items-center gap-2 text-sm text-surface-foreground">
                <input type="checkbox" checked={details.is_active} onChange={(e) => setDetails({ ...details, is_active: e.target.checked })} />
                {t('employees.isActive')}
              </label>
              {isEdit && (
                <p className="text-xs text-muted-foreground rounded bg-muted p-3">{t('employees.accountLinkingHint')}</p>
              )}
            </Tabs.Content>

            <Tabs.Content value="services" className="flex flex-col gap-2">
              {(services || []).length === 0 ? (
                <p className="text-sm text-muted-foreground">{t('services.empty')}</p>
              ) : (
                (services || []).map((s) => (
                  <label key={s.id} className="flex items-center gap-2 text-sm text-surface-foreground">
                    <input type="checkbox" checked={serviceIds.includes(s.id)} onChange={() => toggleService(s.id)} />
                    {s.name}
                  </label>
                ))
              )}
            </Tabs.Content>

            <Tabs.Content value="hours" className="flex flex-col gap-3">
              {hours.map((h, idx) => (
                <div key={idx} className="flex items-center gap-2">
                  <Select value={h.weekday} onChange={(e) => updateHourRow(idx, { weekday: e.target.value })} className="w-32">
                    {weekdayNames.map((label, i) => (
                      <option key={i} value={i}>
                        {label}
                      </option>
                    ))}
                  </Select>
                  <Input type="time" value={h.start_time} onChange={(e) => updateHourRow(idx, { start_time: e.target.value })} />
                  <span className="text-muted-foreground text-sm">–</span>
                  <Input type="time" value={h.end_time} onChange={(e) => updateHourRow(idx, { end_time: e.target.value })} />
                  <Button size="icon" variant="ghost" onClick={() => removeHourRow(idx)} aria-label={t('common.delete')}>
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              ))}
              <Button size="sm" variant="outline" onClick={addHourRow} type="button">
                <Plus className="h-4 w-4" /> {t('employees.addInterval')}
              </Button>
            </Tabs.Content>

            <Tabs.Content value="timeoff" className="flex flex-col gap-3">
              {timeOff.map((r, idx) => (
                <div key={idx} className="flex items-center gap-2 flex-wrap">
                  <Input type="date" value={r.starts_on} onChange={(e) => updateTimeOffRow(idx, { starts_on: e.target.value })} />
                  <span className="text-muted-foreground text-sm">–</span>
                  <Input type="date" value={r.ends_on} onChange={(e) => updateTimeOffRow(idx, { ends_on: e.target.value })} />
                  <Input
                    placeholder={t('employees.label')}
                    value={r.label}
                    onChange={(e) => updateTimeOffRow(idx, { label: e.target.value })}
                    className="w-32"
                  />
                  <Button size="icon" variant="ghost" onClick={() => removeTimeOffRow(idx)} aria-label={t('common.delete')}>
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              ))}
              <Button size="sm" variant="outline" onClick={addTimeOffRow} type="button">
                <Plus className="h-4 w-4" /> {t('employees.addTimeOff')}
              </Button>
            </Tabs.Content>
          </Tabs.Root>
        )}

        {error && (
          <p role="alert" className="text-sm text-destructive mt-3">
            {error}
          </p>
        )}

        <div className="flex gap-2 pt-4 border-t border-border mt-4">
          <Button onClick={onSave} disabled={pending}>
            {pending ? t('common.saving') : t('common.save')}
          </Button>
          <Button variant="ghost" onClick={() => onOpenChange(false)}>
            {t('common.cancel')}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
