import { useEffect } from 'react';
import type { ReactNode } from 'react';

interface ModalProps {
  onClose: () => void;
  children: ReactNode;
  /** Tailwind max-width class for the card (default max-w-lg). */
  maxWidth?: string;
  /** Whether clicking the dark backdrop closes the modal (default true). */
  closeOnBackdrop?: boolean;
  /** Whether pressing Escape closes the modal (default true). */
  closeOnEscape?: boolean;
}

/** Centered dialog with a dark backdrop. Stops click propagation inside the card. */
const Modal = ({
  onClose,
  children,
  maxWidth = 'max-w-lg',
  closeOnBackdrop = true,
  closeOnEscape = true,
}: ModalProps) => {
  useEffect(() => {
    if (!closeOnEscape) return;

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') onClose();
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [closeOnEscape, onClose]);

  return (
    <div
      className="fixed inset-0 z-50 flex items-end justify-center bg-black/60 p-0 sm:items-center sm:p-4"
      onClick={closeOnBackdrop ? onClose : undefined}
      role="presentation"
    >
      <div
        role="dialog"
        aria-modal="true"
        className={`max-h-[92dvh] w-full overflow-y-auto rounded-t-2xl bg-white p-5 shadow-2xl sm:rounded-xl sm:p-8 ${maxWidth}`}
        onClick={(e) => e.stopPropagation()}
      >
        {children}
      </div>
    </div>
  );
};

export default Modal;
