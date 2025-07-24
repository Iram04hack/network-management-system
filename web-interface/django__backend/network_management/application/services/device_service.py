"""
Service d'application pour la gestion des équipements réseau.

Ce module contient le service d'application qui implémente
les cas d'utilisation liés aux équipements réseau.
"""

from typing import Dict, Any, List, Optional, Union
from ...domain.exceptions import ResourceNotFoundException, ValidationException
from ..ports.input_ports import NetworkDeviceUseCases
from ..ports.output_ports import DevicePersistencePort, InterfacePersistencePort


class DeviceService(NetworkDeviceUseCases):
    """
    Service d'application pour la gestion des équipements réseau.
    
    Cette classe implémente les cas d'utilisation liés aux équipements réseau
    en utilisant les ports de sortie pour interagir avec les adaptateurs secondaires.
    """
    
    def __init__(
        self,
        device_repository: DevicePersistencePort,
        interface_repository: InterfacePersistencePort
    ):
        """
        Initialise le service avec les dépendances nécessaires.
        
        Args:
            device_repository: Repository pour les équipements réseau
            interface_repository: Repository pour les interfaces réseau
        """
        self.device_repository = device_repository
        self.interface_repository = interface_repository
    
    def get_device(self, device_id: int) -> Dict[str, Any]:
        """
        Récupère un équipement réseau par son ID.
        
        Args:
            device_id: ID de l'équipement
            
        Returns:
            Informations sur l'équipement
            
        Raises:
            ResourceNotFoundException: Si l'équipement n'existe pas
        """
        return self.device_repository.get_device_by_id(device_id)
    
    def get_all_devices(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Récupère tous les équipements réseau correspondant aux filtres.
        
        Args:
            filters: Filtres à appliquer (optionnel)
            
        Returns:
            Liste des équipements
        """
        return self.device_repository.get_all_devices(filters)
    
    def create_device(self, device_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crée un nouvel équipement réseau.
        
        Args:
            device_data: Données de l'équipement
            
        Returns:
            Équipement créé
            
        Raises:
            ValidationException: Si les données sont invalides
        """
        self._validate_device_data(device_data)
        return self.device_repository.create_device(device_data)
    
    def update_device(self, device_id: int, device_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Met à jour un équipement réseau.
        
        Args:
            device_id: ID de l'équipement
            device_data: Nouvelles données
            
        Returns:
            Équipement mis à jour
            
        Raises:
            ResourceNotFoundException: Si l'équipement n'existe pas
            ValidationException: Si les données sont invalides
        """
        # Vérifie que l'équipement existe
        self.get_device(device_id)
        
        # Valide les données
        self._validate_device_data(device_data, is_update=True)
        
        return self.device_repository.update_device(device_id, device_data)
    
    def delete_device(self, device_id: int) -> bool:
        """
        Supprime un équipement réseau.
        
        Args:
            device_id: ID de l'équipement
            
        Returns:
            True si la suppression a réussi
            
        Raises:
            ResourceNotFoundException: Si l'équipement n'existe pas
        """
        # Vérifie que l'équipement existe
        self.get_device(device_id)
        
        return self.device_repository.delete_device(device_id)
    
    def get_device_interfaces(self, device_id: int) -> List[Dict[str, Any]]:
        """
        Récupère les interfaces d'un équipement réseau.
        
        Args:
            device_id: ID de l'équipement
            
        Returns:
            Liste des interfaces
            
        Raises:
            ResourceNotFoundException: Si l'équipement n'existe pas
        """
        # Vérifie que l'équipement existe
        self.get_device(device_id)
        
        return self.interface_repository.get_interfaces_by_device(device_id)
    
    def get_device_status(self, device_id: int) -> Dict[str, Any]:
        """
        Récupère le statut d'un équipement réseau.
        
        Args:
            device_id: ID de l'équipement
            
        Returns:
            Statut de l'équipement
            
        Raises:
            ResourceNotFoundException: Si l'équipement n'existe pas
        """
        # Récupère l'équipement
        device = self.get_device(device_id)
        
        # Récupère les interfaces
        interfaces = self.get_device_interfaces(device_id)
        
        # Calcule le statut
        status = {
            "id": device_id,
            "name": device.get("name", ""),
            "status": device.get("status", "unknown"),
            "last_seen": device.get("last_seen"),
            "uptime": device.get("uptime"),
            "cpu_usage": device.get("cpu_usage"),
            "memory_usage": device.get("memory_usage"),
            "interfaces_count": len(interfaces),
            "interfaces_up": sum(1 for interface in interfaces if interface.get("status") == "up"),
            "interfaces_down": sum(1 for interface in interfaces if interface.get("status") == "down")
        }
        
        return status
    
    def _validate_device_data(self, device_data: Dict[str, Any], is_update: bool = False) -> None:
        """
        Valide les données d'un équipement.
        
        Args:
            device_data: Données à valider
            is_update: True si c'est une mise à jour, False si c'est une création
            
        Raises:
            ValidationException: Si les données sont invalides
        """
        errors = {}
        
        # Validation des champs requis (seulement pour la création)
        if not is_update:
            required_fields = ["name", "ip_address", "device_type"]
            for field in required_fields:
                if field not in device_data or not device_data[field]:
                    errors[field] = f"Le champ {field} est requis"
        
        # Validation de l'adresse IP
        if "ip_address" in device_data:
            ip = device_data["ip_address"]
            if not self._is_valid_ip(ip):
                errors["ip_address"] = f"L'adresse IP {ip} est invalide"
        
        # Si des erreurs sont détectées, lève une exception
        if errors:
            raise ValidationException("Données d'équipement invalides", errors)
    
    def _is_valid_ip(self, ip: str) -> bool:
        """
        Vérifie si une adresse IP est valide.
        
        Args:
            ip: Adresse IP à vérifier
            
        Returns:
            True si l'adresse IP est valide
        """
        parts = ip.split(".")
        if len(parts) != 4:
            return False
        
        try:
            return all(0 <= int(part) <= 255 for part in parts)
        except ValueError:
            return False 