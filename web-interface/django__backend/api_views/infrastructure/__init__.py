"""
Infrastructure pour le module api_views.

Ce module expose les services d'infrastructure pour le module api_views,
notamment les adaptateurs de persistance, les services de cache et les WebSockets.
"""

# Exposition des repositories
from .repositories import (
    DjangoDashboardRepository,
    DjangoTopologyDiscoveryRepository,
    DjangoAPISearchRepository,
)

# Exposition des services de cache
from .cache_config import (
    api_cache, 
    monitor_cache_hit_rate,
    cache_dashboard_view,
    cache_topology_view,
    cache_search_view,
    cache_device_view,
    cache_monitoring_view,
    invalidate_cache_pattern,
)

# Exposition des services WebSocket
from .websocket_config import (
    send_dashboard_update,
    send_alert_notification,
    send_monitoring_update,
    DASHBOARD_GROUP,
    ALERTS_GROUP,
    DEVICE_STATUS_GROUP,
    MONITORING_GROUP,
    TOPOLOGY_GROUP,
)

# Exposition du routing WebSocket
from .routing import websocket_urlpatterns, application as websocket_application

# Exposition des vues d'infrastructure
# from .haproxy_views import HAProxyViewSet  # Vue temporairement commentée pour résoudre les imports

__all__ = [
    # Repositories
    'DjangoDashboardRepository',
    'DjangoTopologyDiscoveryRepository',
    'DjangoAPISearchRepository',
    
    # Cache
    'api_cache',
    'monitor_cache_hit_rate',
    'cache_dashboard_view',
    'cache_topology_view',
    'cache_search_view',
    'cache_device_view',
    'cache_monitoring_view',
    'invalidate_cache_pattern',
    
    # WebSockets
    'send_dashboard_update',
    'send_alert_notification',
    'send_monitoring_update',
    'DASHBOARD_GROUP',
    'ALERTS_GROUP',
    'DEVICE_STATUS_GROUP',
    'MONITORING_GROUP',
    'TOPOLOGY_GROUP',
    
    # Routing
    'websocket_urlpatterns',
    'websocket_application',
    
    # Views
    # 'HAProxyViewSet',  # Temporairement commenté
] 