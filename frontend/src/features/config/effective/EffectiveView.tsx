import { useState, useMemo } from 'react';
import { Input } from '@/components/ui/Input';
import { Badge, getSourceBadgeVariant } from '@/components/ui/Badge';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { ErrorDisplay } from '@/components/ui/ErrorDisplay';
import { EmptyState } from '@/components/ui/EmptyState';
import { ToastContainer, type Toast } from '@/components/ui/Toast';
import { TerminalSquare, Database, AlertTriangle, Trash2, ChevronLeft, ChevronRight } from 'lucide-react';
import { ConfirmDialog } from '@/components/ui/Modal';
import { useEffectiveCapabilities, useDeleteCapability } from './hooks';
import type { EffectiveCapability } from '@/types/common';

const SOURCE_COLORS: Record<string, string> = {
  global_native: '#2D5B8A',
  project_native: '#2C5F43',
  global_plugin: '#8C5A35',
  project_plugin: '#583E7A',
};

const SOURCE_LABELS: Record<string, string> = {
  global_native: 'Global Native',
  project_native: 'Project Native',
  global_plugin: 'Global Plugin',
  project_plugin: 'Project Plugin',
};

const ITEMS_PER_PAGE = 5;
const TABLE_HEIGHT = '380px'; // Fixed height to match Skills/Mcps/Plugins views
const CONTENT_MIN_HEIGHT = '520px'; // Fixed min height to match MetricsPage and HistoryPage

