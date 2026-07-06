import type { ReactNode } from 'react';
import { useEffect, useRef } from 'react';
import { Button } from './Button';
import { cn } from '@/lib/utils';

interface ModalProps {
  open: boolean;
  onClose: () => void;
  title: string;
  children: ReactNode;
  className?: string;
}

export function Modal({ open, onClose, title, children, className }: ModalProps) {
  const overlayRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };

    document.addEventListener('keydown', handleKeyDown);
    document.body.style.overflow = 'hidden';

    return () => {
      document.removeEventListener('keydown', handleKeyDown);
      document.body.style.overflow = '';
    };
  }, [open, onClose]);

  if (!open) return null;

  return (
    <div
      ref={overlayRef}
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm"
      onClick={(e) => {
        if (e.target === overlayRef.current) onClose();
      }}
    >
      <div
        className={cn(
          'relative z-10 bg-anthro-bg rounded-2xl border border-anthro-border shadow-xl p-6 max-w-lg w-full mx-4 animate-in fade-in zoom-in-95 duration-200',
          className
        )}
      >
        <div className="flex justify-between items-center mb-6">
          <h3 className="text-xl font-serif text-anthro-text-heading">{title}</h3>
          <button
            onClick={onClose}
            className="text-anthro-text-muted hover:text-anthro-text-heading hover:bg-anthro-hover rounded-lg p-1.5 transition-colors"
          >
            ✕
          </button>
        </div>
        {children}
      </div>
    </div>
  );
}

interface ConfirmDialogProps {
  open: boolean;
  onClose: () => void;
  onConfirm: () => void;
  title: string;
  message: string;
  confirmLabel?: string;
  danger?: boolean;
}

export function ConfirmDialog({
  open,
  onClose,
  onConfirm,
  title,
  message,
  confirmLabel = 'Confirm',
  danger = true,
}: ConfirmDialogProps) {
  return (
    <Modal open={open} onClose={onClose} title={title}>
      <p className="text-sm text-anthro-text-body mb-6">{message}</p>
      <div className="flex justify-end gap-3">
        <Button variant="secondary" size="md" onClick={onClose}>
          Cancel
        </Button>
        <Button
          variant={danger ? 'danger' : 'primary'}
          size="md"
          onClick={() => {
            onConfirm();
            onClose();
          }}
        >
          {confirmLabel}
        </Button>
      </div>
    </Modal>
  );
}
