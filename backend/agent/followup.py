import logging
import os
from datetime import timedelta

from django.utils import timezone

from .models import Chat, ChatMessage
from .waha import enviar_whatsapp

logger = logging.getLogger(__name__)

FOLLOWUP_AFTER_HOURS = float(os.getenv("AGENT_FOLLOWUP_AFTER_HOURS", "4"))
FOLLOWUP_MAX_PER_CHAT = int(os.getenv("AGENT_FOLLOWUP_MAX_PER_CHAT", "1"))


def verificar_followup():
    limite = timezone.now() - timedelta(hours=FOLLOWUP_AFTER_HOURS)
    chats = Chat.objects.filter(status="active", canal="whatsapp", updated_at__lt=limite)

    for chat in chats:
        ultima = chat.mensagens.last()
        if not ultima or ultima.role != "bot":
            continue
        if ultima.content.startswith("[Follow-up]"):
            continue

        ultimo_usuario = chat.mensagens.filter(role="user").order_by("-created_at").first()
        if not ultimo_usuario:
            continue

        followups_depois_do_usuario = chat.mensagens.filter(
            role="bot",
            content__startswith="[Follow-up]",
            created_at__gt=ultimo_usuario.created_at,
        ).count()
        if followups_depois_do_usuario >= FOLLOWUP_MAX_PER_CHAT:
            continue

        resposta = _montar_followup(chat)

        enviar_whatsapp(chat.lead.telefone, resposta)
        ChatMessage.objects.create(chat=chat, role="bot", content=f"[Follow-up] {resposta}")
        chat.updated_at = timezone.now()
        chat.save(update_fields=["updated_at"])
        logger.info("Follow-up enviado para %s", chat.lead.telefone)


def _montar_followup(chat: Chat) -> str:
    if chat.provider_recomendado:
        return (
            f"Oi! Quer seguir com {chat.provider_recomendado.name} "
            "ou prefere que eu busque outra opcao?"
        )
    return "Oi! Conseguiu ver as opcoes? Quer que eu busque outra cidade ou outro profissional?"
