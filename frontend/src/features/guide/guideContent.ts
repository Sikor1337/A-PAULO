/**
 * Static, per-module content for the in-app guide (PAP-75).
 *
 * Kept as plain data so it is trivial to extend as the product grows. Each
 * section maps to a module; `permission` (when set) hides the section from
 * users who cannot access that module, so the guide mirrors what a person can
 * actually see.
 */
import type { PermissionCode } from '@/types';

export interface GuideTopic {
  heading: string;
  body: string;
}

export interface GuideSection {
  key: string;
  icon: string;
  title: string;
  intro: string;
  topics: GuideTopic[];
  /** Show only to users who hold this permission (omit = always visible). */
  permission?: PermissionCode;
  /** Show only to these account statuses (omit = any). */
  adminOnly?: boolean;
}

export const guideSections: GuideSection[] = [
  {
    key: 'start',
    icon: '👋',
    title: 'Wprowadzenie',
    intro: 'A-PAULO to system do zarządzania wolontariatem: podopiecznymi, wolontariuszami, grupami, wydarzeniami i rekrutacją.',
    topics: [
      { heading: 'Nawigacja', body: 'Menu po lewej stronie pokazuje tylko te moduły, do których masz uprawnienia. Jeśli czegoś nie widzisz, poproś administratora o nadanie dostępu.' },
      { heading: 'Twoje konto', body: 'Kliknij swój awatar na dole menu, aby otworzyć „Moje konto”, ten przewodnik lub się wylogować.' },
      { heading: 'Wyszukiwanie i filtry', body: 'Większość list ma pole wyszukiwania oraz filtry (status, grupa, data). Kolumny można sortować, klikając nagłówek.' },
    ],
  },
  {
    key: 'beneficiaries',
    icon: '📄',
    title: 'Podopieczni',
    intro: 'Kartoteka osób objętych pomocą (podopiecznych).',
    permission: 'CAN_VIEW_BENEFICIARIES',
    topics: [
      { heading: 'Dodawanie i edycja', body: 'Przycisk „+ Dodaj” tworzy nowego podopiecznego. Kliknięcie wiersza otwiera szczegóły z historią zmian.' },
      { heading: 'Status', body: 'OBECNY, ZMARŁY, BYŁY lub DPS/ZOL. Pole „BO” oznacza objęcie Budżetem Obywatelskim.' },
      { heading: 'Import/eksport CSV', body: 'Możesz wgrać listę z pliku CSV lub wyeksportować bieżący widok do arkusza.' },
    ],
  },
  {
    key: 'volunteers',
    icon: '🙋',
    title: 'Wolontariusze',
    intro: 'Baza wolontariuszy wraz z funkcjami i historią współpracy.',
    permission: 'CAN_VIEW_VOLUNTEERS',
    topics: [
      { heading: 'Profil', body: 'Każdy wolontariusz ma e-mail, status (Aktywny/Były), datę dołączenia, funkcje i notatki.' },
      { heading: 'Przypisania', body: 'Wolontariusze są łączeni z podopiecznymi i grupami. Główny wolontariusz podopiecznego jest oznaczony osobno.' },
    ],
  },
  {
    key: 'groups',
    icon: '👥',
    title: 'Grupy',
    intro: 'Grupy A-PAULO koordynują pracę wolontariuszy przy podopiecznych.',
    permission: 'CAN_VIEW_PI_GROUPS',
    topics: [
      { heading: 'Skład grupy', body: 'Grupa ma lidera oraz wolontariuszy. Podopieczni są przypisywani do grupy.' },
      { heading: 'Karty BO', body: 'Do grupy można wgrywać karty BO (załączniki) powiązane z parą podopieczny–wolontariusz i okresem.' },
    ],
  },
  {
    key: 'recruitment',
    icon: '🧭',
    title: 'Rekrutacja',
    intro: 'Formularz rekrutacyjny kandydatów i proces wdrażania nowych wolontariuszy.',
    permission: 'CAN_VIEW_RECRUITMENT',
    topics: [
      { heading: 'Ankiety', body: 'Zakładka „Ankiety” pozwala edytować pytania formularza rekrutacyjnego oraz przeglądać odpowiedzi kandydatów.' },
      { heading: 'Wdrażanie', body: 'Zakładka „Wdrażanie” prowadzi kandydata przez wymagane spotkania, aż do akceptacji lub odrzucenia.' },
      { heading: 'Link dla kandydata', body: 'Rekrutacja korzysta z osobnego, prywatnego linku — to nie to samo co rejestracja konta w systemie.' },
    ],
  },
  {
    key: 'events',
    icon: '📅',
    title: 'Kalendarz i wydarzenia',
    intro: 'Wydarzenia całej organizacji w widoku miesięcznym i listowym.',
    permission: 'CAN_VIEW_EVENTS',
    topics: [
      { heading: 'Tworzenie wydarzeń', body: 'Osoby z uprawnieniami dodają wydarzenia z godziną (format 24-godzinny), lokalizacją i powtarzalnością.' },
      { heading: 'Widok listy', body: 'Przełącznik „Lista” pokazuje wydarzenia w wybranym zakresie dat — także z innych miesięcy.' },
      { heading: 'Subskrypcja .ics', body: 'Kalendarz można zasubskrybować w Google Calendar przez prywatny link (tylko do odczytu).' },
    ],
  },
  {
    key: 'departments',
    icon: '🗂️',
    title: 'Działy',
    intro: 'Działy grupują wolontariuszy wokół konkretnych obszarów pracy.',
    permission: 'CAN_VIEW_DEPARTMENTS',
    topics: [
      { heading: 'Dołączanie', body: 'Wejdź w dział i kliknij „Dołącz”. Twoja prośba czeka na akceptację osoby z uprawnieniami.' },
      { heading: 'Opuszczanie', body: 'W każdej chwili możesz opuścić dział przyciskiem „Opuść dział”.' },
      { heading: 'Zarządzanie', body: 'Osoby zarządzające zatwierdzają prośby, dodają i usuwają członków oraz archiwizują działy (bez trwałego usuwania).' },
    ],
  },
  {
    key: 'tasks',
    icon: '📋',
    title: 'Zadania',
    intro: 'Zadania z checklistą, przypisaniami i śledzeniem postępu.',
    permission: 'CAN_VIEW_TASKS',
    topics: [
      { heading: 'Checklisty', body: 'Odhaczenie wszystkich punktów automatycznie kończy zadanie; ręczna zmiana statusu ma pierwszeństwo nad automatyką.' },
      { heading: 'Przypisania', body: 'Zadanie i pojedyncze punkty checklisty można przypisać konkretnym wolontariuszom, a całość powiązać z działem lub wydarzeniem.' },
    ],
  },
  {
    key: 'bug-reports',
    icon: '🐛',
    title: 'Zgłoś błąd',
    intro: 'Zgłaszanie problemów z platformą zespołowi technicznemu.',
    topics: [
      { heading: 'Nowe zgłoszenie', body: 'Opisz problem i opcjonalnie dołącz zrzut ekranu lub log. Swoje zgłoszenia widzisz na własnej liście.' },
      { heading: 'Obsługa', body: 'Osoby z odpowiednimi uprawnieniami zmieniają status i dodają komentarz rozwiązania.' },
    ],
  },
  {
    key: 'departure',
    icon: '🚪',
    title: 'Ankieta odejścia',
    intro: 'Krótka ankieta wypełniana przy kończeniu współpracy.',
    topics: [
      { heading: 'Wypełnienie', body: 'Odpowiedz na pytania i wyślij ankietę. Po wysłaniu możesz jeszcze poprawić swoje odpowiedzi.' },
    ],
  },
  {
    key: 'settings',
    icon: '⚙️',
    title: 'Ustawienia i administracja',
    intro: 'Zarządzanie użytkownikami, grupami uprawnień i bezpieczeństwem.',
    adminOnly: true,
    topics: [
      { heading: 'Użytkownicy', body: 'Twórz i edytuj konta oraz przypisuj je do grup uprawnień.' },
      { heading: 'Grupy i uprawnienia', body: 'Uprawnienia nadaje się przez grupy. Grupa systemowa STAFF jest edytowalna, aby np. wyłączyć wybrane moduły testerom.' },
      { heading: 'Historia zmian', body: 'Kluczowe operacje są rejestrowane w audycie — przycisk „Historia” pokazuje kto i co zmienił.' },
    ],
  },
];
