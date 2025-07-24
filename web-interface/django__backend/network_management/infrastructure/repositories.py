"""
Implémentations des repositories pour le module network_management.

Ce module contient les implémentations concrètes des interfaces
de repositories définies dans le domaine, utilisant Django ORM.
"""

from typing import List, Dict, Any, Optional
from .models import NetworkDevice, NetworkInterface
from ..domain.interfaces import NetworkDeviceRepository, NetworkInterfaceRepository


class DjangoNetworkDeviceRepository(NetworkDeviceRepository):
    """
    Implémentation Django du repository pour les équipements réseau.
    
    Cette classe implémente l'interface NetworkDeviceRepository en utilisant
    l'ORM Django pour persister les données dans une base de données relationnelle.
    """
    
    def find_all(self) -> List[Dict[str, Any]]:
        """
        Récupère tous les équipements réseau.
        
        Returns:
            List[Dict[str, Any]]: Liste des équipements réseau.
        """
        devices = NetworkDevice.objects.all()
        return [self._to_dict(device) for device in devices]
    
    def find_by_id(self, device_id: int) -> Optional[Dict[str, Any]]:
        """
        Récupère un équipement réseau par son identifiant.
        
        Args:
            device_id (int): Identifiant de l'équipement réseau.
            
        Returns:
            Optional[Dict[str, Any]]: L'équipement réseau, ou None s'il n'existe pas.
        """
        try:
            device = NetworkDevice.objects.get(pk=device_id)
            return self._to_dict(device)
        except NetworkDevice.DoesNotExist:
            return None
    
    def save(self, device_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enregistre un équipement réseau.
        
        Args:
            device_data (Dict[str, Any]): Données de l'équipement réseau.
            
        Returns:
            Dict[str, Any]: L'équipement réseau enregistré.
        """
        device_id = device_data.get('id')
        
        if device_id:
            # Mise à jour
            device = NetworkDevice.objects.get(pk=device_id)
            for key, value in device_data.items():
                if key != 'id' and hasattr(device, key):
                    setattr(device, key, value)
        else:
            # Création
            device = NetworkDevice(**{k: v for k, v in device_data.items() if k != 'id'})
        
        device.save()
        return self._to_dict(device)
    
    def delete(self, device_id: int) -> bool:
        """
        Supprime un équipement réseau.
        
        Args:
            device_id (int): Identifiant de l'équipement réseau.
            
        Returns:
            bool: True si l'équipement a été supprimé, False sinon.
        """
        try:
            device = NetworkDevice.objects.get(pk=device_id)
            device.delete()
            return True
        except NetworkDevice.DoesNotExist:
            return False
    
    def _to_dict(self, device: NetworkDevice) -> Dict[str, Any]:
        """
        Convertit un modèle NetworkDevice en dictionnaire.
        
        Args:
            device (NetworkDevice): Modèle d'équipement réseau.
            
        Returns:
            Dict[str, Any]: Dictionnaire représentant l'équipement réseau.
        """
        return {
            'id': device.id,
            'name': device.name,
            'hostname': getattr(device, 'hostname', ''),
            'ip_address': device.ip_address,
            'mac_address': getattr(device, 'mac_address', ''),
            'device_type': device.device_type,
            'manufacturer': getattr(device, 'manufacturer', ''),
            'vendor': device.vendor,
            'model': getattr(device, 'model', ''),
            'os': getattr(device, 'os', ''),
            'os_version': getattr(device, 'os_version', ''),
            'location': getattr(device, 'location', ''),
            'description': getattr(device, 'description', ''),
            'is_active': getattr(device, 'is_active', True),
            'is_virtual': getattr(device, 'is_virtual', False),
            'management_interface': getattr(device, 'management_interface', ''),
            'metadata': getattr(device, 'metadata', None),
            'created_at': device.created_at,
            'updated_at': device.updated_at,
        }


class DjangoNetworkInterfaceRepository(NetworkInterfaceRepository):
    """
    Implémentation Django du repository pour les interfaces réseau.
    
    Cette classe implémente l'interface NetworkInterfaceRepository en utilisant
    l'ORM Django pour persister les données dans une base de données relationnelle.
    """
    
    def find_all(self) -> List[Dict[str, Any]]:
        """
        Récupère toutes les interfaces réseau.
        
        Returns:
            List[Dict[str, Any]]: Liste des interfaces réseau.
        """
        interfaces = NetworkInterface.objects.all()
        return [self._to_dict(interface) for interface in interfaces]
    
    def find_by_id(self, interface_id: int) -> Optional[Dict[str, Any]]:
        """
        Récupère une interface réseau par son identifiant.
        
        Args:
            interface_id (int): Identifiant de l'interface réseau.
            
        Returns:
            Optional[Dict[str, Any]]: L'interface réseau, ou None si elle n'existe pas.
        """
        try:
            interface = NetworkInterface.objects.get(pk=interface_id)
            return self._to_dict(interface)
        except NetworkInterface.DoesNotExist:
            return None
    
    def find_by_device(self, device_id: int) -> List[Dict[str, Any]]:
        """
        Récupère toutes les interfaces d'un équipement réseau.
        
        Args:
            device_id (int): Identifiant de l'équipement réseau.
            
        Returns:
            List[Dict[str, Any]]: Liste des interfaces réseau.
        """
        interfaces = NetworkInterface.objects.filter(device_id=device_id)
        return [self._to_dict(interface) for interface in interfaces]
    
    def save(self, interface_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enregistre une interface réseau.
        
        Args:
            interface_data (Dict[str, Any]): Données de l'interface réseau.
            
        Returns:
            Dict[str, Any]: L'interface réseau enregistrée.
        """
        interface_id = interface_data.get('id')
        
        if interface_id:
            # Mise à jour
            interface = NetworkInterface.objects.get(pk=interface_id)
            for key, value in interface_data.items():
                if key != 'id' and hasattr(interface, key):
                    setattr(interface, key, value)
        else:
            # Création
            interface = NetworkInterface(**{k: v for k, v in interface_data.items() if k != 'id'})
        
        interface.save()
        return self._to_dict(interface)
    
    def delete(self, interface_id: int) -> bool:
        """
        Supprime une interface réseau.
        
        Args:
            interface_id (int): Identifiant de l'interface réseau.
            
        Returns:
            bool: True si l'interface a été supprimée, False sinon.
        """
        try:
            interface = NetworkInterface.objects.get(pk=interface_id)
            interface.delete()
            return True
        except NetworkInterface.DoesNotExist:
            return False
    
    def _to_dict(self, interface: NetworkInterface) -> Dict[str, Any]:
        """
        Convertit un modèle NetworkInterface en dictionnaire.
        
        Args:
            interface (NetworkInterface): Modèle d'interface réseau.
            
        Returns:
            Dict[str, Any]: Dictionnaire représentant l'interface réseau.
        """
        return {
            'id': interface.id,
            'device_id': interface.device_id,
            'name': interface.name,
            'description': interface.description,
            'mac_address': interface.mac_address,
            'ip_address': interface.ip_address,
            'subnet_mask': interface.subnet_mask,
            'interface_type': interface.interface_type,
            'speed': interface.speed,
            'mtu': interface.mtu,
            'status': interface.status,
            'extra_data': interface.extra_data,
            'created_at': interface.created_at,
            'updated_at': interface.updated_at,
        } 