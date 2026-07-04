# Ankiety odejścia wolontariuszy (PAP-29)

Mechanizm znajduje się w module backendowym `recruitment`, ale jest rozdzielony
od rekrutacji kandydatów na osobne pliki `departures.py`, `departure.py`,
`departure_constants.py` i `departure_dependencies.py` w odpowiednich warstwach.

## Przepływ

1. Wolontariusz otrzymuje informację, żeby przed odejściem zalogować się do
   platformy i otworzyć pozycję `Ankieta odejścia`.
2. Samodzielnie wypełnia dynamiczną ankietę i ją wysyła.
3. Backend ustala profil wolontariusza na podstawie zaakceptowanego zgłoszenia
   rekrutacyjnego, a dla starszych kont na podstawie zgodnego adresu e-mail.
   Identyfikator wolontariusza nie pochodzi z danych wysyłanych przez przeglądarkę.
4. Backend zapisuje migawkę pytań i odpowiedzi, ustawia status wolontariusza na
   `Były` oraz dopisuje zdarzenie do historii.
5. Pracownicy konfigurują pytania i oglądają przesłane ankiety w zakładce
   `Rekrutacja → Odejścia`. Nie mogą wypełniać ankiety za wolontariusza.

Na jednego wolontariusza przypada jedna ankieta odejścia. Relacja używa
`ON DELETE RESTRICT`, żeby usunięcie wolontariusza nie skasowało dokumentacji
odejścia. Pytania można edytować zbiorczo; pola systemowe zachowują swój typ,
wymagalność i aktywność.

## Endpointy

- `GET/PUT /api/v1/recruitment/departures/fields`
- `GET /api/v1/recruitment/departures`
- `GET /api/v1/recruitment/departures/{id}`
- `GET /api/v1/recruitment/departures/me`
- `POST /api/v1/recruitment/departures/me`

Odczyt administracyjny pól i ankiet wymaga `CAN_VIEW_RECRUITMENT`, a zmiana
pytań `CAN_MANAGE_RECRUITMENT`. Endpointy `/me` wymagają zalogowanego konta i
zawsze działają wyłącznie na przypisanym do niego wolontariuszu. Migracja
`pap29_departures` jest bezpośrednim następcą baseline PAP-69.
