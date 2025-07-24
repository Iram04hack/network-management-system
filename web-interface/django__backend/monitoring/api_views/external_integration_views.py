"""
Vues API pour l'intégration des services externes.

Ce module expose les endpoints pour interagir avec 
Prometheus, Grafana, Elasticsearch et SNMP.
"""

import logging
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from ..di_container import resolve

logger = logging.getLogger(__name__)


@swagger_auto_schema(
    method='get',
    operation_description="Teste la connectivité avec tous les services externes",
    responses={
        200: openapi.Response(
            description="État de tous les services externes",
            examples={
                "application/json": {
                    "success": True,
                    "timestamp": "2025-01-01T12:00:00Z",
                    "overall_status": "healthy",
                    "services": {
                        "prometheus": {
                            "name": "Prometheus",
                            "status": "healthy",
                            "url": "http://localhost:9090"
                        },
                        "grafana": {
                            "name": "Grafana", 
                            "status": "healthy",
                            "url": "http://localhost:3000"
                        },
                        "elasticsearch": {
                            "name": "Elasticsearch",
                            "status": "healthy",
                            "url": "http://localhost:9200"
                        },
                        "snmp": {
                            "name": "SNMP Tools",
                            "status": "healthy"
                        }
                    },
                    "unhealthy_services": []
                }
            }
        )
    },
    tags=['Monitoring']
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def test_external_services(request):
    """Teste la connectivité avec tous les services externes."""
    try:
        external_service = resolve('external_integration_service')
        result = external_service.test_all_connections()
        
        return Response({
            'success': True,
            'data': result
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Erreur lors du test des services externes: {e}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@swagger_auto_schema(
    method='post',
    operation_description="Collecte des métriques complètes pour un équipement",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=['device_ip', 'device_id'],
        properties={
            'device_ip': openapi.Schema(
                type=openapi.TYPE_STRING,
                description="Adresse IP de l'équipement"
            ),
            'device_id': openapi.Schema(
                type=openapi.TYPE_INTEGER,
                description="ID de l'équipement"
            ),
            'community': openapi.Schema(
                type=openapi.TYPE_STRING,
                description="Communauté SNMP (défaut: public)",
                default="public"
            )
        }
    ),
    responses={
        200: openapi.Response(
            description="Métriques collectées avec succès",
            examples={
                "application/json": {
                    "success": True,
                    "data": {
                        "device_id": 1,
                        "device_ip": "192.168.1.1",
                        "success": True,
                        "metrics": {
                            "snmp": {
                                "system_info": {
                                    "sysName": "Router-01",
                                    "sysDescr": "Cisco IOS"
                                },
                                "interfaces": {}
                            }
                        },
                        "elasticsearch_indexed": True
                    }
                }
            }
        )
    },
    tags=['Monitoring']
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def collect_device_metrics(request):
    """Collecte des métriques complètes pour un équipement."""
    try:
        device_ip = request.data.get('device_ip')
        device_id = request.data.get('device_id')
        community = request.data.get('community', 'public')
        
        if not device_ip or not device_id:
            return Response({
                'success': False,
                'error': 'device_ip et device_id sont requis'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        external_service = resolve('external_integration_service')
        result = external_service.collect_device_metrics(device_ip, device_id, community)
        
        return Response({
            'success': True,
            'data': result
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Erreur lors de la collecte de métriques: {e}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@swagger_auto_schema(
    method='post',
    operation_description="Crée un tableau de bord Grafana pour un équipement",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=['device_id', 'device_name', 'device_ip'],
        properties={
            'device_id': openapi.Schema(
                type=openapi.TYPE_INTEGER,
                description="ID de l'équipement"
            ),
            'device_name': openapi.Schema(
                type=openapi.TYPE_STRING,
                description="Nom de l'équipement"
            ),
            'device_ip': openapi.Schema(
                type=openapi.TYPE_STRING,
                description="Adresse IP de l'équipement"
            )
        }
    ),
    responses={
        200: openapi.Response(
            description="Tableau de bord créé avec succès"
        )
    },
    tags=['Monitoring']
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_device_dashboard(request):
    """Crée un tableau de bord Grafana pour un équipement."""
    try:
        device_id = request.data.get('device_id')
        device_name = request.data.get('device_name')
        device_ip = request.data.get('device_ip')
        
        if not all([device_id, device_name, device_ip]):
            return Response({
                'success': False,
                'error': 'device_id, device_name et device_ip sont requis'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        external_service = resolve('external_integration_service')
        result = external_service.create_device_dashboard(device_id, device_name, device_ip)
        
        return Response({
            'success': True,
            'data': result
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Erreur lors de la création du tableau de bord: {e}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@swagger_auto_schema(
    method='get',
    operation_description="Recherche les alertes pour un équipement",
    manual_parameters=[
        openapi.Parameter(
            'device_id',
            openapi.IN_QUERY,
            description="ID de l'équipement",
            type=openapi.TYPE_INTEGER,
            required=True
        ),
        openapi.Parameter(
            'hours',
            openapi.IN_QUERY,
            description="Nombre d'heures à rechercher (défaut: 24)",
            type=openapi.TYPE_INTEGER,
            default=24
        )
    ],
    responses={
        200: openapi.Response(
            description="Alertes trouvées"
        )
    },
    tags=['Monitoring']
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def search_device_alerts(request):
    """Recherche les alertes pour un équipement."""
    try:
        device_id = request.query_params.get('device_id')
        hours = int(request.query_params.get('hours', 24))
        
        if not device_id:
            return Response({
                'success': False,
                'error': 'device_id est requis'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        external_service = resolve('external_integration_service')
        result = external_service.search_device_alerts(int(device_id), hours)
        
        return Response({
            'success': True,
            'data': result
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Erreur lors de la recherche d'alertes: {e}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@swagger_auto_schema(
    method='get',
    operation_description="Évalue la santé globale de l'infrastructure de monitoring",
    responses={
        200: openapi.Response(
            description="État de santé de l'infrastructure",
            examples={
                "application/json": {
                    "success": True,
                    "data": {
                        "overall_health": "healthy",
                        "timestamp": "2025-01-01T12:00:00Z",
                        "services": {},
                        "recommendations": [
                            "Tous les services fonctionnent correctement"
                        ],
                        "critical_services_down": [],
                        "optional_services_down": []
                    }
                }
            }
        )
    },
    tags=['Monitoring']
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_infrastructure_health(request):
    """Évalue la santé globale de l'infrastructure de monitoring."""
    try:
        external_service = resolve('external_integration_service')
        result = external_service.get_infrastructure_health()
        
        return Response({
            'success': True,
            'data': result
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Erreur lors de l'évaluation de la santé: {e}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@swagger_auto_schema(
    method='post',
    operation_description="Collecte des métriques pour plusieurs équipements en parallèle",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=['devices'],
        properties={
            'devices': openapi.Schema(
                type=openapi.TYPE_ARRAY,
                items=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'ip_address': openapi.Schema(type=openapi.TYPE_STRING),
                        'snmp_community': openapi.Schema(type=openapi.TYPE_STRING, default="public")
                    }
                ),
                description="Liste des équipements à surveiller"
            )
        }
    ),
    responses={
        200: openapi.Response(
            description="Résultats de la collecte en bulk"
        )
    },
    tags=['Monitoring']
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def bulk_collect_metrics(request):
    """Collecte des métriques pour plusieurs équipements en parallèle."""
    try:
        devices = request.data.get('devices', [])
        
        if not devices:
            return Response({
                'success': False,
                'error': 'Liste d\'équipements requise'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        external_service = resolve('external_integration_service')
        result = external_service.bulk_collect_metrics(devices)
        
        return Response({
            'success': True,
            'data': result
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Erreur lors de la collecte en bulk: {e}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR) 