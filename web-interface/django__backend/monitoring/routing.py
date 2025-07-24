"""
Routing WebSocket pour le module monitoring.

Configuration des routes WebSocket pour les fonctionnalités
de monitoring en temps réel.
"""

from django.urls import re_path, path
from . import consumers

websocket_urlpatterns = [
    # Monitoring général
    re_path(r'ws/monitoring/$', consumers.MonitoringWebSocketConsumer.as_asgi()),
    
    # Monitoring spécifique à un équipement
    re_path(r'ws/monitoring/device/(?P<device_id>\d+)/$', consumers.MonitoringWebSocketConsumer.as_asgi()),
    
    # Alertes en temps réel
    re_path(r'ws/monitoring/alerts/$', consumers.AlertsWebSocketConsumer.as_asgi()),
    
    # Compatibilité avec l'ancien format
    re_path(r'ws/monitoring/metrics/$', consumers.MonitoringWebSocketConsumer.as_asgi()),
    path('ws/monitoring/metrics/<str:device_id>/', consumers.MonitoringWebSocketConsumer.as_asgi()),
    path('ws/monitoring/dashboards/<str:dashboard_uid>/', consumers.MonitoringWebSocketConsumer.as_asgi()),
    path('ws/monitoring/notifications/', consumers.AlertsWebSocketConsumer.as_asgi()),
] 