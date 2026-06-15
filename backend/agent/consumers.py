import base64
import json
import logging
import tempfile
from pathlib import Path

from django.conf import settings
from rest_framework.authtoken.models import Token

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer

from .buffer import TEMPO_ESPERA_SITE, push
from .models import ChatLead
from .audio import transcrever_audio
from .vision import analisar_imagem

logger = logging.getLogger(__name__)
MAX_SITE_MEDIA_BYTES = 8 * 1024 * 1024


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = await self._autenticar_usuario()
        if self.user is None:
            logger.warning("WebSocket recusado: usuario nao autenticado")
            await self.close(code=4401)
            return

        self.telefone = self.scope["url_route"]["kwargs"]["telefone"]
        self.room_group_name = f"chat_{self.telefone}"
        await self._garantir_lead()
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()
        logger.info("WebSocket conectado: %s", self.telefone)

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
        logger.info("WebSocket desconectado: %s", self.telefone)

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            logger.warning("WebSocket payload invalido: %s", text_data[:120])
            return

        conteudo = data.get("content", "")
        media = data.get("media")
        if conteudo or media:
            await self.send(
                text_data=json.dumps(
                    {
                        "role": "bot",
                        "content": "",
                        "typing": True,
                    }
                )
            )
            await self._buffer_site(conteudo, media)

    async def bot_message(self, event):
        await self.send(
            text_data=json.dumps(
                {
                    "role": "bot",
                    "content": event["content"],
                    "typing": event.get("typing", False),
                }
            )
        )

    async def provider_cards(self, event):
        await self.send(
            text_data=json.dumps(
                {
                    "role": "bot",
                    "type": "provider_cards",
                    "providers": event.get("providers", []),
                }
            )
        )

    @database_sync_to_async
    def _garantir_lead(self):
        nome = self.user.get_full_name() or self.user.email or self.user.username
        ChatLead.objects.update_or_create(
            telefone=self.telefone,
            defaults={"nome_site": nome, "canal_origem": "site"},
        )

    @database_sync_to_async
    def _autenticar_usuario(self):
        cookies = _parse_cookies(self.scope.get("headers", []))
        token_key = cookies.get(settings.AUTH_COOKIE_NAME)
        if not token_key:
            return None
        token = Token.objects.select_related("user").filter(key=token_key).first()
        return token.user if token else None

    @database_sync_to_async
    def _buffer_site(self, conteudo: str, media: dict | None = None):
        if media:
            conteudo = _conteudo_midia_site(self.telefone, conteudo, media)
        push(self.telefone, conteudo, espera=TEMPO_ESPERA_SITE)


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


def _conteudo_midia_site(telefone: str, caption: str, media: dict) -> str:
    mime_type = str(media.get("mime_type") or "")
    raw_data = str(media.get("data") or "")
    filename = str(media.get("name") or "upload")

    if "," in raw_data and raw_data.startswith("data:"):
        raw_data = raw_data.split(",", 1)[1]

    try:
        content = base64.b64decode(raw_data, validate=True)
    except Exception:
        logger.warning("Upload site invalido para %s", telefone)
        return caption or "[Arquivo nao pode ser processado]"

    if len(content) > MAX_SITE_MEDIA_BYTES:
        return "[Arquivo muito grande para o chat. Envie um arquivo de ate 8MB.]"

    suffix = _suffix(filename, mime_type)
    temp_dir = Path(tempfile.gettempdir()) / "hivee_site_uploads" / telefone
    temp_dir.mkdir(parents=True, exist_ok=True)
    path = temp_dir / f"upload_{len(content)}{suffix}"
    path.write_bytes(content)

    if mime_type.startswith("audio/"):
        transcricao = transcrever_audio(str(path)).strip()
        if not transcricao:
            return f"{caption}\n[Áudio sem fala identificável]".strip()
        return f"{caption}\n[Áudio transcrito]: {transcricao}".strip()
    if mime_type.startswith("image/"):
        return analisar_imagem(str(path), caption)
    return caption or f"[Arquivo recebido: {filename}]"


def _suffix(filename: str, mime_type: str) -> str:
    if "." in filename:
        return "." + filename.rsplit(".", 1)[-1].lower()
    if "/" in mime_type:
        subtype = mime_type.split("/", 1)[1].split(";")[0]
        return ".jpg" if subtype == "jpeg" else f".{subtype}"
    return ".bin"
