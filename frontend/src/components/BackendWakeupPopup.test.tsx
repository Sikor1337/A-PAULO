import { act, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import {
  BACKEND_WAKEUP_DELAY_MS,
  resetBackendWakeupNotice,
  startBackendRequest,
} from '@/lib/backendWakeup';
import BackendWakeupPopup from './BackendWakeupPopup';

describe('BackendWakeupPopup', () => {
  beforeEach(() => {
    vi.useFakeTimers();
    resetBackendWakeupNotice();
  });

  afterEach(() => {
    resetBackendWakeupNotice();
    vi.useRealTimers();
  });

  it('appears after five seconds and disappears when the request completes', () => {
    render(<BackendWakeupPopup />);

    let finishRequest: () => void = () => undefined;
    act(() => {
      finishRequest = startBackendRequest();
      vi.advanceTimersByTime(BACKEND_WAKEUP_DELAY_MS - 1);
    });
    expect(screen.queryByRole('status')).not.toBeInTheDocument();

    act(() => vi.advanceTimersByTime(1));
    expect(screen.getByRole('status')).toHaveTextContent(
      'Trwa uruchamianie serwera',
    );
    expect(screen.getByRole('status')).toHaveTextContent('30–60 sekund');

    act(() => finishRequest());
    expect(screen.queryByRole('status')).not.toBeInTheDocument();
  });

  it('stays visible until every slow request completes', () => {
    render(<BackendWakeupPopup />);

    let finishFirst: () => void = () => undefined;
    let finishSecond: () => void = () => undefined;
    act(() => {
      finishFirst = startBackendRequest();
      finishSecond = startBackendRequest();
      vi.advanceTimersByTime(BACKEND_WAKEUP_DELAY_MS);
    });

    act(() => finishFirst());
    expect(screen.getByRole('status')).toBeInTheDocument();

    act(() => finishSecond());
    expect(screen.queryByRole('status')).not.toBeInTheDocument();
  });
});
