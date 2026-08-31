import { Loader2 } from 'lucide-react';
import { cn } from '@/lib/utils';

export default function Spinner({ className, label }) {
  return (
    <span className="inline-flex items-center gap-2 text-muted-foreground" role="status" aria-live="polite">
      <Loader2 className={cn('h-4 w-4 animate-spin', className)} aria-hidden="true" />
      {label && <span className="text-sm">{label}</span>}
    </span>
  );
}
