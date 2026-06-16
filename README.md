# HIVEE

Marketplace para contratar prestadores de serviço, com busca, perfis públicos,
cadastro de profissionais, recomendações, chat inteligente, notificações e
suporte por tickets.

O projeto tem backend Django + DRF + Channels e frontend React + Vite. O banco
SQLite `backend/hivee.db` está versionado para facilitar testes locais.

## Visão Geral

### Principais recursos

- Busca de prestadores por cidade, categoria, texto livre e ordenação.
- Perfil público do prestador com mapa, galeria, preço, avaliação e CTAs.
- Chat flutuante global no site, com a assistente Vee.
- Chat com texto, imagem, áudio gravado no navegador e upload de mídia.
- Mini-cards de prestadores dentro do chat do site.
- Fluxos específicos para cadastro, "quero ser prestador", dúvidas e suporte.
- Abertura de tickets pelo chat e por telas dedicadas de suporte.
- Central de Ajuda pública com artigos/FAQ.
- Notificações no site e notificações best-effort por WhatsApp quando configurado.
- Recomendações, favoritos, swipe/deck e gamificação.
- RAG via Supabase opcional, usado somente quando `RAG_ENABLED=True`.

### Stack

| Camada | Tecnologias |
|---|---|
| Frontend | React 19, Vite 6, TypeScript, Tailwind v4, React Router 7, Framer Motion, GSAP, Leaflet |
| Backend | Django 5/6 compatível, Django REST Framework, Channels, Daphne, SQLite, Token Auth |
| IA | OpenAI API para chat, Whisper e visão; Supabase opcional para RAG |
| WhatsApp | WAHA API opcional |
| Docs/API | drf-spectacular e Swagger |

## Rotas do Frontend

| Rota | Descrição |
|---|---|
| `/` | Home |
| `/buscar` | Busca de prestadores |
| `/prestador/:slug` | Perfil público do prestador |
| `/recomendados` | Recomendações/deck |
| `/sou-prestador` | Cadastro/edição inicial de perfil profissional |
| `/painel` | Painel do prestador |
| `/minha-conta` | Dados do usuário |
| `/notificacoes` | Central de notificações |
| `/ajuda` | Central de Ajuda pública |
| `/ajuda/:slug` | Artigo de ajuda |
| `/suporte/novo` | Abrir ticket |
| `/suporte/tickets` | Meus tickets |
| `/suporte/tickets/:id` | Detalhe do ticket |
| `/entrar` | Login |
| `/cadastrar` | Cadastro |

O chat não usa mais a rota `/chat`. Ele abre como widget flutuante em qualquer
tela. Quando o usuário não está logado, o widget mostra atalhos para entrar,
criar conta, virar prestador e abrir a Central de Ajuda.

## Pré-requisitos

- Python 3.12 ou superior.
- Node.js 18 ou superior.
- npm.
- Git.

No Windows, os comandos abaixo assumem PowerShell.

## Instalação Local

### Backend

```powershell
cd backend
python -m venv venv
.\venv\Scripts\python.exe -m pip install -r requirements.txt
.\venv\Scripts\python.exe manage.py migrate
```

O banco `backend/hivee.db` já vem populado. Se quiser recriar dados demo:

```powershell
.\venv\Scripts\python.exe manage.py seed
.\venv\Scripts\python.exe manage.py seed_support
```

### Frontend

```powershell
cd frontend
npm install
```

## Variáveis de Ambiente

O projeto roda localmente sem `.env` para a maior parte das telas. Para usar o
agente com OpenAI, WhatsApp ou RAG, crie `backend/.env` a partir de
`backend/.env.example`.

Nunca versione `backend/.env`, `KEYS_AGENTE.md` ou exports de workflow com
credenciais.

### Usando o zip de ambiente do professor

Se você recebeu o arquivo `hivee-env-professor.zip` por fora do GitHub, ele
contém o `.env` real necessário para testar integrações externas.

1. Baixe ou clone este repositório.
2. Coloque `hivee-env-professor.zip` na raiz do projeto, ao lado de `README.md`.
3. Extraia o zip na raiz do projeto.
4. Confirme que o arquivo abaixo passou a existir:

