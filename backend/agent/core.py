import json
import logging
import re
import unicodedata

from django.utils import timezone

from catalog.models import Provider

from .formatador import enviar_provider_cards_site, enviar_site, formatar_e_enviar
from .models import Chat, ChatLead, ChatMessage
from .openai_client import get_openai_client
from .rag import buscar_rag_para_agente
from .tools import buscar_prestadores, montar_provider_card
from .waha import enviar_whatsapp

logger = logging.getLogger(__name__)

MODELO_CHAT = "gpt-4.1-mini"

AGENT_POLICY = {
    "identity": {
        "name": "Vee",
        "role": "assistente comercial consultiva da HIVEE",
        "mission": "ajudar o usuario a encontrar, comparar e dar o proximo passo com um prestador adequado",
        "language": "pt-BR",
        "tone": ["humano", "calmo", "objetivo", "prestativo", "sem pressao"],
    },
    "sales_strategy": {
        "framework": "venda consultiva",
        "principles": [
            "descobrir necessidade antes de recomendar",
            "fazer uma pergunta por vez",
            "reduzir friccao com opcoes claras",
            "tratar objecoes com empatia e alternativa concreta",
            "sempre sugerir o proximo passo",
        ],
        "qualification_fields": ["servico", "cidade", "urgencia", "tipo_de_imovel", "orcamento_quando_relevante"],
        "next_step_examples": [
            "Quer abrir o perfil desse profissional?",
            "Quer que eu busque opcoes em outra cidade?",
            "Quer comparar por menor preco ou melhor avaliacao?",
            "Quer me mandar uma foto do problema para eu entender melhor?",
        ],
    },
    "hard_rules": [
        "use apenas prestadores fornecidos pelo backend",
        "nunca invente disponibilidade, telefone ou preco",
        "se faltar servico ou cidade, pergunte so esse dado",
        "cidade vem antes de recomendacao",
        "recomende no maximo 2 prestadores por resposta",
        "quando houver 2 bons prestadores, apresente os 2",
        "inclua o link exato do perfil recebido",
        "se nao houver prestador na cidade, diga isso e sugira cidades alternativas",
        "termine sempre com uma pergunta objetiva de proximo passo",
    ],
    "response_shape": {
        "max_paragraphs": 4,
        "avoid": ["textao", "jargao", "promessa exagerada", "listas longas"],
        "include_when_recommending": ["nome", "motivo", "nota ou prova social", "preco se existir", "link"],
    },
}

SYSTEM_PROMPT = json.dumps(AGENT_POLICY, ensure_ascii=False, separators=(",", ":"))

SERVICE_SYNONYMS = {
    "eletrica": {
        "eletrica",
        "eletricista",
        "eletrico",
        "tomada",
        "chuveiro",
        "luz",
        "iluminacao",
        "quadro de luz",
        "curto circuito",
    },
    "encanamento": {
        "encanamento",
        "encanador",
        "hidraulica",
        "hidraulico",
        "vazamento",
        "desentupimento",
        "torneira",
        "cano",
    },
    "pintura": {"pintura", "pintor", "pintar", "parede", "massa corrida"},
    "limpeza": {"limpeza", "faxina", "faxineira", "diarista", "pos obra"},
    "jardinagem": {
        "jardinagem",
        "jardineiro",
        "jardim",
        "jardins",
        "manutencao de jardim",
        "manutencao de jardins",
        "corte de grama",
        "adubacao",
        "plantio",
        "grama",
        "poda",
        "paisagismo",
    },
    "beleza": {"beleza", "cabelo", "manicure", "maquiagem", "sobrancelha"},
    "aulas": {"aulas", "professor", "reforco", "enem", "matematica", "ingles"},
    "tecnologia": {"tecnologia", "ti", "tecnico", "computador", "notebook", "wifi", "site"},
    "fotografia": {"fotografia", "fotografo", "foto", "ensaio"},
    "eventos": {"eventos", "festa", "dj", "buffet", "decoracao", "garcom"},
    "pets": {"pets", "pet", "cachorro", "gato", "banho", "tosa", "adestramento"},
}

# Frases que indicam, de forma inequivoca, que o usuario quer suporte HUMANO da
# plataforma (nao a busca por prestador). Sao multi-palavra de proposito: evita
# sequestrar o fluxo normal por causa de termos soltos como "ajuda" ou "problema".
_INTENCAO_SUPORTE = (
    "atendente",  # palavra inequivoca de atendimento humano
    "falar com um humano",
    "falar com humano",
    "falar com uma pessoa",
    "falar com alguem da equipe",
    "quero um humano",
    "suporte humano",
    "suporte da hivee",
    "abrir um ticket",
    "abrir outro ticket",
    "abrir ticket",
    "criar ticket",
    "novo ticket",
    "ticket de suporte",
    "meu ticket",
    "fazer uma reclamacao",
    "quero reclamar",
    "registrar uma reclamacao",
)

_INTENCAO_PRESTADOR = (
    "quero ser prestador",
    "ser prestador",
    "sou prestador",
    "trabalhar na hivee",
    "trabalhar com voces",
    "oferecer servico",
    "oferecer meus servicos",
    "cadastrar como prestador",
    "cadastro de prestador",
    "virar prestador",
    "me tornar prestador",
)

_INTENCAO_CADASTRO = (
    "nao tenho cadastro",
    "não tenho cadastro",
    "criar cadastro",
    "criar conta",
    "fazer cadastro",
    "me cadastrar",
    "cadastro",
    "registrar conta",
)

_INTENCAO_AJUDA = (
    "como funciona",
    "tenho uma duvida",
    "tenho uma dúvida",
    "duvida",
    "dúvida",
    "faq",
    "central de ajuda",
    "pagamento",
    "garantia",
    "seguranca",
    "segurança",
    "cpf",
)


def _detecta_intencao_suporte(mensagem: str) -> bool:
    """True quando a mensagem pede explicitamente atendimento humano/suporte."""
    texto = _normalizar_texto(mensagem)
    return any(frase in texto for frase in _INTENCAO_SUPORTE)


def _detecta_intencao(frases: tuple[str, ...], mensagem: str) -> bool:
    texto = _normalizar_texto(mensagem)
    return any(_normalizar_texto(frase) in texto for frase in frases)


def processar_mensagem(telefone: str, mensagem_completa: str):
    logger.info("processar_mensagem[%s] inicio | msg=%s", telefone, mensagem_completa[:100])
    lead = None
    chat = None
    try:
        try:
            lead = ChatLead.objects.get(telefone=telefone)
        except ChatLead.DoesNotExist:
            logger.warning("Lead nao encontrado para %s, ignorando", telefone)
            return

        chat, _ = Chat.objects.get_or_create(
            lead=lead,
            canal=lead.canal_origem,
            defaults={"status": "active"},
        )

        ChatMessage.objects.create(chat=chat, role="user", content=mensagem_completa)

        # Escalonamento para suporte humano: se o usuario pedir atendente/abrir
        # ticket, abrimos um SupportTicket em vez de seguir para a recomendacao.
        if _detecta_intencao_suporte(mensagem_completa):
            _escalar_para_suporte(lead, chat, mensagem_completa)
            logger.info("processar_mensagem[%s] escalonado para suporte humano", telefone)
            return
        if _detecta_intencao(_INTENCAO_PRESTADOR, mensagem_completa):
            _responder_intencao_prestador(lead, chat)
            logger.info("processar_mensagem[%s] orientado para cadastro de prestador", telefone)
            return
        if _detecta_intencao(_INTENCAO_CADASTRO, mensagem_completa):
            _responder_intencao_cadastro(lead, chat)
            logger.info("processar_mensagem[%s] orientado para cadastro/login", telefone)
            return
        if _detecta_intencao(_INTENCAO_AJUDA, mensagem_completa):
            _responder_duvida_geral(lead, chat, mensagem_completa)
            logger.info("processar_mensagem[%s] orientado para ajuda/FAQ", telefone)
            return

        provider_slug = _detectar_slug_prestador(mensagem_completa)
        if provider_slug:
            provider = Provider.objects.filter(slug=provider_slug, status="approved").select_related("category").first()
            if provider:
                _responder_contexto_prestador(lead, chat, provider)
                logger.info("processar_mensagem[%s] orientado para prestador especifico %s", telefone, provider.slug)
                return

        if _audio_nao_entendido(mensagem_completa):
            _pedir_audio_novamente(lead, chat)
            logger.info("processar_mensagem[%s] pausado aguardando audio/texto compreensivel", telefone)
            return

        cidade_detectada = _detectar_cidade(chat, mensagem_completa)
        servico_detectado = _detectar_servico(chat, mensagem_completa)
        if not servico_detectado:
            _pedir_servico(lead, chat, cidade_detectada)
            logger.info("processar_mensagem[%s] pausado aguardando servico", telefone)
            return

        if not cidade_detectada:
            _pedir_cidade(lead, chat, servico_detectado)
            logger.info("processar_mensagem[%s] pausado aguardando cidade", telefone)
            return

        prestadores_encontrados = buscar_prestadores(
            query=servico_detectado["query"],
            cidade=cidade_detectada,
            categoria=servico_detectado["categoria"],
            limite=2,
        )
        logger.info(
            "Busca direta | cidade=%s servico=%s categoria=%s encontrados=%d",
            cidade_detectada,
            servico_detectado["query"],
            servico_detectado["categoria"],
            len(prestadores_encontrados),
        )

        if not prestadores_encontrados:
            resposta_final = _resposta_sem_prestadores(
                cidade_detectada,
                {
                    "query": servico_detectado["query"],
                    "categoria": servico_detectado["categoria"],
                },
            )
        else:
            resposta_final = _gerar_resposta_recomendacao(
                chat=chat,
                cidade=cidade_detectada,
                servico=servico_detectado,
                prestadores=prestadores_encontrados,
            )

        if not resposta_final:
            logger.warning("OpenAI retornou resposta vazia para %s", telefone)
            resposta_final = "Desculpe, nao consegui processar. Pode repetir?"
        resposta_final = _garantir_pergunta_final(resposta_final)

        ChatMessage.objects.create(chat=chat, role="bot", content=resposta_final)
        _salvar_provider_recomendado(chat, resposta_final)

        chat.updated_at = timezone.now()
        chat.save(update_fields=["updated_at"])

        formatar_e_enviar(lead, chat, resposta_final)
        if lead.canal_origem == "site":
            cards = [montar_provider_card(provider) for provider in prestadores_encontrados[:2]]
            enviar_provider_cards_site(lead.telefone, cards)
        logger.info("processar_mensagem[%s] concluido com sucesso", telefone)
    except Exception:
        logger.exception("processar_mensagem[%s] ERRO nao tratado", telefone)
        _responder_falha(telefone, lead, chat)


def _salvar_provider_recomendado(chat: Chat, resposta_final: str):
    match = re.search(r"hivee\.app/prestador/([^/\s]+)/?", resposta_final)
    if not match:
        return
    from catalog.models import Provider

    try:
        provider = Provider.objects.get(slug=match.group(1))
        chat.provider_recomendado = provider
        chat.save(update_fields=["provider_recomendado"])
        logger.info("Provider recomendado: %s", provider.slug)
    except Provider.DoesNotExist:
        logger.warning("Provider slug %s nao encontrado no banco", match.group(1))


def _role_openai(role: str) -> str:
    if role == "bot":
        return "assistant"
    return role


def _pedir_cidade(lead: ChatLead, chat: Chat, servico: dict | None = None):
    prefixo = _intro_vee(chat)
    if servico:
        resposta = (
            f"{prefixo}Entendi que você precisa de {_servico_label(servico['categoria'])}. "
            "Em qual cidade você quer que eu procure?"
        )
    else:
        resposta = f"{prefixo}Em qual cidade você precisa do serviço?"
    ChatMessage.objects.create(chat=chat, role="bot", content=resposta)
    chat.updated_at = timezone.now()
    chat.save(update_fields=["updated_at"])
    formatar_e_enviar(lead, chat, resposta)


def _pedir_servico(lead: ChatLead, chat: Chat, cidade: str | None):
    prefixo = _intro_vee(chat)
    if cidade:
        resposta = (
            f"{prefixo}Perfeito, vou considerar {cidade}. "
            "Qual serviço você precisa agora? Pode ser elétrica, encanamento, limpeza, pintura ou outro."
        )
    else:
        resposta = (
            f"{prefixo}Me conta qual serviço você precisa e em qual cidade. "
            "Se preferir, pode mandar em áudio ou foto também."
        )
    ChatMessage.objects.create(chat=chat, role="bot", content=resposta)
    chat.updated_at = timezone.now()
    chat.save(update_fields=["updated_at"])
    formatar_e_enviar(lead, chat, resposta)


def _pedir_audio_novamente(lead: ChatLead, chat: Chat):
    prefixo = _intro_vee(chat)
    resposta = (
        f"{prefixo}Recebi seu áudio, mas não consegui entender com segurança. "
        "Pode gravar de novo falando o serviço e a cidade, ou escrever por aqui?"
    )
    ChatMessage.objects.create(chat=chat, role="bot", content=resposta)
    chat.updated_at = timezone.now()
    chat.save(update_fields=["updated_at"])
    formatar_e_enviar(lead, chat, resposta)


def _detectar_slug_prestador(mensagem: str) -> str | None:
    match = re.search(r"/prestador/([a-z0-9-]+)", mensagem or "", flags=re.IGNORECASE)
    return match.group(1).strip().lower() if match else None


def _responder_contexto_prestador(lead: ChatLead, chat: Chat, provider: Provider):
    prefixo = _intro_vee(chat)
    categoria = provider.category.name if provider.category else "serviço"
    cidade = provider.city or "cidade não informada"
    estado = f" - {provider.state}" if provider.state else ""
    preco = f"R$ {provider.hourly_rate:.0f}/h" if provider.hourly_rate is not None else "preço não informado"
    resposta = (
        f"{prefixo}Perfeito, você está falando do perfil de {provider.name}. "
        f"Ele atende {categoria} em {cidade}{estado}, tem nota {float(provider.rating):.1f} "
        f"com {provider.reviews_count} avaliações e cobra {preco}. "
        f"Perfil: /prestador/{provider.slug}. "
        "Quer que eu te ajude a solicitar orçamento com esse profissional ou prefere comparar com outros da mesma cidade?"
    )
    _responder_bot(lead, chat, resposta)
    if lead.canal_origem == "site":
        enviar_provider_cards_site(lead.telefone, [_montar_card_provider_model(provider)])


def _montar_card_provider_model(provider: Provider) -> dict:
    habilidades = provider.skills if isinstance(provider.skills, list) else []
    return montar_provider_card(
        {
            "id": provider.id,
            "nome": provider.name,
            "slug": provider.slug,
            "categoria": provider.category.name if provider.category else "",
            "cidade": provider.city or "",
            "estado": provider.state or "",
            "nota": float(provider.rating),
            "avaliacoes": provider.reviews_count,
            "descricao": provider.headline,
            "avatar_url": provider.avatar_url or (provider.avatar.url if provider.avatar else ""),
            "preco_hora": float(provider.hourly_rate),
            "tempo_resposta": provider.response_time,
            "habilidades": habilidades,
            "link": f"/prestador/{provider.slug}",
        }
    )