export function EffectiveView() {
  const [search, setSearch] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [deleteTarget, setDeleteTarget] = useState<EffectiveCapability | null>(null);
  const [toasts, setToasts] = useState<Toast[]>([]);
  const { data: capabilities, isLoading, error } = useEffectiveCapabilities();
  const deleteMutation = useDeleteCapability();

  // Helper to add a toast
  const addToast = (type: 'success' | 'error', message: string) => {
    const id = Math.random().toString(36).substring(2, 9);
    setToasts((prev) => [...prev, { id, type, message }]);
  };

  const dismissToast = (id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  };

  const filtered = useMemo(() => {
    return (capabilities || []).filter((c) =>
      c.name.toLowerCase().includes(search.toLowerCase())
    );
  }, [capabilities, search]);

  // Pagination
  const totalPages = Math.max(1, Math.ceil(filtered.length / ITEMS_PER_PAGE));
  const paginatedItems = useMemo(() => {
    const start = (currentPage - 1) * ITEMS_PER_PAGE;
    return filtered.slice(start, start + ITEMS_PER_PAGE);
  }, [filtered, currentPage]);

  // Reset to page 1 when search changes
  const handleSearchChange = (value: string) => {
    setSearch(value);
    setCurrentPage(1);
  };

  const handleDelete = () => {
    if (!deleteTarget) return;
    deleteMutation.mutate({
      name: deleteTarget.name,
      type: deleteTarget.type,
      scope: deleteTarget.scope,
    }, {
      onSuccess: () => {
        addToast('success', `"${deleteTarget.name}" has been deleted successfully.`);
      },
      onError: (error) => {
        console.error('Failed to delete capability:', error);
        addToast('error', `Failed to delete "${deleteTarget.name}": ${error instanceof Error ? error.message : 'Unknown error'}`);
      },
    });
    setDeleteTarget(null);
  };

  if (isLoading) {
    return (
      <Card padding="lg" className="min-h-[520px]">
        <LoadingSpinner message="Loading capabilities..." />
      </Card>
    );
  }

  if (error) {
    return (
      <Card padding="lg" className="min-h-[520px]">
        <ErrorDisplay
          message="Failed to load capabilities"
          details={error.message}
        />
      </Card>
    );
  }

  return (
    <div className="space-y-3 animate-in fade-in duration-500">
      {/* Toast Container */}
      <ToastContainer toasts={toasts} onDismiss={dismissToast} />

      {/* Header - compact layout to prevent height shift */}
      <div className="mb-1">
        <h2 className="text-3xl font-serif text-anthro-text-heading tracking-tight">
          Unified View
        </h2>
        <p className="text-anthro-text-body text-sm mt-0.5 font-medium">
          Manage Global and Project-level Skills, MCPs, and Plugins with scope priority.
        </p>
      </div>

      {/* Search and Legend - fixed toolbar */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 shrink-0">
        <div className="relative flex-1 max-w-md">
          <Input
            searchIcon
            placeholder="Search capabilities..."
            value={search}
            onChange={(e) => handleSearchChange(e.target.value)}
            className="w-full"
          />
        </div>
        <div className="flex flex-wrap gap-3 shrink-0">
          {Object.entries(SOURCE_LABELS).map(([key, label]) => (
            <span key={key} className="flex items-center text-xs font-medium text-anthro-text-body whitespace-nowrap">
              <div className="w-2 h-2 rounded-full mr-2" style={{ backgroundColor: SOURCE_COLORS[key] }} />
              {label}
            </span>
          ))}
        </div>
      </div>

      {/* Table Container - fixed height with always-visible scrollbar to prevent layout shift */}
      <Card padding={undefined} className="p-0 overflow-hidden">
        {filtered.length === 0 ? (
          <div className="p-12">
            <EmptyState
              title="No capabilities found"
              description={search ? "No capabilities match your search." : "No skills or MCP servers configured yet."}
            />
          </div>
        ) : (
          <div className="overflow-auto scrollbar-always" style={{ height: TABLE_HEIGHT }}>
            <table className="w-full text-left border-collapse">
              <thead
                className="sticky top-0 z-10 shadow-sm"
                style={{ backgroundColor: '#FDFCF6', backdropFilter: 'none' }}
              >
                <tr className="border-b border-anthro-border">
                  <th className="py-4 px-6 text-xs font-medium tracking-wide uppercase text-anthro-text-muted whitespace-nowrap">Name</th>
                  <th className="py-4 px-6 text-xs font-medium tracking-wide uppercase text-anthro-text-muted whitespace-nowrap">Type</th>
                  <th className="py-4 px-6 text-xs font-medium tracking-wide uppercase text-anthro-text-muted whitespace-nowrap">Source</th>
                  <th className="py-4 px-6 text-xs font-medium tracking-wide uppercase text-anthro-text-muted whitespace-nowrap">Overridden</th>
                  <th className="py-4 px-6 text-xs font-medium tracking-wide uppercase text-anthro-text-muted whitespace-nowrap text-right">Actions</th>
                </tr>
              </thead>
              <tbody>
                {paginatedItems.map((item) => (
                  <tr
                    key={`${item.type}-${item.name}-${item.scope}`}
                    className="border-b border-anthro-bg hover:bg-anthro-hover/50 transition-all duration-150 ease-in-out"
                  >
                    <td className="py-4 px-6">
                      <div className="flex items-start gap-2">
                        {item.type === 'skill' ? (
                          <TerminalSquare className="w-4 h-4 text-anthro-text-muted shrink-0 mt-0.5" />
                        ) : (
                          <Database className="w-4 h-4 text-anthro-text-muted shrink-0 mt-0.5" />
                        )}
                        <div className="min-w-0">
                          <span className="font-medium text-anthro-text-heading block truncate">{item.name}</span>
                          {item.plugin_name && (
                            <span className="text-xs text-anthro-text-muted font-medium block mt-0.5">via {item.plugin_name}</span>
                          )}
                        </div>
                      </div>
                    </td>
                    <td className="py-4 px-6 text-sm font-medium text-anthro-text-body uppercase whitespace-nowrap">{item.type}</td>
                    <td className="py-4 px-6 align-middle">
                      <div className="flex items-center gap-2">
                        <div className="w-2 h-2 rounded-full shrink-0" style={{ backgroundColor: SOURCE_COLORS[item.source] || '#999999' }} />
                        <Badge variant={getSourceBadgeVariant(SOURCE_LABELS[item.source] || item.source)}>
                          {SOURCE_LABELS[item.source] || item.source}
                        </Badge>
                      </div>
                    </td>
                    <td className="py-4 px-6 align-middle">
                      {item.overridden_by ? (
                        <div className="inline-flex flex-col">
                          <span className="text-[10px] font-medium text-anthro-text-muted uppercase tracking-wider">Overrides</span>
                          <span className="text-xs font-medium text-[#B55A30] truncate max-w-[120px]" title={item.overridden_by}>
                            {item.overridden_by.replace('_', ' ')}
                          </span>
                        </div>
                      ) : (
                        <span className="text-anthro-text-muted">-</span>
                      )}
                    </td>
                    <td className="py-4 px-6 text-right align-middle shrink-0">
                      {item.plugin_name ? (
                        <span className="text-sm text-anthro-text-muted whitespace-nowrap">-</span>
                      ) : (
                        <button
                          className="p-2 text-anthro-text-muted hover:text-red-500 hover:bg-red-50 rounded-lg transition-all duration-200"
                          title="Delete"
                          onClick={() => setDeleteTarget(item)}
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      {/* Pagination - fixed height container with invisible content to prevent layout shift */}
      <div className="flex justify-between items-center h-10">
        {totalPages > 1 ? (
          <>
            <p className="text-sm text-anthro-text-muted">
              Page {currentPage} of {totalPages} ({filtered.length} total)
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
          </>
        ) : (
          <div className="flex justify-between items-center w-full">
            <div />
            <div />
          </div>
        )}
      </div>

      {/* Delete Confirmation */}
      <ConfirmDialog
        open={!!deleteTarget}
        onClose={() => setDeleteTarget(null)}
        onConfirm={handleDelete}
        title={`Delete ${deleteTarget?.type || 'item'}`}
        message={`Are you sure you want to delete "${deleteTarget?.name}"? This action cannot be undone.`}
        confirmLabel="Delete"
        danger
      />
    </div>
  );
}
