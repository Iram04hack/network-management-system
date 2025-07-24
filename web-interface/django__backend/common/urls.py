"""
Configuration des URLs pour le module Common - Infrastructure Centralisée.

Ce module expose toutes les APIs de l'infrastructure centrale du NMS :
- Service Central GNS3 avec WebSocket et événements temps réel
- Communication inter-modules et workflow engine
- Découverte et monitoring des équipements
- Hub de communication centralisé
- Interface simplifiée pour l'intégration des modules

Toutes les APIs sont unifiées sous le tag 'Common - Infrastructure' dans Swagger.
"""
from django.urls import path, include
from django.http import JsonResponse

app_name = 'common'

def common_api_root(request):
    """
    Vue racine des APIs du module Common avec documentation complète.
    
    Fournit une vue d'ensemble de toutes les APIs disponibles pour le frontend.
    """
    return JsonResponse({
        "module": "Common - Infrastructure",
        "description": "Services d'infrastructure centralisés pour le NMS",
        "version": "1.0",
        "documentation": "/swagger/",
        "endpoints": {
            "gns3_central": {
                "base_url": "/api/common/api/gns3-central/",
                "description": "Service Central GNS3 avec cache Redis et événements",
                "endpoints": {
                    "status": "GET /status/ - État du service central",
                    "start_node": "POST /start_node/ - Démarrer un nœud",
                    "stop_node": "POST /stop_node/ - Arrêter un nœud",
                    "restart_node": "POST /restart_node/ - Redémarrer un nœud",
                    "start_project": "POST /start_project/ - Démarrer un projet complet",
                    "topology": "GET /topology/ - Topologie complète du réseau",
                    "refresh_topology": "POST /refresh_topology/ - Rafraîchir la topologie",
                    "node_status": "GET /node_status/ - Statut d'un nœud spécifique",
                    "create_module_interface": "POST /create_module_interface/ - Interface module"
                }
            },
            "events": {
                "base_url": "/api/common/api/gns3-events/",
                "description": "Système d'événements temps réel avec WebSocket",
                "endpoints": {
                    "stats": "GET /stats/ - Statistiques des événements",
                    "websocket": "WebSocket /ws/gns3/events/ - Événements temps réel"
                }
            },
            "integration": {
                "base_url": "/api/common/api/v1/integration/",
                "description": "Services d'intégration et communication inter-modules",
                "endpoints": {
                    "status": "GET /status/ - Statut d'intégration générale",
                    "health": "GET /health/ - Health check complet",
                    "gns3_detect": "POST /gns3/detect/ - Détection serveur GNS3",
                    "gns3_projects": "GET /gns3/projects/ - Projets GNS3 disponibles",
                    "topology": "GET /topology/ - Topologie consolidée",
                    "start_monitoring": "POST /monitoring/start/ - Démarrer monitoring",
                    "stop_monitoring": "POST /monitoring/stop/ - Arrêter monitoring",
                    "modules": "GET /modules/ - Modules intégrés",
                    "send_message": "POST /messages/send/ - Envoyer message inter-modules",
                    "message_history": "GET /messages/history/ - Historique messages",
                    "send_notification": "POST /notifications/send/ - Envoyer notification"
                }
            },
            "equipment": {
                "base_url": "/api/common/api/v1/equipment/",
                "description": "Découverte et monitoring des équipements réseau",
                "endpoints": {
                    "list_project_equipment": "GET /projects/{id}/equipment/ - Équipements du projet",
                    "equipment_details": "GET /projects/{id}/equipment/{eq_id}/ - Détails équipement",
                    "discover_project": "POST /projects/{id}/discover/ - Découverte complète projet"
                }
            },
            "snmp": {
                "base_url": "/api/common/api/v1/snmp/",
                "description": "Monitoring SNMP avec sessions persistantes",
                "endpoints": {
                    "start_monitoring": "POST /monitoring/start/ - Démarrer monitoring SNMP",
                    "list_sessions": "GET /monitoring/sessions/ - Sessions actives",
                    "get_session_data": "GET /monitoring/sessions/{id}/ - Données session",
                    "stop_session": "DELETE /monitoring/sessions/{id}/ - Arrêter session",
                    "test_connectivity": "POST /test/ - Test connectivité SNMP"
                }
            },
            "hub": {
                "base_url": "/api/common/api/v1/hub/",
                "description": "Hub de communication centralisé avec workflow engine",
                "endpoints": {
                    "status": "GET /status/ - Statut du hub",
                    "start": "POST /start/ - Démarrer le hub",
                    "stop": "POST /stop/ - Arrêter le hub",
                    "register_module": "POST /modules/register/ - Enregistrer module",
                    "send_message": "POST /messages/send/ - Envoyer message",
                    "broadcast": "POST /messages/broadcast/ - Diffuser message",
                    "list_workflows": "GET /workflows/ - Workflows disponibles",
                    "execute_workflow": "POST /workflows/execute/ - Exécuter workflow"
                }
            }
        },
        "websocket": {
            "gns3_events": {
                "url": "ws://localhost:8000/ws/gns3/events/",
                "description": "Événements GNS3 temps réel",
                "events": [
                    "node.started", "node.stopped", "node.suspended",
                    "node.created", "node.deleted", "project.opened",
                    "project.closed", "topology.changed", "link.created", "link.deleted"
                ]
            }
        },
        "features": {
            "cache_redis": "Cache Redis pour performances optimales",
            "circuit_breaker": "Circuit breaker pour résilience",
            "event_system": "Système d'événements temps réel",
            "inter_module_communication": "Communication inter-modules",
            "auto_discovery": "Auto-découverte des équipements",
            "snmp_monitoring": "Monitoring SNMP persistant",
            "workflow_engine": "Moteur de workflows",
            "health_checks": "Vérifications santé automatiques"
        }
    })

urlpatterns = [
    # Vue racine des APIs Common
    path('', common_api_root, name='common-api-root'),
    
    # === SERVICE CENTRAL GNS3 (APIs principales) ===
    path('api/', include('common.api.urls')),
    
    # === APIS D'INTÉGRATION ET COMMUNICATION ===
    path('api/v1/', include('common.api_urls_modules.api_urls', namespace='integration')),
    
    # === ENDPOINTS LEGACY POUR COMPATIBILITÉ ===
    # Redirection pour les anciennes URLs
    path('gns3/', include('common.api.urls')),
    path('integration/', include('common.api_urls_modules.api_urls', namespace='integration_legacy')),
]