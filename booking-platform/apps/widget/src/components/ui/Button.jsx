import { forwardRef } from 'react';
import { cva } from 'class-variance-authority';
import { cn } from '@/lib/utils';

const buttonVariants = cva(
  'bw-btn inline-flex items-center justify-center gap-2 rounded font-medium transition-opacity disabled:opacity-50 disabled:pointer-events-none focus-visible:outline-none',
  {
    variants: {
      variant: {
        primary: 'bg-primary text-primary-foreground hover:opacity-90',
        secondary: 'bg-muted text-surface-foreground hover:opacity-90 border border-border',
        ghost: 'bg-transparent text-surface-foreground hover:bg-muted',
        destructive: 'bg-destructive text-destructive-foreground hover:opacity-90',
        outline: 'bg-transparent border border-border text-surface-foreground hover:bg-muted',
      },
      size: {
        default: 'h-11 px-4 text-sm',
        sm: 'h-9 px-3 text-sm',
        lg: 'h-12 px-5 text-base w-full',
      },
    },
    defaultVariants: { variant: 'primary', size: 'default' },
  }
);

const Button = forwardRef(({ className, variant, size, type = 'button', ...props }, ref) => (
  <button ref={ref} type={type} className={cn(buttonVariants({ variant, size }), className)} {...props} />
));
Button.displayName = 'Button';

export default Button;
