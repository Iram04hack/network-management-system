"""
API REST pour les services d'intégration GNS3 et inter-modules.
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.utils import timezone
import json

from ..infrastructure.central_topology_service import central_topology_service
from ..infrastructure.gns3_integration_service import gns3_integration_service
from ..infrastructure.inter_module_service import inter_module_service, MessageType
from ..infrastructure.ubuntu_notification_service import ubuntu_notification_service

# Schémas Swagger pour la documentation
gns3_status_response = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'gns3_client_initialized': openapi.Schema(type=openapi.TYPE_BOOLEAN),
        'gns3_server_available': openapi.Schema(type=openapi.TYPE_BOOLEAN),
        'monitoring_active': openapi.Schema(type=openapi.TYPE_BOOLEAN),
        'gns3_config': openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'host': openapi.Schema(type=openapi.TYPE_STRING),
                'port': openapi.Schema(type=openapi.TYPE_INTEGER),
                'protocol': openapi.Schema(type=openapi.TYPE_STRING),
            }
        ),
        'last_detection_time': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME),
        'projects_count': openapi.Schema(type=openapi.TYPE_INTEGER),
    }
)

topology_response = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'gns3_topology': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_OBJECT)),
        'docker_services': openapi.Schema(type=openapi.TYPE_OBJECT),
        'modules_topology': openapi.Schema(type=openapi.TYPE_OBJECT),
        'integration_map': openapi.Schema(type=openapi.TYPE_OBJECT),
        'consolidation_time': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME),
    }
)

@swagger_auto_schema(
    method='get',
    operation_description="Récupère le statut complet des services d'intégration",
    responses={
        200: openapi.Response(
            description="Statut des services d'intégration",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'topology_service': openapi.Schema(type=openapi.TYPE_OBJECT),
                    'gns3_service': gns3_status_response,
                    'inter_module_service': openapi.Schema(type=openapi.TYPE_OBJECT),
                    'notification_service': openapi.Schema(type=openapi.TYPE_OBJECT),
                    'timestamp': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME),
                }
            )
        )
    },
    tags=['Common - Infrastructure']
)
@api_view(['GET'])
@permission_classes([])
def integration_status(request):
    """
    Récupère le statut complet des services d'intégration.
    
    Retourne l'état de tous les services : topologie, GNS3, inter-modules et notifications.
    """
    try:
        # Récupération des statuts
        topology_status = central_topology_service.get_integration_status()
        gns3_status = gns3_integration_service.get_status()
        inter_module_status = inter_module_service.get_status()
        notification_status = ubuntu_notification_service.get_status()
        
        response_data = {
            'topology_service': topology_status,
            'gns3_service': gns3_status,
            'inter_module_service': inter_module_status,
            'notification_service': notification_status,
            'timestamp': timezone.now().isoformat()
        }
        
        return Response(response_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {'error': f'Erreur lors de la récupération du statut: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@swagger_auto_schema(
    method='post',
    operation_description="Force une détection du serveur GNS3",
    responses={
        200: openapi.Response(
            description="Résultat de la détection GNS3",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'available': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                    'host': openapi.Schema(type=openapi.TYPE_STRING),
                    'port': openapi.Schema(type=openapi.TYPE_INTEGER),
                    'version': openapi.Schema(type=openapi.TYPE_STRING),
                    'projects_count': openapi.Schema(type=openapi.TYPE_INTEGER),
                    'detection_time': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME),
                    'error': openapi.Schema(type=openapi.TYPE_STRING),
                }
            )
        )
    },
    tags=['Common - Infrastructure']
)
@api_view(['POST'])
@permission_classes([])
def detect_gns3(request):
    """
    Force une détection du serveur GNS3.
    
    Lance une nouvelle détection du serveur GNS3 et retourne le résultat.
    """
    try:
        detection_result = gns3_integration_service.detect_gns3_server()
        return Response(detection_result, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {'error': f'Erreur lors de la détection GNS3: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@swagger_auto_schema(
    method='get',
    operation_description="Récupère la topologie consolidée de tous les services",
    responses={200: openapi.Response(description="Topologie consolidée", schema=topology_response)},
    tags=['Common - Infrastructure']
)
@api_view(['GET'])
@permission_classes([])
def consolidated_topology(request):
    """
    Récupère la topologie consolidée de tous les services.
    
    Retourne une vue unifiée des projets GNS3, services Docker et modules intégrés.
    """
    try:
        topology = central_topology_service.get_consolidated_topology()
        return Response(topology, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {'error': f'Erreur lors de la récupération de la topologie: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@swagger_auto_schema(
    method='get',
    operation_description="Récupère la liste des projets GNS3 détectés",
    responses={
        200: openapi.Response(
            description="Liste des projets GNS3",
            schema=openapi.Schema(
                type=openapi.TYPE_ARRAY,
                items=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'project_id': openapi.Schema(type=openapi.TYPE_STRING),
                        'name': openapi.Schema(type=openapi.TYPE_STRING),
                        'status': openapi.Schema(type=openapi.TYPE_STRING),
                        'node_count': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'nodes': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_OBJECT)),
                    }
                )
            )
        )
    },
    tags=['Common - Infrastructure']
)
@api_view(['GET'])
@permission_classes([])
def gns3_projects(request):
    """
    Récupère la liste des projets GNS3 détectés.
    
    Retourne tous les projets GNS3 avec leurs nœuds et statuts.
    """
    try:
        projects = gns3_integration_service.get_topology_data()
        return Response(projects, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {'error': f'Erreur lors de la récupération des projets GNS3: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@swagger_auto_schema(
    method='post',
    operation_description="Démarre la surveillance GNS3",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'interval': openapi.Schema(type=openapi.TYPE_INTEGER, description="Intervalle en secondes", default=30)
        }
    ),
    responses={
        200: openapi.Response(description="Surveillance démarrée"),
        400: openapi.Response(description="Paramètres invalides")
    },
    tags=['Common - Infrastructure']
)
@api_view(['POST'])
@permission_classes([])
def start_monitoring(request):
    """
    Démarre la surveillance GNS3.
    
    Lance la surveillance continue du serveur GNS3 avec l'intervalle spécifié.
    """
    try:
        interval = request.data.get('interval', 30)
        
        if not isinstance(interval, int) or interval < 5:
            return Response(
                {'error': 'L\'intervalle doit être un entier >= 5 secondes'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        central_topology_service.start_monitoring(interval)
        
        return Response(
            {
                'message': 'Surveillance démarrée',
                'interval': interval,
                'timestamp': timezone.now().isoformat()
            },
            status=status.HTTP_200_OK
        )
        
    except Exception as e:
        return Response(
            {'error': f'Erreur lors du démarrage de la surveillance: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@swagger_auto_schema(
    method='post',
    operation_description="Arrête la surveillance GNS3",
    responses={200: openapi.Response(description="Surveillance arrêtée")},
    tags=['Common - Infrastructure']
)
@api_view(['POST'])
@permission_classes([])
def stop_monitoring(request):
    """
    Arrête la surveillance GNS3.
    
    Stoppe la surveillance continue du serveur GNS3.
    """
    try:
        central_topology_service.stop_monitoring()
        
        return Response(
            {
                'message': 'Surveillance arrêtée',
                'timestamp': timezone.now().isoformat()
            },
            status=status.HTTP_200_OK
        )
        
    except Exception as e:
        return Response(
            {'error': f'Erreur lors de l\'arrêt de la surveillance: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@swagger_auto_schema(
    method='get',
    operation_description="Récupère la liste des modules intégrés",
    responses={
        200: openapi.Response(
            description="Liste des modules intégrés",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'modules': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_STRING)),
                    'health_status': openapi.Schema(type=openapi.TYPE_OBJECT),
                    'docker_services': openapi.Schema(type=openapi.TYPE_OBJECT),
                }
            )
        )
    },
    tags=['Common - Infrastructure']
)
@api_view(['GET'])
@permission_classes([])
def integrated_modules(request):
    """
    Récupère la liste des modules intégrés.
    
    Retourne tous les modules intégrés avec leur statut de santé.
    """
    try:
        # Health check des modules
        health_status = inter_module_service.health_check_all_modules()
        
        # Services Docker
        docker_services = inter_module_service.get_all_docker_services()
        
        # Statut inter-modules
        inter_status = inter_module_service.get_status()
        
        response_data = {
            'modules': inter_status['registered_modules'],
            'health_status': health_status,
            'docker_services': docker_services,
            'message_history_size': inter_status['message_history_size'],
            'timestamp': timezone.now().isoformat()
        }
        
        return Response(response_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {'error': f'Erreur lors de la récupération des modules: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@swagger_auto_schema(
    method='post',
    operation_description="Envoie un message inter-modules",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=['message_type', 'data'],
        properties={
            'message_type': openapi.Schema(
                type=openapi.TYPE_STRING,
                enum=['topology_update', 'node_status_change', 'network_event', 'security_alert', 'monitoring_data', 'qos_policy_update', 'configuration_change', 'service_discovery', 'health_check', 'notification'],
                description="Type de message"
            ),
            'data': openapi.Schema(type=openapi.TYPE_OBJECT, description="Données du message"),
            'target': openapi.Schema(type=openapi.TYPE_STRING, description="Module cible (optionnel, diffusion si absent)")
        }
    ),
    responses={
        200: openapi.Response(description="Message envoyé"),
        400: openapi.Response(description="Paramètres invalides")
    },
    tags=['Common - Infrastructure']
)
@api_view(['POST'])
@permission_classes([])
def send_inter_module_message(request):
    """
    Envoie un message inter-modules.
    
    Permet d'envoyer un message à tous les modules ou à un module spécifique.
    """
    try:
        message_type_str = request.data.get('message_type')
        data = request.data.get('data', {})
        target = request.data.get('target')
        
        if not message_type_str:
            return Response(
                {'error': 'Le type de message est requis'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            message_type = MessageType(message_type_str)
        except ValueError:
            return Response(
                {'error': f'Type de message invalide: {message_type_str}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Ajouter des métadonnées
        data.update({
            'api_sender': request.user.username,
            'api_timestamp': timezone.now().isoformat()
        })
        
        inter_module_service.send_message(
            message_type,
            data,
            sender='api_client',
            target=target
        )
        
        return Response(
            {
                'message': 'Message envoyé',
                'message_type': message_type_str,
                'target': target or 'all_modules',
                'timestamp': timezone.now().isoformat()
            },
            status=status.HTTP_200_OK
        )
        
    except Exception as e:
        return Response(
            {'error': f'Erreur lors de l\'envoi du message: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@swagger_auto_schema(
    method='get',
    operation_description="Récupère l'historique des messages inter-modules",
    manual_parameters=[
        openapi.Parameter('module', openapi.IN_QUERY, description="Filtrer par module", type=openapi.TYPE_STRING),
        openapi.Parameter('message_type', openapi.IN_QUERY, description="Filtrer par type de message", type=openapi.TYPE_STRING),
        openapi.Parameter('limit', openapi.IN_QUERY, description="Nombre maximum de messages", type=openapi.TYPE_INTEGER, default=50),
    ],
    responses={
        200: openapi.Response(
            description="Historique des messages",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'messages': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_OBJECT)),
                    'total_count': openapi.Schema(type=openapi.TYPE_INTEGER),
                    'filters_applied': openapi.Schema(type=openapi.TYPE_OBJECT),
                }
            )
        )
    },
    tags=['Common - Infrastructure']
)
@api_view(['GET'])
@permission_classes([])
def message_history(request):
    """
    Récupère l'historique des messages inter-modules.
    
    Permet de filtrer par module, type de message et limiter le nombre de résultats.
    """
    try:
        # Paramètres de filtrage
        module_filter = request.GET.get('module')
        message_type_filter = request.GET.get('message_type')
        limit = int(request.GET.get('limit', 50))
        
        # Convertir le type de message si fourni
        message_type_enum = None
        if message_type_filter:
            try:
                message_type_enum = MessageType(message_type_filter)
            except ValueError:
                return Response(
                    {'error': f'Type de message invalide: {message_type_filter}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Récupérer l'historique
        messages = inter_module_service.get_message_history(
            module_name=module_filter,
            message_type=message_type_enum,
            limit=limit
        )
        
        response_data = {
            'messages': messages,
            'total_count': len(messages),
            'filters_applied': {
                'module': module_filter,
                'message_type': message_type_filter,
                'limit': limit
            },
            'timestamp': timezone.now().isoformat()
        }
        
        return Response(response_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {'error': f'Erreur lors de la récupération de l\'historique: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@swagger_auto_schema(
    method='post',
    operation_description="Envoie une notification Ubuntu de test",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'title': openapi.Schema(type=openapi.TYPE_STRING, description="Titre de la notification"),
            'message': openapi.Schema(type=openapi.TYPE_STRING, description="Message de la notification"),
            'urgency': openapi.Schema(type=openapi.TYPE_STRING, enum=['low', 'normal', 'critical'], default='normal'),
        }
    ),
    responses={
        200: openapi.Response(description="Notification envoyée"),
        400: openapi.Response(description="Paramètres invalides")
    },
    tags=['Common - Infrastructure']
)
@api_view(['POST'])
@permission_classes([])
def send_notification(request):
    """
    Envoie une notification Ubuntu.
    
    Permet d'envoyer une notification système personnalisée.
    """
    try:
        title = request.data.get('title', 'Notification API')
        message = request.data.get('message', 'Test depuis l\'API REST')
        urgency = request.data.get('urgency', 'normal')
        
        if urgency not in ['low', 'normal', 'critical']:
            return Response(
                {'error': 'Urgence doit être: low, normal ou critical'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        success = ubuntu_notification_service.send_notification(
            title=title,
            message=message,
            urgency=urgency,
            category='api.test'
        )
        
        if success:
            return Response(
                {
                    'message': 'Notification envoyée',
                    'title': title,
                    'urgency': urgency,
                    'timestamp': timezone.now().isoformat()
                },
                status=status.HTTP_200_OK
            )
        else:
            return Response(
                {'error': 'Échec de l\'envoi de la notification'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
    except Exception as e:
        return Response(
            {'error': f'Erreur lors de l\'envoi de la notification: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@swagger_auto_schema(
    method='get',
    operation_description="Effectue un health check complet du système",
    responses={
        200: openapi.Response(
            description="Résultat du health check",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'overall_status': openapi.Schema(type=openapi.TYPE_STRING, enum=['ok', 'warning', 'critical']),
                    'services': openapi.Schema(type=openapi.TYPE_OBJECT),
                    'modules': openapi.Schema(type=openapi.TYPE_OBJECT),
                    'gns3_available': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                    'notifications_available': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                    'recommendations': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_STRING)),
                }
            )
        )
    },
    tags=['Common - Infrastructure']
)
@api_view(['GET'])
@permission_classes([])
def health_check(request):
    """
    Effectue un health check complet du système.
    
    Vérifie l'état de tous les services et modules intégrés.
    """
    try:
        # Health check des modules
        modules_health = inter_module_service.health_check_all_modules()
        
        # Statut GNS3
        gns3_status = gns3_integration_service.get_status()
        gns3_available = gns3_status.get('gns3_server_available', False)
        
        # Statut notifications
        notification_status = ubuntu_notification_service.get_status()
        notifications_available = notification_status.get('notify_send_available', False)
        
        # Statut des services
        topology_status = central_topology_service.get_integration_status()
        
        # Analyser les problèmes
        problems = []
        warnings = []
        
        # Vérifier les modules en erreur
        error_modules = [name for name, status in modules_health.items() 
                        if status.get('status') == 'error']
        if error_modules:
            problems.append(f"Modules en erreur: {', '.join(error_modules)}")
        
        # Vérifier GNS3
        if not gns3_available:
            warnings.append("Serveur GNS3 non disponible")
        
        # Vérifier les notifications
        if not notifications_available:
            warnings.append("Notifications Ubuntu non disponibles")
        
        # Déterminer le statut global
        if problems:
            overall_status = 'critical'
        elif warnings:
            overall_status = 'warning'
        else:
            overall_status = 'ok'
        
        # Recommandations
        recommendations = []
        if error_modules:
            recommendations.append("Vérifiez les logs des modules en erreur")
        if not gns3_available:
            recommendations.append("Vérifiez que le serveur GNS3 est démarré sur localhost:3080")
        if not notifications_available:
            recommendations.append("Installez notify-send: sudo apt install libnotify-bin")
        if overall_status == 'ok':
            recommendations.append("Tous les services fonctionnent correctement")
        
        response_data = {
            'overall_status': overall_status,
            'services': {
                'topology_service': topology_status['service_status'],
                'gns3_service': 'ok' if gns3_available else 'error',
                'inter_module_service': 'ok',
                'notification_service': 'ok' if notifications_available else 'warning'
            },
            'modules': modules_health,
            'gns3_available': gns3_available,
            'notifications_available': notifications_available,
            'problems': problems,
            'warnings': warnings,
            'recommendations': recommendations,
            'timestamp': timezone.now().isoformat()
        }
        
        return Response(response_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {'error': f'Erreur lors du health check: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )