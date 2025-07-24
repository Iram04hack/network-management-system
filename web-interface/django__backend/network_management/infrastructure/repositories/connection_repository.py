"""
Module contenant le repository pour les connexions réseau.
"""

from typing import List, Optional, Type, Dict, Any

from django.db.models import QuerySet, Q

from ..models import NetworkConnection, NetworkDevice, NetworkInterface
from .base_repository import BaseRepository


class ConnectionRepository(BaseRepository[NetworkConnection]):
    """
    Repository pour les connexions réseau.
    
    Cette classe fournit des méthodes pour accéder aux données
    des connexions réseau dans la base de données.
    """
    
    @property
    def model_class(self) -> Type[NetworkConnection]:
        """
        Retourne la classe du modèle géré par ce repository.
        
        Returns:
            Type[NetworkConnection]: La classe du modèle NetworkConnection.
        """
        return NetworkConnection
    
    def get_by_source_device(self, device: NetworkDevice) -> QuerySet[NetworkConnection]:
        """
        Récupère les connexions dont l'équipement source est spécifié.
        
        Args:
            device (NetworkDevice): L'équipement source.
            
        Returns:
            QuerySet[NetworkConnection]: Un QuerySet contenant les connexions.
        """
        return self.model_class.objects.filter(source_device=device)
    
    def get_by_target_device(self, device: NetworkDevice) -> QuerySet[NetworkConnection]:
        """
        Récupère les connexions dont l'équipement cible est spécifié.
        
        Args:
            device (NetworkDevice): L'équipement cible.
            
        Returns:
            QuerySet[NetworkConnection]: Un QuerySet contenant les connexions.
        """
        return self.model_class.objects.filter(target_device=device)
    
    def get_by_device(self, device: NetworkDevice) -> QuerySet[NetworkConnection]:
        """
        Récupère les connexions dont l'équipement source ou cible est spécifié.
        
        Args:
            device (NetworkDevice): L'équipement source ou cible.
            
        Returns:
            QuerySet[NetworkConnection]: Un QuerySet contenant les connexions.
        """
        return self.model_class.objects.filter(
            Q(source_device=device) | Q(target_device=device)
        )
    
    def get_by_source_interface(self, interface: NetworkInterface) -> QuerySet[NetworkConnection]:
        """
        Récupère les connexions dont l'interface source est spécifiée.
        
        Args:
            interface (NetworkInterface): L'interface source.
            
        Returns:
            QuerySet[NetworkConnection]: Un QuerySet contenant les connexions.
        """
        return self.model_class.objects.filter(source_interface=interface)
    
    def get_by_target_interface(self, interface: NetworkInterface) -> QuerySet[NetworkConnection]:
        """
        Récupère les connexions dont l'interface cible est spécifiée.
        
        Args:
            interface (NetworkInterface): L'interface cible.
            
        Returns:
            QuerySet[NetworkConnection]: Un QuerySet contenant les connexions.
        """
        return self.model_class.objects.filter(target_interface=interface)
    
    def get_by_interface(self, interface: NetworkInterface) -> QuerySet[NetworkConnection]:
        """
        Récupère les connexions dont l'interface source ou cible est spécifiée.
        
        Args:
            interface (NetworkInterface): L'interface source ou cible.
            
        Returns:
            QuerySet[NetworkConnection]: Un QuerySet contenant les connexions.
        """
        return self.model_class.objects.filter(
            Q(source_interface=interface) | Q(target_interface=interface)
        )
    
    def get_by_connection_type(self, connection_type: str) -> QuerySet[NetworkConnection]:
        """
        Récupère les connexions par type de connexion.
        
        Args:
            connection_type (str): Le type de connexion.
            
        Returns:
            QuerySet[NetworkConnection]: Un QuerySet contenant les connexions du type spécifié.
        """
        return self.model_class.objects.filter(connection_type=connection_type)
    
    def get_by_status(self, status: str) -> QuerySet[NetworkConnection]:
        """
        Récupère les connexions par statut.
        
        Args:
            status (str): Le statut des connexions.
            
        Returns:
            QuerySet[NetworkConnection]: Un QuerySet contenant les connexions avec le statut spécifié.
        """
        return self.model_class.objects.filter(status=status)
    
    def get_between_devices(self, device1: NetworkDevice, device2: NetworkDevice) -> QuerySet[NetworkConnection]:
        """
        Récupère les connexions entre deux équipements.
        
        Args:
            device1 (NetworkDevice): Le premier équipement.
            device2 (NetworkDevice): Le deuxième équipement.
            
        Returns:
            QuerySet[NetworkConnection]: Un QuerySet contenant les connexions entre les deux équipements.
        """
        return self.model_class.objects.filter(
            (Q(source_device=device1) & Q(target_device=device2)) |
            (Q(source_device=device2) & Q(target_device=device1))
        )
    
    def get_between_interfaces(self, interface1: NetworkInterface, interface2: NetworkInterface) -> Optional[NetworkConnection]:
        """
        Récupère la connexion entre deux interfaces.
        
        Args:
            interface1 (NetworkInterface): La première interface.
            interface2 (NetworkInterface): La deuxième interface.
            
        Returns:
            Optional[NetworkConnection]: La connexion entre les deux interfaces ou None si aucune connexion n'existe.
        """
        try:
            return self.model_class.objects.get(
                (Q(source_interface=interface1) & Q(target_interface=interface2)) |
                (Q(source_interface=interface2) & Q(target_interface=interface1))
            )
        except self.model_class.DoesNotExist:
            return None
    
    def get_with_devices_and_interfaces(self) -> QuerySet[NetworkConnection]:
        """
        Récupère toutes les connexions avec leurs équipements et interfaces préchargés.
        
        Returns:
            QuerySet[NetworkConnection]: Un QuerySet contenant les connexions avec leurs équipements et interfaces.
        """
        return self.model_class.objects.select_related(
            'source_device', 'source_interface', 'target_device', 'target_interface'
        ) 