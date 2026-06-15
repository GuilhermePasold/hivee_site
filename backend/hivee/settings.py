"""Django settings for the HIVEE backend."""
import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "django-insecure-hivee-dev-fallback")
DEBUG = os.getenv("DJANGO_DEBUG", "True").lower() == "true"
# Smell fix: hosts come from configuration (env), never a wildcard. The safe
# default covers local development; production passes its own real hostnames.
ALLOWED_HOSTS = [
    host.strip()
    for host in os.getenv("DJANGO_ALLOWED_HOSTS", "127.0.0.1,localhost").split(",")
    if host.strip()
]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "daphne",
    "django.contrib.staticfiles",
    "rest_framework",
    "rest_framework.authtoken",
    "drf_spectacular",
    "corsheaders",
    "channels",
    "catalog",
    "agent.apps.AgentConfig",
    "logs",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "logs.middleware.RequestLogMiddleware",
]

ROOT_URLCONF = "hivee.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "base" / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "hivee.wsgi.application"
ASGI_APPLICATION = "hivee.asgi.application"

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels.layers.InMemoryChannelLayer",
    },
}

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "hivee.db",
    },
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": 6}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
]

LANGUAGE_CODE = "pt-br"
TIME_ZONE = "America/Sao_Paulo"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "base" / "static"]
STATIC_ROOT = BASE_DIR / "static_files"
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        # Le o token do header Authorization (Swagger/Postman) OU de um
        # cookie httpOnly enviado pelo navegador (front-end seguro).
        "catalog.authentication.CookieTokenAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.AllowAny"],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 9,
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": os.getenv("DJANGO_THROTTLE_ANON", "1000/hour" if DEBUG else "20/hour"),
        "user": os.getenv("DJANGO_THROTTLE_USER", "200/hour"),
    },
}

SPECTACULAR_SETTINGS = {
    "TITLE": "API do HIVEE",
    "DESCRIPTION": "Documentacao oficial da API de prestadores e categorias do HIVEE.",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
}

# Cookie httpOnly que transporta o token de autenticacao (smell fix #2).
# `Secure` so e exigido fora de DEBUG, para funcionar em http://localhost.
AUTH_COOKIE_NAME = os.getenv("DJANGO_AUTH_COOKIE_NAME", "hivee_token")
AUTH_COOKIE_SECURE = not DEBUG
AUTH_COOKIE_SAMESITE = "Lax"
AUTH_COOKIE_MAX_AGE = 60 * 60 * 24 * 14  # 14 dias

# URL pública do front-end, usada para montar links em canais externos
# (ex.: WhatsApp) onde o caminho relativo da notificação não basta.
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5200")

CORS_ALLOW_ALL_ORIGINS = True

CSRF_TRUSTED_ORIGINS = [
    host.strip()
    for host in os.getenv("DJANGO_CSRF_TRUSTED_ORIGINS", "http://localhost:5200,http://127.0.0.1:5200").split(",")
    if host.strip()
]
