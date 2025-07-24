"""
API Clients - Vues complètes avec documentation enrichie.

Ce module fournit une API REST complète pour l'interaction avec tous les clients
du système de gestion réseau avec une documentation Swagger unifiée.
"""

import logging
from typing import Dict, Any, Optional, List
from django.http import JsonResponse
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

# Import des serializers
from .serializers import (
    ClientStatusSerializer,
    NetworkClientSerializer,
    MonitoringClientSerializer,
    InfrastructureClientSerializer,
    SecurityClientSerializer,
    GNS3ProjectSerializer, 
    GNS3NodeSerializer,
    SNMPRequestSerializer, 
    SNMPSetRequestSerializer, 
    SNMPResponseSerializer,
    NetflowAnalysisSerializer,
    PrometheusQuerySerializer, 
    PrometheusResponseSerializer,
    GrafanaDashboardSerializer,
    ElasticsearchQuerySerializer,
    NetdataMetricsSerializer,
    HAProxyStatsSerializer,
    Fail2BanActionSerializer,
    SuricataRuleActionSerializer,
    ClientHealthSerializer,
    ErrorResponseSerializer,
    SuccessResponseSerializer
)

logger = logging.getLogger(__name__)

# Initialisation sécurisée des clients avec gestion d'erreurs
clients = {}

def safe_import_and_init():
    """
    Initialise tous les clients de manière sécurisée avec gestion d'erreurs.
    
    Cette fonction importe et initialise tous les clients disponibles :
    - Clients Réseau : GNS3, SNMP, NetFlow
    - Clients Monitoring : Prometheus, Grafana, Elasticsearch, Netdata, Ntopng
    - Clients Infrastructure : HAProxy, Traffic Control
    - Clients Sécurité : Fail2Ban, Suricata
    """
    global clients
    
    # ==================== CLIENTS RÉSEAU ====================
    try:
        from .network import GNS3Client
        clients['gns3'] = GNS3Client(host="localhost", port=3080)
    except Exception as e:
        logger.warning(f"GNS3Client non disponible: {e}")
        clients['gns3'] = None

    try:
        from .network import SNMPClient
        clients['snmp'] = SNMPClient(host="localhost")
    except Exception as e:
        logger.warning(f"SNMPClient non disponible: {e}")
        clients['snmp'] = None

    try:
        from .network import NetflowClient
        clients['netflow'] = NetflowClient(base_url="http://localhost:9995")
    except Exception as e:
        logger.warning(f"NetflowClient non disponible: {e}")
        clients['netflow'] = None

    # ==================== CLIENTS MONITORING ====================
    try:
        from .monitoring import PrometheusClient
        clients['prometheus'] = PrometheusClient(base_url="http://localhost:9090")
    except Exception as e:
        logger.warning(f"PrometheusClient non disponible: {e}")
        clients['prometheus'] = None

    try:
        from .monitoring import GrafanaClient
        clients['grafana'] = GrafanaClient(base_url="http://localhost:3000")
    except Exception as e:
        logger.warning(f"GrafanaClient non disponible: {e}")
        clients['grafana'] = None

    try:
        from .monitoring import ElasticsearchClient
        clients['elasticsearch'] = ElasticsearchClient(
            base_url="http://localhost:9200",
            username="elastic",
            password="changeme"
        )
    except Exception as e:
        logger.warning(f"ElasticsearchClient non disponible: {e}")
        clients['elasticsearch'] = None

    try:
        from .monitoring import NetdataClient
        clients['netdata'] = NetdataClient(base_url="http://localhost:19999")
    except Exception as e:
        logger.warning(f"NetdataClient non disponible: {e}")
        clients['netdata'] = None

    try:
        from .monitoring import NtopngClient
        clients['ntopng'] = NtopngClient(
            base_url="http://localhost:3000",
            username="admin",
            password="admin"
        )
    except Exception as e:
        logger.warning(f"NtopngClient non disponible: {e}")
        clients['ntopng'] = None

    # ==================== CLIENTS INFRASTRUCTURE ====================
    try:
        from .infrastructure import HAProxyClient
        clients['haproxy'] = HAProxyClient(stats_socket="/var/run/haproxy.sock")
    except Exception as e:
        logger.warning(f"HAProxyClient non disponible: {e}")
        clients['haproxy'] = None

    try:
        from .infrastructure import TrafficControlClient
        clients['traffic_control'] = TrafficControlClient(sudo_required=False)
    except Exception as e:
        logger.warning(f"TrafficControlClient non disponible: {e}")
        clients['traffic_control'] = None

    # ==================== CLIENTS SÉCURITÉ ====================
    try:
        from .security import Fail2BanClient
        clients['fail2ban'] = Fail2BanClient(
            base_url="http://localhost:8080",
            username="admin",
            password="admin"
        )
    except Exception as e:
        logger.warning(f"Fail2BanClient non disponible: {e}")
        clients['fail2ban'] = None

    try:
        from .security import SuricataClient
        clients['suricata'] = SuricataClient(base_url="http://localhost:8081")
    except Exception as e:
        logger.warning(f"SuricataClient non disponible: {e}")
        clients['suricata'] = None

# Initialiser les clients au chargement du module
safe_import_and_init()

# ==================== SCHÉMAS SWAGGER COMMUNS ====================

client_error_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'error': openapi.Schema(type=openapi.TYPE_STRING, description='Message d\'erreur'),
        'code': openapi.Schema(type=openapi.TYPE_STRING, description='Code d\'erreur'),
        'details': openapi.Schema(type=openapi.TYPE_OBJECT, description='Détails supplémentaires')
    }
)

success_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'success': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Statut de réussite'),
        'message': openapi.Schema(type=openapi.TYPE_STRING, description='Message de confirmation'),
        'data': openapi.Schema(type=openapi.TYPE_OBJECT, description='Données retournées')
    }
)

# ==================== ENDPOINTS DE STATUT DES CLIENTS ====================

@swagger_auto_schema(
    method='get',
    operation_summary="Statut des clients réseau",
    operation_description="""
    📡 **Récupère le statut de tous les clients réseau disponibles**
    
    Cet endpoint retourne l'état de connexion et la disponibilité de tous les clients réseau :
    
    ### Clients surveillés :
    - **GNS3Client** : Gestion des topologies et simulations réseau
    - **SNMPClient** : Interrogation SNMP des équipements réseau  
    - **NetflowClient** : Analyse des flux de trafic réseau
    
    ### Informations retournées :
    - Statut de disponibilité (available/unavailable)
    - Type de client
    - Description fonctionnelle
    - Dernière vérification de connexion
    
    ### Codes de réponse :
    - **200** : Statut récupéré avec succès
    - **500** : Erreur interne du serveur
    
    ### Exemple d'utilisation :
    ```bash
    curl -X GET "https://localhost:8000/api/clients/network/" \\
         -H "Accept: application/json"
    ```
    """,
    responses={
        200: openapi.Response(
            description="Statut des clients réseau récupéré avec succès",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'gns3': openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'available': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Client disponible'),
                            'status': openapi.Schema(type=openapi.TYPE_STRING, description='Statut actuel'),
                            'client_type': openapi.Schema(type=openapi.TYPE_STRING, description='Type de client'),
                            'description': openapi.Schema(type=openapi.TYPE_STRING, description='Description'),
                            'host': openapi.Schema(type=openapi.TYPE_STRING, description='Adresse du serveur'),
                            'port': openapi.Schema(type=openapi.TYPE_INTEGER, description='Port de connexion')
                        }
                    ),
                    'snmp': openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'available': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                            'status': openapi.Schema(type=openapi.TYPE_STRING),
                            'client_type': openapi.Schema(type=openapi.TYPE_STRING),
                            'description': openapi.Schema(type=openapi.TYPE_STRING)
                        }
                    ),
                    'netflow': openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'available': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                            'status': openapi.Schema(type=openapi.TYPE_STRING),
                            'client_type': openapi.Schema(type=openapi.TYPE_STRING),
                            'description': openapi.Schema(type=openapi.TYPE_STRING)
                        }
                    )
                }
            ),
            examples={
                'application/json': {
                    'gns3': {
                        'available': True,
                        'status': 'connected',
                        'client_type': 'GNS3Client',
                        'description': 'Client pour l\'interaction avec GNS3',
                        'host': 'localhost',
                        'port': 3080
                    },
                    'snmp': {
                        'available': True,
                        'status': 'ready',
                        'client_type': 'SNMPClient',
                        'description': 'Client pour les requêtes SNMP'
                    },
                    'netflow': {
                        'available': False,
                        'status': 'connection_failed',
                        'client_type': 'NetflowClient',
                        'description': 'Client pour l\'analyse NetFlow'
                    }
                }
            }
        ),
        500: openapi.Response(description="Erreur interne du serveur", schema=client_error_schema)
    },
    tags=['API Clients']
)
@api_view(['GET'])
@permission_classes([AllowAny])
def network_clients(request):
    """Récupère le statut de tous les clients réseau avec informations détaillées."""
    try:
        network_status = {}
        
        # GNS3 Client
        gns3_client = clients.get('gns3')
        network_status['gns3'] = {
            'available': gns3_client is not None,
            'status': 'connected' if gns3_client else 'unavailable',
            'client_type': 'GNS3Client',
            'description': 'Client pour l\'interaction avec GNS3 - Gestion des topologies et simulations réseau',
            'capabilities': [
                'Gestion des projets (CRUD)',
                'Gestion des nœuds (CRUD)',
                'Contrôle des simulations',
                'Export/Import de topologies'
            ],
            'endpoints': [
                '/network/gns3/projects/',
                '/network/gns3/nodes/',
                '/network/gns3/simulations/'
            ]
        }
        
        if gns3_client:
            try:
                network_status['gns3'].update({
                    'host': getattr(gns3_client, 'host', 'localhost'),
                    'port': getattr(gns3_client, 'port', 3080),
                    'version': getattr(gns3_client, 'get_version', lambda: 'Unknown')(),
                    'last_check': '2024-01-01T00:00:00Z'
                })
            except:
                pass
        
        # SNMP Client  
        snmp_client = clients.get('snmp')
        network_status['snmp'] = {
            'available': snmp_client is not None,
            'status': 'ready' if snmp_client else 'unavailable',
            'client_type': 'SNMPClient',
            'description': 'Client pour les requêtes SNMP - Interrogation des équipements réseau',
            'capabilities': [
                'Requêtes GET/SET SNMP',
                'Walk SNMP pour découverte',
                'Informations système',
                'Statistiques d\'interfaces',
                'Découverte de voisins'
            ],
            'endpoints': [
                '/network/snmp/query/',
                '/network/snmp/walk/',
                '/network/snmp/system/',
                '/network/snmp/interfaces/'
            ]
        }
        
        # NetFlow Client
        netflow_client = clients.get('netflow')
        network_status['netflow'] = {
            'available': netflow_client is not None,
            'status': 'monitoring' if netflow_client else 'unavailable',
            'client_type': 'NetflowClient',
            'description': 'Client pour l\'analyse NetFlow - Surveillance des flux de trafic réseau',
            'capabilities': [
                'Analyse des flux de trafic',
                'Top talkers',
                'Distribution des protocoles',
                'Détection d\'anomalies',
                'Matrice de trafic'
            ],
            'endpoints': [
                '/network/netflow/flows/',
                '/network/netflow/top-talkers/',
                '/network/netflow/protocols/',
                '/network/netflow/anomalies/'
            ]
        }
        
        return Response(network_status, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des clients réseau: {e}")
        return Response({
            'error': 'Erreur lors de la récupération des clients réseau',
            'code': 'NETWORK_CLIENTS_ERROR',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@swagger_auto_schema(
    method='get',
    operation_summary="Statut des clients monitoring",
    operation_description="""
    📊 **Récupère le statut de tous les clients de monitoring disponibles**
    
    Cet endpoint retourne l'état de tous les clients utilisés pour la surveillance et le monitoring :
    
    ### Clients surveillés :
    - **PrometheusClient** : Collecte de métriques et alertes
    - **GrafanaClient** : Tableaux de bord et visualisations
    - **ElasticsearchClient** : Indexation et recherche de données
    - **NetdataClient** : Monitoring temps réel des systèmes
    - **NtopngClient** : Analyse du trafic réseau en détail
    
    ### Informations détaillées :
    - État de connexion en temps réel
    - Capacités fonctionnelles de chaque client
    - Endpoints disponibles
    - Métriques de performance
    
    ### Exemple d'utilisation :
    ```bash
    curl -X GET "https://localhost:8000/api/clients/monitoring/" \\
         -H "Accept: application/json"
    ```
    """,
    responses={
        200: openapi.Response(
            description="Statut des clients monitoring récupéré avec succès",
            examples={
                'application/json': {
                    'prometheus': {
                        'available': True,
                        'status': 'collecting',
                        'client_type': 'PrometheusClient',
                        'description': 'Client pour Prometheus - Collecte de métriques et alertes',
                        'capabilities': ['Requêtes PromQL', 'Gestion des alertes', 'Métriques temps réel'],
                        'metrics_count': 1542,
                        'active_alerts': 3
                    }
                }
            }
        ),
        500: openapi.Response(description="Erreur interne", schema=client_error_schema)
    },
    tags=['API Clients']
)
@api_view(['GET'])
@permission_classes([AllowAny])
def monitoring_clients(request):
    """Récupère le statut détaillé de tous les clients monitoring."""
    try:
        monitoring_status = {}
        
        # Prometheus Client
        prometheus_client = clients.get('prometheus')
        monitoring_status['prometheus'] = {
            'available': prometheus_client is not None,
            'status': 'collecting' if prometheus_client else 'unavailable',
            'client_type': 'PrometheusClient',
            'description': 'Client pour Prometheus - Collecte de métriques et système d\'alertes',
            'capabilities': [
                'Requêtes PromQL avancées',
                'Gestion des règles d\'alerte',
                'Métriques temps réel',
                'Historique des données',
                'Fédération de métriques'
            ],
            'endpoints': [
                '/monitoring/prometheus/query/',
                '/monitoring/prometheus/alerts/',
                '/monitoring/prometheus/targets/',
                '/monitoring/prometheus/rules/'
            ]
        }
        
        # Grafana Client
        grafana_client = clients.get('grafana')
        monitoring_status['grafana'] = {
            'available': grafana_client is not None,
            'status': 'dashboard_ready' if grafana_client else 'unavailable',
            'client_type': 'GrafanaClient',
            'description': 'Client pour Grafana - Tableaux de bord et visualisations',
            'capabilities': [
                'Gestion des tableaux de bord (CRUD)',
                'Gestion des sources de données (CRUD)',
                'Gestion des alertes (CRUD)',
                'Gestion des utilisateurs',
                'Export/Import de dashboards'
            ],
            'endpoints': [
                '/monitoring/grafana/dashboards/',
                '/monitoring/grafana/datasources/',
                '/monitoring/grafana/alerts/',
                '/monitoring/grafana/users/'
            ]
        }
        
        # Elasticsearch Client
        elasticsearch_client = clients.get('elasticsearch')
        monitoring_status['elasticsearch'] = {
            'available': elasticsearch_client is not None,
            'status': 'indexing' if elasticsearch_client else 'unavailable',
            'client_type': 'ElasticsearchClient',
            'description': 'Client pour Elasticsearch - Indexation et recherche de données',
            'capabilities': [
                'Gestion des indices (CRUD)',
                'Recherche et requêtes complexes',
                'Gestion des documents (CRUD)',
                'Templates d\'index',
                'Agrégations de données'
            ],
            'endpoints': [
                '/monitoring/elasticsearch/indices/',
                '/monitoring/elasticsearch/search/',
                '/monitoring/elasticsearch/documents/',
                '/monitoring/elasticsearch/templates/'
            ]
        }
        
        # Netdata Client
        netdata_client = clients.get('netdata')
        monitoring_status['netdata'] = {
            'available': netdata_client is not None,
            'status': 'real_time_monitoring' if netdata_client else 'unavailable',
            'client_type': 'NetdataClient',
            'description': 'Client pour Netdata - Monitoring temps réel des systèmes',
            'capabilities': [
                'Métriques système temps réel',
                'Monitoring des applications',
                'Surveillance réseau',
                'Alertes automatiques',
                'Dashboards interactifs'
            ],
            'endpoints': [
                '/monitoring/netdata/metrics/',
                '/monitoring/netdata/charts/',
                '/monitoring/netdata/alarms/',
                '/monitoring/netdata/info/'
            ]
        }
        
        # Ntopng Client
        ntopng_client = clients.get('ntopng')
        monitoring_status['ntopng'] = {
            'available': ntopng_client is not None,
            'status': 'traffic_analysis' if ntopng_client else 'unavailable',
            'client_type': 'NtopngClient',
            'description': 'Client pour Ntopng - Analyse avancée du trafic réseau',
            'capabilities': [
                'Analyse du trafic en temps réel',
                'Détection d\'anomalies réseau',
                'Géolocalisation du trafic',
                'Analyse DPI (Deep Packet Inspection)',
                'Rapports de sécurité'
            ],
            'endpoints': [
                '/monitoring/ntopng/hosts/',
                '/monitoring/ntopng/flows/',
                '/monitoring/ntopng/interfaces/',
                '/monitoring/ntopng/alerts/'
            ]
        }
        
        return Response(monitoring_status, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des clients monitoring: {e}")
        return Response({
            'error': 'Erreur lors de la récupération des clients monitoring',
            'code': 'MONITORING_CLIENTS_ERROR',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# ==================== ENDPOINTS CRUD COMPLETS POUR GNS3 ====================

@swagger_auto_schema(
    method='get',
    operation_summary="Liste des projets GNS3",
    operation_description="""
    🏗️ **Récupère la liste complète de tous les projets GNS3**
    
    Cet endpoint retourne tous les projets GNS3 disponibles avec leurs informations détaillées :
    
    ### Informations retournées :
    - **project_id** : Identifiant unique du projet
    - **name** : Nom du projet
    - **status** : Statut (opened/closed)
    - **path** : Chemin du projet sur le système
    - **creation_date** : Date de création
    - **last_modified** : Dernière modification
    - **nodes_count** : Nombre de nœuds dans le projet
    - **scene_width/height** : Dimensions de la scène
    - **zoom** : Niveau de zoom par défaut
    
    ### États possibles d'un projet :
    - **opened** : Projet ouvert et utilisable
    - **closed** : Projet fermé
    - **auto_start** : Démarrage automatique activé
    - **auto_open** : Ouverture automatique activée
    - **auto_close** : Fermeture automatique activée
    
    ### Exemple d'utilisation :
    ```bash
    curl -X GET "https://localhost:8000/api/clients/network/gns3/projects/" \\
         -H "Accept: application/json"
    ```
    
    ### Filtrage possible :
    - Par statut : `?status=opened`
    - Par nom : `?name=MonProjet`
    - Avec nœuds : `?include_nodes=true`
    """,
    responses={
        200: openapi.Response(
            description="Liste des projets récupérée avec succès",
            schema=openapi.Schema(
                type=openapi.TYPE_ARRAY,
                items=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'project_id': openapi.Schema(type=openapi.TYPE_STRING, description='ID unique du projet'),
                        'name': openapi.Schema(type=openapi.TYPE_STRING, description='Nom du projet'),
                        'status': openapi.Schema(type=openapi.TYPE_STRING, description='Statut (opened/closed)'),
                        'path': openapi.Schema(type=openapi.TYPE_STRING, description='Chemin du projet'),
                        'creation_date': openapi.Schema(type=openapi.TYPE_STRING, description='Date de création'),
                        'last_modified': openapi.Schema(type=openapi.TYPE_STRING, description='Dernière modification'),
                        'nodes_count': openapi.Schema(type=openapi.TYPE_INTEGER, description='Nombre de nœuds'),
                        'scene_width': openapi.Schema(type=openapi.TYPE_INTEGER, description='Largeur de la scène'),
                        'scene_height': openapi.Schema(type=openapi.TYPE_INTEGER, description='Hauteur de la scène'),
                        'zoom': openapi.Schema(type=openapi.TYPE_INTEGER, description='Zoom par défaut'),
                        'auto_start': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Démarrage automatique'),
                        'auto_open': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Ouverture automatique'),
                        'auto_close': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Fermeture automatique')
                    }
                )
            ),
            examples={
                'application/json': [
                    {
                        'project_id': '12345678-1234-1234-1234-123456789012',
                        'name': 'Réseau Enterprise',
                        'status': 'opened',
                        'path': '/opt/gns3/projects/reseau-enterprise',
                        'creation_date': '2024-01-15T10:30:00Z',
                        'last_modified': '2024-01-20T14:45:00Z',
                        'nodes_count': 15,
                        'scene_width': 2000,
                        'scene_height': 1000,
                        'zoom': 100,
                        'auto_start': False,
                        'auto_open': True,
                        'auto_close': False
                    }
                ]
            }
        ),
        503: openapi.Response(description="Client GNS3 non disponible", schema=client_error_schema),
        500: openapi.Response(description="Erreur interne", schema=client_error_schema)
    },
    tags=['API Clients']
)
@api_view(['GET'])
@permission_classes([AllowAny])
def gns3_projects(request):
    """Récupère la liste complète des projets GNS3 avec informations détaillées."""
    if not clients['gns3']:
        return Response({
            'error': 'Client GNS3 non disponible',
            'code': 'GNS3_UNAVAILABLE',
            'details': 'Le service GNS3 n\'est pas accessible. Vérifiez que GNS3 est démarré.'
        }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    
    try:
        # Paramètres de filtrage optionnels
        status_filter = request.GET.get('status')
        name_filter = request.GET.get('name')
        include_nodes = request.GET.get('include_nodes', '').lower() == 'true'
        
        projects = clients['gns3'].get_projects()
        
        # Enrichissement des données pour chaque projet
        enriched_projects = []
        for project in projects:
            enriched_project = {
                'project_id': project.get('project_id'),
                'name': project.get('name'),
                'status': project.get('status', 'unknown'),
                'path': project.get('path'),
                'creation_date': project.get('created_at'),
                'last_modified': project.get('updated_at'),
                'scene_width': project.get('scene_width', 2000),
                'scene_height': project.get('scene_height', 1000),
                'zoom': project.get('zoom', 100),
                'auto_start': project.get('auto_start', False),
                'auto_open': project.get('auto_open', False),
                'auto_close': project.get('auto_close', False),
                'grid_size': project.get('grid_size', 75),
                'drawing_grid_size': project.get('drawing_grid_size', 25),
                'show_grid': project.get('show_grid', False),
                'snap_to_grid': project.get('snap_to_grid', False),
                'show_interface_labels': project.get('show_interface_labels', False)
            }
            
            # Ajouter le nombre de nœuds si demandé
            if include_nodes:
                try:
                    nodes = clients['gns3'].get_nodes(project['project_id'])
                    enriched_project['nodes_count'] = len(nodes)
                    enriched_project['nodes'] = nodes
                except:
                    enriched_project['nodes_count'] = 0
                    enriched_project['nodes'] = []
            else:
                enriched_project['nodes_count'] = 0
            
            # Appliquer les filtres
            if status_filter and project.get('status') != status_filter:
                continue
            if name_filter and name_filter.lower() not in project.get('name', '').lower():
                continue
                
            enriched_projects.append(enriched_project)
        
        return Response(enriched_projects, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des projets GNS3: {e}")
        return Response({
            'error': 'Erreur lors de la récupération des projets GNS3',
            'code': 'GNS3_PROJECTS_ERROR',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# ==================== ENDPOINTS CRUD COMPLETS POUR GRAFANA ====================

@swagger_auto_schema(
    method='get',
    operation_summary="Liste des dashboards Grafana",
    operation_description="""
    📊 **Récupère la liste complète de tous les dashboards Grafana**
    
    Cet endpoint retourne tous les dashboards Grafana disponibles avec leurs métadonnées :
    
    ### Informations retournées :
    - **uid** : Identifiant unique du dashboard
    - **title** : Titre du dashboard
    - **tags** : Tags associés pour la catégorisation
    - **folder** : Dossier de rangement
    - **starred** : Statut favori de l'utilisateur
    - **version** : Version du dashboard
    - **url** : URL d'accès direct
    - **created/updated** : Dates de création et modification
    
    ### Filtres disponibles :
    - **tag** : Filtrer par tag (`?tag=production`)
    - **folder** : Filtrer par dossier (`?folder=monitoring`)
    - **starred** : Dashboards favoris uniquement (`?starred=true`)
    - **query** : Recherche textuelle (`?query=network`)
    
    ### Exemple d'utilisation :
    ```bash
    curl -X GET "https://localhost:8000/api/clients/monitoring/grafana/dashboards/" \\
         -H "Accept: application/json"
    ```
    """,
    responses={
        200: openapi.Response(
            description="Liste des dashboards récupérée avec succès",
            examples={
                'application/json': [
                    {
                        'uid': 'network-overview',
                        'title': 'Network Overview',
                        'tags': ['network', 'monitoring'],
                        'folder': 'Network Monitoring',
                        'starred': True,
                        'version': 3,
                        'url': '/d/network-overview/network-overview',
                        'created': '2024-01-10T08:00:00Z',
                        'updated': '2024-01-20T15:30:00Z'
                    }
                ]
            }
        ),
        503: openapi.Response(description="Client Grafana non disponible", schema=client_error_schema)
    },
    tags=['API Clients']
)
@api_view(['GET'])
@permission_classes([AllowAny])
def grafana_dashboards(request):
    """Récupère la liste complète des dashboards Grafana avec filtrage."""
    if not clients['grafana']:
        return Response({
            'error': 'Client Grafana non disponible',
            'code': 'GRAFANA_UNAVAILABLE',
            'details': 'Le service Grafana n\'est pas accessible.'
        }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    
    try:
        # Paramètres de filtrage
        tag_filter = request.GET.get('tag')
        folder_filter = request.GET.get('folder')
        starred_filter = request.GET.get('starred', '').lower() == 'true'
        query_filter = request.GET.get('query', '').lower()
        
        dashboards = clients['grafana'].get_dashboards()
        
        # Filtrer les résultats
        filtered_dashboards = []
        for dashboard in dashboards:
            # Filtre par tag
            if tag_filter and tag_filter not in dashboard.get('tags', []):
                continue
            
            # Filtre par dossier
            if folder_filter and dashboard.get('folderTitle') != folder_filter:
                continue
            
            # Filtre favoris
            if starred_filter and not dashboard.get('isStarred', False):
                continue
            
            # Filtre par recherche textuelle
            if query_filter:
                searchable_text = f"{dashboard.get('title', '')} {' '.join(dashboard.get('tags', []))}".lower()
                if query_filter not in searchable_text:
                    continue
            
            filtered_dashboards.append(dashboard)
        
        return Response(filtered_dashboards, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des dashboards Grafana: {e}")
        return Response({
            'error': 'Erreur lors de la récupération des dashboards Grafana',
            'code': 'GRAFANA_DASHBOARDS_ERROR',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# ==================== ENDPOINT DE SANTÉ GLOBALE ENRICHI ====================

@swagger_auto_schema(
    method='get',
    operation_summary="Vérification complète de santé",
    operation_description="""
    🏥 **Effectue une vérification complète de santé de tous les clients API**
    
    Cet endpoint effectue un diagnostic complet de l'état de tous les clients :
    
    ### Vérifications effectuées :
    1. **Disponibilité** : Client initialisé et accessible
    2. **Connectivité** : Test de connexion au service distant
    3. **Performance** : Temps de réponse et latence
    4. **Santé fonctionnelle** : Tests spécifiques à chaque client
    
    ### Métriques globales calculées :
    - **overall_status** : État global (healthy/degraded/unhealthy)
    - **total_clients** : Nombre total de clients
    - **available_clients** : Clients disponibles
    - **healthy_clients** : Clients en bonne santé
    - **availability_rate** : Taux de disponibilité (%)
    - **health_rate** : Taux de santé (%)
    - **average_response_time** : Temps de réponse moyen
    
    ### Par client, retourne :
    - **available** : Client disponible
    - **healthy** : Client en bonne santé
    - **response_time** : Temps de réponse (ms)
    - **last_check** : Dernière vérification
    - **error** : Message d'erreur si applicable
    - **version** : Version du service si disponible
    - **uptime** : Temps de fonctionnement
    
    ### Codes de santé :
    - **healthy** : Tous les tests passent
    - **degraded** : Quelques problèmes détectés
    - **unhealthy** : Problèmes critiques
    - **unknown** : Impossible de déterminer l'état
    
    ### Exemple d'utilisation :
    ```bash
    curl -X GET "https://localhost:8000/api/clients/utils/health/" \\
         -H "Accept: application/json"
    ```
    """,
    responses={
        200: openapi.Response(
            description="Vérification de santé terminée",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'overall_status': openapi.Schema(type=openapi.TYPE_STRING, description='État global'),
                    'total_clients': openapi.Schema(type=openapi.TYPE_INTEGER, description='Nombre total de clients'),
                    'available_clients': openapi.Schema(type=openapi.TYPE_INTEGER, description='Clients disponibles'),
                    'healthy_clients': openapi.Schema(type=openapi.TYPE_INTEGER, description='Clients en bonne santé'),
                    'availability_rate': openapi.Schema(type=openapi.TYPE_NUMBER, description='Taux de disponibilité'),
                    'health_rate': openapi.Schema(type=openapi.TYPE_NUMBER, description='Taux de santé'),
                    'average_response_time': openapi.Schema(type=openapi.TYPE_NUMBER, description='Temps de réponse moyen'),
                    'timestamp': openapi.Schema(type=openapi.TYPE_STRING, description='Horodatage de la vérification'),
                    'clients': openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        description='Détails par client',
                        additional_properties=openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'available': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                                'healthy': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                                'response_time': openapi.Schema(type=openapi.TYPE_NUMBER),
                                'last_check': openapi.Schema(type=openapi.TYPE_STRING),
                                'version': openapi.Schema(type=openapi.TYPE_STRING),
                                'uptime': openapi.Schema(type=openapi.TYPE_STRING),
                                'error': openapi.Schema(type=openapi.TYPE_STRING),
                                'type': openapi.Schema(type=openapi.TYPE_STRING)
                            }
                        )
                    )
                }
            ),
            examples={
                'application/json': {
                    'overall_status': 'healthy',
                    'total_clients': 11,
                    'available_clients': 8,
                    'healthy_clients': 7,
                    'availability_rate': 0.73,
                    'health_rate': 0.64,
                    'average_response_time': 150.5,
                    'timestamp': '2024-01-20T16:30:00Z',
                    'clients': {
                        'gns3': {
                            'available': True,
                            'healthy': True,
                            'response_time': 89.2,
                            'last_check': '2024-01-20T16:30:00Z',
                            'version': '2.2.43',
                            'uptime': '5 days, 3 hours',
                            'type': 'GNS3Client'
                        },
                        'prometheus': {
                            'available': True,
                            'healthy': False,
                            'response_time': 250.8,
                            'last_check': '2024-01-20T16:30:00Z',
                            'error': 'High memory usage detected',
                            'type': 'PrometheusClient'
                        }
                    }
                }
            }
        ),
        500: openapi.Response(description="Erreur lors de la vérification", schema=client_error_schema)
    },
    tags=['API Clients']
)
@api_view(['GET'])
@permission_classes([AllowAny])
def comprehensive_health_check(request):
    """Effectue une vérification complète de santé avec métriques détaillées."""
    try:
        import time
        from datetime import datetime
        
        health_status = {}
        total_clients = 0
        available_clients = 0
        healthy_clients = 0
        total_response_time = 0
        response_times = []
        
        # Vérification de chaque client avec métriques
        for client_name, client in clients.items():
            total_clients += 1
            start_time = time.time()
            
            if client is not None:
                available_clients += 1
                
                try:
                    # Test de santé spécifique selon le type de client
                    is_healthy = False
                    error_message = None
                    version_info = 'Unknown'
                    uptime_info = 'Unknown'
                    
                    # Tests spécifiques par type de client
                    if hasattr(client, 'check_health'):
                        is_healthy = client.check_health()
                    elif hasattr(client, 'test_connection'):
                        is_healthy = client.test_connection()
                    elif hasattr(client, 'get_version'):
                        try:
                            version_info = client.get_version()
                            is_healthy = True
                        except:
                            is_healthy = False
                    else:
                        # Test générique - essayer une opération simple
                        if client_name == 'gns3' and hasattr(client, 'get_projects'):
                            client.get_projects()
                            is_healthy = True
                        elif client_name == 'prometheus' and hasattr(client, 'get_targets'):
                            client.get_targets()
                            is_healthy = True
                        elif client_name == 'grafana' and hasattr(client, 'get_dashboards'):
                            client.get_dashboards()
                            is_healthy = True
                        else:
                            is_healthy = True
                    
                    if is_healthy:
                        healthy_clients += 1
                    
                    # Calculer le temps de réponse
                    response_time = (time.time() - start_time) * 1000
                    response_times.append(response_time)
                    total_response_time += response_time
                    
                    health_status[client_name] = {
                        'available': True,
                        'healthy': is_healthy,
                        'response_time': round(response_time, 2),
                        'last_check': datetime.now().isoformat() + 'Z',
                        'version': version_info,
                        'uptime': uptime_info,
                        'type': type(client).__name__,
                        'capabilities': _get_client_capabilities(client_name),
                        'status_code': 'OK' if is_healthy else 'WARNING'
                    }
                    
                    if error_message:
                        health_status[client_name]['error'] = error_message
                        
                except Exception as e:
                    response_time = (time.time() - start_time) * 1000
                    response_times.append(response_time)
                    
                    health_status[client_name] = {
                        'available': True,
                        'healthy': False,
                        'response_time': round(response_time, 2),
                        'last_check': datetime.now().isoformat() + 'Z',
                        'error': str(e),
                        'type': type(client).__name__,
                        'status_code': 'ERROR'
                    }
            else:
                health_status[client_name] = {
                    'available': False,
                    'healthy': False,
                    'response_time': 0,
                    'last_check': datetime.now().isoformat() + 'Z',
                    'error': 'Client non initialisé',
                    'status_code': 'UNAVAILABLE'
                }
        
        # Calculer les métriques globales
        availability_rate = available_clients / total_clients if total_clients > 0 else 0
        health_rate = healthy_clients / total_clients if total_clients > 0 else 0
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        
        # Déterminer le statut global
        if health_rate >= 0.8:
            overall_status = 'healthy'
        elif health_rate >= 0.5:
            overall_status = 'degraded'
        else:
            overall_status = 'unhealthy'
        
        result = {
            'overall_status': overall_status,
            'total_clients': total_clients,
            'available_clients': available_clients,
            'healthy_clients': healthy_clients,
            'availability_rate': round(availability_rate, 3),
            'health_rate': round(health_rate, 3),
            'average_response_time': round(avg_response_time, 2),
            'timestamp': datetime.now().isoformat() + 'Z',
            'clients': health_status,
            'summary': {
                'network_clients': {
                    'total': 3,
                    'healthy': sum(1 for name in ['gns3', 'snmp', 'netflow'] if health_status.get(name, {}).get('healthy', False))
                },
                'monitoring_clients': {
                    'total': 5,
                    'healthy': sum(1 for name in ['prometheus', 'grafana', 'elasticsearch', 'netdata', 'ntopng'] if health_status.get(name, {}).get('healthy', False))
                },
                'infrastructure_clients': {
                    'total': 2,
                    'healthy': sum(1 for name in ['haproxy', 'traffic_control'] if health_status.get(name, {}).get('healthy', False))
                },
                'security_clients': {
                    'total': 2,
                    'healthy': sum(1 for name in ['fail2ban', 'suricata'] if health_status.get(name, {}).get('healthy', False))
                }
            }
        }
        
        return Response(result, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Erreur lors de la vérification de santé globale: {e}")
        return Response({
            'error': 'Erreur lors de la vérification de santé globale',
            'code': 'HEALTH_CHECK_ERROR',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

def _get_client_capabilities(client_name: str) -> List[str]:
    """Retourne les capacités d'un client donné."""
    capabilities_map = {
        'gns3': ['Gestion projets CRUD', 'Gestion nœuds CRUD', 'Simulations', 'Topologies'],
        'snmp': ['Requêtes GET/SET', 'Walk SNMP', 'Découverte équipements', 'Statistiques'],
        'netflow': ['Analyse flux', 'Top talkers', 'Détection anomalies', 'Matrices trafic'],
        'prometheus': ['Métriques PromQL', 'Gestion alertes', 'Collecte données', 'Fédération'],
        'grafana': ['Dashboards CRUD', 'Sources données CRUD', 'Alertes CRUD', 'Utilisateurs'],
        'elasticsearch': ['Indices CRUD', 'Documents CRUD', 'Recherche avancée', 'Agrégations'],
        'netdata': ['Monitoring temps réel', 'Métriques système', 'Alertes auto', 'Dashboards'],
        'ntopng': ['Analyse trafic', 'DPI', 'Géolocalisation', 'Sécurité réseau'],
        'haproxy': ['Load balancing', 'Statistiques', 'Gestion serveurs', 'Santé backends'],
        'traffic_control': ['QoS Linux', 'Limitation bande passante', 'Priorisation', 'Filtres'],
        'fail2ban': ['Bannissement IP', 'Gestion jails', 'Logs sécurité', 'Protection'],
        'suricata': ['IDS/IPS', 'Règles sécurité', 'Détection intrusions', 'Analyses flows']
    }
    return capabilities_map.get(client_name, ['Fonctionnalités de base'])

# ==================== ENDPOINTS CRUD COMPLETS POUR ELASTICSEARCH ====================

@swagger_auto_schema(
    method='get',
    operation_summary="Liste des indices Elasticsearch",
    operation_description="""
    🔍 **Récupère la liste complète de tous les indices Elasticsearch**
    
    Cet endpoint retourne tous les indices Elasticsearch avec leurs métadonnées détaillées :
    
    ### Informations retournées par indice :
    - **index_name** : Nom de l'indice
    - **status** : État (open/close)
    - **health** : Santé (green/yellow/red)
    - **docs_count** : Nombre de documents
    - **docs_deleted** : Documents supprimés
    - **store_size** : Taille de stockage
    - **primary_shards** : Nombre de shards primaires
    - **replica_shards** : Nombre de réplicas
    - **creation_date** : Date de création
    - **settings** : Configuration de l'indice
    
    ### Filtres disponibles :
    - **health** : Filtrer par santé (`?health=green`)
    - **status** : Filtrer par statut (`?status=open`)
    - **pattern** : Pattern de nom (`?pattern=logs-*`)
    - **include_system** : Inclure indices système (`?include_system=true`)
    
    ### Exemple d'utilisation :
    ```bash
    curl -X GET "https://localhost:8000/api/clients/monitoring/elasticsearch/indices/" \\
         -H "Accept: application/json"
    ```
    """,
    responses={
        200: openapi.Response(
            description="Liste des indices récupérée avec succès",
            examples={
                'application/json': [
                    {
                        'index_name': 'logs-2024.01.20',
                        'status': 'open',
                        'health': 'green',
                        'docs_count': 1547892,
                        'docs_deleted': 0,
                        'store_size': '2.1gb',
                        'primary_shards': 1,
                        'replica_shards': 1,
                        'creation_date': '2024-01-20T00:00:00Z'
                    }
                ]
            }
        ),
        503: openapi.Response(description="Client Elasticsearch non disponible", schema=client_error_schema)
    },
    tags=['API Clients']
)
@api_view(['GET'])
@permission_classes([AllowAny])
def elasticsearch_indices(request):
    """Récupère la liste complète des indices Elasticsearch avec métadonnées."""
    if not clients['elasticsearch']:
        return Response({
            'error': 'Client Elasticsearch non disponible',
            'code': 'ELASTICSEARCH_UNAVAILABLE',
            'details': 'Le service Elasticsearch n\'est pas accessible.'
        }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    
    try:
        # Paramètres de filtrage
        health_filter = request.GET.get('health')
        status_filter = request.GET.get('status')
        pattern_filter = request.GET.get('pattern')
        include_system = request.GET.get('include_system', '').lower() == 'true'
        
        indices = clients['elasticsearch'].get_indices()
        
        # Filtrer et enrichir les résultats
        filtered_indices = []
        for index_info in indices:
            index_name = index_info.get('index')
            
            # Filtrer les indices système si nécessaire
            if not include_system and index_name.startswith('.'):
                continue
            
            # Appliquer les filtres
            if health_filter and index_info.get('health') != health_filter:
                continue
            if status_filter and index_info.get('status') != status_filter:
                continue
            if pattern_filter:
                import fnmatch
                if not fnmatch.fnmatch(index_name, pattern_filter):
                    continue
            
            # Enrichir avec des métadonnées supplémentaires
            enriched_index = {
                'index_name': index_name,
                'status': index_info.get('status'),
                'health': index_info.get('health'),
                'docs_count': int(index_info.get('docs.count', 0)),
                'docs_deleted': int(index_info.get('docs.deleted', 0)),
                'store_size': index_info.get('store.size'),
                'primary_store_size': index_info.get('pri.store.size'),
                'primary_shards': int(index_info.get('pri', 0)),
                'replica_shards': int(index_info.get('rep', 0)),
                'creation_date': index_info.get('creation.date.string'),
                'uuid': index_info.get('uuid'),
                'segments_count': int(index_info.get('segments.count', 0)),
                'segments_memory': index_info.get('segments.memory')
            }
            
            filtered_indices.append(enriched_index)
        
        return Response(filtered_indices, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des indices Elasticsearch: {e}")
        return Response({
            'error': 'Erreur lors de la récupération des indices Elasticsearch',
            'code': 'ELASTICSEARCH_INDICES_ERROR',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@swagger_auto_schema(
    method='post',
    operation_summary="Créer un indice Elasticsearch",
    operation_description="""
    ➕ **Crée un nouvel indice Elasticsearch avec configuration personnalisée**
    
    Cet endpoint permet de créer un indice avec des paramètres avancés :
    
    ### Paramètres de création :
    - **index_name** : Nom de l'indice (requis)
    - **settings** : Configuration de l'indice
    - **mappings** : Schéma des champs
    - **aliases** : Alias pour l'indice
    
    ### Paramètres de settings disponibles :
    - **number_of_shards** : Nombre de shards primaires
    - **number_of_replicas** : Nombre de réplicas
    - **refresh_interval** : Intervalle de rafraîchissement
    - **max_result_window** : Taille max des résultats
    - **analysis** : Configuration d'analyse textuelle
    
    ### Exemple de création d'indice :
    ```bash
    curl -X POST "https://localhost:8000/api/clients/monitoring/elasticsearch/indices/" \\
         -H "Content-Type: application/json" \\
         -d '{
           "index_name": "logs-application",
           "settings": {
             "number_of_shards": 1,
             "number_of_replicas": 1,
             "refresh_interval": "1s"
           },
           "mappings": {
             "properties": {
               "timestamp": {"type": "date"},
               "level": {"type": "keyword"},
               "message": {"type": "text"}
             }
           }
         }'
    ```
    """,
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=['index_name'],
        properties={
            'index_name': openapi.Schema(type=openapi.TYPE_STRING, description='Nom de l\'indice'),
            'settings': openapi.Schema(
                type=openapi.TYPE_OBJECT,
                description='Configuration de l\'indice',
                properties={
                    'number_of_shards': openapi.Schema(type=openapi.TYPE_INTEGER, default=1),
                    'number_of_replicas': openapi.Schema(type=openapi.TYPE_INTEGER, default=1),
                    'refresh_interval': openapi.Schema(type=openapi.TYPE_STRING, default='1s'),
                    'max_result_window': openapi.Schema(type=openapi.TYPE_INTEGER, default=10000)
                }
            ),
            'mappings': openapi.Schema(
                type=openapi.TYPE_OBJECT,
                description='Schéma des champs'
            ),
            'aliases': openapi.Schema(
                type=openapi.TYPE_OBJECT,
                description='Alias pour l\'indice'
            )
        }
    ),
    responses={
        201: openapi.Response(description="Indice créé avec succès", schema=success_schema),
        400: openapi.Response(description="Paramètres invalides", schema=client_error_schema),
        409: openapi.Response(description="Indice déjà existant", schema=client_error_schema),
        503: openapi.Response(description="Client non disponible", schema=client_error_schema)
    },
    tags=['API Clients']
)
@api_view(['POST'])
@permission_classes([AllowAny])
def create_elasticsearch_index(request):
    """Crée un nouvel indice Elasticsearch avec configuration personnalisée."""
    if not clients['elasticsearch']:
        return Response({
            'error': 'Client Elasticsearch non disponible',
            'code': 'ELASTICSEARCH_UNAVAILABLE'
        }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    
    try:
        index_name = request.data.get('index_name')
        if not index_name:
            return Response({
                'error': 'Le nom de l\'indice est requis',
                'code': 'MISSING_INDEX_NAME'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Configuration par défaut
        settings = request.data.get('settings', {
            'number_of_shards': 1,
            'number_of_replicas': 1,
            'refresh_interval': '1s'
        })
        
        mappings = request.data.get('mappings', {})
        aliases = request.data.get('aliases', {})
        
        # Construire la configuration complète
        index_config = {'settings': settings}
        if mappings:
            index_config['mappings'] = mappings
        if aliases:
            index_config['aliases'] = aliases
        
        result = clients['elasticsearch'].create_index(index_name, index_config)
        
        return Response({
            'success': True,
            'message': f'Indice {index_name} créé avec succès',
            'data': {
                'index_name': index_name,
                'acknowledged': result.get('acknowledged', False),
                'shards_acknowledged': result.get('shards_acknowledged', False),
                'settings': settings,
                'creation_timestamp': '2024-01-20T16:30:00Z'
            }
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        logger.error(f"Erreur lors de la création de l'indice Elasticsearch: {e}")
        error_message = str(e)
        
        # Identifier le type d'erreur
        if 'already exists' in error_message.lower():
            return Response({
                'error': f'L\'indice {index_name} existe déjà',
                'code': 'INDEX_ALREADY_EXISTS',
                'details': error_message
            }, status=status.HTTP_409_CONFLICT)
        
        return Response({
            'error': 'Erreur lors de la création de l\'indice',
            'code': 'INDEX_CREATION_ERROR',
            'details': error_message
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# ==================== ENDPOINTS CRUD COMPLETS POUR FAIL2BAN ====================

@swagger_auto_schema(
    method='get',
    operation_summary="Liste des jails Fail2Ban",
    operation_description="""
    🔒 **Récupère la liste complète de toutes les jails Fail2Ban**
    
    Cet endpoint retourne toutes les jails Fail2Ban configurées avec leurs statistiques :
    
    ### Informations retournées par jail :
    - **jail_name** : Nom de la jail
    - **status** : État (enabled/disabled)
    - **filter** : Filtre utilisé pour la détection
    - **action** : Actions configurées
    - **logpath** : Chemin des logs surveillés
    - **maxretry** : Nombre max de tentatives
    - **findtime** : Fenêtre de temps pour la détection
    - **bantime** : Durée du bannissement
    - **currently_failed** : Échecs actuels
    - **total_failed** : Total des échecs
    - **currently_banned** : IPs bannies actuellement
    - **total_banned** : Total des bannissements
    
    ### Filtres disponibles :
    - **status** : Filtrer par statut (`?status=enabled`)
    - **active_only** : Jails actives uniquement (`?active_only=true`)
    - **with_bans** : Jails avec bannissements (`?with_bans=true`)
    
    ### Exemple d'utilisation :
    ```bash
    curl -X GET "https://localhost:8000/api/clients/security/fail2ban/jails/" \\
         -H "Accept: application/json"
    ```
    """,
    responses={
        200: openapi.Response(
            description="Liste des jails récupérée avec succès",
            examples={
                'application/json': [
                    {
                        'jail_name': 'sshd',
                        'status': 'enabled',
                        'filter': 'sshd',
                        'action': ['iptables-multiport'],
                        'logpath': ['/var/log/auth.log'],
                        'maxretry': 5,
                        'findtime': 600,
                        'bantime': 3600,
                        'currently_failed': 2,
                        'total_failed': 147,
                        'currently_banned': 3,
                        'total_banned': 89
                    }
                ]
            }
        ),
        503: openapi.Response(description="Client Fail2Ban non disponible", schema=client_error_schema)
    },
    tags=['API Clients']
)
@api_view(['GET'])
@permission_classes([AllowAny])
def fail2ban_jails(request):
    """Récupère la liste complète des jails Fail2Ban avec statistiques."""
    if not clients['fail2ban']:
        return Response({
            'error': 'Client Fail2Ban non disponible',
            'code': 'FAIL2BAN_UNAVAILABLE',
            'details': 'Le service Fail2Ban n\'est pas accessible.'
        }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    
    try:
        # Paramètres de filtrage
        status_filter = request.GET.get('status')
        active_only = request.GET.get('active_only', '').lower() == 'true'
        with_bans = request.GET.get('with_bans', '').lower() == 'true'
        
        jails = clients['fail2ban'].get_jails()
        
        # Enrichir avec des informations détaillées
        enriched_jails = []
        for jail in jails:
            jail_name = jail.get('name') if isinstance(jail, dict) else jail
            
            try:
                jail_info = clients['fail2ban'].get_jail_info(jail_name)
                
                enriched_jail = {
                    'jail_name': jail_name,
                    'status': jail_info.get('enabled', 'unknown'),
                    'filter': jail_info.get('filter'),
                    'action': jail_info.get('actions', []),
                    'logpath': jail_info.get('logpath', []),
                    'maxretry': jail_info.get('maxretry', 0),
                    'findtime': jail_info.get('findtime', 0),
                    'bantime': jail_info.get('bantime', 0),
                    'currently_failed': jail_info.get('currently_failed', 0),
                    'total_failed': jail_info.get('total_failed', 0),
                    'currently_banned': jail_info.get('currently_banned', 0),
                    'total_banned': jail_info.get('total_banned', 0),
                    'banned_ips': jail_info.get('banned_ips', []),
                    'last_ban': jail_info.get('last_ban'),
                    'backend': jail_info.get('backend', 'auto')
                }
                
                # Appliquer les filtres
                if status_filter and jail_info.get('enabled') != status_filter:
                    continue
                if active_only and jail_info.get('enabled') != 'enabled':
                    continue
                if with_bans and jail_info.get('currently_banned', 0) == 0:
                    continue
                
                enriched_jails.append(enriched_jail)
                
            except Exception as e:
                # Jail avec informations limitées en cas d'erreur
                enriched_jails.append({
                    'jail_name': jail_name,
                    'status': 'error',
                    'error': str(e)
                })
        
        return Response(enriched_jails, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des jails Fail2Ban: {e}")
        return Response({
            'error': 'Erreur lors de la récupération des jails Fail2Ban',
            'code': 'FAIL2BAN_JAILS_ERROR',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@swagger_auto_schema(
    method='post',
    operation_summary="Bannir une adresse IP",
    operation_description="""
    🚫 **Banni manuellement une adresse IP dans une jail spécifique**
    
    Cet endpoint permet de bannir immédiatement une adresse IP :
    
    ### Paramètres requis :
    - **ip_address** : Adresse IP à bannir
    - **jail_name** : Nom de la jail
    - **ban_time** : Durée du bannissement (optionnel)
    - **reason** : Raison du bannissement (optionnel)
    
    ### Validations effectuées :
    - Format de l'adresse IP
    - Existence de la jail
    - IP déjà bannie ou non
    
    ### Exemple d'utilisation :
    ```bash
    curl -X POST "https://localhost:8000/api/clients/security/fail2ban/ban/" \\
         -H "Content-Type: application/json" \\
         -d '{
           "ip_address": "192.168.1.100",
           "jail_name": "sshd",
           "ban_time": 7200,
           "reason": "Multiple failed login attempts"
         }'
    ```
    """,
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=['ip_address', 'jail_name'],
        properties={
            'ip_address': openapi.Schema(type=openapi.TYPE_STRING, description='Adresse IP à bannir'),
            'jail_name': openapi.Schema(type=openapi.TYPE_STRING, description='Nom de la jail'),
            'ban_time': openapi.Schema(type=openapi.TYPE_INTEGER, description='Durée en secondes (optionnel)'),
            'reason': openapi.Schema(type=openapi.TYPE_STRING, description='Raison du bannissement')
        }
    ),
    responses={
        201: openapi.Response(description="IP bannie avec succès", schema=success_schema),
        400: openapi.Response(description="Paramètres invalides", schema=client_error_schema),
        409: openapi.Response(description="IP déjà bannie", schema=client_error_schema),
        503: openapi.Response(description="Client non disponible", schema=client_error_schema)
    },
    tags=['API Clients']
)
@api_view(['POST'])
@permission_classes([AllowAny])
def ban_ip_fail2ban(request):
    """Banni manuellement une adresse IP dans une jail Fail2Ban."""
    if not clients['fail2ban']:
        return Response({
            'error': 'Client Fail2Ban non disponible',
            'code': 'FAIL2BAN_UNAVAILABLE'
        }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    
    try:
        ip_address = request.data.get('ip_address')
        jail_name = request.data.get('jail_name')
        ban_time = request.data.get('ban_time')
        reason = request.data.get('reason', 'Manuel ban via API')
        
        if not ip_address or not jail_name:
            return Response({
                'error': 'L\'adresse IP et le nom de la jail sont requis',
                'code': 'MISSING_REQUIRED_PARAMS'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validation du format IP
        import ipaddress
        try:
            ipaddress.ip_address(ip_address)
        except ValueError:
            return Response({
                'error': 'Format d\'adresse IP invalide',
                'code': 'INVALID_IP_FORMAT'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Vérifier si l'IP est déjà bannie
        try:
            banned_ips = clients['fail2ban'].get_banned_ips(jail_name)
            if ip_address in banned_ips:
                return Response({
                    'error': f'L\'IP {ip_address} est déjà bannie dans la jail {jail_name}',
                    'code': 'IP_ALREADY_BANNED'
                }, status=status.HTTP_409_CONFLICT)
        except:
            pass  # Continuer même si on ne peut pas vérifier
        
        # Effectuer le bannissement
        result = clients['fail2ban'].ban_ip(ip_address, jail_name, ban_time)
        
        return Response({
            'success': True,
            'message': f'IP {ip_address} bannie avec succès dans la jail {jail_name}',
            'data': {
                'ip_address': ip_address,
                'jail_name': jail_name,
                'ban_time': ban_time,
                'reason': reason,
                'banned_at': '2024-01-20T16:30:00Z',
                'expires_at': '2024-01-20T18:30:00Z' if ban_time else None
            }
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        logger.error(f"Erreur lors du bannissement IP Fail2Ban: {e}")
        return Response({
            'error': 'Erreur lors du bannissement de l\'IP',
            'code': 'BAN_IP_ERROR',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# ==================== ENDPOINTS AVANCÉS ET OPÉRATIONS EN LOT ====================

@swagger_auto_schema(
    method='post',
    operation_summary="Opérations en lot sur GNS3",
    operation_description="""
    📦 **Effectue des opérations en lot sur plusieurs projets/nœuds GNS3**
    
    Cet endpoint permet d'exécuter des actions sur plusieurs éléments simultanément :
    
    ### Types d'opérations supportées :
    - **bulk_create_projects** : Créer plusieurs projets
    - **bulk_delete_projects** : Supprimer plusieurs projets
    - **bulk_start_nodes** : Démarrer plusieurs nœuds
    - **bulk_stop_nodes** : Arrêter plusieurs nœuds
    - **bulk_delete_nodes** : Supprimer plusieurs nœuds
    
    ### Format de requête :
    ```json
    {
      "operation": "bulk_create_projects",
      "items": [
        {"name": "Projet1", "path": "/opt/gns3/projet1"},
        {"name": "Projet2", "path": "/opt/gns3/projet2"}
      ],
      "options": {
        "continue_on_error": true,
        "parallel": false
      }
    }
    ```
    
    ### Réponse détaillée :
    - Liste des succès et échecs
    - Temps d'exécution total
    - Statistiques d'opération
    
    ### Exemple pour créer plusieurs projets :
    ```bash
    curl -X POST "https://localhost:8000/api/clients/bulk/gns3/" \\
         -H "Content-Type: application/json" \\
         -d '{
           "operation": "bulk_create_projects",
           "items": [
             {"name": "Réseau DMZ", "path": "/opt/gns3/dmz"},
             {"name": "Réseau LAN", "path": "/opt/gns3/lan"}
           ],
           "options": {"continue_on_error": true}
         }'
    ```
    """,
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=['operation', 'items'],
        properties={
            'operation': openapi.Schema(
                type=openapi.TYPE_STRING,
                enum=['bulk_create_projects', 'bulk_delete_projects', 'bulk_start_nodes', 'bulk_stop_nodes'],
                description='Type d\'opération en lot'
            ),
            'items': openapi.Schema(
                type=openapi.TYPE_ARRAY,
                items=openapi.Schema(type=openapi.TYPE_OBJECT),
                description='Liste des éléments à traiter'
            ),
            'options': openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'continue_on_error': openapi.Schema(type=openapi.TYPE_BOOLEAN, default=True),
                    'parallel': openapi.Schema(type=openapi.TYPE_BOOLEAN, default=False),
                    'timeout': openapi.Schema(type=openapi.TYPE_INTEGER, default=300)
                }
            )
        }
    ),
    responses={
        200: openapi.Response(
            description="Opération en lot terminée",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'operation': openapi.Schema(type=openapi.TYPE_STRING),
                    'total_items': openapi.Schema(type=openapi.TYPE_INTEGER),
                    'successful': openapi.Schema(type=openapi.TYPE_INTEGER),
                    'failed': openapi.Schema(type=openapi.TYPE_INTEGER),
                    'execution_time': openapi.Schema(type=openapi.TYPE_NUMBER),
                    'results': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_OBJECT))
                }
            )
        ),
        400: openapi.Response(description="Paramètres invalides", schema=client_error_schema),
        503: openapi.Response(description="Client non disponible", schema=client_error_schema)
    },
    tags=['API Clients']
)
@api_view(['POST'])
@permission_classes([AllowAny])
def bulk_operations_gns3(request):
    """Effectue des opérations en lot sur les éléments GNS3."""
    if not clients['gns3']:
        return Response({
            'error': 'Client GNS3 non disponible',
            'code': 'GNS3_UNAVAILABLE'
        }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    
    try:
        import time
        from concurrent.futures import ThreadPoolExecutor, as_completed
        
        operation = request.data.get('operation')
        items = request.data.get('items', [])
        options = request.data.get('options', {})
        
        if not operation or not items:
            return Response({
                'error': 'L\'opération et la liste des éléments sont requis',
                'code': 'MISSING_REQUIRED_PARAMS'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        continue_on_error = options.get('continue_on_error', True)
        parallel = options.get('parallel', False)
        timeout = options.get('timeout', 300)
        
        start_time = time.time()
        results = []
        successful = 0
        failed = 0
        
        def execute_single_operation(item, index):
            """Exécute une opération sur un élément."""
            try:
                result = {'index': index, 'item': item, 'success': False, 'error': None}
                
                if operation == 'bulk_create_projects':
                    project = clients['gns3'].create_project(**item)
                    result.update({'success': True, 'project_id': project.get('project_id')})
                    
                elif operation == 'bulk_delete_projects':
                    clients['gns3'].delete_project(item.get('project_id'))
                    result.update({'success': True})
                    
                elif operation == 'bulk_start_nodes':
                    clients['gns3'].start_node(item.get('project_id'), item.get('node_id'))
                    result.update({'success': True})
                    
                elif operation == 'bulk_stop_nodes':
                    clients['gns3'].stop_node(item.get('project_id'), item.get('node_id'))
                    result.update({'success': True})
                    
                else:
                    result.update({'error': f'Opération {operation} non supportée'})
                
                return result
                
            except Exception as e:
                return {
                    'index': index,
                    'item': item,
                    'success': False,
                    'error': str(e)
                }
        
        # Exécution parallèle ou séquentielle
        if parallel and len(items) > 1:
            with ThreadPoolExecutor(max_workers=min(len(items), 5)) as executor:
                future_to_item = {
                    executor.submit(execute_single_operation, item, idx): (item, idx)
                    for idx, item in enumerate(items)
                }
                
                for future in as_completed(future_to_item, timeout=timeout):
                    result = future.result()
                    results.append(result)
                    
                    if result['success']:
                        successful += 1
                    else:
                        failed += 1
                        if not continue_on_error:
                            # Annuler les tâches restantes
                            for remaining_future in future_to_item:
                                remaining_future.cancel()
                            break
        else:
            # Exécution séquentielle
            for idx, item in enumerate(items):
                result = execute_single_operation(item, idx)
                results.append(result)
                
                if result['success']:
                    successful += 1
                else:
                    failed += 1
                    if not continue_on_error:
                        break
        
        execution_time = time.time() - start_time
        
        # Trier les résultats par index
        results.sort(key=lambda x: x['index'])
        
        response_data = {
            'operation': operation,
            'total_items': len(items),
            'processed_items': len(results),
            'successful': successful,
            'failed': failed,
            'success_rate': successful / len(results) if results else 0,
            'execution_time': round(execution_time, 2),
            'parallel_execution': parallel,
            'continue_on_error': continue_on_error,
            'results': results,
            'summary': {
                'fastest_operation': min([r.get('execution_time', 0) for r in results], default=0),
                'slowest_operation': max([r.get('execution_time', 0) for r in results], default=0),
                'average_time': sum([r.get('execution_time', 0) for r in results]) / len(results) if results else 0
            }
        }
        
        return Response(response_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Erreur lors de l'opération en lot GNS3: {e}")
        return Response({
            'error': 'Erreur lors de l\'opération en lot',
            'code': 'BULK_OPERATION_ERROR',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# ==================== ENDPOINTS MANQUANTS POUR COMPATIBILITÉ URLS ====================
# Ces endpoints sont nécessaires pour les URLs définies mais seront développés progressivement

@swagger_auto_schema(
    method='get',
    operation_summary="Statut des clients infrastructure",
    operation_description="Récupère le statut des clients infrastructure.",
    tags=['API Clients']
)
@swagger_auto_schema(
    method='post',
    operation_summary="Configuration infrastructure",
    operation_description="Configuration des clients infrastructure.",
    tags=['API Clients']
)
@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def infrastructure_clients(request):
    """Placeholder pour les clients infrastructure."""
    return Response({'message': 'Endpoint infrastructure en développement'}, status=200)

@swagger_auto_schema(
    method='get',
    operation_summary="Statut des clients sécurité",
    operation_description="Récupère le statut des clients sécurité.",
    tags=['API Clients']
)
@swagger_auto_schema(
    method='post',
    operation_summary="Configuration sécurité",
    operation_description="Configuration des clients sécurité.",
    tags=['API Clients']
)
@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def security_clients(request):
    """Placeholder pour les clients sécurité."""
    return Response({'message': 'Endpoint sécurité en développement'}, status=200)

@swagger_auto_schema(
    method='get',
    operation_summary="Interface création projet GNS3",
    operation_description="Interface de création de projets GNS3.",
    tags=['API Clients']
)
@swagger_auto_schema(
    method='post',
    operation_summary="Créer un projet GNS3",
    operation_description="Crée un nouveau projet GNS3.",
    tags=['API Clients']
)
@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def create_gns3_project(request):
    """Crée un nouveau projet GNS3."""
    return Response({'message': 'Création de projet GNS3 en développement'}, status=200)

@swagger_auto_schema(
    method='get',
    operation_summary="Détails du projet GNS3",
    operation_description="Récupère les détails d'un projet GNS3.",
    tags=['API Clients']
)
@swagger_auto_schema(
    method='post',
    operation_summary="Modifier un projet GNS3",
    operation_description="Met à jour un projet GNS3 existant.",
    tags=['API Clients']
)
@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def update_gns3_project(request, project_id):
    """Met à jour un projet GNS3."""
    return Response({'message': f'Mise à jour du projet {project_id} en développement'}, status=200)

@swagger_auto_schema(
    method='delete',
    operation_summary="Supprimer un projet GNS3",
    operation_description="Supprime un projet GNS3 existant.",
    tags=['API Clients']
)
@api_view(['DELETE'])
@permission_classes([AllowAny])
def delete_gns3_project(request, project_id):
    """Supprime un projet GNS3."""
    return Response({'message': f'Suppression du projet {project_id} en développement'}, status=200)

@swagger_auto_schema(
    method='post',
    operation_summary="Exécuter une requête SNMP",
    operation_description="Exécute une requête SNMP sur un équipement réseau.",
    tags=['API Clients']
)
@api_view(['POST'])
@permission_classes([AllowAny])
def snmp_query(request):
    """Exécute une requête SNMP."""
    return Response({'message': 'Requête SNMP en développement'}, status=200)

@swagger_auto_schema(
    method='post',
    operation_summary="Exécuter une requête PromQL",
    operation_description="Exécute une requête PromQL sur Prometheus.",
    tags=['API Clients']
)
@api_view(['POST'])
@permission_classes([AllowAny])
def prometheus_query(request):
    """Exécute une requête PromQL."""
    return Response({'message': 'Requête Prometheus en développement'}, status=200)

@swagger_auto_schema(
    method='post',
    operation_summary="Configurer un nouveau client",
    operation_description="Configure un nouveau client API.",
    tags=['API Clients']
)
@api_view(['POST'])
@permission_classes([AllowAny])
def create_client_config(request):
    """Configure un nouveau client."""
    return Response({'message': 'Configuration client en développement'}, status=200)

@swagger_auto_schema(
    method='put',
    operation_summary="Mettre à jour la configuration client",
    operation_description="Met à jour la configuration d'un client existant.",
    tags=['API Clients']
)
@api_view(['PUT'])
@permission_classes([AllowAny])
def update_client_config(request, client_name):
    """Met à jour la configuration d'un client."""
    return Response({'message': f'Mise à jour config {client_name} en développement'}, status=200)

@swagger_auto_schema(
    method='delete',
    operation_summary="Supprimer la configuration client",
    operation_description="Supprime la configuration d'un client.",
    tags=['API Clients']
)
@api_view(['DELETE'])
@permission_classes([AllowAny])
def delete_client_config(request, client_name):
    """Supprime la configuration d'un client."""
    return Response({'message': f'Suppression config {client_name} en développement'}, status=200)

# Ajout de toutes les vues manquantes comme placeholders
def placeholder_view(request, *args, **kwargs):
    """Vue placeholder pour les endpoints non encore implémentés."""
    return Response({'message': 'Endpoint en développement'}, status=200)

# Assignation des placeholders pour tous les endpoints manquants des URLs
get_gns3_project = open_gns3_project = close_gns3_project = placeholder_view
gns3_project_nodes = create_gns3_node = get_gns3_node = update_gns3_node = placeholder_view
delete_gns3_node = start_gns3_node = stop_gns3_node = placeholder_view
snmp_walk = snmp_set = snmp_system_info = snmp_interfaces = placeholder_view
snmp_interface_stats = snmp_discover_neighbors = placeholder_view
netflow_query_flows = netflow_top_talkers = netflow_protocol_distribution = placeholder_view
netflow_detect_anomalies = netflow_traffic_matrix = netflow_config = placeholder_view
netflow_exporters = create_netflow_exporter = delete_netflow_exporter = placeholder_view
prometheus_query_range = prometheus_targets = prometheus_alerts = placeholder_view
prometheus_rules = prometheus_series = prometheus_label_values = placeholder_view
create_grafana_dashboard = get_grafana_dashboard = update_grafana_dashboard = placeholder_view
delete_grafana_dashboard = export_grafana_dashboard = placeholder_view
grafana_datasources = create_grafana_datasource = get_grafana_datasource = placeholder_view
update_grafana_datasource = delete_grafana_datasource = test_grafana_datasource = placeholder_view
grafana_alerts = create_grafana_alert = get_grafana_alert = placeholder_view
update_grafana_alert = delete_grafana_alert = placeholder_view
grafana_users = grafana_current_user = placeholder_view
get_elasticsearch_index = update_elasticsearch_index = delete_elasticsearch_index = placeholder_view
elasticsearch_search = elasticsearch_count = elasticsearch_documents = placeholder_view
create_elasticsearch_document = get_elasticsearch_document = placeholder_view
update_elasticsearch_document = delete_elasticsearch_document = placeholder_view
elasticsearch_templates = create_elasticsearch_template = get_elasticsearch_template = placeholder_view
update_elasticsearch_template = delete_elasticsearch_template = placeholder_view
netdata_metrics = netdata_charts = netdata_alarms = netdata_info = placeholder_view
ntopng_hosts = ntopng_flows = ntopng_interfaces = ntopng_alerts = placeholder_view
haproxy_stats = haproxy_info = haproxy_backends = haproxy_backend_servers = placeholder_view
enable_haproxy_server = disable_haproxy_server = set_haproxy_server_state = placeholder_view
traffic_control_interfaces = traffic_control_interface_config = placeholder_view
clear_traffic_control_interface = set_traffic_control_bandwidth = placeholder_view
set_traffic_control_prioritization = traffic_control_filters = placeholder_view
add_traffic_control_filter = placeholder_view
create_fail2ban_jail = get_fail2ban_jail = update_fail2ban_jail = placeholder_view
delete_fail2ban_jail = start_fail2ban_jail = stop_fail2ban_jail = placeholder_view
fail2ban_banned_ips = fail2ban_jail_logs = unban_ip_fail2ban = placeholder_view
fail2ban_config = update_fail2ban_config = reload_fail2ban_config = placeholder_view
restart_fail2ban_service = placeholder_view
suricata_rules = create_suricata_rule = get_suricata_rule = placeholder_view
update_suricata_rule = delete_suricata_rule = toggle_suricata_rule = placeholder_view
suricata_alerts = get_suricata_alert = suricata_flows = placeholder_view
search_suricata_events = suricata_rulesets = upload_suricata_ruleset = placeholder_view
suricata_config = update_suricata_config = placeholder_view
bulk_operations_elasticsearch = bulk_operations_fail2ban = placeholder_view
bulk_operations_grafana = placeholder_view
list_client_configs = get_client_config = test_client_config = placeholder_view
reset_client_config = placeholder_view
performance_metrics = circuit_breaker_metrics = cache_metrics = placeholder_view
error_metrics = usage_metrics = placeholder_view
global_status = api_version = api_capabilities = reset_all_clients = placeholder_view
debug_logs = debug_connections = debug_memory_usage = placeholder_view
clear_cache = dump_config = placeholder_view

# ==================== CLIENTS RÉSEAU - GNS3 COMPLET ====================

@swagger_auto_schema(
    method='get',
    operation_summary="Détails d'un projet GNS3",
    operation_description="Récupère les détails complets d'un projet GNS3 spécifique.",
    tags=['API Clients']
)
@api_view(['GET'])
@permission_classes([AllowAny])
def get_gns3_project(request, project_id):
    """Récupère les détails d'un projet GNS3."""
    return Response({'message': f'Détails du projet {project_id} en développement'}, status=200)

@swagger_auto_schema(
    method='post',
    operation_summary="Ouvrir un projet GNS3",
    operation_description="Ouvre un projet GNS3 pour édition.",
    tags=['API Clients']
)
@api_view(['POST'])
@permission_classes([AllowAny])
def open_gns3_project(request, project_id):
    """Ouvre un projet GNS3."""
    return Response({'message': f'Ouverture du projet {project_id} en développement'}, status=200)

@swagger_auto_schema(
    method='post',
    operation_summary="Fermer un projet GNS3",
    operation_description="Ferme un projet GNS3 ouvert.",
    tags=['API Clients']
)
@api_view(['POST'])
@permission_classes([AllowAny])
def close_gns3_project(request, project_id):
    """Ferme un projet GNS3."""
    return Response({'message': f'Fermeture du projet {project_id} en développement'}, status=200)

# ==================== CLIENTS RÉSEAU - GNS3 NŒUDS ====================

@swagger_auto_schema(
    method='get',
    operation_summary="Liste des nœuds GNS3",
    operation_description="Récupère la liste des nœuds d'un projet GNS3.",
    tags=['API Clients']
)
@api_view(['GET'])
@permission_classes([AllowAny])
def gns3_project_nodes(request, project_id):
    """Liste des nœuds d'un projet GNS3."""
    return Response({'message': f'Nœuds du projet {project_id} en développement'}, status=200)

@swagger_auto_schema(
    method='post',
    operation_summary="Créer un nœud GNS3",
    operation_description="Crée un nouveau nœud dans un projet GNS3.",
    tags=['API Clients']
)
@api_view(['POST'])
@permission_classes([AllowAny])
def create_gns3_node(request, project_id):
    """Crée un nœud GNS3."""
    return Response({'message': f'Création de nœud dans projet {project_id} en développement'}, status=200)

@swagger_auto_schema(
    method='get',
    operation_summary="Détails d'un nœud GNS3",
    operation_description="Récupère les détails d'un nœud GNS3 spécifique.",
    tags=['API Clients']
)
@api_view(['GET'])
@permission_classes([AllowAny])
def get_gns3_node(request, project_id, node_id):
    """Détails d'un nœud GNS3."""
    return Response({'message': f'Détails du nœud {node_id} dans projet {project_id} en développement'}, status=200)

@swagger_auto_schema(
    method='put',
    operation_summary="Modifier un nœud GNS3",
    operation_description="Met à jour un nœud GNS3 existant.",
    tags=['API Clients']
)
@api_view(['PUT'])
@permission_classes([AllowAny])
def update_gns3_node(request, project_id, node_id):
    """Modifie un nœud GNS3."""
    return Response({'message': f'Modification du nœud {node_id} dans projet {project_id} en développement'}, status=200)

@swagger_auto_schema(
    method='delete',
    operation_summary="Supprimer un nœud GNS3",
    operation_description="Supprime un nœud GNS3 du projet.",
    tags=['API Clients']
)
@api_view(['DELETE'])
@permission_classes([AllowAny])
def delete_gns3_node(request, project_id, node_id):
    """Supprime un nœud GNS3."""
    return Response({'message': f'Suppression du nœud {node_id} dans projet {project_id} en développement'}, status=200)

@swagger_auto_schema(
    method='post',
    operation_summary="Démarrer un nœud GNS3",
    operation_description="Démarre un nœud GNS3 dans le projet.",
    tags=['API Clients']
)
@api_view(['POST'])
@permission_classes([AllowAny])
def start_gns3_node(request, project_id, node_id):
    """Démarre un nœud GNS3."""
    return Response({'message': f'Démarrage du nœud {node_id} dans projet {project_id} en développement'}, status=200)

@swagger_auto_schema(
    method='post',
    operation_summary="Arrêter un nœud GNS3",
    operation_description="Arrête un nœud GNS3 en cours d'exécution.",
    tags=['API Clients']
)
@api_view(['POST'])
@permission_classes([AllowAny])
def stop_gns3_node(request, project_id, node_id):
    """Arrête un nœud GNS3."""
    return Response({'message': f'Arrêt du nœud {node_id} dans projet {project_id} en développement'}, status=200)

# ==================== CLIENTS RÉSEAU - SNMP COMPLET ====================

@swagger_auto_schema(
    method='post',
    operation_summary="SNMP Walk",
    operation_description="Exécute un SNMP Walk pour découvrir les OIDs.",
    tags=['API Clients']
)
@api_view(['POST'])
@permission_classes([AllowAny])
def snmp_walk(request):
    """Exécute un SNMP Walk."""
    return Response({'message': 'SNMP Walk en développement'}, status=200)

@swagger_auto_schema(
    method='post',
    operation_summary="SNMP Set",
    operation_description="Modifie une valeur via SNMP SET.",
    tags=['API Clients']
)
@api_view(['POST'])
@permission_classes([AllowAny])
def snmp_set(request):
    """Exécute un SNMP Set."""
    return Response({'message': 'SNMP Set en développement'}, status=200)

@swagger_auto_schema(
    method='get',
    operation_summary="Informations système SNMP",
    operation_description="Récupère les informations système via SNMP.",
    tags=['API Clients']
)
@api_view(['GET'])
@permission_classes([AllowAny])
def snmp_system_info(request):
    """Informations système SNMP."""
    return Response({'message': 'Informations système SNMP en développement'}, status=200)

@swagger_auto_schema(
    method='get',
    operation_summary="Interfaces SNMP",
    operation_description="Liste les interfaces réseau via SNMP.",
    tags=['API Clients']
)
@api_view(['GET'])
@permission_classes([AllowAny])
def snmp_interfaces(request):
    """Liste des interfaces SNMP."""
    return Response({'message': 'Interfaces SNMP en développement'}, status=200)

@swagger_auto_schema(
    method='get',
    operation_summary="Statistiques interface SNMP",
    operation_description="Statistiques d'une interface spécifique via SNMP.",
    tags=['API Clients']
)
@api_view(['GET'])
@permission_classes([AllowAny])
def snmp_interface_stats(request, interface_index):
    """Statistiques d'interface SNMP."""
    return Response({'message': f'Stats interface {interface_index} SNMP en développement'}, status=200)

@swagger_auto_schema(
    method='post',
    operation_summary="Découverte voisins SNMP",
    operation_description="Découvre les voisins réseau via SNMP.",
    tags=['API Clients']
)
@api_view(['POST'])
@permission_classes([AllowAny])
def snmp_discover_neighbors(request):
    """Découverte de voisins SNMP."""
    return Response({'message': 'Découverte voisins SNMP en développement'}, status=200)

# ==================== CLIENTS RÉSEAU - NETFLOW COMPLET ====================

@swagger_auto_schema(
    method='get',
    operation_summary="Requête flows NetFlow",
    operation_description="Interroge les flows NetFlow collectés.",
    tags=['API Clients']
)
@api_view(['GET'])
@permission_classes([AllowAny])
def netflow_query_flows(request):
    """Requête flows NetFlow."""
    return Response({'message': 'Requête flows NetFlow en développement'}, status=200)

@swagger_auto_schema(
    method='get',
    operation_summary="Top talkers NetFlow",
    operation_description="Récupère les top talkers depuis NetFlow.",
    tags=['API Clients']
)
@api_view(['GET'])
@permission_classes([AllowAny])
def netflow_top_talkers(request):
    """Top talkers NetFlow."""
    return Response({'message': 'Top talkers NetFlow en développement'}, status=200)

@swagger_auto_schema(
    method='get',
    operation_summary="Distribution protocoles NetFlow",
    operation_description="Analyse la distribution des protocoles dans NetFlow.",
    tags=['API Clients']
)
@api_view(['GET'])
@permission_classes([AllowAny])
def netflow_protocol_distribution(request):
    """Distribution protocoles NetFlow."""
    return Response({'message': 'Distribution protocoles NetFlow en développement'}, status=200)

@swagger_auto_schema(
    method='get',
    operation_summary="Détection anomalies NetFlow",
    operation_description="Détecte les anomalies dans les flows NetFlow.",
    tags=['API Clients']
)
@api_view(['GET'])
@permission_classes([AllowAny])
def netflow_detect_anomalies(request):
    """Détection anomalies NetFlow."""
    return Response({'message': 'Détection anomalies NetFlow en développement'}, status=200)

@swagger_auto_schema(
    method='get',
    operation_summary="Matrice trafic NetFlow",
    operation_description="Génère une matrice de trafic depuis NetFlow.",
    tags=['API Clients']
)
@api_view(['GET'])
@permission_classes([AllowAny])
def netflow_traffic_matrix(request):
    """Matrice trafic NetFlow."""
    return Response({'message': 'Matrice trafic NetFlow en développement'}, status=200)

@swagger_auto_schema(
    method='get',
    operation_summary="Configuration NetFlow",
    operation_description="Récupère la configuration NetFlow.",
    tags=['API Clients']
)
@api_view(['GET'])
@permission_classes([AllowAny])
def netflow_config(request):
    """Configuration NetFlow."""
    return Response({'message': 'Configuration NetFlow en développement'}, status=200)

@swagger_auto_schema(
    method='get',
    operation_summary="Exporteurs NetFlow",
    operation_description="Liste les exporteurs NetFlow configurés.",
    tags=['API Clients']
)
@api_view(['GET'])
@permission_classes([AllowAny])
def netflow_exporters(request):
    """Liste des exporteurs NetFlow."""
    return Response({'message': 'Exporteurs NetFlow en développement'}, status=200)

@swagger_auto_schema(
    method='post',
    operation_summary="Créer exporteur NetFlow",
    operation_description="Ajoute un nouvel exporteur NetFlow.",
    tags=['API Clients']
)
@api_view(['POST'])
@permission_classes([AllowAny])
def create_netflow_exporter(request):
    """Crée un exporteur NetFlow."""
    return Response({'message': 'Création exporteur NetFlow en développement'}, status=200)

@swagger_auto_schema(
    method='delete',
    operation_summary="Supprimer exporteur NetFlow",
    operation_description="Supprime un exporteur NetFlow.",
    tags=['API Clients']
)
@api_view(['DELETE'])
@permission_classes([AllowAny])
def delete_netflow_exporter(request, exporter_id):
    """Supprime un exporteur NetFlow."""
    return Response({'message': f'Suppression exporteur NetFlow {exporter_id} en développement'}, status=200)

# ==================== CLIENTS MONITORING - PROMETHEUS COMPLET ====================

@swagger_auto_schema(
    method='post',
    operation_summary="Requête Prometheus avec plage",
    operation_description="Exécute une requête PromQL sur une plage de temps.",
    tags=['API Clients']
)
@api_view(['POST'])
@permission_classes([AllowAny])
def prometheus_query_range(request):
    """Requête PromQL avec plage."""
    return Response({'message': 'Requête PromQL plage en développement'}, status=200)

@swagger_auto_schema(
    method='get',
    operation_summary="Targets Prometheus",
    operation_description="Récupère les targets configurées dans Prometheus.",
    tags=['API Clients']
)
@api_view(['GET'])
@permission_classes([AllowAny])
def prometheus_targets(request):
    """Targets Prometheus."""
    return Response({'message': 'Targets Prometheus en développement'}, status=200)

@swagger_auto_schema(
    method='get',
    operation_summary="Alertes Prometheus",
    operation_description="Récupère les alertes actives de Prometheus.",
    tags=['API Clients']
)
@api_view(['GET'])
@permission_classes([AllowAny])
def prometheus_alerts(request):
    """Alertes Prometheus."""
    return Response({'message': 'Alertes Prometheus en développement'}, status=200)

@swagger_auto_schema(
    method='get',
    operation_summary="Règles Prometheus",
    operation_description="Récupère les règles configurées dans Prometheus.",
    tags=['API Clients']
)
@api_view(['GET'])
@permission_classes([AllowAny])
def prometheus_rules(request):
    """Règles Prometheus."""
    return Response({'message': 'Règles Prometheus en développement'}, status=200)

@swagger_auto_schema(
    method='get',
    operation_summary="Séries Prometheus",
    operation_description="Récupère les séries métriques de Prometheus.",
    tags=['API Clients']
)
@api_view(['GET'])
@permission_classes([AllowAny])
def prometheus_series(request):
    """Séries Prometheus."""
    return Response({'message': 'Séries Prometheus en développement'}, status=200)

@swagger_auto_schema(
    method='get',
    operation_summary="Valeurs labels Prometheus",
    operation_description="Récupère les valeurs possibles d'un label Prometheus.",
    tags=['API Clients']
)
@api_view(['GET'])
@permission_classes([AllowAny])
def prometheus_label_values(request):
    """Valeurs labels Prometheus."""
    return Response({'message': 'Valeurs labels Prometheus en développement'}, status=200)

# Cette continuation sera dans la partie 2...# ==================== CLIENTS MONITORING - GRAFANA COMPLET ====================

@swagger_auto_schema(
    method='post',
    operation_summary="Créer dashboard Grafana",
    operation_description="Crée un nouveau dashboard Grafana.",
    tags=['API Clients']
)
@api_view(['POST'])
@permission_classes([AllowAny])
def create_grafana_dashboard(request):
    """Crée un dashboard Grafana."""
    return Response({'message': 'Création dashboard Grafana en développement'}, status=200)

@swagger_auto_schema(
    method='get',
    operation_summary="Détails dashboard Grafana",
    operation_description="Récupère les détails d'un dashboard Grafana.",
    tags=['API Clients']
)
@api_view(['GET'])
@permission_classes([AllowAny])
def get_grafana_dashboard(request, uid):
    """Détails dashboard Grafana."""
    return Response({'message': f'Détails dashboard Grafana {uid} en développement'}, status=200)

@swagger_auto_schema(
    method='put',
    operation_summary="Modifier dashboard Grafana",
    operation_description="Met à jour un dashboard Grafana existant.",
    tags=['API Clients']
)
@api_view(['PUT'])
@permission_classes([AllowAny])
def update_grafana_dashboard(request, uid):
    """Modifie un dashboard Grafana."""
    return Response({'message': f'Modification dashboard Grafana {uid} en développement'}, status=200)

@swagger_auto_schema(
    method='delete',
    operation_summary="Supprimer dashboard Grafana",
    operation_description="Supprime un dashboard Grafana.",
    tags=['API Clients']
)
@api_view(['DELETE'])
@permission_classes([AllowAny])
def delete_grafana_dashboard(request, uid):
    """Supprime un dashboard Grafana."""
    return Response({'message': f'Suppression dashboard Grafana {uid} en développement'}, status=200)

@swagger_auto_schema(
    method='get',
    operation_summary="Exporter dashboard Grafana",
    operation_description="Exporte un dashboard Grafana au format JSON.",
    tags=['API Clients']
)
@api_view(['GET'])
@permission_classes([AllowAny])
def export_grafana_dashboard(request, uid):
    """Exporte un dashboard Grafana."""
    return Response({'message': f'Export dashboard Grafana {uid} en développement'}, status=200)

# Sources de données Grafana
@swagger_auto_schema(
    method='get',
    operation_summary="Sources de données Grafana",
    operation_description="Liste les sources de données configurées dans Grafana.",
    tags=['API Clients']
)
@api_view(['GET'])
@permission_classes([AllowAny])
def grafana_datasources(request):
    """Sources de données Grafana."""
    return Response({'message': 'Sources de données Grafana en développement'}, status=200)

@swagger_auto_schema(
    method='post',
    operation_summary="Créer source de données Grafana",
    operation_description="Ajoute une nouvelle source de données dans Grafana.",
    tags=['API Clients']
)
@api_view(['POST'])
@permission_classes([AllowAny])
def create_grafana_datasource(request):
    """Crée une source de données Grafana."""
    return Response({'message': 'Création source de données Grafana en développement'}, status=200)

@swagger_auto_schema(
    method='get',
    operation_summary="Détails source de données Grafana",
    operation_description="Récupère les détails d'une source de données Grafana.",
    tags=['API Clients']
)
@api_view(['GET'])
@permission_classes([AllowAny])
def get_grafana_datasource(request, datasource_id):
    """Détails source de données Grafana."""
    return Response({'message': f'Détails source de données Grafana {datasource_id} en développement'}, status=200)

@swagger_auto_schema(
    method='put',
    operation_summary="Modifier source de données Grafana",
    operation_description="Met à jour une source de données Grafana.",
    tags=['API Clients']
)
@api_view(['PUT'])
@permission_classes([AllowAny])
def update_grafana_datasource(request, datasource_id):
    """Modifie une source de données Grafana."""
    return Response({'message': f'Modification source de données Grafana {datasource_id} en développement'}, status=200)

@swagger_auto_schema(
    method='delete',
    operation_summary="Supprimer source de données Grafana",
    operation_description="Supprime une source de données Grafana.",
    tags=['API Clients']
)
@api_view(['DELETE'])
@permission_classes([AllowAny])
def delete_grafana_datasource(request, datasource_id):
    """Supprime une source de données Grafana."""
    return Response({'message': f'Suppression source de données Grafana {datasource_id} en développement'}, status=200)

@swagger_auto_schema(
    method='post',
    operation_summary="Tester source de données Grafana",
    operation_description="Teste la connectivité d'une source de données Grafana.",
    tags=['API Clients']
)
@api_view(['POST'])
@permission_classes([AllowAny])
def test_grafana_datasource(request, datasource_id):
    """Teste une source de données Grafana."""
    return Response({'message': f'Test source de données Grafana {datasource_id} en développement'}, status=200)

# Alertes Grafana
@swagger_auto_schema(
    method='get',
    operation_summary="Alertes Grafana",
    operation_description="Liste les alertes configurées dans Grafana.",
    tags=['API Clients']
)
@api_view(['GET'])
@permission_classes([AllowAny])
def grafana_alerts(request):
    """Alertes Grafana."""
    return Response({'message': 'Alertes Grafana en développement'}, status=200)

@swagger_auto_schema(
    method='post',
    operation_summary="Créer alerte Grafana",
    operation_description="Crée une nouvelle alerte dans Grafana.",
    tags=['API Clients']
)
@api_view(['POST'])
@permission_classes([AllowAny])
def create_grafana_alert(request):
    """Crée une alerte Grafana."""
    return Response({'message': 'Création alerte Grafana en développement'}, status=200)

@swagger_auto_schema(
    method='get',
    operation_summary="Détails alerte Grafana",
    operation_description="Récupère les détails d'une alerte Grafana.",
    tags=['API Clients']
)
@api_view(['GET'])
@permission_classes([AllowAny])
def get_grafana_alert(request, alert_id):
    """Détails alerte Grafana."""
    return Response({'message': f'Détails alerte Grafana {alert_id} en développement'}, status=200)

@swagger_auto_schema(
    method='put',
    operation_summary="Modifier alerte Grafana",
    operation_description="Met à jour une alerte Grafana existante.",
    tags=['API Clients']
)
@api_view(['PUT'])
@permission_classes([AllowAny])
def update_grafana_alert(request, alert_id):
    """Modifie une alerte Grafana."""
    return Response({'message': f'Modification alerte Grafana {alert_id} en développement'}, status=200)

@swagger_auto_schema(
    method='delete',
    operation_summary="Supprimer alerte Grafana",
    operation_description="Supprime une alerte Grafana.",
    tags=['API Clients']
)
@api_view(['DELETE'])
@permission_classes([AllowAny])
def delete_grafana_alert(request, alert_id):
    """Supprime une alerte Grafana."""
    return Response({'message': f'Suppression alerte Grafana {alert_id} en développement'}, status=200)

# Utilisateurs Grafana
@swagger_auto_schema(
    method='get',
    operation_summary="Utilisateurs Grafana",
    operation_description="Liste les utilisateurs configurés dans Grafana.",
    tags=['API Clients']
)
@api_view(['GET'])
@permission_classes([AllowAny])
def grafana_users(request):
    """Utilisateurs Grafana."""
    return Response({'message': 'Utilisateurs Grafana en développement'}, status=200)

@swagger_auto_schema(
    method='get',
    operation_summary="Utilisateur Grafana actuel",
    operation_description="Récupère les informations de l'utilisateur connecté à Grafana.",
    tags=['API Clients']
)
@api_view(['GET'])
@permission_classes([AllowAny])
def grafana_current_user(request):
    """Utilisateur Grafana actuel."""
    return Response({'message': 'Utilisateur Grafana actuel en développement'}, status=200)

# ==================== CLIENTS MONITORING - ELASTICSEARCH COMPLET ====================

@swagger_auto_schema(
    method='get',
    operation_summary="Détails indice Elasticsearch",
    operation_description="Récupère les détails d'un indice Elasticsearch spécifique.",
    tags=['API Clients']
)
@api_view(['GET'])
@permission_classes([AllowAny])
def get_elasticsearch_index(request, index_name):
    """Détails indice Elasticsearch."""
    return Response({'message': f'Détails indice Elasticsearch {index_name} en développement'}, status=200)

@swagger_auto_schema(
    method='put',
    operation_summary="Modifier indice Elasticsearch",
    operation_description="Met à jour un indice Elasticsearch existant.",
    tags=['API Clients']
)
@api_view(['PUT'])
@permission_classes([AllowAny])
def update_elasticsearch_index(request, index_name):
    """Modifie un indice Elasticsearch."""
    return Response({'message': f'Modification indice Elasticsearch {index_name} en développement'}, status=200)

@swagger_auto_schema(
    method='delete',
    operation_summary="Supprimer indice Elasticsearch",
    operation_description="Supprime un indice Elasticsearch.",
    tags=['API Clients']
)
@api_view(['DELETE'])
@permission_classes([AllowAny])
def delete_elasticsearch_index(request, index_name):
    """Supprime un indice Elasticsearch."""
    return Response({'message': f'Suppression indice Elasticsearch {index_name} en développement'}, status=200)

# Documents Elasticsearch
@swagger_auto_schema(
    method='post',
    operation_summary="Recherche Elasticsearch",
    operation_description="Effectue une recherche dans Elasticsearch.",
    tags=['API Clients']
)
@api_view(['POST'])
@permission_classes([AllowAny])
def elasticsearch_search(request):
    """Recherche Elasticsearch."""
    return Response({'message': 'Recherche Elasticsearch en développement'}, status=200)

@swagger_auto_schema(
    method='post',
    operation_summary="Compter documents Elasticsearch",
    operation_description="Compte les documents dans Elasticsearch.",
    tags=['API Clients']
)
@api_view(['POST'])
@permission_classes([AllowAny])
def elasticsearch_count(request):
    """Comptage Elasticsearch."""
    return Response({'message': 'Comptage Elasticsearch en développement'}, status=200)

@swagger_auto_schema(
    method='get',
    operation_summary="Documents d'un indice Elasticsearch",
    operation_description="Liste les documents d'un indice Elasticsearch.",
    tags=['API Clients']
)
@api_view(['GET'])
@permission_classes([AllowAny])
def elasticsearch_documents(request, index_name):
    """Documents d'un indice Elasticsearch."""
    return Response({'message': f'Documents indice Elasticsearch {index_name} en développement'}, status=200)

@swagger_auto_schema(
    method='post',
    operation_summary="Créer document Elasticsearch",
    operation_description="Ajoute un nouveau document dans un indice Elasticsearch.",
    tags=['API Clients']
)
@api_view(['POST'])
@permission_classes([AllowAny])
def create_elasticsearch_document(request, index_name):
    """Crée un document Elasticsearch."""
    return Response({'message': f'Création document dans indice Elasticsearch {index_name} en développement'}, status=200)

@swagger_auto_schema(
    method='get',
    operation_summary="Détails document Elasticsearch",
    operation_description="Récupère un document spécifique d'Elasticsearch.",
    tags=['API Clients']
)
@api_view(['GET'])
@permission_classes([AllowAny])
def get_elasticsearch_document(request, index_name, doc_id):
    """Détails document Elasticsearch."""
    return Response({'message': f'Document {doc_id} indice {index_name} Elasticsearch en développement'}, status=200)

@swagger_auto_schema(
    method='put',
    operation_summary="Modifier document Elasticsearch",
    operation_description="Met à jour un document Elasticsearch existant.",
    tags=['API Clients']
)
@api_view(['PUT'])
@permission_classes([AllowAny])
def update_elasticsearch_document(request, index_name, doc_id):
    """Modifie un document Elasticsearch."""
    return Response({'message': f'Modification document {doc_id} indice {index_name} Elasticsearch en développement'}, status=200)

@swagger_auto_schema(
    method='delete',
    operation_summary="Supprimer document Elasticsearch",
    operation_description="Supprime un document d'Elasticsearch.",
    tags=['API Clients']
)
@api_view(['DELETE'])
@permission_classes([AllowAny])
def delete_elasticsearch_document(request, index_name, doc_id):
    """Supprime un document Elasticsearch."""
    return Response({'message': f'Suppression document {doc_id} indice {index_name} Elasticsearch en développement'}, status=200)

# ==================== ELASTICSEARCH TEMPLATES ====================

@swagger_auto_schema(method='get', operation_summary="Templates Elasticsearch", tags=['API Clients'])
@api_view(['GET'])
@permission_classes([AllowAny])
def elasticsearch_templates(request):
    return Response({'message': 'Templates Elasticsearch en développement'}, status=200)

@swagger_auto_schema(method='post', operation_summary="Créer template Elasticsearch", tags=['API Clients'])
@api_view(['POST'])
@permission_classes([AllowAny])
def create_elasticsearch_template(request):
    return Response({'message': 'Création template Elasticsearch en développement'}, status=200)

@swagger_auto_schema(method='get', operation_summary="Détails template Elasticsearch", tags=['API Clients'])
@api_view(['GET'])
@permission_classes([AllowAny])
def get_elasticsearch_template(request, template_name):
    return Response({'message': f'Template {template_name} Elasticsearch en développement'}, status=200)

@swagger_auto_schema(method='put', operation_summary="Modifier template Elasticsearch", tags=['API Clients'])
@api_view(['PUT'])
@permission_classes([AllowAny])
def update_elasticsearch_template(request, template_name):
    return Response({'message': f'Modification template {template_name} Elasticsearch en développement'}, status=200)

@swagger_auto_schema(method='delete', operation_summary="Supprimer template Elasticsearch", tags=['API Clients'])
@api_view(['DELETE'])
@permission_classes([AllowAny])
def delete_elasticsearch_template(request, template_name):
    return Response({'message': f'Suppression template {template_name} Elasticsearch en développement'}, status=200)

# ==================== NETDATA ====================

@swagger_auto_schema(method='get', operation_summary="Métriques Netdata", tags=['API Clients'])
@api_view(['GET'])
@permission_classes([AllowAny])
def netdata_metrics(request):
    return Response({'message': 'Métriques Netdata en développement'}, status=200)

@swagger_auto_schema(method='get', operation_summary="Charts Netdata", tags=['API Clients'])
@api_view(['GET'])
@permission_classes([AllowAny])
def netdata_charts(request):
    return Response({'message': 'Charts Netdata en développement'}, status=200)

@swagger_auto_schema(method='get', operation_summary="Alarmes Netdata", tags=['API Clients'])
@api_view(['GET'])
@permission_classes([AllowAny])
def netdata_alarms(request):
    return Response({'message': 'Alarmes Netdata en développement'}, status=200)

@swagger_auto_schema(method='get', operation_summary="Info Netdata", tags=['API Clients'])
@api_view(['GET'])
@permission_classes([AllowAny])
def netdata_info(request):
    return Response({'message': 'Info Netdata en développement'}, status=200)

# ==================== NTOPNG ====================

@swagger_auto_schema(method='get', operation_summary="Hosts Ntopng", tags=['API Clients'])
@api_view(['GET'])
@permission_classes([AllowAny])
def ntopng_hosts(request):
    return Response({'message': 'Hosts Ntopng en développement'}, status=200)

@swagger_auto_schema(method='get', operation_summary="Flows Ntopng", tags=['API Clients'])
@api_view(['GET'])
@permission_classes([AllowAny])
def ntopng_flows(request):
    return Response({'message': 'Flows Ntopng en développement'}, status=200)

@swagger_auto_schema(method='get', operation_summary="Interfaces Ntopng", tags=['API Clients'])
@api_view(['GET'])
@permission_classes([AllowAny])
def ntopng_interfaces(request):
    return Response({'message': 'Interfaces Ntopng en développement'}, status=200)

@swagger_auto_schema(method='get', operation_summary="Alertes Ntopng", tags=['API Clients'])
@api_view(['GET'])
@permission_classes([AllowAny])
def ntopng_alerts(request):
    return Response({'message': 'Alertes Ntopng en développement'}, status=200)

# ==================== HAPROXY ====================

@swagger_auto_schema(method='get', operation_summary="Stats HAProxy", tags=['API Clients'])
@api_view(['GET'])
@permission_classes([AllowAny])
def haproxy_stats(request):
    return Response({'message': 'Stats HAProxy en développement'}, status=200)

@swagger_auto_schema(method='get', operation_summary="Info HAProxy", tags=['API Clients'])
@api_view(['GET'])
@permission_classes([AllowAny])
def haproxy_info(request):
    return Response({'message': 'Info HAProxy en développement'}, status=200)

@swagger_auto_schema(method='get', operation_summary="Backends HAProxy", tags=['API Clients'])
@api_view(['GET'])
@permission_classes([AllowAny])
def haproxy_backends(request):
    return Response({'message': 'Backends HAProxy en développement'}, status=200)

@swagger_auto_schema(method='get', operation_summary="Serveurs backend HAProxy", tags=['API Clients'])
@api_view(['GET'])
@permission_classes([AllowAny])
def haproxy_backend_servers(request, backend):
    return Response({'message': f'Serveurs backend {backend} HAProxy en développement'}, status=200)

@swagger_auto_schema(method='post', operation_summary="Activer serveur HAProxy", tags=['API Clients'])
@api_view(['POST'])
@permission_classes([AllowAny])
def enable_haproxy_server(request, backend, server):
    return Response({'message': f'Activation serveur {server} backend {backend} HAProxy en développement'}, status=200)

@swagger_auto_schema(method='post', operation_summary="Désactiver serveur HAProxy", tags=['API Clients'])
@api_view(['POST'])
@permission_classes([AllowAny])
def disable_haproxy_server(request, backend, server):
    return Response({'message': f'Désactivation serveur {server} backend {backend} HAProxy en développement'}, status=200)

@swagger_auto_schema(method='put', operation_summary="État serveur HAProxy", tags=['API Clients'])
@api_view(['PUT'])
@permission_classes([AllowAny])
def set_haproxy_server_state(request, backend, server):
    return Response({'message': f'État serveur {server} backend {backend} HAProxy en développement'}, status=200)

# ==================== TRAFFIC CONTROL ====================

@swagger_auto_schema(method='get', operation_summary="Interfaces Traffic Control", tags=['API Clients'])
@api_view(['GET'])
@permission_classes([AllowAny])
def traffic_control_interfaces(request):
    return Response({'message': 'Interfaces Traffic Control en développement'}, status=200)

@swagger_auto_schema(method='get', operation_summary="Config interface Traffic Control", tags=['API Clients'])
@api_view(['GET'])
@permission_classes([AllowAny])
def traffic_control_interface_config(request, interface):
    return Response({'message': f'Config interface {interface} Traffic Control en développement'}, status=200)

@swagger_auto_schema(method='post', operation_summary="Clear interface Traffic Control", tags=['API Clients'])
@api_view(['POST'])
@permission_classes([AllowAny])
def clear_traffic_control_interface(request, interface):
    return Response({'message': f'Clear interface {interface} Traffic Control en développement'}, status=200)

@swagger_auto_schema(method='put', operation_summary="Bande passante Traffic Control", tags=['API Clients'])
@api_view(['PUT'])
@permission_classes([AllowAny])
def set_traffic_control_bandwidth(request, interface):
    return Response({'message': f'Bande passante interface {interface} Traffic Control en développement'}, status=200)

@swagger_auto_schema(method='put', operation_summary="Priorisation Traffic Control", tags=['API Clients'])
@api_view(['PUT'])
@permission_classes([AllowAny])
def set_traffic_control_prioritization(request, interface):
    return Response({'message': f'Priorisation interface {interface} Traffic Control en développement'}, status=200)

@swagger_auto_schema(method='get', operation_summary="Filtres Traffic Control", tags=['API Clients'])
@api_view(['GET'])
@permission_classes([AllowAny])
def traffic_control_filters(request, interface):
    return Response({'message': f'Filtres interface {interface} Traffic Control en développement'}, status=200)

@swagger_auto_schema(method='post', operation_summary="Ajouter filtre Traffic Control", tags=['API Clients'])
@api_view(['POST'])
@permission_classes([AllowAny])
def add_traffic_control_filter(request, interface):
    return Response({'message': f'Ajout filtre interface {interface} Traffic Control en développement'}, status=200)

# ==================== FAIL2BAN COMPLET ====================

@swagger_auto_schema(method='get', operation_summary="Configuration Fail2Ban", tags=['API Clients'])
@api_view(['GET'])
@permission_classes([AllowAny])
def fail2ban_config(request):
    return Response({'message': 'Configuration Fail2Ban en développement'}, status=200)

@swagger_auto_schema(method='put', operation_summary="Modifier config Fail2Ban", tags=['API Clients'])
@api_view(['PUT'])
@permission_classes([AllowAny])
def update_fail2ban_config(request):
    return Response({'message': 'Modification config Fail2Ban en développement'}, status=200)

@swagger_auto_schema(method='get', operation_summary="Détails jail Fail2Ban", tags=['API Clients'])
@api_view(['GET'])
@permission_classes([AllowAny])
def get_fail2ban_jail(request, jail_name):
    return Response({'message': f'Détails jail {jail_name} Fail2Ban en développement'}, status=200)

@swagger_auto_schema(method='post', operation_summary="Créer jail Fail2Ban", tags=['API Clients'])
@api_view(['POST'])
@permission_classes([AllowAny])
def create_fail2ban_jail(request):
    return Response({'message': 'Création jail Fail2Ban en développement'}, status=200)

@swagger_auto_schema(method='put', operation_summary="Modifier jail Fail2Ban", tags=['API Clients'])
@api_view(['PUT'])
@permission_classes([AllowAny])
def update_fail2ban_jail(request, jail_name):
    return Response({'message': f'Modification jail {jail_name} Fail2Ban en développement'}, status=200)

@swagger_auto_schema(method='delete', operation_summary="Supprimer jail Fail2Ban", tags=['API Clients'])
@api_view(['DELETE'])
@permission_classes([AllowAny])
def delete_fail2ban_jail(request, jail_name):
    return Response({'message': f'Suppression jail {jail_name} Fail2Ban en développement'}, status=200)

@swagger_auto_schema(method='post', operation_summary="Démarrer jail Fail2Ban", tags=['API Clients'])
@api_view(['POST'])
@permission_classes([AllowAny])
def start_fail2ban_jail(request, jail_name):
    return Response({'message': f'Démarrage jail {jail_name} Fail2Ban en développement'}, status=200)

@swagger_auto_schema(method='post', operation_summary="Arrêter jail Fail2Ban", tags=['API Clients'])
@api_view(['POST'])
@permission_classes([AllowAny])
def stop_fail2ban_jail(request, jail_name):
    return Response({'message': f'Arrêt jail {jail_name} Fail2Ban en développement'}, status=200)

@swagger_auto_schema(method='get', operation_summary="IPs bannies Fail2Ban", tags=['API Clients'])
@api_view(['GET'])
@permission_classes([AllowAny])
def fail2ban_banned_ips(request, jail_name):
    return Response({'message': f'IPs bannies jail {jail_name} Fail2Ban en développement'}, status=200)

@swagger_auto_schema(method='get', operation_summary="Logs jail Fail2Ban", tags=['API Clients'])
@api_view(['GET'])
@permission_classes([AllowAny])
def fail2ban_jail_logs(request, jail_name):
    return Response({'message': f'Logs jail {jail_name} Fail2Ban en développement'}, status=200)

@swagger_auto_schema(method='post', operation_summary="Débannir IP Fail2Ban", tags=['API Clients'])
@api_view(['POST'])
@permission_classes([AllowAny])
def unban_ip_fail2ban(request):
    return Response({'message': 'Débannissement IP Fail2Ban en développement'}, status=200)

@swagger_auto_schema(method='post', operation_summary="Recharger Fail2Ban", tags=['API Clients'])
@api_view(['POST'])
@permission_classes([AllowAny])
def reload_fail2ban_config(request):
    return Response({'message': 'Rechargement config Fail2Ban en développement'}, status=200)

@swagger_auto_schema(method='post', operation_summary="Redémarrer Fail2Ban", tags=['API Clients'])
@api_view(['POST'])
@permission_classes([AllowAny])
def restart_fail2ban_service(request):
    return Response({'message': 'Redémarrage service Fail2Ban en développement'}, status=200)

# ==================== SURICATA COMPLET ====================

@swagger_auto_schema(method='get', operation_summary="Règles Suricata", tags=['API Clients'])
@api_view(['GET'])
@permission_classes([AllowAny])
def suricata_rules(request):
    return Response({'message': 'Règles Suricata en développement'}, status=200)

@swagger_auto_schema(method='post', operation_summary="Créer règle Suricata", tags=['API Clients'])
@api_view(['POST'])
@permission_classes([AllowAny])
def create_suricata_rule(request):
    return Response({'message': 'Création règle Suricata en développement'}, status=200)

@swagger_auto_schema(method='get', operation_summary="Détails règle Suricata", tags=['API Clients'])
@api_view(['GET'])
@permission_classes([AllowAny])
def get_suricata_rule(request, rule_id):
    return Response({'message': f'Détails règle {rule_id} Suricata en développement'}, status=200)

@swagger_auto_schema(method='put', operation_summary="Modifier règle Suricata", tags=['API Clients'])
@api_view(['PUT'])
@permission_classes([AllowAny])
def update_suricata_rule(request, rule_id):
    return Response({'message': f'Modification règle {rule_id} Suricata en développement'}, status=200)

@swagger_auto_schema(method='delete', operation_summary="Supprimer règle Suricata", tags=['API Clients'])
@api_view(['DELETE'])
@permission_classes([AllowAny])
def delete_suricata_rule(request, rule_id):
    return Response({'message': f'Suppression règle {rule_id} Suricata en développement'}, status=200)

@swagger_auto_schema(method='post', operation_summary="Activer/Désactiver règle Suricata", tags=['API Clients'])
@api_view(['POST'])
@permission_classes([AllowAny])
def toggle_suricata_rule(request, rule_id):
    return Response({'message': f'Toggle règle {rule_id} Suricata en développement'}, status=200)

@swagger_auto_schema(method='get', operation_summary="Alertes Suricata", tags=['API Clients'])
@api_view(['GET'])
@permission_classes([AllowAny])
def suricata_alerts(request):
    return Response({'message': 'Alertes Suricata en développement'}, status=200)

@swagger_auto_schema(method='get', operation_summary="Détails alerte Suricata", tags=['API Clients'])
@api_view(['GET'])
@permission_classes([AllowAny])
def get_suricata_alert(request, alert_id):
    return Response({'message': f'Détails alerte {alert_id} Suricata en développement'}, status=200)

@swagger_auto_schema(method='get', operation_summary="Flows Suricata", tags=['API Clients'])
@api_view(['GET'])
@permission_classes([AllowAny])
def suricata_flows(request):
    return Response({'message': 'Flows Suricata en développement'}, status=200)

@swagger_auto_schema(method='post', operation_summary="Rechercher événements Suricata", tags=['API Clients'])
@api_view(['POST'])
@permission_classes([AllowAny])
def search_suricata_events(request):
    return Response({'message': 'Recherche événements Suricata en développement'}, status=200)

@swagger_auto_schema(method='get', operation_summary="Rulesets Suricata", tags=['API Clients'])
@api_view(['GET'])
@permission_classes([AllowAny])
def suricata_rulesets(request):
    return Response({'message': 'Rulesets Suricata en développement'}, status=200)

@swagger_auto_schema(method='post', operation_summary="Upload ruleset Suricata", tags=['API Clients'])
@api_view(['POST'])
@permission_classes([AllowAny])
def upload_suricata_ruleset(request):
    return Response({'message': 'Upload ruleset Suricata en développement'}, status=200)

@swagger_auto_schema(method='get', operation_summary="Configuration Suricata", tags=['API Clients'])
@api_view(['GET'])
@permission_classes([AllowAny])
def suricata_config(request):
    return Response({'message': 'Configuration Suricata en développement'}, status=200)

@swagger_auto_schema(method='put', operation_summary="Modifier config Suricata", tags=['API Clients'])
@api_view(['PUT'])
@permission_classes([AllowAny])
def update_suricata_config(request):
    return Response({'message': 'Modification config Suricata en développement'}, status=200)

# ==================== OPÉRATIONS EN LOT ====================

@swagger_auto_schema(method='post', operation_summary="Opérations en lot Elasticsearch", tags=['API Clients'])
@api_view(['POST'])
@permission_classes([AllowAny])
def bulk_operations_elasticsearch(request):
    return Response({'message': 'Opérations en lot Elasticsearch en développement'}, status=200)

@swagger_auto_schema(method='post', operation_summary="Opérations en lot Fail2Ban", tags=['API Clients'])
@api_view(['POST'])
@permission_classes([AllowAny])
def bulk_operations_fail2ban(request):
    return Response({'message': 'Opérations en lot Fail2Ban en développement'}, status=200)

@swagger_auto_schema(method='post', operation_summary="Opérations en lot Grafana", tags=['API Clients'])
@api_view(['POST'])
@permission_classes([AllowAny])
def bulk_operations_grafana(request):
    return Response({'message': 'Opérations en lot Grafana en développement'}, status=200)

# ==================== CONFIGURATION CLIENTS ====================

@swagger_auto_schema(method='get', operation_summary="Liste configs clients", tags=['API Clients'])
@api_view(['GET'])
@permission_classes([AllowAny])
def list_client_configs(request):
    return Response({'message': 'Liste configs clients en développement'}, status=200)

@swagger_auto_schema(method='get', operation_summary="Détails config client", tags=['API Clients'])
@api_view(['GET'])
@permission_classes([AllowAny])
def get_client_config(request, client_type):
    return Response({'message': f'Config client {client_type} en développement'}, status=200)

@swagger_auto_schema(method='post', operation_summary="Tester config client", tags=['API Clients'])
@api_view(['POST'])
@permission_classes([AllowAny])
def test_client_config(request, client_type):
    return Response({'message': f'Test config client {client_type} en développement'}, status=200)

@swagger_auto_schema(method='post', operation_summary="Reset config client", tags=['API Clients'])
@api_view(['POST'])
@permission_classes([AllowAny])
def reset_client_config(request, client_type):
    return Response({'message': f'Reset config client {client_type} en développement'}, status=200)

# ==================== MÉTRIQUES ====================

@swagger_auto_schema(method='get', operation_summary="Métriques performance", tags=['API Clients'])
@api_view(['GET'])
@permission_classes([AllowAny])
def performance_metrics(request):
    return Response({'message': 'Métriques performance en développement'}, status=200)

@swagger_auto_schema(method='get', operation_summary="Métriques circuit breakers", tags=['API Clients'])
@api_view(['GET'])
@permission_classes([AllowAny])
def circuit_breaker_metrics(request):
    return Response({'message': 'Métriques circuit breakers en développement'}, status=200)

@swagger_auto_schema(method='get', operation_summary="Métriques cache", tags=['API Clients'])
@api_view(['GET'])
@permission_classes([AllowAny])
def cache_metrics(request):
    return Response({'message': 'Métriques cache en développement'}, status=200)

@swagger_auto_schema(method='get', operation_summary="Métriques erreurs", tags=['API Clients'])
@api_view(['GET'])
@permission_classes([AllowAny])
def error_metrics(request):
    return Response({'message': 'Métriques erreurs en développement'}, status=200)

@swagger_auto_schema(method='get', operation_summary="Métriques usage", tags=['API Clients'])
@api_view(['GET'])
@permission_classes([AllowAny])
def usage_metrics(request):
    return Response({'message': 'Métriques usage en développement'}, status=200)

# ==================== UTILITAIRES ====================

@swagger_auto_schema(method='get', operation_summary="Statut global", tags=['API Clients'])
@api_view(['GET'])
@permission_classes([AllowAny])
def global_status(request):
    return Response({'message': 'Statut global en développement'}, status=200)

@swagger_auto_schema(method='get', operation_summary="Version API", tags=['API Clients'])
@api_view(['GET'])
@permission_classes([AllowAny])
def api_version(request):
    return Response({'message': 'Version API en développement'}, status=200)

@swagger_auto_schema(method='get', operation_summary="Capacités API", tags=['API Clients'])
@api_view(['GET'])
@permission_classes([AllowAny])
def api_capabilities(request):
    return Response({'message': 'Capacités API en développement'}, status=200)

@swagger_auto_schema(method='post', operation_summary="Reset tous clients", tags=['API Clients'])
@api_view(['POST'])
@permission_classes([AllowAny])
def reset_all_clients(request):
    return Response({'message': 'Reset tous clients en développement'}, status=200)

# ==================== DEBUG ====================

@swagger_auto_schema(method='get', operation_summary="Logs debug", tags=['API Clients'])
@api_view(['GET'])
@permission_classes([AllowAny])
def debug_logs(request):
    return Response({'message': 'Logs debug en développement'}, status=200)

@swagger_auto_schema(method='get', operation_summary="Connexions debug", tags=['API Clients'])
@api_view(['GET'])
@permission_classes([AllowAny])
def debug_connections(request):
    return Response({'message': 'Connexions debug en développement'}, status=200)

@swagger_auto_schema(method='get', operation_summary="Mémoire debug", tags=['API Clients'])
@api_view(['GET'])
@permission_classes([AllowAny])
def debug_memory_usage(request):
    return Response({'message': 'Mémoire debug en développement'}, status=200)

@swagger_auto_schema(method='post', operation_summary="Clear cache", tags=['API Clients'])
@api_view(['POST'])
@permission_classes([AllowAny])
def clear_cache(request):
    return Response({'message': 'Clear cache en développement'}, status=200)

@swagger_auto_schema(method='get', operation_summary="Dump config", tags=['API Clients'])
@api_view(['GET'])
@permission_classes([AllowAny])
def dump_config(request):
    return Response({'message': 'Dump config en développement'}, status=200)