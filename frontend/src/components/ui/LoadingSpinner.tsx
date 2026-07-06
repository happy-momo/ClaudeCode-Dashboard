import { cn } from '@/lib/utils';

interface LoadingSpinnerProps {
  message?: string;
  className?: string;
}

export function LoadingSpinner({ message = 'Loading...', className }: LoadingSpinnerProps) {
  return (
    <div className={cn('flex flex-col items-center justify-center py-12', className)}>
      <div className="w-8 h-8 border-2 border-anthro-border border-t-anthro-accent rounded-full animate-spin" />
      {message && (
        <p className="mt-4 text-sm text-anthro-text-muted font-medium">{message}</p>
      )}
    </div>
  );
}
