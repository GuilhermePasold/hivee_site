from django.conf import settings
from django.db import models


class Category(models.Model):
    """A service category."""

    name = models.CharField(max_length=80, unique=True)
    slug = models.SlugField(max_length=90, unique=True)
    icon = models.CharField(
        max_length=40,
        help_text="lucide-react icon name in PascalCase (e.g. 'Wrench').",
    )
    tagline = models.CharField(max_length=140, blank=True)
    accent = models.CharField(max_length=7, default="#eab308", help_text="Hex accent color.")
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "name"]
        verbose_name = "Categoria"
        verbose_name_plural = "Categorias"

    def __str__(self) -> str:
        return self.name


class Tag(models.Model):
    """Free-text service tag, compartilhada entre prestadores.

    Funciona como vocabulário vivo: o prestador digita uma tag; se já existe ela é
    sugerida, se não, é criada. Ajuda a busca por termos além da categoria.
    """

    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=60, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Tag de serviço"
        verbose_name_plural = "Tags de serviço"

    def __str__(self) -> str:
        return self.name


class Provider(models.Model):
    """A service provider listed on the marketplace."""

    name = models.CharField(max_length=120)
    slug = models.SlugField(max_length=140, unique=True)
    headline = models.CharField(max_length=160)
    bio = models.TextField(blank=True)
    category = models.ForeignKey(
        Category, on_delete=models.CASCADE, related_name="providers"
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="provider_profiles",
    )

    avatar_url = models.URLField(blank=True, default="")
    cover_url = models.URLField(blank=True)

    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    reviews_count = models.PositiveIntegerField(default=0)
    jobs_done = models.PositiveIntegerField(default=0)

    hourly_rate = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    currency = models.CharField(max_length=3, default="BRL")

    city = models.CharField(max_length=80, blank=True, default="")
    neighborhood = models.CharField(max_length=80, blank=True, default="")
    state = models.CharField(max_length=2, blank=True, default="")
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    verified = models.BooleanField(default=False)
    top_rated = models.BooleanField(default=False)
    response_time = models.CharField(max_length=40, default="em 1 hora")
    availability = models.CharField(max_length=60, default="Disponível esta semana")
    skills = models.JSONField(default=list)
    tags = models.ManyToManyField(Tag, blank=True, related_name="providers")
    member_since = models.PositiveIntegerField(default=2026)

    status = models.CharField(
        max_length=20,
        default="pending",
        choices=[("pending", "Em análise"), ("approved", "Aprovado"), ("rejected", "Rejeitado")],
    )
    avatar = models.ImageField(upload_to="avatars/", blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-top_rated", "-rating", "-reviews_count"]
        verbose_name = "Prestador"
        verbose_name_plural = "Prestadores"

    def __str__(self) -> str:
        return f"{self.name} - {self.category.name}"


class ProviderImage(models.Model):
    """Optional gallery image for a service provider."""

    provider = models.ForeignKey(
        Provider, on_delete=models.CASCADE, related_name="images"
    )
    image = models.ImageField(upload_to="providers/gallery/%Y/%m/%d/")
    alt_text = models.CharField(max_length=160, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Imagem do prestador"
        verbose_name_plural = "Imagens dos prestadores"

    def __str__(self) -> str:
        return self.alt_text or f"Imagem de {self.provider.name}"


class AvailabilitySlot(models.Model):
    provider = models.ForeignKey(Provider, on_delete=models.CASCADE, related_name="availability_slots")
    day_of_week = models.IntegerField(choices=[(0, "Seg"), (1, "Ter"), (2, "Qua"), (3, "Qui"), (4, "Sex"), (5, "Sáb"), (6, "Dom")])
    start_time = models.TimeField()
    end_time = models.TimeField()

    class Meta:
        verbose_name = "Horário disponível"
        verbose_name_plural = "Horários disponíveis"
        ordering = ["day_of_week", "start_time"]

    def __str__(self) -> str:
        days = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]
        return f"{days[self.day_of_week]} {self.start_time:%H:%M}-{self.end_time:%H:%M}"


class UserProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile"
    )
    cpf = models.CharField(max_length=14, unique=True, blank=True, null=True)
    telefone = models.CharField(max_length=15, blank=True, default="")
    cpf_status = models.CharField(
        max_length=30,
        default="pending_verification",
        choices=[
            ("verified", "Verificado"),
            ("pending_verification", "Pendente de verificação"),
            ("mismatch", "Nome não confere com o CPF"),
        ],
    )
    cpf_name = models.CharField(max_length=200, blank=True, default="")
    provider_status = models.CharField(
        max_length=20,
        blank=True,
        default="",
        choices=[
            ("", "Não é prestador"),
            ("pending", "Pendente de aprovação"),
            ("approved", "Aprovado"),
            ("rejected", "Rejeitado"),
        ],
    )

    class Meta:
        verbose_name = "Perfil do usuário"
        verbose_name_plural = "Perfis de usuários"

    def __str__(self) -> str:
        return f"Perfil de {self.user.email}"


class ProviderSwipe(models.Model):
    """Tinder-like decision of a user over a recommended provider.

    `like` == favorito (aparece na aba "Prestadores favoritos"); `dislike` == passou.
    Em ambos os casos o prestador deixa de aparecer no deck de recomendações.
    """

    LIKE = "like"
    DISLIKE = "dislike"
    ACTIONS = [(LIKE, "Curtiu"), (DISLIKE, "Passou")]

    DECK = "deck"
    PROFILE = "profile"
    SOURCES = [(DECK, "Deck de recomendações"), (PROFILE, "Perfil do prestador")]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="provider_swipes"
    )
    provider = models.ForeignKey(
        Provider, on_delete=models.CASCADE, related_name="swipes"
    )
    action = models.CharField(max_length=10, choices=ACTIONS, db_index=True)
    # `deck` conta para o limite diário de recomendações; `profile` (favoritar
    # direto no perfil) é uma ação deliberada e não gasta a cota do dia.
    source = models.CharField(max_length=10, choices=SOURCES, default=DECK)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "provider")
        ordering = ["-created_at"]
        verbose_name = "Swipe de prestador"
        verbose_name_plural = "Swipes de prestadores"

    def __str__(self) -> str:
        return f"{self.user} {self.action} {self.provider.name}"


class Demand(models.Model):
    """Uma demanda publicada por um cliente para prestadores se candidatarem.

    Modelo TaskRabbit: o cliente descreve o que precisa e prestadores verificados
    se oferecem para realizar. A localização pode ser diferente da do cliente.
    """

    STATUS_CHOICES = [
        ("open", "Aberta"),
        ("in_progress", "Em andamento"),
        ("closed", "Encerrada"),
        ("cancelled", "Cancelada"),
    ]

    client = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="demands"
    )
    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL, null=True, blank=True, related_name="demands"
    )
    tags = models.ManyToManyField(Tag, blank=True, related_name="demands")

    # Localização (pode ser diferente da do cliente)
    city = models.CharField(max_length=80, blank=True, default="")
    neighborhood = models.CharField(max_length=80, blank=True, default="")
    state = models.CharField(max_length=2, blank=True, default="")
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    # Prazo e orçamento (texto livre, sem compromisso de valor fechado)
    preferred_schedule = models.CharField(
        max_length=160, blank=True, default="",
        help_text="Ex.: 'Segunda-feira de manhã' ou 'Até 15 de julho'",
    )
    budget_hint = models.CharField(
        max_length=80, blank=True, default="",
        help_text="Ex.: 'Até R$ 500' ou 'A combinar'",
    )

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="open")
    offer_count = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Demanda"
        verbose_name_plural = "Demandas"

    def __str__(self) -> str:
        return f"{self.title} — {self.client.email}"


