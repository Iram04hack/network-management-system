"""
Configuration des routes WebSocket pour le module api_views.

Ce module définit les chemins URL pour les consommateurs WebSocket
permettant les mises à jour en temps réel.
"""

from django.urls import path
from channels.routing import URLRouter
from channels.auth import AuthMiddlewareStack
from .websocket_config import DashboardConsumer, AlertsConsumer, MonitoringConsumer


# Routes WebSocket
websocket_urlpatterns = [
    path('ws/api_views/dashboard/', DashboardConsumer.as_asgi()),
    path('ws/api_views/alerts/', AlertsConsumer.as_asgi()),
    path('ws/api_views/monitoring/', MonitoringConsumer.as_asgi()),
]

# Application ASGI pour le module api_views
application = AuthMiddlewareStack(
    URLRouter(websocket_urlpatterns)
) 