# Sistema de Notificações — Prestador e Cliente

## 1. Contexto

A HIVEE atualmente não possui um sistema de notificações. Usuários não são alertados
quando:

- Um prestador é aprovado/rejeitado
- Um cliente solicita um serviço
- O status de um serviço muda
- Recebem uma nova mensagem no chat
- Um prestador favoritado fica disponível
- O CPF é verificado

A única comunicação existente é o chat via WebSocket (site) e WhatsApp (via WAHA),
ambos no escopo do **agent** (chat IA). Não há canal genérico de notificações.

Este documento propõe a implementação completa de um sistema de notificações
in-app (WebSocket) e WhatsApp, seguindo os padrões existentes do projeto.

---

## 2. Visão Geral da Arquitetura

```
                    ┌──────────────────────────────────┐
                    │      Evento de Negócio            │
                    │  (ex: service_order.transition)   │
                    └──────────┬───────────────────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │  NotificationService │
                    │  (create_notification)│
                    └──────┬───────────────┘
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
     ┌────────────┐ ┌──────────┐ ┌──────────┐
     │   Banco    │ │ WebSocket│ │ WhatsApp │
     │ (historico)│ │ (tempo   │ │ (WAHA)   │
     │           │ │  real)   │ │ (opcional)│
     └────────────┘ └──────────┘ └──────────┘
```

Três camadas:
1. **Modelo `Notification`** — persiste o histórico (seguindo padrão `LogEvent`)
2. **`NotificationsConsumer`** (WebSocket) — entrega em tempo real para usuários logados
3. **WAHA** — canal alternativo/fallback para prestadores que usam WhatsApp

---

## 3. Modelo de Dados

### 3.1 Notification (`catalog/models.py`)

Adicionar ao final do arquivo:

```python
class Notification(models.Model):
    class Tipo(models.TextChoices):
        # Conta / Prestador
        PROVIDER_APPROVED = "provider_approved", "Perfil aprovado"
        PROVIDER_REJECTED = "provider_rejected", "Perfil rejeitado"
        CPF_VERIFIED = "cpf_verified", "CPF verificado"
        CPF_MISMATCH = "cpf_mismatch", "CPF não confere"

        # Ordens de serviço
        ORDER_REQUESTED = "order_requested", "Nova solicitação de serviço"
        ORDER_CONFIRMED = "order_confirmed", "Serviço confirmado"
        ORDER_IN_PROGRESS = "order_in_progress", "Serviço em andamento"
        ORDER_COMPLETED = "order_completed", "Serviço concluído"
        ORDER_CANCELLED = "order_cancelled", "Serviço cancelado"
        ORDER_DISPUTED = "order_disputed", "Disputa aberta"
        ORDER_REVIEWED = "order_reviewed", "Serviço avaliado"

        # Chat
        NEW_MESSAGE = "new_message", "Nova mensagem"

        # Plataforma
        NEW_PROVIDER_IN_AREA = "new_provider_in_area", "Novo profissional na sua área"
        RECOMMENDATION = "recommendation", "Recomendação para você"

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    tipo = models.CharField(max_length=30, choices=Tipo.choices)
    title = models.CharField(max_length=200)
    body = models.TextField(blank=True)
    link = models.CharField(max_length=300, blank=True, default="")
    payload = models.JSONField(default=dict, blank=True)
    is_read = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["recipient", "is_read"]),
            models.Index(fields=["recipient", "-created_at"]),
        ]
        verbose_name = "Notificação"
        verbose_name_plural = "Notificações"

    def __str__(self) -> str:
        return f"[{self.get_tipo_display()}] {self.recipient} — {self.title[:60]}"
```

### 3.2 Por que este design

- **`recipient`**: FK para `User` — tanto clientes quanto prestadores são `User`.
  A distinção é feita pelo `tipo` e pelo `payload`.
- **`tipo`**: enum centralizado com todas as categorias, evitando strings soltas.
- **`link`**: URL relativa para onde o usuário deve ser levado ao clicar
  (ex: `/meus-servicos/42`, `/prestador/eletricista-joao`).
- **`payload`**: JSON flexível para dados extras (slug do provider, id da ordem, etc.),
  exatamente como `LogEvent.payload`.
- **`is_read`**: índice composto com `recipient` para queries rápidas de "não lidas".
- Segue as mesmas convenções dos modelos existentes (verbose_name em pt-BR, `Meta`,
  `__str__`).

---

## 4. NotificationService (Core)

Arquivo novo: `backend/catalog/services.py`

```python
import json
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.contrib.auth import get_user_model

from .models import Notification

User = get_user_model()


def notify_user(
    *,
    recipient: User,
    tipo: str,
    title: str,
    body: str = "",
    link: str = "",
    payload: dict | None = None,
    via_whatsapp: bool = False,
) -> Notification:
    """Cria uma notificação e a envia em tempo real via WebSocket.

    Parâmetros
    ----------
    recipient : User
        Usuário destinatário.
    tipo : str
        Uma das chaves de Notification.Tipo (ex: 'order_requested').
    title, body : str
        Texto da notificação.
    link : str
        URL relativa para ação (ex: '/meus-servicos/5').
    payload : dict | None
        Dados extras (ex: {'provider_slug': '...', 'order_id': 5}).
    via_whatsapp : bool
        Se True, também tenta enviar via WhatsApp (se o usuário tiver telefone).
    """
    notification = Notification.objects.create(
        recipient=recipient,
        tipo=tipo,
        title=title,
        body=body,
        link=link,
        payload=payload or {},
    )

    # Envia via WebSocket em tempo real
    _send_via_ws(notification)

    # Canal opcional: WhatsApp
    if via_whatsapp:
        _send_via_wpp(recipient, title, body, link)

    return notification


# ── Internals ──────────────────────────────────────────────────────────

def _send_via_ws(notification: Notification) -> None:
    """Envia a notificação para o grupo WebSocket do usuário."""
    try:
        layer = get_channel_layer()
    except Exception:
        return  # sem channel layer configurado

    async_to_sync(layer.group_send)(
        f"notify_user_{notification.recipient_id}",
        {
            "type": "notification.message",
            "data": {
                "id": notification.id,
                "tipo": notification.tipo,
                "title": notification.title,
                "body": notification.body,
                "link": notification.link,
                "payload": notification.payload,
                "is_read": False,
                "created_at": notification.created_at.isoformat(),
            },
        },
    )


def _send_via_wpp(recipient: User, title: str, body: str, link: str) -> None:
    """Tenta enviar notificação via WhatsApp usando a infraestrutura WAHA existente.

    Só envia se o usuário tiver telefone cadastrado no perfil e o WhatsApp
    estiver configurado.
    """
    from django.conf import settings

    telefone = getattr(getattr(recipient, "profile", None), "telefone", "")
    if not telefone:
        return

    try:
        from agent.waha import enviar_whatsapp
        texto = f"*{title}*\n\n{body}\n\n{settings.FRONTEND_URL}{link}"
        enviar_whatsapp(telefone, texto)
    except Exception:
        pass  # fallback silencioso — o canal WebSocket já entregou
```

### Dependência: `FRONTEND_URL` no settings

Adicionar em `backend/hivee/settings.py`:

```python
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5200")
```

---

## 5. WebSocket — NotificationsConsumer

### 5.1 Consumer (`backend/catalog/consumers.py`)

Arquivo novo — seguindo o padrão de `ChatConsumer` em `agent/consumers.py`:

```python
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from catalog.authentication import CookieTokenAuthentication

class NotificationsConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        user = await self._authenticate()
        if user is None:
            await self.close(code=4001)
            return

        self.user = user
        self.group_name = f"notify_user_{user.id}"

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data):
        """Aceita comandos do cliente para marcar notificações como lidas."""
        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            return

        action = data.get("action")

        if action == "mark_read":
            await self._mark_read(data.get("id"))
        elif action == "mark_all_read":
            await self._mark_all_read()

    async def notification_message(self, event):
        """Envia notificação para o cliente (chamado por group_send)."""
        await self.send(text_data=json.dumps({
            "type": "notification",
            "data": event["data"],
        }))

    async def unread_count(self, event):
        """Envia contagem atualizada de não lidas."""
        await self.send(text_data=json.dumps({
            "type": "unread_count",
            "count": event["count"],
        }))

    # ── Helpers ──────────────────────────────────────────────────────

    async def _authenticate(self):
        """Autentica via cookie httpOnly (mesmo padrão do ChatConsumer)."""
        from django.contrib.auth import get_user_model
        from rest_framework.authtoken.models import Token

        User = get_user_model()
        headers = dict(self.scope.get("headers", []))
        cookie_header = headers.get(b"cookie", b"").decode()

        for part in cookie_header.split(";"):
            part = part.strip()
            if part.startswith("hivee_token="):
                key = part[len("hivee_token="):]
                try:
                    token = await self._get_token(key)
                    if token:
                        return token.user
                except Exception:
                    return None
        return None

    async def _get_token(self, key):
        """Retorna o token de forma assíncrona segura."""
        from database import sync_to_async
        from rest_framework.authtoken.models import Token
        try:
            return await sync_to_async(Token.objects.select_related("user").get)(key=key)
        except Exception:
            return None

    async def _mark_read(self, notification_id):
        from .models import Notification
        from database import sync_to_async

        if notification_id:
            await sync_to_async(
                lambda: Notification.objects.filter(
                    id=notification_id, recipient=self.user
                ).update(is_read=True)
            )()

    async def _mark_all_read(self):
        from .models import Notification
        from database import sync_to_async

        await sync_to_async(
            lambda: Notification.objects.filter(
                recipient=self.user, is_read=False
            ).update(is_read=True)
        )()
```

### 5.2 Registro de rota WebSocket (`backend/hivee/asgi.py`)

Adicionar ao `URLRouter`:

```python
from catalog.consumers import NotificationsConsumer

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": URLRouter([
        re_path(r"ws/chat/(?P<telefone>[\w-]+)/$", ChatConsumer.as_asgi()),
        re_path(r"ws/notifications/$", NotificationsConsumer.as_asgi()),
    ]),
})
```

### 5.3 Proxy do Vite (`frontend/vite.config.ts`)

Já roteia `/ws` para o backend — nenhuma alteração necessária.

---

## 6. API REST de Notificações

### 6.1 ViewSet (`backend/catalog/views/api_views.py`)

Adicionar ao final do arquivo:

```python
class NotificationViewSet(ViewSet):
    permission_classes = [IsAuthenticated]

    def get_queryset(self, request):
        return Notification.objects.filter(recipient=request.user)

    def list(self, request):
        qs = self.get_queryset(request)

        # Filtro opcional: só não lidas
        if request.query_params.get("unread_only") == "1":
            qs = qs.filter(is_read=False)

        # Paginação
        page = max(1, int(request.query_params.get("page", 1)))
        page_size = min(50, max(1, int(request.query_params.get("page_size", 20))))
        total = qs.count()
        start = (page - 1) * page_size
        chunk = qs[start : start + page_size]

        data = [
            {
                "id": n.id,
                "tipo": n.tipo,
                "title": n.title,
                "body": n.body,
                "link": n.link,
                "payload": n.payload,
                "is_read": n.is_read,
                "created_at": n.created_at.isoformat(),
            }
            for n in chunk
        ]

        def page_url(n):
            return request.build_absolute_uri(
                _replace_query(request, "page", n)
            )

        return Response({
            "count": total,
            "next": page_url(page + 1) if start + page_size < total else None,
            "previous": page_url(page - 1) if page > 1 else None,
            "results": data,
        })

    def retrieve(self, request, pk=None):
        try:
            n = self.get_queryset(request).get(pk=pk)
        except Notification.DoesNotExist:
            return Response({"detail": "Notificação não encontrada."}, status=404)
        return Response({
            "id": n.id,
            "tipo": n.tipo,
            "title": n.title,
            "body": n.body,
            "link": n.link,
            "payload": n.payload,
            "is_read": n.is_read,
            "created_at": n.created_at.isoformat(),
        })

    @action(detail=True, methods=["post"])
    def mark_read(self, request, pk=None):
        try:
            n = self.get_queryset(request).get(pk=pk)
        except Notification.DoesNotExist:
            return Response({"detail": "Notificação não encontrada."}, status=404)
        n.is_read = True
        n.save(update_fields=["is_read"])
        return Response(status=204)

    @action(detail=False, methods=["post"])
    def mark_all_read(self, request):
        self.get_queryset(request).filter(is_read=False).update(is_read=True)
        return Response(status=204)

    @action(detail=False, methods=["get"])
    def unread_count(self, request):
        count = self.get_queryset(request).filter(is_read=False).count()
        return Response({"count": count})
```

### 6.2 Registro de rota (`backend/catalog/urls.py`)

```python
router.register(r"notifications", NotificationViewSet, basename="notification")
```

### 6.3 Endpoints gerados

| Método | URL | Descrição |
|--------|-----|-----------|
| GET | `/api/notifications/` | Lista (paginada, filtro `?unread_only=1`) |
| GET | `/api/notifications/{id}/` | Detalhe |
| POST | `/api/notifications/{id}/mark_read/` | Marca uma como lida |
| POST | `/api/notifications/mark_all_read/` | Marca todas como lidas |
| GET | `/api/notifications/unread_count/` | Contagem de não lidas |

---

## 7. Gatilhos de Notificação (Onde chamar `notify_user`)

### 7.1 Exemplos de uso espalhados pelo código existente

| Evento | Arquivo / Local | Chamada |
|--------|----------------|---------|
| Provider aprovado | `catalog/admin.py` (action `approve_providers`) | `notify_user(recipient=provider.owner, tipo="provider_approved", ...)` |
| Provider rejeitado | `catalog/admin.py` (action `reject_providers`) | `notify_user(recipient=provider.owner, tipo="provider_rejected", ...)` |
| CPF verificado | `catalog/serializers.py` (RegisterSerializer / consulta ReceitaWS) | `notify_user(recipient=user, tipo="cpf_verified", ...)` |
| Ordem solicitada | `catalog/views/api_views.py` (ServiceOrderViewSet.create) | `notify_user(recipient=provider.owner, tipo="order_requested", ..., via_whatsapp=True)` |
| Ordem confirmada | `ServiceOrderViewSet.transition` (pending → confirmed) | `notify_user(recipient=order.client, tipo="order_confirmed", ...)` |
| Ordem em andamento | `ServiceOrderViewSet.transition` (confirmed → in_progress) | `notify_user(recipient=order.client, tipo="order_in_progress", ...)` |
| Ordem concluída | `ServiceOrderViewSet.transition` (in_progress → completed) | `notify_user(recipient=order.client, tipo="order_completed", ...)` |
| Ordem cancelada | `ServiceOrderViewSet.transition` (qualquer → cancelled) | `notify_user(recipient=order.provider.owner if cliente cancela ou vice-versa, tipo="order_cancelled", ...)` |
| Disputa aberta | `ServiceOrderViewSet.transition` (in_progress → disputed) | `notify_user(recipient=order.provider.owner, tipo="order_disputed", ..., via_whatsapp=True)` |
| Serviço avaliado | `ServiceOrderViewSet.review` | `notify_user(recipient=order.provider.owner, tipo="order_reviewed", ...)` |
| Nova mensagem no chat | `agent/core.py` ou `agent/formatador.py` | `notify_user(recipient=..., tipo="new_message", link="/chat")` |

### 7.2 Exemplo concreto: notificar ao criar ordem

Dentro de `ServiceOrderViewSet.create()`, após salvar a ordem:

```python
from catalog.services import notify_user

notify_user(
    recipient=provider.owner,
    tipo=Notification.Tipo.ORDER_REQUESTED,
    title="Nova solicitação de serviço",
    body=f"{request.user.first_name} solicitou: {order.title}",
    link=f"/meus-servicos/{order.id}",
    payload={"order_id": order.id, "client_id": request.user.id},
    via_whatsapp=True,  # prestador recebe também no WhatsApp
)
```

---

## 8. Frontend — Types (`frontend/src/types.ts`)

```typescript
export type NotificationTipo =
  | "provider_approved"
  | "provider_rejected"
  | "cpf_verified"
  | "cpf_mismatch"
  | "order_requested"
  | "order_confirmed"
  | "order_in_progress"
  | "order_completed"
  | "order_cancelled"
  | "order_disputed"
  | "order_reviewed"
  | "new_message"
  | "new_provider_in_area"
  | "recommendation";

export interface AppNotification {
  id: number;
  tipo: NotificationTipo;
  title: string;
  body: string;
  link: string;
  payload: Record<string, unknown>;
  is_read: boolean;
  created_at: string;
}

export interface UnreadCount {
  count: number;
}
```

---

## 9. Frontend — API Client (`frontend/src/lib/api.ts`)

```typescript
// Dentro do objeto `api`:
notifications: (params?: { unread_only?: number; page?: number; page_size?: number }) =>
  request<Paginated<AppNotification>>("/notifications/", { params }),
notification: (id: number) =>
  request<AppNotification>(`/notifications/${id}/`),
markNotificationRead: (id: number) =>
  request<void>(`/notifications/${id}/mark_read/`, { method: "POST" }),
markAllNotificationsRead: () =>
  request<void>("/notifications/mark_all_read/", { method: "POST" }),
unreadNotificationCount: () =>
  request<UnreadCount>("/notifications/unread_count/"),
```

---

## 10. Frontend — Componentes

### 10.1 NotificationBell (`frontend/src/components/NotificationBell.tsx`)

Ícone de sino na Navbar com badge de contagem de não lidas. Conecta ao
WebSocket de notificações para atualização em tempo real.

**Comportamento:**
- Ao montar: conecta WebSocket `ws://host/ws/notifications/`
- Recebe `type: "notification"`: adiciona à lista, incrementa badge
- Recebe `type: "unread_count"`: atualiza badge
- Ao clicar: abre `NotificationPanel` (dropdown)
- Ao desconectar: tenta reconectar a cada 3s

### 10.2 NotificationPanel (`frontend/src/components/NotificationPanel.tsx`)

Dropdown exibido ao clicar no sino:

- Lista das últimas notificações (mais recentes primeiro)
- Cada item: ícone por tipo, título, corpo, timestamp relativo
- Ao clicar: marca como lida + navega para `notification.link`
- Botão "Marcar todas como lidas"
- Link "Ver todas" → `/notificacoes` (página completa)

### 10.3 Página de Notificações (`frontend/src/pages/Notificacoes.tsx`)

Rota: `/notificacoes`

- Lista paginada completa (scroll infinito ou paginação)
- Filtro: "Todas" / "Não lidas"
- Cada notificável clicável (marca como lida + navega)
- Agrupamento por data (Hoje, Ontem, Esta semana, etc.)

### 10.4 Toast de Notificação (`frontend/src/components/NotificationToast.tsx`)

Toast animado (Framer Motion) que aparece no canto inferior direito quando
uma notificação chega via WebSocket e o usuário está em outra página.

- Auto-dismiss após 6s
- Ao clicar: navega para o link
- Ícone de acordo com o tipo

---

## 11. Frontend — Rotas (`frontend/src/main.tsx`)

```tsx
import Notificacoes from "@/pages/Notificacoes";

// Dentro de <Route element={<Layout />}>
<Route path="/notificacoes" element={<Notificacoes />} />
```

### Atualizar Navbar

Em `Navbar.tsx`:

```tsx
import NotificationBell from "@/components/NotificationBell";

// Dentro do bloco "Right: auth", ao lado do nome do usuário:
<NotificationBell />
```

---

## 12. WebSocket de Notificações — Diagrama de Conexão

```
Frontend (qualquer página)
  |
  |  conecta WebSocket: ws://host/ws/notifications/
  |  (cookie httpOnly enviado automaticamente pelo navegador)
  v
NotificationsConsumer.connect()
  |  autentica via cookie → extrai user.id
  |  entra no grupo: notify_user_{user.id}
  |  aceita conexão
  v
  ── aguarda eventos ──

── Quando um evento de negócio ocorre (ex: ordem criada) ──

notify_user(recipient=provider.owner, ...)
  |
  |  1. Cria Notification no banco (is_read=False)
  |  2. channel_layer.group_send("notify_user_{id}", {
  |       type: "notification.message",
  |       data: { ... }
  |     })
  |  3. (opcional) enviar_whatsapp()
  v
NotificationsConsumer.notification_message()
  |  send(text_data=json.dumps({ type: "notification", data }))
  v
Frontend WebSocket onmessage()
  |  atualiza badge do sino (se NotificationPanel fechado)
  |  mostra toast (se usuário em outra página)
  |  adiciona à lista (se NotificationPanel aberto)
```

---

## 13. Máquina de Estados das Notificações

```
Notification.is_read:
  false ──(clique ou "marcar como lida")──→ true
  true  ───────────── (não volta) ──────────
```

Notificações **não são deletadas** — o histórico fica disponível para consulta.
A limpeza de notificações antigas pode ser feita via management command
agendado no APScheduler (ex: deletar notificações lidas com mais de 90 dias).

