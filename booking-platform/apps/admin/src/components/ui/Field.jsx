import { cn } from '@/lib/utils';

export function Field({ id, label, error, hint, children }) {
  return (
    <div className="flex flex-col gap-1.5">
      {label && (
        <label htmlFor={id} className="text-sm font-medium text-surface-foreground">
          {label}
        </label>
      )}
      {children}
      {hint && !error && <p className="text-xs text-muted-foreground">{hint}</p>}
      {error && (
        <p role="alert" className={cn('text-xs text-destructive')}>
          {error}
        </p>
      )}
    </div>
  );
}
