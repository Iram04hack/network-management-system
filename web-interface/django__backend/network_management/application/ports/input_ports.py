"""
Ports d'entrée pour l'application Network Management.

Ce module définit les interfaces des ports d'entrée qui permettent
aux adaptateurs primaires (UI, API, etc.) d'interagir avec la couche application.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union


class NetworkDeviceUseCases(ABC):
    """
    Interface pour les cas d'utilisation liés aux équipements réseau.
    
    Cette interface définit le contrat que doivent respecter
    les services applicatifs qui gèrent les équipements réseau.
    """
    
    @abstractmethod
    def get_device(self, device_id: int) -> Dict[str, Any]:
        """
        Récupère un équipement réseau par son ID.
        
        Args:
            device_id: ID de l'équipement
            
        Returns:
            Informations sur l'équipement
        """
        pass
    
    @abstractmethod
    def get_all_devices(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Récupère tous les équipements réseau correspondant aux filtres.
        
        Args:
            filters: Filtres à appliquer (optionnel)
            
        Returns:
            Liste des équipements
        """
        pass
    
    @abstractmethod
    def create_device(self, device_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crée un nouvel équipement réseau.
        
        Args:
            device_data: Données de l'équipement
            
        Returns:
            Équipement créé
        """
        pass
    
    @abstractmethod
    def update_device(self, device_id: int, device_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Met à jour un équipement réseau.
        
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
        Supprime un équipement réseau.
        
        Args:
            device_id: ID de l'équipement
            
        Returns:
            True si la suppression a réussi
        """
        pass
    
    @abstractmethod
    def get_device_interfaces(self, device_id: int) -> List[Dict[str, Any]]:
        """
        Récupère les interfaces d'un équipement réseau.
        
        Args:
            device_id: ID de l'équipement
            
        Returns:
            Liste des interfaces
        """
        pass
    
    @abstractmethod
    def get_device_status(self, device_id: int) -> Dict[str, Any]:
        """
        Récupère le statut d'un équipement réseau.
        
        Args:
            device_id: ID de l'équipement
            
        Returns:
            Statut de l'équipement
        """
        pass


class NetworkInterfaceUseCases(ABC):
    """
    Interface pour les cas d'utilisation liés aux interfaces réseau.
    
    Cette interface définit le contrat que doivent respecter
    les services applicatifs qui gèrent les interfaces réseau.
    """
    
    @abstractmethod
    def get_interface(self, interface_id: int) -> Dict[str, Any]:
        """
        Récupère une interface réseau par son ID.
        
        Args:
            interface_id: ID de l'interface
            
        Returns:
            Informations sur l'interface
        """
        pass
    
    @abstractmethod
    def get_interface_by_name_and_device(self, device_id: int, name: str) -> Dict[str, Any]:
        """
        Récupère une interface réseau par son nom et l'ID de son équipement.
        
        Args:
            device_id: ID de l'équipement
            name: Nom de l'interface
            
        Returns:
            Informations sur l'interface
        """
        pass
    
    @abstractmethod
    def update_interface(self, interface_id: int, interface_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Met à jour une interface réseau.
        
        Args:
            interface_id: ID de l'interface
            interface_data: Nouvelles données
            
        Returns:
            Interface mise à jour
        """
        pass
    
    @abstractmethod
    def get_interface_statistics(self, interface_id: int) -> Dict[str, Any]:
        """
        Récupère les statistiques d'une interface réseau.
        
        Args:
            interface_id: ID de l'interface
            
        Returns:
            Statistiques de l'interface
        """
        pass


class NetworkDiscoveryUseCases(ABC):
    """
    Interface pour les cas d'utilisation liés à la découverte réseau.
    
    Cette interface définit le contrat que doivent respecter
    les services applicatifs qui gèrent la découverte réseau.
    """
    
    @abstractmethod
    def discover_device(self, ip_address: str, credentials: Dict[str, Any]) -> Dict[str, Any]:
        """
        Découvre un équipement réseau.
        
        Args:
            ip_address: Adresse IP de l'équipement
            credentials: Informations d'authentification
            
        Returns:
            Informations sur l'équipement découvert
        """
        pass
    
    @abstractmethod
    def discover_subnet(self, subnet: str, credentials: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Découvre les équipements d'un sous-réseau.
        
        Args:
            subnet: Sous-réseau CIDR (e.g. "192.168.1.0/24")
            credentials: Informations d'authentification
            
        Returns:
            Liste des équipements découverts
        """
        pass
    
    @abstractmethod
    def discover_topology(self, seed_devices: List[str], credentials: Dict[str, Any]) -> Dict[str, Any]:
        """
        Découvre la topologie réseau à partir d'équipements de départ.
        
        Args:
            seed_devices: Liste d'adresses IP des équipements de départ
            credentials: Informations d'authentification
            
        Returns:
            Topologie découverte
        """
        pass
    
    @abstractmethod
    def schedule_discovery(self, discovery_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Planifie une découverte réseau.
        
        Args:
            discovery_config: Configuration de la découverte
            
        Returns:
            Informations sur la tâche planifiée
        """
        pass


class NetworkMonitoringUseCases(ABC):
    """
    Interface pour les cas d'utilisation liés à la surveillance réseau.
    
    Cette interface définit le contrat que doivent respecter
    les services applicatifs qui gèrent la surveillance réseau.
    """
    
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
    def acknowledge_alert(self, alert_id: int, comment: Optional[str] = None) -> Dict[str, Any]:
        """
        Acquitte une alerte.
        
        Args:
            alert_id: ID de l'alerte
            comment: Commentaire (optionnel)
            
        Returns:
            Alerte acquittée
        """
        pass
    
    @abstractmethod
    def create_alert_rule(self, rule_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crée une règle d'alerte.
        
        Args:
            rule_data: Données de la règle
            
        Returns:
            Règle créée
        """
        pass


class NetworkConfigurationUseCases(ABC):
    """
    Interface pour les cas d'utilisation liés à la configuration réseau.
    
    Cette interface définit le contrat que doivent respecter
    les services applicatifs qui gèrent la configuration réseau.
    """
    
    @abstractmethod
    def get_device_configuration(self, device_id: int) -> Dict[str, Any]:
        """
        Récupère la configuration actuelle d'un équipement.
        
        Args:
            device_id: ID de l'équipement
            
        Returns:
            Configuration de l'équipement
        """
        pass
    
    @abstractmethod
    def get_configuration_history(self, device_id: int, limit: int = 10) -> List[Dict[str, Any]]:
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
    def apply_configuration(self, device_id: int, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Applique une configuration à un équipement.
        
        Args:
            device_id: ID de l'équipement
            config_data: Données de configuration
            
        Returns:
            Résultat de l'opération
        """
        pass
    
    @abstractmethod
    def validate_configuration(self, device_id: int, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Valide une configuration pour un équipement.
        
        Args:
            device_id: ID de l'équipement
            config_data: Données de configuration
            
        Returns:
            Résultat de la validation
        """
        pass
    
    @abstractmethod
    def rollback_configuration(self, device_id: int, version_id: int) -> Dict[str, Any]:
        """
        Restaure une version précédente de la configuration d'un équipement.
        
        Args:
            device_id: ID de l'équipement
            version_id: ID de la version de configuration
            
        Returns:
            Résultat de l'opération
        """
        pass
    
    @abstractmethod
    def get_configuration_templates(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Récupère les modèles de configuration correspondant aux filtres.
        
        Args:
            filters: Filtres à appliquer (optionnel)
            
        Returns:
            Liste des modèles
        """
        pass
    
    @abstractmethod
    def render_configuration_template(self, template_id: int, variables: Dict[str, Any]) -> Dict[str, Any]:
        """
        Génère une configuration à partir d'un modèle.
        
        Args:
            template_id: ID du modèle
            variables: Variables à injecter
            
        Returns:
            Configuration générée
        """
        pass


class NetworkComplianceUseCases(ABC):
    """
    Interface pour les cas d'utilisation liés à la conformité réseau.
    
    Cette interface définit le contrat que doivent respecter
    les services applicatifs qui gèrent la conformité réseau.
    """
    
    @abstractmethod
    def check_device_compliance(self, device_id: int, policy_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Vérifie la conformité d'un équipement par rapport à une politique.
        
        Args:
            device_id: ID de l'équipement
            policy_id: ID de la politique (optionnel)
            
        Returns:
            Résultat de la vérification
        """
        pass
    
    @abstractmethod
    def get_compliance_policies(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Récupère les politiques de conformité correspondant aux filtres.
        
        Args:
            filters: Filtres à appliquer (optionnel)
            
        Returns:
            Liste des politiques
        """
        pass
    
    @abstractmethod
    def create_compliance_policy(self, policy_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crée une politique de conformité.
        
        Args:
            policy_data: Données de la politique
            
        Returns:
            Politique créée
        """
        pass
    
    @abstractmethod
    def update_compliance_policy(self, policy_id: int, policy_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Met à jour une politique de conformité.
        
        Args:
            policy_id: ID de la politique
            policy_data: Nouvelles données
            
        Returns:
            Politique mise à jour
        """
        pass
    
    @abstractmethod
    def get_compliance_report(self, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Génère un rapport de conformité.
        
        Args:
            filters: Filtres à appliquer (optionnel)
            
        Returns:
            Rapport de conformité
        """
        pass


class NetworkTopologyUseCases(ABC):
    """
    Interface pour les cas d'utilisation liés à la topologie réseau.
    
    Cette interface définit le contrat que doivent respecter
    les services applicatifs qui gèrent la topologie réseau.
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
    def get_path_between_devices(self, source_id: int, target_id: int) -> List[Dict[str, Any]]:
        """
        Calcule le chemin entre deux équipements.
        
        Args:
            source_id: ID de l'équipement source
            target_id: ID de l'équipement cible
            
        Returns:
            Liste des équipements et interfaces sur le chemin
        """
        pass
    
    @abstractmethod
    def get_device_neighbors(self, device_id: int) -> List[Dict[str, Any]]:
        """
        Récupère les voisins d'un équipement.
        
        Args:
            device_id: ID de l'équipement
            
        Returns:
            Liste des voisins
        """
        pass
    
    @abstractmethod
    def update_topology_layout(self, layout_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Met à jour la disposition de la topologie.
        
        Args:
            layout_data: Données de disposition
            
        Returns:
            Disposition mise à jour
        """
        pass


class NetworkDiagnosticUseCases(ABC):
    """
    Interface pour les cas d'utilisation liés au diagnostic réseau.
    
    Cette interface définit le contrat que doivent respecter
    les services applicatifs qui gèrent le diagnostic réseau.
    """
    
    @abstractmethod
    def ping_device(self, device_id: int, count: int = 4) -> Dict[str, Any]:
        """
        Envoie des requêtes ICMP à un équipement.
        
        Args:
            device_id: ID de l'équipement
            count: Nombre de paquets à envoyer
            
        Returns:
            Résultat du ping
        """
        pass
    
    @abstractmethod
    def traceroute_device(self, device_id: int, max_hops: int = 30) -> List[Dict[str, Any]]:
        """
        Trace la route vers un équipement.
        
        Args:
            device_id: ID de l'équipement
            max_hops: Nombre maximum de sauts
            
        Returns:
            Résultat du traceroute
        """
        pass
    
    @abstractmethod
    def scan_device_ports(self, device_id: int, ports: List[int]) -> Dict[int, str]:
        """
        Scanne les ports d'un équipement.
        
        Args:
            device_id: ID de l'équipement
            ports: Liste des ports à scanner
            
        Returns:
            État des ports
        """
        pass
    
    @abstractmethod
    def execute_command(self, device_id: int, command: str) -> Dict[str, Any]:
        """
        Exécute une commande sur un équipement.
        
        Args:
            device_id: ID de l'équipement
            command: Commande à exécuter
            
        Returns:
            Résultat de la commande
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