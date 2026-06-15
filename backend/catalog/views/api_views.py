import gzip
import json
import os
import uuid
import urllib.request

from django.conf import settings
from django.contrib.auth import authenticate
from django.db.models import Avg, Count, Sum
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ViewSet

from ..geo import haversine_km
from ..models import Category, Provider, UserProfile
from ..serializers import (
    CategorySerializer,
    ProviderSerializer,
    ProviderWriteSerializer,
    RecommendationSerializer,
    RegisterSerializer,
    UserSerializer,
)


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


def _matches_terms(provider, terms):
    """True quando todos os termos da busca aparecem nos campos do prestador."""
    haystack = " ".join(
        [
            provider.name,
            provider.headline,
            provider.category.name,
            provider.city or "",
            provider.neighborhood or "",
            " ".join(provider.skills),
        ]
    ).lower()
    return all(term in haystack for term in terms)


class CategoryListView(ListAPIView):
    serializer_class = CategorySerializer
    pagination_class = None

    def get_queryset(self):
        return Category.objects.annotate(provider_count=Count("providers")).order_by(
            "order", "name"
        )


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
        qs = Provider.objects.select_related("category")
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
        provider = Provider.objects.select_related("category").get(slug=slug)
        user = request.user
        if provider.status != "approved" and not (user.is_staff or user.is_superuser) and provider.owner != user:
            return Response(
                {"detail": "Profissional não encontrado."},
                status=status.HTTP_404_NOT_FOUND,
            )
        lat, lng = _parse_point(request)
        _attach_distance([provider], lat, lng)
        return Response(ProviderSerializer(provider).data)

    @action(detail=False, methods=["get"])
    def recommended(self, request):
        lat, lng = _parse_point(request)
        providers = list(Provider.objects.select_related("category").filter(status="approved"))
        _attach_distance(providers, lat, lng)

        scored = []
        for provider in providers:
            score, reason = _score(provider)
            provider.match_score = score
            provider.match_reason = reason
            scored.append(provider)

        scored.sort(key=lambda provider: provider.match_score, reverse=True)
        return Response(RecommendationSerializer(scored[:8], many=True).data)

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
MIN_SCORE = 40
MAX_SCORE = 99


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
