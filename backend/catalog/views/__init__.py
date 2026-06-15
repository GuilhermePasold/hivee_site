from .api_views import (
    AvatarUploadView,
    CategoryListView,
    CitiesByStateView,
    CitiesView,
    DemandViewSet,
    FAQArticleListView,
    LoginView,
    LogoutView,
    MeView,
    NotificationViewSet,
    ProviderViewSet,
    RegisterView,
    StatsView,
    SupportCategoryListView,
    SupportTicketViewSet,
    TagListView,
)
from .booking_views import (
    ProviderHorariosView,
    ServicoViewSet,
    SolicitarServicoView,
)
from .gamification_views import GamificationMeView, GamificationProviderView
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
    "NotificationViewSet",
    "DemandViewSet",
    "ProviderViewSet",
    "RegisterView",
    "StatsView",
    "TagListView",
    "FAQArticleListView",
    "SupportCategoryListView",
    "SupportTicketViewSet",
    "ServicoViewSet",
    "ProviderHorariosView",
    "SolicitarServicoView",
    "GamificationMeView",
    "GamificationProviderView",
    "cadastrar_cliente",
    "login_cliente",
    "logout_cliente",
    "checar_sessao",
    "deletar_conta",
    "editar_perfil",
    "detalhe_prestador",
    "listar_prestadores",
]
