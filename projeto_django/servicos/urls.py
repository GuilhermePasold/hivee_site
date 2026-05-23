from django.urls import path
from . import views

app_name = 'servicos'

urlpatterns = [
    # Home do marketplace — vitrine de prestadores
    path('', views.listar_produtos, name='listar_produtos'),
    # Perfil público de um prestador
    path('prestador/<slug:slug>/', views.perfil_prestador, name='perfil_prestador'),
    # Solicitar serviço a um prestador específico
    path('prestador/<slug:slug>/solicitar/', views.solicitar_servico, name='solicitar_servico'),
    # Painel do usuário (cliente + prestador)
    path('painel/', views.meu_painel, name='meu_painel'),
    # Atualizar status de um contrato (para prestadores)
    path('contrato/<int:contrato_id>/status/<str:novo_status>/', views.atualizar_status_contrato, name='atualizar_status'),
    # Avaliar contrato concluído (para clientes)
    path('contrato/<int:contrato_id>/avaliar/', views.avaliar_contrato, name='avaliar_contrato'),
    # Editar Perfil Prestador
    path('perfil/editar/', views.editar_perfil, name='editar_perfil'),
    
    # API endpoints
    path('api/categorias/', views.CategoriaListAPIView.as_view(), name='api_categorias'),
    path('api/prestadores/', views.PrestadorListAPIView.as_view(), name='api_prestadores'),
    path('api/prestadores/<int:pk>/', views.PrestadorRetrieveAPIView.as_view(), name='api_prestador_detail'),
    path('api/login/', views.LoginAPIView.as_view(), name='api_login'),
    path('api/register/', views.RegisterAPIView.as_view(), name='api_register'),
    path('api/logout/', views.LogoutAPIView.as_view(), name='api_logout'),
    path('api/profile/', views.ProfileAPIView.as_view(), name='api_profile'),
    path('api/become-professional/', views.BecomeProfessionalAPIView.as_view(), name='api_become_professional'),
    path('api/post-demand/', views.PostDemandAPIView.as_view(), name='api_post_demand'),
    path('api/contratos/', views.ContratoListAPIView.as_view(), name='api_contratos'),
]






