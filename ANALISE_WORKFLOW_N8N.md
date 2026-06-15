# Análise do Workflow "SUPER AGENTE" (n8n)

> Workflow JSON extraído de `message (1).txt`
> Total: ~8400 linhas, ~89 nós

---

## 1. Visão Geral do Fluxo

O workflow é um **chatbot omnichannel para WhatsApp** que integra **Evolution API** (conexão WhatsApp), **OpenAI** (GPT-4.1, GPT-5, GPT-4o-mini), **Supabase** (banco + storage + vector store), **Redis** (memória de curto prazo), **PostgreSQL** (memória de longo prazo + histórico), **Google Drive** (RAG documents) e **Google Sheets** (treinamento).

Atende **2 grandes áreas de negócio** simultaneamente:

| Área | Agente | Descrição |
|---|---|---|
| **Farmácia/Super Agente** | **SOFIA** | Venda de medicamentos, RAG de estoque/preço/bulas, receita médica, carrinho |
| **Terapia/Psicologia** | **Gabriela** | Secretária da Dra. Ana Miranda, agendamento de consultas, pagamento Pix |

---

## 2. Fluxo Passo a Passo

### FASE 0 — Webhook (Trigger)

```
Webhook EVO (Evolution API)
  ↓
Entrada de Contato (extrai remoteJid)
  ↓
Extrair Número (limpa o @s.whatsapp.net)
  ↓
Refaz numero (reconstrói com @s.whatsapp.net)
  ↓
Dados (enriquece: content_type, content, timestamp, event, Telefone, NomeWpp)
```

- Webhook escuta `POST` da Evolution API
- Evento: `messages.upsert` (qualquer mensagem incoming)
- Extrai: tipo da msg (texto/áudio/imagem), conteúdo, número, nome do push

### FASE 1 — Cadastro/Reconhecimento do Lead

```
Dados
  ↓
Supabase (SELECT dados_cliente WHERE telefone = X)
  ↓
If1 (telefone existe?)
  ├── SIM → Filtro_Saida_IA (já é lead conhecido)
  └── NÃO → Create a row (insere novo lead em dados_cliente)
              ↓
            Filtro_Saida_IA
```

### FASE 2 — Verificação de Pausa da IA

```
Filtro_Saida_IA (Switch: incoming vs outcoming)
  ├── outcoming → Palavra para despausar
  └── incoming → Verificar Pause
                   ↓
                 Rota Atendimento (Switch: atendimento_ia == "pause"?)
                   ├── IA Ativa → Switch1 (processa mensagem)
                   └── IA Pausada → Salvar Historicoo Humano1
```

**Sistema de Pausa/Retomada:**
- Se `atendimento_ia == "pause"`, a IA não responde — mensagem vai direto pra histórico humano
- Palavra mágica para despausar: "Atendimento finalizado" (envia para `Palavra para despausar` → `Espera para reativar a IA` → `Reativar IA`)

### FASE 3 — Roteamento por Tipo de Mensagem (Switch1)

```
Switch1 (messageType)
  ├── text (extendedTextMessage ou conversation) → Text Memory1
  ├── text (conversation) → Text Memory1
  ├── audio → Edit Fields → Convert to File → OpenAI (Whisper/transcribe) → Audio Memory1
  └── image → Edit Fields3 → Convert to File1 → OpenAI1 (GPT-4o-mini analisa) → If3
                ├── legenda vazia → Redis5 (só imagem)
                └── com legenda → Redis4 (imagem + texto)
```

### FASE 4 — Memória no Redis (Buffer de mensagens)

```
Text Memory1 / Audio Memory1 / Redis4 / Redis5
  ↓ (push na lista Redis = telefone)
Get Memory 1 (lê a lista Redis)
  ↓
Espera para responder (wait 12s — aguarda mais mensagens)
  ↓
Get Memory 2 (relê a lista Redis após espera)
  ↓
Edit Fields8 (compara Redis1 vs Redis2)
  ↓
Compara Get Memory1 (se igual → já estabilizou; se diferente → volta)
  ↓
Mensagem Completa (código JS: merge + dedup → mensagem_completa)
```

**Propósito:** buffer de 12 segundos que acumula mensagens picadas do WhatsApp e só prossegue quando a conversa estabiliza.

### FASE 5 — RAG (Retrieval Augmented Generation)

