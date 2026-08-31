import { useMemo, useState } from 'react';
import {
  startOfDay,
  endOfDay,
  startOfWeek,
  endOfWeek,
  startOfMonth,
  endOfMonth,
  addDays,
  addWeeks,
  addMonths,
  subDays,
  subWeeks,
  subMonths,
  eachDayOfInterval,
  isSameDay,
  isSameMonth,
  format,
} from 'date-fns';
import { ChevronLeft, ChevronRight, Plus } from 'lucide-react';
import Button from '@/components/ui/Button';
import Badge from '@/components/ui/Badge';
import { LoadingBlock, ErrorBlock } from '@/components/ui/StateBlock';
import { useAppointmentsRange } from '@/hooks/useAppointments';
import AppointmentDetail from '@/components/appointments/AppointmentDetail';
import AppointmentForm from '@/components/appointments/AppointmentForm';
import { cn } from '@/lib/utils';
import useT from '@/i18n/LanguageContext';

const VIEWS = ['day', 'week', 'month'];

function rangeFor(view, anchor) {
  if (view === 'day') return [startOfDay(anchor), endOfDay(anchor)];
  if (view === 'week') return [startOfWeek(anchor), endOfWeek(anchor)];
  return [startOfMonth(startOfWeek(startOfMonth(anchor))), endOfMonth(endOfWeek(endOfMonth(anchor)))];
}

function shift(view, anchor, dir) {
  if (view === 'day') return dir > 0 ? addDays(anchor, 1) : subDays(anchor, 1);
  if (view === 'week') return dir > 0 ? addWeeks(anchor, 1) : subWeeks(anchor, 1);
  return dir > 0 ? addMonths(anchor, 1) : subMonths(anchor, 1);
}

export default function CalendarView() {
  const t = useT();
  const [view, setView] = useState('week');
  const [anchor, setAnchor] = useState(new Date());
  const [detailAppt, setDetailAppt] = useState(null);
  const [formOpen, setFormOpen] = useState(false);
  const [formInitial, setFormInitial] = useState(null);
  const [formDate, setFormDate] = useState(null);

  const [rangeStart, rangeEnd] = useMemo(() => rangeFor(view, anchor), [view, anchor]);
  const { data: appointments, isLoading, isError, refetch } = useAppointmentsRange(rangeStart.toISOString(), rangeEnd.toISOString());

  const days = useMemo(() => eachDayOfInterval({ start: rangeStart, end: rangeEnd }), [rangeStart, rangeEnd]);

  const byDay = useMemo(() => {
    const map = new Map();
    (appointments || []).forEach((a) => {
      const key = format(new Date(a.starts_at), 'yyyy-MM-dd');
      if (!map.has(key)) map.set(key, []);
      map.get(key).push(a);
    });
    for (const list of map.values()) list.sort((a, b) => a.starts_at.localeCompare(b.starts_at));
    return map;
  }, [appointments]);

  const openNew = (date) => {
    setFormInitial(null);
    setFormDate(date || anchor);
    setFormOpen(true);
  };

  const openReschedule = (appt) => {
    setDetailAppt(null);
    setFormInitial(appt);
    setFormOpen(true);
  };

  const headerLabel =
    view === 'day' ? format(anchor, 'PPP') : view === 'week' ? `${format(rangeStart, 'MMM d')} – ${format(rangeEnd, 'MMM d, yyyy')}` : format(anchor, 'MMMM yyyy');

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-2xl font-bold text-surface-foreground">{t('calendar.title')}</h1>
        <Button size="sm" onClick={() => openNew(anchor)}>
          <Plus className="h-4 w-4" /> {t('calendar.newAppointment')}
        </Button>
      </div>

      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <Button size="icon" variant="outline" onClick={() => setAnchor(shift(view, anchor, -1))} aria-label={t('common.back')}>
            <ChevronLeft className="h-4 w-4" />
          </Button>
          <Button size="sm" variant="outline" onClick={() => setAnchor(new Date())}>
            {t('calendar.today')}
          </Button>
          <Button size="icon" variant="outline" onClick={() => setAnchor(shift(view, anchor, 1))} aria-label={t('common.back')}>
            <ChevronRight className="h-4 w-4" />
          </Button>
          <span className="text-sm font-medium text-surface-foreground ms-2">{headerLabel}</span>
        </div>
        <div className="flex gap-1 rounded border border-border p-0.5">
          {VIEWS.map((v) => (
            <button
              key={v}
              onClick={() => setView(v)}
              className={cn('px-3 py-1.5 text-sm rounded', view === v ? 'bg-primary text-primary-foreground' : 'text-muted-foreground hover:bg-muted')}
            >
              {t(`calendar.${v}`)}
            </button>
          ))}
        </div>
      </div>

      {isLoading ? (
        <LoadingBlock />
      ) : isError ? (
        <ErrorBlock onRetry={refetch} />
      ) : view === 'month' ? (
        <MonthGrid days={days} anchor={anchor} byDay={byDay} onSelectDay={(d) => { setView('day'); setAnchor(d); }} />
      ) : (
        <AgendaColumns days={days} byDay={byDay} onSelect={setDetailAppt} onAddAt={openNew} />
      )}

      <AppointmentDetail appointment={detailAppt} open={!!detailAppt} onOpenChange={(o) => !o && setDetailAppt(null)} onReschedule={openReschedule} />
      <AppointmentForm open={formOpen} onOpenChange={setFormOpen} initial={formInitial} defaultDate={formDate} />
    </div>
  );
}

