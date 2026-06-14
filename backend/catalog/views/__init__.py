from .api_views import (
    AvatarUploadView,
    CategoryListView,
    CitiesView,
    LoginView,
    LogoutView,
    MeView,
    ProviderViewSet,
    RegisterView,
    StatsView,
)
from .auth_views import cadastrar_cliente, login_cliente, logout_cliente
from .perfil_views import checar_sessao, deletar_conta, editar_perfil
from .provider_views import detalhe_prestador, listar_prestadores

__all__ = [
    "AvatarUploadView",
    "CategoryListView",
    "CitiesView",
    "LoginView",
    "LogoutView",
    "MeView",
    "ProviderViewSet",
    "RegisterView",
    "StatsView",
    "cadastrar_cliente",
    "login_cliente",
    "logout_cliente",
    "checar_sessao",
    "deletar_conta",
    "editar_perfil",
    "detalhe_prestador",
    "listar_prestadores",
]
