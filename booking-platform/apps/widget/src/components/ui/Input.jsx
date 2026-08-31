import { forwardRef } from 'react';
import { cn } from '@/lib/utils';

const Input = forwardRef(({ className, ...props }, ref) => (
  <input
    ref={ref}
    className={cn(
      'bw-input flex h-11 w-full rounded border border-border bg-surface px-3 text-sm text-surface-foreground placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-primary',
      className
    )}
    {...props}
  />
));
Input.displayName = 'Input';

export default Input;
