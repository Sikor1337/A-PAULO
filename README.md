# A-PAULO

System do zarządzania wolontariatem, podopiecznymi, grupami oraz obiegiem Kart BO.

## Quick Start

**Backend:** zobacz [backend/README.md](backend/README.md)  
**Frontend:** zobacz [frontend/README.md](frontend/README.md)  
**Dokumentacja:** zobacz [docs/](docs/)

### Backend

```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
alembic upgrade head
python -m scripts.seed_required_data
.\venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

Backend działa pod adresem `http://127.0.0.1:8000`, a dokumentacja API pod `/docs`.

### Frontend

```powershell
cd frontend
npm install
npm run dev
```

Frontend działa pod adresem `http://localhost:5173`.

## Zakres Systemu

- Uwierzytelnianie JWT z tokenem dostępu i odświeżania.
- Zarządzanie użytkownikami, podopiecznymi, wolontariuszami i grupami.
- Przypisywanie podopiecznych do grup i wolontariuszy.
- Obsługa obiegu Kart BO i załączników.
- Panel administracyjny dla danych słownikowych i użytkowników.

## Tech Stack

| Warstwa | Technologia |
|---------|-------------|
| Backend | FastAPI, SQLAlchemy 2.0, Alembic, PostgreSQL, JWT |
| Frontend | React 19, TypeScript, Vite 7, Tailwind CSS v4, React Router 7 |
| Stan i API | Zustand, TanStack React Query, Axios |
| Testy | Pytest, Vitest, Testing Library |

## Struktura Projektu

```text
/
├── backend/
│   ├── alembic/                 # Migracje bazy danych
│   ├── app/
│   │   ├── core/                # Konfiguracja, DB dependencies, błędy
│   │   ├── infrastructure/sql/  # SQLAlchemy Base, factory, registry modeli
│   │   └── modules/
│   │       ├── attachments/     # Załączniki
│   │       ├── core_data/       # Użytkownicy
│   │       ├── pi/              # Podopieczni, wolontariusze, grupy
│   │       └── security/        # Auth, hasła, JWT
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── components/
│       ├── hooks/
│       ├── pages/
│       ├── services/
│       ├── stores/
│       └── types/
├── docs/
└── README.md
```

## Dokumentacja

- [Wymagania biznesowe](docs/business-requirements.md)
- [Architektura backendu](docs/backend-architecture.md)
- [Architektura frontendu](docs/frontend-architecture.md)
- [Plan hostingu](docs/hosting-PLAN.md)
- [Responsywny layout frontendu](docs/frontend-responsive-layout.md)

## Testy

```powershell
cd backend
.\venv\Scripts\python.exe -m pytest -q

cd ../frontend
npm run build
npm run lint
```

## Przydatne linki

- [Jira](https://lukaszpiaseckidev.atlassian.net/jira/software/c/projects/PAP/boards/4/backlog)
- [Dokument wymagań od Koo](https://docs.google.com/document/d/1HbTbXshl_aBdHJvJ6wtJXOhL2fLGdkbENAm6HyZKa9Y/edit?tab=t.0)

### Bazy danych

- [Wzór nowej bazy danych](APAULO.xlsx)
- [Supabase z danymi](https://supabase.com/dashboard/project/bskdfwgejlgnwuwohjak/database/tables)

### Zaproponowane UI

- [Propozycja 1](https://sikor1337.github.io/A-PAULO/APAULOdemo.html)
- [Propozycja 2](https://sikor1337.github.io/A-PAULO/apaulo_recruitment_clubs_wdra%C5%BCanie.html)

### Nagrania

- [2025-12-08](https://drive.google.com/file/d/1r8pBNMnZSO0xudMJzs13zTNxlzXG6nbw/view?usp=drive_link)
- [2025-05-16 - SDI Solution](https://drive.google.com/file/d/1bnDum9YhBuo4Am7-GkyjC3xCaKVpHPjB/view?usp=drive_link)
