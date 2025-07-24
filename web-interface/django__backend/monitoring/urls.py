"""
Configuration des URLs pour l'application monitoring.
Documentation intégrée dans la configuration Swagger globale.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .api_views.metrics_api import (
    MetricsDefinitionViewSet,
    DeviceMetricViewSet,
    MetricValueViewSet
)
from .api_views.service_check_api import (
    ServiceCheckViewSet,
    DeviceServiceCheckViewSet,
    CheckResultViewSet
)
from .api_views.alerts_api import AlertViewSet
from .api_views.dashboard_api import (
    DashboardViewSet,
    DashboardWidgetViewSet,
    DashboardShareViewSet
)
from .api_views.notifications_api import (
    NotificationViewSet,
    NotificationChannelViewSet,
    NotificationRuleViewSet
)
from .api_views.external_integration_views import (
    test_external_services,
    collect_device_metrics,
    create_device_dashboard,
    search_device_alerts,
    get_infrastructure_health,
    bulk_collect_metrics
)
from .api_views.topology_integration_views import (
    get_monitorable_devices,
    get_device_configuration,
    update_monitoring_status,
    get_topology_health,
    sync_with_topology,
    check_topology_service_status
)
from .api_views.unified_monitoring_api import (
    unified_monitoring_status,
    nms_services_health,
    unified_metrics_collection,
    unified_monitoring_dashboard,
    specialized_service_data,
    monitoring_service_endpoints,
    service_integration_status,
    test_services_connectivity
)

# Configuration du routeur API REST
router = DefaultRouter()

# Module monitoring complet - Tous les ViewSets fonctionnels
router.register(r'metrics-definitions', MetricsDefinitionViewSet, basename='metrics-definition')
router.register(r'device-metrics', DeviceMetricViewSet, basename='device-metric')
router.register(r'metric-values', MetricValueViewSet, basename='metric-value')
router.register(r'alerts', AlertViewSet, basename='alert')
router.register(r'service-checks', ServiceCheckViewSet, basename='service-check')
router.register(r'device-checks', DeviceServiceCheckViewSet, basename='device-check')
router.register(r'check-results', CheckResultViewSet, basename='check-result')
router.register(r'dashboards', DashboardViewSet, basename='dashboard')
router.register(r'dashboard-widgets', DashboardWidgetViewSet, basename='dashboard-widget')
router.register(r'dashboard-shares', DashboardShareViewSet, basename='dashboard-share')
router.register(r'notifications', NotificationViewSet, basename='notification')
router.register(r'notification-channels', NotificationChannelViewSet, basename='notification-channel')
router.register(r'notification-rules', NotificationRuleViewSet, basename='notification-rule')

urlpatterns = [
    # API REST - routes principales
    path('', include(router.urls)),
    
    # ==================== API UNIFIÉE MONITORING GNS3 + DOCKER ====================
    # Service Unifié Principal
    path('unified/status/', unified_monitoring_status, name='unified-monitoring-status'),
    path('unified/metrics/', unified_metrics_collection, name='unified-metrics-collection'),
    path('unified/dashboard/', unified_monitoring_dashboard, name='unified-monitoring-dashboard'),
    
    # Santé des Services NMS Docker
    path('unified/nms-health/', nms_services_health, name='nms-services-health'),
    path('unified/specialized/', specialized_service_data, name='specialized-service-data'),
    
    # Configuration et Intégration
    path('unified/endpoints/', monitoring_service_endpoints, name='monitoring-service-endpoints'),
    path('unified/integration-status/', service_integration_status, name='service-integration-status'),
    path('unified/test-connectivity/', test_services_connectivity, name='test-services-connectivity'),
    
    # ==================== API D'INTÉGRATION EXTERNE (LEGACY) ====================
    # API d'intégration des services externes
    path('external/test-services/', test_external_services, name='test-external-services'),
    path('external/collect-metrics/', collect_device_metrics, name='collect-device-metrics'),
    path('external/create-dashboard/', create_device_dashboard, name='create-device-dashboard'),
    path('external/search-alerts/', search_device_alerts, name='search-device-alerts'),
    path('external/infrastructure-health/', get_infrastructure_health, name='infrastructure-health'),
    path('external/bulk-collect/', bulk_collect_metrics, name='bulk-collect-metrics'),
    
    # ==================== API D'INTÉGRATION TOPOLOGIE (LEGACY) ====================
    # API d'intégration avec le Service Central de Topologie
    path('topology/devices/', get_monitorable_devices, name='topology-monitorable-devices'),
    path('topology/devices/<int:device_id>/config/', get_device_configuration, name='topology-device-config'),
    path('topology/devices/<int:device_id>/status/', update_monitoring_status, name='topology-update-status'),
    path('topology/health/', get_topology_health, name='topology-health'),
    path('topology/sync/', sync_with_topology, name='topology-sync'),
    path('topology/service-status/', check_topology_service_status, name='topology-service-status'),
]