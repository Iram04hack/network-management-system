# Contenu pour nms_backend/routing.py
from django.urls import re_path

# Import des consumers WebSocket
websocket_urlpatterns = []

# Consumers monitoring avec import sécurisé
try:
    from monitoring.consumers import MonitoringWebSocketConsumer, AlertsWebSocketConsumer
    
    websocket_urlpatterns.extend([
        # Monitoring WebSocket URLs
        re_path(r'ws/monitoring/$', MonitoringWebSocketConsumer.as_asgi()),
        re_path(r'ws/monitoring/device/(?P<device_id>\d+)/$', MonitoringWebSocketConsumer.as_asgi()),
        re_path(r'ws/monitoring/alerts/$', AlertsWebSocketConsumer.as_asgi()),
        re_path(r'ws/monitoring/metrics/$', MonitoringWebSocketConsumer.as_asgi()),
        
        # Compatibilité avec anciennes URLs
        re_path(r'ws/metrics/(?P<device_id>\d+)/(?P<metric_type>\w+)/$', MonitoringWebSocketConsumer.as_asgi()),
        re_path(r'ws/metrics/$', MonitoringWebSocketConsumer.as_asgi()),
        re_path(r'ws/alerts/(?P<alert_type>\w+)/$', AlertsWebSocketConsumer.as_asgi()),
    ])
    print("✅ Monitoring WebSocket consumers chargés")
except ImportError as e:
    print(f"⚠️ Monitoring consumers non disponibles: {e}")
    pass

# Ajouter les routes pour l'assistant IA
try:
    from ai_assistant.consumers import ChatConsumer, NetworkMonitoringConsumer
    
    websocket_urlpatterns += [
        re_path(r'ws/ai/chat/$', ChatConsumer.as_asgi()),
        re_path(r'ws/ai/monitoring/$', NetworkMonitoringConsumer.as_asgi()),
    ]
except ImportError:
    print("Info: ai_assistant.consumers non disponible")
    pass

# Intégration des WebSockets dashboard
try:
    from dashboard.routing import websocket_urlpatterns as dashboard_ws_urls
    websocket_urlpatterns += dashboard_ws_urls
    print("✅ Dashboard WebSocket consumers chargés")
except ImportError as e:
    print(f"⚠️ Dashboard consumers non disponibles: {e}")
    pass

# Intégration des WebSockets GNS3
try:
    from common.routing import websocket_urlpatterns as gns3_ws_urls
    websocket_urlpatterns += gns3_ws_urls
    print("✅ GNS3 WebSocket consumers chargés")
except ImportError as e:
    print(f"⚠️ GNS3 consumers non disponibles: {e}")
    # Fallback pour GNS3 WebSocket si common.routing n'est pas disponible
    try:
        from common.infrastructure.realtime_event_system import GNS3WebSocketConsumer
        websocket_urlpatterns.extend([
            re_path(r'ws/gns3/events/$', GNS3WebSocketConsumer.as_asgi()),
            re_path(r'ws/gns3/events/(?P<room_name>\w+)/$', GNS3WebSocketConsumer.as_asgi()),
            re_path(r'ws/gns3/module/(?P<module_name>\w+)/$', GNS3WebSocketConsumer.as_asgi()),
            re_path(r'ws/gns3/topology/$', GNS3WebSocketConsumer.as_asgi()),
            re_path(r'ws/gns3/nodes/$', GNS3WebSocketConsumer.as_asgi()),
        ])
        print("✅ GNS3 WebSocket consumers chargés (fallback)")
    except ImportError as e2:
        print(f"⚠️ Fallback GNS3 consumers non disponibles: {e2}")
        pass

# Intégration des WebSockets api_views  
try:
    from api_views.infrastructure.routing import websocket_urlpatterns as api_views_ws_urls
    websocket_urlpatterns += api_views_ws_urls
except ImportError:
    print("Info: api_views.infrastructure.routing non disponible")
    pass
