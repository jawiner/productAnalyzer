import { useState } from 'react';
import { format } from 'date-fns';
import { Dialog, DialogContent } from '@/components/ui/Dialog';
import Button from '@/components/ui/Button';
import Badge from '@/components/ui/Badge';
import Textarea from '@/components/ui/Textarea';
import { Field } from '@/components/ui/Field';
import { formatCurrency } from '@/lib/utils';
import { useUpdateAppointment, useCancelAppointment } from '@/hooks/useAppointments';
import useT from '@/i18n/LanguageContext';

export default function AppointmentDetail({ appointment, open, onOpenChange, onReschedule }) {
  const t = useT();
  const updateAppt = useUpdateAppointment();
  const cancelAppt = useCancelAppointment();
  const [confirmingCancel, setConfirmingCancel] = useState(false);
  const [cancelReason, setCancelReason] = useState('');
  const [error, setError] = useState(null);

  if (!appointment) return null;

  const setStatus = async (status) => {
    setError(null);
    try {
      await updateAppt.mutateAsync({ id: appointment.id, status });
    } catch (err) {
      setError(err.message?.includes('exclude') ? t('errors.conflict') : t('errors.saveFailed'));
    }
  };

  const doCancel = async () => {
    setError(null);
    try {
      await cancelAppt.mutateAsync({ id: appointment.id, reason: cancelReason });
      setConfirmingCancel(false);
      onOpenChange(false);
    } catch (err) {
      setError(t('errors.saveFailed'));
    }
  };

  const canAct = !['cancelled'].includes(appointment.status);

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent title={t('appt.title')}>
        <div className="flex flex-col gap-4">
          <div className="flex items-center justify-between">
            <Badge status={appointment.status}>{t(`appt.status.${appointment.status}`)}</Badge>
            <span className="text-xs text-muted-foreground">
              {t('appt.confirmationCode')}: {appointment.confirmation_code}
            </span>
          </div>

          <dl className="grid grid-cols-3 gap-x-3 gap-y-2 text-sm">
            <dt className="text-muted-foreground">{t('appt.customer')}</dt>
            <dd className="col-span-2 text-surface-foreground">
              {appointment.customers?.full_name}
              <div className="text-xs text-muted-foreground">
                {appointment.customers?.phone} {appointment.customers?.email ? `· ${appointment.customers.email}` : ''}
              </div>
            </dd>

            <dt className="text-muted-foreground">{t('appt.service')}</dt>
            <dd className="col-span-2 text-surface-foreground">{appointment.services?.name}</dd>

            <dt className="text-muted-foreground">{t('appt.employee')}</dt>
            <dd className="col-span-2 text-surface-foreground">{appointment.employees?.name || t('appt.unassigned')}</dd>

            <dt className="text-muted-foreground">{t('appt.starts')}</dt>
            <dd className="col-span-2 text-surface-foreground">{format(new Date(appointment.starts_at), 'PPP p')}</dd>

            <dt className="text-muted-foreground">{t('appt.ends')}</dt>
            <dd className="col-span-2 text-surface-foreground">{format(new Date(appointment.ends_at), 'PPP p')}</dd>

            {appointment.price_at_booking != null && (
              <>
                <dt className="text-muted-foreground">{t('appt.price')}</dt>
                <dd className="col-span-2 text-surface-foreground">{formatCurrency(appointment.price_at_booking)}</dd>
              </>
            )}

            {appointment.notes && (
              <>
                <dt className="text-muted-foreground">{t('appt.notes')}</dt>
                <dd className="col-span-2 text-surface-foreground whitespace-pre-wrap">{appointment.notes}</dd>
              </>
            )}
          </dl>

          {error && (
            <p role="alert" className="text-sm text-destructive">
              {error}
            </p>
          )}

          {canAct && !confirmingCancel && (
            <div className="flex flex-wrap gap-2 pt-2 border-t border-border">
              {appointment.status !== 'completed' && (
                <Button size="sm" variant="secondary" onClick={() => setStatus('completed')} disabled={updateAppt.isPending}>
                  {t('appt.markCompleted')}
                </Button>
              )}
              {appointment.status !== 'no_show' && (
                <Button size="sm" variant="secondary" onClick={() => setStatus('no_show')} disabled={updateAppt.isPending}>
                  {t('appt.markNoShow')}
                </Button>
              )}
              <Button size="sm" variant="outline" onClick={() => onReschedule(appointment)}>
                {t('appt.reschedule')}
              </Button>
              <Button size="sm" variant="destructive" onClick={() => setConfirmingCancel(true)}>
                {t('appt.cancelAppointment')}
              </Button>
            </div>
          )}

          {confirmingCancel && (
            <div className="flex flex-col gap-3 pt-2 border-t border-border">
              <p className="text-sm font-medium text-surface-foreground">{t('appt.cancelConfirm')}</p>
              <p className="text-xs text-muted-foreground">{t('appt.cancelConfirmBody')}</p>
              <Field id="cancelReason" label={t('appt.cancelReason')}>
                <Textarea id="cancelReason" value={cancelReason} onChange={(e) => setCancelReason(e.target.value)} rows={2} />
              </Field>
              <div className="flex gap-2">
                <Button size="sm" variant="destructive" onClick={doCancel} disabled={cancelAppt.isPending}>
                  {t('common.confirm')}
                </Button>
                <Button size="sm" variant="ghost" onClick={() => setConfirmingCancel(false)}>
                  {t('common.cancel')}
                </Button>
              </div>
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}