```text
backend/.env
```

No PowerShell, a extração pode ser feita assim:

```powershell
Expand-Archive .\hivee-env-professor.zip -DestinationPath . -Force
Test-Path .\backend\.env
```

Depois rode:

```powershell
.\start-dev.ps1
```

O zip não é versionado por segurança. Ele deve ser enviado separadamente para
quem realmente precisa testar OpenAI, WhatsApp ou RAG.

### Mínimo para chat com IA

```env
OPENAI_API_KEY=sua_chave_openai
RAG_ENABLED=False
WHATSAPP_ENABLED=False
```

### RAG com Supabase, opcional

Use somente se quiser contexto RAG:

```env
RAG_ENABLED=True
SUPABASE_URL=https://...
SUPABASE_SERVICE_KEY=...
```

O Supabase é usado apenas pelo RAG do agente. O backend principal continua em
Django/SQLite neste ambiente.

### WhatsApp via WAHA, opcional

```env
WHATSAPP_ENABLED=True
WAHA_API_URL=https://sua-instancia-waha
WAHA_SESSION=hivee
WAHA_API_KEY=opcional
```

Cheque o ambiente com:

```powershell
cd backend
.\venv\Scripts\python.exe manage.py check_env
```

## Rodando o Projeto

### Backend recomendado para o chat

Use Daphne, porque o chat do site usa WebSocket:

```powershell
cd backend
.\venv\Scripts\daphne.exe -p 8000 hivee.asgi:application
```

URL backend: `http://127.0.0.1:8000`

### Frontend

```powershell
cd frontend
npm run dev
```

URL frontend: `http://localhost:5200`

O Vite faz proxy de `/api` e `/ws` para o backend na porta `8000`.

### Atalho

Na raiz do projeto, o script abaixo instala dependências ausentes, roda
migrações, semeia dados básicos quando necessário e sobe backend com Daphne +
frontend com Vite:

```powershell
.\start-dev.ps1
```

## Usuários e Admin

Admin local:

- URL: `http://127.0.0.1:8000/admin/`
- Usuário: `admin`
- Senha: `admin12345`

Se o usuário admin não existir no seu banco local, rode o seed:

```powershell
cd backend
.\venv\Scripts\python.exe manage.py seed
```

## API Principal

| Método | Rota | Descrição |
|---|---|---|
| GET | `/api/categories/` | Categorias |
| GET | `/api/tags/` | Tags/autocomplete |
| GET | `/api/cities/` | Cidades distintas |
| GET | `/api/stats/` | Estatísticas públicas |
| GET | `/api/providers/` | Lista filtrável de prestadores |
| GET | `/api/providers/:slug/` | Detalhe do prestador |
| POST | `/api/providers/` | Cria perfil de prestador |
| GET | `/api/providers/recommended/` | Recomendações |
| GET | `/api/providers/for-you/` | Deck personalizado |
| POST | `/api/providers/:slug/swipe/` | Favoritar/dispensar |
| DELETE | `/api/providers/:slug/swipe/` | Remover favorito |
| GET | `/api/providers/favorites/` | Favoritos |
| POST | `/api/auth/register/` | Criar conta |
| POST | `/api/auth/login/` | Login |
| POST | `/api/auth/logout/` | Logout |
| GET/PATCH | `/api/auth/me/` | Usuário atual |
| GET | `/api/faq/` | Artigos publicados da FAQ, público |
| GET | `/api/faq/categories/` | Categorias da FAQ, público |
| GET/POST | `/api/support/tickets/` | Listar/criar tickets |
| GET | `/api/support/tickets/:id/` | Detalhe do ticket |
| POST | `/api/support/tickets/:id/message/` | Responder ticket |
| POST | `/api/support/tickets/:id/transition/` | Mudar status |
| GET | `/api/notifications/` | Notificações |
| GET | `/api/schema/` | OpenAPI |
| GET | `/api/docs/` | Swagger |

Webhook WAHA:

```text
POST /api/agent/webhook/
```

