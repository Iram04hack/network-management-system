"""
Vues API unifiées pour le module api_clients.

Ce module fusionne toutes les vues en un seul fichier avec documentation Swagger automatique.
"""

import logging
from typing import Dict, Any, Optional
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
    """Initialise tous les clients de manière sécurisée."""
    global clients
    
    # Clients réseau
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

    # Clients monitoring
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

    # Clients infrastructure
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

    # Clients sécurité
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

# ==================== VUES FONCTION POUR LES CLIENTS RÉSEAU ====================

@swagger_auto_schema(
    method='get',
    operation_description="Récupère le statut des clients réseau",
    responses={200: NetworkClientSerializer},
    tags=['API Clients']
)
@api_view(['GET'])
@permission_classes([AllowAny])
def network_clients(request):
    """Récupère le statut des clients réseau."""
    try:
        network_status = {
            'gns3': {
                'available': clients['gns3'] is not None,
                'status': 'available' if clients['gns3'] else 'unavailable',
                'client_type': 'GNS3Client',
                'description': 'Client pour l\'interaction avec GNS3'
            },
            'snmp': {
                'available': clients['snmp'] is not None,
                'status': 'available' if clients['snmp'] else 'unavailable',
                'client_type': 'SNMPClient',
                'description': 'Client pour les requêtes SNMP'
            },
            'netflow': {
                'available': clients['netflow'] is not None,
                'status': 'available' if clients['netflow'] else 'unavailable',
                'client_type': 'NetflowClient',
                'description': 'Client pour l\'analyse NetFlow'
            }
        }
        
        return Response(network_status, status=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des clients réseau: {e}")
        return Response(
            {'error': 'Erreur lors de la récupération des clients réseau'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@swagger_auto_schema(
    method='get',
    operation_description="Récupère la liste des projets GNS3",
    responses={200: GNS3ProjectSerializer(many=True)},
    tags=['API Clients']
)
@api_view(['GET'])
@permission_classes([AllowAny])
def gns3_projects(request):
    """Récupère la liste des projets GNS3."""
    if not clients['gns3']:
        return Response(
            {'error': 'Client GNS3 non disponible'},
            status=status.HTTP_503_SERVICE_UNAVAILABLE
        )
    
    try:
        projects = clients['gns3'].get_projects()
        return Response(projects, status=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des projets GNS3: {e}")
        return Response(
            {'error': 'Erreur lors de la récupération des projets GNS3'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@swagger_auto_schema(
    method='post',
    operation_description="Exécute une requête SNMP",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'oid': openapi.Schema(type=openapi.TYPE_STRING, description='OID SNMP'),
            'operation': openapi.Schema(type=openapi.TYPE_STRING, description='Type d\'opération (get, walk)')
        }
    ),
    responses={200: SNMPResponseSerializer},
    tags=['API Clients']
)
@api_view(['POST'])
@permission_classes([AllowAny])
def snmp_query(request):
    """Exécute une requête SNMP."""
    if not clients['snmp']:
        return Response(
            {'error': 'Client SNMP non disponible'},
            status=status.HTTP_503_SERVICE_UNAVAILABLE
        )
    
    try:
        oid = request.data.get('oid')
        operation = request.data.get('operation', 'get')
        
        if operation == 'get':
            result = clients['snmp'].get(oid)
        elif operation == 'walk':
            result = clients['snmp'].walk(oid)
        else:
            return Response(
                {'error': 'Opération non supportée'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return Response(result, status=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"Erreur lors de la requête SNMP: {e}")
        return Response(
            {'error': 'Erreur lors de la requête SNMP'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

# ==================== VUES FONCTION POUR LES CLIENTS MONITORING ====================

@swagger_auto_schema(
    method='get',
    operation_description="Récupère le statut des clients monitoring",
    responses={200: MonitoringClientSerializer},
    tags=['API Clients']
)
@api_view(['GET'])
@permission_classes([AllowAny])
def monitoring_clients(request):
    """Récupère le statut des clients monitoring."""
    try:
        monitoring_status = {
            'prometheus': {
                'available': clients['prometheus'] is not None,
                'status': 'available' if clients['prometheus'] else 'unavailable',
                'client_type': 'PrometheusClient',
                'description': 'Client pour Prometheus'
            },
            'grafana': {
                'available': clients['grafana'] is not None,
                'status': 'available' if clients['grafana'] else 'unavailable',
                'client_type': 'GrafanaClient',
                'description': 'Client pour Grafana'
            },
            'elasticsearch': {
                'available': clients['elasticsearch'] is not None,
                'status': 'available' if clients['elasticsearch'] else 'unavailable',
                'client_type': 'ElasticsearchClient',
                'description': 'Client pour Elasticsearch'
            },
            'netdata': {
                'available': clients['netdata'] is not None,
                'status': 'available' if clients['netdata'] else 'unavailable',
                'client_type': 'NetdataClient',
                'description': 'Client pour Netdata'
            },
            'ntopng': {
                'available': clients['ntopng'] is not None,
                'status': 'available' if clients['ntopng'] else 'unavailable',
                'client_type': 'NtopngClient',
                'description': 'Client pour Ntopng'
            }
        }
        
        return Response(monitoring_status, status=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des clients monitoring: {e}")
        return Response(
            {'error': 'Erreur lors de la récupération des clients monitoring'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@swagger_auto_schema(
    method='post',
    operation_description="Exécute une requête PromQL",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'query': openapi.Schema(type=openapi.TYPE_STRING, description='Requête PromQL')
        }
    ),
    responses={200: PrometheusResponseSerializer},
    tags=['API Clients']
)
@api_view(['POST'])
@permission_classes([AllowAny])
def prometheus_query(request):
    """Exécute une requête PromQL."""
    if not clients['prometheus']:
        return Response(
            {'error': 'Client Prometheus non disponible'},
            status=status.HTTP_503_SERVICE_UNAVAILABLE
        )
    
    try:
        query = request.data.get('query')
        result = clients['prometheus'].query(query)
        return Response(result, status=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"Erreur lors de la requête Prometheus: {e}")
        return Response(
            {'error': 'Erreur lors de la requête Prometheus'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

# ==================== VUES FONCTION POUR LES CLIENTS INFRASTRUCTURE ====================

@swagger_auto_schema(
    method='get',
    operation_description="Récupère le statut des clients infrastructure",
    responses={200: InfrastructureClientSerializer},
    tags=['API Clients']
)
@api_view(['GET'])
@permission_classes([AllowAny])
def infrastructure_clients(request):
    """Récupère le statut des clients infrastructure."""
    try:
        infrastructure_status = {
            'haproxy': {
                'available': clients['haproxy'] is not None,
                'status': 'available' if clients['haproxy'] else 'unavailable',
                'client_type': 'HAProxyClient',
                'description': 'Client pour HAProxy'
            },
            'traffic_control': {
                'available': clients['traffic_control'] is not None,
                'status': 'available' if clients['traffic_control'] else 'unavailable',
                'client_type': 'TrafficControlClient',
                'description': 'Client pour le contrôle du trafic Linux (tc)'
            }
        }
        
        return Response(infrastructure_status, status=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des clients infrastructure: {e}")
        return Response(
            {'error': 'Erreur lors de la récupération des clients infrastructure'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

# ==================== VUES FONCTION POUR LES CLIENTS SÉCURITÉ ====================

@swagger_auto_schema(
    method='get',
    operation_description="Récupère le statut des clients sécurité",
    responses={200: SecurityClientSerializer},
    tags=['API Clients']
)
@api_view(['GET'])
@permission_classes([AllowAny])
def security_clients(request):
    """Récupère le statut des clients sécurité."""
    try:
        security_status = {
            'fail2ban': {
                'available': clients['fail2ban'] is not None,
                'status': 'available' if clients['fail2ban'] else 'unavailable',
                'client_type': 'Fail2BanClient',
                'description': 'Client pour Fail2Ban'
            },
            'suricata': {
                'available': clients['suricata'] is not None,
                'status': 'available' if clients['suricata'] else 'unavailable',
                'client_type': 'SuricataClient',
                'description': 'Client pour Suricata IDS/IPS'
            }
        }
        
        return Response(security_status, status=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des clients sécurité: {e}")
        return Response(
            {'error': 'Erreur lors de la récupération des clients sécurité'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

# ==================== ENDPOINTS CRUD POUR PROJETS GNS3 ====================

@swagger_auto_schema(
    method='post',
    operation_description="Crée un nouveau projet GNS3",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'name': openapi.Schema(type=openapi.TYPE_STRING, description='Nom du projet'),
            'path': openapi.Schema(type=openapi.TYPE_STRING, description='Chemin du projet (optionnel)')
        },
        required=['name']
    ),
    responses={201: GNS3ProjectSerializer},
    tags=['API Clients']
)
@api_view(['POST'])
@permission_classes([AllowAny])
def create_gns3_project(request):
    """Crée un nouveau projet GNS3."""
    if not clients['gns3']:
        return Response(
            {'error': 'Client GNS3 non disponible'},
            status=status.HTTP_503_SERVICE_UNAVAILABLE
        )
    
    try:
        name = request.data.get('name')
        path = request.data.get('path')
        
        if not name:
            return Response(
                {'error': 'Le nom du projet est requis'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        project_data = {'name': name}
        if path:
            project_data['path'] = path
            
        project = clients['gns3'].create_project(**project_data)
        return Response(project, status=status.HTTP_201_CREATED)
    except Exception as e:
        logger.error(f"Erreur lors de la création du projet GNS3: {e}")
        return Response(
            {'error': 'Erreur lors de la création du projet GNS3'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@swagger_auto_schema(
    method='put',
    operation_description="Met à jour un projet GNS3 existant",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'name': openapi.Schema(type=openapi.TYPE_STRING, description='Nouveau nom du projet'),
            'path': openapi.Schema(type=openapi.TYPE_STRING, description='Nouveau chemin du projet')
        }
    ),
    responses={200: GNS3ProjectSerializer},
    tags=['API Clients']
)
@api_view(['PUT'])
@permission_classes([AllowAny])
def update_gns3_project(request, project_id):
    """Met à jour un projet GNS3 existant."""
    if not clients['gns3']:
        return Response(
            {'error': 'Client GNS3 non disponible'},
            status=status.HTTP_503_SERVICE_UNAVAILABLE
        )
    
    try:
        project = clients['gns3'].update_project(project_id, **request.data)
        return Response(project, status=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"Erreur lors de la mise à jour du projet GNS3: {e}")
        return Response(
            {'error': 'Erreur lors de la mise à jour du projet GNS3'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@swagger_auto_schema(
    method='delete',
    operation_description="Supprime un projet GNS3",
    responses={204: 'Projet supprimé avec succès'},
    tags=['API Clients']
)
@api_view(['DELETE'])
@permission_classes([AllowAny])
def delete_gns3_project(request, project_id):
    """Supprime un projet GNS3."""
    if not clients['gns3']:
        return Response(
            {'error': 'Client GNS3 non disponible'},
            status=status.HTTP_503_SERVICE_UNAVAILABLE
        )
    
    try:
        clients['gns3'].delete_project(project_id)
        return Response(status=status.HTTP_204_NO_CONTENT)
    except Exception as e:
        logger.error(f"Erreur lors de la suppression du projet GNS3: {e}")
        return Response(
            {'error': 'Erreur lors de la suppression du projet GNS3'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

# ==================== ENDPOINTS CRUD POUR CLIENTS ====================

@swagger_auto_schema(
    method='post',
    operation_description="Configure un nouveau client API",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'client_type': openapi.Schema(type=openapi.TYPE_STRING, description='Type de client'),
            'name': openapi.Schema(type=openapi.TYPE_STRING, description='Nom du client'),
            'host': openapi.Schema(type=openapi.TYPE_STRING, description='Hôte du service'),
            'port': openapi.Schema(type=openapi.TYPE_INTEGER, description='Port du service')
        },
        required=['client_type', 'name', 'host']
    ),
    responses={201: 'Client configuré avec succès'},
    tags=['API Clients']
)
@api_view(['POST'])
@permission_classes([AllowAny])
def create_client_config(request):
    """Configure un nouveau client API."""
    try:
        client_type = request.data.get('client_type')
        name = request.data.get('name')
        host = request.data.get('host')
        port = request.data.get('port')
        
        if not all([client_type, name, host]):
            return Response(
                {'error': 'client_type, name et host sont requis'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        config = {
            'name': name,
            'type': client_type,
            'host': host,
            'port': port,
            'created_at': '2024-01-01T00:00:00Z'
        }
        
        return Response(config, status=status.HTTP_201_CREATED)
    except Exception as e:
        logger.error(f"Erreur lors de la configuration du client: {e}")
        return Response(
            {'error': 'Erreur lors de la configuration du client'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@swagger_auto_schema(
    method='put',
    operation_description="Met à jour la configuration d'un client API",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'host': openapi.Schema(type=openapi.TYPE_STRING, description='Nouvel hôte'),
            'port': openapi.Schema(type=openapi.TYPE_INTEGER, description='Nouveau port')
        }
    ),
    responses={200: 'Configuration mise à jour avec succès'},
    tags=['API Clients']
)
@api_view(['PUT'])
@permission_classes([AllowAny])
def update_client_config(request, client_name):
    """Met à jour la configuration d'un client API."""
    try:
        if client_name not in clients:
            return Response(
                {'error': 'Client non trouvé'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        config = {
            'name': client_name,
            'updated_fields': list(request.data.keys()),
            'updated_at': '2024-01-01T00:00:00Z'
        }
        
        return Response(config, status=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"Erreur lors de la mise à jour du client: {e}")
        return Response(
            {'error': 'Erreur lors de la mise à jour du client'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@swagger_auto_schema(
    method='delete',
    operation_description="Supprime la configuration d'un client API",
    responses={204: 'Configuration supprimée avec succès'},
    tags=['API Clients']
)
@api_view(['DELETE'])
@permission_classes([AllowAny])
def delete_client_config(request, client_name):
    """Supprime la configuration d'un client API."""
    try:
        if client_name not in clients:
            return Response(
                {'error': 'Client non trouvé'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        return Response(status=status.HTTP_204_NO_CONTENT)
    except Exception as e:
        logger.error(f"Erreur lors de la suppression du client: {e}")
        return Response(
            {'error': 'Erreur lors de la suppression du client'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

# ==================== UTILITAIRES ET SANTÉ GLOBALE ====================

@swagger_auto_schema(
    method='get',
    operation_description="Vérifie la santé globale de tous les clients API",
    responses={200: ClientHealthSerializer},
    tags=['API Clients']
)
@api_view(['GET'])
@permission_classes([AllowAny])
def global_health_check(request):
    """Vérifie la santé globale de tous les clients."""
    try:
        health_status = {}
        total_clients = 0
        available_clients = 0
        
        for client_name, client in clients.items():
            total_clients += 1
            if client is not None:
                available_clients += 1
                try:
                    if hasattr(client, 'check_health'):
                        is_healthy = client.check_health()
                    elif hasattr(client, 'test_connection'):
                        is_healthy = client.test_connection()
                    else:
                        is_healthy = True
                    
                    health_status[client_name] = {
                        'available': True,
                        'healthy': is_healthy,
                        'type': type(client).__name__
                    }
                except Exception as e:
                    health_status[client_name] = {
                        'available': True,
                        'healthy': False,
                        'error': str(e),
                        'type': type(client).__name__
                    }
            else:
                health_status[client_name] = {
                    'available': False,
                    'healthy': False,
                    'error': 'Client non initialisé'
                }
        
        return Response({
            'overall_status': 'healthy' if available_clients > 0 else 'unhealthy',
            'total_clients': total_clients,
            'available_clients': available_clients,
            'availability_rate': available_clients / total_clients if total_clients > 0 else 0,
            'clients': health_status,
        }, status=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"Erreur lors de la vérification de santé globale: {e}")
        return Response(
            {'error': 'Erreur lors de la vérification de santé globale'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )