import logging

from django.db import models

logger = logging.getLogger(__name__)


class ChatLead(models.Model):
    telefone = models.CharField(max_length=20, unique=True, verbose_name="Telefone/ID")
    nome_wpp = models.CharField(max_length=200, blank=True, default="", verbose_name="Nome WhatsApp")
    nome_site = models.CharField(max_length=200, blank=True, default="", verbose_name="Nome no Site")
    canal_origem = models.CharField(
        max_length=20,
        choices=[("whatsapp", "WhatsApp"), ("site", "Site")],
        default="whatsapp",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Lead do Chat"
        verbose_name_plural = "Leads do Chat"

    def __str__(self):
        return f"{self.nome_wpp or self.nome_site or self.telefone} ({self.get_canal_origem_display()})"


class Chat(models.Model):
    lead = models.ForeignKey(ChatLead, on_delete=models.CASCADE, related_name="chats")
    canal = models.CharField(max_length=20, choices=[("whatsapp", "WhatsApp"), ("site", "Site")])
    status = models.CharField(
        max_length=20,
        choices=[("active", "Ativo"), ("closed", "Encerrado")],
        default="active",
    )
    provider_recomendado = models.ForeignKey(
        "catalog.Provider",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        verbose_name="Prestador recomendado",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Chat"
        verbose_name_plural = "Chats"
        ordering = ["-updated_at"]

    def __str__(self):
        return f"Chat {self.lead} - {self.get_canal_display()}"


class ChatMessage(models.Model):
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE, related_name="mensagens")
    role = models.CharField(max_length=10, choices=[("user", "Usuario"), ("bot", "Bot"), ("system", "System")])
    content = models.TextField()
    msg_type = models.CharField(
        max_length=20,
        default="text",
        choices=[("text", "Texto"), ("audio", "Audio"), ("image", "Imagem")],
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Mensagem"
        verbose_name_plural = "Mensagens"
        ordering = ["created_at"]

    def __str__(self):
        return f"[{self.created_at:%H:%M}] {self.role}: {self.content[:50]}..."
