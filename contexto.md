# HIVEE — Contexto do Projeto

> Marketplace de contratação de prestadores de serviço (eletricista, encanador, pedreiro, pintor, etc.).
> App de **páginas reais** com React Router no front e uma API REST de verdade no back — todo clique leva a uma tela, todo filtro muda os resultados de fato.

---

## 1. Visão geral

HIVEE é uma plataforma onde o usuário busca, filtra e compara profissionais por categoria, cidade e proximidade, vê o perfil completo de cada um (com mapa), recebe recomendações com um *score* de match, e pode criar conta para se cadastrar como prestador.

Princípios de produto que guiam o código:

- **Se tem clique, tem tela.** Nada de SPA de uma página só. Cada ação é uma rota real (perfil, busca, cadastro, login, minha conta).
- **Tipografia grande e ousada, pouco texto.** Headings enormes, parágrafos curtos.
- **Animações suaves e performáticas (60fps).** Anima só `transform`/`opacity`; nunca `filter`/`blur`/`backdrop-filter` em elementos fixos ou em grids grandes.
- **Backend com lógica de verdade.** Filtro de cidade, busca, ordenação por distância (haversine) e score de recomendação são todos computados sobre o banco — nada hardcoded.

---

## 2. Stack

### Frontend (`frontend/`)
- **React 19** + **Vite 6** + **TypeScript 5**
- **React Router 7** (`react-router-dom`)
- **Tailwind CSS v4** (via `@tailwindcss/vite`) com tokens shadcn-compatíveis em `@theme`
- **Framer Motion** (animações de UI) + **GSAP** (intro cinematográfica com scroll-pin)
- **React-Leaflet 5** + **Leaflet** (mapa no perfil do prestador)
- **lucide-react** e **@phosphor-icons/react** (ícones)
- Utilitário `cn` (clsx + tailwind-merge) em [`src/lib/utils.ts`](frontend/src/lib/utils.ts)
- Alias `@` → `frontend/src`
- Dev na **porta 5200** (5173–5179 ficam ocupadas por outros projetos), com proxy `/api` → `127.0.0.1:8000`

### Backend (`backend/`)
- **Django 5.2+** + **Django REST Framework** + **django-cors-headers**
- **SQLite** (`backend/hivee.db`)
- **Faker** (`pt_BR`) para gerar dados de seed
- App único: `catalog`
- Autenticação por **Token** (DRF `authtoken`)
- Só dependências *puro-Python* — instala limpo em Python 3.14 (sem wheels para compilar)

---

## 3. Estrutura de pastas

```
HIVEE SITE/
├─ contexto.md            ← este arquivo
├─ start-dev.ps1          ← sobe backend + frontend (cria venv/seed na 1ª vez)
├─ arquivo.md             ← notas/direção
├─ components.md          ← código de referência de componentes
├─ componentsui.md        ← links do 21st.dev (referências de UI)
│
├─ backend/
│  ├─ manage.py
│  ├─ requirements.txt
│  ├─ hivee/              ← projeto Django (settings, urls, wsgi/asgi)
│  └─ catalog/            ← app único
│     ├─ models.py        ← Category, Provider
│     ├─ serializers.py   ← Provider/Category/Recommendation/auth/write
│     ├─ views.py         ← ViewSet + APIViews (filtro, score, auth, stats)
│     ├─ urls.py          ← rotas /api/...
│     ├─ geo.py           ← haversine_km
│     ├─ admin.py
│     ├─ migrations/      ← 0001_initial, 0002_provider_owner
│     └─ management/commands/seed.py   ← popula 180 prestadores
│
└─ frontend/
   ├─ index.html
   ├─ vite.config.ts      ← porta 5200 + proxy /api
   ├─ package.json
   └─ src/
      ├─ main.tsx         ← BrowserRouter + rotas + AuthProvider
      ├─ index.css        ← design tokens + classes .glass/.surface/.btn-gold
      ├─ types.ts         ← tipos da API
      ├─ lib/             ← api.ts, utils.ts, geocode.ts
      ├─ context/         ← AuthContext.tsx
      ├─ components/       ← Layout, Navbar, Footer, ProviderCard, PhoneApp, ...
      │  └─ ui/           ← componentes "reais" do 21st.dev + GlassSelect, Icon, Tilt3D
      └─ pages/           ← Home, Search, Recommended, ProviderProfile,
                            BecomeProvider, MinhaConta, Login, Register
```

