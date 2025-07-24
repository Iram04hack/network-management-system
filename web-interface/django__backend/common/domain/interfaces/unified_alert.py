"""
Interface pour le service d'alerte unifié.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional


class UnifiedAlertInterface(ABC):
    """Interface pour le service d'alerte unifié qui centralise les alertes de différentes sources."""

    @abstractmethod
    def get_all_alerts(
        self, 
        days: int = 7, 
        filter_by: Optional[Dict[str, Any]] = None,
        user_id: Optional[int] = None, 
        device_ids: Optional[List[int]] = None,
        limit: int = 100
    ) -> Dict[str, Any]:
        """
        Récupère toutes les alertes de toutes les sources.
        
        Args:
            days: Nombre de jours en arrière pour la recherche
            filter_by: Filtres à appliquer (severity, status, etc.)
            user_id: ID de l'utilisateur pour filtrer les alertes ack
            device_ids: Liste des IDs d'équipements à filtrer
            limit: Nombre maximum d'alertes à retourner
            
        Returns:
            Alertes consolidées de toutes les sources
        """
        pass

    @abstractmethod
    def acknowledge_alert(self, alert_id: str, user_id: int) -> Dict[str, Any]:
        """
        Acquitte une alerte.
        
        Args:
            alert_id: ID de l'alerte au format "type-id"
            user_id: ID de l'utilisateur qui acquitte
            
        Returns:
            Résultat de l'opération
        """
        pass

    @abstractmethod
    def resolve_alert(self, alert_id: str, user_id: int) -> Dict[str, Any]:
        """
        Résoud une alerte.
        
        Args:
            alert_id: ID de l'alerte au format "type-id"
            user_id: ID de l'utilisateur qui résoud
            
        Returns:
            Résultat de l'opération
        """
        pass

    @abstractmethod
    def get_alert_statistics(self, days: int = 7, device_ids: Optional[List[int]] = None) -> Dict[str, Any]:
        """
        Récupère des statistiques sur les alertes.
        
        Args:
            days: Nombre de jours en arrière pour la recherche
            device_ids: Liste des IDs d'équipements à filtrer
            
        Returns:
            Statistiques sur les alertes
        """
        pass 