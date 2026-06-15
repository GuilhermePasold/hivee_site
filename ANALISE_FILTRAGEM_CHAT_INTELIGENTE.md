# Análise — Filtragem Inteligente de Chat (Ofensas, Circunvenção, Moderação Automática)

## 1. Visão Geral

**Problema:** Usuários do chat HIVEE podem enviar mensagens ofensivas, tentar
combinar serviços por fora da plataforma (circunvenção), ou enviar conteúdo
inapropriado. O sistema atual não tem nenhuma camada de moderação.

**Solução:** Pipeline de moderação em 3 camadas que age no momento do envio:
1. **Regex / blacklist** (instantâneo, zero custo)
2. **OpenAI Moderation API** (gratuita, categoriza em hate/harassment/sexual/violence)
3. **Classificador contextual via GPT** (detecta circunvenção: "me chama no zap", etc.)

Mensagens reprovadas são:
- **Barradas** (não chegam ao agente nem ao prestador)
- **Logadas** no `LogEvent` com novo tipo `"moderation"`
- **Expõem métricas no Dashboard** de logs existente

---

## 2. Análise do Pipeline Atual

### 2.1 Fluxo de mensagens hoje

```
Cliente (Site/WhatsApp)
  │
  ▼
[WebSocket / Webhook]  ← consumers.py / webhooks.py
  │
  ▼
[Buffer (12s)]  ← buffer.py (debounce WhatsApp)
  │
  ▼
[Core: processar_mensagem]  ← core.py
  │
  ▼
[Detecta cidade] → [RAG] → [OpenAI GPT-4.1-mini + tools]
  │
  ▼
[Formatador] → [WS / WhatsApp] ← formatador.py / waha.py
```

### 2.2 Gap: nenhuma moderação

| Etapa | Tem moderação? | Risco |
|---|---|---|
| Entrada WebSocket (`consumers.py:receive`) | ❌ | Usuário envia ofensa direto |
| Entrada Webhook (`webhooks.py:waha_webhook`) | ❌ | WhatsApp sem filtro |
| Saída do agente (`core.py`) | ❌ | GPT pode gerar conteúdo inadequado |
| Armazenamento (`ChatMessage`) | ❌ | Mensagens ficam no banco sem flag |
| Dashboard de logs | ❌ | Nenhuma métrica de moderação |

### 2.3 Infraestrutura existente que será reusada

- **OpenAI client** (`agent/openai_client.py`): singleton já configurado
- **LogEvent** (`logs/models.py`): modelo de log com `tipo`, `payload`, `usuario`
- **Dashboard** (`logs/dashboard.py` + `dashboard.html`): template Chart.js,
  pronto para estender com novos cards e seções
- **ChatMessage** (`agent/models.py`): armazena role "user" / "bot"
- **RequestLogMiddleware** (`logs/middleware.py`): intercepta requests
- **ChatLead/Chat** (`agent/models.py`): identifica o autor da mensagem

---

## 3. Arquitetura Proposta

### 3.1 Pipeline de moderação (3 camadas)

```
Mensagem do usuário
  │
  ├─► Camada 1: Blacklist (Regex)
  │   ├─ Palavrões, ofensas conhecidas
  │   ├─ Padrões de telefone/e-mail/whatsapp
  │   └─ Palavras-chave de circunvenção
  │   │
  │   ├── FLAGGED (score ≥ 0.9) → BLOQUEIA + LOG
  │   └── SUSPECT (score 0.3–0.9) → Camada 2
  │
  ├─► Camada 2: OpenAI Moderation API
  │   ├─ Gratuita, multi-categoria
  │   ├─ Detecta: hate, harassment, sexual, violence, self-harm
  │   └─ Threshold configurável por categoria
  │   │
  │   ├── FLAGGED → BLOQUEIA + LOG
  │   └── SUSPECT → Camada 3
  │
  ├─► Camada 3: Classificador contextual (GPT-4o-mini)
  │   ├─ Detecta circunvenção ("me liga no zap", "vou te pagar fora")
  │   ├─ Detecta spam, pedidos de dados pessoais
  │   └─ Prompt system especializado + structured output
  │   │
  │   ├── FLAGGED → BLOQUEIA + LOG
  │   └── CLEAN → ✅ Libera para o agente
```

