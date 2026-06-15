import logging
import unicodedata
from typing import Optional

from catalog.models import Provider

logger = logging.getLogger(__name__)


def buscar_prestadores(
    query: str,
    cidade: Optional[str] = None,
    categoria: Optional[str] = None,
    limite: int = 5,
) -> list[dict]:
    qs = Provider.objects.filter(status="approved").select_related("category")

    providers = list(qs)
    if cidade:
        cidade_norm = _normalize(cidade)
        providers = [provider for provider in providers if cidade_norm in _normalize(provider.city)]
    if categoria:
        categoria_norm = _normalize(categoria)
        providers = [
            provider
            for provider in providers
            if _matches_category(provider.category.name, categoria_norm)
        ]

    terms = [term.lower() for term in (query or "").split() if term.strip()]
    if terms:
        providers = [provider for provider in providers if _matches_terms(provider, terms)]

    providers.sort(key=lambda p: (float(p.rating), p.reviews_count), reverse=True)
    providers = providers[: max(1, limite)]

    return [
        {
            "id": p.id,
            "nome": p.name,
            "slug": p.slug,
            "categoria": p.category.name,
            "cidade": p.city,
            "estado": p.state,
            "nota": float(p.rating),
            "avaliacoes": p.reviews_count,
            "verificado": p.verified,
            "descricao": p.headline,
            "avatar_url": p.avatar_url or (p.avatar.url if p.avatar else ""),
            "preco_hora": float(p.hourly_rate),
            "tempo_resposta": p.response_time,
            "habilidades": p.skills if isinstance(p.skills, list) else [],
            "link": f"/prestador/{p.slug}",
        }
        for p in providers
    ]


def _matches_terms(provider, terms: list[str]) -> bool:
    ignored_terms = {
        "a",
        "as",
        "com",
        "da",
        "das",
        "de",
        "do",
        "dos",
        "e",
        "em",
        "na",
        "nas",
        "no",
        "nos",
        "o",
        "os",
        "para",
        "preciso",
        "quero",
        "um",
        "uma",
    }
    terms = [_normalize(term) for term in terms if _normalize(term) not in ignored_terms]
    if not terms:
        return True

    skills = provider.skills if isinstance(provider.skills, list) else []
    haystack = _normalize(
        " ".join(
            [
                provider.name,
                provider.headline,
                provider.bio or "",
                provider.category.name,
                provider.city or "",
                provider.neighborhood or "",
                " ".join(str(skill) for skill in skills),
            ]
        )
    )
    return all(any(variant in haystack for variant in _term_variants(term)) for term in terms)


def _matches_category(category_name: str, categoria_norm: str) -> bool:
    haystack = _normalize(category_name)
    if categoria_norm in haystack:
        return True
    for word in categoria_norm.split():
        if any(variant in haystack for variant in _term_variants(word)):
            return True
    return any(variant in haystack for variant in _term_variants(categoria_norm))


def _term_variants(term: str) -> set[str]:
    variants = {term}
    synonyms = {
        "eletricista": {"eletrica", "eletrico", "eletricos", "instalacao", "tomada", "luz"},
        "eletrica": {"eletricista", "eletrico", "eletricos"},
        "encanador": {"encanamento", "hidraulica", "hidraulico", "vazamento"},
        "pintor": {"pintura", "pintura interna", "pintura externa"},
        "faxineira": {"limpeza", "faxina"},
        "diarista": {"limpeza", "faxina"},
        "jardineiro": {"jardinagem", "paisagismo", "grama"},
        "professor": {"aulas", "reforco"},
        "tecnico": {"tecnologia", "ti", "suporte"},
        "fotografo": {"fotografia", "foto", "eventos"},
    }
    variants.update(synonyms.get(term, set()))
    return variants


def _normalize(value: str) -> str:
    value = unicodedata.normalize("NFKD", value or "")
    value = "".join(char for char in value if not unicodedata.combining(char))
    return value.lower().strip()


def montar_provider_card(provider: dict) -> dict:
    return {
        "id": provider.get("id"),
        "nome": provider.get("nome", ""),
        "slug": provider.get("slug", ""),
        "categoria": provider.get("categoria", ""),
        "cidade": provider.get("cidade", ""),
        "estado": provider.get("estado", ""),
        "nota": provider.get("nota"),
        "avaliacoes": provider.get("avaliacoes"),
        "descricao": provider.get("descricao", ""),
        "avatar_url": provider.get("avatar_url", ""),
        "preco_hora": provider.get("preco_hora"),
        "tempo_resposta": provider.get("tempo_resposta", ""),
        "habilidades": provider.get("habilidades", [])[:3],
        "link": provider.get("link", ""),
    }


ferramenta_buscar_prestadores = {
    "type": "function",
    "function": {
        "name": "buscar_prestadores",
        "description": "Busca prestadores de servico cadastrados na plataforma HIVEE que correspondam a necessidade do usuario.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Palavras-chave, como eletricista ou personal trainer"},
                "cidade": {"type": ["string", "null"], "description": "Cidade opcional"},
                "categoria": {"type": ["string", "null"], "description": "Categoria opcional"},
                "limite": {"type": "integer", "description": "Maximo de resultados", "default": 5},
            },
            "required": ["query", "cidade", "categoria", "limite"],
            "additionalProperties": False,
        },
        "strict": True,
    },
}
