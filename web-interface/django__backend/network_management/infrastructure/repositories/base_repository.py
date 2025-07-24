"""
Module contenant la classe de base pour les repositories.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, TypeVar, Generic, Type

from django.db.models import Model, QuerySet

T = TypeVar('T', bound=Model)


class BaseRepository(Generic[T], ABC):
    """
    Classe de base pour tous les repositories.
    
    Cette classe définit l'interface commune à tous les repositories
    et fournit des implémentations par défaut pour les opérations CRUD.
    """
    
    @property
    @abstractmethod
    def model_class(self) -> Type[T]:
        """
        Retourne la classe du modèle géré par ce repository.
        
        Returns:
            Type[T]: La classe du modèle.
        """
        pass
    
    def get_all(self) -> QuerySet[T]:
        """
        Récupère tous les objets du modèle.
        
        Returns:
            QuerySet[T]: Un QuerySet contenant tous les objets.
        """
        return self.model_class.objects.all()
    
    def get_by_id(self, id: int) -> Optional[T]:
        """
        Récupère un objet par son ID.
        
        Args:
            id (int): L'ID de l'objet à récupérer.
            
        Returns:
            Optional[T]: L'objet trouvé ou None si aucun objet n'a été trouvé.
        """
        try:
            return self.model_class.objects.get(pk=id)
        except self.model_class.DoesNotExist:
            return None
    
    def get_by_ids(self, ids: List[int]) -> QuerySet[T]:
        """
        Récupère des objets par leurs IDs.
        
        Args:
            ids (List[int]): Liste des IDs des objets à récupérer.
            
        Returns:
            QuerySet[T]: Un QuerySet contenant les objets trouvés.
        """
        return self.model_class.objects.filter(pk__in=ids)
    
    def filter(self, **kwargs) -> QuerySet[T]:
        """
        Filtre les objets selon les critères spécifiés.
        
        Args:
            **kwargs: Les critères de filtrage.
            
        Returns:
            QuerySet[T]: Un QuerySet contenant les objets filtrés.
        """
        return self.model_class.objects.filter(**kwargs)
    
    def create(self, **kwargs) -> T:
        """
        Crée un nouvel objet.
        
        Args:
            **kwargs: Les attributs de l'objet à créer.
            
        Returns:
            T: L'objet créé.
        """
        return self.model_class.objects.create(**kwargs)
    
    def update(self, instance: T, **kwargs) -> T:
        """
        Met à jour un objet existant.
        
        Args:
            instance (T): L'objet à mettre à jour.
            **kwargs: Les attributs à mettre à jour.
            
        Returns:
            T: L'objet mis à jour.
        """
        for key, value in kwargs.items():
            setattr(instance, key, value)
        instance.save()
        return instance
    
    def delete(self, instance: T) -> None:
        """
        Supprime un objet.
        
        Args:
            instance (T): L'objet à supprimer.
        """
        instance.delete()
    
    def delete_by_id(self, id: int) -> bool:
        """
        Supprime un objet par son ID.
        
        Args:
            id (int): L'ID de l'objet à supprimer.
            
        Returns:
            bool: True si l'objet a été supprimé, False sinon.
        """
        try:
            instance = self.model_class.objects.get(pk=id)
            instance.delete()
            return True
        except self.model_class.DoesNotExist:
            return False
    
    def count(self, **kwargs) -> int:
        """
        Compte le nombre d'objets correspondant aux critères spécifiés.
        
        Args:
            **kwargs: Les critères de filtrage.
            
        Returns:
            int: Le nombre d'objets.
        """
        return self.model_class.objects.filter(**kwargs).count()
    
    def exists(self, **kwargs) -> bool:
        """
        Vérifie si des objets correspondant aux critères spécifiés existent.
        
        Args:
            **kwargs: Les critères de filtrage.
            
        Returns:
            bool: True si des objets existent, False sinon.
        """
        return self.model_class.objects.filter(**kwargs).exists() 