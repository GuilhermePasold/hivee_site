"""WebSocket de notificações in-app.

Cada usuário logado entra no grupo ``notify_user_<id>``. O `notify_user()`
(catalog/services.py) faz ``group_send`` para esse grupo quando um evento de
negócio acontece. Segue o mesmo padrão de autenticação por cookie httpOnly do
`agent.consumers.ChatConsumer`.
"""
import json
import logging

from django.conf import settings
from rest_framework.authtoken.models import Token

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer

logger = logging.getLogger(__name__)


class NotificationsConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = await self._autenticar_usuario()
        if self.user is None:
            await self.close(code=4401)
            return

        self.group_name = f"notify_user_{self.user.id}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        # Envia a contagem inicial assim que conecta.
        await self._enviar_unread_count()

    async def disconnect(self, close_code):
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data):
        """Aceita comandos do cliente para marcar notificações como lidas."""
        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            return

        action = data.get("action")
        if action == "mark_read":
            await self._marcar_lida(data.get("id"))
            await self._enviar_unread_count()
        elif action == "mark_all_read":
            await self._marcar_todas_lidas()
            await self._enviar_unread_count()

    # ── Handlers de eventos do canal (group_send) ────────────────────────

    async def notification_message(self, event):
        """Entrega uma notificação nova ao cliente (chamado por group_send)."""
        await self.send(
            text_data=json.dumps({"type": "notification", "data": event["data"]})
        )

    async def unread_count(self, event):
        """Envia a contagem atualizada de não lidas."""
        await self.send(
            text_data=json.dumps({"type": "unread_count", "count": event["count"]})
        )

    # ── Helpers ──────────────────────────────────────────────────────────

    async def _enviar_unread_count(self):
        count = await self._contar_nao_lidas()
        await self.send(text_data=json.dumps({"type": "unread_count", "count": count}))

    @database_sync_to_async
    def _autenticar_usuario(self):
        cookies = _parse_cookies(self.scope.get("headers", []))
        token_key = cookies.get(settings.AUTH_COOKIE_NAME)
        if not token_key:
            return None
        token = Token.objects.select_related("user").filter(key=token_key).first()
        return token.user if token else None

    @database_sync_to_async
    def _contar_nao_lidas(self):
        from .models import Notification

        return Notification.objects.filter(recipient=self.user, is_read=False).count()

    @database_sync_to_async
    def _marcar_lida(self, notification_id):
        from .models import Notification

        if notification_id:
            Notification.objects.filter(
                id=notification_id, recipient=self.user
            ).update(is_read=True)

    @database_sync_to_async
    def _marcar_todas_lidas(self):
        from .models import Notification

        Notification.objects.filter(recipient=self.user, is_read=False).update(
            is_read=True
        )


def _parse_cookies(headers) -> dict[str, str]:
    for name, value in headers:
        if name == b"cookie":
            raw = value.decode("latin1")
            cookies = {}
            for part in raw.split(";"):
                if "=" in part:
                    key, val = part.split("=", 1)
                    cookies[key.strip()] = val.strip()
            return cookies
    return {}
