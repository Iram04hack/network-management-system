"""
Package des vues API pour le module de monitoring.
"""

from .metrics_api import MetricsDefinitionViewSet, DeviceMetricViewSet, MetricValueViewSet
# from .metrics_views import MetricsView, MetricDataView, MetricThresholdView  # Fichier dupliqué
from .service_check_api import ServiceCheckViewSet, DeviceServiceCheckViewSet, CheckResultViewSet
from .alerts_api import AlertViewSet
from .dashboard_api import DashboardViewSet, DashboardWidgetViewSet, DashboardShareViewSet
from .notifications_api import NotificationViewSet, NotificationChannelViewSet, NotificationRuleViewSet
from .swagger import schema_view

__all__ = [
    # Vues API pour les métriques
    'MetricsDefinitionViewSet',
    'DeviceMetricViewSet',
    'MetricValueViewSet',
    
    # Vues traditionnelles pour les métriques (commentées car dupliquées)
    # 'MetricsView',
    # 'MetricDataView',
    # 'MetricThresholdView',
    
    # Vues API pour les vérifications de service
    'ServiceCheckViewSet',
    'DeviceServiceCheckViewSet',
    'CheckResultViewSet',
    
    # Vues API pour les alertes
    'AlertViewSet',
    
    # Vues API pour les tableaux de bord
    'DashboardViewSet',
    'DashboardWidgetViewSet',
    'DashboardShareViewSet',
    
    # Vues API pour les notifications
    'NotificationViewSet',
    'NotificationChannelViewSet',
    'NotificationRuleViewSet',
    
    # Documentation Swagger
    'schema_view',
] 