def _responder_intencao_prestador(lead: ChatLead, chat: Chat):
    usuario = _resolver_usuario_do_lead(lead)
    prefixo = _intro_vee(chat)
    if usuario is None:
        resposta = (
            f"{prefixo}Para se tornar prestador na HIVEE, primeiro você precisa criar uma conta. "
            "Depois disso, é só preencher seu perfil profissional, serviços, cidade, preço e documentos. "
            "Quer criar sua conta agora em https://hivee.app/cadastrar?"
        )
        _responder_bot(lead, chat, resposta)
        return

    perfil = getattr(usuario, "profile", None)
    status_prestador = getattr(perfil, "provider_status", "") if perfil else ""
    provider = Provider.objects.filter(owner=usuario).order_by("-created_at").first()
    if status_prestador == "approved" and provider:
        resposta = (
            f"{prefixo}Você já tem um perfil de prestador aprovado na HIVEE. "
            f"Seu perfil está aqui: https://hivee.app/prestador/{provider.slug}/. "
            "Quer abrir seu painel para atualizar agenda, fotos ou serviços?"
        )
    elif status_prestador == "pending":
        resposta = (
            f"{prefixo}Seu cadastro de prestador está em análise. "
            "Enquanto isso, vale revisar suas informações, fotos e serviços em https://hivee.app/sou-prestador. "
            "Quer que eu te diga o que costuma deixar um perfil mais forte?"
        )
    elif status_prestador == "rejected":
        resposta = (
            f"{prefixo}Seu cadastro de prestador não foi aprovado na análise anterior. "
            "O melhor caminho é revisar os dados e, se precisar, abrir um ticket para nossa equipe orientar. "
            "Quer que eu abra um ticket de suporte para isso?"
        )
    else:
        resposta = (
            f"{prefixo}Claro! Para vender seus serviços na HIVEE, você começa por aqui: "
            "https://hivee.app/sou-prestador. "
            "Você vai cadastrar serviços, cidade de atendimento, preço, fotos e CPF para análise. "
            "Quer que eu te acompanhe nesse cadastro?"
        )
    _responder_bot(lead, chat, resposta)


def _responder_intencao_cadastro(lead: ChatLead, chat: Chat):
    usuario = _resolver_usuario_do_lead(lead)
    prefixo = _intro_vee(chat)
    if usuario is None:
        resposta = (
            f"{prefixo}Sem problema. Para usar melhor a HIVEE, salvar profissionais, abrir tickets e acompanhar solicitações, "
            "crie sua conta aqui: https://hivee.app/cadastrar. "
            "Você quer se cadastrar como cliente ou como prestador?"
        )
    else:
        resposta = (
            f"{prefixo}Você já está com uma conta ativa na HIVEE. "
            "Se quiser ajustar seus dados, vá em https://hivee.app/minha-conta. "
            "Você quer procurar um profissional ou se cadastrar como prestador?"
        )
    _responder_bot(lead, chat, resposta)


def _responder_duvida_geral(lead: ChatLead, chat: Chat, mensagem: str):
    artigo = _buscar_artigo_ajuda(mensagem)
    prefixo = _intro_vee(chat)
    if artigo:
        resposta = (
            f"{prefixo}Encontrei uma resposta na Central de Ajuda: {artigo.question}\n\n"
            f"{_resumir_texto(artigo.answer, 420)}\n\n"
            f"Você pode ver o artigo completo em https://hivee.app/ajuda/{artigo.slug}. "
            "Isso resolve sua dúvida ou quer que eu abra um ticket para a equipe?"
        )
    else:
        resposta = (
            f"{prefixo}Posso te ajudar com dúvidas sobre cadastro, busca de profissionais, pagamento, segurança, tickets e perfil de prestador. "
            "Você também pode abrir a Central de Ajuda em https://hivee.app/ajuda. "
            "Qual dessas partes você quer resolver agora?"
        )
    _responder_bot(lead, chat, resposta)


def _buscar_artigo_ajuda(mensagem: str):
    from catalog.models import FAQArticle

    termos = [
        termo
        for termo in re.findall(r"[\wÀ-ÿ]+", _normalizar_texto(mensagem))
        if len(termo) > 3 and termo not in {"como", "funciona", "duvida", "dúvida", "ajuda"}
    ]
    artigos = list(FAQArticle.objects.filter(is_published=True).select_related("category"))
    if not artigos:
        return None

    def score(artigo):
        texto = _normalizar_texto(f"{artigo.question} {artigo.answer} {artigo.category.name if artigo.category else ''}")
        return sum(1 for termo in termos if termo in texto)

    artigos.sort(key=score, reverse=True)
    return artigos[0] if score(artigos[0]) > 0 else None


def _resumir_texto(texto: str, limite: int) -> str:
    texto = " ".join((texto or "").split())
    if len(texto) <= limite:
        return texto
    return texto[: limite - 3].rsplit(" ", 1)[0] + "..."


def _intro_vee(chat: Chat) -> str:
    if chat.mensagens.filter(role="bot").exists():
        return ""
    return "Oi! Eu sou a Vee, agente da HIVEE. Vou te ajudar a encontrar o profissional certo. "


def _audio_nao_entendido(mensagem: str) -> bool:
    texto = _normalizar_texto(mensagem)
    return any(
        marcador in texto
        for marcador in (
            "audio sem fala identificavel",
            "audio nao pode ser processado",
            "audio nao pode ser entendido",
            "transcricao vazia",
        )
    )


def _gerar_resposta_recomendacao(
    chat: Chat,
    cidade: str,
    servico: dict,
    prestadores: list[dict],
) -> str:
    contexto_rag = buscar_rag_para_agente(servico["query"])
    logger.debug("RAG contexto: %s", str(contexto_rag)[:120])

    historico = ChatMessage.objects.filter(chat=chat).order_by("-created_at")[:8]
    historico_formatado = [
        {"role": _role_openai(msg.role), "content": msg.content}
        for msg in reversed(historico)
        if _role_openai(msg.role) in {"user", "assistant", "system"}
    ]
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "system",
            "content": (
                "Responda com base exclusivamente nos prestadores fornecidos. "
                "Se houver 2 prestadores, apresente os 2 de forma curta. "
                "Inclua o link de cada perfil e termine com uma pergunta de proximo passo."
            ),
        },
        {
            "role": "system",
            "content": f"Cidade confirmada: {cidade}. Servico detectado: {servico['query']}.",
        },
        {"role": "system", "content": f"Contexto RAG:\n{contexto_rag}"},
        *historico_formatado,
        {
            "role": "user",
            "content": "Prestadores encontrados:\n" + json.dumps(prestadores, ensure_ascii=False),
        },
    ]

    try:
        response = get_openai_client().chat.completions.create(
            model=MODELO_CHAT,
            messages=messages,
            temperature=0.45,
            max_tokens=450,
        )
        _log_usage("core.recomendacao_direta", response)
        return response.choices[0].message.content or ""
    except Exception:
        logger.exception("Falha ao gerar recomendacao via OpenAI; usando fallback deterministico")
        return _resposta_recomendacao_fallback(prestadores)


def _resposta_recomendacao_fallback(prestadores: list[dict]) -> str:
    linhas = ["Encontrei estas opções para você:"]
    for index, provider in enumerate(prestadores[:2], start=1):
        linhas.append(
            (
                f"{index}. {provider['nome']} - {provider['descricao']} em "
                f"{provider['cidade']} ({provider['estado']}), nota {provider['nota']:.1f}. "
                f"Perfil: {provider['link']}"
            )
        )
    linhas.append("Você quer abrir o perfil de algum deles ou buscar mais opções?")
    return "\n\n".join(linhas)


def _resposta_sem_prestadores(cidade: str, args: dict) -> str:
    query = args.get("query") or "esse servico"
    categoria = args.get("categoria")
    servico = _servico_label(categoria or query)
    alternativas = buscar_prestadores(
        query=query,
        categoria=categoria,
        limite=5,
    )
    cidades = []
    cidade_normalizada = _normalizar_texto(cidade)
    for provider in alternativas:
        nome_cidade = provider.get("cidade")
        estado = provider.get("estado")
        if not nome_cidade or _normalizar_texto(nome_cidade) == cidade_normalizada:
            continue
        label = f"{nome_cidade} ({estado})" if estado else nome_cidade
        if label not in cidades:
            cidades.append(label)
        if len(cidades) == 3:
            break

    if cidades:
        opcoes = ", ".join(cidades)
        return (
            f"Infelizmente não encontrei {servico} disponível em {cidade} agora. "
            f"Mas encontrei opções em {opcoes}. Você quer que eu busque em alguma dessas cidades?"
        )
    return (
        f"Infelizmente não encontrei {servico} disponível em {cidade} agora. "
        "Você quer tentar outra cidade ou ajustar o tipo de serviço?"
    )


def _servico_label(valor: str) -> str:
    texto = _normalizar_texto(valor)
    if "encan" in texto or "hidraulic" in texto:
        return "encanador"
    if "eletric" in texto:
        return "eletricista"
    if "pint" in texto:
        return "pintor"
    if "limp" in texto or "faxin" in texto:
        return "profissional de limpeza"
    return valor.strip() or "esse servico"


