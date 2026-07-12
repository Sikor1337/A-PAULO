import { fireEvent, render, screen } from '@testing-library/react';
import { useState } from 'react';
import { describe, expect, it } from 'vitest';
import { appDialog } from '@/lib/appDialog';
import AppDialogProvider from './AppDialogProvider';

const TestActions = () => {
  const [result, setResult] = useState('');
  return (
    <>
      <button
        type="button"
        onClick={async () => {
          const accepted = await appDialog.confirm('Usunąć rekord?', {
            title: 'Potwierdzenie testowe',
            confirmLabel: 'Usuń',
            tone: 'error',
          });
          setResult(accepted ? 'tak' : 'nie');
        }}
      >
        Otwórz dialog
      </button>
      <button type="button" onClick={() => appDialog.error('Błąd testowy')}>
        Pokaż błąd
      </button>
      <output>{result}</output>
    </>
  );
};

describe('AppDialogProvider', () => {
  it('resolves custom confirmations without browser dialogs', async () => {
    render(<AppDialogProvider><TestActions /></AppDialogProvider>);

    fireEvent.click(screen.getByRole('button', { name: 'Otwórz dialog' }));
    expect(await screen.findByRole('heading', { name: 'Potwierdzenie testowe' })).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Usuń' }));

    expect(await screen.findByText('tak')).toBeInTheDocument();
  });

  it('shows application notifications', async () => {
    render(<AppDialogProvider><TestActions /></AppDialogProvider>);

    fireEvent.click(screen.getByRole('button', { name: 'Pokaż błąd' }));

    expect(await screen.findByRole('alert')).toHaveTextContent('Błąd testowy');
  });
});
