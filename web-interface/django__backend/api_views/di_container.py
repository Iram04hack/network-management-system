"""
Conteneur d'injection de dépendances pour le module api_views.

Ce fichier configure les dépendances pour le module api_views
en liant les interfaces aux implémentations concrètes.
"""

from dependency_injector import containers, providers

from .domain.interfaces import (
    DashboardRepository, TopologyDiscoveryRepository, APISearchRepository
)
from .infrastructure import (
    DjangoDashboardRepository, DjangoTopologyDiscoveryRepository, DjangoAPISearchRepository
)
from .application import (
    GetDashboardDataUseCase, SaveDashboardConfigurationUseCase,
    GetNetworkTopologyUseCase, StartTopologyDiscoveryUseCase,
    SearchResourcesUseCase, GetResourceDetailsUseCase
)

class APIViewsContainer(containers.DeclarativeContainer):
    """
    Conteneur d'injection de dépendances pour le module api_views.
    """
    
    # Repositories
    dashboard_repository = providers.Singleton(DjangoDashboardRepository)
    topology_repository = providers.Singleton(DjangoTopologyDiscoveryRepository)
    search_repository = providers.Singleton(DjangoAPISearchRepository)
    
    # Cas d'utilisation
    get_dashboard_data_use_case = providers.Factory(
        GetDashboardDataUseCase,
        dashboard_repository=dashboard_repository
    )
    
    save_dashboard_configuration_use_case = providers.Factory(
        SaveDashboardConfigurationUseCase,
        dashboard_repository=dashboard_repository
    )
    
    get_network_topology_use_case = providers.Factory(
        GetNetworkTopologyUseCase,
        topology_repository=topology_repository
    )
    
    start_topology_discovery_use_case = providers.Factory(
        StartTopologyDiscoveryUseCase,
        topology_repository=topology_repository
    )
    
    search_resources_use_case = providers.Factory(
        SearchResourcesUseCase,
        search_repository=search_repository
    )
    
    get_resource_details_use_case = providers.Factory(
        GetResourceDetailsUseCase,
        search_repository=search_repository
    )


# Créer une instance du conteneur
container = APIViewsContainer()

# Pour faciliter la résolution des dépendances
def resolve(dependency):
    """
    Résout une dépendance à partir du conteneur.
    
    Args:
        dependency: Interface ou chaîne de caractères identifiant la dépendance
        
    Returns:
        Instance concrète de la dépendance
    """
    # Mapper les dépendances directement aux providers du conteneur
    dependency_map = {
        'DashboardRepository': container.dashboard_repository,
        'TopologyDiscoveryRepository': container.topology_repository,
        'APISearchRepository': container.search_repository,
        DashboardRepository: container.dashboard_repository,
        TopologyDiscoveryRepository: container.topology_repository,
        APISearchRepository: container.search_repository,
        GetDashboardDataUseCase: container.get_dashboard_data_use_case,
        SaveDashboardConfigurationUseCase: container.save_dashboard_configuration_use_case,
        GetNetworkTopologyUseCase: container.get_network_topology_use_case,
        StartTopologyDiscoveryUseCase: container.start_topology_discovery_use_case,
        SearchResourcesUseCase: container.search_resources_use_case,
        GetResourceDetailsUseCase: container.get_resource_details_use_case,
    }
    
    if dependency in dependency_map:
        return dependency_map[dependency]()
    
    raise ValueError(f"Dépendance {dependency} non trouvée dans le conteneur")

# Accesseurs pour les cas d'utilisation
def get_dashboard_data_use_case():
    """
    Récupère le cas d'utilisation de récupération des données de tableau de bord.
    
    Returns:
        Instance du cas d'utilisation de données de tableau de bord
    """
    return container.get_dashboard_data_use_case()

def get_search_use_case():
    """
    Récupère le cas d'utilisation de recherche.
    
    Returns:
        Instance du cas d'utilisation de recherche
    """
    return container.search_resources_use_case()

def get_topology_use_case():
    """
    Récupère le cas d'utilisation de topologie.
    
    Returns:
        Instance du cas d'utilisation de topologie
    """
    return container.get_network_topology_use_case() 