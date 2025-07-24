"""
API REST pour le Service Central GNS3 avec pattern fonction-based views.

Ce module suit le pattern existant des APIs Common qui fonctionnent.
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.utils import timezone
import asyncio
import json
import logging

from ..infrastructure.gns3_central_service import gns3_central_service
from ..infrastructure.realtime_event_system import realtime_event_manager
from ..api.gns3_module_interface import create_gns3_interface

logger = logging.getLogger(__name__)

# Schémas Swagger pour la documentation
gns3_service_status_response = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'service_name': openapi.Schema(type=openapi.TYPE_STRING),
        'version': openapi.Schema(type=openapi.TYPE_STRING),
        'status': openapi.Schema(type=openapi.TYPE_STRING, enum=['connected', 'disconnected']),
        'gns3_server': openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'host': openapi.Schema(type=openapi.TYPE_STRING),
                'port': openapi.Schema(type=openapi.TYPE_INTEGER),
                'connected': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                'version': openapi.Schema(type=openapi.TYPE_STRING),
            }
        ),
        'cache': openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'network_state_cached': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                'cache_size': openapi.Schema(type=openapi.TYPE_INTEGER),
                'last_update': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME),
            }
        ),
        'monitoring': openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'active': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                'websocket_connected': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                'events_system_running': openapi.Schema(type=openapi.TYPE_BOOLEAN),
            }
        ),
        'statistics': openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'events_processed': openapi.Schema(type=openapi.TYPE_INTEGER),
                'api_calls': openapi.Schema(type=openapi.TYPE_INTEGER),
                'cache_hits': openapi.Schema(type=openapi.TYPE_INTEGER),
                'cache_misses': openapi.Schema(type=openapi.TYPE_INTEGER),
                'uptime_seconds': openapi.Schema(type=openapi.TYPE_NUMBER),
            }
        ),
        'timestamp': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME),
    }
)

node_action_response = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'success': openapi.Schema(type=openapi.TYPE_BOOLEAN),
        'node_id': openapi.Schema(type=openapi.TYPE_STRING),
        'project_id': openapi.Schema(type=openapi.TYPE_STRING),
        'action': openapi.Schema(type=openapi.TYPE_STRING),
        'old_status': openapi.Schema(type=openapi.TYPE_STRING),
        'new_status': openapi.Schema(type=openapi.TYPE_STRING),
        'message': openapi.Schema(type=openapi.TYPE_STRING),
        'timestamp': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME),
    }
)

topology_response = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'projects': openapi.Schema(type=openapi.TYPE_OBJECT),
        'nodes': openapi.Schema(type=openapi.TYPE_OBJECT),
        'links': openapi.Schema(type=openapi.TYPE_OBJECT),
        'drawings': openapi.Schema(type=openapi.TYPE_OBJECT),
        'last_update': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME),
        'cached': openapi.Schema(type=openapi.TYPE_BOOLEAN),
        'summary': openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'total_projects': openapi.Schema(type=openapi.TYPE_INTEGER),
                'total_nodes': openapi.Schema(type=openapi.TYPE_INTEGER),
                'total_links': openapi.Schema(type=openapi.TYPE_INTEGER),
                'nodes_by_status': openapi.Schema(type=openapi.TYPE_OBJECT),
                'nodes_by_type': openapi.Schema(type=openapi.TYPE_OBJECT),
            }
        ),
    }
)

def run_async_function(async_func, *args, **kwargs):
    """
    Utilitaire pour exécuter des fonctions async dans des vues synchrones.
    """
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # Si on est déjà dans une boucle, utiliser run_until_complete
            return loop.run_until_complete(async_func(*args, **kwargs))
        else:
            # Sinon, créer une nouvelle boucle
            return asyncio.run(async_func(*args, **kwargs))
    except RuntimeError:
        # En cas d'erreur, créer une nouvelle boucle
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(async_func(*args, **kwargs))
        finally:
            loop.close()

# ==================== STATUT DU SERVICE ====================

@swagger_auto_schema(
    method='get',
    operation_summary="État du Service Central GNS3",
    operation_description="""
    Récupère l'état complet du service central GNS3 incluant :
    - Statut de connexion au serveur GNS3
    - Statistiques d'utilisation
    - État du cache Redis
    - Monitoring WebSocket
    - Performances système
    """,
    tags=['Common - Infrastructure'],
    responses={
        200: openapi.Response(
            description="État du service récupéré avec succès",
            schema=gns3_service_status_response
        ),
        500: "Erreur interne du serveur"
    }
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def gns3_central_status(request):
    """Récupère l'état complet du service central GNS3."""
    try:
        service_status = gns3_central_service.get_service_status()
        service_status['timestamp'] = timezone.now().isoformat()
        
        return Response(service_status, status=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"Erreur lors de la récupération du statut du service: {e}")
        return Response(
            {
                "error": f"Erreur lors de la récupération du statut: {str(e)}",
                "timestamp": timezone.now().isoformat()
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

# ==================== GESTION DES NŒUDS ====================

@swagger_auto_schema(
    method='post',
    operation_summary="Démarrer un nœud GNS3",
    operation_description="""
    Démarre un nœud spécifique dans un projet GNS3.
    
    Cette action :
    - Envoie la commande de démarrage au serveur GNS3
    - Met à jour le cache Redis avec le nouveau statut
    - Génère un événement NODE_STARTED pour les modules abonnés
    - Retourne le résultat de l'opération
    """,
    tags=['Common - Infrastructure'],
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'project_id': openapi.Schema(type=openapi.TYPE_STRING, description="ID du projet GNS3"),
            'node_id': openapi.Schema(type=openapi.TYPE_STRING, description="ID du nœud à démarrer"),
        },
        required=['project_id', 'node_id']
    ),
    responses={
        200: openapi.Response(
            description="Nœud démarré avec succès",
            schema=node_action_response
        ),
        400: "Paramètres invalides",
        500: "Erreur lors du démarrage du nœud"
    }
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def start_node(request):
    """Démarre un nœud GNS3."""
    try:
        # Récupération des paramètres
        project_id = request.data.get('project_id')
        node_id = request.data.get('node_id')
        
        if not project_id or not node_id:
            return Response(
                {
                    "error": "project_id et node_id sont requis",
                    "timestamp": timezone.now().isoformat()
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Exécution de l'action async
        result = run_async_function(gns3_central_service.start_node, project_id, node_id)
        
        if result.get('success', True):
            result['timestamp'] = timezone.now().isoformat()
            return Response(result, status=status.HTTP_200_OK)
        else:
            return Response(result, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
    except Exception as e:
        logger.error(f"Erreur lors du démarrage du nœud {node_id}: {e}")
        return Response(
            {
                "error": f"Erreur lors du démarrage: {str(e)}",
                "timestamp": timezone.now().isoformat()
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@swagger_auto_schema(
    method='post',
    operation_summary="Arrêter un nœud GNS3",
    operation_description="""
    Arrête un nœud spécifique dans un projet GNS3.
    
    Cette action :
    - Envoie la commande d'arrêt au serveur GNS3
    - Met à jour le cache Redis avec le nouveau statut
    - Génère un événement NODE_STOPPED pour les modules abonnés
    - Retourne le résultat de l'opération
    """,
    tags=['Common - Infrastructure'],
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'project_id': openapi.Schema(type=openapi.TYPE_STRING, description="ID du projet GNS3"),
            'node_id': openapi.Schema(type=openapi.TYPE_STRING, description="ID du nœud à arrêter"),
        },
        required=['project_id', 'node_id']
    ),
    responses={
        200: openapi.Response(
            description="Nœud arrêté avec succès",
            schema=node_action_response
        ),
        400: "Paramètres invalides",
        500: "Erreur lors de l'arrêt du nœud"
    }
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def stop_node(request):
    """Arrête un nœud GNS3."""
    try:
        # Récupération des paramètres
        project_id = request.data.get('project_id')
        node_id = request.data.get('node_id')
        
        if not project_id or not node_id:
            return Response(
                {
                    "error": "project_id et node_id sont requis",
                    "timestamp": timezone.now().isoformat()
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Exécution de l'action async
        result = run_async_function(gns3_central_service.stop_node, project_id, node_id)
        
        if result.get('success', True):
            result['timestamp'] = timezone.now().isoformat()
            return Response(result, status=status.HTTP_200_OK)
        else:
            return Response(result, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
    except Exception as e:
        logger.error(f"Erreur lors de l'arrêt du nœud {node_id}: {e}")
        return Response(
            {
                "error": f"Erreur lors de l'arrêt: {str(e)}",
                "timestamp": timezone.now().isoformat()
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@swagger_auto_schema(
    method='post',
    operation_summary="Redémarrer un nœud GNS3",
    operation_description="""
    Redémarre un nœud spécifique dans un projet GNS3.
    
    Cette action effectue un arrêt puis un redémarrage du nœud.
    """,
    tags=['Common - Infrastructure'],
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'project_id': openapi.Schema(type=openapi.TYPE_STRING, description="ID du projet GNS3"),
            'node_id': openapi.Schema(type=openapi.TYPE_STRING, description="ID du nœud à redémarrer"),
        },
        required=['project_id', 'node_id']
    ),
    responses={
        200: openapi.Response(
            description="Nœud redémarré avec succès",
            schema=node_action_response
        ),
        400: "Paramètres invalides",
        500: "Erreur lors du redémarrage du nœud"
    }
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def restart_node(request):
    """Redémarre un nœud GNS3."""
    try:
        # Récupération des paramètres
        project_id = request.data.get('project_id')
        node_id = request.data.get('node_id')
        
        if not project_id or not node_id:
            return Response(
                {
                    "error": "project_id et node_id sont requis",
                    "timestamp": timezone.now().isoformat()
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Exécution de l'action async
        result = run_async_function(gns3_central_service.restart_node, project_id, node_id)
        
        if result.get('success', True):
            result['timestamp'] = timezone.now().isoformat()
            return Response(result, status=status.HTTP_200_OK)
        else:
            return Response(result, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
    except Exception as e:
        logger.error(f"Erreur lors du redémarrage du nœud {node_id}: {e}")
        return Response(
            {
                "error": f"Erreur lors du redémarrage: {str(e)}",
                "timestamp": timezone.now().isoformat()
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

# ==================== GESTION DES PROJETS ====================

@swagger_auto_schema(
    method='post',
    operation_summary="Démarrer un projet GNS3 complet",
    operation_description="""
    Démarre tous les nœuds d'un projet GNS3 en parallèle.
    
    Cette action :
    - Démarre tous les nœuds du projet simultanément
    - Met à jour le cache pour tous les nœuds
    - Génère des événements pour chaque nœud démarré
    - Retourne un résumé des opérations
    """,
    tags=['Common - Infrastructure'],
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'project_id': openapi.Schema(type=openapi.TYPE_STRING, description="ID du projet GNS3"),
        },
        required=['project_id']
    ),
    responses={
        200: openapi.Response(
            description="Projet démarré avec succès",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'success': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                    'project_id': openapi.Schema(type=openapi.TYPE_STRING),
                    'nodes_started': openapi.Schema(type=openapi.TYPE_INTEGER),
                    'nodes_failed': openapi.Schema(type=openapi.TYPE_INTEGER),
                    'results': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_OBJECT)),
                    'timestamp': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME),
                }
            )
        ),
        400: "Paramètres invalides",
        500: "Erreur lors du démarrage du projet"
    }
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def start_project(request):
    """Démarre un projet GNS3 complet."""
    try:
        # Récupération des paramètres
        project_id = request.data.get('project_id')
        
        if not project_id:
            return Response(
                {
                    "error": "project_id est requis",
                    "timestamp": timezone.now().isoformat()
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Exécution de l'action async
        result = run_async_function(gns3_central_service.start_project, project_id)
        
        if result.get('success', True):
            result['timestamp'] = timezone.now().isoformat()
            return Response(result, status=status.HTTP_200_OK)
        else:
            return Response(result, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
    except Exception as e:
        logger.error(f"Erreur lors du démarrage du projet {project_id}: {e}")
        return Response(
            {
                "error": f"Erreur lors du démarrage du projet: {str(e)}",
                "timestamp": timezone.now().isoformat()
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

# ==================== GESTION DE LA TOPOLOGIE ====================

@swagger_auto_schema(
    method='get',
    operation_summary="Topologie complète du réseau GNS3",
    operation_description="""
    Récupère la topologie complète du réseau GNS3 avec :
    - Tous les projets et leurs détails
    - Tous les nœuds avec leur statut
    - Tous les liens entre nœuds
    - Métadonnées et résumés
    - Données mises en cache pour les performances
    """,
    tags=['Common - Infrastructure'],
    responses={
        200: openapi.Response(
            description="Topologie récupérée avec succès",
            schema=topology_response
        ),
        500: "Erreur lors de la récupération de la topologie"
    }
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_topology(request):
    """Récupère la topologie complète du réseau GNS3."""
    try:
        # Récupération de la topologie (méthode synchrone)
        topology = gns3_central_service.get_cached_topology()
        
        if topology:
            return Response(topology, status=status.HTTP_200_OK)
        else:
            return Response(
                {
                    "error": "Topologie non disponible",
                    "timestamp": timezone.now().isoformat()
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            
    except Exception as e:
        logger.error(f"Erreur lors de la récupération de la topologie: {e}")
        return Response(
            {
                "error": f"Erreur lors de la récupération de la topologie: {str(e)}",
                "timestamp": timezone.now().isoformat()
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@swagger_auto_schema(
    method='post',
    operation_summary="Rafraîchir la topologie GNS3",
    operation_description="""
    Force un rafraîchissement de la topologie depuis le serveur GNS3.
    
    Cette action :
    - Récupère les données fraîches du serveur GNS3
    - Met à jour le cache Redis
    - Génère un événement TOPOLOGY_CHANGED
    - Retourne la topologie mise à jour
    """,
    tags=['Common - Infrastructure'],
    responses={
        200: openapi.Response(
            description="Topologie rafraîchie avec succès",
            schema=topology_response
        ),
        500: "Erreur lors du rafraîchissement de la topologie"
    }
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def refresh_topology(request):
    """Rafraîchit la topologie GNS3."""
    try:
        # Exécution de l'action async
        result = run_async_function(gns3_central_service.refresh_topology)
        
        if result.get('success', True):
            return Response(result, status=status.HTTP_200_OK)
        else:
            return Response(result, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
    except Exception as e:
        logger.error(f"Erreur lors du rafraîchissement de la topologie: {e}")
        return Response(
            {
                "error": f"Erreur lors du rafraîchissement: {str(e)}",
                "timestamp": timezone.now().isoformat()
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

# ==================== INTERFACE MODULES ====================

@swagger_auto_schema(
    method='post',
    operation_summary="Créer une interface module GNS3",
    operation_description="""
    Crée une interface simplifiée pour qu'un module interagisse avec GNS3.
    
    Cette action :
    - Crée une interface GNS3ModuleInterface
    - Configure l'abonnement aux événements
    - Initialise le cache pour le module
    - Retourne les détails de l'interface
    """,
    tags=['Common - Infrastructure'],
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'module_name': openapi.Schema(type=openapi.TYPE_STRING, description="Nom du module"),
            'events': openapi.Schema(
                type=openapi.TYPE_ARRAY,
                items=openapi.Schema(type=openapi.TYPE_STRING),
                description="Types d'événements à écouter"
            ),
        },
        required=['module_name']
    ),
    responses={
        201: openapi.Response(
            description="Interface module créée avec succès",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'success': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                    'module_name': openapi.Schema(type=openapi.TYPE_STRING),
                    'interface_id': openapi.Schema(type=openapi.TYPE_STRING),
                    'subscriptions': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_STRING)),
                    'timestamp': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME),
                }
            )
        ),
        400: "Paramètres invalides",
        500: "Erreur lors de la création de l'interface"
    }
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_module_interface(request):
    """Crée une interface module GNS3."""
    try:
        # Récupération des paramètres
        module_name = request.data.get('module_name')
        events = request.data.get('events', [])
        
        if not module_name:
            return Response(
                {
                    "error": "module_name est requis",
                    "timestamp": timezone.now().isoformat()
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Création de l'interface
        interface = create_gns3_interface(module_name)
        
        # Configuration des abonnements si des événements sont spécifiés
        if events:
            interface.subscribe_to_events(events, lambda event: None)
        
        result = {
            'success': True,
            'module_name': module_name,
            'interface_id': f"gns3_interface_{module_name}",
            'subscriptions': events,
            'timestamp': timezone.now().isoformat()
        }
        
        return Response(result, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        logger.error(f"Erreur lors de la création de l'interface pour {module_name}: {e}")
        return Response(
            {
                "error": f"Erreur lors de la création de l'interface: {str(e)}",
                "timestamp": timezone.now().isoformat()
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

# ==================== ÉVÉNEMENTS ====================

@swagger_auto_schema(
    method='get',
    operation_summary="Statistiques des événements GNS3",
    operation_description="""
    Récupère les statistiques complètes du système d'événements temps réel :
    - Nombre d'événements traités
    - Connexions WebSocket actives
    - Latence moyenne
    - Répartition par type et priorité
    """,
    tags=['Common - Infrastructure'],
    responses={
        200: openapi.Response(
            description="Statistiques récupérées avec succès",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'events_published': openapi.Schema(type=openapi.TYPE_INTEGER),
                    'events_delivered': openapi.Schema(type=openapi.TYPE_INTEGER),
                    'events_failed': openapi.Schema(type=openapi.TYPE_INTEGER),
                    'connections_active': openapi.Schema(type=openapi.TYPE_INTEGER),
                    'average_latency_ms': openapi.Schema(type=openapi.TYPE_NUMBER),
                    'events_by_type': openapi.Schema(type=openapi.TYPE_OBJECT),
                    'events_by_priority': openapi.Schema(type=openapi.TYPE_OBJECT),
                    'is_running': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                    'timestamp': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME),
                }
            )
        ),
        500: "Erreur lors de la récupération des statistiques"
    }
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_events_stats(request):
    """Récupère les statistiques des événements GNS3."""
    try:
        # Récupération des statistiques
        stats = realtime_event_manager.get_statistics()
        stats['timestamp'] = timezone.now().isoformat()
        
        return Response(stats, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des statistiques: {e}")
        return Response(
            {
                "error": f"Erreur lors de la récupération des statistiques: {str(e)}",
                "timestamp": timezone.now().isoformat()
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )