# SUPER AGENTE HIVEE — Prompt de Implementação para Agente de Código

## Status da Implementacao - revisado em 2026-06-14

Legenda: `[x]` feito, `[~]` feito parcialmente, `[ ]` pendente.

### Regras Gerais

| Item | Status | Observacao |
|---|---:|---|
| R1 - Leitura dos arquivos obrigatorios | [x] | Arquivos de backend e frontend foram lidos antes das alteracoes. |
| R2 - Execucao sequencial por sprints | [~] | Sprints foram implementadas em uma passada unica; validacoes foram feitas, mas sem pausa manual entre sprints. |
| R3 - Gerenciamento de contexto | [x] | Nao foi necessario abrir nova sessao. |
| R4 - Buscas na web quando necessario | [x] | WAHA foi conferido na documentacao oficial. |
| R5 - Preservar arquivos existentes | [x] | Alteracoes foram feitas de forma localizada. |
| R6 - Sistema de logs sem `print()` no app `agent` | [x] | Modulos do `agent` usam `logging.getLogger(__name__)`. |
| R7 - Criterio final de pronto | [~] | Check, testes, Daphne e build passam; RAG ficou opcional e nao bloqueia o ambiente. |

### Sprint 0 - Fundacao

| Passo | Status | Observacao |
|---|---:|---|
| 0.1 Ler arquivos do projeto | [x] | Concluido. |
| 0.2 Criar app `agent` | [x] | Criado em `backend/agent`. |
| 0.3 Settings: `agent`, `channels`, ASGI e channel layer | [x] | `daphne` tambem foi adicionado antes de `staticfiles`, exigencia do pacote. |
| 0.4 Dependencias no `requirements.txt` e install | [x] | Instalado na venv do backend. |
| 0.5 Models `ChatLead`, `Chat`, `ChatMessage` | [x] | Implementados. |
| 0.6 Migracoes | [x] | `agent.0001_initial` criada e aplicada. |
| 0.7 Admin | [x] | Implementado com filtros e busca. |
| 0.8 ASGI com WebSocket | [x] | Implementado em `hivee/asgi.py`. |
| 0.9 URLs do agent | [x] | `api/agent/webhook/` aponta para WAHA. |
| 0.10 URLs raiz | [x] | `include("agent.urls")` adicionado. |

### Sprint 1 - Core do Agente

| Passo | Status | Observacao |
|---|---:|---|
| 1.1 Buffer 12s | [x] | Implementado com `threading.Timer`; timers daemon para nao prender processo. |
| 1.2 RAG Supabase | [x] | Codigo pronto e opcional via `RAG_ENABLED`; se desligado, o agente segue sem contexto RAG. |
| 1.3 Tool `buscar_prestadores` | [x] | Implementada usando ORM; busca em `skills` adaptada para JSONField/SQLite; cidade/categoria agora toleram acento e sinonimos basicos. |
| 1.4 Core OpenAI + tool call | [x] | Implementado com cliente OpenAI lazy; fluxo agora exige cidade antes de recomendar e injeta a cidade detectada no tool call. |
| 1.5 Webhook WAHA | [x] | Implementado para payload WAHA (`event`, `payload`, `body`, `media`, `fromMe`). |
| 1.6 Adaptador WAHA | [x] | Implementado em `backend/agent/waha.py`, substituindo Evolution API. |
| 1.7 Audio Whisper | [x] | Implementado. |
| 1.8 Vision GPT-4o-mini | [x] | Implementado. |
| 1.9 Formatador blocos + delay | [x] | Implementado; delay e divisao via GPT ficam no WhatsApp, enquanto o site recebe resposta sem pausa artificial e sem custo extra de formatacao. |

### Sprint 2 - Canais

| Passo | Status | Observacao |
|---|---:|---|
| 2.1 `ChatConsumer` WebSocket | [x] | Implementado com Channels. |
| 2.2 `ChatWidget` React | [x] | Implementado responsivo, compilando, com mini-card de prestador apenas para o site. |
| 2.3 `ChatPage` | [~] | Arquivo legado mantido, mas a rota `/chat` foi removida do router em favor do chat flutuante global. |
| 2.4 Botao "Enviar mensagem" | [x] | Botao do perfil agora abre o chat global com rascunho contextual, sem navegar para `/chat`. |
| 2.5 Rota `/chat` | [x] | Rota removida do React Router; `/chat` cai no 404 interno da SPA. |
| 2.6 Variaveis `.env` | [x] | `OPENAI_API_KEY`, `RAG_ENABLED=False`, `WAHA_API_URL`, `WAHA_SESSION` e `WHATSAPP_ENABLED=True` configurados. |

### Sprint 3 - Follow-up + Polimento

| Passo | Status | Observacao |
|---|---:|---|
| 3.1 Follow-up | [x] | Implementado usando WAHA. |
| 3.2 Command `run_followup` | [x] | Implementado. |
| 3.3 Scheduler APScheduler | [x] | Implementado em `AgentConfig.ready()`. |
| 3.4 Testes com mock | [x] | `python manage.py test agent --verbosity=1` passou com 7 testes. |
| 3.5 Command `simulate_message` | [~] | Implementado e segura o processo ate o buffer disparar; fluxo real ainda depende OpenAI/RAG/WAHA configurados. |
| 3.6 Command `check_env` | [x] | Implementado; agora valida OpenAI, Supabase e WAHA. |
| 3.7 Verificacao final | [x] | `check_env`, `check`, testes, Daphne, WebSocket do site e build passaram sem exigir Supabase. |

