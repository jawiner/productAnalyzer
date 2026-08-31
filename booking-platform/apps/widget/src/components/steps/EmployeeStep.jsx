import { CardButton } from '@/components/ui/Card';
import useT from '@/i18n/LanguageContext';

// Only rendered when business_settings.show_employee_selection is true —
// the orchestrator (BookingWidget.jsx) skips straight past this step
// otherwise.
export default function EmployeeStep({ employees, onSelect }) {
  const t = useT();

  return (
    <div className="flex flex-col gap-3">
      <div>
        <h2 className="text-lg font-semibold">{t('employee.title')}</h2>
        <p className="text-sm text-muted-foreground">{t('employee.subtitle')}</p>
      </div>
      <div className="flex flex-col gap-2" role="list">
        <CardButton role="listitem" onClick={() => onSelect(null)}>
          <span className="font-medium">{t('employee.any')}</span>
        </CardButton>
        {employees.map((employee) => (
          <CardButton key={employee.id} role="listitem" onClick={() => onSelect(employee)}>
            <div className="flex items-center gap-3">
              {employee.photo_url ? (
                <img src={employee.photo_url} alt="" className="h-10 w-10 rounded-full object-cover flex-shrink-0" loading="lazy" />
              ) : (
                <div className="h-10 w-10 rounded-full bg-muted flex-shrink-0 flex items-center justify-center text-sm font-medium">
                  {employee.name?.[0]?.toUpperCase()}
                </div>
              )}
              <span className="font-medium">{employee.name}</span>
            </div>
          </CardButton>
        ))}
      </div>
    </div>
  );
}
