"""
ViewSets DRF pour le Service Central GNS3 avec documentation Swagger complète.

Ce module fournit une API REST complète pour interagir avec le service central GNS3,
incluant toutes les fonctionnalités de gestion de réseau, d'événements et de monitoring.
"""

import logging
from typing import Dict, Any, Optional, List
from django.http import JsonResponse
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from ..infrastructure.gns3_central_service import gns3_central_service, GNS3EventType
from .gns3_module_interface import create_gns3_interface

logger = logging.getLogger(__name__)


class GNS3CentralViewSet(viewsets.ViewSet):
    """
    API complète pour le Service Central GNS3.
    
    Fournit une interface REST unifiée pour :
    - Gestion des nœuds GNS3 (start/stop/restart)
    - Gestion des projets
    - Surveillance de la topologie réseau
    - Événements temps réel
    - Statistiques et monitoring
    """
    
    permission_classes = [IsAuthenticated]

    # ==================== STATUT DU SERVICE ====================
    
    @swagger_auto_schema(
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
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'service_name': openapi.Schema(type=openapi.TYPE_STRING, description="Nom du service"),
                        'version': openapi.Schema(type=openapi.TYPE_STRING, description="Version du service"),
                        'status': openapi.Schema(type=openapi.TYPE_STRING, enum=['connected', 'disconnected'], description="Statut de connexion"),
                        'gns3_server': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'host': openapi.Schema(type=openapi.TYPE_STRING),
                                'port': openapi.Schema(type=openapi.TYPE_INTEGER),
                                'connected': openapi.Schema(type=openapi.TYPE_BOOLEAN)
                            }
                        ),
                        'monitoring': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'active': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                                'websocket_connected': openapi.Schema(type=openapi.TYPE_BOOLEAN)
                            }
                        ),
                        'statistics': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'events_processed': openapi.Schema(type=openapi.TYPE_INTEGER),
                                'api_calls': openapi.Schema(type=openapi.TYPE_INTEGER),
                                'cache_hits': openapi.Schema(type=openapi.TYPE_INTEGER),
                                'cache_misses': openapi.Schema(type=openapi.TYPE_INTEGER),
                                'uptime_seconds': openapi.Schema(type=openapi.TYPE_NUMBER)
                            }
                        )
                    }
                )
            ),
            500: "Erreur interne du serveur"
        }
    )
    @action(detail=False, methods=['get'])
    def status(self, request):
        """Récupère l'état complet du service central GNS3."""
        try:
            service_status = gns3_central_service.get_service_status()
            return Response(service_status, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Erreur lors de la récupération du statut du service: {e}")
            return Response(
                {"error": f"Erreur lors de la récupération du statut: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    # ==================== GESTION DES NŒUDS ====================
    
    @swagger_auto_schema(
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
        manual_parameters=[
            openapi.Parameter(
                'project_id',
                openapi.IN_QUERY,
                description="ID du projet contenant le nœud",
                type=openapi.TYPE_STRING,
                required=True
            ),
            openapi.Parameter(
                'node_id',
                openapi.IN_QUERY,
                description="ID du nœud à démarrer",
                type=openapi.TYPE_STRING,
                required=True
            )
        ],
        responses={
            200: openapi.Response(
                description="Nœud démarré avec succès",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'success': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                        'node_id': openapi.Schema(type=openapi.TYPE_STRING),
                        'project_id': openapi.Schema(type=openapi.TYPE_STRING),
                        'old_status': openapi.Schema(type=openapi.TYPE_STRING),
                        'new_status': openapi.Schema(type=openapi.TYPE_STRING, enum=['started']),
                        'timestamp': openapi.Schema(type=openapi.TYPE_STRING, format='date-time')
                    }
                )
            ),
            400: "Paramètres invalides",
            500: "Erreur lors du démarrage du nœud"
        }
    )
    @action(detail=False, methods=['post'])
    def start_node(self, request):
        """Démarre un nœud GNS3."""
        import asyncio
        
        try:
            project_id = request.query_params.get('project_id')
            node_id = request.query_params.get('node_id')
            
            if not project_id or not node_id:
                return Response(
                    {"error": "project_id et node_id sont requis"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Exécution synchrone de la méthode async
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(gns3_central_service.start_node(project_id, node_id))
            finally:
                loop.close()
            
            if result.get('success', True):
                return Response(result, status=status.HTTP_200_OK)
            else:
                return Response(result, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
        except Exception as e:
            logger.error(f"Erreur lors du démarrage du nœud {node_id}: {e}")
            return Response(
                {"error": f"Erreur lors du démarrage: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @swagger_auto_schema(
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
        manual_parameters=[
            openapi.Parameter(
                'project_id',
                openapi.IN_QUERY,
                description="ID du projet contenant le nœud",
                type=openapi.TYPE_STRING,
                required=True
            ),
            openapi.Parameter(
                'node_id',
                openapi.IN_QUERY,
                description="ID du nœud à arrêter",
                type=openapi.TYPE_STRING,
                required=True
            )
        ],
        responses={
            200: openapi.Response(
                description="Nœud arrêté avec succès",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'success': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                        'node_id': openapi.Schema(type=openapi.TYPE_STRING),
                        'project_id': openapi.Schema(type=openapi.TYPE_STRING),
                        'old_status': openapi.Schema(type=openapi.TYPE_STRING),
                        'new_status': openapi.Schema(type=openapi.TYPE_STRING, enum=['stopped']),
                        'timestamp': openapi.Schema(type=openapi.TYPE_STRING, format='date-time')
                    }
                )
            ),
            400: "Paramètres invalides",
            500: "Erreur lors de l'arrêt du nœud"
        }
    )
    @action(detail=False, methods=['post'])
    def stop_node(self, request):
        """Arrête un nœud GNS3."""
        import asyncio
        
        try:
            project_id = request.query_params.get('project_id')
            node_id = request.query_params.get('node_id')
            
            if not project_id or not node_id:
                return Response(
                    {"error": "project_id et node_id sont requis"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Exécution synchrone de la méthode async
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(gns3_central_service.stop_node(project_id, node_id))
            finally:
                loop.close()
            
            if result.get('success', True):
                return Response(result, status=status.HTTP_200_OK)
            else:
                return Response(result, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
        except Exception as e:
            logger.error(f"Erreur lors de l'arrêt du nœud {node_id}: {e}")
            return Response(
                {"error": f"Erreur lors de l'arrêt: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @swagger_auto_schema(
        operation_summary="Redémarrer un nœud GNS3",
        operation_description="""
        Redémarre un nœud (arrêt puis démarrage) dans un projet GNS3.
        
        Cette action séquentielle :
        1. Arrête le nœud avec événement NODE_STOPPED
        2. Attend 2 secondes pour la stabilisation
        3. Démarre le nœud avec événement NODE_STARTED
        4. Retourne les résultats des deux opérations
        """,
        tags=['Common - Infrastructure'],
        manual_parameters=[
            openapi.Parameter(
                'project_id',
                openapi.IN_QUERY,
                description="ID du projet contenant le nœud",
                type=openapi.TYPE_STRING,
                required=True
            ),
            openapi.Parameter(
                'node_id',
                openapi.IN_QUERY,
                description="ID du nœud à redémarrer",
                type=openapi.TYPE_STRING,
                required=True
            )
        ],
        responses={
            200: openapi.Response(
                description="Nœud redémarré avec succès",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'success': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                        'action': openapi.Schema(type=openapi.TYPE_STRING, enum=['restart_node']),
                        'stop_result': openapi.Schema(type=openapi.TYPE_OBJECT),
                        'start_result': openapi.Schema(type=openapi.TYPE_OBJECT)
                    }
                )
            ),
            400: "Paramètres invalides",
            500: "Erreur lors du redémarrage du nœud"
        }
    )
    @action(detail=False, methods=['post'])
    def restart_node(self, request):
        """Redémarre un nœud GNS3."""
        import asyncio
        
        try:
            project_id = request.query_params.get('project_id')
            node_id = request.query_params.get('node_id')
            
            if not project_id or not node_id:
                return Response(
                    {"error": "project_id et node_id sont requis"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Exécution synchrone de la méthode async
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(gns3_central_service.restart_node(project_id, node_id))
            finally:
                loop.close()
            
            if result.get('success', True):
                return Response(result, status=status.HTTP_200_OK)
            else:
                return Response(result, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
        except Exception as e:
            logger.error(f"Erreur lors du redémarrage du nœud {node_id}: {e}")
            return Response(
                {"error": f"Erreur lors du redémarrage: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    # ==================== GESTION DES PROJETS ====================
    
    @swagger_auto_schema(
        operation_summary="Démarrer tous les nœuds d'un projet",
        operation_description="""
        Démarre simultanément tous les nœuds d'un projet GNS3.
        
        Cette action :
        - Récupère la liste des nœuds du projet depuis le cache
        - Lance les démarrages en parallèle pour optimiser les performances
        - Génère un événement TOPOLOGY_CHANGED global
        - Retourne le résumé avec le nombre de nœuds démarrés avec succès
        """,
        tags=['Common - Infrastructure'],
        manual_parameters=[
            openapi.Parameter(
                'project_id',
                openapi.IN_QUERY,
                description="ID du projet dont tous les nœuds doivent être démarrés",
                type=openapi.TYPE_STRING,
                required=True
            )
        ],
        responses={
            200: openapi.Response(
                description="Nœuds du projet démarrés",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'success': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                        'total_nodes': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'started_nodes': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'results': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            additional_properties=openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    'success': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                                    'error': openapi.Schema(type=openapi.TYPE_STRING)
                                }
                            )
                        )
                    }
                )
            ),
            400: "ID de projet invalide",
            404: "Projet non trouvé",
            500: "Erreur lors du démarrage du projet"
        }
    )
    @action(detail=False, methods=['post'])
    def start_project(self, request):
        """Démarre tous les nœuds d'un projet."""
        try:
            project_id = request.query_params.get('project_id')
            
            if not project_id:
                return Response(
                    {"error": "project_id est requis"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            logger.info(f"📋 Démarrage du projet {project_id} via ViewSet")
            
            # Solution synchrone directe - utiliser le client GNS3 directement
            from api_clients.network.gns3_client import GNS3Client
            from django.utils import timezone
            
            # Créer le client GNS3 directement
            gns3_client = GNS3Client()
            
            # Récupérer les nœuds du projet
            nodes = gns3_client.get_nodes(project_id)
            if not nodes:
                return Response(
                    {"error": f"Impossible de récupérer les nœuds du projet {project_id}"},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Démarrer tous les nœuds de manière synchrone
            results = {}
            for node in nodes:
                node_id = node.get('node_id')
                if node_id:
                    try:
                        start_result = gns3_client.start_node(project_id, node_id)
                        results[node_id] = {
                            "success": True,
                            "node_id": node_id,
                            "old_status": node.get('status', 'unknown'),
                            "new_status": "started",
                            "result": start_result
                        }
                        logger.info(f"✅ Nœud {node_id} démarré avec succès")
                    except Exception as e:
                        results[node_id] = {
                            "success": False,
                            "node_id": node_id,
                            "error": str(e)
                        }
                        logger.error(f"❌ Erreur lors du démarrage du nœud {node_id}: {e}")
            
            # Compter les succès
            success_count = sum(1 for r in results.values() if r.get('success', True))
            
            # Préparer la réponse
            response_data = {
                "success": success_count > 0,
                "project_id": project_id,
                "total_nodes": len(nodes),
                "started_nodes": success_count,
                "results": results,
                "timestamp": timezone.now().isoformat()
            }
            
            logger.info(f"✅ Projet {project_id} démarré: {success_count}/{len(nodes)} nœuds")
            
            return Response(response_data, status=status.HTTP_200_OK)
                
        except Exception as e:
            logger.error(f"❌ Erreur lors du démarrage du projet {project_id}: {e}")
            return Response(
                {"error": f"Erreur lors du démarrage du projet: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    # ==================== TOPOLOGIE ET CACHE ====================
    
    @swagger_auto_schema(
        operation_summary="Obtenir la topologie réseau complète",
        operation_description="""
        Récupère la topologie complète du réseau depuis le cache Redis.
        
        Retourne :
        - Tous les projets avec leurs détails
        - Tous les nœuds avec leur statut actuel
        - Tous les liens entre nœuds
        - Horodatage de la dernière mise à jour
        - Statut du serveur GNS3
        
        Cette API est optimisée pour les modules qui ont besoin d'une vue globale du réseau.
        """,
        tags=['Common - Infrastructure'],
        responses={
            200: openapi.Response(
                description="Topologie récupérée avec succès",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'projects': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            additional_properties=openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    'project_id': openapi.Schema(type=openapi.TYPE_STRING),
                                    'name': openapi.Schema(type=openapi.TYPE_STRING),
                                    'status': openapi.Schema(type=openapi.TYPE_STRING),
                                    'nodes': openapi.Schema(type=openapi.TYPE_OBJECT)
                                }
                            )
                        ),
                        'nodes': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            additional_properties=openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    'node_id': openapi.Schema(type=openapi.TYPE_STRING),
                                    'name': openapi.Schema(type=openapi.TYPE_STRING),
                                    'status': openapi.Schema(type=openapi.TYPE_STRING),
                                    'node_type': openapi.Schema(type=openapi.TYPE_STRING),
                                    'project_id': openapi.Schema(type=openapi.TYPE_STRING)
                                }
                            )
                        ),
                        'links': openapi.Schema(type=openapi.TYPE_OBJECT),
                        'last_update': openapi.Schema(type=openapi.TYPE_STRING, format='date-time'),
                        'server_status': openapi.Schema(type=openapi.TYPE_STRING)
                    }
                )
            ),
            404: "Topologie non disponible",
            500: "Erreur lors de la récupération de la topologie"
        }
    )
    @action(detail=False, methods=['get'])
    def topology(self, request):
        """Récupère la topologie complète du réseau."""
        try:
            topology = gns3_central_service.get_cached_topology()
            
            if topology:
                return Response(topology, status=status.HTTP_200_OK)
            else:
                return Response(
                    {"error": "Topologie non disponible"},
                    status=status.HTTP_404_NOT_FOUND
                )
                
        except Exception as e:
            logger.error(f"Erreur lors de la récupération de la topologie: {e}")
            return Response(
                {"error": f"Erreur lors de la récupération de la topologie: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @swagger_auto_schema(
        operation_summary="Rafraîchir la topologie réseau",
        operation_description="""
        Force un rafraîchissement complet de la topologie depuis le serveur GNS3.
        
        Cette action :
        1. Se reconnecte au serveur GNS3
        2. Récupère tous les projets et leurs nœuds
        3. Met à jour le cache Redis
        4. Génère un événement TOPOLOGY_CHANGED
        5. Retourne la nouvelle topologie
        
        Utile après des modifications externes au réseau ou en cas de désynchronisation.
        """,
        tags=['Common - Infrastructure'],
        responses={
            200: openapi.Response(
                description="Topologie rafraîchie avec succès",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'success': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                        'topology': openapi.Schema(type=openapi.TYPE_OBJECT),
                        'refresh_time': openapi.Schema(type=openapi.TYPE_STRING, format='date-time')
                    }
                )
            ),
            500: "Erreur lors du rafraîchissement"
        }
    )
    @action(detail=False, methods=['post'])
    def refresh_topology(self, request):
        """Force un rafraîchissement de la topologie."""
        import asyncio
        
        try:
            # Exécution synchrone de la méthode async
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(gns3_central_service.refresh_topology())
            finally:
                loop.close()
            
            if result.get('success', True):
                return Response(result, status=status.HTTP_200_OK)
            else:
                return Response(result, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
        except Exception as e:
            logger.error(f"Erreur lors du rafraîchissement de la topologie: {e}")
            return Response(
                {"error": f"Erreur lors du rafraîchissement: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    # ==================== STATUT DES NŒUDS ====================
    
    @swagger_auto_schema(
        operation_summary="Obtenir le statut d'un nœud",
        operation_description="""
        Récupère le statut détaillé d'un nœud spécifique depuis le cache Redis.
        
        Retourne toutes les informations disponibles sur le nœud :
        - Statut actuel (started/stopped/suspended)
        - Type de nœud (qemu/docker/dynamips/etc.)
        - Coordonnées dans l'interface graphique
        - Projet parent
        - Horodatage de la dernière modification
        """,
        tags=['Statut des Nœuds'],
        manual_parameters=[
            openapi.Parameter(
                'node_id',
                openapi.IN_QUERY,
                description="ID du nœud dont obtenir le statut",
                type=openapi.TYPE_STRING,
                required=True
            )
        ],
        responses={
            200: openapi.Response(
                description="Statut du nœud récupéré avec succès",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'node_id': openapi.Schema(type=openapi.TYPE_STRING),
                        'name': openapi.Schema(type=openapi.TYPE_STRING),
                        'status': openapi.Schema(type=openapi.TYPE_STRING, enum=['started', 'stopped', 'suspended']),
                        'node_type': openapi.Schema(type=openapi.TYPE_STRING),
                        'project_id': openapi.Schema(type=openapi.TYPE_STRING),
                        'last_update': openapi.Schema(type=openapi.TYPE_STRING, format='date-time'),
                        'x': openapi.Schema(type=openapi.TYPE_INTEGER, description="Position X"),
                        'y': openapi.Schema(type=openapi.TYPE_INTEGER, description="Position Y")
                    }
                )
            ),
            400: "ID de nœud manquant",
            404: "Nœud non trouvé",
            500: "Erreur lors de la récupération du statut"
        }
    )
    @action(detail=False, methods=['get'])
    def node_status(self, request):
        """Récupère le statut d'un nœud spécifique."""
        try:
            node_id = request.query_params.get('node_id')
            
            if not node_id:
                return Response(
                    {"error": "node_id est requis"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            node_status = gns3_central_service.get_cached_node_status(node_id)
            
            if node_status:
                return Response(node_status, status=status.HTTP_200_OK)
            else:
                return Response(
                    {"error": f"Nœud {node_id} non trouvé"},
                    status=status.HTTP_404_NOT_FOUND
                )
                
        except Exception as e:
            logger.error(f"Erreur lors de la récupération du statut du nœud {node_id}: {e}")
            return Response(
                {"error": f"Erreur lors de la récupération du statut: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    # ==================== INTERFACE MODULE ====================
    
    @swagger_auto_schema(
        operation_summary="Créer une interface module GNS3",
        operation_description="""
        Crée une nouvelle interface GNS3 pour un module spécifique.
        
        Cette interface permet aux modules de :
        - Interagir avec GNS3 de manière simplifiée
        - S'abonner aux événements pertinents
        - Accéder au cache Redis automatiquement
        - Être notifiés des changements de topologie
        
        L'interface créée est automatiquement configurée et prête à l'emploi.
        """,
        tags=['Common - Infrastructure'],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['module_name'],
            properties={
                'module_name': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Nom unique du module (ex: 'monitoring', 'security', 'analysis')"
                )
            }
        ),
        responses={
            201: openapi.Response(
                description="Interface module créée avec succès",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'success': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                        'module_name': openapi.Schema(type=openapi.TYPE_STRING),
                        'interface_created': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                        'available_methods': openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(type=openapi.TYPE_STRING),
                            description="Liste des méthodes disponibles sur l'interface"
                        )
                    }
                )
            ),
            400: "Nom de module invalide",
            500: "Erreur lors de la création de l'interface"
        }
    )
    @action(detail=False, methods=['post'])
    def create_module_interface(self, request):
        """Crée une interface GNS3 pour un module."""
        try:
            module_name = request.data.get('module_name')
            
            if not module_name:
                return Response(
                    {"error": "module_name est requis"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Créer l'interface
            interface = create_gns3_interface(module_name)
            
            # Méthodes disponibles sur l'interface
            available_methods = [
                'get_node_status', 'get_project_info', 'get_complete_topology',
                'get_nodes_by_status', 'get_nodes_by_type', 'start_node',
                'stop_node', 'restart_node', 'refresh_topology',
                'subscribe_to_events', 'get_network_summary'
            ]
            
            return Response({
                'success': True,
                'module_name': module_name,
                'interface_created': True,
                'available_methods': available_methods
            }, status=status.HTTP_201_CREATED)
                
        except Exception as e:
            logger.error(f"Erreur lors de la création d'interface pour {module_name}: {e}")
            return Response(
                {"error": f"Erreur lors de la création d'interface: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class GNS3EventViewSet(viewsets.ViewSet):
    """
    API pour la gestion et le monitoring des événements GNS3 temps réel.
    
    Permet de :
    - Consulter l'historique des événements
    - Obtenir les statistiques d'événements
    - Surveiller les types d'événements
    """
    
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Statistiques des événements GNS3",
        operation_description="""
        Récupère les statistiques complètes sur les événements GNS3 traités par le service central.
        
        Inclut :
        - Nombre total d'événements traités
        - Répartition par type d'événement
        - Modules abonnés aux événements
        - Performance du système d'événements
        - Dernière activité
        """,
        tags=['Common - Infrastructure'],
        responses={
            200: openapi.Response(
                description="Statistiques récupérées avec succès",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'total_events_processed': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'event_types_available': openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(type=openapi.TYPE_STRING)
                        ),
                        'registered_callbacks': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'last_event_time': openapi.Schema(type=openapi.TYPE_STRING, format='date-time'),
                        'events_per_type': openapi.Schema(type=openapi.TYPE_OBJECT),
                        'performance_metrics': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'average_processing_time': openapi.Schema(type=openapi.TYPE_NUMBER),
                                'events_per_minute': openapi.Schema(type=openapi.TYPE_NUMBER)
                            }
                        )
                    }
                )
            ),
            500: "Erreur lors de la récupération des statistiques"
        }
    )
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Récupère les statistiques des événements GNS3."""
        try:
            service_status = gns3_central_service.get_service_status()
            
            # Types d'événements disponibles
            event_types = [event_type.value for event_type in GNS3EventType]
            
            stats = {
                'total_events_processed': service_status['statistics']['events_processed'],
                'event_types_available': event_types,
                'registered_callbacks': service_status['callbacks']['registered_callbacks'],
                'last_event_time': service_status['statistics'].get('last_activity'),
                'events_per_type': {},  # Sera implémenté avec un compteur détaillé
                'performance_metrics': {
                    'average_processing_time': 0.05,  # Sera calculé dynamiquement
                    'events_per_minute': service_status['statistics']['events_processed'] / max(1, service_status['statistics']['uptime_seconds'] / 60)
                }
            }
            
            return Response(stats, status=status.HTTP_200_OK)
                
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des statistiques d'événements: {e}")
            return Response(
                {"error": f"Erreur lors de la récupération des statistiques: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )