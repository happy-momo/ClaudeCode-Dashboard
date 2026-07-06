import type { ButtonHTMLAttributes, ReactNode } from 'react';
import { cn } from '@/lib/utils';

type ButtonVariant = 'primary' | 'secondary' | 'ghost' | 'danger';
type ButtonSize = 'sm' | 'md';

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  children: ReactNode;
}

const variantStyles: Record<ButtonVariant, string> = {
  primary:
    'bg-anthro-accent text-white hover:bg-anthro-accent-hover shadow-sm transition-all duration-200',
  secondary:
    'border border-anthro-border bg-anthro-surface text-anthro-text-heading hover:bg-anthro-hover hover:border-anthro-border-hover transition-all duration-200 shadow-sm',
  ghost:
    'text-anthro-text-muted hover:text-anthro-text-heading hover:bg-anthro-hover border border-transparent transition-all duration-200',
  danger:
    'border border-[#EFDACD] bg-[#F9EFEA] text-[#B55A30] hover:bg-[#FBEBE7] transition-all duration-200 shadow-sm',
};

const sizeStyles: Record<ButtonSize, string> = {
  sm: 'px-3 py-1.5 text-xs',
  md: 'px-4 py-2 text-sm',
};

export function Button({
  variant = 'primary',
  size = 'md',
  className,
  children,
  ...props
}: ButtonProps) {
  return (
    <button
      className={cn(
        'rounded-xl font-medium flex items-center transition-all duration-200',
        variantStyles[variant],
        sizeStyles[size],
        className
      )}
      {...props}
    >
      {children}
    </button>
  );
}