---

## 14. Types de Notificação — Ícones e Cores (Frontend)

```typescript
const NOTIFICATION_META: Record<NotificationTipo, {
  icon: string;   // lucide-react icon name
  color: string;  // Tailwind color class
}> = {
  provider_approved:     { icon: "BadgeCheck", color: "text-emerald-400" },
  provider_rejected:     { icon: "XCircle",    color: "text-rose-400" },
  cpf_verified:          { icon: "ShieldCheck", color: "text-emerald-400" },
  cpf_mismatch:          { icon: "AlertTriangle", color: "text-amber-400" },
  order_requested:       { icon: "FileText",   color: "text-blue-400" },
  order_confirmed:       { icon: "CalendarCheck", color: "text-gold-400" },
  order_in_progress:     { icon: "Play",       color: "text-cyan-400" },
  order_completed:       { icon: "CheckCircle", color: "text-emerald-400" },
  order_cancelled:       { icon: "Ban",        color: "text-zinc-400" },
  order_disputed:        { icon: "AlertTriangle", color: "text-rose-400" },
  order_reviewed:        { icon: "Star",       color: "text-gold-400" },
  new_message:           { icon: "MessageSquare", color: "text-blue-400" },
  new_provider_in_area:  { icon: "MapPin",     color: "text-gold-400" },
  recommendation:        { icon: "Sparkles",   color: "text-gold-400" },
};
```

---

## 15. Canal WhatsApp — Considerações

O canal WhatsApp via WAHA já existe e é usado pelo chat IA. Para notificações:

**Vantagens:**
- Prestadores já usam WhatsApp como canal principal
- Cobertura mesmo quando o usuário não está no site
- Baixo custo de implementação (reusa `waha.py`)

**Limitações:**
- Taxa de entrega: WAHA pode rate-limit
- Sem confirmação de leitura
- Sessão WAHA pode cair (precisa de health check)
- Apenas texto (sem rich formatting)

**Recomendação de uso:** ativar `via_whatsapp=True` apenas para notificações
críticas que o prestador precisa ver (nova solicitação, disputa),
não para notificações de baixa prioridade (recomendações, provedor aprovado).

---

## 16. Checklist de Implementação

### Backend

#### Modelo e Serviço
- [ ] Criar modelo `Notification` em `backend/catalog/models.py`
- [ ] Executar `makemigrations` e `migrate`
- [ ] Criar `backend/catalog/services.py` com `notify_user()`
- [ ] Adicionar `FRONTEND_URL` em `settings.py`

#### WebSocket
- [ ] Criar `backend/catalog/consumers.py` com `NotificationsConsumer`
- [ ] Registrar rota `ws/notifications/` em `asgi.py`

#### API REST
- [ ] Adicionar `NotificationViewSet` em `catalog/views/api_views.py`
- [ ] Registrar rota `notifications` no `DefaultRouter` em `catalog/urls.py`

#### Gatilhos
- [ ] Adicionar `notify_user()` em `ServiceOrderViewSet.create` (nova solicitação)
- [ ] Adicionar `notify_user()` em `ServiceOrderViewSet.transition` (mudanças de status)
- [ ] Adicionar `notify_user()` em `ServiceOrderViewSet.review` (avaliação)
- [ ] Adicionar `notify_user()` em `admin.py` (aprovação/rejeição de provider)
- [ ] Adicionar `notify_user()` nos pontos de verificação de CPF

### Frontend

#### Infraestrutura
- [ ] Adicionar tipos `AppNotification`, `NotificationTipo`, `UnreadCount` em `types.ts`
- [ ] Adicionar métodos `notifications()`, `markNotificationRead()`, etc. em `api.ts`

#### Componentes
- [ ] Criar `NotificationBell.tsx` (ícone do sino com badge WS)
- [ ] Criar `NotificationPanel.tsx` (dropdown de notificações)
- [ ] Criar `NotificationToast.tsx` (toast animado)
- [ ] Criar página `Notificacoes.tsx` (histórico completo)

#### Integração
- [ ] Adicionar `NotificationBell` na `Navbar.tsx`
- [ ] Adicionar rota `/notificacoes` em `main.tsx`
- [ ] Adicionar link no menu mobile da Navbar
