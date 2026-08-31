import { useEffect, useState } from 'react';
import { Plus, Trash2 } from 'lucide-react';
import { Card, CardBody } from '@/components/ui/Card';
import Button from '@/components/ui/Button';
import Input from '@/components/ui/Input';
import Select from '@/components/ui/Select';
import Switch from '@/components/ui/Switch';
import { Field } from '@/components/ui/Field';
import { LoadingBlock, ErrorBlock } from '@/components/ui/StateBlock';
import { useAuth } from '@/lib/AuthContext';
import {
  useBusinessSettings,
  useSaveBusinessSettings,
  useNotificationSettings,
  useSaveNotificationSettings,
  useSmsUsageThisMonth,
  useBusinessTheme,
  useSaveBusinessTheme,
  useBusinessHours,
  useBusinessHolidays,
  useBusinessBlockedTimes,
  useSaveBlockedTimes,
} from '@/hooks/useSettings';
import { useSaveWorkingHours, useSaveHolidays } from '@/hooks/useEmployees';
import useT from '@/i18n/LanguageContext';

function ToggleRow({ label, checked, onChange }) {
  return (
    <div className="flex items-center justify-between gap-3 py-2">
      <span className="text-sm text-surface-foreground">{label}</span>
      <Switch checked={checked} onCheckedChange={onChange} />
    </div>
  );
}

function SmsQuotaUsage({ quota }) {
  const t = useT();
  const { data: used, isLoading } = useSmsUsageThisMonth();

  if (isLoading || used === undefined) return null;

  const pct = quota > 0 ? Math.min(100, (used / quota) * 100) : 0;
  const isNearLimit = pct >= 80 && pct < 100;
  const isOverLimit = quota > 0 && used >= quota;

  return (
    <div className="flex flex-col gap-1.5 pt-1">
      <div className="flex items-center justify-between text-xs">
        <span className="text-muted-foreground">{t('settings.smsUsageThisMonth', { used, quota })}</span>
      </div>
      <div className="h-1.5 w-full rounded-full bg-muted overflow-hidden">
        <div
          className={`h-full rounded-full ${isOverLimit ? 'bg-destructive' : isNearLimit ? 'bg-warning' : 'bg-primary'}`}
          style={{ width: `${pct}%` }}
        />
      </div>
      {isOverLimit && <p className="text-xs text-destructive">{t('settings.smsQuotaExceeded')}</p>}
      {isNearLimit && <p className="text-xs text-warning">{t('settings.smsQuotaNearLimit')}</p>}
    </div>
  );
}

