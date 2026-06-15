import base64
import logging

from .openai_client import get_openai_client

logger = logging.getLogger(__name__)


def analisar_imagem(caminho_arquivo: str, caption: str = "") -> str:
    with open(caminho_arquivo, "rb") as file_obj:
        b64 = base64.b64encode(file_obj.read()).decode("utf-8")

    response = get_openai_client().chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Descreva esta imagem em portugues. Se for print, transcreva."},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}},
                ],
            }
        ],
        max_tokens=300,
    )
    descricao = response.choices[0].message.content
    logger.info("Imagem analisada: %s", caminho_arquivo)
    return f"{caption}\n[Imagem: {descricao}]" if caption else f"[Imagem: {descricao}]"
