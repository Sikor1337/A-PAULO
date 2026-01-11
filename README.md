# Aplikacja PaPka
System do zarządzania wolontariatem, pomocą indywidualną oraz obiegiem kart ewidencyjnych (BO). 

[Specyfikacja Wymagań Funkcjonalnych](docs/business-requirements.md)

## Tech Stack

### Backend
*   **Język:** Python 3.12+
*   **Framework:** Django + Django REST Framework (DRF)
*   **Autoryzacja:** JWT / Session auth

### Frontend
*   **Framework:** React 18+
*   **Build Tool:** Vite?
*   **Język:** TS or JS?
*   **Mobile:** PWA (Progressive Web App) - `vite-plugin-pwa`

### Baza danych
*   **Baza:** PostgreSQL



##  Project structure

```text
/
├── backend/                #Django
│   ├── core/              
│   ├── app1/     
│   ├── app2/           
│   └── manage.py
├── frontend/               
│   ├── src/
│   ├── public/
│   └── package.json
├── docs/     
│   └── business-requirements.md
└── README.md
```


# Przydatne linki
* [Jira](https://lukaszpiaseckidev.atlassian.net/jira/software/c/projects/PAP/boards/4/backlog)
* [Dokument wymagań od Koo](https://docs.google.com/document/d/1HbTbXshl_aBdHJvJ6wtJXOhL2fLGdkbENAm6HyZKa9Y/edit?tab=t.0)

Bazy danych :
* [Wzór nowej bazy danych](APAULO.xlsx)
* [Supabase z danymi](https://supabase.com/dashboard/project/bskdfwgejlgnwuwohjak/database/tables)

Zaproponowaen UI:
* [Propozycja 1](https://sikor1337.github.io/A-PAULO/APAULO.html)
* [Propozycja 2](https://sikor1337.github.io/A-PAULO/apaulo_recruitment_clubs_wdra%C5%BCanie.html)

Nagrania:
* [2025-12-08](https://drive.google.com/file/d/1r8pBNMnZSO0xudMJzs13zTNxlzXG6nbw/view?usp=drive_link)
* [2025-05-16 - SDI Solution](https://drive.google.com/file/d/1bnDum9YhBuo4Am7-GkyjC3xCaKVpHPjB/view?usp=drive_link)