"""
Module contenant le repository pour les topologies.
"""

from typing import List, Optional, Type, Dict, Any

from django.db.models import QuerySet, Q

from ..models import Topology
from .base_repository import BaseRepository


class TopologyRepository(BaseRepository[Topology]):
    """
    Repository pour les topologies.
    
    Cette classe fournit des méthodes pour accéder aux données
    des topologies dans la base de données.
    """
    
    @property
    def model_class(self) -> Type[Topology]:
        """
        Retourne la classe du modèle géré par ce repository.
        
        Returns:
            Type[Topology]: La classe du modèle Topology.
        """
        return Topology
    
    def get_by_name(self, name: str) -> Optional[Topology]:
        """
        Récupère une topologie par son nom.
        
        Args:
            name (str): Le nom de la topologie à récupérer.
            
        Returns:
            Optional[Topology]: La topologie trouvée ou None si aucune topologie n'a été trouvée.
        """
        try:
            return self.model_class.objects.get(name=name)
        except self.model_class.DoesNotExist:
            return None
    
    def search(self, query: str) -> QuerySet[Topology]:
        """
        Recherche des topologies par nom ou description.
        
        Args:
            query (str): Le terme de recherche.
            
        Returns:
            QuerySet[Topology]: Un QuerySet contenant les topologies trouvées.
        """
        return self.model_class.objects.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query)
        )
    
    def get_auto_discovered(self) -> QuerySet[Topology]:
        """
        Récupère les topologies découvertes automatiquement.
        
        Returns:
            QuerySet[Topology]: Un QuerySet contenant les topologies découvertes automatiquement.
        """
        return self.model_class.objects.filter(is_auto_discovered=True)
    
    def get_manual(self) -> QuerySet[Topology]:
        """
        Récupère les topologies créées manuellement.
        
        Returns:
            QuerySet[Topology]: Un QuerySet contenant les topologies créées manuellement.
        """
        return self.model_class.objects.filter(is_auto_discovered=False)
    
    def get_by_tag(self, tag: str) -> QuerySet[Topology]:
        """
        Récupère des topologies par tag.
        
        Args:
            tag (str): Le tag à rechercher.
            
        Returns:
            QuerySet[Topology]: Un QuerySet contenant les topologies avec le tag spécifié.
        """
        return self.model_class.objects.filter(tags__contains=[tag])
    
    def get_by_created_by(self, created_by: str) -> QuerySet[Topology]:
        """
        Récupère des topologies par créateur.
        
        Args:
            created_by (str): Le créateur des topologies.
            
        Returns:
            QuerySet[Topology]: Un QuerySet contenant les topologies créées par le créateur spécifié.
        """
        return self.model_class.objects.filter(created_by=created_by)
    
    def get_containing_device(self, device_id: int) -> QuerySet[Topology]:
        """
        Récupère des topologies contenant un équipement spécifique.
        
        Args:
            device_id (int): L'ID de l'équipement à rechercher.
            
        Returns:
            QuerySet[Topology]: Un QuerySet contenant les topologies qui incluent l'équipement spécifié.
        """
        return self.model_class.objects.filter(devices__contains=[{'id': device_id}])
    
    def get_containing_connection(self, connection_id: int) -> QuerySet[Topology]:
        """
        Récupère des topologies contenant une connexion spécifique.
        
        Args:
            connection_id (int): L'ID de la connexion à rechercher.
            
        Returns:
            QuerySet[Topology]: Un QuerySet contenant les topologies qui incluent la connexion spécifiée.
        """
        return self.model_class.objects.filter(connections__contains=[{'id': connection_id}]) 