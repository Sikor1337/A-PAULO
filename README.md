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

---

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