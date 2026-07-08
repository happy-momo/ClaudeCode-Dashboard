import { useState, useCallback, useEffect } from 'react';
import { Button } from '@/components/ui/Button';
import type { CreateMcpRequest } from '@/types/mcp';

interface McpFormProps {
  onSubmit: (data: CreateMcpRequest) => void;
  onCancel: () => void;
  initialData?: Partial<CreateMcpRequest>;
  isEdit?: boolean;
}

export function McpForm({ onSubmit, onCancel, initialData, isEdit = false }: McpFormProps) {
  const [name, setName] = useState(initialData?.name || '');
  const [transport, setTransport] = useState<'stdio' | 'http' | 'sse'>(initialData?.transport as 'stdio' | 'http' | 'sse' || 'stdio');
  const [command, setCommand] = useState(initialData?.command || '');
  const [argsText, setArgsText] = useState(
    initialData?.args?.join(' ') || ''
  );
  const [envText, setEnvText] = useState(
    initialData?.env
      ? Object.entries(initialData.env)
          .map(([k, v]) => `${k}=${v}`)
          .join('\n')
      : ''
  );
  const [url, setUrl] = useState(initialData?.url || '');
  const [scope, setScope] = useState<'project' | 'global'>(initialData?.scope || 'project');

  // Reset form when initialData changes (for edit mode)
  useEffect(() => {
    if (initialData) {
      setName(initialData.name || '');
      setTransport(initialData.transport as 'stdio' | 'http' | 'sse' || 'stdio');
      setCommand(initialData.command || '');
      setArgsText(initialData?.args?.join(' ') || '');
      setEnvText(
        initialData?.env
          ? Object.entries(initialData.env)
              .map(([k, v]) => `${k}=${v}`)
              .join('\n')
          : ''
      );
      setUrl(initialData.url || '');
      setScope(initialData.scope as 'project' | 'global' || 'project');
    }
  }, [initialData]);

  const handleSubmit = useCallback((e: React.FormEvent) => {
    e.preventDefault();
    const args = argsText
      .trim()
      .split(/\s+/)
      .filter(Boolean);
    const env: Record<string, string> = {};
    if (envText.trim()) {
      for (const line of envText.trim().split('\n')) {
        const eqIdx = line.indexOf('=');
        if (eqIdx > 0) {
          env[line.slice(0, eqIdx).trim()] = line.slice(eqIdx + 1).trim();
        }
      }
    }

    // Build request based on transport type
    const data: CreateMcpRequest = {
      name,
      scope,
      transport,
    };

    if (transport === 'http' || transport === 'sse') {
      data.url = url;
    } else {
      data.command = command;
      data.args = args.length > 0 ? args : undefined;
      data.env = Object.keys(env).length > 0 ? env : undefined;
    }

    onSubmit(data);
  }, [name, command, argsText, envText, scope, transport, url, onSubmit]);

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label className="block text-sm font-medium text-anthro-text-heading mb-1.5">
          Server Name
        </label>
        <input
          type="text"
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="my-mcp-server"
          className="w-full px-4 py-2 bg-anthro-bg border border-anthro-border rounded-xl text-sm focus:outline-none focus:ring-1 focus:ring-anthro-accent text-anthro-text-heading placeholder:text-anthro-text-muted disabled:opacity-50 disabled:cursor-not-allowed"
          required
          disabled={isEdit}
        />
      </div>

      {/* Transport Type */}
      <div>
        <label className="block text-sm font-medium text-anthro-text-heading mb-2">
          Transport Type
        </label>
        <div className="flex flex-col gap-2">
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="radio"
              name="transport"
              value="stdio"
              checked={transport === 'stdio'}
              onChange={() => setTransport('stdio')}
              className="accent-anthro-accent w-4 h-4"
            />
            <span className="text-sm text-anthro-text-body font-medium">STDIO (Command-based)</span>
          </label>
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="radio"
              name="transport"
              value="http"
              checked={transport === 'http'}
              onChange={() => setTransport('http')}
              className="accent-anthro-accent w-4 h-4"
            />
            <span className="text-sm text-anthro-text-body font-medium">HTTP (URL-based)</span>
          </label>
        </div>
      </div>

      {/* STDIO fields */}
      {transport === 'stdio' && (
        <>
          <div>
            <label className="block text-sm font-medium text-anthro-text-heading mb-1.5">
              Command
            </label>
            <input
              type="text"
              value={command}
              onChange={(e) => setCommand(e.target.value)}
              placeholder="npx @my-org/my-mcp-server"
              className="w-full px-4 py-2 bg-anthro-bg border border-anthro-border rounded-xl text-sm focus:outline-none focus:ring-1 focus:ring-anthro-accent text-anthro-text-heading placeholder:text-anthro-text-muted font-mono"
              required={transport === 'stdio'}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-anthro-text-heading mb-1.5">
              Arguments <span className="text-anthro-text-muted font-normal">(space-separated)</span>
            </label>
            <input
              type="text"
              value={argsText}
              onChange={(e) => setArgsText(e.target.value)}
              placeholder="--port 3000 --verbose"
              className="w-full px-4 py-2 bg-anthro-bg border border-anthro-border rounded-xl text-sm focus:outline-none focus:ring-1 focus:ring-anthro-accent text-anthro-text-heading placeholder:text-anthro-text-muted font-mono"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-anthro-text-heading mb-1.5">
              Environment Variables <span className="text-anthro-text-muted font-normal">(KEY=VALUE per line)</span>
            </label>
            <textarea
              value={envText}
              onChange={(e) => setEnvText(e.target.value)}
              placeholder={"API_KEY=xxx\nDEBUG=true"}
              rows={3}
              className="w-full px-4 py-2 bg-anthro-bg border border-anthro-border rounded-xl text-sm focus:outline-none focus:ring-1 focus:ring-anthro-accent text-anthro-text-heading placeholder:text-anthro-text-muted font-mono resize-y"
            />
          </div>
        </>
      )}

      {/* HTTP fields */}
      {(transport === 'http' || transport === 'sse') && (
        <div>
          <label className="block text-sm font-medium text-anthro-text-heading mb-1.5">
            URL
          </label>
          <input
            type="text"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="http://127.0.0.1:8888/mcp"
            className="w-full px-4 py-2 bg-anthro-bg border border-anthro-border rounded-xl text-sm focus:outline-none focus:ring-1 focus:ring-anthro-accent text-anthro-text-heading placeholder:text-anthro-text-muted font-mono"
            required={transport === 'http' || transport === 'sse'}
          />
        </div>
      )}

      {/* Scope */}
      <div>
        <label className="block text-sm font-medium text-anthro-text-heading mb-2">
          Scope
        </label>
        <div className="flex flex-col gap-2">
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="radio"
              name="scope"
              value="project"
              checked={scope === 'project'}
              onChange={() => setScope('project')}
              className="accent-anthro-accent w-4 h-4"
            />
            <div className="flex items-baseline gap-2">
              <span className="text-sm text-anthro-text-body font-medium">Project</span>
              <span className="text-xs text-anthro-text-muted font-mono bg-anthro-bg px-1.5 py-0.5 rounded">./.mcp.json</span>
            </div>
          </label>
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="radio"
              name="scope"
              value="global"
              checked={scope === 'global'}
              onChange={() => setScope('global')}
              className="accent-anthro-accent w-4 h-4"
            />
            <div className="flex items-baseline gap-2">
              <span className="text-sm text-anthro-text-body font-medium">Global</span>
              <span className="text-xs text-anthro-text-muted font-mono bg-anthro-bg px-1.5 py-0.5 rounded">~/.claude.json</span>
            </div>
          </label>
        </div>
      </div>

      <div className="flex justify-end gap-3 pt-4 border-t border-anthro-border">
        <Button variant="secondary" size="md" type="button" onClick={onCancel}>
          Cancel
        </Button>
        <Button variant="primary" size="md" type="submit">
          {isEdit ? 'Save Changes' : 'Add Server'}
        </Button>
      </div>
    </form>
  );
}