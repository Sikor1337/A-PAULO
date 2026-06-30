# Architektura Frontendu

## Stan serwerowy i cache

- React Query obsługuje dane pobierane z backendu.
- Aplikacja używa jednej instancji `QueryClient` z
  `frontend/src/lib/queryClient.ts`.
- Komponenty i store nie powinny tworzyć dodatkowych globalnych klientów.

## Cykl sesji użytkownika

- `useAuthStore.logout()` jest wspólnym punktem ręcznego i automatycznego
  wylogowania.
- Logout usuwa tokeny, profil użytkownika, cały Query Cache i aktywne komunikaty
  o uruchamianiu backendu.
- Każde rozpoczęcie lub zakończenie sesji zwiększa rewizję sesji. Odpowiedź z
  rozpoczętego wcześniej odświeżania tokenu nie może zapisać tokenów do nowej
  lub zakończonej sesji.
- Nowe ścieżki wylogowania muszą wywoływać akcję store zamiast samodzielnie
  usuwać wybrane klucze z `localStorage`.

## Obsługa zimnego startu backendu

- Wszystkie klienty Axios komunikujące się z backendem używają interceptorów z
  `frontend/src/lib/backendWakeup.ts`.
- Po pięciu sekundach oczekiwania na pierwsze dane odpowiedzi pokazywany jest
  globalny popup informujący o zimnym starcie Rendera.
- Dla multipart uploadu czas odpowiedzi jest liczony dopiero po wysłaniu pliku.
- Pierwszy odebrany fragment odpowiedzi zamyka popup; czas pobierania całego
  pliku nie jest traktowany jako uruchamianie serwera.
- Przy wielu równoległych wolnych requestach popup znika dopiero po odpowiedzi
  ostatniego z nich.

## Responsywność i dostępność

- Globalny popup musi mieścić się na małych ekranach bez poziomego przewijania.
- Komunikat korzysta z `role="status"` i `aria-live="polite"`, aby był ogłaszany
  przez technologie asystujące bez przejmowania fokusu.
- Pozostałe zasady układu opisuje `frontend-responsive-layout.md`.

## Testowanie

- Logout należy testować zarówno bezpośrednio w store, jak i przez automatyczną
  ścieżkę błędu autoryzacji.
- Interceptory wolnych requestów należy testować na instancji Axios z kontrolowaną
  odpowiedzią, w tym dla pierwszego bajtu i multipart uploadu.
- Przed mergem wymagane są: `npm test`, `npm run lint` i `npm run build`.
