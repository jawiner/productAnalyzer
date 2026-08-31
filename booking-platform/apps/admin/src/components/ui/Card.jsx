import { cn } from '@/lib/utils';

export function Card({ className, as: Tag = 'div', ...props }) {
  return <Tag className={cn('rounded-lg border border-border bg-surface', className)} {...props} />;
}

export function CardHeader({ className, ...props }) {
  return <div className={cn('flex items-center justify-between gap-3 border-b border-border p-4', className)} {...props} />;
}

export function CardBody({ className, ...props }) {
  return <div className={cn('p-4', className)} {...props} />;
}
