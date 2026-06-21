# 1. Wprowadzenie

Ten dokument opisuje docelową architekturę systemu. Obecna struktura to **architektura warstwowa (Layered Architecture)** zorganizowana jako **modularny monolit (Modular Monolith)**. Takie podejście zapewnia wyraźny podział odpowiedzialności, łatwość utrzymania oraz testowalność, przy jednoczesnym zachowaniu całej funkcjonalności w jednym artefakcie wdrożeniowym.

## 1.1. Dlaczego architektura warstwowa?

Architektura warstwowa organizuje kod w poziome warstwy, z których każda ma jasno określoną odpowiedzialność:

- **Warstwa prezentacji (API)**: obsługuje żądania HTTP, walidację danych wejściowych oraz formatowanie odpowiedzi  
- **Warstwa logiki biznesowej (Services)**: zawiera przypadki użycia i logikę domenową  
- **Warstwa dostępu do danych (Repositories)**: zarządza zapisem i odczytem danych  
- **Warstwa infrastruktury (Infrastructure)**: dostarcza możliwości techniczne (baza danych, storage, logowanie)  

Podejście to różni się od architektury Clean Architecture (koncentryczne kręgi), ponieważ skupia się na praktycznym podziale poziomym, dobrze dopasowanym do typowych workflow zespołów developerskich.

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

## 1.2. Korzyści z docelowej architektury

1. **Jasny podział odpowiedzialności**: każda warstwa ma jedno główne zadanie  
2. **Testowalność**: serwisy mogą być testowane jednostkowo z użyciem mocków repozytoriów  
3. **Łatwość utrzymania**: zmiany w jednym module mają minimalny wpływ na inne  
4. **Onboarding developerów**: nowi członkowie zespołu szybko rozumieją strukturę systemu  
5. **Skalowalność**: moduły mogą zostać wydzielone do mikroserwisów  
6. **Spójność**: wszystkie moduły mają tę samą strukturę (api/services/repositories/schemas/models)  
7. **Zarządzanie zależnościami**: jasno określone zasady zapobiegają powstawaniu splątanych zależności  

---

# 2. Zasady

1. **Warstwa API** może zależeć od:
   - Service Layer (w tym samym module)
   - Core
   - Errors

2. **Warstwa serwisów** może zależeć od:
   - Repository Layer (w tym samym module lub innych modułach)
   - Other Services (unikać zależności cyklicznych)
   - Core
   - Errors

3. **Warstwa repozytoriów** może zależeć od:
   - Infrastructure
   - Core
   - Errors

4. **Warstwa infrastruktury** może zależeć od:
   - Core
   - Errors

5. **Zakaz przeskakiwania warstw (Layer Skipping)**  
   - Warstwy mogą komunikować się wyłącznie z warstwą bezpośrednio poniżej  
   - Dozwolony przepływ: API → Services → Repositories → Infrastructure  
   - Niedozwolone przykłady:
     - API → Repository (pominięcie Services)
     - API → Infrastructure
     - Services → Infrastructure (bez użycia Repository)
   - Każda operacja musi przechodzić przez pełny łańcuch odpowiedzialności warstw
  
6. **Zależności cykliczne między modułami są zabronione**



# 3. Przykład struktury plików

```text
backend/
├─ app/
│  ├─ main.py
│  ├─ core/
│  │  ├─ config.py
│  │  └─ dependencies.py
│  ├───infrastructure
│  │   └───sql
│  │       ├─ base.py
│  │       ├─ factory.py
│  │       └─ models_registry.py
│  └─ modules/
│     ├─ pi/
│     │  ├─ api/
│     │  │  ├─ volunteers.py
│     │  │  ├─ beneficiaries.py
│     │  │  ├─ groups.py
│     │  │
│     │  ├─ services/
│     │  │  ├─ volunteers.py
│     │  │  ├─ beneficiaries.py
│     │  │  ├─ groups.py
│     │  │
│     │  ├─ repositories/
│     │  │  ├─ volunteers.py
│     │  │  ├─ beneficiaries.py
│     │  │  ├─ groups.py
│     │  │
│     │  ├─ schemas/
│     │  │  ├─ volunteers.py
│     │  │  ├─ beneficiaries.py
│     │  │  ├─ groups.py
│     │  │
│     │  ├─ models/
│     │  │  ├─ volunteer.py
│     │  │  ├─ beneficiary.py
│     │  │  ├─ group.py
│     │  │
│     │  ├─ dependencies.py
│     │
│     ├─ security/
│     │  ├─ api/
│     │  ├─ services/
│     │  ├─ repositories/
│     │  ├─ schemas/
│     │  ├─ dependencies.py
│     │  └─ tests/
│     │
│     └─ core_data/
│        ├─ api/
│        ├─ services/
│        ├─ repositories/
│        ├─ schemas/
│        ├─ models/
│        ├─ dependencies.py
│        └─ tests/
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