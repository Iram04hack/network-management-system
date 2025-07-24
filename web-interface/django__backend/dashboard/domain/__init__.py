"""
Package domain du module dashboard.

Contient les entités, interfaces et règles métier du tableau de bord.
"""

from .entities import (
    DashboardOverview,
    NetworkOverview, 
    TopologyView,
    DeviceStatus,
    ConnectionStatus,
    SystemHealthMetrics,
    AlertInfo,
    DeviceInfo,
    AlertSeverity
)

from .interfaces import (
    IMonitoringDataProvider,
    INetworkDataProvider,
    ICacheService,
    IDashboardDataService,
    INetworkOverviewService,
    ITopologyVisualizationService
)

__all__ = [
    'DashboardOverview',
    'NetworkOverview', 
    'TopologyView',
    'DeviceStatus',
    'ConnectionStatus',
    'SystemHealthMetrics',
    'AlertInfo',
    'DeviceInfo',
    'AlertSeverity',
    'IMonitoringDataProvider',
    'INetworkDataProvider',
    'ICacheService',
    'IDashboardDataService',
    'INetworkOverviewService',
    'ITopologyVisualizationService',
] 