# PAP-49 — moduł Wydarzeń i iCalendar

## Architektura backendu

Moduł znajduje się w `backend/app/modules/calendar/` i zachowuje standardowy
podział `api → services → repositories → models`. PostgreSQL jest źródłem
prawdy. Google Calendar jest wyłącznie jednokierunkowym odbiorcą feedu.

Główne tabele:

- `calendar_events` — treść, termin, strefa, cały dzień, RRULE, widoczność,
  autor, stabilny UID, SEQUENCE i daty audytowe;
- `calendar_feed_tokens` — jeden aktywny token na użytkownika, zapisany tylko
  jako SHA-256;
- `calendar_audit` — utworzenie, edycja, anulowanie, usunięcie wydarzenia oraz
  wygenerowanie/unieważnienie tokenu.

Odczyt wymaga `CAN_VIEW_EVENTS`, a zmiany `CAN_MANAGE_EVENTS`. Widoczność
`admins` oznacza użytkowników z `CAN_MANAGE_EVENTS`, nie sztywną rolę. Backend
egzekwuje permissions niezależnie od frontendu.

## API

- `GET/POST /api/v1/calendar/events`
- `GET/PATCH/DELETE /api/v1/calendar/events/{id}`
- `POST /api/v1/calendar/events/{id}/cancel`
- `GET /api/v1/calendar/events/{id}.ics`
- `GET/POST/DELETE /api/v1/calendar/feed-token`
- `GET /api/v1/calendar-feeds/{token}.ics` — publiczny technicznie, chroniony
  sekretnym tokenem

Feed ma `text/calendar; charset=utf-8`, `Cache-Control: private, no-store`,
stabilne UID, DTSTAMP, SEQUENCE, RRULE i `STATUS:CANCELLED`. Daty godzinowe są
publikowane w UTC, co zachowuje jednoznaczność przy zmianach czasu; wydarzenia
całodniowe używają `VALUE=DATE`.

Feed nie publikuje opisu ani danych domenowych — tylko tytuł, termin,
lokalizację i dane techniczne. Tytuły i lokalizacje nie mogą zawierać danych
wrażliwych. Filtr `uvicorn.access` maskuje token w logach. Na produkcji należy
ustawić `ENVIRONMENT=production`; wtedy endpoint feedu odrzuca żądania HTTP.
Render musi przekazywać prawidłowy nagłówek protokołu proxy.

Jawny adres jest zwracany tylko podczas generowania. Rotacja zastępuje hash i
natychmiast unieważnia stary URL. Nie da się odtworzyć utraconego adresu bez
wygenerowania nowego. Odebranie właścicielowi tokenu `CAN_VIEW_EVENTS` również
natychmiast blokuje feed. Backend odrzuca daty bez jawnej strefy czasowej oraz
reguły RRULE zawierające niepoprawną składnię lub dodatkowe linie iCalendar.

## Frontend

Widok `/events` używa własnego responsywnego kalendarza miesięcznego i listy.
Obsługuje filtrowanie po statusie i widoczności, sortowanie po początku,
szczegóły, CRUD, anulowanie,
wydarzenia całodniowe i podstawowe reguły cykliczne. Akcje modyfikujące są
widoczne tylko z `CAN_MANAGE_EVENTS`.

Modal subskrypcji generuje i kopiuje prywatny URL oraz pokazuje instrukcję
Google Calendar. Informuje, że:

- subskrypcja jest tylko do odczytu;
- Google odświeża ją z opóźnieniem;
- adres należy chronić;
- reset nie usuwa kopii już pobranych przez zewnętrzny kalendarz;
- pojedynczy plik `.ics` jest importem bez późniejszej synchronizacji.

## Rozwój

Synchronizacja dwukierunkowa i OAuth Google pozostają poza etapem pierwszym.
Jeżeli zostaną dodane, nie powinny zmieniać zasady, że A-PAULO jest źródłem
prawdy, dopóki produkt nie zdefiniuje jawnej polityki konfliktów.
