import logging
import os
import time
from pathlib import Path
from urllib.parse import urljoin

import requests

logger = logging.getLogger(__name__)

WAHA_API_URL = os.getenv("WAHA_API_URL", "").rstrip("/")
WAHA_API_KEY = os.getenv("WAHA_API_KEY", "")
WAHA_SESSION = os.getenv("WAHA_SESSION", "hivee")


def normalizar_chat_id(telefone: str) -> str:
    if "@" in telefone:
        return telefone.replace("@s.whatsapp.net", "@c.us")
    return f"{telefone}@c.us"


def _headers() -> dict[str, str]:
    headers = {"Content-Type": "application/json"}
    if WAHA_API_KEY:
        headers["X-Api-Key"] = WAHA_API_KEY
    return headers


def send_presence(telefone: str, presence: str = "typing"):
    if not WAHA_API_URL:
        logger.debug("WAHA nao configurada; presence ignorado")
        return

    url = f"{WAHA_API_URL}/api/{WAHA_SESSION}/presence"
    try:
        requests.post(
            url,
            json={"chatId": normalizar_chat_id(telefone), "presence": presence},
            headers=_headers(),
            timeout=3,
        )
    except Exception:
        logger.exception("Falha ao enviar presence WAHA para %s", telefone)


def send_seen(telefone: str):
    if not WAHA_API_URL:
        logger.debug("WAHA nao configurada; sendSeen ignorado")
        return

    url = f"{WAHA_API_URL}/api/sendSeen"
    try:
        response = requests.post(
            url,
            json={"session": WAHA_SESSION, "chatId": normalizar_chat_id(telefone)},
            headers=_headers(),
            timeout=5,
        )
        response.raise_for_status()
    except Exception:
        logger.exception("Falha ao enviar sendSeen WAHA para %s", telefone)


def enviar_whatsapp(telefone: str, texto: str):
    if not WAHA_API_URL:
        logger.debug("WAHA nao configurada; mensagem ignorada")
        return

    url = f"{WAHA_API_URL}/api/sendText"
    try:
        response = requests.post(
            url,
            json={
                "session": WAHA_SESSION,
                "chatId": normalizar_chat_id(telefone),
                "text": texto,
            },
            headers=_headers(),
            timeout=10,
        )
        response.raise_for_status()
    except Exception:
        logger.exception("Falha ao enviar WhatsApp via WAHA para %s", telefone)


def baixar_midia(media: dict, telefone: str, tipo: str) -> str | None:
    media_url = media.get("url", "")
    if not media_url:
        logger.warning("Midia WAHA sem URL para %s", telefone)
        return None

    if WAHA_API_URL and media_url.startswith("/"):
        media_url = urljoin(WAHA_API_URL, media_url)

    mime_type = media.get("mimetype", "")
    filename = media.get("filename") or ""
    ext = _inferir_extensao(filename, mime_type)

    temp_dir = Path(os.getenv("HIVEE_MEDIA_TMP", "/tmp/hivee_media")) / telefone
    temp_dir.mkdir(parents=True, exist_ok=True)
    arquivo = temp_dir / f"{tipo}_{int(time.time())}.{ext}"

    try:
        response = requests.get(media_url, headers=_headers(), timeout=30)
        response.raise_for_status()
        arquivo.write_bytes(response.content)
        return str(arquivo)
    except Exception:
        logger.exception("Falha ao baixar midia WAHA para %s", telefone)
    return None


def _inferir_extensao(filename: str, mime_type: str) -> str:
    if "." in filename:
        return filename.rsplit(".", 1)[-1]
    if "/" in mime_type:
        subtype = mime_type.split("/", 1)[1]
        return "jpg" if subtype == "jpeg" else subtype.split(";")[0]
    return "bin"
