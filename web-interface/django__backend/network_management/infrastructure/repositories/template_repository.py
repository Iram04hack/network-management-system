"""
Module contenant le repository pour les modèles de configuration.
"""

from typing import List, Optional, Type, Dict, Any

from django.db.models import QuerySet, Q

from ..models import ConfigurationTemplate
from .base_repository import BaseRepository


class TemplateRepository(BaseRepository[ConfigurationTemplate]):
    """
    Repository pour les modèles de configuration.
    
    Cette classe fournit des méthodes pour accéder aux données
    des modèles de configuration dans la base de données.
    """
    
    @property
    def model_class(self) -> Type[ConfigurationTemplate]:
        """
        Retourne la classe du modèle géré par ce repository.
        
        Returns:
            Type[ConfigurationTemplate]: La classe du modèle ConfigurationTemplate.
        """
        return ConfigurationTemplate
    
    def get_by_name(self, name: str) -> Optional[ConfigurationTemplate]:
        """
        Récupère un modèle de configuration par son nom.
        
        Args:
            name (str): Le nom du modèle de configuration à récupérer.
            
        Returns:
            Optional[ConfigurationTemplate]: Le modèle de configuration trouvé ou None si aucun modèle n'a été trouvé.
        """
        try:
            return self.model_class.objects.get(name=name)
        except self.model_class.DoesNotExist:
            return None
    
    def search(self, query: str) -> QuerySet[ConfigurationTemplate]:
        """
        Recherche des modèles de configuration par nom, description ou type d'équipement.
        
        Args:
            query (str): Le terme de recherche.
            
        Returns:
            QuerySet[ConfigurationTemplate]: Un QuerySet contenant les modèles de configuration trouvés.
        """
        return self.model_class.objects.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(device_type__icontains=query)
        )
    
    def get_by_device_type(self, device_type: str) -> QuerySet[ConfigurationTemplate]:
        """
        Récupère des modèles de configuration par type d'équipement.
        
        Args:
            device_type (str): Le type d'équipement.
            
        Returns:
            QuerySet[ConfigurationTemplate]: Un QuerySet contenant les modèles de configuration pour le type d'équipement spécifié.
        """
        return self.model_class.objects.filter(device_type=device_type)
    
    def get_by_vendor(self, vendor: str) -> QuerySet[ConfigurationTemplate]:
        """
        Récupère des modèles de configuration par fabricant.
        
        Args:
            vendor (str): Le fabricant des équipements.
            
        Returns:
            QuerySet[ConfigurationTemplate]: Un QuerySet contenant les modèles de configuration pour le fabricant spécifié.
        """
        return self.model_class.objects.filter(vendor=vendor)
    
    def get_by_os_version(self, os_version: str) -> QuerySet[ConfigurationTemplate]:
        """
        Récupère des modèles de configuration par version d'OS.
        
        Args:
            os_version (str): La version d'OS des équipements.
            
        Returns:
            QuerySet[ConfigurationTemplate]: Un QuerySet contenant les modèles de configuration pour la version d'OS spécifiée.
        """
        return self.model_class.objects.filter(os_version=os_version)
    
    def get_by_created_by(self, created_by: str) -> QuerySet[ConfigurationTemplate]:
        """
        Récupère des modèles de configuration par créateur.
        
        Args:
            created_by (str): Le créateur des modèles de configuration.
            
        Returns:
            QuerySet[ConfigurationTemplate]: Un QuerySet contenant les modèles de configuration créés par le créateur spécifié.
        """
        return self.model_class.objects.filter(created_by=created_by)
    
    def get_by_tag(self, tag: str) -> QuerySet[ConfigurationTemplate]:
        """
        Récupère des modèles de configuration par tag.
        
        Args:
            tag (str): Le tag à rechercher.
            
        Returns:
            QuerySet[ConfigurationTemplate]: Un QuerySet contenant les modèles de configuration avec le tag spécifié.
        """
        return self.model_class.objects.filter(tags__contains=[tag])
    
    def get_compatible_with_device(self, device_type: str, vendor: str = None, os_version: str = None) -> QuerySet[ConfigurationTemplate]:
        """
        Récupère des modèles de configuration compatibles avec un équipement.
        
        Args:
            device_type (str): Le type d'équipement.
            vendor (str, optional): Le fabricant de l'équipement. Defaults to None.
            os_version (str, optional): La version d'OS de l'équipement. Defaults to None.
            
        Returns:
            QuerySet[ConfigurationTemplate]: Un QuerySet contenant les modèles de configuration compatibles.
        """
        query = Q(device_type=device_type)
        
        if vendor:
            query &= (Q(vendor='') | Q(vendor=vendor))
        
        if os_version:
            query &= (Q(os_version='') | Q(os_version=os_version))
        
        return self.model_class.objects.filter(query) 