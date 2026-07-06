import type { ComponentType } from 'react';
import { cn } from '@/lib/utils';

interface NavItem {
  id: string;
  label: string;
  icon: ComponentType<{ className?: string }>;
}

interface SidebarNavProps {
  items: NavItem[];
  activeId: string;
  onChange: (id: string) => void;
}

export function SidebarNav({ items, activeId, onChange }: SidebarNavProps) {
  return (
    <nav className="px-4 py-8 space-y-2">
      {items.map((tab) => {
        const Icon = tab.icon;
        const isActive = activeId === tab.id;
        return (
          <button
            key={tab.id}
            onClick={() => onChange(tab.id)}
            className={cn(
              'w-full flex items-center space-x-3 px-4 py-3 rounded-xl text-sm font-medium transition-all duration-200',
              isActive
                ? 'bg-anthro-bg text-anthro-text-heading shadow-sm border border-anthro-border'
                : 'text-anthro-text-muted hover:bg-anthro-hover hover:text-anthro-text-heading border border-transparent'
            )}
          >
            <Icon className={cn('w-5 h-5', isActive ? 'text-anthro-accent' : 'text-anthro-text-muted')} />
            <span>{tab.label}</span>
          </button>
        );
      })}
    </nav>
  );
}
