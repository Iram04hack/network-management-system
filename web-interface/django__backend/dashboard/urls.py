"""
Configuration des URLs pour le module Dashboard.

Ce fichier définit les routes URL pour accéder aux vues
et API du module Dashboard, incluant les nouvelles vues unifiées.
"""

from django.urls import path, include
from django.views.generic import TemplateView
from . import views

# Import des vues unifiées
from .views.unified_dashboard_views import (
    unified_dashboard,
    gns3_dashboard_data,
    docker_services_status,
    system_health_metrics,
    consolidated_alerts,
    modules_summary,
    refresh_dashboard_cache,
    dashboard_configuration
)

# Import des vues de gestion Docker
from .views.docker_management_views import (
    get_containers_status,
    manage_service,
    manage_service_group,
    get_service_logs,
    get_container_stats,
    get_service_actions
)

# Import du test de correction
from .test_endpoint import test_dashboard_fix

app_name = 'dashboard'

urlpatterns = [
    # Vue principale du tableau de bord
    path('', views.DashboardOverviewView.as_view(), name='index'),

    # Vues spécifiques existantes
    path('network/', views.NetworkOverviewView.as_view(), name='network_overview'),
    path('topology/<int:topology_id>/', views.IntegratedTopologyView.as_view(), name='topology'),
    path('custom/', views.CustomDashboardView.as_view(), name='custom_dashboard'),
    path('stats/', views.DashboardStatsView.as_view(), name='dashboard_stats'),
    
    # API pour les données du tableau de bord existantes
    path('api/', include('dashboard.api.urls')),
    
    # ================== NOUVELLES APIS UNIFIÉES ==================
    
    # API du dashboard unifié avec GNS3 et Docker
    path('api/unified/dashboard/', unified_dashboard, name='unified-dashboard'),
    
    # APIs spécialisées
    path('api/unified/gns3/', gns3_dashboard_data, name='gns3-dashboard-data'),
    path('api/unified/docker-services/', docker_services_status, name='docker-services-status'),
    path('api/unified/system-health/', system_health_metrics, name='system-health-metrics'),
    path('api/unified/alerts/', consolidated_alerts, name='consolidated-alerts'),
    path('api/unified/modules/', modules_summary, name='modules-summary'),
    
    # Utilitaires
    path('api/unified/refresh-cache/', refresh_dashboard_cache, name='refresh-dashboard-cache'),
    path('api/unified/config/', dashboard_configuration, name='dashboard-configuration'),
    
    # Documentation de l'API
    path('api/docs/', TemplateView.as_view(
        template_name='dashboard/api_docs.html',
        extra_context={'title': 'Documentation API Dashboard'}
    ), name='api_docs'),
    
    # ================== GESTION DOCKER ==================
    
    # Statut des conteneurs
    path('api/docker/containers/', get_containers_status, name='docker-containers-status'),
    
    # Gestion des services
    path('api/docker/service/', manage_service, name='docker-manage-service'),
    path('api/docker/group/', manage_service_group, name='docker-manage-group'),
    
    # Logs et statistiques
    path('api/docker/logs/<str:service_name>/', get_service_logs, name='docker-service-logs'),
    path('api/docker/stats/<str:service_name>/', get_container_stats, name='docker-container-stats'),
    
    # Actions disponibles
    path('api/docker/actions/<str:service_name>/', get_service_actions, name='docker-service-actions'),
    
    # TEST DE CORRECTION - Endpoint temporaire pour démontrer la correction
    path('test/fix-verification/', test_dashboard_fix, name='test-dashboard-fix'),
] 