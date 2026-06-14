# HIVEE

Marketplace de contratação de prestadores de serviço. App de **páginas reais**
(busca, perfil do prestador, cadastro, login) com visual dark + dourado,
cinematic GSAP de abertura e localização via OpenStreetMap.

> Entrega e respostas das perguntas em [ENTREGA.md](ENTREGA.md).

## Stack

| Camada    | Tecnologias                                                                       |
|-----------|------------------------------------------------------------------------------------|
| Frontend  | React 19 · Vite 6 · TypeScript · Tailwind v4 · **React Router 7** · Framer Motion · **GSAP** · React-Leaflet |
| Backend   | Django 6 · Django REST Framework · SQLite · Token Auth · Faker (seed)              |
| Geo       | OpenStreetMap / Nominatim (geocoding) · haversine no servidor                      |

## Telas (rotas)

| Rota                 | Tela                                                              |
|----------------------|------------------------------------------------------------------|
| `/`                  | Home: **cinematic GSAP** (mockup de celular) → hero → categorias → recomendados (stacked cards) → como funciona (mockup hover) → CTA |
| `/buscar`            | Busca com **filtro de cidade** (dropdown da API), categoria, ordenação — sincroniza com a URL |
| `/prestador/:slug`   | Perfil completo do prestador, com mapa Leaflet                    |
| `/recomendados`      | Lista recomendada pelo sistema (com o porquê de cada match)       |
| `/sou-prestador`     | Cadastro de profissional (autenticado)                           |
| `/entrar`, `/cadastrar` | Login / criar conta                                           |

## Pré-requisitos

- **Python 3.12 ou superior** (o Django 6 exige 3.12+). Verifique com `python --version`.
- **Node.js 18+** (LTS) e **npm** — só para o frontend. Verifique com `node --version`.
- Nada além disso: o banco (`hivee.db`) já vem no repositório, populado.

## Rodar

**Backend** (porta 8000) — comandos no **Windows / PowerShell**:
```powershell
cd backend
python -m venv venv
.\venv\Scripts\python.exe -m pip install -r requirements.txt
.\venv\Scripts\python.exe manage.py migrate
.\venv\Scripts\python.exe manage.py seed   # opcional: o hivee.db já vem populado
.\venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000
```

No **macOS / Linux** troque o caminho do Python por `venv/bin/python` (e use
`python3`):
```bash
cd backend
python3 -m venv venv
venv/bin/python -m pip install -r requirements.txt
venv/bin/python manage.py migrate
venv/bin/python manage.py seed   # opcional
venv/bin/python manage.py runserver 127.0.0.1:8000
```

> O `hivee.db` já vem versionado e populado (180 prestadores) — o `seed` acima é
> opcional. Não há nada hardcoded: o projeto roda sem `.env` (há fallbacks); para
> customizar, copie `backend/.env.example` para `backend/.env`.
>
> **Admin / docs:** http://localhost:8000/admin/ (usuário `admin`, senha
> `admin12345`) · **Swagger:** http://localhost:8000/api/docs/ ·
> **testes:** `.\venv\Scripts\python.exe manage.py test`

**Frontend** (porta 5200):
```powershell
cd frontend
npm install
npm run dev
```

Ou os dois: `./start-dev.ps1`. O Vite faz proxy de `/api` → `:8000`.

## API

| Método | Rota                                          | Descrição                            |
|--------|-----------------------------------------------|--------------------------------------|
| GET    | `/api/categories/`                            | Categorias + contagem                |
| GET    | `/api/cities/`                                | Cidades distintas (para o filtro)    |
| GET    | `/api/providers/?city=&category=&search=&ordering=` | Lista filtrável                |
| GET    | `/api/providers/recommended/?lat=&lng=`       | Top 8 com `match_score` + `match_reason` |
| GET    | `/api/providers/<slug>/`                      | Detalhe                              |
| POST   | `/api/providers/`                             | Cria perfil (requer autenticação)    |
| POST   | `/api/auth/register/` · `/login/`             | Cria conta / autentica (token no corpo + cookie httpOnly) |
| POST   | `/api/auth/logout/`                           | Limpa o cookie de autenticação       |
| GET    | `/api/auth/me/`                               | Usuário atual (cookie ou `Token` header) |
| GET    | `/api/stats/`                                 | Totais da plataforma                 |
| GET    | `/api/schema/` · `/api/docs/`                 | OpenAPI + Swagger (drf-spectacular)  |

## Design

Tipografia grande (Space Grotesk display + Inter). Cinematic de abertura em GSAP
(scroll-pin + mockup de iPhone). Animações só em `transform`/`opacity`;
`backdrop-filter` usado de forma pontual — sem blur animado, para manter 60fps.
Respeita `prefers-reduced-motion`.
