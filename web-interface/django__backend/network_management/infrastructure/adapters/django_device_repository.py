"""
Adaptateur de persistance Django pour les équipements réseau.

Ce module contient l'implémentation de l'interface DevicePersistencePort
utilisant Django ORM pour persister les équipements réseau.
"""

from typing import Dict, Any, List, Optional
from django.db import transaction
from django.core.exceptions import ObjectDoesNotExist

from ...application.ports.output_ports import DevicePersistencePort
from ...domain.exceptions import ResourceNotFoundException
from ..models import NetworkDevice


class DjangoDeviceRepository(DevicePersistencePort):
    """
    Adaptateur de persistance Django pour les équipements réseau.
    
    Cette classe implémente l'interface DevicePersistencePort en utilisant
    Django ORM pour persister les équipements réseau dans une base de données.
    """
    
    def get_device_by_id(self, device_id: int) -> Dict[str, Any]:
        """
        Récupère un équipement par son ID.
        
        Args:
            device_id: ID de l'équipement
            
        Returns:
            Informations sur l'équipement
            
        Raises:
            ResourceNotFoundException: Si l'équipement n'existe pas
        """
        try:
            device = NetworkDevice.objects.get(id=device_id)
            return self._device_to_dict(device)
        except ObjectDoesNotExist:
            raise ResourceNotFoundException("NetworkDevice", str(device_id))
    
    def get_device_by_ip(self, ip_address: str) -> Dict[str, Any]:
        """
        Récupère un équipement par son adresse IP.
        
        Args:
            ip_address: Adresse IP de l'équipement
            
        Returns:
            Informations sur l'équipement
            
        Raises:
            ResourceNotFoundException: Si l'équipement n'existe pas
        """
        try:
            device = NetworkDevice.objects.get(ip_address=ip_address)
            return self._device_to_dict(device)
        except ObjectDoesNotExist:
            raise ResourceNotFoundException("NetworkDevice", ip_address)
    
    def get_all_devices(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Récupère tous les équipements correspondant aux filtres.
        
        Args:
            filters: Filtres à appliquer (optionnel)
            
        Returns:
            Liste des équipements
        """
        queryset = NetworkDevice.objects.all()
        
        if filters:
            # Applique les filtres
            if "name" in filters:
                queryset = queryset.filter(name__icontains=filters["name"])
            if "ip_address" in filters:
                queryset = queryset.filter(ip_address__icontains=filters["ip_address"])
            if "device_type" in filters:
                queryset = queryset.filter(device_type=filters["device_type"])
            if "vendor" in filters:
                queryset = queryset.filter(vendor=filters["vendor"])
            if "status" in filters:
                queryset = queryset.filter(status=filters["status"])
        
        return [self._device_to_dict(device) for device in queryset]
    
    def create_device(self, device_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crée un nouvel équipement.
        
        Args:
            device_data: Données de l'équipement
            
        Returns:
            Équipement créé
        """
        with transaction.atomic():
            device = NetworkDevice(
                name=device_data.get("name", ""),
                ip_address=device_data.get("ip_address", ""),
                device_type=device_data.get("device_type", "unknown"),
                vendor=device_data.get("vendor", "unknown"),
                model=device_data.get("model", ""),
                os_version=device_data.get("os_version", ""),
                # Champs adaptés à la structure DB réelle
                location=device_data.get("location", ""),
                description=device_data.get("description", ""),
                # Nouveaux champs de la structure DB
                hostname=device_data.get("hostname", ""),
                mac_address=device_data.get("mac_address", ""),
                manufacturer=device_data.get("manufacturer", ""),
                os=device_data.get("os", ""),
                is_active=device_data.get("is_active", True),
                is_virtual=device_data.get("is_virtual", False),
                management_interface=device_data.get("management_interface", ""),
                credentials=device_data.get("credentials"),
                snmp_community=device_data.get("snmp_community", ""),
                metadata=device_data.get("metadata"),
                last_discovered=device_data.get("last_discovered"),
                discovery_method=device_data.get("discovery_method", ""),
                node_id=device_data.get("node_id", ""),
                last_sync=device_data.get("last_sync")
            )
            
            # Les champs supplémentaires peuvent être stockés dans metadata
            # (pas de champ extra_data dans la structure DB actuelle)
            
            device.save()
            
            return self._device_to_dict(device)
    
    def update_device(self, device_id: int, device_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Met à jour un équipement.
        
        Args:
            device_id: ID de l'équipement
            device_data: Nouvelles données
            
        Returns:
            Équipement mis à jour
            
        Raises:
            ResourceNotFoundException: Si l'équipement n'existe pas
        """
        try:
            with transaction.atomic():
                device = NetworkDevice.objects.get(id=device_id)
                
                # Met à jour les champs standard
                if "name" in device_data:
                    device.name = device_data["name"]
                if "ip_address" in device_data:
                    device.ip_address = device_data["ip_address"]
                if "device_type" in device_data:
                    device.device_type = device_data["device_type"]
                if "vendor" in device_data:
                    device.vendor = device_data["vendor"]
                if "model" in device_data:
                    device.model = device_data["model"]
                if "os_version" in device_data:
                    device.os_version = device_data["os_version"]
                # Champs adaptés à la structure DB réelle
                if "location" in device_data:
                    device.location = device_data["location"]
                if "description" in device_data:
                    device.description = device_data["description"]
                if "hostname" in device_data:
                    device.hostname = device_data["hostname"]
                if "mac_address" in device_data:
                    device.mac_address = device_data["mac_address"]
                if "manufacturer" in device_data:
                    device.manufacturer = device_data["manufacturer"]
                if "os" in device_data:
                    device.os = device_data["os"]
                if "is_active" in device_data:
                    device.is_active = device_data["is_active"]
                if "is_virtual" in device_data:
                    device.is_virtual = device_data["is_virtual"]
                if "management_interface" in device_data:
                    device.management_interface = device_data["management_interface"]
                if "credentials" in device_data:
                    device.credentials = device_data["credentials"]
                if "snmp_community" in device_data:
                    device.snmp_community = device_data["snmp_community"]
                if "metadata" in device_data:
                    device.metadata = device_data["metadata"]
                
                # Les champs supplémentaires peuvent être stockés dans metadata
                # (pas de champ extra_data dans la structure DB actuelle)
                device.save()
                
                return self._device_to_dict(device)
        except ObjectDoesNotExist:
            raise ResourceNotFoundException("NetworkDevice", str(device_id))
    
    def delete_device(self, device_id: int) -> bool:
        """
        Supprime un équipement.
        
        Args:
            device_id: ID de l'équipement
            
        Returns:
            True si la suppression a réussi
            
        Raises:
            ResourceNotFoundException: Si l'équipement n'existe pas
        """
        try:
            device = NetworkDevice.objects.get(id=device_id)
            device.delete()
            return True
        except ObjectDoesNotExist:
            raise ResourceNotFoundException("NetworkDevice", str(device_id))
    
    def _device_to_dict(self, device: NetworkDevice) -> Dict[str, Any]:
        """
        Convertit un objet NetworkDevice en dictionnaire.
        
        Args:
            device: Objet NetworkDevice
            
        Returns:
            Dictionnaire représentant l'équipement
        """
        result = {
            "id": device.id,
            "name": device.name,
            "hostname": getattr(device, 'hostname', ''),
            "ip_address": device.ip_address,
            "mac_address": getattr(device, 'mac_address', ''),
            "device_type": device.device_type,
            "manufacturer": getattr(device, 'manufacturer', ''),
            "vendor": device.vendor,
            "model": getattr(device, 'model', ''),
            "os": getattr(device, 'os', ''),
            "os_version": getattr(device, 'os_version', ''),
            "location": getattr(device, 'location', ''),
            "description": getattr(device, 'description', ''),
            "is_active": getattr(device, 'is_active', True),
            "is_virtual": getattr(device, 'is_virtual', False),
            "management_interface": getattr(device, 'management_interface', ''),
            "credentials": getattr(device, 'credentials', None),
            "snmp_community": getattr(device, 'snmp_community', ''),
            "metadata": getattr(device, 'metadata', None),
            "last_discovered": getattr(device, 'last_discovered', None),
            "discovery_method": getattr(device, 'discovery_method', ''),
            "node_id": getattr(device, 'node_id', ''),
            "last_sync": getattr(device, 'last_sync', None),
            "created_at": device.created_at,
            "updated_at": device.updated_at
        }

        return result