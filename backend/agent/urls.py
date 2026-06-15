import logging

from django.urls import path

from . import webhooks

logger = logging.getLogger(__name__)

urlpatterns = [
    path("webhook/", webhooks.waha_webhook, name="waha-webhook"),
]
