"""
Vues unifiées pour le dashboard avec intégration GNS3 et services Docker.

Ces vues utilisent le service unifié pour fournir des données consolidées
depuis GNS3, les services Docker et tous les modules NMS.
"""

import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from ..infrastructure.unified_dashboard_service import unified_dashboard_service

logger = logging.getLogger(__name__)


@swagger_auto_schema(
    method='get',
    operation_summary="Tableau de bord unifié complet",
    operation_description="""
    Récupère le tableau de bord unifié complet avec :
    - Données GNS3 (projets, nœuds, topologies)
    - Statut des services Docker (Prometheus, Grafana, Elasticsearch, etc.)
    - Données de tous les modules NMS (monitoring, security, network, qos, reporting)
    - Métriques consolidées de santé système
    - Alertes unifiées
    """,
    responses={
        200: openapi.Response(
            description="Données du tableau de bord unifié",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'success': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                    'dashboard_data': openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'gns3_projects': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_OBJECT)),
                            'gns3_nodes': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_OBJECT)),
                            'gns3_topology_stats': openapi.Schema(type=openapi.TYPE_OBJECT),
                            'docker_services': openapi.Schema(type=openapi.TYPE_OBJECT),
                            'monitoring_summary': openapi.Schema(type=openapi.TYPE_OBJECT),
                            'security_summary': openapi.Schema(type=openapi.TYPE_OBJECT),
                            'network_summary': openapi.Schema(type=openapi.TYPE_OBJECT),
                            'qos_summary': openapi.Schema(type=openapi.TYPE_OBJECT),
                            'reporting_summary': openapi.Schema(type=openapi.TYPE_OBJECT),
                            'system_health': openapi.Schema(type=openapi.TYPE_OBJECT),
                            'performance_metrics': openapi.Schema(type=openapi.TYPE_OBJECT),
                            'alerts_summary': openapi.Schema(type=openapi.TYPE_OBJECT),
                            'last_updated': openapi.Schema(type=openapi.TYPE_STRING),
                            'refresh_interval': openapi.Schema(type=openapi.TYPE_INTEGER)
                        }
                    )
                }
            )
        ),
        500: openapi.Response(description="Erreur serveur")
    },
    tags=['Dashboard Unifié']
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def unified_dashboard(request):
    """
    Récupère le tableau de bord unifié complet.
    
    Consolidation de toutes les données NMS :
    - GNS3 (projets, nœuds, topologies)
    - Services Docker (Prometheus, Grafana, Elasticsearch, etc.)
    - Modules NMS (monitoring, security, network, qos, reporting)
    - Métriques de santé système
    - Alertes consolidées
    """
    try:
        dashboard_data = unified_dashboard_service.get_unified_dashboard()
        
        # Enrichir avec les informations utilisateur
        if request.user.is_authenticated:
            dashboard_data['user_info'] = {
                'username': request.user.username,
                'is_staff': request.user.is_staff,
                'last_login': request.user.last_login.isoformat() if request.user.last_login else None
            }
        
        return Response(dashboard_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération du dashboard unifié: {e}")
        return Response(
            {
                'success': False,
                'error': 'Erreur lors de la récupération du dashboard unifié',
                'message': str(e)
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@swagger_auto_schema(
    method='get',
    operation_summary="Données GNS3 pour le dashboard",
    operation_description="""
    Récupère spécifiquement les données GNS3 pour le dashboard :
    - Liste des projets GNS3 avec leur statut
    - Nœuds actifs avec métriques de performance
    - Statistiques de topologie
    - Informations du serveur GNS3
    """,
    responses={
        200: openapi.Response(
            description="Données GNS3 du dashboard",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'projects': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_OBJECT)),
                    'nodes': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_OBJECT)),
                    'topology_stats': openapi.Schema(type=openapi.TYPE_OBJECT),
                    'server_info': openapi.Schema(type=openapi.TYPE_OBJECT),
                    'last_update': openapi.Schema(type=openapi.TYPE_STRING),
                    'source': openapi.Schema(type=openapi.TYPE_STRING)
                }
            )
        ),
        500: openapi.Response(description="Erreur serveur")
    },
    tags=['Dashboard Unifié']
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def gns3_dashboard_data(request):
    """
    Récupère les données GNS3 spécifiques au dashboard.
    
    Fournit les informations détaillées sur :
    - Projets GNS3 avec métriques de performance
    - Nœuds actifs et leur état
    - Statistiques de topologie
    - État du serveur GNS3
    """
    try:
        gns3_data = unified_dashboard_service.get_gns3_dashboard_data()
        return Response(gns3_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des données GNS3: {e}")
        return Response(
            {
                'error': 'Erreur lors de la récupération des données GNS3',
                'message': str(e)
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@swagger_auto_schema(
    method='get',
    operation_summary="Statut des services Docker",
    operation_description="""
    Récupère le statut de tous les services Docker du NMS :
    - Prometheus (métriques)
    - Grafana (visualisation)
    - Elasticsearch (recherche et logs)
    - Netdata (monitoring système)
    - ntopng (analyse trafic)
    - Suricata (détection d'intrusion)
    - Fail2Ban (protection)
    - HAProxy (load balancing)
    """,
    responses={
        200: openapi.Response(
            description="Statut des services Docker",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'services_status': openapi.Schema(type=openapi.TYPE_OBJECT),
                    'prometheus': openapi.Schema(type=openapi.TYPE_OBJECT),
                    'grafana': openapi.Schema(type=openapi.TYPE_OBJECT),
                    'elasticsearch': openapi.Schema(type=openapi.TYPE_OBJECT),
                    'netdata': openapi.Schema(type=openapi.TYPE_OBJECT),
                    'ntopng': openapi.Schema(type=openapi.TYPE_OBJECT),
                    'suricata': openapi.Schema(type=openapi.TYPE_OBJECT),
                    'fail2ban': openapi.Schema(type=openapi.TYPE_OBJECT),
                    'haproxy': openapi.Schema(type=openapi.TYPE_OBJECT),
                    'global_metrics': openapi.Schema(type=openapi.TYPE_OBJECT)
                }
            )
        ),
        500: openapi.Response(description="Erreur serveur")
    },
    tags=['Dashboard Unifié']
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def docker_services_status(request):
    """
    Récupère le statut de tous les services Docker.
    
    Contrôle de santé complet des services :
    - Prometheus (métriques)
    - Grafana (visualisation)
    - Elasticsearch (recherche et logs)
    - Netdata (monitoring système)
    - ntopng (analyse trafic)
    - Suricata (détection d'intrusion)
    - Fail2Ban (protection)
    - HAProxy (load balancing)
    """
    try:
        docker_status = unified_dashboard_service.get_docker_services_status()
        return Response(docker_status, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération du statut Docker: {e}")
        return Response(
            {
                'error': 'Erreur lors de la récupération du statut des services Docker',
                'message': str(e)
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@swagger_auto_schema(
    method='get',
    operation_summary="Métriques de santé système",
    operation_description="""
    Récupère les métriques de santé globales du système :
    - Score de santé global
    - Statut des composants (GNS3, Docker, modules)
    - Métriques de performance
    - Temps de réponse moyens
    """,
    responses={
        200: openapi.Response(
            description="Métriques de santé système",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'overall_score': openapi.Schema(type=openapi.TYPE_NUMBER),
                    'status': openapi.Schema(type=openapi.TYPE_STRING),
                    'components': openapi.Schema(type=openapi.TYPE_OBJECT),
                    'performance_metrics': openapi.Schema(type=openapi.TYPE_OBJECT),
                    'last_calculated': openapi.Schema(type=openapi.TYPE_STRING)
                }
            )
        ),
        500: openapi.Response(description="Erreur serveur")
    },
    tags=['Dashboard Unifié']
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def system_health_metrics(request):
    """
    Récupère les métriques de santé globales du système.
    
    Calcule et retourne :
    - Score de santé global (0-100)
    - Statut des composants principaux
    - Métriques de performance
    - Indicateurs de disponibilité
    """
    try:
        dashboard_data = unified_dashboard_service.get_unified_dashboard()
        
        if dashboard_data.get('success'):
            health_data = {
                'system_health': dashboard_data['dashboard_data'].get('system_health', {}),
                'performance_metrics': dashboard_data['dashboard_data'].get('performance_metrics', {}),
                'last_updated': dashboard_data['dashboard_data'].get('last_updated')
            }
            
            return Response(health_data, status=status.HTTP_200_OK)
        else:
            return Response(
                {
                    'error': 'Impossible de récupérer les métriques de santé',
                    'message': dashboard_data.get('error', 'Erreur inconnue')
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des métriques de santé: {e}")
        return Response(
            {
                'error': 'Erreur lors de la récupération des métriques de santé',
                'message': str(e)
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@swagger_auto_schema(
    method='get',
    operation_summary="Alertes système consolidées",
    operation_description="""
    Récupère toutes les alertes du système de manière consolidée :
    - Alertes des services Docker
    - Alertes de sécurité (Suricata, Fail2Ban)
    - Alertes des modules NMS
    - Compteurs par niveau de sévérité
    """,
    responses={
        200: openapi.Response(
            description="Alertes système consolidées",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'alerts': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_OBJECT)),
                    'alert_counts': openapi.Schema(type=openapi.TYPE_OBJECT),
                    'total_alerts': openapi.Schema(type=openapi.TYPE_INTEGER),
                    'last_updated': openapi.Schema(type=openapi.TYPE_STRING)
                }
            )
        ),
        500: openapi.Response(description="Erreur serveur")
    },
    tags=['Dashboard Unifié']
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def consolidated_alerts(request):
    """
    Récupère toutes les alertes système consolidées.
    
    Agrège les alertes de :
    - Services Docker
    - Suricata (sécurité)
    - Fail2Ban (protection)
    - Modules NMS
    """
    try:
        dashboard_data = unified_dashboard_service.get_unified_dashboard()
        
        if dashboard_data.get('success'):
            alerts_data = dashboard_data['dashboard_data'].get('alerts_summary', {})
            return Response(alerts_data, status=status.HTTP_200_OK)
        else:
            return Response(
                {
                    'error': 'Impossible de récupérer les alertes',
                    'message': dashboard_data.get('error', 'Erreur inconnue')
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des alertes: {e}")
        return Response(
            {
                'error': 'Erreur lors de la récupération des alertes',
                'message': str(e)
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@swagger_auto_schema(
    method='get',
    operation_summary="Résumé des modules NMS",
    operation_description="""
    Récupère un résumé de l'état de tous les modules NMS :
    - Monitoring (métriques, alertes)
    - Security (threats, incidents)
    - Network (dispositifs, interfaces)
    - QoS (politiques, SLA)
    - Reporting (rapports, distribution)
    """,
    responses={
        200: openapi.Response(
            description="Résumé des modules NMS",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'monitoring_summary': openapi.Schema(type=openapi.TYPE_OBJECT),
                    'security_summary': openapi.Schema(type=openapi.TYPE_OBJECT),
                    'network_summary': openapi.Schema(type=openapi.TYPE_OBJECT),
                    'qos_summary': openapi.Schema(type=openapi.TYPE_OBJECT),
                    'reporting_summary': openapi.Schema(type=openapi.TYPE_OBJECT),
                    'modules_health': openapi.Schema(type=openapi.TYPE_OBJECT)
                }
            )
        ),
        500: openapi.Response(description="Erreur serveur")
    },
    tags=['Dashboard Unifié']
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def modules_summary(request):
    """
    Récupère un résumé de l'état de tous les modules NMS.
    
    Fournit une vue d'ensemble de :
    - Module Monitoring
    - Module Security
    - Module Network Management
    - Module QoS Management
    - Module Reporting
    """
    try:
        dashboard_data = unified_dashboard_service.get_unified_dashboard()
        
        if dashboard_data.get('success'):
            modules_data = {
                'monitoring_summary': dashboard_data['dashboard_data'].get('monitoring_summary', {}),
                'security_summary': dashboard_data['dashboard_data'].get('security_summary', {}),
                'network_summary': dashboard_data['dashboard_data'].get('network_summary', {}),
                'qos_summary': dashboard_data['dashboard_data'].get('qos_summary', {}),
                'reporting_summary': dashboard_data['dashboard_data'].get('reporting_summary', {}),
                'modules_health': {
                    'monitoring': dashboard_data['dashboard_data'].get('monitoring_summary', {}).get('available', False),
                    'security': dashboard_data['dashboard_data'].get('security_summary', {}).get('available', False),
                    'network': dashboard_data['dashboard_data'].get('network_summary', {}).get('available', False),
                    'qos': dashboard_data['dashboard_data'].get('qos_summary', {}).get('available', False),
                    'reporting': dashboard_data['dashboard_data'].get('reporting_summary', {}).get('available', False),
                }
            }
            
            return Response(modules_data, status=status.HTTP_200_OK)
        else:
            return Response(
                {
                    'error': 'Impossible de récupérer les données des modules',
                    'message': dashboard_data.get('error', 'Erreur inconnue')
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des données des modules: {e}")
        return Response(
            {
                'error': 'Erreur lors de la récupération des données des modules',
                'message': str(e)
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@swagger_auto_schema(
    method='post',
    operation_summary="Forcer la mise à jour du cache",
    operation_description="""
    Force la mise à jour du cache du dashboard unifié.
    Utile pour obtenir des données fraîches immédiatement.
    """,
    responses={
        200: openapi.Response(
            description="Cache mis à jour avec succès",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'success': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                    'message': openapi.Schema(type=openapi.TYPE_STRING),
                    'cache_updated_at': openapi.Schema(type=openapi.TYPE_STRING)
                }
            )
        ),
        500: openapi.Response(description="Erreur serveur")
    },
    tags=['Dashboard Unifié']
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def refresh_dashboard_cache(request):
    """
    Force la mise à jour du cache du dashboard unifié.
    
    Vide le cache existant et force une nouvelle collecte
    de toutes les données du dashboard.
    """
    try:
        from django.core.cache import cache
        
        # Vider le cache
        cache.delete("unified_dashboard_complete")
        
        # Forcer une nouvelle collecte
        dashboard_data = unified_dashboard_service.get_unified_dashboard()
        
        return Response(
            {
                'success': True,
                'message': 'Cache du dashboard mis à jour avec succès',
                'cache_updated_at': datetime.now().isoformat(),
                'data_collected': dashboard_data.get('success', False)
            },
            status=status.HTTP_200_OK
        )
        
    except Exception as e:
        logger.error(f"Erreur lors de la mise à jour du cache: {e}")
        return Response(
            {
                'success': False,
                'error': 'Erreur lors de la mise à jour du cache',
                'message': str(e)
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@swagger_auto_schema(
    method='get',
    operation_summary="Configuration du dashboard",
    operation_description="""
    Récupère la configuration du dashboard unifié :
    - Intervalle de rafraîchissement
    - Sources de données disponibles
    - Paramètres de cache
    - Statut des intégrations
    """,
    responses={
        200: openapi.Response(
            description="Configuration du dashboard",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'refresh_interval': openapi.Schema(type=openapi.TYPE_INTEGER),
                    'cache_timeout': openapi.Schema(type=openapi.TYPE_INTEGER),
                    'data_sources': openapi.Schema(type=openapi.TYPE_OBJECT),
                    'integrations_status': openapi.Schema(type=openapi.TYPE_OBJECT),
                    'supported_features': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_STRING))
                }
            )
        )
    },
    tags=['Dashboard Unifié']
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_configuration(request):
    """
    Récupère la configuration du dashboard unifié.
    
    Informations sur :
    - Paramètres de rafraîchissement
    - Sources de données disponibles
    - Statut des intégrations
    - Fonctionnalités supportées
    """
    try:
        config_data = {
            'refresh_interval': 30,
            'cache_timeout': 300,
            'data_sources': {
                'gns3': {
                    'available': unified_dashboard_service.gns3_adapter.is_available(),
                    'description': 'Projets, nœuds et topologies GNS3'
                },
                'docker_services': {
                    'available': True,
                    'description': 'Services Docker (Prometheus, Grafana, etc.)'
                },
                'nms_modules': {
                    'available': True,
                    'description': 'Modules NMS (monitoring, security, etc.)'
                }
            },
            'integrations_status': {
                'gns3_integration': unified_dashboard_service.gns3_adapter.is_available(),
                'docker_services': True,
                'inter_module_communication': True,
                'caching': True
            },
            'supported_features': [
                'unified_dashboard',
                'gns3_integration',
                'docker_monitoring',
                'inter_module_communication',
                'real_time_updates',
                'consolidated_alerts',
                'system_health_monitoring'
            ]
        }
        
        return Response(config_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération de la configuration: {e}")
        return Response(
            {
                'error': 'Erreur lors de la récupération de la configuration',
                'message': str(e)
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )