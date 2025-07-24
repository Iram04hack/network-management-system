"""
Module contenant le repository pour les configurations d'équipements.
"""

from typing import List, Optional, Type, Dict, Any

from django.db.models import QuerySet, Q

from ..models import DeviceConfiguration, NetworkDevice
from .base_repository import BaseRepository


class ConfigurationRepository(BaseRepository[DeviceConfiguration]):
    """
    Repository pour les configurations d'équipements.
    
    Cette classe fournit des méthodes pour accéder aux données
    des configurations d'équipements dans la base de données.
    """
    
    @property
    def model_class(self) -> Type[DeviceConfiguration]:
        """
        Retourne la classe du modèle géré par ce repository.
        
        Returns:
            Type[DeviceConfiguration]: La classe du modèle DeviceConfiguration.
        """
        return DeviceConfiguration
    
    def get_by_device(self, device: NetworkDevice) -> QuerySet[DeviceConfiguration]:
        """
        Récupère les configurations d'un équipement.
        
        Args:
            device (NetworkDevice): L'équipement dont on veut récupérer les configurations.
            
        Returns:
            QuerySet[DeviceConfiguration]: Un QuerySet contenant les configurations de l'équipement.
        """
        return self.model_class.objects.filter(device=device)
    
    def get_by_device_id(self, device_id: int) -> QuerySet[DeviceConfiguration]:
        """
        Récupère les configurations d'un équipement par son ID.
        
        Args:
            device_id (int): L'ID de l'équipement dont on veut récupérer les configurations.
            
        Returns:
            QuerySet[DeviceConfiguration]: Un QuerySet contenant les configurations de l'équipement.
        """
        return self.model_class.objects.filter(device_id=device_id)
    
    def get_active_by_device(self, device: NetworkDevice) -> Optional[DeviceConfiguration]:
        """
        Récupère la configuration active d'un équipement.
        
        Args:
            device (NetworkDevice): L'équipement dont on veut récupérer la configuration active.
            
        Returns:
            Optional[DeviceConfiguration]: La configuration active de l'équipement ou None si aucune configuration active n'existe.
        """
        try:
            return self.model_class.objects.get(device=device, is_active=True)
        except self.model_class.DoesNotExist:
            return None
    
    def get_active_by_device_id(self, device_id: int) -> Optional[DeviceConfiguration]:
        """
        Récupère la configuration active d'un équipement par son ID.
        
        Args:
            device_id (int): L'ID de l'équipement dont on veut récupérer la configuration active.
            
        Returns:
            Optional[DeviceConfiguration]: La configuration active de l'équipement ou None si aucune configuration active n'existe.
        """
        try:
            return self.model_class.objects.get(device_id=device_id, is_active=True)
        except self.model_class.DoesNotExist:
            return None
    
    def get_by_version(self, device: NetworkDevice, version: str) -> Optional[DeviceConfiguration]:
        """
        Récupère une configuration d'un équipement par sa version.
        
        Args:
            device (NetworkDevice): L'équipement dont on veut récupérer la configuration.
            version (str): La version de la configuration.
            
        Returns:
            Optional[DeviceConfiguration]: La configuration de l'équipement avec la version spécifiée ou None si aucune configuration n'existe.
        """
        try:
            return self.model_class.objects.get(device=device, version=version)
        except self.model_class.DoesNotExist:
            return None
    
    def get_by_version_and_device_id(self, device_id: int, version: str) -> Optional[DeviceConfiguration]:
        """
        Récupère une configuration d'un équipement par son ID et sa version.
        
        Args:
            device_id (int): L'ID de l'équipement dont on veut récupérer la configuration.
            version (str): La version de la configuration.
            
        Returns:
            Optional[DeviceConfiguration]: La configuration de l'équipement avec la version spécifiée ou None si aucune configuration n'existe.
        """
        try:
            return self.model_class.objects.get(device_id=device_id, version=version)
        except self.model_class.DoesNotExist:
            return None
    
    def get_by_status(self, status: str) -> QuerySet[DeviceConfiguration]:
        """
        Récupère des configurations par statut.
        
        Args:
            status (str): Le statut des configurations.
            
        Returns:
            QuerySet[DeviceConfiguration]: Un QuerySet contenant les configurations avec le statut spécifié.
        """
        return self.model_class.objects.filter(status=status)
    
    def get_by_created_by(self, created_by: str) -> QuerySet[DeviceConfiguration]:
        """
        Récupère des configurations par créateur.
        
        Args:
            created_by (str): Le créateur des configurations.
            
        Returns:
            QuerySet[DeviceConfiguration]: Un QuerySet contenant les configurations créées par le créateur spécifié.
        """
        return self.model_class.objects.filter(created_by=created_by)
    
    def get_with_parent(self) -> QuerySet[DeviceConfiguration]:
        """
        Récupère toutes les configurations avec leur configuration parent préchargée.
        
        Returns:
            QuerySet[DeviceConfiguration]: Un QuerySet contenant les configurations avec leur configuration parent.
        """
        return self.model_class.objects.select_related('parent')
    
    def get_with_children(self) -> QuerySet[DeviceConfiguration]:
        """
        Récupère toutes les configurations avec leurs configurations enfants préchargées.
        
        Returns:
            QuerySet[DeviceConfiguration]: Un QuerySet contenant les configurations avec leurs configurations enfants.
        """
        return self.model_class.objects.prefetch_related('children')
    
    def get_with_compliance_checks(self) -> QuerySet[DeviceConfiguration]:
        """
        Récupère toutes les configurations avec leurs vérifications de conformité préchargées.
        
        Returns:
            QuerySet[DeviceConfiguration]: Un QuerySet contenant les configurations avec leurs vérifications de conformité.
        """
        return self.model_class.objects.prefetch_related('compliance_checks') 