def _garantir_pergunta_final(resposta: str) -> str:
    resposta = (resposta or "").strip()
    if resposta.endswith("?"):
        return resposta
    return f"{resposta}\n\nQuer que eu siga com esse próximo passo?"


def _detectar_cidade(chat: Chat, mensagem: str) -> str | None:
    cidades = list(
        Provider.objects.filter(status="approved")
        .exclude(city="")
        .values_list("city", flat=True)
        .distinct()
    )
    if not cidades:
        return None

    aliases = {
        "floripa": "Florianopolis",
        "bh": "Belo Horizonte",
        "sampa": "Sao Paulo",
    }

    cidades_por_normalizada = {_normalizar_texto(cidade): cidade for cidade in cidades}

    cidade_atual = _detectar_cidade_em_texto(mensagem, cidades_por_normalizada, aliases)
    if cidade_atual:
        return cidade_atual

    historico = " ".join(
        ChatMessage.objects.filter(chat=chat)
        .order_by("-created_at")
        .values_list("content", flat=True)[:10]
    )
    return _detectar_cidade_em_texto(historico, cidades_por_normalizada, aliases)


def _detectar_cidade_em_texto(
    texto: str,
    cidades_por_normalizada: dict[str, str],
    aliases: dict[str, str],
) -> str | None:
    texto_normalizado = _normalizar_texto(texto)
    for alias, cidade in aliases.items():
        cidade_normalizada = _normalizar_texto(cidade)
        if re.search(rf"\b{re.escape(alias)}\b", texto_normalizado) and cidade_normalizada in cidades_por_normalizada:
            return cidades_por_normalizada[cidade_normalizada]

    for cidade_normalizada, cidade in sorted(
        cidades_por_normalizada.items(), key=lambda item: len(item[0]), reverse=True
    ):
        if re.search(rf"\b{re.escape(cidade_normalizada)}\b", texto_normalizado):
            return cidade
    return None


def _detectar_servico(chat: Chat, mensagem: str) -> dict | None:
    categorias = list(
        Provider.objects.filter(status="approved")
        .select_related("category")
        .values_list("category__name", "category__slug")
        .distinct()
    )
    if not categorias:
        return None

    servico_atual = _detectar_servico_em_texto(mensagem, categorias)
    if servico_atual:
        return servico_atual

    historico = " ".join(
        ChatMessage.objects.filter(chat=chat, role="user")
        .order_by("-created_at")
        .values_list("content", flat=True)[:6]
    )
    return _detectar_servico_em_texto(historico, categorias)


def _detectar_servico_em_texto(texto: str, categorias: list[tuple[str, str]]) -> dict | None:
    texto_normalizado = _normalizar_texto(texto)

    for nome, slug in categorias:
        nome_normalizado = _normalizar_texto(nome)
        slug_normalizado = _normalizar_texto(slug)
        candidatos = {nome_normalizado, slug_normalizado}
        candidatos.update(SERVICE_SYNONYMS.get(slug_normalizado, set()))
        candidatos.update(SERVICE_SYNONYMS.get(nome_normalizado, set()))

        for candidato in sorted(candidatos, key=len, reverse=True):
            candidato_normalizado = _normalizar_texto(candidato)
            if re.search(rf"\b{re.escape(candidato_normalizado)}\b", texto_normalizado):
                return {
                    "query": candidato,
                    "categoria": nome,
                }
    return None


def _normalizar_texto(valor: str) -> str:
    valor = unicodedata.normalize("NFKD", valor or "")
    valor = "".join(char for char in valor if not unicodedata.combining(char))
    return valor.lower()


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


