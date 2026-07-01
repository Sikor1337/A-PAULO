# PAP-58 — grupy użytkowników i permissions

## Cel i rozdzielenie domen

Autoryzacja A-PAULO używa elastycznego modelu:

```text
User → security_user_groups → security_groups
     → security_group_permissions → security_permissions
```

`security_groups` są grupami kont i nie mają żadnego związku z tabelą `groups`
modułu `pi`, która opisuje zespoły wolontariuszy i podopiecznych.

Uprawnienia są stałym katalogiem akcji (`CAN_VIEW_*`, `CAN_MANAGE_*`). Grupy są
konfigurowalne, a efektywny zestaw praw użytkownika jest sumą praw wszystkich
jego grup. Backend zawsze wykonuje ostateczną kontrolę dostępu.

## Backend

Kod mechanizmu znajduje się w `app/modules/security/`:

- `models/constants.py` — stabilne kody i katalog permissions;
- `models/permissions.py` — `Permission`, `UserGroup` i dwie tabele M2M;
- `repositories/permissions.py` — zapytania o grupy, członkostwa i sumę praw;
- `services/permissions.py` — reguły grup systemowych, ochrona przed lockoutem,
  przypisywanie grup z obu kierunków;
- `dependencies.py` — `require_permission()` i `require_any_permission()`;
- `api/permissions.py` — katalog, CRUD grup, matryca praw i członkostwa.

Endpointy administracyjne są pod `/api/v1/security`. Każdy endpoint domenowy
ma osobne wymaganie odczytu albo zarządzania. Samo ukrycie przycisku na
frontendzie nigdy nie zastępuje kontroli backendowej.

### Grupy systemowe

Migracja tworzy:

- `Admin` — wszystkie permissions;
- `Staff` — operacyjne permissions bez zarządzania użytkownikami i security.

Definicji, nazwy, usunięcia i matrycy grup systemowych nie można zmieniać.
Członkostwo można zarządzać, ale grupa Admin nie może zostać bez użytkownika.
Status konta sam w sobie nie przyznaje żadnego permission. Dotyczy to również
statusu `admin`: pełny dostęp wynika z członkostwa w systemowej grupie `Admin`.
Migracja przypisuje istniejące konta administracyjne do tej grupy i nie pozwala
usunąć z niej ostatniego użytkownika. Przy utworzeniu konta aplikacja może dodać
domyślną grupę systemową, ale późniejsza edycja statusu lub profilu nie nadpisuje
ręcznie skonfigurowanych członkostw. Kontrola każdego endpointu zawsze odczytuje
permissions z grup.

## Frontend

`permissionService` pobiera efektywne prawa bieżącego użytkownika. React Query
przechowuje je pod kluczem `my-permissions`, który jest czyszczony przy
wylogowaniu i odświeżany po zmianie członkostwa.

- `ProtectedRoute` blokuje bezpośrednie wejście na trasę bez permission;
- `Sidebar` pokazuje tylko dostępne moduły;
- Ustawienia mają osobne sekcje użytkowników i grup;
- matryca grupuje permissions według obszaru i zapisuje pełny zestaw zaznaczeń;
- użytkownika można przypisać do grup z tabeli użytkowników, a użytkowników do
  grupy z edytora grupy.

Frontend traktuje `status` jako etap cyklu życia konta (`new_volunteer`,
`regular`, `admin`), a nie jako źródło praw do akcji.

## Dodawanie nowego permission

1. Dodać kod i opis do `PERMISSION_CATALOG`.
2. Dodać go w kolejnej migracji do `security_permissions` i — jeśli potrzeba —
   do chronionych grup systemowych.
3. Podpiąć `require_permission(KOD)` do endpointu.
4. Dodać kod do unii `PermissionCode` na frontendzie.
5. Ochronić trasę, element menu i akcje UI.
6. Dodać test pozytywny i test odpowiedzi `403`.
