"""Camada de gamificação derivada de dados REAIS (0 hardcoded).

Tudo aqui é calculado a partir de serviços finalizados, avaliações, favoritos e
completude de perfil. Nada é "chumbado" no usuário/prestador: se os dados mudam,
o nível e os badges mudam junto.

- Cliente: níveis por contratações concluídas (Bronze → Diamante) + badges.
- Prestador: níveis cumulativos (Iniciante → Mestre) por serviços + nota +
  completude + portfólio, com "falta pouco" para o próximo nível.
"""

from .models import Provider, ProviderSwipe, Review, Servico

# ── Níveis ────────────────────────────────────────────────────────────────

CLIENT_TIERS = [
    {"key": "bronze", "label": "Bronze", "subtitle": "Novo", "color": "#cd7f32", "min": 0},
    {"key": "prata", "label": "Prata", "subtitle": "Explorador", "color": "#cbd5e1", "min": 3},
    {"key": "ouro", "label": "Ouro", "subtitle": "Confiável", "color": "#eab308", "min": 10},
    {"key": "diamante", "label": "Diamante", "subtitle": "VIP", "color": "#22d3ee", "min": 25},
]

PROVIDER_TIERS = [
    {"key": "iniciante", "label": "Iniciante", "stars": 1, "color": "#9ca3af",
     "req": {"jobs": 0, "rating": 0.0, "completeness": 0}},
    {"key": "profissional", "label": "Profissional", "stars": 2, "color": "#60a5fa",
     "req": {"jobs": 5, "rating": 4.5, "completeness": 0}},
    {"key": "expert", "label": "Expert", "stars": 3, "color": "#a78bfa",
     "req": {"jobs": 20, "rating": 4.5, "completeness": 80}},
    {"key": "mestre", "label": "Mestre", "stars": 5, "color": "#eab308",
     "req": {"jobs": 50, "rating": 4.8, "completeness": 100}},
]


def _completeness(provider) -> int:
    checks = [
        bool(provider.avatar_url or provider.avatar),
        bool(provider.headline),
        len(provider.bio or "") >= 40,
        provider.tags.count() >= 3,
        provider.availability_slots.count() >= 1,
        provider.images.count() >= 1,
        provider.latitude is not None and provider.longitude is not None,
    ]
    return round(100 * sum(checks) / len(checks))


def _client_tier_index(concluidos: int) -> int:
    idx = 0
    for i, tier in enumerate(CLIENT_TIERS):
        if concluidos >= tier["min"]:
            idx = i
    return idx


def client_progress(user) -> dict:
    concluidos = Servico.objects.filter(
        cliente_user=user, status=Servico.Status.FINALIZADO
    ).count()
    reviews = Review.objects.filter(reviewer=user).count()
    favoritos = ProviderSwipe.objects.filter(
        user=user, action=ProviderSwipe.LIKE
    ).count()
    categorias = (
        Servico.objects.filter(cliente_user=user, status=Servico.Status.FINALIZADO)
        .values("provider__category").distinct().count()
    )

    idx = _client_tier_index(concluidos)
    tier = CLIENT_TIERS[idx]
    nxt = CLIENT_TIERS[idx + 1] if idx + 1 < len(CLIENT_TIERS) else None
    if nxt:
        base = tier["min"]
        progress = round(100 * (concluidos - base) / max(1, nxt["min"] - base))
        progress = max(0, min(100, progress))
    else:
        progress = 100

    badges = [
        _badge("primeira", "Primeira contratação", "🎉", concluidos >= 1,
               "Contrate seu primeiro serviço"),
        _badge("explorador", "Explorador", "🧭", categorias >= 3,
               f"Contrate em {max(0, 3 - categorias)} categoria(s) diferente(s)"),
        _badge("critico", "Crítico", "📝", reviews >= 10,
               f"Avalie mais {max(0, 10 - reviews)} serviço(s)"),
        _badge("curador", "Curador", "💛", favoritos >= 5,
               f"Salve mais {max(0, 5 - favoritos)} favorito(s)"),
        _badge("vip", "Cliente VIP", "💎", idx >= 3, "Chegue ao nível Diamante"),
    ]

    return {
        "tier": {**tier, "index": idx},
        "next": ({"label": nxt["label"], "needed": nxt["min"], "remaining": nxt["min"] - concluidos} if nxt else None),
        "progress_percent": progress,
        "stats": {
            "concluidos": concluidos,
            "avaliacoes": reviews,
            "favoritos": favoritos,
            "categorias": categorias,
        },
        "badges": badges,
    }


def _provider_tier_index(jobs: int, rating: float, completeness: int) -> int:
    idx = 0
    for i, tier in enumerate(PROVIDER_TIERS):
        r = tier["req"]
        if jobs >= r["jobs"] and rating >= r["rating"] and completeness >= r["completeness"]:
            idx = i
    return idx


def provider_progress(provider) -> dict:
    jobs = provider.jobs_done
    rating = float(provider.rating)
    completeness = _completeness(provider)
    fotos = provider.images.count()
    cinco_estrelas = Review.objects.filter(provider=provider, nota=5).count()

    idx = _provider_tier_index(jobs, rating, completeness)
    tier = PROVIDER_TIERS[idx]
    nxt = PROVIDER_TIERS[idx + 1] if idx + 1 < len(PROVIDER_TIERS) else None

    faltas = []
    progress = 100
    if nxt:
        r = nxt["req"]
        if jobs < r["jobs"]:
            faltas.append(f"{r['jobs'] - jobs} serviço(s)")
        if rating < r["rating"]:
            faltas.append(f"nota {r['rating']}+")
        if completeness < r["completeness"]:
            faltas.append(f"perfil {r['completeness']}%")
        # progresso pela métrica de serviços (a mais tangível)
        base = tier["req"]["jobs"]
        progress = max(0, min(100, round(100 * (jobs - base) / max(1, r["jobs"] - base))))

    badges = [
        _badge("mao_na_massa", "Mão na massa", "🛠️", jobs >= 1, "Conclua seu 1º serviço"),
        _badge("fotografo", "Fotógrafo", "📸", fotos >= 5,
               f"Adicione mais {max(0, 5 - fotos)} foto(s) ao portfólio"),
        _badge("querido", "Querido", "🏅", cinco_estrelas >= 10,
               f"Receba mais {max(0, 10 - cinco_estrelas)} avaliação(ões) 5★"),
        _badge("perfil_diamante", "Perfil Diamante", "💎", completeness >= 100,
               "Complete 100% do perfil"),
        _badge("mestre", "Mestre HIVEE", "👑", idx >= 3, "Alcance o nível Mestre"),
    ]

    return {
        "tier": {**{k: tier[k] for k in ("key", "label", "stars", "color")}, "index": idx},
        "next": ({"label": nxt["label"], "faltam": faltas} if nxt else None),
        "progress_percent": progress,
        "stats": {
            "jobs_done": jobs,
            "rating": round(rating, 2),
            "completeness": completeness,
            "fotos": fotos,
            "avaliacoes_5": cinco_estrelas,
        },
        "badges": badges,
    }


def provider_badge_summary(provider) -> dict:
    """Resumo leve (nível + badges ganhos) para embutir no card/perfil do prestador."""
    data = provider_progress(provider)
    return {
        "tier": data["tier"],
        "earned_badges": [b for b in data["badges"] if b["earned"]],
    }


def _badge(key, label, emoji, earned, hint) -> dict:
    return {"key": key, "label": label, "emoji": emoji, "earned": bool(earned),
            "hint": "" if earned else hint}