export default function Settings() {
  const t = useT();
  const { businessId } = useAuth();

  const { data: settings, isLoading: l1, isError: e1, refetch: r1 } = useBusinessSettings();
  const { data: notificationSettings, isLoading: l6, isError: e6, refetch: r6 } = useNotificationSettings();
  const { data: theme, isLoading: l2, isError: e2, refetch: r2 } = useBusinessTheme();
  const { data: hours, isLoading: l3 } = useBusinessHours();
  const { data: holidays, isLoading: l4 } = useBusinessHolidays();
  const { data: blockedTimes, isLoading: l5 } = useBusinessBlockedTimes();

  const saveSettings = useSaveBusinessSettings();
  const saveNotificationSettings = useSaveNotificationSettings();
  const saveTheme = useSaveBusinessTheme();
  const saveHours = useSaveWorkingHours();
  const saveHolidaysMut = useSaveHolidays();
  const saveBlocked = useSaveBlockedTimes();

  const [settingsForm, setSettingsForm] = useState(null);
  const [notificationForm, setNotificationForm] = useState(null);
  const [themeForm, setThemeForm] = useState(null);
  const [hoursRows, setHoursRows] = useState([]);
  const [holidayRows, setHolidayRows] = useState([]);
  const [blockedRows, setBlockedRows] = useState([]);
  const [saveMsg, setSaveMsg] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (settings) setSettingsForm(settings);
  }, [settings]);
  useEffect(() => {
    if (notificationSettings) setNotificationForm(notificationSettings);
  }, [notificationSettings]);
  useEffect(() => {
    if (theme) setThemeForm(theme);
  }, [theme]);
  useEffect(() => {
    if (hours) setHoursRows(hours.map((h) => ({ weekday: h.weekday, start_time: h.start_time.slice(0, 5), end_time: h.end_time.slice(0, 5) })));
  }, [hours]);
  useEffect(() => {
    if (holidays) setHolidayRows(holidays.map((h) => ({ starts_on: h.starts_on, ends_on: h.ends_on, label: h.label || '' })));
  }, [holidays]);
  useEffect(() => {
    if (blockedTimes)
      setBlockedRows(
        blockedTimes.map((b) => ({
          starts_at: b.starts_at.slice(0, 16),
          ends_at: b.ends_at.slice(0, 16),
          label: b.label || '',
        }))
      );
  }, [blockedTimes]);

  if (l1 || l2 || l6) return <LoadingBlock />;
  if (e1 || e2 || e6) return <ErrorBlock onRetry={() => { r1(); r2(); r6(); }} />;
  if (!settingsForm || !themeForm || !notificationForm) return <LoadingBlock />;

  const addHourRow = () => setHoursRows((p) => [...p, { weekday: 0, start_time: '09:00', end_time: '17:00' }]);
  const updateHourRow = (idx, patch) => setHoursRows((p) => p.map((r, i) => (i === idx ? { ...r, ...patch } : r)));
  const removeHourRow = (idx) => setHoursRows((p) => p.filter((_, i) => i !== idx));

  const addHolidayRow = () => setHolidayRows((p) => [...p, { starts_on: '', ends_on: '', label: '' }]);
  const updateHolidayRow = (idx, patch) => setHolidayRows((p) => p.map((r, i) => (i === idx ? { ...r, ...patch } : r)));
  const removeHolidayRow = (idx) => setHolidayRows((p) => p.filter((_, i) => i !== idx));

  const addBlockedRow = () => setBlockedRows((p) => [...p, { starts_at: '', ends_at: '', label: '' }]);
  const updateBlockedRow = (idx, patch) => setBlockedRows((p) => p.map((r, i) => (i === idx ? { ...r, ...patch } : r)));
  const removeBlockedRow = (idx) => setBlockedRows((p) => p.filter((_, i) => i !== idx));

  const weekdayNames = t('employees.weekdays');

  const onSaveAll = async () => {
    setError(null);
    setSaveMsg(null);
    try {
      await saveSettings.mutateAsync({
        ...settingsForm,
        cancellation_notice_minutes: Number(settingsForm.cancellation_notice_minutes),
        minimum_notice_minutes: Number(settingsForm.minimum_notice_minutes),
        max_booking_days_ahead: Number(settingsForm.max_booking_days_ahead),
        slot_interval_minutes: Number(settingsForm.slot_interval_minutes),
      });
      await saveNotificationSettings.mutateAsync({
        ...notificationForm,
        reminder_hours_before: Number(notificationForm.reminder_hours_before),
      });
      await saveTheme.mutateAsync(themeForm);
      await saveHours.mutateAsync({
        businessId,
        employeeId: null,
        rows: hoursRows.map((h) => ({ weekday: Number(h.weekday), start_time: `${h.start_time}:00`, end_time: `${h.end_time}:00` })),
      });
      await saveHolidaysMut.mutateAsync({
        businessId,
        employeeId: null,
        rows: holidayRows.filter((r) => r.starts_on && r.ends_on).map((r) => ({ starts_on: r.starts_on, ends_on: r.ends_on, label: r.label || null })),
      });
      await saveBlocked.mutateAsync(
        blockedRows
          .filter((r) => r.starts_at && r.ends_at)
          .map((r) => ({ starts_at: new Date(r.starts_at).toISOString(), ends_at: new Date(r.ends_at).toISOString(), label: r.label || null }))
      );
      setSaveMsg(t('settings.saved'));
    } catch (err) {
      setError(t('errors.saveFailed'));
    }
  };

  const pending =
    saveSettings.isPending ||
    saveNotificationSettings.isPending ||
    saveTheme.isPending ||
    saveHours.isPending ||
    saveHolidaysMut.isPending ||
    saveBlocked.isPending;

  return (
    <div className="flex flex-col gap-6">
      <h1 className="text-2xl font-bold text-surface-foreground">{t('settings.title')}</h1>

      <Card>
        <CardBody className="flex flex-col gap-1">
          <h2 className="text-sm font-semibold text-surface-foreground mb-2">{t('settings.business')}</h2>
          <ToggleRow
            label={t('settings.showEmployeeSelection')}
            checked={settingsForm.show_employee_selection}
            onChange={(v) => setSettingsForm({ ...settingsForm, show_employee_selection: v })}
          />
          <ToggleRow
            label={t('settings.showPrices')}
            checked={settingsForm.show_prices}
            onChange={(v) => setSettingsForm({ ...settingsForm, show_prices: v })}
          />
          <ToggleRow
            label={t('settings.allowCancellation')}
            checked={settingsForm.allow_cancellation}
            onChange={(v) => setSettingsForm({ ...settingsForm, allow_cancellation: v })}
          />
          <ToggleRow
            label={t('settings.allowRescheduling')}
            checked={settingsForm.allow_rescheduling}
            onChange={(v) => setSettingsForm({ ...settingsForm, allow_rescheduling: v })}
          />

          <div className="grid grid-cols-2 gap-3 mt-3">
            <Field id="cancellation-notice" label={t('settings.cancellationNoticeMinutes')}>
              <Input
                id="cancellation-notice"
                type="number"
                value={settingsForm.cancellation_notice_minutes}
                onChange={(e) => setSettingsForm({ ...settingsForm, cancellation_notice_minutes: e.target.value })}
              />
            </Field>
            <Field id="minimum-notice" label={t('settings.minimumNoticeMinutes')}>
              <Input
                id="minimum-notice"
                type="number"
                value={settingsForm.minimum_notice_minutes}
                onChange={(e) => setSettingsForm({ ...settingsForm, minimum_notice_minutes: e.target.value })}
              />
            </Field>
            <Field id="max-days" label={t('settings.maxBookingDaysAhead')}>
              <Input
                id="max-days"
                type="number"
                value={settingsForm.max_booking_days_ahead}
                onChange={(e) => setSettingsForm({ ...settingsForm, max_booking_days_ahead: e.target.value })}
              />
            </Field>
            <Field id="slot-interval" label={t('settings.slotIntervalMinutes')}>
              <Input
                id="slot-interval"
                type="number"
                value={settingsForm.slot_interval_minutes}
                onChange={(e) => setSettingsForm({ ...settingsForm, slot_interval_minutes: e.target.value })}
              />
            </Field>
            <Field id="default-lang" label={t('settings.defaultLanguage')}>
              <Select
                id="default-lang"
                value={settingsForm.default_language}
                onChange={(e) => setSettingsForm({ ...settingsForm, default_language: e.target.value })}
              >
                <option value="en">English</option>
                <option value="he">עברית</option>
              </Select>
            </Field>
          </div>
        </CardBody>
      </Card>

      <Card>
        <CardBody className="flex flex-col gap-3">
          <h2 className="text-sm font-semibold text-surface-foreground mb-1">{t('settings.smsNotifications')}</h2>
          <p className="text-xs text-muted-foreground">{t('settings.smsNotificationsHint')}</p>
          <ToggleRow
            label={t('settings.smsEnabled')}
            checked={settingsForm.sms_enabled}
            onChange={(v) => setSettingsForm({ ...settingsForm, sms_enabled: v })}
          />
          <ToggleRow
            label={t('settings.notifyBusinessOnNewBooking')}
            checked={settingsForm.notify_business_on_new_booking}
            onChange={(v) => setSettingsForm({ ...settingsForm, notify_business_on_new_booking: v })}
          />
          <Field id="business-notification-phone" label={t('settings.businessNotificationPhone')}>
            <Input
              id="business-notification-phone"
              type="tel"
              placeholder="+15551234567"
              value={settingsForm.business_notification_phone || ''}
              onChange={(e) => setSettingsForm({ ...settingsForm, business_notification_phone: e.target.value })}
            />
          </Field>
          <div className="grid grid-cols-2 gap-3">
            <Field id="reminder-hours" label={t('settings.reminderHoursBefore')}>
              <Input
                id="reminder-hours"
                type="number"
                min="1"
                value={notificationForm.reminder_hours_before ?? 24}
                onChange={(e) => setNotificationForm({ ...notificationForm, reminder_hours_before: e.target.value })}
              />
            </Field>
            <Field id="sms-quota" label={t('settings.smsMonthlyQuota')}>
              <Input
                id="sms-quota"
                type="number"
                min="0"
                value={notificationForm.sms_monthly_quota ?? 100}
                onChange={(e) => setNotificationForm({ ...notificationForm, sms_monthly_quota: e.target.value })}
              />
            </Field>
          </div>
          <SmsQuotaUsage quota={Number(notificationForm.sms_monthly_quota ?? 100)} />
        </CardBody>
      </Card>

      <Card>
        <CardBody className="flex flex-col gap-3">
          <h2 className="text-sm font-semibold text-surface-foreground mb-1">{t('settings.theme')}</h2>
          <Field id="logo-url" label={t('settings.logoUrl')}>
            <Input id="logo-url" value={themeForm.logo_url || ''} onChange={(e) => setThemeForm({ ...themeForm, logo_url: e.target.value })} />
          </Field>
          <div className="grid grid-cols-2 gap-3">
            <Field id="primary-color" label={t('settings.primaryColor')}>
              <Input
                id="primary-color"
                type="color"
                value={themeForm.primary_color}
                onChange={(e) => setThemeForm({ ...themeForm, primary_color: e.target.value })}
                className="h-10 p-1"
              />
            </Field>
            <Field id="secondary-color" label={t('settings.secondaryColor')}>
              <Input
                id="secondary-color"
                type="color"
                value={themeForm.secondary_color}
                onChange={(e) => setThemeForm({ ...themeForm, secondary_color: e.target.value })}
                className="h-10 p-1"
              />
            </Field>
          </div>
          <Field id="font-family" label={t('settings.fontFamily')}>
            <Input id="font-family" value={themeForm.font_family} onChange={(e) => setThemeForm({ ...themeForm, font_family: e.target.value })} />
          </Field>
          <Field id="button-style" label={t('settings.buttonStyle')}>
            <Select id="button-style" value={themeForm.button_style} onChange={(e) => setThemeForm({ ...themeForm, button_style: e.target.value })}>
              <option value="rounded">{t('settings.buttonStyles.rounded')}</option>
              <option value="square">{t('settings.buttonStyles.square')}</option>
              <option value="pill">{t('settings.buttonStyles.pill')}</option>
            </Select>
          </Field>
        </CardBody>
      </Card>

      <Card>
        <CardBody className="flex flex-col gap-3">
          <div>
            <h2 className="text-sm font-semibold text-surface-foreground">{t('settings.hours')}</h2>
            <p className="text-xs text-muted-foreground">{t('settings.hoursHint')}</p>
          </div>
          {!l3 &&
            hoursRows.map((h, idx) => (
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
          <Button size="sm" variant="outline" onClick={addHourRow} type="button" className="self-start">
            <Plus className="h-4 w-4" /> {t('employees.addInterval')}
          </Button>
        </CardBody>
      </Card>

      <Card>
        <CardBody className="flex flex-col gap-3">
          <h2 className="text-sm font-semibold text-surface-foreground">{t('settings.holidays')}</h2>
          {!l4 &&
            holidayRows.map((r, idx) => (
              <div key={idx} className="flex items-center gap-2 flex-wrap">
                <Input type="date" value={r.starts_on} onChange={(e) => updateHolidayRow(idx, { starts_on: e.target.value })} />
                <span className="text-muted-foreground text-sm">–</span>
                <Input type="date" value={r.ends_on} onChange={(e) => updateHolidayRow(idx, { ends_on: e.target.value })} />
                <Input placeholder={t('employees.label')} value={r.label} onChange={(e) => updateHolidayRow(idx, { label: e.target.value })} className="w-32" />
                <Button size="icon" variant="ghost" onClick={() => removeHolidayRow(idx)} aria-label={t('common.delete')}>
                  <Trash2 className="h-4 w-4" />
                </Button>
              </div>
            ))}
          <Button size="sm" variant="outline" onClick={addHolidayRow} type="button" className="self-start">
            <Plus className="h-4 w-4" /> {t('employees.addTimeOff')}
          </Button>
        </CardBody>
      </Card>

      <Card>
        <CardBody className="flex flex-col gap-3">
          <h2 className="text-sm font-semibold text-surface-foreground">{t('settings.blockedTimes')}</h2>
          {!l5 &&
            blockedRows.map((r, idx) => (
              <div key={idx} className="flex items-center gap-2 flex-wrap">
                <Input type="datetime-local" value={r.starts_at} onChange={(e) => updateBlockedRow(idx, { starts_at: e.target.value })} />
                <span className="text-muted-foreground text-sm">–</span>
                <Input type="datetime-local" value={r.ends_at} onChange={(e) => updateBlockedRow(idx, { ends_at: e.target.value })} />
                <Input placeholder={t('employees.label')} value={r.label} onChange={(e) => updateBlockedRow(idx, { label: e.target.value })} className="w-32" />
                <Button size="icon" variant="ghost" onClick={() => removeBlockedRow(idx)} aria-label={t('common.delete')}>
                  <Trash2 className="h-4 w-4" />
                </Button>
              </div>
            ))}
          <Button size="sm" variant="outline" onClick={addBlockedRow} type="button" className="self-start">
            <Plus className="h-4 w-4" /> {t('common.create')}
          </Button>
        </CardBody>
      </Card>

      {error && (
        <p role="alert" className="text-sm text-destructive">
          {error}
        </p>
      )}
      {saveMsg && <p className="text-sm text-success">{saveMsg}</p>}

      <div>
        <Button onClick={onSaveAll} disabled={pending} size="lg">
          {pending ? t('common.saving') : t('common.save')}
        </Button>
      </div>
    </div>
  );
}
