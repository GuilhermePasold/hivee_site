# Dashboard de Logs — Implementação Única

## O que faz

Captura requisições, erros, logins/logouts e buscas do site existente e expõe numa página `/logs/` acessível só por admin.

## Passos

### 1. Criar app `logs`

```bash
cd backend
python manage.py startapp logs
```

### 2. Modelo único

`backend/logs/models.py`:

```python
from django.db import models
from django.conf import settings


class LogEvent(models.Model):
    TIPOS = [
        ("request", "Requisição"),
        ("login", "Login"),
        ("logout", "Logout"),
        ("error", "Erro"),
        ("search", "Busca"),
    ]

    tipo = models.CharField(max_length=20, choices=TIPOS, db_index=True)
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    rota = models.CharField(max_length=500, blank=True)
    metodo = models.CharField(max_length=10, blank=True)
    status_code = models.SmallIntegerField(null=True, blank=True)
    ip = models.GenericIPAddressField(null=True, blank=True)
    duracao_ms = models.IntegerField(null=True, blank=True)
    payload = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]
```

### 3. Middleware (captura requests + erros + buscas)

`backend/logs/middleware.py`:

```python
import time
from django.utils import timezone


class RequestLogMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        inicio = time.time()
        response = self.get_response(request)
        duracao = int((time.time() - inicio) * 1000)

        if request.path.startswith("/admin/") or request.path.startswith("/api/"):
            from .models import LogEvent

            tipo = "error" if response.status_code >= 500 else "request"
            if "search" in request.GET or "search" in request.path.lower():
                tipo = "search"

            LogEvent.objects.create(
                tipo=tipo,
                usuario=request.user if request.user.is_authenticated else None,
                rota=request.path,
                metodo=request.method,
                status_code=response.status_code,
                ip=request.META.get("REMOTE_ADDR"),
                duracao_ms=duracao,
                payload={"query": dict(request.GET)},
            )

        return response
```

### 4. Signals (captura login/logout)

`backend/logs/signals.py`:

```python
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver
from .models import LogEvent


@receiver(user_logged_in)
def log_login(sender, request, user, **kwargs):
    LogEvent.objects.create(
        tipo="login",
        usuario=user,
        ip=request.META.get("REMOTE_ADDR"),
        payload={"session": request.session.session_key},
    )


@receiver(user_logged_out)
def log_logout(sender, request, user, **kwargs):
    LogEvent.objects.create(tipo="logout", usuario=user)
```

### 5. API (admin-only, paginada, filtrável)

`backend/logs/serializers.py`:

```python
from rest_framework import serializers
from .models import LogEvent


class LogEventSerializer(serializers.ModelSerializer):
    usuario_nome = serializers.SerializerMethodField()

    class Meta:
        model = LogEvent
        fields = "__all__"

    def get_usuario_nome(self, obj):
        return obj.usuario.get_full_name() or obj.usuario.username if obj.usuario else None
```

`backend/logs/views.py`:

```python
from rest_framework import viewsets, permissions
from .models import LogEvent
from .serializers import LogEventSerializer


class LogEventViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = LogEventSerializer
    permission_classes = [permissions.IsAdminUser]
    queryset = LogEvent.objects.all()
    filterset_fields = ["tipo", "status_code", "metodo"]
    search_fields = ["rota", "payload"]
    ordering = ["-created_at"]
```

`backend/logs/urls.py`:

```python
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register("logs", views.LogEventViewSet)

urlpatterns = [
    path("api/admin/", include(router.urls)),
]
```

### 6. Conectar tudo

`backend/logs/apps.py`:

```python
from django.apps import AppConfig


class LogsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "logs"

    def ready(self):
        import logs.signals
```

Em `backend/hivee/settings.py`:

```python
INSTALLED_APPS = [
    ...
    "logs",
]

MIDDLEWARE = [
    ...
    "logs.middleware.RequestLogMiddleware",
]
```

Em `backend/hivee/urls.py`:

```python
urlpatterns = [
    ...
    path("", include("logs.urls")),
]
```

### 7. Migrar

```bash
python manage.py makemigrations logs
python manage.py migrate logs
```

### 8. Página React (única, sem frescura)

`frontend/src/pages/LogDashboard.tsx`:

```tsx
import { useState, useEffect } from "react"
import api from "../lib/api"

interface LogEvent {
  id: number
  tipo: string
  usuario_nome: string | null
  rota: string
  metodo: string
  status_code: number | null
  ip: string | null
  duracao_ms: number | null
  payload: Record<string, unknown>
  created_at: string
}

export default function LogDashboard() {
  const [logs, setLogs] = useState<LogEvent[]>([])
  const [filtro, setFiltro] = useState("")
  const [pagina, setPagina] = useState(1)

  useEffect(() => {
    const params = new URLSearchParams({ page: String(pagina), ordering: "-created_at" })
    if (filtro) params.set("tipo", filtro)
    api.get(`/api/admin/logs/?${params}`).then((r) => setLogs(r.data.results))
  }, [filtro, pagina])

  return (
    <div style={{ padding: 24 }}>
      <h1>Logs do Sistema</h1>
      <select value={filtro} onChange={(e) => { setFiltro(e.target.value); setPagina(1) }}>
        <option value="">Todos</option>
        <option value="request">Requisições</option>
        <option value="login">Login</option>
        <option value="logout">Logout</option>
        <option value="error">Erros</option>
        <option value="search">Buscas</option>
      </select>
      <table border={1} cellPadding={6} style={{ width: "100%", marginTop: 16, borderCollapse: "collapse", fontSize: 13 }}>
        <thead>
          <tr>
            <th>Tipo</th><th>Usuário</th><th>Rota</th><th>Método</th><th>Status</th><th>IP</th><th>Duração</th><th>Data</th>
          </tr>
        </thead>
        <tbody>
          {logs.map((log) => (
            <tr key={log.id}>
              <td>{log.tipo}</td>
              <td>{log.usuario_nome ?? "-"}</td>
              <td style={{ maxWidth: 300, overflow: "hidden", textOverflow: "ellipsis" }}>{log.rota}</td>
              <td>{log.metodo}</td>
              <td>{log.status_code ?? "-"}</td>
              <td>{log.ip ?? "-"}</td>
              <td>{log.duracao_ms != null ? `${log.duracao_ms}ms` : "-"}</td>
              <td>{new Date(log.created_at).toLocaleString("pt-BR")}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <div style={{ marginTop: 12 }}>
        <button onClick={() => setPagina((p) => Math.max(1, p - 1))} disabled={pagina === 1}>Anterior</button>
        <span style={{ margin: "0 12px" }}>Página {pagina}</span>
        <button onClick={() => setPagina((p) => p + 1)}>Próxima</button>
      </div>
    </div>
  )
}
```

Adicionar rota em `frontend/src/main.tsx`:

```tsx
import LogDashboard from "./pages/LogDashboard"
// ...
<Route path="/logs" element={<LogDashboard />} />
```

### 9. Rodar

```bash
python manage.py migrate
python manage.py runserver
# Acessar /logs/ logado como admin
```

## Pronto

- Toda request em `/admin/` e `/api/` é logada
- Logins/logouts são capturados
- Erros 500+ são marcados como `tipo=error`
- Buscas com `?search=` viram `tipo=search`
- Única página React com tabela + filtro por tipo + paginação
- Só admin vê (permission `IsAdminUser`)
