import { cn } from '@/lib/utils';

interface StatCardProps {
  label: string;
  value: string | number;
  subtitle?: string;
  className?: string;
}

export function StatCard({ label, value, subtitle, className }: StatCardProps) {
  return (
    <div className={cn(
      'bg-anthro-surface p-6 rounded-2xl border border-anthro-border shadow-sm flex flex-col',
      className
    )}>
      <span className="text-anthro-text-muted text-sm font-medium tracking-wide uppercase">{label}</span>
      <span className="text-3xl font-serif text-anthro-text-heading mt-3">{typeof value === 'number' ? value.toLocaleString() : value}</span>
      {subtitle && <span className="text-sm text-anthro-text-muted mt-1">{subtitle}</span>}
    </div>
  );
}
