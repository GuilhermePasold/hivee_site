# Sistema de Suporte ao Usuário

## 1. Contexto

Atualmente o único canal de suporte da HIVEE é o **Chat IA** (WhatsApp + WebSocket),
que ajuda usuários a encontrar prestadores. Não há:

- Canal de suporte humano para dúvidas sobre a plataforma (cadastro, pagamento, disputas)
- FAQ ou central de ajuda
- Tickets formais que o usuário possa abrir e acompanhar
- Interface administrativa para a equipe gerir solicitações de suporte
- Histórico de interações de suporte por usuário

Este documento propõe um sistema completo de suporte ao usuário, composto por:

1. **Central de Ajuda (FAQ)** — artigos com perguntas frequentes (apenas para
   usuários logados)
2. **Tickets de Suporte** — solicitações formais com ciclo de vida
3. **Admin de Suporte** — interface para equipe gerenciar tickets
4. **Integração com Chat IA** — escalonamento de conversas para humano
5. **Notificações** — alertas ao usuário sobre respostas (reusa o sistema do
   `docs-sistema-notificacoes.md`)

---

## 2. Regra de Acesso

**Todo o sistema de suporte exige usuário cadastrado e autenticado.**

| Funcionalidade | Requer login | Exceção |
|----------------|-------------|---------|
| FAQ / Central de Ajuda | Sim | — |
| Artigos da FAQ | Sim | — |
| Criar ticket | Sim | — |
| Listar meus tickets | Sim | — |
| Responder ticket | Sim | — |
| Admin (staff) | Sim | Apenas `is_staff=True` |

No frontend, as rotas `/ajuda`, `/ajuda/:slug`, `/suporte/tickets`,
`/suporte/tickets/:id` e `/suporte/novo` devem redirecionar para `/entrar`
se o usuário não estiver autenticado (mesmo padrão usado em
`MinhaConta.tsx` e `ChatPage.tsx`).

No backend, todas as views de suporte usam
`permission_classes = [IsAuthenticated]`.

---

## 3. Modelos de Dados

### 2.1 SupportCategory (`catalog/models.py`)

Agrupa artigos da FAQ e tickets por assunto (ex: "Cadastro", "Pagamento", "Disputa"):

```python
class SupportCategory(models.Model):
    name = models.CharField(max_length=80, unique=True)
    slug = models.SlugField(max_length=90, unique=True)
    icon = models.CharField(max_length=40, blank=True, default="", help_text="lucide-react icon name")
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "name"]
        verbose_name = "Categoria de suporte"
        verbose_name_plural = "Categorias de suporte"

    def __str__(self) -> str:
        return self.name
```

### 2.2 FAQArticle (`catalog/models.py`)

Artigo da central de ajuda:

```python
class FAQArticle(models.Model):
    category = models.ForeignKey(
        SupportCategory, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="articles",
    )
    question = models.CharField(max_length=300)
    slug = models.SlugField(max_length=320, unique=True)
    answer = models.TextField()
    is_published = models.BooleanField(default=False, db_index=True)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order", "question"]
        verbose_name = "Artigo de ajuda"
        verbose_name_plural = "Artigos de ajuda"

    def __str__(self) -> str:
        return self.question
```

### 2.3 SupportTicket (`catalog/models.py`)

Ticket de suporte aberto por um usuário — segue o mesmo padrão de
`ServiceOrder` (status workflow, timestamps, logs):

```python
class SupportTicket(models.Model):
    class Status(models.TextChoices):
        OPEN = "open", "Aberto"
        WAITING_USER = "waiting_user", "Aguardando usuário"
        WAITING_STAFF = "waiting_staff", "Aguardando equipe"
        RESOLVED = "resolved", "Resolvido"
        CLOSED = "closed", "Fechado"

    class Priority(models.TextChoices):
        LOW = "low", "Baixa"
        MEDIUM = "medium", "Média"
        HIGH = "high", "Alta"
        URGENT = "urgent", "Urgente"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="support_tickets",
    )
    category = models.ForeignKey(
        SupportCategory, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="tickets",
    )
    subject = models.CharField(max_length=200)
    description = models.TextField()
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.OPEN, db_index=True,
    )
    priority = models.CharField(
        max_length=10, choices=Priority.choices, default=Priority.MEDIUM,
    )
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name="assigned_tickets",
        verbose_name="Responsável",
    )
    attachment = models.FileField(
        upload_to="support/attachments/%Y/%m/%d/",
        null=True, blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    closed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-updated_at"]
        indexes = [
            models.Index(fields=["user", "status"]),
            models.Index(fields=["status", "priority"]),
        ]
        verbose_name = "Ticket de suporte"
        verbose_name_plural = "Tickets de suporte"

    def __str__(self) -> str:
        return f"[{self.get_status_display()}] {self.subject[:60]}"
```

### 2.4 SupportMessage (`catalog/models.py`)

Mensagem dentro de um ticket (usuário ou staff). Segue o padrão de
`ChatMessage` do agent:

```python
class SupportMessage(models.Model):
    ticket = models.ForeignKey(
        SupportTicket, on_delete=models.CASCADE, related_name="messages",
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
    )
    content = models.TextField()
    is_staff = models.BooleanField(default=False, db_index=True)
    attachment = models.FileField(
        upload_to="support/messages/%Y/%m/%d/",
        null=True, blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]
        verbose_name = "Mensagem de suporte"
        verbose_name_plural = "Mensagens de suporte"

    def __str__(self) -> str:
        return f"{self.author.first_name}: {self.content[:60]}..."
```

### 2.5 SupportTicketLog (`catalog/models.py`)

Histórico de alterações do ticket (auditoria) — mesmo padrão de
`ServiceStatusLog`:

```python
class SupportTicketLog(models.Model):
    ticket = models.ForeignKey(
        SupportTicket, on_delete=models.CASCADE, related_name="logs",
    )
    from_status = models.CharField(max_length=20, blank=True, default="")
    to_status = models.CharField(max_length=20)
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
    )
    note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]
        verbose_name = "Log de ticket"
        verbose_name_plural = "Logs de tickets"

    def __str__(self) -> str:
        return f"#{self.ticket_id} {self.from_status} → {self.to_status}"
```

### Observações sobre os modelos

- `SupportTicket.Status` define um workflow similar ao de `ServiceOrder`.
- `SupportTicket.Priority` permite que a equipe priorize tickets críticos.
- `SupportMessage.is_staff` distingue mensagens do usuário vs. da equipe.
- `assigned_to` permite designar um membro da equipe como responsável.
- Todos seguem as convenções existentes (verbose_name pt-BR, `Meta`, `__str__`).

---

## 4. Diagrama de Fluxo dos Tickets

```
                    ┌──────────┐
                    │   OPEN   │ ← Usuário abre ticket
                    └────┬─────┘
                         │
              ┌──────────┴──────────┐
              ▼                     ▼
    ┌──────────────┐      ┌──────────────┐
    │ WAITING_STAFF│      │ WAITING_USER │ ← Staff pediu mais info
    └──────┬───────┘      └──────┬───────┘
           │                     │
           └──────────┬──────────┘
                      ▼
              ┌──────────────┐
              │   RESOLVED   │ ← Staff marca como resolvido
              └──────┬───────┘
                     │
                     ▼
              ┌──────────────┐
              │    CLOSED    │ ← Usuário confirma ou sistema fecha
              └──────────────┘
```

Transições permitidas:

| De | Para | Quem |
|----|------|------|
| open | waiting_staff | Sistema (ao criar) |
| open | closed | Usuário (desistiu) |
| waiting_staff | waiting_user | Staff (respondeu) |
| waiting_staff | resolved | Staff |
| waiting_user | waiting_staff | Usuário (respondeu) |
| waiting_user | closed | Usuário |
| resolved | closed | Usuário ou sistema |
| resolved | waiting_staff | Usuário (não concordou) |
| closed | *(nenhum)* | Final |

---

## 5. Serializers

```python
# catalog/serializers.py

class SupportCategorySerializer(serializers.ModelSerializer):
    article_count = serializers.IntegerField(read_only=True, required=False)

    class Meta:
        model = SupportCategory
        fields = ["id", "slug", "name", "icon", "order", "article_count"]


class FAQArticleSerializer(serializers.ModelSerializer):
    category = SupportCategorySerializer(read_only=True)

    class Meta:
        model = FAQArticle
        fields = ["id", "category", "question", "slug", "answer", "order"]


class SupportMessageSerializer(serializers.ModelSerializer):
    author_name = serializers.SerializerMethodField()

    class Meta:
        model = SupportMessage
        fields = ["id", "author_name", "content", "is_staff", "attachment", "created_at"]
        read_only_fields = ["author", "is_staff"]

    def get_author_name(self, obj) -> str:
        return obj.author.first_name or obj.author.email


class SupportTicketLogSerializer(serializers.ModelSerializer):
    changed_by_name = serializers.SerializerMethodField()

    class Meta:
        model = SupportTicketLog
        fields = ["id", "from_status", "to_status", "changed_by_name", "note", "created_at"]

    def get_changed_by_name(self, obj) -> str:
        return obj.changed_by.first_name if obj.changed_by else "Sistema"


class SupportTicketSerializer(serializers.ModelSerializer):
    messages = SupportMessageSerializer(many=True, read_only=True)
    logs = SupportTicketLogSerializer(many=True, read_only=True)
    category = SupportCategorySerializer(read_only=True)
    category_slug = serializers.SlugRelatedField(
        source="category", slug_field="slug",
        queryset=SupportCategory.objects.all(),
        write_only=True, required=False,
    )
    can_transition = serializers.SerializerMethodField()
    user_name = serializers.SerializerMethodField()
    assigned_to_name = serializers.SerializerMethodField()

    class Meta:
        model = SupportTicket
        fields = [
            "id",
            "user_name",
            "category",
            "category_slug",
            "subject",
            "description",
            "status",
            "priority",
            "assigned_to",
            "assigned_to_name",
            "messages",
            "logs",
            "can_transition",
            "created_at",
            "updated_at",
            "resolved_at",
            "closed_at",
        ]
        read_only_fields = [
            "user", "status", "assigned_to",
            "created_at", "updated_at", "resolved_at", "closed_at",
        ]

    def get_user_name(self, obj) -> str:
        return obj.user.first_name or obj.user.email

    def get_assigned_to_name(self, obj) -> str | None:
        return obj.assigned_to.first_name if obj.assigned_to else None

    def get_can_transition(self, obj) -> list[str]:
        request = self.context.get("request")
        if not request:
            return []
        return SupportTicketViewSet._allowed_transitions(obj, request.user)
```

