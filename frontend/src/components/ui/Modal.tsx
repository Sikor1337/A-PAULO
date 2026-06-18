import type { ReactNode } from 'react';

interface ModalProps {
  onClose: () => void;
  children: ReactNode;
  /** Tailwind max-width class for the card (default max-w-lg). */
  maxWidth?: string;
  /** Whether clicking the dark backdrop closes the modal (default true). */
  closeOnBackdrop?: boolean;
}

/** Centered dialog with a dark backdrop. Stops click propagation inside the card. */
const Modal = ({ onClose, children, maxWidth = 'max-w-lg', closeOnBackdrop = true }: ModalProps) => (
  <div
    className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4"
    onClick={closeOnBackdrop ? onClose : undefined}
  >
    <div
      className={`bg-white rounded-xl p-8 w-full ${maxWidth} shadow-2xl max-h-[90vh] overflow-y-auto`}
      onClick={(e) => e.stopPropagation()}
    >
      {children}
    </div>
  </div>
);

export default Modal;