```
Mensagem Completa
  ↓
Agente_RAG_Pesquisador (GPT-4.1-mini agent com tools)
  ├── buscar_produtos (Supabase Vector Store → OpenAI embeddings → busca por similaridade)
  │     └── conteúdo: estoque, preços, disponibilidade
  └── buscar_conhecimento (Supabase Vector Store → busca por similaridade)
        └── conteúdo: bulas, políticas de entrega, regras de receituário
  ↓
output_produtos + output_conhecimento
```

**Fontes do RAG:**
- Google Drive → pasta "RAG FARMACIA" → PDFs, planilhas, docs → extraídos → chunked → embeddings → Supabase Vector Store (`documents` table)
- Schedule diário às 5h reindexa tudo (deleta documentos antigos, baixa novamente, reinsere)

### FASE 6 — Gerente de Setor (Opcional)

```
Mensagem Completa
  ↓
Gerente Setor (GPT-4.1 agent + tool Supabase)
  → Classifica a conversa em MATRICULA, SUPORTE ou vazio
  → Atualiza coluna `setor` em `dados_cliente` via Supabase
```

### FASE 7 — Roteador de Intenção

```
Espera gerente Geral (wait 10s)
  ↓
Get a row (lê dados_cliente atualizado)
  ↓
Roteador_Intencao_Atendimento (Switch pelo setor)
  ├── MATRICULA → (para agente de matrícula — não implementado no JSON visível)
  ├── SUPORTE → (para agente de suporte — não implementado no JSON visível)
  └── vazio → Cerebro (orquestrador principal)
```

### FASE 8 — Cérebro (Orquestrador)

```
Cerebro (GPT-4.1-nano agent — roteia para o agente correto)
  ├── tool: SOFIA (farmácia)
  └── tool: Gabriela (terapia)
  ↓
  ├── SOFIA → Nome agent andre → Switch2
  └── Gabriela → Nome agent Gabriela → Switch2
```

### FASE 9 — Agentes de Atendimento

**SOFIA (Farmácia — GPT-5):**
- System prompt define personalidade, regras de venda, script
- Recebe `fontes_dados` do RAG (produtos + conhecimento)
- Tools disponíveis:
  - `buscar_produtos` / `buscar_conhecimento` (via Cerebro)
  - `enviar_img1` (tool workflow → envia PDF de planos via sub-workflow)
  - `Ferramenta_Adicionar_Carrinho` (estrutura JSON → Supabase insert em `carrinho_itens`)
  - `Ferramenta_Ler_Receita` (estrutura JSON → OpenAI Vision API para analisar foto de receita)

**Gabriela (Terapia — GPT-4.1):**
- System prompt: secretária da Dra. Ana Miranda
- Regras: sem emojis, uma pergunta por vez, não confirma horário, pagamento via Pix
- Encaminha para humano se fora do escopo

### FASE 10 — Pós-processamento (Switch2)

```
Switch2 (a saída do agente contém "251213"?)
  ├── NÃO contém → Continuar na IA → Basic LLM Chain (formatação + split)
  └── SIM contém → Avisar Lead grupo → Salvar Metricas (Supabase)
```

**"251213"** é um código de ação: se presente na resposta da IA, significa que o lead deve ser avisado no grupo (não enviar resposta normal).

### FASE 11 — Formatação e Envio

```
Basic LLM Chain (formata a resposta em JSON com array de mensagens)
  ↓
Structured Output Parser + Auto-fixing Output Parser
  ↓
Split Out1 (separa o array em itens individuais)
  ↓
Loop Over Items1 (1 por vez)
  ↓
Wait4 (6s entre mensagens — humano-like)
  ↓
Switch (texto vs áudio)
  ├── texto → Enviar texto (Evolution API)
  └── audio → Enviar audio (Evolution API)
```

### FASE 12 — Histórico e Persistência

```
Após envio, salva no Supabase:
  - Cria Histórico Supabase1 (chat_messages: phone, bot_message, user_message, message_type)
  - Adiciona/Atualiza CHAT (tabela chats)
  - Delete Memory1 (limpa Redis)
```

### FASE EXTRA — Agente de Treinamento RAG

```
Separado do fluxo principal:
  Schedule Trigger → Google Drive → Download → Extrair → Chunk → Embeddings → Supabase Vector Store
```

- Roda **todos os dias às 5h**
- Deleta documentos antigos, baixa tudo do Google Drive, reprocessa

### FASE EXTRA — Follow-up Automático

```
Schedule Trigger1 (CRON: 50 8 * * 1-5 = 08:50 segunda a sexta)
  ↓
ListChats-Supabase (chats com updated_at < 5min atrás = parados)
  ↓
Loop Over Items2
  ↓
ListMessages-Supabase
  ↓
Aggregate → Code4 (formata conversa)
  ↓
Text Classifier (categorias: pendente_resposta, encerrada, personal, sem resposta)
  ↓
Basic LLM Chain2/3 (gera resposta de follow-up)
  ↓
Evolution API (envia)
```

### FASE EXTRA — Backup Automático

```
Schedule Trigger → Google Drive1 (cria pasta "N8N - BACKUP DIA - dd/MM/yyyy")
  → Exporta workflows via n8n API → salva no Drive
```

---

## 3. Tecnologias e Credenciais Utilizadas

| Serviço | Uso | Nós |
|---|---|---|
| Evolution API | Envio/recebimento WhatsApp | `Webhook EVO`, `Enviar texto`, `Enviar audio`, `Evolution API3/6/7` |
| OpenAI | LLMs, Whisper, Visão | GPT-5, GPT-4.1, GPT-4.1-mini, GPT-4.1-nano, GPT-4o-mini, text-embedding-3-small |
| Supabase | PostgreSQL + Storage + Vector | `dados_cliente`, `chats`, `chat_messages`, `documents`, `n8n_chat_histories`, `carrinho_itens` |
| Redis | Buffer de mensagens, estado | `Text Memory1`, `Audio Memory1`, `Get Memory 1/2`, `Redis4/5` |
| PostgreSQL | Chat memory (LangChain) | `n8n_chat_histories`, `n8n_chat_histories_gerente` |
| Google Drive | RAG document source | `Search files and folders`, `Download file` |
| Google Sheets | Treinamento RAG | `Treinamento_feito`, `Atualizar_treinamento` |
| Google Calendar | Agendamentos (terapia) | MCP Server + Calendar tools (disabled) |
| n8n | Orquestração total | 89 nós conectados |

---

## 4. Daria para Codar Isso em Python (sem n8n)?

**Sim, completamente.** Cada nó do n8n equivale a uma função/biblioteca Python.

### Equivalência n8n → Python

| n8n Node | Python Equivalente |
|---|---|
| **Webhook EVO** | `FastAPI` ou `Flask` endpoint POST |
| **Evolution API** | `evolution-api` ou `whatsapp-web.js` via subprocess |
| **Supabase (CRUD)** | `supabase-py` |
| **Supabase Vector Store** | `supabase-py` + `pgvector` + `openai` embeddings |
| **OpenAI Chat** | `openai` SDK |
| **OpenAI Whisper** | `openai.Audio.transcribe()` |
| **OpenAI Vision** | `openai` com `gpt-4-vision-preview` |
| **Redis** | `redis-py` |
| **Postgres Chat Memory** | `psycopg2` + `sqlalchemy` |
| **Google Drive** | `google-api-python-client` |
| **Google Sheets** | `gspread` |
| **Google Calendar** | `google-api-python-client` |
| **Code/Function** | Python functions |
| **Switch/IF** | `if/elif/else` |
| **Wait** | `asyncio.sleep()` |
| **Split In Batches** | `for` loop |
| **Aggregate** | List comprehensions |
| **Schedule Trigger** | `APScheduler` ou `celery beat` |
| **Structured Output Parser** | Pydantic models + `response_format` |
| **Auto-fixing Parser** | Pydantic validation + retry |
| **MCP Client** | `mcp` Python SDK |

### Arquitetura Sugerida (Python)

