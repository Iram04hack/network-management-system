"""
Configuration du routage des WebSockets pour le module dashboard.

Ce module définit les routes WebSocket pour les mises à jour en temps réel
du tableau de bord et des topologies.
"""

from django.urls import re_path
from .consumers import DashboardConsumer, TopologyConsumer

websocket_urlpatterns = [
    # WebSocket pour les mises à jour générales du dashboard
    re_path(r'ws/dashboard/$', DashboardConsumer.as_asgi()),
    
    # WebSocket pour les mises à jour de topologie spécifique
    re_path(r'ws/dashboard/topology/(?P<topology_id>\d+)/$', TopologyConsumer.as_asgi()),
] 