import { useState } from 'react';
import Modal from '@/components/ui/Modal';
import type { RecruitmentFieldDraft, RecruitmentFieldType } from '@/types';
import { useUnsavedChanges } from '@/hooks/useUnsavedChanges';

interface Props {
  field: RecruitmentFieldDraft | null;
  onClose: () => void;
  onSave: (data: RecruitmentFieldDraft) => void;
  excludedTypes?: RecruitmentFieldType[];
  systemFieldHelp?: string;
}

const fieldTypes: { value: RecruitmentFieldType; label: string }[] = [
  { value: 'text', label: 'Krótka odpowiedź' },
  { value: 'textarea', label: 'Długa odpowiedź' },
  { value: 'email', label: 'Adres e-mail' },
  { value: 'tel', label: 'Numer telefonu' },
  { value: 'date', label: 'Data' },
  { value: 'select', label: 'Lista wyboru' },
  { value: 'radio', label: 'Jedna z opcji' },
  { value: 'multiselect', label: 'Wiele z wielu' },
  { value: 'checkbox', label: 'Potwierdzenie' },
];

const SurveyFieldModal = ({
  field,
  onClose,
  onSave,
  excludedTypes = [],
  systemFieldHelp = 'To podstawowe pole formularza. Możesz zmienić jego nazwę i podpowiedź, ale nie typ ani wymagalność.',
}: Props) => {
  const [label, setLabel] = useState(field?.label ?? '');
  const [fieldType, setFieldType] = useState<RecruitmentFieldType>(field?.field_type ?? 'text');
  const [required, setRequired] = useState(field?.required ?? false);
  const [placeholder, setPlaceholder] = useState(field?.placeholder ?? '');
  const [optionsText, setOptionsText] = useState(field?.options.join('\n') ?? '');
  const hasOptions = fieldType === 'select' || fieldType === 'radio' || fieldType === 'multiselect';
  const isDirty = label !== (field?.label ?? '')
    || fieldType !== (field?.field_type ?? 'text')
    || required !== (field?.required ?? false)
    || placeholder !== (field?.placeholder ?? '')
    || optionsText !== (field?.options.join('\n') ?? '');
  const confirmDiscard = useUnsavedChanges(isDirty);
  const close = async () => {
    if (await confirmDiscard()) onClose();
  };

  const submit = (event: React.FormEvent) => {
    event.preventDefault();
    onSave({
      label: label.trim(),
      field_type: fieldType,
      required,
      placeholder: placeholder.trim(),
      options: hasOptions
        ? optionsText.split('\n').map((option) => option.trim()).filter(Boolean)
        : [],
      is_active: field?.is_active ?? true,
      ...(field?.id ? { id: field.id } : {}),
      ...(field?.is_system ? { is_system: true } : {}),
    });
  };

  const inputClass = 'mt-1 min-h-11 w-full rounded-lg border border-gray-200 px-3 outline-none focus:border-indigo-500';
  return (
    <Modal onClose={close} maxWidth="max-w-xl">
      <form onSubmit={submit} className="space-y-5">
        <div>
          <p className="text-xs font-bold uppercase tracking-wider text-indigo-600">Kreator formularza</p>
          <h2 className="mt-1 text-2xl font-bold text-gray-900">{field ? 'Edytuj pytanie' : 'Nowe pytanie'}</h2>
        </div>
        <label className="block text-sm font-semibold text-gray-700">
          Treść pytania
          <input required value={label} onChange={(event) => setLabel(event.target.value)} className={inputClass} />
        </label>
        <label className="block text-sm font-semibold text-gray-700">
          Typ odpowiedzi
          <select value={fieldType} disabled={field?.is_system} onChange={(event) => setFieldType(event.target.value as RecruitmentFieldType)} className={`${inputClass} bg-white disabled:bg-gray-100`}>
            {fieldTypes.filter((type) => !excludedTypes.includes(type.value)).map((type) => <option key={type.value} value={type.value}>{type.label}</option>)}
          </select>
        </label>
        <label className="block text-sm font-semibold text-gray-700">
          Tekst pomocniczy
          <input value={placeholder} onChange={(event) => setPlaceholder(event.target.value)} className={inputClass} />
        </label>
        {hasOptions && (
          <label className="block text-sm font-semibold text-gray-700">
            Opcje odpowiedzi — każda w osobnym wierszu
            <textarea required rows={5} value={optionsText} onChange={(event) => setOptionsText(event.target.value)} className="mt-1 w-full rounded-lg border border-gray-200 p-3 outline-none focus:border-indigo-500" />
          </label>
        )}
        <label className="flex items-center gap-3 rounded-lg bg-gray-50 p-3 text-sm font-semibold text-gray-700">
          <input type="checkbox" checked={required} disabled={field?.is_system} onChange={(event) => setRequired(event.target.checked)} className="h-4 w-4" />
          Odpowiedź wymagana
        </label>
        {field?.is_system && <p className="rounded-lg bg-blue-50 p-3 text-sm text-blue-800">{systemFieldHelp}</p>}
        <div className="flex justify-end gap-3 border-t pt-4">
          <button type="button" onClick={close} className="rounded-lg px-4 py-2 font-semibold text-gray-500">Anuluj</button>
          <button className="rounded-lg bg-indigo-600 px-5 py-2 font-bold text-white">
            Zastosuj zmianę
          </button>
        </div>
      </form>
    </Modal>
  );
};

export default SurveyFieldModal;