---

## 6. Views e ViewSets

**Todas as views exigem `IsAuthenticated`** — usuário não logado recebe 401.

### 6.1 FAQ / Categorias — autenticadas

```python
# catalog/views/api_views.py
from rest_framework.permissions import IsAuthenticated

class FAQArticleListView(ListAPIView):
    """Lista artigos publicados da FAQ (apenas para usuários logados)."""

    permission_classes = [IsAuthenticated]
    serializer_class = FAQArticleSerializer
    pagination_class = None

    def get_queryset(self):
        qs = FAQArticle.objects.filter(is_published=True).select_related("category")
        category = self.request.query_params.get("category")
        if category:
            qs = qs.filter(category__slug=category)
        search = self.request.query_params.get("search", "").strip()
        if search:
            qs = qs.filter(question__icontains=search)
        return qs


class SupportCategoryListView(ListAPIView):
    """Lista categorias de suporte com contagem de artigos (autenticado)."""

    permission_classes = [IsAuthenticated]
    serializer_class = SupportCategorySerializer
    pagination_class = None

    def get_queryset(self):
        return SupportCategory.objects.annotate(
            article_count=Count("articles", filter=Q(articles__is_published=True))
        ).order_by("order", "name")
```

### 6.2 SupportTicketViewSet

```python
class SupportTicketViewSet(ViewSet):
    permission_classes = [IsAuthenticated]

    def get_queryset(self, request):
        user = request.user
        if user.is_staff:
            return SupportTicket.objects.select_related("user", "category").all()
        return SupportTicket.objects.filter(user=user).select_related("category")

    def list(self, request):
        qs = self.get_queryset(request)

        status_filter = request.query_params.get("status")
        if status_filter:
            qs = qs.filter(status=status_filter)

        # Staff pode filtrar por usuário
        user_filter = request.query_params.get("user_id")
        if user_filter and request.user.is_staff:
            qs = qs.filter(user_id=user_filter)

        # Staff: ordenar por prioridade + data
        if request.user.is_staff:
            qs = qs.order_by("-priority", "-updated_at")
        else:
            qs = qs.order_by("-updated_at")

        page = max(1, int(request.query_params.get("page", 1)))
        page_size = min(50, max(1, int(request.query_params.get("page_size", 20))))
        total = qs.count()
        start = (page - 1) * page_size
        chunk = qs[start : start + page_size]

        data = SupportTicketSerializer(
            chunk, many=True, context={"request": request}
        ).data

        return Response({
            "count": total,
            "next": _page_url(request, page + 1) if start + page_size < total else None,
            "previous": _page_url(request, page - 1) if page > 1 else None,
            "results": data,
        })

    def create(self, request):
        serializer = SupportTicketSerializer(
            data=request.data, context={"request": request},
        )
        serializer.is_valid(raise_exception=True)

        ticket = SupportTicket.objects.create(
            user=request.user,
            category=serializer.validated_data.get("category"),
            subject=serializer.validated_data["subject"],
            description=serializer.validated_data.get("description", ""),
            status=SupportTicket.Status.OPEN,
        )

        SupportTicketLog.objects.create(
            ticket=ticket,
            from_status="",
            to_status=SupportTicket.Status.OPEN,
            changed_by=request.user,
            note="Ticket aberto pelo usuário.",
        )

        # Notifica staff (via sistema de notificações)
        _notify_staff_new_ticket(ticket)

        return Response(
            SupportTicketSerializer(ticket, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )

    def retrieve(self, request, pk=None):
        try:
            ticket = self.get_queryset(request).get(pk=pk)
        except SupportTicket.DoesNotExist:
            return Response(
                {"detail": "Ticket não encontrado."},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(
            SupportTicketSerializer(ticket, context={"request": request}).data
        )

    @action(detail=True, methods=["post"])
    def message(self, request, pk=None):
        """Adiciona uma mensagem ao ticket e atualiza o status."""
        try:
            ticket = self.get_queryset(request).get(pk=pk)
        except SupportTicket.DoesNotExist:
            return Response(
                {"detail": "Ticket não encontrado."},
                status=status.HTTP_404_NOT_FOUND,
            )

        content = request.data.get("content", "").strip()
        if not content:
            return Response(
                {"detail": "Conteúdo da mensagem é obrigatório."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        is_staff = request.user.is_staff
        msg = SupportMessage.objects.create(
            ticket=ticket,
            author=request.user,
            content=content,
            is_staff=is_staff,
        )

        # Transiciona status automaticamente conforme o remetente
        old_status = ticket.status
        new_status = None

        if is_staff:
            if ticket.status == SupportTicket.Status.OPEN:
                new_status = SupportTicket.Status.WAITING_USER
            elif ticket.status == SupportTicket.Status.WAITING_STAFF:
                new_status = SupportTicket.Status.WAITING_USER
        else:
            if ticket.status == SupportTicket.Status.WAITING_USER:
                new_status = SupportTicket.Status.WAITING_STAFF
            elif ticket.status in (SupportTicket.Status.RESOLVED,):
                new_status = SupportTicket.Status.WAITING_STAFF

        if new_status and new_status != old_status:
            ticket.status = new_status
            ticket.save(update_fields=["status"])
            SupportTicketLog.objects.create(
                ticket=ticket,
                from_status=old_status,
                to_status=new_status,
                changed_by=request.user,
                note="Status atualizado por nova mensagem.",
            )

        # Notifica o outro lado
        if is_staff:
            _notify_ticket_reply(ticket, "Sua solicitação de suporte foi respondida.")
        else:
            _notify_staff_new_message(ticket)

        return Response(
            SupportMessageSerializer(msg).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["post"])
    def transition(self, request, pk=None):
        try:
            ticket = self.get_queryset(request).get(pk=pk)
        except SupportTicket.DoesNotExist:
            return Response(
                {"detail": "Ticket não encontrado."},
                status=status.HTTP_404_NOT_FOUND,
            )

        new_status = request.data.get("status", "")
        note = request.data.get("note", "")

        allowed = self._allowed_transitions(ticket, request.user)
        if new_status not in allowed:
            return Response(
                {
                    "detail": f"Transição '{ticket.status}' → '{new_status}' não permitida. "
                    f"Transições possíveis: {', '.join(allowed) if allowed else 'nenhuma'}.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        old_status = ticket.status
        ticket.status = new_status

        timestamp_map = {
            SupportTicket.Status.RESOLVED: "resolved_at",
            SupportTicket.Status.CLOSED: "closed_at",
        }
        if new_status in timestamp_map:
            setattr(ticket, timestamp_map[new_status], timezone.now())
        ticket.save()

        SupportTicketLog.objects.create(
            ticket=ticket,
            from_status=old_status,
            to_status=new_status,
            changed_by=request.user,
            note=note,
        )

        return Response(
            SupportTicketSerializer(ticket, context={"request": request}).data
        )

    @action(detail=True, methods=["post"])
    def assign(self, request, pk=None):
        """Staff designa um responsável pelo ticket."""
        if not request.user.is_staff:
            return Response(status=status.HTTP_403_FORBIDDEN)

        try:
            ticket = self.get_queryset(request).get(pk=pk)
        except SupportTicket.DoesNotExist:
            return Response(
                {"detail": "Ticket não encontrado."},
                status=status.HTTP_404_NOT_FOUND,
            )

        user_id = request.data.get("user_id")
        try:
            user = get_user_model().objects.get(pk=user_id, is_staff=True)
        except get_user_model().DoesNotExist:
            return Response(
                {"detail": "Membro da equipe não encontrado."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        ticket.assigned_to = user
        ticket.save(update_fields=["assigned_to"])

        SupportTicketLog.objects.create(
            ticket=ticket,
            from_status=ticket.status,
            to_status=ticket.status,
            changed_by=request.user,
            note=f"Ticket designado para {user.first_name or user.email}.",
        )

        return Response(
            SupportTicketSerializer(ticket, context={"request": request}).data
        )

    @action(detail=False, methods=["get"])
    def counts(self, request):
        """Contagem de tickets agrupados por status."""
        qs = self.get_queryset(request)
        counts = qs.values("status").annotate(count=Count("id")).order_by("status")
        return Response({item["status"]: item["count"] for item in counts})

    # ── Máquina de estados ─────────────────────────────────────────

    @staticmethod
    def _allowed_transitions(ticket, user):
        is_owner = ticket.user == user
        is_staff = user.is_staff

        transitions = {
            SupportTicket.Status.OPEN: [
                SupportTicket.Status.WAITING_STAFF,
                SupportTicket.Status.CLOSED,
            ],
            SupportTicket.Status.WAITING_USER: [
                SupportTicket.Status.RESOLVED,
            ],
            SupportTicket.Status.WAITING_STAFF: [
                SupportTicket.Status.WAITING_USER,
                SupportTicket.Status.CLOSED,
            ],
            SupportTicket.Status.RESOLVED: [
                SupportTicket.Status.CLOSED,
                SupportTicket.Status.WAITING_STAFF,
            ],
            SupportTicket.Status.CLOSED: [],
        }

        allowed = list(transitions.get(ticket.status, []))

        # Restrições por papel
        if not is_staff:
            if ticket.status == SupportTicket.Status.OPEN:
                return [s for s in allowed if s == SupportTicket.Status.CLOSED]
            if ticket.status == SupportTicket.Status.WAITING_STAFF:
                return [s for s in allowed if s == SupportTicket.Status.CLOSED]
            if ticket.status == SupportTicket.Status.RESOLVED:
                return [
                    s for s in allowed
                    if s in (SupportTicket.Status.CLOSED, SupportTicket.Status.WAITING_STAFF)
                ]
            return []

        return allowed
```

