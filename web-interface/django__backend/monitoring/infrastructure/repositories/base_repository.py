"""
Base repository implémentant les opérations CRUD de base pour tous les repositories.
"""

import logging
from typing import List, Dict, Any, TypeVar, Generic, Type, Optional

from django.db import models
from django.db.models import Q

# Type variable pour le modèle Django
T = TypeVar('T', bound=models.Model)

# Configuration du logger
logger = logging.getLogger(__name__)


class BaseRepository(Generic[T]):
    """
    Classe de base pour tous les repositories.
    
    Attributes:
        model_class: Classe du modèle Django utilisé par ce repository
    """
    
    def __init__(self, model_class: Type[T]):
        """
        Initialise le repository avec la classe de modèle.
        
        Args:
            model_class: Classe du modèle Django utilisé par ce repository
        """
        self.model_class = model_class
    
    def get_by_id(self, id: int) -> Optional[T]:
        """
        Récupère une entité par son ID.
        
        Args:
            id: ID de l'entité à récupérer
            
        Returns:
            L'entité si elle existe, None sinon
        """
        try:
            return self.model_class.objects.get(id=id)
        except self.model_class.DoesNotExist:
            logger.warning(f"{self.model_class.__name__} avec ID {id} n'existe pas")
            return None
    
    def get_all(self) -> List[T]:
        """
        Récupère toutes les entités.
        
        Returns:
            Liste de toutes les entités
        """
        return list(self.model_class.objects.all())
    
    def filter(self, **kwargs) -> List[T]:
        """
        Filtre les entités selon les critères donnés.
        
        Args:
            **kwargs: Critères de filtrage
            
        Returns:
            Liste des entités filtrées
        """
        return list(self.model_class.objects.filter(**kwargs))
    
    def filter_by_query(self, query: Q) -> List[T]:
        """
        Filtre les entités selon une requête Q.
        
        Args:
            query: Requête Q Django
            
        Returns:
            Liste des entités filtrées
        """
        return list(self.model_class.objects.filter(query))
    
    def create(self, **kwargs) -> T:
        """
        Crée une nouvelle entité.
        
        Args:
            **kwargs: Attributs de l'entité à créer
            
        Returns:
            L'entité créée
        """
        return self.model_class.objects.create(**kwargs)
    
    def update(self, entity: T, **kwargs) -> T:
        """
        Met à jour une entité existante.
        
        Args:
            entity: Entité à mettre à jour
            **kwargs: Attributs à mettre à jour
            
        Returns:
            L'entité mise à jour
        """
        for key, value in kwargs.items():
            setattr(entity, key, value)
        entity.save()
        return entity
    
    def delete(self, entity: T) -> bool:
        """
        Supprime une entité.
        
        Args:
            entity: Entité à supprimer
            
        Returns:
            True si la suppression a réussi, False sinon
        """
        try:
            entity.delete()
            return True
        except Exception as e:
            logger.error(f"Erreur lors de la suppression de {self.model_class.__name__}: {e}")
            return False
    
    def delete_by_id(self, id: int) -> bool:
        """
        Supprime une entité par son ID.
        
        Args:
            id: ID de l'entité à supprimer
            
        Returns:
            True si la suppression a réussi, False sinon
        """
        entity = self.get_by_id(id)
        if entity:
            return self.delete(entity)
        return False
    
    def count(self, **kwargs) -> int:
        """
        Compte le nombre d'entités correspondant aux critères.
        
        Args:
            **kwargs: Critères de filtrage
            
        Returns:
            Nombre d'entités
        """
        return self.model_class.objects.filter(**kwargs).count() 