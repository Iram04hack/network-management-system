"""
Module contenant l'adaptateur pour le repository de configurations.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime

from ...domain.interfaces import DeviceConfigurationRepository
from ...domain.entities import NetworkDeviceEntity as DomainDevice, DeviceConfigurationEntity as DomainConfiguration
from ..repositories.configuration_repository import ConfigurationRepository
from ..models import DeviceConfiguration as DjangoConfiguration, NetworkDevice as DjangoDevice


class DjangoConfigurationRepository(DeviceConfigurationRepository):
    """
    Adaptateur Django pour le repository de configurations.

    Cette classe implémente l'interface DeviceConfigurationRepository
    en utilisant le repository Django ConfigurationRepository.
    """
    
    def __init__(self):
        """
        Initialise une nouvelle instance de DjangoConfigurationRepository.
        """
        self._repository = ConfigurationRepository()
    
    def _to_domain(self, django_config: DjangoConfiguration) -> DomainConfiguration:
        """
        Convertit une configuration Django en configuration du domaine.
        
        Args:
            django_config (DjangoConfiguration): La configuration Django à convertir.
            
        Returns:
            DomainConfiguration: La configuration du domaine correspondante.
        """
        device = DomainDevice(
            id=django_config.device.id,
            name=django_config.device.name,
            ip_address=django_config.device.ip_address,
            device_type=django_config.device.device_type,
            vendor=django_config.device.vendor,
            status=django_config.device.status
        )
        
        parent_id = django_config.parent.id if django_config.parent else None
        
        return DomainConfiguration(
            id=django_config.id,
            device=device,
            content=django_config.content,
            version=django_config.version,
            is_active=django_config.is_active,
            status=django_config.status,
            comment=django_config.comment,
            created_by=django_config.created_by,
            created_at=django_config.created_at,
            applied_at=django_config.applied_at,
            parent_id=parent_id
        )
    
    def _to_django(self, domain_config: DomainConfiguration, django_device: Optional[DjangoDevice] = None,
                  django_parent: Optional[DjangoConfiguration] = None) -> Dict[str, Any]:
        """
        Convertit une configuration du domaine en dictionnaire pour création/mise à jour Django.
        
        Args:
            domain_config (DomainConfiguration): La configuration du domaine à convertir.
            django_device (Optional[DjangoDevice]): L'équipement Django associé, si disponible.
            django_parent (Optional[DjangoConfiguration]): La configuration parent Django, si disponible.
            
        Returns:
            Dict[str, Any]: Un dictionnaire contenant les attributs pour création/mise à jour Django.
        """
        data = {
            'content': domain_config.content,
            'version': domain_config.version,
            'is_active': domain_config.is_active,
            'status': domain_config.status,
            'comment': domain_config.comment,
            'created_by': domain_config.created_by
        }
        
        if domain_config.applied_at:
            data['applied_at'] = domain_config.applied_at
        
        if django_device:
            data['device'] = django_device
            
        if django_parent:
            data['parent'] = django_parent
        
        return data
    
    def get_by_id(self, config_id: int) -> Optional[DomainConfiguration]:
        """
        Récupère une configuration par son ID.
        
        Args:
            config_id (int): L'ID de la configuration à récupérer.
            
        Returns:
            Optional[DomainConfiguration]: La configuration trouvée ou None si aucune configuration n'a été trouvée.
        """
        django_config = self._repository.get_by_id(config_id)
        if django_config:
            return self._to_domain(django_config)
        return None
    
    def get_by_device_id(self, device_id: int) -> List[DomainConfiguration]:
        """
        Récupère les configurations d'un équipement par son ID.
        
        Args:
            device_id (int): L'ID de l'équipement dont on veut récupérer les configurations.
            
        Returns:
            List[DomainConfiguration]: Une liste contenant les configurations de l'équipement.
        """
        django_configs = self._repository.get_by_device_id(device_id)
        return [self._to_domain(config) for config in django_configs]
    
    def get_active_by_device_id(self, device_id: int) -> Optional[DomainConfiguration]:
        """
        Récupère la configuration active d'un équipement par son ID.
        
        Args:
            device_id (int): L'ID de l'équipement dont on veut récupérer la configuration active.
            
        Returns:
            Optional[DomainConfiguration]: La configuration active de l'équipement ou None si aucune configuration active n'existe.
        """
        django_config = self._repository.get_active_by_device_id(device_id)
        if django_config:
            return self._to_domain(django_config)
        return None
    
    def get_by_version_and_device_id(self, version: str, device_id: int) -> Optional[DomainConfiguration]:
        """
        Récupère une configuration d'un équipement par sa version et l'ID de l'équipement.
        
        Args:
            version (str): La version de la configuration.
            device_id (int): L'ID de l'équipement dont on veut récupérer la configuration.
            
        Returns:
            Optional[DomainConfiguration]: La configuration de l'équipement avec la version spécifiée ou None si aucune configuration n'existe.
        """
        django_config = self._repository.get_by_version_and_device_id(device_id, version)
        if django_config:
            return self._to_domain(django_config)
        return None
    
    def create(self, config: DomainConfiguration) -> DomainConfiguration:
        """
        Crée une nouvelle configuration.
        
        Args:
            config (DomainConfiguration): La configuration à créer.
            
        Returns:
            DomainConfiguration: La configuration créée avec son ID généré.
        """
        from ..adapters.django_device_repository import DjangoDeviceRepository
        device_repo = DjangoDeviceRepository()
        django_device = device_repo._repository.get_by_id(config.device.id)
        
        if not django_device:
            raise ValueError(f"Device with id {config.device.id} not found")
        
        django_parent = None
        if config.parent_id:
            django_parent = self._repository.get_by_id(config.parent_id)
            if not django_parent:
                raise ValueError(f"Parent configuration with id {config.parent_id} not found")
        
        data = self._to_django(config, django_device, django_parent)
        django_config = self._repository.create(**data)
        return self._to_domain(django_config)
    
    def update(self, config: DomainConfiguration) -> DomainConfiguration:
        """
        Met à jour une configuration existante.
        
        Args:
            config (DomainConfiguration): La configuration à mettre à jour.
            
        Returns:
            DomainConfiguration: La configuration mise à jour.
        """
        django_config = self._repository.get_by_id(config.id)
        if not django_config:
            raise ValueError(f"Configuration with id {config.id} not found")
        
        django_parent = None
        if config.parent_id:
            django_parent = self._repository.get_by_id(config.parent_id)
            if not django_parent:
                raise ValueError(f"Parent configuration with id {config.parent_id} not found")
        
        data = self._to_django(config, None, django_parent)
        django_config = self._repository.update(django_config, **data)
        return self._to_domain(django_config)
    
    def delete(self, config_id: int) -> bool:
        """
        Supprime une configuration.
        
        Args:
            config_id (int): L'ID de la configuration à supprimer.
            
        Returns:
            bool: True si la configuration a été supprimée, False sinon.
        """
        return self._repository.delete(config_id)
    
    def get_all(self, filters: Optional[Dict[str, Any]] = None) -> List[DomainConfiguration]:
        """
        Récupère toutes les configurations selon les filtres fournis.
        
        Args:
            filters (Optional[Dict[str, Any]]): Filtres à appliquer.
            
        Returns:
            List[DomainConfiguration]: Une liste contenant toutes les configurations.
        """
        django_configs = self._repository.get_all()
        
        if filters:
            # Appliquer les filtres côté Python pour simplifier
            # Dans une vraie implémentation, on filtrerait au niveau de la base de données
            filtered_configs = []
            for config in django_configs:
                match = True
                
                if 'device_id' in filters and config.device.id != filters['device_id']:
                    match = False
                if 'is_active' in filters and config.is_active != filters['is_active']:
                    match = False
                if 'status' in filters and config.status != filters['status']:
                    match = False
                
                if match:
                    filtered_configs.append(config)
            
            django_configs = filtered_configs
        
        return [self._to_domain(config) for config in django_configs]
    
    def get_latest_by_device(self, device_id: int) -> DomainConfiguration:
        """
        Récupère la dernière configuration d'un équipement.
        
        Args:
            device_id: ID de l'équipement
            
        Returns:
            Configuration de l'équipement
            
        Raises:
            ResourceNotFoundException: Si aucune configuration n'existe
        """
        from ...domain.exceptions import NetworkDeviceNotFoundException
        
        django_configs = self._repository.get_by_device_id(device_id)
        
        if not django_configs:
            raise NetworkDeviceNotFoundException(f"No configurations found for device {device_id}")
        
        # Trier par date de création pour obtenir la plus récente
        latest_config = max(django_configs, key=lambda c: c.created_at)
        return self._to_domain(latest_config)
    
    def get_history_by_device(self, device_id: int, limit: int = 10) -> List[DomainConfiguration]:
        """
        Récupère l'historique des configurations d'un équipement.
        
        Args:
            device_id: ID de l'équipement
            limit: Nombre maximum de configurations à récupérer
            
        Returns:
            Liste des configurations
        """
        django_configs = self._repository.get_by_device_id(device_id)
        
        # Trier par date de création (plus récent en premier) et limiter
        sorted_configs = sorted(django_configs, key=lambda c: c.created_at, reverse=True)
        limited_configs = sorted_configs[:limit]
        
        return [self._to_domain(config) for config in limited_configs]
    
    def set_active(self, config_id: int, device_id: int) -> Optional[DomainConfiguration]:
        """
        Définit une configuration comme active pour un équipement.
        
        Args:
            config_id (int): L'ID de la configuration à définir comme active.
            device_id (int): L'ID de l'équipement.
            
        Returns:
            Optional[DomainConfiguration]: La configuration activée ou None si la configuration n'a pas pu être activée.
        """
        # Désactiver toutes les configurations actives de l'équipement
        active_configs = self._repository.filter(device_id=device_id, is_active=True)
        for config in active_configs:
            self._repository.update(config, is_active=False)
        
        # Activer la configuration spécifiée
        config = self._repository.get_by_id(config_id)
        if config and config.device_id == device_id:
            config = self._repository.update(config, is_active=True, applied_at=datetime.now())
            return self._to_domain(config)
        return None 