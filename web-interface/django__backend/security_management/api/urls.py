"""
Configuration des URLs pour les APIs REST du module security_management.

Ce module définit toutes les routes pour :
- Les APIs unifiées de sécurité avec intégration GNS3
- La gestion CRUD des règles de sécurité
- L'analyse d'événements et détection d'anomalies
- La surveillance des services Docker
- Les métriques et rapports de sécurité
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

# Import des APIs unifiées
from ..api_views.unified_security_api import (
    get_security_dashboard,
    process_security_event,
    run_security_analysis,
    get_security_status,
    get_security_alerts,
    get_security_rules,
    get_vulnerabilities,
    get_security_metrics
)

# Import des APIs existantes
from .views import (
    security_api_root,
    SecurityRuleViewSet,
    SecurityRuleConflictAPIView,
    SecurityRuleImpactAnalysisAPIView,
    DockerServiceMonitoringAPIView,
    validate_security_rule,
    get_conflict_resolution_suggestions
)
from .additional_views import (
    dashboard_api,
    health_check_api,
    metrics_api,
    bulk_operations_api,
    export_rules_api,
    import_rules_api,
    conflict_reports_api,
    performance_reports_api,
    security_reports_api
)
from .event_analysis_views import (
    SecurityEventAnalysisAPIView,
    AnomalyDetectionAPIView
)
from .correlation_views import (
    EventCorrelationAPIView
)

# Configuration du router pour les ViewSets
router = DefaultRouter()
router.register(r'rules', SecurityRuleViewSet, basename='security-rules')

# URLs des APIs REST
urlpatterns = [
    # Vue racine de l'API Security Management
    path('', security_api_root, name='security-api-root'),
    
    # ===== APIs UNIFIÉES DE SÉCURITÉ =====
    path('dashboard/', get_security_dashboard, name='unified-security-dashboard'),
    path('events/process/', process_security_event, name='process-security-event'),
    path('analysis/', run_security_analysis, name='run-security-analysis'),
    path('status/', get_security_status, name='security-status'),
    path('alerts/', get_security_alerts, name='security-alerts'),
    path('rules/', get_security_rules, name='security-rules-list'),
    path('vulnerabilities/', get_vulnerabilities, name='vulnerabilities-list'),
    path('metrics/', get_security_metrics, name='security-metrics'),
    
    # ===== APIs CRUD EXISTANTES =====
    path('crud/', include(router.urls)),
    
    # ===== APIs DE DÉTECTION DE CONFLITS =====
    path('conflicts/', SecurityRuleConflictAPIView.as_view(), name='rule-conflicts'),
    path('conflicts/suggestions/<str:conflict_id>/', 
         get_conflict_resolution_suggestions, 
         name='conflict-resolution-suggestions'),
    
    # ===== APIs D'ANALYSE D'IMPACT =====
    path('impact-analysis/', SecurityRuleImpactAnalysisAPIView.as_view(), name='impact-analysis'),
    path('impact-analysis/<int:rule_id>/', 
         SecurityRuleImpactAnalysisAPIView.as_view(), 
         name='rule-impact-analysis'),
    
    # ===== APIs DE SURVEILLANCE DOCKER =====
    path('docker/services/', DockerServiceMonitoringAPIView.as_view(), name='docker-services'),
    path('docker/services/<str:service_name>/', 
         DockerServiceMonitoringAPIView.as_view(), 
         name='docker-service-detail'),
    
    # ===== APIs DE VALIDATION =====
    path('validate/', validate_security_rule, name='validate-rule'),
    
    # ===== APIs D'ADMINISTRATION ET DE STATISTIQUES =====
    path('admin/dashboard/', dashboard_api, name='admin-dashboard'),
    path('admin/health/', health_check_api, name='health-check'),
    path('admin/metrics/', metrics_api, name='admin-metrics'),
    
    # ===== APIs DE GESTION EN LOT =====
    path('bulk-operations/', bulk_operations_api, name='bulk-operations'),
    
    # ===== APIs D'EXPORT ET D'IMPORT =====
    path('export/', export_rules_api, name='export-rules'),
    path('import/', import_rules_api, name='import-rules'),
    
    # ===== APIs DE REPORTING =====
    path('reports/conflicts/', conflict_reports_api, name='conflict-reports'),
    path('reports/performance/', performance_reports_api, name='performance-reports'),
    path('reports/security/', security_reports_api, name='security-reports'),
    
    # ===== APIs D'ANALYSE D'ÉVÉNEMENTS ET D'ANOMALIES =====
    path('events/analysis/', SecurityEventAnalysisAPIView.as_view(), name='event-analysis'),
    path('anomalies/detection/', AnomalyDetectionAPIView.as_view(), name='anomaly-detection'),
    path('correlation/analysis/', EventCorrelationAPIView.as_view(), name='correlation-analysis'),
]

app_name = 'security_management_api'