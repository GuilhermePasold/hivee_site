"""Endpoints de gamificação (níveis + badges + progresso), tudo derivado de dados reais."""

from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from ..gamification import client_progress, provider_progress
from ..models import Provider


class GamificationMeView(APIView):
    """GET /api/gamification/me/ — nível e conquistas do cliente logado."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(client_progress(request.user))


class GamificationProviderView(APIView):
    """GET /api/gamification/provider/<slug>/ — nível e conquistas do prestador (público)."""

    def get(self, request, slug=None):
        provider = get_object_or_404(Provider, slug=slug)
        return Response(provider_progress(provider))
