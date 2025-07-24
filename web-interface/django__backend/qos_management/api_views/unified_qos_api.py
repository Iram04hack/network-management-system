"""
APIs unifiées pour le module QoS Management avec intégration GNS3 Central et Docker.

APIs modernes utilisant le pattern function-based views pour :
- Statut unifié du système QoS
- Collecte de données QoS depuis GNS3 et Docker
- Dashboard QoS temps réel
- Santé de l'infrastructure QoS
- Gestion des politiques QoS et SLA

Documentation Swagger automatique incluse.
"""

import logging
from typing import Dict, Any
from datetime import datetime
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from ..infrastructure.unified_qos_service import unified_qos_service
from ..models import QoSPolicy, InterfaceQoSPolicy, SLAComplianceRecord

logger = logging.getLogger(__name__)

# Paramètres Swagger réutilisables
swagger_tags = ['QoS Management Unifié']
swagger_operation_description_base = """
API unifiée pour la gestion QoS avec intégration complète :
- Service Central GNS3 pour la synchronisation des topologies
- Services Docker pour le contrôle de trafic (Traffic Control, HAProxy, etc.)
- Monitoring temps réel et conformité SLA
- Application automatique des politiques QoS

**Authentification requise**
"""


@swagger_auto_schema(
    method='get',
    operation_summary="Statut unifié du système QoS",
    operation_description=f"{swagger_operation_description_base}\n\nRécupère le statut complet du système QoS incluant la connectivité GNS3, Docker et la base de données.",
    tags=swagger_tags,
    responses={
        200: openapi.Response(
            description="Statut récupéré avec succès",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'timestamp': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME),
                    'service': openapi.Schema(type=openapi.TYPE_STRING, example='qos_management'),
                    'version': openapi.Schema(type=openapi.TYPE_STRING, example='1.0.0'),
                    'operational': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                    'components': openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'docker': openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    'available': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                                    'services_count': openapi.Schema(type=openapi.TYPE_INTEGER),
                                    'last_check': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME)
                                }
                            ),
                            'gns3': openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    'available': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                                    'interface_connected': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                                    'last_check': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME)
                                }
                            ),
                            'database': openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    'available': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                                    'policies_count': openapi.Schema(type=openapi.TYPE_INTEGER),
                                    'active_policies': openapi.Schema(type=openapi.TYPE_INTEGER),
                                    'interfaces_configured': openapi.Schema(type=openapi.TYPE_INTEGER)
                                }
                            )
                        }
                    ),
                    'summary': openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'total_policies': openapi.Schema(type=openapi.TYPE_INTEGER),
                            'active_policies': openapi.Schema(type=openapi.TYPE_INTEGER),
                            'configured_interfaces': openapi.Schema(type=openapi.TYPE_INTEGER),
                            'docker_services': openapi.Schema(type=openapi.TYPE_INTEGER),
                            'gns3_connected': openapi.Schema(type=openapi.TYPE_BOOLEAN)
                        }
                    )
                }
            )
        ),
        500: openapi.Response(description="Erreur interne du serveur")
    }
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def unified_qos_status(request):
    """
    Récupère le statut unifié du système QoS.
    
    Retourne l'état de santé complet incluant :
    - Connectivité GNS3 Central Service
    - Services Docker QoS (Traffic Control, HAProxy, etc.)
    - État de la base de données
    - Résumé des politiques QoS actives
    """
    try:
        status_data = unified_qos_service.get_comprehensive_status()
        return Response(status_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération du statut QoS unifié: {e}")
        return Response(
            {'error': f'Erreur lors de la récupération du statut: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@swagger_auto_schema(
    method='get',
    operation_summary="Collecte des données QoS unifiées",
    operation_description=f"{swagger_operation_description_base}\n\nCollecte toutes les données QoS depuis GNS3 et Docker, incluant les politiques appliquées et les statuts des services.",
    tags=swagger_tags,
    responses={
        200: openapi.Response(
            description="Données collectées avec succès",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'timestamp': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME),
                    'sources': openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'docker': openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    'status': openapi.Schema(type=openapi.TYPE_STRING),
                                    'services_count': openapi.Schema(type=openapi.TYPE_INTEGER),
                                    'services': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_OBJECT))
                                }
                            ),
                            'gns3': openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    'status': openapi.Schema(type=openapi.TYPE_STRING),
                                    'applied_policies_count': openapi.Schema(type=openapi.TYPE_INTEGER),
                                    'policies': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_OBJECT))
                                }
                            )
                        }
                    ),
                    'summary': openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'successful_collections': openapi.Schema(type=openapi.TYPE_INTEGER),
                            'failed_collections': openapi.Schema(type=openapi.TYPE_INTEGER),
                            'total_sources': openapi.Schema(type=openapi.TYPE_INTEGER)
                        }
                    )
                }
            )
        ),
        500: openapi.Response(description="Erreur lors de la collecte")
    }
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def unified_qos_data(request):
    """
    Collecte toutes les données QoS depuis GNS3 et Docker.
    
    Retourne :
    - Statut des services Docker QoS (Traffic Control, HAProxy, monitoring)
    - Politiques QoS appliquées dans GNS3
    - Métriques de performance et de santé
    """
    try:
        qos_data = unified_qos_service.collect_all_qos_data()
        return Response(qos_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Erreur lors de la collecte des données QoS: {e}")
        return Response(
            {'error': f'Erreur lors de la collecte: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@swagger_auto_schema(
    method='get',
    operation_summary="Dashboard QoS temps réel",
    operation_description=f"{swagger_operation_description_base}\n\nFournit toutes les données nécessaires pour le dashboard QoS, incluant les métriques de performance, la conformité SLA et la santé de l'infrastructure.",
    tags=swagger_tags,
    responses={
        200: openapi.Response(
            description="Données de dashboard récupérées avec succès",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'timestamp': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME),
                    'qos_overview': openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'total_policies': openapi.Schema(type=openapi.TYPE_INTEGER),
                            'active_policies': openapi.Schema(type=openapi.TYPE_INTEGER),
                            'inactive_policies': openapi.Schema(type=openapi.TYPE_INTEGER),
                            'total_traffic_classes': openapi.Schema(type=openapi.TYPE_INTEGER),
                            'configured_interfaces': openapi.Schema(type=openapi.TYPE_INTEGER),
                            'policy_types': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_STRING))
                        }
                    ),
                    'performance_metrics': openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'services_health': openapi.Schema(type=openapi.TYPE_OBJECT),
                            'response_times': openapi.Schema(type=openapi.TYPE_OBJECT),
                            'availability': openapi.Schema(type=openapi.TYPE_OBJECT)
                        }
                    ),
                    'sla_compliance': openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'overall_compliance': openapi.Schema(type=openapi.TYPE_NUMBER),
                            'compliant_devices': openapi.Schema(type=openapi.TYPE_INTEGER),
                            'total_devices': openapi.Schema(type=openapi.TYPE_INTEGER),
                            'trend': openapi.Schema(type=openapi.TYPE_STRING)
                        }
                    ),
                    'active_policies': openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'total_active': openapi.Schema(type=openapi.TYPE_INTEGER),
                            'by_type': openapi.Schema(type=openapi.TYPE_OBJECT),
                            'total_allocated_bandwidth': openapi.Schema(type=openapi.TYPE_INTEGER),
                            'average_priority': openapi.Schema(type=openapi.TYPE_NUMBER)
                        }
                    ),
                    'infrastructure_health': openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'total_services': openapi.Schema(type=openapi.TYPE_INTEGER),
                            'healthy_services': openapi.Schema(type=openapi.TYPE_INTEGER),
                            'running_services': openapi.Schema(type=openapi.TYPE_INTEGER),
                            'health_percentage': openapi.Schema(type=openapi.TYPE_NUMBER),
                            'gns3_connected': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                            'docker_connected': openapi.Schema(type=openapi.TYPE_BOOLEAN)
                        }
                    )
                }
            )
        ),
        500: openapi.Response(description="Erreur lors de la génération du dashboard")
    }
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def unified_qos_dashboard(request):
    """
    Fournit les données complètes pour le dashboard QoS.
    
    Inclut :
    - Vue d'ensemble des politiques QoS
    - Métriques de performance en temps réel
    - Conformité SLA et tendances
    - Santé de l'infrastructure QoS
    """
    try:
        dashboard_data = unified_qos_service.get_dashboard_data()
        return Response(dashboard_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Erreur lors de la génération du dashboard QoS: {e}")
        return Response(
            {'error': f'Erreur lors de la génération du dashboard: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@swagger_auto_schema(
    method='get',
    operation_summary="Santé de l'infrastructure QoS",
    operation_description=f"{swagger_operation_description_base}\n\nÉvalue la santé de tous les composants de l'infrastructure QoS incluant les services Docker et les connexions GNS3.",
    tags=swagger_tags,
    responses={
        200: openapi.Response(
            description="Santé de l'infrastructure évaluée avec succès",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'timestamp': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME),
                    'overall_health': openapi.Schema(type=openapi.TYPE_STRING, enum=['healthy', 'degraded', 'critical']),
                    'health_score': openapi.Schema(type=openapi.TYPE_NUMBER, minimum=0, maximum=100),
                    'components': openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'docker_services': openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    'total': openapi.Schema(type=openapi.TYPE_INTEGER),
                                    'healthy': openapi.Schema(type=openapi.TYPE_INTEGER),
                                    'unhealthy': openapi.Schema(type=openapi.TYPE_INTEGER),
                                    'services_detail': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_OBJECT))
                                }
                            ),
                            'gns3_connectivity': openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    'connected': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                                    'last_check': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME),
                                    'response_time': openapi.Schema(type=openapi.TYPE_NUMBER)
                                }
                            ),
                            'database_connectivity': openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    'connected': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                                    'policies_accessible': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                                    'last_check': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME)
                                }
                            )
                        }
                    ),
                    'recommendations': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_STRING))
                }
            )
        ),
        500: openapi.Response(description="Erreur lors de l'évaluation de la santé")
    }
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def qos_infrastructure_health(request):
    """
    Évalue la santé complète de l'infrastructure QoS.
    
    Analyse :
    - Santé des services Docker QoS (Traffic Control, HAProxy, monitoring)
    - Connectivité GNS3 Central Service
    - Accessibilité de la base de données
    - Recommandations d'amélioration
    """
    try:
        # Récupérer les données de santé depuis le service unifié
        infrastructure_health = unified_qos_service._get_infrastructure_health()
        
        # Évaluer la santé globale
        health_score = 0
        total_checks = 0
        
        # Santé des services Docker
        docker_health = infrastructure_health.get('health_percentage', 0)
        health_score += docker_health
        total_checks += 1
        
        # Connectivité GNS3
        if infrastructure_health.get('gns3_connected', False):
            health_score += 100
        total_checks += 1
        
        # Connectivité Docker
        if infrastructure_health.get('docker_connected', False):
            health_score += 100
        total_checks += 1
        
        overall_score = health_score / total_checks if total_checks > 0 else 0
        
        # Déterminer l'état de santé global
        if overall_score >= 80:
            overall_health = 'healthy'
        elif overall_score >= 50:
            overall_health = 'degraded'
        else:
            overall_health = 'critical'
            
        # Générer des recommandations
        recommendations = []
        if not infrastructure_health.get('gns3_connected', False):
            recommendations.append("Vérifier la connectivité au serveur GNS3")
        if not infrastructure_health.get('docker_connected', False):
            recommendations.append("Vérifier la connectivité au daemon Docker")
        if docker_health < 80:
            recommendations.append("Certains services Docker QoS sont en panne")
            
        # Détails des services Docker
        docker_services = unified_qos_service.docker_collector.collect_qos_services_status()
        
        health_data = {
            'timestamp': datetime.now().isoformat(),
            'overall_health': overall_health,
            'health_score': round(overall_score, 2),
            'components': {
                'docker_services': {
                    'total': infrastructure_health.get('total_services', 0),
                    'healthy': infrastructure_health.get('healthy_services', 0),
                    'unhealthy': infrastructure_health.get('total_services', 0) - infrastructure_health.get('healthy_services', 0),
                    'services_detail': docker_services
                },
                'gns3_connectivity': {
                    'connected': infrastructure_health.get('gns3_connected', False),
                    'last_check': datetime.now().isoformat(),
                    'response_time': 0.0  # À implémenter si nécessaire
                },
                'database_connectivity': {
                    'connected': True,  # Si on arrive ici, la DB est connectée
                    'policies_accessible': QoSPolicy.objects.exists(),
                    'last_check': datetime.now().isoformat()
                }
            },
            'recommendations': recommendations
        }
        
        return Response(health_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Erreur lors de l'évaluation de la santé de l'infrastructure QoS: {e}")
        return Response(
            {'error': f'Erreur lors de l\'évaluation: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@swagger_auto_schema(
    method='get',
    operation_summary="Points de terminaison QoS disponibles",
    operation_description=f"{swagger_operation_description_base}\n\nListe tous les points de terminaison disponibles pour l'API QoS unifiée avec leurs descriptions.",
    tags=swagger_tags,
    responses={
        200: openapi.Response(
            description="Liste des endpoints récupérée avec succès",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'service': openapi.Schema(type=openapi.TYPE_STRING, example='qos_management'),
                    'version': openapi.Schema(type=openapi.TYPE_STRING, example='1.0.0'),
                    'endpoints': openapi.Schema(
                        type=openapi.TYPE_ARRAY,
                        items=openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'path': openapi.Schema(type=openapi.TYPE_STRING),
                                'method': openapi.Schema(type=openapi.TYPE_STRING),
                                'description': openapi.Schema(type=openapi.TYPE_STRING),
                                'authentication_required': openapi.Schema(type=openapi.TYPE_BOOLEAN)
                            }
                        )
                    )
                }
            )
        )
    }
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def unified_qos_endpoints(request):
    """
    Liste tous les points de terminaison disponibles pour l'API QoS unifiée.
    
    Retourne une liste complète des endpoints avec descriptions et exigences d'authentification.
    """
    endpoints = [
        {
            'path': '/api/qos_management/unified/status/',
            'method': 'GET',
            'description': 'Statut unifié du système QoS (GNS3 + Docker + BDD)',
            'authentication_required': True
        },
        {
            'path': '/api/qos_management/unified/qos-data/',
            'method': 'GET', 
            'description': 'Collecte de toutes les données QoS depuis GNS3 et Docker',
            'authentication_required': True
        },
        {
            'path': '/api/qos_management/unified/dashboard/',
            'method': 'GET',
            'description': 'Données complètes pour le dashboard QoS temps réel',
            'authentication_required': True
        },
        {
            'path': '/api/qos_management/unified/infrastructure-health/',
            'method': 'GET',
            'description': 'Évaluation de la santé de l\'infrastructure QoS',
            'authentication_required': True
        },
        {
            'path': '/api/qos_management/unified/endpoints/',
            'method': 'GET',
            'description': 'Liste des points de terminaison disponibles',
            'authentication_required': True
        },
        {
            'path': '/api/qos_management/unified/integration-status/',
            'method': 'GET',
            'description': 'Statut détaillé des intégrations GNS3 et Docker',
            'authentication_required': True
        }
    ]
    
    return Response({
        'service': 'qos_management',
        'version': '1.0.0',
        'endpoints': endpoints
    }, status=status.HTTP_200_OK)


