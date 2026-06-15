"""Serviço central de notificações.

Um único ponto de entrada (`notify_user`) cria a notificação no banco, entrega
em tempo real via WebSocket (canal `notify_user_<id>`) e, opcionalmente, envia
pelo WhatsApp reusando a infraestrutura WAHA já existente no app `agent`.
"""
import logging

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.contrib.auth import get_user_model

from .models import Notification

logger = logging.getLogger(__name__)

User = get_user_model()


def notify_user(
    *,
    recipient,
    tipo: str,
    title: str,
    body: str = "",
    link: str = "",
    payload: dict | None = None,
    via_whatsapp: bool = False,
) -> Notification:
    """Cria uma notificação e a entrega em tempo real via WebSocket.

    Parâmetros
    ----------
    recipient : User
        Usuário destinatário.
    tipo : str
        Uma das chaves de ``Notification.Tipo`` (ex.: ``"order_requested"``).
    title, body : str
        Texto da notificação.
    link : str
        URL relativa para ação (ex.: ``"/notificacoes"``).
    payload : dict | None
        Dados extras (ex.: ``{"provider_slug": "...", "order_id": 5}``).
    via_whatsapp : bool
        Se ``True``, também tenta enviar via WhatsApp (se o usuário tiver
        telefone cadastrado e o WAHA estiver configurado).
    """
    notification = Notification.objects.create(
        recipient=recipient,
        tipo=tipo,
        title=title,
        body=body,
        link=link,
        payload=payload or {},
    )

    _send_via_ws(notification)

    if via_whatsapp:
        _send_via_wpp(recipient, title, body, link)

    return notification


# ── Internals ──────────────────────────────────────────────────────────


def _send_via_ws(notification: Notification) -> None:
    """Envia a notificação para o grupo WebSocket do usuário."""
    layer = get_channel_layer()
    if layer is None:
        return  # sem channel layer configurado

    try:
        async_to_sync(layer.group_send)(
            f"notify_user_{notification.recipient_id}",
            {
                "type": "notification.message",
                "data": _serialize(notification),
            },
        )
    except Exception:
        logger.exception("Falha ao enviar notificação via WebSocket (id=%s)", notification.id)


def _send_via_wpp(recipient, title: str, body: str, link: str) -> None:
    """Tenta enviar a notificação via WhatsApp usando o WAHA do app `agent`.

    Só envia se o usuário tiver telefone no perfil. Falha de forma silenciosa —
    o canal WebSocket já é a entrega principal.
    """
    from django.conf import settings

    telefone = getattr(getattr(recipient, "profile", None), "telefone", "")
    if not telefone:
        return

    try:
        from agent.waha import enviar_whatsapp

        base = getattr(settings, "FRONTEND_URL", "")
        rodape = f"\n\n{base}{link}" if link else ""
        texto = f"*{title}*\n\n{body}{rodape}".strip()
        enviar_whatsapp(telefone, texto)
    except Exception:
        logger.exception("Falha ao enviar notificação via WhatsApp para %s", telefone)


def _serialize(notification: Notification) -> dict:
    """Forma canônica de uma notificação no fio (WS e REST compartilham)."""
    return {
        "id": notification.id,
        "tipo": notification.tipo,
        "title": notification.title,
        "body": notification.body,
        "link": notification.link,
        "payload": notification.payload,
        "is_read": notification.is_read,
        "created_at": notification.created_at.isoformat(),
    }
