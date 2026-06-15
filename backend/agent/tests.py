import logging
import time
from datetime import timedelta
from unittest.mock import MagicMock, patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from catalog.models import Category, FAQArticle, Provider, SupportCategory, SupportTicket

from .models import Chat, ChatLead, ChatMessage

logger = logging.getLogger(__name__)


class AgentModelsTest(TestCase):
    def test_criar_lead(self):
        lead = ChatLead.objects.create(telefone="5511999999999", nome_wpp="Teste", canal_origem="whatsapp")
        self.assertEqual(str(lead), "Teste (WhatsApp)")

    def test_criar_chat(self):
        lead = ChatLead.objects.create(telefone="5511999999999", canal_origem="whatsapp")
        chat = Chat.objects.create(lead=lead, canal="whatsapp")
        self.assertEqual(chat.status, "active")

    def test_criar_mensagem(self):
        lead = ChatLead.objects.create(telefone="5511999999999", canal_origem="whatsapp")
        chat = Chat.objects.create(lead=lead, canal="whatsapp")
        msg = ChatMessage.objects.create(chat=chat, role="user", content="Ola")
        self.assertTrue("Ola" in msg.content)


class AgentBufferTest(TestCase):
    def test_push_acumula_e_flush(self):
        from .buffer import _buffer, push

        push("5511999999999", "quero um eletricista")
        push("5511999999999", "em sao paulo")
        self.assertIn("5511999999999", _buffer)
        self.assertEqual(len(_buffer["5511999999999"]["mensagens"]), 2)
        _buffer["5511999999999"]["timer"].cancel()
        _buffer.clear()

    @patch("agent.core.processar_mensagem")
    def test_push_usa_debounce_e_junta_mensagens(self, mock_processar):
        from .buffer import _buffer, push

        push("5511222222222", "preciso de encanador", espera=0.05)
        push("5511222222222", "em sao paulo", espera=0.05)
        time.sleep(0.15)

        mock_processar.assert_called_once_with("5511222222222", "preciso de encanador\nem sao paulo")
        self.assertNotIn("5511222222222", _buffer)


