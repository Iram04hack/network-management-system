"""
Configuration du routage WebSocket pour les événements GNS3 temps réel.

Ce module configure les routes WebSocket Django Channels pour permettre
la communication bidirectionnelle temps réel avec les clients.
"""

from django.urls import re_path, path
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from channels.security.websocket import AllowedHostsOriginValidator

from .realtime_event_system import GNS3WebSocketConsumer


# Routes WebSocket pour les événements GNS3
websocket_urlpatterns = [
    # Connexion principale pour les événements GNS3
    re_path(r'ws/gns3/events/$', GNS3WebSocketConsumer.as_asgi()),
    
    # Routes spécialisées par type d'événement
    re_path(r'ws/gns3/events/nodes/$', GNS3WebSocketConsumer.as_asgi()),
    re_path(r'ws/gns3/events/projects/$', GNS3WebSocketConsumer.as_asgi()),
    re_path(r'ws/gns3/events/topology/$', GNS3WebSocketConsumer.as_asgi()),
    
    # Route pour les modules spécifiques
    re_path(r'ws/gns3/events/module/(?P<module_name>\w+)/$', GNS3WebSocketConsumer.as_asgi()),
]

# Configuration principale du routage des protocoles
application = ProtocolTypeRouter({
    # Routage WebSocket avec authentification et validation d'origine
    'websocket': AllowedHostsOriginValidator(
        AuthMiddlewareStack(
            URLRouter(websocket_urlpatterns)
        )
    ),
})