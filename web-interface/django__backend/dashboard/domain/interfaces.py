"""
Interfaces du domaine pour le module Dashboard.

Ce module définit les contrats que doivent respecter les implémentations
concrètes des services liés au tableau de bord.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union, Tuple
from datetime import datetime
from .entities import DeviceStatus, AlertInfo, SystemHealthMetrics, DashboardOverview, NetworkOverview, TopologyView


class IMonitoringDataProvider(ABC):
    """
    Interface pour le fournisseur de données de monitoring.
    
    Responsable de fournir des données de surveillance pour le tableau de bord.
    """
    
    @abstractmethod
    async def get_system_alerts(self, limit: int = 5, status_filter: Optional[List[str]] = None) -> List[AlertInfo]:
        """
        Récupère les alertes système récentes.
        
        Args:
            limit: Nombre maximum d'alertes à récupérer
            status_filter: Liste des statuts pour filtrer les alertes
            
        Returns:
            Liste des alertes système
        """
        pass
    
    @abstractmethod
    async def get_performance_metrics(self, time_range: Optional[Tuple[datetime, datetime]] = None) -> Dict[str, Any]:
        """
        Récupère les données de performance agrégées.
        
        Args:
            time_range: Plage de temps pour les métriques (début, fin)
            
        Returns:
            Dictionnaire contenant les métriques de performance
        """
        pass
    
    @abstractmethod
    async def get_device_metrics(self, device_id: int) -> Dict[str, Any]:
        """
        Récupère les métriques spécifiques à un équipement.
        
        Args:
            device_id: ID de l'équipement
            
        Returns:
            Dictionnaire contenant les métriques de l'équipement
        """
        pass
        
    @abstractmethod
    async def get_system_health_metrics(self) -> SystemHealthMetrics:
        """
        Récupère les métriques de santé du système.
        
        Returns:
            Objet contenant les métriques de santé système
        """
        pass


class INetworkDataProvider(ABC):
    """
    Interface pour le fournisseur de données réseau.
    
    Responsable de fournir des données de réseau pour le tableau de bord.
    """
    
    @abstractmethod
    async def get_device_summary(self) -> Dict[str, Any]:
        """
        Récupère un résumé des équipements réseau.
        
        Returns:
            Dictionnaire contenant les statistiques sur les équipements
        """
        pass
    
    @abstractmethod
    async def get_interface_summary(self) -> Dict[str, Any]:
        """
        Récupère un résumé des interfaces réseau.
        
        Returns:
            Dictionnaire contenant les statistiques sur les interfaces
        """
        pass
    
    @abstractmethod
    async def get_qos_summary(self) -> Dict[str, Any]:
        """
        Récupère un résumé des politiques QoS.
        
        Returns:
            Dictionnaire contenant les statistiques sur les politiques QoS
        """
        pass
    
    @abstractmethod
    async def get_topology_data(self, topology_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Récupère les données de topologie.
        
        Args:
            topology_id: ID de la topologie (optionnel)
            
        Returns:
            Données de topologie
        """
        pass
        
    @abstractmethod
    async def get_network_alerts(self, limit: int = 5, 
                                severity_filter: Optional[List[str]] = None) -> List[AlertInfo]:
        """
        Récupère les alertes réseau.
        
        Args:
            limit: Nombre maximum d'alertes à récupérer
            severity_filter: Liste des niveaux de sévérité pour filtrer les alertes
            
        Returns:
            Liste des alertes réseau
        """
        pass


class ICacheService(ABC):
    """
    Interface pour le service de cache.
    
    Responsable de gérer le cache des données du tableau de bord.
    """
    
    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """
        Récupère une valeur du cache.
        
        Args:
            key: Clé de la valeur à récupérer
            
        Returns:
            Valeur mise en cache ou None si absente
        """
        pass
    
    @abstractmethod
    async def set(self, key: str, value: Any, ttl: int = 300) -> bool:
        """
        Définit une valeur dans le cache.
        
        Args:
            key: Clé de la valeur à stocker
            value: Valeur à stocker
            ttl: Durée de vie en secondes (par défaut: 5 minutes)
            
        Returns:
            True si l'opération a réussi, False sinon
        """
        pass
        
    @abstractmethod
    async def invalidate(self, pattern: str) -> int:
        """
        Invalide les entrées de cache correspondant à un motif.
        
        Args:
            pattern: Motif de clés à invalider
            
        Returns:
            Nombre d'entrées invalidées
        """
        pass


class IDashboardDataService(ABC):
    """
    Interface pour le service de données du tableau de bord.
    
    Responsable de fournir des données consolidées pour les différentes vues du tableau de bord.
    """
    
    @abstractmethod
    async def get_dashboard_overview(self, user_id: Optional[int] = None) -> DashboardOverview:
        """
        Récupère les données de vue d'ensemble pour le tableau de bord.
        
        Args:
            user_id: ID de l'utilisateur pour personnalisation
            
        Returns:
            Objet contenant les données agrégées du tableau de bord
        """
        pass
    
    @abstractmethod
    async def get_custom_dashboard(self, dashboard_id: str, user_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Récupère les données d'un tableau de bord personnalisé.
        
        Args:
            dashboard_id: ID du tableau de bord personnalisé
            user_id: ID de l'utilisateur propriétaire du tableau de bord
            
        Returns:
            Dictionnaire contenant les données du tableau de bord personnalisé
        """
        pass
        
    @abstractmethod
    async def save_custom_dashboard(self, dashboard_id: str, config: Dict[str, Any], 
                                  user_id: int) -> Dict[str, Any]:
        """
        Enregistre la configuration d'un tableau de bord personnalisé.
        
        Args:
            dashboard_id: ID du tableau de bord personnalisé
            config: Configuration du tableau de bord
            user_id: ID de l'utilisateur propriétaire du tableau de bord
            
        Returns:
            Dictionnaire contenant les données du tableau de bord enregistré
        """
        pass


class INetworkOverviewService(ABC):
    """
    Interface pour le service de vue d'ensemble du réseau.
    
    Responsable de fournir des données consolidées sur l'état du réseau.
    """
    
    @abstractmethod
    async def get_network_overview(self) -> NetworkOverview:
        """
        Récupère une vue d'ensemble du réseau avec les informations de santé.
        
        Returns:
            Objet contenant les informations sur les équipements, interfaces et alertes
        """
        pass
    
    @abstractmethod
    async def get_network_stats(self, time_range: Optional[Tuple[datetime, datetime]] = None) -> Dict[str, Any]:
        """
        Récupère des statistiques réseau pour une période donnée.
        
        Args:
            time_range: Plage de temps pour les statistiques (début, fin)
            
        Returns:
            Dictionnaire contenant les statistiques réseau
        """
        pass


class ITopologyVisualizationService(ABC):
    """
    Interface pour le service de visualisation de topologie intégrée.
    
    Responsable de fournir les données enrichies pour l'affichage des topologies.
    """
    
    @abstractmethod
    async def get_integrated_topology(self, topology_id: int) -> TopologyView:
        """
        Récupère les détails d'une topologie avec informations enrichies.
        
        Args:
            topology_id: ID de la topologie à récupérer
            
        Returns:
            Objet contenant les informations enrichies sur la topologie
        """
        pass
    
    @abstractmethod
    async def get_device_health_status(self, device_id: int) -> DeviceStatus:
        """
        Détermine le statut de santé d'un équipement.
        
        Args:
            device_id: ID de l'équipement
            
        Returns:
            Statut de santé de l'équipement
        """
        pass
    
    @abstractmethod
    async def get_connection_status(self, source_id: int, target_id: int) -> str:
        """
        Détermine le statut d'une connexion entre deux équipements.
        
        Args:
            source_id: ID de l'équipement source
            target_id: ID de l'équipement cible
            
        Returns:
            Statut de la connexion ('critical', 'warning', 'healthy', 'unknown')
        """
        pass 