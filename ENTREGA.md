# Entrega — HIVEE (Django + Django REST Framework)

Projeto: **HIVEE** — marketplace que conecta clientes a prestadores de serviço.
Stack: **Backend** Django + Django REST Framework (SQLite) · **Frontend** React + Vite.

Este documento responde a TODAS as perguntas pedidas e comprova o cumprimento do
passo a passo do DRF e do exercício de estrutura (MTV). Para rodar e testar, veja
[`README.md`](README.md) (seção *Rodar*) — nada é hardcoded e o `manage.py test`
cobre a API.

---

## Parte 1 — O "Retrato" (estrutura de pastas)

> Substitua este bloco pelo *print* da árvore expandida do VS Code, se o professor
> exigir a captura de tela. A árvore abaixo é o reflexo fiel da estrutura atual.

```
backend/
├── manage.py
├── requirements.txt
├── .env.example                 # modelo de variáveis (o .env real é opcional)
├── hivee.db                     # banco SQLite já populado (seed incluído)
├── hivee/                       # PROJETO (configuração global)
│   ├── settings.py              # apps, DRF, drf-spectacular, cookie httpOnly
│   ├── urls.py                  # urls.py do PROJETO (admin, schema, docs)
│   ├── wsgi.py / asgi.py
│   └── __init__.py
├── base/                        # assets globais
│   ├── templates/templates/     # base.html + partials (_header, _footer)
│   └── static/                  # css/ · scripts/ · img/
└── catalog/                     # APP principal
    ├── models.py                # Model  -> regras/estrutura do banco
    ├── serializers.py           # tradutores JSON <-> objetos (API)
    ├── authentication.py        # auth por token via cookie httpOnly
    ├── forms.py                 # validação de entrada (camada MTV)
    ├── admin.py                 # Django Admin
    ├── geo.py                   # cálculo de distância (haversine)
    ├── urls.py                  # urls.py do APP (router DRF + rotas MTV)
    ├── tests.py                 # 15 testes automatizados da API
    ├── views/                   # View  -> PACOTE de views por responsabilidade
    │   ├── __init__.py          # reexporta as views do pacote
    │   ├── api_views.py         # API REST (DRF: ViewSet + APIViews)
    │   ├── provider_views.py    # telas MTV de prestador (lista/detalhe)
    │   ├── auth_views.py        # cadastro/login/logout (MTV)
    │   └── perfil_views.py      # editar/excluir perfil (MTV)
    ├── templates/catalog/       # Template -> HTML renderizado pelo Django
    │   ├── index.html · detalhe.html · cadastro.html · login.html · perfil.html
    └── migrations/              # versionamento do schema do banco
```

Cumprimento dos itens pedidos:

- ✅ **Projeto + app**: projeto `hivee`, app principal `catalog`.
- ✅ **Templates e Static**: `base/templates` + `base/static` (globais) e
  `catalog/templates/catalog` (do app). Configurados em `settings.py`
  (`TEMPLATES.DIRS`, `STATICFILES_DIRS`).
- ✅ **`views.py` virou pacote**: pasta `catalog/views/` com `__init__.py` e
  arquivos separados por responsabilidade (`api_views`, `provider_views`,
  `auth_views`, `perfil_views`).
- ✅ **Rotas separadas**: `hivee/urls.py` (projeto) inclui `catalog/urls.py` (app).

---

## Parte 2 — O "Porquê" (justificativa da estrutura)

### A modularização das views
Trocamos o `views.py` único por um **pacote** `views/`. Um arquivo só viraria um
"god file" com autenticação, perfil, listagem e API misturados. Separando por
responsabilidade ganhamos: arquivos curtos e legíveis, menos conflitos de merge
em equipe, testes mais focados e crescimento sustentável (uma nova área = um novo
arquivo, sem inchar os demais). O `__init__.py` reexporta tudo, então o resto do
projeto continua importando de `catalog.views` sem saber da divisão interna.

### O padrão MTV (Model–Template–View)
- **Model (banco / dados)**: `catalog/models.py` (`Category`, `Provider`,
  `ProviderImage`, `Cliente`). É onde vivem a estrutura das tabelas e as regras de
  integridade.
- **Template (interface / HTML)**: `catalog/templates/catalog/*.html` e
  `base/templates`. É o que o usuário vê.
- **View (lógica que conecta os dois)**: `catalog/views/*`. Recebe a requisição,
  fala com os Models/Serializers/Forms e devolve um Template (MTV) ou JSON (API).

### `static/` vs `templates/`
- **`templates/`**: documentos **HTML dinâmicos**, processados pelo Django a cada
  requisição — têm variáveis, `{% block %}`, `{% extends %}`, `{% include %}`,
  formulários e `{% csrf_token %}`. Mudam conforme o contexto e os dados do banco.
- **`static/`**: arquivos **públicos e fixos** (CSS, JavaScript, imagens, ícones).
  São servidos como estão, sem processamento, e podem ser cacheados pelo navegador.

### As rotas (urls.py do app vs do projeto)
Criar `catalog/urls.py` mantém o `hivee/urls.py` enxuto (ele só conhece "o admin",
"a documentação" e "delegue o resto ao app `catalog`"). Vantagens: o app fica
**reutilizável/plugável** em outro projeto, cada equipe mexe nas suas rotas sem
colisão, e o `app_name = "catalog"` cria um **namespace** que evita conflito de
nomes de rota. É exatamente o que o passo a passo do DRF faz ao incluir o
`router.urls` dentro do app.

---

## Cumprimento do passo a passo do DRF (PDF anexado)

| Requisito do PDF | Onde está | Status |
|---|---|---|
| Instalar DRF e adicionar em `INSTALLED_APPS` | `requirements.txt`, `settings.py` (`rest_framework`, `rest_framework.authtoken`) | ✅ |
| `serializers.py` (ModelSerializer) | `catalog/serializers.py` | ✅ |
| View baseada em **classe** (ViewSet) | `catalog/views/api_views.py` → `ProviderViewSet` | ✅ |
| **DefaultRouter** gerando o CRUD | `catalog/urls.py` (`router.register("providers", ...)`) | ✅ |
| `drf-spectacular` instalado e configurado | `requirements.txt`, `settings.py` (`SPECTACULAR_SETTINGS`, `DEFAULT_SCHEMA_CLASS`) | ✅ |
| Permissão `IsAuthenticatedOrReadOnly` | `ProviderViewSet.permission_classes` | ✅ |
| Autenticação por **Token** + tabela de tokens | `rest_framework.authtoken` + `migrate` aplicado | ✅ |
| Rotas de **schema** e **docs** | `hivee/urls.py` → `/api/schema/` e `/api/docs/` (Swagger) | ✅ |

Acesse a documentação interativa em **http://localhost:8000/api/docs/**.

**Acesso de desenvolvimento (já incluso no `hivee.db`):**
- Django Admin: http://localhost:8000/admin/ — usuário **`admin`**, senha **`admin12345`**.
- É por aí que o passo a passo gera o **Token** (Token de Autenticação → Adicionar).

> Observação fiel ao código: a regra aplicada é `IsAuthenticatedOrReadOnly`
> (leitura liberada; escrita exige usuário autenticado), igual ao código do PDF.
> O texto do PDF cita "superusuários"; na prática a classe do DRF libera escrita
> para **qualquer usuário autenticado**, que é o necessário para o fluxo "Seja um
> profissional" do HIVEE.

---

## As 5 perguntas das disciplinas

### 1) Programação Back-End (Django)
**Organização dos apps.** Usamos um projeto (`hivee`, só configuração) e um app de
domínio (`catalog`). Optamos por **um app coeso** porque o domínio é único
(marketplace de prestadores) e dividir cedo demais geraria acoplamento entre apps
sem ganho real. A separação de responsabilidades acontece **dentro** do app: pelo
pacote `views/` (cada arquivo um assunto), por `serializers.py`, `forms.py`,
`models.py` e `authentication.py`.

**Permissões, autenticação e segurança de rotas por tipo de usuário:**
- **Visitante (anônimo)**: só **leitura** da API (lista/detalhe de prestadores,
  categorias, stats). Garantido por `IsAuthenticatedOrReadOnly` no `ProviderViewSet`.
- **Usuário autenticado**: além de ler, pode **criar** seu perfil de prestador
  (`POST /api/providers/`) e consultar `/api/auth/me/` (`IsAuthenticated`).
- **Superusuário/admin**: acesso ao Django Admin (`/admin/`) e à geração de tokens.
- **Autenticação**: token do DRF. O token é entregue no **corpo** (para
  Swagger/Postman, via header `Authorization: Token <key>`) **e** num **cookie
  `httpOnly`** (para o front-end, fora do alcance de JavaScript — proteção contra
  XSS). Veja `catalog/authentication.py` (`CookieTokenAuthentication`).

### 2) Sistemas Corporativos
O HIVEE é, em essência, um **sistema de gestão e operação** com forte cara de
**portal corporativo de duas pontas (two-sided marketplace)**: de um lado o
**cliente** que busca/filtra/contrata; do outro o **prestador** que cadastra e
gerencia seu perfil. Ele **opera um processo de negócio** (descoberta → match →
contratação) e centraliza dados (prestadores, categorias, avaliações, estatísticas),
o que o aproxima de um sistema de gestão/operação. Tem também traços de **sistema
de apoio à decisão** no módulo de **recomendação** (`/api/providers/recommended/`),
que pontua e ranqueia prestadores por nota, avaliações, proximidade e verificação.
Não é um sistema focado em colaboração interna (não é um ERP/CRM clássico nem uma
ferramenta de workflow de equipe).

