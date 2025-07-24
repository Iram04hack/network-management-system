"""
Configuration des URLs pour le module API Views.

Ce module définit toutes les routes URL pour les vues API du système de gestion réseau,
intégrant tous les composants avec pagination, filtrage et recherche avancés.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
# Configuration Swagger intégrée dans le module global
# from .docs.swagger import schema_view as swagger_schema_view, API_TAGS  # Intégré dans la config globale

# Import des vues principales
from .views.dashboard_views import (
    DashboardViewSet,
    SystemDashboardView,
    NetworkDashboardView,
    SecurityDashboardView,
    MonitoringDashboardView,
    CustomDashboardView,
    DashboardWidgetViewSet
)

from .views.topology_discovery_views import (
    TopologyDiscoveryViewSet
)

from .views.device_management_views import (
    DeviceManagementViewSet
)

from .views.search_views import (
    GlobalSearchViewSet,
    ResourceSearchViewSet,
    SearchHistoryViewSet
)

# Import des vues de monitoring
from .views.prometheus_views import (
    PrometheusViewSet,
    PrometheusMetricsView,
    PrometheusDeviceMetricsView
)

from .views.grafana_views import (
    GrafanaViewSet,
    GrafanaDashboardView,
    GrafanaImportDashboardView
)

from .views.security_views import (
    Fail2banViewSet,
    SuricataViewSet
)

# Import de la vue de test
from .test_swagger import test_api

# Configuration Swagger intégrée dans le module global
# schema_view = swagger_schema_view  # Commenté - utilise la config globale

# Configuration du routeur principal
router = DefaultRouter()

# Enregistrement des ViewSets
router.register(r'dashboards', DashboardViewSet, basename='api-dashboard')
router.register(r'dashboard-widgets', DashboardWidgetViewSet, basename='api-dashboard-widget')
router.register(r'topology-discovery', TopologyDiscoveryViewSet, basename='api-topology-discovery')
router.register(r'device-management', DeviceManagementViewSet, basename='api-device-management')
router.register(r'search', GlobalSearchViewSet, basename='api-global-search')
router.register(r'resource-search', ResourceSearchViewSet, basename='api-resource-search')
router.register(r'search-history', SearchHistoryViewSet, basename='api-search-history')
router.register(r'prometheus', PrometheusViewSet, basename='api-prometheus')
router.register(r'grafana', GrafanaViewSet, basename='api-grafana')
router.register(r'fail2ban', Fail2banViewSet, basename='api-fail2ban')
router.register(r'suricata', SuricataViewSet, basename='api-suricata')

# URLs principales
urlpatterns = [
    # API Router (inclut toutes les routes des ViewSets)
    path('', include(router.urls)),
    
    # === DASHBOARD APIs ===
    path('dashboards/system/', SystemDashboardView.as_view(), name='api-system-dashboard'),
    path('dashboards/network/', NetworkDashboardView.as_view(), name='api-network-dashboard'),
    path('dashboards/security/', SecurityDashboardView.as_view(), name='api-security-dashboard'),
    path('dashboards/monitoring/', MonitoringDashboardView.as_view(), name='api-monitoring-dashboard'),
    path('dashboards/custom/<int:dashboard_id>/', CustomDashboardView.as_view(), name='api-custom-dashboard'),
    
    # === ROUTES SPÉCIALISÉES ===
    # Les routes principales sont gérées par les ViewSets ci-dessus
    
    # === PROMETHEUS MONITORING APIs ===
    path('prometheus/metrics/', PrometheusMetricsView.as_view(), name='api-prometheus-metrics'),
    path('prometheus/device-metrics/<int:device_id>/', PrometheusDeviceMetricsView.as_view(), name='api-prometheus-device-metrics'),
    
    # === GRAFANA MONITORING APIs ===
    path('grafana/dashboards/<int:dashboard_id>/', GrafanaDashboardView.as_view(), name='api-grafana-dashboard'),
    path('grafana/import-dashboard/', GrafanaImportDashboardView.as_view(), name='api-grafana-import-dashboard'),
    
    # === SECURITY APIs ===
    # Les routes Fail2ban et Suricata sont gérées par les ViewSets ci-dessus
    
    # === DOCUMENTATION APIs ===
    # Documentation intégrée dans la configuration Swagger globale
    
    # === TEST API ===
    path('test/', test_api, name='api-test'),
]

# Patterns d'URL nommés pour référence externe
app_name = 'api_views' 