class AgentCoreTest(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name="Eletrica", slug="eletrica", icon="Zap")
        Provider.objects.create(
            name="Joao Eletricista",
            slug="joao-eletricista",
            headline="Eletricista residencial",
            category=self.category,
            city="Sao Paulo",
            state="SP",
            status="approved",
        )

    @patch("agent.core.get_openai_client")
    @patch("agent.core.buscar_rag_para_agente")
    @patch("agent.formatador.send_presence")
    @patch("agent.formatador.enviar_whatsapp")
    def test_fluxo_completo(self, mock_enviar, mock_presence, mock_rag, mock_get_client):
        lead = ChatLead.objects.create(telefone="5511999999999", nome_wpp="Teste", canal_origem="whatsapp")

        mock_rag.return_value = "Contexto de teste"
        message = MagicMock()
        message.tool_calls = None
        message.content = "Recomendo o eletricista Joao! Acesse hivee.app/prestador/joao-eletricista/"
        mock_get_client.return_value.chat.completions.create.return_value.choices[0].message = message

        from .core import processar_mensagem

        processar_mensagem("5511999999999", "preciso de um eletricista em Sao Paulo")

        chat = Chat.objects.get(lead=lead)
        msgs = ChatMessage.objects.filter(chat=chat).order_by("created_at")
        self.assertEqual(msgs.count(), 2)
        self.assertEqual(msgs[0].role, "user")
        self.assertEqual(msgs[1].role, "bot")
        self.assertIn("eletricista", msgs[1].content)
        mock_enviar.assert_called_once()

    @patch("agent.formatador.send_presence")
    @patch("agent.formatador.enviar_whatsapp")
    def test_pergunta_cidade_antes_de_recomendar(self, mock_enviar, mock_presence):
        lead = ChatLead.objects.create(telefone="5511888888888", nome_wpp="Teste", canal_origem="whatsapp")

        from .core import processar_mensagem

        processar_mensagem("5511888888888", "preciso de um eletricista")

        chat = Chat.objects.get(lead=lead)
        msgs = ChatMessage.objects.filter(chat=chat).order_by("created_at")
        self.assertEqual(msgs.count(), 2)
        self.assertIn("qual cidade", msgs[1].content.lower())
        mock_enviar.assert_called_once()

    @patch("agent.core.get_openai_client")
    @patch("agent.core.buscar_rag_para_agente")
    @patch("agent.formatador.send_presence")
    @patch("agent.formatador.enviar_whatsapp")
    def test_sem_prestador_na_cidade_sugere_outra_cidade(
        self, mock_enviar, mock_presence, mock_rag, mock_get_client
    ):
        lead = ChatLead.objects.create(telefone="5511777777777", nome_wpp="Teste", canal_origem="whatsapp")
        encanamento = Category.objects.create(name="Encanamento", slug="encanamento", icon="Wrench")
        Provider.objects.create(
            name="Ana Encanadora",
            slug="ana-encanadora",
            headline="Reparos hidraulicos",
            category=encanamento,
            city="Sao Paulo",
            state="SP",
            status="approved",
        )
        Provider.objects.create(
            name="Bia Eletricista",
            slug="bia-eletricista",
            headline="Instalacoes eletricas",
            category=self.category,
            city="Florianopolis",
            state="SC",
            status="approved",
        )

        mock_rag.return_value = "RAG desativado"
        tool_call = MagicMock()
        tool_call.id = "tool_1"
        tool_call.function.name = "buscar_prestadores"
        tool_call.function.arguments = '{"query": "encanador", "categoria": "Encanamento"}'
        message = MagicMock()
        message.tool_calls = [tool_call]
        message.content = None
        mock_get_client.return_value.chat.completions.create.return_value.choices[0].message = message

        from .core import processar_mensagem

        processar_mensagem("5511777777777", "preciso de um encanador em Florianopolis")

        chat = Chat.objects.get(lead=lead)
        resposta = ChatMessage.objects.filter(chat=chat, role="bot").latest("created_at").content
        self.assertIn("não encontrei encanador", resposta.lower())
        self.assertIn("Sao Paulo", resposta)
        self.assertTrue(resposta.endswith("?"))

    @patch("agent.core.formatar_e_enviar")
    def test_intencao_cadastro_sem_usuario_direciona_para_cadastro(self, mock_send):
        lead = ChatLead.objects.create(telefone="5511444444444", canal_origem="whatsapp")

        from .core import processar_mensagem

        processar_mensagem(lead.telefone, "nao tenho cadastro")

        chat = Chat.objects.get(lead=lead)
        resposta = ChatMessage.objects.filter(chat=chat, role="bot").latest("created_at").content
        self.assertIn("Vee", resposta)
        self.assertIn("https://hivee.app/cadastrar", resposta)
        self.assertTrue(resposta.endswith("?"))
        mock_send.assert_called_once()

    @patch("agent.core.formatar_e_enviar")
    def test_intencao_prestador_logado_direciona_para_fluxo_prestador(self, mock_send):
        user = get_user_model().objects.create_user(
            username="prestador@hivee.dev",
            email="prestador@hivee.dev",
            password="x12345",
            first_name="Prestador",
        )
        lead = ChatLead.objects.create(telefone=f"site_user_{user.id}", canal_origem="site")

        from .core import processar_mensagem

        processar_mensagem(lead.telefone, "quero ser prestador")

        chat = Chat.objects.get(lead=lead)
        resposta = ChatMessage.objects.filter(chat=chat, role="bot").latest("created_at").content
        self.assertIn("https://hivee.app/sou-prestador", resposta)
        self.assertTrue(resposta.endswith("?"))
        mock_send.assert_called_once()

    @patch("agent.core.formatar_e_enviar")
    def test_intencao_ajuda_responde_com_artigo_publicado(self, mock_send):
        categoria = SupportCategory.objects.create(name="Pagamento", slug="pagamento", icon="CreditCard")
        FAQArticle.objects.create(
            category=categoria,
            question="Como funciona o pagamento?",
            slug="como-funciona-pagamento",
            answer="O pagamento deve ser combinado com o profissional antes do servico.",
            is_published=True,
        )
        lead = ChatLead.objects.create(telefone="5511333333333", canal_origem="whatsapp")

        from .core import processar_mensagem

        processar_mensagem(lead.telefone, "como funciona pagamento")

        chat = Chat.objects.get(lead=lead)
        resposta = ChatMessage.objects.filter(chat=chat, role="bot").latest("created_at").content
        self.assertIn("https://hivee.app/ajuda/como-funciona-pagamento", resposta)
        self.assertTrue(resposta.endswith("?"))
        mock_send.assert_called_once()

    @patch("agent.core._notificar_staff_ticket")
    @patch("agent.core.formatar_e_enviar")
    def test_intencao_suporte_cria_ticket_para_usuario_site(self, mock_send, mock_notify):
        user = get_user_model().objects.create_user(
            username="cliente@hivee.dev",
            email="cliente@hivee.dev",
            password="x12345",
            first_name="Cliente",
        )
        lead = ChatLead.objects.create(telefone=f"site_user_{user.id}", canal_origem="site")

        from .core import processar_mensagem

        processar_mensagem(lead.telefone, "quero abrir um ticket sobre meu cadastro")

        ticket = SupportTicket.objects.get(user=user)
        self.assertEqual(ticket.status, SupportTicket.Status.OPEN)
        self.assertIn("[Chat IA]", ticket.subject)
        chat = Chat.objects.get(lead=lead)
        resposta = ChatMessage.objects.filter(chat=chat, role="bot").latest("created_at").content
        self.assertIn("ticket", resposta.lower())
        self.assertTrue(resposta.endswith("?"))
        mock_notify.assert_called_once_with(ticket)
        mock_send.assert_called_once()

    @patch("agent.core._notificar_staff_ticket")
    @patch("agent.core.formatar_e_enviar")
    def test_intencao_suporte_reaproveita_ticket_aberto(self, mock_send, mock_notify):
        user = get_user_model().objects.create_user(
            username="cliente2@hivee.dev",
            email="cliente2@hivee.dev",
            password="x12345",
            first_name="Cliente",
        )
        lead = ChatLead.objects.create(telefone=f"site_user_{user.id}", canal_origem="site")

        from .core import processar_mensagem

        processar_mensagem(lead.telefone, "quero abrir um ticket")
        processar_mensagem(lead.telefone, "quero abrir outro ticket")

        self.assertEqual(SupportTicket.objects.filter(user=user).count(), 1)
        resposta = ChatMessage.objects.filter(chat__lead=lead, role="bot").latest("created_at").content
        ticket = SupportTicket.objects.get(user=user)
        self.assertIn(f"https://hivee.app/suporte/tickets/{ticket.id}", resposta)
        self.assertTrue(resposta.endswith("?"))
        mock_notify.assert_called_once_with(ticket)
        self.assertEqual(mock_send.call_count, 2)

    @patch("agent.core.enviar_provider_cards_site")
    @patch("agent.core.formatar_e_enviar")
    def test_contexto_de_perfil_tem_prioridade_sobre_historico_antigo(self, mock_send, mock_cards):
        user = get_user_model().objects.create_user(
            username="perfil@hivee.dev",
            email="perfil@hivee.dev",
            password="x12345",
            first_name="Perfil",
        )
        jardinagem = Category.objects.create(name="Jardinagem", slug="jardinagem", icon="Sprout")
        Provider.objects.create(
            name="Carlos Eduardo Viana",
            slug="carlos-eduardo-viana-167",
            headline="Manutencao de jardins",
            category=jardinagem,
            city="Belo Horizonte",
            state="MG",
            status="approved",
            rating=5,
            reviews_count=270,
            hourly_rate=90,
        )
        lead = ChatLead.objects.create(telefone=f"site_user_{user.id}", canal_origem="site")
        chat = Chat.objects.create(lead=lead, canal="site")
        ChatMessage.objects.create(chat=chat, role="user", content="preciso de eletricista em Florianopolis")
        ChatMessage.objects.create(chat=chat, role="bot", content="Quer ver eletricistas em Florianopolis?")

        from .core import processar_mensagem

        processar_mensagem(
            lead.telefone,
            (
                "Tenho interesse em conversar com o prestador Carlos Eduardo Viana. "
                "Perfil: /prestador/carlos-eduardo-viana-167. Categoria: Jardinagem. "
                "Servico: Manutencao de jardins. Cidade: Belo Horizonte."
            ),
        )

        resposta = ChatMessage.objects.filter(chat=chat, role="bot").latest("created_at").content
        self.assertIn("Carlos Eduardo Viana", resposta)
        self.assertIn("/prestador/carlos-eduardo-viana-167", resposta)
        self.assertIn("Belo Horizonte", resposta)
        self.assertNotIn("eletricista", resposta.lower())
        self.assertNotIn("Florianopolis", resposta)
        mock_send.assert_called_once()
        mock_cards.assert_called_once()


