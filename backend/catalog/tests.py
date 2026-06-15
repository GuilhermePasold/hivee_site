"""Testes automatizados da API REST do HIVEE (Django REST Framework).

Cobrem: listagem/paginacao, detalhe por slug, acao `recommended`, controle de
permissao (leitura publica x escrita autenticada), fluxo de autenticacao por
token e disponibilidade da documentacao (schema + Swagger).

Rodar:  python manage.py test
"""
import tempfile

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from rest_framework import status
from rest_framework.test import APITestCase

from .models import (
    Category,
    FAQArticle,
    Provider,
    ProviderImage,
    SupportCategory,
    SupportTicket,
    Tag,
)

User = get_user_model()

# PNG 1x1 válido (para testar upload de galeria sem depender de arquivos externos).
TINY_PNG = bytes.fromhex(
    "89504e470d0a1a0a0000000d4948445200000001000000010802000000907753de"
    "0000000c4944415408d76360000000020001e221bc330000000049454e44ae426082"
)


class ApiTestBase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.category = Category.objects.create(
            name="Eletrica", slug="eletrica", icon="Zap", order=1
        )
        cls.provider = Provider.objects.create(
            name="Carlos Eletricista",
            slug="carlos-eletricista",
            headline="Instalacoes e reparos eletricos",
            category=cls.category,
            avatar_url="https://example.com/avatar.png",
            rating=4.8,
            reviews_count=120,
            jobs_done=300,
            hourly_rate=90,
            city="Campinas",
            neighborhood="Centro",
            state="SP",
            latitude=-22.9,
            longitude=-47.06,
            verified=True,
            skills=["eletrica", "reparos"],
            status="approved",
        )
        cls.user = User.objects.create_user(
            username="cliente@hivee.dev",
            email="cliente@hivee.dev",
            password="senha123",
            first_name="Cliente",
        )


class ReadEndpointsTests(ApiTestBase):
    def test_categories_list(self):
        res = self.client.get("/api/categories/")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data[0]["slug"], "eletrica")
        self.assertEqual(res.data[0]["provider_count"], 1)

    def test_providers_list_is_paginated(self):
        res = self.client.get("/api/providers/")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["count"], 1)
        self.assertIn("results", res.data)
        self.assertEqual(res.data["results"][0]["slug"], "carlos-eletricista")

    def test_provider_detail_by_slug(self):
        res = self.client.get(f"/api/providers/{self.provider.slug}/")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["name"], "Carlos Eletricista")

    def test_recommended_action(self):
        res = self.client.get("/api/providers/recommended/?lat=-22.9&lng=-47.06")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(res.data), 1)
        self.assertIn("match_score", res.data[0])
        self.assertIn("match_reason", res.data[0])

    def test_search_filter(self):
        res = self.client.get("/api/providers/?search=eletricista")
        self.assertEqual(res.data["count"], 1)
        res = self.client.get("/api/providers/?search=encanador")
        self.assertEqual(res.data["count"], 0)

    def test_stats_and_cities(self):
        self.assertEqual(self.client.get("/api/stats/").status_code, 200)
        self.assertEqual(self.client.get("/api/cities/").status_code, 200)


