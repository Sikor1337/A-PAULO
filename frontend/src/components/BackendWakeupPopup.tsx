import { useSyncExternalStore } from 'react';
import {
  getBackendWakeupSnapshot,
  subscribeToBackendWakeup,
} from '@/lib/backendWakeup';

const BackendWakeupPopup = () => {
  const isVisible = useSyncExternalStore(
    subscribeToBackendWakeup,
    getBackendWakeupSnapshot,
    getBackendWakeupSnapshot,
  );

  if (!isVisible) return null;

  return (
    <div className="pointer-events-none fixed inset-0 z-[100] flex items-center justify-center bg-slate-950/35 px-4 backdrop-blur-[2px]">
      <div
        role="status"
        aria-live="polite"
        className="w-full max-w-lg rounded-2xl border border-amber-200 bg-white p-6 shadow-2xl sm:p-8"
      >
        <div className="flex items-start gap-4">
          <div
            aria-hidden="true"
            className="mt-1 size-10 shrink-0 animate-spin rounded-full border-4 border-amber-100 border-t-amber-500"
          />
          <div>
            <h2 className="text-xl font-bold text-slate-900">
              Trwa uruchamianie serwera…
            </h2>
            <p className="mt-3 text-sm leading-6 text-slate-600 sm:text-base">
              Ponieważ do pierwszej wersji używamy darmowego hostingu backendu i
              aplikacja nie była używana przez jakiś czas, pierwsze załadowanie może
              potrwać około 30–60 sekund. Prosimy o cierpliwość.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default BackendWakeupPopup;
