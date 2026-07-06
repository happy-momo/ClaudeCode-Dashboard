import { Button } from './Button';
import { AlertTriangle } from 'lucide-react';

interface ErrorDisplayProps {
  message: string;
  details?: string;
  onRetry?: () => void;
  className?: string;
}

export function ErrorDisplay({ message, details, onRetry, className }: ErrorDisplayProps) {
  return (
    <div className={`flex flex-col items-center justify-center py-12 ${className || ''}`}>
      <div className="w-12 h-12 rounded-full bg-[#F9EFEA] flex items-center justify-center mb-4">
        <AlertTriangle className="w-6 h-6 text-[#B55A30]" />
      </div>
      <p className="text-sm text-anthro-text-body font-medium mb-2">{message}</p>
      {details && (
        <p className="text-sm text-anthro-text-muted mb-4 max-w-md text-center">{details}</p>
      )}
      {onRetry && (
        <Button variant="secondary" size="sm" onClick={onRetry}>
          Try Again
        </Button>
      )}
    </div>
  );
}
