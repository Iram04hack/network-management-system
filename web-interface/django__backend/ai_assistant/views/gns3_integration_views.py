"""
Vues pour l'intégration GNS3 dans l'assistant IA.

Ces vues permettent d'exploiter les fonctionnalités d'analyse réseau
avec le contexte GNS3 directement depuis l'interface de l'assistant IA.
"""

import logging
import asyncio
from datetime import datetime
from typing import Dict, Any, List, Optional

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from ..application.ai_assistant_service import AIAssistantService
from ..infrastructure.gns3_ai_adapter import gns3_ai_adapter
from ..infrastructure.adapters import get_ai_assistant_service

logger = logging.getLogger(__name__)


@swagger_auto_schema(
    method='get',
    operation_summary="Contexte réseau GNS3 pour l'IA",
    operation_description="""
    Récupère le contexte réseau GNS3 formaté pour enrichir les réponses de l'assistant IA.
    
    Inclut :
    - Résumé de la topologie réseau
    - Analyse des dispositifs et projets
    - Statistiques d'infrastructure
    - Dispositifs actifs et types d'équipements
    """,
    responses={
        200: openapi.Response(
            description="Contexte réseau GNS3",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'topology_summary': openapi.Schema(type=openapi.TYPE_STRING),
                    'analysis_summary': openapi.Schema(type=openapi.TYPE_STRING),
                    'infrastructure_stats': openapi.Schema(type=openapi.TYPE_OBJECT),
                    'available_projects': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_STRING)),
                    'active_devices': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_STRING)),
                    'device_types': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_STRING)),
                    'gns3_server_status': openapi.Schema(type=openapi.TYPE_STRING),
                    'context_available': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                    'last_updated': openapi.Schema(type=openapi.TYPE_STRING)
                }
            )
        ),
        500: openapi.Response(description="Erreur serveur")
    },
    tags=['AI Assistant - Intégration GNS3']
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_network_context(request):
    """
    Récupère le contexte réseau GNS3 pour l'assistant IA.
    
    Fournit un contexte détaillé de l'infrastructure réseau
    pour enrichir les réponses de l'assistant IA.
    """
    try:
        # Récupérer le contexte réseau de manière asynchrone
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            network_context = loop.run_until_complete(gns3_ai_adapter.get_network_context_for_ai())
        finally:
            loop.close()
        
        return Response(network_context, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération du contexte réseau: {e}")
        return Response(
            {
                'error': 'Erreur lors de la récupération du contexte réseau',
                'message': str(e),
                'context_available': False
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@swagger_auto_schema(
    method='post',
    operation_summary="Analyser un dispositif réseau",
    operation_description="""
    Analyse un dispositif réseau spécifique avec l'IA et le contexte GNS3.
    
    L'analyse comprend :
    - Informations détaillées du dispositif
    - Analyse de performance avec l'IA
    - Recommandations d'optimisation
    - Contexte de topologie
    """,
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=['conversation_id', 'device_name'],
        properties={
            'conversation_id': openapi.Schema(type=openapi.TYPE_STRING, description="ID de la conversation"),
            'device_name': openapi.Schema(type=openapi.TYPE_STRING, description="Nom du dispositif à analyser")
        }
    ),
    responses={
        200: openapi.Response(
            description="Analyse du dispositif",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'device_info': openapi.Schema(type=openapi.TYPE_OBJECT),
                    'ai_analysis': openapi.Schema(type=openapi.TYPE_STRING),
                    'technical_details': openapi.Schema(type=openapi.TYPE_OBJECT),
                    'recommendations': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_STRING)),
                    'device_name': openapi.Schema(type=openapi.TYPE_STRING),
                    'analysis_time': openapi.Schema(type=openapi.TYPE_NUMBER)
                }
            )
        ),
        400: openapi.Response(description="Paramètres manquants"),
        404: openapi.Response(description="Dispositif non trouvé"),
        500: openapi.Response(description="Erreur serveur")
    },
    tags=['AI Assistant - Intégration GNS3']
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def analyze_device(request):
    """
    Analyse un dispositif réseau avec l'IA et le contexte GNS3.
    
    Fournit une analyse complète du dispositif incluant
    les recommandations d'optimisation générées par l'IA.
    """
    try:
        # Validation des paramètres
        conversation_id = request.data.get('conversation_id')
        device_name = request.data.get('device_name')
        
        if not conversation_id or not device_name:
            return Response(
                {'error': 'conversation_id et device_name sont requis'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Récupérer le service IA
        ai_service = get_ai_assistant_service()
        
        # Analyser le dispositif de manière asynchrone
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            analysis_result = loop.run_until_complete(
                ai_service.analyze_network_device(conversation_id, request.user.id, device_name)
            )
        finally:
            loop.close()
        
        # Vérifier si le dispositif a été trouvé
        if 'error' in analysis_result:
            if 'non trouvé' in analysis_result['error']:
                return Response(analysis_result, status=status.HTTP_404_NOT_FOUND)
            else:
                return Response(analysis_result, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response(analysis_result, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Erreur lors de l'analyse du dispositif: {e}")
        return Response(
            {
                'error': 'Erreur lors de l\'analyse du dispositif',
                'message': str(e)
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@swagger_auto_schema(
    method='post',
    operation_summary="Analyser un projet réseau",
    operation_description="""
    Analyse un projet de topologie réseau avec l'IA et le contexte GNS3.
    
    L'analyse comprend :
    - Statistiques de topologie
    - Analyse de la densité et redondance
    - Dispositifs centraux et isolés
    - Recommandations d'amélioration générées par l'IA
    """,
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=['conversation_id', 'project_name'],
        properties={
            'conversation_id': openapi.Schema(type=openapi.TYPE_STRING, description="ID de la conversation"),
            'project_name': openapi.Schema(type=openapi.TYPE_STRING, description="Nom du projet à analyser")
        }
    ),
    responses={
        200: openapi.Response(
            description="Analyse du projet",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'project_info': openapi.Schema(type=openapi.TYPE_OBJECT),
                    'ai_analysis': openapi.Schema(type=openapi.TYPE_STRING),
                    'topology_stats': openapi.Schema(type=openapi.TYPE_OBJECT),
                    'topology_analysis': openapi.Schema(type=openapi.TYPE_OBJECT),
                    'devices': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_OBJECT)),
                    'recommendations': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_STRING)),
                    'project_name': openapi.Schema(type=openapi.TYPE_STRING),
                    'analysis_time': openapi.Schema(type=openapi.TYPE_NUMBER)
                }
            )
        ),
        400: openapi.Response(description="Paramètres manquants"),
        404: openapi.Response(description="Projet non trouvé"),
        500: openapi.Response(description="Erreur serveur")
    },
    tags=['AI Assistant - Intégration GNS3']
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def analyze_project(request):
    """
    Analyse un projet de topologie réseau avec l'IA et le contexte GNS3.
    
    Fournit une analyse complète de la topologie incluant
    les recommandations d'optimisation générées par l'IA.
    """
    try:
        # Validation des paramètres
        conversation_id = request.data.get('conversation_id')
        project_name = request.data.get('project_name')
        
        if not conversation_id or not project_name:
            return Response(
                {'error': 'conversation_id et project_name sont requis'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Récupérer le service IA
        ai_service = get_ai_assistant_service()
        
        # Analyser le projet de manière asynchrone
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            analysis_result = loop.run_until_complete(
                ai_service.analyze_network_project(conversation_id, request.user.id, project_name)
            )
        finally:
            loop.close()
        
        # Vérifier si le projet a été trouvé
        if 'error' in analysis_result:
            if 'non trouvé' in analysis_result['error']:
                return Response(analysis_result, status=status.HTTP_404_NOT_FOUND)
            else:
                return Response(analysis_result, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response(analysis_result, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Erreur lors de l'analyse du projet: {e}")
        return Response(
            {
                'error': 'Erreur lors de l\'analyse du projet',
                'message': str(e)
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@swagger_auto_schema(
    method='get',
    operation_summary="Statut de l'intégration GNS3",
    operation_description="""
    Récupère le statut de l'intégration GNS3 avec l'assistant IA.
    
    Informations incluses :
    - Disponibilité du serveur GNS3
    - Dernière mise à jour du contexte
    - Fonctionnalités supportées
    - État de l'intégration
    """,
    responses={
        200: openapi.Response(
            description="Statut de l'intégration GNS3",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'gns3_available': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                    'last_update_info': openapi.Schema(type=openapi.TYPE_OBJECT),
                    'integration_enabled': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                    'supported_features': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_STRING))
                }
            )
        )
    },
    tags=['AI Assistant - Intégration GNS3']
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_integration_status(request):
    """
    Récupère le statut de l'intégration GNS3.
    
    Fournit des informations sur la disponibilité et l'état
    de l'intégration GNS3 avec l'assistant IA.
    """
    try:
        ai_service = get_ai_assistant_service()
        status_info = ai_service.get_gns3_integration_status()
        
        return Response(status_info, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération du statut d'intégration: {e}")
        return Response(
            {
                'error': 'Erreur lors de la récupération du statut',
                'message': str(e),
                'gns3_available': False,
                'integration_enabled': False
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@swagger_auto_schema(
    method='get',
    operation_summary="Liste des dispositifs réseau disponibles",
    operation_description="""
    Récupère la liste de tous les dispositifs réseau disponibles dans GNS3.
    
    Utile pour l'autocomplétion et la sélection de dispositifs
    dans l'interface de l'assistant IA.
    """,
    responses={
        200: openapi.Response(
            description="Liste des dispositifs",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'devices': openapi.Schema(
                        type=openapi.TYPE_ARRAY,
                        items=openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'name': openapi.Schema(type=openapi.TYPE_STRING),
                                'type': openapi.Schema(type=openapi.TYPE_STRING),
                                'status': openapi.Schema(type=openapi.TYPE_STRING),
                                'project': openapi.Schema(type=openapi.TYPE_STRING)
                            }
                        )
                    ),
                    'total_devices': openapi.Schema(type=openapi.TYPE_INTEGER),
                    'devices_by_type': openapi.Schema(type=openapi.TYPE_OBJECT),
                    'devices_by_status': openapi.Schema(type=openapi.TYPE_OBJECT)
                }
            )
        ),
        500: openapi.Response(description="Erreur serveur")
    },
    tags=['AI Assistant - Intégration GNS3']
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_available_devices(request):
    """
    Récupère la liste des dispositifs réseau disponibles.
    
    Fournit une liste complète des dispositifs GNS3 avec
    leurs informations de base pour l'interface utilisateur.
    """
    try:
        # Récupérer le contexte réseau de manière asynchrone
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            topology_context = loop.run_until_complete(gns3_ai_adapter.context_service.get_topology_context())
        finally:
            loop.close()
        
        # Formater les informations des dispositifs
        devices = []
        for node in topology_context.nodes:
            device_info = {
                'name': node.get('name', 'Dispositif sans nom'),
                'type': node.get('node_type', 'Type inconnu'),
                'status': node.get('status', 'Statut inconnu'),
                'project': node.get('project_name', 'Projet inconnu'),
                'project_id': node.get('project_id', ''),
                'node_id': node.get('node_id', '')
            }
            devices.append(device_info)
        
        # Calculer les statistiques
        devices_by_type = {}
        devices_by_status = {}
        
        for device in devices:
            device_type = device['type']
            device_status = device['status']
            
            devices_by_type[device_type] = devices_by_type.get(device_type, 0) + 1
            devices_by_status[device_status] = devices_by_status.get(device_status, 0) + 1
        
        result = {
            'devices': devices,
            'total_devices': len(devices),
            'devices_by_type': devices_by_type,
            'devices_by_status': devices_by_status,
            'last_updated': topology_context.last_updated.isoformat(),
            'gns3_server_status': topology_context.server_info.status.value
        }
        
        return Response(result, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des dispositifs: {e}")
        return Response(
            {
                'error': 'Erreur lors de la récupération des dispositifs',
                'message': str(e),
                'devices': [],
                'total_devices': 0
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@swagger_auto_schema(
    method='get',
    operation_summary="Liste des projets réseau disponibles",
    operation_description="""
    Récupère la liste de tous les projets réseau disponibles dans GNS3.
    
    Utile pour l'autocomplétion et la sélection de projets
    dans l'interface de l'assistant IA.
    """,
    responses={
        200: openapi.Response(
            description="Liste des projets",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'projects': openapi.Schema(
                        type=openapi.TYPE_ARRAY,
                        items=openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'name': openapi.Schema(type=openapi.TYPE_STRING),
                                'status': openapi.Schema(type=openapi.TYPE_STRING),
                                'project_id': openapi.Schema(type=openapi.TYPE_STRING),
                                'nodes_count': openapi.Schema(type=openapi.TYPE_INTEGER),
                                'links_count': openapi.Schema(type=openapi.TYPE_INTEGER)
                            }
                        )
                    ),
                    'total_projects': openapi.Schema(type=openapi.TYPE_INTEGER),
                    'projects_by_status': openapi.Schema(type=openapi.TYPE_OBJECT)
                }
            )
        ),
        500: openapi.Response(description="Erreur serveur")
    },
    tags=['AI Assistant - Intégration GNS3']
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_available_projects(request):
    """
    Récupère la liste des projets réseau disponibles.
    
    Fournit une liste complète des projets GNS3 avec
    leurs statistiques pour l'interface utilisateur.
    """
    try:
        # Récupérer le contexte réseau de manière asynchrone
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            topology_context = loop.run_until_complete(gns3_ai_adapter.context_service.get_topology_context())
        finally:
            loop.close()
        
        # Formater les informations des projets
        projects = []
        for project in topology_context.projects:
            project_id = project.get('project_id', '')
            
            # Compter les nœuds et liens du projet
            project_nodes = [n for n in topology_context.nodes if n.get('project_id') == project_id]
            project_links = [l for l in topology_context.links if l.get('project_id') == project_id]
            
            project_info = {
                'name': project.get('name', 'Projet sans nom'),
                'status': project.get('status', 'Statut inconnu'),
                'project_id': project_id,
                'nodes_count': len(project_nodes),
                'links_count': len(project_links),
                'created_at': project.get('created_at', ''),
                'updated_at': project.get('updated_at', '')
            }
            projects.append(project_info)
        
        # Calculer les statistiques
        projects_by_status = {}
        for project in projects:
            project_status = project['status']
            projects_by_status[project_status] = projects_by_status.get(project_status, 0) + 1
        
        result = {
            'projects': projects,
            'total_projects': len(projects),
            'projects_by_status': projects_by_status,
            'last_updated': topology_context.last_updated.isoformat(),
            'gns3_server_status': topology_context.server_info.status.value
        }
        
        return Response(result, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des projets: {e}")
        return Response(
            {
                'error': 'Erreur lors de la récupération des projets',
                'message': str(e),
                'projects': [],
                'total_projects': 0
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )