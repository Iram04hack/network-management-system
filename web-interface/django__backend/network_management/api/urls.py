"""
Module contenant les URLs pour les vues API du module Network Management.

Inclut :
- APIs unifiées modernes (GNS3 + Docker)
- APIs legacy (ViewSets existants)
- Intégration avec le Service Central GNS3
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

# Legacy ViewSets
from .device_views import DeviceViewSet
from .interface_views import InterfaceViewSet
from .configuration_views import ConfigurationViewSet
from .topology_views import NetworkTopologyViewSet

# Nouvelles APIs unifiées
from ..api_views.unified_network_api import (
    unified_status,
    unified_network_data,
    unified_dashboard,
    network_infrastructure_health,
    unified_endpoints,
    integration_status
)

# Créer un routeur pour les APIs legacy
router = DefaultRouter()
router.register(r'devices', DeviceViewSet, basename='device')
router.register(r'interfaces', InterfaceViewSet, basename='interface')
router.register(r'configurations', ConfigurationViewSet, basename='configuration')
router.register(r'topology', NetworkTopologyViewSet, basename='network-topology')

# Définir les URLs
urlpatterns = [
    # === APIs UNIFIÉES (MODERNES) ===
    # Utilisation du pattern function-based views du monitoring
    path('unified/status/', unified_status, name='unified-status'),
    path('unified/network-data/', unified_network_data, name='unified-network-data'),
    path('unified/dashboard/', unified_dashboard, name='unified-dashboard'),
    path('unified/infrastructure-health/', network_infrastructure_health, name='network-infrastructure-health'),
    path('unified/endpoints/', unified_endpoints, name='unified-endpoints'),
    path('unified/integration-status/', integration_status, name='integration-status'),
    
    # === APIs LEGACY (COMPATIBILITÉ) ===
    # ViewSets existants pour compatibilité ascendante
    path('', include(router.urls)),
]