### 3.2 Modelos de dados

#### Novo modelo: `ModerationEvent` (backend/logs/models.py)

```python
class ModerationEvent(models.Model):
    """Evento de moderacao: registro de mensagem barrada ou suspeita."""

    CATEGORIES = [
        ("offense", "Ofensa / Palavrão"),
        ("harassment", "Assédio"),
        ("hate", "Discurso de ódio"),
        ("sexual", "Conteúdo sexual"),
        ("violence", "Violência"),
        ("circumvention", "Circunvenção (fora da plataforma)"),
        ("spam", "Spam"),
        ("personal_data", "Tentativa de obter dados pessoais"),
        ("other", "Outro"),
    ]

    ACTION_CHOICES = [
        ("blocked", "Barrada"),
        ("warned", "Avisado"),
        ("approved", "Aprovada (suspeita mas liberada)"),
    ]

    message = models.TextField()
    category = models.CharField(max_length=30, choices=CATEGORIES, db_index=True)
    confidence = models.FloatField(help_text="Score 0.0 a 1.0")
    action_taken = models.CharField(max_length=10, choices=ACTION_CHOICES)
    layer = models.CharField(
        max_length=10,
        choices=[("regex", "Regex"), ("moderation_api", "Moderation API"), ("classifier", "Classificador")],
    )
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL
    )
    telefone = models.CharField(max_length=20, blank=True)
    chat = models.ForeignKey("agent.Chat", null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Evento de Moderação"
        verbose_name_plural = "Eventos de Moderação"
```

#### Extensão em `ChatMessage` (agent/models.py)

```python
# Novo campo opcional
moderation_flagged = models.BooleanField(default=False)
moderation_category = models.CharField(max_length=30, blank=True, default="")
```

#### Tipo extra em LogEvent

Adicionar `"moderation"` à lista `TIPOS` em `LogEvent`:

```python
TIPOS = [
    ...
    ("moderation", "Moderação"),
]
```

### 3.3 Módulo de moderação

Arquivo novo: **`backend/agent/moderation.py`**

```python
"""
Pipeline de moderacao de mensagens do chat HIVEE.

3 camadas:
  Layer 1 — Regex/Blacklist (instantaneo)
  Layer 2 — OpenAI Moderation API (gratuito)
  Layer 3 — Classificador contextual GPT (circunvencao, spam)
"""

import re
import logging
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

THRESHOLD_BLOCK = 0.85        # Acima disso bloqueia direto
THRESHOLD_ESCALATE = 0.30     # Acima disso vai pra prox camada

CIRCUMVENTION_PATTERNS = [
    # Telefone
    r"(\d{2,3}[\s.-]?)?\d{4,5}[\s.-]?\d{4}",
    # WhatsApp / zap / telegram
    r"\b(zap|whatsapp|wpp|telegram|telefone|celular|cel|whats)\b",
    # Combinar fora
    r"(fora\s+(da\s+)?(plataforma|hivee|app|site)|por\s+fora|sem\s+(a\s+)?plataforma)",
    r"(me\s+(chama|liga|manda|add|adiciona|passa)\s*(no|pelo|por))",
    r"(pagamento\s+direto|dinheiro\s+direto|pix\s+direto)",
    # Email
    r"\b[\w.+-]+@[\w-]+\.[\w.]+",
    # Instagram / redes sociais
    r"\b(@\w+|instagram\.com|facebook\.com)",
]

OFFENSE_KEYWORDS = [
    # Padrões de ofensas comuns em PT-BR
    r"\b(vai\s+(tomar|se\s+fuder|pro\s+caralho)|filho\s+da\s+puta)\b",
    # Lista expandivel via admin futuramente
]
```

#### Função principal: `moderate_message`

```python
@dataclass
class ModerationResult:
    flagged: bool = False
    category: str = ""
    confidence: float = 0.0
    layer: str = ""
    action: str = "approved"      # blocked | warned | approved
    details: dict = field(default_factory=dict)

def moderate_message(
    text: str,
    usuario=None,
    telefone: str = "",
    chat=None,
) -> ModerationResult:
    # Layer 1: Regex/Blacklist
    result = _layer_regex(text)
    if result.flagged and result.confidence >= THRESHOLD_BLOCK:
        _save_event(result, text, usuario, telefone, chat)
        return result
    if result.confidence >= THRESHOLD_ESCALATE:
        # Passa contexto pra prox camada
        result.details["regex_hits"] = result.details.get("matches", [])

    # Layer 2: OpenAI Moderation API
    result = _layer_moderation_api(text, result)
    if result.flagged and result.confidence >= THRESHOLD_BLOCK:
        _save_event(result, text, usuario, telefone, chat)
        return result

    # Layer 3: Classificador contextual
    result = _layer_classifier(text, result)
    if result.flagged:
        _save_event(result, text, usuario, telefone, chat)

    return result
```

#### Layer 1 — Regex

```python
def _layer_regex(text: str) -> ModerationResult:
    text_lower = text.lower()
    matches = []

    # Checa ofensas
    for pattern in OFFENSE_KEYWORDS:
        if re.search(pattern, text_lower):
            matches.append({"pattern": pattern, "type": "offense"})

    # Checa circunvencao
    for pattern in CIRCUMVENTION_PATTERNS:
        if re.search(pattern, text_lower):
            matches.append({"pattern": pattern, "type": "circumvention"})

    if not matches:
        return ModerationResult()

    confidence = min(1.0, len(matches) * 0.25)
    types = {m["type"] for m in matches}
    primary = "circumvention" if "circumvention" in types else "offense"

    action = "blocked" if confidence >= THRESHOLD_BLOCK else "warned"

    return ModerationResult(
        flagged=confidence >= THRESHOLD_ESCALATE,
        category=primary,
        confidence=round(confidence, 2),
        layer="regex",
        action=action,
        details={"matches": matches},
    )
```

#### Layer 2 — OpenAI Moderation API

```python
def _layer_moderation_api(text: str, prev: ModerationResult) -> ModerationResult:
    from .openai_client import get_openai_client

    try:
        response = get_openai_client().moderations.create(
            model="omni-moderation-latest",
            input=text,
        )
        result = response.results[0]

        categories = result.categories
        scores = result.category_scores

        # Mapeia categorias do OpenAI para as do HIVEE
        CAT_MAP = {
            "hate": "hate",
            "hate/threatening": "hate",
            "harassment": "harassment",
            "harassment/threatening": "harassment",
            "sexual": "sexual",
            "violence": "violence",
            "self-harm": "other",
        }

        if not result.flagged:
            return prev  # Passa adiante (ainda pode ser circunvencao)

        max_cat, max_score = "", 0.0
        for cat_key, hivee_cat in CAT_MAP.items():
            score = getattr(scores, cat_key, 0) or 0
            if score > max_score:
                max_score = score
                max_cat = hivee_cat

        # Combina com score da camada anterior
        combined_confidence = max(prev.confidence, round(max_score, 2))

        action = "blocked" if combined_confidence >= THRESHOLD_BLOCK else "warned"

        return ModerationResult(
            flagged=True,
            category=max_cat or prev.category,
            confidence=combined_confidence,
            layer="moderation_api",
            action=action,
            details={**prev.details, "openai_categories": {c: getattr(scores, c, 0) for c in CAT_MAP}},
        )
    except Exception:
        logger.exception("Moderation API falhou, ignorando camada 2")
        return prev
```

#### Layer 3 — Classificador contextual (circunvenção)

