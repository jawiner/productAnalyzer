import { ChevronLeft, ChevronRight } from 'lucide-react';
import { useLang } from '@/i18n/LanguageContext';

// Minimal step indicator + back button, shared across the flow for
// consistent keyboard/focus navigation between steps.
export default function StepProgress({ stepIndex, totalSteps, onBack, backLabel }) {
  const { isRtl } = useLang();
  const BackIcon = isRtl ? ChevronRight : ChevronLeft;

  return (
    <div className="flex items-center justify-between mb-4">
      {onBack ? (
        <button
          type="button"
          onClick={onBack}
          className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-surface-foreground h-9 -ms-2 px-2 rounded focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-primary"
        >
          <BackIcon className="h-4 w-4" aria-hidden="true" />
          {backLabel}
        </button>
      ) : (
        <span />
      )}
      <div className="flex gap-1" aria-hidden="true">
        {Array.from({ length: totalSteps }).map((_, i) => (
          <span
            key={i}
            className={`h-1.5 w-4 rounded-full ${i <= stepIndex ? 'bg-primary' : 'bg-muted'}`}
          />
        ))}
      </div>
    </div>
  );
}
