# Sistema de Rastreio de Serviços em Andamento

## 1. Contexto

Atualmente a HIVEE permite que clientes encontrem prestadores, favoritem perfis e iniciem
conversas pelo chat, mas **não existe um fluxo formal de contratação**. O cliente não tem
como:

- Solicitar formalmente um serviço
- Acompanhar o status de serviços contratados
- O prestador não tem como aceitar/recusar, marcar como em andamento ou concluir
- Avaliar o prestador após a conclusão

Este documento propõe a implementação completa de um **sistema de rastreio de serviços em
andamento**, seguindo os padrões existentes do projeto (DRF ViewSet, React Router, cookies
httpOnly, Tailwind glassmorphism, etc.).

---

## 2. Modelos de Dados (Backend — `catalog/models.py`)

Adicionar ao final do arquivo, antes de `Cliente` ou após `ProviderSwipe`:

```python
class ServiceOrder(models.Model):
    STATUS_CHOICES = [
        ("pending",       "Aguardando confirmação"),
        ("confirmed",     "Confirmado pelo profissional"),
        ("in_progress",   "Em andamento"),
        ("completed",     "Concluído"),
        ("cancelled",     "Cancelado"),
        ("disputed",      "Em disputa"),
    ]

    client = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="service_orders_as_client",
    )
    provider = models.ForeignKey(
        Provider,
        on_delete=models.CASCADE,
        related_name="service_orders",
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")

    # Descrição do serviço contratado
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)

    # Valores
    estimated_hours = models.DecimalField(max_digits=6, decimal_places=1, null=True, blank=True)
    total_value = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    # Endereço da prestação
    address_city = models.CharField(max_length=80, blank=True, default="")
    address_neighborhood = models.CharField(max_length=80, blank=True, default="")
    address_street = models.CharField(max_length=200, blank=True, default="")
    address_number = models.CharField(max_length=20, blank=True, default="")

    # Agendamento
    scheduled_date = models.DateField(null=True, blank=True)
    scheduled_time = models.TimeField(null=True, blank=True)

    # Timestamps
    requested_at = models.DateTimeField(auto_now_add=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-requested_at"]
        verbose_name = "Ordem de serviço"
        verbose_name_plural = "Ordens de serviço"

    def __str__(self) -> str:
        return f"{self.client.first_name} → {self.provider.name} ({self.get_status_display()})"


class ServiceStatusLog(models.Model):
    """Histórico de alterações de status de uma ordem de serviço."""

    order = models.ForeignKey(
        ServiceOrder, on_delete=models.CASCADE, related_name="status_logs"
    )
    from_status = models.CharField(max_length=20, blank=True, default="")
    to_status = models.CharField(max_length=20)
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]
        verbose_name = "Log de status"
        verbose_name_plural = "Logs de status"

    def __str__(self) -> str:
        return f"{self.order} → {self.to_status}"


class ServiceReview(models.Model):
    """Avaliação do cliente sobre o prestador após a conclusão."""

    order = models.OneToOneField(
        ServiceOrder, on_delete=models.CASCADE, related_name="review"
    )
    rating = models.PositiveIntegerField()  # 1-5
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Avaliação de serviço"
        verbose_name_plural = "Avaliações de serviços"

    def __str__(self) -> str:
        return f"{self.order} — {self.rating}/5"
```

### Observações sobre o modelo

- `ServiceOrder` é o núcleo: liga `User` (cliente) a `Provider`, com ciclo de vida
  completo de status, valores e agendamento.
- `ServiceStatusLog` preserva o histórico de cada transição de status (auditoria).
- `ServiceReview` vincula avaliação 1:1 à ordem concluída, evitando avaliações órfãs.
- Segue as mesmas convenções dos modelos existentes (verbose_name em pt-BR, Meta
  ordering, related_names).

---

## 3. Serializers (Backend — `catalog/serializers.py`)

Adicionar antes de `ProviderUpdateSerializer` ou após os serializers existentes:

```python
class ServiceStatusLogSerializer(serializers.ModelSerializer):
    changed_by_name = serializers.SerializerMethodField()

    class Meta:
        model = ServiceStatusLog
        fields = ["id", "from_status", "to_status", "changed_by_name", "note", "created_at"]

    def get_changed_by_name(self, obj) -> str:
        return obj.changed_by.first_name if obj.changed_by else "Sistema"


class ServiceReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceReview
        fields = ["id", "rating", "comment", "created_at"]


class ServiceOrderSerializer(serializers.ModelSerializer):
    provider = ProviderSerializer(read_only=True)
    provider_slug = serializers.SlugRelatedField(
        source="provider",
        slug_field="slug",
        queryset=Provider.objects.all(),
        write_only=True,
    )
    status_logs = ServiceStatusLogSerializer(many=True, read_only=True)
    review = ServiceReviewSerializer(read_only=True)
    client_name = serializers.SerializerMethodField()
    can_transition = serializers.SerializerMethodField()

    class Meta:
        model = ServiceOrder
        fields = [
            "id",
            "provider",
            "provider_slug",
            "client_name",
            "status",
            "title",
            "description",
            "estimated_hours",
            "total_value",
            "address_city",
            "address_neighborhood",
            "address_street",
            "address_number",
            "scheduled_date",
            "scheduled_time",
            "requested_at",
            "confirmed_at",
            "started_at",
            "completed_at",
            "cancelled_at",
            "updated_at",
            "status_logs",
            "review",
            "can_transition",
        ]
        read_only_fields = [
            "client",
            "status",
            "requested_at",
            "confirmed_at",
            "started_at",
            "completed_at",
            "cancelled_at",
            "updated_at",
            "status_logs",
            "review",
        ]

    def get_client_name(self, obj) -> str:
        return obj.client.first_name or obj.client.email

    def get_can_transition(self, obj) -> list[str]:
        """Retorna os próximos status permitidos para o usuário atual."""
        request = self.context.get("request")
        if not request:
            return []
        user = request.user
        return ServiceOrderViewSet._allowed_transitions(obj, user)
```

---

## 4. Views / ViewSet (Backend — `catalog/views/api_views.py`)

Adicionar ao final do arquivo, antes ou depois de `AvatarUploadView`:

```python
class ServiceOrderViewSet(ViewSet):
    permission_classes = [IsAuthenticated]

    def get_queryset(self, request):
        user = request.user
        if user.is_staff:
            return ServiceOrder.objects.select_related("provider", "client").all()
        return ServiceOrder.objects.select_related("provider", "client").filter(
            models.Q(client=user) | models.Q(provider__owner=user)
        )

    def list(self, request):
        qs = self.get_queryset(request)
        # Filtro opcional por status
        status_filter = request.query_params.get("status")
        if status_filter:
            qs = qs.filter(status=status_filter)
        # Filtro opcional: só do usuário como cliente ou como prestador
        role = request.query_params.get("role")
        if role == "client":
            qs = qs.filter(client=request.user)
        elif role == "provider":
            qs = qs.filter(provider__owner=request.user)
        serializer = ServiceOrderSerializer(qs, many=True, context={"request": request})
        return Response(serializer.data)

    def create(self, request):
        serializer = ServiceOrderSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        provider = serializer.validated_data["provider"]

        # Verifica se o provider existe e está aprovado
        if provider.status != "approved":
            return Response(
                {"detail": "Este profissional não está disponível no momento."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Verifica se o cliente não é o próprio prestador
        if provider.owner == request.user:
            return Response(
                {"detail": "Você não pode contratar a si mesmo."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        order = ServiceOrder.objects.create(
            client=request.user,
            provider=provider,
            title=serializer.validated_data.get("title"),
            description=serializer.validated_data.get("description", ""),
            estimated_hours=serializer.validated_data.get("estimated_hours"),
            total_value=serializer.validated_data.get("total_value"),
            address_city=serializer.validated_data.get("address_city", ""),
            address_neighborhood=serializer.validated_data.get("address_neighborhood", ""),
            address_street=serializer.validated_data.get("address_street", ""),
            address_number=serializer.validated_data.get("address_number", ""),
            scheduled_date=serializer.validated_data.get("scheduled_date"),
            scheduled_time=serializer.validated_data.get("scheduled_time"),
            status="pending",
        )
        ServiceStatusLog.objects.create(
            order=order,
            from_status="",
            to_status="pending",
            changed_by=request.user,
            note="Solicitação de serviço enviada.",
        )

        return Response(
            ServiceOrderSerializer(order, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )

    def retrieve(self, request, pk=None):
        try:
            order = self.get_queryset(request).get(pk=pk)
        except ServiceOrder.DoesNotExist:
            return Response({"detail": "Ordem não encontrada."}, status=status.HTTP_404_NOT_FOUND)
        return Response(ServiceOrderSerializer(order, context={"request": request}).data)

    @action(detail=True, methods=["post"])
    def transition(self, request, pk=None):
        """Transiciona o status da ordem para o próximo estado permitido."""
        try:
            order = self.get_queryset(request).get(pk=pk)
        except ServiceOrder.DoesNotExist:
            return Response({"detail": "Ordem não encontrada."}, status=status.HTTP_404_NOT_FOUND)

        new_status = request.data.get("status", "")
        note = request.data.get("note", "")

        allowed = self._allowed_transitions(order, request.user)
        if new_status not in allowed:
            return Response(
                {
                    "detail": f"Transição de '{order.status}' para '{new_status}' não permitida. "
                    f"Transições possíveis: {', '.join(allowed) if allowed else 'nenhuma'}."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        old_status = order.status
        order.status = new_status

        # Timestamps automáticos
        now = timezone.now()
        timestamp_map = {
            "confirmed": "confirmed_at",
            "in_progress": "started_at",
            "completed": "completed_at",
            "cancelled": "cancelled_at",
        }
        if new_status in timestamp_map:
            setattr(order, timestamp_map[new_status], now)
        order.save()

        ServiceStatusLog.objects.create(
            order=order,
            from_status=old_status,
            to_status=new_status,
            changed_by=request.user,
            note=note,
        )

        return Response(
            ServiceOrderSerializer(order, context={"request": request}).data
        )

    @action(detail=True, methods=["post"])
    def review(self, request, pk=None):
        """Cliente avalia o prestador após conclusão."""
        try:
            order = self.get_queryset(request).get(pk=pk)
        except ServiceOrder.DoesNotExist:
            return Response({"detail": "Ordem não encontrada."}, status=status.HTTP_404_NOT_FOUND)

        if order.status != "completed":
            return Response(
                {"detail": "Só é possível avaliar serviços concluídos."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if order.client != request.user:
            return Response(
                {"detail": "Só o cliente pode avaliar o serviço."},
                status=status.HTTP_403_FORBIDDEN,
            )
        if hasattr(order, "review"):
            return Response(
                {"detail": "Este serviço já foi avaliado."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        rating = request.data.get("rating")
        comment = request.data.get("comment", "")
        try:
            rating = int(rating)
        except (TypeError, ValueError):
            return Response({"detail": "rating deve ser um número inteiro."}, status=status.HTTP_400_BAD_REQUEST)
        if rating < 1 or rating > 5:
            return Response({"detail": "rating deve estar entre 1 e 5."}, status=status.HTTP_400_BAD_REQUEST)

        review = ServiceReview.objects.create(order=order, rating=rating, comment=comment)

        # Atualiza a média do prestador
        provider = order.provider
        agg = ServiceReview.objects.filter(order__provider=provider).aggregate(
            avg=Avg("rating"), count=Count("id")
        )
        provider.rating = round(agg["avg"] or 0, 2)
        provider.reviews_count = agg["count"] or 0
        provider.save(update_fields=["rating", "reviews_count"])

        return Response(ServiceReviewSerializer(review).data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["get"])
    def counts(self, request):
        """Retorna contagem de ordens agrupadas por status — útil para badges."""
        user = request.user
        qs = self.get_queryset(request)
        counts = qs.values("status").annotate(count=Count("id")).order_by("status")
        return Response({item["status"]: item["count"] for item in counts})

    @staticmethod
    def _allowed_transitions(order, user):
        """Define a máquina de estados: quem pode fazer o quê."""
        is_client = order.client == user
        is_provider_owner = order.provider.owner == user
        is_staff = user.is_staff

        transitions = {
            "pending":     ["confirmed", "cancelled"],       # provider confirma ou cliente cancela
            "confirmed":   ["in_progress", "cancelled"],     # provider inicia ou cliente cancela
            "in_progress": ["completed", "disputed"],        # provider conclui ou cliente abre disputa
            "completed":   [],                               # finalizado
            "cancelled":   [],                               # finalizado
            "disputed":    ["completed", "cancelled"],       # staff resolve
        }

        allowed = list(transitions.get(order.status, []))

        # Aplica regras de papel
        if not is_staff:
            if order.status == "pending":
                # pending: provider confirma, cliente cancela
                if is_provider_owner:
                    return [s for s in allowed if s == "confirmed"]
                elif is_client:
                    return [s for s in allowed if s == "cancelled"]
                else:
                    return []
            elif order.status == "confirmed":
                # confirmed: provider inicia, cliente cancela
                if is_provider_owner:
                    return [s for s in allowed if s == "in_progress"]
                elif is_client:
                    return [s for s in allowed if s == "cancelled"]
                else:
                    return []
            elif order.status == "in_progress":
                # in_progress: provider conclui, cliente abre disputa
                if is_provider_owner:
                    return [s for s in allowed if s == "completed"]
                elif is_client:
                    return [s for s in allowed if s == "disputed"]
                else:
                    return []
            elif order.status == "disputed" and not is_staff:
                return []

        # Staff pode fazer qualquer transição permitida (inclusive resolver disputas)
        return allowed
```

