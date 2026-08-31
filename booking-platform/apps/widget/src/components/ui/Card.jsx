import { cn } from '@/lib/utils';

export function Card({ className, as: Tag = 'div', ...props }) {
  return <Tag className={cn('bw-card rounded-lg border border-border bg-surface p-4', className)} {...props} />;
}

export function CardButton({ className, selected, ...props }) {
  return (
    <button
      type="button"
      className={cn(
        'bw-card w-full rounded-lg border p-4 text-start transition-colors',
        selected ? 'border-primary ring-1 ring-primary bg-muted' : 'border-border hover:bg-muted',
        className
      )}
      aria-pressed={selected}
      {...props}
    />
  );
}