### Validacoes ja executadas

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py showmigrations agent
python manage.py test agent --verbosity=2
npm run build
daphne -p 8000 hivee.asgi:application
```

### Rodada de feedback - chat do site

| Item | Status | Observacao |
|---|---:|---|
| Perguntar cidade antes de listar/recomendar | [x] | Backend detecta cidade no historico; sem cidade, responde apenas perguntando a cidade. |
| Recomendar mais de um prestador quando houver opcoes boas | [x] | Tool limitada a ate 2 prestadores e prompt pede apresentar as duas opcoes quando retornadas. |
| Link do perfil na resposta | [x] | Prompt exige URL exata retornada pela ferramenta. |
| Mini-perfil visual no chat do site | [x] | WebSocket envia evento `provider_cards`; React renderiza avatar, nota, cidade, preco e botao `Ver perfil`. |
| Reduzir sensacao de "digitando para sempre" no site | [x] | Removido delay entre blocos no canal site; delay permanece no WhatsApp. |
| Consumo de tokens | [~] | Logs `OpenAI tokens[...]` foram instrumentados; ainda nao ha dashboard/agregado por conversa. |

### Rodada de otimizacao - 2026-06-15

| Item | Status | Observacao |
|---|---:|---|
| Buffer funcional por canal | [x] | WhatsApp usa debounce maior; site usa debounce curto para juntar mensagens separadas sem parecer travado. |
| Busca direta antes da OpenAI | [x] | Para casos comuns, o backend detecta cidade/servico, consulta o ORM e usa OpenAI so para redigir a recomendacao. |
| Sem resultado na cidade | [x] | Resposta deterministica sugere cidades alternativas e termina com pergunta. |
| Follow-up quando usuario nao responde | [x] | Corrigido para disparar quando a ultima mensagem foi do bot; roda em intervalo configuravel. |
| WAHA seen/presence | [x] | Webhook envia `sendSeen`; typing/presence segue manual no envio. |
| Tool schema estrito | [x] | `buscar_prestadores` agora usa `strict=True` e `additionalProperties=False`. |
| Reset de memoria de testes | [x] | Criado `python manage.py reset_chat_memory --yes`; memoria real foi limpa apos os smokes. |

### Rodada de produto - vendedor consultivo e chat global

| Item | Status | Observacao |
|---|---:|---|
| Prompt em JSON | [x] | `SYSTEM_PROMPT` agora e uma politica JSON compacta com identidade, estrategia comercial, regras duras e formato de resposta. |
| Agente vendedor consultivo | [x] | Prompt e fluxo reforcam descoberta, prova social, baixa pressao, objecoes e pergunta final de proximo passo. |
| Chat flutuante global | [x] | Criado `ChatProvider`; icone fixo no canto inferior direito em todas as telas. |
| Remover fluxo `/chat` do CTA | [x] | Botao do perfil abre o chat global com rascunho contextual; rota `/chat` foi removida do router. |
| Imagem/audio no chat do site | [x] | WebSocket aceita upload base64; imagem passa por Vision e audio por Whisper antes de entrar no buffer. |
| Teste visual com Playwright | [x] | Smoke confirmou botao global e `/chat` caindo no 404 interno da SPA. |
| Pesquisa de libs/repos | [x] | Avaliados Agents SDK, LangGraph e SalesGPT; mantida arquitetura Django direta por ser menor custo/latencia agora. |

### Rodada de suporte, cadastro e prestador - 2026-06-15

| Item | Status | Observacao |
|---|---:|---|
| Integracao com suporte/tickets | [x] | Intencao explicita de suporte humano abre `SupportTicket` para usuario logado e notifica staff. Sem conta, orienta cadastro. |
| Duvidas gerais e FAQ | [x] | FAQ/categorias agora sao publicas; Vee busca artigo publicado e direciona para `/ajuda/{slug}`. |
| Usuario sem cadastro | [x] | Chat guest mostra CTAs imediatos para criar conta, entrar, ser prestador e central de ajuda. |
| Quero ser prestador | [x] | Agente detecta intencao de prestador e direciona para `/sou-prestador`, ou informa status/perfil quando ja existir. |
| Testes de regressao | [x] | `python manage.py test agent --verbosity=2` passou com 18 testes cobrindo suporte, FAQ, cadastro e prestador. |

### Pendencias objetivas

- [ ] Preencher `SUPABASE_URL` no `backend/.env` somente quando `RAG_ENABLED=True`.
- [ ] Preencher `SUPABASE_SERVICE_KEY` no `backend/.env` somente quando `RAG_ENABLED=True`.
- [ ] Confirmar/criar tabela `documents` com `embedding vector(1536)`.
- [ ] Confirmar/criar RPC `match_documents`.
- [x] Reiniciar Daphne depois das ultimas alteracoes WAHA/RAG.
- [ ] Testar um webhook real vindo da WAHA com sessao autenticada.

### Correcao emergencial do catalogo

- [x] Restaurados os prestadores visiveis na base local: 180 seeds foram marcados como `approved`.
- [x] Corrigido `catalog/management/commands/seed.py` para criar prestadores demo com `status="approved"`.
- [x] Validado `/api/providers/?page_size=1`: retorna `count=180`.

### Correcao do chat do site

- [x] Chat do site exige usuario autenticado no frontend e no WebSocket.
- [x] WebSocket do site autentica pelo cookie httpOnly `hivee_token`.
- [x] Canal site nao usa mais buffer de 12s; processa imediatamente.
- [x] Historico enviado para OpenAI converte `bot` para `assistant`, evitando erro 400 em mensagens subsequentes.
- [x] Vite proxy encaminha `/ws` para Daphne, preservando cookies no desenvolvimento.

---

> Este documento é um **plano executável** para um agente de código (Codex, Claude Code, etc.).
> O agente deve lê-lo por completo ANTES de começar a codificar e executar cada sprint na ordem.
> Cada sprint deve ser concluída e validada antes de solicitar autorização para a próxima.

---

## Sumário Executivo

Criar um **app Django `agent`** que implementa um assistente omnichannel (WhatsApp + Site). O agente:
1. Recebe mensagens via **WAHA (WhatsApp HTTP API)** (WhatsApp) ou **WebSocket** (site)
2. Acumula mensagens em **buffer de 12s** (dict + threading.Timer, sem Redis)
3. Roteia por tipo: **texto** direto, **áudio** → Whisper, **imagem** → GPT-4o-mini
4. Busca contexto no **RAG** (Supabase Vector Store — já existe)
5. Chama **tool `buscar_prestadores`** que consulta o **Django ORM** (app `catalog`)
6. GPT-4.1 recomenda o prestador ideal e envia **link do perfil**
7. Formata resposta em **blocos com delay 6s + typing indicator**
8. Salva **histórico** nos models do próprio app `agent`
9. **Follow-up** automático em chats parados >24h
10. **Chat no site** via Django Channels + React `ChatWidget`

---

## Regras para o Agente de Código

### R1. ANTES de codificar, LEIA estes arquivos do projeto

O agente DEVE ler estes arquivos para entender a estrutura existente antes de modificar qualquer coisa:

```
backend/hivee/settings.py          → Database config, INSTALLED_APPS, MIDDLEWARE
backend/hivee/urls.py              → Rotas raiz
backend/hivee/wsgi.py              → WSGI atual (não mexer)
backend/hivee/asgi.py              → ASGI (precisa adicionar WebSocket)
backend/catalog/models.py          → Provider, Category (referência para a tool)
backend/catalog/views/api_views.py → Como a API atual funciona
backend/catalog/urls.py            → Rotas do catalog
backend/requirements.txt           → Dependências atuais
backend/.env                       → Variáveis de ambiente existentes
frontend/src/main.tsx              → Rotas do React
frontend/src/lib/api.ts            → Cliente HTTP do frontend
frontend/src/pages/ProviderProfile.tsx → Botão "Enviar mensagem" (linha ~170)
frontend/src/types.ts              → Typescript interfaces
frontend/package.json              → Dependências do frontend
```

Se algum arquivo não existir ou mudou de lugar, o agente deve ajustar.

### R2. Estrutura de Sprints

Cada sprint deve ser executada **sequencialmente**. Ao final de cada sprint:

1. Rodar `python manage.py check` para validar
2. Rodar `python manage.py migrate` (se criou models)
3. Testar minimamente o que foi implementado
4. **AVISAR O USUÁRIO** via print/chat: `"✅ Sprint X concluída. Pode iniciar Sprint Y?"`
5. **AGUARDAR** resposta do usuário antes de continuar

### R3. Gerenciamento de Tokens/Contexto

Se o agente detectar que:

- O **custo de tokens está muito alto** (>80% do limite estimado)
- O **contexto está muito longo** (histórico de mensagens grande)
- A **recomendação do modelo** for iniciar uma nova sessão

O agente DEVE:
1. **Salvar o progresso** (git commit ou anotar o estado atual)
2. **Gerar um prompt de continuação** em texto puro com:
   - Sprint atual e o que já foi feito
   - Próximos passos com referência às seções deste plano
   - Estado atual dos arquivos (o que foi modificado)
3. **Imprimir o prompt** para o usuário copiar na nova sessão

### R4. Buscas na Web

O agente **DEVE** usar buscas na web sempre que precisar de informação adicional, padrões de código, documentação de bibliotecas ou exemplos de implementação. Este plano é o guia principal, mas não é exaustivo — buscar conhecimento ativamente é **incentivado**.

Regras:
- O plano de implementação é sempre a **fonte primária**
- Use buscas para complementar: docs de APIs, syntax de bibliotecas, resolução de erros, patterns Django/Python
- Se encontrar algo que contradiz o plano, **siga o plano** e anote a divergência para o usuário revisar

### R5. Modificações em Arquivos Existentes

O agente DEVE usar `edit` (não `write`) para modificar arquivos existentes, preservando o código original não relacionado à task. Use `write` apenas para arquivos novos.

### R6. Sistema de Logs

TODO arquivo .py DEVE usar `logger = logging.getLogger(__name__)` no topo. NUNCA use `print()`.

O agente DEVE criar `backend/agent/logging_config.py` com:

```python
import logging
import sys

def setup_logging():
    logger = logging.getLogger("agent")
    logger.setLevel(logging.DEBUG)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.DEBUG)

    formatter = logging.Formatter(
        "[%(asctime)s] %(name)s.%(funcName)s:%(lineno)d  %(levelname)s  %(message)s",
        datefmt="%H:%M:%S",
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger
```

TODO módulo do `agent` DEVE importar e usar:

```python
import logging
logger = logging.getLogger(__name__)
# ...
logger.info("Mensagem processada para %s", telefone)
logger.error("Falha no RAG: %s", e)
```

### R7. Finalização — Critério de "Pronto"

O sistema está **pronto** quando:

1. `python manage.py check` passa sem erros
2. `python manage.py test agent` passa todos os testes
3. O servidor **Daphne** sobe sem erros: `daphne -p 8000 hivee.asgi:application`
4. O comando `python manage.py simulate_message --telefone=5511999999999 --mensagem="preciso de um eletricista"` roda e mostra o log completo do fluxo
5. O `ChatWidget` no frontend compila: `cd frontend && npm run build`

Se todos os 5 passos funcionarem, o agente deve reportar: **"✅ Sistema pronto. Servidor rodando em Daphne na porta 8000. WebSocket em /ws/chat/. Webhook em /api/agent/webhook/."**

---

## Sprint 0 — Fundação (Leitura + Setup)

### Objetivo
Configurar o app `agent`, models, settings, dependências.

### Passos

#### 0.1 Ler arquivos do projeto (lista R1 acima)

#### 0.2 Criar app `agent`

```bash
cd C:\Users\guipa\Documents\HIVEE SITE\backend
python manage.py startapp agent
```

#### 0.3 Adicionar ao `settings.py`

```python
INSTALLED_APPS = [
    ...
    "catalog",
    "agent",
    "channels",
]

ASGI_APPLICATION = "hivee.asgi.application"

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels.layers.InMemoryChannelLayer",
    },
}
```

#### 0.4 Adicionar ao `requirements.txt`

```
openai>=1.0.0
supabase>=2.0.0
channels>=4.0.0
daphne>=4.0.0
APScheduler>=3.10.0
requests>=2.31.0
```

Rodar `pip install -r requirements.txt`

#### 0.5 Criar `backend/agent/models.py`

```python
from django.db import models


class ChatLead(models.Model):
    telefone = models.CharField(max_length=20, unique=True, verbose_name="Telefone/ID")
    nome_wpp = models.CharField(max_length=200, blank=True, default="", verbose_name="Nome WhatsApp")
    nome_site = models.CharField(max_length=200, blank=True, default="", verbose_name="Nome no Site")
    canal_origem = models.CharField(
        max_length=20,
        choices=[("whatsapp", "WhatsApp"), ("site", "Site")],
        default="whatsapp",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Lead do Chat"
        verbose_name_plural = "Leads do Chat"

    def __str__(self):
        return f"{self.nome_wpp or self.nome_site or self.telefone} ({self.canal_origem})"


class Chat(models.Model):
    lead = models.ForeignKey(ChatLead, on_delete=models.CASCADE, related_name="chats")
    canal = models.CharField(max_length=20, choices=[("whatsapp", "WhatsApp"), ("site", "Site")])
    status = models.CharField(
        max_length=20,
        choices=[("active", "Ativo"), ("closed", "Encerrado")],
        default="active",
    )
    provider_recomendado = models.ForeignKey(
        "catalog.Provider",
        null=True, blank=True,
        on_delete=models.SET_NULL,
        verbose_name="Prestador recomendado",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Chat"
        verbose_name_plural = "Chats"
        ordering = ["-updated_at"]

    def __str__(self):
        return f"Chat {self.lead} - {self.get_canal_display()}"


class ChatMessage(models.Model):
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE, related_name="mensagens")
    role = models.CharField(max_length=10, choices=[("user", "Usuário"), ("bot", "Bot"), ("system", "System")])
    content = models.TextField()
    msg_type = models.CharField(max_length=20, default="text", choices=[
        ("text", "Texto"), ("audio", "Áudio"), ("image", "Imagem"),
    ])
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Mensagem"
        verbose_name_plural = "Mensagens"
        ordering = ["created_at"]

    def __str__(self):
        return f"[{self.created_at:%H:%M}] {self.role}: {self.content[:50]}..."
```

#### 0.6 Rodar migrações

```bash
python manage.py makemigrations agent
python manage.py migrate agent
python manage.py check
```

#### 0.7 Criar `backend/agent/admin.py`

```python
from django.contrib import admin
from .models import ChatLead, Chat, ChatMessage

@admin.register(ChatLead)
class ChatLeadAdmin(admin.ModelAdmin):
    list_display = ["telefone", "nome_wpp", "canal_origem", "created_at"]
    search_fields = ["telefone", "nome_wpp"]

@admin.register(Chat)
class ChatAdmin(admin.ModelAdmin):
    list_display = ["lead", "canal", "status", "provider_recomendado", "updated_at"]
    list_filter = ["status", "canal"]

@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ["chat", "role", "msg_type", "created_at", "content_preview"]
    list_filter = ["role", "msg_type"]

    def content_preview(self, obj):
        return obj.content[:60] + "..." if len(obj.content) > 60 else obj.content
```

#### 0.8 Atualizar `backend/hivee/asgi.py`

```python
import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from django.urls import re_path

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "hivee.settings")

