import { useMemo } from 'react';
import { startOfDay, endOfDay, subDays } from 'date-fns';
import { Card, CardBody } from '@/components/ui/Card';
import { LoadingBlock, ErrorBlock } from '@/components/ui/StateBlock';
import { useAppointmentsRange } from '@/hooks/useAppointments';
import { formatCurrency, cn } from '@/lib/utils';
import useT from '@/i18n/LanguageContext';

function StatCard({ label, value, hint, className }) {
  return (
    <Card className={className}>
      <CardBody>
        <p className="text-sm text-muted-foreground">{label}</p>
        <p className="text-3xl font-bold text-surface-foreground mt-1">{value}</p>
        {hint && <p className="text-xs text-muted-foreground mt-2">{hint}</p>}
      </CardBody>
    </Card>
  );
}

export default function Dashboard() {
  const t = useT();
  const rangeStart = useMemo(() => startOfDay(subDays(new Date(), 30)).toISOString(), []);
  const rangeEnd = useMemo(() => endOfDay(new Date()).toISOString(), []);
  const { data: appointments, isLoading, isError, refetch } = useAppointmentsRange(rangeStart, rangeEnd);

  const todayStart = useMemo(() => startOfDay(new Date()).toISOString(), []);
  const todayEnd = useMemo(() => endOfDay(new Date()).toISOString(), []);

  if (isLoading) return <LoadingBlock />;
  if (isError) return <ErrorBlock onRetry={refetch} />;

  const todayAppts = appointments.filter((a) => a.starts_at >= todayStart && a.starts_at <= todayEnd && a.status !== 'cancelled');
  const upcoming = appointments.filter((a) => a.starts_at > new Date().toISOString() && a.status !== 'cancelled');
  const cancelled = appointments.filter((a) => a.status === 'cancelled');
  const hasPrices = appointments.some((a) => a.price_at_booking != null);
  const revenue = appointments
    .filter((a) => ['completed', 'confirmed'].includes(a.status) && a.price_at_booking != null)
    .reduce((sum, a) => sum + Number(a.price_at_booking), 0);

  return (
    <div className="flex flex-col gap-6">
      <h1 className="text-2xl font-bold text-surface-foreground">{t('dashboard.title')}</h1>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard label={t('dashboard.today')} value={todayAppts.length} />
        <StatCard label={t('dashboard.upcoming')} value={upcoming.length} />
        <StatCard label={t('dashboard.cancelled')} value={cancelled.length} />
        <StatCard
          label={t('dashboard.revenue')}
          value={hasPrices ? formatCurrency(revenue) : '—'}
          hint={hasPrices ? t('dashboard.revenueHint') : t('dashboard.noPrices')}
        />
      </div>

      <Card>
        <CardBody>
          <h2 className="text-sm font-semibold text-surface-foreground mb-3">{t('dashboard.today')}</h2>
          {todayAppts.length === 0 ? (
            <p className="text-sm text-muted-foreground">{t('calendar.noAppointments')}</p>
          ) : (
            <ul className="flex flex-col divide-y divide-border">
              {todayAppts
                .sort((a, b) => a.starts_at.localeCompare(b.starts_at))
                .map((a) => (
                  <li key={a.id} className="py-2.5 flex items-center justify-between gap-3 text-sm">
                    <div className="min-w-0">
                      <p className="font-medium text-surface-foreground truncate">{a.customers?.full_name}</p>
                      <p className="text-muted-foreground truncate">
                        {a.services?.name}
                        {a.employees?.name ? ` · ${a.employees.name}` : ''}
                      </p>
                    </div>
                    <span className="text-muted-foreground shrink-0">
                      {new Date(a.starts_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </span>
                  </li>
                ))}
            </ul>
          )}
        </CardBody>
      </Card>
    </div>
  );
}
