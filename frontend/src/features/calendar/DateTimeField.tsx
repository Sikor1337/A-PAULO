interface Props {
  /** Value as a local `YYYY-MM-DDTHH:mm` string (same shape as datetime-local). */
  value: string;
  onChange: (value: string) => void;
  className?: string;
}

const pad = (value: number) => String(value).padStart(2, '0');
const HOURS = Array.from({ length: 24 }, (_, hour) => pad(hour));
const MINUTES = Array.from({ length: 12 }, (_, index) => pad(index * 5));

const split = (value: string) => {
  const [datePart = '', timePart = ''] = value.split('T');
  const [hour = '', minute = ''] = timePart.split(':');
  return { datePart, hour, minute };
};

/**
 * 24-hour date + time picker that does not depend on the browser/OS locale.
 *
 * Native `<input type="datetime-local">` renders a 12-hour AM/PM control on
 * 12-hour locales and fails to show a time picker in some Firefox builds
 * (PAP-97). Composing an explicit date input with hour/minute selects keeps a
 * predictable 0–23 control everywhere.
 */
const DateTimeField = ({ value, onChange, className = '' }: Props) => {
  const { datePart, hour, minute } = split(value);
  // Preserve an off-grid minute (e.g. an imported event at 10:37).
  const minuteOptions = minute && !MINUTES.includes(minute)
    ? [...MINUTES, minute].sort()
    : MINUTES;

  const emit = (next: { date?: string; hour?: string; minute?: string }) => {
    const date = next.date ?? datePart;
    const nextHour = next.hour ?? (hour || '00');
    const nextMinute = next.minute ?? (minute || '00');
    onChange(`${date}T${nextHour}:${nextMinute}`);
  };

  const selectClass = 'h-10 rounded-lg border border-gray-200 px-2 text-sm outline-none focus:border-indigo-500';
  return (
    <div className={`mt-1 flex gap-2 ${className}`}>
      <input
        type="date"
        value={datePart}
        onChange={(event) => emit({ date: event.target.value })}
        className="h-10 min-w-0 flex-1 rounded-lg border border-gray-200 px-3 text-sm outline-none focus:border-indigo-500"
      />
      <select value={hour || '00'} onChange={(event) => emit({ hour: event.target.value })} className={selectClass} aria-label="Godzina">
        {HOURS.map((option) => <option key={option} value={option}>{option}</option>)}
      </select>
      <span className="self-center font-bold text-gray-400">:</span>
      <select value={minute || '00'} onChange={(event) => emit({ minute: event.target.value })} className={selectClass} aria-label="Minuta">
        {minuteOptions.map((option) => <option key={option} value={option}>{option}</option>)}
      </select>
    </div>
  );
};

export default DateTimeField;
