# HIVEE

Marketplace de contratação de prestadores de serviço. App de **páginas reais**
(busca, perfil do prestador, cadastro, login) com visual dark + dourado,
cinematic GSAP de abertura e localização via OpenStreetMap.

> Os componentes visuais vêm das referências em `componentsui.md` (21st.dev) e
> `components.md` — usados de verdade, não recriados.

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

## Rodar

**Backend** (porta 8000):
```powershell
cd backend
python -m venv venv
.\venv\Scripts\python.exe -m pip install -r requirements.txt
.\venv\Scripts\python.exe manage.py migrate
.\venv\Scripts\python.exe manage.py seed
.\venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000
```

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
| POST   | `/api/providers/`                             | Cria perfil (requer token)           |
| POST   | `/api/auth/register/` · `/login/`             | Cria conta / autentica (retorna token) |
| GET    | `/api/auth/me/`                               | Usuário atual (Bearer Token)         |
| GET    | `/api/stats/`                                 | Totais da plataforma                 |

## Design

Tipografia grande (Space Grotesk display + Inter). Cinematic de abertura em GSAP
(scroll-pin + mockup de iPhone). Animações só em `transform`/`opacity`;
`backdrop-filter` usado de forma pontual — sem blur animado, para manter 60fps.
Respeita `prefers-reduced-motion`.
