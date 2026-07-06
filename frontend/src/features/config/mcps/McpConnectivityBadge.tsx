import { cn } from '@/lib/utils';
import { CheckCircle2, AlertTriangle, Loader2 } from 'lucide-react';
import type { ConnectivityStatus } from '@/types/mcp';

interface McpConnectivityBadgeProps {
  status: ConnectivityStatus;
  message?: string;
  className?: string;
}

export function McpConnectivityBadge({ status, message, className }: McpConnectivityBadgeProps) {
  switch (status) {
    case 'connected':
      return (
        <span className={cn('flex items-center text-[#2C5F43] text-xs font-medium', className)}>
          <CheckCircle2 className="w-3.5 h-3.5 mr-1" /> Connected
        </span>
      );
    case 'testing':
      return (
        <span className={cn('flex items-center text-anthro-text-muted text-xs font-medium', className)}>
          <Loader2 className="w-3.5 h-3.5 mr-1 animate-spin" /> Testing...
        </span>
      );
    case 'error':
      return (
        <span
          className={cn(
            'flex items-center text-[#B55A30] text-xs font-medium',
            className
          )}
          title={message}
        >
          <AlertTriangle className="w-3.5 h-3.5 mr-1" /> Error
        </span>
      );
    default:
      return (
        <span className={cn('flex items-center text-anthro-text-muted text-xs', className)}>
          Unknown
        </span>
      );
  }
}
