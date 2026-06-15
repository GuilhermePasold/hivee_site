import logging

from .openai_client import get_openai_client

logger = logging.getLogger(__name__)


def transcrever_audio(caminho_arquivo: str) -> str:
    with open(caminho_arquivo, "rb") as file_obj:
        transcript = get_openai_client().audio.transcriptions.create(
            model="whisper-1",
            file=file_obj,
            language="pt",
        )
    logger.info("Audio transcrito: %s", caminho_arquivo)
    return transcript.text
