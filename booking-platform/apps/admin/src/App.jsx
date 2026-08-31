import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClientProvider } from '@tanstack/react-query';
import { queryClient } from '@/lib/queryClient';
import { AuthProvider, useAuth } from '@/lib/AuthContext';
import { LanguageProvider } from '@/i18n/LanguageContext';
import { LoadingBlock, ErrorBlock } from '@/components/ui/StateBlock';
import AppLayout from '@/components/layout/AppLayout';
import Login from '@/pages/Login';
import SuperAdminNotice from '@/pages/SuperAdminNotice';
import Dashboard from '@/pages/Dashboard';
import CalendarView from '@/pages/CalendarView';
import Services from '@/pages/Services';
import Employees from '@/pages/Employees';
import Customers from '@/pages/Customers';
import Settings from '@/pages/Settings';
import Embed from '@/pages/Embed';
import Broadcast from '@/pages/Broadcast';

function AuthenticatedApp() {
  const { isLoading, isAuthenticated, role, profileError } = useAuth();

  if (isLoading) return <LoadingBlock />;
  if (!isAuthenticated) return <Login />;

  if (profileError) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-muted px-4">
        <ErrorBlock message={profileError} />
      </div>
    );
  }

  // super_admin has no single business_id — this app is scoped to one
  // business at a time, so send them to the (future) platform-wide app
  // instead of letting every business-scoped query fail silently.
  if (role === 'super_admin') return <SuperAdminNotice />;

  // Staff get a reduced-scope UI: their own appointments via the calendar
  // and dashboard, plus customer lookup (RLS permits business-wide reads
  // on customers/services/employees for staff), but no services/employees/
  // settings/embed management — Sidebar/MobileNav already hide those routes
  // for role !== 'owner', and we redirect any direct navigation here too.
  const ownerOnly = ['/services', '/employees', '/settings', '/embed', '/broadcast'];

  return (
    <Routes>
      <Route element={<AppLayout />}>
        <Route path="/" element={<Dashboard />} />
        <Route path="/calendar" element={<CalendarView />} />
        <Route path="/customers" element={<Customers />} />
        {role === 'owner' ? (
          <>
            <Route path="/services" element={<Services />} />
            <Route path="/employees" element={<Employees />} />
            <Route path="/settings" element={<Settings />} />
            <Route path="/embed" element={<Embed />} />
            <Route path="/broadcast" element={<Broadcast />} />
          </>
        ) : (
          ownerOnly.map((path) => <Route key={path} path={path} element={<Navigate to="/" replace />} />)
        )}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  );
}

export default function App() {
  return (
    <LanguageProvider>
      <AuthProvider>
        <QueryClientProvider client={queryClient}>
          <Router>
            <AuthenticatedApp />
          </Router>
        </QueryClientProvider>
      </AuthProvider>
    </LanguageProvider>
  );
}
