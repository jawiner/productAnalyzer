import { format } from 'date-fns';
import { CalendarPlus, CheckCircle2 } from 'lucide-react';
import Button from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { buildIcsDataUri } from '@/lib/ics';
import useT from '@/i18n/LanguageContext';

export default function ConfirmationStep({
  business,
  settings,
  service,
  employee,
  appointment,
  customerName,
  onManageBooking,
  onBookAnother,
}) {
  const t = useT();

  const icsHref = buildIcsDataUri({
    businessName: business.name,
    serviceName: service.name,
    employeeName: employee?.name,
    startsAt: appointment.starts_at,
    endsAt: appointment.ends_at,
    confirmationCode: appointment.confirmation_code,
    address: business.address,
  });

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-col items-center text-center gap-2 py-2">
        <CheckCircle2 className="h-10 w-10 text-primary" aria-hidden="true" />
        <h2 className="text-lg font-semibold">{t('confirmation.title')}</h2>
        <p className="text-sm text-muted-foreground">{t('confirmation.subtitle')}</p>
      </div>

      <Card className="flex flex-col gap-2 text-sm">
        <Row label={t('confirmation.business')} value={business.name} />
        <Row label={t('confirmation.service')} value={service.name} />
        {employee && <Row label={t('confirmation.employee')} value={employee.name} />}
        <Row label={t('confirmation.when')} value={format(new Date(appointment.starts_at), 'PPPP p')} />
        <Row label={t('confirmation.customer')} value={customerName} />
        <Row label={t('confirmation.code')} value={<span className="font-mono font-semibold">{appointment.confirmation_code}</span>} />
      </Card>

      <a
        href={icsHref}
        download={`${service.name.replace(/\s+/g, '-')}.ics`}
        className="bw-btn inline-flex items-center justify-center gap-2 h-11 px-4 text-sm rounded border border-border hover:bg-muted"
      >
        <CalendarPlus className="h-4 w-4" aria-hidden="true" />
        {t('confirmation.addToCalendar')}
      </a>

      {(settings.allow_cancellation || settings.allow_rescheduling) && (
        <div className="flex gap-2">
          {settings.allow_cancellation && (
            <Button
              variant="outline"
              size="sm"
              className="flex-1"
              onClick={() => onManageBooking(appointment.confirmation_code, 'cancel')}
            >
              {t('confirmation.cancelBooking')}
            </Button>
          )}
          {settings.allow_rescheduling && (
            <Button
              variant="outline"
              size="sm"
              className="flex-1"
              onClick={() => onManageBooking(appointment.confirmation_code, 'reschedule')}
            >
              {t('confirmation.rescheduleBooking')}
            </Button>
          )}
        </div>
      )}

      <Button variant="ghost" onClick={onBookAnother}>
        {t('confirmation.bookAnother')}
      </Button>
    </div>
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
