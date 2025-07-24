"""
Vues API pour l'intégration avec le Service Central de Topologie.

Ces vues exposent les fonctionnalités d'intégration entre le module
monitoring et le Service Central de Topologie.
"""

import logging
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication, SessionAuthentication
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from ..infrastructure.services.topology_integration_service import TopologyIntegrationService

logger = logging.getLogger(__name__)


# Configuration de l'authentification
auth_classes = [TokenAuthentication, SessionAuthentication]
permission_classes_list = [IsAuthenticated]


@swagger_auto_schema(
    method='get',
    operation_description="Récupère la liste des équipements monitorables depuis la topologie",
    responses={
        200: openapi.Response(
            description="Liste des équipements monitorables",
            examples={
                'application/json': {
                    'success': True,
                    'devices': [
                        {
                            'id': 1,
                            'name': 'Router-Main',
                            'ip_address': '192.168.1.1',
                            'device_type': 'router',
                            'monitoring': {
                                'monitoring_enabled': True,
                                'collection_interval': 60,
                                'priority': 'critical'
                            }
                        }
                    ],
                    'total_count': 1,
                    'timestamp': '2025-07-05T11:48:00Z'
                }
            }
        ),
        500: openapi.Response(description="Erreur serveur")
    },
    tags=['Monitoring']
)
@api_view(['GET'])
@authentication_classes(auth_classes)
@permission_classes(permission_classes_list)
def get_monitorable_devices(request):
    """
    Récupère la liste des équipements monitorables.
    
    Cette endpoint utilise le Service Central de Topologie pour obtenir
    la liste des équipements avec leurs configurations de monitoring.
    """
    try:
        topology_service = TopologyIntegrationService()
        
        # Filtres optionnels depuis les paramètres de requête
        device_filter = {}
        if request.GET.get('device_type'):
            device_filter['device_type'] = request.GET.get('device_type')
        if request.GET.get('is_active'):
            device_filter['is_active'] = request.GET.get('is_active').lower() == 'true'
        if request.GET.get('priority'):
            device_filter['priority'] = request.GET.get('priority')
        
        result = topology_service.get_monitorable_devices(device_filter if device_filter else None)
        
        if result['success']:
            return Response(result, status=status.HTTP_200_OK)
        else:
            return Response(
                {
                    'success': False,
                    'error': result['error']
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des équipements monitorables: {e}")
        return Response(
            {
                'success': False,
                'error': 'Erreur interne du serveur'
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@swagger_auto_schema(
    method='get',
    operation_description="Récupère la configuration complète d'un équipement pour le monitoring",
    responses={
        200: openapi.Response(
            description="Configuration de l'équipement",
            examples={
                'application/json': {
                    'success': True,
                    'device': {
                        'id': 1,
                        'name': 'Router-Main',
                        'ip_address': '192.168.1.1',
                        'device_type': 'router',
                        'monitoring': {
                            'monitoring_enabled': True,
                            'collection_interval': 60,
                            'priority': 'critical',
                            'metrics_to_collect': [
                                {
                                    'name': 'cpu_utilization',
                                    'oid': '1.3.6.1.4.1.9.9.109.1.1.1.1.7.1',
                                    'type': 'snmp'
                                }
                            ]
                        }
                    }
                }
            }
        ),
        404: openapi.Response(description="Équipement non trouvé"),
        500: openapi.Response(description="Erreur serveur")
    },
    tags=['Monitoring']
)
@api_view(['GET'])
@authentication_classes(auth_classes)
@permission_classes(permission_classes_list)
def get_device_configuration(request, device_id):
    """
    Récupère la configuration complète d'un équipement pour le monitoring.
    
    Args:
        device_id: ID de l'équipement
    """
    try:
        topology_service = TopologyIntegrationService()
        result = topology_service.get_device_configuration(int(device_id))
        
        if result['success']:
            return Response(result, status=status.HTTP_200_OK)
        else:
            return Response(
                {
                    'success': False,
                    'error': result['error']
                },
                status=status.HTTP_404_NOT_FOUND
            )
            
    except ValueError:
        return Response(
            {
                'success': False,
                'error': 'ID d\'équipement invalide'
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        logger.error(f"Erreur lors de la récupération de la configuration {device_id}: {e}")
        return Response(
            {
                'success': False,
                'error': 'Erreur interne du serveur'
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@swagger_auto_schema(
    method='post',
    operation_description="Met à jour le statut de monitoring d'un équipement",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'last_collection': openapi.Schema(type=openapi.TYPE_STRING, format='date-time'),
            'metrics_collected': openapi.Schema(type=openapi.TYPE_INTEGER),
            'success_rate': openapi.Schema(type=openapi.TYPE_NUMBER),
            'errors': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_STRING))
        },
        required=['last_collection']
    ),
    responses={
        200: openapi.Response(
            description="Statut mis à jour avec succès",
            examples={
                'application/json': {
                    'success': True,
                    'message': 'Statut de monitoring mis à jour'
                }
            }
        ),
        400: openapi.Response(description="Données invalides"),
        404: openapi.Response(description="Équipement non trouvé"),
        500: openapi.Response(description="Erreur serveur")
    },
    tags=['Monitoring']
)
@api_view(['POST'])
@authentication_classes(auth_classes)
@permission_classes(permission_classes_list)
def update_monitoring_status(request, device_id):
    """
    Met à jour le statut de monitoring d'un équipement.
    
    Args:
        device_id: ID de l'équipement
    """
    try:
        topology_service = TopologyIntegrationService()
        status_data = request.data
        
        # Validation des données requises
        if 'last_collection' not in status_data:
            return Response(
                {
                    'success': False,
                    'error': 'Champ last_collection requis'
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        result = topology_service.update_monitoring_status(int(device_id), status_data)
        
        if result['success']:
            return Response(result, status=status.HTTP_200_OK)
        else:
            return Response(
                {
                    'success': False,
                    'error': result['error']
                },
                status=status.HTTP_404_NOT_FOUND if 'non trouvé' in result['error'] else status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            
    except ValueError:
        return Response(
            {
                'success': False,
                'error': 'ID d\'équipement invalide'
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        logger.error(f"Erreur lors de la mise à jour du statut {device_id}: {e}")
        return Response(
            {
                'success': False,
                'error': 'Erreur interne du serveur'
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@swagger_auto_schema(
    method='get',
    operation_description="Récupère l'état de santé de la topologie réseau",
    responses={
        200: openapi.Response(
            description="État de santé de la topologie",
            examples={
                'application/json': {
                    'success': True,
                    'topology_health': {
                        'overall_status': 'healthy',
                        'devices_online': 25,
                        'devices_offline': 2,
                        'services_status': {
                            'gns3': 'healthy',
                            'database': 'healthy'
                        }
                    }
                }
            }
        ),
        500: openapi.Response(description="Erreur serveur")
    },
    tags=['Monitoring']
)
@api_view(['GET'])
@authentication_classes(auth_classes)
@permission_classes(permission_classes_list)
def get_topology_health(request):
    """
    Récupère l'état de santé de la topologie réseau.
    
    Cette endpoint fournit une vue d'ensemble de l'état de santé
    de l'infrastructure réseau gérée par la topologie.
    """
    try:
        topology_service = TopologyIntegrationService()
        result = topology_service.get_topology_health()
        
        if result['success']:
            return Response(result, status=status.HTTP_200_OK)
        else:
            return Response(
                {
                    'success': False,
                    'error': result['error'],
                    'health_status': result.get('health_status', 'unknown')
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            
    except Exception as e:
        logger.error(f"Erreur lors de la récupération de l'état de santé: {e}")
        return Response(
            {
                'success': False,
                'error': 'Erreur interne du serveur',
                'health_status': 'critical'
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@swagger_auto_schema(
    method='post',
    operation_description="Lance une synchronisation avec le Service Central de Topologie",
    responses={
        200: openapi.Response(
            description="Synchronisation réussie",
            examples={
                'application/json': {
                    'success': True,
                    'sync_duration_seconds': 12.5,
                    'results': {
                        'total_devices': 25,
                        'synchronized_devices': 23,
                        'failed_devices': 2,
                        'new_devices': 1,
                        'updated_devices': 22
                    }
                }
            }
        ),
        500: openapi.Response(description="Erreur lors de la synchronisation")
    },
    tags=['Monitoring']
)
@api_view(['POST'])
@authentication_classes(auth_classes)
@permission_classes(permission_classes_list)
def sync_with_topology(request):
    """
    Lance une synchronisation avec le Service Central de Topologie.
    
    Cette opération synchronise les données de monitoring avec
    les dernières informations de la topologie réseau.
    """
    try:
        topology_service = TopologyIntegrationService()
        result = topology_service.sync_with_topology()
        
        if result['success']:
            return Response(result, status=status.HTTP_200_OK)
        else:
            return Response(
                {
                    'success': False,
                    'error': result['error']
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            
    except Exception as e:
        logger.error(f"Erreur lors de la synchronisation: {e}")
        return Response(
            {
                'success': False,
                'error': 'Erreur interne du serveur'
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@swagger_auto_schema(
    method='get',
    operation_description="Vérifie la disponibilité du Service Central de Topologie",
    responses={
        200: openapi.Response(
            description="Statut de disponibilité",
            examples={
                'application/json': {
                    'available': True,
                    'service_name': 'Service Central de Topologie',
                    'status': 'operational',
                    'last_check': '2025-07-05T11:48:00Z'
                }
            }
        )
    },
    tags=['Monitoring']
)
@api_view(['GET'])
@authentication_classes(auth_classes)
@permission_classes(permission_classes_list)
def check_topology_service_status(request):
    """
    Vérifie la disponibilité du Service Central de Topologie.
    
    Cette endpoint permet de vérifier si le Service Central de Topologie
    est disponible et opérationnel.
    """
    try:
        topology_service = TopologyIntegrationService()
        is_available = topology_service.is_topology_service_available()
        
        response_data = {
            'available': is_available,
            'service_name': 'Service Central de Topologie',
            'status': 'operational' if is_available else 'unavailable',
            'last_check': '2025-07-05T11:48:00Z'  # Timestamp actuel en réalité
        }
        
        return Response(response_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Erreur lors de la vérification du statut: {e}")
        return Response(
            {
                'available': False,
                'service_name': 'Service Central de Topologie',
                'status': 'error',
                'error': str(e),
                'last_check': '2025-07-05T11:48:00Z'
            },
            status=status.HTTP_200_OK  # Toujours 200 pour le statut, l'erreur est dans les données
        )