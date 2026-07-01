# Dostęp do ankiety rekrutacyjnej

## Dwa niezależne sposoby rejestracji

- Zwykła rejestracja w aplikacji tworzy konto ze statusem `regular` i prowadzi
  użytkownika do panelu.
- Rejestracja rozpoczęta przez link rekrutacyjny przekazuje do backendu token i
  tworzy konto ze statusem `new_volunteer`. Takie konto musi wypełnić ankietę.

Frontend zapamiętuje kontekst linku w `sessionStorage` podczas przejścia przez
rejestrację i logowanie. Nie kieruje kont `regular` ani `admin` do ankiety, a
token nie przechodzi przypadkowo do późniejszej sesji innej osoby.

## Stały link

Link ma postać `/recrutation/<token>`. Token jest stabilnym HMAC wyliczanym z
backendowego `SECRET_KEY`, dzięki czemu nie trzeba przechowywać go w bazie ani
ujawniać struktury endpointów w publicznym adresie. Token używa wyłącznie znaków
bezpiecznych dla URL. Zmiana `SECRET_KEY` celowo unieważnia poprzedni link.

Backend zwraca ścieżkę uprawnionym użytkownikom przez
`GET /api/v1/recruitment/access-link`. Pobranie i wysłanie ankiety wymaga tokenu
w nagłówku `X-Recruitment-Token` oraz konta `new_volunteer`.

## Kontrola wdrożenia

Test integracyjny sprawdza router rzeczywistej aplikacji `app.main`, w tym
`/api/v1/recruitment/fields`. Jeżeli produkcja zwraca dla tej ścieżki 404, mimo
że test przechodzi dla wdrażanego commita, uruchomiona jest starsza wersja
backendu i usługę Render trzeba ponownie zbudować z właściwego brancha/commita.

Lista zgłoszeń normalizuje również historyczne odpowiedzi zapisane jako obiekt
JSON. Pojedynczy rekord ze starego formatu nie powoduje już odpowiedzi 500 dla
całego `GET /api/v1/recruitment/submissions`.
