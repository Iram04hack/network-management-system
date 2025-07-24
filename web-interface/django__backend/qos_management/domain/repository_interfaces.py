"""
Interfaces de repository pour la gestion des politiques QoS.

Ce module définit les interfaces de repository pour la gestion de la qualité de service (QoS)
selon les principes de l'architecture hexagonale et d'Interface Segregation Principle.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional


class QoSPolicyReader(ABC):
    """
    Interface pour la lecture des politiques QoS.
    
    Cette interface définit le contrat pour les opérations de lecture seule
    sur les politiques QoS.
    """
    
    @abstractmethod
    def get_by_id(self, policy_id: int) -> Dict[str, Any]:
        """
        Récupère une politique QoS par son ID.
        
        Args:
            policy_id: ID de la politique
            
        Returns:
            Données de la politique QoS
            
        Raises:
            Exception: Si la politique n'existe pas
        """
        pass
    
    @abstractmethod
    def get_all(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Récupère toutes les politiques QoS correspondant aux filtres.
        
        Args:
            filters: Filtres à appliquer
            
        Returns:
            Liste des politiques QoS
        """
        pass


class QoSPolicyWriter(ABC):
    """
    Interface pour l'écriture des politiques QoS.
    
    Cette interface définit le contrat pour les opérations d'écriture
    sur les politiques QoS.
    """
    
    @abstractmethod
    def create(self, policy_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crée une nouvelle politique QoS.
        
        Args:
            policy_data: Données de la politique
            
        Returns:
            Politique QoS créée
        """
        pass
    
    @abstractmethod
    def update(self, policy_id: int, policy_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Met à jour une politique QoS.
        
        Args:
            policy_id: ID de la politique
            policy_data: Nouvelles données
            
        Returns:
            Politique QoS mise à jour
        """
        pass
    
    @abstractmethod
    def delete(self, policy_id: int) -> bool:
        """
        Supprime une politique QoS.
        
        Args:
            policy_id: ID de la politique
            
        Returns:
            True si la suppression a réussi
        """
        pass


class QoSPolicyQueryService(ABC):
    """
    Interface pour les requêtes spécialisées sur les politiques QoS.
    
    Cette interface définit le contrat pour les opérations de requête avancées
    sur les politiques QoS.
    """
    
    @abstractmethod
    def get_by_device(self, device_id: int) -> List[Dict[str, Any]]:
        """
        Récupère les politiques QoS associées à un équipement.
        
        Args:
            device_id: ID de l'équipement
            
        Returns:
            Liste des politiques QoS
        """
        pass
    
    @abstractmethod
    def get_by_interface(self, interface_id: int) -> List[Dict[str, Any]]:
        """
        Récupère les politiques QoS associées à une interface.
        
        Args:
            interface_id: ID de l'interface
            
        Returns:
            Liste des politiques QoS
        """
        pass
    
    @abstractmethod
    def search_by_criteria(self, criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Recherche des politiques QoS selon des critères spécifiques.
        
        Args:
            criteria: Critères de recherche (nom, type, priorité, etc.)
            
        Returns:
            Liste des politiques QoS correspondantes
        """
        pass


class QoSPolicyRepository(QoSPolicyReader, QoSPolicyWriter, QoSPolicyQueryService):
    """
    Interface complète pour le repository des politiques QoS.
    
    Cette interface hérite de toutes les interfaces spécialisées
    pour offrir une implémentation complète si nécessaire.
    """
    pass 