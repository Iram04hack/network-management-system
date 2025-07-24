"""
Ports de sortie pour l'application Network Management.

Ce module définit les interfaces des ports de sortie qui permettent
à la couche application d'interagir avec les adaptateurs secondaires (repositories, services externes, etc.).
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union
from datetime import datetime


class DevicePersistencePort(ABC):
    """
    Interface pour la persistance des équipements réseau.
    
    Cette interface définit le contrat que doit respecter
    tout adaptateur de persistance pour les équipements réseau.
    """
    
    @abstractmethod
    def get_device_by_id(self, device_id: int) -> Dict[str, Any]:
        """
        Récupère un équipement par son ID.
        
        Args:
            device_id: ID de l'équipement
            
        Returns:
            Informations sur l'équipement
        """
        pass
    
    @abstractmethod
    def get_device_by_ip(self, ip_address: str) -> Dict[str, Any]:
        """
        Récupère un équipement par son adresse IP.
        
        Args:
            ip_address: Adresse IP de l'équipement
            
        Returns:
            Informations sur l'équipement
        """
        pass
    
    @abstractmethod
    def get_all_devices(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Récupère tous les équipements correspondant aux filtres.
        
        Args:
            filters: Filtres à appliquer (optionnel)
            
        Returns:
            Liste des équipements
        """
        pass
    
    @abstractmethod
    def create_device(self, device_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crée un nouvel équipement.
        
        Args:
            device_data: Données de l'équipement
            
        Returns:
            Équipement créé
        """
        pass
    
    @abstractmethod
    def update_device(self, device_id: int, device_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Met à jour un équipement.
        
        Args:
            device_id: ID de l'équipement
            device_data: Nouvelles données
            
        Returns:
            Équipement mis à jour
        """
        pass
    
    @abstractmethod
    def delete_device(self, device_id: int) -> bool:
        """
        Supprime un équipement.
        
        Args:
            device_id: ID de l'équipement
            
        Returns:
            True si la suppression a réussi
        """
        pass


class InterfacePersistencePort(ABC):
    """
    Interface pour la persistance des interfaces réseau.
    
    Cette interface définit le contrat que doit respecter
    tout adaptateur de persistance pour les interfaces réseau.
    """
    
    @abstractmethod
    def get_interface_by_id(self, interface_id: int) -> Dict[str, Any]:
        """
        Récupère une interface par son ID.
        
        Args:
            interface_id: ID de l'interface
            
        Returns:
            Informations sur l'interface
        """
        pass
    
    @abstractmethod
    def get_interface_by_name_and_device(self, device_id: int, name: str) -> Dict[str, Any]:
        """
        Récupère une interface par son nom et l'ID de son équipement.
        
        Args:
            device_id: ID de l'équipement
            name: Nom de l'interface
            
        Returns:
            Informations sur l'interface
        """
        pass
    
    @abstractmethod
    def get_interfaces_by_device(self, device_id: int) -> List[Dict[str, Any]]:
        """
        Récupère toutes les interfaces d'un équipement.
        
        Args:
            device_id: ID de l'équipement
            
        Returns:
            Liste des interfaces
        """
        pass
    
    @abstractmethod
    def create_interface(self, interface_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crée une nouvelle interface.
        
        Args:
            interface_data: Données de l'interface
            
        Returns:
            Interface créée
        """
        pass
    
    @abstractmethod
    def update_interface(self, interface_id: int, interface_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Met à jour une interface.
        
        Args:
            interface_id: ID de l'interface
            interface_data: Nouvelles données
            
        Returns:
            Interface mise à jour
        """
        pass
    
    @abstractmethod
    def delete_interface(self, interface_id: int) -> bool:
        """
        Supprime une interface.
        
        Args:
            interface_id: ID de l'interface
            
        Returns:
            True si la suppression a réussi
        """
        pass


class ConnectionPersistencePort(ABC):
    """
    Interface pour la persistance des connexions réseau.
    
    Cette interface définit le contrat que doit respecter
    tout adaptateur de persistance pour les connexions réseau.
    """
    
    @abstractmethod
    def get_connection_by_id(self, connection_id: int) -> Dict[str, Any]:
        """
        Récupère une connexion par son ID.
        
        Args:
            connection_id: ID de la connexion
            
        Returns:
            Informations sur la connexion
        """
        pass
    
    @abstractmethod
    def get_connections_by_device(self, device_id: int) -> List[Dict[str, Any]]:
        """
        Récupère toutes les connexions d'un équipement.
        
        Args:
            device_id: ID de l'équipement
            
        Returns:
            Liste des connexions
        """
        pass
    
    @abstractmethod
    def get_connections_by_interface(self, interface_id: int) -> List[Dict[str, Any]]:
        """
        Récupère toutes les connexions d'une interface.
        
        Args:
            interface_id: ID de l'interface
            
        Returns:
            Liste des connexions
        """
        pass
    
    @abstractmethod
    def create_connection(self, connection_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crée une nouvelle connexion.
        
        Args:
            connection_data: Données de la connexion
            
        Returns:
            Connexion créée
        """
        pass
    
    @abstractmethod
    def update_connection(self, connection_id: int, connection_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Met à jour une connexion.
        
        Args:
            connection_id: ID de la connexion
            connection_data: Nouvelles données
            
        Returns:
            Connexion mise à jour
        """
        pass
    
    @abstractmethod
    def delete_connection(self, connection_id: int) -> bool:
        """
        Supprime une connexion.
        
        Args:
            connection_id: ID de la connexion
            
        Returns:
            True si la suppression a réussi
        """
        pass


class ConfigurationPersistencePort(ABC):
    """
    Interface pour la persistance des configurations d'équipements.
    
    Cette interface définit le contrat que doit respecter
    tout adaptateur de persistance pour les configurations d'équipements.
    """
    
    @abstractmethod
    def get_configuration_by_id(self, config_id: int) -> Dict[str, Any]:
        """
        Récupère une configuration par son ID.
        
        Args:
            config_id: ID de la configuration
            
        Returns:
            Informations sur la configuration
        """
        pass
    
    @abstractmethod
    def get_latest_configuration_by_device(self, device_id: int) -> Dict[str, Any]:
        """
        Récupère la dernière configuration d'un équipement.
        
        Args:
            device_id: ID de l'équipement
            
        Returns:
            Dernière configuration
        """
        pass
    
    @abstractmethod
    def get_configuration_history_by_device(self, device_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Récupère l'historique des configurations d'un équipement.
        
        Args:
            device_id: ID de l'équipement
            limit: Nombre maximum de configurations à récupérer
            
        Returns:
            Liste des configurations
        """
        pass
    
    @abstractmethod
    def create_configuration(self, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crée une nouvelle configuration.
        
        Args:
            config_data: Données de la configuration
            
        Returns:
            Configuration créée
        """
        pass
    
    @abstractmethod
    def update_configuration(self, config_id: int, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Met à jour une configuration.
        
        Args:
            config_id: ID de la configuration
            config_data: Nouvelles données
            
        Returns:
            Configuration mise à jour
        """
        pass
    
    @abstractmethod
    def delete_configuration(self, config_id: int) -> bool:
        """
        Supprime une configuration.
        
        Args:
            config_id: ID de la configuration
            
        Returns:
            True si la suppression a réussi
        """
        pass


class TemplatePersistencePort(ABC):
    """
    Interface pour la persistance des modèles de configuration.
    
    Cette interface définit le contrat que doit respecter
    tout adaptateur de persistance pour les modèles de configuration.
    """
    
    @abstractmethod
    def get_template_by_id(self, template_id: int) -> Dict[str, Any]:
        """
        Récupère un modèle par son ID.
        
        Args:
            template_id: ID du modèle
            
        Returns:
            Informations sur le modèle
        """
        pass
    
    @abstractmethod
    def get_templates_by_device_type(self, device_type: str, vendor: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Récupère les modèles pour un type d'équipement.
        
        Args:
            device_type: Type d'équipement
            vendor: Fabricant (optionnel)
            
        Returns:
            Liste des modèles
        """
        pass
    
    @abstractmethod
    def get_all_templates(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Récupère tous les modèles correspondant aux filtres.
        
        Args:
            filters: Filtres à appliquer (optionnel)
            
        Returns:
            Liste des modèles
        """
        pass
    
    @abstractmethod
    def create_template(self, template_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crée un nouveau modèle.
        
        Args:
            template_data: Données du modèle
            
        Returns:
            Modèle créé
        """
        pass
    
    @abstractmethod
    def update_template(self, template_id: int, template_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Met à jour un modèle.
        
        Args:
            template_id: ID du modèle
            template_data: Nouvelles données
            
        Returns:
            Modèle mis à jour
        """
        pass
    
    @abstractmethod
    def delete_template(self, template_id: int) -> bool:
        """
        Supprime un modèle.
        
        Args:
            template_id: ID du modèle
            
        Returns:
            True si la suppression a réussi
        """
        pass


class TopologyPersistencePort(ABC):
    """
    Interface pour la persistance des topologies réseau.
    
    Cette interface définit le contrat que doit respecter
    tout adaptateur de persistance pour les topologies réseau.
    """
    
    @abstractmethod
    def get_topology(self, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Récupère la topologie réseau correspondant aux filtres.
        
        Args:
            filters: Filtres à appliquer (optionnel)
            
        Returns:
            Topologie réseau
        """
        pass
    
    @abstractmethod
    def save_topology(self, topology_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enregistre une topologie réseau.
        
        Args:
            topology_data: Données de la topologie
            
        Returns:
            Topologie enregistrée
        """
        pass
    
    @abstractmethod
    def update_topology_layout(self, layout_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Met à jour la disposition d'une topologie.
        
        Args:
            layout_data: Données de disposition
            
        Returns:
            Disposition mise à jour
        """
        pass


class AlertPersistencePort(ABC):
    """
    Interface pour la persistance des alertes.
    
    Cette interface définit le contrat que doit respecter
    tout adaptateur de persistance pour les alertes.
    """
    
    @abstractmethod
    def get_alert_by_id(self, alert_id: int) -> Dict[str, Any]:
        """
        Récupère une alerte par son ID.
        
        Args:
            alert_id: ID de l'alerte
            
        Returns:
            Informations sur l'alerte
        """
        pass
    
    @abstractmethod
    def get_alerts(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Récupère les alertes correspondant aux filtres.
        
        Args:
            filters: Filtres à appliquer (optionnel)
            
        Returns:
            Liste des alertes
        """
        pass
    
    @abstractmethod
    def create_alert(self, alert_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crée une nouvelle alerte.
        
        Args:
            alert_data: Données de l'alerte
            
        Returns:
            Alerte créée
        """
        pass
    
    @abstractmethod
    def update_alert(self, alert_id: int, alert_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Met à jour une alerte.
        
        Args:
            alert_id: ID de l'alerte
            alert_data: Nouvelles données
            
        Returns:
            Alerte mise à jour
        """
        pass
    
    @abstractmethod
    def acknowledge_alert(self, alert_id: int, user_id: int, comment: Optional[str] = None) -> Dict[str, Any]:
        """
        Acquitte une alerte.
        
        Args:
            alert_id: ID de l'alerte
            user_id: ID de l'utilisateur
            comment: Commentaire (optionnel)
            
        Returns:
            Alerte acquittée
        """
        pass


class PolicyPersistencePort(ABC):
    """
    Interface pour la persistance des politiques de conformité.
    
    Cette interface définit le contrat que doit respecter
    tout adaptateur de persistance pour les politiques de conformité.
    """
    
    @abstractmethod
    def get_policy_by_id(self, policy_id: int) -> Dict[str, Any]:
        """
        Récupère une politique par son ID.
        
        Args:
            policy_id: ID de la politique
            
        Returns:
            Informations sur la politique
        """
        pass
    
    @abstractmethod
    def get_policies(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Récupère les politiques correspondant aux filtres.
        
        Args:
            filters: Filtres à appliquer (optionnel)
            
        Returns:
            Liste des politiques
        """
        pass
    
    @abstractmethod
    def create_policy(self, policy_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crée une nouvelle politique.
        
        Args:
            policy_data: Données de la politique
            
        Returns:
            Politique créée
        """
        pass
    
    @abstractmethod
    def update_policy(self, policy_id: int, policy_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Met à jour une politique.
        
        Args:
            policy_id: ID de la politique
            policy_data: Nouvelles données
            
        Returns:
            Politique mise à jour
        """
        pass
    
    @abstractmethod
    def delete_policy(self, policy_id: int) -> bool:
        """
        Supprime une politique.
        
        Args:
            policy_id: ID de la politique
            
        Returns:
            True si la suppression a réussi
        """
        pass


class MetricPersistencePort(ABC):
    """
    Interface pour la persistance des métriques.
    
    Cette interface définit le contrat que doit respecter
    tout adaptateur de persistance pour les métriques.
    """
    
    @abstractmethod
    def save_device_metrics(self, device_id: int, metrics: Dict[str, Any], timestamp: Optional[datetime] = None) -> bool:
        """
        Enregistre des métriques pour un équipement.
        
        Args:
            device_id: ID de l'équipement
            metrics: Métriques à enregistrer
            timestamp: Horodatage (optionnel, utilise l'heure actuelle par défaut)
            
        Returns:
            True si l'enregistrement a réussi
        """
        pass
    
    @abstractmethod
    def save_interface_metrics(self, interface_id: int, metrics: Dict[str, Any], timestamp: Optional[datetime] = None) -> bool:
        """
        Enregistre des métriques pour une interface.
        
        Args:
            interface_id: ID de l'interface
            metrics: Métriques à enregistrer
            timestamp: Horodatage (optionnel, utilise l'heure actuelle par défaut)
            
        Returns:
            True si l'enregistrement a réussi
        """
        pass
    
    @abstractmethod
    def get_device_metrics(self, device_id: int, metrics: List[str], timeframe: Dict[str, Any]) -> Dict[str, Any]:
        """
        Récupère les métriques d'un équipement.
        
        Args:
            device_id: ID de l'équipement
            metrics: Liste des métriques à récupérer
            timeframe: Période de temps (début, fin, granularité)
            
        Returns:
            Métriques de l'équipement
        """
        pass
    
    @abstractmethod
    def get_interface_metrics(self, interface_id: int, metrics: List[str], timeframe: Dict[str, Any]) -> Dict[str, Any]:
        """
        Récupère les métriques d'une interface.
        
        Args:
            interface_id: ID de l'interface
            metrics: Liste des métriques à récupérer
            timeframe: Période de temps (début, fin, granularité)
            
        Returns:
            Métriques de l'interface
        """
        pass


class LogPersistencePort(ABC):
    """
    Interface pour la persistance des logs.
    
    Cette interface définit le contrat que doit respecter
    tout adaptateur de persistance pour les logs.
    """
    
    @abstractmethod
    def save_log(self, log_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enregistre un log.
        
        Args:
            log_data: Données du log
            
        Returns:
            Log enregistré
        """
        pass
    
    @abstractmethod
    def get_logs(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Récupère les logs correspondant aux filtres.
        
        Args:
            filters: Filtres à appliquer (optionnel)
            
        Returns:
            Liste des logs
        """
        pass
    
    @abstractmethod
    def get_device_logs(self, device_id: int, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Récupère les logs d'un équipement.
        
        Args:
            device_id: ID de l'équipement
            filters: Filtres à appliquer (optionnel)
            
        Returns:
            Liste des logs
        """
        pass 