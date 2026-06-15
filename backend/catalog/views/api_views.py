import gzip
import json
import os
import uuid
import urllib.request

from django.conf import settings
from django.contrib.auth import authenticate, get_user_model
from django.db.models import Avg, Count, F, Q, Sum
from django.utils import timezone
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action
from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ViewSet

from ..geo import haversine_km
from ..models import (
    Category,
    Demand,
    DemandOffer,
    FAQArticle,
    Notification,
    Provider,
    ProviderImage,
    ProviderSwipe,
    SupportCategory,
    SupportMessage,
    SupportTicket,
    SupportTicketLog,
    Tag,
    UserProfile,
)
from ..recommender import _matches_terms  # regra de busca textual compartilhada
from ..recommender import search_signals, similar_categories
from ..serializers import (
    CategorySerializer,
    CreateDemandSerializer,
    CreateOfferSerializer,
    DemandOfferSerializer,
    DemandSerializer,
    FAQArticleSerializer,
    ProviderImageSerializer,
    ProviderSerializer,
    ProviderUpdateSerializer,
    ProviderWriteSerializer,
    RecommendationSerializer,
    RegisterSerializer,
    SupportCategorySerializer,
    SupportMessageSerializer,
    SupportTicketSerializer,
    TagSerializer,
    UserSerializer,
)

# Prefetch padrão para serializar prestador completo (tags, galeria, agenda) sem N+1.
PROVIDER_PREFETCH = ("tags", "images", "availability_slots")
MAX_GALLERY_IMAGES = 12


def _parse_point(request):
    try:
        lat = float(request.query_params.get("lat"))
        lng = float(request.query_params.get("lng"))
        return lat, lng
    except (TypeError, ValueError):
        return None, None


def _attach_distance(providers, lat, lng):
    for provider in providers:
        provider.distance_km = (
            haversine_km(lat, lng, provider.latitude, provider.longitude)
            if lat is not None and lng is not None
            and provider.latitude is not None and provider.longitude is not None
            else None
        )
    return providers


def _fallback_resposta(city=""):
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


class CategoryListView(ListAPIView):
    serializer_class = CategorySerializer
    pagination_class = None

    def get_queryset(self):
        return Category.objects.annotate(provider_count=Count("providers")).order_by(
            "order", "name"
        )


class TagListView(ListAPIView):
    """Autocomplete de tags de serviço: `?search=` filtra; ordena por popularidade.

    Usado tanto pelo editor do prestador (sugerir/criar tag) quanto pela barra de
    busca (sugerir termos além da categoria)."""

    serializer_class = TagSerializer
    pagination_class = None

    def get_queryset(self):
        qs = Tag.objects.annotate(provider_count=Count("providers"))
        search = (self.request.query_params.get("search") or "").strip()
        if search:
            qs = qs.filter(name__icontains=search)
        return qs.order_by("-provider_count", "name")[:20]


