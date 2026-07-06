import { useState, useRef, useEffect, useMemo, KeyboardEvent } from 'react';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Toggle } from '@/components/ui/Toggle';
import { ConfirmDialog } from '@/components/ui/Modal';
import { ToastContainer, type Toast } from '@/components/ui/Toast';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { ErrorDisplay } from '@/components/ui/ErrorDisplay';
import { EmptyState } from '@/components/ui/EmptyState';
import { Input } from '@/components/ui/Input';
import { PluginBrowserModal } from './PluginBrowserModal';
import { InstallLocalPluginModal } from './InstallLocalPluginModal';
import { Layers, TerminalSquare, Database, Package, Trash2, Pencil, Check, X, FolderOpen, Search, ChevronLeft, ChevronRight } from 'lucide-react';
import type { PluginResponse } from '@/types/plugin';
import { usePlugins, useTogglePlugin, useUninstallPlugin, useUpdatePluginVersion } from './hooks';

const PLUGINS_PER_PAGE = 5;
const PLUGIN_LIST_MAX_HEIGHT = '380px'; // Reduced height to match HistoryPage exactly
const PLUGIN_CARD_HEIGHT = '68px'; // Fixed height per plugin card for consistent layout

function PluginCard({
  plugin,
  onToggle,
  onUninstall,
  onUpdateVersion,
}: {
  plugin: PluginResponse;
  onToggle: (checked: boolean) => void;
  onUninstall: () => void;
  onUpdateVersion: (version: string) => void;
}) {
  const isGlobal = plugin.level === 'global';
  const [editingVersion, setEditingVersion] = useState(false);
  const [versionDraft, setVersionDraft] = useState(plugin.version);
  const [versionError, setVersionError] = useState('');
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (editingVersion && inputRef.current) {
      inputRef.current.focus();
      inputRef.current.select();
    }
  }, [editingVersion]);

  // Sync draft when plugin version changes from external update
  useEffect(() => {
    setVersionDraft(plugin.version);
  }, [plugin.version]);

  const handleVersionSave = () => {
    const trimmed = versionDraft.trim();
    if (!trimmed) {
      setVersionError('Version cannot be empty');
      return;
    }
    if (trimmed === plugin.version) {
      setEditingVersion(false);
      setVersionError('');
      return;
    }
    setVersionError('');
    onUpdateVersion(trimmed);
    setEditingVersion(false);
  };

  const handleVersionKeyDown = (e: KeyboardEvent) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleVersionSave();
    } else if (e.key === 'Escape') {
      setVersionDraft(plugin.version);
      setEditingVersion(false);
      setVersionError('');
    }
  };

  return (
    <Card padding="lg" className="transition-all duration-300 hover:shadow-md" style={{ minHeight: PLUGIN_CARD_HEIGHT }}>
      <div className="flex justify-between items-start" style={{ marginBottom: '0.75rem' }}>
        <div className="flex items-center gap-4 min-w-0">
          <div className="p-3 bg-anthro-bg text-anthro-text-heading rounded-xl border border-anthro-border transition-transform duration-200 hover:scale-105 shrink-0">
            <Layers className="w-5 h-5" />
          </div>
          <div className="min-w-0 flex-1">
            <div className="font-serif text-lg text-anthro-text-heading flex items-center gap-2">
              <span className="truncate max-w-[200px] sm:max-w-[300px]">{plugin.name}</span>
              {editingVersion ? (
                <span className="inline-flex items-center gap-1">
                  <input
                    ref={inputRef}
                    type="text"
                    value={versionDraft}
                    onChange={(e) => setVersionDraft(e.target.value)}
                    onKeyDown={handleVersionKeyDown}
                    className="w-20 px-2 py-0.5 text-xs font-sans font-medium border border-anthro-accent/50 rounded-md bg-anthro-surface text-anthro-text-heading focus:outline-none focus:ring-2 focus:ring-anthro-accent/30"
                  />
                  <button
                    onClick={handleVersionSave}
                    className="p-0.5 text-green-600 hover:bg-green-50 rounded transition-colors"
                    title="Save version"
                  >
                    <Check className="w-3 h-3" />
                  </button>
                  <button
                    onClick={() => { setVersionDraft(plugin.version); setEditingVersion(false); setVersionError(''); }}
                    className="p-0.5 text-anthro-text-muted hover:bg-anthro-hover rounded transition-colors"
                    title="Cancel"
                  >
                    <X className="w-3 h-3" />
                  </button>
                </span>
              ) : (
                <span
                  className="text-xs text-anthro-text-muted font-sans font-medium inline-flex items-center gap-1 cursor-pointer group"
                  onClick={() => setEditingVersion(true)}
                  title="Click to edit version"
                >
                  v{plugin.version}
                  <Pencil className="w-2.5 h-2.5 opacity-0 group-hover:opacity-60 transition-opacity" />
                </span>
              )}
              <span
                className={`px-2 py-0.5 text-[9px] rounded uppercase font-bold tracking-widest border font-sans ${
                  isGlobal
                    ? 'bg-[#EAEFF5] text-[#2D5B8A] border-[#D0DFEF]'
                    : 'bg-[#EBF1ED] text-[#2C5F43] border-[#D1E0D7]'
                }`}
              >
                {isGlobal ? 'Global' : 'Project'}
              </span>
            </div>
            {versionError && (
              <div className="text-xs text-red-500 mt-0.5">{versionError}</div>
            )}
            <div className="text-sm text-anthro-text-body mt-0.5 line-clamp-1 truncate max-w-[400px] sm:max-w-[600px]">{plugin.description}</div>
          </div>
        </div>
        <div className="flex gap-1.5 items-center shrink-0">
          <Toggle checked={plugin.active} onChange={onToggle} />
          <button
            className="p-1.5 text-anthro-text-muted hover:text-red-500 hover:bg-red-50 rounded-lg transition-colors"
            title="Uninstall"
            onClick={onUninstall}
          >
            <Trash2 className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      <div className="bg-anthro-bg rounded-xl p-3 text-xs flex flex-col md:flex-row gap-3 md:gap-6 border border-anthro-border">
        <div className="flex items-center">
          <span className="text-anthro-text-muted font-medium flex items-center">
            <TerminalSquare className="w-3.5 h-3.5 mr-1.5" /> Skills:
          </span>
          <span className="ml-1.5 font-medium text-anthro-text-heading truncate max-w-[200px]">
            {plugin.skills.length > 0 ? plugin.skills.join(', ') : (
              <span className="text-anthro-text-muted italic">No skills</span>
            )}
          </span>
        </div>
        <div className="flex items-center">
          <span className="text-anthro-text-muted font-medium flex items-center">
            <Database className="w-3.5 h-3.5 mr-1.5" /> MCPs:
          </span>
          <span className="ml-1.5 font-medium text-anthro-text-heading truncate max-w-[200px]">
            {plugin.mcps.length > 0 ? plugin.mcps.join(', ') : (
              <span className="text-anthro-text-muted italic">No MCPs</span>
            )}
          </span>
        </div>
      </div>
    </Card>
  );
}

