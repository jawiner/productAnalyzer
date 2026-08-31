import { useEffect, useRef } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import Input from '@/components/ui/Input';
import { Field } from '@/components/ui/Field';
import Button from '@/components/ui/Button';
import useT from '@/i18n/LanguageContext';

function buildSchema(t) {
  return z.object({
    full_name: z.string().trim().min(1, t('details.errors.fullNameRequired')),
    phone: z.string().trim().min(7, t('details.errors.phoneRequired')),
    email: z.union([z.string().trim().email(t('details.errors.emailInvalid')), z.literal('')]).optional(),
    notes: z.string().optional(),
  });
}

export default function DetailsStep({ onSubmit, isSubmitting, submitError }) {
  const t = useT();
  const nameRef = useRef(null);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm({
    resolver: zodResolver(buildSchema(t)),
    defaultValues: { full_name: '', phone: '', email: '', notes: '' },
  });

  // Focus management: move focus to the first field when this step mounts.
  useEffect(() => {
    nameRef.current?.focus();
  }, []);

  const { ref: nameFieldRef, ...nameField } = register('full_name');

  return (
    <form
      className="flex flex-col gap-4"
      onSubmit={handleSubmit((values) =>
        onSubmit({ ...values, email: values.email || undefined, notes: values.notes || undefined })
      )}
      noValidate
    >
      <div>
        <h2 className="text-lg font-semibold">{t('details.title')}</h2>
        <p className="text-sm text-muted-foreground">{t('details.subtitle')}</p>
      </div>

      <Field id="full_name" label={t('details.fullName')} error={errors.full_name?.message}>
        <Input
          id="full_name"
          autoComplete="name"
          placeholder={t('details.fullNamePlaceholder')}
          aria-invalid={Boolean(errors.full_name)}
          ref={(el) => {
            nameFieldRef(el);
            nameRef.current = el;
          }}
          {...nameField}
        />
      </Field>

      <Field id="phone" label={t('details.phone')} error={errors.phone?.message}>
        <Input
          id="phone"
          type="tel"
          autoComplete="tel"
          placeholder={t('details.phonePlaceholder')}
          aria-invalid={Boolean(errors.phone)}
          {...register('phone')}
        />
      </Field>

      <Field id="email" label={`${t('details.email')} (${t('common.optional')})`} error={errors.email?.message}>
        <Input
          id="email"
          type="email"
          autoComplete="email"
          placeholder={t('details.emailPlaceholder')}
          aria-invalid={Boolean(errors.email)}
          {...register('email')}
        />
      </Field>

      <Field id="notes" label={`${t('details.notes')} (${t('common.optional')})`}>
        <textarea
          id="notes"
          rows={3}
          placeholder={t('details.notesPlaceholder')}
          className="flex w-full rounded border border-border bg-surface px-3 py-2 text-sm text-surface-foreground placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-primary"
          {...register('notes')}
        />
      </Field>

      {submitError && (
        <p role="alert" className="text-sm text-destructive">
          {submitError}
        </p>
      )}

      <Button type="submit" size="lg" disabled={isSubmitting}>
        {isSubmitting ? t('common.submitting') : t('details.submit')}
      </Button>
    </form>
  );
}
