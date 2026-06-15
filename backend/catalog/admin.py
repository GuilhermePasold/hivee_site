import json
import time
import urllib.request
from urllib.error import URLError

from django.contrib import admin, messages
from django.utils import timezone

from .models import (
    AvailabilitySlot,
    Category,
    Cliente,
    Demand,
    DemandOffer,
    FAQArticle,
    Notification,
    Provider,
    ProviderImage,
    ProviderSwipe,
    SupportCategory,
    SupportMessage,
    SupportTicket,
    SupportTicketLog,
    Tag,
    UserProfile,
)
from .services import notify_user

RECEITAWS_URL = "https://www.receitaws.com.br/v1/cpf/%s"


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "icon", "order")
    prepopulated_fields = {"slug": ("name",)}


class ProviderImageInline(admin.TabularInline):
    model = ProviderImage
    extra = 1


@admin.register(Provider)
class ProviderAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "city", "rating", "status", "verified", "cpf_status_display")
    list_filter = ("category", "verified", "top_rated", "state", "status")
    search_fields = ("name", "headline", "city", "neighborhood")
    inlines = [ProviderImageInline]
    actions = ["approve_providers", "reject_providers"]

    def cpf_status_display(self, obj):
        try:
            return obj.owner.profile.get_cpf_status_display()
        except (AttributeError, UserProfile.DoesNotExist):
            return "—"
    cpf_status_display.short_description = "CPF"

    def approve_providers(self, request, queryset):
        blocked = []
        approved = []
        for provider in queryset:
            try:
                cpf_status = provider.owner.profile.cpf_status
            except (AttributeError, UserProfile.DoesNotExist):
                cpf_status = "verified"
            if cpf_status == "mismatch":
                blocked.append(provider.name)
            else:
                provider.status = "approved"
                provider.verified = True
                provider.save(update_fields=["status", "verified"])
                try:
                    provider.owner.profile.provider_status = "approved"
                    provider.owner.profile.save(update_fields=["provider_status"])
                except (AttributeError, UserProfile.DoesNotExist):
                    pass
                if provider.owner_id:
                    notify_user(
                        recipient=provider.owner,
                        tipo=Notification.Tipo.PROVIDER_APPROVED,
                        title="Seu perfil de prestador foi aprovado!",
                        body=f"{provider.name}, você já aparece nas buscas do HIVEE.",
                        link=f"/prestador/{provider.slug}",
                        payload={"provider_slug": provider.slug},
                    )
                approved.append(provider.name)

        if approved:
            self.message_user(request, f"{len(approved)} prestador(es) aprovado(s).", messages.SUCCESS)
        if blocked:
            self.message_user(
                request,
                f"BLOQUEADOS (CPF com nome divergente): {', '.join(blocked)}",
                messages.ERROR,
            )
    approve_providers.short_description = "Aprovar prestadores selecionados (verifica CPF)"

    def reject_providers(self, request, queryset):
        for provider in queryset:
            provider.status = "rejected"
            provider.save(update_fields=["status"])
            try:
                provider.owner.profile.provider_status = "rejected"
                provider.owner.profile.save(update_fields=["provider_status"])
            except (AttributeError, UserProfile.DoesNotExist):
                pass
            if provider.owner_id:
                notify_user(
                    recipient=provider.owner,
                    tipo=Notification.Tipo.PROVIDER_REJECTED,
                    title="Seu cadastro de prestador não foi aprovado",
                    body="Revise seus dados e tente novamente, ou fale com o suporte.",
                    link="/minha-conta",
                    payload={"provider_slug": provider.slug},
                )
        self.message_user(request, f"{queryset.count()} prestador(es) rejeitado(s).")
    reject_providers.short_description = "Rejeitar prestadores selecionados"


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("tipo", "recipient", "title", "is_read", "created_at")
    list_filter = ("tipo", "is_read", "created_at")
    search_fields = ("recipient__email", "title", "body")
    readonly_fields = ("created_at",)


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ("nome", "cpf", "telefone", "email", "ativo", "criado_em")
    list_filter = ("ativo", "criado_em")
    search_fields = ("nome", "cpf", "email")
    fields = ("nome", "cpf", "email", "telefone", "senha", "ativo")

    def save_model(self, request, obj, form, change):
        raw = form.cleaned_data.get("senha")
        if raw and not raw.startswith("pbkdf2_"):
            from django.contrib.auth.hashers import make_password
            obj.senha = make_password(raw)
        super().save_model(request, obj, form, change)


@admin.register(AvailabilitySlot)
class AvailabilitySlotAdmin(admin.ModelAdmin):
    list_display = ("provider", "day_of_week", "start_time", "end_time")
    list_filter = ("day_of_week",)


@admin.register(ProviderSwipe)
class ProviderSwipeAdmin(admin.ModelAdmin):
    list_display = ("user", "provider", "action", "created_at")
    list_filter = ("action", "created_at")
    search_fields = ("user__email", "provider__name")


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "provider_count")
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}

    def provider_count(self, obj):
        return obj.providers.count()
    provider_count.short_description = "Prestadores"


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "cpf", "cpf_status", "cpf_name", "telefone", "provider_status")
    list_filter = ("cpf_status", "provider_status")
    search_fields = ("user__email", "cpf", "user__first_name")
    actions = ["verificar_cpfs_pendentes"]

    def verificar_cpfs_pendentes(self, request, queryset):
        pendentes = queryset.filter(cpf_status="pending_verification", cpf__isnull=False).exclude(cpf="")
        total = pendentes.count()
        if not total:
            self.message_user(request, "Nenhum CPF pendente de verificação.", messages.WARNING)
            return

        verificados = 0
        erros = 0
        for i, profile in enumerate(pendentes):
            if i > 0:
                time.sleep(21)
            cpf_limpo = "".join(c for c in profile.cpf if c.isdigit())
            try:
                req = urllib.request.Request(
                    f"https://www.receitaws.com.br/v1/cpf/{cpf_limpo}",
                    headers={"User-Agent": "HIVEE-ADMIN/1.0"},
                )
                with urllib.request.urlopen(req, timeout=10) as res:
                    data = json.loads(res.read().decode())
                if data.get("status") == "ERROR":
                    profile.cpf_status = "pending_verification"
                    profile.save(update_fields=["cpf_status"])
                    erros += 1
                    continue
                nome_receita = (data.get("nome") or "").strip().upper()
                nome_usuario = (profile.user.first_name or "").strip().upper()
                if nome_receita == nome_usuario:
                    profile.cpf_status = "verified"
                    profile.cpf_name = nome_receita
                    notify_user(
                        recipient=profile.user,
                        tipo=Notification.Tipo.CPF_VERIFIED,
                        title="CPF verificado",
                        body="Seu CPF foi confirmado na Receita Federal.",
                        link="/minha-conta",
                    )
                elif nome_receita:
                    profile.cpf_status = "mismatch"
                    profile.cpf_name = nome_receita
                    notify_user(
                        recipient=profile.user,
                        tipo=Notification.Tipo.CPF_MISMATCH,
                        title="CPF não confere",
                        body="O nome cadastrado não bate com o CPF na Receita Federal.",
                        link="/minha-conta",
                    )
                else:
                    profile.cpf_status = "pending_verification"
                profile.save(update_fields=["cpf_status", "cpf_name"])
                verificados += 1
            except (URLError, json.JSONDecodeError, OSError):
                erros += 1

        self.message_user(
            request,
            f"{verificados} CPF(s) verificados, {erros} falha(s).",
            messages.SUCCESS if not erros else messages.WARNING,
        )
    verificar_cpfs_pendentes.short_description = "Verificar CPFs pendentes (Respeita rate limit)"


# --- Suporte ao usuário ----------------------------------------------------
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
    actions = ["assign_to_me", "mark_resolved", "mark_closed"]

    def subject_short(self, obj):
        return obj.subject[:80]
    subject_short.short_description = "Assunto"

    def assign_to_me(self, request, queryset):
        updated = queryset.update(assigned_to=request.user)
        self.message_user(request, f"{updated} ticket(s) designados a você.")
    assign_to_me.short_description = "Designar para mim"

    def mark_resolved(self, request, queryset):
        now = timezone.now()
        count = 0
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
            count += 1
        self.message_user(request, f"{count} ticket(s) marcados como resolvidos.")
    mark_resolved.short_description = "Marcar como resolvido"

    def mark_closed(self, request, queryset):
        now = timezone.now()
        count = 0
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
            count += 1
        self.message_user(request, f"{count} ticket(s) fechados.")
    mark_closed.short_description = "Fechar tickets"

    def changelist_view(self, request, extra_context=None):
        """Adiciona métricas de tickets ao topo da listagem."""
        extra = extra_context or {}
        base = SupportTicket.objects.all()
        active = base.exclude(
            status__in=[SupportTicket.Status.RESOLVED, SupportTicket.Status.CLOSED]
        )
        extra["ticket_metrics"] = {
            "total": base.count(),
            "open": base.filter(status=SupportTicket.Status.OPEN).count(),
            "waiting_user": base.filter(status=SupportTicket.Status.WAITING_USER).count(),
            "waiting_staff": base.filter(status=SupportTicket.Status.WAITING_STAFF).count(),
            "unassigned": active.filter(assigned_to__isnull=True).count(),
            "high_priority": active.filter(
                priority__in=[SupportTicket.Priority.HIGH, SupportTicket.Priority.URGENT]
            ).count(),
        }
        return super().changelist_view(request, extra_context=extra)


# --- Demandas --------------------------------------------------------------
class DemandOfferInline(admin.TabularInline):
    model = DemandOffer
    fields = ("provider", "status", "suggested_value", "message", "created_at")
    readonly_fields = ("provider", "created_at")
    extra = 0
    ordering = ("-created_at",)


@admin.register(Demand)
class DemandAdmin(admin.ModelAdmin):
    list_display = ("title", "client", "category", "city", "status", "offer_count", "created_at")
    list_filter = ("status", "category", "state", "created_at")
    search_fields = ("title", "description", "client__email", "client__first_name", "city")
    list_select_related = ("client", "category")
    date_hierarchy = "created_at"
    inlines = [DemandOfferInline]
    readonly_fields = ("offer_count", "created_at", "updated_at")


@admin.register(DemandOffer)
class DemandOfferAdmin(admin.ModelAdmin):
    list_display = ("provider", "demand", "status", "suggested_value", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("provider__name", "demand__title")
    list_select_related = ("provider", "demand")


from .models import Review as _Review, Servico as _Servico


@admin.register(_Servico)
class ServicoAdmin(admin.ModelAdmin):
    list_display = ("id", "provider", "cliente_nome", "status", "valor_combinado", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("provider__name", "cliente_nome", "cliente_email")
    date_hierarchy = "created_at"


@admin.register(_Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("provider", "reviewer", "nota", "created_at")
    list_filter = ("nota", "created_at")
    search_fields = ("provider__name",)
