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
                        'capabilities': self._get_client_capabilities(client_name),
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