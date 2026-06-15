import logging

from django.contrib import admin

from .models import Chat, ChatLead, ChatMessage

logger = logging.getLogger(__name__)


@admin.register(ChatLead)
class ChatLeadAdmin(admin.ModelAdmin):
    list_display = ["telefone", "nome_wpp", "nome_site", "canal_origem", "created_at"]
    search_fields = ["telefone", "nome_wpp", "nome_site"]
    list_filter = ["canal_origem"]


@admin.register(Chat)
class ChatAdmin(admin.ModelAdmin):
    list_display = ["lead", "canal", "status", "provider_recomendado", "updated_at"]
    list_filter = ["status", "canal"]
    search_fields = ["lead__telefone", "lead__nome_wpp", "lead__nome_site"]


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ["chat", "role", "msg_type", "created_at", "content_preview"]
    list_filter = ["role", "msg_type"]
    search_fields = ["content", "chat__lead__telefone"]

    def content_preview(self, obj):
        return obj.content[:60] + "..." if len(obj.content) > 60 else obj.content
