# PLANO DE IMPLEMENTAÇÃO — PRESTADORES EM DESTAQUE NA REGIÃO

> **Versão:** 2.0 — 2026-06-15 ✅ **IMPLEMENTADO**
> **Baseado em:** HIVEE Marketplace (Django 6 + React 19)
> **Feature:** Endpoint backend que retorna prestadores em destaque filtrados por proximidade (até 100km) para exibição na tela inicial
>
> **Status Geral:** ✅ **100% IMPLEMENTADO** — 25 testes, 0 falhas, 70 testes no suite completo

---

---

## Regras de Negócio ✅

| # | Regra | Status |
|---|-------|--------|
| 1 | Retorna **mínimo 2, máximo 5** prestadores | ✅ |
| 2 | Ordenação: **1º `jobs_done` decrescente, 2º `rating` decrescente** | ✅ |
| 3 | Só inclui prestadores com **localização confirmada** (`latitude` e `longitude` não nulas) | ✅ |
| 4 | Filtro geográfico: **até 100km** de distância do usuário | ✅ |
| 5 | Se o usuário **não enviou localização** (`lat`/`lng`), usa `city` + `state` do provider como fallback textual (mesmo raio de 100km via geocoding reverso ou ignorando distância se não houver coordenadas) | ✅ |
| 6 | Se **nenhum prestador encontrado** no raio, retorna `{ prestadores: [], fallback: true, mensagem: "..." }` | ✅ |
| 7 | O prestador deve estar com `status = "approved"` | ✅ |
| 8 | **Sem autenticação necessária** (tela inicial é pública) | ✅ |

---

## Endpoint ✅

```
GET /api/providers/featured/?lat=-23.5505&lng=-46.6333
```

### Parâmetros

| Parâmetro | Tipo | Obrigatório | Descrição |
|-----------|------|-------------|-----------|
| `lat` | float | Não | Latitude do usuário (obtida via geolocation do navegador) |
| `lng` | float | Não | Longitude do usuário |
| `city` | string | Não | Cidade do usuário (fallback se não tiver lat/lng) |

### Resposta (sucesso)

```json
{
  "prestadores": [
    {
      "id": 42,
      "slug": "joao-eletricista",
      "name": "João Eletricista",
      "headline": "Instalações e reparos elétricos",
      "avatar_url": "https://...",
      "rating": 4.9,
      "reviews_count": 320,
      "jobs_done": 1500,
      "hourly_rate": 90.00,
      "city": "São Paulo",
      "neighborhood": "Centro",
      "state": "SP",
      "distance_km": 3.2,
      "category": { "slug": "eletrica", "name": "Elétrica", "icon": "Zap" },
      "verified": true
    }
  ],
  "total": 4,
  "fallback": false,
  "mensagem": null
}
```

### Resposta (fallback — nenhum encontrado)

```json
{
  "prestadores": [],
  "total": 0,
  "fallback": true,
  "mensagem": "Nenhum prestador em destaque encontrado num raio de 100 km da sua localização."
}
```

---

## Lógica do Backend ✅