WebSocket do chat do site:

```text
ws://localhost:5200/ws/chat/site_user_<id>/
```

O frontend monta esse WebSocket automaticamente para o usuário logado.

## Como a Vee Funciona

A Vee é a assistente comercial da HIVEE. Ela:

- pede serviço e cidade antes de recomendar;
- prioriza a mensagem atual antes de usar histórico;
- detecta quando o usuário quer suporte humano;
- abre ticket se o usuário logado pedir suporte;
- evita abrir tickets duplicados quando já existe um ticket aberto pela IA;
- direciona visitantes para cadastro/login;
- orienta quem quer se tornar prestador;
- responde dúvidas com artigos da Central de Ajuda;
- aceita áudio e imagens no chat do site;
- envia mini-cards de prestadores no chat do site;
- usa RAG apenas se estiver habilitado.

Comandos úteis do agente:

```powershell
cd backend
.\venv\Scripts\python.exe manage.py simulate_message 5511999999999 "preciso de eletricista em São Paulo"
.\venv\Scripts\python.exe manage.py run_followup
.\venv\Scripts\python.exe manage.py reset_chat_memory --yes
.\venv\Scripts\python.exe manage.py check_env
```

## Testes e Qualidade

Backend:

```powershell
cd backend
.\venv\Scripts\python.exe manage.py check
.\venv\Scripts\python.exe manage.py test
.\venv\Scripts\python.exe manage.py test agent --verbosity=1
```

Frontend:

```powershell
cd frontend
npm run typecheck
npm run build
```

O build pode avisar que alguns chunks passam de 500 kB. Isso não quebra a build;
é um aviso de otimização futura.

## Estrutura Relevante

```text
backend/
  agent/                  # Vee, WebSocket, WAHA, OpenAI, RAG opcional
  catalog/                # Prestadores, busca, suporte, notificações, demandas
  hivee/                  # Settings, ASGI, URLs
  hivee.db                # SQLite local versionado

frontend/
  src/components/         # UI, chat, cards, notificações
  src/context/            # Auth, chat, notificações
  src/pages/              # Telas da aplicação
  src/lib/api.ts          # Cliente HTTP
```

## Segurança e Segredos

Não commitar:

- `backend/.env`
- `KEYS_AGENTE.md`
- `message (1).txt`
- `hivee-env-professor.zip`
- `.run-logs/`
- `backend/logs/`
- `backend/media/`
- `frontend/node_modules/`
- `frontend/dist/`

Se uma chave real tiver sido exposta em arquivo local, revogue a chave no painel
do provedor antes de compartilhar o repositório.

## Troubleshooting

### O chat abre, mas fica desconectado

- Confirme que o backend está rodando com Daphne, não apenas `runserver`.
- Confirme que `http://localhost:5200` está usando o proxy do Vite.
- Faça login antes de testar o chat completo; visitante vê apenas CTAs.

### A Vee responde fallback de instabilidade

- Verifique `OPENAI_API_KEY`.
- Rode `python manage.py check_env`.
- Veja logs em `.run-logs/agent-daphne.err.log` se estiver usando os comandos de
  restart locais.

### Não aparecem prestadores

- Confirme que o banco tem dados:

```powershell
cd backend
.\venv\Scripts\python.exe manage.py shell -c "from catalog.models import Provider; print(Provider.objects.filter(status='approved').count())"
```

- Se necessário, rode `python manage.py seed`.

### FAQ não aparece

- Rode `python manage.py seed_support`.
- A FAQ é pública, mas tickets exigem login.

## Deploy

Para produção:

- Use `DJANGO_DEBUG=False`.
- Configure `DJANGO_SECRET_KEY`, `DJANGO_ALLOWED_HOSTS` e `DJANGO_CSRF_TRUSTED_ORIGINS`.
- Use HTTPS para cookies seguros.
- Configure CORS com domínios específicos.
- Rode ASGI com Daphne/Uvicorn para WebSocket.
- Não use SQLite para produção real.
- Mantenha OpenAI, WAHA e Supabase em variáveis de ambiente do provedor.
