"""
URLs pour l'API Service Central GNS3.

Ce module configure toutes les routes pour l'API REST du service central GNS3,
avec documentation Swagger automatique et versioning.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions

from .gns3_central_viewsets import GNS3CentralViewSet, GNS3EventViewSet

# Configuration du schéma Swagger/OpenAPI
schema_view = get_schema_view(
    openapi.Info(
        title="Service Central GNS3 API",
        default_version='v1',
        description="""
# API Service Central GNS3

Cette API fournit une interface REST complète pour interagir avec le service central GNS3 
du système de gestion réseau.

## Fonctionnalités principales

### 🎛️ Gestion des Nœuds
- **Démarrage/Arrêt/Redémarrage** de nœuds individuels
- **Contrôle en masse** de plusieurs nœuds
- **Surveillance du statut** en temps réel via cache Redis
- **Actions batch** pour optimiser les performances

### 🏗️ Gestion des Projets  
- **Démarrage complet** de tous les nœuds d'un projet
- **Surveillance des projets** et de leur état
- **Opérations en parallèle** pour les performances

### 🗺️ Topologie Réseau
- **Vue globale** de la topologie avec cache Redis
- **Rafraîchissement forcé** depuis le serveur GNS3
- **Filtrage avancé** par statut, type, projet
- **Données temps réel** avec mise à jour automatique

### 📡 Système d'Événements
- **Événements temps réel** via WebSocket et système de messages
- **Abonnements ciblés** par type d'événement
- **Diffusion automatique** vers tous les modules abonnés
- **Historique et statistiques** d'événements

### 🔧 Interface Modules
- **Interface simplifiée** pour les modules externes
- **Abstraction complète** de la complexité GNS3
- **Cache transparent** et gestion d'erreurs automatique
- **Abonnements aux événements** plug-and-play

## Architecture

Le service central GNS3 utilise une architecture événementielle avec :

- **Cache Redis** pour les performances et la cohérence
- **Communication inter-modules** via message bus
- **Circuit breaker** pour la résilience
- **WebSocket** pour les événements temps réel (à venir)
- **Monitoring complet** avec métriques et statistiques

## Authentification

Toutes les APIs nécessitent une authentification Django standard.
Utilisez votre token d'authentification dans l'en-tête Authorization.

## Types d'événements GNS3

| Type | Description |
|------|-------------|
| `node.started` | Nœud démarré |
| `node.stopped` | Nœud arrêté |  
| `node.suspended` | Nœud suspendu |
| `node.created` | Nouveau nœud créé |
| `node.deleted` | Nœud supprimé |
| `project.opened` | Projet ouvert |
| `project.closed` | Projet fermé |
| `topology.changed` | Changement de topologie |
| `link.created` | Nouveau lien créé |
| `link.deleted` | Lien supprimé |

## Codes de retour

- **200** : Succès
- **201** : Ressource créée
- **400** : Paramètres invalides
- **401** : Non authentifié
- **404** : Ressource non trouvée
- **500** : Erreur serveur

## Exemples d'utilisation

### Démarrer un nœud
```bash
curl -X POST "http://localhost:8000/api/gns3-central/start_node/" \\
     -H "Authorization: Bearer YOUR_TOKEN" \\
     -d "project_id=12345&node_id=67890"
```

### Obtenir la topologie
```bash
curl -X GET "http://localhost:8000/api/gns3-central/topology/" \\
     -H "Authorization: Bearer YOUR_TOKEN"
```

### Créer une interface module
```bash
curl -X POST "http://localhost:8000/api/gns3-central/create_module_interface/" \\
     -H "Authorization: Bearer YOUR_TOKEN" \\
     -H "Content-Type: application/json" \\
     -d '{"module_name": "monitoring"}'
```

## Support