@swagger_auto_schema(
    method='get',
    operation_summary="Statut des intégrations GNS3 et Docker",
    operation_description=f"{swagger_operation_description_base}\n\nFournit un statut détaillé des intégrations avec GNS3 Central Service et les services Docker QoS.",
    tags=swagger_tags,
    responses={
        200: openapi.Response(
            description="Statut des intégrations récupéré avec succès",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'timestamp': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME),
                    'gns3_integration': openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'status': openapi.Schema(type=openapi.TYPE_STRING, enum=['connected', 'disconnected', 'error']),
                            'available': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                            'last_check': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME),
                            'event_subscriptions': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_STRING)),
                            'supported_operations': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_STRING))
                        }
                    ),
                    'docker_integration': openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'status': openapi.Schema(type=openapi.TYPE_STRING, enum=['connected', 'disconnected', 'error']),
                            'available': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                            'last_check': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME),
                            'monitored_services': openapi.Schema(type=openapi.TYPE_INTEGER),
                            'healthy_services': openapi.Schema(type=openapi.TYPE_INTEGER),
                            'service_types': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_STRING))
                        }
                    ),
                    'integration_health': openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'overall_status': openapi.Schema(type=openapi.TYPE_STRING, enum=['healthy', 'degraded', 'offline']),
                            'gns3_score': openapi.Schema(type=openapi.TYPE_NUMBER, minimum=0, maximum=100),
                            'docker_score': openapi.Schema(type=openapi.TYPE_NUMBER, minimum=0, maximum=100),
                            'combined_score': openapi.Schema(type=openapi.TYPE_NUMBER, minimum=0, maximum=100)
                        }
                    )
                }
            )
        ),
        500: openapi.Response(description="Erreur lors de la vérification des intégrations")
    }
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def integration_status(request):
    """
    Fournit un statut détaillé des intégrations GNS3 et Docker.
    
    Analyse :
    - Connectivité et disponibilité GNS3 Central Service
    - État des services Docker QoS
    - Santé globale des intégrations
    - Opérations supportées
    """
    try:
        # Vérifier l'intégration GNS3
        gns3_available = unified_qos_service.gns3_adapter.is_available()
        gns3_status = 'connected' if gns3_available else 'disconnected'
        
        gns3_events = [
            'project.updated', 'node.updated', 'link.created', 
            'link.updated', 'link.deleted', 'node.started', 'node.stopped'
        ]
        
        gns3_operations = [
            'policy_application', 'node_synchronization', 'topology_monitoring',
            'automatic_qos_deployment', 'event_handling'
        ]
        
        # Vérifier l'intégration Docker
        docker_available = unified_qos_service.docker_collector.is_available()
        docker_status = 'connected' if docker_available else 'disconnected'
        
        docker_services = unified_qos_service.docker_collector.collect_qos_services_status()
        healthy_docker_services = sum(1 for service in docker_services if service.get('is_healthy', False))
        
        service_types = list(set(service.get('service_type', 'unknown') for service in docker_services))
        
        # Calculer les scores de santé
        gns3_score = 100 if gns3_available else 0
        docker_score = (healthy_docker_services / len(docker_services) * 100) if docker_services else 0
        combined_score = (gns3_score + docker_score) / 2
        
        # Déterminer le statut global
        if combined_score >= 80:
            overall_status = 'healthy'
        elif combined_score >= 50:
            overall_status = 'degraded'
        else:
            overall_status = 'offline'
            
        integration_data = {
            'timestamp': datetime.now().isoformat(),
            'gns3_integration': {
                'status': gns3_status,
                'available': gns3_available,
                'last_check': datetime.now().isoformat(),
                'event_subscriptions': gns3_events,
                'supported_operations': gns3_operations
            },
            'docker_integration': {
                'status': docker_status,
                'available': docker_available,
                'last_check': datetime.now().isoformat(),
                'monitored_services': len(docker_services),
                'healthy_services': healthy_docker_services,
                'service_types': service_types
            },
            'integration_health': {
                'overall_status': overall_status,
                'gns3_score': round(gns3_score, 2),
                'docker_score': round(docker_score, 2),
                'combined_score': round(combined_score, 2)
            }
        }
        
        return Response(integration_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Erreur lors de la vérification du statut des intégrations QoS: {e}")
        return Response(
            {'error': f'Erreur lors de la vérification: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )