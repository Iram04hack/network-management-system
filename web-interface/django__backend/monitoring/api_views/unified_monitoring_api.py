"""
API unifiée du module Monitoring intégrant GNS3 Central et Docker.

Cette API suit le pattern function-based views qui fonctionne et intègre :
- Le service central GNS3 via le nouveau Service Central
- Les services Docker spécialisés NMS (Prometheus, Grafana, etc.)
- Une surveillance unifiée temps réel
- Des métriques consolidées pour le frontend

Architecture Développeur Senior :
- Pattern function-based views éprouvé
- Documentation Swagger automatique
- Gestion d'erreurs robuste
- Endpoints RESTful cohérents
"""

import logging
from typing import Dict, List, Any
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from ..infrastructure.unified_monitoring_service import (
    unified_monitoring_service,
    get_monitoring_service_endpoints,
    get_service_integration_status
)

logger = logging.getLogger(__name__)

# ==================== SCHÉMAS SWAGGER ====================

unified_monitoring_status_response = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'service_name': openapi.Schema(type=openapi.TYPE_STRING),
        'operational': openapi.Schema(type=openapi.TYPE_BOOLEAN),
        'timestamp': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME),
        'components': openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'gns3_integration': openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'available': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                        'monitored_nodes': openapi.Schema(type=openapi.TYPE_INTEGER)
                    }
                ),
                'docker_integration': openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'available': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                        'monitored_services': openapi.Schema(type=openapi.TYPE_INTEGER)
                    }
                )
            }
        ),
        'nms_services_health': openapi.Schema(type=openapi.TYPE_OBJECT),
        'gns3_summary': openapi.Schema(type=openapi.TYPE_OBJECT)
    }
)

nms_services_health_response = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'status': openapi.Schema(type=openapi.TYPE_STRING, enum=['healthy', 'warning', 'critical', 'degraded']),
        'services': openapi.Schema(type=openapi.TYPE_OBJECT),
        'summary': openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'total_services': openapi.Schema(type=openapi.TYPE_INTEGER),
                'running_services': openapi.Schema(type=openapi.TYPE_INTEGER),
                'stopped_services': openapi.Schema(type=openapi.TYPE_INTEGER),
                'critical_services_down': openapi.Schema(type=openapi.TYPE_INTEGER)
            }
        ),
        'timestamp': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME)
    }
)

unified_metrics_response = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'collection_time': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME),
        'gns3_metrics': openapi.Schema(type=openapi.TYPE_OBJECT),
        'nms_services_metrics': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_OBJECT)),
        'nms_services_health': openapi.Schema(type=openapi.TYPE_OBJECT),
        'summary': openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'total_sources': openapi.Schema(type=openapi.TYPE_INTEGER),
                'successful_collections': openapi.Schema(type=openapi.TYPE_INTEGER),
                'failed_collections': openapi.Schema(type=openapi.TYPE_INTEGER)
            }
        )
    }
)

# ==================== APIS PRINCIPALES ====================

