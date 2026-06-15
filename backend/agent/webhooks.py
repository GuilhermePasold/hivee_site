import logging
import re

from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import JSONParser
from rest_framework.response import Response

from .audio import transcrever_audio
from .buffer import push
from .models import ChatLead
from .vision import analisar_imagem
from .waha import baixar_midia, send_seen

logger = logging.getLogger(__name__)


def limpar_telefone(remote_jid: str) -> str:
    return re.sub(r"@.*$", "", remote_jid)


def extrair_conteudo(payload: dict, telefone: str) -> str:
    body = payload.get("body", "")
    media = payload.get("media") or {}
    mime_type = media.get("mimetype", "")

    if media and mime_type.startswith("audio/"):
        caminho = baixar_midia(media, telefone, "audio")
        if caminho:
            return f"[Audio transcrito]: {transcrever_audio(caminho)}"
        return "[Audio nao pode ser processado]"

    if media and mime_type.startswith("image/"):
        caminho = baixar_midia(media, telefone, "image")
        if caminho:
            return analisar_imagem(caminho, body)
        return body or "[Imagem sem descricao]"

    if body:
        return body

    logger.debug("Mensagem WAHA nao reconhecida payload=%s", str(payload)[:120])
    return "[Mensagem nao reconhecida]"


@api_view(["POST"])
@parser_classes([JSONParser])
def waha_webhook(request):
    data = request.data
    payload = data.get("payload", data.get("body", data))
    event = data.get("event", "")

    if event and event != "message":
        logger.debug("Webhook WAHA ignorado: event=%s", event)
        return Response({"status": "ignored", "reason": "evento nao suportado"})

    if payload.get("fromMe"):
        logger.debug("Webhook WAHA ignorado: mensagem propria")
        return Response({"status": "ignored", "reason": "fromMe"})

    chat_id = payload.get("from") or payload.get("chatId") or payload.get("id", "")
    if not chat_id:
        logger.warning("Webhook WAHA ignorado: sem chat id | payload=%s", str(data)[:200])
        return Response({"status": "ignored", "reason": "sem chat id"})

    if "@g.us" in chat_id:
        logger.debug("Webhook WAHA ignorado: grupo %s", chat_id)
        return Response({"status": "ignored", "reason": "grupo"})

    push_name = payload.get("pushName") or payload.get("_data", {}).get("notifyName", "")
    telefone = limpar_telefone(chat_id)

    ChatLead.objects.get_or_create(
        telefone=telefone,
        defaults={"nome_wpp": push_name, "canal_origem": "whatsapp"},
    )

    conteudo = extrair_conteudo(payload, telefone)
    logger.info("Webhook WAHA[%s] | conteudo=%s", telefone, str(conteudo)[:100])
    send_seen(telefone)
    push(telefone, conteudo)

    return Response({"status": "ok"})
