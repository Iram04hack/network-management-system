"""
APIs unifiées pour le Network Management avec intégration GNS3 Central et Docker.

Ces APIs utilisent le service unifié pour fournir une interface moderne
et centralisée pour la gestion réseau.

Architecture Développeur Senior :
- Function-based views (pattern éprouvé du monitoring)
- Documentation Swagger automatique
- Intégration transparente GNS3 + Docker
- Gestion d'erreurs robuste
"""

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
import logging

from ..infrastructure.unified_network_service import unified_network_service

logger = logging.getLogger(__name__)


@swagger_auto_schema(
    method='get',
    operation_description="Récupère le statut global du network management unifié",
    responses={
        200: openapi.Response(
            description="Statut global du network management",
            examples={
                "application/json": {
                    "operational": True,
                    "components": {
                        "gns3_integration": {
                            "available": True,
                            "synchronized_devices": 5,
                            "active_connections": 3
                        },
                        "docker_integration": {
                            "summary": {
                                "total_services": 12,
                                "running_services": 11,
                                "global_status": "healthy"
                            }
                        }
                    },
                    "model_statistics": {
                        "devices": 8,
                        "interfaces": 24,
                        "configurations": 5,
                        "connections": 7
                    }
                }
            }
        )
    }
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def unified_status(request):
    """
    API pour récupérer le statut global du network management unifié.
    
    Retourne le statut de toutes les intégrations (GNS3, Docker) et 
    les statistiques des modèles.
    """
    try:
        status_data = unified_network_service.get_comprehensive_status()
        return Response(status_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Erreur récupération statut network management: {e}")
        return Response(
            {'error': f'Erreur interne: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@swagger_auto_schema(
    method='get',
    operation_description="Collecte toutes les données réseau depuis GNS3 et Docker",
    responses={
        200: openapi.Response(
            description="Données réseau complètes",
            examples={
                "application/json": {
                    "sources": {
                        "docker_infrastructure": {
                            "summary": {
                                "total_services": 12,
                                "running_services": 11,
                                "healthy_services": 10
                            },
                            "detailed_services": []
                        },
                        "gns3_network": {
                            "available": True,
                            "synchronized_devices": 5
                        }
                    },
                    "summary": {
                        "total_sources": 2,
                        "successful_collections": 2,
                        "failed_collections": 0
                    }
                }
            }
        )
    }
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def unified_network_data(request):
    """
    API pour collecter toutes les données réseau.
    
    Collecte et agrège les données depuis GNS3 et les services Docker.
    """
    try:
        network_data = unified_network_service.collect_all_network_data()
        return Response(network_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Erreur collecte données réseau: {e}")
        return Response(
            {'error': f'Erreur interne: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@swagger_auto_schema(
    method='get',
    operation_description="Récupère les données optimisées pour le dashboard réseau",
    responses={
        200: openapi.Response(
            description="Données dashboard réseau",
            examples={
                "application/json": {
                    "devices": [
                        {
                            "id": 1,
                            "name": "Router-01",
                            "ip_address": "192.168.1.1",
                            "device_type": "router",
                            "vendor": "Cisco",
                            "is_active": True
                        }
                    ],
                    "interfaces": [
                        {
                            "id": 1,
                            "name": "GigabitEthernet0/0",
                            "device__name": "Router-01",
                            "ip_address": "192.168.1.1",
                            "status": "up"
                        }
                    ],
                    "connections": [
                        {
                            "id": 1,
                            "source_device__name": "Router-01",
                            "target_device__name": "Switch-01",
                            "connection_type": "ethernet",
                            "status": "active"
                        }
                    ],
                    "statistics": {
                        "total_devices": 8,
                        "active_devices": 7,
                        "virtual_devices": 3,
                        "total_interfaces": 24,
                        "active_connections": 7
                    }
                }
            }
        )
    }
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def unified_dashboard(request):
    """
    API pour récupérer les données dashboard réseau unifié.
    
    Fournit des données optimisées pour l'affichage dans le dashboard
    avec statistiques et états des intégrations.
    """
    try:
        dashboard_data = unified_network_service.get_network_dashboard_data()
        return Response(dashboard_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Erreur récupération dashboard réseau: {e}")
        return Response(
            {'error': f'Erreur interne: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@swagger_auto_schema(
    method='get',
    operation_description="Récupère la santé de l'infrastructure réseau Docker NMS",
    responses={
        200: openapi.Response(
            description="Santé infrastructure réseau Docker",
            examples={
                "application/json": {
                    "summary": {
                        "total_services": 12,
                        "running_services": 11,
                        "healthy_services": 10,
                        "global_status": "healthy",
                        "availability_percent": 91.67
                    },
                    "services_by_type": {
                        "snmp_protocol": {"total": 1, "running": 1},
                        "netflow_collector": {"total": 1, "running": 1},
                        "traffic_analysis": {"total": 1, "running": 1},
                        "load_balancer": {"total": 1, "running": 1}
                    },
                    "detailed_services": []
                }
            }
        )
    }
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def network_infrastructure_health(request):
    """
    API pour récupérer la santé de l'infrastructure réseau Docker.
    
    Analyse l'état de tous les services Docker NMS liés au réseau
    et fournit un rapport de santé détaillé.
    """
    try:
        if not unified_network_service.docker_collector.is_available():
            return Response(
                {
                    'available': False,
                    'error': 'Docker non disponible',
                    'services': []
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
            
        health_data = unified_network_service.docker_collector.get_network_infrastructure_health()
        return Response(health_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Erreur récupération santé infrastructure réseau: {e}")
        return Response(
            {'error': f'Erreur interne: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@swagger_auto_schema(
    method='get',
    operation_description="Liste tous les endpoints disponibles du network management unifié",
    responses={
        200: openapi.Response(
            description="Liste des endpoints disponibles",
            examples={
                "application/json": {
                    "unified_apis": [
                        {
                            "endpoint": "/api/network_management/unified/status/",
                            "method": "GET",
                            "description": "Statut global du network management"
                        },
                        {
                            "endpoint": "/api/network_management/unified/network-data/",
                            "method": "GET", 
                            "description": "Données réseau complètes"
                        }
                    ],
                    "legacy_apis": [
                        {
                            "endpoint": "/api/network_management/devices/",
                            "method": "GET",
                            "description": "Gestion des équipements (legacy)"
                        }
                    ],
                    "integrations": {
                        "gns3_available": True,
                        "docker_available": True
                    }
                }
            }
        )
    }
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def unified_endpoints(request):
    """
    API pour lister tous les endpoints disponibles.
    
    Fournit une vue d'ensemble de toutes les APIs disponibles
    avec leur statut et description.
    """
    try:
        # Vérifier les intégrations disponibles
        service_status = unified_network_service.get_comprehensive_status()
        
        endpoints_data = {
            'unified_apis': [
                {
                    'endpoint': '/api/network_management/unified/status/',
                    'method': 'GET',
                    'description': 'Statut global du network management unifié'
                },
                {
                    'endpoint': '/api/network_management/unified/network-data/',
                    'method': 'GET',
                    'description': 'Collecte toutes les données réseau (GNS3 + Docker)'
                },
                {
                    'endpoint': '/api/network_management/unified/dashboard/',
                    'method': 'GET',
                    'description': 'Données optimisées pour dashboard réseau'
                },
                {
                    'endpoint': '/api/network_management/unified/infrastructure-health/',
                    'method': 'GET',
                    'description': 'Santé infrastructure réseau Docker NMS'
                },
                {
                    'endpoint': '/api/network_management/unified/endpoints/',
                    'method': 'GET',
                    'description': 'Liste des endpoints disponibles'
                },
                {
                    'endpoint': '/api/network_management/unified/integration-status/',
                    'method': 'GET',
                    'description': 'Statut détaillé des intégrations'
                }
            ],
            'legacy_apis': [
                {
                    'endpoint': '/api/network_management/devices/',
                    'method': 'GET/POST/PUT/DELETE',
                    'description': 'Gestion des équipements réseau (ViewSets legacy)'
                },
                {
                    'endpoint': '/api/network_management/interfaces/',
                    'method': 'GET/POST/PUT/DELETE',
                    'description': 'Gestion des interfaces réseau (ViewSets legacy)'
                },
                {
                    'endpoint': '/api/network_management/configurations/',
                    'method': 'GET/POST/PUT/DELETE',
                    'description': 'Gestion des configurations (ViewSets legacy)'
                },
                {
                    'endpoint': '/api/network_management/topology/',
                    'method': 'GET/POST/PUT/DELETE',
                    'description': 'Gestion des topologies (ViewSets legacy)'
                }
            ],
            'integrations': {
                'gns3_available': service_status['components']['gns3_integration']['available'],
                'docker_available': service_status['components']['docker_integration']['summary']['global_status'] == 'healthy',
                'operational': service_status['operational']
            },
            'timestamp': service_status['timestamp']
        }
        
        return Response(endpoints_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Erreur récupération endpoints network management: {e}")
        return Response(
            {'error': f'Erreur interne: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@swagger_auto_schema(
    method='get',
    operation_description="Récupère le statut détaillé de toutes les intégrations",
    responses={
        200: openapi.Response(
            description="Statut détaillé des intégrations",
            examples={
                "application/json": {
                    "gns3_integration": {
                        "available": True,
                        "synchronized_devices": 5,
                        "active_connections": 3,
                        "event_subscriptions": 6,
                        "last_update": "2025-07-08T22:30:00Z"
                    },
                    "docker_integration": {
                        "available": True,
                        "services_status": {
                            "total_services": 12,
                            "running_services": 11,
                            "global_status": "healthy"
                        },
                        "network_services": [
                            {
                                "service_name": "nms-snmp-agent",
                                "status": "running",
                                "service_type": "snmp_protocol",
                                "port": 161
                            }
                        ]
                    },
                    "overall_health": "operational"
                }
            }
        )
    }
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def integration_status(request):
    """
    API pour récupérer le statut détaillé des intégrations.
    
    Fournit des informations complètes sur l'état de toutes
    les intégrations (GNS3, Docker) avec détails techniques.
    """
    try:
        # Récupérer les statuts détaillés
        gns3_status = unified_network_service.gns3_adapter.get_gns3_network_status()
        docker_status = unified_network_service.docker_collector.get_network_infrastructure_health()
        
        integration_data = {
            'gns3_integration': gns3_status,
            'docker_integration': {
                'available': unified_network_service.docker_collector.is_available(),
                'services_status': docker_status.get('summary', {}),
                'network_services': docker_status.get('detailed_services', [])
            },
            'overall_health': 'operational' if (
                gns3_status.get('available', False) or 
                docker_status.get('summary', {}).get('global_status') == 'healthy'
            ) else 'degraded',
            'timestamp': docker_status.get('timestamp')
        }
        
        return Response(integration_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Erreur récupération statut intégrations: {e}")
        return Response(
            {'error': f'Erreur interne: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )