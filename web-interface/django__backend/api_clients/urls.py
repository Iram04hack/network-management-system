"""
Configuration des URLs pour l'application api_clients.
Documentation intégrée dans la configuration Swagger globale.
Version simplifiée pour test Swagger.
"""

from django.urls import path
from django.http import JsonResponse
from . import views

def test_endpoint(request):
    """Endpoint de test simple pour vérifier que le module fonctionne."""
    return JsonResponse({
        "message": "✅ Module api_clients fonctionne !",
        "module": "api_clients",
        "status": "OK"
    })

urlpatterns = [
    # ==================== TEST ENDPOINT ====================
    path('test/', test_endpoint, name='test-endpoint'),
    # ==================== STATUT DES CLIENTS ====================
    path('network/', views.network_clients, name='network-clients-status'),
    path('monitoring/', views.monitoring_clients, name='monitoring-clients-status'),
    path('infrastructure/', views.infrastructure_clients, name='infrastructure-clients-status'),
    path('security/', views.security_clients, name='security-clients-status'),
    
    # ==================== CLIENTS RÉSEAU - GNS3 ====================
    path('network/gns3/projects/', views.gns3_projects, name='gns3-projects-list'),
    path('network/gns3/projects/create/', views.create_gns3_project, name='gns3-projects-create'),
    path('network/gns3/projects/<str:project_id>/', views.get_gns3_project, name='gns3-project-detail'),
    
    # ==================== CLIENTS RÉSEAU - SNMP ====================
    path('network/snmp/query/', views.snmp_query, name='snmp-query'),
    path('network/snmp/walk/', views.snmp_walk, name='snmp-walk'),
    path('network/snmp/system/', views.snmp_system_info, name='snmp-system-info'),
    
    # ==================== CLIENTS MONITORING - PROMETHEUS ====================
    path('monitoring/prometheus/query/', views.prometheus_query, name='prometheus-query'),
    
    # ==================== CLIENTS SÉCURITÉ - FAIL2BAN ====================
    path('security/fail2ban/jails/', views.fail2ban_jails, name='fail2ban-jails'),
    
    # ==================== HEALTH MONITORING ====================
    path('health/', views.comprehensive_health_check, name='comprehensive-health-check'),
    path('status/', views.global_status, name='global-status'),
]