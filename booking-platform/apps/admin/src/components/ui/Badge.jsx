import { cn } from '@/lib/utils';

const STATUS_STYLES = {
  pending: 'bg-amber-100 text-amber-800',
  confirmed: 'bg-blue-100 text-blue-800',
  completed: 'bg-green-100 text-green-800',
  cancelled: 'bg-slate-200 text-slate-600',
  no_show: 'bg-red-100 text-red-800',
};

export default function Badge({ className, status, children }) {
  return (
    <span
      className={cn(
        'inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium',
        status ? STATUS_STYLES[status] || 'bg-muted text-muted-foreground' : 'bg-muted text-muted-foreground',
        className
      )}
    >
      {children}
    </span>
  );
}