### Registro de Rotas (Backend — `catalog/urls.py`)

Adicionar no `DefaultRouter`:

```python
router.register(r"orders", ServiceOrderViewSet, basename="order")
```

Isso gera automaticamente:

| Método | URL | Ação |
|--------|-----|------|
| GET | `/api/orders/` | Listar ordens (filtros: `?status=`, `?role=client\|provider`) |
| POST | `/api/orders/` | Criar nova solicitação |
| GET | `/api/orders/{id}/` | Detalhe da ordem |
| POST | `/api/orders/{id}/transition/` | Transicionar status |
| POST | `/api/orders/{id}/review/` | Avaliar (cliente, após conclusão) |
| GET | `/api/orders/counts/` | Contagem por status |

---

## 5. Frontend — Types (`frontend/src/types.ts`)

Adicionar:

```typescript
export type OrderStatus =
  | "pending"
  | "confirmed"
  | "in_progress"
  | "completed"
  | "cancelled"
  | "disputed";

export interface ServiceStatusLog {
  id: number;
  from_status: string;
  to_status: string;
  changed_by_name: string;
  note: string;
  created_at: string;
}

export interface ServiceReview {
  id: number;
  rating: number;
  comment: string;
  created_at: string;
}

export interface ServiceOrder {
  id: number;
  provider: Provider;
  client_name: string;
  status: OrderStatus;
  title: string;
  description: string;
  estimated_hours: number | null;
  total_value: number | null;
  address_city: string;
  address_neighborhood: string;
  address_street: string;
  address_number: string;
  scheduled_date: string | null;
  scheduled_time: string | null;
  requested_at: string;
  confirmed_at: string | null;
  started_at: string | null;
  completed_at: string | null;
  cancelled_at: string | null;
  updated_at: string;
  status_logs: ServiceStatusLog[];
  review: ServiceReview | null;
  can_transition: string[];
}

export interface OrderCounts {
  [status: string]: number;
}
```

---

## 6. Frontend — API Client (`frontend/src/lib/api.ts`)

Adicionar aos métodos do objeto `api`:

```typescript
export interface ServiceOrderInput {
  provider_slug: string;
  title: string;
  description?: string;
  estimated_hours?: number;
  total_value?: number;
  address_city?: string;
  address_neighborhood?: string;
  address_street?: string;
  address_number?: string;
  scheduled_date?: string;
  scheduled_time?: string;
}
```

```typescript
// Dentro do objeto `api`:
orders: (params?: { status?: string; role?: string }) =>
  request<ServiceOrder[]>("/orders/", { params }),
order: (id: number) =>
  request<ServiceOrder>(`/orders/${id}/`),
createOrder: (input: ServiceOrderInput) =>
  request<ServiceOrder>("/orders/", { method: "POST", body: input }),
transitionOrder: (id: number, status: string, note?: string) =>
  request<ServiceOrder>(`/orders/${id}/transition/`, { method: "POST", body: { status, note } }),
reviewOrder: (id: number, rating: number, comment?: string) =>
  request<ServiceReview>(`/orders/${id}/review/`, { method: "POST", body: { rating, comment } }),
orderCounts: () =>
  request<OrderCounts>("/orders/counts/"),
```

---

## 7. Frontend — Novas Páginas e Componentes

### 7.1 Página `MeusServicos.tsx` (`frontend/src/pages/MeusServicos.tsx`)

Lista todas as ordens do usuário logado, com abas para alternar entre
"Como Cliente" e "Como Prestador" (se for prestador). Cada card exibe:

- Nome do prestador/cliente
- Título do serviço
- Status com badge colorido
- Valor
- Datas
- Botão de ação de acordo com o status (confirmar, iniciar, concluir, avaliar)

**Rota**: `/meus-servicos`

### 7.2 Página `DetalheOrdem.tsx` (`frontend/src/pages/DetalheOrdem.tsx`)

Detalhes completos de uma ordem (`/meus-servicos/:id`):

- Informações do profissional (link para perfil)
- Linha do tempo de status (`ServiceStatusLog`)
- Informações de agendamento e endereço
- Card de ações (botões de transição conforme `can_transition`)
- Se concluído e sem review: formulário de avaliação
- Se já avaliado: exibir review

### 7.3 Componente `OrderStatusBadge.tsx` (`frontend/src/components/OrderStatusBadge.tsx`)

Badge reutilizável que exibe o status com cor e ícone:

| Status | Cor |
|--------|-----|
| pending | Amarelo |
| confirmed | Azul |
| in_progress | Ciano |
| completed | Verde |
| cancelled | Cinza |
| disputed | Vermelho |

### 7.4 Botão "Contratar" no perfil do prestador

No `ProviderProfile.tsx`, adicionar um botão que abra um modal ou navegue
para uma página de solicitação de serviço, passando o slug do provider como
parâmetro: `/contratar/:slug`.

### 7.5 Página `Contratar.tsx` (`frontend/src/pages/Contratar.tsx`)

Formulário para criar uma nova ordem:

- Título do serviço
- Descrição detalhada
- Horas estimadas
- Valor total (opcional)
- Endereço da prestação
- Data/hora agendada
- Botão "Solicitar"

Após criar, redireciona para o detalhe da ordem.

---

## 8. Frontend — Rotas (`frontend/src/main.tsx`)

Adicionar:

```tsx
import MeusServicos from "@/pages/MeusServicos";
import DetalheOrdem from "@/pages/DetalheOrdem";
import Contratar from "@/pages/Contratar";
```

Dentro do `<Route element={<Layout />}>`:

```tsx
<Route path="/meus-servicos" element={<MeusServicos />} />
<Route path="/meus-servicos/:id" element={<DetalheOrdem />} />
<Route path="/contratar/:slug" element={<Contratar />} />
```

### Atualizar Navbar

Em `Navbar.tsx`, adicionar link "Meus Serviços" ao array `LINKS` e/ou
como link condicional dentro da área logada.

---

## 9. Diagrama de Fluxo de Status

```
                    ┌──────────┐
                    │ PENDING  │ ← Solicitação criada pelo cliente
                    └────┬─────┘
                 ┌───────┴───────┐
                 ▼               ▼
          ┌──────────┐    ┌──────────┐
          │CONFIRMED │    │CANCELLED │ ← Cliente desiste
          └────┬─────┘    └──────────┘
               ▼
          ┌──────────┐
          │IN_PROGRES│ ← Prestador iniciou
          └────┬─────┘
           ┌───┴───┐
           ▼       ▼
     ┌────────┐ ┌────────┐
     │COMPLET │ │DISPUTED│ ← Cliente abriu disputa
     └───┬────┘ └───┬────┘
         │          ├────────────┐
         ▼          ▼            ▼
    (avaliação) ┌────────┐  ┌────────┐
                │COMPLET │  │CANCELL │ ← Staff resolve
                └───┬────┘  └────────┘
                    ▼
              (avaliação)
```

---

## 10. Regras de Transição (Máquina de Estados)

| Status Atual | Próximo | Quem Pode | Efeito |
|-------------|---------|-----------|--------|
| pending | confirmed | Prestador | `confirmed_at = now` |
| pending | cancelled | Cliente | `cancelled_at = now` |
| confirmed | in_progress | Prestador | `started_at = now` |
| confirmed | cancelled | Cliente | `cancelled_at = now` |
| in_progress | completed | Prestador | `completed_at = now` |
| in_progress | disputed | Cliente | — |
| disputed | completed | Staff | `completed_at = now` |
| disputed | cancelled | Staff | `cancelled_at = now` |

---

## 11. Numeração das Migrations

Criar migração no app `catalog`:

```bash
cd backend
python manage.py makemigrations catalog
```

Isso gerará uma migration (ex.: `catalog/0005_serviceorder_servicestatuslog_servicereview.py`).

---

## 12. Checklist de Implementação

### Backend
- [ ] Adicionar modelos `ServiceOrder`, `ServiceStatusLog`, `ServiceReview` em `catalog/models.py`
- [ ] Executar `makemigrations` e `migrate`
- [ ] Adicionar serializers em `catalog/serializers.py`
- [ ] Adicionar `ServiceOrderViewSet` em `catalog/views/api_views.py`
- [ ] Registrar rota no `DefaultRouter` em `catalog/urls.py`

### Frontend
- [ ] Adicionar tipos `ServiceOrder`, `ServiceOrderStatus`, `ServiceReview`, etc. em `types.ts`
- [ ] Adicionar métodos `orders()`, `createOrder()`, etc. em `api.ts`
- [ ] Criar componente `OrderStatusBadge.tsx`
- [ ] Criar página `MeusServicos.tsx`
- [ ] Criar página `DetalheOrdem.tsx`
- [ ] Criar página `Contratar.tsx`
- [ ] Adicionar rotas em `main.tsx`
- [ ] Adicionar link "Meus Serviços" na `Navbar.tsx`
- [ ] Adicionar botão "Contratar" no `ProviderProfile.tsx`
