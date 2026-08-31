import { format } from 'date-fns';
import { useAvailability } from '@/hooks/useAvailability';
import { LoadingBlock, ErrorBlock, EmptyBlock } from '@/components/ui/StateBlock';
import Button from '@/components/ui/Button';
import useT from '@/i18n/LanguageContext';

export default function TimeStep({ businessId, serviceId, employeeId, date, onSelect, onPickAnotherDate }) {
  const t = useT();
  const { data: slots, isLoading, isError, refetch } = useAvailability({ businessId, serviceId, employeeId, date });

  return (
    <div className="flex flex-col gap-3">
      <div>
        <h2 className="text-lg font-semibold">{t('time.title')}</h2>
        <p className="text-sm text-muted-foreground">
          {t('time.subtitle', { date: format(new Date(date), 'PPPP') })}
        </p>
      </div>

      {isLoading && <LoadingBlock />}
      {isError && <ErrorBlock message={t('errors.generic')} onRetry={refetch} />}
      {!isLoading && !isError && slots && slots.length === 0 && (
        <EmptyBlock
          message={t('time.noSlots')}
          action={
            <Button variant="secondary" size="sm" onClick={onPickAnotherDate}>
              {t('time.pickAnotherDate')}
            </Button>
          }
        />
      )}
      {!isLoading && !isError && slots && slots.length > 0 && (
        <div className="grid grid-cols-3 gap-2" role="list">
          {slots.map((slot) => (
            <button
              key={slot.startsAt}
              type="button"
              role="listitem"
              onClick={() => onSelect(slot)}
              className="h-11 rounded border border-border text-sm font-medium hover:bg-muted focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-primary"
            >
              {format(new Date(slot.startsAt), 'p')}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
