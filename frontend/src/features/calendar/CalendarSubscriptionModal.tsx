import { useState } from 'react';
import Modal from '@/components/ui/Modal';
import { useCalendarSubscription } from '@/hooks/useCalendar';

const CalendarSubscriptionModal = ({ onClose }: { onClose: () => void }) => {
  const { status, generate, revoke } = useCalendarSubscription();
  const [copied, setCopied] = useState(false);
  const feedUrl = generate.data?.feed_url;
  const generateAddress = () => {
    if (status.data?.has_active_token && !confirm('Wygenerowanie nowego adresu unieważni poprzedni. Kontynuować?')) return;
    generate.mutate();
  };
  const copy = async () => {
    if (!feedUrl) return;
    await navigator.clipboard.writeText(feedUrl);
    setCopied(true);
  };

  return (
    <Modal onClose={onClose} maxWidth="max-w-2xl">
      <h2 className="text-xl font-bold text-gray-900">Subskrypcja w Google Calendar</h2>
      <p className="mt-2 text-sm leading-6 text-gray-600">
        To kalendarz tylko do odczytu: A-PAULO → Google. Zmiany wykonane w Google nie wracają do aplikacji,
        a odświeżenie wydarzeń przez Google może potrwać od kilku godzin do nawet doby.
      </p>
      <ol className="mt-4 list-decimal space-y-2 pl-5 text-sm text-gray-700">
        <li>Wygeneruj prywatny adres poniżej.</li>
        <li>W Google Calendar wybierz „Inne kalendarze” → „+” → „Z adresu URL”.</li>
        <li>Wklej adres i dodaj kalendarz.</li>
      </ol>
      <div className="mt-5 rounded-xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">
        Każdy posiadacz adresu może odczytać opublikowane wydarzenia. Nie udostępniaj go osobom nieuprawnionym.
        Reset blokuje przyszłe pobrania, ale nie usuwa kopii wcześniej pobranych przez Google.
      </div>
      {feedUrl && (
        <div className="mt-4 flex flex-col gap-2 rounded-xl bg-gray-100 p-3 sm:flex-row sm:items-center">
          <code className="min-w-0 flex-1 break-all text-xs text-gray-800">{feedUrl}</code>
          <button type="button" onClick={copy} className="rounded-lg bg-emerald-600 px-4 py-2 text-sm font-bold text-white">{copied ? 'Skopiowano' : 'Kopiuj'}</button>
        </div>
      )}
      {status.data?.has_active_token && !feedUrl && (
        <p className="mt-4 rounded-lg bg-blue-50 p-3 text-sm text-blue-800">
          Masz aktywną subskrypcję. Ze względów bezpieczeństwa jawny token nie jest przechowywany — wygeneruj nowy adres, jeśli go nie masz.
        </p>
      )}
      <div className="mt-6 flex flex-wrap justify-end gap-2">
        {status.data?.has_active_token && (
          <button type="button" onClick={() => confirm('Unieważnić adres subskrypcji?') && revoke.mutate()} className="rounded-lg bg-rose-50 px-4 py-2 text-sm font-bold text-rose-700">Unieważnij</button>
        )}
        <button type="button" disabled={generate.isPending} onClick={generateAddress} className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-bold text-white disabled:opacity-50">
          {status.data?.has_active_token ? 'Wygeneruj nowy adres' : 'Wygeneruj adres'}
        </button>
      </div>
    </Modal>
  );
};

export default CalendarSubscriptionModal;
