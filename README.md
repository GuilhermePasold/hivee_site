# Hivee - Local Service Marketplace

![TypeScript](https://img.shields.io/badge/TypeScript-007ACC?style=flat-square&logo=typescript&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white)
![Django](https://img.shields.io/badge/Django-092E20?style=flat-square&logo=django&logoColor=white)
![React](https://img.shields.io/badge/React-20232A?style=flat-square&logo=react&logoColor=61DAFB)
![CSS3](https://img.shields.io/badge/CSS3-1572B6?style=flat-square&logo=css3&logoColor=white)

> Full-stack marketplace connecting local clients with independent service providers. Built with a Django REST API backend and a React TypeScript frontend dashboard.

**Award:** 1st place at Programa NASCER (SEBRAE/SC + TIFAPESC) among 60+ projects | Top 13 statewide among 2,000+ projects in Santa Catarina.

---

## Overview

Hivee is a platform where clients can post service demands and browse local professionals across categories. Service providers can register, build a profile, and receive contract requests directly through the platform.

The system was designed with clean separation between backend logic and frontend presentation, using REST API communication between layers.

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | Python 3.10+, Django, Django REST Framework |
| Frontend | React, TypeScript, CSS |
| Database | SQLite3 |
| Auth | Token-based (local storage) |

---

## Project Structure

```
hivee_site/
projetodjango/
   base/static/        # Static assets
   frontend/           # React TypeScript frontend
   project/            # Django project settings
   servicos/           # Services app (models, views, serializers)
   manage.py
   req.txt
```

---

## Features

- User registration and authentication (clients and professionals)
- Service demand posting with location tagging
- Professional profile creation and discovery
- Active contract tracking and metrics
- Role-based access (client vs. provider)

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/login/` | User authentication |
| POST | `/api/register/` | New user registration |
| POST | `/api/become-professional/` | Upgrade account to provider |
| POST | `/api/post-demand/` | Post a new service request |
| GET | `/api/contratos/` | List active contracts and metrics |

---

## Getting Started

### Prerequisites

- Python 3.10+
- Node.js 18+
- pip and npm

### Backend Setup

```bash
cd projeto_django
pip install -r req.txt
python manage.py migrate
python manage.py runserver
```

### Frontend Setup

```bash
cd projeto_django/frontend
npm install
npm start
```

---

## Author

**Guilherme Pasold** - [LinkedIn](https://linkedin.com/in/guilherme-pasold-de-queiroz) - [GitHub](https://github.com/GuilhermePasold)