```python
# backend/catalog/views/api_views.py — adicionar ao ProviderViewSet

FEATURED_RADIUS_KM = 100.0
FEATURED_MIN = 2
FEATURED_MAX = 5


@extend_schema(
    summary="Prestadores em destaque na região (tela inicial)",
    description="Retorna prestadores próximos (até 100km) ordenados por serviços realizados e avaliação."
               "Mínimo 2, máximo 5. Se não encontrar, retorna fallback.",
    parameters=[
        OpenApiParameter("lat", float, description="Latitude do usuário (opcional)"),
        OpenApiParameter("lng", float, description="Longitude do usuário (opcional)"),
        OpenApiParameter("city", str, description="Cidade do usuário (fallback textual)"),
    ],
    responses=OpenApiTypes.OBJECT,
)
@action(detail=False, methods=["get"])
def featured(self, request):
    lat, lng = _parse_point(request)
    city = request.query_params.get("city", "").strip()

    providers = list(
        Provider.objects
        .filter(status="approved", latitude__isnull=False, longitude__isnull=False)
        .select_related("category")
    )

    if not providers:
        return self._fallback_resposta()

    # Calcula distância para todos
    _attach_distance(providers, lat, lng)

    # Filtra por raio de 100km
    if lat is not None and lng is not None:
        proximos = [p for p in providers if p.distance_km is not None and p.distance_km <= FEATURED_RADIUS_KM]
    elif city:
        proximos = [p for p in providers if p.city and p.city.lower() == city.lower()]
    else:
        proximos = providers  # sem localização, mostra os melhores gerais

    if not proximos:
        return self._fallback_resposta(city=city)

    # Ordena: 1º jobs_done, 2º rating
    proximos.sort(key=lambda p: (p.jobs_done, float(p.rating)), reverse=True)

    # Pega mínimo 2, máximo 5
    selecionados = proximos[:FEATURED_MAX]
    if len(selecionados) < FEATURED_MIN:
        return self._fallback_resposta(city=city)

    data = ProviderSerializer(selecionados, many=True).data
    return Response({
        "prestadores": data,
        "total": len(data),
        "fallback": False,
        "mensagem": None,
    })


def _fallback_resposta(self, city=""):
    if city:
        msg = f"Nenhum prestador em destaque encontrado em {city} ou num raio de {FEATURED_RADIUS_KM} km."
    else:
        msg = f"Nenhum prestador em destaque encontrado num raio de {FEATURED_RADIUS_KM} km da sua localização."
    return Response({
        "prestadores": [],
        "total": 0,
        "fallback": True,
        "mensagem": msg,
    })
```

---

## Views: Caminho do Código ✅

```python
# catalog/views/__init__.py — ProviderViewSet já importado (sem alterações)
# ProviderViewSet fica em catalog/views/api_views.py

# Action 'featured' adicionada ao ProviderViewSet com:
#   @extend_schema(...)
#   @action(detail=False, methods=["get"])
#   def featured(self, request):
#       ...
```

---

## Reúso de Código Existente ✅

| Função/Constante | Arquivo | Uso |
|-----------------|---------|-----|
| `_parse_point(request)` | `api_views.py:36` | Extrai `lat`, `lng` dos query params |
| `_attach_distance(providers, lat, lng)` | `api_views.py:45` | Calcula `distance_km` em cada provider |
| `haversine_km()` | `geo.py:11` | Cálculo de distância entre coordenadas |
| `FEATURED_RADIUS_KM = 100.0` | `api_views.py` | Novo — raio de 100km para o destaque |
| `ProviderSerializer` | `serializers.py:93` | Serialização dos dados do provider |
| `Provider.status = "approved"` | `models.py:89` | Filtro de prestadores aprovados |
| `Provider.jobs_done` | `models.py:70` | Critério de ordenação primário |
| `Provider.rating` | `models.py:68` | Critério de ordenação secundário |
| `Provider.latitude, longitude` | `models.py:78-79` | Validação de localização confirmada |

---

## Fluxo de Decisão ✅

```
GET /api/providers/featured/?lat=-23.55&lng=-46.63
       │
       ▼
Provider.objects.filter(status="approved", latitude__isnull=False, longitude__isnull=False)
       │
       ▼
_lista vazia? ──SIM──→ { fallback: true, "Nenhum prestador..." }
       │
      NÃO
       ▼
_attach_distance(providers, lat, lng)   (calcula distância em km para cada um)
       │
       ▼
lat/lng fornecidos? ──SIM──→ filtra: distance_km <= 100km
       │                         │
      NÃO                        ▼
       │                   lista vazia? ──SIM→ fallback
       │                         │
       ▼                        NÃO
city fornecida? ──SIM──→        ▼
       │              filtra: city (case-insensitive)
       │                   │
      NÃO                  ▼
       │             ordena: jobs_done DESC, rating DESC
       ▼                   │
usa todos (sem            ▼
filtro geo)         pega [0:5]
       │                   │
       ▼                   ▼
   len < 2? ──SIM──→ fallback
       │
      NÃO
       ▼
{ prestadores: [...], total: N, fallback: false }
```

---

## Casos de Borda ✅

| Cenário | Comportamento | Status |
|---------|---------------|
| Usuário sem geolocation (`lat`/`lng` vazios, `city` vazia) | Retorna os **top 5 globais** por jobs_done + rating (sem filtro geográfico) | ✅ |
| Usuário com `lat`/`lng` mas nenhum provider num raio de 100km | Fallback: `"Nenhum prestador em destaque encontrado num raio de 100 km da sua localização."` | ✅ |
| Usuário com `city` e só 1 provider na cidade | Fallback: o mínimo é 2 | ✅ |
| Usuário com `city` e 6+ providers na cidade | Retorna os top 5 | ✅ |
| Usuário com `lat`/`lng` e apenas 2-4 providers no raio | Retorna os que existirem (2 a 4, sem falhar) | ✅ |
| Todos os providers sem localização (`latitude = null`) | Fallback (não entra no queryset) | ✅ |
| Provider com `status != "approved"` | Não entra (filtro no queryset) | ✅ |

---

## Testes ✅

**25 testes implementados** — 8 originais do plano + 17 adicionais. Todos passando (70 testes no total do suite).

```python
# catalog/tests.py — Lista completa dos 25 testes:

class FeaturedProvidersTests(ApiTestBase):
    # setUpTestData: Carlos Eletricista (base) + Maria Encanadora + João Pintor

    # --- Plano original (8 testes) ---
    ✅ test_featured_returns_top_5_by_jobs_and_rating
    ✅ test_featured_filters_by_distance
    ✅ test_featured_fallback_when_none_nearby
    ✅ test_featured_fallback_when_fewer_than_2
    ✅ test_featured_ordering
    ✅ test_featured_excludes_unapproved
    ✅ test_featured_excludes_no_location
    ✅ test_featured_response_structure

    # --- Testes expandidos (17 testes) ---
    ✅ test_featured_public_no_auth_required        # Regra 8
    ✅ test_featured_city_filter_matches             # Regra 5
    ✅ test_featured_city_filter_case_insensitive    # Regra 5
    ✅ test_featured_city_filter_no_match_fallback   # Regra 6
    ✅ test_featured_city_filter_fewer_than_2        # Regra 1
    ✅ test_featured_returns_exact_count_when_2_to_5 # Regra 1
    ✅ test_featured_distance_km_rounded             # Regra 4
    ✅ test_featured_lat_lng_overrides_city          # Regra 5
    ✅ test_featured_category_serialized             # Resposta
    ✅ test_featured_selected_fields_present         # Resposta
    ✅ test_featured_ordering_jobs_then_rating       # Regra 2
    ✅ test_featured_fallback_mensagem_sem_localizacao
    ✅ test_featured_fallback_mensagem_com_city
    ✅ test_featured_excludes_rejected               # Regra 7
    ✅ test_featured_excludes_pending                # Regra 7
    ✅ test_featured_with_partial_location_data_none # Regra 3
    ✅ test_featured_sem_parametros_retorna_melhores_globais
```

---

## Resumo de Arquivos Alterados ✅

| Arquivo | Mudança | Status |
|---------|---------|--------|
| `backend/catalog/views/api_views.py` | Action `featured` adicionada ao `ProviderViewSet`, constantes `FEATURED_RADIUS_KM`/`FEATURED_MIN`/`FEATURED_MAX`, função auxiliar `_fallback_resposta` | ✅ |
| `backend/catalog/views/__init__.py` | Nenhuma — `featured` é action do `ProviderViewSet` já exportado | ✅ |
| `backend/catalog/tests.py` | Classe `FeaturedProvidersTests` com **25 testes** (Setup: 3 providers em Campinas; Testes: 8 originais + 17 expandidos) | ✅ |
| `backend/catalog/urls.py` | Nenhuma — `DefaultRouter` já expõe actions automaticamente como `/api/providers/featured/` | ✅ |

---

## Nenhuma Nova Dependência ✅

Tudo já existia no projeto e foi reutilizado:
- `haversine_km` em `geo.py`
- `_parse_point` em `api_views.py`
- `_attach_distance` em `api_views.py`
- `ProviderSerializer` em `serializers.py`
- `Provider` model com `latitude`, `longitude`, `jobs_done`, `rating`