### 6.3 Helpers de notificação

```python
# catalog/views/api_views.py

def _notify_staff_new_ticket(ticket):
    """Notifica toda a equipe staff sobre um novo ticket."""
    from catalog.services import notify_user
    from django.contrib.auth import get_user_model

    staff = get_user_model().objects.filter(is_staff=True, is_active=True)
    for member in staff:
        if member == ticket.user:
            continue
        notify_user(
            recipient=member,
            tipo="new_ticket",
            title="Novo ticket de suporte",
            body=f"{ticket.user.first_name}: {ticket.subject[:80]}",
            link=f"/admin/suporte/tickets/{ticket.id}",
            payload={"ticket_id": ticket.id, "user_id": ticket.user_id},
        )


def _notify_staff_new_message(ticket):
    """Notifica o responsável (ou toda staff) sobre nova mensagem do usuário."""
    from catalog.services import notify_user

    if ticket.assigned_to:
        recipients = [ticket.assigned_to]
    else:
        recipients = get_user_model().objects.filter(is_staff=True, is_active=True)

    for member in recipients:
        if member == ticket.user:
            continue
        notify_user(
            recipient=member,
            tipo="ticket_message",
            title=f"Resposta em: {ticket.subject[:60]}",
            body=ticket.messages.last().content[:120] if ticket.messages.exists() else "",
            link=f"/admin/suporte/tickets/{ticket.id}",
            payload={"ticket_id": ticket.id},
        )


def _notify_ticket_reply(ticket, title):
    """Notifica o usuário dono do ticket sobre uma resposta da equipe."""
    from catalog.services import notify_user

    notify_user(
        recipient=ticket.user,
        tipo="ticket_reply",
        title=title,
        body=ticket.messages.last().content[:120] if ticket.messages.exists() else "",
        link=f"/suporte/tickets/{ticket.id}",
        payload={"ticket_id": ticket.id},
        via_whatsapp=True,
    )
```

