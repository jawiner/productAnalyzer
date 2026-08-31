import { AlertCircle, Inbox } from 'lucide-react';
import Button from './Button';
import useT from '@/i18n/LanguageContext';

export function LoadingBlock({ label }) {
  const t = useT();
  return (
    <div className="flex flex-col items-center justify-center gap-3 py-16 text-center">
      <div className="h-8 w-8 animate-spin rounded-full border-4 border-muted border-t-primary" role="status" aria-label={label || t('common.loading')} />
      <p className="text-sm text-muted-foreground">{label || t('common.loading')}</p>
    </div>
  );
}

export function ErrorBlock({ message, onRetry }) {
  const t = useT();
  return (
    <div className="flex flex-col items-center justify-center gap-3 py-16 text-center px-4" role="alert">
      <AlertCircle className="h-8 w-8 text-destructive" aria-hidden="true" />
      <p className="text-sm text-surface-foreground max-w-xs">{message || t('errors.generic')}</p>
      {onRetry && (
        <Button variant="secondary" size="sm" onClick={onRetry}>
          {t('common.retry')}
        </Button>
      )}
    </div>
  );
}

export function EmptyBlock({ message, action }) {
  const t = useT();
  return (
    <div className="flex flex-col items-center justify-center gap-3 py-16 text-center px-4">
      <Inbox className="h-8 w-8 text-muted-foreground" aria-hidden="true" />
      <p className="text-sm text-muted-foreground max-w-xs">{message || t('common.noResults')}</p>
      {action}
    </div>
  );
}
