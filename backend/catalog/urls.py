from django.urls import path

from . import views
from .views import (
    CategoryListView,
    CitiesView,
    LoginView,
    MeView,
    ProviderViewSet,
    RegisterView,
    StatsView,
)

app_name = "catalog"

provider_list = ProviderViewSet.as_view({"get": "list", "post": "create"})
provider_recommended = ProviderViewSet.as_view({"get": "recommended"})
provider_detail = ProviderViewSet.as_view({"get": "retrieve"})

urlpatterns = [
    path("mtv/", views.listar_prestadores, name="listar_prestadores"),
    path("mtv/prestador/<slug:slug>/", views.detalhe_prestador, name="detalhe_prestador"),
    path("mtv/cadastrar/", views.cadastrar_cliente, name="cadastrar_cliente"),
    path("mtv/entrar/", views.login_cliente, name="login_cliente"),
    path("mtv/sair/", views.logout_cliente, name="logout_cliente"),
    path("mtv/perfil/", views.editar_perfil, name="editar_perfil"),
    path("mtv/perfil/deletar/", views.deletar_conta, name="deletar_conta"),
    path("api/categories/", CategoryListView.as_view(), name="categories"),
    path("api/cities/", CitiesView.as_view(), name="cities"),
    path("api/stats/", StatsView.as_view(), name="stats"),
    path("api/auth/register/", RegisterView.as_view(), name="register"),
    path("api/auth/login/", LoginView.as_view(), name="login"),
    path("api/auth/me/", MeView.as_view(), name="me"),
    path("api/providers/", provider_list, name="provider-list"),
    path("api/providers/recommended/", provider_recommended, name="provider-recommended"),
    path("api/providers/<slug:slug>/", provider_detail, name="provider-detail"),
]
