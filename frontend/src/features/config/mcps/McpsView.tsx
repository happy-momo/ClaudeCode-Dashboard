import { useState, useMemo } from 'react';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Modal } from '@/components/ui/Modal';
import { ConfirmDialog } from '@/components/ui/Modal';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { ErrorDisplay } from '@/components/ui/ErrorDisplay';
import { EmptyState } from '@/components/ui/EmptyState';
import type { McpServerConfig } from '@/types/mcp';
import { McpForm } from './McpForm';
import { Plus, Trash2, ChevronLeft, ChevronRight } from 'lucide-react';
import { useMcpServers, useCreateMcpServer, useDeleteMcpServer, useTestConnectivity } from './hooks';

const MCPS_PER_PAGE = 5;
const MCP_LIST_HEIGHT = '380px'; // Fixed height for 5 MCP cards with pagination - matches PluginsView
const MCP_CARD_MIN_HEIGHT = '80px'; // Fixed min height for consistent layout

function McpCard({
  name,
  config,
  overridden,
  onDelete,
  onTest,
}: {
  name: string;
  config: McpServerConfig;
  overridden?: Record<string, unknown> | null;
  onDelete: () => void;
  onTest: () => void;
}) {
  const isOverridden = overridden != null;
  const cmd = config.args ? `${config.command} ${config.args.join(' ')}` : config.command;

  return (
    <div
      className={`flex justify-between items-start p-4 border rounded-xl ${
        isOverridden
          ? 'border-[#EFDACD] bg-[#F9EFEA]/40'
          : 'border-anthro-border hover:bg-anthro-bg'
      }`}
      style={{ minHeight: MCP_CARD_MIN_HEIGHT }}
    >
      <div className="flex-1 min-w-0">
        <div className="font-medium text-anthro-text-heading text-sm flex items-center gap-2">
          <span className="truncate max-w-[180px] sm:max-w-[240px]">{name}</span>
          {isOverridden && (
            <span className="text-[10px] uppercase bg-[#EFDACD] text-[#B55A30] px-2 py-0.5 rounded font-bold tracking-widest shrink-0">
              Overridden
            </span>
          )}
        </div>
        <div className="text-xs text-anthro-text-muted font-mono mt-2 px-2 py-1 bg-anthro-bg rounded-md border border-anthro-border w-fit max-w-[200px] sm:max-w-[300px] truncate">
          {cmd}
        </div>
      </div>
      <div className="flex items-center gap-2 ml-3 shrink-0">
        <button
          className="p-1.5 text-anthro-text-muted hover:text-anthro-accent hover:bg-anthro-hover rounded-lg text-xs"
          title="Test connectivity"
          onClick={onTest}
        >
          Test
        </button>
        <button
          className="p-1.5 text-anthro-text-muted hover:text-red-500 hover:bg-red-50 rounded-lg"
          title="Delete server"
          onClick={onDelete}
        >
          <Trash2 className="w-3.5 h-3.5" />
        </button>
      </div>
    </div>
  );
}

export function McpsView() {
  const { data: projectMcps, isLoading: projectLoading, error: projectError } = useMcpServers('project');
  const { data: globalMcps, isLoading: globalLoading, error: globalError } = useMcpServers('global');
  const createMutation = useCreateMcpServer();
  const deleteMutation = useDeleteMcpServer();
  const testMutation = useTestConnectivity();

  const [showAddServer, setShowAddServer] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState<{ name: string; scope: string } | null>(null);
  const [projectPage, setProjectPage] = useState(1);
  const [globalPage, setGlobalPage] = useState(1);

  const handleDelete = () => {
    if (!deleteTarget) return;
    deleteMutation.mutate({ name: deleteTarget.name, scope: deleteTarget.scope });
    setDeleteTarget(null);
  };

  // Pagination for project MCPs
  const projectMcpsPaginated = useMemo(() => {
    if (!projectMcps) return [];
    const start = (projectPage - 1) * MCPS_PER_PAGE;
    return projectMcps.slice(start, start + MCPS_PER_PAGE);
  }, [projectMcps, projectPage]);

  const projectTotalPages = Math.max(1, Math.ceil((projectMcps?.length || 0) / MCPS_PER_PAGE));

  // Pagination for global MCPs
  const globalMcpsPaginated = useMemo(() => {
    if (!globalMcps) return [];
    const start = (globalPage - 1) * MCPS_PER_PAGE;
    return globalMcps.slice(start, start + MCPS_PER_PAGE);
  }, [globalMcps, globalPage]);

  const globalTotalPages = Math.max(1, Math.ceil((globalMcps?.length || 0) / MCPS_PER_PAGE));

  if (projectLoading || globalLoading) {
    return (
      <Card padding="lg" className="min-h-[520px]">
        <LoadingSpinner message="Loading MCP servers..." />
      </Card>
    );
  }

  if (projectError || globalError) {
    return (
      <Card padding="lg" className="min-h-[520px]">
        <ErrorDisplay
          message="Failed to load MCP servers"
          details={projectError?.message || globalError?.message}
        />
      </Card>
    );
  }

  return (
    <div className="space-y-4 animate-in fade-in duration-700">
      <div className="flex justify-between items-center shrink-0">
        <p className="text-sm font-medium text-anthro-text-body">
          Manage Model Context Protocol servers for external tool access.
        </p>
        <Button variant="primary" size="md" onClick={() => setShowAddServer(true)}>
          <Plus className="w-4 h-4 mr-2" /> Add Server
        </Button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Project MCP Servers Column */}
        <Card>
          <h3 className="text-lg font-serif text-anthro-text-heading mb-1 flex items-center">
            <div className="w-2.5 h-2.5 rounded-full bg-[#2C5F43] mr-3" />
            Project-Level Servers
          </h3>
          <p className="text-xs text-anthro-text-muted mb-3 font-mono bg-anthro-bg px-2 py-1 rounded inline-block">
            ./.claude/settings.json
          </p>
          <div className="space-y-3" style={{ height: MCP_LIST_HEIGHT, overflowY: 'auto' }}>
            {!projectMcps || projectMcps.length === 0 ? (
              <EmptyState
                title="No project MCP servers"
                description="Add MCP servers to provide external tools for this project."
              />
            ) : (
              projectMcpsPaginated.map((mcp) => (
                <McpCard
                  key={mcp.name}
                  name={mcp.name}
                  config={mcp.config}
                  overridden={mcp.overridden ?? null}
                  onDelete={() => { setDeleteTarget({ name: mcp.name, scope: mcp.scope }); }}
                  onTest={() => testMutation.mutate({ name: mcp.name, scope: mcp.scope })}
                />
              ))
            )}
          </div>
          {/* Pagination for Project MCPs */}
          {projectTotalPages > 1 && (
            <div className="flex justify-between items-center mt-3 pt-3 border-t border-anthro-border">
              <p className="text-xs text-anthro-text-muted">
                Page {projectPage} of {projectTotalPages}
              </p>
              <div className="flex gap-2">
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={() => setProjectPage((p) => Math.max(1, p - 1))}
                  disabled={projectPage === 1}
                >
                  <ChevronLeft className="w-3 h-3 mr-0.5" />
                  Prev
                </Button>
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={() => setProjectPage((p) => Math.min(projectTotalPages, p + 1))}
                  disabled={projectPage === projectTotalPages}
                >
                  Next
                  <ChevronRight className="w-3 h-3 ml-0.5" />
                </Button>
              </div>
            </div>
          )}
        </Card>

        {/* Global MCP Servers Column */}
        <Card>
          <h3 className="text-lg font-serif text-anthro-text-heading mb-1 flex items-center">
            <div className="w-2.5 h-2.5 rounded-full bg-[#2D5B8A] mr-3" />
            Global Servers
          </h3>
          <p className="text-xs text-anthro-text-muted mb-3 font-mono bg-anthro-bg px-2 py-1 rounded inline-block">
            ~/.claude/settings.json
          </p>
          <div className="space-y-3" style={{ height: MCP_LIST_HEIGHT, overflowY: 'auto' }}>
            {!globalMcps || globalMcps.length === 0 ? (
              <EmptyState
                title="No global MCP servers"
                description="Add global MCP servers to provide tools across all projects."
              />
            ) : (
              globalMcpsPaginated.map((mcp) => (
                <McpCard
                  key={mcp.name}
                  name={mcp.name}
                  config={mcp.config}
                  overridden={mcp.overridden ?? null}
                  onDelete={() => { setDeleteTarget({ name: mcp.name, scope: mcp.scope }); }}
                  onTest={() => testMutation.mutate({ name: mcp.name, scope: mcp.scope })}
                />
              ))
            )}
          </div>
          {/* Pagination for Global MCPs */}
          {globalTotalPages > 1 && (
            <div className="flex justify-between items-center mt-3 pt-3 border-t border-anthro-border">
              <p className="text-xs text-anthro-text-muted">
                Page {globalPage} of {globalTotalPages}
              </p>
              <div className="flex gap-2">
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={() => setGlobalPage((p) => Math.max(1, p - 1))}
                  disabled={globalPage === 1}
                >
                  <ChevronLeft className="w-3 h-3 mr-0.5" />
                  Prev
                </Button>
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={() => setGlobalPage((p) => Math.min(globalTotalPages, p + 1))}
                  disabled={globalPage === globalTotalPages}
                >
                  Next
                  <ChevronRight className="w-3 h-3 ml-0.5" />
                </Button>
              </div>
            </div>
          )}
        </Card>
      </div>

      {/* Add Server Modal */}
      <Modal open={showAddServer} onClose={() => setShowAddServer(false)} title="Add MCP Server">
        <McpForm
          onSubmit={(data) => {
            createMutation.mutate(data);
            setShowAddServer(false);
          }}
          onCancel={() => setShowAddServer(false)}
        />
      </Modal>

      {/* Delete Confirmation */}
      <ConfirmDialog
        open={!!deleteTarget}
        onClose={() => setDeleteTarget(null)}
        onConfirm={handleDelete}
        title="Delete MCP Server"
        message={`Are you sure you want to delete "${deleteTarget?.name}"? This action cannot be undone.`}
        confirmLabel="Delete"
        danger
      />
    </div>
  );
}
