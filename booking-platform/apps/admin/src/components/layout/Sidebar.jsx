import { NavLink } from 'react-router-dom';
import { LayoutDashboard, Calendar, Scissors, Users, UserRound, Settings, Code2, Megaphone, LogOut, Globe } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useAuth } from '@/lib/AuthContext';
import useT, { useLang } from '@/i18n/LanguageContext';

export default function Sidebar() {
  const t = useT();
  const { lang, setLang } = useLang();
  const { role, signOut, user } = useAuth();

  const items = [
    { to: '/', label: t('nav.dashboard'), icon: LayoutDashboard, end: true },
    { to: '/calendar', label: t('nav.calendar'), icon: Calendar },
    { to: '/services', label: t('nav.services'), icon: Scissors, ownerOnly: true },
    { to: '/employees', label: t('nav.employees'), icon: Users, ownerOnly: true },
    { to: '/customers', label: t('nav.customers'), icon: UserRound },
    { to: '/broadcast', label: t('nav.broadcast'), icon: Megaphone, ownerOnly: true },
    { to: '/settings', label: t('nav.settings'), icon: Settings, ownerOnly: true },
    { to: '/embed', label: t('nav.embed'), icon: Code2, ownerOnly: true },
  ].filter((item) => !item.ownerOnly || role === 'owner');

  return (
    <aside className="hidden md:flex flex-col w-60 shrink-0 h-screen sticky top-0 border-e border-border bg-surface px-4 py-6 gap-6">
      <div className="px-2">
        <p className="text-lg font-bold text-surface-foreground">{t('auth.title')}</p>
        <p className="text-xs text-muted-foreground truncate">{user?.email}</p>
      </div>

      <nav className="flex-1 flex flex-col gap-0.5">
        {items.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.end}
            className={({ isActive }) =>
              cn(
                'flex items-center gap-2.5 rounded px-3 py-2 text-sm transition-colors',
                isActive ? 'bg-muted text-surface-foreground font-semibold' : 'text-muted-foreground hover:bg-muted hover:text-surface-foreground'
              )
            }
          >
            <item.icon className="h-4 w-4 shrink-0" strokeWidth={1.8} />
            {item.label}
          </NavLink>
        ))}
      </nav>

      <div className="flex flex-col gap-2 border-t border-border pt-4">
        <button
          onClick={() => setLang(lang === 'en' ? 'he' : 'en')}
          className="flex items-center gap-2.5 rounded px-3 py-2 text-sm text-muted-foreground hover:bg-muted hover:text-surface-foreground"
        >
          <Globe className="h-4 w-4" strokeWidth={1.8} />
          {lang === 'en' ? 'עברית' : 'English'}
        </button>
        <button
          onClick={signOut}
          className="flex items-center gap-2.5 rounded px-3 py-2 text-sm text-muted-foreground hover:bg-muted hover:text-surface-foreground"
        >
          <LogOut className="h-4 w-4" strokeWidth={1.8} />
          {t('auth.signOut')}
        </button>
      </div>
    </aside>
  );
}