### 6.4 Registro de rotas

Em `catalog/urls.py`:

```python
router.register(r"support/tickets", SupportTicketViewSet, basename="support-ticket")

# Rotas avulsas (fora do router)
urlpatterns += [
    path("api/faq/", FAQArticleListView.as_view(), name="faq"),
    path("api/faq/categories/", SupportCategoryListView.as_view(), name="faq-categories"),
]
```

### 6.5 Endpoints gerados

| Método | URL | Requer auth | Descrição |
|--------|-----|-------------|-----------|
| GET | `/api/faq/` | Sim | Artigos publicados (`?category=&search=`) |
| GET | `/api/faq/categories/` | Sim | Categorias da FAQ |
| GET | `/api/support/tickets/` | Sim | Listar tickets (staff vê todos) |
| POST | `/api/support/tickets/` | Sim | Abrir ticket |
| GET | `/api/support/tickets/{id}/` | Sim | Detalhe do ticket |
| POST | `/api/support/tickets/{id}/message/` | Sim | Enviar mensagem |
| POST | `/api/support/tickets/{id}/transition/` | Sim | Transicionar status |
| POST | `/api/support/tickets/{id}/assign/` | Sim (staff) | Designar responsável |
| GET | `/api/support/tickets/counts/` | Sim | Contagem por status |

---

## 7. Admin de Suporte (Django Admin)

### 7.1 Registro no admin (`catalog/admin.py`)

