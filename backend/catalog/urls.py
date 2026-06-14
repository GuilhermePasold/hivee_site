from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views
from .views import (
    CategoryListView,
    CitiesView,
    LoginView,
    LogoutView,
    MeView,
    ProviderViewSet,
    RegisterView,
    StatsView,
)

app_name = "catalog"

# DefaultRouter gera automaticamente as rotas REST do ProviderViewSet
# (list, create, retrieve, recommended) sem precisarmos escrever um path
# por metodo HTTP, exatamente como descrito no passo a passo do DRF.
router = DefaultRouter()
router.register(r"providers", ProviderViewSet, basename="provider")

urlpatterns = [
    # --- Camada MTV (templates renderizados pelo Django) ---
    path("mtv/", views.listar_prestadores, name="listar_prestadores"),
    path("mtv/prestador/<slug:slug>/", views.detalhe_prestador, name="detalhe_prestador"),
    path("mtv/cadastrar/", views.cadastrar_cliente, name="cadastrar_cliente"),
    path("mtv/entrar/", views.login_cliente, name="login_cliente"),
    path("mtv/sair/", views.logout_cliente, name="logout_cliente"),
    path("mtv/perfil/", views.editar_perfil, name="editar_perfil"),
    path("mtv/perfil/deletar/", views.deletar_conta, name="deletar_conta"),
    # --- API REST (DRF) ---
    path("api/categories/", CategoryListView.as_view(), name="categories"),
    path("api/cities/", CitiesView.as_view(), name="cities"),
    path("api/stats/", StatsView.as_view(), name="stats"),
    path("api/auth/register/", RegisterView.as_view(), name="register"),
    path("api/auth/login/", LoginView.as_view(), name="login"),
    path("api/auth/logout/", LogoutView.as_view(), name="logout"),
    path("api/auth/me/", MeView.as_view(), name="me"),
    # Rotas de /api/providers/ geradas pelo roteador do DRF.
    path("api/", include(router.urls)),
]
