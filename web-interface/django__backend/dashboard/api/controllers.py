"""
Contrôleurs API pour le module Dashboard.

Ce fichier contient les vues et contrôleurs API qui exposent
les fonctionnalités du tableau de bord à l'interface utilisateur.
"""

import asyncio
import logging
from typing import Dict, Any, Optional

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views import View
import json

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from ..di_container import container

logger = logging.getLogger(__name__)


# Vue de test sans authentification
def test_dashboard_status(request):
    """Vue de test pour vérifier que les APIs dashboard fonctionnent."""
    import asyncio
    
    try:
        # Récupérer le service depuis le conteneur
        dashboard_service = container.get_service('dashboard_service')

        # Tester l'appel de service
        async def test_service():
            try:
                result = await dashboard_service.get_dashboard_overview(user_id=1)
                return {
                    'service_call_success': True,
                    'result_type': str(type(result)),
                    'result_data': {
                        'devices': result.devices,
                        'alerts_count': len(result.security_alerts) + len(result.system_alerts),
                        'timestamp': result.timestamp.isoformat()
                    }
                }
            except Exception as e:
                return {
                    'service_call_success': False,
                    'error': str(e)
                }
        
        service_test_result = asyncio.run(test_service())

        return JsonResponse({
            'status': 'success',
            'message': 'Dashboard API is working',
            'service_available': dashboard_service is not None,
            'service_test': service_test_result,
            'fix_applied': 'Method execute() error has been resolved',
            'crud_endpoints': {
                'configs': '/api/dashboard/configs/ (GET, POST, PUT, PATCH, DELETE)',
                'widgets': '/api/dashboard/widgets/ (GET, POST, PUT, PATCH, DELETE)',
                'presets': '/api/dashboard/presets/ (GET, POST, PUT, PATCH, DELETE)',
                'custom': '/api/dashboard/custom/ (GET, POST, PUT, PATCH, DELETE)'
            },
            'data_endpoints': [
                '/api/dashboard/data/',
                '/api/dashboard/config/',
                '/api/dashboard/network/overview/',
                '/api/dashboard/network/health/',
                '/api/dashboard/topology/list/',
                '/api/dashboard/topology/data/',
            ]
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


class DashboardDataView(APIView):
    """
    Vue API pour récupérer les données du tableau de bord.

    Cette vue fournit les données agrégées du tableau de bord
    incluant les métriques réseau, les alertes et les statistiques.
    """
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Récupère les données agrégées du tableau de bord",
        operation_summary="Données du tableau de bord",
        tags=['Dashboard'],
        responses={
            200: openapi.Response(
                description="Données du tableau de bord récupérées avec succès",
                examples={
                    "application/json": {
                        "status": "success",
                        "data": {
                            "widgets": [],
                            "metrics": {
                                "total_devices": 25,
                                "active_devices": 23,
                                "alerts_count": 3
                            },
                            "last_updated": "2025-06-29T12:00:00Z",
                            "user_preferences": {
                                "theme": "light",
                                "layout": "grid"
                            }
                        }
                    }
                }
            ),
            401: openapi.Response(description="Non authentifié"),
            500: openapi.Response(description="Erreur serveur")
        }
    )
    def get(self, request):
        """Récupère les données agrégées du tableau de bord."""
        try:
            # Récupérer le service depuis le conteneur
            dashboard_service = container.get_service('dashboard_service')

            # Récupérer l'ID utilisateur
            user_id = request.user.id

            # Wrapper pour appel asynchrone depuis contexte synchrone
            async def get_dashboard_data_async():
                return await dashboard_service.get_dashboard_overview(user_id)

            # Exécution asynchrone dans contexte synchrone
            dashboard_data = asyncio.run(get_dashboard_data_async())

            # Sérialisation sécurisée
            safe_data = {
                'widgets': getattr(dashboard_data, 'widgets', []),
                'metrics': getattr(dashboard_data, 'metrics', {}),
                'last_updated': getattr(dashboard_data, 'last_updated', None),
                'user_preferences': getattr(dashboard_data, 'user_preferences', {})
            }

            # Convertir en format JSON et renvoyer
            return Response({
                'status': 'success',
                'data': safe_data
            }, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des données du tableau de bord: {e}")
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UserDashboardConfigView(APIView):
    """
    Vue API pour gérer la configuration du tableau de bord utilisateur.

    Permet de récupérer et modifier la configuration personnalisée
    du tableau de bord pour l'utilisateur connecté.
    """
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Récupère la configuration du tableau de bord de l'utilisateur",
        operation_summary="Configuration utilisateur",
        tags=['Dashboard'],
        responses={
            200: openapi.Response(
                description="Configuration récupérée avec succès",
                examples={
                    "application/json": {
                        "status": "success",
                        "data": {
                            "theme": "light",
                            "layout": "grid",
                            "refresh_interval": 60,
                            "widgets": [
                                {"type": "system_health", "position": {"x": 0, "y": 0}}
                            ]
                        }
                    }
                }
            ),
            401: openapi.Response(description="Non authentifié"),
            500: openapi.Response(description="Erreur serveur")
        }
    )
    def get(self, request):
        """Récupère la configuration du tableau de bord de l'utilisateur."""
        try:
            # Récupérer le service depuis le conteneur
            dashboard_service = container.get_service('dashboard_service')

            # Récupérer l'ID utilisateur
            user_id = request.user.id

            # Wrapper pour appel asynchrone depuis contexte synchrone
            async def get_user_config_async():
                return await dashboard_service.get_user_dashboard_config(user_id)

            # Exécution asynchrone dans contexte synchrone
            config = asyncio.run(get_user_config_async())

            # Renvoyer la configuration
            return Response({
                'status': 'success',
                'data': config
            }, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Erreur lors de la récupération de la configuration utilisateur: {e}")
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @swagger_auto_schema(
        operation_description="Enregistre la configuration du tableau de bord de l'utilisateur",
        operation_summary="Sauvegarder configuration",
        tags=['Dashboard'],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'theme': openapi.Schema(type=openapi.TYPE_STRING, description='Thème du tableau de bord'),
                'layout': openapi.Schema(type=openapi.TYPE_STRING, description='Type de disposition'),
                'refresh_interval': openapi.Schema(type=openapi.TYPE_INTEGER, description='Intervalle de rafraîchissement'),
                'widgets': openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    description='Configuration des widgets',
                    items=openapi.Schema(type=openapi.TYPE_OBJECT)
                )
            }
        ),
        responses={
            200: openapi.Response(description="Configuration sauvegardée avec succès"),
            400: openapi.Response(description="Données invalides"),
            401: openapi.Response(description="Non authentifié"),
            500: openapi.Response(description="Erreur serveur")
        }
    )
    def post(self, request):
        """Enregistre la configuration du tableau de bord de l'utilisateur."""
        try:
            # Récupérer le service depuis le conteneur
            dashboard_service = container.get_service('dashboard_service')

            # Récupérer l'ID utilisateur
            user_id = request.user.id

            # Récupérer les données de la requête
            data = request.data

            # Wrapper pour appel asynchrone depuis contexte synchrone
            async def save_user_config_async():
                return await dashboard_service.save_user_dashboard_config(user_id, data)

            # Exécution asynchrone dans contexte synchrone
            success = asyncio.run(save_user_config_async())

            if success:
                return Response({
                    'status': 'success',
                    'message': 'Configuration enregistrée avec succès'
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'status': 'error',
                    'message': 'Échec de l\'enregistrement de la configuration'
                }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Erreur lors de l'enregistrement de la configuration utilisateur: {e}")
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class NetworkOverviewView(APIView):
    """
    Vue API pour récupérer la vue d'ensemble du réseau.

    Fournit les données de topologie réseau, statistiques
    des équipements et alertes actives.
    """
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Récupère la vue d'ensemble du réseau",
        operation_summary="Vue d'ensemble réseau",
        tags=['Dashboard'],
        responses={
            200: openapi.Response(
                description="Vue d'ensemble du réseau récupérée avec succès",
                examples={
                    "application/json": {
                        "status": "success",
                        "data": {
                            "devices": [
                                {"id": 1, "name": "Router-01", "status": "active", "ip": "192.168.1.1"}
                            ],
                            "links": [
                                {"source": 1, "target": 2, "status": "up", "bandwidth": "1Gbps"}
                            ],
                            "statistics": {
                                "total_devices": 25,
                                "active_devices": 23,
                                "total_bandwidth": "10Gbps"
                            },
                            "alerts": [
                                {"id": 1, "severity": "warning", "message": "High CPU usage"}
                            ]
                        }
                    }
                }
            ),
            401: openapi.Response(description="Non authentifié"),
            500: openapi.Response(description="Erreur serveur")
        }
    )
    def get(self, request):
        """Récupère la vue d'ensemble du réseau."""
        try:
            # Récupérer le service depuis le conteneur
            network_service = container.get_service('network_overview_service')

            # Wrapper pour appel asynchrone depuis contexte synchrone
            async def get_network_overview_async():
                return await network_service.get_network_overview()

            # Exécution asynchrone dans contexte synchrone
            overview_data = asyncio.run(get_network_overview_async())

            # Sérialisation sécurisée
            safe_data = {
                'devices': getattr(overview_data, 'devices', []),
                'links': getattr(overview_data, 'links', []),
                'statistics': getattr(overview_data, 'statistics', {}),
                'alerts': getattr(overview_data, 'alerts', [])
            }

            # Renvoyer les données
            return Response({
                'status': 'success',
                'data': safe_data
            }, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Erreur lors de la récupération de l'aperçu réseau: {e}")
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class TopologyDataView(APIView):
    """
    Vue API pour récupérer les données de topologie.

    Fournit les données de topologie réseau pour la visualisation
    graphique des équipements et de leurs connexions.
    """
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Récupère les données de topologie pour visualisation",
        operation_summary="Données de topologie",
        tags=['Dashboard'],
        manual_parameters=[
            openapi.Parameter(
                'topology_id',
                openapi.IN_QUERY,
                description="ID de la topologie à récupérer (optionnel)",
                type=openapi.TYPE_INTEGER,
                required=False
            )
        ],
        responses={
            200: openapi.Response(
                description="Données de topologie récupérées avec succès",
                examples={
                    "application/json": {
                        "status": "success",
                        "data": {
                            "nodes": [
                                {"id": 1, "name": "Router-01", "type": "router", "x": 100, "y": 200}
                            ],
                            "edges": [
                                {"source": 1, "target": 2, "type": "ethernet"}
                            ],
                            "metadata": {
                                "last_updated": "2025-06-29T12:00:00Z",
                                "total_nodes": 25
                            }
                        }
                    }
                }
            ),
            401: openapi.Response(description="Non authentifié"),
            500: openapi.Response(description="Erreur serveur")
        }
    )
    def get(self, request):
        """Récupère les données de topologie pour visualisation."""
        try:
            # Récupérer le service depuis le conteneur
            topology_service = container.get_service('topology_service')

            # Récupérer l'ID de la topologie depuis les paramètres de requête
            topology_id = request.GET.get('topology_id')
            if topology_id:
                topology_id = int(topology_id)

            # Wrapper pour appel asynchrone depuis contexte synchrone
            async def get_topology_data_async():
                return await topology_service.get_topology_data(topology_id)

            # Exécution asynchrone dans contexte synchrone
            topology_data = asyncio.run(get_topology_data_async())

            # Renvoyer les données
            return Response({
                'status': 'success',
                'data': topology_data
            }, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des données de topologie: {e}")
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class TopologyListView(APIView):
    """
    Vue API pour récupérer la liste des topologies disponibles.

    Fournit la liste de toutes les topologies réseau configurées
    dans le système avec leurs métadonnées.
    """
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Récupère la liste des topologies disponibles",
        operation_summary="Liste des topologies",
        tags=['Dashboard'],
        responses={
            200: openapi.Response(
                description="Liste des topologies récupérée avec succès",
                examples={
                    "application/json": {
                        "status": "success",
                        "data": [
                            {
                                "id": 1,
                                "name": "Topologie principale",
                                "description": "Topologie du réseau principal",
                                "created_at": "2025-06-29T10:00:00Z",
                                "node_count": 25
                            }
                        ]
                    }
                }
            ),
            401: openapi.Response(description="Non authentifié"),
            500: openapi.Response(description="Erreur serveur")
        }
    )
    def get(self, request):
        """Récupère la liste des topologies disponibles."""
        try:
            # Récupérer le service depuis le conteneur
            topology_service = container.get_service('topology_service')

            # Wrapper pour appel asynchrone depuis contexte synchrone
            async def get_available_topologies_async():
                return await topology_service.get_available_topologies()

            # Exécution asynchrone dans contexte synchrone
            topologies = asyncio.run(get_available_topologies_async())

            # Renvoyer la liste
            return Response({
                'status': 'success',
                'data': topologies
            }, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des topologies disponibles: {e}")
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SystemHealthView(APIView):
    """
    Vue API pour récupérer les métriques de santé du système.

    Fournit les métriques système en temps réel incluant
    CPU, mémoire, disque et statut des services.
    """
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Récupère les métriques de santé du système",
        operation_summary="Santé du système",
        tags=['Dashboard'],
        responses={
            200: openapi.Response(
                description="Métriques de santé récupérées avec succès",
                examples={
                    "application/json": {
                        "status": "success",
                        "data": {
                            "cpu_usage": 45.2,
                            "memory_usage": 67.8,
                            "disk_usage": 34.1,
                            "network_status": "healthy",
                            "services_status": {
                                "database": "running",
                                "web_server": "running",
                                "monitoring": "running"
                            }
                        }
                    }
                }
            ),
            401: openapi.Response(description="Non authentifié"),
            500: openapi.Response(description="Erreur serveur")
        }
    )
    def get(self, request):
        """Récupère les métriques de santé du système."""
        try:
            # Récupérer le service depuis le conteneur
            dashboard_service = container.get_service('dashboard_service')

            # Wrapper pour appel asynchrone depuis contexte synchrone
            async def get_system_health_async():
                # Récupérer les métriques de santé depuis le service de monitoring
                monitoring_adapter = container.get_service('monitoring_adapter')
                return await monitoring_adapter.get_system_health_metrics()

            # Exécution asynchrone dans contexte synchrone
            health_metrics = asyncio.run(get_system_health_async())

            # Sérialisation sécurisée
            safe_data = {
                'cpu_usage': getattr(health_metrics, 'cpu_usage', 0),
                'memory_usage': getattr(health_metrics, 'memory_usage', 0),
                'disk_usage': getattr(health_metrics, 'disk_usage', 0),
                'network_status': getattr(health_metrics, 'network_status', 'unknown'),
                'services_status': getattr(health_metrics, 'services_status', {})
            }

            # Renvoyer les métriques
            return Response({
                'status': 'success',
                'data': safe_data
            }, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des métriques de santé: {e}")
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DeviceMetricsView(APIView):
    """
    Vue API pour récupérer les métriques d'un équipement spécifique.

    Fournit les métriques détaillées d'un équipement réseau
    incluant performances, statut et historique.
    """
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Récupère les métriques d'un équipement spécifique",
        operation_summary="Métriques d'équipement",
        tags=['Dashboard'],
        manual_parameters=[
            openapi.Parameter(
                'device_id',
                openapi.IN_PATH,
                description="ID de l'équipement",
                type=openapi.TYPE_INTEGER,
                required=True
            )
        ],
        responses={
            200: openapi.Response(
                description="Métriques de l'équipement récupérées avec succès",
                examples={
                    "application/json": {
                        "status": "success",
                        "data": {
                            "device_id": 1,
                            "name": "Router-01",
                            "cpu_usage": 23.5,
                            "memory_usage": 45.2,
                            "interface_stats": {
                                "eth0": {"rx_bytes": 1024000, "tx_bytes": 512000}
                            },
                            "uptime": 86400,
                            "last_seen": "2025-06-29T12:00:00Z"
                        }
                    }
                }
            ),
            401: openapi.Response(description="Non authentifié"),
            404: openapi.Response(description="Équipement non trouvé"),
            500: openapi.Response(description="Erreur serveur")
        }
    )
    def get(self, request, device_id):
        """Récupère les métriques d'un équipement spécifique."""
        try:
            # Récupérer le service depuis le conteneur
            monitoring_adapter = container.get_service('monitoring_adapter')

            # Wrapper pour appel asynchrone depuis contexte synchrone
            async def get_device_metrics_async():
                return await monitoring_adapter.get_device_metrics(device_id)

            # Exécution asynchrone dans contexte synchrone
            metrics = asyncio.run(get_device_metrics_async())

            # Renvoyer les métriques
            return Response({
                'status': 'success',
                'data': metrics
            }, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des métriques de l'équipement {device_id}: {e}")
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)