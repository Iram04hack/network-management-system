"""
Service d'application pour la découverte réseau.

Ce module contient le service d'application qui implémente
les cas d'utilisation liés à la découverte réseau.
"""

from typing import Dict, Any, List, Optional, Union
from ...domain.exceptions import ResourceNotFoundException, ValidationException
from ...domain.interfaces import NetworkDiscoveryPort
from ..ports.input_ports import NetworkDiscoveryUseCases
from ..ports.output_ports import DevicePersistencePort, InterfacePersistencePort, ConnectionPersistencePort, TopologyPersistencePort


class DiscoveryService(NetworkDiscoveryUseCases):
    """
    Service d'application pour la découverte réseau.
    
    Cette classe implémente les cas d'utilisation liés à la découverte réseau
    en utilisant les ports de sortie pour interagir avec les adaptateurs secondaires.
    """
    
    def __init__(
        self,
        discovery_port: NetworkDiscoveryPort,
        device_repository: DevicePersistencePort,
        interface_repository: InterfacePersistencePort,
        connection_repository: ConnectionPersistencePort,
        topology_repository: TopologyPersistencePort
    ):
        """
        Initialise le service avec les dépendances nécessaires.
        
        Args:
            discovery_port: Port pour la découverte réseau
            device_repository: Repository pour les équipements réseau
            interface_repository: Repository pour les interfaces réseau
            connection_repository: Repository pour les connexions réseau
            topology_repository: Repository pour les topologies réseau
        """
        self.discovery_port = discovery_port
        self.device_repository = device_repository
        self.interface_repository = interface_repository
        self.connection_repository = connection_repository
        self.topology_repository = topology_repository
    
    def discover_device(self, ip_address: str, credentials: Dict[str, Any]) -> Dict[str, Any]:
        """
        Découvre un équipement réseau et l'enregistre dans le système.
        
        Args:
            ip_address: Adresse IP de l'équipement
            credentials: Informations d'authentification
            
        Returns:
            Informations sur l'équipement découvert
            
        Raises:
            ValidationException: Si les données sont invalides
        """
        # Valide l'adresse IP
        self._validate_ip_address(ip_address)
        
        # Découvre l'équipement
        device_info = self.discovery_port.discover_device(ip_address)
        
        # Vérifie si l'équipement existe déjà
        try:
            existing_device = self.device_repository.get_device_by_ip(ip_address)
            # Met à jour l'équipement existant
            device_id = existing_device["id"]
            device = self.device_repository.update_device(device_id, device_info)
        except ResourceNotFoundException:
            # Crée un nouvel équipement
            device = self.device_repository.create_device(device_info)
        
        # Traite les interfaces découvertes
        if "interfaces" in device_info:
            self._process_interfaces(device["id"], device_info["interfaces"])
        
        return device
    
    def discover_subnet(self, subnet: str, credentials: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Découvre les équipements d'un sous-réseau et les enregistre dans le système.
        
        Args:
            subnet: Sous-réseau CIDR (e.g. "192.168.1.0/24")
            credentials: Informations d'authentification
            
        Returns:
            Liste des équipements découverts
            
        Raises:
            ValidationException: Si les données sont invalides
        """
        # Valide le sous-réseau
        self._validate_subnet(subnet)
        
        # Découvre les équipements
        devices_info = self.discovery_port.discover_subnet(subnet)
        
        # Traite les équipements découverts
        devices = []
        for device_info in devices_info:
            try:
                # Récupère l'adresse IP
                ip_address = device_info.get("ip_address")
                if not ip_address:
                    continue
                
                # Vérifie si l'équipement existe déjà
                try:
                    existing_device = self.device_repository.get_device_by_ip(ip_address)
                    # Met à jour l'équipement existant
                    device_id = existing_device["id"]
                    device = self.device_repository.update_device(device_id, device_info)
                except ResourceNotFoundException:
                    # Crée un nouvel équipement
                    device = self.device_repository.create_device(device_info)
                
                # Traite les interfaces découvertes
                if "interfaces" in device_info:
                    self._process_interfaces(device["id"], device_info["interfaces"])
                
                devices.append(device)
            except Exception as e:
                # Continue avec l'équipement suivant en cas d'erreur
                continue
        
        return devices
    
    def discover_topology(self, seed_devices: List[str], credentials: Dict[str, Any]) -> Dict[str, Any]:
        """
        Découvre la topologie réseau à partir d'équipements de départ.
        
        Args:
            seed_devices: Liste d'adresses IP des équipements de départ
            credentials: Informations d'authentification
            
        Returns:
            Topologie découverte
            
        Raises:
            ValidationException: Si les données sont invalides
        """
        # Valide les adresses IP
        for ip_address in seed_devices:
            self._validate_ip_address(ip_address)
        
        # Découvre la topologie
        topology_info = self.discovery_port.discover_topology(seed_devices)
        
        # Traite les équipements découverts
        devices = {}
        for device_info in topology_info.get("devices", []):
            try:
                # Récupère l'adresse IP
                ip_address = device_info.get("ip_address")
                if not ip_address:
                    continue
                
                # Vérifie si l'équipement existe déjà
                try:
                    existing_device = self.device_repository.get_device_by_ip(ip_address)
                    # Met à jour l'équipement existant
                    device_id = existing_device["id"]
                    device = self.device_repository.update_device(device_id, device_info)
                except ResourceNotFoundException:
                    # Crée un nouvel équipement
                    device = self.device_repository.create_device(device_info)
                
                # Traite les interfaces découvertes
                if "interfaces" in device_info:
                    self._process_interfaces(device["id"], device_info["interfaces"])
                
                devices[ip_address] = device
            except Exception as e:
                # Continue avec l'équipement suivant en cas d'erreur
                continue
        
        # Traite les connexions découvertes
        connections = []
        for connection_info in topology_info.get("connections", []):
            try:
                # Récupère les informations de connexion
                source_ip = connection_info.get("source_ip")
                source_interface = connection_info.get("source_interface")
                target_ip = connection_info.get("target_ip")
                target_interface = connection_info.get("target_interface")
                
                if not (source_ip and source_interface and target_ip and target_interface):
                    continue
                
                # Récupère les équipements
                source_device = devices.get(source_ip)
                target_device = devices.get(target_ip)
                
                if not (source_device and target_device):
                    continue
                
                # Récupère les interfaces
                try:
                    source_if = self.interface_repository.get_interface_by_name_and_device(
                        source_device["id"], source_interface
                    )
                except ResourceNotFoundException:
                    # Crée l'interface si elle n'existe pas
                    source_if = self.interface_repository.create_interface({
                        "device_id": source_device["id"],
                        "name": source_interface,
                        "status": "up"
                    })
                
                try:
                    target_if = self.interface_repository.get_interface_by_name_and_device(
                        target_device["id"], target_interface
                    )
                except ResourceNotFoundException:
                    # Crée l'interface si elle n'existe pas
                    target_if = self.interface_repository.create_interface({
                        "device_id": target_device["id"],
                        "name": target_interface,
                        "status": "up"
                    })
                
                # Crée la connexion
                connection = self.connection_repository.create_connection({
                    "source_device_id": source_device["id"],
                    "source_interface_id": source_if["id"],
                    "target_device_id": target_device["id"],
                    "target_interface_id": target_if["id"],
                    "connection_type": connection_info.get("type", "ethernet"),
                    "status": "up"
                })
                
                connections.append(connection)
            except Exception as e:
                # Continue avec la connexion suivante en cas d'erreur
                continue
        
        # Enregistre la topologie
        topology = {
            "name": topology_info.get("name", "Discovered Topology"),
            "description": topology_info.get("description", "Automatically discovered topology"),
            "devices": list(devices.values()),
            "connections": connections
        }
        
        saved_topology = self.topology_repository.save_topology(topology)
        
        return saved_topology
    
    def schedule_discovery(self, discovery_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Planifie une découverte réseau.
        
        Args:
            discovery_config: Configuration de la découverte
            
        Returns:
            Informations sur la tâche planifiée
            
        Raises:
            ValidationException: Si les données sont invalides
        """
        # Valide la configuration
        self._validate_discovery_config(discovery_config)
        
        # Ici, on pourrait utiliser un système de tâches comme Celery
        # pour planifier la découverte réseau
        # Pour l'instant, on simule la planification
        
        task_info = {
            "id": 1,  # Simulé
            "type": discovery_config.get("type", "subnet"),
            "target": discovery_config.get("target", ""),
            "schedule": discovery_config.get("schedule", {}),
            "status": "scheduled",
            "created_at": "2023-01-01T00:00:00Z"  # Simulé
        }
        
        return task_info
    
    def _process_interfaces(self, device_id: int, interfaces_info: List[Dict[str, Any]]) -> None:
        """
        Traite les interfaces découvertes pour un équipement.
        
        Args:
            device_id: ID de l'équipement
            interfaces_info: Informations sur les interfaces
        """
        for interface_info in interfaces_info:
            try:
                # Récupère le nom de l'interface
                name = interface_info.get("name")
                if not name:
                    continue
                
                # Vérifie si l'interface existe déjà
                try:
                    existing_interface = self.interface_repository.get_interface_by_name_and_device(
                        device_id, name
                    )
                    # Met à jour l'interface existante
                    interface_id = existing_interface["id"]
                    interface_info["device_id"] = device_id
                    self.interface_repository.update_interface(interface_id, interface_info)
                except ResourceNotFoundException:
                    # Crée une nouvelle interface
                    interface_info["device_id"] = device_id
                    self.interface_repository.create_interface(interface_info)
            except Exception as e:
                # Continue avec l'interface suivante en cas d'erreur
                continue
    
    def _validate_ip_address(self, ip_address: str) -> None:
        """
        Valide une adresse IP.
        
        Args:
            ip_address: Adresse IP à valider
            
        Raises:
            ValidationException: Si l'adresse IP est invalide
        """
        parts = ip_address.split(".")
        if len(parts) != 4:
            raise ValidationException(f"Adresse IP invalide: {ip_address}")
        
        try:
            if not all(0 <= int(part) <= 255 for part in parts):
                raise ValidationException(f"Adresse IP invalide: {ip_address}")
        except ValueError:
            raise ValidationException(f"Adresse IP invalide: {ip_address}")
    
    def _validate_subnet(self, subnet: str) -> None:
        """
        Valide un sous-réseau CIDR.
        
        Args:
            subnet: Sous-réseau à valider (e.g. "192.168.1.0/24")
            
        Raises:
            ValidationException: Si le sous-réseau est invalide
        """
        try:
            ip, prefix = subnet.split("/")
            self._validate_ip_address(ip)
            
            prefix_int = int(prefix)
            if not (0 <= prefix_int <= 32):
                raise ValidationException(f"Préfixe de sous-réseau invalide: {prefix}")
        except ValueError:
            raise ValidationException(f"Format de sous-réseau invalide: {subnet}")
    
    def _validate_discovery_config(self, config: Dict[str, Any]) -> None:
        """
        Valide une configuration de découverte.
        
        Args:
            config: Configuration à valider
            
        Raises:
            ValidationException: Si la configuration est invalide
        """
        errors = {}
        
        # Validation du type de découverte
        discovery_type = config.get("type")
        if not discovery_type:
            errors["type"] = "Le type de découverte est requis"
        elif discovery_type not in ["device", "subnet", "topology"]:
            errors["type"] = f"Type de découverte invalide: {discovery_type}"
        
        # Validation de la cible
        target = config.get("target")
        if not target:
            errors["target"] = "La cible de découverte est requise"
        elif discovery_type == "device":
            try:
                self._validate_ip_address(target)
            except ValidationException as e:
                errors["target"] = str(e)
        elif discovery_type == "subnet":
            try:
                self._validate_subnet(target)
            except ValidationException as e:
                errors["target"] = str(e)
        elif discovery_type == "topology":
            if not isinstance(target, list):
                errors["target"] = "La cible doit être une liste d'adresses IP"
            else:
                for ip in target:
                    try:
                        self._validate_ip_address(ip)
                    except ValidationException:
                        errors["target"] = f"Adresse IP invalide dans la liste: {ip}"
                        break
        
        # Validation des informations d'authentification
        credentials = config.get("credentials")
        if not credentials:
            errors["credentials"] = "Les informations d'authentification sont requises"
        
        # Si des erreurs sont détectées, lève une exception
        if errors:
            raise ValidationException("Configuration de découverte invalide", errors) 