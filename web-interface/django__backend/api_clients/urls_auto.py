"""
URLs automatiques pour l'application api_clients.

Ce module utilise le système automatique de documentation Swagger
sans configuration manuelle.
"""

from django.urls import path, include
from rest_framework import permissions
from rest_framework.routers import DefaultRouter
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from . import views_auto

# Import des ViewSets complets de views_limited.py
from .views_limited import (
    NetworkClientsViewSet,
    MonitoringClientsViewSet, 
    InfrastructureClientsViewSet,
    ClientUtilsViewSet
)

# Configuration du router pour les ViewSets
router = DefaultRouter()
router.register(r'viewsets/network', NetworkClientsViewSet, basename='network-clients-viewset')
router.register(r'viewsets/monitoring', MonitoringClientsViewSet, basename='monitoring-clients-viewset')
router.register(r'viewsets/infrastructure', InfrastructureClientsViewSet, basename='infrastructure-clients-viewset')
router.register(r'viewsets/utils', ClientUtilsViewSet, basename='client-utils-viewset')

# Configuration automatique de Swagger UI
schema_view = get_schema_view(
    openapi.Info(
        title="API Clients - Documentation Automatique",
        default_version='v1',
        description="""
Documentation API automatique pour l'intégration avec différents clients réseau et services d'infrastructure.

Cette API expose automatiquement :
- **Clients Réseau** : GNS3, SNMP, NetFlow
- **Clients Monitoring** : Prometheus, Grafana, Elasticsearch, Netdata, Ntopng  
- **Clients Infrastructure** : HAProxy, Traffic Control (tc)
- **Clients Sécurité** : Fail2Ban, Suricata
- **Utilitaires** : Santé globale, configuration

La documentation est générée automatiquement par introspection des fonctions Python
sans nécessiter de configuration manuelle des schémas Swagger.
        """,
        terms_of_service="https://www.nms.local/terms/",
        contact=openapi.Contact(email="admin@nms.local"),
        license=openapi.License(name="MIT License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    # ==================== DOCUMENTATION AUTOMATIQUE ====================
    path('docs/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    path('swagger.json', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    
    # ==================== CLIENTS RÉSEAU (AUTOMATIQUE) ====================
    path('network/', views_auto.network_clients, name='network-clients'),
    path('network/gns3/projects/', views_auto.gns3_projects, name='gns3-projects'),
    path('network/gns3/projects/create/', views_auto.create_gns3_project, name='gns3-projects-create'),
    path('network/gns3/projects/<str:project_id>/', views_auto.update_gns3_project, name='gns3-projects-update'),
    path('network/gns3/projects/<str:project_id>/delete/', views_auto.delete_gns3_project, name='gns3-projects-delete'),
    path('network/snmp/query/', views_auto.snmp_query, name='snmp-query'),
    
    # ==================== CLIENTS MONITORING (AUTOMATIQUE) ====================
    path('monitoring/', views_auto.monitoring_clients, name='monitoring-clients'),
    path('monitoring/prometheus/query/', views_auto.prometheus_query, name='prometheus-query'),
    
    # ==================== CLIENTS INFRASTRUCTURE (AUTOMATIQUE) ====================
    path('infrastructure/', views_auto.infrastructure_clients, name='infrastructure-clients'),
    
    # ==================== CLIENTS SÉCURITÉ (AUTOMATIQUE) ====================
    path('security/', views_auto.security_clients, name='security-clients'),
    
    # ==================== CONFIGURATION DES CLIENTS (AUTOMATIQUE) ====================
    path('config/create/', views_auto.create_client_config, name='client-config-create'),
    path('config/<str:client_name>/', views_auto.update_client_config, name='client-config-update'),
    path('config/<str:client_name>/delete/', views_auto.delete_client_config, name='client-config-delete'),
    
    # ==================== UTILITAIRES ET SANTÉ (AUTOMATIQUE) ====================
    path('utils/health/', views_auto.global_health_check, name='global-health-check'),
    
    # ==================== VIEWSETS COMPLETS ====================
    # Intégration des ViewSets avec endpoints avancés
    path('', include(router.urls)),
]