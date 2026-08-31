import { QueryClientProvider } from '@tanstack/react-query';
import { createAppQueryClient } from '@/lib/queryClient';
import { LanguageProvider } from '@/i18n/LanguageContext';
import BookingWidget from '@/components/BookingWidget';

const queryClient = createAppQueryClient();

// Standalone dev-mode app shell (npm run dev / npm run build). Reads a
// business id from a URL param or env fallback so the flow can be
// previewed locally without embedding the custom element. The production
// embed path is src/widget-entry.jsx instead.
function getDevBusinessId() {
  const params = new URLSearchParams(window.location.search);
  return params.get('business_id') || import.meta.env.VITE_DEV_BUSINESS_ID || '';
}

export default function App() {
  const businessId = getDevBusinessId();

  return (
    <QueryClientProvider client={queryClient}>
      <LanguageProvider initialLanguage="en">
        <div className="booking-widget-root min-h-screen">
          {businessId ? (
            <BookingWidget businessId={businessId} />
          ) : (
            <div className="p-6 text-sm text-muted-foreground max-w-md mx-auto">
              Pass a business to preview: <code>?business_id=&lt;uuid&gt;</code> in the URL, or set{' '}
              <code>VITE_DEV_BUSINESS_ID</code> in <code>.env</code>.
            </div>
          )}
        </div>
      </LanguageProvider>
    </QueryClientProvider>
  );
}
