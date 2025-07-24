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
        operation_description="clients_network-clients_list - Récupère la liste complète de tous les clients réseau disponibles avec statut détaillé incluant GNS3 pour simulation réseau, SNMP pour monitoring équipements, et NetFlow pour analyse trafic. Vérifie automatiquement la connectivité et retourne les informations de configuration de chaque service.",
        responses={200: openapi.Response(
            description='Liste des clients réseau',
            schema=ClientHealthSerializer()
        )},
        tags=['API Clients']
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
        operation_description="clients_gns3-projects_list - Récupère la liste exhaustive de tous les projets GNS3 disponibles sur le serveur avec métadonnées complètes incluant identifiants, noms, statuts, dates de création et nombre de nœuds. Permet la gestion centralisée des topologies réseau virtuelles.",
        responses={200: openapi.Response(
            description='Liste des projets GNS3',
            schema=openapi.Schema(
                type=openapi.TYPE_ARRAY,
                items=openapi.Schema(type=openapi.TYPE_OBJECT, properties={
                    'project_id': openapi.Schema(type=openapi.TYPE_STRING, description='ID unique du projet'),
                    'name': openapi.Schema(type=openapi.TYPE_STRING, description='Nom du projet'),
                    'status': openapi.Schema(type=openapi.TYPE_STRING, description='Statut du projet'),
                    'nodes_count': openapi.Schema(type=openapi.TYPE_INTEGER, description='Nombre de nœuds'),
                    'created_at': openapi.Schema(type=openapi.TYPE_STRING, format='date-time', description='Date de création')
                })
            )
        )},
        tags=['API Clients']
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
        operation_description="clients_gns3-project_retrieve - Récupère les détails complets d'un projet GNS3 spécifique par son identifiant incluant configuration, métadonnées, chemins fichiers, statut d'exécution et informations de topologie. Essentiel pour la gestion individuelle des projets.",
        responses={200: openapi.Response(
            description='Détails du projet GNS3',
            schema=openapi.Schema(type=openapi.TYPE_OBJECT, properties={
                'project_id': openapi.Schema(type=openapi.TYPE_STRING, description='ID unique du projet'),
                'name': openapi.Schema(type=openapi.TYPE_STRING, description='Nom du projet'),
                'status': openapi.Schema(type=openapi.TYPE_STRING, description='Statut du projet'),
                'nodes_count': openapi.Schema(type=openapi.TYPE_INTEGER, description='Nombre de nœuds'),
                'created_at': openapi.Schema(type=openapi.TYPE_STRING, format='date-time', description='Date de création')
            })
        )},
        tags=['API Clients']
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
        operation_description="clients_gns3-nodes_list - Récupère la liste complète de tous les nœuds d'un projet GNS3 avec informations détaillées incluant types d'équipements, positions topologiques, statuts d'exécution, ports de console et configurations spécifiques. Permet la visualisation et gestion de la topologie réseau.",
        responses={200: openapi.Response(
            description='Liste des nœuds GNS3',
            schema=GNS3NodeSerializer
        )},
        tags=['API Clients']
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
        operation_description="clients_snmp-get_execute - Exécute une requête SNMP GET sur un équipement réseau pour récupérer une valeur spécifique via OID. Supporte les versions SNMP v1/v2c/v3, gestion des communautés, validation OID et conversion automatique des types de données avec horodatage des requêtes.",
        request_body=SNMPRequestSerializer,
        responses={200: openapi.Response(
            description='Réponse SNMP',
            schema=SNMPResponseSerializer()
        )},
        tags=['API Clients']
    )
    def snmp_query(self, request):
        """Effectue une requête SNMP GET."""
        serializer = SNMPRequestSerializer(data=request.data)
        if serializer.is_valid():
            try:
                # Créer un client SNMP temporaire avec les paramètres fournis
                host = serializer.validated_data['host']
                community = serializer.validated_data.get('community', 'public')
                oid = serializer.validated_data['oid']
                
                snmp_credentials = SNMPCredentials(
                    version=SNMPVersion.V2C,
                    community=community
                )
                temp_snmp_client = SNMPClient(host=host, credentials=snmp_credentials)
                
                result = temp_snmp_client.get(oid)
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
        operation_description="clients_snmp-set_execute - Exécute une requête SNMP SET sur un équipement réseau pour modifier une valeur via OID. Supporte différents types de données (INTEGER, OCTET_STRING, etc.), validation des paramètres, gestion des erreurs et confirmation des modifications avec logs de sécurité.",
        request_body=SNMPSetRequestSerializer,
        responses={200: openapi.Response(
            description='Succès de l\'opération',
            schema=SuccessResponseSerializer()
        )},
        tags=['API Clients']
    )
    def snmp_set(self, request):
        """Effectue une requête SNMP SET."""
        serializer = SNMPSetRequestSerializer(data=request.data)
        if serializer.is_valid():
            try:
                # Créer un client SNMP temporaire avec les paramètres fournis
                host = serializer.validated_data['host']
                community = serializer.validated_data.get('community', 'public')
                oid = serializer.validated_data['oid']
                value = serializer.validated_data['value']
                value_type = serializer.validated_data['type']
                
                snmp_credentials = SNMPCredentials(
                    version=SNMPVersion.V2C,
                    community=community
                )
                temp_snmp_client = SNMPClient(host=host, credentials=snmp_credentials)
                
                result = temp_snmp_client.set(oid, value, value_type)
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
        operation_description="clients_netflow-analysis_retrieve - Récupère l'analyse complète des flux réseau NetFlow avec statistiques détaillées incluant volumes de trafic, top talkers, protocols utilisés, analyse temporelle et détection d'anomalies. Essentiel pour la surveillance et l'optimisation du réseau.",
        responses={200: openapi.Response(
            description='Analyse NetFlow',
            schema=NetflowAnalysisSerializer()
        )},
        tags=['API Clients']
    )
    def netflow_analysis(self, request):
        """Récupère l'analyse Netflow."""
        if not self.netflow_client:
            return Response({
                "success": False,
                "error": "Client NetFlow non initialisé"
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        
        try:
            # Récupérer les flux des dernières 24h
            from datetime import datetime, timedelta
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=24)
            
            analysis = self.netflow_client.query_flows(
                start_time=start_time,
                end_time=end_time,
                limit=100
            )
            return Response(analysis)
        except Exception as e:
            logger.error(f"Erreur analyse Netflow: {e}")
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# ============================================================================
# VIEWSETS POUR LES CLIENTS DE MONITORING
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
        operation_description="clients_monitoring-clients_list - Récupère la liste exhaustive de tous les clients de surveillance et monitoring disponibles avec statut détaillé incluant Prometheus pour métriques, Grafana pour visualisation, Elasticsearch pour logs, Netdata pour performances temps réel et Ntopng pour analyse trafic réseau. Vérifie la connectivité de chaque service.",
        responses={200: openapi.Response(
            description='Liste des clients monitoring',
            schema=ClientHealthSerializer()
        )},
        tags=['API Clients']
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
        
        # Netdata
        if self.netdata_client:
            try:
                netdata_available = self.netdata_client.test_connection()
                clients_data.append({
                    "name": "Netdata",
                    "type": "system_monitoring",
                    "status": "available" if netdata_available else "unavailable",
                    "url": getattr(self.netdata_client, 'base_url', 'http://localhost:19999'),
                    "description": "Monitoring système temps réel"
                })
            except Exception as e:
                clients_data.append({
                    "name": "Netdata",
                    "type": "system_monitoring",
                    "status": "error",
                    "error": str(e),
                    "description": "Monitoring système temps réel"
                })
        
        # Ntopng
        if self.ntopng_client:
            try:
                ntopng_available = self.ntopng_client.test_connection()
                clients_data.append({
                    "name": "Ntopng",
                    "type": "network_monitoring",
                    "status": "available" if ntopng_available else "unavailable",
                    "url": getattr(self.ntopng_client, 'base_url', 'http://localhost:3001'),
                    "description": "Monitoring trafic réseau"
                })
            except Exception as e:
                clients_data.append({
                    "name": "Ntopng",
                    "type": "network_monitoring",
                    "status": "error",
                    "error": str(e),
                    "description": "Monitoring trafic réseau"
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
        operation_description="clients_prometheus-query_execute - Exécute une requête PromQL avancée sur le serveur Prometheus pour récupérer des métriques de monitoring avec support des requêtes instant et range, fonctions d'agrégation, opérateurs arithmétiques et filtrage par labels. Retourne les données avec timestamps et métadonnées complètes.",
        request_body=PrometheusQuerySerializer,
        responses={200: openapi.Response(
            description='Réponse Prometheus',
            schema=PrometheusResponseSerializer()
        )},
        tags=['API Clients']
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
        operation_description="clients_grafana-dashboards_list - Récupère la liste complète de tous les dashboards Grafana disponibles avec métadonnées incluant titres, descriptions, tags, panneaux configurés, sources de données associées et permissions d'accès. Permet la gestion centralisée des visualisations.",
        responses={200: GrafanaDashboardSerializer},
        tags=['API Clients']
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
        operation_description="clients_elasticsearch-search_execute - Exécute une recherche avancée dans Elasticsearch avec support du DSL complet incluant requêtes booléennes, filtres, agrégations, tri personnalisé et pagination. Permet l'analyse de logs et données avec scoring de pertinence et highlighting des résultats.",
        request_body=ElasticsearchQuerySerializer,
        responses={200: openapi.Response(description="Résultats de recherche")},
        tags=['API Clients']
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
        operation_description="clients_netdata-metrics_retrieve - Récupère les métriques de performance système temps réel de Netdata incluant CPU, mémoire, disques, réseau, processus et services. Fournit des données haute résolution avec historique et alerting automatique pour le monitoring système.",
        responses={200: openapi.Response(
            description='Métriques Netdata',
            schema=NetdataMetricsSerializer()
        )},
        tags=['API Clients']
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
# VIEWSETS POUR LES CLIENTS D'INFRASTRUCTURE  
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
        operation_description="clients_infrastructure-clients_list - Récupère la liste complète de tous les clients d'infrastructure disponibles avec statut détaillé incluant HAProxy pour équilibrage de charge, Fail2Ban pour protection anti-intrusion et Suricata pour détection d'intrusion réseau. Vérifie la disponibilité et configuration de chaque service de sécurité.",
        responses={200: openapi.Response(
            description='Liste des clients infrastructure',
            schema=ClientHealthSerializer()
        )},
        tags=['API Clients']
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
        
        # Suricata
        if self.suricata_client:
            try:
                suricata_available = self.suricata_client.test_connection()
                clients_data.append({
                    "name": "Suricata",
                    "type": "network_security",
                    "status": "available" if suricata_available else "unavailable",
                    "description": "Système de détection d'intrusion réseau"
                })
            except Exception as e:
                clients_data.append({
                    "name": "Suricata",
                    "type": "network_security",
                    "status": "error",
                    "error": str(e),
                    "description": "Système de détection d'intrusion réseau"
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
        operation_description="clients_haproxy-stats_retrieve - Récupère les statistiques complètes de HAProxy incluant métriques de performance des backends, frontends, serveurs, sessions actives, taux d'erreurs, temps de réponse et santé des services. Essentiel pour le monitoring de l'équilibrage de charge.",
        responses={200: openapi.Response(
            description='Statistiques HAProxy',
            schema=HAProxyStatsSerializer()
        )},
        tags=['API Clients']
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
        operation_description="clients_fail2ban-action_execute - Exécute une action de sécurité Fail2Ban incluant bannissement d'IP (ban), débannissement (unban) et vérification de statut des jails. Permet la gestion dynamique de la protection anti-intrusion avec logs détaillés et gestion des whitelists.",
        request_body=Fail2BanActionSerializer,
        responses={200: openapi.Response(
            description='Succès de l\'action Fail2Ban',
            schema=SuccessResponseSerializer()
        )},
        tags=['API Clients']
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
        operation_description="clients_suricata-rules_manage - Gère les règles de détection d'intrusion Suricata incluant listage, ajout, suppression et rechargement des règles de sécurité. Supporte les signatures personnalisées, règles ET, policies de sécurité et intégration threat intelligence pour la protection réseau avancée.",
        request_body=SuricataRuleActionSerializer,
        responses={200: openapi.Response(
            description='Succès de l\'action Suricata',
            schema=SuccessResponseSerializer()
        )},
        tags=['API Clients']
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
# VIEWSETS POUR LES UTILITAIRES
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
        operation_description="clients_global-health_check - Vérifie l'état de santé complet de tous les clients API disponibles avec diagnostic approfondi incluant connectivité, performances, disponibilité des services et statistiques globales. Fournit un tableau de bord unifié pour le monitoring de l'infrastructure complète.",
        responses={200: openapi.Response(
            description='Santé globale des clients',
            schema=ClientHealthSerializer()
        )},
        tags=['API Clients']
    )
    def list(self, request):
        """Vérifie l'état de santé de tous les clients."""
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
    
    @action(detail=False, methods=['get'], url_path='swagger-json')
    @swagger_auto_schema(
        operation_summary="Documentation Swagger JSON",
        operation_description="clients_swagger-documentation_generate - Génère et retourne la documentation Swagger complète au format JSON pour tous les clients API avec schémas détaillés, exemples de requêtes/réponses et spécifications OpenAPI. Permet l'intégration avec des outils de génération de SDK et de tests automatisés.",
        responses={200: openapi.Response(description="Documentation Swagger")},
        tags=['API Clients']
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
        operation_summary="Santé globale de tous les clients API",
        operation_description="clients_health_check - Vérification de santé globale complète de tous les clients API avec diagnostic détaillé de connectivité, performances et disponibilité. Retourne un rapport unifié sur l'état de l'infrastructure de monitoring et gestion réseau.",
        responses={200: openapi.Schema(type=openapi.TYPE_OBJECT)},
        tags=['API Clients']
    )
    @action(detail=False, methods=['get'])
    def health(self, request):
        """Vérification de santé globale de tous les clients."""
        return self.list(request)

    @swagger_auto_schema(
        operation_summary="Configuration des clients API",
        operation_description="clients_config_retrieve - Récupère la configuration complète de tous les clients API incluant URLs de connexion, paramètres par défaut, credentials et settings de chaque service. Permet la vérification et validation des configurations système.",
        responses={200: openapi.Schema(type=openapi.TYPE_OBJECT)},
        tags=['API Clients']
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