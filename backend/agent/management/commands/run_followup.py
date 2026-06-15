import logging

from django.core.management.base import BaseCommand

from agent.followup import verificar_followup

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Verifica chats parados e envia follow-up"

    def handle(self, *args, **options):
        verificar_followup()
        logger.info("Follow-up concluido")
        self.stdout.write(self.style.SUCCESS("Follow-up concluido"))
