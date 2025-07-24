"""
Vues pour la gestion des conteneurs Docker depuis le dashboard.

Ces vues permettent de contrôler les services Docker du NMS
directement depuis l'interface web dashboard.
"""

import logging
import asyncio
from datetime import datetime
from typing import Dict, Any, List

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework import status

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from ..infrastructure.docker_management_service import (
    docker_management_service,
    ContainerAction,
    ServiceGroup
)

logger = logging.getLogger(__name__)


@swagger_auto_schema(
    method='get',
    operation_summary="Statut des conteneurs Docker",
    operation_description="""
    Récupère le statut de tous les conteneurs Docker du NMS organisés par groupes :
    - Base : PostgreSQL, Redis, Django, Celery
    - Security : Suricata, Elasticsearch, Kibana, Fail2ban
    - Monitoring : Netdata, ntopng, HAProxy, Prometheus, Grafana
    - Traffic : Traffic Control (QoS)
    
    Inclut les métriques globales et le statut des services critiques.
    """,
    responses={
        200: openapi.Response(
            description="Statut des conteneurs par groupe",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'base': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_OBJECT)),
                    'security': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_OBJECT)),
                    'monitoring': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_OBJECT)),
                    'traffic': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_OBJECT)),
                    'global_metrics': openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'total_containers': openapi.Schema(type=openapi.TYPE_INTEGER),
                            'running_containers': openapi.Schema(type=openapi.TYPE_INTEGER),
                            'stopped_containers': openapi.Schema(type=openapi.TYPE_INTEGER),
                            'availability_percentage': openapi.Schema(type=openapi.TYPE_NUMBER),
                            'critical_services_status': openapi.Schema(type=openapi.TYPE_OBJECT)
                        }
                    ),
                    'last_updated': openapi.Schema(type=openapi.TYPE_STRING)
                }
            )
        ),
        500: openapi.Response(description="Erreur serveur")
    },
    tags=['Dashboard - Gestion Docker']
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_containers_status(request):
    """
    Récupère le statut de tous les conteneurs Docker.
    
    Organise les conteneurs par groupes fonctionnels et fournit
    des métriques globales de disponibilité.
    """
    try:
        # Récupérer le statut de manière asynchrone
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            containers_status = loop.run_until_complete(docker_management_service.get_containers_status())
        finally:
            loop.close()
        
        return Response(containers_status, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération du statut des conteneurs: {e}")
        return Response(
            {
                'error': 'Erreur lors de la récupération du statut des conteneurs',
                'message': str(e)
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@swagger_auto_schema(
    method='post',
    operation_summary="Gérer un service Docker",
    operation_description="""
    Exécute une action sur un service Docker spécifique.
    
    Actions disponibles :
    - start : Démarrer le service
    - stop : Arrêter le service
    - restart : Redémarrer le service
    - pause : Mettre en pause le conteneur
    - unpause : Reprendre le conteneur
    - remove : Supprimer le conteneur (services non-critiques seulement)
    
    Les services critiques (postgres, redis, django) ont des actions limitées pour la sécurité.
    """,
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=['service_name', 'action'],
        properties={
            'service_name': openapi.Schema(
                type=openapi.TYPE_STRING,
                description="Nom du service (ex: postgres, django, elasticsearch)"
            ),
            'action': openapi.Schema(
                type=openapi.TYPE_STRING,
                enum=['start', 'stop', 'restart', 'pause', 'unpause', 'remove'],
                description="Action à effectuer"
            )
        }
    ),
    responses={
        200: openapi.Response(
            description="Résultat de l'opération",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'service_name': openapi.Schema(type=openapi.TYPE_STRING),
                    'action': openapi.Schema(type=openapi.TYPE_STRING),
                    'success': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                    'message': openapi.Schema(type=openapi.TYPE_STRING),
                    'execution_time': openapi.Schema(type=openapi.TYPE_NUMBER),
                    'details': openapi.Schema(type=openapi.TYPE_OBJECT)
                }
            )
        ),
        400: openapi.Response(description="Paramètres invalides"),
        403: openapi.Response(description="Action non autorisée"),
        500: openapi.Response(description="Erreur serveur")
    },
    tags=['Dashboard - Gestion Docker']
)
@api_view(['POST'])
@permission_classes([IsAdminUser])  # Seuls les admins peuvent gérer les services
def manage_service(request):
    """
    Gère un service Docker spécifique.
    
    Exécute une action sur un service avec validation des permissions
    et protection des services critiques.
    """
    try:
        # Validation des paramètres
        service_name = request.data.get('service_name')
        action_str = request.data.get('action')
        
        if not service_name or not action_str:
            return Response(
                {'error': 'service_name et action sont requis'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Valider l'action
        try:
            action = ContainerAction(action_str)
        except ValueError:
            return Response(
                {'error': f'Action invalide: {action_str}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Vérifier les actions disponibles pour ce service
        available_actions = docker_management_service.get_available_actions(service_name)
        if action_str not in available_actions:
            return Response(
                {
                    'error': f'Action {action_str} non autorisée pour le service {service_name}',
                    'available_actions': available_actions
                },
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Exécuter l'action de manière asynchrone
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            operation_result = loop.run_until_complete(
                docker_management_service.manage_service(service_name, action)
            )
        finally:
            loop.close()
        
        # Convertir le résultat en dictionnaire
        result = {
            'service_name': operation_result.service_name,
            'action': operation_result.action,
            'success': operation_result.success,
            'message': operation_result.message,
            'execution_time': operation_result.execution_time,
            'details': operation_result.details,
            'timestamp': datetime.now().isoformat()
        }
        
        # Log de l'action
        if operation_result.success:
            logger.info(f"Action {action_str} réussie sur {service_name} par {request.user.username}")
        else:
            logger.warning(f"Action {action_str} échouée sur {service_name} par {request.user.username}: {operation_result.message}")
        
        return Response(result, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Erreur lors de la gestion du service: {e}")
        return Response(
            {
                'error': 'Erreur lors de la gestion du service',
                'message': str(e)
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@swagger_auto_schema(
    method='post',
    operation_summary="Gérer un groupe de services",
    operation_description="""
    Exécute une action sur un groupe de services Docker.
    
    Groupes disponibles :
    - base : Services de base (PostgreSQL, Redis, Django, Celery)
    - security : Services de sécurité (Suricata, Elasticsearch, Kibana, Fail2ban)
    - monitoring : Services de monitoring (Netdata, ntopng, HAProxy, Prometheus, Grafana)
    - traffic : Services de trafic (Traffic Control QoS)
    - all : Tous les services
    
    L'opération est exécutée en parallèle sur tous les services du groupe.
    """,
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=['group', 'action'],
        properties={
            'group': openapi.Schema(
                type=openapi.TYPE_STRING,
                enum=['base', 'security', 'monitoring', 'traffic', 'all'],
                description="Groupe de services"
            ),
            'action': openapi.Schema(
                type=openapi.TYPE_STRING,
                enum=['start', 'stop', 'restart'],
                description="Action à effectuer"
            )
        }
    ),
    responses={
        200: openapi.Response(
            description="Résultats des opérations",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'group': openapi.Schema(type=openapi.TYPE_STRING),
                    'action': openapi.Schema(type=openapi.TYPE_STRING),
                    'operations': openapi.Schema(
                        type=openapi.TYPE_ARRAY,
                        items=openapi.Schema(type=openapi.TYPE_OBJECT)
                    ),
                    'summary': openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'total': openapi.Schema(type=openapi.TYPE_INTEGER),
                            'successful': openapi.Schema(type=openapi.TYPE_INTEGER),
                            'failed': openapi.Schema(type=openapi.TYPE_INTEGER)
                        }
                    )
                }
            )
        ),
        400: openapi.Response(description="Paramètres invalides"),
        403: openapi.Response(description="Action non autorisée"),
        500: openapi.Response(description="Erreur serveur")
    },
    tags=['Dashboard - Gestion Docker']
)
@api_view(['POST'])
@permission_classes([IsAdminUser])
def manage_service_group(request):
    """
    Gère un groupe de services Docker.
    
    Exécute une action sur tous les services d'un groupe
    en parallèle et retourne un résumé des résultats.
    """
    try:
        # Validation des paramètres
        group_str = request.data.get('group')
        action_str = request.data.get('action')
        
        if not group_str or not action_str:
            return Response(
                {'error': 'group et action sont requis'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Valider le groupe
        try:
            group = ServiceGroup(group_str)
        except ValueError:
            return Response(
                {'error': f'Groupe invalide: {group_str}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Valider l'action (limitée pour les groupes)
        allowed_group_actions = ['start', 'stop', 'restart']
        if action_str not in allowed_group_actions:
            return Response(
                {'error': f'Action {action_str} non autorisée pour les groupes'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            action = ContainerAction(action_str)
        except ValueError:
            return Response(
                {'error': f'Action invalide: {action_str}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Exécuter l'action de manière asynchrone
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            operations = loop.run_until_complete(
                docker_management_service.manage_service_group(group, action)
            )
        finally:
            loop.close()
        
        # Calculer le résumé
        total = len(operations)
        successful = sum(1 for op in operations if op.success)
        failed = total - successful
        
        # Convertir les résultats
        results = []
        for op in operations:
            results.append({
                'service_name': op.service_name,
                'action': op.action,
                'success': op.success,
                'message': op.message,
                'execution_time': op.execution_time
            })
        
        result = {
            'group': group_str,
            'action': action_str,
            'operations': results,
            'summary': {
                'total': total,
                'successful': successful,
                'failed': failed,
                'success_rate': round((successful / total) * 100, 2) if total > 0 else 0
            },
            'timestamp': datetime.now().isoformat()
        }
        
        # Log de l'action
        logger.info(f"Action {action_str} sur groupe {group_str} par {request.user.username}: {successful}/{total} réussies")
        
        return Response(result, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Erreur lors de la gestion du groupe de services: {e}")
        return Response(
            {
                'error': 'Erreur lors de la gestion du groupe de services',
                'message': str(e)
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@swagger_auto_schema(
    method='get',
    operation_summary="Logs d'un service Docker",
    operation_description="""
    Récupère les logs d'un service Docker spécifique.
    
    Permet de récupérer les dernières lignes de logs pour diagnostiquer
    les problèmes ou surveiller l'activité d'un service.
    """,
    manual_parameters=[
        openapi.Parameter(
            'service_name',
            openapi.IN_PATH,
            description="Nom du service",
            type=openapi.TYPE_STRING,
            required=True
        ),
        openapi.Parameter(
            'lines',
            openapi.IN_QUERY,
            description="Nombre de lignes à récupérer (défaut: 100)",
            type=openapi.TYPE_INTEGER,
            required=False
        )
    ],
    responses={
        200: openapi.Response(
            description="Logs du service",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'success': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                    'service': openapi.Schema(type=openapi.TYPE_STRING),
                    'logs': openapi.Schema(type=openapi.TYPE_STRING),
                    'lines_requested': openapi.Schema(type=openapi.TYPE_INTEGER),
                    'timestamp': openapi.Schema(type=openapi.TYPE_STRING)
                }
            )
        ),
        400: openapi.Response(description="Paramètres invalides"),
        404: openapi.Response(description="Service non trouvé"),
        500: openapi.Response(description="Erreur serveur")
    },
    tags=['Dashboard - Gestion Docker']
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_service_logs(request, service_name):
    """
    Récupère les logs d'un service Docker.
    
    Fournit les logs récents d'un service pour le diagnostic
    et la surveillance.
    """
    try:
        # Paramètres optionnels
        lines = int(request.GET.get('lines', 100))
        
        # Valider le nombre de lignes
        if lines < 1 or lines > 1000:
            return Response(
                {'error': 'Le nombre de lignes doit être entre 1 et 1000'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Récupérer les logs de manière asynchrone
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            logs_result = loop.run_until_complete(
                docker_management_service.get_service_logs(service_name, lines)
            )
        finally:
            loop.close()
        
        if logs_result['success']:
            return Response(logs_result, status=status.HTTP_200_OK)
        else:
            return Response(logs_result, status=status.HTTP_404_NOT_FOUND)
        
    except ValueError:
        return Response(
            {'error': 'Le paramètre lines doit être un entier'},
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des logs de {service_name}: {e}")
        return Response(
            {
                'error': 'Erreur lors de la récupération des logs',
                'message': str(e)
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@swagger_auto_schema(
    method='get',
    operation_summary="Statistiques d'un conteneur",
    operation_description="""
    Récupère les statistiques de performance d'un conteneur Docker.
    
    Inclut les métriques CPU, mémoire, réseau et disque en temps réel.
    """,
    manual_parameters=[
        openapi.Parameter(
            'service_name',
            openapi.IN_PATH,
            description="Nom du service",
            type=openapi.TYPE_STRING,
            required=True
        )
    ],
    responses={
        200: openapi.Response(
            description="Statistiques du conteneur",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'success': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                    'service': openapi.Schema(type=openapi.TYPE_STRING),
                    'stats': openapi.Schema(type=openapi.TYPE_OBJECT),
                    'timestamp': openapi.Schema(type=openapi.TYPE_STRING)
                }
            )
        ),
        404: openapi.Response(description="Service non trouvé"),
        500: openapi.Response(description="Erreur serveur")
    },
    tags=['Dashboard - Gestion Docker']
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_container_stats(request, service_name):
    """
    Récupère les statistiques d'un conteneur Docker.
    
    Fournit les métriques de performance en temps réel
    pour surveiller l'utilisation des ressources.
    """
    try:
        # Récupérer les stats de manière asynchrone
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            stats_result = loop.run_until_complete(
                docker_management_service.get_container_stats(service_name)
            )
        finally:
            loop.close()
        
        if stats_result['success']:
            return Response(stats_result, status=status.HTTP_200_OK)
        else:
            return Response(stats_result, status=status.HTTP_404_NOT_FOUND)
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des stats de {service_name}: {e}")
        return Response(
            {
                'error': 'Erreur lors de la récupération des statistiques',
                'message': str(e)
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@swagger_auto_schema(
    method='get',
    operation_summary="Actions disponibles pour un service",
    operation_description="""
    Récupère la liste des actions disponibles pour un service spécifique.
    
    Les services critiques (postgres, redis, django) ont des actions limitées
    pour éviter les arrêts accidentels du système.
    """,
    manual_parameters=[
        openapi.Parameter(
            'service_name',
            openapi.IN_PATH,
            description="Nom du service",
            type=openapi.TYPE_STRING,
            required=True
        )
    ],
    responses={
        200: openapi.Response(
            description="Actions disponibles",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'service_name': openapi.Schema(type=openapi.TYPE_STRING),
                    'available_actions': openapi.Schema(
                        type=openapi.TYPE_ARRAY,
                        items=openapi.Schema(type=openapi.TYPE_STRING)
                    ),
                    'is_critical': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                    'description': openapi.Schema(type=openapi.TYPE_STRING)
                }
            )
        )
    },
    tags=['Dashboard - Gestion Docker']
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_service_actions(request, service_name):
    """
    Récupère les actions disponibles pour un service.
    
    Retourne la liste des actions autorisées en fonction
    du type de service (critique ou non).
    """
    try:
        available_actions = docker_management_service.get_available_actions(service_name)
        is_critical = service_name in docker_management_service.critical_services
        
        result = {
            'service_name': service_name,
            'available_actions': available_actions,
            'is_critical': is_critical,
            'description': f"Service {'critique' if is_critical else 'standard'} du NMS",
            'port': docker_management_service.service_ports.get(service_name, 'N/A')
        }
        
        return Response(result, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des actions de {service_name}: {e}")
        return Response(
            {
                'error': 'Erreur lors de la récupération des actions',
                'message': str(e)
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )