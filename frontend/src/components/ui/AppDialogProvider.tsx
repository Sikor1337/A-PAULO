import { useEffect, useMemo, useRef, useState } from 'react';
import type { ReactNode } from 'react';
import {
  subscribeToDialogs,
  subscribeToNotifications,
  type DialogRequest,
  type NotificationRequest,
  type NotificationTone,
} from '../../lib/appDialog';
import Modal from './Modal';

interface AppDialogProviderProps {
  children: ReactNode;
}

const toneClasses: Record<NotificationTone, { card: string; icon: string; symbol: string }> = {
  success: { card: 'border-emerald-200 bg-emerald-50 text-emerald-950', icon: 'bg-emerald-600', symbol: '✓' },
  error: { card: 'border-rose-200 bg-rose-50 text-rose-950', icon: 'bg-rose-600', symbol: '!' },
  warning: { card: 'border-amber-200 bg-amber-50 text-amber-950', icon: 'bg-amber-500', symbol: '!' },
  info: { card: 'border-blue-200 bg-blue-50 text-blue-950', icon: 'bg-blue-600', symbol: 'i' },
};

const Notification = ({ item, onClose }: { item: NotificationRequest; onClose: () => void }) => {
  useEffect(() => {
    const timer = window.setTimeout(onClose, item.durationMs);
    return () => window.clearTimeout(timer);
  }, [item.durationMs, onClose]);

  const style = toneClasses[item.tone];
  return (
    <div
      className={`pointer-events-auto flex w-full items-start gap-3 rounded-xl border p-4 shadow-xl ${style.card}`}
      role={item.tone === 'error' ? 'alert' : 'status'}
    >
      <span className={`flex h-7 w-7 shrink-0 items-center justify-center rounded-full font-black text-white ${style.icon}`} aria-hidden="true">
        {style.symbol}
      </span>
      <p className="min-w-0 flex-1 whitespace-pre-line text-sm font-semibold leading-6">{item.message}</p>
      <button
        type="button"
        className="rounded-md px-2 py-1 text-lg leading-none opacity-60 transition hover:bg-black/10 hover:opacity-100"
        onClick={onClose}
        aria-label="Zamknij powiadomienie"
      >
        ×
      </button>
    </div>
  );
};

const AppDialogProvider = ({ children }: AppDialogProviderProps) => {
  const [queue, setQueue] = useState<DialogRequest[]>([]);
  const [notifications, setNotifications] = useState<NotificationRequest[]>([]);
  const [promptValues, setPromptValues] = useState<Record<number, string>>({});
  const primaryActionRef = useRef<HTMLButtonElement>(null);
  const promptInputRef = useRef<HTMLInputElement>(null);

  const active = queue[0];

  useEffect(() => subscribeToDialogs((request) => {
    if (request.kind === 'prompt') {
      setPromptValues((current) => ({ ...current, [request.id]: request.options.defaultValue ?? '' }));
    }
    setQueue((current) => [...current, request]);
  }), []);
  useEffect(() => subscribeToNotifications((item) => setNotifications((current) => [...current, item])), []);

  useEffect(() => {
    if (!active) return;
    if (active.kind === 'prompt') {
      window.setTimeout(() => promptInputRef.current?.focus(), 0);
    } else {
      window.setTimeout(() => primaryActionRef.current?.focus(), 0);
    }
  }, [active]);

  const labels = useMemo(() => ({
    title: active?.options.title ?? (active?.kind === 'prompt' ? 'Uzupełnij informację' : 'Potwierdź operację'),
    confirm: active?.options.confirmLabel ?? (active?.kind === 'prompt' ? 'Zapisz' : 'Potwierdź'),
    cancel: active?.options.cancelLabel ?? 'Anuluj',
  }), [active]);
  const promptValue = active?.kind === 'prompt' ? promptValues[active.id] ?? '' : '';

  const closeActive = (result: boolean | string | null) => {
    if (!active) return;
    if (active.kind === 'confirm') active.resolve(result === true);
    else {
      active.resolve(typeof result === 'string' ? result : null);
      setPromptValues((current) => {
        const next = { ...current };
        delete next[active.id];
        return next;
      });
    }
    setQueue((current) => current.slice(1));
  };

  const submitPrompt = () => {
    if (!active || active.kind !== 'prompt') return;
    const value = promptValue.trim();
    if (active.options.required && !value) return;
    closeActive(value);
  };

  const destructive = active?.options.tone === 'error' || active?.options.tone === 'warning';

  return (
    <>
      {children}

      <div className="pointer-events-none fixed right-3 top-3 z-[70] flex w-[min(26rem,calc(100vw-1.5rem))] flex-col gap-2 sm:right-5 sm:top-5" aria-live="polite">
        {notifications.map((item) => (
          <Notification
            key={item.id}
            item={item}
            onClose={() => setNotifications((current) => current.filter((entry) => entry.id !== item.id))}
          />
        ))}
      </div>

      {active && (
        <Modal onClose={() => closeActive(active.kind === 'confirm' ? false : null)} closeOnBackdrop={false}>
          <form
            onSubmit={(event) => {
              event.preventDefault();
              if (active.kind === 'prompt') submitPrompt();
              else closeActive(true);
            }}
          >
            <div className="mb-5 flex items-start gap-4">
              <span className={`flex h-11 w-11 shrink-0 items-center justify-center rounded-full text-xl font-black text-white ${destructive ? 'bg-rose-600' : 'bg-blue-600'}`} aria-hidden="true">
                {active.kind === 'prompt' ? '✎' : destructive ? '!' : '?'}
              </span>
              <div>
                <h2 className="text-xl font-black text-slate-950">{labels.title}</h2>
                <p className="mt-2 whitespace-pre-line text-sm leading-6 text-slate-600">{active.message}</p>
              </div>
            </div>

            {active.kind === 'prompt' && (
              <input
                ref={promptInputRef}
                value={promptValue}
                onChange={(event) => setPromptValues((current) => ({ ...current, [active.id]: event.target.value }))}
                placeholder={active.options.placeholder}
                required={active.options.required}
                className="mb-6 w-full rounded-lg border border-slate-300 px-3 py-2.5 outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
              />
            )}

            <div className="flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
              <button
                type="button"
                onClick={() => closeActive(active.kind === 'confirm' ? false : null)}
                className="rounded-lg border border-slate-300 px-4 py-2.5 text-sm font-bold text-slate-700 transition hover:bg-slate-50"
              >
                {labels.cancel}
              </button>
              <button
                ref={primaryActionRef}
                type="submit"
                disabled={active.kind === 'prompt' && Boolean(active.options.required) && !promptValue.trim()}
                className={`rounded-lg px-4 py-2.5 text-sm font-bold text-white transition disabled:cursor-not-allowed disabled:opacity-50 ${destructive ? 'bg-rose-600 hover:bg-rose-700' : 'bg-blue-600 hover:bg-blue-700'}`}
              >
                {labels.confirm}
              </button>
            </div>
          </form>
        </Modal>
      )}
    </>
  );
};

export default AppDialogProvider;
