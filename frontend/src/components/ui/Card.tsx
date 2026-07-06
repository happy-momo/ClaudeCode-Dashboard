import type { ReactNode, HTMLAttributes } from 'react';
import { cn } from '@/lib/utils';

interface CardProps extends HTMLAttributes<HTMLDivElement> {
  children: ReactNode;
  padding?: 'sm' | 'md' | 'lg';
}

const paddingMap = { sm: 'p-4', md: 'p-6', lg: 'p-8' };

export function Card({ children, className, padding = 'md' }: CardProps) {
  return (
    <div className={cn(
      'bg-anthro-surface rounded-2xl border border-anthro-border shadow-sm',
      paddingMap[padding],
      className
    )}>
      {children}
    </div>
  );
}
