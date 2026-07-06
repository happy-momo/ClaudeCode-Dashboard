import { AppShell } from '@/components/layout/AppShell';
import { AppProviders } from '@/providers/AppProviders';
import { SessionProvider } from '@/lib/SessionContext';

export default function App() {
  return (
    <AppProviders>
      <SessionProvider>
        <AppShell />
      </SessionProvider>
    </AppProviders>
  );
}
