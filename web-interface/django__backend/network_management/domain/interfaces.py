"""
Interfaces du domaine pour le module Network Management.

Ce module définit les interfaces du domaine pour la gestion du réseau
selon les principes de l'architecture hexagonale.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union, Callable, TypeVar, Generic
from datetime import datetime

T = TypeVar('T')
Entity = TypeVar('Entity')


class Repository(Generic[Entity], ABC):
    """
    Interface générique pour tous les repositories.
    
    Cette interface définit le contrat de base que tout repository doit respecter.
    """
    
    @abstractmethod
    def get_by_id(self, entity_id: int) -> Entity:
        """
        Récupère une entité par son ID.
        
        Args:
            entity_id: ID de l'entité
            
        Returns:
            L'entité récupérée
            
        Raises:
            ResourceNotFoundException: Si l'entité n'existe pas
        """
        pass
    
    @abstractmethod
    def get_all(self, filters: Optional[Dict[str, Any]] = None) -> List[Entity]:
        """
        Récupère toutes les entités correspondant aux filtres.
        
        Args:
            filters: Filtres à appliquer (optionnel)
            
        Returns:
            Liste des entités
        """
        pass
    
    @abstractmethod
    def create(self, entity_data: Dict[str, Any]) -> Entity:
        """
        Crée une nouvelle entité.
        
        Args:
            entity_data: Données de l'entité
            
        Returns:
            L'entité créée
        """
        pass
    
    @abstractmethod
    def update(self, entity_id: int, entity_data: Dict[str, Any]) -> Entity:
        """
        Met à jour une entité.
        
        Args:
            entity_id: ID de l'entité
            entity_data: Nouvelles données
            
        Returns:
            L'entité mise à jour
        """
        pass
    
    @abstractmethod
    def delete(self, entity_id: int) -> bool:
        """
        Supprime une entité.
        
        Args:
            entity_id: ID de l'entité
            
        Returns:
            True si la suppression a réussi
        """
        pass


class NetworkDeviceRepository(Repository[Dict[str, Any]], ABC):
    """
    Interface pour le repository des équipements réseau.
    
    Cette interface définit le contrat que doit respecter
    tout repository permettant de persister les équipements réseau.
    """
    
    @abstractmethod
    def get_by_ip(self, ip_address: str) -> Dict[str, Any]:
        """
        Récupère un équipement réseau par son adresse IP.
        
        Args:
            ip_address: Adresse IP de l'équipement
            
        Returns:
            Informations sur l'équipement
            
        Raises:
            ResourceNotFoundException: Si l'équipement n'existe pas
        """
        pass


class NetworkInterfaceRepository(Repository[Dict[str, Any]], ABC):
    """
    Interface pour le repository des interfaces réseau.
    
    Cette interface définit le contrat que doit respecter
    tout repository permettant de persister les interfaces réseau.
    """
    
    @abstractmethod
    def get_by_name_and_device(self, device_id: int, name: str) -> Dict[str, Any]:
        """
        Récupère une interface réseau par son nom et l'ID de son équipement.
        
        Args:
            device_id: ID de l'équipement
            name: Nom de l'interface
            
        Returns:
            Informations sur l'interface
            
        Raises:
            ResourceNotFoundException: Si l'interface n'existe pas
        """
        pass
    
    @abstractmethod
    def get_all_by_device(self, device_id: int) -> List[Dict[str, Any]]:
        """
        Récupère toutes les interfaces d'un équipement réseau.
        
        Args:
            device_id: ID de l'équipement
            
        Returns:
            Liste des interfaces
        """
        pass


class NetworkConnectionRepository(Repository[Dict[str, Any]], ABC):
    """
    Interface pour le repository des connexions réseau.
    
    Cette interface définit le contrat que doit respecter
    tout repository permettant de persister les connexions réseau.
    """
    
    @abstractmethod
    def get_all_by_device(self, device_id: int) -> List[Dict[str, Any]]:
        """
        Récupère toutes les connexions d'un équipement réseau.
        
        Args:
            device_id: ID de l'équipement
            
        Returns:
            Liste des connexions
        """
        pass


class EventBus(ABC):
    """
    Interface pour le bus d'événements.
    
    Cette interface définit le contrat que doit respecter
    tout service de bus d'événements pour la communication entre modules.
    """
    
    @abstractmethod
    def publish(self, event: Any) -> bool:
        """
        Publie un événement de manière synchrone.
        
        Args:
            event: L'événement à publier
            
        Returns:
            True si la publication a réussi
        """
        pass
    
    @abstractmethod
    def publish_async(self, event: Any) -> bool:
        """
        Publie un événement de manière asynchrone.
        
        Args:
            event: L'événement à publier
            
        Returns:
            True si la publication a été mise en file d'attente
        """
        pass
    
    @abstractmethod
    def subscribe(self, event_type: str, handler: Callable[[Any], None]) -> str:
        """
        Souscrit à un type d'événement.
        
        Args:
            event_type: Type d'événement
            handler: Fonction de traitement
            
        Returns:
            ID de souscription
        """
        pass
    
    @abstractmethod
    def unsubscribe(self, subscription_id: str) -> bool:
        """
        Annule une souscription.
        
        Args:
            subscription_id: ID de souscription
            
        Returns:
            True si la désinscription a réussi
        """
        pass


class DeviceConfigurationRepository(Repository[Dict[str, Any]], ABC):
    """
    Interface pour le repository des configurations d'équipements.
    
    Cette interface définit le contrat que doit respecter
    tout repository permettant de persister les configurations d'équipements.
    """
    
    @abstractmethod
    def get_latest_by_device(self, device_id: int) -> Dict[str, Any]:
        """
        Récupère la dernière configuration d'un équipement.
        
        Args:
            device_id: ID de l'équipement
            
        Returns:
            Configuration de l'équipement
            
        Raises:
            ResourceNotFoundException: Si aucune configuration n'existe
        """
        pass
    
    @abstractmethod
    def get_history_by_device(self, device_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Récupère l'historique des configurations d'un équipement.
        
        Args:
            device_id: ID de l'équipement
            limit: Nombre maximum de configurations à récupérer
            
        Returns:
            Liste des configurations
        """
        pass


class DeviceConfigPort(ABC):
    """
    Interface pour la gestion des configurations d'équipements.

    Cette interface définit le contrat que doit respecter
    tout adaptateur pour la gestion des configurations d'équipements.
    """

    @abstractmethod
    def get_current_config(self, device_id: int) -> Dict[str, Any]:
        """
        Récupère la configuration actuelle d'un équipement.

        Args:
            device_id: ID de l'équipement

        Returns:
            Configuration actuelle
        """
        pass

    @abstractmethod
    def apply_config(self, device_id: int, config_id: int) -> Dict[str, Any]:
        """
        Applique une configuration à un équipement.

        Args:
            device_id: ID de l'équipement
            config_id: ID de la configuration

        Returns:
            Résultat de l'opération
        """
        pass

    @abstractmethod
    def rollback_config(self, device_id: int, version_id: int) -> Dict[str, Any]:
        """
        Restaure une version précédente de la configuration.

        Args:
            device_id: ID de l'équipement
            version_id: ID de la version

        Returns:
            Résultat de l'opération
        """
        pass


class ConfigurationValidationPort(ABC):
    """
    Interface pour la validation des configurations.

    Cette interface définit le contrat que doit respecter
    tout adaptateur pour la validation des configurations.
    """

    @abstractmethod
    def validate(self, device_id: int, config_content: str) -> Dict[str, Any]:
        """
        Valide une configuration pour un équipement.

        Args:
            device_id: ID de l'équipement
            config_content: Contenu de la configuration

        Returns:
            Résultat de la validation
        """
        pass


class ConfigurationTemplateService(ABC):
    """
    Interface pour le service de modèles de configuration.

    Cette interface définit le contrat que doit respecter
    tout service de gestion des modèles de configuration.
    """

    @abstractmethod
    def extract_variables(self, template_content: str) -> List[str]:
        """
        Extrait les variables d'un modèle.

        Args:
            template_content: Contenu du modèle

        Returns:
            Liste des variables
        """
        pass

    @abstractmethod
    def render_template(self, template_id: int, variables: Dict[str, Any]) -> str:
        """
        Génère une configuration à partir d'un modèle.

        Args:
            template_id: ID du modèle
            variables: Variables à injecter

        Returns:
            Configuration générée
        """
        pass


class NetworkDiscoveryPort(ABC):
    """
    Interface pour la découverte réseau.

    Cette interface définit le contrat que doit respecter
    tout adaptateur pour la découverte d'équipements réseau.
    """

    @abstractmethod
    def discover_devices(self, network_range: str, discovery_options: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Découvre les équipements dans une plage réseau.

        Args:
            network_range: Plage réseau à scanner (ex: "192.168.1.0/24")
            discovery_options: Options de découverte (optionnel)

        Returns:
            Liste des équipements découverts
        """
        pass

    @abstractmethod
    def discover_device_details(self, ip_address: str, discovery_options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Découvre les détails d'un équipement spécifique.

        Args:
            ip_address: Adresse IP de l'équipement
            discovery_options: Options de découverte (optionnel)

        Returns:
            Détails de l'équipement
        """
        pass

    @abstractmethod
    def discover_topology(self, seed_devices: List[str], discovery_options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Découvre la topologie réseau à partir d'équipements de départ.

        Args:
            seed_devices: Liste des adresses IP des équipements de départ
            discovery_options: Options de découverte (optionnel)

        Returns:
            Topologie découverte
        """
        pass


class NetworkTopologyRepository(Repository[Dict[str, Any]], ABC):
    """
    Interface pour le repository des topologies réseau.

    Cette interface définit le contrat que doit respecter
    tout repository permettant de persister les topologies réseau.
    """

    @abstractmethod
    def get_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Récupère une topologie par son nom.

        Args:
            name: Nom de la topologie

        Returns:
            Topologie trouvée ou None
        """
        pass

    @abstractmethod
    def get_connections_by_topology(self, topology_id: int) -> List[Dict[str, Any]]:
        """
        Récupère les connexions d'une topologie.

        Args:
            topology_id: ID de la topologie

        Returns:
            Liste des connexions
        """
        pass

    @abstractmethod
    def add_device_to_topology(self, topology_id: int, device_id: int) -> bool:
        """
        Ajoute un équipement à une topologie.

        Args:
            topology_id: ID de la topologie
            device_id: ID de l'équipement

        Returns:
            True si l'ajout a réussi
        """
        pass

    @abstractmethod
    def remove_device_from_topology(self, topology_id: int, device_id: int) -> bool:
        """
        Supprime un équipement d'une topologie.

        Args:
            topology_id: ID de la topologie
            device_id: ID de l'équipement

        Returns:
            True si la suppression a réussi
        """
        pass