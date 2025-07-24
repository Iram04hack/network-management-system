"""
Vues API pour le Service Central de Topologie.

Ce module expose les fonctionnalités du service central de topologie
via des ViewSets DRF avec documentation Swagger complète.
"""

import logging
import asyncio
from typing import Dict, Any
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication, SessionAuthentication
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

logger = logging.getLogger(__name__)


class NetworkTopologyViewSet(viewsets.ViewSet):
    """
    ViewSet pour le Service Central de Topologie.
    
    Fournit les endpoints pour la découverte réseau, synchronisation GNS3
    et gestion centralisée de la topologie réseau.
    """
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_summary="Résumé de la topologie réseau",
        operation_description="Récupère un résumé complet de la topologie réseau",
        tags=['Network Management'],
        responses={
            200: openapi.Response(
                description="Résumé de la topologie",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'devices_total': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'devices_managed': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'devices_monitored': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'devices_online': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'interfaces_total': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'topologies_total': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'gns3_devices': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'discovered_devices': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'device_types': openapi.Schema(type=openapi.TYPE_OBJECT),
                        'vendors': openapi.Schema(type=openapi.TYPE_OBJECT),
                        'last_discovery': openapi.Schema(type=openapi.TYPE_STRING),
                        'last_gns3_sync': openapi.Schema(type=openapi.TYPE_STRING)
                    }
                )
            ),
            500: "Erreur interne du serveur"
        }
    )
    def list(self, request: Request) -> Response:
        """Récupère le résumé de la topologie réseau."""
        try:
            from ..services.topology_service import topology_service
            
            summary = topology_service.get_topology_summary()
            return Response(summary, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération du résumé de topologie: {e}")
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @swagger_auto_schema(
        method='post',
        operation_summary="Synchronisation avec GNS3",
        operation_description="Lance une synchronisation avec le serveur GNS3",
        tags=['Network Management'],
        manual_parameters=[
            openapi.Parameter(
                'force_sync',
                openapi.IN_QUERY,
                description="Force la synchronisation même si GNS3 n'est pas disponible",
                type=openapi.TYPE_BOOLEAN,
                default=False
            )
        ],
        responses={
            200: openapi.Response(
                description="Résultat de la synchronisation",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'success': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                        'devices_synced': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'interfaces_synced': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'topologies_synced': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'gns3_available': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                        'errors': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_STRING)),
                        'sync_timestamp': openapi.Schema(type=openapi.TYPE_STRING)
                    }
                )
            ),
            500: "Erreur interne du serveur"
        }
    )
    @action(detail=False, methods=['post'])
    def sync_gns3(self, request: Request) -> Response:
        """Lance la synchronisation avec GNS3."""
        try:
            from ..services.topology_service import topology_service
            
            force_sync = request.query_params.get('force_sync', 'false').lower() == 'true'
            
            # Exécuter la synchronisation de manière asynchrone
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                sync_result = loop.run_until_complete(
                    topology_service.sync_with_gns3(force_sync)
                )
            finally:
                loop.close()
            
            return Response(sync_result, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Erreur lors de la synchronisation GNS3: {e}")
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @swagger_auto_schema(
        method='post',
        operation_summary="Découverte automatique du réseau",
        operation_description="Lance la découverte automatique des équipements réseau",
        tags=['Network Management'],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'scan_ranges': openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(type=openapi.TYPE_STRING),
                    description="Plages IP à scanner (ex: ['192.168.1.0/24'])"
                )
            }
        ),
        responses={
            200: openapi.Response(
                description="Résultat de la découverte",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'success': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                        'devices_discovered': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'devices_updated': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'scan_ranges': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_STRING)),
                        'discovery_methods': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_STRING)),
                        'errors': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_STRING)),
                        'timestamp': openapi.Schema(type=openapi.TYPE_STRING)
                    }
                )
            ),
            500: "Erreur interne du serveur"
        }
    )
    @action(detail=False, methods=['post'])
    def discover_network(self, request: Request) -> Response:
        """Lance la découverte automatique du réseau."""
        try:
            from ..services.topology_service import topology_service
            
            scan_ranges = request.data.get('scan_ranges', [])
            
            # Exécuter la découverte de manière asynchrone
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                discovery_result = loop.run_until_complete(
                    topology_service.discover_network_devices(scan_ranges)
                )
            finally:
                loop.close()
            
            return Response(discovery_result, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Erreur lors de la découverte réseau: {e}")
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @swagger_auto_schema(
        method='get',
        operation_summary="Équipements pour un module spécifique",
        operation_description="Récupère les équipements filtrés pour un module spécifique",
        tags=['Network Management'],
        manual_parameters=[
            openapi.Parameter(
                'module',
                openapi.IN_QUERY,
                description="Nom du module (monitoring, dashboard, ai_assistant, etc.)",
                type=openapi.TYPE_STRING,
                required=True
            ),
            openapi.Parameter(
                'device_type',
                openapi.IN_QUERY,
                description="Type d'équipement à filtrer",
                type=openapi.TYPE_STRING,
                required=False
            ),
            openapi.Parameter(
                'status',
                openapi.IN_QUERY,
                description="Statut des équipements à filtrer",
                type=openapi.TYPE_STRING,
                required=False
            )
        ],
        responses={
            200: openapi.Response(
                description="Liste des équipements filtrés",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'module': openapi.Schema(type=openapi.TYPE_STRING),
                        'devices_count': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'devices': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_OBJECT))
                    }
                )
            ),
            400: "Paramètres invalides",
            500: "Erreur interne du serveur"
        }
    )
    @action(detail=False, methods=['get'])
    def devices_for_module(self, request: Request) -> Response:
        """Récupère les équipements pour un module spécifique."""
        try:
            from ..services.topology_service import topology_service
            from .serializers import DeviceSerializer
            
            module_name = request.query_params.get('module')
            if not module_name:
                return Response(
                    {'error': 'Le paramètre "module" est requis'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Construire les filtres supplémentaires
            device_filter = {}
            if request.query_params.get('device_type'):
                device_filter['device_type'] = request.query_params.get('device_type')
            if request.query_params.get('status'):
                device_filter['status'] = request.query_params.get('status')
            
            # Récupérer les équipements
            devices = topology_service.get_devices_for_module(module_name, device_filter)
            
            # Sérialiser les résultats
            serializer = DeviceSerializer(devices, many=True)
            
            return Response({
                'module': module_name,
                'devices_count': len(devices),
                'devices': serializer.data,
                'filters_applied': device_filter
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des équipements pour module: {e}")
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @swagger_auto_schema(
        method='get',
        operation_summary="Statut de santé de la topologie",
        operation_description="Vérifie la santé globale de la topologie réseau",
        tags=['Network Management'],
        responses={
            200: openapi.Response(
                description="Statut de santé",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'overall_health': openapi.Schema(type=openapi.TYPE_STRING),
                        'health_score': openapi.Schema(type=openapi.TYPE_NUMBER),
                        'gns3_available': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                        'devices_online_percentage': openapi.Schema(type=openapi.TYPE_NUMBER),
                        'critical_issues': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_STRING)),
                        'recommendations': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_STRING)),
                        'last_check': openapi.Schema(type=openapi.TYPE_STRING)
                    }
                )
            ),
            500: "Erreur interne du serveur"
        }
    )
    @action(detail=False, methods=['get'])
    def health_status(self, request: Request) -> Response:
        """Vérifie la santé globale de la topologie réseau."""
        try:
            from ..services.topology_service import topology_service
            from gns3_integration.infrastructure.gns3_detection_service import get_gns3_server_status
            from django.utils import timezone
            
            # Récupérer le résumé de la topologie
            summary = topology_service.get_topology_summary()
            
            # Vérifier le statut GNS3
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                gns3_status = loop.run_until_complete(get_gns3_server_status())
            finally:
                loop.close()
            
            # Calculer les métriques de santé
            total_devices = summary.get('devices_total', 0)
            online_devices = summary.get('devices_online', 0)
            online_percentage = (online_devices / total_devices * 100) if total_devices > 0 else 0
            
            # Déterminer la santé globale
            health_score = 0
            critical_issues = []
            recommendations = []
            
            # Score basé sur la disponibilité des équipements
            if online_percentage >= 90:
                health_score += 40
            elif online_percentage >= 70:
                health_score += 25
                critical_issues.append(f"Seulement {online_percentage:.1f}% des équipements sont en ligne")
            else:
                health_score += 10
                critical_issues.append(f"Disponibilité critique: {online_percentage:.1f}% des équipements en ligne")
            
            # Score basé sur GNS3
            if gns3_status.is_available:
                health_score += 30
            else:
                health_score += 0
                critical_issues.append("Serveur GNS3 indisponible")
                recommendations.append("Vérifier la connexion au serveur GNS3")
            
            # Score basé sur la gestion
            managed_percentage = (summary.get('devices_managed', 0) / total_devices * 100) if total_devices > 0 else 0
            if managed_percentage >= 80:
                health_score += 20
            elif managed_percentage >= 50:
                health_score += 10
                recommendations.append("Augmenter le nombre d'équipements gérés")
            else:
                health_score += 0
                critical_issues.append(f"Seulement {managed_percentage:.1f}% des équipements sont gérés")
            
            # Score basé sur la surveillance
            monitored_percentage = (summary.get('devices_monitored', 0) / total_devices > 0) if total_devices > 0 else 0
            if monitored_percentage >= 80:
                health_score += 10
            else:
                recommendations.append("Activer la surveillance pour plus d'équipements")
            
            # Déterminer le statut global
            if health_score >= 80:
                overall_health = "healthy"
            elif health_score >= 60:
                overall_health = "warning"
            else:
                overall_health = "critical"
            
            # Recommandations générales
            if total_devices == 0:
                recommendations.append("Lancer la découverte automatique du réseau")
            elif summary.get('gns3_devices', 0) == 0:
                recommendations.append("Synchroniser avec GNS3 pour importer la topologie")
            
            return Response({
                'overall_health': overall_health,
                'health_score': round(health_score, 1),
                'gns3_available': gns3_status.is_available,
                'devices_online_percentage': round(online_percentage, 1),
                'critical_issues': critical_issues,
                'recommendations': recommendations,
                'last_check': timezone.now().isoformat(),
                'summary': summary
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Erreur lors de la vérification de santé: {e}")
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )