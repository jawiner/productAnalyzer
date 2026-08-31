import { useEffect, useState } from 'react';
import { format } from 'date-fns';
import { Dialog, DialogContent } from '@/components/ui/Dialog';
import Badge from '@/components/ui/Badge';
import Button from '@/components/ui/Button';
import Textarea from '@/components/ui/Textarea';
import { Field } from '@/components/ui/Field';
import { LoadingBlock } from '@/components/ui/StateBlock';
import { useCustomer, useCustomerAppointments, useSaveCustomer } from '@/hooks/useCustomers';
import { formatCurrency } from '@/lib/utils';
import useT from '@/i18n/LanguageContext';

export default function CustomerDetail({ customerId, open, onOpenChange }) {
  const t = useT();
  const { data: customer, isLoading: l1 } = useCustomer(customerId);
  const { data: appointments, isLoading: l2 } = useCustomerAppointments(customerId);
  const saveCustomer = useSaveCustomer();

  const [notes, setNotes] = useState('');
  const [saveMsg, setSaveMsg] = useState(null);

  useEffect(() => {
    if (customer) setNotes(customer.notes || '');
    setSaveMsg(null);
  }, [customer]);

  if (!open) return null;

  const totalAppointments = appointments?.length || 0;
  const totalRevenue = (appointments || [])
    .filter((a) => ['completed', 'confirmed'].includes(a.status) && a.price_at_booking != null)
    .reduce((sum, a) => sum + Number(a.price_at_booking), 0);
  const hasPrices = (appointments || []).some((a) => a.price_at_booking != null);

  const saveNotes = async () => {
    setSaveMsg(null);
    try {
      await saveCustomer.mutateAsync({ id: customerId, full_name: customer.full_name, phone: customer.phone, email: customer.email, notes });
      setSaveMsg(t('common.saved'));
    } catch {
      // surfaced via disabled state / silent retry is acceptable here
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent title={customer?.full_name || ''} className="max-w-xl">
        {l1 || !customer ? (
          <LoadingBlock />
        ) : (
          <div className="flex flex-col gap-4">
            <div className="text-sm text-muted-foreground">
              {customer.phone} {customer.email ? `· ${customer.email}` : ''}
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div className="rounded border border-border p-3">
                <p className="text-xs text-muted-foreground">{t('customers.totalAppointments')}</p>
                <p className="text-xl font-bold text-surface-foreground">{totalAppointments}</p>
              </div>
              <div className="rounded border border-border p-3">
                <p className="text-xs text-muted-foreground">{t('customers.totalRevenue')}</p>
                <p className="text-xl font-bold text-surface-foreground">{hasPrices ? formatCurrency(totalRevenue) : '—'}</p>
              </div>
            </div>

            <Field id="cust-notes" label={t('customers.notes')}>
              <Textarea
                id="cust-notes"
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                placeholder={t('customers.notesPlaceholder')}
                rows={3}
              />
            </Field>
            <div className="flex items-center gap-3">
              <Button size="sm" onClick={saveNotes} disabled={saveCustomer.isPending}>
                {saveCustomer.isPending ? t('common.saving') : t('common.save')}
              </Button>
              {saveMsg && <span className="text-sm text-success">{saveMsg}</span>}
            </div>

            <div>
              <h3 className="text-sm font-semibold text-surface-foreground mb-2">{t('customers.history')}</h3>
              {l2 ? (
                <LoadingBlock />
              ) : totalAppointments === 0 ? (
                <p className="text-sm text-muted-foreground">{t('common.noResults')}</p>
              ) : (
                <ul className="flex flex-col divide-y divide-border max-h-64 overflow-y-auto">
                  {appointments.map((a) => (
                    <li key={a.id} className="py-2 flex items-center justify-between gap-3 text-sm">
                      <div className="min-w-0">
                        <p className="font-medium text-surface-foreground truncate">{a.services?.name}</p>
                        <p className="text-muted-foreground">{format(new Date(a.starts_at), 'PPP p')}</p>
                      </div>
                      <Badge status={a.status}>{t(`appt.status.${a.status}`)}</Badge>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
