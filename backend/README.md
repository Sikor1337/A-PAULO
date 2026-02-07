# Backend

Django REST Framework backend.

## 📋 Wymagania

- **Python:** 3.12+
- **Database:** PostgreSQL 14+
- **Inne:** pip 

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

Utwórz plik `.env` w folderze `backend/` (lub ustaw zmienne środowiskowe):

```env
# Database
DB_NAME=apaulo_db
DB_USER=postgres
DB_PASSWORD=haslo
DB_HOST=localhost
DB_PORT=5432

# Django
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
```

**Alternatywnie:** Edytuj `core/settings.py` bezpośrednio (dla dev lokalnego).

### 4. Migracje

```bash
# Wykonaj migracje
python manage.py migrate

# Utwórz superusera
python manage.py createsuperuser
```

### 5. Uruchomienie serwera

```bash
python manage.py runserver
```

Aplikacja będzie dostępna pod: **http://127.0.0.1:8000**  
Panel admin: **http://127.0.0.1:8000/admin**

## 📂 Struktura Aplikacji

```
backend/
├── core/                   # Ustawienia projektu Django
│   ├── settings.py        # Konfiguracja główna
│   ├── urls.py            # Routing główny
│   └── wsgi.py / asgi.py  # WSGI/ASGI entry points
├── authentication/         # Moduł uwierzytelniania
│   ├── models.py          # UserProfile (custom user)
│   ├── serializers.py     # Serializery JWT
│   ├── views.py           # Login, Register, Token Refresh
│   └── urls.py
├── beneficiaries/          # Moduł podopiecznych
│   ├── models.py          # Beneficiary, Group, Assignment
│   ├── serializers.py
│   ├── views.py           # CRUD endpoints
│   ├── filters.py         # Django-filters
│   └── urls.py
├── volunteers/             # Moduł wolontariuszy
│   ├── models.py          # Volunteer
│   ├── serializers.py
│   ├── views.py
│   ├── filters.py
│   └── urls.py
├── manage.py
└── requirements.txt
```

## 🔧 Główne Zależności

| Pakiet | Wersja | Opis |
|--------|--------|------|
| Django | 6.0.1 | Framework webowy |
| djangorestframework | 3.16.1 | REST API toolkit |
| djangorestframework-simplejwt | 5.5.1 | JWT authentication |
| psycopg2-binary | 2.9.11 | PostgreSQL adapter |
| django-cors-headers | 4.9.0 | CORS support |
| drf-spectacular | 0.29.0 | OpenAPI schema generator |
| django-filter | (dependency) | Filtrowanie query |

