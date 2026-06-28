# PAP-57 — analiza integracji z Google Calendar

- **Status:** spike / analiza techniczna
- **Data:** 2026-06-28
- **Zakres:** wyświetlanie wydarzeń z Google Calendar, zapis wydarzeń do Google Calendar oraz kalendarz A-PAULO możliwy do subskrybowania w Google Calendar.

## 1. Wniosek w skrócie

Integracja jest możliwa na kilka sposobów, ale nie wszystkie spełniają wymagania dotyczące prywatności i edycji.

**Rekomendowane rozwiązanie dla A-PAULO:** zbudować moduł Wydarzeń w A-PAULO i traktować bazę aplikacji jako źródło prawdy. Następnie udostępnić użytkownikowi:

1. kalendarz i edycję wydarzeń w aplikacji zgodnie z rolami A-PAULO;
2. indywidualny, odwoływalny adres subskrypcji iCalendar (`.ics`), który można dodać do Google Calendar;
3. opcjonalnie plik `.ics` dla pojedynczego wydarzenia.

Ten wariant nie wymaga logowania do Google w A-PAULO ani przechowywania danych kont Gmail. Jest niezależny od jednego dostawcy i pozwala zachować kontrolę dostępu po stronie aplikacji. Subskrypcja w Google jest jednak **jednokierunkowa i tylko do odczytu**: A-PAULO → Google Calendar.

Jeżeli w przyszłości wymagane będzie tworzenie wydarzeń bezpośrednio w Google albo synchronizacja dwukierunkowa, należy dodać drugi etap: integrację backendu A-PAULO z Google Calendar API przez OAuth 2.0.

## 2. Odpowiedzi na pytania ze spike'a

### 2.1. Czy można umieścić Google Calendar w aplikacji?

