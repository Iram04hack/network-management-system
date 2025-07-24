"""
API pour contrôler le hub de communication centralisé.
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.utils import timezone

from ..infrastructure.centralized_communication_hub import communication_hub, Priority, MessageType, CommunicationMessage

@swagger_auto_schema(
    method='get',
    operation_description="Récupère le statut du hub de communication",
    responses={
        200: openapi.Response(
            description="Statut du hub de communication",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'hub_status': openapi.Schema(type=openapi.TYPE_STRING),
                    'registered_modules': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_STRING)),
                    'queue_sizes': openapi.Schema(type=openapi.TYPE_OBJECT),
                    'statistics': openapi.Schema(type=openapi.TYPE_OBJECT),
                    'available_workflows': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_STRING)),
                    'module_health': openapi.Schema(type=openapi.TYPE_OBJECT),
                }
            )
        )
    },
    tags=['Common - Infrastructure']
)
@api_view(['GET'])
@permission_classes([])
def get_hub_status(request):
    """
    Récupère le statut complet du hub de communication.
    
    Retourne les informations sur les modules, files d'attente et statistiques.
    """
    try:
        hub_status = communication_hub.get_status()
        return Response(hub_status, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {'error': f'Erreur lors de la récupération du statut: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@swagger_auto_schema(
    method='post',
    operation_description="Démarre le hub de communication",
    responses={
        200: openapi.Response(description="Hub démarré"),
        400: openapi.Response(description="Hub déjà en fonctionnement")
    },
    tags=['Common - Infrastructure']
)
@api_view(['POST'])
@permission_classes([])
def start_hub(request):
    """
    Démarre le hub de communication centralisé.
    
    Lance le traitement des messages et l'orchestration inter-modules.
    """
    try:
        if communication_hub.is_running:
            return Response(
                {'message': 'Le hub de communication est déjà en fonctionnement'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        communication_hub.start()
        
        return Response({
            'message': 'Hub de communication démarré',
            'timestamp': timezone.now().isoformat()
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {'error': f'Erreur lors du démarrage du hub: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@swagger_auto_schema(
    method='post',
    operation_description="Arrête le hub de communication",
    responses={
        200: openapi.Response(description="Hub arrêté")
    },
    tags=['Common - Infrastructure']
)
@api_view(['POST'])
@permission_classes([])
def stop_hub(request):
    """
    Arrête le hub de communication centralisé.
    
    Termine le traitement des messages en cours et arrête l'orchestration.
    """
    try:
        communication_hub.stop()
        
        return Response({
            'message': 'Hub de communication arrêté',
            'timestamp': timezone.now().isoformat()
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {'error': f'Erreur lors de l\'arrêt du hub: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@swagger_auto_schema(
    method='post',
    operation_description="Enregistre un module dans le hub",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=['module_name', 'capabilities'],
        properties={
            'module_name': openapi.Schema(type=openapi.TYPE_STRING),
            'capabilities': openapi.Schema(
                type=openapi.TYPE_ARRAY,
                items=openapi.Schema(type=openapi.TYPE_STRING),
                description="Capacités du module"
            ),
        }
    ),
    responses={
        200: openapi.Response(description="Module enregistré")
    },
    tags=['Common - Infrastructure']
)
@api_view(['POST'])
@permission_classes([])
def register_module(request):
    """
    Enregistre un module dans le hub de communication.
    
    Permet à un module de s'enregistrer avec ses capacités.
    """
    try:
        module_name = request.data.get('module_name')
        capabilities = request.data.get('capabilities', [])
        
        if not module_name:
            return Response(
                {'error': 'module_name est requis'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        communication_hub.register_module(module_name, capabilities)
        
        return Response({
            'message': f'Module {module_name} enregistré',
            'capabilities': capabilities,
            'timestamp': timezone.now().isoformat()
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {'error': f'Erreur lors de l\'enregistrement du module: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@swagger_auto_schema(
    method='post',
    operation_description="Envoie un message via le hub",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=['sender', 'message_type', 'data'],
        properties={
            'sender': openapi.Schema(type=openapi.TYPE_STRING),
            'target': openapi.Schema(type=openapi.TYPE_STRING, description="Module cible (optionnel pour diffusion)"),
            'message_type': openapi.Schema(
                type=openapi.TYPE_STRING,
                enum=['topology_update', 'node_status_change', 'network_event', 'security_alert', 'monitoring_data', 'qos_policy_update', 'configuration_change', 'service_discovery', 'health_check', 'notification']
            ),
            'data': openapi.Schema(type=openapi.TYPE_OBJECT),
            'priority': openapi.Schema(
                type=openapi.TYPE_STRING,
                enum=['low', 'normal', 'high', 'critical'],
                default='normal'
            ),
            'timeout_seconds': openapi.Schema(type=openapi.TYPE_INTEGER, default=30),
        }
    ),
    responses={
        200: openapi.Response(
            description="Message envoyé",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'message_id': openapi.Schema(type=openapi.TYPE_STRING),
                    'status': openapi.Schema(type=openapi.TYPE_STRING),
                }
            )
        )
    },
    tags=['Common - Infrastructure']
)
@api_view(['POST'])
@permission_classes([])
def send_message(request):
    """
    Envoie un message via le hub de communication.
    
    Permet d'envoyer un message à un module spécifique ou en diffusion.
    """
    try:
        sender = request.data.get('sender')
        target = request.data.get('target')
        message_type_str = request.data.get('message_type')
        data = request.data.get('data', {})
        priority_str = request.data.get('priority', 'normal')
        timeout_seconds = request.data.get('timeout_seconds', 30)
        
        if not sender or not message_type_str:
            return Response(
                {'error': 'sender et message_type sont requis'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # Convertir les enums
        try:
            message_type = MessageType(message_type_str)
        except ValueError:
            return Response(
                {'error': f'Type de message invalide: {message_type_str}'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        try:
            priority = Priority(priority_str)
        except ValueError:
            return Response(
                {'error': f'Priorité invalide: {priority_str}'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # Créer le message
        message = CommunicationMessage(
            sender=sender,
            target=target,
            message_type=message_type,
            data=data,
            priority=priority,
            timeout_seconds=timeout_seconds
        )
        
        # Envoyer via le hub
        message_id = communication_hub.send_message(message)
        
        return Response({
            'message_id': message_id,
            'status': 'queued',
            'priority': priority_str,
            'target': target or 'broadcast',
            'timestamp': timezone.now().isoformat()
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {'error': f'Erreur lors de l\'envoi du message: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@swagger_auto_schema(
    method='post',
    operation_description="Diffuse un message à plusieurs modules",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=['sender', 'message_type', 'data'],
        properties={
            'sender': openapi.Schema(type=openapi.TYPE_STRING),
            'message_type': openapi.Schema(type=openapi.TYPE_STRING),
            'data': openapi.Schema(type=openapi.TYPE_OBJECT),
            'capability_filter': openapi.Schema(type=openapi.TYPE_STRING, description="Filtrer par capacité"),
        }
    ),
    responses={
        200: openapi.Response(
            description="Message diffusé",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'message_ids': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_STRING)),
                    'target_count': openapi.Schema(type=openapi.TYPE_INTEGER),
                }
            )
        )
    },
    tags=['Common - Infrastructure']
)
@api_view(['POST'])
@permission_classes([])
def broadcast_message(request):
    """
    Diffuse un message à plusieurs modules.
    
    Envoie un message à tous les modules ou ceux ayant une capacité spécifique.
    """
    try:
        sender = request.data.get('sender')
        message_type_str = request.data.get('message_type')
        data = request.data.get('data', {})
        capability_filter = request.data.get('capability_filter')
        
        if not sender or not message_type_str:
            return Response(
                {'error': 'sender et message_type sont requis'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        try:
            message_type = MessageType(message_type_str)
        except ValueError:
            return Response(
                {'error': f'Type de message invalide: {message_type_str}'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # Diffuser le message
        message_ids = communication_hub.broadcast_message(
            sender, message_type, data, capability_filter
        )
        
        return Response({
            'message_ids': message_ids,
            'target_count': len(message_ids),
            'capability_filter': capability_filter,
            'timestamp': timezone.now().isoformat()
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {'error': f'Erreur lors de la diffusion: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@swagger_auto_schema(
    method='post',
    operation_description="Exécute un workflow prédéfini",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=['workflow_name'],
        properties={
            'workflow_name': openapi.Schema(
                type=openapi.TYPE_STRING,
                enum=['equipment_discovery', 'incident_response', 'topology_update', 'security_testing_full_workflow']
            ),
            'initial_data': openapi.Schema(type=openapi.TYPE_OBJECT, default={}),
        }
    ),
    responses={
        200: openapi.Response(
            description="Workflow démarré",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'workflow_id': openapi.Schema(type=openapi.TYPE_STRING),
                    'workflow_name': openapi.Schema(type=openapi.TYPE_STRING),
                    'status': openapi.Schema(type=openapi.TYPE_STRING),
                }
            )
        )
    },
    tags=['Common - Infrastructure']
)
@api_view(['POST'])
@permission_classes([])
def execute_workflow(request):
    """
    Exécute un workflow prédéfini.
    
    Lance une séquence orchestrée d'actions inter-modules.
    """
    try:
        workflow_name = request.data.get('workflow_name')
        initial_data = request.data.get('initial_data', {})
        
        if not workflow_name:
            return Response(
                {'error': 'workflow_name est requis'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # Exécuter le workflow
        workflow_id = communication_hub.execute_workflow(workflow_name, initial_data)
        
        return Response({
            'workflow_id': workflow_id,
            'workflow_name': workflow_name,
            'status': 'started',
            'initial_data': initial_data,
            'timestamp': timezone.now().isoformat()
        }, status=status.HTTP_200_OK)
        
    except ValueError as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        return Response(
            {'error': f'Erreur lors de l\'exécution du workflow: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@swagger_auto_schema(
    method='get',
    operation_description="Liste les workflows disponibles",
    responses={
        200: openapi.Response(
            description="Liste des workflows",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'workflows': openapi.Schema(type=openapi.TYPE_OBJECT),
                }
            )
        )
    },
    tags=['Common - Infrastructure']
)
@api_view(['GET'])
@permission_classes([])
def list_workflows(request):
    """
    Liste tous les workflows disponibles.
    
    Retourne la définition de tous les workflows prédéfinis.
    """
    try:
        workflows = communication_hub.workflows
        
        # Formater les workflows pour l'affichage
        formatted_workflows = {}
        for name, steps in workflows.items():
            formatted_workflows[name] = {
                'name': name,
                'total_steps': len(steps),
                'steps': [
                    {
                        'step_name': step['step'],
                        'module': step['module'],
                        'action': step['action'],
                        'timeout': step['timeout']
                    }
                    for step in steps
                ]
            }
        
        return Response({
            'workflows': formatted_workflows,
            'total_count': len(workflows),
            'timestamp': timezone.now().isoformat()
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {'error': f'Erreur lors de la récupération des workflows: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )