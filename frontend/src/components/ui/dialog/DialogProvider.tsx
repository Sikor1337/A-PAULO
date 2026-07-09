import { createContext, useCallback, useContext, useMemo, useRef, useState } from 'react';
import type { ReactNode } from 'react';
import Modal from '@/components/ui/Modal';

type Tone = 'default' | 'danger';

interface ConfirmOptions {
  title?: string;
  message: ReactNode;
  confirmLabel?: string;
  cancelLabel?: string;
  tone?: Tone;
}

interface AlertOptions {
  title?: string;
  message: ReactNode;
  confirmLabel?: string;
  tone?: Tone;
}

interface PromptOptions {
  title?: string;
  message?: ReactNode;
  defaultValue?: string;
  placeholder?: string;
  confirmLabel?: string;
  cancelLabel?: string;
  /** Reject an empty (whitespace-only) value instead of resolving. */
  required?: boolean;
  multiline?: boolean;
}

interface Dialogs {
  confirm: (options: ConfirmOptions) => Promise<boolean>;
  alert: (options: AlertOptions) => Promise<void>;
  /** Resolves with the trimmed value, or null if cancelled. */
  prompt: (options: PromptOptions) => Promise<string | null>;
}

type Request =
  | { kind: 'confirm'; options: ConfirmOptions; resolve: (value: boolean) => void }
  | { kind: 'alert'; options: AlertOptions; resolve: () => void }
  | { kind: 'prompt'; options: PromptOptions; resolve: (value: string | null) => void };

const asText = (value: ReactNode) => (typeof value === 'string' ? value : '');

/**
 * Fallback used when no provider is mounted (unit tests, or a misuse). The app
 * always wraps its tree in <DialogProvider>, so real users get the styled
 * dialogs; this only keeps `useDialogs` from throwing outside that tree.
 */
const fallbackDialogs: Dialogs = {
  confirm: ({ message, title }) => Promise.resolve(window.confirm(asText(title) || asText(message))),
  alert: ({ message, title }) => { window.alert(asText(title) || asText(message)); return Promise.resolve(); },
  prompt: ({ message, title, defaultValue = '' }) => {
    const result = window.prompt(asText(title) || asText(message), defaultValue);
    return Promise.resolve(result === null ? null : result.trim());
  },
};

const DialogContext = createContext<Dialogs>(fallbackDialogs);

const primaryClass = (tone: Tone) =>
  tone === 'danger'
    ? 'rounded-lg bg-rose-600 px-5 py-2 text-sm font-bold text-white hover:bg-rose-700'
    : 'rounded-lg bg-indigo-600 px-5 py-2 text-sm font-bold text-white hover:bg-indigo-700';

const cancelClass = 'rounded-lg border px-4 py-2 text-sm font-bold text-gray-600 hover:bg-gray-50';

export const DialogProvider = ({ children }: { children: ReactNode }) => {
  const [request, setRequest] = useState<Request | null>(null);
  const [promptValue, setPromptValue] = useState('');
  // Guards against a backdrop/escape close racing with a button click.
  const settled = useRef(false);

  const open = useCallback((next: Request, initialValue = '') => {
    settled.current = false;
    setPromptValue(initialValue);
    setRequest(next);
  }, []);

  const dialogs = useMemo<Dialogs>(() => ({
    confirm: (options) =>
      new Promise<boolean>((resolve) => open({ kind: 'confirm', options, resolve })),
    alert: (options) =>
      new Promise<void>((resolve) => open({ kind: 'alert', options, resolve })),
    prompt: (options) =>
      new Promise<string | null>((resolve) =>
        open({ kind: 'prompt', options, resolve }, options.defaultValue ?? ''),
      ),
  }), [open]);

  const finish = useCallback((settle: () => void) => {
    if (settled.current) return;
    settled.current = true;
    settle();
    setRequest(null);
  }, []);

  const cancel = useCallback(() => {
    if (!request) return;
    if (request.kind === 'alert') finish(() => request.resolve());
    else if (request.kind === 'confirm') finish(() => request.resolve(false));
    else finish(() => request.resolve(null));
  }, [request, finish]);

  const submitPrompt = useCallback(() => {
    if (!request || request.kind !== 'prompt') return;
    const trimmed = promptValue.trim();
    if (request.options.required && !trimmed) return;
    finish(() => request.resolve(trimmed));
  }, [request, promptValue, finish]);

  return (
    <DialogContext.Provider value={dialogs}>
      {children}
      {request && (
        <Modal onClose={cancel} maxWidth="max-w-md">
          {request.options.title && (
            <h2 className="text-lg font-bold text-gray-900">{request.options.title}</h2>
          )}
          {request.kind === 'prompt' ? (
            <form
              onSubmit={(event) => {
                event.preventDefault();
                submitPrompt();
              }}
            >
              {request.options.message && (
                <p className="mt-2 text-sm text-gray-600">{request.options.message}</p>
              )}
              {request.options.multiline ? (
                <textarea
                  autoFocus
                  rows={3}
                  value={promptValue}
                  placeholder={request.options.placeholder}
                  onChange={(event) => setPromptValue(event.target.value)}
                  className="mt-3 w-full rounded-lg border border-gray-200 px-3 py-2 text-sm outline-none focus:border-indigo-500"
                />
              ) : (
                <input
                  autoFocus
                  value={promptValue}
                  placeholder={request.options.placeholder}
                  onChange={(event) => setPromptValue(event.target.value)}
                  className="mt-3 h-10 w-full rounded-lg border border-gray-200 px-3 text-sm outline-none focus:border-indigo-500"
                />
              )}
              <div className="mt-6 flex justify-end gap-2">
                <button type="button" onClick={cancel} className={cancelClass}>
                  {request.options.cancelLabel ?? 'Anuluj'}
                </button>
                <button
                  type="submit"
                  disabled={request.options.required && !promptValue.trim()}
                  className={`${primaryClass('default')} disabled:opacity-50`}
                >
                  {request.options.confirmLabel ?? 'OK'}
                </button>
              </div>
            </form>
          ) : (
            <>
              <div className={`text-sm text-gray-600 ${request.options.title ? 'mt-2' : ''}`}>
                {request.options.message}
              </div>
              <div className="mt-6 flex justify-end gap-2">
                {request.kind === 'confirm' && (
                  <button type="button" onClick={cancel} className={cancelClass}>
                    {request.options.cancelLabel ?? 'Anuluj'}
                  </button>
                )}
                <button
                  type="button"
                  autoFocus
                  onClick={() => finish(() => {
                    if (request.kind === 'confirm') request.resolve(true);
                    else request.resolve();
                  })}
                  className={primaryClass(request.options.tone ?? (request.kind === 'confirm' ? 'danger' : 'default'))}
                >
                  {request.options.confirmLabel ?? (request.kind === 'confirm' ? 'Potwierdź' : 'OK')}
                </button>
              </div>
            </>
          )}
        </Modal>
      )}
    </DialogContext.Provider>
  );
};

// eslint-disable-next-line react-refresh/only-export-components
export const useDialogs = (): Dialogs => useContext(DialogContext);
