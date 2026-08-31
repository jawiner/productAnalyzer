import { useEffect, useMemo, useRef, useState } from 'react';
import { useBusinessData } from '@/hooks/useBusinessData';
import { bookingApi } from '@/lib/functions';
import { applyTheme } from '@/lib/theme';
import { LoadingBlock, ErrorBlock } from '@/components/ui/StateBlock';
import StepProgress from '@/components/StepProgress';
import ServiceStep from '@/components/steps/ServiceStep';
import EmployeeStep from '@/components/steps/EmployeeStep';
import DateStep from '@/components/steps/DateStep';
import TimeStep from '@/components/steps/TimeStep';
import DetailsStep from '@/components/steps/DetailsStep';
import ConfirmationStep from '@/components/steps/ConfirmationStep';
import ManageBooking from '@/components/ManageBooking';
import useT, { useLang } from '@/i18n/LanguageContext';

/**
 * @param {{ businessId: string, rootEl?: HTMLElement, themeOverrides?: object }} props
 * rootEl/themeOverrides are only set when mounted via the <booking-widget>
 * custom element (see widget-entry.jsx); the standalone dev app passes just
 * businessId and theme application is skipped (default CSS vars apply).
 */
export default function BookingWidget({ businessId, rootEl, themeOverrides = {} }) {
  const t = useT();
  const { setLang } = useLang();
  const { data, isLoading, isError, error, refetch } = useBusinessData(businessId);

  const [step, setStep] = useState('service'); // service | employee | date | time | details | confirmation | manage
  const [selectedService, setSelectedService] = useState(null);
  const [selectedEmployee, setSelectedEmployee] = useState(null); // null = "any"
  const [selectedDate, setSelectedDate] = useState(null);
  const [selectedSlot, setSelectedSlot] = useState(null);
  const [conflictNotice, setConflictNotice] = useState(false);
  const [appointment, setAppointment] = useState(null);
  const [customerName, setCustomerName] = useState('');
  const [submitError, setSubmitError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [manageCode, setManageCode] = useState('');
  const [manageIntent, setManageIntent] = useState('cancel');

  const contentRef = useRef(null);

  // Apply the business's default language, unless overridden by the
  // `language` widget attribute (themeOverrides.language wins).
  useEffect(() => {
    if (themeOverrides.language) {
      setLang(themeOverrides.language);
    } else if (data?.settings?.default_language) {
      setLang(data.settings.default_language);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [data?.settings?.default_language, themeOverrides.language]);

  // Apply business_themes as CSS custom properties on the widget root.
  // Attribute overrides from <booking-widget> win over fetched theme values.
  useEffect(() => {
    if (rootEl) applyTheme(rootEl, data?.theme, themeOverrides);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [rootEl, data?.theme]);

  // Move focus to the step heading on every step change for accessible
  // navigation between steps.
  useEffect(() => {
    contentRef.current?.focus();
  }, [step]);

  const employeesForService = useMemo(() => {
    if (!data || !selectedService) return [];
    const allowedEmployeeIds = new Set(
      data.employeeServices.filter((es) => es.service_id === selectedService.id).map((es) => es.employee_id)
    );
    // If no employee_services rows link this service, fall back to showing
    // all active employees (business hasn't restricted assignment).
    if (data.employeeServices.filter((es) => es.service_id === selectedService.id).length === 0) {
      return data.employees;
    }
    return data.employees.filter((e) => allowedEmployeeIds.has(e.id));
  }, [data, selectedService]);

  if (isLoading) return <LoadingBlock />;
  if (isError) {
    const message = error?.isBusinessNotFound ? t('errors.businessNotFound') : t('errors.network');
    return <ErrorBlock message={message} onRetry={error?.isBusinessNotFound ? undefined : refetch} />;
  }
  if (!data) return null;

  const { business, settings, services, workingHours, holidays } = data;

  function goBackFrom(current) {
    setSubmitError('');
    if (current === 'employee') setStep('service');
    else if (current === 'date') setStep(settings.show_employee_selection ? 'employee' : 'service');
    else if (current === 'time') setStep('date');
    else if (current === 'details') setStep('time');
    else if (current === 'manage') setStep('confirmation');
  }

  function handleServiceSelect(service) {
    setSelectedService(service);
    setSelectedEmployee(null);
    setStep(settings.show_employee_selection ? 'employee' : 'date');
  }

  function handleEmployeeSelect(employee) {
    setSelectedEmployee(employee);
    setStep('date');
  }

  function handleDateSelect(dateStr) {
    setSelectedDate(dateStr);
    setSelectedSlot(null);
    setStep('time');
  }

  function handleSlotSelect(slot) {
    setSelectedSlot(slot);
    setConflictNotice(false);
    setStep('details');
  }

  async function handleDetailsSubmit(customer) {
    setIsSubmitting(true);
    setSubmitError('');
    try {
      const result = await bookingApi.createBooking({
        business_id: businessId,
        service_id: selectedService.id,
        employee_id: selectedEmployee?.id || undefined,
        starts_at: selectedSlot.startsAt,
        customer: { full_name: customer.full_name, phone: customer.phone, email: customer.email },
        notes: customer.notes,
      });
      setAppointment(result);
      setCustomerName(customer.full_name);
      setStep('confirmation');
    } catch (err) {
      if (err.isConflict) {
        // 409: someone else took the slot. Send the user back to time
        // selection with availability re-fetched (React Query will refetch
        // on remount since the slot list is no longer fresh/cached for a
        // stale response, and TimeStep always queries fresh on mount).
        setConflictNotice(true);
        setStep('time');
      } else if (err.isNetworkError) {
        setSubmitError(t('errors.network'));
      } else {
        setSubmitError(err.message || t('errors.generic'));
      }
    } finally {
      setIsSubmitting(false);
    }
  }

  function handleBookAnother() {
    setSelectedService(null);
    setSelectedEmployee(null);
    setSelectedDate(null);
    setSelectedSlot(null);
    setAppointment(null);
    setCustomerName('');
    setConflictNotice(false);
    setStep('service');
  }

  const stepOrder = settings.show_employee_selection
    ? ['service', 'employee', 'date', 'time', 'details']
    : ['service', 'date', 'time', 'details'];
  const stepIndex = Math.max(0, stepOrder.indexOf(step));

  return (
    <div className="flex flex-col p-4 max-w-md mx-auto" dir="auto">
      {step !== 'confirmation' && step !== 'manage' && (
        <StepProgress
          stepIndex={stepIndex}
          totalSteps={stepOrder.length}
          onBack={step !== 'service' ? () => goBackFrom(step) : undefined}
          backLabel={t('common.back')}
        />
      )}

      <div ref={contentRef} tabIndex={-1} className="outline-none">
        {conflictNotice && step === 'time' && (
          <p role="alert" className="mb-3 rounded border border-destructive text-destructive text-sm px-3 py-2">
            {t('errors.conflict')}
          </p>
        )}

        {step === 'service' && (
          <ServiceStep services={services} showPrices={settings.show_prices} onSelect={handleServiceSelect} />
        )}

        {step === 'employee' && (
          <EmployeeStep employees={employeesForService} onSelect={handleEmployeeSelect} />
        )}

        {step === 'date' && (
          <DateStep
            settings={settings}
            workingHours={workingHours}
            holidays={holidays}
            employeeId={selectedEmployee?.id}
            selectedDate={selectedDate}
            onSelect={handleDateSelect}
          />
        )}

        {step === 'time' && (
          <TimeStep
            businessId={businessId}
            serviceId={selectedService.id}
            employeeId={selectedEmployee?.id}
            date={selectedDate}
            onSelect={handleSlotSelect}
            onPickAnotherDate={() => setStep('date')}
          />
        )}

        {step === 'details' && (
          <DetailsStep onSubmit={handleDetailsSubmit} isSubmitting={isSubmitting} submitError={submitError} />
        )}

        {step === 'confirmation' && appointment && (
          <ConfirmationStep
            business={business}
            settings={settings}
            service={selectedService}
            employee={selectedEmployee}
            appointment={appointment}
            customerName={customerName}
            onManageBooking={(code, intent) => {
              setManageCode(code);
              setManageIntent(intent);
              setStep('manage');
            }}
            onBookAnother={handleBookAnother}
          />
        )}

        {step === 'manage' && (
          <ManageBooking initialCode={manageCode} intent={manageIntent} onClose={() => setStep('confirmation')} />
        )}
      </div>
    </div>
  );
}
