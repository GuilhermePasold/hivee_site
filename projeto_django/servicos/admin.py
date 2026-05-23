from django.contrib import admin
from .models import UserProfile, CategoriaServico, PrestadorPerfil, Contrato, Avaliacao


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'tipo', 'cidade', 'estado', 'cep', 'plano']
    list_filter = ['tipo', 'plano']
    search_fields = ['user__username', 'user__email', 'cidade']
    list_editable = ['tipo', 'plano']


@admin.register(CategoriaServico)
class CategoriaServicoAdmin(admin.ModelAdmin):
    list_display = ['icone', 'nome', 'slug', 'ativo']
    list_editable = ['ativo']
    prepopulated_fields = {'slug': ('nome',)}


class AvaliacaoInline(admin.TabularInline):
    model = Avaliacao
    extra = 0
    readonly_fields = ['criado_em']


@admin.register(PrestadorPerfil)
class PrestadorPerfilAdmin(admin.ModelAdmin):
    list_display = ['user', 'get_localizacao', 'valor_hora', 'nota_media', 'total_servicos', 'disponivel', 'status_adesao', 'deleted']
    list_filter = ['disponivel', 'status_adesao', 'estado']
    search_fields = ['user__username', 'user__first_name', 'user__last_name', 'cidade']
    list_editable = ['disponivel', 'status_adesao']
    filter_horizontal = ['especialidades']
    readonly_fields = ['nota_media', 'total_servicos', 'criado_em', 'atualizado_em']

    @admin.display(description='Localização')
    def get_localizacao(self, obj):
        return obj.get_localizacao()


@admin.register(Contrato)
class ContratoAdmin(admin.ModelAdmin):
    list_display = ['id', 'titulo', 'cliente', 'prestador', 'status', 'status_pagamento', 'valor_acordado', 'data_solicitacao']
    list_filter = ['status', 'status_pagamento']
    search_fields = ['titulo', 'cliente__username', 'prestador__user__username']
    list_editable = ['status', 'status_pagamento']
    readonly_fields = ['data_solicitacao', 'data_aceite', 'data_inicio', 'data_conclusao']
    inlines = [AvaliacaoInline]


@admin.register(Avaliacao)
class AvaliacaoAdmin(admin.ModelAdmin):
    list_display = ['prestador', 'cliente', 'estrelas', 'criado_em']
    list_filter = ['estrelas']
    readonly_fields = ['criado_em']
