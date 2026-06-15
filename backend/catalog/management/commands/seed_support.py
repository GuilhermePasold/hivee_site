"""Popula a Central de Ajuda (categorias + artigos da FAQ).

    python manage.py seed_support

Idempotente: usa get_or_create por slug, então rodar de novo não duplica.
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.text import slugify

from catalog.models import FAQArticle, SupportCategory

CATEGORIES = [
    {
        "name": "Cadastro & Conta",
        "icon": "UserCircle",
        "articles": [
            (
                "Como crio minha conta na HIVEE?",
                "Clique em **Criar conta** no topo do site, informe seu nome, e-mail e "
                "uma senha. Você pode adicionar seu CPF para acelerar a verificação. "
                "Pronto: já dá pra buscar profissionais e abrir tickets de suporte.",
            ),
            (
                "Esqueci minha senha, e agora?",
                "Na tela de login, use a opção de recuperação de senha e siga as "
                "instruções enviadas para o seu e-mail cadastrado.",
            ),
            (
                "Como atualizo meus dados (nome, telefone)?",
                "Acesse **Meu perfil** > seus dados podem ser editados ali. O telefone "
                "é importante para receber avisos por WhatsApp.",
            ),
        ],
    },
    {
        "name": "Para Profissionais",
        "icon": "Wrench",
        "articles": [
            (
                "Como me torno um profissional na plataforma?",
                "Em **Sou profissional**, preencha seu perfil (categoria, descrição, "
                "região e valores). Seu cadastro passa por análise da equipe antes de "
                "aparecer nas buscas.",
            ),
            (
                "Por que meu perfil ainda não aparece na busca?",
                "Perfis novos ficam com status *Em análise* até a aprovação da equipe. "
                "Se o CPF não conferir com a Receita Federal, a aprovação fica bloqueada "
                "até a correção.",
            ),
            (
                "Como melhoro meu posicionamento nas recomendações?",
                "Complete o perfil: foto, descrição detalhada, tags de serviço, agenda "
                "de disponibilidade e fotos de trabalhos. Avaliações e proximidade do "
                "cliente também contam pontos.",
            ),
        ],
    },
    {
        "name": "Pagamentos",
        "icon": "CreditCard",
        "articles": [
            (
                "Como funciona o pagamento dos serviços?",
                "O valor e a forma de pagamento são combinados diretamente entre você e "
                "o profissional. Sempre alinhe escopo e preço antes de iniciar o serviço.",
            ),
            (
                "A HIVEE cobra alguma taxa do cliente?",
                "A busca e o contato com profissionais são gratuitos para o cliente. "
                "Qualquer cobrança refere-se ao serviço contratado com o profissional.",
            ),
        ],
    },
    {
        "name": "Disputas & Segurança",
        "icon": "ShieldCheck",
        "articles": [
            (
                "Tive um problema com um profissional. O que faço?",
                "Abra um **ticket de suporte** descrevendo o ocorrido com o máximo de "
                "detalhes (datas, valores, prints). Nossa equipe analisa e media a "
                "situação.",
            ),
            (
                "Como sei se um profissional é confiável?",
                "Procure o selo de verificado, a nota e o número de avaliações no perfil. "
                "O selo indica que o CPF foi conferido na Receita Federal.",
            ),
        ],
    },
    {
        "name": "Usando o Chat IA",
        "icon": "MessageCircle",
        "articles": [
            (
                "Como o assistente virtual me ajuda?",
                "O Chat IA entende o serviço que você precisa e a sua cidade, e "
                "recomenda os melhores profissionais com link direto para o perfil.",
            ),
            (
                "Posso falar com um atendente humano?",
                "Sim. No chat, peça para *falar com um atendente* ou *abrir um ticket* — "
                "o assistente cria um ticket de suporte e nossa equipe assume a conversa. "
                "É preciso estar logado na sua conta.",
            ),
        ],
    },
]


class Command(BaseCommand):
    help = "Popula a Central de Ajuda com categorias e artigos da FAQ."

    @transaction.atomic
    def handle(self, *args, **options):
        cat_count = 0
        art_count = 0
        for order, cat in enumerate(CATEGORIES):
            category, created = SupportCategory.objects.get_or_create(
                slug=slugify(cat["name"]),
                defaults={"name": cat["name"], "icon": cat["icon"], "order": order},
            )
            if created:
                cat_count += 1
            for art_order, (question, answer) in enumerate(cat["articles"]):
                slug = slugify(question)[:320]
                _, art_created = FAQArticle.objects.get_or_create(
                    slug=slug,
                    defaults={
                        "category": category,
                        "question": question,
                        "answer": answer,
                        "is_published": True,
                        "order": art_order,
                    },
                )
                if art_created:
                    art_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Central de Ajuda populada: +{cat_count} categoria(s), +{art_count} artigo(s)."
            )
        )
