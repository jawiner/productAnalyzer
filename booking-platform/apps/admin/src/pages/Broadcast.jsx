import { useState } from 'react';
import { MessageSquareWarning } from 'lucide-react';
import { Card, CardBody } from '@/components/ui/Card';
import Button from '@/components/ui/Button';
import Textarea from '@/components/ui/Textarea';
import { Field } from '@/components/ui/Field';
import { LoadingBlock } from '@/components/ui/StateBlock';
import { useCustomerCount } from '@/hooks/useCustomers';
import { useBusinessSettings } from '@/hooks/useSettings';
import { bookingApi } from '@/lib/functions';
import useT from '@/i18n/LanguageContext';

const MAX_LENGTH = 1500;

export default function Broadcast() {
  const t = useT();
  const { data: customerCount, isLoading: countLoading } = useCustomerCount();
  const { data: settings, isLoading: settingsLoading } = useBusinessSettings();

  const [message, setMessage] = useState('');
  const [confirming, setConfirming] = useState(false);
  const [isSending, setIsSending] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');

  if (countLoading || settingsLoading) return <LoadingBlock />;

  const smsDisabled = !settings?.sms_enabled;
  const trimmed = message.trim();
  const canSend = trimmed.length > 0 && trimmed.length <= MAX_LENGTH && !smsDisabled;

  const handleSend = async () => {
    setError('');
    setIsSending(true);
    try {
      const res = await bookingApi.sendBroadcast({ message: trimmed });
      setResult(res);
      setMessage('');
      setConfirming(false);
    } catch (err) {
      setError(err.message === 'request_failed' ? t('errors.generic') : err.message);
    } finally {
      setIsSending(false);
    }
  };

  return (
    <div className="flex flex-col gap-6 max-w-2xl">
      <div>
        <h1 className="text-2xl font-bold text-surface-foreground">{t('broadcast.title')}</h1>
        <p className="text-sm text-muted-foreground">{t('broadcast.subtitle')}</p>
      </div>

      {smsDisabled && (
        <Card>
          <CardBody className="flex items-start gap-3">
            <MessageSquareWarning className="h-5 w-5 text-warning shrink-0 mt-0.5" />
            <p className="text-sm text-surface-foreground">{t('broadcast.smsDisabledHint')}</p>
          </CardBody>
        </Card>
      )}

      <Card>
        <CardBody className="flex flex-col gap-4">
          <Field id="broadcast-message" label={t('broadcast.messageLabel')} hint={t('broadcast.messageHint')}>
            <Textarea
              id="broadcast-message"
              rows={5}
              maxLength={MAX_LENGTH}
              value={message}
              disabled={smsDisabled || isSending}
              onChange={(e) => {
                setMessage(e.target.value);
                setConfirming(false);
                setResult(null);
              }}
              placeholder={t('broadcast.messagePlaceholder')}
            />
            <p className="text-xs text-muted-foreground text-end mt-1">
              {trimmed.length} / {MAX_LENGTH}
            </p>
          </Field>

          <p className="text-sm text-muted-foreground">{t('broadcast.recipientCount', { count: customerCount ?? 0 })}</p>

          {error && (
            <p role="alert" className="text-sm text-destructive">
              {error}
            </p>
          )}

          {result && (
            <p className="text-sm text-success">
              {t('broadcast.result', { sent: result.sent, failed: result.failed, skipped: result.skipped, total: result.total })}
            </p>
          )}

          {!confirming ? (
            <Button onClick={() => setConfirming(true)} disabled={!canSend} className="self-start">
              {t('broadcast.review')}
            </Button>
          ) : (
            <div className="flex flex-col gap-3 rounded-lg border border-warning/40 bg-warning/5 p-4">
              <p className="text-sm font-medium text-surface-foreground">
                {t('broadcast.confirmTitle', { count: customerCount ?? 0 })}
              </p>
              <p className="text-sm text-muted-foreground whitespace-pre-wrap">{trimmed}</p>
              <div className="flex gap-2">
                <Button variant="outline" onClick={() => setConfirming(false)} disabled={isSending}>
                  {t('common.back')}
                </Button>
                <Button variant="destructive" onClick={handleSend} disabled={isSending}>
                  {isSending ? t('common.submitting') : t('broadcast.confirmSend')}
                </Button>
              </div>
            </div>
          )}
        </CardBody>
      </Card>
    </div>
  );
}
