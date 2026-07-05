import { fireEvent, render, screen } from '@testing-library/react';
import { useState } from 'react';
import { createMemoryRouter, Link, RouterProvider } from 'react-router-dom';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { useUnsavedChanges } from './useUnsavedChanges';

const Editor = () => {
  const [dirty, setDirty] = useState(false);
  useUnsavedChanges(dirty);
  return (
    <>
      <button type="button" onClick={() => setDirty(true)}>Zmień</button>
      <Link to="/other">Wyjdź</Link>
    </>
  );
};

const renderEditor = () => {
  const router = createMemoryRouter([
    { path: '/', element: <Editor /> },
    { path: '/other', element: <p>Inna strona</p> },
  ]);
  render(<RouterProvider router={router} />);
};

describe('useUnsavedChanges', () => {
  afterEach(() => vi.restoreAllMocks());

  it('keeps the user on the page after cancelling navigation', () => {
    vi.spyOn(window, 'confirm').mockReturnValue(false);
    renderEditor();
    fireEvent.click(screen.getByRole('button', { name: 'Zmień' }));
    fireEvent.click(screen.getByRole('link', { name: 'Wyjdź' }));
    expect(window.confirm).toHaveBeenCalledOnce();
    expect(screen.getByRole('button', { name: 'Zmień' })).toBeInTheDocument();
  });

  it('allows conscious navigation away from dirty data', () => {
    vi.spyOn(window, 'confirm').mockReturnValue(true);
    renderEditor();
    fireEvent.click(screen.getByRole('button', { name: 'Zmień' }));
    fireEvent.click(screen.getByRole('link', { name: 'Wyjdź' }));
    expect(screen.getByText('Inna strona')).toBeInTheDocument();
  });

  it('registers the native browser close warning while dirty', () => {
    renderEditor();
    fireEvent.click(screen.getByRole('button', { name: 'Zmień' }));
    const event = new Event('beforeunload', { cancelable: true });
    window.dispatchEvent(event);
    expect(event.defaultPrevented).toBe(true);
  });
});
