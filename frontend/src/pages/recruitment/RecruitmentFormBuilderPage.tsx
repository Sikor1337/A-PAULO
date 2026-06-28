import { useState } from 'react';
import RecruitmentFieldModal from '@/features/recruitment/RecruitmentFieldModal';
import { recruitmentStatusLabel } from '@/features/recruitment/recruitmentStatus';
import { useRecruitmentFields, useRecruitmentInvitations } from '@/hooks/useRecruitment';
import type { RecruitmentField, RecruitmentFieldInput, RecruitmentInvitation } from '@/types';

const typeLabels = {
  text: 'Krótka odpowiedź',
  textarea: 'Długa odpowiedź',
  email: 'E-mail',
  tel: 'Telefon',
  date: 'Data',
  select: 'Lista wyboru',
  radio: 'Jedna z opcji',
  checkbox: 'Potwierdzenie',
};

const RecruitmentFormBuilderPage = () => {
  const { data = [], isLoading, create, update, remove, reorder } = useRecruitmentFields();
  const invitations = useRecruitmentInvitations();
  const [editing, setEditing] = useState<RecruitmentField | null | undefined>(undefined);
  const [copiedToken, setCopiedToken] = useState<string | null>(null);
  const [inviteName, setInviteName] = useState('');
  const [inviteEmail, setInviteEmail] = useState('');
  const [createdInvitation, setCreatedInvitation] = useState<RecruitmentInvitation | null>(null);
  const invitationUrl = (token: string) => `${window.location.origin}/recruitment/apply/${token}`;

  const save = (values: RecruitmentFieldInput) => {
    const onSuccess = () => setEditing(undefined);
    if (editing) update.mutate({ id: editing.id, data: values }, { onSuccess });
    else create.mutate(values, { onSuccess });
  };

  const copyLink = async (token: string) => {
    await navigator.clipboard.writeText(invitationUrl(token));
    setCopiedToken(token);
    window.setTimeout(() => setCopiedToken(null), 1800);
  };

  const createInvitation = (event: React.FormEvent) => {
    event.preventDefault();
    invitations.create.mutate(
      { recipient_name: inviteName.trim(), recipient_email: inviteEmail.trim() },
      {
        onSuccess: (invitation) => {
          setCreatedInvitation(invitation);
          setInviteName('');
          setInviteEmail('');
        },
      },
    );
  };

  const move = (field: RecruitmentField, direction: -1 | 1) => {
    const index = data.findIndex((item) => item.id === field.id);
    const neighbor = data[index + direction];
    if (!neighbor) return;
    const ordered = [...data];
    const current = ordered[index]!;
    ordered[index] = ordered[index + direction]!;
    ordered[index + direction] = current;
    reorder.mutate(ordered.map((item) => item.id));
  };

  return (
    <section>
      <div className="mb-6 rounded-xl border border-indigo-100 bg-indigo-50 p-4 sm:p-5">
        <h2 className="font-bold text-indigo-950">Utwórz jednorazowy link rekrutacyjny</h2>
        <p className="mt-1 text-sm text-indigo-700">Każdy kandydat otrzymuje własny link. Po wysłaniu można go otworzyć ponownie dopiero po zwrocie formularza.</p>
        <form onSubmit={createInvitation} className="mt-4 grid gap-3 md:grid-cols-[1fr_1fr_auto]">
          <input value={inviteName} onChange={(event) => setInviteName(event.target.value)} placeholder="Imię i nazwisko (opcjonalnie)" className="min-h-11 rounded-lg border border-indigo-200 bg-white px-3 text-sm outline-none focus:border-indigo-500" />
          <input required type="email" value={inviteEmail} onChange={(event) => setInviteEmail(event.target.value)} placeholder="E-mail kandydata" className="min-h-11 rounded-lg border border-indigo-200 bg-white px-3 text-sm outline-none focus:border-indigo-500" />
          <button disabled={invitations.create.isPending} className="min-h-11 rounded-lg bg-indigo-600 px-5 text-sm font-bold text-white disabled:opacity-50">{invitations.create.isPending ? 'Tworzenie…' : 'Utwórz link'}</button>
        </form>
        {createdInvitation && (
          <div className="mt-4 flex flex-col gap-2 rounded-lg bg-white p-3 sm:flex-row sm:items-center">
            <code className="min-w-0 flex-1 break-all text-xs text-indigo-900">{invitationUrl(createdInvitation.token)}</code>
            <button onClick={() => copyLink(createdInvitation.token)} className="shrink-0 rounded-lg bg-emerald-600 px-4 py-2 text-sm font-bold text-white">{copiedToken === createdInvitation.token ? 'Skopiowano' : 'Kopiuj link'}</button>
          </div>
        )}
      </div>

      <div className="mb-7">
        <h2 className="mb-3 text-lg font-bold text-gray-900">Wystawione zaproszenia</h2>
        {invitations.isLoading ? <p className="text-sm text-gray-400">Ładowanie…</p> : !invitations.data?.length ? <p className="rounded-lg border border-dashed p-5 text-sm text-gray-500">Nie utworzono jeszcze żadnego zaproszenia.</p> : (
          <div className="space-y-2">
            {invitations.data.map((invitation) => (
              <article key={invitation.id} className="flex flex-col gap-3 rounded-lg border border-gray-200 p-3 sm:flex-row sm:items-center">
                <div className="min-w-0 flex-1">
                  <p className="truncate text-sm font-bold text-gray-900">{invitation.recipient_name || invitation.recipient_email || 'Kandydat'}</p>
                  <p className="truncate text-xs text-gray-500">{invitation.recipient_email}</p>
                </div>
                <span className="text-xs font-bold text-gray-500">{!invitation.is_active ? 'Wyłączone' : invitation.submission_status ? recruitmentStatusLabel[invitation.submission_status] : 'Niewykorzystane'}</span>
                <div className="flex gap-2">
                  <button onClick={() => copyLink(invitation.token)} className="rounded-lg bg-indigo-50 px-3 py-2 text-xs font-bold text-indigo-700">{copiedToken === invitation.token ? 'Skopiowano' : 'Kopiuj'}</button>
                  {invitation.is_active && !invitation.submission_id && <button onClick={() => window.confirm('Wyłączyć ten link?') && invitations.revoke.mutate(invitation.id)} className="rounded-lg bg-rose-50 px-3 py-2 text-xs font-bold text-rose-700">Wyłącz</button>}
                </div>
              </article>
            ))}
          </div>
        )}
      </div>

      <div className="mb-4 flex items-center justify-between gap-3">
        <div>
          <h2 className="text-xl font-bold text-gray-900">Pytania w formularzu</h2>
          <p className="text-sm text-gray-500">Zmiany pojawią się od razu w publicznym formularzu.</p>
        </div>
        <button onClick={() => setEditing(null)} className="shrink-0 rounded-lg bg-emerald-600 px-4 py-2 text-sm font-bold text-white">+ Dodaj pole</button>
      </div>

      {isLoading ? (
        <div className="p-10 text-center text-gray-400">Ładowanie…</div>
      ) : (
        <div className="space-y-3">
          {data.map((field, index) => (
            <article key={field.id} className={`rounded-xl border p-4 ${field.is_active ? 'border-gray-200 bg-white' : 'border-dashed border-gray-300 bg-gray-50 opacity-70'}`}>
              <div className="flex flex-col gap-4 sm:flex-row sm:items-center">
                <div className="flex min-w-0 flex-1 gap-3">
                  <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-gray-100 text-sm font-black text-gray-500">{index + 1}</span>
                  <div className="min-w-0">
                    <div className="flex flex-wrap items-center gap-2">
                      <h3 className="font-bold text-gray-900">{field.label}</h3>
                      {field.required && <span className="rounded bg-rose-100 px-2 py-0.5 text-[10px] font-bold uppercase text-rose-700">Wymagane</span>}
                      {field.is_system && <span className="rounded bg-blue-100 px-2 py-0.5 text-[10px] font-bold uppercase text-blue-700">Podstawowe</span>}
                      {!field.is_active && <span className="rounded bg-gray-200 px-2 py-0.5 text-[10px] font-bold uppercase text-gray-600">Ukryte</span>}
                    </div>
                    <p className="mt-1 text-sm text-gray-500">{typeLabels[field.field_type]}{field.options.length ? ` · ${field.options.join(' / ')}` : ''}</p>
                  </div>
                </div>
                <div className="flex flex-wrap gap-2 sm:justify-end">
                  <button disabled={index === 0 || reorder.isPending} onClick={() => move(field, -1)} className="rounded-lg border px-3 py-2 text-xs font-bold text-gray-500 disabled:opacity-30" aria-label="Przenieś wyżej">↑</button>
                  <button disabled={index === data.length - 1 || reorder.isPending} onClick={() => move(field, 1)} className="rounded-lg border px-3 py-2 text-xs font-bold text-gray-500 disabled:opacity-30" aria-label="Przenieś niżej">↓</button>
                  {!field.is_system && <button onClick={() => update.mutate({ id: field.id, data: { is_active: !field.is_active } })} className="rounded-lg border px-3 py-2 text-xs font-bold text-gray-600">{field.is_active ? 'Ukryj' : 'Pokaż'}</button>}
                  <button onClick={() => setEditing(field)} className="rounded-lg bg-indigo-50 px-3 py-2 text-xs font-bold text-indigo-700">Edytuj</button>
                  {!field.is_system && <button onClick={() => window.confirm('Usunąć to pole? Zapisane odpowiedzi pozostaną w archiwum.') && remove.mutate(field.id)} className="rounded-lg bg-rose-50 px-3 py-2 text-xs font-bold text-rose-700">Usuń</button>}
                </div>
              </div>
            </article>
          ))}
        </div>
      )}

      {editing !== undefined && (
        <RecruitmentFieldModal
          field={editing}
          nextPosition={data.length}
          isPending={create.isPending || update.isPending}
          onClose={() => setEditing(undefined)}
          onSave={save}
        />
      )}
    </section>
  );
};

export default RecruitmentFormBuilderPage;
