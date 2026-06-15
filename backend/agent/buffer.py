import logging
import os
import threading
import time

logger = logging.getLogger(__name__)

_buffer: dict[str, dict] = {}
_lock = threading.Lock()
TEMPO_ESPERA_WHATSAPP = float(os.getenv("AGENT_BUFFER_WHATSAPP_SECONDS", "8"))
TEMPO_ESPERA_SITE = float(os.getenv("AGENT_BUFFER_SITE_SECONDS", "1.5"))
TEMPO_ESPERA = TEMPO_ESPERA_WHATSAPP


def push(telefone: str, conteudo: str, espera: float | None = None):
    """Acumula mensagem e reagenda processamento apos a ultima mensagem."""
    tempo_espera = TEMPO_ESPERA if espera is None else espera
    with _lock:
        if telefone not in _buffer:
            _buffer[telefone] = {"mensagens": [], "timer": None, "inicio": time.time()}

        buf = _buffer[telefone]
        buf["mensagens"].append(conteudo)
        buf["inicio"] = time.time()

        if buf["timer"] is not None:
            buf["timer"].cancel()

        timer = threading.Timer(tempo_espera, _flush, args=[telefone])
        timer.daemon = True
        buf["timer"] = timer
        timer.start()
        logger.debug(
            "Buffer[%s] acumulou %d mensagens | flush em %.1fs",
            telefone,
            len(buf["mensagens"]),
            tempo_espera,
        )


def _flush(telefone: str):
    with _lock:
        buf = _buffer.pop(telefone, None)

    if buf is None or not buf["mensagens"]:
        logger.debug("Buffer[%s] flush vazio, ignorando", telefone)
        return

    vistos = set()
    unicos = []
    for msg in buf["mensagens"]:
        if msg not in vistos:
            vistos.add(msg)
            unicos.append(msg)

    mensagem_completa = "\n".join(unicos)
    logger.info(
        "Buffer[%s] flush com %d msgs unicas | total=%d | conteudo=%s",
        telefone,
        len(unicos),
        len(buf["mensagens"]),
        mensagem_completa[:80],
    )
    from .core import processar_mensagem

    processar_mensagem(telefone, mensagem_completa)
