import { NavLink } from 'react-router-dom';
import { LayoutDashboard, Calendar, Users, UserRound, Settings } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useAuth } from '@/lib/AuthContext';
import useT from '@/i18n/LanguageContext';

export default function MobileNav() {
  const t = useT();
  const { role } = useAuth();

  const items = [
    { to: '/', label: t('nav.dashboard'), icon: LayoutDashboard, end: true },
    { to: '/calendar', label: t('nav.calendar'), icon: Calendar },
    { to: '/customers', label: t('nav.customers'), icon: UserRound },
    role === 'owner'
      ? { to: '/employees', label: t('nav.employees'), icon: Users }
      : { to: '/settings', label: t('nav.settings'), icon: Settings },
  ];

  return (
    <nav className="md:hidden fixed bottom-0 inset-x-0 z-30 flex border-t border-border bg-surface">
      {items.map((item) => (
        <NavLink
          key={item.to}
          to={item.to}
          end={item.end}
          className={({ isActive }) =>
            cn(
              'flex-1 flex flex-col items-center gap-0.5 py-2.5 text-[11px]',
              isActive ? 'text-primary font-semibold' : 'text-muted-foreground'
            )
          }
        >
          <item.icon className="h-5 w-5" strokeWidth={1.8} />
          {item.label}
        </NavLink>
      ))}
    </nav>
  );
}
