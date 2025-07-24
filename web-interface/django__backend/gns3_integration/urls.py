"""
Configuration des URLs pour le module GNS3 Integration avec ViewSets REST Framework.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from django.http import JsonResponse

from .views import (
    ServerViewSet,
    ProjectViewSet,
    NodeViewSet,
    LinkViewSet,
    TemplateViewSet
)
from .views.multi_project_views import MultiProjectViewSet
from .views.startup_status_views import StartupStatusViewSet
from .views.server_status_views import (
    gns3_server_status,
    gns3_health_report,
    gns3_projects_organized,
    test_gns3_notifications,
    force_gns3_detection,
    gns3_notification_status,
    toggle_gns3_notifications
)

def gns3_api_root(request):
    """Vue racine de l'API GNS3 avec informations sur les modules disponibles."""
    return JsonResponse({
        "message": "✅ Module GNS3 Integration - API REST",
        "module": "gns3_integration", 
        "status": "OK",
        "description": "Interface REST complète pour l'intégration GNS3 avec notifications Ubuntu",
        "endpoints": {
            "servers": "/api/gns3/servers/ - Gestion des serveurs GNS3",
            "projects": "/api/gns3/projects/ - Gestion des projets GNS3", 
            "multi_projects": "/api/gns3/multi-projects/ - Gestion multi-projets avec basculement automatique",
            "nodes": "/api/gns3/nodes/ - Gestion des nœuds GNS3",
            "links": "/api/gns3/links/ - Gestion des liens GNS3",
            "templates": "/api/gns3/templates/ - Gestion des templates GNS3",
            "startup_status": "/api/gns3/startup-status/ - Statut d'allumage des projets GNS3",
            "server_status": "/api/gns3/server/status/ - Statut temps réel du serveur",
            "health_report": "/api/gns3/server/health/ - Rapport de santé GNS3",
            "projects_organized": "/api/gns3/projects/organized/ - Organisation multi-projets"
        },
        "notifications": {
            "test_notifications": "/api/gns3/notifications/test/ - 🧪 Test du système de notifications",
            "force_detection": "/api/gns3/notifications/detect/ - 🔍 Forcer détection avec notification",
            "notification_status": "/api/gns3/notifications/status/ - 📊 Statut du système de notifications",
            "toggle_notifications": "/api/gns3/notifications/toggle/ - ⚙️ Activer/désactiver notifications"
        },
        "notification_features": {
            "ubuntu_integration": "Notifications natives Ubuntu via notify-send",
            "auto_detection": "Détection automatique serveur GNS3 avec notifications",
            "smart_caching": "Cache intelligent pour éviter spam de notifications",
            "detailed_info": "Informations détaillées dans les notifications (version, projets, performance)"
        }
    })

# Configuration du routeur API REST
router = DefaultRouter()

# Enregistrement des ViewSets
router.register(r'servers', ServerViewSet, basename='server')
router.register(r'projects', ProjectViewSet, basename='project')
router.register(r'multi-projects', MultiProjectViewSet, basename='multi-project')
router.register(r'startup-status', StartupStatusViewSet, basename='startup-status')
router.register(r'nodes', NodeViewSet, basename='node')
router.register(r'links', LinkViewSet, basename='link')
router.register(r'templates', TemplateViewSet, basename='template')

urlpatterns = [
    # Vue racine de l'API GNS3
    path('', gns3_api_root, name='gns3-api-root'),
    
    # API REST - routes principales
    path('', include(router.urls)),
    
    # Nouvelles vues pour le statut temps réel et l'organisation
    path('server/status/', gns3_server_status, name='gns3-server-status'),
    path('server/health/', gns3_health_report, name='gns3-health-report'),
    path('projects/organized/', gns3_projects_organized, name='gns3-projects-organized'),
    
    # Nouvelles vues pour les notifications système
    path('notifications/test/', test_gns3_notifications, name='gns3-test-notifications'),
    path('notifications/detect/', force_gns3_detection, name='gns3-force-detection'),
    path('notifications/status/', gns3_notification_status, name='gns3-notification-status'),
    path('notifications/toggle/', toggle_gns3_notifications, name='gns3-toggle-notifications'),
    
    # Compatibilité avec l'ancien endpoint de test
    path('test/', gns3_api_root, name='gns3-test'),
]