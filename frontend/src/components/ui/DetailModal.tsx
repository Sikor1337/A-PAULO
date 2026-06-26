import type { ReactNode } from 'react';
import Modal from './Modal';

export interface DetailField {
  label: string;
  value: ReactNode;
}

interface DetailModalProps {
  title: string;
  fields: DetailField[];
  onClose: () => void;
  /** Optional colored eyebrow above the title (e.g. "Podopieczny"). */
  tag?: { text: string; className: string };
  /** Tailwind classes for each value (<dd>); defaults to bold gray. */
  valueClassName?: string;
  /** Footer content (action buttons). Defaults to a single "Zamknij" button. */
  footer?: ReactNode;
}

/** Config-driven read-only details dialog (dl/dt/dd). Replaces the duplicated detail modals. */
const DetailModal = ({
  title,
  fields,
  onClose,
  tag,
  valueClassName = 'text-gray-800 font-bold',
  footer,
}: DetailModalProps) => (
  <Modal onClose={onClose}>
    <div className="mb-6 flex items-start justify-between gap-4">
      <div>
        {tag && <p className={`text-[10px] font-bold uppercase tracking-wider mb-1 ${tag.className}`}>{tag.text}</p>}
        <h2 className="break-words text-xl font-bold text-gray-900">{title}</h2>
      </div>
      <button onClick={onClose} className="text-gray-400 hover:text-gray-600 text-2xl leading-none">
        &times;
      </button>
    </div>
    <dl className="space-y-3 text-sm">
      {fields.map(({ label, value }) => (
        <div key={label}>
          <dt className="text-[10px] font-black uppercase text-gray-400">{label}</dt>
          <dd className={valueClassName}>{value || '—'}</dd>
        </div>
      ))}
    </dl>
    <div className="mt-6 flex flex-col-reverse gap-2 border-t pt-6 sm:flex-row sm:justify-end sm:gap-3">
      {footer ?? (
        <button onClick={onClose} className="px-4 py-2 text-gray-400 font-bold">
          Zamknij
        </button>
      )}
    </div>
  </Modal>
);

export default DetailModal;
