import { useAuth } from '@/lib/AuthContext';
import Button from '@/components/ui/Button';
import useT from '@/i18n/LanguageContext';

export default function SuperAdminNotice() {
  const t = useT();
  const { signOut } = useAuth();
  return (
    <div className="min-h-screen flex items-center justify-center bg-muted px-4">
      <div className="w-full max-w-md rounded-lg border border-border bg-surface p-6 text-center shadow-sm">
        <h1 className="text-lg font-bold text-surface-foreground">{t('superAdmin.title')}</h1>
        <p className="text-sm text-muted-foreground mt-2 mb-6">{t('superAdmin.body')}</p>
        <Button variant="secondary" onClick={signOut}>
          {t('auth.signOut')}
        </Button>
      </div>
    </div>
  );
}
