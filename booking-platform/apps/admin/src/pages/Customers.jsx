import { useState } from 'react';
import { Search } from 'lucide-react';
import Input from '@/components/ui/Input';
import { Card, CardBody } from '@/components/ui/Card';
import { LoadingBlock, ErrorBlock, EmptyBlock } from '@/components/ui/StateBlock';
import { useCustomers } from '@/hooks/useCustomers';
import CustomerDetail from '@/components/customers/CustomerDetail';
import useT from '@/i18n/LanguageContext';

export default function Customers() {
  const t = useT();
  const [search, setSearch] = useState('');
  const [selectedId, setSelectedId] = useState(null);
  const { data: customers, isLoading, isError, refetch } = useCustomers(search);

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold text-surface-foreground">{t('customers.title')}</h1>
        <p className="text-sm text-muted-foreground">{t('customers.subtitle')}</p>
      </div>

      <div className="relative max-w-sm">
        <Search className="absolute start-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
        <Input
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder={t('customers.searchPlaceholder')}
          className="ps-9"
        />
      </div>

      {isLoading ? (
        <LoadingBlock />
      ) : isError ? (
        <ErrorBlock onRetry={refetch} />
      ) : customers.length === 0 ? (
        <EmptyBlock message={t('customers.empty')} />
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {customers.map((c) => (
            <Card key={c.id} as="button" onClick={() => setSelectedId(c.id)} className="text-start hover:bg-muted/50 transition-colors">
              <CardBody>
                <p className="font-semibold text-surface-foreground">{c.full_name}</p>
                <p className="text-sm text-muted-foreground">{c.phone}</p>
                {c.email && <p className="text-sm text-muted-foreground truncate">{c.email}</p>}
              </CardBody>
            </Card>
          ))}
        </div>
      )}

      <CustomerDetail customerId={selectedId} open={!!selectedId} onOpenChange={(o) => !o && setSelectedId(null)} />
    </div>
  );
}
