import { useState } from 'react';
import { useAuth } from '@/lib/AuthContext';
import Button from '@/components/ui/Button';
import Input from '@/components/ui/Input';
import { Field } from '@/components/ui/Field';
import useT from '@/i18n/LanguageContext';

export default function Login() {
  const t = useT();
  const { signIn } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  const onSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await signIn(email, password);
    } catch (err) {
      setError(t('errors.loginFailed'));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-muted px-4">
      <form onSubmit={onSubmit} className="w-full max-w-sm rounded-lg border border-border bg-surface p-6 shadow-sm">
        <h1 className="text-xl font-bold text-surface-foreground">{t('auth.title')}</h1>
        <p className="text-sm text-muted-foreground mt-1 mb-6">{t('auth.subtitle')}</p>

        <div className="flex flex-col gap-4">
          <Field id="email" label={t('auth.email')}>
            <Input
              id="email"
              type="email"
              autoComplete="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
          </Field>
          <Field id="password" label={t('auth.password')}>
            <Input
              id="password"
              type="password"
              autoComplete="current-password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </Field>

          {error && (
            <p role="alert" className="text-sm text-destructive">
              {error}
            </p>
          )}

          <Button type="submit" size="lg" className="w-full" disabled={submitting}>
            {submitting ? t('auth.signingIn') : t('auth.signIn')}
          </Button>
        </div>
      </form>
    </div>
  );
}