---

## 4. Rotas do frontend (`src/main.tsx`)

| Rota | Página | Descrição |
|------|--------|-----------|
| `/` | `Home` | Intro cinematográfica (GSAP) → hero → categorias → recomendados → mockup → CTA |
| `/buscar` | `Search` | Busca com filtro de cidade (dropdown da API), categoria, ordenação; sincroniza com a URL |
| `/recomendados` | `Recommended` | Top 8 prestadores com score de match e motivo |
| `/prestador/:slug` | `ProviderProfile` | Perfil completo + mapa Leaflet |
| `/sou-prestador` | `BecomeProvider` | Cadastro de perfil de prestador (autenticado) |
| `/minha-conta` | `MinhaConta` | Área logada do usuário |
| `/entrar` | `Login` | Login |
| `/cadastrar` | `Register` | Criação de conta |
| `*` | `NotFound` | 404 |

Todas as rotas ficam dentro de um `<Layout>` (navbar + footer compartilhados).

---

## 5. API REST (`/api/...`)

Base montada em `hivee/urls.py` → `catalog/urls.py`.

| Método | Endpoint | O que faz |
|--------|----------|-----------|
| `GET` | `/api/categories/` | Categorias com contagem de prestadores |
| `GET` | `/api/cities/` | Cidades distintas (com contagem) para o dropdown |
| `GET` | `/api/stats/` | Métricas da plataforma (totais, nota média, jobs) |
| `GET` | `/api/providers/` | Lista paginada, com filtros e ordenação |
| `POST` | `/api/providers/` | Cria perfil de prestador (**autenticado**) |
| `GET` | `/api/providers/recommended/` | Top 8 por score de match |
| `GET` | `/api/providers/<slug>/` | Detalhe de um prestador |
| `POST` | `/api/auth/register/` | Cria usuário, retorna token + user |
| `POST` | `/api/auth/login/` | Autentica por e-mail/senha, retorna token |
| `GET` | `/api/auth/me/` | Usuário atual (**autenticado**) |

### Filtros de `/api/providers/` (query params)
- `category` — slug da categoria
- `city` — **`icontains`**, filtra de verdade
- `search` — busca por termos em nome/headline/categoria/skills (todos os termos precisam casar)
- `lat` + `lng` — calcula `distance_km` por haversine
- `ordering` — `distance` | `-rating` | `hourly_rate` | (default: relevância = top_rated → rating → reviews)
- `page` + `page_size` (default 9, máx 48)

### Score de recomendação (`views._score`)
Pontuação 0–100 (clampada em 40–99) combinando: nota (até 42), nº de avaliações (até 16), jobs feitos (até 10), verificado (8) e proximidade (até 24, decai até ~30 km). Acompanha um `match_reason` em texto (ex.: *"Recomendado por Nota 4.8, 210 avaliações, a 3.2 km de você, responde em 1 hora."*).

---

## 6. Modelos de dados (`catalog/models.py`)

- **`Category`** — `name`, `slug`, `icon` (nome do ícone lucide em PascalCase), `tagline`, `accent` (hex), `order`.
- **`Provider`** — `name`, `slug`, `headline`, `bio`, FK `category`, FK opcional `owner` (User), `avatar_url`/`cover_url`, `rating`/`reviews_count`/`jobs_done`, `hourly_rate`/`currency`, localização (`city`/`neighborhood`/`state`/`latitude`/`longitude`), flags `verified`/`top_rated`, `response_time`, `availability`, `skills` (JSON list), `member_since`.

Ordenação default de Provider: `-top_rated`, `-rating`, `-reviews_count`.

---

## 7. Autenticação

