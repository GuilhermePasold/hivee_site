from django.contrib import admin

from .models import Category, Cliente, Provider, ProviderImage


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "icon", "order")
    prepopulated_fields = {"slug": ("name",)}


class ProviderImageInline(admin.TabularInline):
    model = ProviderImage
    extra = 1


@admin.register(Provider)
class ProviderAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "city", "rating", "reviews_count", "verified")
    list_filter = ("category", "verified", "top_rated", "state")
    search_fields = ("name", "headline", "city", "neighborhood")
    inlines = [ProviderImageInline]


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ("nome", "cpf", "telefone", "email", "ativo", "criado_em")
    list_filter = ("ativo", "criado_em")
    search_fields = ("nome", "cpf", "email")
