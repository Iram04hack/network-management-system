"""
Module contenant le repository pour les interfaces réseau.
"""

from typing import List, Optional, Type, Dict, Any

from django.db.models import QuerySet, Q

from ..models import NetworkInterface, NetworkDevice
from .base_repository import BaseRepository


class InterfaceRepository(BaseRepository[NetworkInterface]):
    """
    Repository pour les interfaces réseau.
    
    Cette classe fournit des méthodes pour accéder aux données
    des interfaces réseau dans la base de données.
    """
    
    @property
    def model_class(self) -> Type[NetworkInterface]:
        """
        Retourne la classe du modèle géré par ce repository.
        
        Returns:
            Type[NetworkInterface]: La classe du modèle NetworkInterface.
        """
        return NetworkInterface
    
    def get_by_device(self, device: NetworkDevice) -> QuerySet[NetworkInterface]:
        """
        Récupère les interfaces d'un équipement.
        
        Args:
            device (NetworkDevice): L'équipement dont on veut récupérer les interfaces.
            
        Returns:
            QuerySet[NetworkInterface]: Un QuerySet contenant les interfaces de l'équipement.
        """
        return self.model_class.objects.filter(device=device)
    
    def get_by_device_id(self, device_id: int) -> QuerySet[NetworkInterface]:
        """
        Récupère les interfaces d'un équipement par son ID.
        
        Args:
            device_id (int): L'ID de l'équipement dont on veut récupérer les interfaces.
            
        Returns:
            QuerySet[NetworkInterface]: Un QuerySet contenant les interfaces de l'équipement.
        """
        return self.model_class.objects.filter(device_id=device_id)
    
    def get_by_name_and_device(self, name: str, device: NetworkDevice) -> Optional[NetworkInterface]:
        """
        Récupère une interface par son nom et son équipement.
        
        Args:
            name (str): Le nom de l'interface.
            device (NetworkDevice): L'équipement auquel appartient l'interface.
            
        Returns:
            Optional[NetworkInterface]: L'interface trouvée ou None si aucune interface n'a été trouvée.
        """
        try:
            return self.model_class.objects.get(name=name, device=device)
        except self.model_class.DoesNotExist:
            return None
    
    def get_by_name_and_device_id(self, name: str, device_id: int) -> Optional[NetworkInterface]:
        """
        Récupère une interface par son nom et l'ID de son équipement.
        
        Args:
            name (str): Le nom de l'interface.
            device_id (int): L'ID de l'équipement auquel appartient l'interface.
            
        Returns:
            Optional[NetworkInterface]: L'interface trouvée ou None si aucune interface n'a été trouvée.
        """
        try:
            return self.model_class.objects.get(name=name, device_id=device_id)
        except self.model_class.DoesNotExist:
            return None
    
    def get_by_mac_address(self, mac_address: str) -> Optional[NetworkInterface]:
        """
        Récupère une interface par son adresse MAC.
        
        Args:
            mac_address (str): L'adresse MAC de l'interface.
            
        Returns:
            Optional[NetworkInterface]: L'interface trouvée ou None si aucune interface n'a été trouvée.
        """
        try:
            return self.model_class.objects.get(mac_address=mac_address)
        except self.model_class.DoesNotExist:
            return None
    
    def get_by_ip_address(self, ip_address: str) -> Optional[NetworkInterface]:
        """
        Récupère une interface par son adresse IP.
        
        Args:
            ip_address (str): L'adresse IP de l'interface.
            
        Returns:
            Optional[NetworkInterface]: L'interface trouvée ou None si aucune interface n'a été trouvée.
        """
        try:
            return self.model_class.objects.get(ip_address=ip_address)
        except self.model_class.DoesNotExist:
            return None
    
    def search(self, query: str) -> QuerySet[NetworkInterface]:
        """
        Recherche des interfaces par nom, adresse MAC, adresse IP ou type.
        
        Args:
            query (str): Le terme de recherche.
            
        Returns:
            QuerySet[NetworkInterface]: Un QuerySet contenant les interfaces trouvées.
        """
        return self.model_class.objects.filter(
            Q(name__icontains=query) |
            Q(mac_address__icontains=query) |
            Q(ip_address__icontains=query) |
            Q(interface_type__icontains=query)
        )
    
    def get_by_status(self, status: str) -> QuerySet[NetworkInterface]:
        """
        Récupère des interfaces par statut.
        
        Args:
            status (str): Le statut des interfaces.
            
        Returns:
            QuerySet[NetworkInterface]: Un QuerySet contenant les interfaces avec le statut spécifié.
        """
        return self.model_class.objects.filter(status=status)
    
    def get_by_type(self, interface_type: str) -> QuerySet[NetworkInterface]:
        """
        Récupère des interfaces par type.
        
        Args:
            interface_type (str): Le type d'interface.
            
        Returns:
            QuerySet[NetworkInterface]: Un QuerySet contenant les interfaces du type spécifié.
        """
        return self.model_class.objects.filter(interface_type=interface_type)
    
    def get_with_connections(self) -> QuerySet[NetworkInterface]:
        """
        Récupère toutes les interfaces avec leurs connexions préchargées.
        
        Returns:
            QuerySet[NetworkInterface]: Un QuerySet contenant les interfaces avec leurs connexions.
        """
        return self.model_class.objects.prefetch_related('source_connections', 'target_connections')
    
    def get_with_alerts(self) -> QuerySet[NetworkInterface]:
        """
        Récupère toutes les interfaces avec leurs alertes préchargées.
        
        Returns:
            QuerySet[NetworkInterface]: Un QuerySet contenant les interfaces avec leurs alertes.
        """
        return self.model_class.objects.prefetch_related('alerts')
    
    def get_with_metrics(self) -> QuerySet[NetworkInterface]:
        """
        Récupère toutes les interfaces avec leurs métriques préchargées.
        
        Returns:
            QuerySet[NetworkInterface]: Un QuerySet contenant les interfaces avec leurs métriques.
        """
        return self.model_class.objects.prefetch_related('metrics') 