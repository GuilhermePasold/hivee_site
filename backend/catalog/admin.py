from django.contrib import admin

from .models import AvailabilitySlot, Category, Cliente, Provider, ProviderImage, UserProfile


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "icon", "order")
    prepopulated_fields = {"slug": ("name",)}


class ProviderImageInline(admin.TabularInline):
    model = ProviderImage
    extra = 1


@admin.register(Provider)
class ProviderAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "city", "rating", "status", "verified")
    list_filter = ("category", "verified", "top_rated", "state", "status")
    search_fields = ("name", "headline", "city", "neighborhood")
    inlines = [ProviderImageInline]
    actions = ["approve_providers", "reject_providers"]

    def approve_providers(self, request, queryset):
        queryset.update(status="approved", verified=True)
        self.message_user(request, f"{queryset.count()} prestador(es) aprovado(s).")
    approve_providers.short_description = "Aprovar prestadores selecionados"

    def reject_providers(self, request, queryset):
        queryset.update(status="rejected")
        self.message_user(request, f"{queryset.count()} prestador(es) rejeitado(s).")
    reject_providers.short_description = "Rejeitar prestadores selecionados"


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ("nome", "cpf", "telefone", "email", "ativo", "criado_em")
    list_filter = ("ativo", "criado_em")
    search_fields = ("nome", "cpf", "email")


@admin.register(AvailabilitySlot)
class AvailabilitySlotAdmin(admin.ModelAdmin):
    list_display = ("provider", "day_of_week", "start_time", "end_time")
    list_filter = ("day_of_week",)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "cpf", "telefone")
    search_fields = ("user__email", "cpf")
