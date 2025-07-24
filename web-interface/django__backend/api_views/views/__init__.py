"""
Module d'initialisation pour les vues API.

Ce module expose toutes les vues API pour les différentes fonctionnalités du système.
"""

# Commenté pour éviter les erreurs d'importation circulaire
# from .topology_discovery_views import (
#     TopologyDiscoveryView,
#     NetworkTopologyView,
#     GetNetworkTopologyView,
#     StartTopologyDiscoveryView,
#     GetTopologyDiscoveryStatusView,
# )

from .topology_discovery_views import (
    TopologyDiscoveryViewSet,
    TopologyDiscoveryView,
    NetworkMapView,
    ConnectionsView,
    DeviceDependenciesView,
    PathDiscoveryView,
)

from .dashboard_views import (
    DashboardViewSet,
    SystemDashboardView,
    NetworkDashboardView,
    SecurityDashboardView,
    MonitoringDashboardView,
    CustomDashboardView,
    DashboardWidgetViewSet,
)

from .device_management_views import (
    DeviceManagementViewSet,
    DeviceListView,
    DeviceDetailView,
    DeviceConfigurationView,
    DeviceMetricsView,
    DeviceStatusView,
    DeviceInterfacesView,
    DeviceBackupView,
    DeviceRestoreView,
    DeviceBulkOperationView,
    DeviceComplianceView,
    DeviceRelationshipsView,
    DeviceInventoryView,
)

from .search_views import (
    GlobalSearchViewSet,
    ResourceSearchViewSet,
    ResourceDetailView,
    SearchAnalyticsView,
    SearchHistoryViewSet,
)

from .prometheus_views import (
    PrometheusViewSet,
    PrometheusMetricsView,
    PrometheusDeviceMetricsView,
)

from .grafana_views import (
    GrafanaViewSet,
    GrafanaDashboardView,
    GrafanaImportDashboardView,
)

from .security_views import (
    Fail2banViewSet,
    SuricataViewSet,
)

__all__ = [
    # ViewSets de découverte de topologie
    'TopologyDiscoveryViewSet',
    'TopologyDiscoveryView',
    'NetworkMapView',
    'ConnectionsView',
    'DeviceDependenciesView',
    'PathDiscoveryView',
    
    # ViewSets de tableaux de bord
    'DashboardViewSet',
    'SystemDashboardView',
    'NetworkDashboardView',
    'SecurityDashboardView',
    'MonitoringDashboardView',
    'CustomDashboardView',
    'DashboardWidgetViewSet',
    
    # ViewSets de gestion des équipements
    'DeviceManagementViewSet',
    'DeviceListView',
    'DeviceDetailView',
    'DeviceConfigurationView',
    'DeviceMetricsView',
    'DeviceStatusView',
    'DeviceInterfacesView',
    'DeviceBackupView',
    'DeviceRestoreView',
    'DeviceBulkOperationView',
    'DeviceComplianceView',
    'DeviceRelationshipsView',
    'DeviceInventoryView',
    
    # ViewSets de recherche
    'GlobalSearchViewSet',
    'ResourceSearchViewSet',
    'ResourceDetailView',
    'SearchAnalyticsView',
    'SearchHistoryViewSet',
    
    # ViewSets de monitoring Prometheus
    'PrometheusViewSet',
    'PrometheusMetricsView',
    'PrometheusDeviceMetricsView',
    
    # ViewSets de monitoring Grafana
    'GrafanaViewSet', 
    'GrafanaDashboardView',
    'GrafanaImportDashboardView',
    
    # ViewSets de sécurité
    'Fail2banViewSet',
    'SuricataViewSet',
] 