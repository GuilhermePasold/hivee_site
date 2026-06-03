from django.contrib.auth import authenticate
from django.db.models import Avg, Count, Sum
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ViewSet

from ..geo import haversine_km
from ..models import Category, Provider
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
            else None
        )
    return providers


class CategoryListView(ListAPIView):
    serializer_class = CategorySerializer
    pagination_class = None

    def get_queryset(self):
        return Category.objects.annotate(provider_count=Count("providers")).order_by(
            "order", "name"
        )


class ProviderViewSet(ViewSet):
    lookup_field = "slug"

    def _filtered(self, request):
        qs = Provider.objects.select_related("category").all()
        category = request.query_params.get("category")
        if category:
            qs = qs.filter(category__slug=category)

        city = request.query_params.get("city")
        if city:
            qs = qs.filter(city__icontains=city)

        items = list(qs)
        search = (request.query_params.get("search") or "").strip().lower()
        if search:
            terms = search.split()

            def matches(provider):
                haystack = " ".join(
                    [
                        provider.name,
                        provider.headline,
                        provider.category.name,
                        provider.city,
                        provider.neighborhood,
                        " ".join(provider.skills),
                    ]
                ).lower()
                return all(term in haystack for term in terms)

            items = [provider for provider in items if matches(provider)]

        lat, lng = _parse_point(request)
        _attach_distance(items, lat, lng)

        ordering = request.query_params.get("ordering", "")
        if ordering == "distance" and lat is not None:
            items.sort(key=lambda provider: provider.distance_km)
        elif ordering == "-rating":
            items.sort(
                key=lambda provider: (float(provider.rating), provider.reviews_count),
                reverse=True,
            )
        elif ordering == "hourly_rate":
            items.sort(key=lambda provider: float(provider.hourly_rate))
        else:
            items.sort(
                key=lambda provider: (
                    provider.top_rated,
                    float(provider.rating),
                    provider.reviews_count,
                ),
                reverse=True,
            )
        return items

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
        lat, lng = _parse_point(request)
        _attach_distance([provider], lat, lng)
        return Response(ProviderSerializer(provider).data)

    @action(detail=False, methods=["get"])
    def recommended(self, request):
        lat, lng = _parse_point(request)
        providers = list(Provider.objects.select_related("category").all())
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
        if not request.user.is_authenticated:
            return Response(
                {"detail": "Entre na sua conta para se cadastrar como profissional."},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        serializer = ProviderWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        provider = serializer.save(owner=request.user, verified=False)
        return Response(
            ProviderSerializer(provider).data, status=status.HTTP_201_CREATED
        )


class CitiesView(APIView):
    def get(self, request):
        rows = (
            Provider.objects.values("city", "state")
            .annotate(count=Count("id"))
            .order_by("-count", "city")
        )
        return Response(
            [
                {"city": row["city"], "state": row["state"], "count": row["count"]}
                for row in rows
            ]
        )


class RegisterView(APIView):
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        token, _ = Token.objects.get_or_create(user=user)
        return Response(
            {"token": token.key, "user": UserSerializer(user).data},
            status=status.HTTP_201_CREATED,
        )


class LoginView(APIView):
    def post(self, request):
        email = request.data.get("email", "")
        password = request.data.get("password", "")
        user = authenticate(username=email, password=password)
        if user is None:
            return Response(
                {"detail": "E-mail ou senha invalidos."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        token, _ = Token.objects.get_or_create(user=user)
        return Response({"token": token.key, "user": UserSerializer(user).data})


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data)


class StatsView(APIView):
    def get(self, request):
        agg = Provider.objects.aggregate(avg=Avg("rating"), jobs=Sum("jobs_done"))
        cities = Provider.objects.values_list("city", flat=True).distinct().count()
        return Response(
            {
                "providers": Provider.objects.count(),
                "categories": Category.objects.count(),
                "cities": cities,
                "avg_rating": round(agg["avg"] or 0, 2),
                "jobs_done": agg["jobs"] or 0,
            }
        )


def _score(provider):
    rating = float(provider.rating)
    reviews = provider.reviews_count
    dist = provider.distance_km

    rating_pts = (rating / 5.0) * 42
    review_pts = min(reviews / 300.0, 1.0) * 16
    jobs_pts = min(provider.jobs_done / 600.0, 1.0) * 10
    verified_pts = 8 if provider.verified else 0
    dist_pts = max(0.0, 1.0 - dist / 30.0) * 24 if dist is not None else 14
    score = round(rating_pts + review_pts + jobs_pts + verified_pts + dist_pts)
    score = max(40, min(99, score))

    parts = [f"Nota {rating:.1f}"]
    if reviews:
        parts.append(f"{reviews} avaliacoes")
    if dist is not None and dist <= 30:
        parts.append(f"a {dist:.1f} km de voce")
    parts.append(f"responde {provider.response_time}")
    return score, "Recomendado por " + ", ".join(parts) + "."


def _replace_query(request, key, value):
    params = request.query_params.copy()
    params[key] = value
    return f"{request.path}?{params.urlencode()}"
