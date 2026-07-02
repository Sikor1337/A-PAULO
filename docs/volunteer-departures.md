# Ankiety odejścia wolontariuszy (PAP-29)

Mechanizm znajduje się w module backendowym `recruitment`, ale jest rozdzielony
od rekrutacji kandydatów na osobne pliki `departures.py`, `departure.py`,
`departure_constants.py` i `departure_dependencies.py` w odpowiednich warstwach.

## Przepływ

1. Pracownik otwiera aktywnego wolontariusza i wybiera „Oznacz odejście”.
2. Wypełnia dynamiczną ankietę, w tym datę, powód oraz zgodę na dalszy kontakt.
3. Backend zapisuje migawkę pytań i odpowiedzi, ustawia status wolontariusza na
   `Były` oraz dopisuje zdarzenie do historii.
4. Ankiety są dostępne w zakładce `Rekrutacja → Odejścia`.

Na jednego wolontariusza przypada jedna ankieta odejścia. Relacja używa
`ON DELETE RESTRICT`, żeby usunięcie wolontariusza nie skasowało dokumentacji
odejścia. Pytania można edytować zbiorczo; pola systemowe zachowują swój typ,
wymagalność i aktywność.

## Endpointy

- `GET/PUT /api/v1/recruitment/departures/fields`
- `GET/POST /api/v1/recruitment/departures`
- `GET /api/v1/recruitment/departures/{id}`

Odczyt pól i ankiet wymaga `CAN_VIEW_RECRUITMENT`. Zmiana pytań oraz zapis
ankiety wymagają `CAN_MANAGE_RECRUITMENT`. Migracja `pap29_departures` jest
bezpośrednim następcą baseline PAP-69.
