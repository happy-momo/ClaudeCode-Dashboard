import { useState, useMemo } from 'react';
import { Modal } from '@/components/ui/Modal';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { Search, ChevronLeft, ChevronRight } from 'lucide-react';
import { usePluginCatalog, useInstallPlugin } from '../plugins/hooks';
import type { CatalogPluginEntry } from '@/types/plugin';

interface PluginBrowserModalProps {
  open: boolean;
  onClose: () => void;
  filter?: 'all' | 'skills' | 'mcps'; // Filter to show only plugins with skills/mcps
}

const PLUGINS_PER_PAGE = 5;

export function PluginBrowserModal({ open, onClose, filter = 'all' }: PluginBrowserModalProps) {
  const { data: catalog, isLoading } = usePluginCatalog();
  const installMutation = useInstallPlugin();
  const [search, setSearch] = useState('');
  const [installScope, setInstallScope] = useState<'project' | 'global'>('global');
  const [installing, setInstalling] = useState<string | null>(null);
  const [currentPage, setCurrentPage] = useState(1);

  const filtered = useMemo(() => {
    return (catalog || [])
      .filter((p) => {
        if (filter === 'skills' && p.skills_count === 0) return false;
        if (filter === 'mcps' && p.mcps_count === 0) return false;
        return true;
      })
      .filter((p) => {
        if (!search.trim()) return true;
        const q = search.toLowerCase();
        return p.name.toLowerCase().includes(q) || p.description.toLowerCase().includes(q);
      });
  }, [catalog, search, filter]);

  // Pagination
  const totalPages = Math.max(1, Math.ceil(filtered.length / PLUGINS_PER_PAGE));
  const paginatedPlugins = useMemo(() => {
    const start = (currentPage - 1) * PLUGINS_PER_PAGE;
    return filtered.slice(start, start + PLUGINS_PER_PAGE);
  }, [filtered, currentPage]);

  // Reset to page 1 when search changes
  const handleSearchChange = (value: string) => {
    setSearch(value);
    setCurrentPage(1);
  };

  const handleInstall = async (plugin: CatalogPluginEntry) => {
    // Check if plugin is already installed in the selected scope
    const isInstalledInSelectedScope = installScope === 'project'
      ? plugin.installedInProject
      : plugin.installedInGlobal;

    if (isInstalledInSelectedScope) {
      alert(`Plugin "${plugin.name}" is already installed in ${installScope} scope.`);
      return;
    }

    setInstalling(plugin.name);
    try {
      await installMutation.mutateAsync({
        plugin_name: plugin.name,
        marketplace: plugin.marketplace,
        scope: installScope,
      });
      // Close modal after successful install
      onClose();
    } catch (err) {
      // Log error for debugging
      console.error('Failed to install plugin:', err);
      alert(`Failed to install plugin: ${err instanceof Error ? err.message : 'Unknown error'}`);
    } finally {
      setInstalling(null);
    }
  };

  return (
    <Modal open={open} onClose={onClose} title="Browse Plugins" className="max-w-3xl max-h-[80vh]">
      <div className="space-y-4">
        {/* Search + Scope */}
        <div className="flex gap-3">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-anthro-text-muted" />
            <input
              type="text"
              placeholder="Search plugins by name..."
              value={search}
              onChange={(e) => handleSearchChange(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-anthro-border rounded-lg bg-anthro-surface text-anthro-text-body text-sm placeholder:text-anthro-text-muted focus:outline-none focus:ring-2 focus:ring-anthro-accent/30 transition-all duration-200"
            />
          </div>
          <div className="flex gap-1 border border-anthro-border rounded-lg p-0.5">
            <button
              className={`px-3 py-1.5 rounded-md text-xs font-medium transition-all duration-200 ${
                installScope === 'project'
                  ? 'bg-anthro-accent text-white shadow-sm'
                  : 'text-anthro-text-muted hover:text-anthro-text-heading hover:bg-anthro-hover/50'
              }`}
              onClick={() => setInstallScope('project')}
            >
              Project
            </button>
            <button
              className={`px-3 py-1.5 rounded-md text-xs font-medium transition-all duration-200 ${
                installScope === 'global'
                  ? 'bg-anthro-accent text-white shadow-sm'
                  : 'text-anthro-text-muted hover:text-anthro-text-heading hover:bg-anthro-hover/50'
              }`}
              onClick={() => setInstallScope('global')}
            >
              Global
            </button>
          </div>
        </div>

        {/* Plugin list */}
        <div className="overflow-y-auto max-h-[50vh] space-y-2 pr-1">
          {isLoading && (
            <p className="text-sm text-anthro-text-muted text-center py-8 animate-pulse">Loading catalog...</p>
          )}

          {!isLoading && filtered.length === 0 && (
            <p className="text-sm text-anthro-text-muted text-center py-8">
              {search ? 'No plugins match your search' : 'No plugins available'}
            </p>
          )}

          {paginatedPlugins.map((plugin) => {
            // Check if plugin is installed in the selected scope
            const isInstalledInSelectedScope = installScope === 'project'
              ? plugin.installedInProject
              : plugin.installedInGlobal;

            return (
            <div
              key={plugin.name}
              className="flex items-center justify-between p-3 border border-anthro-border rounded-lg hover:bg-anthro-hover/30 hover:border-anthro-accent/30 transition-all duration-200"
            >
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium text-anthro-text-heading truncate">
                    {plugin.name}
                  </span>
                  {isInstalledInSelectedScope && (
                    <span className="text-[10px] px-1.5 py-0.5 bg-green-50 text-green-700 rounded-full border border-green-200 font-medium">
                      Installed
                    </span>
                  )}
                </div>
                <div className="flex items-center gap-3 mt-1">
                  <span className="text-xs text-anthro-text-muted">{plugin.marketplace || 'Unknown'}</span>
                  {plugin.skills_count > 0 && (
                    <span className="text-xs text-anthro-text-muted flex items-center gap-0.5">
                      <span className="w-1.5 h-1.5 rounded-full bg-anthro-accent/40" />
                      {plugin.skills_count} skill{plugin.skills_count !== 1 ? 's' : ''}
                    </span>
                  )}
                  {plugin.mcps_count > 0 && (
                    <span className="text-xs text-anthro-text-muted flex items-center gap-0.5">
                      <span className="w-1.5 h-1.5 rounded-full bg-anthro-accent/40" />
                      {plugin.mcps_count} MCP{plugin.mcps_count !== 1 ? 's' : ''}
                    </span>
                  )}
                </div>
              </div>
              <Button
                variant={isInstalledInSelectedScope ? 'secondary' : 'primary'}
                size="sm"
                onClick={() => handleInstall(plugin)}
                disabled={isInstalledInSelectedScope || installing === plugin.name}
                className="transition-all duration-200"
              >
                {installing === plugin.name ? (
                  <span className="flex items-center gap-1.5">
                    <span className="w-3 h-3 border-2 border-current border-t-transparent rounded-full animate-spin" />
                    Installing...
                  </span>
                ) : isInstalledInSelectedScope ? (
                  'Installed'
                ) : (
                  'Install'
                )}
              </Button>
            </div>
            );
          })}
        </div>

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="flex justify-between items-center pt-2 border-t border-anthro-border">
            <p className="text-xs text-anthro-text-muted">
              Page {currentPage} of {totalPages} ({filtered.length} total)
            </p>
            <div className="flex gap-2">
              <Button
                variant="secondary"
                size="sm"
                onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                disabled={currentPage === 1}
                className="transition-all duration-200"
              >
                <ChevronLeft className="w-3.5 h-3.5" />
                Previous
              </Button>
              <Button
                variant="secondary"
                size="sm"
                onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
                disabled={currentPage === totalPages}
                className="transition-all duration-200"
              >
                Next
                <ChevronRight className="w-3.5 h-3.5" />
              </Button>
            </div>
          </div>
        )}

        {/* Footer */}
        <div className="flex justify-end pt-2">
          <Button variant="secondary" size="md" onClick={onClose} className="transition-all duration-200">
            Close
          </Button>
        </div>
      </div>
    </Modal>
  );
}
