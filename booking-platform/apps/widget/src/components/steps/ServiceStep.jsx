import { CardButton } from '@/components/ui/Card';
import { EmptyBlock } from '@/components/ui/StateBlock';
import useT from '@/i18n/LanguageContext';

export default function ServiceStep({ services, showPrices, onSelect }) {
  const t = useT();

  if (services.length === 0) {
    return <EmptyBlock message={t('service.noServices')} />;
  }

  return (
    <div className="flex flex-col gap-3">
      <div>
        <h2 className="text-lg font-semibold">{t('service.title')}</h2>
        <p className="text-sm text-muted-foreground">{t('service.subtitle')}</p>
      </div>
      <div className="flex flex-col gap-2" role="list">
        {services.map((service) => (
          <CardButton key={service.id} role="listitem" onClick={() => onSelect(service)}>
            <div className="flex items-center gap-3">
              {service.image_url && (
                <img
                  src={service.image_url}
                  alt=""
                  className="h-14 w-14 flex-shrink-0 rounded object-cover"
                  loading="lazy"
                />
              )}
              <div className="flex-1 min-w-0">
                <div className="flex items-baseline justify-between gap-2">
                  <span className="font-medium truncate">{service.name}</span>
                  {showPrices && service.price != null && (
                    <span className="text-sm font-medium text-primary flex-shrink-0">
                      {new Intl.NumberFormat(undefined, { style: 'currency', currency: 'ILS' }).format(service.price)}
                    </span>
                  )}
                </div>
                {service.description && (
                  <p className="text-sm text-muted-foreground line-clamp-2">{service.description}</p>
                )}
                <span className="text-xs text-muted-foreground">
                  {t('service.duration', { minutes: service.duration_minutes })}
                </span>
              </div>
            </div>
          </CardButton>
        ))}
      </div>
    </div>
  );
}