- **Backend:** `TokenAuthentication` (DRF). Registro/login geram um token; rotas protegidas (`/auth/me`, criar prestador) exigem `Authorization: Token <key>`. O `username` é o próprio e-mail.
- **Frontend:** `AuthContext` guarda o token no `localStorage` (chave `hivee_token`) e injeta o header em `lib/api.ts`. O `UserSerializer` expõe `is_provider` e `provider_slug` para a UI saber se o usuário já tem perfil.

---

## 8. Design & tema (`src/index.css`)

- **Dark mode** com fundo quase-preto (`#09090b`) e **acento dourado** (`--color-gold-*`).
- Fonte única em todo o site: **Inter** (sans e display) — combina com a intro cinematográfica.
- Tokens shadcn-compatíveis: `--color-background/foreground/muted/muted-foreground/card/border`.
- Classes utilitárias: `.glass` (chrome translúcido), `.surface` (cards com look de liquid-glass), `.btn-gold`.

### Regras de performance (não-negociáveis)
- **Nunca animar `backdrop-filter`/`blur`/`filter`/`drop-shadow`/`mix-blend-mode`.** Mesmo estático, `backdrop-filter` em elemento **fixo** (navbar) ou em **grid de muitos cards** repinta o blur a cada frame de scroll → trava. Por isso navbar e cards usam tinta translúcida sólida (sobre o fundo quase-preto o blur não teria nada para borrar — o visual fica idêntico).
- **Sem transform 3D sobre `backdrop-filter`** (combo mais caro que existe).
- **Animação ambiente infinita → `@keyframes` CSS** (roda no compositor), nunca `framer-motion repeat: Infinity` (roda em JS na main thread e compete com o scroll).
- Animar só `transform` e `opacity`.

### Componentes de referência (em `src/components/ui/`)
Trazidos do **21st.dev** (registry shadcn) e adaptados — não recriados do zero:
`cinematic-landing-hero` (GSAP scroll-pin + mockup de iPhone), `minimalist-hero`, `nav-header` (cursor deslizante → virou `Navbar`), `section-with-mockup`, `stacked-cards-interaction`.

---

## 9. Como rodar

### Atalho (cria venv, migra, faz seed e sobe os dois)
```powershell
./start-dev.ps1
```

### Manual
**Backend** (Django em `:8000`):
```powershell
cd backend
.\venv\Scripts\python.exe manage.py migrate
.\venv\Scripts\python.exe manage.py seed      # 180 prestadores (use --count N p/ variar)
.\venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000
```

**Frontend** (Vite em `:5200`):
```powershell
cd frontend
npm install
npm run dev
```

Acesse **http://localhost:5200** (o Vite faz proxy de `/api` para o Django).

### Scripts npm úteis
- `npm run dev` — dev server (porta 5200)
- `npm run build` — build de produção
- `npm run typecheck` — `tsc --noEmit`
- `npm run preview` — preview do build (porta 4173)

---

## 10. Seed de dados (`catalog/management/commands/seed.py`)

`python manage.py seed` gera **180 prestadores** fictícios mas realistas com **Faker pt_BR**, distribuídos por categorias (Reformas & Construção, Elétrica, Encanamento, etc.), cidades reais e coordenadas. O comando é `@transaction.atomic`.

> ⚠️ **Python 3.14 / console Windows:** não emita emoji em management commands — o console cp1252 quebra com `UnicodeEncodeError`, e como o seed é atômico um erro causa rollback de tudo.

---

## 11. Notas de ambiente

- **Plataforma:** Windows 10, PowerShell. Use sintaxe PS (`$env:VAR`, `$null`, backtick para continuação).
- **Python 3.14:** Django/DRF/Faker são puro-Python → instalam sem compilar.
- O `SECRET_KEY` em `settings.py` é de dev; `DEBUG=True` e `CORS_ALLOW_ALL_ORIGINS=True` são conveniências de desenvolvimento — trocar antes de produção.
- Arquivos de referência de UI ficam na raiz: `arquivo.md`, `components.md`, `componentsui.md`. Ao construir UI, **ler essas referências primeiro** e reaproveitar o que já existe em vez de improvisar.
