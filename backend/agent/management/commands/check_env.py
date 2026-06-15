import logging
import os
import sys

from django.core.management.base import BaseCommand

logger = logging.getLogger(__name__)

CORE_REQUIRED = {
    "OPENAI_API_KEY": "OpenAI - chamadas do agente",
}

RAG_REQUIRED = {
    "SUPABASE_URL": "Supabase - conexao com o Vector Store do RAG",
    "SUPABASE_SERVICE_KEY": "Supabase - chave de acesso ao Vector Store do RAG",
}

WHATSAPP_REQUIRED = {
    "WAHA_API_URL": "WAHA - envio de WhatsApp",
    "WAHA_SESSION": "WAHA - nome da sessao",
}


class Command(BaseCommand):
    help = "Verifica se todas as variaveis de ambiente necessarias estao configuradas"

    def handle(self, *args, **options):
        missing = []
        missing.extend(_missing(CORE_REQUIRED))

        rag_enabled = _truthy(os.getenv("RAG_ENABLED", "False"))
        whatsapp_enabled = _truthy(os.getenv("WHATSAPP_ENABLED", "False"))

        if rag_enabled:
            missing.extend(_missing(RAG_REQUIRED))
        if whatsapp_enabled:
            missing.extend(_missing(WHATSAPP_REQUIRED))

        if missing:
            self.stdout.write(self.style.ERROR("Variaveis de ambiente faltando:"))
            for item in missing:
                self.stdout.write(item)
            logger.warning("Variaveis faltando: %s", ", ".join(missing))
            sys.exit(1)

        logger.info("Ambiente configurado. RAG=%s WhatsApp=%s", rag_enabled, whatsapp_enabled)
        self.stdout.write(self.style.SUCCESS("Ambiente minimo configurado"))
        self.stdout.write(f"RAG_ENABLED={rag_enabled}")
        self.stdout.write(f"WHATSAPP_ENABLED={whatsapp_enabled}")


def _truthy(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "on", "sim"}


def _missing(required: dict[str, str]) -> list[str]:
    return [f"  - {var} ({desc})" for var, desc in required.items() if not os.getenv(var)]