```python
SYSTEM_MODERATION_PROMPT = """Voce e um classificador de mensagens para uma plataforma de servicos.

Classifique a mensagem do usuario nas seguintes categorias. Responda APENAS JSON:

{
  "flagged": true/false,
  "category": "circumvention" | "spam" | "personal_data" | "offense" | "none",
  "confidence": 0.0-1.0,
  "reason": "explicacao curta em pt-br"
}

Categorias a detectar:
- circumvention: usuario tentando combinar servico por fora da plataforma
  (pedir/whatsapp/telefone/email/instagram, pagamento direto, "fora da plataforma")
- spam: mensagem repetitiva, propaganda, irrelevante
- personal_data: pedindo dados pessoais do prestador (CPF, endereco completo)
- offense: ofensa, xingamento, assedio
- none: mensagem normal, sem problemas
"""

def _layer_classifier(text: str, prev: ModerationResult) -> ModerationResult:
    # Se ja foi bloqueado por regex ou moderation API, nao precisa classificar
    if prev.action == "blocked":
        return prev

    from .openai_client import get_openai_client

    try:
        response = get_openai_client().chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_MODERATION_PROMPT},
                {"role": "user", "content": text},
            ],
            response_format={"type": "json_object"},
            max_tokens=150,
            temperature=0,
        )
        import json
        parsed = json.loads(response.choices[0].message.content)

        if not parsed.get("flagged"):
            # Se camadas anteriores suspeitaram mas o classifier disse "none",
            # a mensagem pode passar (prev.action = "warned" → libera)
            if prev.flagged and prev.action == "warned":
                return ModerationResult(
                    flagged=False,
                    category="none",
                    confidence=0,
                    layer="classifier",
                    action="approved",
                    details={"overriden_by": "classifier", "reason": parsed.get("reason")},
                )
            return prev

        confidence = round(max(prev.confidence, parsed.get("confidence", 0.5)), 2)
        action = "blocked" if confidence >= THRESHOLD_BLOCK else "warned"

        return ModerationResult(
            flagged=True,
            category=parsed.get("category", prev.category) or "other",
            confidence=confidence,
            layer="classifier",
            action=action,
            details={**prev.details, "classifier_reason": parsed.get("reason")},
        )
    except Exception:
        logger.exception("Classifier contextual falhou")
        return prev
```

#### Persistência do evento

```python
def _save_event(result: ModerationResult, text: str, usuario, telefone: str, chat):
    from logs.models import LogEvent, ModerationEvent

    # Salva ModerationEvent (detalhado)
    ModerationEvent.objects.create(
        message=text[:500],
        category=result.category,
        confidence=result.confidence,
        action_taken=result.action,
        layer=result.layer,
        usuario=usuario,
        telefone=telefone,
        chat=chat,
    )

    # Salva LogEvent (para o dashboard existente)
    LogEvent.objects.create(
        tipo="moderation",
        usuario=usuario,
        rota=f"/ws/chat/{telefone}/" if telefone else "/moderation/",
        metodo="MODERATE",
        status_code=403 if result.action == "blocked" else 200,
        payload={
            "category": result.category,
            "confidence": result.confidence,
            "action": result.action,
            "layer": result.layer,
            "message_preview": text[:100],
        },
        session_id=getattr(chat, "id", None) or "",
        user_agent="",
    )
```

---

## 4. Pontos de Injeção no Pipeline

### 4.1 consumers.py — antes de processar

```python
async def receive(self, text_data):
    try:
        data = json.loads(text_data)
    except json.JSONDecodeError:
        return

    conteudo = data.get("content", "")
    if not conteudo:
        return

    # --- NOVO: moderação ---
    from .moderation import moderate_message

    result = moderate_message(
        text=conteudo,
        usuario=self.user,
        telefone=self.telefone,
    )

    if result.action == "blocked":
        await self.send(text_data=json.dumps({
            "role": "bot",
            "content": "⚠️ Sua mensagem foi bloqueada por violar nossas diretrizes de uso.",
            "typing": False,
        }))
        logger.warning(
            "Mensagem BLOQUEADA [%s] cat=%s conf=%.2f layer=%s",
            self.telefone, result.category, result.confidence, result.layer,
        )
        return

    if result.action == "warned":
        await self.send(text_data=json.dumps({
            "role": "bot",
            "content": "⚠️ Atenção: sua mensagem parece violar nossas diretrizes. Evite ofensas e não tente combinar serviços fora da plataforma.",
            "typing": False,
        }))
        # Ainda assim deixa passar (warned ≠ blocked)
    # --- FIM NOVO ---

    await self.send(text_data=json.dumps({"role": "bot", "content": "", "typing": True}))
    await self._processar_site(conteudo)
```

### 4.2 webhooks.py — antes de enfileirar

```python
@api_view(["POST"])
def waha_webhook(request):
    ...
    conteudo = extrair_conteudo(payload, telefone)

    # --- NOVO: moderação ---
    from .moderation import moderate_message

    result = moderate_message(
        text=conteudo,
        telefone=telefone,
    )

    if result.action == "blocked":
        logger.warning(
            "WhatsApp BLOQUEADO [%s] cat=%s conf=%.2f layer=%s msg=%s",
            telefone, result.category, result.confidence, result.layer, conteudo[:60],
        )
        enviar_whatsapp(
            telefone,
            "⚠️ Sua mensagem foi bloqueada por violar nossas diretrizes de uso.",
        )
        return Response({"status": "blocked", "reason": result.category})

    if result.action == "warned":
        enviar_whatsapp(
            telefone,
            "⚠️ Atenção: sua mensagem parece violar nossas diretrizes. Evite ofensas e não tente combinar serviços fora da plataforma.",
        )
    # --- FIM NOVO ---

    push(telefone, conteudo)
    return Response({"status": "ok"})
```

### 4.3 Opcional: moderação na saída do agente (core.py)

```python
# Em processar_mensagem, após receber resposta do GPT:
resposta_final = response2.choices[0].message.content

# --- NOVO: moderação de saída ---
output_result = moderate_message(text=resposta_final or "", layer_filter="moderation_api")
if output_result.flagged:
    logger.warning("Saida do GPT MODERADA cat=%s", output_result.category)
    resposta_final = (
        "Desculpe, não posso responder isso. "
        "Vamos manter a conversa respeitosa e dentro das regras da plataforma."
    )
# --- FIM NOVO ---
```

---

## 5. Dashboard — Novas Seções

### 5.1 Cards no topo

No `dashboard.html`, adicionar ao grid-cards:

```html
<div class="card vermelho">
  <div class="valor vermelho">{{ total_moderacoes }}</div>
  <div class="rotulo">Mensagens moderadas</div>
</div>
<div class="card laranja">
  <div class="valor laranja">{{ bloqueios }}</div>
  <div class="rotulo">Bloqueios</div>
</div>
<div class="card roxo">
  <div class="valor roxo">{{ circunvencoes }}</div>
  <div class="rotulo">Tentativas de circunvenção</div>
</div>
```

### 5.2 Nova seção: "Últimas moderações"

```html
{% if moderacoes %}
<div class="secao">
  <div class="header">
    <h2>🛡️ Últimas moderações</h2>
    <span class="count">{{ moderacoes|length }}</span>
  </div>
  <div class="panel" style="padding:0">
    <table>
      <thead>
        <tr>
          <th>Data</th>
          <th>Usuário</th>
          <th>Categoria</th>
          <th>Confiança</th>
          <th>Ação</th>
          <th>Camada</th>
          <th>Mensagem</th>
        </tr>
      </thead>
      <tbody>
        {% for m in moderacoes %}
        <tr class="{% if m.action_taken == 'blocked' %}erro-linha{% endif %}">
          <td>{{ m.created_at|date:"d/m H:i:s" }}</td>
          <td>{{ m.usuario.get_full_name|default:m.telefone|default:"-" }}</td>
          <td><span class="badge badge-{{ m.category }}">{{ m.get_category_display }}</span></td>
          <td>{{ m.confidence|floatformat:2 }}</td>
          <td>
            <span class="badge badge-{% if m.action_taken == 'blocked' %}error{% else %}search{% endif %}">
              {{ m.get_action_taken_display }}
            </span>
          </td>
          <td>{{ m.get_layer_display }}</td>
          <td style="max-width:200px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap" title="{{ m.message }}">
            {{ m.message|truncatechars:40 }}
          </td>
        </tr>
        {% endfor %}
      </tbody>
    </table>
  </div>
</div>
{% endif %}
```

