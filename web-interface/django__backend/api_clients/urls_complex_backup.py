"""
Configuration des URLs pour l'application api_clients.

Ce module définit les points d'entrée URL pour l'application api_clients
avec toutes les fonctionnalités avancées.
"""

from django.urls import path, include
from rest_framework import permissions
from rest_framework.routers import DefaultRouter
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from . import views

# Configuration de Swagger UI
schema_view = get_schema_view(
    openapi.Info(
        title="API Clients - Documentation Automatique",
        default_version='v1',
        description="""
🤖 **Documentation générée automatiquement** pour l'intégration avec différents clients réseau et services d'infrastructure.

Cette API expose automatiquement :
- **Clients Réseau** : GNS3, SNMP, NetFlow
- **Clients Monitoring** : Prometheus, Grafana, Elasticsearch, Netdata, Ntopng  
- **Clients Infrastructure** : HAProxy, Traffic Control (tc)
- **Clients Sécurité** : Fail2Ban, Suricata
- **Utilitaires** : Santé globale, configuration

⚡ **Avantages du système automatique :**
- Documentation générée par introspection du code Python
- Pas d'erreurs manuelles dans les schémas
- Mise à jour automatique lors des modifications du code
- Cohérence garantie entre le code et la documentation
        """,
        terms_of_service="https://www.nms.local/terms/",
        contact=openapi.Contact(email="admin@nms.local"),
        license=openapi.License(name="MIT License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    # ==================== DOCUMENTATION ====================
    path('docs/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    path('swagger.json', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    
    # ==================== CLIENTS RÉSEAU ====================
    path('network/', views.network_clients, name='network-clients'),
    path('network/gns3/projects/', views.gns3_projects, name='gns3-projects'),
    path('network/gns3/projects/create/', views.create_gns3_project, name='gns3-projects-create'),
    path('network/gns3/projects/<str:project_id>/', views.update_gns3_project, name='gns3-projects-update'),
    path('network/gns3/projects/<str:project_id>/delete/', views.delete_gns3_project, name='gns3-projects-delete'),
    path('network/snmp/query/', views.snmp_query, name='snmp-query'),
    
    # ==================== CLIENTS MONITORING ====================
    path('monitoring/', views.monitoring_clients, name='monitoring-clients'),
    path('monitoring/prometheus/query/', views.prometheus_query, name='prometheus-query'),
    
    # ==================== CLIENTS INFRASTRUCTURE ====================
    path('infrastructure/', views.infrastructure_clients, name='infrastructure-clients'),
    
    # ==================== CLIENTS SÉCURITÉ ====================
    path('security/', views.security_clients, name='security-clients'),
    
    # ==================== CONFIGURATION DES CLIENTS ====================
    path('config/create/', views.create_client_config, name='client-config-create'),
    path('config/<str:client_name>/', views.update_client_config, name='client-config-update'),
    path('config/<str:client_name>/delete/', views.delete_client_config, name='client-config-delete'),
    
    # ==================== UTILITAIRES ET SANTÉ ====================
    path('utils/health/', views.global_health_check, name='global-health-check'),
    
]