"""
Conteneur d'injection de dépendances pour le module Dashboard.

Ce fichier configure les dépendances du module Dashboard et fournit
un moyen d'accéder aux services correctement initialisés.
"""

import logging
from typing import Dict, Any, Optional

from .infrastructure.cache_service import RedisCacheService
from .infrastructure.monitoring_adapter import MonitoringAdapter
from .infrastructure.network_adapter import NetworkAdapter
from .infrastructure.services import (
    DashboardDataServiceImpl,
    NetworkOverviewServiceImpl,
    TopologyVisualizationServiceImpl
)

logger = logging.getLogger(__name__)


class DashboardContainer:
    """
    Conteneur d'injection de dépendances pour le module Dashboard.
    
    Cette classe gère la création et l'initialisation des services
    et adaptateurs utilisés par le module Dashboard.
    """
    
    def __init__(self):
        """Initialise le conteneur avec des services vides."""
        self._services = {}
        self._initialized = False
    
    def init_resources(self):
        """
        Initialise les ressources et services du conteneur.
        
        Cette méthode crée et configure tous les services nécessaires
        au fonctionnement du module Dashboard.
        """
        if self._initialized:
            logger.debug("Le conteneur Dashboard est déjà initialisé")
            return
        
        try:
            # Créer les adaptateurs et services d'infrastructure
            cache_service = RedisCacheService()
            monitoring_adapter = MonitoringAdapter()
            network_adapter = NetworkAdapter()
            
            # Créer les services d'application
            dashboard_service = DashboardDataServiceImpl(
                network_service=network_adapter,
                monitoring_service=monitoring_adapter,
                cache_service=cache_service
            )
            
            network_overview_service = NetworkOverviewServiceImpl(
                network_service=network_adapter,
                monitoring_service=monitoring_adapter,
                cache_service=cache_service
            )
            
            topology_service = TopologyVisualizationServiceImpl(
                network_service=network_adapter,
                cache_service=cache_service
            )
            
            # Enregistrer les services dans le conteneur
            self._services = {
                'cache_service': cache_service,
                'monitoring_adapter': monitoring_adapter,
                'network_adapter': network_adapter,
                'dashboard_service': dashboard_service,
                'network_overview_service': network_overview_service,
                'topology_service': topology_service
            }
            
            self._initialized = True
            logger.info("Conteneur Dashboard initialisé avec succès")
        except Exception as e:
            logger.error(f"Erreur lors de l'initialisation du conteneur Dashboard: {e}")
            raise
    
    def get_service(self, service_name: str) -> Any:
        """
        Récupère un service par son nom.
        
        Args:
            service_name: Nom du service à récupérer
            
        Returns:
            Instance du service demandé
            
        Raises:
            ValueError: Si le service demandé n'existe pas
            RuntimeError: Si le conteneur n'est pas initialisé
        """
        if not self._initialized:
            self.init_resources()
        
        if service_name not in self._services:
            raise ValueError(f"Service {service_name} non trouvé dans le conteneur Dashboard")
        
        return self._services[service_name]
    
    def get_services(self) -> Dict[str, Any]:
        """
        Récupère tous les services enregistrés.
        
        Returns:
            Dictionnaire contenant tous les services
            
        Raises:
            RuntimeError: Si le conteneur n'est pas initialisé
        """
        if not self._initialized:
            self.init_resources()
        
        return self._services


# Instance singleton du conteneur
container = DashboardContainer() 