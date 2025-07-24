"""
ASGI config for nms_backend project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/asgi/
"""

import os
import django
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nms_backend.settings')

# Initialiser Django avant d'importer les modules qui utilisent les modèles
django.setup()

# Maintenant, on peut importer les modules qui dépendent des modèles
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from channels.security.websocket import AllowedHostsOriginValidator

# Import du routing principal WebSocket
try:
    from nms_backend.routing import websocket_urlpatterns
    print(f"✅ Routing WebSocket chargé avec {len(websocket_urlpatterns)} patterns")
except ImportError as e:
    print(f"❌ Erreur chargement routing WebSocket: {e}")
    websocket_urlpatterns = []

# Créer l'application ASGI avec support WebSocket complet
application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AllowedHostsOriginValidator(
        AuthMiddlewareStack(
            URLRouter(websocket_urlpatterns)
        )
    ),
})
