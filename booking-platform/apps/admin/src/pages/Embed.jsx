import { useState } from 'react';
import { Copy, Check } from 'lucide-react';
import { Card, CardBody } from '@/components/ui/Card';
import Button from '@/components/ui/Button';
import { useAuth } from '@/lib/AuthContext';
import useT from '@/i18n/LanguageContext';

export default function Embed() {
  const t = useT();
  const { businessId } = useAuth();
  const [copied, setCopied] = useState(false);

  // The widget's own origin is a separate deployment from this admin app;
  // in production this should be the widget's actual hosted URL. Using a
  // relative-looking placeholder host here that operators swap in — the
  // real value ships via an env var once the widget's deploy URL is known.
  const widgetSrc = import.meta.env.VITE_WIDGET_EMBED_URL || 'https://widget.yourbookingplatform.com/widget.js';
  const snippet = `<script src="${widgetSrc}"></script>\n<booking-widget business-id="${businessId}"></booking-widget>`;

  const onCopy = async () => {
    try {
      await navigator.clipboard.writeText(snippet);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // clipboard API unavailable — user can still select/copy manually
    }
  };

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold text-surface-foreground">{t('embed.title')}</h1>
        <p className="text-sm text-muted-foreground">{t('embed.subtitle')}</p>
      </div>

      <Card>
        <CardBody className="flex flex-col gap-3">
          <pre className="rounded bg-muted p-4 text-xs overflow-x-auto whitespace-pre-wrap break-all">
            <code>{snippet}</code>
          </pre>
          <div className="flex items-center gap-3">
            <Button size="sm" variant="secondary" onClick={onCopy}>
              {copied ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
              {copied ? t('embed.copied') : t('embed.copy')}
            </Button>
          </div>
          <p className="text-xs text-muted-foreground">{t('embed.instructions')}</p>
        </CardBody>
      </Card>
    </div>
  );
}
