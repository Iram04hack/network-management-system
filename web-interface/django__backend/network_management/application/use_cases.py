"""
Implémentations des cas d'utilisation pour le module network_management.

Ce module contient les implémentations concrètes des interfaces
de cas d'utilisation définies dans le domaine.
"""

from typing import List, Dict, Any, Optional
from ..domain.interfaces import NetworkDeviceRepository, NetworkInterfaceRepository


class NetworkDeviceUseCasesImpl:
    """
    Implémentation des cas d'utilisation pour les équipements réseau.
    """
    
    def __init__(self, device_repository: NetworkDeviceRepository):
        """
        Initialise les cas d'utilisation pour les équipements réseau.
        
        Args:
            device_repository (NetworkDeviceRepository): Repository pour les équipements réseau.
        """
        self.device_repository = device_repository
    
    def get_all_devices(self) -> List[Dict[str, Any]]:
        """
        Récupère tous les équipements réseau.
        
        Returns:
            List[Dict[str, Any]]: Liste des équipements réseau.
        """
        return self.device_repository.find_all()
    
    def get_device(self, device_id: int) -> Optional[Dict[str, Any]]:
        """
        Récupère un équipement réseau par son identifiant.
        
        Args:
            device_id (int): Identifiant de l'équipement réseau.
            
        Returns:
            Optional[Dict[str, Any]]: L'équipement réseau, ou None s'il n'existe pas.
        """
        return self.device_repository.find_by_id(device_id)
    
    def create_device(self, device_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crée un nouvel équipement réseau.
        
        Args:
            device_data (Dict[str, Any]): Données de l'équipement réseau.
            
        Returns:
            Dict[str, Any]: L'équipement réseau créé.
        """
        # Validation des données
        if not device_data.get('name'):
            raise ValueError("Le nom de l'équipement est obligatoire")
        
        if not device_data.get('ip_address'):
            raise ValueError("L'adresse IP de l'équipement est obligatoire")
        
        return self.device_repository.save(device_data)
    
    def update_device(self, device_id: int, device_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Met à jour un équipement réseau.
        
        Args:
            device_id (int): Identifiant de l'équipement réseau.
            device_data (Dict[str, Any]): Données de l'équipement réseau.
            
        Returns:
            Dict[str, Any]: L'équipement réseau mis à jour.
        """
        # Vérification de l'existence de l'équipement
        existing_device = self.device_repository.find_by_id(device_id)
        if not existing_device:
            raise ValueError(f"Équipement réseau avec ID {device_id} non trouvé")
        
        # Mise à jour des données
        device_data['id'] = device_id
        return self.device_repository.save(device_data)
    
    def delete_device(self, device_id: int) -> bool:
        """
        Supprime un équipement réseau.
        
        Args:
            device_id (int): Identifiant de l'équipement réseau.
            
        Returns:
            bool: True si l'équipement a été supprimé, False sinon.
        """
        return self.device_repository.delete(device_id)


class NetworkInterfaceUseCasesImpl:
    """
    Implémentation des cas d'utilisation pour les interfaces réseau.
    """
    
    def __init__(self, interface_repository: NetworkInterfaceRepository):
        """
        Initialise les cas d'utilisation pour les interfaces réseau.
        
        Args:
            interface_repository (NetworkInterfaceRepository): Repository pour les interfaces réseau.
        """
        self.interface_repository = interface_repository
    
    def get_all_interfaces(self) -> List[Dict[str, Any]]:
        """
        Récupère toutes les interfaces réseau.
        
        Returns:
            List[Dict[str, Any]]: Liste des interfaces réseau.
        """
        return self.interface_repository.find_all()
    
    def get_interface(self, interface_id: int) -> Optional[Dict[str, Any]]:
        """
        Récupère une interface réseau par son identifiant.
        
        Args:
            interface_id (int): Identifiant de l'interface réseau.
            
        Returns:
            Optional[Dict[str, Any]]: L'interface réseau, ou None si elle n'existe pas.
        """
        return self.interface_repository.find_by_id(interface_id)
    
    def get_interfaces_by_device(self, device_id: int) -> List[Dict[str, Any]]:
        """
        Récupère toutes les interfaces d'un équipement réseau.
        
        Args:
            device_id (int): Identifiant de l'équipement réseau.
            
        Returns:
            List[Dict[str, Any]]: Liste des interfaces réseau.
        """
        return self.interface_repository.find_by_device(device_id)
    
    def create_interface(self, interface_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crée une nouvelle interface réseau.
        
        Args:
            interface_data (Dict[str, Any]): Données de l'interface réseau.
            
        Returns:
            Dict[str, Any]: L'interface réseau créée.
        """
        # Validation des données
        if not interface_data.get('name'):
            raise ValueError("Le nom de l'interface est obligatoire")
        
        if not interface_data.get('device_id'):
            raise ValueError("L'ID de l'équipement est obligatoire")
        
        return self.interface_repository.save(interface_data)
    
    def update_interface(self, interface_id: int, interface_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Met à jour une interface réseau.
        
        Args:
            interface_id (int): Identifiant de l'interface réseau.
            interface_data (Dict[str, Any]): Données de l'interface réseau.
            
        Returns:
            Dict[str, Any]: L'interface réseau mise à jour.
        """
        # Vérification de l'existence de l'interface
        existing_interface = self.interface_repository.find_by_id(interface_id)
        if not existing_interface:
            raise ValueError(f"Interface réseau avec ID {interface_id} non trouvée")
        
        # Mise à jour des données
        interface_data['id'] = interface_id
        return self.interface_repository.save(interface_data)
    
    def delete_interface(self, interface_id: int) -> bool:
        """
        Supprime une interface réseau.
        
        Args:
            interface_id (int): Identifiant de l'interface réseau.
            
        Returns:
            bool: True si l'interface a été supprimée, False sinon.
        """
        return self.interface_repository.delete(interface_id) 