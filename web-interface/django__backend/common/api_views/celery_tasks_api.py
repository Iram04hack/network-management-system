"""
API centralisée pour déclencher les tâches Celery de tous les modules.

Ce module permet de déclencher toutes les tâches Celery définies
dans les modules Django via un point d'entrée centralisé.
"""

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.utils import timezone
from celery import current_app
import logging

logger = logging.getLogger(__name__)

@swagger_auto_schema(
    method='post',
    operation_description="Déclenche une tâche Celery spécifique",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=['task_name'],
        properties={
            'task_name': openapi.Schema(
                type=openapi.TYPE_STRING,
                description="Nom de la tâche Celery à déclencher",
                enum=[
                    'common.tasks.orchestrate_system_monitoring',
                    'common.tasks.start_gns3_project_complete',
                    'gns3_integration.tasks.monitor_multi_projects_traffic',
                    'monitoring.tasks.collect_metrics',
                    'security_management.tasks.monitor_security_alerts',
                    'qos_management.tasks.collect_traffic_statistics',
                    'network_management.tasks.discover_network_devices',
                    'ai_assistant.tasks.check_ai_services_health',
                ]
            ),
            'args': openapi.Schema(
                type=openapi.TYPE_ARRAY,
                items=openapi.Schema(type=openapi.TYPE_STRING),
                description="Arguments positionnels pour la tâche"
            ),
            'kwargs': openapi.Schema(
                type=openapi.TYPE_OBJECT,
                description="Arguments nommés pour la tâche"
            ),
            'countdown': openapi.Schema(
                type=openapi.TYPE_INTEGER,
                description="Délai d'exécution en secondes"
            ),
        }
    ),
    responses={
        200: openapi.Response(
            description="Tâche déclenchée avec succès",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'task_id': openapi.Schema(type=openapi.TYPE_STRING),
                    'task_name': openapi.Schema(type=openapi.TYPE_STRING),
                    'status': openapi.Schema(type=openapi.TYPE_STRING),
                }
            )
        )
    },
    tags=['Common - Infrastructure']
)
@api_view(['POST'])
@permission_classes([])
def trigger_celery_task(request):
    """
    Déclenche une tâche Celery spécifique.
    
    Permet de déclencher n'importe quelle tâche Celery définie
    dans les modules Django du système NMS.
    """
    try:
        task_name = request.data.get('task_name')
        args = request.data.get('args', [])
        kwargs = request.data.get('kwargs', {})
        countdown = request.data.get('countdown', 0)
        
        if not task_name:
            return Response(
                {'error': 'task_name est requis'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Ajouter des métadonnées de session
        kwargs.update({
            'triggered_by': 'celery_tasks_api',
            'timestamp': timezone.now().isoformat(),
            'trigger_source': request.data.get('trigger_source', 'api_call')
        })
        
        # Déclencher la tâche Celery
        try:
            task = current_app.send_task(
                task_name,
                args=args,
                kwargs=kwargs,
                countdown=countdown
            )
            
            logger.info(f"✅ Tâche Celery déclenchée: {task_name} (ID: {task.id})")
            
            return Response({
                'task_id': task.id,
                'task_name': task_name,
                'status': 'triggered',
                'args': args,
                'kwargs': kwargs,
                'countdown': countdown,
                'timestamp': timezone.now().isoformat()
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"❌ Erreur déclenchement tâche {task_name}: {e}")
            return Response(
                {'error': f'Erreur déclenchement tâche: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            
    except Exception as e:
        return Response(
            {'error': f'Erreur traitement requête: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@swagger_auto_schema(
    method='post',
    operation_description="Déclenche les tâches de monitoring de sécurité",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'action': openapi.Schema(type=openapi.TYPE_STRING, default='start_security_monitoring'),
            'trigger_source': openapi.Schema(type=openapi.TYPE_STRING),
            'enhanced_detection': openapi.Schema(type=openapi.TYPE_BOOLEAN, default=True),
        }
    ),
    responses={
        200: openapi.Response(description="Monitoring de sécurité démarré")
    },
    tags=['Common - Infrastructure']
)
@api_view(['POST'])
@permission_classes([])
def trigger_security_monitoring(request):
    """
    Déclenche le monitoring de sécurité via les tâches Celery.
    
    Lance automatiquement monitor_security_alerts et fetch_suricata_alerts.
    """
    try:
        trigger_source = request.data.get('trigger_source', 'security_api')
        enhanced_detection = request.data.get('enhanced_detection', True)
        
        triggered_tasks = []
        
        # Déclencher monitor_security_alerts
        try:
            monitor_task = current_app.send_task(
                'security_management.tasks.monitor_security_alerts',
                kwargs={
                    'trigger_source': trigger_source,
                    'enhanced_detection': enhanced_detection,
                    'timestamp': timezone.now().isoformat()
                }
            )
            triggered_tasks.append({
                'task_id': monitor_task.id,
                'task_name': 'monitor_security_alerts'
            })
            logger.info(f"✅ Tâche monitor_security_alerts déclenchée: {monitor_task.id}")
        except Exception as e:
            logger.error(f"❌ Erreur déclenchement monitor_security_alerts: {e}")
        
        # Déclencher fetch_suricata_alerts
        try:
            suricata_task = current_app.send_task(
                'security_management.tasks.fetch_suricata_alerts',
                kwargs={
                    'trigger_source': trigger_source,
                    'timestamp': timezone.now().isoformat()
                }
            )
            triggered_tasks.append({
                'task_id': suricata_task.id,
                'task_name': 'fetch_suricata_alerts'
            })
            logger.info(f"✅ Tâche fetch_suricata_alerts déclenchée: {suricata_task.id}")
        except Exception as e:
            logger.error(f"❌ Erreur déclenchement fetch_suricata_alerts: {e}")
        
        return Response({
            'status': 'triggered',
            'action': 'start_security_monitoring',
            'triggered_tasks': triggered_tasks,
            'timestamp': timezone.now().isoformat()
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {'error': f'Erreur déclenchement monitoring sécurité: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@swagger_auto_schema(
    method='post',
    operation_description="Déclenche les tâches de monitoring réseau",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'action': openapi.Schema(type=openapi.TYPE_STRING, default='start_network_monitoring'),
            'trigger_source': openapi.Schema(type=openapi.TYPE_STRING),
            'scan_ranges': openapi.Schema(
                type=openapi.TYPE_ARRAY,
                items=openapi.Schema(type=openapi.TYPE_STRING),
                description="Plages IP à scanner"
            ),
        }
    ),
    responses={
        200: openapi.Response(description="Monitoring réseau démarré")
    },
    tags=['Common - Infrastructure']
)
@api_view(['POST'])
@permission_classes([])
def trigger_network_monitoring(request):
    """
    Déclenche le monitoring réseau via les tâches Celery.
    
    Lance automatiquement update_device_statuses et discover_network_devices.
    """
    try:
        trigger_source = request.data.get('trigger_source', 'network_api')
        scan_ranges = request.data.get('scan_ranges', None)
        
        triggered_tasks = []
        
        # Déclencher update_device_statuses
        try:
            status_task = current_app.send_task(
                'network_management.tasks.update_device_statuses',
                kwargs={
                    'trigger_source': trigger_source,
                    'timestamp': timezone.now().isoformat()
                }
            )
            triggered_tasks.append({
                'task_id': status_task.id,
                'task_name': 'update_device_statuses'
            })
            logger.info(f"✅ Tâche update_device_statuses déclenchée: {status_task.id}")
        except Exception as e:
            logger.error(f"❌ Erreur déclenchement update_device_statuses: {e}")
        
        # Déclencher discover_network_devices
        try:
            discovery_kwargs = {
                'trigger_source': trigger_source,
                'timestamp': timezone.now().isoformat()
            }
            if scan_ranges:
                discovery_kwargs['scan_ranges'] = scan_ranges
                
            discovery_task = current_app.send_task(
                'network_management.tasks.discover_network_devices',
                kwargs=discovery_kwargs
            )
            triggered_tasks.append({
                'task_id': discovery_task.id,
                'task_name': 'discover_network_devices'
            })
            logger.info(f"✅ Tâche discover_network_devices déclenchée: {discovery_task.id}")
        except Exception as e:
            logger.error(f"❌ Erreur déclenchement discover_network_devices: {e}")
        
        return Response({
            'status': 'triggered',
            'action': 'start_network_monitoring',
            'triggered_tasks': triggered_tasks,
            'scan_ranges': scan_ranges,
            'timestamp': timezone.now().isoformat()
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {'error': f'Erreur déclenchement monitoring réseau: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@swagger_auto_schema(
    method='get',
    operation_description="Liste toutes les tâches Celery disponibles",
    responses={
        200: openapi.Response(
            description="Liste des tâches Celery disponibles",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'available_tasks': openapi.Schema(
                        type=openapi.TYPE_ARRAY,
                        items=openapi.Schema(type=openapi.TYPE_STRING)
                    ),
                }
            )
        )
    },
    tags=['Common - Infrastructure']
)
@api_view(['GET'])
@permission_classes([])
def list_available_tasks(request):
    """
    Liste toutes les tâches Celery disponibles dans le système.
    """
    try:
        # Récupérer toutes les tâches enregistrées
        available_tasks = list(current_app.tasks.keys())
        
        # Filtrer les tâches du système NMS
        nms_tasks = [
            task for task in available_tasks 
            if any(module in task for module in [
                'common.tasks',
                'gns3_integration.tasks',
                'monitoring.tasks',
                'security_management.tasks',
                'qos_management.tasks',
                'network_management.tasks',
                'ai_assistant.tasks',
                'reporting.tasks'
            ])
        ]
        
        return Response({
            'available_tasks': sorted(nms_tasks),
            'total_count': len(nms_tasks),
            'timestamp': timezone.now().isoformat()
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {'error': f'Erreur récupération tâches: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )