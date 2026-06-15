"""Testes automatizados da API REST do HIVEE (Django REST Framework).

Cobrem: listagem/paginacao, detalhe por slug, acao `recommended`, controle de
permissao (leitura publica x escrita autenticada), fluxo de autenticacao por
token e disponibilidade da documentacao (schema + Swagger).

Rodar:  python manage.py test
"""
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Category, Provider

User = get_user_model()


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