from agent.consumers import ChatConsumer

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": URLRouter([
        re_path(r"ws/chat/(?P<telefone>\w+)/$", ChatConsumer.as_asgi()),
    ]),
})
```

#### 0.9 Criar `backend/agent/urls.py`

```python
from django.urls import path
from . import webhooks

urlpatterns = [
    path("webhook/", webhooks.waha_webhook, name="waha-webhook"),
]
```

#### 0.10 Atualizar `backend/hivee/urls.py`

Adicionar: `path("api/agent/", include("agent.urls")),`

### ✅ Validação da Sprint 0

```
python manage.py check  # sem erros
python manage.py showmigrations agent  # migrações aplicadas
```

**AVISAR USUÁRIO:** "✅ Sprint 0 concluída. App agent criado, models migrados, settings configurados."

---

## Sprint 1 — Core do Agente (Buffer + RAG + Webhook)

### Objetivo
Implementar o buffer de mensagens, o RAG no Supabase, o webhook da WAHA (WhatsApp HTTP API), e o processamento principal com a tool de busca.

### 1.1 Criar `backend/agent/buffer.py`

```python
import logging
import threading
import time

logger = logging.getLogger(__name__)

_buffer: dict[str, dict] = {}
_lock = threading.Lock()
TEMPO_ESPERA = 12


def push(telefone: str, conteudo: str):
    """Acumula mensagem e (re)agenda processamento para 12s após a última."""
    with _lock:
        if telefone not in _buffer:
            _buffer[telefone] = {"mensagens": [], "timer": None, "inicio": time.time()}

        buf = _buffer[telefone]
        buf["mensagens"].append(conteudo)
        buf["inicio"] = time.time()

        if buf["timer"] is not None:
            buf["timer"].cancel()

        buf["timer"] = threading.Timer(TEMPO_ESPERA, _flush, args=[telefone])
        buf["timer"].start()
        logger.debug("Buffer[%s] acumulou %d mensagens | flush em %ds", telefone, len(buf["mensagens"]), TEMPO_ESPERA)


def _flush(telefone: str):
    with _lock:
        buf = _buffer.pop(telefone, None)

    if buf is None or not buf["mensagens"]:
        logger.debug("Buffer[%s] flush vazio, ignorando", telefone)
        return

    vistos = set()
    unicos = []
    for msg in buf["mensagens"]:
        if msg not in vistos:
            vistos.add(msg)
            unicos.append(msg)

    mensagem_completa = "\n".join(unicos)
    logger.info("Buffer[%s] flush com %d msgs únicas | total=%d | conteudo=%s", telefone, len(unicos), len(buf["mensagens"]), mensagem_completa[:80])
    from .core import processar_mensagem
    processar_mensagem(telefone, mensagem_completa)
```

### 1.2 Criar `backend/agent/rag.py`

```python
import os
from supabase import create_client, Client
from openai import OpenAI

openai_client = OpenAI()

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "")

supabase: Client | None = None
if SUPABASE_URL and SUPABASE_KEY:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


def buscar_rag(query: str, limite: int = 5) -> list[dict]:
    if not supabase:
        return []

    embedding = openai_client.embeddings.create(
        model="text-embedding-3-small",
        input=query,
    ).data[0].embedding

    try:
        result = supabase.rpc("match_documents", {
            "query_embedding": embedding,
            "match_count": limite,
        }).execute()
        return [
            {"content": doc["content"], "source": doc.get("metadata", {}).get("source", "desconhecida")}
            for doc in result.data
        ]
    except Exception as e:
        print(f"[RAG] Erro: {e}")
        return []


def buscar_rag_para_agente(query: str, limite: int = 5) -> str:
    docs = buscar_rag(query, limite)
    if not docs:
        return "Nenhum documento relevante encontrado."
    linhas = [f"- {doc['content']} (fonte: {doc['source']})" for doc in docs]
    return "\n".join(linhas)
```

### 1.3 Criar `backend/agent/tools.py`

```python
from typing import Optional
from django.db import models
from catalog.models import Provider


def buscar_prestadores(
    query: str,
    cidade: Optional[str] = None,
    categoria: Optional[str] = None,
    limite: int = 5,
) -> list[dict]:
    qs = Provider.objects.filter(status="approved").select_related("category")

    if query:
        qs = qs.filter(
            models.Q(name__icontains=query)
            | models.Q(headline__icontains=query)
            | models.Q(bio__icontains=query)
            | models.Q(category__name__icontains=query)
            | models.Q(skills__icontains=query)
        )
    if cidade:
        qs = qs.filter(city__icontains=cidade)
    if categoria:
        qs = qs.filter(category__name__icontains=categoria)

    qs = qs.order_by("-rating", "-reviews_count")[:limite]

    return [
        {
            "nome": p.name,
            "slug": p.slug,
            "categoria": p.category.name,
            "cidade": p.city,
            "estado": p.state,
            "nota": float(p.rating),
            "avaliacoes": p.reviews_count,
            "verificado": p.verified,
            "descricao": p.headline,
            "link": f"https://hivee.app/prestador/{p.slug}/",
        }
        for p in qs
    ]


ferramenta_buscar_prestadores = {
    "type": "function",
    "function": {
        "name": "buscar_prestadores",
        "description": "Busca prestadores de serviço cadastrados na plataforma HIVEE que correspondam à necessidade do usuário.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Palavras-chave (ex: 'eletricista', 'personal trainer')"},
                "cidade": {"type": "string", "description": "Cidade (opcional)"},
                "categoria": {"type": "string", "description": "Categoria (opcional)"},
                "limite": {"type": "integer", "description": "Máx resultados", "default": 5},
            },
            "required": ["query"],
        },
    },
}
```

### 1.4 Criar `backend/agent/core.py`

```python
import json
import logging
import re
from django.utils import timezone
from openai import OpenAI

from .models import ChatLead, Chat, ChatMessage
from .rag import buscar_rag_para_agente
from .tools import buscar_prestadores, ferramenta_buscar_prestadores
from .formatador import formatar_e_enviar

logger = logging.getLogger(__name__)
client = OpenAI()

SYSTEM_PROMPT = """Você é a assistente virtual da HIVEE, plataforma que conecta clientes a prestadores de serviço.

## SUA FUNÇÃO
1. Entenda o que o usuário está procurando (tipo de serviço, localização)
2. Use a ferramenta `buscar_prestadores` para encontrar profissionais
3. Recomende o melhor prestador com base na conversa
4. Envie o link do perfil para o usuário

## REGRAS
- Sempre use `buscar_prestadores` antes de recomendar
- Se faltar informação, pergunte educadamente
- Recomende 1-2 prestadores por vez
- Explique POR QUE cada um foi escolhido
- Responda em português brasileiro, tom informal
- Não invente prestadores — use apenas os retornados
- Se não encontrar nada adequado, peça para refinar a busca"""


