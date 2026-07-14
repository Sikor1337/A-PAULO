import { useCallback, useEffect, useRef } from 'react';
import { useBlocker } from 'react-router-dom';
import { appDialog } from '@/lib/appDialog';

export const UNSAVED_CHANGES_MESSAGE =
  'Masz niezapisane zmiany. Czy na pewno chcesz opuścić tę stronę?';

/** Protects dirty forms from route changes, tab closing and explicit cancellation. */
export const useUnsavedChanges = (
  isDirty: boolean,
  message = UNSAVED_CHANGES_MESSAGE,
) => {
  const blocker = useBlocker(isDirty);
  const handlingBlocker = useRef(false);

  useEffect(() => {
    if (blocker.state !== 'blocked') {
      handlingBlocker.current = false;
      return;
    }
    if (handlingBlocker.current) return;
    handlingBlocker.current = true;
    void appDialog.confirm(message, {
      title: 'Niezapisane zmiany',
      confirmLabel: 'Opuść stronę',
      tone: 'warning',
    }).then((accepted) => {
      if (accepted) blocker.proceed();
      else blocker.reset();
    }).finally(() => {
      handlingBlocker.current = false;
    });
  }, [blocker, message]);

  useEffect(() => {
    if (!isDirty) return;
    const handleBeforeUnload = (event: BeforeUnloadEvent) => {
      event.preventDefault();
      event.returnValue = '';
    };
    window.addEventListener('beforeunload', handleBeforeUnload);
    return () => window.removeEventListener('beforeunload', handleBeforeUnload);
  }, [isDirty]);

  return useCallback(
    () => isDirty
      ? appDialog.confirm(message, { title: 'Niezapisane zmiany', confirmLabel: 'Odrzuć zmiany', tone: 'warning' })
      : Promise.resolve(true),
    [isDirty, message],
  );
};
