"""
Module contenant l'adaptateur pour le repository d'interfaces réseau.
"""

from typing import List, Optional, Dict, Any

from ...domain.interfaces import NetworkInterfaceRepository
from ...domain.entities import NetworkDeviceEntity as DomainDevice, NetworkInterfaceEntity as DomainInterface
from ..repositories.interface_repository import InterfaceRepository
from ..models import NetworkInterface as DjangoInterface, NetworkDevice as DjangoDevice


class DjangoInterfaceRepository(NetworkInterfaceRepository):
    """
    Adaptateur Django pour le repository d'interfaces réseau.

    Cette classe implémente l'interface NetworkInterfaceRepository
    en utilisant le repository Django InterfaceRepository.
    """
    
    def __init__(self):
        """
        Initialise une nouvelle instance de DjangoInterfaceRepository.
        """
        self._repository = InterfaceRepository()
    
    def _to_domain(self, django_interface: DjangoInterface) -> DomainInterface:
        """
        Convertit une interface Django en interface du domaine.
        
        Args:
            django_interface (DjangoInterface): L'interface Django à convertir.
            
        Returns:
            DomainInterface: L'interface du domaine correspondante.
        """
        device = DomainDevice(
            id=django_interface.device.id,
            name=django_interface.device.name,
            ip_address=django_interface.device.ip_address,
            device_type=django_interface.device.device_type,
            vendor=django_interface.device.vendor,
            status=django_interface.device.status
        )
        
        return DomainInterface(
            id=django_interface.id,
            name=django_interface.name,
            device=device,
            mac_address=django_interface.mac_address,
            ip_address=django_interface.ip_address,
            subnet_mask=django_interface.subnet_mask,
            interface_type=django_interface.interface_type,
            speed=django_interface.speed,
            status=django_interface.status,
            description=django_interface.description
        )
    
    def _to_django(self, domain_interface: DomainInterface, django_device: Optional[DjangoDevice] = None) -> Dict[str, Any]:
        """
        Convertit une interface du domaine en dictionnaire pour création/mise à jour Django.
        
        Args:
            domain_interface (DomainInterface): L'interface du domaine à convertir.
            django_device (Optional[DjangoDevice]): L'équipement Django associé, si disponible.
            
        Returns:
            Dict[str, Any]: Un dictionnaire contenant les attributs pour création/mise à jour Django.
        """
        data = {
            'name': domain_interface.name,
            'mac_address': domain_interface.mac_address,
            'ip_address': domain_interface.ip_address,
            'subnet_mask': domain_interface.subnet_mask,
            'interface_type': domain_interface.interface_type,
            'speed': domain_interface.speed,
            'status': domain_interface.status,
            'description': domain_interface.description
        }
        
        if django_device:
            data['device'] = django_device
        
        return data
    
    def get_by_id(self, interface_id: int) -> Optional[DomainInterface]:
        """
        Récupère une interface par son ID.
        
        Args:
            interface_id (int): L'ID de l'interface à récupérer.
            
        Returns:
            Optional[DomainInterface]: L'interface trouvée ou None si aucune interface n'a été trouvée.
        """
        django_interface = self._repository.get_by_id(interface_id)
        if django_interface:
            return self._to_domain(django_interface)
        return None
    
    def get_by_device_id(self, device_id: int) -> List[DomainInterface]:
        """
        Récupère les interfaces d'un équipement par son ID.
        
        Args:
            device_id (int): L'ID de l'équipement dont on veut récupérer les interfaces.
            
        Returns:
            List[DomainInterface]: Une liste contenant les interfaces de l'équipement.
        """
        django_interfaces = self._repository.get_by_device_id(device_id)
        return [self._to_domain(interface) for interface in django_interfaces]
    
    def get_by_name_and_device_id(self, name: str, device_id: int) -> Optional[DomainInterface]:
        """
        Récupère une interface par son nom et l'ID de son équipement.
        
        Args:
            name (str): Le nom de l'interface.
            device_id (int): L'ID de l'équipement auquel appartient l'interface.
            
        Returns:
            Optional[DomainInterface]: L'interface trouvée ou None si aucune interface n'a été trouvée.
        """
        django_interface = self._repository.get_by_name_and_device_id(name, device_id)
        if django_interface:
            return self._to_domain(django_interface)
        return None
    
    def get_all(self, filters: Optional[Dict] = None) -> List[DomainInterface]:
        """
        Récupère toutes les interfaces réseau.
        
        Args:
            filters: Filtres optionnels (non utilisés pour le moment).
            
        Returns:
            List[DomainInterface]: Liste de toutes les interfaces.
        """
        django_interfaces = self._repository.get_all()
        return [self._to_domain(interface) for interface in django_interfaces]
    
    def get_all_by_device(self, device_id: int) -> List[DomainInterface]:
        """
        Récupère toutes les interfaces d'un équipement.
        
        Args:
            device_id (int): L'ID de l'équipement.
            
        Returns:
            List[DomainInterface]: Liste des interfaces de l'équipement.
        """
        return self.get_by_device_id(device_id)
    
    def get_by_name_and_device(self, device_id: int, name: str) -> Optional[DomainInterface]:
        """
        Récupère une interface par nom et équipement.
        
        Args:
            device_id (int): L'ID de l'équipement.
            name (str): Le nom de l'interface.
            
        Returns:
            Optional[DomainInterface]: L'interface trouvée ou None.
        """
        return self.get_by_name_and_device_id(name, device_id)
    
    def create(self, interface: DomainInterface) -> DomainInterface:
        """
        Crée une nouvelle interface.
        
        Args:
            interface (DomainInterface): L'interface à créer.
            
        Returns:
            DomainInterface: L'interface créée avec son ID généré.
        """
        from ..adapters.django_device_repository import DjangoDeviceRepository
        device_repo = DjangoDeviceRepository()
        django_device = device_repo._repository.get_by_id(interface.device.id)
        
        if not django_device:
            raise ValueError(f"Device with id {interface.device.id} not found")
        
        data = self._to_django(interface, django_device)
        django_interface = self._repository.create(**data)
        return self._to_domain(django_interface)
    
    def update(self, interface: DomainInterface) -> DomainInterface:
        """
        Met à jour une interface existante.
        
        Args:
            interface (DomainInterface): L'interface à mettre à jour.
            
        Returns:
            DomainInterface: L'interface mise à jour.
        """
        django_interface = self._repository.get_by_id(interface.id)
        if not django_interface:
            raise ValueError(f"Interface with id {interface.id} not found")
        
        data = self._to_django(interface)
        django_interface = self._repository.update(django_interface, **data)
        return self._to_domain(django_interface)
    
    def delete(self, interface_id: int) -> bool:
        """
        Supprime une interface par son ID.
        
        Args:
            interface_id (int): L'ID de l'interface à supprimer.
            
        Returns:
            bool: True si l'interface a été supprimée, False sinon.
        """
        return self._repository.delete_by_id(interface_id)
    
    def search(self, query: str) -> List[DomainInterface]:
        """
        Recherche des interfaces par nom, adresse MAC, adresse IP ou type.
        
        Args:
            query (str): Le terme de recherche.
            
        Returns:
            List[DomainInterface]: Une liste contenant les interfaces trouvées.
        """
        django_interfaces = self._repository.search(query)
        return [self._to_domain(interface) for interface in django_interfaces]
    
    # Méthodes abstraites de Repository[Dict[str, Any]]
    def get_all(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Récupère toutes les interfaces avec filtres optionnels.
        
        Args:
            filters: Filtres à appliquer (optionnel)
            
        Returns:
            Liste de dictionnaires contenant les informations des interfaces
        """
        django_interfaces = self._repository.get_all()
        result = []
        
        for interface in django_interfaces:
            interface_dict = {
                'id': interface.id,
                'name': interface.name,
                'device_id': interface.device.id,
                'device_name': interface.device.name,
                'mac_address': interface.mac_address,
                'ip_address': interface.ip_address,
                'subnet_mask': interface.subnet_mask,
                'interface_type': interface.interface_type,
                'speed': interface.speed,
                'status': interface.status,
                'description': interface.description
            }
            
            # Appliquer les filtres si spécifiés
            if filters:
                if filters.get('device_id') and interface.device.id != filters['device_id']:
                    continue
                if filters.get('status') and interface.status != filters['status']:
                    continue
                if filters.get('interface_type') and interface.interface_type != filters['interface_type']:
                    continue
            
            result.append(interface_dict)
        
        return result
    
    def get_all_by_device(self, device_id: int) -> List[Dict[str, Any]]:
        """
        Récupère toutes les interfaces d'un équipement réseau.
        
        Args:
            device_id: ID de l'équipement
            
        Returns:
            Liste des interfaces sous forme de dictionnaires
        """
        django_interfaces = self._repository.get_by_device_id(device_id)
        return [
            {
                'id': interface.id,
                'name': interface.name,
                'device_id': interface.device.id,
                'device_name': interface.device.name,
                'mac_address': interface.mac_address,
                'ip_address': interface.ip_address,
                'subnet_mask': interface.subnet_mask,
                'interface_type': interface.interface_type,
                'speed': interface.speed,
                'status': interface.status,
                'description': interface.description
            }
            for interface in django_interfaces
        ]
    
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
        from ...domain.exceptions import ResourceNotFoundException
        
        django_interface = self._repository.get_by_name_and_device_id(name, device_id)
        
        if not django_interface:
            raise ResourceNotFoundException("NetworkInterface", f"name={name}, device_id={device_id}")
        
        return {
            'id': django_interface.id,
            'name': django_interface.name,
            'device_id': django_interface.device.id,
            'device_name': django_interface.device.name,
            'mac_address': django_interface.mac_address,
            'ip_address': django_interface.ip_address,
            'subnet_mask': django_interface.subnet_mask,
            'interface_type': django_interface.interface_type,
            'speed': django_interface.speed,
            'status': django_interface.status,
            'description': django_interface.description
        } 