def processar_mensagem(telefone: str, mensagem_completa: str):
    logger.info("processar_mensagem[%s] inicio | msg=%s", telefone, mensagem_completa[:100])
    try:
        try:
            lead = ChatLead.objects.get(telefone=telefone)
        except ChatLead.DoesNotExist:
            logger.warning("Lead nao encontrado para %s, ignorando", telefone)
            return

        chat, _ = Chat.objects.get_or_create(
            lead=lead,
            canal=lead.canal_origem,
            defaults={"status": "active"},
        )

        ChatMessage.objects.create(chat=chat, role="user", content=mensagem_completa)

        contexto_rag = buscar_rag_para_agente(mensagem_completa)
        logger.debug("RAG contexto: %s", str(contexto_rag)[:120])

        historico = ChatMessage.objects.filter(chat=chat).order_by("-created_at")[:10]
        historico_formatado = []
        for msg in reversed(historico):
            historico_formatado.append({"role": msg.role, "content": msg.content})

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "system", "content": f"Contexto RAG:\n{contexto_rag}"},
            *historico_formatado,
        ]

        response = client.chat.completions.create(
            model="gpt-4.1",
            messages=messages,
            tools=[ferramenta_buscar_prestadores],
            tool_choice="auto",
            temperature=0.7,
        )

        resposta_final = ""
        msg = response.choices[0].message

        if msg.tool_calls:
            messages.append(msg)
            for tool_call in msg.tool_calls:
                if tool_call.function.name == "buscar_prestadores":
                    args = json.loads(tool_call.function.arguments)
                    logger.info("Tool call buscar_prestadores args=%s", args)
                    prestadores = buscar_prestadores(**args)
                    logger.info("Tool result: %d prestadores encontrados", len(prestadores))
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": json.dumps(prestadores, ensure_ascii=False),
                    })

            response2 = client.chat.completions.create(
                model="gpt-4.1",
                messages=messages,
                temperature=0.7,
            )
            resposta_final = response2.choices[0].message.content
        else:
            resposta_final = msg.content

        if not resposta_final:
            logger.warning("OpenAI retornou resposta vazia para %s", telefone)
            resposta_final = "Desculpe, não consegui processar. Pode repetir?"

        ChatMessage.objects.create(chat=chat, role="bot", content=resposta_final)

        match = re.search(r"hivee\.app/prestador/([^/\s]+)/?", resposta_final)
        if match:
            from catalog.models import Provider
            try:
                provider = Provider.objects.get(slug=match.group(1))
                chat.provider_recomendado = provider
                chat.save(update_fields=["provider_recomendado"])
                logger.info("Provider recomendado: %s", provider.slug)
            except Provider.DoesNotExist:
                logger.warning("Provider slug %s nao encontrado no banco", match.group(1))

        chat.updated_at = timezone.now()
        chat.save(update_fields=["updated_at"])

        formatar_e_enviar(lead, chat, resposta_final)
        logger.info("processar_mensagem[%s] concluido com sucesso", telefone)
    except Exception:
        logger.exception("processar_mensagem[%s] ERRO nao tratado", telefone)
```

### 1.5 Criar `backend/agent/webhooks.py`

```python
import logging
import re
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import JSONParser
from rest_framework.response import Response

from .models import ChatLead
from .buffer import push
from .waha import baixar_midia
from .audio import transcrever_audio
from .vision import analisar_imagem

logger = logging.getLogger(__name__)


def limpar_telefone(remote_jid: str) -> str:
    return re.sub(r"@.*$", "", remote_jid)


def extrair_conteudo(payload: dict) -> str:
    msg_type = payload.get("type", "")
    body = payload.get("body", "")
    media = payload.get("media")

    if msg_type == "text":
        return body

    if msg_type == "audio" and media:
        caminho = baixar_midia(media.get("url", ""))
        if caminho:
            return f"[Áudio transcrito]: {transcrever_audio(caminho)}"
        return "[Áudio não pôde ser processado]"

    if msg_type == "image" and media:
        caption = body
        caminho = baixar_midia(media.get("url", ""))
        if caminho:
            return analisar_imagem(caminho, caption)
        return caption or "[Imagem sem descrição]"

    if msg_type in ("ptt", "voice"):
        caminho = baixar_midia(media.get("url", "")) if media else None
        if caminho:
            return f"[Áudio transcrito]: {transcrever_audio(caminho)}"
        return "[Áudio não pôde ser processado]"

    return body or "[Mensagem não reconhecida]"


@api_view(["POST"])
@parser_classes([JSONParser])
def waha_webhook(request):
    data = request.data
    evento = data.get("payload", data)
    remote_jid = evento.get("from", "")

    if not remote_jid:
        logger.warning("Webhook ignorado: sem from | payload=%s", str(data)[:200])
        return Response({"status": "ignored", "reason": "sem from"})

    telefone = limpar_telefone(remote_jid)

    if "@g.us" in remote_jid:
        logger.debug("Webhook ignorado: grupo %s", remote_jid)
        return Response({"status": "ignored", "reason": "grupo"})

    if evento.get("fromMe"):
        return Response({"status": "ignored", "reason": "mensagem do proprio bot"})

    push_name = evento.get("pushName", "")

    ChatLead.objects.get_or_create(
        telefone=telefone,
        defaults={"nome_wpp": push_name, "canal_origem": "whatsapp"},
    )

    conteudo = extrair_conteudo(evento)
    logger.info("Webhook[%s] type=%s | conteudo=%s", telefone, evento.get("type"), str(conteudo)[:100])
    push(telefone, conteudo)

    return Response({"status": "ok"})
```

### 1.6 Criar `backend/agent/waha.py`

```python
import os
import requests
from pathlib import Path
from urllib.parse import urljoin

WAHA_URL = os.getenv("WAHA_API_URL", "http://localhost:3000")
WAHA_SESSION = os.getenv("WAHA_SESSION", "hivee")

CHAT_ID = lambda tel: f"{tel}@c.us"


def send_presence(telefone: str, type: str = "typing"):
    url = urljoin(WAHA_URL, f"/api/{WAHA_SESSION}/presence")
    try:
        requests.post(url, json={"presence": type, "chatId": CHAT_ID(telefone)}, timeout=3)
    except Exception:
        pass


def enviar_whatsapp(telefone: str, texto: str):
    url = urljoin(WAHA_URL, "/api/sendText")
    try:
        requests.post(url, json={"session": WAHA_SESSION, "chatId": CHAT_ID(telefone), "text": texto}, timeout=10)
    except Exception as e:
        import logging
        logging.getLogger(__name__).error("Falha ao enviar WhatsApp para %s: %s", telefone, e)


def baixar_midia(url_midia: str) -> str | None:
    if not url_midia:
        return None
    try:
        resp = requests.get(url_midia, timeout=30)
        if resp.status_code == 200:
            ext = resp.headers.get("Content-Type", "").split("/")[-1] or "bin"
            temp_dir = Path("/tmp/hivee_media")
            temp_dir.mkdir(parents=True, exist_ok=True)
            arquivo = temp_dir / f"media_{id(url_midia)}.{ext}"
            with open(arquivo, "wb") as f:
                f.write(resp.content)
            return str(arquivo)
    except Exception as e:
        import logging
        logging.getLogger(__name__).error("Falha ao baixar mídia: %s", e)
    return None
```

### 1.7 Criar `backend/agent/audio.py`

```python
from openai import OpenAI

client = OpenAI()

def transcrever_audio(caminho_arquivo: str) -> str:
    with open(caminho_arquivo, "rb") as f:
        transcript = client.audio.transcriptions.create(
            model="whisper-1", file=f, language="pt",
        )
    return transcript.text
```

### 1.8 Criar `backend/agent/vision.py`

```python
from openai import OpenAI
import base64

client = OpenAI()

def analisar_imagem(caminho_arquivo: str, caption: str = "") -> str:
    with open(caminho_arquivo, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("utf-8")

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": [
            {"type": "text", "text": "Descreva esta imagem em português. Se for print, transcreva."},
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}},
        ]}],
        max_tokens=300,
    )
    descricao = response.choices[0].message.content
    return f"{caption}\n[Imagem: {descricao}]" if caption else f"[Imagem: {descricao}]"
```

### 1.9 Criar `backend/agent/formatador.py`

```python
import logging
import time
import json
from openai import OpenAI

from .waha import enviar_whatsapp, send_presence

logger = logging.getLogger(__name__)
client = OpenAI()
DELAY_ENTRE_BLOCOS = 6


def formatar_e_enviar(lead, chat, resposta_bruta: str):
    logger.info("formatar_e_enviar[%s] inicio | %d chars", lead.telefone, len(resposta_bruta))
    blocos = _dividir_em_blocos(resposta_bruta)
    logger.info("Resposta dividida em %d blocos", len(blocos))

    for i, bloco in enumerate(blocos):
        if i == 0 and lead.canal_origem == "whatsapp":
            send_presence(lead.telefone, "typing")
            time.sleep(2)

        logger.debug("Enviando bloco %d/%d: %s", i + 1, len(blocos), bloco[:60])

        if lead.canal_origem == "whatsapp":
            enviar_whatsapp(lead.telefone, bloco)
        else:
            from channels.layers import get_channel_layer
            from asgiref.sync import async_to_sync
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f"chat_{lead.telefone}",
                {"type": "bot_message", "content": bloco, "typing": False},
            )

        if i < len(blocos) - 1:
            logger.debug("Aguardando %ds antes do prox bloco...", DELAY_ENTRE_BLOCOS)
            time.sleep(DELAY_ENTRE_BLOCOS)

    if lead.canal_origem == "whatsapp":
        send_presence(lead.telefone, "paused")
    logger.info("formatar_e_enviar[%s] concluido", lead.telefone)


def _dividir_em_blocos(texto: str) -> list[str]:
    if len(texto) < 200:
        return [texto]
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": "Divida o texto abaixo em blocos naturais de até 200 caracteres cada. Responda APENAS array JSON de strings."},
                      {"role": "user", "content": texto}],
            response_format={"type": "json_object"},
            max_tokens=500,
        )
        blocos = json.loads(response.choices[0].message.content)
        if isinstance(blocos, dict):
            for v in blocos.values():
                if isinstance(v, list):
                    blocos = v
                    break
        if isinstance(blocos, list) and len(blocos) > 1:
            return blocos
    except Exception:
        logger.warning("Falha ao dividir blocos via GPT, fallback para paragrafos", exc_info=True)
    paragrafos = [p.strip() for p in texto.split("\n\n") if p.strip()]
    return paragrafos if len(paragrafos) > 1 else [texto]
```

### ✅ Validação da Sprint 1

```bash
python manage.py check
python -c "from agent.buffer import push; from agent.rag import buscar_rag_para_agente; from agent.tools import buscar_prestadores; print('Import OK')"
```

**AVISAR USUÁRIO:** "✅ Sprint 1 concluída. Buffer, RAG, webhook, ferramenta de busca e processador principal implementados."

---

## Sprint 2 — Canais (WebSocket + Frontend + Envio WhatsApp)

### Objetivo
Conectar o chat no site via WebSocket + React, e garantir que o fluxo WhatsApp esteja completo com WAHA.

### 2.1 Criar `backend/agent/consumers.py`

```python
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import ChatLead
from .buffer import push


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.telefone = self.scope["url_route"]["kwargs"]["telefone"]
        self.room_group_name = f"chat_{self.telefone}"
        await self._garantir_lead()
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        conteudo = data.get("content", "")
        if conteudo:
            push(self.telefone, conteudo)

    async def bot_message(self, event):
        await self.send(text_data=json.dumps({
            "role": "bot",
            "content": event["content"],
            "typing": event.get("typing", False),
        }))

    @database_sync_to_async
    def _garantir_lead(self):
        ChatLead.objects.get_or_create(
            telefone=self.telefone,
            defaults={"canal_origem": "site"},
        )
```

### 2.2 Criar `frontend/src/components/ChatWidget.tsx`

```tsx
import { useState, useEffect, useRef, useCallback } from "react";

interface Message {
  role: "user" | "bot";
  content: string;
}

interface Props {
  telefone: string;
}

export function ChatWidget({ telefone }: Props) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [connected, setConnected] = useState(false);
  const [isTyping, setIsTyping] = useState(false);
  const ws = useRef<WebSocket | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const host = import.meta.env.DEV ? "localhost:8000" : window.location.host;
    ws.current = new WebSocket(`${protocol}//${host}/ws/chat/${telefone}/`);

    ws.current.onopen = () => setConnected(true);
    ws.current.onclose = () => setConnected(false);

    ws.current.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.typing) {
        setIsTyping(true);
      } else {
        setIsTyping(false);
        setMessages((prev) => [...prev, { role: "bot", content: data.content }]);
      }
    };

    return () => ws.current?.close();
  }, [telefone]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isTyping]);

  const send = useCallback(() => {
    if (!input.trim() || !ws.current) return;
    ws.current.send(JSON.stringify({ content: input }));
    setMessages((prev) => [...prev, { role: "user", content: input }]);
    setInput("");
  }, [input]);

  return (
    <div className="fixed bottom-24 right-6 w-96 h-[32rem] bg-zinc-900 border border-zinc-700 rounded-2xl shadow-2xl flex flex-col overflow-hidden z-50">
      <div className="bg-amber-500/10 border-b border-zinc-700 px-4 py-3 flex items-center gap-3">
        <div className={`w-2 h-2 rounded-full ${connected ? "bg-green-500" : "bg-red-500"}`} />
        <span className="text-zinc-100 font-medium">HIVEE Chat</span>
      </div>
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {messages.map((msg, i) => (
          <div key={i} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
            <div className={`max-w-[80%] px-4 py-2 rounded-2xl text-sm ${
              msg.role === "user"
                ? "bg-amber-500 text-black rounded-br-md"
                : "bg-zinc-800 text-zinc-100 rounded-bl-md"
            }`}>
              {msg.content}
            </div>
          </div>
        ))}
        {isTyping && (
          <div className="flex justify-start">
            <div className="bg-zinc-800 text-zinc-400 px-4 py-2 rounded-2xl rounded-bl-md text-sm italic">
              digitando...
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>
      <div className="border-t border-zinc-700 p-3 flex gap-2">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && send()}
          placeholder="Digite sua mensagem..."
          className="flex-1 bg-zinc-800 text-zinc-100 px-4 py-2 rounded-xl text-sm outline-none focus:ring-1 focus:ring-amber-500"
        />
        <button onClick={send} className="bg-amber-500 text-black px-4 py-2 rounded-xl text-sm font-medium hover:bg-amber-400">
          Enviar
        </button>
      </div>
    </div>
  );
}
```

### 2.3 Criar `frontend/src/pages/ChatPage.tsx`

```tsx
import { ChatWidget } from "../components/ChatWidget";
import { useSearchParams } from "react-router-dom";

