"""Motor de recomendação personalizada a partir do sistema de logs.

Regra do produto:
  - Usuário nunca pesquisou nada  -> NÃO recomenda (deck vazio).
  - Usuário pesquisou             -> recomenda a(s) categoria(s) pesquisada(s)
    e categorias PARECIDAS, de preferência na localização do usuário.
  - Sem localização               -> recomenda só por categoria.

Hierarquia (do mais forte ao mais fraco): Localização > Categoria Pesquisada >
Categoria Parecida. O deck diário (5 itens) tenta SEMPRE conter pelo menos um de
cada nível disponível.

Os sinais de "o que o usuário pesquisou" saem de `logs.LogEvent` (gravado pelo
middleware): filtros `?category=<slug>` e termos `?search=<texto>` em
`/api/providers/`.
"""

from collections import Counter

from logs.models import LogEvent

from .models import Category, Provider

# Pesos dos sinais de busca.
W_CATEGORY_FILTER = 3  # filtrou explicitamente por uma categoria
W_SEARCH_MATCH = 2  # termo de busca que casa com prestadores de uma categoria
MAX_EVENTS = 800  # quantos eventos recentes do usuário olhar

# Categorias "parecidas" (curado para as categorias reais do seed). Ordenadas da
# mais parecida para a menos parecida. Slugs fora do mapa simplesmente não têm
# similares (o nível "categoria parecida" fica vazio para eles).
SIMILAR_CATEGORIES = {
    "reformas-construcao": ["pintura", "encanamento", "eletrica", "jardinagem"],
    "eletrica": ["encanamento", "reformas-construcao", "tecnologia-ti"],
    "encanamento": ["eletrica", "reformas-construcao", "pintura"],
    "pintura": ["reformas-construcao", "encanamento", "limpeza"],
    "limpeza": ["jardinagem", "pintura", "pets"],
    "jardinagem": ["limpeza", "reformas-construcao", "pets"],
    "beleza-estetica": ["fotografia", "eventos-festas", "pets"],
    "aulas-reforco": ["tecnologia-ti", "fotografia", "eventos-festas"],
    "tecnologia-ti": ["aulas-reforco", "eletrica", "fotografia"],
    "fotografia": ["eventos-festas", "beleza-estetica", "aulas-reforco"],
    "eventos-festas": ["fotografia", "beleza-estetica", "aulas-reforco"],
    "pets": ["limpeza", "jardinagem", "beleza-estetica"],
}


def _first(value):
    """Query params do log vêm como listas (`{"search": ["encanador"]}`)."""
    if isinstance(value, (list, tuple)):
        return value[0] if value else None
    return value


def _matches_terms(provider, terms):
    """True quando todos os termos da busca aparecem nos campos do prestador.

    Mesma regra da busca textual do site, centralizada aqui para ser reaproveitada
    tanto pela listagem quanto pelo recomendador (evita import circular).
    """
    haystack = " ".join(
        [
            provider.name,
            provider.headline,
            provider.category.name,
            provider.city or "",
            provider.neighborhood or "",
            " ".join(provider.skills),
            " ".join(t.name for t in provider.tags.all()),
        ]
    ).lower()
    return all(term in haystack for term in terms)


def search_signals(user):
    """Lê os logs do usuário e devolve (has_searched, weights).

    `has_searched`: True se houver pelo menos UMA busca/filtro de categoria no log.
    `weights`: Counter {category_slug: peso} das categorias efetivamente pesquisadas.
    """
    events = list(
        LogEvent.objects.filter(usuario=user, rota__startswith="/api/providers")
        .order_by("-created_at")
        .values("rota", "payload")[:MAX_EVENTS]
    )

    valid_slugs = set(Category.objects.values_list("slug", flat=True))
    weights = Counter()
    searches = Counter()
    has_searched = False

    for ev in events:
        payload = ev.get("payload") or {}
        query = payload.get("query") if isinstance(payload, dict) else {}
        query = query or {}

        categoria = _first(query.get("category"))
        if categoria in valid_slugs:
            weights[categoria] += W_CATEGORY_FILTER
            has_searched = True

        termo = _first(query.get("search"))
        if termo and termo.strip():
            searches[termo.strip().lower()] += 1
            has_searched = True

    # Termos de busca -> categorias dos prestadores que casam com o termo.
    if searches:
        providers = list(
            Provider.objects.select_related("category")
            .prefetch_related("tags")
            .filter(status="approved")
        )
        for termo, vezes in searches.items():
            terms = termo.split()
            if not terms:
                continue
            peso = W_SEARCH_MATCH * min(vezes, 3)
            for provider in providers:
                if _matches_terms(provider, terms):
                    weights[provider.category.slug] += peso

    return has_searched, weights


def similar_categories(searched_slugs):
    """Lista ordenada de categorias parecidas com as pesquisadas (sem repetir as buscadas)."""
    out = []
    seen = set(searched_slugs)
    for slug in searched_slugs:
        for similar in SIMILAR_CATEGORIES.get(slug, []):
            if similar not in seen:
                seen.add(similar)
                out.append(similar)
    return out
