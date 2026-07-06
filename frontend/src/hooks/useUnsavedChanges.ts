import { useCallback, useEffect } from 'react';
import { useBlocker } from 'react-router-dom';

export const UNSAVED_CHANGES_MESSAGE =
  'Masz niezapisane zmiany. Czy na pewno chcesz opuścić tę stronę?';

/** Protects dirty forms from route changes, tab closing and explicit cancellation. */
export const useUnsavedChanges = (
  isDirty: boolean,
  message = UNSAVED_CHANGES_MESSAGE,
) => {
  const blocker = useBlocker(isDirty);

  useEffect(() => {
    if (blocker.state !== 'blocked') return;
    if (window.confirm(message)) blocker.proceed();
    else blocker.reset();
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
    () => !isDirty || window.confirm(message),
    [isDirty, message],
  );
};
