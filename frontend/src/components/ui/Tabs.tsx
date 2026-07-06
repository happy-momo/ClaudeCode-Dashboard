import { cn } from '@/lib/utils';

interface TabItem {
  id: string;
  label: string;
}

interface TabsProps {
  items: TabItem[];
  activeId: string;
  onChange: (id: string) => void;
  className?: string;
}

export function Tabs({ items, activeId, onChange, className }: TabsProps) {
  return (
    <div className={cn('flex space-x-6 border-b border-anthro-border', className)}>
      {items.map((tab) => (
        <button
          key={tab.id}
          onClick={() => onChange(tab.id)}
          className={cn(
            'pb-4 text-sm font-medium transition-colors relative',
            activeId === tab.id
              ? 'text-anthro-text-heading'
              : 'text-anthro-text-muted hover:text-anthro-text-body'
          )}
        >
          {tab.label}
          {activeId === tab.id && (
            <span className="absolute bottom-0 left-0 w-full h-0.5 bg-anthro-accent rounded-t-full" />
          )}
        </button>
      ))}
    </div>
  );
}