### 5.3 Novos estilos de badge

```css
.badge-moderation { background: rgba(239,68,68,0.12); color: #f87171; }
.badge-offense { background: rgba(239,68,68,0.12); color: #f87171; }
.badge-harassment { background: rgba(239,68,68,0.12); color: #f87171; }
.badge-hate { background: rgba(239,68,68,0.12); color: #f87171; }
.badge-sexual { background: rgba(239,68,68,0.12); color: #f87171; }
.badge-violence { background: rgba(239,68,68,0.12); color: #f87171; }
.badge-circumvention { background: rgba(245,158,11,0.12); color: #fbbf24; }
.badge-spam { background: rgba(107,114,128,0.12); color: #9ca3af; }
```

### 5.4 Gráfico de pizza de categorias de moderação

```javascript
initChart('chartModeracao', {
  type: 'doughnut',
  data: {
    labels: {{ moderacao_por_categoria_json|safe }}.map(p => p[0]),
    datasets: [{
      data: {{ moderacao_por_categoria_json|safe }}.map(p => p[1]),
      backgroundColor: ['#ef4444','#f87171','#f59e0b','#9ca3af','#a78bfa','#22d3ee'],
      borderWidth: 0,
    }],
  },
  options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { position: 'bottom', labels: { color: '#888', padding: 10, font: {size:10} } } } },
});
```

### 5.5 Dados do contexto (dashboard.py)

```python
# Adicionar ao dashboard():
moderacoes = ModerationEvent.objects.filter(created_at__gte=inicio_periodo)
total_moderacoes = moderacoes.count()
bloqueios = moderacoes.filter(action_taken="blocked").count()
circunvencoes = moderacoes.filter(category="circumvention").count()
moderacoes_lista = moderacoes.select_related("usuario").order_by("-created_at")[:25]

moderacao_por_categoria = dict(
    moderacoes.values_list("category")
    .annotate(total=Count("id"))
    .order_by("-total")
)

# Adicionar ao context dict:
{
    "total_moderacoes": total_moderacoes,
    "bloqueios": bloqueios,
    "circunvencoes": circunvencoes,
    "moderacoes": moderacoes_lista,
    "moderacao_por_categoria_json": list(moderacao_por_categoria.items()),
}
```

---

## 6. Tabela de Categorias de Moderação

| Categoria | O que detecta | Exemplo | Camada principal |
|---|---|---|---|
| `offense` | Palavrões, xingamentos, ofensas diretas | "você é um incompetente" | Regex + Classifier |
| `harassment` | Assédio, perseguição, ameaças | "seu bairro é tal, vou te achar" | Moderation API |
| `hate` | Discurso de ódio (raça, gênero, religião) | insultos raciais | Moderation API |
| `sexual` | Conteúdo sexual explícito | assédio sexual | Moderation API |
| `violence` | Violência, ameaça física | "vou te quebrar" | Moderation API |
| `circumvention` | "Fora da plataforma" | "me chama no zap 11999999999" | Regex + Classifier |
| `spam` | Repetitivo, propaganda | "contrata meu primo também" | Classifier |
| `personal_data` | Pedido de dados sensíveis | "me passa seu CPF e endereço" | Classifier |

---

## 7. Plano de Implementação

### Fase 1 — Backend: modelo + módulo de moderação

1. Criar `ModerationEvent` em `backend/logs/models.py`
2. Adicionar `"moderation"` aos TIPOS de `LogEvent`
3. Rodar `makemigrations` + `migrate`
4. Criar `backend/agent/moderation.py` com o pipeline de 3 camadas
5. Registrar `ModerationEvent` no admin (`backend/logs/admin.py`)

### Fase 2 — Pontos de injeção

1. Modificar `consumers.py:receive()` para chamar `moderate_message` antes de processar
2. Modificar `webhooks.py:waha_webhook()` para moderar WhatsApp
3. Opcional: moderar saída do GPT em `core.py`

### Fase 3 — Dashboard

1. Estender `logs/dashboard.py` com métricas de moderação
2. Estender `logs/templates/logs/dashboard.html` com cards + tabela + gráfico
3. Adicionar filtro de moderação no seletor de range

### Fase 4 — Refinamentos

1. Implementar **rate limiting** por usuário (X bloqueios/dia → mute temporário)
2. Implementar **escalonamento manual** (admin revisa mensagens "warned")
3. Adicionar webhook opcional para notificar admin sobre pico de bloqueios
4. Cache de resultados de moderação (evitar re-classificar mensagens idênticas)
5. Testes unitários para o pipeline de moderação

---

## 8. Considerações de Segurança e Privacidade

| Aspecto | Decisão |
|---|---|
| Armazenamento | Mensagens barradas salvam preview (até 500 chars) para auditoria, nunca texto completo |
| Retenção | `ModerationEvent` segue TTL dos logs (30 dias via `limpar_logs`) |
| False positives | Mensagens `warned` passam mesmo assim (nunca bloqueamos por engano na dúvida) |
| Custo | Moderation API é gratuita; Classificador gpt-4o-mini custa ~$0.15/1M input tokens |
| Latência | Regex: 0ms. Moderation API: ~200-400ms. Classifier: ~500-800ms. Total < 1.5s |
| Fallback | Se qualquer camada falhar (timeout/erro), mensagem passa sem moderação |

---

## 9. Resumo Arquitetural

```
INPUT (WS/WHATSAPP)
    │
    ▼
┌─────────────────────────────────────┐
│  moderation.py                      │
│                                     │
│  Layer 1: Regex (0ms) ──► FLAGGED? ──► BLOCK + LOG
│       │  suspect?                    │
│       ▼                              │
│  Layer 2: Moderation API (free) ──► FLAGGED? ──► BLOCK + LOG
│       │  suspect?                    │
│       ▼                              │
│  Layer 3: GPT Classifier ────────► FLAGGED? ──► BLOCK/LOG
│       │  clean                       │
│       ▼                              ▼
│    ✅ LIBERADO                  🛑 BLOQUEADO
└─────────────────────────────────────┘
    │
    ▼
  Agent Core (processar_mensagem)
    │
    ▼
  Dashboard (LogEvent + ModerationEvent)
```

**Integração com o ecossistema existente:**
- `LogEvent.tipo = "moderation"` → aparece automaticamente nos filtros do dashboard
- `ModerationEvent` → tabela dedicada com detalhes (categoria, confiança, camada)
- Dashboard Chart.js → novo gráfico de pizza e cards de resumo
- Admin Django → `ModerationEventAdmin` com list_filter e search

---

## 10. Referências

- **OpenAI Moderation API** (gratuito): detecta hate, harassment, sexual, violence,
  self-harm em texto e imagem. Documentação: https://platform.openai.com/docs/guides/moderation
- **OpenAI Safety Best Practices**: recomenda usar Moderation API + KYC + rate limiting
  https://developers.openai.com/api/docs/guides/safety-best-practices
- **Padrão de arquitetura**: pipeline multi-camada com fallthrough (LangChain
  OpenAIModerationMiddleware como referência)
- **Código existente reutilizado**: `get_openai_client()` (singleton), `LogEvent`
  (log unificado), `ChatMessage` (persistência), dashboard template + Chart.js