function AgendaColumns({ days, byDay, onSelect, onAddAt }) {
  const t = useT();
  return (
    <div className={cn('grid gap-3', days.length === 1 ? 'grid-cols-1' : 'grid-cols-1 sm:grid-cols-2 lg:grid-cols-7')}>
      {days.map((day) => {
        const key = format(day, 'yyyy-MM-dd');
        const list = byDay.get(key) || [];
        return (
          <div key={key} className="rounded-lg border border-border bg-surface p-3 min-h-[140px]">
            <div className="flex items-center justify-between mb-2">
              <p className="text-sm font-semibold text-surface-foreground">{format(day, 'EEE d')}</p>
              <button onClick={() => onAddAt(day)} className="text-muted-foreground hover:text-primary" aria-label={t('calendar.newAppointment')}>
                <Plus className="h-4 w-4" />
              </button>
            </div>
            {list.length === 0 ? (
              <p className="text-xs text-muted-foreground">{t('calendar.noAppointments')}</p>
            ) : (
              <ul className="flex flex-col gap-1.5">
                {list.map((a) => (
                  <li key={a.id}>
                    <button
                      onClick={() => onSelect(a)}
                      className="w-full text-start rounded border border-border bg-muted/40 hover:bg-muted px-2 py-1.5 text-xs"
                    >
                      <div className="flex items-center justify-between gap-2">
                        <span className="font-medium text-surface-foreground truncate">
                          {format(new Date(a.starts_at), 'HH:mm')} {a.customers?.full_name}
                        </span>
                        <Badge status={a.status} className="shrink-0">
                          {t(`appt.status.${a.status}`)}
                        </Badge>
                      </div>
                      <p className="text-muted-foreground truncate">{a.services?.name}</p>
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </div>
        );
      })}
    </div>
  );
}

function MonthGrid({ days, anchor, byDay, onSelectDay }) {
  const t = useT();
  const weekdayLabels = useMemo(() => {
    const start = startOfWeek(new Date());
    return Array.from({ length: 7 }, (_, i) => format(addDays(start, i), 'EEE'));
  }, []);

  return (
    <div className="rounded-lg border border-border bg-surface overflow-hidden">
      <div className="grid grid-cols-7 border-b border-border bg-muted/50">
        {weekdayLabels.map((label) => (
          <div key={label} className="p-2 text-xs font-medium text-muted-foreground text-center">
            {label}
          </div>
        ))}
      </div>
      <div className="grid grid-cols-7">
        {days.map((day) => {
          const key = format(day, 'yyyy-MM-dd');
          const list = byDay.get(key) || [];
          const inMonth = isSameMonth(day, anchor);
          const isToday = isSameDay(day, new Date());
          return (
            <button
              key={key}
              onClick={() => onSelectDay(day)}
              className={cn(
                'border-b border-e border-border p-2 text-start min-h-[84px] hover:bg-muted/50 transition-colors',
                !inMonth && 'bg-muted/30 text-muted-foreground'
              )}
            >
              <span className={cn('text-xs font-medium', isToday && 'inline-flex h-5 w-5 items-center justify-center rounded-full bg-primary text-primary-foreground')}>
                {format(day, 'd')}
              </span>
              {list.length > 0 && (
                <p className="text-[11px] text-muted-foreground mt-1">
                  {list.length} {list.length === 1 ? t('nav.appointments').replace(/s$/, '') : t('nav.appointments').toLowerCase()}
                </p>
              )}
            </button>
          );
        })}
      </div>
    </div>
  );
}
