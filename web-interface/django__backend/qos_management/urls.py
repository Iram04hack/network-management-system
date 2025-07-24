"""
URLs pour l'application QoS Management avec APIs unifiées.

Inclut :
- APIs unifiées modernes (GNS3 + Docker)
- APIs legacy (ViewSets existants)
- Intégration avec le Service Central GNS3
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

# Legacy ViewSets
from .views.qos_policy_views import QoSPolicyViewSet
from .views.qos_policy_application_views import QoSPolicyApplicationViewSet
from .views.qos_policy_validation_views import QoSPolicyValidationViewSet
from .views.traffic_class_views import TrafficClassViewSet
from .views.traffic_classifier_views import TrafficClassifierViewSet
from .views.interface_qos_views import InterfaceQoSPolicyViewSet
from .views.qos_visualization_views import QoSVisualizationView
from .views.qos_configurer_views import (
    QoSConfigurerView,
    CBWFQConfigView,
    BandwidthAllocationView
)
from .views.qos_sla_reporting_views import (
    SLAComplianceReportView,
    QoSPerformanceReportView,
    SLATrendAnalysisView
)

# Nouvelles APIs unifiées
from .api_views.unified_qos_api import (
    unified_qos_status,
    unified_qos_data,
    unified_qos_dashboard,
    qos_infrastructure_health,
    unified_qos_endpoints,
    integration_status
)

# Router principal pour les opérations CRUD de base
router = DefaultRouter()
router.register(r'policies', QoSPolicyViewSet, basename='qos-policy')
router.register(r'traffic-classes', TrafficClassViewSet, basename='traffic-class')
router.register(r'classifiers', TrafficClassifierViewSet, basename='traffic-classifier')
router.register(r'interface-policies', InterfaceQoSPolicyViewSet, basename='interface-qos-policy')

# Router pour les opérations d'application des politiques QoS
application_router = DefaultRouter()
application_router.register(r'policy-application', QoSPolicyApplicationViewSet, basename='qos-policy-application')

# Router pour les opérations de validation des politiques QoS
validation_router = DefaultRouter()
validation_router.register(r'policy-validation', QoSPolicyValidationViewSet, basename='qos-policy-validation')

urlpatterns = [
    # === APIs UNIFIÉES (MODERNES) ===
    # Utilisation du pattern function-based views du monitoring et network_management
    path('unified/status/', unified_qos_status, name='unified-qos-status'),
    path('unified/qos-data/', unified_qos_data, name='unified-qos-data'),
    path('unified/dashboard/', unified_qos_dashboard, name='unified-qos-dashboard'),
    path('unified/infrastructure-health/', qos_infrastructure_health, name='qos-infrastructure-health'),
    path('unified/endpoints/', unified_qos_endpoints, name='unified-qos-endpoints'),
    path('unified/integration-status/', integration_status, name='qos-integration-status'),
    
    # === APIs LEGACY (COMPATIBILITÉ) ===
    # ViewSets existants pour compatibilité ascendante
    path('', include(router.urls)),
    path('', include(application_router.urls)),
    path('', include(validation_router.urls)),
    
    # URLs de visualisation
    path('visualization/<int:policy_id>/', QoSVisualizationView.as_view(), name='qos-visualization-policy'),
    path('visualization/', QoSVisualizationView.as_view(), name='qos-visualization'),
    
    # URLs de configuration
    path('configure/', QoSConfigurerView.as_view(), name='qos-configurer'),
    
    # URLs pour CBWFQ
    path('policies/<int:policy_id>/cbwfq/', CBWFQConfigView.as_view(), name='qos-cbwfq'),
    path('policies/<int:policy_id>/bandwidth-allocation/', BandwidthAllocationView.as_view(), name='qos-bandwidth-allocation'),
    
    # URLs pour les rapports SLA et QoS
    path('reports/sla/<int:device_id>/', SLAComplianceReportView.as_view(), name='sla-compliance-report'),
    path('reports/qos/', QoSPerformanceReportView.as_view(), name='qos-performance-report'),
    path('reports/sla/<int:device_id>/trends/', SLATrendAnalysisView.as_view(), name='sla-trend-analysis'),
] 