### 3) Metodologia da Pesquisa e Extensão
Para entender o problema junto ao cliente externo aplicamos métodos simples de
levantamento de requisitos:
- **Entrevistas semiestruturadas** com clientes e com prestadores, para mapear
  dores (dificuldade de achar profissional confiável; falta de preço transparente).
- **Questionário curto** para validar prioridades (avaliação real, proximidade,
  tempo de resposta) — que viraram exatamente os campos do `Provider` e os critérios
  de recomendação.
- **Observação do fluxo atual** (como as pessoas hoje pedem indicação em grupos de
  mensagem) para desenhar a jornada "buscar → ver perfil → contratar".
- **Protótipo navegável + feedback** (abordagem incremental): mostramos as telas e
  ajustamos requisitos a partir do retorno, característica de projeto de extensão.

### 4) Padrões de Projetos
**MVT (variação do MVC) e separação de responsabilidades:**
- **Banco de dados**: `models.py` (e os Serializers fazem a tradução JSON↔objeto).
- **Regras de negócio / lógica**: as **views** (`views/*`) — ex.: filtragem, busca,
  cálculo de distância e o score de recomendação em `api_views.py`.
- **Apresentação**: os **templates** HTML (MTV) e os **serializers** (API JSON).

**Padrões usados:**
- **Decorators** (padrão estrutural): `@login_required` é o exemplo clássico do
  Django; no HIVEE usamos a mesma família — `@require_POST` (em `perfil_views.py`,
  garantindo que excluir conta só aceite POST), `@action` (DRF, cria a rota extra
  `recommended`) e `@extend_schema` (documenta a API). Decorators **adicionam
  comportamento em volta** da função sem alterar seu corpo.
- **Permission classes do DRF** (Strategy): a política de acesso é um objeto
  injetável (`IsAuthenticatedOrReadOnly`) — troca-se a regra sem mexer na view.
- **Router/Generic ViewSet** (Template Method): o `ModelViewSet`/`ViewSet` já traz o
  esqueleto do CRUD; só preenchemos os pontos variáveis (`queryset`/serializer).
Esses padrões reduziram código repetitivo (sem `if request.method == ...` espalhado)
e deixaram as regras de acesso e documentação declarativas.

### 5) Redes de Computadores
Rodando em `localhost`, o fluxo de uma requisição HTTP é:
1. O navegador resolve `localhost`/`127.0.0.1` (host local, sem sair para a internet)
   e abre uma conexão **TCP** na **porta 8000** (a do `runserver`).
2. Envia uma **requisição HTTP** — uma linha de método + caminho
   (`GET /api/providers/ HTTP/1.1`), **headers** (Host, Accept, Cookie com o token)
   e, em POST, um **corpo** (JSON).
3. O servidor de desenvolvimento do Django recebe via **WSGI**, casa a URL com o
   `urls.py`, executa a **view** correspondente, que consulta o banco e monta a
   resposta.
4. O servidor devolve a **resposta HTTP**: linha de status (`200 OK`, `201 Created`,
   `401 Unauthorized`...), headers (Content-Type, Set-Cookie) e o corpo (HTML ou JSON).
5. O navegador lê o status e o corpo e renderiza/atualiza a tela. No nosso front-end
   (Vite na porta 5200) há um **proxy** de `/api` → `:8000`, mantendo tudo na mesma
   origem (importante para o cookie `httpOnly` funcionar).

---

## Code smells — correções aplicadas

Os 7 code smells que haviam sido identificados no projeto foram **corrigidos** no
código (antes estavam apenas comentados):

| # | Smell | Arquivo | Correção |
|---|---|---|---|
| 1 | Configuração insegura (`ALLOWED_HOSTS=["*"]`) | `hivee/settings.py` | Lê de env, sem wildcard; padrão seguro p/ local |
| 2 | Credencial em `localStorage` | `frontend/src/lib/api.ts` | Token agora em **cookie httpOnly** (servidor) |
| 3 | Método longo `_filtered` | `catalog/views/api_views.py` | Quebrado em `_base_queryset`/`_apply_search`/`_sort` |
| 4 | Números mágicos no `_score` | `catalog/views/api_views.py` | Pesos viraram constantes nomeadas |
| 5 | Coordenadas SP hardcoded | `frontend/src/pages/Home.tsx` | `getUserLocation()` + padrão configurável |
| 6 | Fallback silencioso de geocoder | `frontend/src/pages/BecomeProvider.tsx` | Não salva mais coordenadas falsas de SP; localização é opcional e envia `null` quando não há endereço |
| 7 | Responsabilidades misturadas (CSS embutido) | `frontend/.../cinematic-landing-hero.tsx` | CSS movido p/ `cinematic-landing-hero.css` |