export default function ChatPage() {
  const [params] = useSearchParams();
  const telefone = params.get("tel") || `site_${Date.now()}`;
  return (
    <div className="min-h-screen bg-black pt-20">
      <ChatWidget telefone={telefone} />
    </div>
  );
}
```

### 2.4 Modificar `frontend/src/pages/ProviderProfile.tsx`

Localizar o botão "Enviar mensagem" (linha ~170) que está sem handler e substituir:

```tsx
import { useNavigate } from "react-router-dom";
const navigate = useNavigate();
// ...
<button onClick={() => navigate(`/chat?provider=${slug}`)}>
  Enviar mensagem
</button>
```

### 2.5 Adicionar rota no frontend

Em `frontend/src/main.tsx` (ou `App.tsx`), adicionar:

```tsx
import ChatPage from "./pages/ChatPage";
// ...
<Route path="/chat" element={<ChatPage />} />
```

### 2.6 Verificar variáveis de ambiente (.env)

```env
WAHA_API_URL=http://localhost:3000
WAHA_SESSION=hivee
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_SERVICE_KEY=eyJ...
OPENAI_API_KEY=sk-...
```

### ✅ Validação da Sprint 2

```bash
python manage.py check
# Frontend: npm run build (verificar se compila)
```

**AVISAR USUÁRIO:** "✅ Sprint 2 concluída. WebSocket, ChatWidget React e integração WhatsApp implementados. Configure as credenciais no .env."

---

## Sprint 3 — Follow-up + Polimento

### Objetivo
Follow-up automático, testes mínimos, verificação final.

### 3.1 Criar `backend/agent/followup.py`

```python
from datetime import timedelta
from django.utils import timezone
from openai import OpenAI

from .models import Chat, ChatMessage
from .waha import enviar_whatsapp

client = OpenAI()


def verificar_followup():
    limite = timezone.now() - timedelta(hours=24)
    chats = Chat.objects.filter(status="active", canal="whatsapp", updated_at__lt=limite)

    for chat in chats:
        ultima = chat.mensagens.last()
        if not ultima or ultima.role == "bot":
            continue

        historico = chat.mensagens.order_by("-created_at")[:6]
        linhas = []
        for msg in reversed(historico):
            papel = "Cliente" if msg.role == "user" else "Bot"
            linhas.append(f"{papel}: {msg.content[:100]}")
        contexto = "\n".join(linhas)

        resposta = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Gere mensagem curta de follow-up para WhatsApp. Máx 80 caracteres. Tom amigável. Apenas o texto."},
                {"role": "user", "content": f"Histórico:\n{contexto}"},
            ],
            max_tokens=100,
        ).choices[0].message.content

        enviar_whatsapp(chat.lead.telefone, resposta)
        ChatMessage.objects.create(chat=chat, role="bot", content=f"[Follow-up] {resposta}")
        chat.updated_at = timezone.now()
        chat.save(update_fields=["updated_at"])
```

### 3.2 Criar management command

`backend/agent/management/commands/run_followup.py`:

```python
from django.core.management.base import BaseCommand
from agent.followup import verificar_followup

class Command(BaseCommand):
    help = "Verifica chats parados e envia follow-up"

    def handle(self, *args, **options):
        verificar_followup()
        self.stdout.write(self.style.SUCCESS("Follow-up concluído"))
```

### 3.3 Criar `backend/agent/apps.py` com scheduler

```python
import os
from django.apps import AppConfig

class AgentConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "agent"

    def ready(self):
        if os.environ.get("RUN_MAIN") or os.environ.get("APSCHEDULER_RUNNING"):
            return
        os.environ["APSCHEDULER_RUNNING"] = "1"
        from apscheduler.schedulers.background import BackgroundScheduler
        scheduler = BackgroundScheduler()
        scheduler.add_job(
            "agent.followup:verificar_followup",
            trigger="cron", day_of_week="mon-fri", hour=8, minute=50,
        )
        scheduler.start()
```

### 3.4 Testes de integração com mock

Criar `backend/agent/tests.py`:

```python
from unittest.mock import patch, MagicMock
from django.test import TestCase, override_settings
from .models import ChatLead, Chat, ChatMessage


class AgentModelsTest(TestCase):
    def test_criar_lead(self):
        lead = ChatLead.objects.create(telefone="5511999999999", nome_wpp="Teste", canal_origem="whatsapp")
        self.assertEqual(str(lead), "Teste (WhatsApp)")

    def test_criar_chat(self):
        lead = ChatLead.objects.create(telefone="5511999999999", canal_origem="whatsapp")
        chat = Chat.objects.create(lead=lead, canal="whatsapp")
        self.assertEqual(chat.status, "active")

    def test_criar_mensagem(self):
        lead = ChatLead.objects.create(telefone="5511999999999", canal_origem="whatsapp")
        chat = Chat.objects.create(lead=lead, canal="whatsapp")
        msg = ChatMessage.objects.create(chat=chat, role="user", content="Olá")
        self.assertTrue("Olá" in msg.content)


class AgentBufferTest(TestCase):
    def test_push_acumula_e_flush(self):
        from .buffer import push
        push("5511999999999", "quero um eletricista")
        push("5511999999999", "em são paulo")
        from .buffer import _buffer
        self.assertIn("5511999999999", _buffer)
        self.assertEqual(len(_buffer["5511999999999"]["mensagens"]), 2)


class AgentCoreTest(TestCase):
    @patch("agent.core.client.chat.completions.create")
    @patch("agent.core.buscar_rag_para_agente")
    @patch("agent.formatador.enviar_whatsapp")
    def test_fluxo_completo(self, mock_enviar, mock_rag, mock_openai):
        lead = ChatLead.objects.create(telefone="5511999999999", nome_wpp="Teste", canal_origem="whatsapp")

        mock_rag.return_value = "Contexto de teste"
        mock_openai.return_value.choices[0].message.tool_calls = None
        mock_openai.return_value.choices[0].message.content = "Recomendo o eletricista João! Acesse hivee.app/prestador/joao-eletricista/"

        from .core import processar_mensagem
        processar_mensagem("5511999999999", "preciso de um eletricista")

        chat = Chat.objects.get(lead=lead)
        msgs = ChatMessage.objects.filter(chat=chat).order_by("created_at")
        self.assertEqual(msgs.count(), 2)
        self.assertEqual(msgs[0].role, "user")
        self.assertEqual(msgs[1].role, "bot")
        self.assertIn("eletricista", msgs[1].content)
        mock_enviar.assert_called_once()