```
┌──────────────┐     ┌─────────────────────────────┐
│  Evolution   │────▶│   FastAPI (webhook handler)  │
│  API         │     │   /webhook/evolution         │
└──────────────┘     └──────────┬──────────────────┘
                                │
                    ┌───────────▼───────────────────┐
                    │   Message Buffer (Redis)       │
                    │   12s wait + dedup             │
                    └───────────┬───────────────────┘
                                │
                    ┌───────────▼───────────────────┐
                    │   Router (message type)        │
                    │   text / audio / image         │
                    └───────────┬───────────────────┘
                                │
                    ┌───────────▼───────────────────┐
                    │   RAG Pipeline                 │
                    │   Embeddings → Vector Search   │
                    └───────────┬───────────────────┘
                                │
                    ┌───────────▼───────────────────┐
                    │   Agent Orchestrator           │
                    │   Cerebro → Sofia/Gabriela     │
                    │   (LangChain agents)           │
                    └───────────┬───────────────────┘
                                │
                    ┌───────────▼───────────────────┐
                    │   Post-processor               │
                    │   Split messages, formatting   │
                    └───────────┬───────────────────┘
                                │
                    ┌───────────▼───────────────────┐
                    │   Evolution API (send)         │
                    └───────────────────────────────┘

Background tasks (APScheduler):
  - RAG reindex (daily 5h)
  - Follow-up (08:50 weekdays)
  - Google Drive backup
```

### Exemplo Mínimo em Python

```python
from fastapi import FastAPI, Request
from openai import OpenAI
from supabase import create_client
import redis

app = FastAPI()
openai = OpenAI()
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
r = redis.Redis()

@app.post("/webhook/evolution")
async def webhook(request: Request):
    data = await request.json()
    telefone = data["body"]["data"]["key"]["remoteJid"]
    msg_type = data["body"]["data"]["messageType"]
    content = data["body"]["data"]["message"].get("conversation", "")

    # 1. Busca lead no Supabase
    lead = supabase.table("dados_cliente").select("*").eq("telefone", telefone).execute()
    if not lead.data:
        supabase.table("dados_cliente").insert({
            "telefone": telefone,
            "nomewpp": data["body"]["data"]["pushName"],
            "created_at": "now()"
        }).execute()

    # 2. Verifica se IA está pausada
    if lead.data and lead.data[0].get("atendimento_ia") == "pause":
        return {"status": "paused"}

    # 3. Buffer Redis (12s wait)
    r.lpush(telefone, content)
    # ... (lógica de wait + dedup)

    # 4. RAG: busca vetorial
    embedding = openai.embeddings.create(
        model="text-embedding-3-small",
        input=content
    ).data[0].embedding
    docs = supabase.rpc("match_documents", {
        "query_embedding": embedding,
        "match_count": 10
    }).execute()

    # 5. LLM
    response = openai.chat.completions.create(
        model="gpt-5",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT_SOFIA},
            {"role": "user", "content": content}
        ]
    )
    reply = response.choices[0].message.content

    # 6. Envia via Evolution API
    requests.post(f"{EVO_URL}/message/send", json={
        "number": telefone,
        "text": reply
    })

    # 7. Salva histórico
    supabase.table("chat_messages").insert({
        "phone": telefone,
        "bot_message": reply,
        "user_message": content,
        "message_type": msg_type
    }).execute()

    return {"status": "ok"}
```

---

## 5. Prós e Contras: n8n vs Código

| Aspecto | n8n | Código Python |
|---|---|---|
| **Velocidade de desenvolvimento** | ✅ Rápido (drag & drop) | ❌ Mais lento no início |
| **Manutenção visual** | ✅ Fluxo visível | ❌ Requer leitura de código |
| **Debugar** | ❌ Difícil (logs limitados) | ✅ Pdb/breakpoints/logs |
| **Testes automatizados** | ❌ Quase impossível | ✅ pytest completo |
| **Versionamento** | ❌ JSON gigante (8k linhas) | ✅ Código diff-friendly |
| **Custo** | ⚠️ n8n cloud ou self-host | ✅ Só infraestrutura |
| **Performance** | ❌ Overhead do n8n | ✅ Mais leve |
| **Escalabilidade** | ❌ Single thread | ✅ Async + workers |
| **Integração com Django** | ❌ HTTP calls separadas | ✅ Mesmo processo |
| **Controle fino** | ❌ Limitado ao que os nós oferecem | ✅ Total liberdade |

---

## 6. Conclusão

**Sim, daria para codar todo esse fluxo em Python**, e em muitos aspectos seria **superior** — especialmente em testabilidade, versionamento e performance. O n8n oferece velocidade inicial e visibilidade, mas o código oferece controle total e integração direta com seu Django backend.

**Recomendação:** migrar gradualmente — comece com o fluxo principal (webhook → IA → envio) em Python, mantendo o RAG e ferramentas auxiliares no n8n até estabilizar. Ou mantenha no n8n e apenas conecte ao Django para as operações de negócio (CPF, providers, upload).
