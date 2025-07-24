"""
Interfaces du domaine pour le module QoS Management.

Ce module définit les interfaces du domaine pour la gestion de la qualité de service (QoS)
selon les principes de l'architecture hexagonale.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from datetime import datetime

# Importation des interfaces de repository séparées
from .repository_interfaces import (
    QoSPolicyReader,
    QoSPolicyWriter,
    QoSPolicyQueryService,
    QoSPolicyRepository
)


class NetworkDeviceRepository(ABC):
    """
    Interface pour le repository des équipements réseau.
    
    Cette interface définit le contrat que doit respecter
    tout repository permettant de gérer les équipements réseau
    dans le contexte QoS.
    """
    
    @abstractmethod
    def get_device(self, device_id: int) -> Optional[Dict[str, Any]]:
        """
        Récupère un équipement réseau par son ID.
        
        Args:
            device_id: ID de l'équipement
            
        Returns:
            Données de l'équipement ou None si non trouvé
        """
        pass
    
    @abstractmethod
    def list_devices(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Liste les équipements réseau selon des filtres optionnels.
        
        Args:
            filters: Filtres à appliquer (type, status, location, etc.)
            
        Returns:
            Liste des équipements correspondants
        """
        pass
    
    @abstractmethod
    def get_device_interfaces(self, device_id: int) -> List[Dict[str, Any]]:
        """
        Récupère les interfaces d'un équipement.
        
        Args:
            device_id: ID de l'équipement
            
        Returns:
            Liste des interfaces de l'équipement
        """
        pass
    
    @abstractmethod
    def get_device_qos_capabilities(self, device_id: int) -> Dict[str, Any]:
        """
        Récupère les capacités QoS d'un équipement.
        
        Args:
            device_id: ID de l'équipement
            
        Returns:
            Capacités QoS supportées par l'équipement
        """
        pass
    
    @abstractmethod
    def update_device_qos_config(self, device_id: int, qos_config: Dict[str, Any]) -> bool:
        """
        Met à jour la configuration QoS d'un équipement.
        
        Args:
            device_id: ID de l'équipement
            qos_config: Configuration QoS à appliquer
            
        Returns:
            True si la mise à jour a réussi
        """
        pass
    
    @abstractmethod
    def get_device_status(self, device_id: int) -> Dict[str, Any]:
        """
        Récupère le statut d'un équipement.
        
        Args:
            device_id: ID de l'équipement
            
        Returns:
            Statut de l'équipement (online, offline, error, etc.)
        """
        pass


class QoSConfigurationService(ABC):
    """
    Interface pour le service de configuration de QoS.
    
    Cette interface définit le contrat que doit respecter
    tout service permettant d'appliquer des configurations de QoS
    aux équipements réseau.
    """
    
    @abstractmethod
    def apply_policy(self, device_id: int, interface_id: int, policy_id: int) -> bool:
        """
        Applique une politique QoS à une interface d'un équipement.
        
        Args:
            device_id: ID de l'équipement
            interface_id: ID de l'interface
            policy_id: ID de la politique
            
        Returns:
            True si l'application a réussi
        """
        pass
    
    @abstractmethod
    def remove_policy(self, device_id: int, interface_id: int) -> bool:
        """
        Supprime la politique QoS d'une interface.
        
        Args:
            device_id: ID de l'équipement
            interface_id: ID de l'interface
            
        Returns:
            True si la suppression a réussi
        """
        pass
    
    @abstractmethod
    def get_applied_policies(self, device_id: int) -> Dict[str, Any]:
        """
        Récupère les politiques QoS appliquées sur un équipement.
        
        Args:
            device_id: ID de l'équipement
            
        Returns:
            Dictionnaire des politiques appliquées par interface
        """
        pass


class QoSVisualizationService(ABC):
    """
    Interface pour le service de visualisation QoS.
    
    Cette interface définit le contrat que doit respecter
    tout service permettant de générer des visualisations
    des politiques et performances QoS.
    """
    
    @abstractmethod
    def get_policy_visualization(self, policy_id: int) -> Dict[str, Any]:
        """
        Récupère les données de visualisation pour une politique QoS.
        
        Args:
            policy_id: ID de la politique QoS
            
        Returns:
            Données de visualisation pour la politique
        """
        pass


class QoSMonitoringService(ABC):
    """
    Interface pour le service de monitoring QoS.
    
    Cette interface définit le contrat que doit respecter
    tout service permettant de surveiller les performances QoS.
    """
    
    @abstractmethod
    def get_metrics(self, device_id: int, interface_id: Optional[int] = None, 
                    period: str = "1h") -> Dict[str, Any]:
        """
        Récupère les métriques QoS d'un équipement ou d'une interface.
        
        Args:
            device_id: ID de l'équipement
            interface_id: ID de l'interface (optionnel)
            period: Période sur laquelle récupérer les métriques
            
        Returns:
            Métriques QoS
        """
        pass
    
    @abstractmethod
    def get_interface_metrics(self, interface_name: str, duration: str = '1h') -> Dict[str, Any]:
        """
        Récupère les métriques de performance pour une interface réseau spécifique.
        
        Args:
            interface_name: Nom de l'interface
            duration: Durée de l'historique (ex: 1h, 12h, 1d)
            
        Returns:
            Dict contenant les métriques de performance
        """
        pass
    
    @abstractmethod
    def get_sla_compliance(self, device_id: int, period: str = "24h") -> Dict[str, Any]:
        """
        Récupère le taux de conformité aux SLA pour un équipement.
        
        Args:
            device_id: ID de l'équipement
            period: Période sur laquelle calculer la conformité
            
        Returns:
            Rapport de conformité SLA
        """
        pass
    
    @abstractmethod
    def get_qos_report(self, device_ids: Optional[List[int]] = None, 
                      period: str = "7d") -> Dict[str, Any]:
        """
        Génère un rapport global sur les performances QoS.
        
        Args:
            device_ids: Liste des IDs d'équipements à inclure (optionnel)
            period: Période du rapport
            
        Returns:
            Rapport QoS
        """
        pass


class TrafficClassificationService(ABC):
    """
    Interface pour le service de classification de trafic.
    
    Cette interface définit le contrat que doit respecter
    tout service permettant de classifier le trafic réseau
    pour appliquer des politiques QoS.
    """
    
    @abstractmethod
    def classify_traffic(self, traffic_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Classifie le trafic réseau.
        
        Args:
            traffic_data: Données de trafic à classifier
            
        Returns:
            Classification du trafic
        """
        pass
    
    @abstractmethod
    def suggest_qos_policy(self, traffic_class: str) -> Dict[str, Any]:
        """
        Suggère une politique QoS adaptée à une classe de trafic.
        
        Args:
            traffic_class: Classe de trafic
            
        Returns:
            Politique QoS suggérée
        """
        pass
    
    @abstractmethod
    def get_traffic_classes(self) -> List[str]:
        """
        Récupère la liste des classes de trafic disponibles.
        
        Returns:
            Liste des classes de trafic
        """
        pass


class TrafficClassRepository(ABC):
    """
    Interface pour le repository des classes de trafic.
    
    Définit les méthodes pour manipuler les classes de trafic.
    """
    
    @abstractmethod
    def get_traffic_class(self, class_id: int) -> Dict[str, Any]:
        """
        Récupère une classe de trafic par son ID.
        
        Args:
            class_id: ID de la classe de trafic
            
        Returns:
            Données de la classe de trafic
        """
        pass
    
    @abstractmethod
    def list_traffic_classes(self, policy_id: Optional[int] = None, 
                           filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Liste les classes de trafic selon des filtres optionnels.
        
        Args:
            policy_id: ID de la politique QoS (optionnel)
            filters: Dictionnaire de filtres
            
        Returns:
            Liste des classes de trafic
        """
        pass
    
    @abstractmethod
    def create_traffic_class(self, class_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crée une nouvelle classe de trafic.
        
        Args:
            class_data: Données de la classe de trafic
            
        Returns:
            Classe de trafic créée
        """
        pass
    
    @abstractmethod
    def update_traffic_class(self, class_id: int, class_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Met à jour une classe de trafic existante.
        
        Args:
            class_id: ID de la classe de trafic
            class_data: Nouvelles données
            
        Returns:
            Classe de trafic mise à jour
        """
        pass
    
    @abstractmethod
    def delete_traffic_class(self, class_id: int) -> bool:
        """
        Supprime une classe de trafic.
        
        Args:
            class_id: ID de la classe de trafic
            
        Returns:
            True si la suppression a réussi
        """
        pass


class TrafficClassifierRepository(ABC):
    """
    Interface pour le repository des classificateurs de trafic.
    
    Définit les méthodes pour manipuler les classificateurs.
    """
    
    @abstractmethod
    def get_classifier(self, classifier_id: int) -> Dict[str, Any]:
        """
        Récupère un classificateur par son ID.
        
        Args:
            classifier_id: ID du classificateur
            
        Returns:
            Données du classificateur
        """
        pass
    
    @abstractmethod
    def list_classifiers(self, traffic_class_id: Optional[int] = None, 
                       filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Liste les classificateurs selon des filtres optionnels.
        
        Args:
            traffic_class_id: ID de la classe de trafic (optionnel)
            filters: Dictionnaire de filtres
            
        Returns:
            Liste des classificateurs
        """
        pass
    
    @abstractmethod
    def create_classifier(self, classifier_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crée un nouveau classificateur.
        
        Args:
            classifier_data: Données du classificateur
            
        Returns:
            Classificateur créé
        """
        pass
    
    @abstractmethod
    def update_classifier(self, classifier_id: int, classifier_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Met à jour un classificateur existant.
        
        Args:
            classifier_id: ID du classificateur
            classifier_data: Nouvelles données
            
        Returns:
            Classificateur mis à jour
        """
        pass
    
    @abstractmethod
    def delete_classifier(self, classifier_id: int) -> bool:
        """
        Supprime un classificateur.
        
        Args:
            classifier_id: ID du classificateur
            
        Returns:
            True si la suppression a réussi
        """
        pass


class InterfaceQoSPolicyRepository(ABC):
    """
    Interface pour le repository des politiques QoS appliquées aux interfaces.
    
    Définit les méthodes pour gérer l'association entre politiques et interfaces.
    """
    
    @abstractmethod
    def get_interface_policy(self, interface_id: int) -> Dict[str, Any]:
        """
        Récupère la politique QoS appliquée à une interface.
        
        Args:
            interface_id: ID de l'interface
            
        Returns:
            Politique QoS appliquée
        """
        pass
    
    @abstractmethod
    def list_interface_policies(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Liste les associations interface-politique selon des filtres optionnels.
        
        Args:
            filters: Dictionnaire de filtres
            
        Returns:
            Liste des associations interface-politique
        """
        pass
    
    @abstractmethod
    def apply_policy_to_interface(self, policy_id: int, interface_id: int, 
                                parameters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Applique une politique QoS à une interface.
        
        Args:
            policy_id: ID de la politique
            interface_id: ID de l'interface
            parameters: Paramètres d'application (optionnel)
            
        Returns:
            Association créée
        """
        pass
    
    @abstractmethod
    def remove_policy_from_interface(self, interface_id: int) -> bool:
        """
        Supprime la politique QoS d'une interface.
        
        Args:
            interface_id: ID de l'interface
            
        Returns:
            True si la suppression a réussi
        """
        pass


class TrafficControlService(ABC):
    """
    Interface pour le service de contrôle de trafic.
    
    Cette interface définit le contrat que doit respecter
    tout service permettant de contrôler le flux de trafic.
    """
    
    @abstractmethod
    def apply_policy(self, policy_data: Dict[str, Any], interface_name: str) -> Dict[str, Any]:
        """
        Applique une politique de contrôle de trafic à une interface.
        
        Args:
            policy_data: Données de la politique
            interface_name: Nom de l'interface
            
        Returns:
            Résultat de l'application
        """
        pass
    
    @abstractmethod
    def remove_policy(self, interface_name: str) -> Dict[str, Any]:
        """
        Supprime la politique de contrôle de trafic d'une interface.
        
        Args:
            interface_name: Nom de l'interface
            
        Returns:
            Résultat de la suppression
        """
        pass
    
    @abstractmethod
    def get_statistics(self, interface_name: str) -> Dict[str, Any]:
        """
        Récupère les statistiques de trafic d'une interface.
        
        Args:
            interface_name: Nom de l'interface
            
        Returns:
            Statistiques de trafic
        """
        pass
    
    @abstractmethod
    def validate_policy(self, policy_data: Dict[str, Any], 
                      interface_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Valide une politique de contrôle de trafic.
        
        Args:
            policy_data: Données de la politique
            interface_name: Nom de l'interface (optionnel)
            
        Returns:
            Résultat de la validation
        """
        pass 