# Architektura Backendu — Dokumentacja Techniczna

---

## Spis treści

1. [Przegląd architektury](#1-przegląd-architektury)
2. [Zasady architektury](#2-zasady-architektury)
3. [Struktura projektu](#3-struktura-projektu)
4. [Warstwy współdzielone](#4-warstwy-współdzielone)
   - 4.1 [core/](#41-core)
   - 4.2 [infrastructure/](#42-infrastructure)
5. [Template modułu domenowego](#5-template-modułu-domenowego)
   - 5.1 [Struktura katalogów](#51-struktura-katalogów)
   - 5.2 [Odpowiedzialność każdej warstwy](#52-odpowiedzialność-każdej-warstwy)
   - 5.3 [Wiring zależności — dependencies.py](#53-wiring-zależności--dependenciespy)
6. [Moduły specjalne](#6-moduły-specjalne)
   - 6.1 [security/](#61-security--autentykacja-i-autoryzacja)
   - 6.2 [core_data/](#62-core_data)
7. [Obsługa błędów](#7-obsługa-błędów)
8. [Strategia testowania](#8-strategia-testowania)

---

# 1. Przegląd architektury

Architektura systemu to **architektura warstwowa (Layered Architecture)** zorganizowana jako **modularny monolit (Modular Monolith)**.

Kod podzielony jest na cztery poziome warstwy: **API → Services → Repositories → Infrastructure**. Każda warstwa ma jedno jasno określone zadanie i zależy wyłącznie od warstwy bezpośrednio poniżej. Warstwy `core/` i `errors` są przekrojowe — mogą być importowane na każdym poziomie.

:::mermaid
flowchart TB
    API["API"]
    SERVICES["Services"]
    REPOSITORIES["Repositories"]
    INFRASTRUCTURE["Infrastructure"]

    CORE["Core"]
    ERRORS["Errors"]

    API --> SERVICES
    SERVICES --> REPOSITORIES
    REPOSITORIES --> INFRASTRUCTURE

    API -.-> CORE
    SERVICES -.-> CORE
    REPOSITORIES -.-> CORE
    INFRASTRUCTURE -.-> CORE

    API -.-> ERRORS
    SERVICES -.-> ERRORS
    REPOSITORIES -.-> ERRORS
    INFRASTRUCTURE -.-> ERRORS
:::

**Dlaczego architektura warstwowa, a nie Clean Architecture?**
Skupia się na praktycznym, poziomym podziale odpowiedzialności — bardziej czytelnym i dopasowanym do typowego workflow zespołu.

**Korzyści:**

| Korzyść | Opis |
|---|---|
| Podział odpowiedzialności | Każda warstwa ma jedno główne zadanie |
| Testowalność | Serwisy testowane jednostkowo z mockami repozytoriów |
| Łatwość utrzymania | Zmiany w jednym module mają minimalny wpływ na inne |
| Onboarding | Nowi developerzy szybko rozumieją strukturę |
| Skalowalność | Moduły mogą zostać wydzielone do mikroserwisów |
| Spójność | Wszystkie moduły mają identyczną strukturę |
| Zarządzanie zależnościami | Jasne zasady zapobiegają splątanym zależnościom |

---

# 2. Zasady architektury

## 2.1. Dozwolone zależności między warstwami

| Warstwa | Może importować z |
|---|---|
| **API** | Services (własny moduł), Core, Errors |
| **Services** | Repositories (własny lub inny moduł), inne Services, Core, Errors |
| **Repositories** | Infrastructure, Core, Errors |
| **Infrastructure** | Core, Errors |

## 2.2. Zakaz przeskakiwania warstw

Każda operacja musi przechodzić przez pełny łańcuch: `API → Services → Repositories → Infrastructure`.

```
✅  API → Services → Repositories → Infrastructure
❌  API → Repositories              (pominięcie Services)
❌  API → Infrastructure
❌  Services → Infrastructure       (pominięcie Repositories)
```

## 2.3. Komunikacja między modułami

Cross-module odbywa się **wyłącznie przez warstwę serwisów**:

```python
from app.modules.notifications.services.email import EmailService    # ✅
from app.modules.notifications.repositories.email import EmailRepository  # ❌
```

## 2.4. Zakaz zależności cyklicznych

Jeśli dwa serwisy wzajemnie się potrzebują:
- Wydziel wspólną logikę do `core/` lub osobnego modułu
- Zastąp bezpośrednie wywołanie zdarzeniem (event/message)
- Zrewiduj podział — być może moduły powinny być scalone

---

# 3. Struktura projektu

```text
backend/
├─ app/
│  ├─ main.py
│  ├─ core/
│  │  ├─ config.py
│  │  ├─ dependencies.py
│  │  ├─ base.py
│  │  └─ errors.py
│  ├─ infrastructure/
│  │  ├─ sql/
│  │  │  ├─ base.py
│  │  │  ├─ factory.py
│  │  │  └─ models_registry.py
│  │  ├─ nosql/
│  │  │  └─ factory.py
│  │  └─ storage/
│  │     └─ client.py
│  └─ modules/
│     ├─ <domain_module>/          ← template opisany w sekcji 5
│     │  ├─ api/
│     │  ├─ services/
│     │  ├─ repositories/
│     │  ├─ schemas/
│     │  ├─ models/
│     │  ├─ dependencies.py
│     │  ├─ exceptions.py
│     │  └─ tests/
│     ├─ security/                 ← sekcja 6.1
│     └─ core_data/               ← sekcja 6.2
│
├─ alembic/
│  ├─ versions/
│  ├─ env.py
│  └─ script.py.mako
│
├─ alembic.ini
├─ pyproject.toml
├─ .env
├─ .env.example
└─ README.md
```

---

# 4. Warstwy współdzielone

## 4.1. `core/`

Zawiera elementy współdzielone przez wszystkie moduły. **Nie zawiera logiki biznesowej.**

| Plik | Odpowiedzialność |
|---|---|
| `config.py` | Ustawienia aplikacji z zmiennych środowiskowych (`Pydantic BaseSettings`): połączenia z bazą danych, klucze JWT, nazwy bucketów, flagi feature |
| `dependencies.py` | Globalne zależności FastAPI (`Depends()`): `get_db_session`, `get_current_user`, `get_nosql_client` |
| `base.py` | Abstrakcyjne klasy bazowe: `BaseRepository`, `BaseService` — spójny interfejs dla wszystkich modułów |
| `errors.py` | Hierarchia wyjątków aplikacji: `BaseAppException` i klasy pochodne (szczegóły w sekcji 7) |

## 4.2. `infrastructure/`

Dostarcza narzędzia techniczne do komunikacji z zewnętrznymi systemami. **Nie zawiera logiki biznesowej ani domenowej.**

### `infrastructure/sql/`

| Plik | Odpowiedzialność |
|---|---|
| `base.py` | `DeclarativeBase` SQLAlchemy — wszystkie modele ORM dziedziczą z tej klasy |
| `factory.py` | Fabryka sesji: `AsyncSessionLocal`, `engine` — używana przez `get_db_session` w `core/dependencies.py` |
| `models_registry.py` | Importuje wszystkie modele ORM dla Alembic `autogenerate` — **każdy nowy model musi być tu zarejestrowany** |

### `infrastructure/nosql/`

| Plik | Odpowiedzialność |
|---|---|
| `factory.py` | Klient NoSQL (np. Firestore, MongoDB) gotowy do wstrzyknięcia przez `Depends()` |

### `infrastructure/storage/`

Klient usługi przechowywania plików (np. GCS, S3). Operacje: `upload`, `download`, `delete`, `generate_signed_url`.

---

# 5. Template modułu domenowego

## 5.1. Struktura katalogów

Każdy moduł domenowy stosuje identyczną strukturę:

```text
modules/<domain>/
├─ api/
│  └─ <resource>.py        # Endpointy HTTP
├─ services/
│  └─ <resource>.py        # Logika biznesowa
├─ repositories/
│  └─ <resource>.py        # Dostęp do danych
├─ schemas/
│  └─ <resource>.py        # Schematy Pydantic (request/response)
├─ models/
│  └─ <resource>.py        # Modele ORM SQLAlchemy
├─ dependencies.py         # Fabryki DI dla FastAPI
├─ exceptions.py           # Wyjątki domenowe modułu
└─ tests/
```

## 5.2. Odpowiedzialność każdej warstwy

### `api/<resource>.py`

- Definiuje endpointy HTTP (`@router.get`, `@router.post`, itd.)
- Waliduje dane wejściowe przez schematy Pydantic
- Ustawia kody statusu HTTP i formatuje odpowiedź
- **Nie zawiera** logiki biznesowej — deleguje do serwisu
- **Nie importuje** repozytoriów ani modeli ORM

```python
@router.post("/", response_model=ResourceResponse, status_code=201)
async def create_resource(
    data: ResourceCreateRequest,
    service: ResourceService = Depends(get_resource_service),
) -> ResourceResponse:
    return await service.create(data)
```

### `services/<resource>.py`

- Implementuje logikę biznesową i przypadki użycia
- Orkestruje wiele wywołań repozytoriów w jednej operacji
- Może korzystać z serwisów innych modułów (bez zależności cyklicznych)
- **Nie importuje** `Request`, `Response` ani typów HTTP
- **Nie wykonuje** bezpośrednich zapytań do bazy danych

```python
class ResourceService:
    def __init__(self, repository: ResourceRepository):
        self._repo = repository

    async def create(self, data: ResourceCreateRequest) -> ResourceResponse:
        if await self._repo.exists(name=data.name):
            raise ResourceAlreadyExistsError(data.name)
        entity = await self._repo.create(data)
        return ResourceResponse.model_validate(entity)
```

### `repositories/<resource>.py`

- Wykonuje operacje odczytu i zapisu danych (SQL/NoSQL)
- Zawiera wyłącznie logikę dostępu do danych — **żadnej logiki biznesowej**
- Zwraca modele domenowe lub ORM, nigdy obiekty sesji/kursorów
- **Nie importuje** nic z warstwy `api/` ani `services/`

### `schemas/<resource>.py`

- Definiuje schematy Pydantic do walidacji danych wejściowych i wyjściowych
- Konwencja nazewnictwa: `<Resource>CreateRequest`, `<Resource>UpdateRequest`, `<Resource>Response`
- Wyłącznie walidacja i transformacja danych — **brak logiki biznesowej**

### `models/<resource>.py`

- Definiuje modele ORM SQLAlchemy mapowane na tabele bazy danych
- Dziedziczy z `Base` z `infrastructure/sql/base.py`
- **Wymagane:** zarejestrowanie w `infrastructure/sql/models_registry.py`

### `exceptions.py`

- Wyjątki domenowe specyficzne dla modułu
- Dziedziczą z klas bazowych w `core/errors.py`

## 5.3. Wiring zależności — `dependencies.py`

Plik konfiguruje łańcuch wstrzykiwania zależności FastAPI:

```
API  →  Depends(get_<resource>_service)
         └─ Service  →  Depends(get_<resource>_repository)
                          └─ Repository  →  Depends(get_db_session)  [z core/]
```

**Zasady:**
- `api/` deklaruje `Depends()` **wyłącznie** na funkcjach zwracających Service
- `services/` **nie używają** `Depends()` — przyjmują zależności przez `__init__`
- Sesję DB (`AsyncSession`) wstrzykuje **wyłącznie** Repository

```python
def get_resource_repository(
    session: AsyncSession = Depends(get_db_session),
) -> ResourceRepository:
    return ResourceRepository(session)

def get_resource_service(
    repository: ResourceRepository = Depends(get_resource_repository),
) -> ResourceService:
    return ResourceService(repository)
```

**Zabronione wzorce:**

```python
# ❌ API wstrzykuje Repository bezpośrednio
async def get_items(repo: ItemRepository = Depends(get_item_repository)): ...

# ❌ API wstrzykuje sesję DB bezpośrednio
async def get_items(session: AsyncSession = Depends(get_db_session)): ...

# ✅ API wstrzykuje wyłącznie Service
async def get_items(service: ItemService = Depends(get_item_service)): ...
```

---

# 6. Moduły specjalne

## 6.1. `security/` — autentykacja i autoryzacja

Moduł `security/` jest modułem przekrojowym — dostarcza autentykację i autoryzację dla całej aplikacji. Inne moduły korzystają **wyłącznie** z jego warstwy `dependencies/`.

### Struktura

```text
modules/security/
├─ api/
│  └─ auth.py              # POST /auth/login, POST /auth/refresh, POST /auth/logout
├─ services/
│  └─ auth.py              # Logika logowania, generowanie i odświeżanie tokenów
├─ schemas/
│  ├─ token.py             # TokenResponse, TokenPayload
│  └─ user.py              # LoginRequest, UserInfo
├─ config.py               # JWTSettings: secret, algorithm, expiry_minutes
├─ dependencies/
│  ├─ __init__.py
│  ├─ auth.py              # get_current_user, get_current_active_user
│  └─ permissions.py       # require_role("admin"), require_permission("read:data")
├─ exceptions.py           # InvalidCredentialsError, TokenExpiredError, InsufficientPermissionsError
├─ utils.py                # create_access_token(), verify_token(), hash_password(), verify_password()
└─ tests/
```

### Użycie w innych modułach

```python
# modules/<domain>/api/resource.py
from app.modules.security.dependencies.auth import get_current_user
from app.modules.security.dependencies.permissions import require_role

@router.delete("/{id}", dependencies=[Depends(require_role("admin"))])
async def delete_resource(id: int, current_user = Depends(get_current_user)):
    ...
```

> **Niedozwolone:** importowanie z `security/services/` lub `security/utils/` w modułach domenowych.

## 6.2. `core_data/`

Moduł przechowujący dane słownikowe i konfiguracyjne współdzielone przez inne moduły domenowe. Stosuje standardową strukturę modułu (sekcja 5.1). Inne moduły korzystają z jego serwisów — nigdy bezpośrednio z repozytoriów.

---

# 7. Obsługa błędów

## 7.1. Przepływ wyjątków

```
Repository  →  rzuca wyjątek domenowy (np. ResourceNotFoundError)
    ↓
Service     →  przepuszcza lub transformuje wyjątek domenowy
    ↓
API         →  tłumaczy wyjątek domenowy na HTTPException
    ↓
Client      ←  odpowiedź HTTP z kodem błędu i komunikatem
```

## 7.2. Hierarchia wyjątków (`core/errors.py`)

```python
class BaseAppException(Exception):
    status_code: int = 500
    detail: str = "Internal server error"

class NotFoundError(BaseAppException):
    status_code = 404

class ValidationError(BaseAppException):
    status_code = 422

class PermissionDeniedError(BaseAppException):
    status_code = 403

class ConflictError(BaseAppException):
    status_code = 409
```

Wyjątki domenowe modułów dziedziczą z powyższych klas:

```python
# modules/<domain>/exceptions.py
class ResourceNotFoundError(NotFoundError):
    def __init__(self, resource_id: int):
        self.detail = f"Resource {resource_id} not found"

class ResourceAlreadyExistsError(ConflictError):
    def __init__(self, name: str):
        self.detail = f"Resource '{name}' already exists"
```

## 7.3. Globalny handler wyjątków (`main.py`)

Automatycznie tłumaczy wyjątki domenowe na odpowiedzi HTTP — warstwa API nie musi obsługiwać każdego wyjątku ręcznie:

```python
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from app.core.errors import BaseAppException

app = FastAPI()

@app.exception_handler(BaseAppException)
async def app_exception_handler(request: Request, exc: BaseAppException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )
```

---

# 8. Strategia testowania

## 8.1. Poziomy testów

| Poziom | Co testujemy | Narzędzia | Izolacja |
|---|---|---|---|
| **Unit** | Logika w serwisach | `pytest`, `pytest-mock` | Mock repozytoriów |
| **Integration** | Endpointy API + baza danych | `pytest`, `TestClient`, baza testowa | Prawdziwa baza (rollback transakcji) |
| **E2E** | Pełny flow HTTP | `httpx`, zewnętrzna baza | Brak izolacji |

## 8.2. Testy jednostkowe serwisów

Serwisy testujemy **bez bazy danych** — repozytoria są mockowane przez `AsyncMock`:

```python
# tests/test_services.py
from unittest.mock import AsyncMock
import pytest
from app.modules.example.services.resource import ResourceService
from app.modules.example.exceptions import ResourceNotFoundError

@pytest.fixture
def mock_repo():
    return AsyncMock()

@pytest.fixture
def service(mock_repo):
    return ResourceService(repository=mock_repo)

async def test_get_resource_not_found(service, mock_repo):
    mock_repo.get_by_id.return_value = None
    with pytest.raises(ResourceNotFoundError):
        await service.get_by_id(resource_id=999)
```

## 8.3. Testy integracyjne endpointów

Używają `TestClient` z FastAPI. Każdy test weryfikuje jeden endpoint z nagłówkami autoryzacji i sprawdza kod statusu oraz kształt odpowiedzi.
