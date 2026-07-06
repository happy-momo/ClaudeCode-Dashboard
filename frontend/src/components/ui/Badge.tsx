import type { ReactNode } from 'react';
import { cn } from '@/lib/utils';

type BadgeVariant = 'project_native' | 'global_native' | 'global_plugin' | 'project_plugin' | 'override';

interface BadgeProps {
  variant: BadgeVariant;
  children: ReactNode;
  className?: string;
}

const variantStyles: Record<BadgeVariant, string> = {
  project_native: 'bg-[#EBF1ED] text-[#2C5F43] border-[#D1E0D7]',
  global_native: 'bg-[#EAEFF5] text-[#2D5B8A] border-[#D0DFEF]',
  global_plugin: 'bg-[#F6EFEA] text-[#8C5A35] border-[#EADAD0]',
  project_plugin: 'bg-[#F2EEF5] text-[#583E7A] border-[#E1D8EB]',
  override: 'bg-[#F9EFEA] text-[#B55A30] border-[#EFDACD]',
};

export function Badge({ variant, children, className }: BadgeProps) {
  return (
    <span
      className={cn(
        'px-2.5 py-1 text-xs font-medium rounded-md border',
        variantStyles[variant],
        className
      )}
    >
      {children}
    </span>
  );
}

/**
 * Maps a source string from the effective view to a BadgeVariant.
 */
export function getSourceBadgeVariant(source: string): BadgeVariant {
  if (source.includes('Project Native')) return 'project_native';
  if (source.includes('Global Native')) return 'global_native';
  if (source.includes('Project Plugin')) return 'project_plugin';
  if (source.includes('Global Plugin')) return 'global_plugin';
  return 'project_native';
}