class AgentToolsTest(TestCase):
    def test_buscar_prestadores_sem_resultado(self):
        from .tools import buscar_prestadores
        resultado = buscar_prestadores(query="xyz123naoexiste")
        self.assertEqual(resultado, [])
```

### 3.5 Management command para simular mensagem (teste sem WAHA)

Criar `backend/agent/management/commands/simulate_message.py`:

```python
import logging
from django.core.management.base import BaseCommand

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Simula o recebimento de uma mensagem para testar o fluxo completo do agente"

    def add_arguments(self, parser):
        parser.add_argument("--telefone", required=True)
        parser.add_argument("--mensagem", required=True)
        parser.add_argument("--canal", default="whatsapp", choices=["whatsapp", "site"])

    def handle(self, *args, **options):
        telefone = options["telefone"]
        mensagem = options["mensagem"]
        canal = options["canal"]

        from agent.models import ChatLead
        lead, created = ChatLead.objects.get_or_create(
            telefone=telefone,
            defaults={"nome_wpp": "Teste Simulacao", "canal_origem": canal},
        )
        if created:
            logger.info("Lead criado: %s", lead)

        from agent.buffer import push
        push(telefone, mensagem)

        self.stdout.write(self.style.SUCCESS(
            f"Mensagem enfileirada para {telefone}. "
            f"Aguardando {12 + 6}s para processamento + blocos. "
            f"Veja os logs acima para acompanhar o fluxo."
        ))
```

### 3.6 Comando para validar ambiente na inicialização

Criar `backend/agent/management/commands/check_env.py`:

```python
import os
import sys
from django.core.management.base import BaseCommand

REQUIRED = {
    "OPENAI_API_KEY": "OpenAI — chamadas do agente",
    "SUPABASE_URL": "Supabase — conexão com o Vector Store",
    "SUPABASE_KEY": "Supabase — chave de acesso ao Vector Store",
    "WAHA_API_URL": "WAHA — envio de WhatsApp",
    "WAHA_SESSION": "WAHA — nome da sessão",
}


class Command(BaseCommand):
    help = "Verifica se todas as variáveis de ambiente necessárias estão configuradas"

    def handle(self, *args, **options):
        missing = []
        for var, desc in REQUIRED.items():
            if not os.getenv(var):
                missing.append(f"  - {var} ({desc})")

        if missing:
            self.stdout.write(self.style.ERROR("❌ Variáveis de ambiente faltando:"))
            for m in missing:
                self.stdout.write(m)
            sys.exit(1)
        else:
            self.stdout.write(self.style.SUCCESS("✅ Todas as variáveis de ambiente estão configuradas"))
```

### 3.7 Verificação final

```bash
python manage.py check_env              # valida environment
python manage.py check                   # valida Django
python manage.py test agent --verbosity=2  # roda testes
python manage.py simulate_message --telefone=5511999999999 --mensagem="preciso de um eletricista" --canal=whatsapp
```

> **Importante:** NUNCA use `runserver` — ele não suporta WebSocket. Use **Daphne**:
> ```bash
> daphne -p 8000 hivee.asgi:application
> ```

### ✅ Validação da Sprint 3

```bash
python manage.py check_env
python manage.py check
python manage.py test agent --verbosity=2
daphne -p 8000 hivee.asgi:application  # sobe e testa manualmente no navegador
```

**AVISAR USUÁRIO:** "✅ Sprint 3 concluída. Follow-up, scheduler, testes com mock, comando de simulação e validação de ambiente implementados. Sistema pronto para produção."

---

## Referência Rápida de Arquivos

### App `agent` — todos os arquivos a criar

```
backend/agent/
├── __init__.py
├── apps.py                  # AppConfig + scheduler
├── models.py                # ChatLead, Chat, ChatMessage
├── admin.py                 # Admin para os models
├── urls.py                  # Rota do webhook
├── logging_config.py        # Setup centralizado de logs
├── buffer.py                # Buffer 12s (dict + Timer)
├── webhooks.py              # waha_webhook()
├── consumers.py             # ChatConsumer (WebSocket)
├── core.py                  # processar_mensagem() → agente
├── rag.py                   # buscar_rag() Supabase Vector Store
├── tools.py                 # buscar_prestadores() tool
├── waha.py                  # enviar_whatsapp(), send_presence()
├── audio.py                 # transcrever_audio() Whisper
├── vision.py                # analisar_imagem() GPT-4o-mini
├── formatador.py            # dividir blocos + delay 6s + typing
├── followup.py              # verificar_followup()
├── tests.py                 # Testes com mock do fluxo completo
├── management/
│   └── commands/
│       ├── run_followup.py      # Executar follow-up manualmente
│       ├── simulate_message.py  # Simular mensagem sem WAHA
│       └── check_env.py         # Validar variáveis de ambiente
└── migrations/
    └── __init__.py
```

### Frontend — novos arquivos

```
frontend/src/components/ChatWidget.tsx
frontend/src/pages/ChatPage.tsx
```

### Arquivos a modificar

| Arquivo | O que fazer |
|---|---|
| `backend/hivee/settings.py` | +agent, +channels, ASGI_APPLICATION, CHANNEL_LAYERS |
| `backend/hivee/asgi.py` | ProtocolTypeRouter com WebSocket |
| `backend/hivee/urls.py` | include("agent.urls") |
| `backend/requirements.txt` | Adicionar novas dependências |
| `frontend/src/main.tsx` | Rota /chat |
| `frontend/src/pages/ProviderProfile.tsx` | Ativar botão "Enviar mensagem" |

---

## Prompt de Continuação (se atingir limite de tokens)

Copie e cole isto em uma nova sessão:

```
[CONTINUAÇÃO] Super Agente HIVEE

Sprint atual: [SPRINT X]
Já implementado:
- [lista do que já foi feito]

Próximo passo:
[descrição do que fazer a seguir]

Arquivos modificados até agora:
[lista]

Consulte o plano completo em PLANO_IMPLEMENTACAO_V3.md
seção [NOME DA SEÇÃO] para o código detalhado.
```

---

## Fluxo Final (resumo visual)

```
Usuário envia mensagem (WhatsApp ou Site)
  → Buffer acumula por 12 segundos (dict + Timer)
  → Se áudio: Whisper transcreve
  → Se imagem: GPT-4o-mini analisa
  → RAG busca contexto no Supabase Vector Store
  → GPT-4.1 interpreta + chama tool buscar_prestadores(query, cidade, categoria)
  → Tool consulta Django ORM (Provider.objects.filter(...))
  → GPT-4.1 monta resposta com link do perfil (hivee.app/prestador/{slug}/)
  → Formatador divide em blocos de ~200 chars (GPT-4o-mini)
  → Envia "digitando..." no WhatsApp (WAHA sendPresence)
  → Envia bloco 1 → espera 6s → bloco 2 → ... → bloco N
  → Salva tudo no histórico (Chat + ChatMessage)
  → Se ninguém responder em 24h, follow-up automático pergunta se ainda precisa
```
