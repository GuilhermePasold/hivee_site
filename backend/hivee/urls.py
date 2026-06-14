from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path("admin/", admin.site.urls),
    # Documentacao da API (drf-spectacular):
    # 1. schema -> arquivo OpenAPI (JSON/YAML) com todas as definicoes da API.
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    # 2. docs -> interface visual Swagger que le o schema acima.
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("", include("catalog.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