```python
from .models import SupportCategory, FAQArticle, SupportTicket, SupportMessage, SupportTicketLog


@admin.register(SupportCategory)
class SupportCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "icon", "order", "article_count")
    prepopulated_fields = {"slug": ("name",)}

    def article_count(self, obj):
        return obj.articles.count()
    article_count.short_description = "Artigos"


@admin.register(FAQArticle)
class FAQArticleAdmin(admin.ModelAdmin):
    list_display = ("question", "category", "is_published", "order")
    list_filter = ("category", "is_published")
    search_fields = ("question", "answer")
    prepopulated_fields = {"slug": ("question",)}


class SupportMessageInline(admin.TabularInline):
    model = SupportMessage
    fields = ("author", "content", "is_staff", "created_at")
    readonly_fields = ("author", "content", "is_staff", "created_at")
    can_delete = False
    extra = 0
    ordering = ("created_at",)
    max_num = 0  # read-only


class SupportTicketLogInline(admin.TabularInline):
    model = SupportTicketLog
    fields = ("from_status", "to_status", "changed_by", "note", "created_at")
    readonly_fields = fields
    can_delete = False
    extra = 0
    ordering = ("created_at",)
    max_num = 0


@admin.register(SupportTicket)
class SupportTicketAdmin(admin.ModelAdmin):
    list_display = (
        "id", "user", "subject_short", "category", "status",
        "priority", "assigned_to", "created_at",
    )
    list_filter = ("status", "priority", "category", "created_at")
    search_fields = ("subject", "description", "user__email", "user__first_name")
    inlines = [SupportMessageInline, SupportTicketLogInline]
    fields = (
        "user", "category", "subject", "description", "status",
        "priority", "assigned_to", "created_at", "updated_at",
        "resolved_at", "closed_at",
    )
    readonly_fields = ("user", "created_at", "updated_at", "resolved_at", "closed_at")
    list_select_related = ("user", "category", "assigned_to")
    date_hierarchy = "created_at"

    def subject_short(self, obj):
        return obj.subject[:80]
    subject_short.short_description = "Assunto"

    actions = ["assign_to_me", "mark_resolved", "mark_closed"]

    def assign_to_me(self, request, queryset):
        updated = queryset.update(assigned_to=request.user)
        self.message_user(request, f"{updated} ticket(s) designados a você.")
    assign_to_me.short_description = "Designar para mim"

    def mark_resolved(self, request, queryset):
        now = timezone.now()
        for ticket in queryset:
            old = ticket.status
            ticket.status = SupportTicket.Status.RESOLVED
            ticket.resolved_at = now
            ticket.save(update_fields=["status", "resolved_at"])
            SupportTicketLog.objects.create(
                ticket=ticket,
                from_status=old,
                to_status=SupportTicket.Status.RESOLVED,
                changed_by=request.user,
            )
        self.message_user(request, f"{queryset.count()} ticket(s) marcados como resolvidos.")
    mark_resolved.short_description = "Marcar como resolvido"

    def mark_closed(self, request, queryset):
        now = timezone.now()
        for ticket in queryset:
            old = ticket.status
            ticket.status = SupportTicket.Status.CLOSED
            ticket.closed_at = now
            ticket.save(update_fields=["status", "closed_at"])
            SupportTicketLog.objects.create(
                ticket=ticket,
                from_status=old,
                to_status=SupportTicket.Status.CLOSED,
                changed_by=request.user,
            )
        self.message_user(request, f"{queryset.count()} ticket(s) fechados.")
    mark_closed.short_description = "Fechar tickets"
```

### 7.2 Dashboard de Suporte (Admin)

Adicionar uma view no admin com métricas de tickets:

```python
@admin.register(SupportTicket)
class SupportTicketAdmin(admin.ModelAdmin):
    # ... (código acima)

    def changelist_view(self, request, extra_context=None):
        """Adiciona métricas ao topo da listagem."""
        from django.db.models import Count

        extra = extra_context or {}
        base = SupportTicket.objects.all()

        extra["ticket_metrics"] = {
            "total": base.count(),
            "open": base.filter(status=SupportTicket.Status.OPEN).count(),
            "waiting_user": base.filter(status=SupportTicket.Status.WAITING_USER).count(),
            "waiting_staff": base.filter(status=SupportTicket.Status.WAITING_STAFF).count(),
            "unassigned": base.filter(assigned_to__isnull=True)
                .exclude(status__in=[SupportTicket.Status.RESOLVED, SupportTicket.Status.CLOSED])
                .count(),
            "high_priority": base.filter(
                priority__in=[SupportTicket.Priority.HIGH, SupportTicket.Priority.URGENT],
            ).exclude(
                status__in=[SupportTicket.Status.RESOLVED, SupportTicket.Status.CLOSED],
            ).count(),
        }

        return super().changelist_view(request, extra_context=extra)
```

E no template `admin/catalog/supportticket/change_list.html`:

```html
{% extends "admin/change_list.html" %}
{% block content_title %}
  <div class="support-metrics" style="display:flex;gap:1.5rem;margin-bottom:1rem;flex-wrap:wrap;">
    <div style="padding:0.75rem 1.25rem;background:#1a1a2e;border-radius:12px;border:1px solid rgba(255,255,255,0.1);">
      <strong>📊 Tickets</strong>
    </div>
    <div style="padding:0.75rem 1.25rem;background:#1a1a2e;border-radius:12px;">
      <span style="color:#facc15;">{{ ticket_metrics.open }}</span> Abertos
    </div>
    <div style="padding:0.75rem 1.25rem;background:#1a1a2e;border-radius:12px;">
      <span style="color:#60a5fa;">{{ ticket_metrics.waiting_user }}</span> Aguardando usuário
    </div>
    <div style="padding:0.75rem 1.25rem;background:#1a1a2e;border-radius:12px;">
      <span style="color:#f97316;">{{ ticket_metrics.high_priority }}</span> Alta prioridade
    </div>
    <div style="padding:0.75rem 1.25rem;background:#1a1a2e;border-radius:12px;">
      <span style="color:#a78bfa;">{{ ticket_metrics.unassigned }}</span> Não designados
    </div>
  </div>
  {{ block.super }}
{% endblock %}
```

