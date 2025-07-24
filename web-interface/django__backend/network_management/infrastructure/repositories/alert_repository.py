"""
Module contenant le repository pour les alertes.
"""

from typing import List, Optional, Type, Dict, Any
from datetime import datetime

from django.db.models import QuerySet, Q

from ..models import Alert, NetworkDevice, NetworkInterface
from .base_repository import BaseRepository


class AlertRepository(BaseRepository[Alert]):
    """
    Repository pour les alertes.
    
    Cette classe fournit des méthodes pour accéder aux données
    des alertes dans la base de données.
    """
    
    @property
    def model_class(self) -> Type[Alert]:
        """
        Retourne la classe du modèle géré par ce repository.
        
        Returns:
            Type[Alert]: La classe du modèle Alert.
        """
        return Alert
    
    def get_by_device(self, device: NetworkDevice) -> QuerySet[Alert]:
        """
        Récupère les alertes d'un équipement.
        
        Args:
            device (NetworkDevice): L'équipement dont on veut récupérer les alertes.
            
        Returns:
            QuerySet[Alert]: Un QuerySet contenant les alertes de l'équipement.
        """
        return self.model_class.objects.filter(device=device)
    
    def get_by_device_id(self, device_id: int) -> QuerySet[Alert]:
        """
        Récupère les alertes d'un équipement par son ID.
        
        Args:
            device_id (int): L'ID de l'équipement dont on veut récupérer les alertes.
            
        Returns:
            QuerySet[Alert]: Un QuerySet contenant les alertes de l'équipement.
        """
        return self.model_class.objects.filter(device_id=device_id)
    
    def get_by_interface(self, interface: NetworkInterface) -> QuerySet[Alert]:
        """
        Récupère les alertes d'une interface.
        
        Args:
            interface (NetworkInterface): L'interface dont on veut récupérer les alertes.
            
        Returns:
            QuerySet[Alert]: Un QuerySet contenant les alertes de l'interface.
        """
        return self.model_class.objects.filter(interface=interface)
    
    def get_by_interface_id(self, interface_id: int) -> QuerySet[Alert]:
        """
        Récupère les alertes d'une interface par son ID.
        
        Args:
            interface_id (int): L'ID de l'interface dont on veut récupérer les alertes.
            
        Returns:
            QuerySet[Alert]: Un QuerySet contenant les alertes de l'interface.
        """
        return self.model_class.objects.filter(interface_id=interface_id)
    
    def get_by_severity(self, severity: str) -> QuerySet[Alert]:
        """
        Récupère des alertes par sévérité.
        
        Args:
            severity (str): La sévérité des alertes.
            
        Returns:
            QuerySet[Alert]: Un QuerySet contenant les alertes avec la sévérité spécifiée.
        """
        return self.model_class.objects.filter(severity=severity)
    
    def get_by_status(self, status: str) -> QuerySet[Alert]:
        """
        Récupère des alertes par statut.
        
        Args:
            status (str): Le statut des alertes.
            
        Returns:
            QuerySet[Alert]: Un QuerySet contenant les alertes avec le statut spécifié.
        """
        return self.model_class.objects.filter(status=status)
    
    def get_active(self) -> QuerySet[Alert]:
        """
        Récupère les alertes actives.
        
        Returns:
            QuerySet[Alert]: Un QuerySet contenant les alertes actives.
        """
        return self.model_class.objects.filter(status='active')
    
    def get_acknowledged(self) -> QuerySet[Alert]:
        """
        Récupère les alertes acquittées.
        
        Returns:
            QuerySet[Alert]: Un QuerySet contenant les alertes acquittées.
        """
        return self.model_class.objects.filter(acknowledged=True)
    
    def get_unacknowledged(self) -> QuerySet[Alert]:
        """
        Récupère les alertes non acquittées.
        
        Returns:
            QuerySet[Alert]: Un QuerySet contenant les alertes non acquittées.
        """
        return self.model_class.objects.filter(acknowledged=False)
    
    def get_by_source(self, source: str) -> QuerySet[Alert]:
        """
        Récupère des alertes par source.
        
        Args:
            source (str): La source des alertes.
            
        Returns:
            QuerySet[Alert]: Un QuerySet contenant les alertes de la source spécifiée.
        """
        return self.model_class.objects.filter(source=source)
    
    def get_by_category(self, category: str) -> QuerySet[Alert]:
        """
        Récupère des alertes par catégorie.
        
        Args:
            category (str): La catégorie des alertes.
            
        Returns:
            QuerySet[Alert]: Un QuerySet contenant les alertes de la catégorie spécifiée.
        """
        return self.model_class.objects.filter(category=category)
    
    def get_by_acknowledged_by(self, acknowledged_by: str) -> QuerySet[Alert]:
        """
        Récupère des alertes par acquitteur.
        
        Args:
            acknowledged_by (str): L'acquitteur des alertes.
            
        Returns:
            QuerySet[Alert]: Un QuerySet contenant les alertes acquittées par l'acquitteur spécifié.
        """
        return self.model_class.objects.filter(acknowledged_by=acknowledged_by)
    
    def get_by_date_range(self, start_date: datetime, end_date: datetime) -> QuerySet[Alert]:
        """
        Récupère des alertes par plage de dates.
        
        Args:
            start_date (datetime): La date de début de la plage.
            end_date (datetime): La date de fin de la plage.
            
        Returns:
            QuerySet[Alert]: Un QuerySet contenant les alertes créées dans la plage de dates spécifiée.
        """
        return self.model_class.objects.filter(created_at__range=(start_date, end_date))
    
    def search(self, query: str) -> QuerySet[Alert]:
        """
        Recherche des alertes par titre, message, source ou catégorie.
        
        Args:
            query (str): Le terme de recherche.
            
        Returns:
            QuerySet[Alert]: Un QuerySet contenant les alertes trouvées.
        """
        return self.model_class.objects.filter(
            Q(title__icontains=query) |
            Q(message__icontains=query) |
            Q(source__icontains=query) |
            Q(category__icontains=query)
        )
    
    def get_with_related(self) -> QuerySet[Alert]:
        """
        Récupère toutes les alertes avec leurs relations préchargées.
        
        Returns:
            QuerySet[Alert]: Un QuerySet contenant les alertes avec leurs relations.
        """
        return self.model_class.objects.select_related('device', 'interface') 