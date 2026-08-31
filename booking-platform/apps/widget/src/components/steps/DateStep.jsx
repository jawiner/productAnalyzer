import { useMemo, useState } from 'react';
import { addDays, addMonths, subMonths, format, startOfMonth, endOfMonth, startOfWeek, endOfWeek, isSameMonth, isSameDay, isBefore, startOfDay } from 'date-fns';
import { ChevronLeft, ChevronRight } from 'lucide-react';
import { cn } from '@/lib/utils';
import { dateCouldHaveAvailability } from '@/lib/availabilityHeuristic';
import useT, { useLang } from '@/i18n/LanguageContext';

// Calendar UI. Dates that the client-side heuristic says can't possibly have
// availability (closed weekday / holiday / beyond max advance window) are
// visually de-emphasized but still selectable — only get-availability (the
// TimeStep) is authoritative about actual bookability for a given date.
export default function DateStep({ settings, workingHours, holidays, employeeId, onSelect, selectedDate }) {
  const t = useT();
  const { isRtl } = useLang();
  const [cursor, setCursor] = useState(() => selectedDate ? new Date(selectedDate) : new Date());

  const now = useMemo(() => new Date(), []);
  const today = startOfDay(now);
  const maxDate = addDays(today, settings.max_booking_days_ahead);

  const scopedHolidays = useMemo(
    () => holidays.filter((h) => !h.employee_id || h.employee_id === employeeId),
    [holidays, employeeId]
  );
  const scopedHours = useMemo(() => {
    const employeeHours = employeeId ? workingHours.filter((h) => h.employee_id === employeeId) : [];
    if (employeeHours.length > 0) return employeeHours;
    return workingHours.filter((h) => !h.employee_id);
  }, [workingHours, employeeId]);

  const monthStart = startOfMonth(cursor);
  const monthEnd = endOfMonth(cursor);
  const gridStart = startOfWeek(monthStart);
  const gridEnd = endOfWeek(monthEnd);

  const days = [];
  for (let d = gridStart; d <= gridEnd; d = addDays(d, 1)) days.push(d);

  const PrevIcon = isRtl ? ChevronRight : ChevronLeft;
  const NextIcon = isRtl ? ChevronLeft : ChevronRight;

  return (
    <div className="flex flex-col gap-3">
      <div>
        <h2 className="text-lg font-semibold">{t('date.title')}</h2>
        <p className="text-sm text-muted-foreground">{t('date.subtitle')}</p>
      </div>

      <div className="flex items-center justify-between">
        <button
          type="button"
          aria-label={t('common.back')}
          className="h-9 w-9 flex items-center justify-center rounded hover:bg-muted disabled:opacity-30"
          onClick={() => setCursor((c) => subMonths(c, 1))}
          disabled={isSameMonth(cursor, today) || isBefore(cursor, today)}
        >
          <PrevIcon className="h-4 w-4" aria-hidden="true" />
        </button>
        <span className="font-medium text-sm" aria-live="polite">
          {format(cursor, 'MMMM yyyy')}
        </span>
        <button
          type="button"
          aria-label={t('common.next')}
          className="h-9 w-9 flex items-center justify-center rounded hover:bg-muted"
          onClick={() => setCursor((c) => addMonths(c, 1))}
        >
          <NextIcon className="h-4 w-4" aria-hidden="true" />
        </button>
      </div>

      <div className="grid grid-cols-7 gap-1 text-center text-xs text-muted-foreground" aria-hidden="true">
        {Array.from({ length: 7 }).map((_, i) => (
          <div key={i}>{format(addDays(startOfWeek(new Date()), i), 'EEEEE')}</div>
        ))}
      </div>

      <div className="grid grid-cols-7 gap-1" role="grid">
        {days.map((day) => {
          const dateStr = format(day, 'yyyy-MM-dd');
          const inMonth = isSameMonth(day, cursor);
          const isPast = isBefore(day, today);
          const isTooFar = day > maxDate;
          const disabled = !inMonth || isPast || isTooFar;
          const likelyAvailable = dateCouldHaveAvailability({
            date: dateStr,
            now,
            maxBookingDaysAhead: settings.max_booking_days_ahead,
            workingHours: scopedHours,
            holidays: scopedHolidays,
          });
          const isSelected = selectedDate && isSameDay(day, new Date(selectedDate));

          return (
            <button
              key={dateStr}
              type="button"
              role="gridcell"
              disabled={disabled}
              aria-selected={isSelected}
              aria-label={format(day, 'PPPP')}
              onClick={() => onSelect(dateStr)}
              className={cn(
                'h-10 rounded text-sm transition-colors disabled:opacity-25 disabled:pointer-events-none',
                !inMonth && 'invisible',
                isSelected ? 'bg-primary text-primary-foreground' : 'hover:bg-muted',
                !isSelected && !disabled && !likelyAvailable && 'text-muted-foreground opacity-50'
              )}
            >
              {format(day, 'd')}
            </button>
          );
        })}
      </div>
    </div>
  );
}