@extend_schema_view(
    list=extend_schema(
        summary="Lista prestadores (filtravel e paginada)",
        parameters=[
            OpenApiParameter("category", str, description="Slug da categoria."),
            OpenApiParameter("city", str, description="Filtra por cidade."),
            OpenApiParameter("search", str, description="Busca textual livre."),
            OpenApiParameter(
                "ordering", str, description="distance | -rating | hourly_rate"
            ),
            OpenApiParameter("lat", float, description="Latitude do usuario."),
            OpenApiParameter("lng", float, description="Longitude do usuario."),
            OpenApiParameter("page", int),
            OpenApiParameter("page_size", int),
        ],
        responses=ProviderSerializer(many=True),
    ),
    retrieve=extend_schema(
        summary="Detalhe de um prestador",
        parameters=[
            OpenApiParameter(
                "slug", str, location=OpenApiParameter.PATH,
                description="Slug unico do prestador.",
            )
        ],
        responses=ProviderSerializer,
    ),
    create=extend_schema(
        summary="Cadastra um prestador (requer autenticacao)",
        request=ProviderWriteSerializer,
        responses=ProviderSerializer,
    ),
    recommended=extend_schema(
        summary="Top 8 prestadores recomendados",
        responses=RecommendationSerializer(many=True),
    ),
)
class ProviderViewSet(ViewSet):
    # Smell fix (passo a passo do DRF): superusuarios/usuarios autenticados podem
    # escrever (POST), os demais so podem ler (GET). Substitui o controle manual
    # de autenticacao que existia dentro de create().
    serializer_class = ProviderSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    lookup_field = "slug"

    # Smell fix: o antigo `_filtered` concentrava filtro de banco, busca textual,
    # distancia e ordenacao. Foi quebrado em passos coesos e testaveis abaixo.
    def _filtered(self, request):
        items = list(self._base_queryset(request))
        items = self._apply_search(items, request)
        lat, lng = _parse_point(request)
        _attach_distance(items, lat, lng)
        self._sort(items, request, has_location=lat is not None)
        return items

    @staticmethod
    def _base_queryset(request):
        """Filtros que o banco resolve: status, categoria e cidade."""
        qs = Provider.objects.select_related("category").prefetch_related(*PROVIDER_PREFETCH)
        user = request.user
        if user.is_staff or user.is_superuser:
            qs = qs.all()
        else:
            qs = qs.filter(status="approved")
        category = request.query_params.get("category")
        if category:
            qs = qs.filter(category__slug=category)
        city = request.query_params.get("city")
        if city:
            qs = qs.filter(city__icontains=city)
        return qs

    @staticmethod
    def _apply_search(items, request):
        """Busca textual livre por todos os termos informados."""
        search = (request.query_params.get("search") or "").strip().lower()
        if not search:
            return items
        terms = search.split()
        return [p for p in items if _matches_terms(p, terms)]

    @staticmethod
    def _sort(items, request, has_location):
        """Ordenacao em memoria conforme o parametro `ordering`."""
        ordering = request.query_params.get("ordering", "")
        if ordering == "distance" and has_location:
            items.sort(key=lambda p: p.distance_km)
        elif ordering == "-rating":
            items.sort(key=lambda p: (float(p.rating), p.reviews_count), reverse=True)
        elif ordering == "hourly_rate":
            items.sort(key=lambda p: float(p.hourly_rate))
        else:
            items.sort(
                key=lambda p: (p.top_rated, float(p.rating), p.reviews_count),
                reverse=True,
            )

    def list(self, request):
        items = self._filtered(request)
        count = len(items)

        try:
            page = max(1, int(request.query_params.get("page", 1)))
            page_size = min(48, max(1, int(request.query_params.get("page_size", 9))))
        except ValueError:
            page, page_size = 1, 9

        start = (page - 1) * page_size
        chunk = items[start : start + page_size]
        data = ProviderSerializer(chunk, many=True).data

        def page_url(n):
            return request.build_absolute_uri(_replace_query(request, "page", n))

        return Response(
            {
                "count": count,
                "next": page_url(page + 1) if start + page_size < count else None,
                "previous": page_url(page - 1) if page > 1 else None,
                "results": data,
            }
        )

    def retrieve(self, request, slug=None):
        provider = (
            Provider.objects.select_related("category")
            .prefetch_related(*PROVIDER_PREFETCH)
            .get(slug=slug)
        )
        user = request.user
        if provider.status != "approved" and not (user.is_staff or user.is_superuser) and provider.owner != user:
            return Response(
                {"detail": "Profissional não encontrado."},
                status=status.HTTP_404_NOT_FOUND,
            )
        lat, lng = _parse_point(request)
        _attach_distance([provider], lat, lng)
        data = ProviderSerializer(provider).data
        data["is_favorited"] = bool(
            user.is_authenticated
            and ProviderSwipe.objects.filter(
                user=user, provider=provider, action=ProviderSwipe.LIKE
            ).exists()
        )
        return Response(data)

    @action(detail=False, methods=["get"])
    def recommended(self, request):
        lat, lng = _parse_point(request)
        providers = list(
            Provider.objects.select_related("category")
            .prefetch_related(*PROVIDER_PREFETCH)
            .filter(status="approved")
        )
        _attach_distance(providers, lat, lng)

        scored = []
        for provider in providers:
            score, reason = _score(provider)
            provider.match_score = score
            provider.match_reason = reason
            scored.append(provider)

        scored.sort(key=lambda provider: provider.match_score, reverse=True)
        return Response(RecommendationSerializer(scored[:8], many=True).data)

    @extend_schema(
        summary="Prestadores em destaque na região (tela inicial)",
        description="Retorna prestadores próximos (até 100km) ordenados por serviços realizados e avaliação. "
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
            return _fallback_resposta(city=city)

        _attach_distance(providers, lat, lng)

        if lat is not None and lng is not None:
            proximos = [p for p in providers if p.distance_km is not None and p.distance_km <= FEATURED_RADIUS_KM]
        elif city:
            proximos = [p for p in providers if p.city and p.city.lower() == city.lower()]
        else:
            proximos = providers

        if not proximos:
            return _fallback_resposta(city=city)

        proximos.sort(key=lambda p: (p.jobs_done, float(p.rating)), reverse=True)

        selecionados = proximos[:FEATURED_MAX]
        if len(selecionados) < FEATURED_MIN:
            return _fallback_resposta(city=city)

        data = ProviderSerializer(selecionados, many=True).data
        return Response({
            "prestadores": data,
            "total": len(data),
            "fallback": False,
            "mensagem": None,
        })

    @action(detail=False, methods=["get"], url_path="for-you", permission_classes=[IsAuthenticated])
    def for_you(self, request):
        """Deck personalizado, baseado SÓ no que o usuário pesquisou (via logs).

        - Nunca pesquisou nada  -> deck vazio (`has_searched=False`).
        - Pesquisou             -> categoria(s) buscada(s) + categorias parecidas,
          priorizando a localização. O deck diário (5) sempre tenta conter pelo
          menos um da localização, um da categoria buscada e um de categoria parecida.
        """
        user = request.user
        lat, lng = _parse_point(request)

        has_searched, weights = search_signals(user)
        if not has_searched:
            # Sem nenhuma pesquisa no log: não recomenda nada (use mais a plataforma).
            return Response(
                {
                    "results": [],
                    "daily_limit": DAILY_DECK_LIMIT,
                    "remaining_today": 0,
                    "has_searched": False,
                }
            )

        remaining = max(0, DAILY_DECK_LIMIT - _swiped_today(user))
        if remaining == 0:
            return Response(
                {
                    "results": [],
                    "daily_limit": DAILY_DECK_LIMIT,
                    "remaining_today": 0,
                    "has_searched": True,
                }
            )

        searched_cats = [slug for slug, _ in weights.most_common()]
        searched_set = set(searched_cats)
        similar_set = set(similar_categories(searched_cats))
        relevant = searched_set | similar_set
        max_aff = max(weights.values()) if weights else 0

        swiped_ids = set(
            ProviderSwipe.objects.filter(user=user).values_list("provider_id", flat=True)
        )
        providers = [
            p
            for p in Provider.objects.select_related("category")
            .prefetch_related(*PROVIDER_PREFETCH)
            .filter(status="approved")
            if p.id not in swiped_ids and p.category.slug in relevant
        ]
        _attach_distance(providers, lat, lng)

        def is_local(p):
            return p.distance_km is not None and p.distance_km <= LOCATION_RADIUS_KM

        for provider in providers:
            base, _ = _score(provider)
            aff = weights.get(provider.category.slug, 0)
            personal = round(PERSONAL_WEIGHT * aff / max_aff) if max_aff else 0
            provider.match_score = min(MAX_SCORE, base + personal)
            in_searched = provider.category.slug in searched_set
            local = is_local(provider)
            nome = provider.category.name
            if in_searched:
                provider.match_reason = (
                    f"{nome}: categoria que você buscou"
                    + (", e perto de você." if local else ".")
                )
            else:
                provider.match_reason = (
                    f"{nome}: parecida com o que você buscou"
                    + (", e perto de você." if local else ".")
                )

        # Hierarquia: Localização > Categoria Buscada > Categoria Parecida > nota.
        ranked = sorted(
            providers,
            key=lambda p: (
                is_local(p),
                p.category.slug in searched_set,
                weights.get(p.category.slug, 0),
                p.match_score,
                -p.id,
            ),
            reverse=True,
        )

        # Monta o deck garantindo um de cada nível disponível, depois preenche.
        deck, chosen = [], set()

        def add(provider):
            if provider is not None and provider.id not in chosen and len(deck) < remaining:
                deck.append(provider)
                chosen.add(provider.id)

        if lat is not None and lng is not None:
            add(next((p for p in ranked if is_local(p)), None))  # 1) localização
        add(next((p for p in ranked if p.category.slug in searched_set), None))  # 2) buscada
        add(next((p for p in ranked if p.category.slug in similar_set), None))  # 3) parecida
        for provider in ranked:  # 4) preenche o resto por hierarquia
            add(provider)

        return Response(
            {
                "results": RecommendationSerializer(deck, many=True).data,
                "daily_limit": DAILY_DECK_LIMIT,
                "remaining_today": remaining,
                "has_searched": True,
            }
        )

    @action(detail=True, methods=["post", "delete"], permission_classes=[IsAuthenticated])
    def swipe(self, request, slug=None):
        """POST {action: like|dislike} registra o swipe; DELETE remove o swipe
        (ex.: tirar dos favoritos)."""
        provider = Provider.objects.filter(slug=slug).first()
        if not provider:
            return Response(
                {"detail": "Profissional não encontrado."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if request.method == "DELETE":
            ProviderSwipe.objects.filter(user=request.user, provider=provider).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

        acao = request.data.get("action")
        if acao not in (ProviderSwipe.LIKE, ProviderSwipe.DISLIKE):
            return Response(
                {"detail": "action deve ser 'like' ou 'dislike'."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        origem = request.data.get("source", ProviderSwipe.DECK)
        if origem not in (ProviderSwipe.DECK, ProviderSwipe.PROFILE):
            origem = ProviderSwipe.DECK

        ja_swipou = ProviderSwipe.objects.filter(
            user=request.user, provider=provider
        ).exists()
        # Limite diário só vale para o deck e só para um prestador NOVO.
        if (
            origem == ProviderSwipe.DECK
            and not ja_swipou
            and _swiped_today(request.user) >= DAILY_DECK_LIMIT
        ):
            return Response(
                {
                    "detail": f"Você atingiu seu limite de {DAILY_DECK_LIMIT} "
                    "recomendações por hoje. Volte amanhã!",
                    "daily_limit": DAILY_DECK_LIMIT,
                    "remaining_today": 0,
                },
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        swipe, _ = ProviderSwipe.objects.update_or_create(
            user=request.user,
            provider=provider,
            defaults={"action": acao, "source": origem},
        )
        return Response(
            {
                "action": swipe.action,
                "provider": provider.slug,
                "remaining_today": max(0, DAILY_DECK_LIMIT - _swiped_today(request.user)),
            },
            status=status.HTTP_200_OK,
        )

    @action(detail=False, methods=["get"], permission_classes=[IsAuthenticated])
    def favorites(self, request):
        """Prestadores que o usuário curtiu no swipe (aba 'Prestadores favoritos')."""
        lat, lng = _parse_point(request)
        providers = [
            s.provider
            for s in ProviderSwipe.objects.filter(
                user=request.user, action=ProviderSwipe.LIKE
            )
            .select_related("provider__category")
            .prefetch_related(
                "provider__tags", "provider__images", "provider__availability_slots"
            )
        ]
        _attach_distance(providers, lat, lng)
        return Response(ProviderSerializer(providers, many=True).data)

    def create(self, request):
        # A autenticacao ja e garantida por IsAuthenticatedOrReadOnly.
        if Provider.objects.filter(owner=request.user).exists():
            return Response(
                {"detail": "Você já possui um cadastro como prestador."},
                status=status.HTTP_409_CONFLICT,
            )
        serializer = ProviderWriteSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        provider = serializer.save(owner=request.user, verified=False)
        return Response(
            ProviderSerializer(provider).data, status=status.HTTP_201_CREATED
        )

    def _owned_provider(self, request, slug):
        """Prestador do qual o usuário logado é dono (ou None)."""
        return Provider.objects.filter(slug=slug, owner=request.user).first()

    def partial_update(self, request, slug=None):
        """O prestador edita o próprio perfil: campos, tags e agenda de disponibilidade."""
        provider = self._owned_provider(request, slug)
        if not provider:
            return Response(
                {"detail": "Você não pode editar este perfil."},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = ProviderUpdateSerializer(
            provider, data=request.data, partial=True, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        provider = (
            Provider.objects.select_related("category")
            .prefetch_related(*PROVIDER_PREFETCH)
            .get(pk=provider.pk)
        )
        return Response(ProviderSerializer(provider).data)

    @action(detail=True, methods=["post"], url_path="gallery", permission_classes=[IsAuthenticated])
    def add_gallery(self, request, slug=None):
        """Adiciona uma foto de serviço realizado à galeria do prestador (dono)."""
        provider = self._owned_provider(request, slug)
        if not provider:
            return Response(
                {"detail": "Você não pode editar este perfil."},
                status=status.HTTP_404_NOT_FOUND,
            )
        if provider.images.count() >= MAX_GALLERY_IMAGES:
            return Response(
                {"detail": f"Limite de {MAX_GALLERY_IMAGES} fotos atingido."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        file = request.FILES.get("image")
        if not file:
            return Response(
                {"detail": "Nenhuma imagem enviada."}, status=status.HTTP_400_BAD_REQUEST
            )
        image = ProviderImage.objects.create(
            provider=provider, image=file, alt_text=request.data.get("alt_text", "")[:160]
        )
        return Response(ProviderImageSerializer(image).data, status=status.HTTP_201_CREATED)

    @action(
        detail=True,
        methods=["delete"],
        url_path=r"gallery/(?P<image_id>[0-9]+)",
        permission_classes=[IsAuthenticated],
    )
    def remove_gallery(self, request, slug=None, image_id=None):
        """Remove uma foto da galeria (dono)."""
        provider = self._owned_provider(request, slug)
        if not provider:
            return Response(
                {"detail": "Você não pode editar este perfil."},
                status=status.HTTP_404_NOT_FOUND,
            )
        ProviderImage.objects.filter(id=image_id, provider=provider).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class CitiesView(APIView):
    @extend_schema(
        summary="Cidades distintas com contagem de prestadores",
        responses=OpenApiTypes.OBJECT,
    )
    def get(self, request):
        rows = (
            Provider.objects.exclude(city="")
            .values("city", "state")
            .annotate(count=Count("id"))
            .order_by("-count", "city")
        )
        return Response(
            [
                {"city": row["city"], "state": row["state"], "count": row["count"]}
                for row in rows
            ]
        )


def _auth_response(user, http_status=status.HTTP_200_OK):
    """Monta a resposta de login/cadastro: token novo (rotação) no corpo
    E num cookie httpOnly (navegador), conforme o smell fix #2."""
    Token.objects.filter(user=user).delete()
    token = Token.objects.create(user=user)
    response = Response(
        {"token": token.key, "user": UserSerializer(user).data},
        status=http_status,
    )
    response.set_cookie(
        settings.AUTH_COOKIE_NAME,
        token.key,
        max_age=settings.AUTH_COOKIE_MAX_AGE,
        httponly=True,
        secure=settings.AUTH_COOKIE_SECURE,
        samesite=settings.AUTH_COOKIE_SAMESITE,
    )
    return response


class RegisterView(APIView):
    @extend_schema(
        summary="Cria uma conta e devolve o token de autenticacao",
        request=RegisterSerializer,
        responses=OpenApiTypes.OBJECT,
    )
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return _auth_response(user, http_status=status.HTTP_201_CREATED)


class LoginView(APIView):
    @extend_schema(
        summary="Autentica por e-mail/senha e devolve o token",
        request=OpenApiTypes.OBJECT,
        responses=OpenApiTypes.OBJECT,
    )
    def post(self, request):
        email = request.data.get("email", "")
        password = request.data.get("password", "")
        user = authenticate(username=email, password=password)
        if user is None:
            return Response(
                {"detail": "E-mail ou senha invalidos."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return _auth_response(user)


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Encerra a sessao limpando o cookie de token",
        request=None,
        responses={204: None},
    )
    def post(self, request):
        try:
            request.user.auth_token.delete()
        except Exception:
            pass
        response = Response(status=status.HTTP_204_NO_CONTENT)
        response.delete_cookie(settings.AUTH_COOKIE_NAME)
        return response


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Usuario autenticado no momento", responses=UserSerializer
    )
    def get(self, request):
        return Response(UserSerializer(request.user).data)

    @extend_schema(
        summary="Edita os dados do próprio usuário (nome, telefone)",
        request=OpenApiTypes.OBJECT,
        responses=UserSerializer,
    )
    def patch(self, request):
        user = request.user
        nome = request.data.get("first_name")
        if nome is not None:
            user.first_name = str(nome).strip()[:120]
            user.save(update_fields=["first_name"])
        telefone = request.data.get("telefone")
        if telefone is not None:
            profile, _ = UserProfile.objects.get_or_create(user=user)
            profile.telefone = str(telefone).strip()[:15]
            profile.save(update_fields=["telefone"])
        return Response(UserSerializer(user).data)


class StatsView(APIView):
    @extend_schema(
        summary="Totais da plataforma", responses=OpenApiTypes.OBJECT
    )
    def get(self, request):
        qs = Provider.objects.filter(status="approved")
        agg = qs.aggregate(avg=Avg("rating"), jobs=Sum("jobs_done"))
        cities = qs.exclude(city="").values_list("city", flat=True).distinct().count()
        return Response(
            {
                "providers": qs.count(),
                "categories": Category.objects.count(),
                "cities": cities,
                "avg_rating": round(agg["avg"] or 0, 2),
                "jobs_done": agg["jobs"] or 0,
            }
        )


# Smell fix: pesos da recomendacao com nomes explicativos no lugar de numeros
# magicos espalhados. Centralizar facilita calibrar, auditar e testar a regra.
MAX_RATING = 5.0
RATING_WEIGHT = 42  # peso da nota media do prestador
REVIEWS_WEIGHT = 16  # peso do volume de avaliacoes
REVIEWS_SATURATION = 300  # acima disso, mais avaliacoes nao somam pontos
JOBS_WEIGHT = 10  # peso dos servicos concluidos
JOBS_SATURATION = 600  # acima disso, mais servicos nao somam pontos
VERIFIED_BONUS = 8  # bonus fixo para perfil verificado
DISTANCE_WEIGHT = 24  # peso da proximidade do usuario
DISTANCE_RADIUS_KM = 30.0  # raio em que a distancia ainda pontua
DISTANCE_UNKNOWN_PTS = 14  # pontuacao neutra quando nao ha localizacao

FEATURED_RADIUS_KM = 100.0
FEATURED_MIN = 2
FEATURED_MAX = 5
MIN_SCORE = 40
MAX_SCORE = 99
PERSONAL_WEIGHT = 40  # quanto a afinidade (historico de busca) empurra o match no /for-you
DAILY_DECK_LIMIT = 5  # quantos prestadores o usuario pode "swipar" por dia
LOCATION_RADIUS_KM = 60.0  # ate onde um prestador conta como "na localizacao do usuario"


def _swiped_today(user):
    """Quantos swipes vindos do DECK o usuario ja deu hoje (limita a X por dia).

    Favoritar direto no perfil do prestador (source=profile) nao gasta a cota.
    """
    return ProviderSwipe.objects.filter(
        user=user,
        source=ProviderSwipe.DECK,
        created_at__date=timezone.localdate(),
    ).count()


def _score(provider):
    rating = float(provider.rating)
    reviews = provider.reviews_count
    dist = provider.distance_km

    rating_pts = (rating / MAX_RATING) * RATING_WEIGHT
    review_pts = min(reviews / REVIEWS_SATURATION, 1.0) * REVIEWS_WEIGHT
    jobs_pts = min(provider.jobs_done / JOBS_SATURATION, 1.0) * JOBS_WEIGHT
    verified_pts = VERIFIED_BONUS if provider.verified else 0
    dist_pts = (
        max(0.0, 1.0 - dist / DISTANCE_RADIUS_KM) * DISTANCE_WEIGHT
        if dist is not None
        else DISTANCE_UNKNOWN_PTS
    )
    score = round(rating_pts + review_pts + jobs_pts + verified_pts + dist_pts)
    score = max(MIN_SCORE, min(MAX_SCORE, score))

    parts = [f"Nota {rating:.1f}"]
    if reviews:
        parts.append(f"{reviews} avaliacoes")
    if dist is not None and dist <= DISTANCE_RADIUS_KM:
        parts.append(f"a {dist:.1f} km de voce")
    parts.append(f"responde {provider.response_time}")
    return score, "Recomendado por " + ", ".join(parts) + "."


def _replace_query(request, key, value):
    params = request.query_params.copy()
    params[key] = value
    return f"{request.path}?{params.urlencode()}"


class CitiesByStateView(APIView):
    @extend_schema(
        summary="Cidades de um estado via IBGE",
        parameters=[OpenApiParameter("uf", str, location=OpenApiParameter.PATH)],
        responses=OpenApiTypes.OBJECT,
    )
    def get(self, request, uf):
        try:
            req = urllib.request.Request(
                f"https://servicodados.ibge.gov.br/api/v1/localidades/estados/{uf}/municipios",
                headers={"User-Agent": "HIVEE/1.0", "Accept-Encoding": "gzip"},
            )
            with urllib.request.urlopen(req, timeout=8) as res:
                raw = res.read()
                try:
                    text = gzip.decompress(raw).decode()
                except OSError:
                    text = raw.decode()
                data = json.loads(text)
            cities = sorted(
                [{"city": m["nome"], "state": uf.upper()} for m in data],
                key=lambda x: x["city"],
            )
            return Response(cities)
        except Exception as e:
            return Response(
                {"detail": f"Erro ao carregar cidades: {e}"},
                status=status.HTTP_502_BAD_GATEWAY,
            )


class AvatarUploadView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Faz upload da foto do perfil do prestador",
        request=OpenApiTypes.OBJECT,
        responses=OpenApiTypes.OBJECT,
    )
    def post(self, request):
        file = request.FILES.get("avatar")
        if not file:
            return Response({"detail": "Nenhum arquivo enviado."}, status=status.HTTP_400_BAD_REQUEST)
        slug = request.data.get("slug", "")
        provider = Provider.objects.filter(slug=slug, owner=request.user).first()
        if not provider:
            return Response({"detail": "Prestador não encontrado."}, status=status.HTTP_404_NOT_FOUND)
        safe_name = f"{uuid.uuid4()}{os.path.splitext(file.name)[1] if file.name else '.jpg'}"
        provider.avatar.save(safe_name, file, save=True)
        provider.avatar_url = provider.avatar.url
        provider.save(update_fields=["avatar_url"])
        return Response({"avatar_url": provider.avatar.url}, status=status.HTTP_200_OK)


@extend_schema_view(
    list=extend_schema(
        summary="Lista as notificações do usuário logado (paginada)",
        parameters=[
            OpenApiParameter("unread_only", str, description="1 = só não lidas."),
            OpenApiParameter("page", int),
            OpenApiParameter("page_size", int),
        ],
        responses=OpenApiTypes.OBJECT,
    ),
    retrieve=extend_schema(summary="Detalhe de uma notificação", responses=OpenApiTypes.OBJECT),
)
class NotificationViewSet(ViewSet):
    """Histórico e ações sobre as notificações do usuário autenticado."""

    permission_classes = [IsAuthenticated]

    def get_queryset(self, request):
        return Notification.objects.filter(recipient=request.user)

    def list(self, request):
        qs = self.get_queryset(request)
        if request.query_params.get("unread_only") == "1":
            qs = qs.filter(is_read=False)

        try:
            page = max(1, int(request.query_params.get("page", 1)))
            page_size = min(50, max(1, int(request.query_params.get("page_size", 20))))
        except ValueError:
            page, page_size = 1, 20

        total = qs.count()
        start = (page - 1) * page_size
        chunk = qs[start : start + page_size]
        data = [_notification_dict(n) for n in chunk]

        def page_url(n):
            return request.build_absolute_uri(_replace_query(request, "page", n))

        return Response(
            {
                "count": total,
                "next": page_url(page + 1) if start + page_size < total else None,
                "previous": page_url(page - 1) if page > 1 else None,
                "results": data,
            }
        )

    def retrieve(self, request, pk=None):
        n = self.get_queryset(request).filter(pk=pk).first()
        if n is None:
            return Response(
                {"detail": "Notificação não encontrada."}, status=status.HTTP_404_NOT_FOUND
            )
        return Response(_notification_dict(n))

    @action(detail=True, methods=["post"])
    def mark_read(self, request, pk=None):
        n = self.get_queryset(request).filter(pk=pk).first()
        if n is None:
            return Response(
                {"detail": "Notificação não encontrada."}, status=status.HTTP_404_NOT_FOUND
            )
        if not n.is_read:
            n.is_read = True
            n.save(update_fields=["is_read"])
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=["post"])
    def mark_all_read(self, request):
        self.get_queryset(request).filter(is_read=False).update(is_read=True)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=["get"])
    def unread_count(self, request):
        count = self.get_queryset(request).filter(is_read=False).count()
        return Response({"count": count})


def _notification_dict(n: Notification) -> dict:
    return {
        "id": n.id,
        "tipo": n.tipo,
        "title": n.title,
        "body": n.body,
        "link": n.link,
        "payload": n.payload,
        "is_read": n.is_read,
        "created_at": n.created_at.isoformat(),
    }


# ── Suporte ao usuário ─────────────────────────────────────────────────────
# Todo o sistema de suporte exige usuário autenticado (FAQ inclusive).


class FAQArticleListView(ListAPIView):
    """Lista artigos publicados da FAQ."""

    permission_classes = [AllowAny]
    serializer_class = FAQArticleSerializer
    pagination_class = None

    def get_queryset(self):
        qs = FAQArticle.objects.filter(is_published=True).select_related("category")
        category = self.request.query_params.get("category")
        if category:
            qs = qs.filter(category__slug=category)
        search = (self.request.query_params.get("search") or "").strip()
        if search:
            qs = qs.filter(question__icontains=search)
        return qs


class SupportCategoryListView(ListAPIView):
    """Lista categorias de suporte com contagem de artigos publicados."""

    permission_classes = [AllowAny]
    serializer_class = SupportCategorySerializer
    pagination_class = None

    def get_queryset(self):
        return SupportCategory.objects.annotate(
            article_count=Count("articles", filter=Q(articles__is_published=True))
        ).order_by("order", "name")


@extend_schema_view(
    list=extend_schema(summary="Lista tickets de suporte (staff vê todos)"),
    create=extend_schema(summary="Abre um novo ticket de suporte"),
    retrieve=extend_schema(summary="Detalhe de um ticket"),
)
class SupportTicketViewSet(ViewSet):
    """Tickets de suporte com ciclo de vida (open → … → closed).

    O usuário comum só enxerga os próprios tickets; o staff enxerga todos e pode
    designar responsáveis. A máquina de estados (`_allowed_transitions`) decide o
    que cada papel pode fazer em cada status.
    """

    permission_classes = [IsAuthenticated]

    def get_queryset(self, request):
        user = request.user
        base = SupportTicket.objects.select_related("user", "category", "assigned_to")
        base = base.prefetch_related("messages", "logs", "logs__changed_by", "messages__author")
        if user.is_staff:
            return base.all()
        return base.filter(user=user)

    def list(self, request):
        qs = self.get_queryset(request)

        status_filter = request.query_params.get("status")
        if status_filter:
            qs = qs.filter(status=status_filter)

        # Staff pode filtrar por usuário específico.
        user_filter = request.query_params.get("user_id")
        if user_filter and request.user.is_staff:
            qs = qs.filter(user_id=user_filter)

        if request.user.is_staff:
            qs = qs.order_by("-priority", "-updated_at")
        else:
            qs = qs.order_by("-updated_at")

        try:
            page = max(1, int(request.query_params.get("page", 1)))
            page_size = min(50, max(1, int(request.query_params.get("page_size", 20))))
        except ValueError:
            page, page_size = 1, 20

        total = qs.count()
        start = (page - 1) * page_size
        chunk = qs[start : start + page_size]
        data = SupportTicketSerializer(chunk, many=True, context={"request": request}).data

        def page_url(n):
            return request.build_absolute_uri(_replace_query(request, "page", n))

        return Response(
            {
                "count": total,
                "next": page_url(page + 1) if start + page_size < total else None,
                "previous": page_url(page - 1) if page > 1 else None,
                "results": data,
            }
        )

    def create(self, request):
        serializer = SupportTicketSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)

        ticket = SupportTicket.objects.create(
            user=request.user,
            category=serializer.validated_data.get("category"),
            subject=serializer.validated_data["subject"],
            description=serializer.validated_data.get("description", ""),
            priority=serializer.validated_data.get("priority", SupportTicket.Priority.MEDIUM),
            status=SupportTicket.Status.OPEN,
        )

        SupportTicketLog.objects.create(
            ticket=ticket,
            from_status="",
            to_status=SupportTicket.Status.OPEN,
            changed_by=request.user,
            note="Ticket aberto pelo usuário.",
        )

        _notify_staff_new_ticket(ticket)

        return Response(
            SupportTicketSerializer(ticket, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )

    def retrieve(self, request, pk=None):
        ticket = self.get_queryset(request).filter(pk=pk).first()
        if ticket is None:
            return Response(
                {"detail": "Ticket não encontrado."}, status=status.HTTP_404_NOT_FOUND
            )
        return Response(
            SupportTicketSerializer(ticket, context={"request": request}).data
        )

    @action(detail=True, methods=["post"])
    def message(self, request, pk=None):
        """Adiciona uma mensagem ao ticket e atualiza o status automaticamente."""
        ticket = self.get_queryset(request).filter(pk=pk).first()
        if ticket is None:
            return Response(
                {"detail": "Ticket não encontrado."}, status=status.HTTP_404_NOT_FOUND
            )

        content = (request.data.get("content") or "").strip()
        if not content:
            return Response(
                {"detail": "Conteúdo da mensagem é obrigatório."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if ticket.status == SupportTicket.Status.CLOSED:
            return Response(
                {"detail": "Este ticket está fechado e não aceita novas mensagens."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        is_staff = request.user.is_staff
        msg = SupportMessage.objects.create(
            ticket=ticket, author=request.user, content=content, is_staff=is_staff
        )

        # Transição automática conforme o remetente.
        old_status = ticket.status
        new_status = None
        if is_staff:
            if ticket.status in (SupportTicket.Status.OPEN, SupportTicket.Status.WAITING_STAFF):
                new_status = SupportTicket.Status.WAITING_USER
        else:
            if ticket.status in (SupportTicket.Status.WAITING_USER, SupportTicket.Status.RESOLVED):
                new_status = SupportTicket.Status.WAITING_STAFF

        if new_status and new_status != old_status:
            ticket.status = new_status
            ticket.save(update_fields=["status", "updated_at"])
            SupportTicketLog.objects.create(
                ticket=ticket,
                from_status=old_status,
                to_status=new_status,
                changed_by=request.user,
                note="Status atualizado por nova mensagem.",
            )
        else:
            ticket.save(update_fields=["updated_at"])

        if is_staff:
            _notify_ticket_reply(ticket, "Sua solicitação de suporte foi respondida.")
        else:
            _notify_staff_new_message(ticket)

        return Response(
            SupportMessageSerializer(msg).data, status=status.HTTP_201_CREATED
        )

    @action(detail=True, methods=["post"])
    def transition(self, request, pk=None):
        ticket = self.get_queryset(request).filter(pk=pk).first()
        if ticket is None:
            return Response(
                {"detail": "Ticket não encontrado."}, status=status.HTTP_404_NOT_FOUND
            )

        new_status = request.data.get("status", "")
        note = request.data.get("note", "")

        allowed = self._allowed_transitions(ticket, request.user)
        if new_status not in allowed:
            return Response(
                {
                    "detail": f"Transição '{ticket.status}' → '{new_status}' não permitida. "
                    f"Transições possíveis: {', '.join(allowed) if allowed else 'nenhuma'}.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        old_status = ticket.status
        ticket.status = new_status

        timestamp_map = {
            SupportTicket.Status.RESOLVED: "resolved_at",
            SupportTicket.Status.CLOSED: "closed_at",
        }
        if new_status in timestamp_map:
            setattr(ticket, timestamp_map[new_status], timezone.now())
        ticket.save()

        SupportTicketLog.objects.create(
            ticket=ticket,
            from_status=old_status,
            to_status=new_status,
            changed_by=request.user,
            note=note,
        )

        # Avisa a contraparte sobre a mudança relevante.
        if request.user.is_staff and new_status == SupportTicket.Status.RESOLVED:
            _notify_ticket_reply(ticket, "Seu ticket foi marcado como resolvido.")

        return Response(
            SupportTicketSerializer(ticket, context={"request": request}).data
        )

    @action(detail=True, methods=["post"])
    def assign(self, request, pk=None):
        """Staff designa um responsável pelo ticket."""
        if not request.user.is_staff:
            return Response(
                {"detail": "Apenas a equipe pode designar responsáveis."},
                status=status.HTTP_403_FORBIDDEN,
            )

        ticket = self.get_queryset(request).filter(pk=pk).first()
        if ticket is None:
            return Response(
                {"detail": "Ticket não encontrado."}, status=status.HTTP_404_NOT_FOUND
            )

        user_id = request.data.get("user_id")
        member = get_user_model().objects.filter(pk=user_id, is_staff=True).first()
        if member is None:
            return Response(
                {"detail": "Membro da equipe não encontrado."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        ticket.assigned_to = member
        ticket.save(update_fields=["assigned_to", "updated_at"])

        SupportTicketLog.objects.create(
            ticket=ticket,
            from_status=ticket.status,
            to_status=ticket.status,
            changed_by=request.user,
            note=f"Ticket designado para {member.first_name or member.email}.",
        )

        return Response(
            SupportTicketSerializer(ticket, context={"request": request}).data
        )

    @action(detail=False, methods=["get"])
    def counts(self, request):
        """Contagem de tickets agrupados por status (respeita o escopo do usuário)."""
        qs = self.get_queryset(request)
        counts = qs.values("status").annotate(count=Count("id")).order_by("status")
        return Response({item["status"]: item["count"] for item in counts})

    # ── Máquina de estados ─────────────────────────────────────────────
    @staticmethod
    def _allowed_transitions(ticket, user):
        is_staff = user.is_staff

        transitions = {
            SupportTicket.Status.OPEN: [
                SupportTicket.Status.WAITING_STAFF,
                SupportTicket.Status.CLOSED,
            ],
            SupportTicket.Status.WAITING_USER: [
                SupportTicket.Status.RESOLVED,
            ],
            SupportTicket.Status.WAITING_STAFF: [
                SupportTicket.Status.WAITING_USER,
                SupportTicket.Status.CLOSED,
            ],
            SupportTicket.Status.RESOLVED: [
                SupportTicket.Status.CLOSED,
                SupportTicket.Status.WAITING_STAFF,
            ],
            SupportTicket.Status.CLOSED: [],
        }

        allowed = list(transitions.get(ticket.status, []))

        if not is_staff:
            if ticket.status == SupportTicket.Status.OPEN:
                return [s for s in allowed if s == SupportTicket.Status.CLOSED]
            if ticket.status == SupportTicket.Status.WAITING_STAFF:
                return [s for s in allowed if s == SupportTicket.Status.CLOSED]
            if ticket.status == SupportTicket.Status.RESOLVED:
                return [
                    s
                    for s in allowed
                    if s in (SupportTicket.Status.CLOSED, SupportTicket.Status.WAITING_STAFF)
                ]
            return []

        return allowed


# ── Helpers de notificação do suporte ──────────────────────────────────────
# Reusam o serviço central `catalog.services.notify_user`. As chamadas degradam
# de forma silenciosa: uma falha de notificação nunca derruba o fluxo do ticket.


def _safe_notify(**kwargs):
    try:
        from ..services import notify_user

        notify_user(**kwargs)
    except Exception:  # pragma: no cover - notificação é best-effort
        import logging

        logging.getLogger(__name__).exception("Falha ao notificar (%s)", kwargs.get("tipo"))


def _notify_staff_new_ticket(ticket):
    """Notifica toda a equipe staff ativa sobre um novo ticket."""
    staff = get_user_model().objects.filter(is_staff=True, is_active=True)
    for member in staff:
        if member.id == ticket.user_id:
            continue
        _safe_notify(
            recipient=member,
            tipo="new_ticket",
            title="Novo ticket de suporte",
            body=f"{ticket.user.first_name or ticket.user.email}: {ticket.subject[:80]}",
            link=f"/admin/catalog/supportticket/{ticket.id}/change/",
            payload={"ticket_id": ticket.id, "user_id": ticket.user_id},
        )


def _notify_staff_new_message(ticket):
    """Notifica o responsável (ou toda a staff) sobre nova mensagem do usuário."""
    if ticket.assigned_to_id:
        recipients = [ticket.assigned_to]
    else:
        recipients = get_user_model().objects.filter(is_staff=True, is_active=True)

    last = ticket.messages.last()
    for member in recipients:
        if member.id == ticket.user_id:
            continue
        _safe_notify(
            recipient=member,
            tipo="ticket_message",
            title=f"Resposta em: {ticket.subject[:60]}",
            body=last.content[:120] if last else "",
            link=f"/admin/catalog/supportticket/{ticket.id}/change/",
            payload={"ticket_id": ticket.id},
        )


def _notify_ticket_reply(ticket, title):
    """Notifica o usuário dono do ticket sobre uma resposta/mudança da equipe."""
    last = ticket.messages.last()
    _safe_notify(
        recipient=ticket.user,
        tipo="ticket_reply",
        title=title,
        body=last.content[:120] if last else "",
        link=f"/suporte/tickets/{ticket.id}",
        payload={"ticket_id": ticket.id},
        via_whatsapp=True,
    )


# ── Demandas (cliente publica, prestador verificado se oferece) ─────────────
DEMAND_PREFETCH = ("tags",)
DEMAND_SELECT = ("category", "client")


def _approved_provider(user):
    """Retorna o Provider APROVADO do usuário logado, ou None.

    É a fonte de verdade para "prestador verificado": só quem tem um perfil de
    prestador com `status=approved` pode ver o feed de demandas e se oferecer.
    """
    if not user or not user.is_authenticated:
        return None
    return (
        Provider.objects.select_related("category")
        .prefetch_related(*PROVIDER_PREFETCH)
        .filter(owner=user, status="approved")
        .first()
    )


def _demand_base():
    return Demand.objects.select_related(*DEMAND_SELECT).prefetch_related(*DEMAND_PREFETCH)


@extend_schema_view(
    list=extend_schema(
        summary="Feed de demandas abertas (prestador verificado) ou as próprias do cliente",
        parameters=[
            OpenApiParameter("category", str, description="Slug da categoria."),
            OpenApiParameter("city", str, description="Filtra por cidade."),
            OpenApiParameter("search", str, description="Busca no título/descrição."),
            OpenApiParameter("lat", float),
            OpenApiParameter("lng", float),
            OpenApiParameter("page", int),
            OpenApiParameter("page_size", int),
        ],
        responses=OpenApiTypes.OBJECT,
    ),
    create=extend_schema(
        summary="Cria uma demanda (qualquer usuário autenticado)",
        request=CreateDemandSerializer,
        responses=DemandSerializer,
    ),
    retrieve=extend_schema(summary="Detalhe da demanda (+ ofertas, se for o dono)"),
)
class DemandViewSet(ViewSet):
    """Demandas estilo TaskRabbit.

    - Qualquer usuário autenticado **cria** demandas.
    - Apenas prestadores **aprovados** veem o feed de abertas e podem se oferecer.
    - Só o **dono** vê as ofertas recebidas e aceita/recusa.
    """

    permission_classes = [IsAuthenticated]

    # ── Listagem ───────────────────────────────────────────────────────
    def list(self, request):
        provider = _approved_provider(request.user)
        if provider:
            qs = _demand_base().filter(status="open").exclude(client=request.user)
            category = request.query_params.get("category")
            if category:
                qs = qs.filter(category__slug=category)
            city = request.query_params.get("city")
            if city:
                qs = qs.filter(city__icontains=city)
            search = (request.query_params.get("search") or "").strip()
            if search:
                qs = qs.filter(
                    Q(title__icontains=search) | Q(description__icontains=search)
                )
        else:
            # Quem não é prestador aprovado só enxerga as próprias demandas aqui.
            qs = _demand_base().filter(client=request.user)

        try:
            page = max(1, int(request.query_params.get("page", 1)))
            page_size = min(48, max(1, int(request.query_params.get("page_size", 12))))
        except ValueError:
            page, page_size = 1, 12

        total = qs.count()
        start = (page - 1) * page_size
        chunk = list(qs[start : start + page_size])

        lat, lng = _parse_point(request)
        _attach_distance(chunk, lat, lng)

        context = {"request": request}
        if provider:
            context["offered_demand_ids"] = set(
                DemandOffer.objects.filter(
                    provider=provider, demand_id__in=[d.id for d in chunk]
                ).values_list("demand_id", flat=True)
            )
        data = DemandSerializer(chunk, many=True, context=context).data

        def page_url(n):
            return request.build_absolute_uri(_replace_query(request, "page", n))

        return Response(
            {
                "count": total,
                "next": page_url(page + 1) if start + page_size < total else None,
                "previous": page_url(page - 1) if page > 1 else None,
                "results": data,
            }
        )

    def create(self, request):
        serializer = CreateDemandSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        demand = serializer.save(client=request.user)
        demand = _demand_base().get(pk=demand.pk)
        return Response(
            DemandSerializer(demand, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )

    def retrieve(self, request, pk=None):
        demand = _demand_base().filter(pk=pk).first()
        if demand is None:
            return Response({"detail": "Demanda não encontrada."}, status=status.HTTP_404_NOT_FOUND)

        is_owner = demand.client_id == request.user.id
        provider = _approved_provider(request.user)
        my_offer = (
            DemandOffer.objects.filter(demand=demand, provider=provider).first()
            if provider
            else None
        )

        # Visibilidade: dono sempre; prestador aprovado se a demanda está aberta
        # ou se ele já se ofereceu nela.
        if not is_owner and not (provider and (demand.status == "open" or my_offer)):
            return Response({"detail": "Demanda não encontrada."}, status=status.HTTP_404_NOT_FOUND)

        lat, lng = _parse_point(request)
        _attach_distance([demand], lat, lng)

        context = {"request": request}
        if my_offer:
            context["offered_demand_ids"] = {demand.id}
        data = DemandSerializer(demand, context=context).data
        data["is_owner"] = is_owner

        if is_owner:
            offers = (
                DemandOffer.objects.filter(demand=demand)
                .select_related("provider__category")
                .prefetch_related(
                    "provider__tags", "provider__images", "provider__availability_slots"
                )
            )
            data["offers"] = DemandOfferSerializer(offers, many=True).data
        elif my_offer:
            data["my_offer"] = DemandOfferSerializer(my_offer).data

        return Response(data)

    def partial_update(self, request, pk=None):
        """O dono edita a demanda: encerrar/cancelar ou ajustar os textos."""
        demand = Demand.objects.filter(pk=pk, client=request.user).first()
        if demand is None:
            return Response(
                {"detail": "Você não pode editar esta demanda."},
                status=status.HTTP_404_NOT_FOUND,
            )

        new_status = request.data.get("status")
        if new_status is not None:
            if new_status not in ("closed", "cancelled", "open"):
                return Response(
                    {"detail": "Status inválido. Use 'closed', 'cancelled' ou 'open'."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            demand.status = new_status

        for field in ("title", "description", "preferred_schedule", "budget_hint", "city", "neighborhood", "state"):
            if field in request.data:
                setattr(demand, field, str(request.data[field])[:2000])

        demand.save()
        demand = _demand_base().get(pk=demand.pk)
        return Response(DemandSerializer(demand, context={"request": request}).data)

    # ── Ofertas ────────────────────────────────────────────────────────
    @action(detail=True, methods=["get", "post"], url_path="offers")
    def offers(self, request, pk=None):
        demand = Demand.objects.filter(pk=pk).first()
        if demand is None:
            return Response({"detail": "Demanda não encontrada."}, status=status.HTTP_404_NOT_FOUND)

        if request.method == "GET":
            if demand.client_id != request.user.id:
                return Response(
                    {"detail": "Apenas o dono da demanda vê as ofertas."},
                    status=status.HTTP_403_FORBIDDEN,
                )
            offers = (
                DemandOffer.objects.filter(demand=demand)
                .select_related("provider__category")
                .prefetch_related(
                    "provider__tags", "provider__images", "provider__availability_slots"
                )
            )
            return Response(DemandOfferSerializer(offers, many=True).data)

        # POST → prestador aprovado se oferece
        provider = _approved_provider(request.user)
        if not provider:
            return Response(
                {"detail": "Apenas prestadores verificados podem se oferecer."},
                status=status.HTTP_403_FORBIDDEN,
            )
        if demand.client_id == request.user.id:
            return Response(
                {"detail": "Você não pode se oferecer para a própria demanda."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if demand.status != "open":
            return Response(
                {"detail": "Esta demanda não está mais aberta para ofertas."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if DemandOffer.objects.filter(demand=demand, provider=provider).exists():
            return Response(
                {"detail": "Você já se ofereceu para esta demanda."},
                status=status.HTTP_409_CONFLICT,
            )

        serializer = CreateOfferSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        offer = DemandOffer.objects.create(
            demand=demand, provider=provider, **serializer.validated_data
        )
        Demand.objects.filter(pk=demand.pk).update(offer_count=F("offer_count") + 1)

        _notify_demand_new_offer(offer)

        return Response(
            DemandOfferSerializer(offer).data, status=status.HTTP_201_CREATED
        )

    @action(detail=True, methods=["patch"], url_path=r"offers/(?P<offer_id>[0-9]+)")
    def offer_detail(self, request, pk=None, offer_id=None):
        """O dono aceita/recusa uma oferta. Aceitar recusa as demais e põe a
        demanda em andamento."""
        demand = Demand.objects.filter(pk=pk, client=request.user).first()
        if demand is None:
            return Response(
                {"detail": "Você não pode gerenciar ofertas desta demanda."},
                status=status.HTTP_404_NOT_FOUND,
            )
        offer = DemandOffer.objects.filter(pk=offer_id, demand=demand).first()
        if offer is None:
            return Response({"detail": "Oferta não encontrada."}, status=status.HTTP_404_NOT_FOUND)

        new_status = request.data.get("status")
        if new_status not in ("accepted", "rejected"):
            return Response(
                {"detail": "status deve ser 'accepted' ou 'rejected'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if new_status == "accepted":
            offer.status = "accepted"
            offer.save(update_fields=["status"])
            # As demais ofertas pendentes são recusadas automaticamente.
            rejected = list(
                DemandOffer.objects.filter(demand=demand, status="pending").exclude(pk=offer.pk)
            )
            DemandOffer.objects.filter(demand=demand, status="pending").exclude(
                pk=offer.pk
            ).update(status="rejected")
            demand.status = "in_progress"
            demand.save(update_fields=["status", "updated_at"])
            _notify_demand_offer_decision(offer, accepted=True)
            for other in rejected:
                _notify_demand_offer_decision(other, accepted=False)
        else:
            offer.status = "rejected"
            offer.save(update_fields=["status"])
            _notify_demand_offer_decision(offer, accepted=False)

        return Response(DemandOfferSerializer(offer).data)

    # ── Painéis do usuário ─────────────────────────────────────────────
    @action(detail=False, methods=["get"], url_path="mine")
    def mine(self, request):
        """Demandas criadas pelo usuário logado (painel do cliente)."""
        demands = _demand_base().filter(client=request.user)
        return Response(
            DemandSerializer(demands, many=True, context={"request": request}).data
        )

    @action(detail=False, methods=["get"], url_path="my-offers")
    def my_offers(self, request):
        """Ofertas que o prestador logado fez (painel do prestador)."""
        provider = _approved_provider(request.user)
        if not provider:
            return Response([])
        offers = (
            DemandOffer.objects.filter(provider=provider)
            .select_related("demand__category", "demand__client")
            .prefetch_related("demand__tags")
        )
        data = []
        for offer in offers:
            data.append(
                {
                    "id": offer.id,
                    "status": offer.status,
                    "message": offer.message,
                    "suggested_value": (
                        float(offer.suggested_value) if offer.suggested_value is not None else None
                    ),
                    "created_at": offer.created_at.isoformat(),
                    "demand": DemandSerializer(offer.demand, context={"request": request}).data,
                }
            )
        return Response(data)


# ── Helpers de notificação das demandas ─────────────────────────────────────
def _notify_demand_new_offer(offer):
    """Avisa o cliente dono da demanda que recebeu uma nova oferta."""
    demand = offer.demand
    _safe_notify(
        recipient=demand.client,
        tipo="demand_new_offer",
        title="Nova oferta na sua demanda",
        body=f"{offer.provider.name} se ofereceu para “{demand.title[:80]}”.",
        link=f"/demanda/{demand.id}",
        payload={"demand_id": demand.id, "offer_id": offer.id, "provider_slug": offer.provider.slug},
        via_whatsapp=True,
    )


def _notify_demand_offer_decision(offer, accepted: bool):
    """Avisa o prestador que sua oferta foi aceita ou recusada."""
    owner = offer.provider.owner
    if not owner:
        return
    demand = offer.demand
    if accepted:
        title = "Sua oferta foi aceita! 🎉"
        body = f"O cliente aceitou sua oferta para “{demand.title[:80]}”. Combine os detalhes."
    else:
        title = "Oferta não selecionada"
        body = f"O cliente escolheu outro profissional para “{demand.title[:80]}”."
    _safe_notify(
        recipient=owner,
        tipo="demand_offer_accepted" if accepted else "demand_offer_rejected",
        title=title,
        body=body,
        link="/minhas-ofertas",
        payload={"demand_id": demand.id, "offer_id": offer.id},
        via_whatsapp=accepted,
    )
