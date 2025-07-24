"""
Configuration des URLs principales - Documentation Swagger Globale Unifiée.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse

# Import de la configuration Swagger globale
from .swagger_config import schema_view

def api_root(request):
    """Vue racine de l'API avec informations sur les modules disponibles."""
    return JsonResponse({
        "message": "Network Management System (NMS) API",
        "version": "v1",
        "documentation": "https://localhost:8000/swagger/",
        "modules": {
            "monitoring": {
                "url": "/api/monitoring/",
                "description": "Surveillance système - Alertes, métriques, dashboards"
            },
            "clients": {
                "url": "/api/clients/",
                "description": "Clients externes - Réseau, monitoring, infrastructure, sécurité"
            },
            "gns3": {
                "url": "/api/gns3/",
                "description": "Intégration GNS3 - Serveurs, projets, nœuds, topologies"
            },
            "views": {
                "url": "/api/views/",
                "description": "Vues avancées - APIs métier sophistiquées"
            },
            "dashboard": {
                "url": "/api/dashboard/",
                "description": "Tableaux de bord - Widgets, préréglages, personnalisation"
            },
            "ai": {
                "url": "/api/ai/",
                "description": "Assistant IA - Chat, analyse, automation"
            },
            "reporting": {
                "url": "/api/reporting/",
                "description": "Rapports - Performance, sécurité, inventaire, analyse"
            },
            "security": {
                "url": "/api/security/",
                "description": "Sécurité - Règles, alertes, corrélation, vulnérabilités, incidents"
            },
            "qos": {
                "url": "/api/qos/",
                "description": "QoS Management - Politiques, classes de trafic, monitoring QoS"
            },
            "common": {
                "url": "/api/common/",
                "description": "Services communs - Intégration GNS3, communication inter-modules, notifications"
            }
        }
    })

urlpatterns = [
    # Interface d'administration Django
    path('admin/', admin.site.urls),
    
    # === DOCUMENTATION API SWAGGER GLOBALE ===
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    path('swagger.json/', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    
    # Vue racine de l'API
    path('api/', api_root, name='api-root'),

    # === AUTHENTIFICATION TRANSPARENTE ===
    path('api/auth/', include('nms_backend.auth_urls')),

    # === MODULES API PRINCIPAUX - TOUS RESTAURÉS ===
    
    path('api/clients/', include('api_clients.urls')),
    path('api/monitoring/', include('monitoring.urls')),  # COMPLET ET FONCTIONNEL
    path('api/gns3/', include('gns3_integration.urls')),  # RÉACTIVÉ - Problème RepresenterError corrigé
    path('api/network/', include('network_management.api.urls')),  # FINALISED AVEC VIEWSETS COMPLETS + SNMP RÉEL
    path('api/views/', include('api_views.urls')),  # MODULE RÉACTIVÉ - TOUTES ERREURS CORRIGÉES
    path('api/dashboard/', include('dashboard.urls')),
    path('api/ai/', include('ai_assistant.api.urls')),
    path('api/reporting/', include('reporting.urls')),  # MODULE REPORTING COMPLET AVEC VISUALISATIONS
    path('api/security/', include('security_management.api.urls')),  # MODULE SÉCURITÉ - COMPLET ET FONCTIONNEL
    
    # === MODULE QOS MANAGEMENT ACTIVÉ ===
    path('api/qos/', include('qos_management.urls')),
    
    # === MODULE COMMON - SERVICES D'INTÉGRATION ===
    path('api/common/', include('common.urls')),
    
    # === MODULES EN DÉVELOPPEMENT (DÉSACTIVÉS) ===
    # path('api/plugins/', include('plugins.api.urls')),
]

# Servir les fichiers statiques et media
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)