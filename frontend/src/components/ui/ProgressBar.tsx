import { cn } from '@/lib/utils';

interface Segment {
  label: string;
  value: number;
  color: string;
}

interface ProgressBarProps {
  segments: Segment[];
  max: number;
  className?: string;
}

export function ProgressBar({ segments, max, className }: ProgressBarProps) {
  return (
    <div className={cn('h-3 w-full bg-anthro-bg rounded-full overflow-hidden flex mb-8', className)}>
      {segments.map((segment) => {
        const percentage = (segment.value / max) * 100;
        return (
          <div
            key={segment.label}
            className={cn('h-full', segment.color)}
            style={{ width: `${percentage}%` }}
            title={`${segment.label} (${percentage.toFixed(0)}%)`}
          />
        );
      })}
    </div>
  );
}

interface LegendItem {
  label: string;
  color: string;
}

interface ProgressLegendProps {
  items: LegendItem[];
  className?: string;
}

export function ProgressLegend({ items, className }: ProgressLegendProps) {
  return (
    <div className={cn('grid grid-cols-2 md:grid-cols-4 gap-6 pt-6 border-t border-anthro-border', className)}>
      {items.map((item) => (
        <div key={item.label} className="flex items-center space-x-3">
          <div className={cn('w-2.5 h-2.5 rounded-full', item.color)} />
          <span className="text-sm font-medium text-anthro-text-body">{item.label}</span>
        </div>
      ))}
    </div>
  );
}
