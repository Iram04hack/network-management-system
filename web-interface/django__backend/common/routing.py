"""
Routing WebSocket pour le Service Central GNS3.

Configure les routes WebSocket pour les événements temps réel GNS3
et la communication bidirectionnelle avec les clients.
"""

from django.urls import re_path, path
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from channels.security.websocket import AllowedHostsOriginValidator

from .infrastructure.realtime_event_system import GNS3WebSocketConsumer


# Routes WebSocket pour GNS3
gns3_websocket_urlpatterns = [
    # WebSocket principal pour les événements GNS3
    re_path(r'ws/gns3/events/$', GNS3WebSocketConsumer.as_asgi()),
    
    # WebSocket avec room spécifique pour l'isolation
    re_path(r'ws/gns3/events/(?P<room_name>\w+)/$', GNS3WebSocketConsumer.as_asgi()),
    
    # WebSocket pour un module spécifique
    re_path(r'ws/gns3/module/(?P<module_name>\w+)/$', GNS3WebSocketConsumer.as_asgi()),
    
    # WebSocket pour les événements de topologie uniquement
    re_path(r'ws/gns3/topology/$', GNS3WebSocketConsumer.as_asgi()),
    
    # WebSocket pour les événements de nœuds uniquement
    re_path(r'ws/gns3/nodes/$', GNS3WebSocketConsumer.as_asgi()),
]

# Configuration complète du routing
application = ProtocolTypeRouter({
    # Route HTTP normale (gérée par Django)
    "http": None,  # Sera configuré par Django
    
    # Routes WebSocket
    "websocket": AllowedHostsOriginValidator(
        AuthMiddlewareStack(
            URLRouter(gns3_websocket_urlpatterns)
        )
    ),
})

# Export pour l'utilisation dans les settings
websocket_urlpatterns = gns3_websocket_urlpatterns