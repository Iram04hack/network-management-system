"""
Interfaces du domaine pour le module api_views.

Ce module définit les interfaces que doivent implémenter les repositories 
et services utilisés dans le module api_views.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union


class DashboardRepository(ABC):
    """
    Interface pour le repository de tableaux de bord.
    
    Définit les méthodes pour accéder aux données des tableaux de bord.
    """
    
    @abstractmethod
    def get_dashboard_data(self, dashboard_type: str, user_id: Optional[int] = None,
                         filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Récupère les données d'un tableau de bord.
        
        Args:
            dashboard_type: Type de tableau de bord
            user_id: ID de l'utilisateur (optionnel)
            filters: Filtres supplémentaires (optionnel)
            
        Returns:
            Données du tableau de bord
        """
        pass
    
    @abstractmethod
    def save_dashboard_configuration(self, dashboard_type: str, configuration: Dict[str, Any],
                                  user_id: Optional[int] = None) -> bool:
        """
        Sauvegarde la configuration d'un tableau de bord.
        
        Args:
            dashboard_type: Type de tableau de bord
            configuration: Configuration à sauvegarder
            user_id: ID de l'utilisateur (optionnel)
            
        Returns:
            True si la sauvegarde a réussi, False sinon
        """
        pass
    
    @abstractmethod
    def get_dashboard_configuration(self, dashboard_type: str, 
                                 user_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Récupère la configuration d'un tableau de bord.
        
        Args:
            dashboard_type: Type de tableau de bord
            user_id: ID de l'utilisateur (optionnel)
            
        Returns:
            Configuration du tableau de bord
        """
        pass


class TopologyDiscoveryRepository(ABC):
    """
    Interface pour le repository de découverte de topologie.
    
    Définit les méthodes pour accéder aux données de topologie.
    """
    
    @abstractmethod
    def get_network_topology(self, network_id: Optional[str] = None,
                           filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Récupère la topologie d'un réseau.
        
        Args:
            network_id: ID du réseau (optionnel)
            filters: Filtres supplémentaires (optionnel)
            
        Returns:
            Topologie du réseau
        """
        pass
    
    @abstractmethod
    def start_discovery(self, network_id: str, discovery_params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Démarre une découverte de topologie.
        
        Args:
            network_id: ID du réseau
            discovery_params: Paramètres de la découverte
            
        Returns:
            Informations sur la découverte démarrée
        """
        pass
    
    @abstractmethod
    def get_discovery_status(self, discovery_id: str) -> Dict[str, Any]:
        """
        Récupère le statut d'une découverte de topologie.
        
        Args:
            discovery_id: ID de la découverte
            
        Returns:
            Statut de la découverte
        """
        pass
    
    @abstractmethod
    def save_topology(self, topology_data: Dict[str, Any], network_id: str) -> bool:
        """
        Sauvegarde une topologie découverte.
        
        Args:
            topology_data: Données de la topologie
            network_id: ID du réseau
            
        Returns:
            True si la sauvegarde a réussi, False sinon
        """
        pass


class APISearchRepository(ABC):
    """
    Interface pour le repository de recherche API.
    
    Définit les méthodes pour effectuer des recherches dans les différentes ressources.
    """
    
    @abstractmethod
    def search(self, query: str, resource_types: List[str],
             filters: Optional[Dict[str, Any]] = None,
             pagination: Optional[Dict[str, int]] = None) -> Dict[str, Any]:
        """
        Effectue une recherche dans les ressources.
        
        Args:
            query: Requête de recherche
            resource_types: Types de ressources à rechercher
            filters: Filtres supplémentaires (optionnel)
            pagination: Paramètres de pagination (optionnel)
            
        Returns:
            Résultats de la recherche
        """
        pass
    
    @abstractmethod
    def get_resource_details(self, resource_type: str, resource_id: str) -> Dict[str, Any]:
        """
        Récupère les détails d'une ressource.
        
        Args:
            resource_type: Type de ressource
            resource_id: ID de la ressource
            
        Returns:
            Détails de la ressource
        """
        pass 