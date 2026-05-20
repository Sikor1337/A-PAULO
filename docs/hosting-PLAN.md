# Propozycja Hostingu

## Spis treści
- [Propozycja Hostingu](#propozycja-hostingu)
  - [Spis treści](#spis-treści)
  - [1. Wymagania i charakterystyka projektu](#1-wymagania-i-charakterystyka-projektu)
  - [2. Hosting Backendu](#2-hosting-backendu)
    - [Najlepsze polecane alternatywy dla backendu](#najlepsze-polecane-alternatywy-dla-backendu)
      - [Oracle Cloud (OCI) – Always Free VM](#oracle-cloud-oci--always-free-vm)
      - [Google Cloud Run](#google-cloud-run)
      - [Render (Free Tier)](#render-free-tier)
    - [Opcje odrzucone lub problematyczne](#opcje-odrzucone-lub-problematyczne)
      - [PythonAnywhere (Free)](#pythonanywhere-free)
      - [Fly.io](#flyio)
      - [Azure Functions](#azure-functions)
  - [3. Hosting Frontendu](#3-hosting-frontendu)
    - [Cloudflare Pages](#cloudflare-pages)
    - [Azure Static Web Apps](#azure-static-web-apps)
    - [GitHub Pages](#github-pages)
    - [Netlify / Vercel](#netlify--vercel)
  - [4. Hosting Bazy Danych SQL](#4-hosting-bazy-danych-sql)
    - [Neon (Serverless PostgreSQL)](#neon-serverless-postgresql)
    - [Aiven Free Tier (PostgreSQL / MySQL)](#aiven-free-tier-postgresql--mysql)
    - [Supabase](#supabase)
  - [5. Hosting Danych (Storage)](#5-hosting-danych-storage)
    - [Cloudflare R2](#cloudflare-r2)
    - [Supabase Storage](#supabase-storage)
    - [Wybór](#wybór)

---

## 1. Wymagania i charakterystyka projektu
* **Budżet:** Darmowy (na stałe, bez wygasających kredytów po 3-6 miesiącach).
* **Ruch:** kilka osób, kilkadziesiąt zapytań dziennie.
* **Kluczowy warunek:** Maksymalne zminimalizowanie ryzyka niespodziewanych kosztów (ochrona przed DDoS / złośliwym ruchem).

## 2. Hosting Backendu

### Najlepsze polecane alternatywy dla backendu

#### Oracle Cloud (OCI) – Always Free VM
**Co to jest**
Pełnoprawny serwer VPS (wirtualna maszyna) oferujący najlepszą wydajność w darmowym pakiecie w modelu serwera.

**Darmowy plan (istotne fakty)**
* Do 4 OCPU i 24 GB RAM w architekturze ARM (Ampere A1) – można rozdzielić na kilka instancji.
* Opcjonalnie do 2 mikro instancji x86 (VM.Standard.E2.1.Micro).
* 200 GB darmowego miejsca na dysku (Boot + Block Volume).

**Mocne strony**
* Najwyższe bezpieczeństwo finansowe - w razie ataku DDoS koszty nie rosną, instancja po prostu wyczerpie darmowe zasoby CPU i przestanie odpowiadać, nie generując rachunku.
* Najhojniejsze zasoby w kategorii darmowej: 4 OCPU + 24 GB RAM (ARM) to więcej niż jakakolwiek konkurencja w tym przedziale cenowym.
* Pełna kontrola nad serwerem - możesz uruchomić dowolny stos (Nginx, Caddy, Gunicorn, systemd) i konfigurować system jak na zwykłym VPS.

**Słabe strony / pułapki**
* Konieczne podpięcie karty kredytowej, co budzi obawy - Oracle jednak nie nalicza kosztów automatycznie za przekroczenie limitu darmowego; upgrade do płatnego wymaga ręcznego działania w panelu.
* Instancja ARM może zostać odebrana jeśli jest nieaktywna przez 7 kolejnych dni bez żadnego ruchu - wystarczy skonfigurować prosty cron job pingujący lokalnie endpoint, by temu zapobiec.
* Całość konfiguracji serwera (firewall OCI, SSL, reverse proxy, środowisko Python, zarządzanie procesami) leży po stronie dewelopera - wymaga znajomości Linuxa i jednorazowego nakładu pracy przy setupie.

**Kiedy wybrać**
* Gdy chcesz pełnoprawnego, darmowego serwera, nie boisz się konfiguracji i Linuxa.

---

#### Google Cloud Run
**Co to jest**
Zarządzana platforma serverless od Google (GCP), uruchamiająca aplikacje opakowane w kontenery Docker. Nie zarządzasz serwerem ani systemem operacyjnym - Google automatycznie skaluje liczbę instancji od zera w górę w zależności od liczby przychodzących żądań. Dobrze pasuje do Pythonowego backendu (np. FastAPI w Dockerze) bez angażowania się w DevOps.

**Darmowy plan (istotne fakty)**
* Free tier jest liczony miesięcznie i resetuje się co miesiąc
* 2 mln zapytań (requestów).
* 180 000 vCPU-sekund.

**Mocne strony**
* Prosty deploy z obrazu Docker - wystarczy `gcloud run deploy`, reszta jest zarządzana przez Google (OS, patche, load balancer).
* Automatyczne skalowanie do zera - gdy nikt nie używa aplikacji, nie płacisz nic (w ramach free tier).

**Słabe strony / pułapki**
* Masowy ruch atakujących może wygenerować wysokie rachunki - Cloud Run skaluje się automatycznie w górę bez limitu, co jest jego zaletą i jednocześnie pułapką kosztową. Można ustawić `--max-instances=1` aby ograniczyć skalowanie, ale wówczas przy dużym ruchu serwis staje się niedostępny zamiast skalować. Dla małych projektów z ryzykiem ataku jest to nieakceptowalne ryzyko bez dodatkowej konfiguracji (Cloud Armor, budget alerts).

**Kiedy wybrać**
* Kiedy Twoja aplikacja jest zkonteneryzowana (Docker), a ruch charakteryzuje się ogromnymi pikami w krótkim czasie.

---

#### Render (Free Tier)
**Co to jest**
Platforma PaaS (Platform-as-a-Service) w stylu Heroku - po podpięciu repozytorium Git, każdy push buduje i deployuje aplikację automatycznie. Render zarządza serwerem, systemem operacyjnym i procesem uruchamiania aplikacji. Obsługuje Python (FastAPI, Django, Flask), Node.js i inne środowiska przez konfigurację w pliku `render.yaml` lub ręcznie w panelu.

**Darmowy plan (istotne fakty)**
* Zasoby są statyczne; darmowe instancje są usypiane już po 15 minutach braku ruchu.
* Darmowy Render Postgres w free wariancie ma expiry 30 dni od utworzenia

**Mocne strony**
* Prosty deploy bez konfiguracji serwera - wystarczy podpiąć repo Git, Render sam wykrywa środowisko (Python, Node.js) i buduje aplikację po każdym push.
* Statyczne zasoby (stałe CPU/RAM) oznaczają, że ataki DDoS nie generują dodatkowych kosztów - instancja po prostu wyczerpuje dostępne zasoby, nie skaluje się w górę.

**Słabe strony / pułapki**
* Zimne starty po uśpieniu trwają typowo 30-60 sekund dla pierwszego zapytania - każdy użytkownik wchodzący po przerwie czeka na odpowiedź przez ponad minutę. To dyskwalifikuje Render jako hosting produkcyjny przy jakichkolwiek wymaganiach UX.

**Kiedy wybrać**
* W zastosowaniu hobbystycznym lub do testowego API.

---

### Opcje odrzucone lub problematyczne

#### PythonAnywhere (Free)
**Słabe strony / pułapki**: Posiada obcięty oraz zablokowany outbound traffic (komunikacja do zewnątrz), utrudniający wdrożenia baz zewnętrzne np. w architekturze rozdzielnej.

#### Fly.io
**Słabe strony / pułapki**: Usługa usunęła plan darmowy dla nowo zakładanych kont - pozostają same zasilane kartą.

#### Azure Functions
**Słabe strony / pułapki**: Mikroarchitektura niosąca ukryte koszty za storage pomocniczy. Zbyt skomplikowana architektura wdrożeń dla bardzo małego API.

## 3. Hosting Frontendu

### Cloudflare Pages
**Co to jest**
Platforma do hostingu statycznych stron/aplikacji z CDN od Cloudflare na całą planetę.

**Darmowy plan (istotne fakty)**
* 500 buildów/miesiąc. 1 build na raz
* 100 custom domains per project
* Limity statycznych assetów: 25 MiB na plik oraz do 20,000 plików na site (Free).

**Mocne strony**
* Brak limitów ruchu dla zasobów statycznych (idealne dla ogromnych aplikacji Single Page z obrazkami).

**Słabe strony / pułapki**
* Limit 500 buildów - rygor ogranicza bardzo częste wrzucanie nowych poprawek z CI/CD.

**Kiedy wybrać**
* Hosting czystego SPA bez niespodzianek ruchowych na statyczne i ciężkie asety frontowe.

---

### Azure Static Web Apps
**Co to jest**
Platforma frontowa zintegrowana silnie w Microsoft Azure dla Angular/React.

**Darmowy plan (istotne fakty)**
* 100 GB transferu/miesiąc.
* 2 custom domains w planie Free.
* Storage: 500 MB łącznie (wszystkie środowiska) i 250 MB na środowisko (Free).
* 3 środowiska staging per app (Free)

**Mocne strony**
* GitHub i Azure DevOps integration
* Po wyczerpaniu limitu nie otrzymuje się rachunku, serwis wygasza stronę na moment jego odnowienia (całkowicie bezpieczne dla portfela). 

**Słabe strony / pułapki**
* Transfer 100 GB/mies. może być ograniczeniem przy ciężkich assetach (dużo obrazów/wideo)
* Po wyczerpaniu strona nie wczyta się klientom; darmowy plan pozbawiony jest dobrych umów SLA gwarantujących jakość.

**Kiedy wybrać**
* Dobry do wewnetrznego wykorzystania testowego i małych SPA, szczególnie dla ludzi używających Azure.

---

### GitHub Pages
**Co to jest**
Hosting wizytówek / prostych stron hostowanych plikami bezpośrednio w git na Githubie.

**Darmowy plan (istotne fakty)**
* Zmieszczone repo do około 1GB przy limicie pociągania go soft: 100GB/msc.
* Nie jest przeznaczone do hostowania biznesu online / e‑commerce / SaaS komercyjnego.
* Soft limit transferu: 100 GB/miesiąc
* Soft limit buildów: 10 buildów/godzinę.

**Mocne strony**
* Skrajna prostota dla środowisk deweloperskich. Nie potrzeba instalować zewnętrznych usług.

**Słabe strony / pułapki**
* GitHub nie pozwala z założenia regulaminu hostować środowiska o zabarwieniu e-Commerce bądz transakcyjnym (SaaS komercyjny de factp jest sprzeczny z celem tej usługi).

**Kiedy wybrać**
* Dokumentacje kodowe, skromne Landing Page dla aplikacji otwartych.

---

### Netlify / Vercel
**Co to jest**
Usługi o najnowocześniejszym ekosystemie deweloperskim dla React / Next.js wyposażające we wspaniały DX (Developer Experience).

**Darmowy plan (istotne fakty)**
* W pełni darmowe środowisko dla niekomercyjnych operacji, posiadające limit "kredytowy/zużyciowy" na miesiąc na wezwania funkcji / storage.

**Mocne strony**
* Preview deployments - każda zatwierdzona gałąź git jest z automatu nową, postawioną niezależną i dostępną do podglądu aplikacją.

**Słabe strony / pułapki**
* W darmowych tierach platformy potrafią zablokować i uśpić Twoje zaplecze na dni za nadmierne nadwyrężanie wdrożeń lub po wykryciu zarobku (SaaS) mogą zażądać przymusu aktualizacji do planu pro ($20/msc).

**Kiedy wybrać**
* Kiedy robisz projekt hobbystyczny jako osobisty showcase w portfolio i zależy Ci na najwygodniejszych rozwiązaniach nowożytnych wdrażaczy.

## 4. Hosting Bazy Danych SQL

### Neon (Serverless PostgreSQL)
**Co to jest**
Nowoczesny, skalujący się z zapotrzebowaniem hosting Postgres podchodzący w pełni do zasady Serverless.

**Darmowy plan (istotne fakty)**
* Rozmiarowo do 0.5 GB, usypiająca się moc obliczeniowa już po 5 minutach niko-użytku. 

**Mocne strony**
* Ustanawia faktyczny standard the free forever (dopóki siedzisz w 1 bazie z minimalnym ruchem). Bardzo nowoczesny panel zapytań.

**Słabe strony / pułapki**
* Słynne "Scale-to-Zero" odcina wybudowaną bazę - każdy 1 użytkownik odwiedzający apkę mającą przestój, powoduje oczekiwanie na podniesienie bazy, co zajmuje nawet 7+ sekund spowalniając apkę w startach.

**Kiedy wybrać**
* Chcesz zrzucić z karku rachunki do malutkiej bazy wspierającej panel bez znaczenia czasowego.

---

### Aiven Free Tier (PostgreSQL / MySQL)
**Co to jest**
Platforma DBaaS (Database-as-a-Service) obsługująca kilkanaście silników bazodanowych (PostgreSQL, MySQL, Redis i inne). Aiven zarządza całą infrastrukturą serwera bazodanowego po swojej stronie - aktualizacje, monitoring, replikacja. Ty otrzymujesz standardowy URI połączeniowy i korzystasz z bazy jak z lokalnej. W przeciwieństwie do podejścia serverless, instancja działa ciągle i nie usypia.

**Darmowy plan (istotne fakty)**
* 1 GB pamięci i wirtualnych rdzeni z zachowaną ciągłą pracą (always free i always on).

**Mocne strony**
* Brak zimnych startów - baza odpowiada natychmiast na każde zapytanie, co przekłada się na stabilne czasy odpowiedzi API niezależnie od przerw w ruchu.
* Always-on bez dodatkowej konfiguracji - nie trzeba pingować bazy ani walczyć z timeoutami połączeń wynikającymi z uśpienia.

**Słabe strony / pułapki**
* Brak rozszerzeń i dodatków typowych dla hostowanych baz (brak pgvector, pełnotekstowych rozszerzeń, itp.) - to czysta, naga baza dostępna przez URI.
* Backupy, migracje schematu i zarządzanie połączeniami leżą całkowicie po stronie dewelopera - Aiven nie oferuje narzędzi migracyjnych ani GUI do zarządzania schematem w darmowym planie.

**Kiedy wybrać**
* Gwarantuje idealną kompozycję z aplikacją - bez uśpień serverlessowych i bolesnego opóźnienia. Najlepsze dla klasycznie używających Django.

---

### Supabase
**Co to jest**
Backend-as-a-Service zbudowany na PostgreSQL, często opisywany jako open-source Firebase. Oferuje gotowe moduły: uwierzytelnianie użytkowników (Auth z JWT), przechowywanie plików (Storage), subskrypcje Realtime (WebSocket), Edge Functions (serverless) oraz REST i GraphQL API generowane automatycznie ze schematu bazy. Cały projekt - baza, auth, pliki - zarządzany jest z jednego panelu i przez jedno SDK.

**Darmowy plan (istotne fakty)**
* Rozmiar 500 MB limitowane projekty uśpienia trwające po okresie 1 tygodnia ciszy. Brak limitu funkcji SQLowych.

**Mocne strony**
* Gotowy system autentykacji (rejestracja, logowanie, OAuth, JWT, reset hasła) bez pisania ani linii kodu backendowego - Auth jest wbudowany i zarządzany.
* Jeden projekt pokrywa bazę danych, storage, auth i realtime - zamiast integrować 3-4 osobne serwisy, masz jedno SDK i jeden panel.

**Słabe strony / pułapki**
* Projekt usypia automatycznie po 7 dniach bez ruchu (darmowy plan) - przy sporadycznym używaniu wymaga ręcznego wybudzenia w panelu lub wymuszenia ruchu przez scheduled ping, co jest uciążliwym nawykiem.
* Limit 500 MB na bazę danych jest niski jeśli trzymasz w Supabase pliki lub dane binarne - łatwo go osiągnąć przy intensywniejszym użyciu.

**Kiedy wybrać**
* Przy całkowicie nowym i niecodziennym produkcie gdzie docenisz wsparcie potężnych narzędzi auth + realtime.

## 5. Hosting Danych (Storage)

### Cloudflare R2
**Co to jest**
Object Storage kompatybilny z API Amazon S3, oferowany przez Cloudflare jako tańsza alternatywa. Kluczowa różnica w stosunku do AWS S3: brak opłat za transfer wychodzący (egress) - pobieranie plików przez klientów końcowych jest bezpłatne. Pliki są serwowane przez globalną sieć CDN Cloudflare, co zapewnia niskie opóźnienia niezależnie od lokalizacji użytkownika.

**Darmowy plan (istotne fakty)**
* 10 Giga miesięcznie magazynowania + bezkarnie darmowy egress do świata klientów przy obciążeniu w rejonie 1 lub 10 milionów.

**Mocne strony**
* Zero opłat za egress - pobieranie plików przez użytkowników końcowych jest bezpłatne bez względu na ilość, co jest kluczową przewagą nad AWS S3 (gdzie egress to główne źródło rachunków).
* API kompatybilne z S3 - biblioteki używane z AWS S3 (boto3, aws-sdk) działają z R2 po zmianie endpoint URL, bez przepisywania kodu.

**Słabe strony / pułapki**
* Darmowy tier ma limity na operacje zapisu i odczytu: 1 mln operacji Class A (zapis, listowanie) i 10 mln operacji Class B (odczyt) miesięcznie. Przekroczenie generuje koszt ($4.50 za kolejne 1M operacji Class A). Przy normalnym użyciu przez kilka osób jest to trudne do przekroczenia, ale zautomatyzowane procesy (np. bot piszący wiele małych plików) mogą szybko dobić do limitu.

**Kiedy wybrać**
* Dla pewności bezkompromisowej taniej skali frontów (częste ściąganie mediów klienta np dużej listy).

---

### Supabase Storage
**Co to jest**
Warstwa przechowywania plików wbudowana w ekosystem Supabase, oparta na S3-kompatybilnym API. Reguły dostępu do plików definiuje się przez mechanizm Row Level Security (RLS) w PostgreSQL - ten sam co dla danych w tabelach - co pozwala precyzyjnie określić, kto może odczytywać i zapisywać pliki bez budowania osobnej warstwy autoryzacyjnej. Sensowna opcja wyłącznie wtedy, gdy reszta projektu i tak siedzi w Supabase.

**Darmowy plan (istotne fakty)**
* Wielkość plikowa do zaledwie 1 GB z uśpieniem w 7 dni gdy puste i ciche.

**Mocne strony**
* Ominięcie implementacji zewnętrznego S3 Amazona w Twoim kodzie źródłowym - wszystkie reguły RLS dla weryfikowania odczytu uzytkownika robione w 1 panelu.

**Słabe strony / pułapki**
* Może boleć w aplikacjach przetwarzających grubsze awatary czy pliki wideo - limit 1 GB to niewiele jak na free rozwiązanie Storage'owe w 2024.

**Kiedy wybrać**
* Projekt all-in-one - gdzie korzystamy z baz supabasa równoczesnie z Auth oraz nie planujemy ładować olbrzymich giga multimediów per użytkownik.




### Wybór

Zdecydowane zestawienie hostingowe dla projektu:

| Warstwa | Wybór | Alternatywa (docelowo) |
|---|---|---|
| Frontend | Vercel | Cloudflare Pages |
| Backend | Render | Oracle Cloud OCI |
| Baza danych | Supabase | Aiven Free Tier |
| Storage | Supabase | Cloudflare R2 |

**Uzasadnienie poszczególnych wyborów:**

- **Vercel** (Frontend) - obecnie wykorzystuję ją do swoich projektów, co upraszcza wdrożenie
- **Render** (Backend - początkowo) - wybrany ze względu na ogromną prostotę konfiguracji oraz brak ryzyka nieprzewidzianych kosztów, które mogłyby urosnąć po ataku na infrastrukturę (instancje nie skalują się automatycznie płatnie). W przyszłości planowana jest migracja na **Oracle Cloud OCI**, aby zniwelować zimne starty.
- **Supabase** (Baza danych SQL) - rozwiązanie obecnie przez nas używane. Pozwala wygodnie zarządzać bazą danych i udostępnia wbudowany storage w jednym ekosystemie.
- **Supabase Storage** (Storage) - naturalny wybór przy korzystaniu z bazy Supabase, centralizujący logikę autoryzacji do odczytu i zapisu plików w jednym miejscu.

**Ważne zastrzeżenie dotyczące docelowego Oracle Cloud:**
Oracle wymaga podania karty kredytowej przy rejestracji. Konto pozostaje w trybie "Always Free" - Oracle nie nalicza opłat automatycznie za przekroczenie limitu zasobów darmowych, zasoby są po prostu throttlowane lub odmawiane. Opłaty pojawiają się wyłącznie po ręcznym upgrade'ie do "Pay As You Go". Warto mimo to ustawić alert budżetowy na 0 USD w panelu OCI jako dodatkowe zabezpieczenie.
