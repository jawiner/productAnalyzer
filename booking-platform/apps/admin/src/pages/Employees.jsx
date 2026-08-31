import { useState } from 'react';
import { Plus, Pencil, Trash2 } from 'lucide-react';
import { Card, CardBody } from '@/components/ui/Card';
import Button from '@/components/ui/Button';
import Badge from '@/components/ui/Badge';
import { LoadingBlock, ErrorBlock, EmptyBlock } from '@/components/ui/StateBlock';
import { useEmployees, useDeleteEmployee } from '@/hooks/useEmployees';
import EmployeeForm from '@/components/employees/EmployeeForm';
import useT from '@/i18n/LanguageContext';

export default function Employees() {
  const t = useT();
  const { data: employees, isLoading, isError, refetch } = useEmployees();
  const deleteEmployee = useDeleteEmployee();
  const [formOpen, setFormOpen] = useState(false);
  const [editId, setEditId] = useState(null);
  const [confirmDeleteId, setConfirmDeleteId] = useState(null);

  const openNew = () => {
    setEditId(null);
    setFormOpen(true);
  };

  const openEdit = (id) => {
    setEditId(id);
    setFormOpen(true);
  };

  const onDelete = async (id) => {
    try {
      await deleteEmployee.mutateAsync(id);
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
          <h1 className="text-2xl font-bold text-surface-foreground">{t('employees.title')}</h1>
          <p className="text-sm text-muted-foreground">{t('employees.subtitle')}</p>
        </div>
        <Button size="sm" onClick={openNew}>
          <Plus className="h-4 w-4" /> {t('employees.add')}
        </Button>
      </div>

      {employees.length === 0 ? (
        <EmptyBlock message={t('employees.empty')} action={<Button onClick={openNew}>{t('employees.add')}</Button>} />
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {employees.map((e) => (
            <Card key={e.id}>
              <CardBody className="flex flex-col gap-2">
                <div className="flex items-start justify-between gap-2">
                  <p className="font-semibold text-surface-foreground">{e.name}</p>
                  <Badge className={e.is_active ? 'bg-green-100 text-green-800' : 'bg-slate-200 text-slate-600'}>
                    {e.is_active ? t('common.active') : t('common.inactive')}
                  </Badge>
                </div>
                <div className="text-sm text-muted-foreground">
                  {e.email && <p className="truncate">{e.email}</p>}
                  {e.phone && <p>{e.phone}</p>}
                </div>
                <div className="flex gap-2 pt-2">
                  <Button size="sm" variant="outline" onClick={() => openEdit(e.id)}>
                    <Pencil className="h-3.5 w-3.5" /> {t('common.edit')}
                  </Button>
                  {confirmDeleteId === e.id ? (
                    <Button size="sm" variant="destructive" onClick={() => onDelete(e.id)}>
                      {t('common.confirm')}
                    </Button>
                  ) : (
                    <Button size="sm" variant="ghost" onClick={() => setConfirmDeleteId(e.id)}>
                      <Trash2 className="h-3.5 w-3.5" />
                    </Button>
                  )}
                </div>
              </CardBody>
            </Card>
          ))}
        </div>
      )}

      <EmployeeForm open={formOpen} onOpenChange={setFormOpen} employeeId={editId} />
    </div>
  );
}