class PermissionTests(ApiTestBase):
    payload = {
        "name": "Nova Profissional",
        "headline": "Pintura residencial",
        "bio": "Experiencia de 10 anos",
        "category": "eletrica",
        "hourly_rate": 70,
        "city": "Campinas",
        "neighborhood": "Cambui",
        "state": "SP",
        "latitude": -22.9,
        "longitude": -47.06,
        "response_time": "em 1 hora",
        "availability": "Disponivel",
        "skills": ["pintura"],
    }

    def test_anonymous_can_read(self):
        self.assertEqual(self.client.get("/api/providers/").status_code, 200)

    def test_anonymous_cannot_write(self):
        res = self.client.post("/api/providers/", self.payload, format="json")
        self.assertIn(
            res.status_code,
            (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN),
        )

    def test_authenticated_can_write_without_avatar(self):
        self.client.force_authenticate(user=self.user)
        res = self.client.post("/api/providers/", self.payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertIsNone(res.data["avatar_url"])
        self.assertFalse(res.data["verified"])


class AuthFlowTests(ApiTestBase):
    def test_register_returns_token(self):
        res = self.client.post(
            "/api/auth/register/",
            {"name": "Maria", "email": "maria@hivee.dev", "password": "senha123"},
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertIn("token", res.data)
        self.assertEqual(res.data["user"]["email"], "maria@hivee.dev")

    def test_login_returns_token(self):
        res = self.client.post(
            "/api/auth/login/",
            {"email": "cliente@hivee.dev", "password": "senha123"},
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn("token", res.data)

    def test_login_invalid_credentials(self):
        res = self.client.post(
            "/api/auth/login/",
            {"email": "cliente@hivee.dev", "password": "errada"},
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_me_requires_authentication(self):
        self.assertEqual(self.client.get("/api/auth/me/").status_code, 401)
        self.client.force_authenticate(user=self.user)
        res = self.client.get("/api/auth/me/")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["email"], "cliente@hivee.dev")


class DocumentationTests(ApiTestBase):
    def test_schema_available(self):
        self.assertEqual(self.client.get("/api/schema/").status_code, 200)

    def test_swagger_docs_available(self):
        self.assertEqual(self.client.get("/api/docs/").status_code, 200)


class MatchSwipeTests(ApiTestBase):
    """Sistema de match: deck personalizado via logs, swipe e favoritos."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.encanamento = Category.objects.create(
            name="Encanamento", slug="encanamento", icon="Wrench", order=2
        )
        # Três encanadores para o deck personalizado priorizar.
        for i in range(3):
            Provider.objects.create(
                name=f"Encanador {i}",
                slug=f"encanador-{i}",
                headline="Conserto de encanamento e vazamentos",
                category=cls.encanamento,
                rating=4.5,
                reviews_count=50,
                jobs_done=100,
                hourly_rate=80,
                city="Campinas",
                state="SP",
                skills=["encanador", "vazamento"],
                status="approved",
            )

    def _log_search(self, termo):
        """Simula o registro de busca que o middleware de logs gravaria."""
        from logs.models import LogEvent

        LogEvent.objects.create(
            tipo="search",
            usuario=self.user,
            rota="/api/providers/",
            metodo="GET",
            payload={"query": {"search": [termo]}},
        )

    def test_for_you_requires_auth(self):
        self.assertEqual(self.client.get("/api/providers/for-you/").status_code, 401)

    def test_for_you_prioritizes_searched_category(self):
        # O usuário buscou "encanador" várias vezes -> encanadores no topo.
        for _ in range(3):
            self._log_search("encanador")
        self.client.force_authenticate(user=self.user)
        res = self.client.get("/api/providers/for-you/")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertGreater(len(res.data["results"]), 0)
        self.assertEqual(res.data["results"][0]["category"]["slug"], "encanamento")
        self.assertIn("match_score", res.data["results"][0])
        self.assertEqual(res.data["daily_limit"], 5)

    def test_for_you_empty_without_search(self):
        # Quem nunca pesquisou nada NÃO recebe recomendações.
        self.client.force_authenticate(user=self.user)
        res = self.client.get("/api/providers/for-you/")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertFalse(res.data["has_searched"])
        self.assertEqual(res.data["results"], [])

    def test_for_you_fills_searched_and_similar(self):
        # Buscou "encanador" -> deck tem categoria buscada (encanamento) E parecida (eletrica).
        self._log_search("encanador")
        self.client.force_authenticate(user=self.user)
        res = self.client.get("/api/providers/for-you/")
        cats = [p["category"]["slug"] for p in res.data["results"]]
        self.assertIn("encanamento", cats)  # categoria buscada
        self.assertIn("eletrica", cats)  # categoria parecida (similar de encanamento)

    def test_for_you_prioritizes_location(self):
        # Um encanador perto do usuário (nota baixa) deve vir antes pelo nível "localização".
        Provider.objects.create(
            name="Encanador Pertinho",
            slug="encanador-perto",
            headline="Encanamento ali do lado",
            category=self.encanamento,
            rating=3.0,
            reviews_count=2,
            hourly_rate=70,
            city="Local",
            state="SP",
            latitude=-23.0,
            longitude=-46.0,
            skills=["encanador"],
            status="approved",
        )
        self._log_search("encanador")
        self.client.force_authenticate(user=self.user)
        res = self.client.get("/api/providers/for-you/?lat=-23.0&lng=-46.0")
        self.assertEqual(res.data["results"][0]["slug"], "encanador-perto")

    def test_for_you_capped_at_daily_limit(self):
        self._log_search("encanador")
        # Cria prestadores suficientes e gasta a cota de 5/dia.
        for i in range(8):
            Provider.objects.create(
                name=f"Extra {i}",
                slug=f"extra-{i}",
                headline="Serviço geral",
                category=self.encanamento,
                rating=4,
                hourly_rate=70,
                city="Campinas",
                state="SP",
                skills=["geral"],
                status="approved",
            )
        self.client.force_authenticate(user=self.user)
        # Deck nunca entrega mais que o limite diário de uma vez.
        res = self.client.get("/api/providers/for-you/")
        self.assertLessEqual(len(res.data["results"]), 5)

        # Gasta a cota dando swipe em 5 prestadores distintos.
        for prov in Provider.objects.filter(status="approved")[:5]:
            r = self.client.post(
                f"/api/providers/{prov.slug}/swipe/", {"action": "dislike"}, format="json"
            )
            self.assertEqual(r.status_code, status.HTTP_200_OK)

        # Agora o deck do dia está esgotado.
        res = self.client.get("/api/providers/for-you/")
        self.assertEqual(res.data["remaining_today"], 0)
        self.assertEqual(len(res.data["results"]), 0)

        # E um 6º swipe novo é barrado com 429.
        sexto = Provider.objects.filter(status="approved").exclude(
            swipes__user=self.user
        ).first()
        r = self.client.post(
            f"/api/providers/{sexto.slug}/swipe/", {"action": "like"}, format="json"
        )
        self.assertEqual(r.status_code, status.HTTP_429_TOO_MANY_REQUESTS)

    def test_like_creates_favorite_and_dislike_hides(self):
        self._log_search("encanador")
        self.client.force_authenticate(user=self.user)
        # Curtir um encanador
        res = self.client.post(
            "/api/providers/encanador-0/swipe/", {"action": "like"}, format="json"
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        # Aparece nos favoritos
        favs = self.client.get("/api/providers/favorites/")
        self.assertEqual(favs.status_code, status.HTTP_200_OK)
        slugs = {p["slug"] for p in favs.data}
        self.assertIn("encanador-0", slugs)
        # Passar (dislike) em outro
        self.client.post(
            "/api/providers/encanador-1/swipe/", {"action": "dislike"}, format="json"
        )
        # Quem já recebeu swipe não volta no deck
        deck = self.client.get("/api/providers/for-you/")
        deck_slugs = {p["slug"] for p in deck.data["results"]}
        self.assertNotIn("encanador-0", deck_slugs)
        self.assertNotIn("encanador-1", deck_slugs)

    def test_swipe_invalid_action_rejected(self):
        self.client.force_authenticate(user=self.user)
        res = self.client.post(
            "/api/providers/encanador-0/swipe/", {"action": "maybe"}, format="json"
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unfavorite_removes_from_list(self):
        self.client.force_authenticate(user=self.user)
        self.client.post(
            "/api/providers/encanador-0/swipe/", {"action": "like"}, format="json"
        )
        res = self.client.delete("/api/providers/encanador-0/swipe/")
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        favs = self.client.get("/api/providers/favorites/")
        self.assertEqual(len(favs.data), 0)

    def test_profile_favorite_does_not_spend_daily_quota(self):
        # Favoritar direto no perfil (source=profile) não gasta a cota do deck.
        self._log_search("encanador")
        self.client.force_authenticate(user=self.user)
        res = self.client.post(
            "/api/providers/encanador-0/swipe/",
            {"action": "like", "source": "profile"},
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        deck = self.client.get("/api/providers/for-you/")
        self.assertEqual(deck.data["remaining_today"], 5)  # cota intacta
        favs = self.client.get("/api/providers/favorites/")
        self.assertIn("encanador-0", {p["slug"] for p in favs.data})

    def test_detail_exposes_is_favorited(self):
        self.client.force_authenticate(user=self.user)
        res = self.client.get("/api/providers/encanador-0/")
        self.assertFalse(res.data["is_favorited"])
        self.client.post(
            "/api/providers/encanador-0/swipe/",
            {"action": "like", "source": "profile"},
            format="json",
        )
        res = self.client.get("/api/providers/encanador-0/")
        self.assertTrue(res.data["is_favorited"])


class FeaturedProvidersTests(ApiTestBase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        Provider.objects.create(
            name="Maria Encanadora",
            slug="maria-encanadora",
            headline="Consertos de encanamento",
            category=cls.category,
            rating=4.9,
            reviews_count=200,
            jobs_done=500,
            hourly_rate=85,
            city="Campinas",
            state="SP",
            latitude=-22.91,
            longitude=-47.07,
            verified=True,
            status="approved",
        )
        Provider.objects.create(
            name="João Pintor",
            slug="joao-pintor",
            headline="Pintura residencial e comercial",
            category=cls.category,
            rating=4.7,
            reviews_count=80,
            jobs_done=200,
            hourly_rate=70,
            city="Campinas",
            state="SP",
            latitude=-22.89,
            longitude=-47.05,
            status="approved",
        )

    def test_featured_returns_top_5_by_jobs_and_rating(self):
        """Sem localização, retorna os 5 com mais jobs_done + rating."""
        res = self.client.get("/api/providers/featured/")
        self.assertEqual(res.status_code, 200)
        self.assertLessEqual(len(res.data["prestadores"]), 5)
        self.assertFalse(res.data["fallback"])

    def test_featured_filters_by_distance(self):
        """Com lat/lng, só retorna providers até 100km."""
        res = self.client.get("/api/providers/featured/?lat=-22.9&lng=-47.06")
        for p in res.data["prestadores"]:
            self.assertIsNotNone(p.get("distance_km"))
            self.assertLessEqual(p["distance_km"], 100.0)

    def test_featured_fallback_when_none_nearby(self):
        """Lat/lng no meio do oceano → fallback."""
        res = self.client.get("/api/providers/featured/?lat=0&lng=0")
        self.assertTrue(res.data["fallback"])
        self.assertEqual(len(res.data["prestadores"]), 0)

    def test_featured_fallback_when_fewer_than_2(self):
        """Menos de 2 providers na região → fallback."""
        Provider.objects.create(
            name="Unico",
            slug="unico",
            headline="Só eu aqui",
            category=self.category,
            rating=5.0,
            jobs_done=999,
            latitude=-20.0,
            longitude=-45.0,
            status="approved",
        )
        res = self.client.get("/api/providers/featured/?lat=-20.0&lng=-45.0")
        self.assertTrue(res.data["fallback"])

    def test_featured_ordering(self):
        """Ordenação: mais jobs_done primeiro, depois rating."""
        res = self.client.get("/api/providers/featured/")
        dados = res.data["prestadores"]
        for i in range(len(dados) - 1):
            a, b = dados[i], dados[i + 1]
            if a["jobs_done"] == b["jobs_done"]:
                self.assertGreaterEqual(a["rating"], b["rating"])

    def test_featured_excludes_unapproved(self):
        """Providers não aprovados não entram."""
        Provider.objects.filter(status="pending").update(
            latitude=-23.0, longitude=-46.0, jobs_done=9999
        )
        res = self.client.get("/api/providers/featured/")
        slugs = {p["slug"] for p in res.data["prestadores"]}
        for p in Provider.objects.filter(status="pending"):
            self.assertNotIn(p.slug, slugs)

    def test_featured_excludes_no_location(self):
        """Providers sem lat/lng são excluídos."""
        Provider.objects.create(
            name="Sem Local",
            slug="sem-local",
            headline="Sem coordenadas",
            category=self.category,
            latitude=None,
            longitude=None,
            jobs_done=9999,
            rating=5.0,
            status="approved",
        )
        res = self.client.get("/api/providers/featured/")
        slugs = {p["slug"] for p in res.data["prestadores"]}
        self.assertNotIn("sem-local", slugs)

    def test_featured_response_structure(self):
        """Estrutura da resposta deve ter prestadores, total, fallback, mensagem."""
        res = self.client.get("/api/providers/featured/")
        self.assertIn("prestadores", res.data)
        self.assertIn("total", res.data)
        self.assertIn("fallback", res.data)
        self.assertIn("mensagem", res.data)

    def test_featured_public_no_auth_required(self):
        """Endpoint público — não precisa de autenticação."""
        self.client.force_authenticate(user=None)
        res = self.client.get("/api/providers/featured/")
        self.assertEqual(res.status_code, 200)

    def test_featured_city_filter_matches(self):
        """Com city, filtra prestadores daquela cidade."""
        res = self.client.get("/api/providers/featured/?city=Campinas")
        self.assertEqual(res.status_code, 200)
        self.assertFalse(res.data["fallback"])
        for p in res.data["prestadores"]:
            self.assertEqual(p["city"], "Campinas")

    def test_featured_city_filter_case_insensitive(self):
        """City filter é case-insensitive."""
        res = self.client.get("/api/providers/featured/?city=campinas")
        self.assertEqual(res.status_code, 200)
        self.assertFalse(res.data["fallback"])
        self.assertGreater(len(res.data["prestadores"]), 0)

    def test_featured_city_filter_no_match_fallback(self):
        """City sem prestadores → fallback."""
        res = self.client.get("/api/providers/featured/?city=Recife")
        self.assertTrue(res.data["fallback"])
        self.assertEqual(len(res.data["prestadores"]), 0)
        self.assertIn("Recife", res.data["mensagem"])

    def test_featured_city_filter_fewer_than_2_fallback(self):
        """City com só 1 prestador → fallback (mínimo é 2)."""
        Provider.objects.create(
            name="Só em Hortolândia",
            slug="so-em-hortolandia",
            headline="Único em Hortolândia",
            category=self.category,
            rating=4.0,
            jobs_done=50,
            city="Hortolândia",
            state="SP",
            latitude=-22.86,
            longitude=-47.22,
            status="approved",
        )
        res = self.client.get("/api/providers/featured/?city=Hortolândia")
        self.assertTrue(res.data["fallback"])
        self.assertEqual(len(res.data["prestadores"]), 0)
        self.assertIn("Hortolândia", res.data["mensagem"])

    def test_featured_returns_exact_count_when_2_to_5(self):
        """Entre 2 e 5 prestadores no raio, retorna todos (sem cap artificial)."""
        res = self.client.get("/api/providers/featured/?lat=-22.9&lng=-47.06")
        count = len(res.data["prestadores"])
        self.assertGreaterEqual(count, 2)
        self.assertLessEqual(count, 5)
        self.assertFalse(res.data["fallback"])

    def test_featured_distance_km_rounded(self):
        """distance_km vem arredondado com 2 casas decimais."""
        res = self.client.get("/api/providers/featured/?lat=-22.9&lng=-47.06")
        for p in res.data["prestadores"]:
            d = p.get("distance_km")
            if d is not None:
                self.assertEqual(d, round(d, 2))

    def test_featured_lat_lng_overrides_city(self):
        """lat/lng tem prioridade sobre city quando ambos são enviados."""
        res = self.client.get("/api/providers/featured/?lat=-22.9&lng=-47.06&city=Recife")
        self.assertEqual(res.status_code, 200)
        # Deve filtrar por distância (Campinas), não por city (Recife)
        for p in res.data["prestadores"]:
            self.assertEqual(p["city"], "Campinas")

    def test_featured_category_serialized(self):
        """Cada prestador tem category com slug, name e icon."""
        res = self.client.get("/api/providers/featured/")
        for p in res.data["prestadores"]:
            cat = p.get("category")
            self.assertIsNotNone(cat)
            self.assertIn("slug", cat)
            self.assertIn("name", cat)
            self.assertIn("icon", cat)
            self.assertEqual(cat["slug"], "eletrica")

    def test_featured_selected_fields_present(self):
        """Campos essenciais do prestador na resposta."""
        res = self.client.get("/api/providers/featured/")
        for p in res.data["prestadores"]:
            for field in ("id", "slug", "name", "headline", "rating", "reviews_count",
                          "jobs_done", "hourly_rate", "city", "state", "verified"):
                self.assertIn(field, p, f"Campo {field} ausente em {p['slug']}")

    def test_featured_ordering_jobs_then_rating(self):
        """Ordenação: decrescente por jobs_done, depois rating."""
        res = self.client.get("/api/providers/featured/")
        dados = res.data["prestadores"]
        for i in range(len(dados) - 1):
            self.assertGreaterEqual(
                (dados[i]["jobs_done"], dados[i]["rating"]),
                (dados[i + 1]["jobs_done"], dados[i + 1]["rating"]),
            )

    def test_featured_fallback_mensagem_sem_localizacao(self):
        """Mensagem de fallback sem lat/lng nem city."""
        res = self.client.get("/api/providers/featured/?lat=0&lng=0")
        self.assertIn("100.0 km", res.data["mensagem"])
        self.assertTrue(res.data["mensagem"].startswith("Nenhum prestador"))

    def test_featured_fallback_mensagem_com_city(self):
        """Mensagem de fallback menciona a cidade."""
        res = self.client.get("/api/providers/featured/?city=Manaus")
        self.assertIn("Manaus", res.data["mensagem"])
        self.assertIn("100.0 km", res.data["mensagem"])

    def test_featured_excludes_rejected(self):
        """Providers com status rejected não entram."""
        Provider.objects.create(
            name="Rejeitado",
            slug="rejeitado",
            headline="Sou rejeitado",
            category=self.category,
            rating=5.0,
            jobs_done=9999,
            latitude=-22.9,
            longitude=-47.06,
            status="rejected",
        )
        res = self.client.get("/api/providers/featured/")
        slugs = {p["slug"] for p in res.data["prestadores"]}
        self.assertNotIn("rejeitado", slugs)

    def test_featured_excludes_pending(self):
        """Providers com status pending não entram."""
        Provider.objects.create(
            name="Pendente",
            slug="pendente",
            headline="Sou pendente",
            category=self.category,
            rating=5.0,
            jobs_done=9999,
            latitude=-22.9,
            longitude=-47.06,
            status="pending",
        )
        res = self.client.get("/api/providers/featured/")
        slugs = {p["slug"] for p in res.data["prestadores"]}
        self.assertNotIn("pendente", slugs)

    def test_featured_with_partial_location_data_none(self):
        """Provider com latitude=None mas longitude preenchida → excluído."""
        Provider.objects.create(
            name="Lat Nula",
            slug="lat-nula",
            headline="Latitude nula",
            category=self.category,
            rating=4.0,
            jobs_done=100,
            latitude=None,
            longitude=-47.06,
            status="approved",
        )
        res = self.client.get("/api/providers/featured/")
        slugs = {p["slug"] for p in res.data["prestadores"]}
        self.assertNotIn("lat-nula", slugs)

    def test_featured_sem_parametros_retorna_melhores_globais(self):
        """Sem nenhum parâmetro, retorna top globais (sem filtro geográfico)."""
        res = self.client.get("/api/providers/featured/")
        self.assertEqual(res.status_code, 200)
        self.assertFalse(res.data["fallback"])
        # Ordem esperada: Maria (500 jobs) > Carlos (300) > João (200)
        slugs = [p["slug"] for p in res.data["prestadores"]]
        self.assertEqual(slugs, ["maria-encanadora", "carlos-eletricista", "joao-pintor"])

@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class ProviderProfileExpansionTests(ApiTestBase):
    """Edição do perfil do prestador: tags, agenda, galeria, completude, busca."""

    def setUp(self):
        # carlos-eletricista passa a pertencer a cls.user (vira prestador editável).
        self.provider.owner = self.user
        self.provider.save(update_fields=["owner"])

    def test_tags_autocomplete(self):
        Tag.objects.create(name="Limpeza pesada", slug="limpeza-pesada")
        Tag.objects.create(name="Limpeza pós-obra", slug="limpeza-pos-obra")
        Tag.objects.create(name="Jardinagem", slug="jardinagem")
        res = self.client.get("/api/tags/?search=limp")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        nomes = [t["name"] for t in res.data]
        self.assertIn("Limpeza pesada", nomes)
        self.assertNotIn("Jardinagem", nomes)

    def test_partial_update_tags_and_availability(self):
        self.client.force_authenticate(user=self.user)
        res = self.client.patch(
            f"/api/providers/{self.provider.slug}/",
            {
                "headline": "Eletricista 24h",
                "tags": ["Quadro de luz", "Tomadas", "quadro de luz"],  # dup proposital
                "availability_slots": [
                    {"day_of_week": 0, "start_time": "08:00", "end_time": "12:00"}
                ],
            },
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["headline"], "Eletricista 24h")
        nomes = sorted(t["name"] for t in res.data["tags"])
        self.assertEqual(nomes, ["Quadro de luz", "Tomadas"])  # dedup
        self.assertEqual(res.data["skills"], [t["name"] for t in res.data["tags"]])  # espelho
        self.assertEqual(len(res.data["availability_slots"]), 1)
        # Tag nova foi persistida no vocabulário global.
        self.assertTrue(Tag.objects.filter(slug="quadro-de-luz").exists())

    def test_update_requires_ownership(self):
        other = User.objects.create_user(username="outro@hivee.dev", email="outro@hivee.dev", password="x12345")
        self.client.force_authenticate(user=other)
        res = self.client.patch(
            f"/api/providers/{self.provider.slug}/", {"headline": "hack"}, format="json"
        )
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_gallery_add_and_delete(self):
        self.client.force_authenticate(user=self.user)
        img = SimpleUploadedFile("s.png", TINY_PNG, content_type="image/png")
        res = self.client.post(
            f"/api/providers/{self.provider.slug}/gallery/",
            {"image": img, "alt_text": "Serviço concluído"},
            format="multipart",
        )
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        image_id = res.data["id"]
        self.assertIsNotNone(res.data["image_url"])
        # aparece no perfil
        detail = self.client.get(f"/api/providers/{self.provider.slug}/")
        self.assertEqual(len(detail.data["gallery"]), 1)
        # remove
        res = self.client.delete(f"/api/providers/{self.provider.slug}/gallery/{image_id}/")
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(ProviderImage.objects.filter(provider=self.provider).count(), 0)

    def test_gallery_owner_only(self):
        other = User.objects.create_user(username="z@hivee.dev", email="z@hivee.dev", password="x12345")
        self.client.force_authenticate(user=other)
        img = SimpleUploadedFile("s.png", TINY_PNG, content_type="image/png")
        res = self.client.post(
            f"/api/providers/{self.provider.slug}/gallery/", {"image": img}, format="multipart"
        )
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_search_matches_tags(self):
        # Adiciona uma tag que NÃO está no nome/headline/skills e busca por ela.
        self.client.force_authenticate(user=self.user)
        self.client.patch(
            f"/api/providers/{self.provider.slug}/",
            {"tags": ["Energia Solar"]},
            format="json",
        )
        self.client.force_authenticate(user=None)
        res = self.client.get("/api/providers/?search=solar")
        slugs = [p["slug"] for p in res.data["results"]]
        self.assertIn(self.provider.slug, slugs)

    def test_me_patch_updates_name_and_phone(self):
        self.client.force_authenticate(user=self.user)
        res = self.client.patch(
            "/api/auth/me/", {"first_name": "Carlos Editado", "telefone": "11988887777"}, format="json"
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["first_name"], "Carlos Editado")
        self.assertEqual(res.data["telefone"], "11988887777")

    def test_profile_completeness_is_computed(self):
        res = self.client.get(f"/api/providers/{self.provider.slug}/")
        self.assertIn("profile_completeness", res.data)
        self.assertIsInstance(res.data["profile_completeness"], int)
        self.assertGreaterEqual(res.data["profile_completeness"], 0)
        self.assertLessEqual(res.data["profile_completeness"], 100)



class NotificationTests(ApiTestBase):
    """Cobre o serviço `notify_user` e a API REST de notificações."""

    def setUp(self):
        from .models import Notification
        from .services import notify_user

        self.notify_user = notify_user
        self.Notification = Notification
        # Duas notificações para o usuário base: uma não lida, uma lida.
        notify_user(
            recipient=self.user,
            tipo=Notification.Tipo.PROVIDER_APPROVED,
            title="Perfil aprovado",
            body="Parabéns!",
            link="/minha-conta",
        )
        lida = notify_user(
            recipient=self.user,
            tipo=Notification.Tipo.CPF_VERIFIED,
            title="CPF verificado",
        )
        lida.is_read = True
        lida.save(update_fields=["is_read"])

    def test_service_creates_notification(self):
        n = self.notify_user(
            recipient=self.user,
            tipo=self.Notification.Tipo.RECOMMENDATION,
            title="Olha esse profissional",
            payload={"provider_slug": "carlos-eletricista"},
        )
        self.assertIsNotNone(n.pk)
        self.assertFalse(n.is_read)
        self.assertEqual(n.payload["provider_slug"], "carlos-eletricista")

    def test_anonymous_cannot_list(self):
        res = self.client.get("/api/notifications/")
        self.assertIn(
            res.status_code,
            (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN),
        )

    def test_list_only_own_notifications(self):
        other = User.objects.create_user(
            username="outro@hivee.dev", email="outro@hivee.dev", password="senha123"
        )
        self.notify_user(recipient=other, tipo="new_message", title="Privado")

        self.client.force_authenticate(user=self.user)
        res = self.client.get("/api/notifications/")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["count"], 2)  # só as duas do self.user
        titles = [n["title"] for n in res.data["results"]]
        self.assertNotIn("Privado", titles)

    def test_unread_only_filter(self):
        self.client.force_authenticate(user=self.user)
        res = self.client.get("/api/notifications/?unread_only=1")
        self.assertEqual(res.data["count"], 1)
        self.assertFalse(res.data["results"][0]["is_read"])

    def test_unread_count(self):
        self.client.force_authenticate(user=self.user)
        res = self.client.get("/api/notifications/unread_count/")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["count"], 1)

    def test_mark_read(self):
        self.client.force_authenticate(user=self.user)
        unread = self.Notification.objects.filter(
            recipient=self.user, is_read=False
        ).first()
        res = self.client.post(f"/api/notifications/{unread.pk}/mark_read/")
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        unread.refresh_from_db()
        self.assertTrue(unread.is_read)

    def test_mark_all_read(self):
        self.client.force_authenticate(user=self.user)
        res = self.client.post("/api/notifications/mark_all_read/")
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(
            self.Notification.objects.filter(recipient=self.user, is_read=False).count(),
            0,
        )

    def test_cannot_mark_other_users_notification(self):
        other = User.objects.create_user(
            username="alheio@hivee.dev", email="alheio@hivee.dev", password="senha123"
        )
        alheia = self.notify_user(recipient=other, tipo="new_message", title="Alheia")
        self.client.force_authenticate(user=self.user)
        res = self.client.post(f"/api/notifications/{alheia.pk}/mark_read/")
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        alheia.refresh_from_db()
        self.assertFalse(alheia.is_read)


class SupportSystemTests(ApiTestBase):
    """Central de Ajuda (FAQ) + Tickets de suporte com ciclo de vida."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.staff = User.objects.create_user(
            username="equipe@hivee.dev",
            email="equipe@hivee.dev",
            password="senha123",
            first_name="Equipe",
            is_staff=True,
        )
        cls.support_cat = SupportCategory.objects.create(
            name="Pagamento", slug="pagamento", icon="CreditCard", order=0
        )
        FAQArticle.objects.create(
            category=cls.support_cat,
            question="Como pago um serviço?",
            slug="como-pago-um-servico",
            answer="Combine direto com o profissional.",
            is_published=True,
        )
        FAQArticle.objects.create(
            question="Rascunho oculto",
            slug="rascunho-oculto",
            answer="Não deve aparecer.",
            is_published=False,
        )

    # ── FAQ ─────────────────────────────────────────────────────────────
    def test_faq_is_public(self):
        self.assertEqual(self.client.get("/api/faq/").status_code, status.HTTP_200_OK)
        self.assertEqual(self.client.get("/api/faq/categories/").status_code, status.HTTP_200_OK)

    def test_faq_lists_only_published(self):
        res = self.client.get("/api/faq/")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        slugs = {a["slug"] for a in res.data}
        self.assertIn("como-pago-um-servico", slugs)
        self.assertNotIn("rascunho-oculto", slugs)

    def test_faq_search_and_category_filter(self):
        self.assertEqual(len(self.client.get("/api/faq/?search=pago").data), 1)
        self.assertEqual(len(self.client.get("/api/faq/?search=inexistente").data), 0)
        self.assertEqual(len(self.client.get("/api/faq/?category=pagamento").data), 1)

    def test_faq_categories_count_published_only(self):
        res = self.client.get("/api/faq/categories/")
        cat = next(c for c in res.data if c["slug"] == "pagamento")
        self.assertEqual(cat["article_count"], 1)

    # ── Tickets ─────────────────────────────────────────────────────────
    def test_create_ticket_requires_auth(self):
        res = self.client.post(
            "/api/support/tickets/",
            {"subject": "Ajuda", "description": "Preciso de ajuda"},
            format="json",
        )
        self.assertEqual(res.status_code, 401)

    def test_create_ticket_opens_and_logs(self):
        self.client.force_authenticate(user=self.user)
        res = self.client.post(
            "/api/support/tickets/",
            {
                "subject": "Cobrança indevida",
                "description": "Fui cobrado errado.",
                "category_slug": "pagamento",
                "priority": "high",
            },
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data["status"], "open")
        self.assertEqual(res.data["priority"], "high")
        self.assertEqual(res.data["category"]["slug"], "pagamento")
        # Um log de abertura foi criado.
        self.assertEqual(len(res.data["logs"]), 1)
        self.assertEqual(res.data["logs"][0]["to_status"], "open")

    def test_user_only_sees_own_tickets_staff_sees_all(self):
        other = User.objects.create_user(
            username="outro@hivee.dev", email="outro@hivee.dev", password="senha123"
        )
        SupportTicket.objects.create(user=self.user, subject="Meu", description="x")
        SupportTicket.objects.create(user=other, subject="Alheio", description="y")

        self.client.force_authenticate(user=self.user)
        res = self.client.get("/api/support/tickets/")
        self.assertEqual(res.data["count"], 1)

        self.client.force_authenticate(user=self.staff)
        res = self.client.get("/api/support/tickets/")
        self.assertEqual(res.data["count"], 2)

    def test_user_cannot_retrieve_others_ticket(self):
        other = User.objects.create_user(
            username="outro2@hivee.dev", email="outro2@hivee.dev", password="senha123"
        )
        ticket = SupportTicket.objects.create(user=other, subject="Alheio", description="y")
        self.client.force_authenticate(user=self.user)
        res = self.client.get(f"/api/support/tickets/{ticket.id}/")
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_staff_message_transitions_to_waiting_user(self):
        ticket = SupportTicket.objects.create(
            user=self.user, subject="Dúvida", description="?", status="open"
        )
        self.client.force_authenticate(user=self.staff)
        res = self.client.post(
            f"/api/support/tickets/{ticket.id}/message/",
            {"content": "Olá, pode detalhar?"},
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertTrue(res.data["is_staff"])
        ticket.refresh_from_db()
        self.assertEqual(ticket.status, "waiting_user")

    def test_user_reply_transitions_back_to_waiting_staff(self):
        ticket = SupportTicket.objects.create(
            user=self.user, subject="Dúvida", description="?", status="waiting_user"
        )
        self.client.force_authenticate(user=self.user)
        res = self.client.post(
            f"/api/support/tickets/{ticket.id}/message/",
            {"content": "Aqui estão os detalhes."},
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertFalse(res.data["is_staff"])
        ticket.refresh_from_db()
        self.assertEqual(ticket.status, "waiting_staff")

    def test_empty_message_rejected(self):
        ticket = SupportTicket.objects.create(user=self.user, subject="s", description="d")
        self.client.force_authenticate(user=self.user)
        res = self.client.post(
            f"/api/support/tickets/{ticket.id}/message/", {"content": "   "}, format="json"
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_user_can_close_own_open_ticket(self):
        ticket = SupportTicket.objects.create(
            user=self.user, subject="Desisti", description="d", status="open"
        )
        self.client.force_authenticate(user=self.user)
        res = self.client.post(
            f"/api/support/tickets/{ticket.id}/transition/",
            {"status": "closed", "note": "Resolvi sozinho"},
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        ticket.refresh_from_db()
        self.assertEqual(ticket.status, "closed")
        self.assertIsNotNone(ticket.closed_at)

    def test_invalid_transition_rejected(self):
        ticket = SupportTicket.objects.create(
            user=self.user, subject="s", description="d", status="open"
        )
        self.client.force_authenticate(user=self.user)
        res = self.client.post(
            f"/api/support/tickets/{ticket.id}/transition/",
            {"status": "resolved"},
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        ticket.refresh_from_db()
        self.assertEqual(ticket.status, "open")

    def test_staff_can_resolve_waiting_user_ticket(self):
        ticket = SupportTicket.objects.create(
            user=self.user, subject="s", description="d", status="waiting_user"
        )
        self.client.force_authenticate(user=self.staff)
        res = self.client.post(
            f"/api/support/tickets/{ticket.id}/transition/",
            {"status": "resolved"},
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        ticket.refresh_from_db()
        self.assertEqual(ticket.status, "resolved")
        self.assertIsNotNone(ticket.resolved_at)

    def test_assign_requires_staff(self):
        ticket = SupportTicket.objects.create(user=self.user, subject="s", description="d")
        self.client.force_authenticate(user=self.user)
        res = self.client.post(
            f"/api/support/tickets/{ticket.id}/assign/",
            {"user_id": self.staff.id},
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_staff_can_assign(self):
        ticket = SupportTicket.objects.create(user=self.user, subject="s", description="d")
        self.client.force_authenticate(user=self.staff)
        res = self.client.post(
            f"/api/support/tickets/{ticket.id}/assign/",
            {"user_id": self.staff.id},
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["assigned_to"], self.staff.id)

    def test_counts_endpoint(self):
        SupportTicket.objects.create(user=self.user, subject="a", description="d", status="open")
        SupportTicket.objects.create(
            user=self.user, subject="b", description="d", status="resolved"
        )
        self.client.force_authenticate(user=self.user)
        res = self.client.get("/api/support/tickets/counts/")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data.get("open"), 1)
        self.assertEqual(res.data.get("resolved"), 1)


class ChatSupportEscalationTests(ApiTestBase):
    """Detecção de intenção e abertura de ticket pelo Chat IA."""

    def test_detects_support_intent(self):
        from agent.core import _detecta_intencao_suporte

        self.assertTrue(_detecta_intencao_suporte("Quero falar com um atendente"))
        self.assertTrue(_detecta_intencao_suporte("Preciso abrir um ticket de suporte"))
        self.assertTrue(_detecta_intencao_suporte("Gostaria de fazer uma reclamação"))

    def test_does_not_hijack_normal_search(self):
        from agent.core import _detecta_intencao_suporte

        # Mensagens normais de busca não devem escalar para suporte humano.
        self.assertFalse(_detecta_intencao_suporte("Preciso de um eletricista em Campinas"))
        self.assertFalse(_detecta_intencao_suporte("Pode me ajudar a achar um encanador?"))

    def test_resolves_site_user_from_lead(self):
        from agent.core import _resolver_usuario_do_lead
        from agent.models import ChatLead

        lead = ChatLead.objects.create(
            telefone=f"site_user_{self.user.id}", canal_origem="site"
        )
        self.assertEqual(_resolver_usuario_do_lead(lead), self.user)

        anon = ChatLead.objects.create(telefone="5519999999999", canal_origem="whatsapp")
        self.assertIsNone(_resolver_usuario_do_lead(anon))


class DemandFlowTests(APITestCase):
    """Feature de demandas: cliente publica, prestador verificado se oferece,
    cliente aceita/recusa."""

    @classmethod
    def setUpTestData(cls):
        cls.category = Category.objects.create(
            name="Pintura", slug="pintura", icon="Paintbrush", order=1
        )
        # Cliente que publica demandas.
        cls.client_user = User.objects.create_user(
            username="dono@hivee.dev", email="dono@hivee.dev",
            password="senha123", first_name="Dona",
        )
        # Prestador APROVADO (pode ver feed e se oferecer).
        cls.provider_user = User.objects.create_user(
            username="pintor@hivee.dev", email="pintor@hivee.dev",
            password="senha123", first_name="Pintor",
        )
        cls.provider = Provider.objects.create(
            name="Pintor Pro", slug="pintor-pro", headline="Pintura residencial",
            category=cls.category, owner=cls.provider_user, status="approved",
            verified=True, hourly_rate=80, skills=["pintura"],
        )
        # Prestador NÃO aprovado (pendente).
        cls.pending_user = User.objects.create_user(
            username="novato@hivee.dev", email="novato@hivee.dev",
            password="senha123", first_name="Novato",
        )
        cls.pending_provider = Provider.objects.create(
            name="Novato", slug="novato", headline="Começando",
            category=cls.category, owner=cls.pending_user, status="pending",
            hourly_rate=50, skills=["pintura"],
        )

    def _create_demand(self, **over):
        from .models import Demand

        data = {
            "client": self.client_user, "title": "Pintar a sala",
            "description": "Parede grande, tinta branca.", "category": self.category,
            "city": "Campinas", "state": "SP", "status": "open",
        }
        data.update(over)
        return Demand.objects.create(**data)

    # ── Criação ────────────────────────────────────────────────────────
    def test_create_demand_requires_auth(self):
        res = self.client.post("/api/demands/", {"title": "x", "description": "y"}, format="json")
        self.assertIn(res.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))

    def test_any_user_can_create_demand(self):
        self.client.force_authenticate(self.client_user)
        res = self.client.post(
            "/api/demands/",
            {
                "title": "Pintar quarto", "description": "Quarto 3x3.",
                "category_slug": "pintura", "city": "Campinas", "state": "SP",
                "preferred_schedule": "Sábado de manhã", "budget_hint": "Até R$ 500",
                "tags": ["pintura", "acabamento"],
            },
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data["status"], "open")
        self.assertEqual(res.data["category"]["slug"], "pintura")
        self.assertIn("pintura", res.data["tags"])

    # ── Feed / visibilidade ────────────────────────────────────────────
    def test_feed_shows_open_demands_to_approved_provider(self):
        self._create_demand()
        self.client.force_authenticate(self.provider_user)
        res = self.client.get("/api/demands/")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["count"], 1)
        self.assertEqual(res.data["results"][0]["title"], "Pintar a sala")
        self.assertFalse(res.data["results"][0]["has_my_offer"])

    def test_feed_excludes_own_demands(self):
        # Um prestador que também publicou uma demanda não a vê como lead.
        self._create_demand(client=self.provider_user)
        self.client.force_authenticate(self.provider_user)
        res = self.client.get("/api/demands/")
        self.assertEqual(res.data["count"], 0)

    def test_list_shows_only_own_demands_to_non_provider(self):
        self._create_demand()
        self._create_demand(client=self.provider_user, title="De outro")
        self.client.force_authenticate(self.client_user)
        res = self.client.get("/api/demands/")
        titles = {d["title"] for d in res.data["results"]}
        self.assertEqual(titles, {"Pintar a sala"})

    def test_feed_filters_by_category_and_search(self):
        self._create_demand(title="Pintar muro")
        self.client.force_authenticate(self.provider_user)
        self.assertEqual(self.client.get("/api/demands/?search=muro").data["count"], 1)
        self.assertEqual(self.client.get("/api/demands/?search=encanamento").data["count"], 0)
        self.assertEqual(self.client.get("/api/demands/?category=pintura").data["count"], 1)

    # ── Ofertas ────────────────────────────────────────────────────────
    def test_approved_provider_can_offer(self):
        demand = self._create_demand()
        self.client.force_authenticate(self.provider_user)
        res = self.client.post(
            f"/api/demands/{demand.id}/offers/",
            {"message": "10 anos de experiência.", "suggested_value": "450.00"},
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data["status"], "pending")
        demand.refresh_from_db()
        self.assertEqual(demand.offer_count, 1)

    def test_pending_provider_cannot_offer(self):
        demand = self._create_demand()
        self.client.force_authenticate(self.pending_user)
        res = self.client.post(
            f"/api/demands/{demand.id}/offers/", {"message": "oi"}, format="json"
        )
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_cannot_offer_twice(self):
        demand = self._create_demand()
        self.client.force_authenticate(self.provider_user)
        self.client.post(f"/api/demands/{demand.id}/offers/", {"message": "a"}, format="json")
        res = self.client.post(f"/api/demands/{demand.id}/offers/", {"message": "b"}, format="json")
        self.assertEqual(res.status_code, status.HTTP_409_CONFLICT)

    def test_cannot_offer_on_own_demand(self):
        # provider_user publica e tenta se oferecer na própria demanda.
        demand = self._create_demand(client=self.provider_user)
        self.client.force_authenticate(self.provider_user)
        res = self.client.post(f"/api/demands/{demand.id}/offers/", {"message": "a"}, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_only_owner_sees_offers(self):
        demand = self._create_demand()
        self.client.force_authenticate(self.provider_user)
        self.client.post(f"/api/demands/{demand.id}/offers/", {"message": "a"}, format="json")
        # Prestador (não dono) não pode listar ofertas.
        self.assertEqual(
            self.client.get(f"/api/demands/{demand.id}/offers/").status_code,
            status.HTTP_403_FORBIDDEN,
        )
        # Dono vê.
        self.client.force_authenticate(self.client_user)
        res = self.client.get(f"/api/demands/{demand.id}/offers/")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]["provider"]["slug"], "pintor-pro")

    def test_accept_offer_sets_in_progress_and_rejects_others(self):
        demand = self._create_demand()
        # Dois prestadores se oferecem.
        self.client.force_authenticate(self.provider_user)
        r1 = self.client.post(f"/api/demands/{demand.id}/offers/", {"message": "a"}, format="json")
        # Aprova o segundo prestador e oferece também.
        Provider.objects.create(
            name="Outro", slug="outro", headline="h", category=self.category,
            owner=self.pending_user, status="approved", hourly_rate=60, skills=["pintura"],
        )
        self.pending_provider.delete()  # garante 1 provider aprovado para pending_user
        self.client.force_authenticate(self.pending_user)
        r2 = self.client.post(f"/api/demands/{demand.id}/offers/", {"message": "b"}, format="json")
        self.assertEqual(r2.status_code, status.HTTP_201_CREATED)

        # Dono aceita a primeira oferta.
        self.client.force_authenticate(self.client_user)
        res = self.client.patch(
            f"/api/demands/{demand.id}/offers/{r1.data['id']}/",
            {"status": "accepted"}, format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["status"], "accepted")

        demand.refresh_from_db()
        self.assertEqual(demand.status, "in_progress")
        # A segunda oferta vira rejected automaticamente.
        from .models import DemandOffer

        other = DemandOffer.objects.get(id=r2.data["id"])
        self.assertEqual(other.status, "rejected")

    def test_offer_decision_requires_owner(self):
        demand = self._create_demand()
        self.client.force_authenticate(self.provider_user)
        offer = self.client.post(
            f"/api/demands/{demand.id}/offers/", {"message": "a"}, format="json"
        ).data
        # Prestador tenta aceitar a própria oferta -> não é dono -> 404.
        res = self.client.patch(
            f"/api/demands/{demand.id}/offers/{offer['id']}/",
            {"status": "accepted"}, format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    # ── Detalhe / has_my_offer / painéis ───────────────────────────────
    def test_detail_exposes_offers_to_owner_and_my_offer_to_provider(self):
        demand = self._create_demand()
        self.client.force_authenticate(self.provider_user)
        self.client.post(f"/api/demands/{demand.id}/offers/", {"message": "a"}, format="json")
        # Prestador vê has_my_offer + my_offer, mas não a lista de ofertas.
        res = self.client.get(f"/api/demands/{demand.id}/")
        self.assertTrue(res.data["has_my_offer"])
        self.assertIn("my_offer", res.data)
        self.assertNotIn("offers", res.data)
        # Dono vê a lista de ofertas.
        self.client.force_authenticate(self.client_user)
        res = self.client.get(f"/api/demands/{demand.id}/")
        self.assertTrue(res.data["is_owner"])
        self.assertEqual(len(res.data["offers"]), 1)

    def test_mine_and_my_offers_panels(self):
        demand = self._create_demand()
        self.client.force_authenticate(self.provider_user)
        self.client.post(f"/api/demands/{demand.id}/offers/", {"message": "a"}, format="json")
        my_offers = self.client.get("/api/demands/my-offers/")
        self.assertEqual(my_offers.status_code, status.HTTP_200_OK)
        self.assertEqual(len(my_offers.data), 1)
        self.assertEqual(my_offers.data[0]["demand"]["title"], "Pintar a sala")

        self.client.force_authenticate(self.client_user)
        mine = self.client.get("/api/demands/mine/")
        self.assertEqual(len(mine.data), 1)
        self.assertEqual(mine.data[0]["offer_count"], 1)

    def test_owner_can_cancel_demand(self):
        demand = self._create_demand()
        self.client.force_authenticate(self.client_user)
        res = self.client.patch(f"/api/demands/{demand.id}/", {"status": "cancelled"}, format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["status"], "cancelled")

    def test_offering_on_closed_demand_blocked(self):
        demand = self._create_demand(status="closed")
        self.client.force_authenticate(self.provider_user)
        res = self.client.post(f"/api/demands/{demand.id}/offers/", {"message": "a"}, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)


class BookingFlowTests(ApiTestBase):
    """Agendamento: ciclo completo, avaliação obrigatória, gamificação."""

    def setUp(self):
        from .models import AvailabilitySlot
        self.owner = User.objects.create_user(
            username="dono@hivee.dev", email="dono@hivee.dev", password="x12345"
        )
        self.provider.owner = self.owner
        self.provider.reviews_count = 0
        self.provider.save(update_fields=["owner", "reviews_count"])
        for d in range(7):
            AvailabilitySlot.objects.create(
                provider=self.provider, day_of_week=d, start_time="09:00", end_time="12:00"
            )

    def _solicitar(self, cliente):
        from datetime import timedelta
        from django.utils import timezone
        self.client.force_authenticate(user=cliente)
        dt = (timezone.now() + timedelta(days=1)).isoformat()
        return self.client.post(
            f"/api/providers/{self.provider.slug}/solicitar/",
            {"descricao": "Trocar chuveiro", "endereco": "Rua X, 10", "data_solicitada": dt},
            format="json",
        )

    def _finalizar(self, sid):
        self.client.force_authenticate(user=self.owner)
        self.client.post(f"/api/servicos/{sid}/aprovar/")
        self.client.post(f"/api/servicos/{sid}/concluir/")
        self.client.force_authenticate(user=self.user)
        self.client.post(f"/api/servicos/{sid}/confirmar/")
        self.client.post(f"/api/servicos/{sid}/pagar/")

    def test_horarios_returns_slots(self):
        res = self.client.get(f"/api/providers/{self.provider.slug}/horarios/")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertGreater(len(res.data), 0)

    def test_full_flow_and_rating(self):
        res = self._solicitar(self.user)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        sid = res.data["id"]

        self.client.force_authenticate(user=self.owner)
        self.assertEqual(self.client.post(f"/api/servicos/{sid}/aprovar/").status_code, 200)
        self.assertEqual(self.client.post(f"/api/servicos/{sid}/concluir/").status_code, 200)

        self.client.force_authenticate(user=self.user)
        r = self.client.post(f"/api/servicos/{sid}/confirmar/")
        self.assertEqual(r.data["status"], "aguardando_pagamento")
        self.assertTrue(r.data["pix_copia_cola"])

        jobs_before = Provider.objects.get(pk=self.provider.pk).jobs_done
        r = self.client.post(f"/api/servicos/{sid}/pagar/")
        self.assertEqual(r.data["status"], "finalizado")
        self.assertEqual(Provider.objects.get(pk=self.provider.pk).jobs_done, jobs_before + 1)

        r = self.client.post(f"/api/servicos/{sid}/avaliar/", {"nota": 5, "comentario": "Ótimo"}, format="json")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["review"]["nota"], 5)
        prov = Provider.objects.get(pk=self.provider.pk)
        self.assertEqual(float(prov.rating), 5.0)
        self.assertEqual(prov.reviews_count, 1)

    def test_mandatory_review_blocks_new_booking(self):
        res = self._solicitar(self.user)
        sid = res.data["id"]
        self._finalizar(sid)

        blocked = self._solicitar(self.user)
        self.assertEqual(blocked.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(blocked.data["codigo"], "avaliacao_obrigatoria")

        self.client.force_authenticate(user=self.user)
        vb = self.client.get("/api/servicos/verificar-bloqueio/")
        self.assertFalse(vb.data["pode_contratar"])

        self.client.post(f"/api/servicos/{sid}/avaliar/", {"nota": 4}, format="json")
        unblocked = self._solicitar(self.user)
        self.assertEqual(unblocked.status_code, status.HTTP_201_CREATED)

    def test_only_owner_can_approve(self):
        sid = self._solicitar(self.user).data["id"]
        self.client.force_authenticate(user=self.user)  # cliente tenta aprovar
        self.assertEqual(self.client.post(f"/api/servicos/{sid}/aprovar/").status_code, 403)

    def test_cannot_hire_self(self):
        from datetime import timedelta
        from django.utils import timezone
        self.client.force_authenticate(user=self.owner)
        dt = (timezone.now() + timedelta(days=1)).isoformat()
        r = self.client.post(
            f"/api/providers/{self.provider.slug}/solicitar/",
            {"descricao": "x", "data_solicitada": dt}, format="json",
        )
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)

    def test_list_filters_by_role(self):
        sid = self._solicitar(self.user).data["id"]
        # cliente vê como cliente
        self.client.force_authenticate(user=self.user)
        r = self.client.get("/api/servicos/?papel=cliente")
        self.assertIn(sid, [s["id"] for s in r.data])
        # prestador vê como prestador
        self.client.force_authenticate(user=self.owner)
        r = self.client.get("/api/servicos/?papel=prestador")
        self.assertIn(sid, [s["id"] for s in r.data])

    def test_gamification_endpoints(self):
        self.client.force_authenticate(user=self.user)
        r = self.client.get("/api/gamification/me/")
        self.assertEqual(r.status_code, 200)
        self.assertIn("tier", r.data)
        self.assertIn("badges", r.data)
        self.assertEqual(r.data["tier"]["key"], "bronze")  # 0 contratações

        r = self.client.get(f"/api/gamification/provider/{self.provider.slug}/")
        self.assertEqual(r.status_code, 200)
        self.assertIn("tier", r.data)
        self.assertIn("progress_percent", r.data)

    def test_client_level_up_after_finalize(self):
        sid = self._solicitar(self.user).data["id"]
        self._finalizar(sid)
        self.client.force_authenticate(user=self.user)
        r = self.client.get("/api/gamification/me/")
        self.assertEqual(r.data["stats"]["concluidos"], 1)
        primeira = next(b for b in r.data["badges"] if b["key"] == "primeira")
        self.assertTrue(primeira["earned"])