class DemandOffer(models.Model):
    """Um prestador se oferecendo para realizar uma demanda."""

    STATUS_CHOICES = [
        ("pending", "Pendente"),
        ("accepted", "Aceito"),
        ("rejected", "Recusado"),
    ]

    demand = models.ForeignKey(
        Demand, on_delete=models.CASCADE, related_name="offers"
    )
    provider = models.ForeignKey(
        Provider, on_delete=models.CASCADE, related_name="demand_offers"
    )
    message = models.TextField(
        blank=True, default="",
        help_text="Mensagem do prestador para o cliente",
    )
    suggested_value = models.DecimalField(
        max_digits=8, decimal_places=2, null=True, blank=True
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # Um prestador só pode fazer uma oferta por demanda.
        unique_together = ("demand", "provider")
        ordering = ["-created_at"]
        verbose_name = "Oferta de demanda"
        verbose_name_plural = "Ofertas de demandas"

    def __str__(self) -> str:
        return f"{self.provider.name} → {self.demand.title}"


class Notification(models.Model):
    """Notificação in-app de um usuário (cliente ou prestador).

    Persiste o histórico (seguindo o padrão de `logs.LogEvent`). A entrega em
    tempo real é feita pelo `NotificationsConsumer` (WebSocket); o WhatsApp é um
    canal opcional acionado pelo `notify_user()`.
    """

    class Tipo(models.TextChoices):
        # Conta / Prestador
        PROVIDER_APPROVED = "provider_approved", "Perfil aprovado"
        PROVIDER_REJECTED = "provider_rejected", "Perfil rejeitado"
        CPF_VERIFIED = "cpf_verified", "CPF verificado"
        CPF_MISMATCH = "cpf_mismatch", "CPF não confere"

        # Ordens de serviço (reservado para o futuro sistema de ordens)
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


# --- Suporte ao usuário ----------------------------------------------------
class SupportCategory(models.Model):
    """Agrupa artigos da FAQ e tickets por assunto (ex.: Cadastro, Pagamento)."""

    name = models.CharField(max_length=80, unique=True)
    slug = models.SlugField(max_length=90, unique=True)
    icon = models.CharField(
        max_length=40, blank=True, default="", help_text="lucide-react icon name"
    )
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "name"]
        verbose_name = "Categoria de suporte"
        verbose_name_plural = "Categorias de suporte"

    def __str__(self) -> str:
        return self.name


class FAQArticle(models.Model):
    """Artigo da central de ajuda."""

    category = models.ForeignKey(
        SupportCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
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


class SupportTicket(models.Model):
    """Ticket de suporte aberto por um usuário — workflow estilo ServiceOrder."""

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
        SupportCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="tickets",
    )
    subject = models.CharField(max_length=200)
    description = models.TextField()
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.OPEN, db_index=True
    )
    priority = models.CharField(
        max_length=10, choices=Priority.choices, default=Priority.MEDIUM
    )
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="assigned_tickets",
        verbose_name="Responsável",
    )
    attachment = models.FileField(
        upload_to="support/attachments/%Y/%m/%d/", null=True, blank=True
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


class SupportMessage(models.Model):
    """Mensagem dentro de um ticket (usuário ou staff)."""

    ticket = models.ForeignKey(
        SupportTicket, on_delete=models.CASCADE, related_name="messages"
    )
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    content = models.TextField()
    is_staff = models.BooleanField(default=False, db_index=True)
    attachment = models.FileField(
        upload_to="support/messages/%Y/%m/%d/", null=True, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]
        verbose_name = "Mensagem de suporte"
        verbose_name_plural = "Mensagens de suporte"

    def __str__(self) -> str:
        return f"{self.author.first_name}: {self.content[:60]}..."


class SupportTicketLog(models.Model):
    """Histórico de alterações do ticket (auditoria) — estilo ServiceStatusLog."""

    ticket = models.ForeignKey(
        SupportTicket, on_delete=models.CASCADE, related_name="logs"
    )
    from_status = models.CharField(max_length=20, blank=True, default="")
    to_status = models.CharField(max_length=20)
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL
    )
    note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]
        verbose_name = "Log de ticket"
        verbose_name_plural = "Logs de tickets"

    def __str__(self) -> str:
        return f"#{self.ticket_id} {self.from_status} → {self.to_status}"


class Cliente(models.Model):
    """Classic MTV customer record, independent from DRF token auth."""

    nome = models.CharField(max_length=200)
    cpf = models.CharField(max_length=14, unique=True)
    email = models.EmailField(unique=True)
    telefone = models.CharField(max_length=15)
    senha = models.CharField(max_length=128)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)
    ativo = models.BooleanField(default=True)

    class Meta:
        ordering = ["nome"]
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"

    def __str__(self) -> str:
        return self.nome


class Servico(models.Model):
    """Serviço contratado: gerencia todo o ciclo de vida do agendamento.

    Fluxo: solicitado -> em_andamento -> concluido -> aguardando_pagamento ->
    finalizado. Caminhos alternativos: rejeitado, cancelado, disputa.
    O pagamento é SIMULADO (sem gateway real) para fechar o ciclo localmente.
    """

    class Status(models.TextChoices):
        SOLICITADO = "solicitado", "Pendente de aprovação"
        REJEITADO = "rejeitado", "Rejeitado"
        CANCELADO = "cancelado", "Cancelado"
        EM_ANDAMENTO = "em_andamento", "Em andamento"
        CONCLUIDO = "concluido", "Aguardando confirmação"
        AGUARDANDO_PAGAMENTO = "aguardando_pagamento", "Aguardando pagamento"
        FINALIZADO = "finalizado", "Finalizado"
        DISPUTA = "disputa", "Em disputa"

    # Estados que ainda estão "abertos" (ocupam um horário / em andamento).
    ABERTOS = ["solicitado", "em_andamento", "concluido", "aguardando_pagamento", "disputa"]

    provider = models.ForeignKey(Provider, on_delete=models.CASCADE, related_name="servicos")
    cliente_user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="servicos_contratados"
    )
    cliente_nome = models.CharField(max_length=200)
    cliente_email = models.EmailField(blank=True)
    cliente_telefone = models.CharField(max_length=15, blank=True)

    descricao = models.TextField()
    endereco = models.TextField(blank=True)
    observacoes = models.TextField(blank=True)

    data_solicitada = models.DateTimeField()
    data_aprovacao = models.DateTimeField(null=True, blank=True)
    data_inicio = models.DateTimeField(null=True, blank=True)
    data_conclusao = models.DateTimeField(null=True, blank=True)
    data_pagamento = models.DateTimeField(null=True, blank=True)

    valor_combinado = models.DecimalField(max_digits=10, decimal_places=2)
    comissao_percent = models.DecimalField(max_digits=5, decimal_places=2, default=10)
    valor_comissao = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    valor_liquido = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    status = models.CharField(
        max_length=24, choices=Status.choices, default=Status.SOLICITADO, db_index=True
    )
    motivo_rejeicao = models.TextField(blank=True)
    sugestao_horario = models.DateTimeField(null=True, blank=True)
    # Pix simulado (apenas para visual do fluxo de pagamento).
    pix_copia_cola = models.TextField(blank=True)
    pago = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Serviço"
        verbose_name_plural = "Serviços"

    def __str__(self) -> str:
        return f"Serviço #{self.pk} {self.provider.name} x {self.cliente_nome} [{self.status}]"


class Review(models.Model):
    """Avaliação obrigatória de um serviço finalizado. Recalcula o rating do prestador."""

    servico = models.OneToOneField(Servico, on_delete=models.CASCADE, related_name="review")
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reviews_feitas"
    )
    provider = models.ForeignKey(Provider, on_delete=models.CASCADE, related_name="reviews")
    nota = models.PositiveSmallIntegerField()  # 1..5
    comentario = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Avaliação"
        verbose_name_plural = "Avaliações"

    def __str__(self) -> str:
        return f"{self.nota}★ {self.provider.name} por {self.reviewer}"
