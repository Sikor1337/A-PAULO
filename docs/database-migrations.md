# Migracje i odtwarzanie bazy

## Stan po PAP-69

Stary, niespójny graf migracji został zastąpiony jedną migracją bazową:
`cd317ee086f0` (`baseline current schema`). Baseline został wygenerowany z
aktualnego `Base.metadata` na pustym i odizolowanym schemacie `dev1`.

Przyczyną wcześniejszych błędów był między innymi `search_path` ustawiony na
`<wybrany_schemat>, public`. Gdy wybrany schemat był pusty, refleksja PostgreSQL
widziała tabele z `public`, a Alembic generował niepełną różnicę zamiast migracji
od zera. Środowisko Alembic ustawia teraz wyłącznie wskazany schemat.

Stan zweryfikowany 2026-07-01:

| Schemat | Rewizja | Tabele modelowe | Dane |
| --- | --- | ---: | --- |
| `dev1` | `cd317ee086f0` | 18 | pusty |
| `production` | `cd317ee086f0` | 18 | pusty biznesowo, gotowy do wdrożenia |
| `public` | `cd317ee086f0` | 18 | dane demonstracyjne |

Wdrożenie korzystające ze schematu produkcyjnego musi mieć ustawione
`DATABASE_SCHEMA=production`. Samo istnienie poprawnego schematu nie zmienia
konfiguracji działającej usługi Render.

## Bezpieczne polecenia

Wszystkie polecenia uruchamia się z katalogu `backend/`.

```powershell
$env:DATABASE_SCHEMA='dev1'
.\venv\Scripts\python.exe -m alembic upgrade head
.\venv\Scripts\python.exe -m scripts.verify_schema
.\venv\Scripts\python.exe -m alembic check
```

Reset jest celowo ograniczony do `public`, `production` i `dev1` oraz wymaga
jawnego potwierdzenia:

```powershell
.\venv\Scripts\python.exe -m scripts.reset_schemas dev1 --confirm RESET_APP_SCHEMAS
```

Narzędzie usuwa tabele, widoki i sekwencje we wskazanym schemacie, ale zachowuje
sam schemat oraz jego uprawnienia. Nigdy nie należy uruchamiać resetu bez
wcześniejszego audytu danych.

## Dane demonstracyjne

Po migracji pustego `public` dane przykładowe można wgrać jednokrotnie:

```powershell
$env:DATABASE_SCHEMA='public'
.\venv\Scripts\python.exe -m scripts.seed_sample_data
```

Skrypt odmawia działania poza `public` oraz wtedy, gdy istnieją już użytkownicy.
Tworzy dwa konta, 10 wolontariuszy, cztery grupy, 10 podopiecznych i przykładowe
zgłoszenie rekrutacyjne. Każdy wolontariusz należy do grupy, a każdy podopieczny
ma przypisaną grupę. Seed nie przypisuje wolontariuszom funkcji, kierowania grupą
ani opieki nad podopiecznym, ponieważ takie dane muszą wynikać z rzeczywistych
decyzji organizacji. Hasło demonstracyjne jest
wyświetlane po poprawnym wykonaniu seeda i nie może być używane w `production`.
