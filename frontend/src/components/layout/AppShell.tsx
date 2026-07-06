import { useState } from 'react';
import { Activity, History, Settings, ExternalLink, Terminal } from 'lucide-react';
import { Sidebar } from './Sidebar';
import { MetricsPage } from '@/features/metrics/MetricsPage';
import { HistoryPage } from '@/features/history/HistoryPage';
import { ConfigPage } from '@/features/config/ConfigPage';
import { useSession, type SessionInfo } from '@/lib/SessionContext';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';

const navItems = [
  { id: 'metrics', label: 'Metrics', icon: Activity },
  { id: 'history', label: 'Conversations', icon: History },
  { id: 'config', label: 'Management', icon: Settings },
];

export function AppShell() {
  const { sessionId, projectDir, loading, error, activeSessions } = useSession();
  const [activeTab, setActiveTab] = useState('metrics');

  // Loading state
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-anthro-bg">
        <LoadingSpinner message="Loading..." />
      </div>
    );
  }

  // No session_id - show welcome page
  if (!sessionId) {
    return (
      <div className="min-h-screen bg-anthro-bg text-anthro-text-body">
        <div className="max-w-3xl mx-auto p-8 pt-24">
          <div className="text-center mb-12">
            <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-anthro-accent/10 mb-6">
              <Terminal className="w-8 h-8 text-anthro-accent" />
            </div>
            <h1 className="text-4xl font-serif text-anthro-text-heading mb-4">
              Claude Dashboard
            </h1>
            <p className="text-lg text-anthro-text-muted">
              Manage your Claude Code sessions, skills, MCPs, and plugins
            </p>
          </div>

          <Card padding="lg" className="mb-8">
            <h2 className="text-xl font-serif text-anthro-text-heading mb-4">
              Getting Started
            </h2>
            <ol className="space-y-4 text-anthro-text-body">
              <li className="flex items-start gap-3">
                <span className="flex-shrink-0 w-6 h-6 rounded-full bg-anthro-accent/10 text-anthro-accent text-sm font-medium flex items-center justify-center">
                  1
                </span>
                <div>
                  <p className="font-medium mb-1">Start Claude Code in your project</p>
                  <code className="text-xs bg-anthro-bg px-2 py-1 rounded block mt-1">
                    claude
                  </code>
                </div>
              </li>
              <li className="flex items-start gap-3">
                <span className="flex-shrink-0 w-6 h-6 rounded-full bg-anthro-accent/10 text-anthro-accent text-sm font-medium flex items-center justify-center">
                  2
                </span>
                <div>
                  <p className="font-medium mb-1">Click the dashboard link shown in Claude Code</p>
                  <p className="text-sm text-anthro-text-muted mt-1">
                    The link will look like: <code className="text-xs">http://127.0.0.1:18080/?session_id=xxx</code>
                  </p>
                </div>
              </li>
            </ol>
          </Card>

          {activeSessions.length > 0 && (
            <Card padding="lg">
              <h2 className="text-xl font-serif text-anthro-text-heading mb-4">
                Active Sessions
              </h2>
              <div className="space-y-2">
                {activeSessions.map((session: SessionInfo) => (
                  <a
                    key={session.session_id}
                    href={`/?session_id=${session.session_id}`}
                    className="block p-4 rounded-lg border border-anthro-border hover:bg-anthro-hover transition-colors"
                  >
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="font-medium text-anthro-text-heading">
                          {session.project_dir.split('/').pop() || session.project_dir}
                        </p>
                        <p className="text-sm text-anthro-text-muted">
                          Session: {session.session_id.slice(0, 8)}...
                        </p>
                      </div>
                      <ExternalLink className="w-4 h-4 text-anthro-text-muted" />
                    </div>
                  </a>
                ))}
              </div>
            </Card>
          )}
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-anthro-bg p-8">
        <Card padding="lg" className="max-w-md">
          <h2 className="text-xl font-serif text-anthro-text-heading mb-4">
            Session Error
          </h2>
          <p className="text-anthro-text-muted mb-6">{error}</p>
          <div className="flex gap-2">
            <Button variant="primary" onClick={() => window.location.href = '/'}>
              Go to Home
            </Button>
            <Button variant="secondary" onClick={() => window.location.reload()}>
              Refresh
            </Button>
          </div>
        </Card>
      </div>
    );
  }

  return (
    <div className="h-screen bg-anthro-bg text-anthro-text-body font-sans flex flex-col selection:bg-anthro-accent selection:text-white overflow-hidden">
      {/* Session info bar */}
      <div className="bg-anthro-surface border-b border-anthro-border px-4 py-2 z-50 flex-shrink-0">
        <div className="max-w-6xl mx-auto flex justify-between items-center text-xs">
          <span className="text-anthro-text-muted">
            Session: <span className="font-mono text-anthro-accent">{sessionId?.slice(0, 8)}...</span>
            {projectDir && (
              <span className="ml-2 text-anthro-text-muted">
                | Project: <span className="text-anthro-text-heading">{projectDir.split('/').pop() || projectDir}</span>
              </span>
            )}
          </span>
          <a
            href="/"
            className="text-anthro-text-muted hover:text-anthro-accent transition-colors"
            title="Return to session selection"
          >
            New Session
          </a>
        </div>
      </div>

      {/* Main content area */}
      <div className="flex flex-1 overflow-hidden">
        <Sidebar items={navItems} activeId={activeTab} onChange={setActiveTab} />

        <main className="flex-1 overflow-auto">
          <div className="max-w-6xl mx-auto p-4 sm:p-6 md:p-8 lg:p-12 xl:p-16">
            {activeTab === 'metrics' && <MetricsPage />}
            {activeTab === 'history' && <HistoryPage />}
            {activeTab === 'config' && <ConfigPage />}
          </div>
        </main>
      </div>
    </div>
  );
}
