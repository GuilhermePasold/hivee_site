# Hivee - Local Service Procurement Ecosystem

Hivee is a robust marketplace ecosystem bridging local clients and independent service providers. This solution relies on a Python Django REST application core bound together with an advanced interactive React TypeScript frontend dashboard.

## System Architecture

The platform splits operations into independent layers:

1. **Backend Engine (Django Core)**
   - Database operations (SQLite 3 relational maps).
   - Core API endpoints distributing authentication schemas, dynamic provider indices, and open service request models.
2. **Interactive UI (React frontend)**
   - Context isolation handling local storage tokens.
   - Dynamic UI frameworks handling provider lookup routes.

---

## Technical Prerequisites

To install components efficiently, guarantee the existence of:
- Python (version 3.10+)
- Node.js (version 18+)
- Package Managers (`pip`, `npm`)

---

## Quickstart Deployment Guides

### 1. Backend API Layer

Navigate into the primary module path:
```bash
cd projeto_django
```

Activate the designated environment bindings:
- **Windows PowerShell:**
  ```powershell
  venv\Scripts\Activate.ps1
  ```
- **Linux / macOS:**
  ```bash
  source venv/bin/activate
  ```

Apply pending constraints mapping database triggers:
```bash
python manage.py makemigrations
python manage.py migrate
```

Initiate execution contexts:
```bash
python manage.py runserver 0.0.0.0:8000
```

### 2. Frontend Interface Layer

Move into interface trees:
```bash
cd projeto_django/frontend
```

Retrieve dependency trees:
```bash
npm install
```

Boot visual instances:
```bash
npm run dev
```

---

## Endpoint Documentation

Direct connections map across endpoints:

| Endpoint Path | Purpose | Method |
| --- | --- | --- |
| `/api/login/` | Identifies session parameters | POST |
| `/api/register/` | Writes initial users | POST |
| `/api/become-professional/` | Elevates permissions | POST |
| `/api/post-demand/` | Saves localized tasks | POST |
| `/api/contratos/` | Queries active metrics | GET |