Pour plus d'informations, consultez la documentation technique du projet ou 
contactez l'équipe de développement.
        """,
        terms_of_service="https://www.example.com/policies/terms/",
        contact=openapi.Contact(email="admin@networkmanagement.local"),
        license=openapi.License(name="MIT License"),
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
    patterns=[
        path('api/common/', include('common.api.urls')),
    ],
)

# Router pour les ViewSets
router = DefaultRouter()
router.register(r'gns3-central', GNS3CentralViewSet, basename='gns3-central')
router.register(r'gns3-events', GNS3EventViewSet, basename='gns3-events')

# URLs principales
urlpatterns = [
    # API ViewSets avec router DRF
    path('api/', include(router.urls)),
    
    # Documentation Swagger
    path('api/docs/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('api/redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    path('api/schema/', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    
    # Endpoints explicites pour le Service Central GNS3
    path('api/gns3-central/status/', 
         GNS3CentralViewSet.as_view({'get': 'status'}), 
         name='gns3-central-status'),
    path('api/gns3-central/start_node/', 
         GNS3CentralViewSet.as_view({'post': 'start_node'}), 
         name='gns3-central-start-node'),
    path('api/gns3-central/stop_node/', 
         GNS3CentralViewSet.as_view({'post': 'stop_node'}), 
         name='gns3-central-stop-node'),
    path('api/gns3-central/restart_node/', 
         GNS3CentralViewSet.as_view({'post': 'restart_node'}), 
         name='gns3-central-restart-node'),
    path('api/gns3-central/start_project/', 
         GNS3CentralViewSet.as_view({'post': 'start_project'}), 
         name='gns3-central-start-project'),
    path('api/gns3-central/topology/', 
         GNS3CentralViewSet.as_view({'get': 'topology'}), 
         name='gns3-central-topology'),
    path('api/gns3-central/refresh_topology/', 
         GNS3CentralViewSet.as_view({'post': 'refresh_topology'}), 
         name='gns3-central-refresh-topology'),
    path('api/gns3-central/node_status/', 
         GNS3CentralViewSet.as_view({'get': 'node_status'}), 
         name='gns3-central-node-status'),
    path('api/gns3-central/create_module_interface/', 
         GNS3CentralViewSet.as_view({'post': 'create_module_interface'}), 
         name='gns3-central-create-module-interface'),
    
    # Endpoints pour les événements GNS3
    path('api/gns3-events/stats/', 
         GNS3EventViewSet.as_view({'get': 'stats'}), 
         name='gns3-events-stats'),
    
    # Endpoints de compatibilité (quick-access)
    path('api/gns3-central/quick-status/', 
         GNS3CentralViewSet.as_view({'get': 'status'}), 
         name='gns3-quick-status'),
    path('api/gns3-central/quick-topology/', 
         GNS3CentralViewSet.as_view({'get': 'topology'}), 
         name='gns3-quick-topology'),
    path('api/gns3-events/quick-stats/', 
         GNS3EventViewSet.as_view({'get': 'stats'}), 
         name='gns3-quick-events-stats'),
]

# URLs supplémentaires pour l'intégration avec les modules existants
api_patterns = [
    # Compatibilité avec l'existant
    path('gns3/', include([
        path('status/', GNS3CentralViewSet.as_view({'get': 'status'}), name='gns3-legacy-status'),
        path('nodes/start/', GNS3CentralViewSet.as_view({'post': 'start_node'}), name='gns3-legacy-start-node'),
        path('nodes/stop/', GNS3CentralViewSet.as_view({'post': 'stop_node'}), name='gns3-legacy-stop-node'),
        path('topology/', GNS3CentralViewSet.as_view({'get': 'topology'}), name='gns3-legacy-topology'),
    ])),
    
    # Routes pour l'interface modules
    path('modules/', include([
        path('create-interface/', 
             GNS3CentralViewSet.as_view({'post': 'create_module_interface'}), 
             name='gns3-create-module-interface'),
    ])),
    
    # Routes pour les événements  
    path('events/', include([
        path('stats/', GNS3EventViewSet.as_view({'get': 'stats'}), name='gns3-events-stats'),
    ])),
]

# Ajouter les patterns API aux URLs principales
urlpatterns.extend([path('api/', include(api_patterns))])

# URLs pour les webhooks (futur développement)
webhook_patterns = [
    # Webhooks pour les intégrations externes
    # path('webhook/gns3-events/', webhook_gns3_events_view, name='webhook-gns3-events'),
    # path('webhook/topology-change/', webhook_topology_change_view, name='webhook-topology-change'),
]

# Métadonnées pour l'API
app_name = 'common_service'

# Configuration des patterns URL pour différents environnements
import os
if os.environ.get('DJANGO_DEBUG', 'False').lower() == 'true':
    # En mode debug, ajouter des endpoints de test
    from rest_framework.decorators import api_view
    from rest_framework.response import Response
    
    @api_view(['GET'])
    def api_health_check(request):
        """Endpoint de contrôle de santé pour les tests."""
        from ..infrastructure.gns3_central_service import gns3_central_service
        
        try:
            status = gns3_central_service.get_service_status()
            return Response({
                'api_healthy': True,
                'service_status': status['status'],
                'gns3_connected': status.get('gns3_server', {}).get('connected', False),
                'cache_available': status.get('cache', {}).get('network_state_cached', False)
            })
        except Exception as e:
            return Response({
                'api_healthy': False,
                'error': str(e)
            }, status=500)
    
    # Ajouter l'endpoint de health check en mode debug
    urlpatterns.append(path('api/health/', api_health_check, name='api-health-check'))

# Documentation des endpoints pour les développeurs
"""
## Résumé des endpoints disponibles

### Service Central GNS3 (/api/gns3-central/)
- GET /status/                    - État du service central
- POST /start_node/              - Démarrer un nœud  
- POST /stop_node/               - Arrêter un nœud
- POST /restart_node/            - Redémarrer un nœud
- POST /start_project/           - Démarrer un projet complet
- GET /topology/                 - Topologie complète du réseau
- POST /refresh_topology/        - Rafraîchir la topologie
- GET /node_status/              - Statut d'un nœud spécifique
- POST /create_module_interface/ - Créer une interface pour un module

### Événements GNS3 (/api/gns3-events/)  
- GET /stats/                    - Statistiques des événements

### Documentation
- /api/docs/                     - Interface Swagger interactive
- /api/redoc/                    - Documentation ReDoc
- /api/schema/                   - Schéma OpenAPI JSON

### Compatibilité legacy
- /api/gns3/status/              - Ancien endpoint de statut
- /api/gns3/nodes/start/         - Ancien endpoint de démarrage de nœud
- /api/gns3/topology/            - Ancien endpoint de topologie

### Debug (développement seulement)
- /api/health/                   - Contrôle de santé de l'API
"""