class AgentToolsTest(TestCase):
    def test_buscar_prestadores_sem_resultado(self):
        from .tools import buscar_prestadores

        resultado = buscar_prestadores(query="xyz123naoexiste")
        self.assertEqual(resultado, [])


class AgentFollowupTest(TestCase):
    @patch("agent.followup.enviar_whatsapp")
    def test_followup_quando_ultima_mensagem_eh_bot(self, mock_enviar):
        from .followup import verificar_followup

        lead = ChatLead.objects.create(telefone="5511666666666", nome_wpp="Teste", canal_origem="whatsapp")
        chat = Chat.objects.create(lead=lead, canal="whatsapp")
        ChatMessage.objects.create(chat=chat, role="user", content="quero eletricista")
        ChatMessage.objects.create(chat=chat, role="bot", content="Quer ver esse perfil?")
        Chat.objects.filter(pk=chat.pk).update(updated_at=timezone.now() - timedelta(hours=5))

        verificar_followup()

        mock_enviar.assert_called_once()
        self.assertTrue(ChatMessage.objects.filter(chat=chat, content__startswith="[Follow-up]").exists())

    @patch("agent.followup.enviar_whatsapp")
    def test_nao_envia_followup_se_usuario_respondeu_por_ultimo(self, mock_enviar):
        from .followup import verificar_followup

        lead = ChatLead.objects.create(telefone="5511555555555", nome_wpp="Teste", canal_origem="whatsapp")
        chat = Chat.objects.create(lead=lead, canal="whatsapp")
        ChatMessage.objects.create(chat=chat, role="bot", content="Quer ver esse perfil?")
        ChatMessage.objects.create(chat=chat, role="user", content="sim")
        Chat.objects.filter(pk=chat.pk).update(updated_at=timezone.now() - timedelta(hours=5))

        verificar_followup()

        mock_enviar.assert_not_called()


class AgentSiteMediaTest(TestCase):
    @patch("agent.consumers.analisar_imagem")
    def test_midia_site_imagem_vira_conteudo_analisado(self, mock_analisar):
        from .consumers import _conteudo_midia_site

        mock_analisar.return_value = "foto analisada"
        content = _conteudo_midia_site(
            "site_user_1",
            "minha pia",
            {
                "name": "pia.png",
                "mime_type": "image/png",
                "data": "iVBORw0KGgo=",
            },
        )

        self.assertEqual(content, "foto analisada")
        mock_analisar.assert_called_once()

    @patch("agent.consumers.transcrever_audio")
    def test_midia_site_audio_vira_transcricao(self, mock_transcrever):
        from .consumers import _conteudo_midia_site

        mock_transcrever.return_value = "preciso de encanador"
        content = _conteudo_midia_site(
            "site_user_1",
            "",
            {
                "name": "audio.webm",
                "mime_type": "audio/webm",
                "data": "AAAA",
            },
        )

        self.assertIn("[Áudio transcrito]: preciso de encanador", content)

    @patch("agent.consumers.transcrever_audio")
    def test_midia_site_audio_vazio_pede_reenvio(self, mock_transcrever):
        from .consumers import _conteudo_midia_site

        mock_transcrever.return_value = ""
        content = _conteudo_midia_site(
            "site_user_1",
            "",
            {
                "name": "audio.webm",
                "mime_type": "audio/webm",
                "data": "AAAA",
            },
        )

        self.assertIn("[Áudio sem fala identificável]", content)

# Create your tests here.