---

## 8. Frontend — Types

```typescript
export type SupportTicketStatus =
  | "open"
  | "waiting_user"
  | "waiting_staff"
  | "resolved"
  | "closed";

export type SupportTicketPriority =
  | "low"
  | "medium"
  | "high"
  | "urgent";

export interface SupportCategory {
  id: number;
  slug: string;
  name: string;
  icon: string;
  order: number;
  article_count?: number;
}

export interface FAQArticle {
  id: number;
  category: SupportCategory | null;
  question: string;
  slug: string;
  answer: string;
  order: number;
}

export interface SupportMessage {
  id: number;
  author_name: string;
  content: string;
  is_staff: boolean;
  attachment: string | null;
  created_at: string;
}

export interface SupportTicketLog {
  id: number;
  from_status: string;
  to_status: string;
  changed_by_name: string;
  note: string;
  created_at: string;
}

export interface SupportTicket {
  id: number;
  user_name: string;
  category: SupportCategory | null;
  subject: string;
  description: string;
  status: SupportTicketStatus;
  priority: SupportTicketPriority;
  assigned_to: number | null;
  assigned_to_name: string | null;
  messages: SupportMessage[];
  logs: SupportTicketLog[];
  can_transition: string[];
  created_at: string;
  updated_at: string;
  resolved_at: string | null;
  closed_at: string | null;
}
```

---

## 9. Frontend — API Client

```typescript
// api.ts

faq: (params?: { category?: string; search?: string }) =>
  request<FAQArticle[]>("/faq/", { params }),
faqCategories: () =>
  request<SupportCategory[]>("/faq/categories/"),

supportTickets: (params?: { status?: string; page?: number }) =>
  request<Paginated<SupportTicket>>("/support/tickets/", { params }),
supportTicket: (id: number) =>
  request<SupportTicket>(`/support/tickets/${id}/`),
createSupportTicket: (body: { subject: string; description: string; category_slug?: string }) =>
  request<SupportTicket>("/support/tickets/", { method: "POST", body }),
sendTicketMessage: (id: number, content: string) =>
  request<SupportMessage>(`/support/tickets/${id}/message/`, { method: "POST", body: { content } }),
transitionTicket: (id: number, status: string, note?: string) =>
  request<SupportTicket>(`/support/tickets/${id}/transition/`, { method: "POST", body: { status, note } }),
assignTicket: (id: number, userId: number) =>
  request<SupportTicket>(`/support/tickets/${id}/assign/`, { method: "POST", body: { user_id: userId } }),
ticketCounts: () =>
  request<Record<string, number>>("/support/tickets/counts/"),
```

---

## 10. Frontend — Páginas e Componentes

**Todas as páginas de suporte exigem autenticação.** Seguir o mesmo padrão
de `MinhaConta.tsx`: se `user` for `null`, redirecionar para `/entrar` ou
exibir tela de "Faça login para acessar o suporte".

### 10.1 Página `Ajuda.tsx` (`/ajuda`)

Redireciona para `/entrar` se não logado.
Central de Ajuda com FAQ:

- Categorias em grid (ícone + nome + contagem)
- Ao clicar: filtra artigos da categoria
- Campo de busca textual
- Lista de artigos expansíveis (accordion) ou links para páginas individuais
- Links para "Abrir ticket" e "Falar no chat"

### 10.2 Página `ArtigoAjuda.tsx` (`/ajuda/:slug`)

Redireciona para `/entrar` se não logado.
Artigo individual da FAQ:

- Breadcrumb: Ajuda > Categoria > Artigo
- Conteúdo formatado (rich text / markdown)
- Botões: "Isso resolveu?" (feedback), "Abrir ticket", "Falar no chat"

### 10.3 Página `MeusTickets.tsx` (`/suporte/tickets`)

Redireciona para `/entrar` se não logado.
Lista de tickets do usuário logado:

- Abas por status (Abertos, Aguardando, Resolvidos)
- Cada ticket: assunto, status badge, data, última mensagem
- Botão "Novo ticket"
- Ao clicar: vai para detalhe do ticket

### 10.4 Página `DetalheTicket.tsx` (`/suporte/tickets/:id`)

Redireciona para `/entrar` se não logado.
Detalhe completo do ticket:

- Cabeçalho: assunto, status, prioridade, categoria
- Linha do tempo de mensagens (chat-style, igual ao ChatWidget)
  - Mensagens do staff destacadas com badge "Equipe HIVEE"
  - Mensagens do usuário à direita
- Formulário para responder (textarea + enviar)
- Botões de transição de acordo com `can_transition`
- Link "Voltar para meus tickets"

### 10.5 Página `NovoTicket.tsx` (`/suporte/novo`)

Redireciona para `/entrar` se não logado.
Formulário para abrir ticket:

- Categoria (select, carregado da API)
- Assunto
- Descrição (textarea)
- Botão "Enviar"
- Após criar: redireciona para `/suporte/tickets/{id}`

### 10.6 Componente `TicketStatusBadge.tsx`

Badge reutilizável:

| Status | Cor |
|--------|-----|
| open | Azul |
| waiting_user | Âmbar |
| waiting_staff | Laranja |
| resolved | Verde |
| closed | Cinza |

---

## 11. Frontend — Rotas

Todas protegidas — usuário não autenticado redirecionado para `/entrar`.

```tsx
import Ajuda from "@/pages/Ajuda";
import ArtigoAjuda from "@/pages/ArtigoAjuda";
import MeusTickets from "@/pages/MeusTickets";
import DetalheTicket from "@/pages/DetalheTicket";
import NovoTicket from "@/pages/NovoTicket";

// Dentro de <Route element={<Layout />}>
<Route path="/ajuda" element={<Ajuda />} />
<Route path="/ajuda/:slug" element={<ArtigoAjuda />} />
<Route path="/suporte/tickets" element={<MeusTickets />} />
<Route path="/suporte/tickets/:id" element={<DetalheTicket />} />
<Route path="/suporte/novo" element={<NovoTicket />} />
```

---

## 12. Integração com o Chat IA

O Chat IA só pode criar tickets se o usuário estiver autenticado no site.
Usuários do WhatsApp sem cadastro recebem mensagem orientando a criar uma
conta primeiro.

## 13. Navegação — Links visíveis apenas para logados

Os links de suporte no Footer e Navbar **só aparecem para usuários autenticados**,
seguindo o mesmo padrão dos links condicionais já existentes no `Navbar.tsx`
(bloco `{user ? (...)}`).

O Chat IA existente (`agent`) pode escalonar para suporte humano quando:

1. **Usuário pedir explicitamente**: "Quero falar com um humano", "Atendente"
2. **IA não conseguir resolver**: detector de intenção no `core.py` que cria
   um `SupportTicket` automaticamente
3. **Palavras-chave**: "reclamação", "problema", "erro", "suporte"

No `agent/core.py`, adicionar:

```python
_INTENCAO_SUPORTE = {"humano", "atendente", "suporte", "reclamação", "problema", "ajuda"}


def _detecta_intencao_suporte(mensagem: str) -> bool:
    msg = mensagem.lower().strip()
    return any(palavra in msg for palavra in _INTENCAO_SUPORTE)
```

Se detectado, ao invés de chamar a OpenAI, o agente:

1. Cria um `SupportTicket` com `category=None`, status `open`
2. Responde: "Vou abrir um ticket de suporte para você. Em breve nossa equipe responde."
3. Notifica a staff

---

---

## 14. Checklist de Implementação

### Backend — Modelos
- [ ] Criar `SupportCategory`, `FAQArticle`, `SupportTicket`, `SupportMessage`, `SupportTicketLog` em `catalog/models.py`
- [ ] Executar `makemigrations` e `migrate`

### Backend — Serializers
- [ ] Criar `SupportCategorySerializer`, `FAQArticleSerializer`
- [ ] Criar `SupportMessageSerializer`, `SupportTicketLogSerializer`, `SupportTicketSerializer`

### Backend — Views
- [ ] Criar `FAQArticleListView`, `SupportCategoryListView`
- [ ] Criar `SupportTicketViewSet` com ações: `message`, `transition`, `assign`, `counts`
- [ ] Implementar helpers de notificação (`_notify_staff_new_ticket`, `_notify_ticket_reply`, etc.)

### Backend — Rotas
- [ ] Registrar `SupportTicketViewSet` no `DefaultRouter`
- [ ] Adicionar rotas avulsas `/api/faq/`, `/api/faq/categories/`

### Backend — Admin
- [ ] Registrar `SupportCategoryAdmin`, `FAQArticleAdmin`
- [ ] Registrar `SupportTicketAdmin` com inlines, actions, dashboard metrics

### Backend — Chat IA (escalonamento)
- [ ] Adicionar detecção de intenção de suporte em `agent/core.py`

### Frontend — FAQ
- [ ] Adicionar tipos no `types.ts`
- [ ] Adicionar métodos `faq()`, `faqCategories()` no `api.ts`
- [ ] Criar página `Ajuda.tsx`
- [ ] Criar página `ArtigoAjuda.tsx`

### Frontend — Tickets
- [ ] Adicionar métodos `supportTickets()`, `createSupportTicket()`, etc. no `api.ts`
- [ ] Criar página `MeusTickets.tsx`
- [ ] Criar página `DetalheTicket.tsx`
- [ ] Criar página `NovoTicket.tsx`
- [ ] Criar componente `TicketStatusBadge.tsx`

### Frontend — Navegação
- [ ] Adicionar rotas em `main.tsx`
- [ ] Adicionar link "Ajuda" no `Footer.tsx`
- [ ] Adicionar link "Meus tickets" na `Navbar.tsx`
