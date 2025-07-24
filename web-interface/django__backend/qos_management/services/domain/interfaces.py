from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from .entities import QoSPolicyEntity as QoSPolicy, InterfaceQoSPolicyEntity as InterfaceQoSPolicy, TrafficClassEntity as TrafficClass, QoSVisualizationData, QoSRecommendation

class QoSPolicyRepository(ABC):
    @abstractmethod
    def get_by_id(self, policy_id: int) -> QoSPolicy:
        pass
        
    @abstractmethod
    def save(self, policy: QoSPolicy) -> QoSPolicy:
        pass
        
    @abstractmethod
    def delete(self, policy_id: int) -> bool:
        pass
        
    @abstractmethod
    def list_all(self) -> List[QoSPolicy]:
        pass

class InterfaceQoSPolicyRepository(ABC):
    @abstractmethod
    def get_by_interface_and_direction(self, interface_id: int, direction: str) -> Optional[InterfaceQoSPolicy]:
        pass
        
    @abstractmethod
    def save(self, interface_policy: InterfaceQoSPolicy) -> InterfaceQoSPolicy:
        pass
        
    @abstractmethod
    def delete(self, interface_policy_id: int) -> bool:
        pass

class TrafficControlService(ABC):
    @abstractmethod
    def configure_interface(self, interface_name: str, direction: str, 
                          bandwidth_limit: int, traffic_classes: List[TrafficClass]) -> bool:
        pass
        
    @abstractmethod
    def clear_interface(self, interface_name: str) -> bool:
        pass
        
    @abstractmethod
    def test_connection(self) -> bool:
        pass

class QoSMonitoringServiceInterface(ABC):
    @abstractmethod
    def get_interface_statistics(self, interface_name: str) -> Dict[str, Any]:
        """
        Récupère les statistiques d'une interface
        
        Args:
            interface_name: Nom de l'interface
            
        Returns:
            Dictionnaire contenant les statistiques de l'interface
        """
        pass
    
    @abstractmethod
    def get_class_statistics(self, interface_name: str, class_name: str) -> Dict[str, Any]:
        """
        Récupère les statistiques d'une classe de trafic sur une interface
        
        Args:
            interface_name: Nom de l'interface
            class_name: Nom de la classe de trafic
            
        Returns:
            Dictionnaire contenant les statistiques de la classe de trafic
        """
        pass
    
    @abstractmethod
    def get_historical_data(self, interface_name: str, class_name: Optional[str] = None, 
                          time_range: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Récupère les données historiques d'une interface ou d'une classe de trafic
        
        Args:
            interface_name: Nom de l'interface
            class_name: Nom de la classe de trafic (optionnel)
            time_range: Plage de temps pour les données (optionnel)
            
        Returns:
            Dictionnaire contenant les données historiques
        """
        pass

class QoSVisualizationService(ABC):
    @abstractmethod
    def get_policy_visualization(self, policy_id: int) -> QoSVisualizationData:
        """
        Récupère les données de visualisation pour une politique QoS
        
        Args:
            policy_id: ID de la politique QoS
            
        Returns:
            QoSVisualizationData contenant les données de visualisation
            
        Raises:
            ValueError: Si la politique n'existe pas
        """
        pass

class QoSConfigurerService(ABC):
    @abstractmethod
    def generate_recommendations(self, traffic_type: str, network_size: str) -> QoSRecommendation:
        """
        Génère des recommandations de politique QoS basées sur le type de trafic et la taille du réseau
        
        Args:
            traffic_type: Type de trafic (general, voice, streaming, etc.)
            network_size: Taille du réseau (small, medium, large)
            
        Returns:
            QoSRecommendation contenant les recommandations
        """
        pass 