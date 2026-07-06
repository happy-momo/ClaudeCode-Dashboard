import type { InputHTMLAttributes } from 'react';
import { cn } from '@/lib/utils';
import { Search } from 'lucide-react';

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  searchIcon?: boolean;
}

export function Input({ searchIcon, className, ...props }: InputProps) {
  if (searchIcon) {
    return (
      <div className="relative">
        <Search className="w-4 h-4 text-anthro-text-muted absolute left-3 top-1/2 -translate-y-1/2" />
        <input
          type="text"
          className={cn(
            'pl-9 pr-4 py-2 bg-anthro-surface border border-anthro-border rounded-xl text-sm w-64 focus:outline-none focus:ring-1 focus:ring-anthro-accent text-anthro-text-heading placeholder:text-anthro-text-muted',
            className
          )}
          {...props}
        />
      </div>
    );
  }

  return (
    <input
      className={cn(
        'px-4 py-2 bg-anthro-surface border border-anthro-border rounded-xl text-sm focus:outline-none focus:ring-1 focus:ring-anthro-accent text-anthro-text-heading placeholder:text-anthro-text-muted',
        className
      )}
      {...props}
    />
  );
}
