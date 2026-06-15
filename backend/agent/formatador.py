import json
import logging
import time

from .openai_client import get_openai_client
from .waha import enviar_whatsapp, send_presence

logger = logging.getLogger(__name__)
DELAY_ENTRE_BLOCOS_WHATSAPP = 6


def formatar_e_enviar(lead, chat, resposta_bruta: str):
    logger.info("formatar_e_enviar[%s] inicio | %d chars", lead.telefone, len(resposta_bruta))
    blocos = [resposta_bruta] if lead.canal_origem == "site" else _dividir_em_blocos(resposta_bruta)
    logger.info("Resposta dividida em %d blocos", len(blocos))

    for index, bloco in enumerate(blocos):
        if lead.canal_origem == "whatsapp":
            send_presence(lead.telefone, "typing")
            if index == 0:
                time.sleep(2)

        logger.debug("Enviando bloco %d/%d: %s", index + 1, len(blocos), bloco[:60])

        if lead.canal_origem == "whatsapp":
            enviar_whatsapp(lead.telefone, bloco)
        else:
            enviar_site(lead.telefone, bloco, typing=False)

        if lead.canal_origem == "whatsapp" and index < len(blocos) - 1:
            logger.debug("Aguardando %ds antes do prox bloco", DELAY_ENTRE_BLOCOS_WHATSAPP)
            time.sleep(DELAY_ENTRE_BLOCOS_WHATSAPP)

    if lead.canal_origem == "whatsapp":
        send_presence(lead.telefone, "paused")
    logger.info("formatar_e_enviar[%s] concluido", lead.telefone)


def enviar_site(telefone: str, conteudo: str, typing: bool = False):
    from asgiref.sync import async_to_sync
    from channels.layers import get_channel_layer

    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f"chat_{telefone}",
        {"type": "bot_message", "content": conteudo, "typing": typing},
    )


def enviar_provider_cards_site(telefone: str, providers: list[dict]):
    if not providers:
        return

    from asgiref.sync import async_to_sync
    from channels.layers import get_channel_layer

    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f"chat_{telefone}",
        {"type": "provider_cards", "providers": providers},
    )


def _dividir_em_blocos(texto: str) -> list[str]:
    if len(texto) < 200:
        return [texto]
    try:
        response = get_openai_client().chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "Divida o texto abaixo em blocos naturais de ate 200 caracteres cada. Responda apenas JSON com uma chave blocos.",
                },
                {"role": "user", "content": texto},
            ],
            response_format={"type": "json_object"},
            max_tokens=500,
        )
        _log_usage("formatador.dividir_blocos", response)
        parsed = json.loads(response.choices[0].message.content)
        blocos = parsed.get("blocos") if isinstance(parsed, dict) else parsed
        if isinstance(blocos, list) and len(blocos) > 1:
            return [str(bloco) for bloco in blocos if str(bloco).strip()]
    except Exception:
        logger.warning("Falha ao dividir blocos via GPT, fallback para paragrafos", exc_info=True)
    paragrafos = [p.strip() for p in texto.split("\n\n") if p.strip()]
    return paragrafos if len(paragrafos) > 1 else [texto]


def _log_usage(label: str, response):
    usage = getattr(response, "usage", None)
    if usage is None:
        return
    logger.info(
        "OpenAI tokens[%s] prompt=%s completion=%s total=%s",
        label,
        getattr(usage, "prompt_tokens", None),
        getattr(usage, "completion_tokens", None),
        getattr(usage, "total_tokens", None),
    )
