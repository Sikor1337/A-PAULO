import { forwardRef } from 'react';
import type { InputHTMLAttributes, SelectHTMLAttributes, TextareaHTMLAttributes, ReactNode } from 'react';

const LABEL = 'block text-[10px] font-black uppercase text-gray-400 mb-1';
const CONTROL = 'w-full border p-2 rounded-md outline-none focus:border-blue-500';
const ERROR_BORDER = 'border-red-500 bg-red-50';

function ErrorText({ message }: { message?: string }) {
  if (!message) return null;
  return <p className="text-[10px] text-red-500 font-bold mt-1 flex items-center gap-1">⚠️ {message}</p>;
}

interface FieldWrapProps {
  label?: string;
  error?: string;
  children: ReactNode;
}

/** Label + control + inline error wrapper. */
export function Field({ label, error, children }: FieldWrapProps) {
  return (
    <div>
      {label && <label className={LABEL}>{label}</label>}
      {children}
      <ErrorText message={error} />
    </div>
  );
}

type TextInputProps = InputHTMLAttributes<HTMLInputElement> & { label?: string; error?: string };

export const TextInput = forwardRef<HTMLInputElement, TextInputProps>(
  ({ label, error, className = '', ...rest }, ref) => (
    <Field label={label} error={error}>
      <input ref={ref} className={`${CONTROL} ${error ? ERROR_BORDER : ''} ${className}`} {...rest} />
    </Field>
  ),
);
TextInput.displayName = 'TextInput';

type SelectInputProps = SelectHTMLAttributes<HTMLSelectElement> & { label?: string; error?: string };

export const SelectInput = forwardRef<HTMLSelectElement, SelectInputProps>(
  ({ label, error, className = '', children, ...rest }, ref) => (
    <Field label={label} error={error}>
      <select ref={ref} className={`${CONTROL} bg-white ${error ? ERROR_BORDER : ''} ${className}`} {...rest}>
        {children}
      </select>
    </Field>
  ),
);
SelectInput.displayName = 'SelectInput';

type TextAreaProps = TextareaHTMLAttributes<HTMLTextAreaElement> & { label?: string; error?: string };

export const TextArea = forwardRef<HTMLTextAreaElement, TextAreaProps>(
  ({ label, error, className = '', rows = 3, ...rest }, ref) => (
    <Field label={label} error={error}>
      <textarea
        ref={ref}
        rows={rows}
        className={`${CONTROL} resize-none ${error ? ERROR_BORDER : ''} ${className}`}
        {...rest}
      />
    </Field>
  ),
);
TextArea.displayName = 'TextArea';

type CheckboxProps = InputHTMLAttributes<HTMLInputElement> & { label: string };

export const Checkbox = forwardRef<HTMLInputElement, CheckboxProps>(({ label, className = '', ...rest }, ref) => (
  <label className="flex items-center gap-2 cursor-pointer">
    <input ref={ref} type="checkbox" className={`w-4 h-4 rounded ${className}`} {...rest} />
    <span className="text-sm font-medium text-gray-600">{label}</span>
  </label>
));
Checkbox.displayName = 'Checkbox';
