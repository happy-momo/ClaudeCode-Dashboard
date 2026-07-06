import { useState, FormEvent } from 'react';
import { Modal } from '@/components/ui/Modal';
import { Button } from '@/components/ui/Button';
import { FolderOpen } from 'lucide-react';
import { useInstallLocalPlugin } from './hooks';

interface InstallLocalPluginModalProps {
  open: boolean;
  onClose: () => void;
}

export function InstallLocalPluginModal({ open, onClose }: InstallLocalPluginModalProps) {
  const [path, setPath] = useState('');
  const [scope, setScope] = useState<'project' | 'global'>('project');
  const [error, setError] = useState('');
  const installMutation = useInstallLocalPlugin();

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError('');

    const trimmed = path.trim();
    if (!trimmed) {
      setError('Please enter a plugin directory path');
      return;
    }

    try {
      await installMutation.mutateAsync({ path: trimmed, scope });
      setPath('');
      onClose();
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to install plugin';
      setError(message);
    }
  };

  const handleClose = () => {
    if (!installMutation.isPending) {
      setError('');
      setPath('');
      onClose();
    }
  };

  return (
    <Modal open={open} onClose={handleClose} title="Install Local Plugin" className="max-w-xl">
      <form onSubmit={handleSubmit} className="space-y-5">
        <p className="text-sm text-anthro-text-body">
          Install a plugin from a local directory. The directory must contain a{' '}
          <code className="text-xs bg-anthro-bg px-1.5 py-0.5 rounded border border-anthro-border font-mono">
            plugin.json
          </code>{' '}
          or{' '}
          <code className="text-xs bg-anthro-bg px-1.5 py-0.5 rounded border border-anthro-border font-mono">
            .claude-plugin/plugin.json
          </code>{' '}
          manifest file.
        </p>

        {/* Path input */}
        <div>
          <label className="block text-sm font-medium text-anthro-text-heading mb-1.5">
            Plugin Directory Path
          </label>
          <div className="relative">
            <FolderOpen className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-anthro-text-muted" />
            <input
              type="text"
              placeholder="/path/to/plugin-directory"
              value={path}
              onChange={(e) => setPath(e.target.value)}
              className="w-full pl-10 pr-4 py-2.5 border border-anthro-border rounded-lg bg-anthro-surface text-anthro-text-body text-sm placeholder:text-anthro-text-muted focus:outline-none focus:ring-2 focus:ring-anthro-accent/30"
              disabled={installMutation.isPending}
            />
          </div>
        </div>

        {/* Scope toggle */}
        <div>
          <label className="block text-sm font-medium text-anthro-text-heading mb-1.5">
            Install Scope
          </label>
          <div className="flex gap-1 border border-anthro-border rounded-lg p-0.5 w-fit">
            <button
              type="button"
              className={`px-4 py-1.5 rounded-md text-xs font-medium transition-colors ${
                scope === 'project'
                  ? 'bg-anthro-accent text-white'
                  : 'text-anthro-text-muted hover:text-anthro-text-heading'
              }`}
              onClick={() => setScope('project')}
            >
              Project
            </button>
            <button
              type="button"
              className={`px-4 py-1.5 rounded-md text-xs font-medium transition-colors ${
                scope === 'global'
                  ? 'bg-anthro-accent text-white'
                  : 'text-anthro-text-muted hover:text-anthro-text-heading'
              }`}
              onClick={() => setScope('global')}
            >
              Global
            </button>
          </div>
          <p className="text-xs text-anthro-text-muted mt-1.5">
            {scope === 'project'
              ? 'Plugin will be available only in the current project.'
              : 'Plugin will be available across all projects.'}
          </p>
        </div>

        {/* Error message */}
        {error && (
          <div className="text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg px-3 py-2">
            {error}
          </div>
        )}

        {/* Actions */}
        <div className="flex justify-end gap-3 pt-2">
          <Button
            variant="secondary"
            size="md"
            type="button"
            onClick={handleClose}
            disabled={installMutation.isPending}
          >
            Cancel
          </Button>
          <Button
            variant="primary"
            size="md"
            type="submit"
            disabled={installMutation.isPending || !path.trim()}
          >
            {installMutation.isPending ? 'Installing...' : 'Install Plugin'}
          </Button>
        </div>
      </form>
    </Modal>
  );
}
