# Backend

FastAPI backend z SQLAlchemy ORM i Alembic do migracji.

## 📋 Wymagania

- **Python:** 3.12+
- **Database:** PostgreSQL 14+
- **Inne:** pip, Alembic

## 🚀 Setup Lokalny

### 1. Środowisko wirtualne

```powershell
# Create venv
python -m venv venv

# Activate (Windows PowerShell)
.\venv\Scripts\Activate.ps1

# Activate (Unix/Linux)
source venv/bin/activate
```

### 2. Instalacja zależności

```bash
cd backend
pip install -r requirements.txt
```

### 3. Konfiguracja bazy danych

Utwórz plik `.env` w folderze głównym projektu (lub `backend/`):

```env
# Database
DATABASE_URL=postgresql://postgres:haslo@localhost:5432/apaulo_db

# Security
SECRET_KEY=your-super-secret-key-here-at-least-32-chars
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=120

# Attachments
ATTACHMENT_STORAGE_PATH=storage/attachments
```

### 4. Migracje (Alembic)

```bash
cd backend

# Sprawdź status migracji
alembic current

# Wykonaj migracje
alembic upgrade head

# Wgraj wymagane dane startowe (po każdej migracji/deploymentcie)
python -m scripts.seed_required_data

# Utwórz nową migrację (jeśli edytujesz modele)
alembic revision --autogenerate -m "Opis zmian"

# Cofnij ostatnią migrację
alembic downgrade -1
```

### 5. Uruchomienie serwera

```bash
cd backend

# Development (ze reload)
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

# Production
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Aplikacja będzie dostępna pod: **http://127.0.0.1:8000**  
Dokumentacja OpenAPI (Swagger): **http://127.0.0.1:8000/docs**  
ReDoc: **http://127.0.0.1:8000/redoc**

## 📂 Struktura Aplikacji

```
backend/
├── alembic/                    # Migracje bazy danych
│   ├── versions/              # Pliki migracji
│   ├── env.py                 # Konfiguracja Alembica
│   └── script.py.mako         # Template migracji
├── app/                        # Główna aplikacja
│   ├── main.py                # FastAPI app, routing
│   ├── core/
│   │   ├── config.py          # Konfiguracja (settings)
│   │   ├── dependencies.py    # Globalne dependencies
│   │   └── errors.py          # Exception handlers
│   ├── infrastructure/
│   │   └── sql/
│   │       ├── base.py        # SQLAlchemy Base
│   │       ├── factory.py     # Session factory
│   │       ├── models_registry.py  # Rejestr wszystkich modeli
│   │       └── tests/         # SQL testy
│   └── modules/               # Moduły biznesowe
│       ├── attachments/       # Załączniki
│       │   ├── api/
│       │   ├── schemas/
│       │   ├── services/
│       │   ├── repositories/
│       │   ├── models/
│       │   ├── storage.py     # Adapter lokalnego przechowywania
│       │   └── tests/
│       ├── security/          # Uwierzytelnianie & tokeny
│       │   ├── api/
│       │   │   └── auth.py    # Endpoints
│       │   ├── schemas/
│       │   │   └── auth.py    # Pydantic schemas
│       │   ├── services/
│       │   │   ├── auth.py    # Business logic
│       │   │   ├── password.py # Hash/Verify
│       │   │   └── token.py   # JWT management
│       │   ├── dependencies.py# DI (get_auth_service, etc)
│       │   └── tests/
│       ├── core_data/         # Dane użytkowników & role
│       │   ├── api/
│       │   │   ├── users.py   # User endpoints
│       │   │   └── roles.py   # Role endpoints
│       │   ├── schemas/
│       │   ├── services/
│       │   ├── repositories/
│       │   ├── models/
│       │   ├── dependencies.py# DI
│       │   └── tests/
│       └── pi/                # Podopieczni, Wolontariusze & Grupy
│           ├── api/
│           │   ├── volunteers.py
│           │   ├── beneficiaries.py
│           │   └── groups.py
│           ├── schemas/
│           ├── services/
│           ├── repositories/
│           ├── models/
│           ├── dependencies.py
│           └── tests/
├── alembic.ini
├── pyproject.toml
└── requirements.txt
```

## 🏗️ Architektura Modułów

Każdy moduł biznesowy (`security`, `core_data`, `pi`, `attachments`) trzyma własne endpointy,
schematy, serwisy, repozytoria, modele i testy:

```
module/
├── __init__.py           # Exports
├── api/
│   ├── __init__.py       # Exports router
│   └── {resource}.py     # FastAPI endpoints
├── schemas/
│   ├── __init__.py       # Exports schemas
│   └── {resource}.py     # Pydantic models
├── services/
│   ├── __init__.py       # Exports services
│   └── {resource}.py     # Business logic, transaction mgmt
├── repositories/
│   ├── __init__.py       # Exports repos
│   └── {resource}.py     # Data access (no transactions)
├── models/
│   ├── __init__.py       # Exports models
│   └── {resource}.py     # SQLAlchemy ORM models
├── dependencies.py       # Dependency injection
└── tests/
    ├── conftest.py       # Fixtures
    ├── test_api.py
    └── test_service.py
```

## 🔧 Główne Zależności

| Pakiet | Wersja | Opis |
|--------|--------|------|
| fastapi | 0.115+ | Web framework |
| sqlalchemy | 2.0+ | ORM |
| alembic | 1.13+ | Database migrations |
| psycopg2-binary | 2.9+ | PostgreSQL adapter |
| pydantic | 2.0+ | Data validation |
| python-jose | 3.3+ | JWT tokens |
| passlib | 1.7+ | Password hashing |
| bcrypt | 4.0+ | Bcrypt password hashing |

## 📎 Załączniki

Moduł `app/modules/attachments` obsługuje metadane i pliki załączników.

- Endpointy: `/api/v1/attachments`.
- Upload Kart BO: `POST /api/v1/attachments/bo-cards`.
- Upload wykorzystuje `multipart/form-data`: pole `content` zawiera plik, a pola
  `group_id`, `beneficiary_id`, `volunteer_id` i `period` zawierają metadane.
- Lista metadanych: `GET /api/v1/attachments/bo-cards`; opcjonalne filtry
  obejmują m.in. `group_id`, osoby, okres, komentarz i wyszukiwanie tekstowe.
- Archiwum z tymi samymi filtrami: `GET /api/v1/attachments/bo-cards/download`.
- Podgląd/treść pliku: `GET /api/v1/attachments/{attachment_id}/content`.
- Edycja nazwy/opisu: `PATCH /api/v1/attachments/{attachment_id}`.
- Usuwanie: `DELETE /api/v1/attachments/{attachment_id}`.
- Lokalny storage: `storage/attachments` względem folderu `backend/`.
- Obsługiwane pliki: PDF, JPG, PNG, WEBP, HEIC/HEIF do 10 MB.

Pliki są przechowywane poza bazą, a tabela `attachments` trzyma metadane:
kontekst, grupa, podopieczny, wolontariusz, okres, nazwa, typ MIME, rozmiar,
checksum oraz informacje kto i kiedy dodał lub zmienił plik. Dzięki temu podmiana
lokalnego storage na usługę chmurową wymaga głównie nowego adaptera storage.


```bash
# Install production dependencies
pip install gunicorn

# Run with Gunicorn
gunicorn app.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

