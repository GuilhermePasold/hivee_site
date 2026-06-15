from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views
from .views import (
    AvatarUploadView,
    CategoryListView,
    CitiesByStateView,
    CitiesView,
    DemandViewSet,
    FAQArticleListView,
    GamificationMeView,
    GamificationProviderView,
    LoginView,
    LogoutView,
    MeView,
    NotificationViewSet,
    ProviderHorariosView,
    ProviderViewSet,
    RegisterView,
    ServicoViewSet,
    SolicitarServicoView,
    StatsView,
    SupportCategoryListView,
    SupportTicketViewSet,
    TagListView,
)

app_name = "catalog"

# DefaultRouter gera automaticamente as rotas REST do ProviderViewSet
# (list, create, retrieve, recommended) sem precisarmos escrever um path
# por metodo HTTP, exatamente como descrito no passo a passo do DRF.
router = DefaultRouter()
router.register(r"providers", ProviderViewSet, basename="provider")
router.register(r"demands", DemandViewSet, basename="demand")
router.register(r"notifications", NotificationViewSet, basename="notification")
router.register(r"support/tickets", SupportTicketViewSet, basename="support-ticket")
router.register(r"servicos", ServicoViewSet, basename="servico")

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
    path("api/tags/", TagListView.as_view(), name="tags"),
    path("api/cities/", CitiesView.as_view(), name="cities"),
    path("api/stats/", StatsView.as_view(), name="stats"),
    path("api/auth/register/", RegisterView.as_view(), name="register"),
    path("api/auth/login/", LoginView.as_view(), name="login"),
    path("api/auth/logout/", LogoutView.as_view(), name="logout"),
    path("api/auth/me/", MeView.as_view(), name="me"),
    path("api/upload-avatar/", AvatarUploadView.as_view(), name="upload-avatar"),
    path("api/cities-by-state/<str:uf>/", CitiesByStateView.as_view(), name="cities-by-state"),
    # --- Central de Ajuda (FAQ) — exige autenticação ---
    path("api/faq/", FAQArticleListView.as_view(), name="faq"),
    path("api/faq/categories/", SupportCategoryListView.as_view(), name="faq-categories"),
    # --- Agendamento de serviços (precede o router p/ casar antes do detail) ---
    path("api/providers/<slug:slug>/horarios/", ProviderHorariosView.as_view(), name="provider-horarios"),
    path("api/providers/<slug:slug>/solicitar/", SolicitarServicoView.as_view(), name="provider-solicitar"),
    # --- Gamificação ---
    path("api/gamification/me/", GamificationMeView.as_view(), name="gamification-me"),
    path("api/gamification/provider/<slug:slug>/", GamificationProviderView.as_view(), name="gamification-provider"),
    # Rotas de /api/providers/ geradas pelo roteador do DRF.
    path("api/", include(router.urls)),
]
