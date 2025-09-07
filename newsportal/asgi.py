"""
ASGI config for newsportal project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

import os
import django
from django.urls import path
from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application
from graphene_subscriptions.consumers import GraphqlSubscriptionConsumer

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "newsportal.settings")

application = ProtocolTypeRouter(
    {
        "http": get_asgi_application(),
        "websocket": AuthMiddlewareStack(
            URLRouter(
                [
                    path("graphql/", GraphqlSubscriptionConsumer),
                ]
            )
        ),
    }
)
