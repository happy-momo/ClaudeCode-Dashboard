import { useState, useMemo, useCallback } from 'react';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { ErrorDisplay } from '@/components/ui/ErrorDisplay';
import { EmptyState } from '@/components/ui/EmptyState';
import { ConfirmDialog } from '@/components/ui/Modal';
import { ToastContainer, Toast } from '@/components/ui/Toast';
import { Download, Trash2, Search, ChevronLeft, ChevronRight } from 'lucide-react';
import { useConversations, useDeleteConversation, useConversationDetail } from './hooks';
import { cn } from '@/lib/utils';

const PAGE_SIZE = 5;
const TABLE_HEIGHT = '420px'; // Fixed height: 5 rows × 84px = 40% taller for better visibility
const CONTENT_MIN_HEIGHT = '520px'; // Fixed min height to match other pages
const MAX_TITLE_LENGTH = 40; // Max characters for title display

// Parse command tags from title
function parseTitle(title: string): string {
  // Match and extract command content from tags
  const commandNameMatch = title.match(/<command-name>([^<]+)<\/command-name>/);
  const commandMessageMatch = title.match(/<command-message>([^<]+)<\/command-message>/);

  // If command tags exist, extract the command name
  if (commandNameMatch) {
    const cmdName = commandNameMatch[1].trim();
    return cmdName.length > MAX_TITLE_LENGTH ? cmdName.slice(0, MAX_TITLE_LENGTH) + '...' : cmdName || 'command';
  }
  if (commandMessageMatch) {
    const cmdMsg = commandMessageMatch[1].trim();
    return cmdMsg.length > MAX_TITLE_LENGTH ? cmdMsg.slice(0, MAX_TITLE_LENGTH) + '...' : cmdMsg || 'command';
  }

  // Remove any remaining XML-like tags
  let parsed = title.replace(/<[^>]+>/g, '');
  parsed = parsed.trim().replace(/\s+/g, ' ');

  // If empty after parsing, return placeholder
  if (!parsed) {
    return 'Untitled';
  }
  return parsed.length > MAX_TITLE_LENGTH ? parsed.slice(0, MAX_TITLE_LENGTH) + '...' : parsed;
}

// Get display title with command indicator
function getDisplayTitle(title: string): { display: string; isCommand: boolean } {
  const isCommand = title.includes('<command-name>') || title.includes('<command-message>');
  const display = parseTitle(title);
  return { display, isCommand };
}

export function ConversationTable() {
  const { data: conversations, isLoading, error } = useConversations();
  const deleteMutation = useDeleteConversation();
  const [searchQuery, setSearchQuery] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [deleteDialog, setDeleteDialog] = useState<{ open: boolean; sessionId: string; title: string }>({
    open: false,
    sessionId: '',
    title: '',
  });
  const [toasts, setToasts] = useState<Toast[]>([]);

  const addToast = useCallback((type: 'success' | 'error', message: string) => {
    const id = Date.now().toString();
    setToasts((prev) => [...prev, { id, type, message }]);
  }, []);

  const dismissToast = useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  // Filter conversations by search query
  const filteredConversations = useMemo(() => {
    if (!conversations) return [];
    if (!searchQuery.trim()) return conversations;

    const query = searchQuery.toLowerCase();
    return conversations.filter(
      (conv) =>
        conv.id.toLowerCase().includes(query) ||
        conv.title.toLowerCase().includes(query) ||
        parseTitle(conv.title).toLowerCase().includes(query) ||
        (conv.project_folder && conv.project_folder.toLowerCase().includes(query))
    );
  }, [conversations, searchQuery]);

  // Pagination
  const totalPages = Math.ceil(filteredConversations.length / PAGE_SIZE);
  const paginatedConversations = useMemo(() => {
    const start = (currentPage - 1) * PAGE_SIZE;
    return filteredConversations.slice(start, start + PAGE_SIZE);
  }, [filteredConversations, currentPage]);

  // Reset to page 1 when search changes
  const handleSearchChange = (value: string) => {
    setSearchQuery(value);
    setCurrentPage(1);
  };

  const handleDelete = async () => {
    try {
      await deleteMutation.mutateAsync(deleteDialog.sessionId);
      addToast('success', 'Conversation deleted successfully');
    } catch {
      addToast('error', 'Failed to delete conversation');
    }
    setDeleteDialog({ open: false, sessionId: '', title: '' });
  };

  const handleDownload = async (sessionId: string, title: string) => {
    try {
      // Fetch conversation detail
      const response = await fetch(`/api/v1/conversations/${encodeURIComponent(sessionId)}`);
      if (!response.ok) throw new Error('Failed to fetch conversation');
      const data = await response.json();

      // Create and download JSON file
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${parseTitle(title).slice(0, 50).replace(/[^a-zA-Z0-9]/g, '_')}_${sessionId.slice(0, 8)}.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);

      addToast('success', 'Conversation downloaded successfully');
    } catch {
      addToast('error', 'Failed to download conversation');
    }
  };

  if (isLoading) {
    return (
      <Card padding="lg">
        <LoadingSpinner message="Loading conversations..." />
      </Card>
    );
  }

  if (error) {
    return (
      <Card padding="lg">
        <ErrorDisplay message="Failed to load conversations" details={error.message} />
      </Card>
    );
  }

  if (!conversations || conversations.length === 0) {
    return (
      <Card padding="lg">
        <EmptyState
          title="No conversations yet"
          description="Conversations will appear here as you interact with Claude."
        />
      </Card>
    );
  }

  return (
    <>
      {/* Toast Notifications */}
      <ToastContainer toasts={toasts} onDismiss={dismissToast} />

      {/* Search Bar */}
      <div className="mb-4 shrink-0">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-anthro-text-muted" />
          <input
            type="text"
            placeholder="Search by session ID, title, or project..."
            value={searchQuery}
            onChange={(e) => handleSearchChange(e.target.value)}
            className="w-full pl-10 pr-4 py-2.5 border border-anthro-border rounded-lg bg-anthro-surface text-anthro-text-body placeholder:text-anthro-text-muted focus:outline-none focus:ring-2 focus:ring-anthro-accent/30 focus:border-anthro-accent transition-colors"
          />
        </div>
        {searchQuery && (
          <p className="text-sm text-anthro-text-muted mt-2">
            Found {filteredConversations.length} conversation{filteredConversations.length !== 1 ? 's' : ''}
          </p>
        )}
      </div>

      {/* Table - fixed height to prevent layout shift */}
      <Card padding={undefined} className="p-0 overflow-hidden" style={{ minHeight: CONTENT_MIN_HEIGHT }}>
        <div className="overflow-auto scrollbar-always" style={{ height: TABLE_HEIGHT }}>
          <table className="w-full text-left border-collapse">
            <thead
              className="sticky top-0 z-10 shadow-sm"
              style={{ backgroundColor: '#FDFCF6', backdropFilter: 'none' }}
            >
              <tr className="border-b border-anthro-border">
                <th className="py-3 px-6 text-xs font-medium tracking-wide uppercase text-anthro-text-muted whitespace-nowrap">
                  Session
                </th>
                <th className="py-3 px-6 text-xs font-medium tracking-wide uppercase text-anthro-text-muted whitespace-nowrap">Date</th>
                <th className="py-3 px-6 text-xs font-medium tracking-wide uppercase text-anthro-text-muted whitespace-nowrap">Turns</th>
                <th className="py-3 px-6 text-xs font-medium tracking-wide uppercase text-anthro-text-muted whitespace-nowrap">Tokens</th>
                <th className="py-3 px-6 text-xs font-medium tracking-wide uppercase text-anthro-text-muted whitespace-nowrap text-right">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody>
              {paginatedConversations.map((conv) => {
                const { display, isCommand } = getDisplayTitle(conv.title);
                return (
                  <tr key={conv.id} className="border-b border-anthro-bg hover:bg-anthro-hover/50 transition-colors" style={{ height: '84px' }}>
                    <td className="py-3 px-6">
                      <div className="flex flex-col gap-1">
                        <div className={cn('font-serif text-base leading-tight line-clamp-2', isCommand ? 'text-anthro-accent' : 'text-anthro-text-heading')} style={{ maxHeight: '3rem' }}>
                          {display}
                          {isCommand && <span className="ml-1 text-[10px] text-anthro-text-muted font-sans">(cmd)</span>}
                        </div>
                        <div className="text-[10px] text-anthro-text-muted font-mono truncate max-w-[200px]">{conv.id}</div>
                        {conv.project_folder && (
                          <div className="text-[10px] text-anthro-accent font-sans truncate max-w-[200px]">{conv.project_folder}</div>
                        )}
                      </div>
                    </td>
                    <td className="py-3 px-6 text-xs font-medium text-anthro-text-body whitespace-nowrap">{conv.date}</td>
                    <td className="py-3 px-6 text-xs font-medium text-anthro-text-body whitespace-nowrap">{conv.turns}</td>
                    <td className="py-3 px-6 text-xs font-medium text-anthro-text-body whitespace-nowrap">
                      {conv.tokens.toLocaleString()}
                    </td>
                    <td className="py-3 px-6 text-right whitespace-nowrap">
                      <div className="flex justify-end gap-1">
                        <button
                          className="p-1.5 text-anthro-text-muted hover:text-anthro-text-heading hover:bg-anthro-hover rounded-lg transition-colors"
                          title="Download"
                          onClick={() => handleDownload(conv.id, conv.title)}
                        >
                          <Download className="w-3.5 h-3.5" />
                        </button>
                        <button
                          className="p-1.5 text-anthro-text-muted hover:text-red-500 hover:bg-red-50 rounded-lg transition-colors"
                          title="Delete"
                          onClick={() => setDeleteDialog({ open: true, sessionId: conv.id, title: display })}
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </Card>

      {/* Pagination - fixed height container */}
      {totalPages > 1 && (
        <div className="flex justify-between items-center h-10 shrink-0">
          <p className="text-sm text-anthro-text-muted">
            Page {currentPage} of {totalPages} ({filteredConversations.length} total)
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

      {/* Empty search result */}
      {filteredConversations.length === 0 && searchQuery && (
        <Card padding="lg" className="mt-4">
          <EmptyState
            title="No matching conversations"
            description={`No conversations found matching "${searchQuery}"`}
          />
        </Card>
      )}

      {/* Delete Confirmation Dialog */}
      <ConfirmDialog
        open={deleteDialog.open}
        onClose={() => setDeleteDialog({ open: false, sessionId: '', title: '' })}
        onConfirm={handleDelete}
        title="Delete Conversation"
        message={`Are you sure you want to delete "${deleteDialog.title}"? This action cannot be undone.`}
        confirmLabel="Delete"
        danger
      />
    </>
  );
}

export function HistoryPage() {
  return (
    <div className="space-y-6 animate-in fade-in duration-700">
      <div>
        <h2 className="text-3xl font-serif text-anthro-text-heading tracking-tight">Conversation History</h2>
        <p className="text-anthro-text-body text-sm mt-1 font-medium">
          Browse and manage your Claude Code sessions
        </p>
      </div>
      <ConversationTable />
    </div>
  );
}
