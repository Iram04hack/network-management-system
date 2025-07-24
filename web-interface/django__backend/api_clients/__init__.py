"""
Module api_clients pour le système NMS.

Ce module fournit des implémentations de clients API pour interagir avec
des services externes en suivant une architecture hexagonale.

L'architecture est organisée comme suit:
- domain: interfaces et exceptions
- infrastructure: implémentations génériques
- network: clients pour les services réseau
- security: clients pour les services de sécurité
- monitoring: clients pour les services de surveillance
"""

# Import des classes principales
from .base import (
    BaseAPIClient,
    RequestExecutor,
    ResponseHandler
)

from .http_client import HttpClient

# Import des métriques de performance
from .monitoring.metrics.performance import (
    PerformanceMetrics,
    measure_performance,
    MetricPoint,
    MetricSummary
)

from .monitoring.metrics.prometheus_exporter import (
    PrometheusExporter
)

# Import du domaine
from .domain.interfaces import (
    APIClientInterface,
    CircuitBreakerInterface,
    APIResponseHandler
)

# Import des clients réseau
from .network import (
    GNS3Client,
    SNMPClient,
    NetflowClient
)

# Import des clients sécurité
from .security import (
    Fail2BanClient,
    SuricataClient
)

# Import des clients monitoring
from .monitoring import (
    ElasticsearchClient,
    GrafanaClient,
    NetdataClient,
    NtopngClient,
    PrometheusClient
)

# Import de l'utilitaire Swagger automatique
try:
    from .utils.swagger_utils import generate_schema_for_all_views
except ImportError:
    generate_schema_for_all_views = None

__all__ = [
    'BaseAPIClient',
    'RequestExecutor',
    'ResponseHandler',
    'HttpClient',
    
    # Métriques
    'PerformanceMetrics',
    'measure_performance',
    'MetricPoint',
    'MetricSummary',
    'PrometheusExporter',
    
    # Domaine
    'APIClientInterface',
    'CircuitBreakerInterface',
    'APIResponseHandler',
    
    # Clients réseau
    'GNS3Client',
    'SNMPClient',
    'NetflowClient',
    
    # Clients sécurité
    'Fail2BanClient',
    'SuricataClient',
    
    # Clients monitoring
    'ElasticsearchClient',
    'GrafanaClient',
    'NetdataClient',
    'NtopngClient',
    'PrometheusClient',
    
    # Utilitaires Swagger
    'generate_schema_for_all_views',
]

"""
Module d'initialisation pour l'application api_clients.

Ce module contient la configuration de l'application api_clients.
"""

default_app_config = 'api_clients.apps.ApiClientsConfig'

# Application automatique des décorateurs Swagger aux vues
if generate_schema_for_all_views:
    import sys
    try:
        # Tenter d'appliquer les décorateurs automatiquement aux vues
        from . import views
        generate_schema_for_all_views(views)
        print("Documentation Swagger automatiquement générée pour api_clients.")
    except Exception as e:
        print(f"Erreur lors de la génération de la documentation Swagger: {e}", file=sys.stderr)

"""
Module d'intégration avec différents clients réseau externes.

Ce module fournit des interfaces standardisées pour interagir avec divers
outils et services réseau comme GNS3, SNMP, Netflow, etc.
"""

default_app_config = 'api_clients.apps.ApiClientsConfig'
