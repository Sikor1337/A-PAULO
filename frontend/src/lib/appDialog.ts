export type NotificationTone = 'success' | 'error' | 'warning' | 'info';

export interface DialogOptions {
  title?: string;
  confirmLabel?: string;
  cancelLabel?: string;
  tone?: NotificationTone;
}

export interface PromptOptions extends DialogOptions {
  defaultValue?: string;
  placeholder?: string;
  required?: boolean;
}

export type DialogRequest =
  | {
      id: number;
      kind: 'confirm';
      message: string;
      options: DialogOptions;
      resolve: (accepted: boolean) => void;
    }
  | {
      id: number;
      kind: 'prompt';
      message: string;
      options: PromptOptions;
      resolve: (value: string | null) => void;
    };

export interface NotificationRequest {
  id: number;
  message: string;
  tone: NotificationTone;
  durationMs: number;
}

type DialogListener = (request: DialogRequest) => void;
type NotificationListener = (notification: NotificationRequest) => void;

const dialogListeners = new Set<DialogListener>();
const notificationListeners = new Set<NotificationListener>();
let nextId = 1;

const emitDialog = (request: DialogRequest) => {
  dialogListeners.forEach((listener) => listener(request));
};

const emitNotification = (notification: NotificationRequest) => {
  notificationListeners.forEach((listener) => listener(notification));
};

export const subscribeToDialogs = (listener: DialogListener) => {
  dialogListeners.add(listener);
  return () => {
    dialogListeners.delete(listener);
  };
};

export const subscribeToNotifications = (listener: NotificationListener) => {
  notificationListeners.add(listener);
  return () => {
    notificationListeners.delete(listener);
  };
};

const notify = (
  message: string,
  tone: NotificationTone = 'info',
  durationMs = tone === 'error' ? 7000 : 4500,
) => {
  emitNotification({ id: nextId++, message, tone, durationMs });
};

export const appDialog = {
  notify,
  success: (message: string, durationMs?: number) => notify(message, 'success', durationMs),
  error: (message: string, durationMs?: number) => notify(message, 'error', durationMs),
  warning: (message: string, durationMs?: number) => notify(message, 'warning', durationMs),
  info: (message: string, durationMs?: number) => notify(message, 'info', durationMs),
  confirm: (message: string, options: DialogOptions = {}) =>
    new Promise<boolean>((resolve) => {
      emitDialog({ id: nextId++, kind: 'confirm', message, options, resolve });
    }),
  prompt: (message: string, options: PromptOptions = {}) =>
    new Promise<string | null>((resolve) => {
      emitDialog({ id: nextId++, kind: 'prompt', message, options, resolve });
    }),
};
