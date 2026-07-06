import type { ReactNode } from 'react';
import { Button } from './Button';

interface EmptyStateProps {
  icon?: ReactNode;
  title: string;
  description?: string;
  actionLabel?: string;
  onAction?: () => void;
  className?: string;
}

export function EmptyState({
  icon,
  title,
  description,
  actionLabel,
  onAction,
  className,
}: EmptyStateProps) {
  return (
    <div className={`flex flex-col items-center justify-center py-12 ${className || ''}`}>
      {icon && <div className="mb-4 text-anthro-text-muted">{icon}</div>}
      <p className="text-sm text-anthro-text-heading font-medium mb-1">{title}</p>
      {description && (
        <p className="text-sm text-anthro-text-muted mb-4">{description}</p>
      )}
      {actionLabel && onAction && (
        <Button variant="secondary" size="sm" onClick={onAction}>
          {actionLabel}
        </Button>
      )}
    </div>
  );
}
