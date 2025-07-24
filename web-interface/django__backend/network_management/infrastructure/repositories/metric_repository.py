"""
Module contenant le repository pour les métriques.
"""

from typing import List, Optional, Type, Dict, Any
from datetime import datetime

from django.db.models import QuerySet, Q, Avg, Max, Min, Sum

from ..models import Metric, NetworkDevice, NetworkInterface
from .base_repository import BaseRepository


class MetricRepository(BaseRepository[Metric]):
    """
    Repository pour les métriques.
    
    Cette classe fournit des méthodes pour accéder aux données
    des métriques dans la base de données.
    """
    
    @property
    def model_class(self) -> Type[Metric]:
        """
        Retourne la classe du modèle géré par ce repository.
        
        Returns:
            Type[Metric]: La classe du modèle Metric.
        """
        return Metric
    
    def get_by_device(self, device: NetworkDevice) -> QuerySet[Metric]:
        """
        Récupère les métriques d'un équipement.
        
        Args:
            device (NetworkDevice): L'équipement dont on veut récupérer les métriques.
            
        Returns:
            QuerySet[Metric]: Un QuerySet contenant les métriques de l'équipement.
        """
        return self.model_class.objects.filter(device=device)
    
    def get_by_device_id(self, device_id: int) -> QuerySet[Metric]:
        """
        Récupère les métriques d'un équipement par son ID.
        
        Args:
            device_id (int): L'ID de l'équipement dont on veut récupérer les métriques.
            
        Returns:
            QuerySet[Metric]: Un QuerySet contenant les métriques de l'équipement.
        """
        return self.model_class.objects.filter(device_id=device_id)
    
    def get_by_interface(self, interface: NetworkInterface) -> QuerySet[Metric]:
        """
        Récupère les métriques d'une interface.
        
        Args:
            interface (NetworkInterface): L'interface dont on veut récupérer les métriques.
            
        Returns:
            QuerySet[Metric]: Un QuerySet contenant les métriques de l'interface.
        """
        return self.model_class.objects.filter(interface=interface)
    
    def get_by_interface_id(self, interface_id: int) -> QuerySet[Metric]:
        """
        Récupère les métriques d'une interface par son ID.
        
        Args:
            interface_id (int): L'ID de l'interface dont on veut récupérer les métriques.
            
        Returns:
            QuerySet[Metric]: Un QuerySet contenant les métriques de l'interface.
        """
        return self.model_class.objects.filter(interface_id=interface_id)
    
    def get_by_name(self, name: str) -> QuerySet[Metric]:
        """
        Récupère des métriques par nom.
        
        Args:
            name (str): Le nom des métriques.
            
        Returns:
            QuerySet[Metric]: Un QuerySet contenant les métriques avec le nom spécifié.
        """
        return self.model_class.objects.filter(name=name)
    
    def get_by_category(self, category: str) -> QuerySet[Metric]:
        """
        Récupère des métriques par catégorie.
        
        Args:
            category (str): La catégorie des métriques.
            
        Returns:
            QuerySet[Metric]: Un QuerySet contenant les métriques de la catégorie spécifiée.
        """
        return self.model_class.objects.filter(category=category)
    
    def get_by_tag(self, tag: str) -> QuerySet[Metric]:
        """
        Récupère des métriques par tag.
        
        Args:
            tag (str): Le tag à rechercher.
            
        Returns:
            QuerySet[Metric]: Un QuerySet contenant les métriques avec le tag spécifié.
        """
        return self.model_class.objects.filter(tags__contains=[tag])
    
    def get_by_time_range(self, start_time: datetime, end_time: datetime) -> QuerySet[Metric]:
        """
        Récupère des métriques par plage de temps.
        
        Args:
            start_time (datetime): L'heure de début de la plage.
            end_time (datetime): L'heure de fin de la plage.
            
        Returns:
            QuerySet[Metric]: Un QuerySet contenant les métriques dans la plage de temps spécifiée.
        """
        return self.model_class.objects.filter(timestamp__range=(start_time, end_time))
    
    def get_by_device_name_time_range(self, device: NetworkDevice, name: str, start_time: datetime, end_time: datetime) -> QuerySet[Metric]:
        """
        Récupère des métriques d'un équipement par nom et plage de temps.
        
        Args:
            device (NetworkDevice): L'équipement dont on veut récupérer les métriques.
            name (str): Le nom des métriques.
            start_time (datetime): L'heure de début de la plage.
            end_time (datetime): L'heure de fin de la plage.
            
        Returns:
            QuerySet[Metric]: Un QuerySet contenant les métriques de l'équipement avec le nom spécifié dans la plage de temps spécifiée.
        """
        return self.model_class.objects.filter(
            device=device,
            name=name,
            timestamp__range=(start_time, end_time)
        )
    
    def get_by_interface_name_time_range(self, interface: NetworkInterface, name: str, start_time: datetime, end_time: datetime) -> QuerySet[Metric]:
        """
        Récupère des métriques d'une interface par nom et plage de temps.
        
        Args:
            interface (NetworkInterface): L'interface dont on veut récupérer les métriques.
            name (str): Le nom des métriques.
            start_time (datetime): L'heure de début de la plage.
            end_time (datetime): L'heure de fin de la plage.
            
        Returns:
            QuerySet[Metric]: Un QuerySet contenant les métriques de l'interface avec le nom spécifié dans la plage de temps spécifiée.
        """
        return self.model_class.objects.filter(
            interface=interface,
            name=name,
            timestamp__range=(start_time, end_time)
        )
    
    def get_latest_by_device_and_name(self, device: NetworkDevice, name: str) -> Optional[Metric]:
        """
        Récupère la dernière métrique d'un équipement par nom.
        
        Args:
            device (NetworkDevice): L'équipement dont on veut récupérer la métrique.
            name (str): Le nom de la métrique.
            
        Returns:
            Optional[Metric]: La dernière métrique de l'équipement avec le nom spécifié ou None si aucune métrique n'a été trouvée.
        """
        try:
            return self.model_class.objects.filter(device=device, name=name).latest('timestamp')
        except self.model_class.DoesNotExist:
            return None
    
    def get_latest_by_interface_and_name(self, interface: NetworkInterface, name: str) -> Optional[Metric]:
        """
        Récupère la dernière métrique d'une interface par nom.
        
        Args:
            interface (NetworkInterface): L'interface dont on veut récupérer la métrique.
            name (str): Le nom de la métrique.
            
        Returns:
            Optional[Metric]: La dernière métrique de l'interface avec le nom spécifié ou None si aucune métrique n'a été trouvée.
        """
        try:
            return self.model_class.objects.filter(interface=interface, name=name).latest('timestamp')
        except self.model_class.DoesNotExist:
            return None
    
    def get_average_by_device_and_name(self, device: NetworkDevice, name: str, start_time: datetime, end_time: datetime) -> float:
        """
        Calcule la moyenne des valeurs d'une métrique d'un équipement par nom et plage de temps.
        
        Args:
            device (NetworkDevice): L'équipement dont on veut calculer la moyenne des métriques.
            name (str): Le nom de la métrique.
            start_time (datetime): L'heure de début de la plage.
            end_time (datetime): L'heure de fin de la plage.
            
        Returns:
            float: La moyenne des valeurs de la métrique ou 0 si aucune métrique n'a été trouvée.
        """
        result = self.model_class.objects.filter(
            device=device,
            name=name,
            timestamp__range=(start_time, end_time)
        ).aggregate(avg_value=Avg('value'))
        
        return result['avg_value'] or 0.0
    
    def get_max_by_device_and_name(self, device: NetworkDevice, name: str, start_time: datetime, end_time: datetime) -> float:
        """
        Calcule la valeur maximale d'une métrique d'un équipement par nom et plage de temps.
        
        Args:
            device (NetworkDevice): L'équipement dont on veut calculer la valeur maximale des métriques.
            name (str): Le nom de la métrique.
            start_time (datetime): L'heure de début de la plage.
            end_time (datetime): L'heure de fin de la plage.
            
        Returns:
            float: La valeur maximale de la métrique ou 0 si aucune métrique n'a été trouvée.
        """
        result = self.model_class.objects.filter(
            device=device,
            name=name,
            timestamp__range=(start_time, end_time)
        ).aggregate(max_value=Max('value'))
        
        return result['max_value'] or 0.0
    
    def get_min_by_device_and_name(self, device: NetworkDevice, name: str, start_time: datetime, end_time: datetime) -> float:
        """
        Calcule la valeur minimale d'une métrique d'un équipement par nom et plage de temps.
        
        Args:
            device (NetworkDevice): L'équipement dont on veut calculer la valeur minimale des métriques.
            name (str): Le nom de la métrique.
            start_time (datetime): L'heure de début de la plage.
            end_time (datetime): L'heure de fin de la plage.
            
        Returns:
            float: La valeur minimale de la métrique ou 0 si aucune métrique n'a été trouvée.
        """
        result = self.model_class.objects.filter(
            device=device,
            name=name,
            timestamp__range=(start_time, end_time)
        ).aggregate(min_value=Min('value'))
        
        return result['min_value'] or 0.0
    
    def get_sum_by_device_and_name(self, device: NetworkDevice, name: str, start_time: datetime, end_time: datetime) -> float:
        """
        Calcule la somme des valeurs d'une métrique d'un équipement par nom et plage de temps.
        
        Args:
            device (NetworkDevice): L'équipement dont on veut calculer la somme des métriques.
            name (str): Le nom de la métrique.
            start_time (datetime): L'heure de début de la plage.
            end_time (datetime): L'heure de fin de la plage.
            
        Returns:
            float: La somme des valeurs de la métrique ou 0 si aucune métrique n'a été trouvée.
        """
        result = self.model_class.objects.filter(
            device=device,
            name=name,
            timestamp__range=(start_time, end_time)
        ).aggregate(sum_value=Sum('value'))
        
        return result['sum_value'] or 0.0 