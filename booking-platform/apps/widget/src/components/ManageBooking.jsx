import { useState } from 'react';
import { format } from 'date-fns';
import Input from '@/components/ui/Input';
import { Field } from '@/components/ui/Field';
import Button from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { LoadingBlock, ErrorBlock } from '@/components/ui/StateBlock';
import { bookingApi } from '@/lib/functions';
import { useBusinessData } from '@/hooks/useBusinessData';
import DateStep from '@/components/steps/DateStep';
import TimeStep from '@/components/steps/TimeStep';
import useT from '@/i18n/LanguageContext';

// Self-service "enter your confirmation code" view for cancel/reschedule.
// There's no anon read policy on `appointments` (by design — customers
// must not be able to browse each other's bookings), so lookup goes
// through the dedicated get-booking-lookup edge function, which returns
// only the minimal context needed to render this UI (business/service/
// employee identity, current time, status, relevant settings flags).
export default function ManageBooking({ initialCode = '', intent = 'cancel', onClose }) {
  const t = useT();
  const [code, setCode] = useState(initialCode);
  // lookup -> loading -> found -> {cancel|reschedule-date|reschedule-time} -> done
  const [mode, setMode] = useState('lookup');
  const [lookupError, setLookupError] = useState('');
  const [booking, setBooking] = useState(null); // get-booking-lookup response
  const [reason, setReason] = useState('');
  const [selectedDate, setSelectedDate] = useState(null);
  const [actionError, setActionError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [resultMessage, setResultMessage] = useState('');

  // Only fetched once a lookup has resolved, since only then do we know the
  // business_id — used by DateStep/TimeStep for the reschedule picker.
  const businessData = useBusinessData(mode.startsWith('reschedule') ? booking?.business?.id : undefined);

  async function handleLookup(e) {
    e.preventDefault();
    setLookupError('');
    setMode('loading');
    try {
      const result = await bookingApi.getBookingLookup({ confirmation_code: code.trim() });
      if (result.appointment.status === 'cancelled') {
        setLookupError(t('manage.alreadyCancelled'));
        setMode('lookup');
        return;
      }
      setBooking(result);
      setMode('found');
    } catch (err) {
      setLookupError(mapError(err, t));
      setMode('lookup');
    }
  }

  async function handleCancel(e) {
    e.preventDefault();
    setActionError('');
    setIsSubmitting(true);
    try {
      await bookingApi.cancelBooking({ confirmation_code: code.trim(), reason: reason || undefined });
      setResultMessage(t('manage.cancelSuccess'));
      setMode('done');
    } catch (err) {
      setActionError(mapError(err, t));
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleRescheduleConfirm(slot) {
    setActionError('');
    setIsSubmitting(true);
    try {
      await bookingApi.rescheduleBooking({ confirmation_code: code.trim(), new_starts_at: slot.startsAt });
      setResultMessage(t('manage.rescheduleSuccess'));
      setMode('done');
    } catch (err) {
      setActionError(mapError(err, t));
      // A 409 here means the newly-picked slot was itself just taken —
      // stay on the time step so the user can pick again with fresh data.
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="flex flex-col gap-4">
      <div>
        <h2 className="text-lg font-semibold">{t('manage.title')}</h2>
        <p className="text-sm text-muted-foreground">{t('manage.subtitle')}</p>
      </div>

      {(mode === 'lookup' || mode === 'loading') && (
        <form className="flex flex-col gap-4" onSubmit={handleLookup}>
          <Field id="confirmation-code" label={t('manage.codeLabel')} error={lookupError || undefined}>
            <Input
              id="confirmation-code"
              placeholder={t('manage.codePlaceholder')}
              value={code}
              onChange={(e) => setCode(e.target.value.toUpperCase())}
              autoFocus
              disabled={mode === 'loading'}
            />
          </Field>
          <Button type="submit" disabled={!code.trim() || mode === 'loading'}>
            {mode === 'loading' ? t('common.loading') : t('manage.lookup')}
          </Button>
        </form>
      )}

      {mode === 'found' && booking && (
        <FoundBooking
          t={t}
          booking={booking}
          intent={intent}
          onCancel={() => setMode('cancel')}
          onReschedule={() => setMode('reschedule-date')}
          onBack={() => setMode('lookup')}
        />
      )}

      {mode === 'cancel' && (
        <Card as="form" className="flex flex-col gap-3" onSubmit={handleCancel}>
          <p className="text-sm font-medium">{t('manage.cancelConfirmTitle')}</p>
          <p className="text-xs text-muted-foreground">{t('manage.cancelConfirmBody')}</p>
          <Field id="cancel-reason" label={t('manage.cancelReason')}>
            <Input id="cancel-reason" value={reason} onChange={(e) => setReason(e.target.value)} />
          </Field>
          {actionError && (
            <p role="alert" className="text-sm text-destructive">
              {actionError}
            </p>
          )}
          <div className="flex gap-2">
            <Button variant="outline" className="flex-1" type="button" onClick={() => setMode('found')}>
              {t('common.back')}
            </Button>
            <Button variant="destructive" className="flex-1" type="submit" disabled={isSubmitting}>
              {isSubmitting ? t('common.submitting') : t('manage.cancelSubmit')}
            </Button>
          </div>
        </Card>
      )}

      {mode === 'reschedule-date' && (
        <div className="flex flex-col gap-3">
          <p className="text-sm font-medium">{t('manage.rescheduleTitle')}</p>
          {businessData.isLoading && <LoadingBlock />}
          {businessData.isError && <ErrorBlock message={t('errors.generic')} onRetry={businessData.refetch} />}
          {businessData.data && (
            <DateStep
              settings={businessData.data.settings}
              workingHours={businessData.data.workingHours}
              holidays={businessData.data.holidays}
              employeeId={booking.employee?.id}
              selectedDate={selectedDate}
              onSelect={(dateStr) => {
                setSelectedDate(dateStr);
                setMode('reschedule-time');
              }}
            />
          )}
          <Button variant="ghost" onClick={() => setMode('found')}>
            {t('common.back')}
          </Button>
        </div>
      )}

      {mode === 'reschedule-time' && businessData.data && (
        <div className="flex flex-col gap-3">
          <TimeStep
            businessId={booking.business.id}
            serviceId={booking.service.id}
            employeeId={booking.employee?.id}
            date={selectedDate}
            onSelect={handleRescheduleConfirm}
            onPickAnotherDate={() => setMode('reschedule-date')}
          />
          {isSubmitting && <LoadingBlock />}
          {actionError && (
            <p role="alert" className="text-sm text-destructive">
              {actionError}
            </p>
          )}
          <Button variant="ghost" onClick={() => setMode('reschedule-date')} disabled={isSubmitting}>
            {t('common.back')}
          </Button>
        </div>
      )}

      {mode === 'done' && (
        <div className="flex flex-col gap-3 text-center py-6">
          <p className="text-sm font-medium">{resultMessage}</p>
          <Button variant="secondary" onClick={onClose}>
            {t('common.close')}
          </Button>
        </div>
      )}

      {mode === 'lookup' && (
        <Button variant="ghost" onClick={onClose}>
          {t('common.close')}
        </Button>
      )}
    </div>
  );
}

function FoundBooking({ t, booking, intent, onCancel, onReschedule, onBack }) {
  const { business, service, employee, appointment, settings } = booking;
  return (
    <Card className="flex flex-col gap-3 text-sm">
      <div className="flex flex-col gap-1">
        <Row label={t('confirmation.business')} value={business.name} />
        <Row label={t('confirmation.service')} value={service.name} />
        {employee && <Row label={t('confirmation.employee')} value={employee.name} />}
        <Row label={t('confirmation.when')} value={format(new Date(appointment.starts_at), 'PPPP p')} />
      </div>
      <div className="flex gap-2">
        {settings.allow_cancellation && (
          <Button
            variant={intent === 'cancel' ? 'destructive' : 'outline'}
            size="sm"
            className="flex-1"
            onClick={onCancel}
          >
            {t('manage.cancelSubmit')}
          </Button>
        )}
        {settings.allow_rescheduling && (
          <Button
            variant={intent === 'reschedule' ? 'primary' : 'outline'}
            size="sm"
            className="flex-1"
            onClick={onReschedule}
          >
            {t('confirmation.rescheduleBooking')}
          </Button>
        )}
      </div>
      {!settings.allow_cancellation && !settings.allow_rescheduling && (
        <p className="text-xs text-muted-foreground">{t('manage.cancelNotAllowed')}</p>
      )}
      <Button variant="ghost" size="sm" onClick={onBack}>
        {t('common.back')}
      </Button>
    </Card>
  );
}

function Row({ label, value }) {
  return (
    <div className="flex items-baseline justify-between gap-3">
      <span className="text-muted-foreground">{label}</span>
      <span className="font-medium text-end">{value}</span>
    </div>
  );
}

function mapError(err, t) {
  if (err.isNetworkError) return t('errors.network');
  if (err.status === 403) return t('manage.cancelNotAllowed');
  if (err.status === 409) return t('errors.conflict');
  if (err.status === 404) return t('manage.notFound');
  return t('errors.generic');
}
