import { useEffect, useState } from 'react';
import { Plus, Pencil, Trash2 } from 'lucide-react';
import { Card, CardBody } from '@/components/ui/Card';
import Button from '@/components/ui/Button';
import Input from '@/components/ui/Input';
import Textarea from '@/components/ui/Textarea';
import { Field } from '@/components/ui/Field';
import Badge from '@/components/ui/Badge';
import { Dialog, DialogContent } from '@/components/ui/Dialog';
import { LoadingBlock, ErrorBlock, EmptyBlock } from '@/components/ui/StateBlock';
import { useServices, useSaveService, useDeleteService } from '@/hooks/useServices';
import { formatCurrency } from '@/lib/utils';
import useT from '@/i18n/LanguageContext';

const emptyForm = {
  name: '',
  description: '',
  duration_minutes: 30,
  price: '',
  image_url: '',
  is_active: true,
  sort_order: 0,
};

export default function Services() {
  const t = useT();
  const { data: services, isLoading, isError, refetch } = useServices();
  const saveService = useSaveService();
  const deleteService = useDeleteService();

  const [formOpen, setFormOpen] = useState(false);
  const [form, setForm] = useState(emptyForm);
  const [error, setError] = useState(null);
  const [confirmDeleteId, setConfirmDeleteId] = useState(null);

  const openNew = () => {
    setForm(emptyForm);
    setError(null);
    setFormOpen(true);
  };

  const openEdit = (service) => {
    setForm({
      id: service.id,
      name: service.name,
      description: service.description || '',
      duration_minutes: service.duration_minutes,
      price: service.price ?? '',
      image_url: service.image_url || '',
      is_active: service.is_active,
      sort_order: service.sort_order,
    });
    setError(null);
    setFormOpen(true);
  };

  const onSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    if (!form.name || !form.duration_minutes) {
      setError(t('errors.saveFailed'));
      return;
    }
    try {
      await saveService.mutateAsync({
        ...form,
        duration_minutes: Number(form.duration_minutes),
        price: form.price === '' ? null : Number(form.price),
        sort_order: Number(form.sort_order) || 0,
      });
      setFormOpen(false);
    } catch (err) {
      setError(t('errors.saveFailed'));
    }
  };

  const onDelete = async (id) => {
    try {
      await deleteService.mutateAsync(id);
      setConfirmDeleteId(null);
    } catch {
      setConfirmDeleteId(null);
    }
  };

  if (isLoading) return <LoadingBlock />;
  if (isError) return <ErrorBlock onRetry={refetch} />;

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-surface-foreground">{t('services.title')}</h1>
          <p className="text-sm text-muted-foreground">{t('services.subtitle')}</p>
        </div>
        <Button size="sm" onClick={openNew}>
          <Plus className="h-4 w-4" /> {t('services.add')}
        </Button>
      </div>

      {services.length === 0 ? (
        <EmptyBlock message={t('services.empty')} action={<Button onClick={openNew}>{t('services.add')}</Button>} />
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {services.map((s) => (
            <Card key={s.id}>
              <CardBody className="flex flex-col gap-2">
                <div className="flex items-start justify-between gap-2">
                  <p className="font-semibold text-surface-foreground">{s.name}</p>
                  <Badge className={s.is_active ? 'bg-green-100 text-green-800' : 'bg-slate-200 text-slate-600'}>
                    {s.is_active ? t('common.active') : t('common.inactive')}
                  </Badge>
                </div>
                {s.description && <p className="text-sm text-muted-foreground line-clamp-2">{s.description}</p>}
                <div className="flex items-center gap-3 text-sm text-muted-foreground">
                  <span>{t('common.minutes', { n: s.duration_minutes })}</span>
                  <span>{formatCurrency(s.price)}</span>
                </div>
                <div className="flex gap-2 pt-2">
                  <Button size="sm" variant="outline" onClick={() => openEdit(s)}>
                    <Pencil className="h-3.5 w-3.5" /> {t('common.edit')}
                  </Button>
                  {confirmDeleteId === s.id ? (
                    <Button size="sm" variant="destructive" onClick={() => onDelete(s.id)}>
                      {t('common.confirm')}
                    </Button>
                  ) : (
                    <Button size="sm" variant="ghost" onClick={() => setConfirmDeleteId(s.id)}>
                      <Trash2 className="h-3.5 w-3.5" />
                    </Button>
                  )}
                </div>
              </CardBody>
            </Card>
          ))}
        </div>
      )}

      <Dialog open={formOpen} onOpenChange={setFormOpen}>
        <DialogContent title={form.id ? t('services.edit') : t('services.add')}>
          <form onSubmit={onSubmit} className="flex flex-col gap-4">
            <Field id="svc-name" label={t('services.name')}>
              <Input id="svc-name" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} required />
            </Field>
            <Field id="svc-desc" label={`${t('services.description')} (${t('common.optional')})`}>
              <Textarea id="svc-desc" value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} rows={2} />
            </Field>
            <div className="grid grid-cols-2 gap-3">
              <Field id="svc-duration" label={t('services.duration')}>
                <Input
                  id="svc-duration"
                  type="number"
                  min={5}
                  step={5}
                  value={form.duration_minutes}
                  onChange={(e) => setForm({ ...form, duration_minutes: e.target.value })}
                  required
                />
              </Field>
              <Field id="svc-price" label={`${t('services.price')} (${t('common.optional')})`}>
                <Input
                  id="svc-price"
                  type="number"
                  min={0}
                  step="0.01"
                  value={form.price}
                  onChange={(e) => setForm({ ...form, price: e.target.value })}
                />
              </Field>
            </div>
            <Field id="svc-image" label={`${t('services.imageUrl')} (${t('common.optional')})`}>
              <Input id="svc-image" value={form.image_url} onChange={(e) => setForm({ ...form, image_url: e.target.value })} />
            </Field>
            <Field id="svc-sort" label={t('services.sortOrder')}>
              <Input id="svc-sort" type="number" value={form.sort_order} onChange={(e) => setForm({ ...form, sort_order: e.target.value })} />
            </Field>
            <label className="flex items-center gap-2 text-sm text-surface-foreground">
              <input type="checkbox" checked={form.is_active} onChange={(e) => setForm({ ...form, is_active: e.target.checked })} />
              {t('services.isActive')}
            </label>

            {error && (
              <p role="alert" className="text-sm text-destructive">
                {error}
              </p>
            )}

            <div className="flex gap-2 pt-2">
              <Button type="submit" disabled={saveService.isPending}>
                {saveService.isPending ? t('common.saving') : t('common.save')}
              </Button>
              <Button type="button" variant="ghost" onClick={() => setFormOpen(false)}>
                {t('common.cancel')}
              </Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
