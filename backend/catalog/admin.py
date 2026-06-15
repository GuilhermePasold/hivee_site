import json
import time
import urllib.request
from urllib.error import URLError

from django.contrib import admin, messages

from .models import AvailabilitySlot, Category, Cliente, Provider, ProviderImage, UserProfile

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
        self.message_user(request, f"{queryset.count()} prestador(es) rejeitado(s).")
    reject_providers.short_description = "Rejeitar prestadores selecionados"


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
                elif nome_receita:
                    profile.cpf_status = "mismatch"
                    profile.cpf_name = nome_receita
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
