import type { RecruitmentField } from '@/types';

interface Props {
  field: RecruitmentField;
  value: unknown;
  onChange: (value: unknown) => void;
}

const inputClass = 'mt-1 min-h-11 w-full rounded-lg border border-gray-200 bg-white px-3 text-gray-900 outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100';

const PublicSurveyField = ({ field, value, onChange }: Props) => {
  const id = `public-survey-${field.key}`;
  if (field.field_type === 'textarea') return <textarea id={id} rows={4} required={field.required} value={String(value ?? '')} placeholder={field.placeholder} onChange={(event) => onChange(event.target.value)} className={`${inputClass} py-3`} />;
  if (field.field_type === 'select') return <select id={id} required={field.required} value={String(value ?? '')} onChange={(event) => onChange(event.target.value)} className={inputClass}><option value="">Wybierz odpowiedź</option>{field.options.map((option) => <option key={option}>{option}</option>)}</select>;
  if (field.field_type === 'radio') return <div className="mt-2 space-y-2">{field.options.map((option) => <label key={option} className="flex min-h-11 items-center gap-3 rounded-lg border px-3"><input type="radio" name={field.key} required={field.required} checked={value === option} onChange={() => onChange(option)} />{option}</label>)}</div>;
  if (field.field_type === 'multiselect') {
    const selected = Array.isArray(value) ? value as string[] : [];
    return <div className="mt-2 space-y-2">{field.options.map((option) => <label key={option} className="flex min-h-11 items-center gap-3 rounded-lg border px-3"><input type="checkbox" checked={selected.includes(option)} onChange={(event) => onChange(event.target.checked ? [...selected, option] : selected.filter((item) => item !== option))} />{option}</label>)}{field.required && !selected.length && <p className="text-xs text-rose-600">Wybierz co najmniej jedną odpowiedź.</p>}</div>;
  }
  if (field.field_type === 'checkbox') return <label className="mt-2 flex min-h-11 items-start gap-3 rounded-lg border px-3 py-3 font-normal"><input id={id} type="checkbox" required={field.required} checked={Boolean(value)} onChange={(event) => onChange(event.target.checked)} className="mt-1" /><span>Tak, potwierdzam</span></label>;
  return <input id={id} type={field.field_type} required={field.required} value={String(value ?? '')} placeholder={field.placeholder} onChange={(event) => onChange(event.target.value)} className={inputClass} />;
};

export default PublicSurveyField;
