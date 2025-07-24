"""
Vues API pour le module api_clients.

Ce module expose tous les clients API du système de gestion réseau
avec une documentation Swagger générée automatiquement.
"""

import logging
from typing import Dict, Any, List

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

# Import des clients
from .network.gns3_client import GNS3Client
from .network.snmp_client import SNMPClient, SNMPCredentials, SNMPVersion
from .network.netflow_client import NetflowClient
from .monitoring.prometheus_client import PrometheusClient
from .monitoring.grafana_client import GrafanaClient
from .monitoring.elasticsearch_client import ElasticsearchClient
from .monitoring.netdata_client import NetdataClient
from .monitoring.ntopng_client import NtopngClient
from .infrastructure.haproxy_client import HAProxyClient
from .security.fail2ban_client import Fail2BanClient
from .security.suricata_client import SuricataClient

# Import des serializers
from .serializers import (
    GNS3ProjectSerializer, GNS3NodeSerializer,
    SNMPRequestSerializer, SNMPSetRequestSerializer, SNMPResponseSerializer,
    NetflowAnalysisSerializer,
    PrometheusQuerySerializer, PrometheusResponseSerializer,
    GrafanaDashboardSerializer,
    ElasticsearchQuerySerializer,
    NetdataMetricsSerializer,
    HAProxyStatsSerializer,
    Fail2BanActionSerializer,
    SuricataRuleActionSerializer,
    ClientHealthSerializer,
    ErrorResponseSerializer,
    SuccessResponseSerializer,
    ClientStatusSerializer,
    NetworkClientSerializer,
    MonitoringClientSerializer,
    InfrastructureClientSerializer
)

# Import des utilitaires Swagger
from .utils.swagger_utils import auto_schema_viewset

logger = logging.getLogger(__name__)


# ============================================================================
# VIEWSETS POUR LES CLIENTS RÉSEAU
# ============================================================================

@auto_schema_viewset
class NetworkClientsViewSet(viewsets.ViewSet):
    """
    ViewSet pour les clients réseau (GNS3, SNMP, Netflow).
    
    Ce ViewSet expose les fonctionnalités des clients réseau avec
    documentation Swagger automatique.
    """
    permission_classes = [AllowAny]
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        try:
            # Initialiser les clients avec des paramètres par défaut
            self.gns3_client = GNS3Client()
            
            # SNMP avec configuration par défaut
            snmp_credentials = SNMPCredentials(
                version=SNMPVersion.V2C,
                community="public"
            )
            self.snmp_client = SNMPClient(
                host="localhost",  # Hôte par défaut, sera remplacé par les paramètres de requête
                credentials=snmp_credentials
            )
            
            # NetFlow avec configuration par défaut
            self.netflow_client = NetflowClient(
                base_url="http://localhost:9995/api/v1",  # ElastiFlow par défaut
                collector_host="localhost",
                collector_port=2055
            )
            
            logger.info("Clients réseau initialisés avec succès")
        except Exception as e:
            logger.error(f"Erreur lors de l'initialisation des clients réseau: {e}")
            # Initialiser avec des clients None pour éviter les erreurs
            self.gns3_client = None
            self.snmp_client = None
            self.netflow_client = None
    
    @swagger_auto_schema(
        operation_summary="Liste des clients réseau disponibles",
        operation_description="Retourne la liste des clients réseau et leur statut",
        responses={200: ClientHealthSerializer}
    )
    def list(self, request):
        """Liste des clients réseau disponibles."""
        clients_data = []
        
        # Client GNS3
        if self.gns3_client:
            try:
                gns3_available = self.gns3_client.is_available()
                clients_data.append({
                    "name": "GNS3",
                    "type": "network_simulation",
                    "status": "available" if gns3_available else "unavailable",
                    "url": getattr(self.gns3_client, 'base_url', 'http://localhost:3080'),
                    "description": "Simulateur réseau GNS3"
                })
            except Exception as e:
                logger.error(f"Erreur GNS3: {e}")
                clients_data.append({
                    "name": "GNS3",
                    "type": "network_simulation", 
                    "status": "error",
                    "error": str(e),
                    "description": "Simulateur réseau GNS3"
                })
        
        # Client SNMP
        if self.snmp_client:
            try:
                snmp_available = self.snmp_client.test_connection()
                clients_data.append({
                    "name": "SNMP",
                    "type": "network_monitoring",
                    "status": "available" if snmp_available else "unavailable",
                    "host": self.snmp_client.host,
                    "port": self.snmp_client.port,
                    "description": "Client SNMP pour monitoring réseau"
                })
            except Exception as e:
                logger.error(f"Erreur SNMP: {e}")
                clients_data.append({
                    "name": "SNMP",
                    "type": "network_monitoring",
                    "status": "error", 
                    "error": str(e),
                    "description": "Client SNMP pour monitoring réseau"
                })
        
        # Client NetFlow
        if self.netflow_client:
            try:
                netflow_available = self.netflow_client.test_connection()
                clients_data.append({
                    "name": "NetFlow",
                    "type": "traffic_analysis",
                    "status": "available" if netflow_available else "unavailable",
                    "url": getattr(self.netflow_client, 'base_url', 'http://localhost:9995'),
                    "description": "Analyseur de flux NetFlow"
                })
            except Exception as e:
                logger.error(f"Erreur NetFlow: {e}")
                clients_data.append({
                    "name": "NetFlow",
                    "type": "traffic_analysis",
                    "status": "error",
                    "error": str(e),
                    "description": "Analyseur de flux NetFlow"
                })
        
        return Response({
            "success": True,
            "count": len(clients_data),
            "clients": clients_data
        })
    
    # Actions GNS3
    @action(detail=False, methods=['get'], url_path='gns3/projects')
    @swagger_auto_schema(
        operation_summary="Liste des projets GNS3",
        operation_description="Récupère tous les projets GNS3 disponibles",
        responses={200: GNS3ProjectSerializer(many=True)}
    )
    def gns3_projects(self, request):
        """Liste tous les projets GNS3."""
        if not self.gns3_client:
            return Response({
                "success": False,
                "error": "Client GNS3 non initialisé"
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        
        try:
            projects = self.gns3_client.get_projects()
            return Response(projects)
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des projets GNS3: {e}")
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'], url_path='gns3/projects/(?P<project_id>[^/.]+)')
    @swagger_auto_schema(
        operation_summary="Détails d'un projet GNS3",
        operation_description="Récupère les détails d'un projet GNS3 spécifique",
        responses={200: GNS3ProjectSerializer}
    )
    def gns3_project_detail(self, request, project_id=None):
        """Récupère les détails d'un projet GNS3."""
        if not self.gns3_client:
            return Response({
                "success": False,
                "error": "Client GNS3 non initialisé"
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        
        try:
            project = self.gns3_client.get_project(project_id)
            return Response(project)
        except Exception as e:
            logger.error(f"Erreur lors de la récupération du projet GNS3 {project_id}: {e}")
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'], url_path='gns3/projects/(?P<project_id>[^/.]+)/nodes')
    @swagger_auto_schema(
        operation_summary="Nœuds d'un projet GNS3",
        operation_description="Récupère tous les nœuds d'un projet GNS3",
        responses={200: GNS3NodeSerializer(many=True)}
    )
    def gns3_project_nodes(self, request, project_id=None):
        """Liste les nœuds d'un projet GNS3."""
        if not self.gns3_client:
            return Response({
                "success": False,
                "error": "Client GNS3 non initialisé"
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        
        try:
            nodes = self.gns3_client.get_nodes(project_id)
            return Response(nodes)
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des nœuds du projet {project_id}: {e}")
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    # Actions SNMP
    @action(detail=False, methods=['post'], url_path='snmp/query')
    @swagger_auto_schema(
        operation_summary="Requête SNMP GET",
        operation_description="Effectue une requête SNMP GET sur un périphérique",
        request_body=SNMPRequestSerializer,
        responses={200: SNMPResponseSerializer}
    )
    def snmp_query(self, request):
        """Effectue une requête SNMP GET."""
        if not self.snmp_client:
            return Response({
                "success": False,
                "error": "Client SNMP non initialisé"
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        
        serializer = SNMPRequestSerializer(data=request.data)
        if serializer.is_valid():
            try:
                result = self.snmp_client.get(
                    host=serializer.validated_data['host'],
                    oid=serializer.validated_data['oid'],
                    community=serializer.validated_data.get('community', 'public')
                )
                return Response(result)
            except Exception as e:
                logger.error(f"Erreur SNMP: {e}")
                return Response(
                    {'error': str(e)}, 
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'], url_path='snmp/set')
    @swagger_auto_schema(
        operation_summary="Requête SNMP SET",
        operation_description="Effectue une requête SNMP SET sur un périphérique",
        request_body=SNMPSetRequestSerializer,
        responses={200: SuccessResponseSerializer}
    )
    def snmp_set(self, request):
        """Effectue une requête SNMP SET."""
        if not self.snmp_client:
            return Response({
                "success": False,
                "error": "Client SNMP non initialisé"
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        
        serializer = SNMPSetRequestSerializer(data=request.data)
        if serializer.is_valid():
            try:
                result = self.snmp_client.set(
                    host=serializer.validated_data['host'],
                    oid=serializer.validated_data['oid'],
                    value=serializer.validated_data['value'],
                    value_type=serializer.validated_data['type'],
                    community=serializer.validated_data.get('community', 'public')
                )
                return Response(result)
            except Exception as e:
                logger.error(f"Erreur SNMP SET: {e}")
                return Response(
                    {'error': str(e)}, 
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    # Actions Netflow
    @action(detail=False, methods=['get'], url_path='netflow/analysis')
    @swagger_auto_schema(
        operation_summary="Analyse Netflow",
        operation_description="Récupère l'analyse des flux réseau Netflow",
        responses={200: NetflowAnalysisSerializer}
    )
    def netflow_analysis(self, request):
        """Récupère l'analyse Netflow."""
        if not self.netflow_client:
            return Response({
                "success": False,
                "error": "Client NetFlow non initialisé"
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        
        try:
            analysis = self.netflow_client.analyze_flows()
            return Response(analysis)
        except Exception as e:
            logger.error(f"Erreur analyse Netflow: {e}")
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# ============================================================================
# VIEWSETS POUR LES CLIENTS MONITORING
# ============================================================================

@auto_schema_viewset
class MonitoringClientsViewSet(viewsets.ViewSet):
    """
    ViewSet pour les clients de monitoring (Prometheus, Grafana, etc.).
    
    Ce ViewSet expose les fonctionnalités des clients de monitoring avec
    documentation Swagger automatique.
    """
    permission_classes = [AllowAny]
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        try:
            # Initialiser les clients de monitoring avec des paramètres par défaut
            self.prometheus_client = PrometheusClient(base_url="http://localhost:9090/api/v1")
            self.grafana_client = GrafanaClient(base_url="http://localhost:3000/api")
            self.elasticsearch_client = ElasticsearchClient(base_url="http://localhost:9200")
            self.netdata_client = NetdataClient(base_url="http://localhost:19999/api/v1")
            self.ntopng_client = NtopngClient(base_url="http://localhost:3001")
            
            logger.info("Clients de monitoring initialisés avec succès")
        except Exception as e:
            logger.error(f"Erreur lors de l'initialisation des clients de monitoring: {e}")
            # Initialiser avec des clients None pour éviter les erreurs
            self.prometheus_client = None
            self.grafana_client = None
            self.elasticsearch_client = None
            self.netdata_client = None
            self.ntopng_client = None
    
    @swagger_auto_schema(
        operation_summary="Liste des clients monitoring disponibles",
        operation_description="Retourne la liste des clients monitoring et leur statut",
        responses={200: ClientHealthSerializer}
    )
    def list(self, request):
        """Liste des clients monitoring disponibles."""
        clients_data = []
        
        # Prometheus
        if self.prometheus_client:
            try:
                prometheus_available = self.prometheus_client.test_connection()
                clients_data.append({
                    "name": "Prometheus",
                    "type": "metrics_collection",
                    "status": "available" if prometheus_available else "unavailable",
                    "url": getattr(self.prometheus_client, 'base_url', 'http://localhost:9090'),
                    "description": "Système de monitoring et d'alerting"
                })
            except Exception as e:
                clients_data.append({
                    "name": "Prometheus",
                    "type": "metrics_collection",
                    "status": "error",
                    "error": str(e),
                    "description": "Système de monitoring et d'alerting"
                })
        
        # Grafana
        if self.grafana_client:
            try:
                grafana_available = self.grafana_client.test_connection()
                clients_data.append({
                    "name": "Grafana",
                    "type": "visualization",
                    "status": "available" if grafana_available else "unavailable",
                    "url": getattr(self.grafana_client, 'base_url', 'http://localhost:3000'),
                    "description": "Plateforme de visualisation et de dashboards"
                })
            except Exception as e:
                clients_data.append({
                    "name": "Grafana",
                    "type": "visualization", 
                    "status": "error",
                    "error": str(e),
                    "description": "Plateforme de visualisation et de dashboards"
                })
        
        # Elasticsearch
        if self.elasticsearch_client:
            try:
                elasticsearch_available = self.elasticsearch_client.test_connection()
                clients_data.append({
                    "name": "Elasticsearch",
                    "type": "search_analytics",
                    "status": "available" if elasticsearch_available else "unavailable",
                    "url": getattr(self.elasticsearch_client, 'base_url', 'http://localhost:9200'),
                    "description": "Moteur de recherche et d'analyse"
                })
            except Exception as e:
                clients_data.append({
                    "name": "Elasticsearch",
                    "type": "search_analytics",
                    "status": "error",
                    "error": str(e),
                    "description": "Moteur de recherche et d'analyse"
                })
        
        return Response({
            "success": True,
            "count": len(clients_data),
            "clients": clients_data
        })
    
    # Actions Prometheus
    @action(detail=False, methods=['post'], url_path='prometheus/query')
    @swagger_auto_schema(
        operation_summary="Requête Prometheus",
        operation_description="Effectue une requête PromQL sur Prometheus",
        request_body=PrometheusQuerySerializer,
        responses={200: PrometheusResponseSerializer}
    )
    def prometheus_query(self, request):
        """Effectue une requête Prometheus."""
        if not self.prometheus_client:
            return Response({
                "success": False,
                "error": "Client Prometheus non initialisé"
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        
        serializer = PrometheusQuerySerializer(data=request.data)
        if serializer.is_valid():
            try:
                result = self.prometheus_client.query(
                    query=serializer.validated_data['query'],
                    time=serializer.validated_data.get('time')
                )
                return Response(result)
            except Exception as e:
                logger.error(f"Erreur Prometheus: {e}")
                return Response(
                    {'error': str(e)}, 
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    # Actions Grafana
    @action(detail=False, methods=['get'], url_path='grafana/dashboards')
    @swagger_auto_schema(
        operation_summary="Liste des dashboards Grafana",
        operation_description="Récupère tous les dashboards Grafana",
        responses={200: GrafanaDashboardSerializer(many=True)}
    )
    def grafana_dashboards(self, request):
        """Liste les dashboards Grafana."""
        if not self.grafana_client:
            return Response({
                "success": False,
                "error": "Client Grafana non initialisé"
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        
        try:
            dashboards = self.grafana_client.get_dashboards()
            return Response(dashboards)
        except Exception as e:
            logger.error(f"Erreur Grafana: {e}")
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    # Actions Elasticsearch
    @action(detail=False, methods=['post'], url_path='elasticsearch/search')
    @swagger_auto_schema(
        operation_summary="Recherche Elasticsearch",
        operation_description="Effectue une recherche dans Elasticsearch",
        request_body=ElasticsearchQuerySerializer,
        responses={200: openapi.Response(description="Résultats de recherche")}
    )
    def elasticsearch_search(self, request):
        """Recherche dans Elasticsearch."""
        if not self.elasticsearch_client:
            return Response({
                "success": False,
                "error": "Client Elasticsearch non initialisé"
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        
        serializer = ElasticsearchQuerySerializer(data=request.data)
        if serializer.is_valid():
            try:
                result = self.elasticsearch_client.search(
                    index=serializer.validated_data['index'],
                    query=serializer.validated_data['query'],
                    size=serializer.validated_data.get('size', 10)
                )
                return Response(result)
            except Exception as e:
                logger.error(f"Erreur Elasticsearch: {e}")
                return Response(
                    {'error': str(e)}, 
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    # Actions Netdata
    @action(detail=False, methods=['get'], url_path='netdata/metrics')
    @swagger_auto_schema(
        operation_summary="Métriques Netdata",
        operation_description="Récupère les métriques Netdata",
        responses={200: NetdataMetricsSerializer}
    )
    def netdata_metrics(self, request):
        """Récupère les métriques Netdata."""
        if not self.netdata_client:
            return Response({
                "success": False,
                "error": "Client Netdata non initialisé"
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        
        try:
            metrics = self.netdata_client.get_metrics()
            return Response(metrics)
        except Exception as e:
            logger.error(f"Erreur Netdata: {e}")
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# ============================================================================
# VIEWSETS POUR LES CLIENTS INFRASTRUCTURE
# ============================================================================

@auto_schema_viewset
class InfrastructureClientsViewSet(viewsets.ViewSet):
    """
    ViewSet pour les clients d'infrastructure (HAProxy, Fail2Ban, etc.).
    
    Ce ViewSet expose les fonctionnalités des clients d'infrastructure avec
    documentation Swagger automatique.
    """
    permission_classes = [AllowAny]
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        try:
            # Initialiser les clients d'infrastructure avec des paramètres par défaut
            self.haproxy_client = HAProxyClient(base_url="http://localhost:8404/stats")
            self.fail2ban_client = Fail2BanClient()
            self.suricata_client = SuricataClient()
            
            logger.info("Clients d'infrastructure initialisés avec succès")
        except Exception as e:
            logger.error(f"Erreur lors de l'initialisation des clients d'infrastructure: {e}")
            self.haproxy_client = None
            self.fail2ban_client = None
            self.suricata_client = None
    
    @swagger_auto_schema(
        operation_summary="Liste des clients infrastructure disponibles",
        operation_description="Retourne la liste des clients infrastructure et leur statut",
        responses={200: ClientHealthSerializer}
    )
    def list(self, request):
        """Liste des clients infrastructure disponibles."""
        clients_data = []
        
        # HAProxy
        if self.haproxy_client:
            try:
                haproxy_available = self.haproxy_client.test_connection()
                clients_data.append({
                    "name": "HAProxy",
                    "type": "load_balancer",
                    "status": "available" if haproxy_available else "unavailable",
                    "url": getattr(self.haproxy_client, 'base_url', 'http://localhost:8404'),
                    "description": "Load balancer et proxy HTTP"
                })
            except Exception as e:
                clients_data.append({
                    "name": "HAProxy",
                    "type": "load_balancer",
                    "status": "error",
                    "error": str(e),
                    "description": "Load balancer et proxy HTTP"
                })
        
        # Fail2Ban
        if self.fail2ban_client:
            try:
                fail2ban_available = self.fail2ban_client.test_connection()
                clients_data.append({
                    "name": "Fail2Ban",
                    "type": "intrusion_prevention",
                    "status": "available" if fail2ban_available else "unavailable",
                    "description": "Système de prévention d'intrusion"
                })
            except Exception as e:
                clients_data.append({
                    "name": "Fail2Ban",
                    "type": "intrusion_prevention",
                    "status": "error",
                    "error": str(e),
                    "description": "Système de prévention d'intrusion"
                })
        
        return Response({
            "success": True,
            "count": len(clients_data),
            "clients": clients_data
        })
    
    # Actions HAProxy
    @action(detail=False, methods=['get'], url_path='haproxy/stats')
    @swagger_auto_schema(
        operation_summary="Statistiques HAProxy",
        operation_description="Récupère les statistiques HAProxy",
        responses={200: HAProxyStatsSerializer}
    )
    def haproxy_stats(self, request):
        """Récupère les statistiques HAProxy."""
        if not self.haproxy_client:
            return Response({
                "success": False,
                "error": "Client HAProxy non initialisé"
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        
        try:
            stats = self.haproxy_client.get_stats()
            return Response(stats)
        except Exception as e:
            logger.error(f"Erreur HAProxy: {e}")
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    # Actions Fail2Ban
    @action(detail=False, methods=['post'], url_path='fail2ban/action')
    @swagger_auto_schema(
        operation_summary="Action Fail2Ban",
        operation_description="Effectue une action Fail2Ban (ban, unban, status)",
        request_body=Fail2BanActionSerializer,
        responses={200: SuccessResponseSerializer}
    )
    def fail2ban_action(self, request):
        """Effectue une action Fail2Ban."""
        if not self.fail2ban_client:
            return Response({
                "success": False,
                "error": "Client Fail2Ban non initialisé"
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        
        serializer = Fail2BanActionSerializer(data=request.data)
        if serializer.is_valid():
            try:
                action = serializer.validated_data['action']
                ip = serializer.validated_data['ip']
                jail = serializer.validated_data.get('jail', 'sshd')
                
                if action == 'ban':
                    result = self.fail2ban_client.ban_ip(ip, jail)
                elif action == 'unban':
                    result = self.fail2ban_client.unban_ip(ip, jail)
                elif action == 'status':
                    result = self.fail2ban_client.get_status(jail)
                else:
                    return Response(
                        {'error': 'Action non supportée'}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                return Response(result)
            except Exception as e:
                logger.error(f"Erreur Fail2Ban: {e}")
                return Response(
                    {'error': str(e)}, 
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    # Actions Suricata
    @action(detail=False, methods=['post'], url_path='suricata/rules')
    @swagger_auto_schema(
        operation_summary="Gestion des règles Suricata",
        operation_description="Gère les règles Suricata (list, add, remove, reload)",
        request_body=SuricataRuleActionSerializer,
        responses={200: SuccessResponseSerializer}
    )
    def suricata_rules(self, request):
        """Gère les règles Suricata."""
        if not self.suricata_client:
            return Response({
                "success": False,
                "error": "Client Suricata non initialisé"
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        
        serializer = SuricataRuleActionSerializer(data=request.data)
        if serializer.is_valid():
            try:
                action = serializer.validated_data['action']
                
                if action == 'list':
                    result = self.suricata_client.list_rules()
                elif action == 'add':
                    rule = serializer.validated_data.get('rule')
                    if not rule:
                        return Response(
                            {'error': 'Règle requise pour l\'action add'}, 
                            status=status.HTTP_400_BAD_REQUEST
                        )
                    result = self.suricata_client.add_rule(rule)
                elif action == 'remove':
                    rule_id = serializer.validated_data.get('rule_id')
                    if not rule_id:
                        return Response(
                            {'error': 'ID de règle requis pour l\'action remove'}, 
                            status=status.HTTP_400_BAD_REQUEST
                        )
                    result = self.suricata_client.remove_rule(rule_id)
                elif action == 'reload':
                    result = self.suricata_client.reload_rules()
                else:
                    return Response(
                        {'error': 'Action non supportée'}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                return Response(result)
            except Exception as e:
                logger.error(f"Erreur Suricata: {e}")
                return Response(
                    {'error': str(e)}, 
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ============================================================================
# VUES UTILITAIRES
# ============================================================================

@auto_schema_viewset
class ClientUtilsViewSet(viewsets.ViewSet):
    """
    ViewSet pour les utilitaires des clients API.
    
    Ce ViewSet expose des fonctionnalités utilitaires communes à tous les clients.
    """
    permission_classes = [AllowAny]
    
    @swagger_auto_schema(
        operation_summary="Santé globale des clients",
        operation_description="Vérifie l'état de santé de tous les clients API",
        responses={200: ClientHealthSerializer}
    )
    def list(self, request):
        """Vérifie l'état de santé de tous les clients."""
        # Initialiser tous les clients
        clients = {
            'network': {
                'gns3': GNS3Client().is_available(),
                'snmp': SNMPClient().is_available(),
                'netflow': NetflowClient().is_available()
            },
            'monitoring': {
                'prometheus': PrometheusClient().is_available(),
                'grafana': GrafanaClient().is_available(),
                'elasticsearch': ElasticsearchClient().is_available(),
                'netdata': NetdataClient().is_available(),
                'ntopng': NtopngClient().is_available()
            },
            'infrastructure': {
                'haproxy': HAProxyClient().is_available(),
                'fail2ban': Fail2BanClient().is_available(),
                'suricata': SuricataClient().is_available()
            }
        }
        
        # Calculer les statistiques
        total_clients = sum(len(category) for category in clients.values())
        healthy_clients = sum(
            sum(1 for status in category.values() if status)
            for category in clients.values()
        )
        
        return Response({
            'clients': clients,
            'total_clients': total_clients,
            'healthy_clients': healthy_clients
        })
    
    @action(detail=False, methods=['get'], url_path='swagger-json')
    @swagger_auto_schema(
        operation_summary="Documentation Swagger JSON",
        operation_description="Retourne la documentation Swagger au format JSON",
        responses={200: openapi.Response(description="Documentation Swagger")}
    )
    def swagger_json(self, request):
        """Retourne la documentation Swagger au format JSON."""
        try:
            # Génération de la documentation Swagger pour tous les clients
            from .docs.generate_all_swagger import generate_swagger_for_all_clients
            generate_swagger_for_all_clients()
            
            return Response({
                'status': 'success',
                'message': 'Documentation Swagger générée',
                'swagger_files': [
                    'gns3client_swagger.json',
                    'snmpclient_swagger.json',
                    'netflowclient_swagger.json',
                    'prometheusclient_swagger.json',
                    'grafanaclient_swagger.json',
                    'elasticsearchclient_swagger.json',
                    'netdataclient_swagger.json',
                    'ntopngclient_swagger.json',
                    'haproxyclient_swagger.json',
                    'fail2banclient_swagger.json',
                    'suricataclient_swagger.json'
                ]
            })
        except Exception as e:
            logger.error(f"Erreur génération Swagger: {e}")
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @swagger_auto_schema(
        operation_description="Santé globale de tous les clients API",
        responses={200: openapi.Schema(type=openapi.TYPE_OBJECT)}
    )
    @action(detail=False, methods=['get'])
    def health(self, request):
        """Vérification de santé globale de tous les clients."""
        health_data = {
            "success": True,
            "timestamp": "2025-01-01T00:00:00Z",
            "clients": {
                "network": {},
                "monitoring": {},
                "infrastructure": {}
            }
        }
        
        try:
            # Test des clients réseau
            network_viewset = NetworkClientsViewSet()
            network_response = network_viewset.list(request)
            if network_response.status_code == 200:
                health_data["clients"]["network"] = network_response.data
            
            # Test des clients de monitoring
            monitoring_viewset = MonitoringClientsViewSet()
            monitoring_response = monitoring_viewset.list(request)
            if monitoring_response.status_code == 200:
                health_data["clients"]["monitoring"] = monitoring_response.data
            
            # Test des clients d'infrastructure
            infrastructure_viewset = InfrastructureClientsViewSet()
            infrastructure_response = infrastructure_viewset.list(request)
            if infrastructure_response.status_code == 200:
                health_data["clients"]["infrastructure"] = infrastructure_response.data
            
        except Exception as e:
            logger.error(f"Erreur lors du check de santé: {e}")
            health_data["success"] = False
            health_data["error"] = str(e)
        
        return Response(health_data)

    @swagger_auto_schema(
        operation_description="Configuration des clients API",
        responses={200: openapi.Schema(type=openapi.TYPE_OBJECT)}
    )
    @action(detail=False, methods=['get'])
    def config(self, request):
        """Configuration actuelle des clients API."""
        return Response({
            "success": True,
            "config": {
                "network": {
                    "gns3_url": "http://localhost:3080",
                    "snmp_default_community": "public",
                    "netflow_url": "http://localhost:9995"
                },
                "monitoring": {
                    "prometheus_url": "http://localhost:9090",
                    "grafana_url": "http://localhost:3000",
                    "elasticsearch_url": "http://localhost:9200"
                },
                "infrastructure": {
                    "haproxy_stats_url": "http://localhost:8404/stats"
                }
            }
        }) 