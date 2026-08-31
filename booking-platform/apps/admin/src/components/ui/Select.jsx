import { forwardRef } from 'react';
import { cn } from '@/lib/utils';

// Plain native <select> — sufficient for this app's needs (weekday, status,
// language pickers) and keeps forms fully keyboard/screen-reader accessible
// without pulling in Radix's Select just for this.
const Select = forwardRef(({ className, children, ...props }, ref) => (
  <select
    ref={ref}
    className={cn(
      'flex h-10 w-full rounded border border-border bg-surface px-3 text-sm text-surface-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-primary disabled:opacity-50',
      className
    )}
    {...props}
  >
    {children}
  </select>
));
Select.displayName = 'Select';

export default Select;