def _escalar_para_suporte(lead: ChatLead, chat: Chat, mensagem: str):
    """Abre um ticket de suporte humano a partir do chat e avisa a equipe.

    Só cria ticket se o lead estiver associado a um usuário do site. Sem conta
    (ex.: WhatsApp anônimo), orienta o usuário a se cadastrar primeiro.
    """
    usuario = _resolver_usuario_do_lead(lead)
    if usuario is None:
        resposta = (
            "Para falar com nossa equipe de suporte preciso que você tenha uma conta na HIVEE. "
            "Crie a sua em https://hivee.app/cadastrar e volte aqui depois. Posso ajudar em algo mais?"
        )
        _responder_bot(lead, chat, resposta)
        return

    from catalog.models import SupportTicket, SupportTicketLog

    ticket_aberto = (
        SupportTicket.objects.filter(
            user=usuario,
            subject__startswith="[Chat IA]",
            status__in=[
                SupportTicket.Status.OPEN,
                SupportTicket.Status.WAITING_USER,
                SupportTicket.Status.WAITING_STAFF,
            ],
        )
        .order_by("-created_at")
        .first()
    )
    if ticket_aberto:
        resposta = (
            "Você já tem um ticket aberto com nossa equipe. "
            f"Pode acompanhar por aqui: https://hivee.app/suporte/tickets/{ticket_aberto.id}. "
            "Quer que eu te ajude com algo enquanto a equipe responde?"
        )
        _responder_bot(lead, chat, resposta)
        logger.info("Ticket de suporte #%s reaproveitado via chat para usuario %s", ticket_aberto.id, usuario.id)
        return

    ticket = SupportTicket.objects.create(
        user=usuario,
        category=None,
        subject=f"[Chat IA] {mensagem[:80]}".strip(),
        description=mensagem,
        status=SupportTicket.Status.OPEN,
    )
    SupportTicketLog.objects.create(
        ticket=ticket,
        from_status="",
        to_status=SupportTicket.Status.OPEN,
        changed_by=usuario,
        note="Ticket aberto via Chat IA (escalonamento para suporte humano).",
    )
    _notificar_staff_ticket(ticket)

    resposta = (
        "Entendi! Vou abrir um ticket de suporte para nossa equipe cuidar disso. "
        f"Você pode acompanhar por aqui: https://hivee.app/suporte/tickets/{ticket.id}. "
        "Posso ajudar em mais alguma coisa enquanto isso?"
    )
    _responder_bot(lead, chat, resposta)
    logger.info("Ticket de suporte #%s criado via chat para usuario %s", ticket.id, usuario.id)


def _resolver_usuario_do_lead(lead: ChatLead):
    """Resolve o User dono do lead. No site, o telefone é `site_user_<id>`."""
    match = re.fullmatch(r"site_user_(\d+)", (lead.telefone or "").strip())
    if not match:
        return None
    from django.contrib.auth import get_user_model

    return get_user_model().objects.filter(pk=int(match.group(1)), is_active=True).first()


def _notificar_staff_ticket(ticket):
    """Avisa a staff sobre o ticket criado, reusando o helper do app catalog."""
    try:
        from catalog.views.api_views import _notify_staff_new_ticket

        _notify_staff_new_ticket(ticket)
    except Exception:  # pragma: no cover - notificação é best-effort
        logger.exception("Falha ao notificar staff sobre ticket #%s", ticket.id)


def _responder_bot(lead: ChatLead, chat: Chat, resposta: str):
    """Persiste a resposta do bot e a entrega no canal de origem do lead."""
    ChatMessage.objects.create(chat=chat, role="bot", content=resposta)
    chat.updated_at = timezone.now()
    chat.save(update_fields=["updated_at"])
    formatar_e_enviar(lead, chat, resposta)


def _responder_falha(telefone: str, lead: ChatLead | None, chat: Chat | None):
    resposta = "Desculpa, tive uma instabilidade aqui. Pode mandar sua mensagem de novo?"

    if lead is None:
        lead = ChatLead.objects.filter(telefone=telefone).first()
    if lead is None:
        logger.warning("Nao foi possivel enviar fallback: lead %s inexistente", telefone)
        return

    if chat is None:
        chat = Chat.objects.filter(lead=lead, canal=lead.canal_origem).first()
    if chat is not None:
        ChatMessage.objects.create(chat=chat, role="bot", content=resposta)
        chat.updated_at = timezone.now()
        chat.save(update_fields=["updated_at"])

    if lead.canal_origem == "site":
        enviar_site(lead.telefone, resposta, typing=False)
    elif lead.canal_origem == "whatsapp":
        enviar_whatsapp(lead.telefone, resposta)