export function PluginsView() {
  const { data: plugins, isLoading, error } = usePlugins();
  const toggleMutation = useTogglePlugin();
  const uninstallMutation = useUninstallPlugin();
  const updateVersionMutation = useUpdatePluginVersion();

  const [searchQuery, setSearchQuery] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [showBrowser, setShowBrowser] = useState(false);
  const [showLocalInstall, setShowLocalInstall] = useState(false);
  const [uninstallTarget, setUninstallTarget] = useState<{ id: string; name: string } | null>(null);
  const [toasts, setToasts] = useState<Toast[]>([]);

  // Helper to add a toast
  const addToast = (type: 'success' | 'error', message: string) => {
    const id = Math.random().toString(36).substring(2, 9);
    setToasts((prev) => [...prev, { id, type, message }]);
  };

  const dismissToast = (id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  };

  // Filter plugins by search query (search by name)
  const filteredPlugins = useMemo(() => {
    if (!plugins) return [];
    if (!searchQuery.trim()) return plugins;

    const query = searchQuery.toLowerCase();
    return plugins.filter((plugin) =>
      plugin.name.toLowerCase().includes(query) ||
      plugin.description.toLowerCase().includes(query)
    );
  }, [plugins, searchQuery]);

  // Pagination
  const totalPages = Math.max(1, Math.ceil(filteredPlugins.length / PLUGINS_PER_PAGE));
  const paginatedPlugins = useMemo(() => {
    const start = (currentPage - 1) * PLUGINS_PER_PAGE;
    return filteredPlugins.slice(start, start + PLUGINS_PER_PAGE);
  }, [filteredPlugins, currentPage]);

  // Reset to page 1 when search changes
  const handleSearchChange = (value: string) => {
    setSearchQuery(value);
    setCurrentPage(1);
  };

  const handleUninstall = () => {
    if (!uninstallTarget) return;
    uninstallMutation.mutate(uninstallTarget.id, {
      onSuccess: () => {
        addToast('success', `Plugin "${uninstallTarget.name}" has been uninstalled successfully.`);
      },
      onError: (error) => {
        console.error('Failed to uninstall plugin:', error);
        addToast('error', `Failed to uninstall plugin: ${error instanceof Error ? error.message : 'Unknown error'}`);
      },
    });
    setUninstallTarget(null);
  };

  const handleUpdateVersion = (pluginId: string, version: string) => {
    updateVersionMutation.mutate({ id: pluginId, data: { version } });
  };

  const handleTogglePlugin = (pluginId: string, active: boolean) => {
    toggleMutation.mutate({ id: pluginId, active }, {
      onSuccess: () => {
        addToast('success', `Plugin ${active ? 'enabled' : 'disabled'} successfully.`);
      },
      onError: (error) => {
        console.error('Failed to toggle plugin:', error);
        addToast('error', `Failed to toggle plugin: ${error instanceof Error ? error.message : 'Unknown error'}`);
      },
    });
  };

  if (isLoading) {
    return (
      <Card padding="lg" className="min-h-[520px]">
        <LoadingSpinner message="Loading plugins..." />
      </Card>
    );
  }

  if (error) {
    return (
      <Card padding="lg" className="min-h-[520px]">
        <ErrorDisplay
          message="Failed to load plugins"
          details={error.message}
        />
      </Card>
    );
  }

  return (
    <div className="space-y-4 animate-in fade-in duration-500">
      {/* Toast Container */}
      <ToastContainer toasts={toasts} onDismiss={dismissToast} />

      {/* Header - matches HistoryPage structure */}
      <div className="shrink-0">
        <h2 className="text-3xl font-serif text-anthro-text-heading tracking-tight">
          Plugins
        </h2>
        <p className="text-anthro-text-body text-sm mt-1 font-medium">
          Install and manage plugin bundles (Skills + MCPs).
        </p>
      </div>

      {/* Search and Actions - fixed toolbar */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 shrink-0">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-anthro-text-muted" />
          <input
            type="text"
            placeholder="Search plugins by name..."
            value={searchQuery}
            onChange={(e) => handleSearchChange(e.target.value)}
            className="w-full pl-10 pr-4 py-2.5 border border-anthro-border rounded-lg bg-anthro-surface text-anthro-text-body text-sm placeholder:text-anthro-text-muted focus:outline-none focus:ring-2 focus:ring-anthro-accent/30 focus:border-anthro-accent transition-colors"
          />
        </div>
        <div className="flex gap-2 shrink-0">
          <Button variant="secondary" size="md" onClick={() => setShowLocalInstall(true)} className="transition-all duration-200">
            <FolderOpen className="w-4 h-4 mr-2" /> Install from Path
          </Button>
          <Button variant="primary" size="md" onClick={() => setShowBrowser(true)} className="transition-all duration-200">
            <Package className="w-4 h-4 mr-2" /> Browse & Install
          </Button>
        </div>
      </div>

      {/* Plugin List - scrollable container with fixed max height */}
      <div className="space-y-4" style={{ maxHeight: PLUGIN_LIST_MAX_HEIGHT, overflowY: 'auto' }}>
        {!paginatedPlugins || paginatedPlugins.length === 0 ? (
          <Card padding="lg">
            <EmptyState
              title={searchQuery ? "No matching plugins" : "No plugins installed"}
              description={searchQuery ? `No plugins found matching "${searchQuery}"` : "Browse the plugin directory or install from a local path to add plugins."}
            />
          </Card>
        ) : (
          paginatedPlugins.map((plugin, idx) => (
            <div
              key={plugin.id}
              className="animate-in fade-in slide-in-from-bottom-2"
              style={{ animationDelay: `${idx * 50}ms`, animationFillMode: 'both' }}
            >
              <PluginCard
                key={plugin.id}
                plugin={plugin}
                onToggle={(checked) => handleTogglePlugin(plugin.id, checked)}
                onUninstall={() => { setUninstallTarget({ id: plugin.id, name: plugin.name }); }}
                onUpdateVersion={(version) => handleUpdateVersion(plugin.id, version)}
              />
            </div>
          ))
        )}
      </div>

      {/* Pagination - fixed position, matches HistoryPage */}
      {totalPages > 1 && (
        <div className="flex justify-between items-center shrink-0">
          <p className="text-sm text-anthro-text-muted">
            Page {currentPage} of {totalPages} ({filteredPlugins.length} total)
          </p>
          <div className="flex gap-2">
            <Button
              variant="secondary"
              size="sm"
              onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
              disabled={currentPage === 1}
            >
              <ChevronLeft className="w-4 h-4 mr-1" />
              Previous
            </Button>
            <Button
              variant="secondary"
              size="sm"
              onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
              disabled={currentPage === totalPages}
            >
              Next
              <ChevronRight className="w-4 h-4 ml-1" />
            </Button>
          </div>
        </div>
      )}

      {/* Plugin Browser Modal */}
      <PluginBrowserModal
        open={showBrowser}
        onClose={() => setShowBrowser(false)}
      />

      {/* Install Local Plugin Modal */}
      <InstallLocalPluginModal
        open={showLocalInstall}
        onClose={() => setShowLocalInstall(false)}
      />

      {/* Uninstall Confirmation */}
      <ConfirmDialog
        open={!!uninstallTarget}
        onClose={() => setUninstallTarget(null)}
        onConfirm={handleUninstall}
        title="Uninstall Plugin"
        message={`Are you sure you want to uninstall "${uninstallTarget?.name}"? This will remove all its skills and MCPs.`}
        confirmLabel="Uninstall"
        danger
      />
    </div>
  );
}
