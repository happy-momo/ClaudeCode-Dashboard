import type { ComponentType } from 'react';
import { Box } from 'lucide-react';
import { SidebarNav } from './SidebarNav';

interface NavItem {
  id: string;
  label: string;
  icon: ComponentType<{ className?: string }>;
}

interface SidebarProps {
  items: NavItem[];
  activeId: string;
  onChange: (id: string) => void;
}

export function Sidebar({ items, activeId, onChange }: SidebarProps) {
  return (
    <aside className="w-72 bg-anthro-surface border-r border-anthro-border flex flex-col h-full">
      {/* Header */}
      <div className="p-8 border-b border-anthro-border flex items-center space-x-4 flex-shrink-0">
        <div className="w-10 h-10 bg-anthro-text-heading rounded-xl flex items-center justify-center shadow-sm">
          <Box className="w-5 h-5 text-anthro-surface" />
        </div>
        <div>
          <h1 className="font-serif text-xl text-anthro-text-heading tracking-tight">Claude Plugin</h1>
          <p className="text-sm text-anthro-text-muted font-medium mt-0.5">Workspace Config</p>
        </div>
      </div>

      {/* Navigation */}
      <div className="flex-1 overflow-y-auto">
        <SidebarNav items={items} activeId={activeId} onChange={onChange} />
      </div>

      {/* Plugin Active - pinned to bottom of sidebar (screen bottom-left) */}
      <div className="p-6 border-t border-anthro-border flex-shrink-0">
        <div className="flex items-center space-x-3 px-2">
          <div className="relative flex h-3 w-3">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#D97757] opacity-75"></span>
            <span className="relative inline-flex rounded-full h-3 w-3 bg-anthro-accent"></span>
          </div>
          <span className="text-sm font-medium text-anthro-text-heading">Plugin Active</span>
        </div>
      </div>
    </aside>
  );
}
