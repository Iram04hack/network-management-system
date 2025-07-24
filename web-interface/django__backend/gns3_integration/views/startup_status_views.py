"""
Vues pour afficher les statuts d'allumage des projets GNS3.
"""

import logging
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.core.cache import cache
from django.utils import timezone

logger = logging.getLogger(__name__)

class StartupStatusViewSet(viewsets.ViewSet):
    """
    API pour les statuts d'allumage des projets GNS3.
    """
    
    @swagger_auto_schema(
        operation_summary="Récupère le statut d'allumage global",
        operation_description="Retourne l'état global des projets GNS3 et leurs statuts d'allumage",
        tags=['GNS3 Startup Status'],
        responses={
            200: openapi.Response(
                description="Statut d'allumage global",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'global_status': openapi.Schema(type=openapi.TYPE_STRING, description='Statut global'),
                        'active_project': openapi.Schema(type=openapi.TYPE_STRING, description='Projet actif'),
                        'projects_status': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_OBJECT), description='Statuts des projets'),
                        'last_update': openapi.Schema(type=openapi.TYPE_STRING, description='Dernière mise à jour'),
                    }
                )
            )
        }
    )
    @action(detail=False, methods=['get'])
    def global_status(self, request):
        """
        Récupère le statut d'allumage global de tous les projets.
        """
        try:
            # Récupérer les statuts depuis le cache
            global_health = cache.get('nms_global_health', {})
            active_project = cache.get('active_gns3_project', {})
            gns3_metrics = cache.get('gns3_monitoring_metrics', {})
            multi_project_metrics = cache.get('gns3_multi_project_metrics', {})
            
            # Compiler le statut global
            global_status = {
                'global_status': global_health.get('status', 'unknown'),
                'active_project': active_project.get('project_id', None),
                'active_project_name': active_project.get('project_name', 'Aucun'),
                'active_project_nodes': active_project.get('nodes_started', 0),
                'active_project_started_at': active_project.get('started_at', None),
                'server_available': gns3_metrics.get('is_available', False),
                'server_response_time': gns3_metrics.get('response_time_ms', 0),
                'projects_count': gns3_metrics.get('projects_count', 0),
                'multi_project_monitoring': multi_project_metrics.get('monitoring_enabled', False),
                'selected_projects': multi_project_metrics.get('selected_projects_count', 0),
                'projects_with_traffic': multi_project_metrics.get('projects_with_traffic', 0),
                'last_update': timezone.now().isoformat(),
                'projects_status': []
            }
            
            # Ajouter les projets sélectionnés
            selected_projects = cache.get('gns3_selected_projects', [])
            for project_data in selected_projects:
                project_status = {
                    'project_id': project_data.get('project_id', ''),
                    'project_name': project_data.get('project_name', ''),
                    'is_active': project_data.get('is_active', False),
                    'priority': project_data.get('priority', 1),
                    'traffic_detected': project_data.get('traffic_detected', False),
                    'auto_start_on_traffic': project_data.get('auto_start_on_traffic', True),
                    'selected_at': project_data.get('selected_at', None),
                    'last_traffic': project_data.get('last_traffic', None)
                }
                global_status['projects_status'].append(project_status)
            
            return Response(global_status)
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération du statut global: {e}")
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @swagger_auto_schema(
        operation_summary="Récupère le statut d'allumage d'un projet",
        operation_description="Retourne le statut détaillé d'allumage d'un projet spécifique",
        tags=['GNS3 Startup Status'],
        responses={
            200: openapi.Response(
                description="Statut d'allumage du projet",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'project_id': openapi.Schema(type=openapi.TYPE_STRING, description='ID du projet'),
                        'project_name': openapi.Schema(type=openapi.TYPE_STRING, description='Nom du projet'),
                        'startup_status': openapi.Schema(type=openapi.TYPE_STRING, description='Statut d\'allumage'),
                        'nodes_status': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_OBJECT), description='Statuts des nœuds'),
                        'operational_status': openapi.Schema(type=openapi.TYPE_OBJECT, description='Statut opérationnel'),
                        'last_startup': openapi.Schema(type=openapi.TYPE_STRING, description='Dernier allumage'),
                    }
                )
            ),
            404: "Projet non trouvé"
        }
    )
    def retrieve(self, request, pk=None):
        """
        Récupère le statut d'allumage détaillé d'un projet spécifique.
        """
        try:
            # Récupérer le projet actif
            active_project = cache.get('active_gns3_project', {})
            
            if active_project.get('project_id') != pk:
                return Response(
                    {"error": f"Projet {pk} n'est pas le projet actif"},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Récupérer les détails du projet
            project_status = {
                'project_id': pk,
                'project_name': active_project.get('project_name', 'Inconnu'),
                'startup_status': active_project.get('status', 'unknown'),
                'nodes_started': active_project.get('nodes_started', 0),
                'nodes_operational': active_project.get('nodes_operational', 0),
                'nodes_with_console': active_project.get('nodes_with_console', 0),
                'nodes_with_connectivity': active_project.get('nodes_with_connectivity', 0),
                'equipment_with_ips': active_project.get('equipment_with_ips', 0),
                'total_ips_found': active_project.get('total_ips_found', 0),
                'accessible_equipment': active_project.get('accessible_equipment', 0),
                'network_ready_for_traffic': active_project.get('network_ready_for_traffic', False),
                'operational_confirmed': active_project.get('operational_confirmed', False),
                'surveillance_configured': active_project.get('surveillance_configured', False),
                'orchestrator_triggered': active_project.get('orchestrator_triggered', False),
                'started_at': active_project.get('started_at', None),
                'workflow_id': active_project.get('workflow_id', None),
                'last_update': timezone.now().isoformat()
            }
            
            # Ajouter les détails opérationnels si disponibles
            if 'detailed_status' in active_project:
                project_status['detailed_status'] = active_project['detailed_status']
            
            return Response(project_status)
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération du statut du projet {pk}: {e}")
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @swagger_auto_schema(
        operation_summary="Déclenche l'allumage complet d'un projet",
        operation_description="Lance l'allumage complet d'un projet avec vérification opérationnelle",
        tags=['GNS3 Startup Status'],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'workflow_id': openapi.Schema(type=openapi.TYPE_STRING, description='ID du workflow'),
                'trigger_source': openapi.Schema(type=openapi.TYPE_STRING, description='Source du déclenchement'),
                'verify_operational': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Vérifier l\'état opérationnel'),
                'discover_ips': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Découvrir les IPs'),
            }
        ),
        responses={
            200: openapi.Response(
                description="Allumage lancé avec succès",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'status': openapi.Schema(type=openapi.TYPE_STRING, description='Statut de l\'opération'),
                        'message': openapi.Schema(type=openapi.TYPE_STRING, description='Message'),
                        'task_id': openapi.Schema(type=openapi.TYPE_STRING, description='ID de la tâche'),
                    }
                )
            ),
            400: "Données invalides"
        }
    )
    @action(detail=True, methods=['post'])
    def start_complete(self, request, pk=None):
        """
        Déclenche l'allumage complet d'un projet avec vérification opérationnelle.
        """
        try:
            workflow_id = request.data.get('workflow_id', f'manual-{timezone.now().timestamp()}')
            trigger_source = request.data.get('trigger_source', 'web-interface')
            verify_operational = request.data.get('verify_operational', True)
            discover_ips = request.data.get('discover_ips', True)
            
            # Importer la tâche d'allumage
            from common.tasks import start_gns3_project_complete
            
            # Lancer la tâche d'allumage
            task = start_gns3_project_complete.delay(
                project_id=pk,
                workflow_id=workflow_id,
                trigger_source=trigger_source,
                verify_operational=verify_operational,
                discover_ips=discover_ips
            )
            
            return Response({
                'status': 'success',
                'message': f'Allumage du projet {pk} lancé avec succès',
                'task_id': task.id,
                'workflow_id': workflow_id,
                'trigger_source': trigger_source
            })
            
        except Exception as e:
            logger.error(f"Erreur lors du lancement de l'allumage du projet {pk}: {e}")
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @swagger_auto_schema(
        operation_summary="Récupère le statut d'une tâche d'allumage",
        operation_description="Retourne le statut et les résultats d'une tâche d'allumage en cours",
        tags=['GNS3 Startup Status'],
        manual_parameters=[
            openapi.Parameter(
                'task_id',
                openapi.IN_QUERY,
                description="ID de la tâche à vérifier",
                type=openapi.TYPE_STRING,
                required=True
            )
        ],
        responses={
            200: openapi.Response(
                description="Statut de la tâche",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'task_id': openapi.Schema(type=openapi.TYPE_STRING, description='ID de la tâche'),
                        'status': openapi.Schema(type=openapi.TYPE_STRING, description='Statut de la tâche'),
                        'result': openapi.Schema(type=openapi.TYPE_OBJECT, description='Résultat de la tâche'),
                        'progress': openapi.Schema(type=openapi.TYPE_NUMBER, description='Pourcentage de progression'),
                    }
                )
            ),
            400: "ID de tâche manquant"
        }
    )
    @action(detail=False, methods=['get'])
    def task_status(self, request):
        """
        Récupère le statut d'une tâche d'allumage.
        """
        try:
            task_id = request.query_params.get('task_id')
            if not task_id:
                return Response(
                    {"error": "Paramètre 'task_id' requis"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Vérifier le statut de la tâche Celery
            from celery import current_app
            from celery.result import AsyncResult
            
            task_result = AsyncResult(task_id, app=current_app)
            
            task_status = {
                'task_id': task_id,
                'status': task_result.status,
                'result': None,
                'progress': 0
            }
            
            if task_result.ready():
                if task_result.successful():
                    task_status['result'] = task_result.result
                    task_status['progress'] = 100
                else:
                    task_status['result'] = {'error': str(task_result.info)}
                    task_status['progress'] = 0
            else:
                # Tâche en cours
                task_status['progress'] = 50  # Progression estimée
                task_status['result'] = {'message': 'Tâche en cours d\'exécution...'}
            
            return Response(task_status)
            
        except Exception as e:
            logger.error(f"Erreur lors de la vérification du statut de la tâche: {e}")
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )