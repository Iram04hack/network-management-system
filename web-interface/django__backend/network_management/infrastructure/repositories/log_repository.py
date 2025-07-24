"""
Module contenant le repository pour les logs.
"""

from typing import List, Optional, Type, Dict, Any
from datetime import datetime

from django.db.models import QuerySet, Q

from ..models import Log, NetworkDevice
from .base_repository import BaseRepository


class LogRepository(BaseRepository[Log]):
    """
    Repository pour les logs.
    
    Cette classe fournit des méthodes pour accéder aux données
    des logs dans la base de données.
    """
    
    @property
    def model_class(self) -> Type[Log]:
        """
        Retourne la classe du modèle géré par ce repository.
        
        Returns:
            Type[Log]: La classe du modèle Log.
        """
        return Log
    
    def get_by_device(self, device: NetworkDevice) -> QuerySet[Log]:
        """
        Récupère les logs d'un équipement.
        
        Args:
            device (NetworkDevice): L'équipement dont on veut récupérer les logs.
            
        Returns:
            QuerySet[Log]: Un QuerySet contenant les logs de l'équipement.
        """
        return self.model_class.objects.filter(device=device)
    
    def get_by_device_id(self, device_id: int) -> QuerySet[Log]:
        """
        Récupère les logs d'un équipement par son ID.
        
        Args:
            device_id (int): L'ID de l'équipement dont on veut récupérer les logs.
            
        Returns:
            QuerySet[Log]: Un QuerySet contenant les logs de l'équipement.
        """
        return self.model_class.objects.filter(device_id=device_id)
    
    def get_by_level(self, level: str) -> QuerySet[Log]:
        """
        Récupère des logs par niveau.
        
        Args:
            level (str): Le niveau des logs.
            
        Returns:
            QuerySet[Log]: Un QuerySet contenant les logs du niveau spécifié.
        """
        return self.model_class.objects.filter(level=level)
    
    def get_by_source(self, source: str) -> QuerySet[Log]:
        """
        Récupère des logs par source.
        
        Args:
            source (str): La source des logs.
            
        Returns:
            QuerySet[Log]: Un QuerySet contenant les logs de la source spécifiée.
        """
        return self.model_class.objects.filter(source=source)
    
    def get_by_time_range(self, start_time: datetime, end_time: datetime) -> QuerySet[Log]:
        """
        Récupère des logs par plage de temps.
        
        Args:
            start_time (datetime): L'heure de début de la plage.
            end_time (datetime): L'heure de fin de la plage.
            
        Returns:
            QuerySet[Log]: Un QuerySet contenant les logs dans la plage de temps spécifiée.
        """
        return self.model_class.objects.filter(timestamp__range=(start_time, end_time))
    
    def get_by_device_level_time_range(self, device: NetworkDevice, level: str, start_time: datetime, end_time: datetime) -> QuerySet[Log]:
        """
        Récupère des logs d'un équipement par niveau et plage de temps.
        
        Args:
            device (NetworkDevice): L'équipement dont on veut récupérer les logs.
            level (str): Le niveau des logs.
            start_time (datetime): L'heure de début de la plage.
            end_time (datetime): L'heure de fin de la plage.
            
        Returns:
            QuerySet[Log]: Un QuerySet contenant les logs de l'équipement avec le niveau spécifié dans la plage de temps spécifiée.
        """
        return self.model_class.objects.filter(
            device=device,
            level=level,
            timestamp__range=(start_time, end_time)
        )
    
    def get_by_source_level_time_range(self, source: str, level: str, start_time: datetime, end_time: datetime) -> QuerySet[Log]:
        """
        Récupère des logs d'une source par niveau et plage de temps.
        
        Args:
            source (str): La source des logs.
            level (str): Le niveau des logs.
            start_time (datetime): L'heure de début de la plage.
            end_time (datetime): L'heure de fin de la plage.
            
        Returns:
            QuerySet[Log]: Un QuerySet contenant les logs de la source avec le niveau spécifié dans la plage de temps spécifiée.
        """
        return self.model_class.objects.filter(
            source=source,
            level=level,
            timestamp__range=(start_time, end_time)
        )
    
    def search(self, query: str) -> QuerySet[Log]:
        """
        Recherche des logs par message ou source.
        
        Args:
            query (str): Le terme de recherche.
            
        Returns:
            QuerySet[Log]: Un QuerySet contenant les logs trouvés.
        """
        return self.model_class.objects.filter(
            Q(message__icontains=query) |
            Q(source__icontains=query)
        )
    
    def get_errors(self) -> QuerySet[Log]:
        """
        Récupère les logs de niveau erreur.
        
        Returns:
            QuerySet[Log]: Un QuerySet contenant les logs de niveau erreur.
        """
        return self.model_class.objects.filter(level='error')
    
    def get_warnings(self) -> QuerySet[Log]:
        """
        Récupère les logs de niveau avertissement.
        
        Returns:
            QuerySet[Log]: Un QuerySet contenant les logs de niveau avertissement.
        """
        return self.model_class.objects.filter(level='warning')
    
    def get_infos(self) -> QuerySet[Log]:
        """
        Récupère les logs de niveau information.
        
        Returns:
            QuerySet[Log]: Un QuerySet contenant les logs de niveau information.
        """
        return self.model_class.objects.filter(level='info')
    
    def get_debugs(self) -> QuerySet[Log]:
        """
        Récupère les logs de niveau débogage.
        
        Returns:
            QuerySet[Log]: Un QuerySet contenant les logs de niveau débogage.
        """
        return self.model_class.objects.filter(level='debug')
    
    def get_with_device(self) -> QuerySet[Log]:
        """
        Récupère tous les logs avec leur équipement préchargé.
        
        Returns:
            QuerySet[Log]: Un QuerySet contenant les logs avec leur équipement.
        """
        return self.model_class.objects.select_related('device') 