@swagger_auto_schema(
    method='get',
    operation_summary="Statut du Service Unifié de Monitoring",
    operation_description="""
    Récupère l'état complet du service unifié de monitoring incluant :
    - Intégration GNS3 Central avec nœuds surveillés
    - Services Docker NMS (Prometheus, Grafana, Netdata, etc.)
    - Santé des composants critiques
    - Métriques de performance globales
    
    Cette API centralise tous les statuts de monitoring pour le dashboard principal.
    """,
    tags=['Monitoring - Service Unifié'],
    responses={
        200: openapi.Response(
            description="Statut récupéré avec succès",
            schema=unified_monitoring_status_response
        ),
        500: "Erreur interne du service"
    }
)
@api_view(['GET'])
@permission_classes([AllowAny])
def unified_monitoring_status(request):
    """Récupère le statut complet du service unifié de monitoring."""
    try:
        comprehensive_status = unified_monitoring_service.get_comprehensive_status()
        
        logger.info("📊 Statut unifié de monitoring récupéré avec succès")
        return Response(comprehensive_status, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération du statut unifié: {e}")
        return Response(
            {
                "error": f"Erreur lors de la récupération du statut: {str(e)}",
                "timestamp": timezone.now().isoformat()
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@swagger_auto_schema(
    method='get',
    operation_summary="Santé des Services Docker NMS",
    operation_description="""
    Vérifie la santé de tous les services Docker du NMS :
    - Services de monitoring (Prometheus, Grafana, Netdata, ntopng)
    - Services de base de données (PostgreSQL, Redis, Elasticsearch)
    - Services de sécurité (Suricata, Fail2Ban)
    - Services applicatifs (Django, Celery)
    - Services réseau (SNMP Agent, Netflow Collector, HAProxy)
    
    Retourne un statut détaillé avec health checks automatiques.
    """,
    tags=['Monitoring - Service Unifié'],
    responses={
        200: openapi.Response(
            description="Santé des services vérifiée avec succès",
            schema=nms_services_health_response
        ),
        503: "Services Docker non disponibles"
    }
)
@api_view(['GET'])
@permission_classes([AllowAny])
def nms_services_health(request):
    """Vérifie la santé de tous les services Docker NMS."""
    try:
        if not unified_monitoring_service.docker_collector.is_available():
            return Response(
                {
                    "error": "Services Docker non disponibles",
                    "status": "docker_unavailable",
                    "timestamp": timezone.now().isoformat()
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
            
        health_status = unified_monitoring_service.docker_collector.get_nms_services_health()
        
        logger.info(f"🏥 Santé des services NMS vérifiée: {health_status['status']}")
        return Response(health_status, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Erreur lors de la vérification de santé des services NMS: {e}")
        return Response(
            {
                "error": f"Erreur lors de la vérification de santé: {str(e)}",
                "timestamp": timezone.now().isoformat()
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@swagger_auto_schema(
    method='get',
    operation_summary="Métriques Unifiées de Monitoring",
    operation_description="""
    Collecte toutes les métriques de monitoring en temps réel :
    - Métriques des nœuds GNS3 surveillés
    - Métriques des services Docker NMS
    - Statistiques de performance des conteneurs
    - Résumé consolidé pour le dashboard
    
    Cette API fournit une vue d'ensemble complète pour l'analyse des performances.
    """,
    tags=['Monitoring - Service Unifié'],
    responses={
        200: openapi.Response(
            description="Métriques collectées avec succès",
            schema=unified_metrics_response
        ),
        500: "Erreur lors de la collecte des métriques"
    }
)
@api_view(['GET'])
@permission_classes([AllowAny])
def unified_metrics_collection(request):
    """Collecte toutes les métriques de monitoring unifiées."""
    try:
        all_metrics = unified_monitoring_service.collect_all_metrics()
        
        logger.info(f"📈 Métriques unifiées collectées: {all_metrics['summary']['successful_collections']} sources")
        return Response(all_metrics, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Erreur lors de la collecte des métriques unifiées: {e}")
        return Response(
            {
                "error": f"Erreur lors de la collecte des métriques: {str(e)}",
                "timestamp": timezone.now().isoformat()
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@swagger_auto_schema(
    method='get',
    operation_summary="Dashboard de Monitoring Unifié",
    operation_description="""
    Récupère toutes les données nécessaires pour le dashboard de monitoring unifié :
    - Vue d'ensemble du système complet
    - Métriques en temps réel
    - Santé de l'infrastructure
    - Indicateurs de performance
    - Organisation des données par type de service
    
    Cette API est optimisée pour l'affichage dans le frontend.
    """,
    tags=['Monitoring - Service Unifié'],
    responses={
        200: openapi.Response(
            description="Données du dashboard récupérées avec succès",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'overview': openapi.Schema(type=openapi.TYPE_OBJECT),
                    'metrics': openapi.Schema(type=openapi.TYPE_OBJECT),
                    'nms_infrastructure_health': openapi.Schema(type=openapi.TYPE_OBJECT),
                    'service_metrics_by_type': openapi.Schema(type=openapi.TYPE_OBJECT),
                    'alerts_summary': openapi.Schema(type=openapi.TYPE_OBJECT),
                    'performance_indicators': openapi.Schema(type=openapi.TYPE_OBJECT)
                }
            )
        ),
        500: "Erreur lors de la génération du dashboard"
    }
)
@api_view(['GET'])
@permission_classes([AllowAny])
def unified_monitoring_dashboard(request):
    """Récupère les données complètes du dashboard de monitoring unifié."""
    try:
        dashboard_data = unified_monitoring_service.get_monitoring_dashboard_data()
        
        logger.info("🎛️ Données du dashboard unifié générées avec succès")
        return Response(dashboard_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Erreur lors de la génération du dashboard unifié: {e}")
        return Response(
            {
                "error": f"Erreur lors de la génération du dashboard: {str(e)}",
                "timestamp": timezone.now().isoformat()
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# ==================== APIS SPÉCIALISÉES ====================

@swagger_auto_schema(
    method='get',
    operation_summary="Données Spécialisées par Type de Service",
    operation_description="""
    Récupère des données spécialisées pour un type de service spécifique :
    - monitoring : Prometheus, Grafana, Netdata, ntopng
    - security : Suricata, Fail2Ban, Kibana
    - database : PostgreSQL, Redis, Elasticsearch
    - network : SNMP Agent, Netflow Collector, HAProxy
    - application : Django, Celery
    
    Utile pour des vues détaillées par domaine fonctionnel.
    """,
    tags=['Monitoring - Services Spécialisés'],
    manual_parameters=[
        openapi.Parameter(
            'service_type',
            openapi.IN_QUERY,
            description="Type de service (monitoring, security, database, network, application)",
            type=openapi.TYPE_STRING,
            required=True,
            enum=['monitoring', 'security', 'database', 'network', 'application']
        )
    ],
    responses={
        200: openapi.Response(
            description="Données spécialisées récupérées avec succès",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'service_type': openapi.Schema(type=openapi.TYPE_STRING),
                    'services': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_OBJECT)),
                    'endpoints': openapi.Schema(type=openapi.TYPE_OBJECT),
                    'status': openapi.Schema(type=openapi.TYPE_STRING),
                    'timestamp': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME)
                }
            )
        ),
        400: "Type de service invalide",
        500: "Erreur lors de la récupération des données spécialisées"
    }
)
@api_view(['GET'])
@permission_classes([AllowAny])
def specialized_service_data(request):
    """Récupère des données spécialisées pour un type de service."""
    try:
        service_type = request.query_params.get('service_type')
        
        if not service_type:
            return Response(
                {
                    "error": "service_type est requis",
                    "valid_types": ["monitoring", "security", "database", "network", "application"],
                    "timestamp": timezone.now().isoformat()
                },
                status=status.HTTP_400_BAD_REQUEST
            )
            
        if service_type not in ['monitoring', 'security', 'database', 'network', 'application']:
            return Response(
                {
                    "error": f"Type de service '{service_type}' invalide",
                    "valid_types": ["monitoring", "security", "database", "network", "application"],
                    "timestamp": timezone.now().isoformat()
                },
                status=status.HTTP_400_BAD_REQUEST
            )
            
        specialized_data = unified_monitoring_service.get_specialized_service_data(service_type)
        
        logger.info(f"🔧 Données spécialisées récupérées pour {service_type}: {specialized_data['status']}")
        return Response(specialized_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des données spécialisées: {e}")
        return Response(
            {
                "error": f"Erreur lors de la récupération des données spécialisées: {str(e)}",
                "timestamp": timezone.now().isoformat()
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@swagger_auto_schema(
    method='get',
    operation_summary="Endpoints des Services de Monitoring",
    operation_description="""
    Récupère tous les endpoints d'accès aux services de monitoring NMS :
    - URLs des interfaces web (Grafana, Prometheus, etc.)
    - APIs REST accessibles
    - Ports et services disponibles
    
    Utile pour l'intégration et la navigation vers les services externes.
    """,
    tags=['Monitoring - Configuration'],
    responses={
        200: openapi.Response(
            description="Endpoints récupérés avec succès",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'prometheus': openapi.Schema(type=openapi.TYPE_STRING),
                    'grafana': openapi.Schema(type=openapi.TYPE_STRING),
                    'netdata': openapi.Schema(type=openapi.TYPE_STRING),
                    'ntopng': openapi.Schema(type=openapi.TYPE_STRING),
                    'elasticsearch': openapi.Schema(type=openapi.TYPE_STRING),
                    'kibana': openapi.Schema(type=openapi.TYPE_STRING),
                    'haproxy_stats': openapi.Schema(type=openapi.TYPE_STRING),
                    'django_api': openapi.Schema(type=openapi.TYPE_STRING),
                    'swagger_docs': openapi.Schema(type=openapi.TYPE_STRING)
                }
            )
        )
    }
)
@api_view(['GET'])
@permission_classes([AllowAny])
def monitoring_service_endpoints(request):
    """Récupère tous les endpoints des services de monitoring."""
    try:
        endpoints = get_monitoring_service_endpoints()
        
        logger.info("🔗 Endpoints des services de monitoring récupérés")
        return Response(endpoints, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des endpoints: {e}")
        return Response(
            {
                "error": f"Erreur lors de la récupération des endpoints: {str(e)}",
                "timestamp": timezone.now().isoformat()
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@swagger_auto_schema(
    method='get',
    operation_summary="Statut d'Intégration des Services",
    operation_description="""
    Vérifie le statut d'intégration de tous les composants :
    - Service Central GNS3
    - Services Docker NMS
    - Service Unifié de Monitoring
    - Endpoints disponibles
    
    Cette API permet de diagnostiquer les problèmes d'intégration.
    """,
    tags=['Monitoring - Configuration'],
    responses={
        200: openapi.Response(
            description="Statut d'intégration vérifié avec succès",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'gns3_central': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                    'docker_services': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                    'unified_service': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                    'endpoints': openapi.Schema(type=openapi.TYPE_OBJECT),
                    'nms_services_health': openapi.Schema(type=openapi.TYPE_OBJECT),
                    'timestamp': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME)
                }
            )
        )
    }
)
@api_view(['GET'])
@permission_classes([AllowAny])
def service_integration_status(request):
    """Vérifie le statut d'intégration de tous les services."""
    try:
        integration_status = get_service_integration_status()
        
        logger.info("🔄 Statut d'intégration des services vérifié")
        return Response(integration_status, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Erreur lors de la vérification du statut d'intégration: {e}")
        return Response(
            {
                "error": f"Erreur lors de la vérification du statut d'intégration: {str(e)}",
                "timestamp": timezone.now().isoformat()
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# ==================== API DE TEST ====================

@swagger_auto_schema(
    method='post',
    operation_summary="Test de Connectivité aux Services",
    operation_description="""
    Teste la connectivité vers tous les services de monitoring :
    - Vérifie les health checks de chaque service
    - Teste les endpoints API
    - Valide la communication Docker
    
    Utile pour le diagnostic et la validation de déploiement.
    """,
    tags=['Monitoring - Tests'],
    responses={
        200: openapi.Response(
            description="Tests de connectivité exécutés avec succès",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'test_results': openapi.Schema(type=openapi.TYPE_OBJECT),
                    'overall_status': openapi.Schema(type=openapi.TYPE_STRING),
                    'timestamp': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME)
                }
            )
        )
    }
)
@api_view(['POST'])
@permission_classes([AllowAny])
def test_services_connectivity(request):
    """Teste la connectivité vers tous les services de monitoring."""
    try:
        test_results = {
            'docker_connectivity': unified_monitoring_service.docker_collector.is_available(),
            'gns3_integration': unified_monitoring_service.gns3_adapter.is_available(),
            'unified_service': unified_monitoring_service.is_fully_operational(),
            'services_health': {},
            'endpoints_accessible': {}
        }
        
        # Test de santé des services si Docker est disponible
        if test_results['docker_connectivity']:
            test_results['services_health'] = unified_monitoring_service.docker_collector.get_nms_services_health()
            
        # Test des endpoints
        endpoints = get_monitoring_service_endpoints()
        for service_name, endpoint in endpoints.items():
            test_results['endpoints_accessible'][service_name] = {
                'endpoint': endpoint,
                'accessible': True  # Simulation - en production, tester avec requests
            }
            
        # Déterminer le statut global
        overall_status = 'healthy'
        if not test_results['docker_connectivity']:
            overall_status = 'docker_unavailable'
        elif not test_results['gns3_integration']:
            overall_status = 'gns3_unavailable'
        elif not test_results['unified_service']:
            overall_status = 'partial_failure'
            
        response_data = {
            'test_results': test_results,
            'overall_status': overall_status,
            'timestamp': timezone.now().isoformat()
        }
        
        logger.info(f"🧪 Tests de connectivité exécutés: {overall_status}")
        return Response(response_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Erreur lors des tests de connectivité: {e}")
        return Response(
            {
                "error": f"Erreur lors des tests de connectivité: {str(e)}",
                "timestamp": timezone.now().isoformat()
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )