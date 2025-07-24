"""
Cas d'utilisation pour le module de tableau de bord.

Ce module implémente la logique métier du domaine de tableau de bord
indépendamment de l'infrastructure technique ou de l'interface utilisateur.
"""

from typing import Dict, Any, List
from ..domain.interfaces import IDashboardDataService, INetworkOverviewService, ITopologyVisualizationService

class GetDashboardOverviewUseCase:
    """Cas d'utilisation pour récupérer la vue d'ensemble du tableau de bord."""
    
    def __init__(self, dashboard_service: IDashboardDataService):
        self.dashboard_service = dashboard_service
    
    def execute(self) -> Dict[str, Any]:
        """
        Récupère les données consolidées pour la vue d'ensemble du tableau de bord.
        
        Returns:
            Dictionnaire contenant les données agrégées du tableau de bord
        """
        return self.dashboard_service.get_dashboard_overview()

class GetSystemHealthMetricsUseCase:
    """Cas d'utilisation pour récupérer les métriques de santé du système."""
    
    def __init__(self, dashboard_service: IDashboardDataService):
        self.dashboard_service = dashboard_service
    
    def execute(self) -> Dict[str, float]:
        """
        Récupère les métriques de santé du système.
        
        Returns:
            Dictionnaire contenant les métriques de santé système
        """
        return self.dashboard_service.get_system_health_metrics()

class GetNetworkOverviewUseCase:
    """Cas d'utilisation pour récupérer la vue d'ensemble du réseau."""
    
    def __init__(self, network_overview_service: INetworkOverviewService):
        self.network_overview_service = network_overview_service
    
    def execute(self) -> Dict[str, Any]:
        """
        Récupère une vue d'ensemble du réseau avec les informations de santé.
        
        Returns:
            Dictionnaire contenant les informations sur les topologies, anomalies et alertes
        """
        return self.network_overview_service.get_network_overview()

class GetIntegratedTopologyUseCase:
    """Cas d'utilisation pour récupérer une topologie intégrée avec données enrichies."""
    
    def __init__(self, topology_visualization_service: ITopologyVisualizationService):
        self.topology_service = topology_visualization_service
    
    def execute(self, topology_id: int) -> Dict[str, Any]:
        """
        Récupère les détails d'une topologie avec informations enrichies.
        
        Args:
            topology_id: ID de la topologie à récupérer
            
        Returns:
            Dictionnaire contenant les informations enrichies sur la topologie
        """
        return self.topology_service.get_integrated_topology(topology_id)

class GetDeviceHealthStatusUseCase:
    """Cas d'utilisation pour récupérer le statut de santé d'un équipement."""
    
    def __init__(self, topology_visualization_service: ITopologyVisualizationService):
        self.topology_service = topology_visualization_service
    
    def execute(self, device_id: int) -> str:
        """
        Détermine le statut de santé d'un équipement.
        
        Args:
            device_id: ID de l'équipement
            
        Returns:
            Statut de santé de l'équipement ('critical', 'warning', 'healthy', 'inactive')
        """
        return self.topology_service.get_device_health_status(device_id)

class GetConnectionStatusUseCase:
    """Cas d'utilisation pour récupérer le statut d'une connexion réseau."""
    
    def __init__(self, topology_visualization_service: ITopologyVisualizationService):
        self.topology_service = topology_visualization_service
    
    def execute(self, connection_id: int) -> str:
        """
        Détermine le statut d'une connexion.
        
        Args:
            connection_id: ID de la connexion
            
        Returns:
            Statut de la connexion ('critical', 'warning', 'healthy', 'unknown')
        """
        return self.topology_service.get_connection_status(connection_id)