"""
Module contenant le repository pour les équipements réseau.
"""

from typing import List, Optional, Type, Dict, Any

from django.db.models import QuerySet, Q

from ..models import NetworkDevice
from .base_repository import BaseRepository


class DeviceRepository(BaseRepository[NetworkDevice]):
    """
    Repository pour les équipements réseau.
    
    Cette classe fournit des méthodes pour accéder aux données
    des équipements réseau dans la base de données.
    """
    
    @property
    def model_class(self) -> Type[NetworkDevice]:
        """
        Retourne la classe du modèle géré par ce repository.
        
        Returns:
            Type[NetworkDevice]: La classe du modèle NetworkDevice.
        """
        return NetworkDevice
    
    def get_by_name(self, name: str) -> Optional[NetworkDevice]:
        """
        Récupère un équipement par son nom.
        
        Args:
            name (str): Le nom de l'équipement à récupérer.
            
        Returns:
            Optional[NetworkDevice]: L'équipement trouvé ou None si aucun équipement n'a été trouvé.
        """
        try:
            return self.model_class.objects.get(name=name)
        except self.model_class.DoesNotExist:
            return None
    
    def get_by_ip_address(self, ip_address: str) -> Optional[NetworkDevice]:
        """
        Récupère un équipement par son adresse IP.
        
        Args:
            ip_address (str): L'adresse IP de l'équipement à récupérer.
            
        Returns:
            Optional[NetworkDevice]: L'équipement trouvé ou None si aucun équipement n'a été trouvé.
        """
        try:
            return self.model_class.objects.get(ip_address=ip_address)
        except self.model_class.DoesNotExist:
            return None
    
    def search(self, query: str) -> QuerySet[NetworkDevice]:
        """
        Recherche des équipements par nom, adresse IP, type ou emplacement.
        
        Args:
            query (str): Le terme de recherche.
            
        Returns:
            QuerySet[NetworkDevice]: Un QuerySet contenant les équipements trouvés.
        """
        return self.model_class.objects.filter(
            Q(name__icontains=query) |
            Q(ip_address__icontains=query) |
            Q(device_type__icontains=query) |
            Q(location__icontains=query)
        )
    
    def get_by_type(self, device_type: str) -> QuerySet[NetworkDevice]:
        """
        Récupère des équipements par type.
        
        Args:
            device_type (str): Le type d'équipement.
            
        Returns:
            QuerySet[NetworkDevice]: Un QuerySet contenant les équipements du type spécifié.
        """
        return self.model_class.objects.filter(device_type=device_type)
    
    def get_by_vendor(self, vendor: str) -> QuerySet[NetworkDevice]:
        """
        Récupère des équipements par fabricant.
        
        Args:
            vendor (str): Le fabricant des équipements.
            
        Returns:
            QuerySet[NetworkDevice]: Un QuerySet contenant les équipements du fabricant spécifié.
        """
        return self.model_class.objects.filter(vendor=vendor)
    
    def get_by_status(self, status: str) -> QuerySet[NetworkDevice]:
        """
        Récupère des équipements par statut.
        
        Args:
            status (str): Le statut des équipements.
            
        Returns:
            QuerySet[NetworkDevice]: Un QuerySet contenant les équipements avec le statut spécifié.
        """
        return self.model_class.objects.filter(status=status)
    
    def get_by_location(self, location: str) -> QuerySet[NetworkDevice]:
        """
        Récupère des équipements par emplacement.
        
        Args:
            location (str): L'emplacement des équipements.
            
        Returns:
            QuerySet[NetworkDevice]: Un QuerySet contenant les équipements à l'emplacement spécifié.
        """
        return self.model_class.objects.filter(location=location)
    
    def get_with_interfaces(self) -> QuerySet[NetworkDevice]:
        """
        Récupère tous les équipements avec leurs interfaces préchargées.
        
        Returns:
            QuerySet[NetworkDevice]: Un QuerySet contenant les équipements avec leurs interfaces.
        """
        return self.model_class.objects.prefetch_related('interfaces')
    
    def get_with_configurations(self) -> QuerySet[NetworkDevice]:
        """
        Récupère tous les équipements avec leurs configurations préchargées.
        
        Returns:
            QuerySet[NetworkDevice]: Un QuerySet contenant les équipements avec leurs configurations.
        """
        return self.model_class.objects.prefetch_related('configurations')
    
    def get_with_alerts(self) -> QuerySet[NetworkDevice]:
        """
        Récupère tous les équipements avec leurs alertes préchargées.
        
        Returns:
            QuerySet[NetworkDevice]: Un QuerySet contenant les équipements avec leurs alertes.
        """
        return self.model_class.objects.prefetch_related('alerts')
    
    def get_with_metrics(self) -> QuerySet[NetworkDevice]:
        """
        Récupère tous les équipements avec leurs métriques préchargées.
        
        Returns:
            QuerySet[NetworkDevice]: Un QuerySet contenant les équipements avec leurs métriques.
        """
        return self.model_class.objects.prefetch_related('metrics') 