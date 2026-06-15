import logging
import time

from django.core.management.base import BaseCommand

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Simula o recebimento de uma mensagem para testar o fluxo completo do agente"

    def add_arguments(self, parser):
        parser.add_argument("--telefone", required=True)
        parser.add_argument("--mensagem", required=True)
        parser.add_argument("--canal", default="whatsapp", choices=["whatsapp", "site"])

    def handle(self, *args, **options):
        telefone = options["telefone"]
        mensagem = options["mensagem"]
        canal = options["canal"]

        from agent.buffer import TEMPO_ESPERA, push
        from agent.models import ChatLead

        lead, created = ChatLead.objects.get_or_create(
            telefone=telefone,
            defaults={"nome_wpp": "Teste Simulacao", "canal_origem": canal},
        )
        if created:
            logger.info("Lead criado: %s", lead)

        push(telefone, mensagem)

        self.stdout.write(
            self.style.SUCCESS(
                f"Mensagem enfileirada para {telefone}. "
                f"Aguardando {TEMPO_ESPERA + 1}s para o processamento do buffer."
            )
        )
        time.sleep(TEMPO_ESPERA + 1)
