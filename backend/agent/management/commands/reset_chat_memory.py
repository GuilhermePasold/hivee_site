from django.core.management.base import BaseCommand

from agent.models import Chat, ChatMessage


class Command(BaseCommand):
    help = "Remove conversas e mensagens do agente, mantendo os leads cadastrados."

    def add_arguments(self, parser):
        parser.add_argument(
            "--yes",
            action="store_true",
            help="Confirma a limpeza sem prompt interativo.",
        )

    def handle(self, *args, **options):
        if not options["yes"]:
            self.stdout.write("Use --yes para confirmar a limpeza da memoria de chat.")
            return

        mensagens = ChatMessage.objects.count()
        chats = Chat.objects.count()
        ChatMessage.objects.all().delete()
        Chat.objects.all().delete()
        self.stdout.write(
            self.style.SUCCESS(
                f"Memoria de chat limpa: {chats} chats e {mensagens} mensagens removidos."
            )
        )
