import { useState } from 'react';
import type { FormEventHandler, ReactNode } from 'react';
import { useUnsavedChanges } from '@/hooks/useUnsavedChanges';
import Modal from './Modal';

interface FormModalProps {
  title: string;
  onClose: () => void;
  onSubmit: FormEventHandler<HTMLFormElement>;
  isPending: boolean;
  children: ReactNode;
  submitLabel?: string;
}

/** Modal wrapping a CRUD form: title, body fields (children) and a Cancel/Submit footer. */
const FormModal = ({ title, onClose, onSubmit, isPending, children, submitLabel = 'Zatwierdź' }: FormModalProps) => {
  const [isDirty, setIsDirty] = useState(false);
  const confirmDiscard = useUnsavedChanges(isDirty && !isPending);
  const close = async () => {
    if (await confirmDiscard()) onClose();
  };

  return (
    <Modal onClose={close}>
      <h2 className="text-xl font-bold mb-6 text-gray-900">{title}</h2>
      <form
        onSubmit={onSubmit}
        onChange={() => setIsDirty(true)}
        className="space-y-4"
        noValidate
      >
        {children}
        <div className="flex flex-col-reverse gap-2 pt-6 sm:flex-row sm:justify-end sm:gap-3">
          <button type="button" onClick={close} className="px-4 py-2 text-gray-400 font-bold hover:text-gray-600">
            Anuluj
          </button>
          <button
            type="submit"
            disabled={isPending}
            className="bg-blue-600 text-white px-6 py-2 rounded-md font-bold shadow-md hover:bg-blue-700 disabled:opacity-50"
          >
            {isPending ? 'Zapisywanie...' : submitLabel}
          </button>
        </div>
      </form>
    </Modal>
  );
};

export default FormModal;