Tak. Google udostępnia kod `iframe`, który można wkleić na stronie. Widoczność nadal zależy od ustawień udostępniania kalendarza. Aby każdy odwiedzający mógł zobaczyć osadzony kalendarz bez logowania, kalendarz musi być publiczny ([Google Calendar Help — osadzanie kalendarza](https://support.google.com/calendar/answer/41207?hl=en)).

To rozwiązanie jest szybkie, ale ma istotne ograniczenia:

- wygląd i zachowanie kontroluje Google, więc integracja z UI A-PAULO jest ograniczona;
- prywatny kalendarz wymaga, aby użytkownik był zalogowany do właściwego konta Google i miał nadany dostęp;
- publiczny kalendarz może być odnaleziony i subskrybowany przez osoby spoza organizacji; można ujawnić pełne szczegóły albo tylko dostępność ([Google Calendar Help — kalendarze publiczne](https://support.google.com/calendar/answer/37083?hl=en-GB));
- `iframe` nie daje aplikacji własnego mechanizmu tworzenia i edycji wydarzeń.

**Ocena:** dobre wyłącznie dla publicznego kalendarza ogólnych wydarzeń PaP, bez danych osobowych i informacji wewnętrznych. Nie powinno być podstawą przyszłego modułu Wydarzeń.

### 2.2. Czy wystarczy sam link, bez danych logowania do Gmaila?

Tak, ale tylko w określonych wariantach.

#### Publiczny link lub publiczny iCal

Publiczny Google Calendar może udostępniać link WWW i publiczny adres iCal. Taki kalendarz można wyświetlić lub pobrać bez logowania. Google pozwala również dodać publiczny kalendarz przez **Inne kalendarze → Z adresu URL** ([instrukcja subskrypcji](https://support.google.com/calendar/answer/37100?hl=en-uk)).

Konsekwencją jest publiczna dostępność danych. Ten wariant nadaje się tylko do treści, które mogą zostać ujawnione w Internecie.

#### Tajny adres iCal prywatnego kalendarza

Google udostępnia także „Secret address in iCal format”. Pozwala on odczytać prywatny kalendarz w innym programie bez interaktywnego logowania. Jest to dostęp **tylko do odczytu**. Google wyraźnie zaleca, aby nie udostępniać tego adresu innym osobom i zresetować go po wycieku ([Google Calendar Help — tajny adres iCal](https://support.google.com/calendar/answer/37648?hl=en-GB)).

Taki link działa jak hasło:

- nie może trafić do kodu frontendu, repozytorium, logów ani analityki;
- jeżeli A-PAULO miałoby go używać, powinien być zaszyfrowany i odczytywany wyłącznie przez backend;
- nie pozwala dodawać ani zmieniać wydarzeń w Google Calendar;
- administrator Google Workspace może wyłączyć możliwość pobrania tajnego adresu.

**Ocena:** technicznie możliwe do prostego importu Google → A-PAULO, ale słabe jako rozwiązanie docelowe. Jeden wyciek ujawnia cały dostępny kalendarz, a uprawnień nie da się dopasować do ról A-PAULO.

### 2.3. Czy po zalogowaniu można wyświetlać i zapisywać wydarzenia Google?

Tak. Google Calendar API obsługuje odczyt listy wydarzeń oraz ich tworzenie. Odczyt może używać ograniczonych zakresów, np. `calendar.events.owned.readonly`, a zapis do kalendarzy należących do autoryzowanego konta — `calendar.events.owned`. Jeżeli aplikacja sama tworzy dodatkowy kalendarz Google, jeszcze węższym wariantem jest `calendar.app.created`. Szeroki zakres `calendar.events`, obejmujący wydarzenia ze wszystkich dostępnych kalendarzy, powinien być ostatecznością ([Events: list](https://developers.google.com/workspace/calendar/api/v3/reference/events/list), [Events: insert](https://developers.google.com/workspace/calendar/api/v3/reference/events/insert)).

Nie należy jednak zbierać ani przechowywać loginu i hasła Gmail. Poprawnym mechanizmem jest OAuth 2.0:

1. administrator lub użytkownik zostaje przekierowany na stronę Google;
2. loguje się bezpośrednio w Google i świadomie zatwierdza wymagane uprawnienia;
3. backend A-PAULO otrzymuje tokeny, a nie hasło;
4. przy dostępie działającym bez obecności użytkownika backend przechowuje bezpiecznie token odświeżania uzyskany w trybie `offline` ([OAuth 2.0 dla aplikacji serwerowych](https://developers.google.com/identity/protocols/oauth2/web-server)).

Zakresy trzeba ograniczyć do minimum zgodnie z zasadą least privilege ([zakresy Google Calendar API](https://developers.google.com/workspace/calendar/api/auth)). Dla rekomendowanego, dedykowanego konta PaP punktem wyjścia powinien być `calendar.events.owned`; szerszy zakres wymaga osobnego uzasadnienia. Tokeny muszą być szyfrowane w spoczynku, niedostępne dla frontendu i możliwe do unieważnienia.

Integracja OAuth wiąże się z dodatkową konfiguracją projektu Google Cloud, ekranu zgody oraz — zależnie od rodzaju konta, odbiorców i żądanych zakresów — procesem weryfikacji aplikacji. Jest to rozwiązanie o większym koszcie implementacji i utrzymania.

### 2.4. Czy można stworzyć kalendarz w A-PAULO i dodać go do Google Calendar?

Tak. A-PAULO może generować kalendarz w standardzie iCalendar zdefiniowanym przez [RFC 5545](https://www.rfc-editor.org/rfc/rfc5545). Użytkownik dostaje adres HTTPS zwracający zawartość `.ics` i dodaje go w Google Calendar jako kalendarz z adresu URL.

Warianty:

- **subskrypcja kalendarza** — wiele wydarzeń, późniejsze zmiany pobierane okresowo przez Google;
- **pobranie pojedynczego pliku `.ics`** — użytkownik dodaje kopię jednego wydarzenia, bez późniejszej synchronizacji.

Ograniczenia subskrypcji:

- jest jednokierunkowa; edycja kopii po stronie Google nie aktualizuje A-PAULO;
- Google decyduje, kiedy ponownie pobrać feed, więc zmiany nie muszą pojawić się natychmiast;
- oficjalna instrukcja Google gwarantuje dodawanie z URL dla kalendarzy publicznych. Adres z trudnym do odgadnięcia tokenem jest popularnym sposobem ochrony feedu, ale należy potwierdzić jego działanie w krótkim PoC na docelowych kontach Google;
- URL subskrypcji jest sekretem typu bearer: każdy, kto go pozna, może odczytać feed. Powinien być losowy, odwoływalny i możliwy do wygenerowania ponownie;
- unieważnienie URL zatrzymuje kolejne pobrania, ale nie usuwa wydarzeń ani ich kopii zapisanych wcześniej po stronie Google lub użytkownika. Feed nie może więc zawierać danych wrażliwych.

## 3. Porównanie wariantów

| Wariant | Bez logowania Google w A-PAULO | Dane prywatne | Odczyt | Zapis do Google | Kierunek | Złożoność |
|---|:---:|:---:|:---:|:---:|---|---|
| Publiczny `iframe` Google | Tak | Nie | Tak | Nie | Google → widok | Niska |
| Publiczny Google iCal/link | Tak | Nie | Tak | Nie | Google → odbiorca | Niska |
| Tajny Google iCal | Tak, po podaniu linku | Tylko przez tajność URL | Tak | Nie | Google → A-PAULO | Niska/średnia |
| Google Calendar API + OAuth | Jednorazowa zgoda Google wymagana | Tak | Tak | Tak | Jedno- lub dwukierunkowo | Średnia/wysoka |
| Service account + delegacja domenowa | Tak dla użytkownika końcowego | Tak | Tak | Tak | Jedno- lub dwukierunkowo | Wysoka; wymaga Google Workspace |
| **Moduł A-PAULO + feed iCalendar** | **Tak** | **W aplikacji: tak; w eksporcie: tylko zminimalizowane, niewrażliwe dane** | **Tak** | **Nie, Google subskrybuje tylko do odczytu** | **A-PAULO → Google** | **Średnia** |

## 4. Rekomendowana architektura

### Etap 1 — moduł Wydarzeń w A-PAULO

Źródłem prawdy powinna być baza PostgreSQL A-PAULO. Moduł należy zbudować zgodnie z istniejącą architekturą warstwową:

```text
frontend /events
        │
        ▼
backend/modules/events
  api → services → repositories → PostgreSQL
        │
        └── generator iCalendar → /api/v1/calendar-feeds/{token}.ics
                                      │
                                      └── subskrypcja w Google Calendar
```

Minimalny model wydarzenia powinien zawierać co najmniej: tytuł, opis, początek, koniec, strefę czasową, lokalizację, cykliczność, status, autora oraz zakres widoczności. Dostęp do listy i edycji należy powiązać z przyszłym RBAC oraz grupami.

Feed powinien:

- być generowany na backendzie jako poprawny `text/calendar; charset=utf-8`;
- mieć stabilne identyfikatory `UID` i poprawnie aktualizować `DTSTAMP`/`SEQUENCE`;
- używać UTC lub jednoznacznie określonej strefy `Europe/Warsaw`;
- być dostępny wyłącznie przez HTTPS;
- korzystać z kryptograficznie losowego tokenu zapisanego w postaci hasha;
- umożliwiać unieważnienie i wygenerowanie nowego adresu;
- maskować token i pełny URL w logach aplikacji, Rendera, reverse proxy, monitoringu błędów i analityce;
- wyłączyć przechowywanie odpowiedzi przez współdzielone cache (`Cache-Control: private, no-store`);
- publikować tylko pola potrzebne odbiorcy.

Nie należy umieszczać w feedzie publicznym ani możliwym do przekazania dalej: nazwisk podopiecznych, adresów domowych, numerów telefonów, danych zdrowotnych, prywatnych notatek ani szczegółów opieki. Bezpieczniejsze są neutralne tytuły oraz link prowadzący po zalogowaniu do szczegółów w A-PAULO. Rotacja tokenu ogranicza przyszły dostęp, ale nie wycofuje danych już pobranych przez zewnętrzny kalendarz.

### Etap 2 — opcjonalny Google Calendar API

Ten etap jest uzasadniony dopiero, gdy właściciel produktu potwierdzi wymaganie edycji w Google albo synchronizacji dwukierunkowej.

Proponowany wariant:

- osobny kalendarz organizacyjny PaP, nie prywatny kalendarz konkretnego wolontariusza;
- jednorazowa autoryzacja OAuth przez konto administracyjne organizacji;
- przepływ OAuth wyłącznie przez backend FastAPI;
- token odświeżania zaszyfrowany w bazie lub bezpiecznym magazynie sekretów;
- mapowanie `A-PAULO event id ↔ Google event id` oraz obsługa konfliktów;
- początkowa pełna synchronizacja, a następnie synchronizacja przyrostowa przez `syncToken` ([dokumentacja synchronizacji](https://developers.google.com/workspace/calendar/api/guides/sync));
- opcjonalne powiadomienia webhook. Kanały powiadomień wygasają i trzeba je odnawiać, więc zwiększają koszt utrzymania ([push notifications](https://developers.google.com/workspace/calendar/api/guides/push)).

Przed implementacją trzeba jednoznacznie ustalić właściciela danych i regułę konfliktu, np. „ostatnia zmiana wygrywa” albo „A-PAULO zawsze wygrywa”. Bez tej decyzji synchronizacja dwukierunkowa może nadpisywać dane w sposób niezrozumiały dla użytkownika.

### Kiedy użyć service account?

Service account nie jest zamiennikiem zwykłego logowania dla dowolnego konta Gmail. Dostęp do kalendarzy domeny bez danych użytkownika jest przeznaczony dla Google Workspace i wymaga skonfigurowanej przez administratora delegacji w całej domenie ([Google Calendar API — domain-wide delegation](https://developers.google.com/workspace/calendar/api/concepts/domain)).

Należy go rozważyć tylko wtedy, gdy PaP posiada zarządzaną domenę Google Workspace i jej administrator świadomie zatwierdzi takie uprawnienia. W innym przypadku prostszy będzie OAuth na dedykowanym koncie organizacji.

## 5. Proponowany PoC przed modułem Wydarzeń

Krótki PoC powinien potwierdzić ryzyka, których nie rozstrzyga sama dokumentacja:

1. utworzyć przykładowy feed `.ics` z trzema wydarzeniami: jednorazowym, całodniowym i cyklicznym;
2. sprawdzić odpowiedź przez `curl`: status `200`, `Content-Type: text/calendar; charset=utf-8` i `Cache-Control: private, no-store`;
3. dodać feed przez URL do zwykłego konta Gmail oraz — jeżeli organizacja używa — konta Google Workspace;
4. potwierdzić, że Google pobiera adres zawierający losowy token i poprawnie aktualizuje zmienione wydarzenie;
5. sprawdzić kodowanie polskich znaków, strefę `Europe/Warsaw`, zmianę czasu oraz wydarzenia całodniowe;
6. zmierzyć rzeczywiste opóźnienie od zmiany w feedzie do jej pojawienia się w Google;
7. przejrzeć logi aplikacji, hostingu i monitoringu oraz potwierdzić, że nie zawierają tokenu ani pełnego URL feedu;
8. zresetować token i potwierdzić, że poprzedni URL przestaje zwracać dane;
9. potwierdzić, że rotacja tokenu nie usuwa kopii wydarzeń już pobranych przez Google, i uwzględnić to w komunikacie dla użytkownika;
10. potwierdzić minimalny bezpieczny zestaw pól z osobą odpowiedzialną za ochronę danych.

### Jak właściciel zadania może zweryfikować wnioski

Bez implementowania modułu Wydarzeń można ręcznie potwierdzić dwa warianty Google:

1. Utworzyć testowy kalendarz bez danych prawdziwych osób i dodać dwa fikcyjne wydarzenia.
2. Ustawić go jako publiczny, skopiować kod osadzenia i otworzyć podgląd w oknie incognito. Kalendarz powinien być widoczny bez logowania.
3. Skopiować publiczny adres iCal i w Google Calendar na komputerze wybrać **Inne kalendarze → + → Z adresu URL**. Wydarzenia powinny pojawić się jako kalendarz tylko do odczytu.
4. Cofnąć publiczne udostępnienie i potwierdzić w incognito, że publiczny dostęp przestał działać. Google zaznacza, że propagacja zmiany ustawień może potrwać kilka godzin.
5. Dla prywatnego kalendarza skopiować „Secret address in iCal format”, pobrać go testowo, następnie użyć opcji resetowania adresu i potwierdzić, że stary URL przestał działać. Nie wykonywać tego testu na kalendarzu zawierającym prawdziwe dane.

Rekomendowanego wariantu A-PAULO → Google nie da się w pełni zweryfikować samym dokumentem, ponieważ endpoint `.ics` jeszcze nie istnieje. Kryterium zakończenia osobnego PoC stanowi zaliczenie wszystkich dziesięciu punktów powyżej na zwykłym Gmailu i — jeśli jest używany przez PaP — Google Workspace.

### Zaimplementowany PoC osadzenia

Na branchu `pap-57` dodano chroniony widok `/events`, dostępny z pozycji **Wydarzenia** w menu aplikacji. Widok osadza publiczny kalendarz `projektapaulo@gmail.com` przez oficjalny `iframe` Google.

Aby zweryfikować PoC:

1. uruchomić frontend poleceniem `npm run dev` w katalogu `frontend`;
2. zalogować się do A-PAULO;
3. wybrać **Wydarzenia** w bocznym menu;
4. potwierdzić, że kalendarz i utworzone w nim wydarzenia testowe są widoczne;
5. powtórzyć test w wąskim widoku mobilnym i sprawdzić, czy iframe nie wychodzi poza kartę;
6. wylogować się i potwierdzić, że bez sesji wejście na `/events` przekierowuje do `/login`.

Ten PoC potwierdza jedynie możliwość osadzenia publicznego kalendarza. Nie potwierdza prywatnej subskrypcji `.ics`, zapisu przez OAuth ani synchronizacji dwukierunkowej i nie zmienia docelowej rekomendacji architektonicznej.

## 6. Decyzja dla PAP-57

1. **Nie używać publicznego `iframe` jako docelowego modułu Wydarzeń.** Można go użyć jedynie do kalendarza całkowicie publicznych wydarzeń PaP.
2. **Nie przechowywać loginu ani hasła Gmail.** Jeśli powstanie integracja API, stosować OAuth 2.0 i trzymać tokeny wyłącznie na backendzie.
3. **Na pierwszy etap wybrać własny moduł Wydarzeń + iCalendar.** Zapewnia najmniejszy koszt, kontrolę uprawnień i brak zależności logowania od Google.
4. **Google Calendar API pozostawić jako etap drugi.** Wdrożyć tylko po potwierdzeniu potrzeby zapisu lub synchronizacji dwukierunkowej.
5. **Przeprowadzić mały PoC feedu przed estymacją implementacji**, szczególnie dla prywatnego tokenizowanego URL i opóźnienia odświeżania przez Google.

## 7. Źródła

- [Google Calendar Help — osadzanie kalendarza na stronie](https://support.google.com/calendar/answer/41207?hl=en)
- [Google Calendar Help — publiczne kalendarze i adres iCal](https://support.google.com/calendar/answer/37083?hl=en-GB)
- [Google Calendar Help — dodawanie kalendarza z URL](https://support.google.com/calendar/answer/37100?hl=en-uk)
- [Google Calendar Help — tajny adres iCal](https://support.google.com/calendar/answer/37648?hl=en-GB)
- [Google Calendar API — lista wydarzeń](https://developers.google.com/workspace/calendar/api/v3/reference/events/list)
- [Google Calendar API — tworzenie wydarzeń](https://developers.google.com/workspace/calendar/api/v3/reference/events/insert)
- [Google Calendar API — zakresy OAuth](https://developers.google.com/workspace/calendar/api/auth)
- [Google Identity — OAuth 2.0 dla aplikacji serwerowych](https://developers.google.com/identity/protocols/oauth2/web-server)
- [Google Calendar API — synchronizacja przyrostowa](https://developers.google.com/workspace/calendar/api/guides/sync)
- [Google Calendar API — powiadomienia push](https://developers.google.com/workspace/calendar/api/guides/push)
- [Google Calendar API — service account i delegacja domenowa](https://developers.google.com/workspace/calendar/api/concepts/domain)
- [RFC 5545 — iCalendar](https://www.rfc-editor.org/rfc/rfc5545)
