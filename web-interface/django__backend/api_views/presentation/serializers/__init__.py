"""
Sérialiseurs pour le module API Views.

Ce module contient tous les sérialiseurs pour la validation et la transformation
des données dans les API du système de gestion de réseau.
"""

from .base_serializers import (
    BaseAPISerializer,
    PaginatedResponseSerializer,
    ErrorResponseSerializer,
    SuccessResponseSerializer
)

from .dashboard_serializers import (
    DashboardDataSerializer,
    DashboardConfigurationSerializer,
    DashboardRequestSerializer,
    DashboardWidgetSerializer,
    CustomDashboardSerializer
)

from .topology_serializers import (
    TopologyDiscoverySerializer,
    NetworkTopologySerializer,
    TopologyRequestSerializer,
    DiscoveryStatusSerializer,
    NetworkMapSerializer
)

from .device_serializers import (
    DeviceManagementSerializer,
    DeviceDetailSerializer,
    DeviceListSerializer,
    DeviceUpdateSerializer,
    DeviceCreationSerializer
)

from .search_serializers import (
    SearchRequestSerializer,
    SearchResponseSerializer,
    ResourceDetailSerializer,
    SearchSuggestionSerializer,
    GlobalSearchSerializer
)

__all__ = [
    # Base serializers
    'BaseAPISerializer',
    'PaginatedResponseSerializer', 
    'ErrorResponseSerializer',
    'SuccessResponseSerializer',
    
    # Dashboard serializers
    'DashboardDataSerializer',
    'DashboardConfigurationSerializer',
    'DashboardRequestSerializer',
    'DashboardWidgetSerializer',
    'CustomDashboardSerializer',
    
    # Topology serializers
    'TopologyDiscoverySerializer',
    'NetworkTopologySerializer',
    'TopologyRequestSerializer',
    'DiscoveryStatusSerializer',
    'NetworkMapSerializer',
    
    # Device serializers
    'DeviceManagementSerializer',
    'DeviceDetailSerializer',
    'DeviceListSerializer',
    'DeviceUpdateSerializer',
    'DeviceCreationSerializer',
    
    # Search serializers
    'SearchRequestSerializer',
    'SearchResponseSerializer',
    'ResourceDetailSerializer',
    'SearchSuggestionSerializer',
    'GlobalSearchSerializer',
] 