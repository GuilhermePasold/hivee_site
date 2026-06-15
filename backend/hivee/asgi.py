import os

from django.core.asgi import get_asgi_application
from django.urls import re_path

from channels.routing import ProtocolTypeRouter, URLRouter

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "hivee.settings")

django_asgi_app = get_asgi_application()

from agent.consumers import ChatConsumer
from catalog.consumers import NotificationsConsumer

application = ProtocolTypeRouter(
    {
        "http": django_asgi_app,
        "websocket": URLRouter(
            [
                re_path(r"ws/chat/(?P<telefone>[\w-]+)/$", ChatConsumer.as_asgi()),
                re_path(r"ws/notifications/$", NotificationsConsumer.as_asgi()),
            ]
        ),
    }
)
