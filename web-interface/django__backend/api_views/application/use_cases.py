"""
Cas d'utilisation pour le module API Views.

Ce module implémente des cas d'utilisation génériques pour les vues API
selon les principes de l'architecture hexagonale.
"""

from typing import Dict, Any, List, Optional, TypeVar, Generic
from abc import abstractmethod
import logging
from datetime import datetime, timedelta
from functools import lru_cache
import hashlib
import json

from django.conf import settings
from django.core.cache import cache
from django.utils import timezone

from .base_use_case import BaseUseCase, UseCaseResult, ValidationError
from .validation import ValidationRules
from ..domain.interfaces import (
    DashboardRepository, 
    TopologyDiscoveryRepository, 
    APISearchRepository
)

logger = logging.getLogger(__name__)

# Cache configuration
CACHE_ENABLED = getattr(settings, 'API_VIEWS_CACHE_ENABLED', True)
DEFAULT_CACHE_TIMEOUT = getattr(settings, 'API_VIEWS_CACHE_TIMEOUT', 300)  # 5 minutes
CACHE_PREFIX = 'api_views:'

def get_cache_key(prefix: str, *args, **kwargs) -> str:
    """
    Génère une clé de cache unique basée sur les arguments fournis.
    
    Args:
        prefix: Un préfixe pour la clé de cache
        *args: Arguments positionnels
        **kwargs: Arguments nommés
        
    Returns:
        Une clé de cache unique
    """
    # Convertir tous les arguments en une représentation JSON triée pour la cohérence
    key_parts = [prefix]
    
    if args:
        key_parts.append(json.dumps(args, sort_keys=True))
    
    if kwargs:
        key_parts.append(json.dumps(kwargs, sort_keys=True))
    
    key_str = ':'.join(key_parts)
    
    # Hacher les clés longues pour éviter des problèmes de taille
    if len(key_str) > 250:  # La plupart des caches ont une limite de taille de clé
        return f"{CACHE_PREFIX}{prefix}:{hashlib.md5(key_str.encode()).hexdigest()}"
        
    return f"{CACHE_PREFIX}{key_str}"

def cached_result(timeout=DEFAULT_CACHE_TIMEOUT, key_prefix=None):
    """
    Décorateur pour mettre en cache le résultat d'une méthode.
    
    Args:
        timeout: Durée de vie du cache en secondes
        key_prefix: Préfixe pour la clé de cache
        
    Returns:
        Décorateur
    """
    def decorator(func):
        def wrapper(self, *args, **kwargs):
            if not CACHE_ENABLED:
                return func(self, *args, **kwargs)
                
            # Générer une clé de cache
            prefix = key_prefix or f"{func.__module__}.{func.__name__}"
            cache_key = get_cache_key(prefix, *args, **kwargs)
            
            # Essayer de récupérer du cache
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                logger.debug(f"Cache hit for {cache_key}")
                return cached_value
                
            # Exécuter la fonction et mettre en cache le résultat
            result = func(self, *args, **kwargs)
            cache.set(cache_key, result, timeout)
            logger.debug(f"Cache miss for {cache_key}, stored result")
            
            return result
        return wrapper
    return decorator

# Types génériques
T = TypeVar('T')  # Type d'entité


class CRUDUseCase(BaseUseCase, Generic[T]):
    """
    Cas d'utilisation pour les opérations CRUD.
    
    Cette classe fournit une base pour implémenter des cas d'utilisation
    qui effectuent des opérations CRUD sur des entités.
    """
    
    @abstractmethod
    def get_by_id(self, id: int, user_id: Optional[int] = None) -> UseCaseResult:
        """
        Récupère une entité par son ID.
        
        Args:
            id: ID de l'entité
            user_id: ID de l'utilisateur (pour les autorisations)
            
        Returns:
            Résultat contenant l'entité ou une erreur
        """
        pass
    
    @abstractmethod
    def get_all(
        self, 
        filters: Optional[Dict[str, Any]] = None,
        user_id: Optional[int] = None
    ) -> UseCaseResult:
        """
        Récupère toutes les entités correspondant aux filtres.
        
        Args:
            filters: Filtres à appliquer
            user_id: ID de l'utilisateur (pour les autorisations)
            
        Returns:
            Résultat contenant les entités ou une erreur
        """
        pass
    
    @abstractmethod
    def create(
        self, 
        data: Dict[str, Any],
        user_id: Optional[int] = None
    ) -> UseCaseResult:
        """
        Crée une nouvelle entité.
        
        Args:
            data: Données de l'entité
            user_id: ID de l'utilisateur (pour les autorisations)
            
        Returns:
            Résultat contenant l'entité créée ou une erreur
        """
        pass
    
    @abstractmethod
    def update(
        self, 
        id: int,
        data: Dict[str, Any],
        user_id: Optional[int] = None
    ) -> UseCaseResult:
        """
        Met à jour une entité existante.
        
        Args:
            id: ID de l'entité
            data: Nouvelles données
            user_id: ID de l'utilisateur (pour les autorisations)
            
        Returns:
            Résultat contenant l'entité mise à jour ou une erreur
        """
        pass
    
    @abstractmethod
    def delete(self, id: int, user_id: Optional[int] = None) -> UseCaseResult:
        """
        Supprime une entité.
        
        Args:
            id: ID de l'entité
            user_id: ID de l'utilisateur (pour les autorisations)
            
        Returns:
            Résultat indiquant le succès ou l'échec
        """
        pass
    
    def count(
        self, 
        filters: Optional[Dict[str, Any]] = None,
        user_id: Optional[int] = None
    ) -> UseCaseResult:
        """
        Compte le nombre d'entités correspondant aux filtres.
        
        Args:
            filters: Filtres à appliquer
            user_id: ID de l'utilisateur (pour les autorisations)
            
        Returns:
            Résultat contenant le nombre d'entités ou une erreur
        """
        # Implémentation par défaut qui récupère toutes les entités et les compte
        # Les sous-classes peuvent remplacer cette méthode par une implémentation plus efficace
        result = self.get_all(filters, user_id)
        
        if not result.success:
            return result
        
        return self.success({
            "count": len(result.data),
            "filters": filters or {}
        })


class BatchOperationUseCase(BaseUseCase):
    """
    Cas d'utilisation pour les opérations par lot.
    
    Cette classe fournit une base pour implémenter des cas d'utilisation
    qui effectuent des opérations sur plusieurs entités à la fois.
    """
    
    @abstractmethod
    def batch_create(
        self, 
        items: List[Dict[str, Any]],
        user_id: Optional[int] = None
    ) -> UseCaseResult:
        """
        Crée plusieurs entités en une seule opération.
        
        Args:
            items: Liste des données d'entités à créer
            user_id: ID de l'utilisateur (pour les autorisations)
            
        Returns:
            Résultat contenant les entités créées ou une erreur
        """
        pass
    
    @abstractmethod
    def batch_update(
        self, 
        items: List[Dict[str, Any]],
        user_id: Optional[int] = None
    ) -> UseCaseResult:
        """
        Met à jour plusieurs entités en une seule opération.
        
        Args:
            items: Liste des données d'entités à mettre à jour (doit contenir des IDs)
            user_id: ID de l'utilisateur (pour les autorisations)
            
        Returns:
            Résultat contenant les entités mises à jour ou une erreur
        """
        pass
    
    @abstractmethod
    def batch_delete(
        self, 
        ids: List[int],
        user_id: Optional[int] = None
    ) -> UseCaseResult:
        """
        Supprime plusieurs entités en une seule opération.
        
        Args:
            ids: Liste des IDs d'entités à supprimer
            user_id: ID de l'utilisateur (pour les autorisations)
            
        Returns:
            Résultat indiquant le succès ou l'échec
        """
        pass


class SearchUseCase(BaseUseCase):
    """
    Cas d'utilisation pour les opérations de recherche.
    
    Cette classe fournit une base pour implémenter des cas d'utilisation
    qui effectuent des recherches avancées sur des entités.
    """
    
    @abstractmethod
    def search(
        self, 
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        page: int = 1,
        page_size: int = 20,
        user_id: Optional[int] = None
    ) -> UseCaseResult:
        """
        Effectue une recherche sur les entités.
        
        Args:
            query: Requête de recherche
            filters: Filtres additionnels
            page: Numéro de page
            page_size: Taille de la page
            user_id: ID de l'utilisateur (pour les autorisations)
            
        Returns:
            Résultat contenant les entités trouvées ou une erreur
        """
        pass
    
    @abstractmethod
    def suggest(
        self, 
        query: str,
        limit: int = 5,
        user_id: Optional[int] = None
    ) -> UseCaseResult:
        """
        Suggère des entités correspondant à la requête.
        
        Args:
            query: Requête de suggestion
            limit: Nombre maximum de suggestions
            user_id: ID de l'utilisateur (pour les autorisations)
            
        Returns:
            Résultat contenant les suggestions ou une erreur
        """
        pass


class GetDashboardDataUseCase:
    """
    Cas d'utilisation pour récupérer les données d'un tableau de bord.
    """
    
    def __init__(self, dashboard_repository: DashboardRepository):
        self.dashboard_repository = dashboard_repository
        
        # Règles de validation
        self.validation = ValidationRules({
            'dashboard_type': {
                'required': True,
                'type': str,
                'choices': ['system-overview', 'network-status', 'security', 'monitoring', 'custom']
            },
            'time_range': {
                'required': False,
                'type': str,
                'default': '24h',
                'choices': ['1h', '6h', '12h', '24h', '7d', '30d', 'custom']
            },
            'start_date': {
                'required': False,
                'type': datetime,
                'conditional': lambda data: data.get('time_range') == 'custom'
            },
            'end_date': {
                'required': False,
                'type': datetime,
                'conditional': lambda data: data.get('time_range') == 'custom'
            }
        })
    
    @cached_result(timeout=60, key_prefix="dashboard_data")
    def execute(self, dashboard_type: str, user_id: Optional[int] = None,
                time_range: Optional[str] = '24h', start_date: Optional[datetime] = None,
                end_date: Optional[datetime] = None, **kwargs) -> Dict[str, Any]:
        """
        Récupère les données d'un tableau de bord.
        
        Args:
            dashboard_type: Type de tableau de bord
            user_id: ID de l'utilisateur (optionnel)
            time_range: Plage de temps ('1h', '6h', '12h', '24h', '7d', '30d', 'custom')
            start_date: Date de début (pour plage de temps 'custom')
            end_date: Date de fin (pour plage de temps 'custom')
            **kwargs: Arguments supplémentaires
            
        Returns:
            Données du tableau de bord
        """
        # Valider les entrées
        data = {
            'dashboard_type': dashboard_type,
            'time_range': time_range,
            'start_date': start_date,
            'end_date': end_date
        }
        self.validation.validate(data)
        
        # Convertir la plage de temps en filtres pour le repository
        filters = self._time_range_to_filters(time_range, start_date, end_date)
        
        # Récupérer les données
        return self.dashboard_repository.get_dashboard_data(dashboard_type, user_id, filters)
        
    def _time_range_to_filters(self, time_range: str, start_date: Optional[datetime] = None,
                            end_date: Optional[datetime] = None) -> Dict[str, Any]:
        """
        Convertit une plage de temps en filtres pour le repository.
        
        Args:
            time_range: Plage de temps ('1h', '6h', '12h', '24h', '7d', '30d', 'custom')
            start_date: Date de début (pour plage de temps 'custom')
            end_date: Date de fin (pour plage de temps 'custom')
            
        Returns:
            Filtres pour le repository
        """
        now = timezone.now()
        filters = {}
        
        if time_range == 'custom':
            if start_date and end_date:
                filters['start_date'] = start_date
                filters['end_date'] = end_date
        else:
            # Convertir la plage de temps en delta
            delta_mapping = {
                '1h': timedelta(hours=1),
                '6h': timedelta(hours=6),
                '12h': timedelta(hours=12),
                '24h': timedelta(days=1),
                '7d': timedelta(days=7),
                '30d': timedelta(days=30)
            }
            delta = delta_mapping.get(time_range, timedelta(days=1))
            
            filters['start_date'] = now - delta
            filters['end_date'] = now
            
        return filters


class SaveDashboardConfigurationUseCase:
    """
    Cas d'utilisation pour sauvegarder la configuration d'un tableau de bord.
    """
    
    def __init__(self, dashboard_repository: DashboardRepository):
        self.dashboard_repository = dashboard_repository
    
    def execute(self, dashboard_type: str, configuration: Dict[str, Any],
               user_id: Optional[int] = None) -> bool:
        """
        Sauvegarde la configuration d'un tableau de bord.
        
        Args:
            dashboard_type: Type de tableau de bord
            configuration: Configuration à sauvegarder
            user_id: ID de l'utilisateur (optionnel)
            
        Returns:
            True si la sauvegarde a réussi
            
        Raises:
            APIValidationException: Si la configuration est invalide
            DashboardException: Si une erreur se produit lors de la sauvegarde
        """
        # Validation de la configuration
        errors = {}
        if not configuration:
            errors["configuration"] = "La configuration ne peut pas être vide"
        
        if errors:
            raise APIValidationException("DashboardConfiguration", errors=errors)
            
        # Invalidation du cache pour ce tableau de bord
        cache_key = get_cache_key("dashboard_data", dashboard_type, user_id)
        cache.delete(cache_key)
        
        try:
            return self.dashboard_repository.save_dashboard_configuration(
                dashboard_type, configuration, user_id
            )
        except Exception as e:
            raise DashboardException(
                dashboard_type=dashboard_type,
                message=f"Erreur lors de la sauvegarde de la configuration: {str(e)}",
                details={"configuration_size": len(str(configuration))}
            )


class GetNetworkTopologyUseCase:
    """
    Cas d'utilisation pour récupérer la topologie d'un réseau.
    """
    
    def __init__(self, topology_repository: TopologyDiscoveryRepository):
        self.topology_repository = topology_repository
    
    @cached_result(timeout=300, key_prefix="network_topology")
    def execute(self, network_id: Optional[str] = None,
               filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Récupère la topologie d'un réseau.
        
        Args:
            network_id: ID du réseau (optionnel)
            filters: Filtres supplémentaires (optionnel)
            
        Returns:
            Topologie du réseau
            
        Raises:
            TopologyDiscoveryException: Si une erreur se produit lors de la récupération
            ResourceNotFoundException: Si le réseau n'existe pas
        """
        try:
            topology = self.topology_repository.get_network_topology(network_id, filters)
            
            if not topology:
                raise ResourceNotFoundException("Réseau", network_id)
                
            return topology
        except ResourceNotFoundException:
            raise
        except Exception as e:
            raise TopologyDiscoveryException(
                message=f"Erreur lors de la récupération de la topologie: {str(e)}",
                details={"network_id": network_id}
            )


class StartTopologyDiscoveryUseCase:
    """
    Cas d'utilisation pour démarrer une découverte de topologie.
    """
    
    def __init__(self, topology_repository: TopologyDiscoveryRepository):
        self.topology_repository = topology_repository
    
    def execute(self, network_id: str, discovery_params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Démarre une découverte de topologie.
        
        Args:
            network_id: ID du réseau
            discovery_params: Paramètres de la découverte
            
        Returns:
            Informations sur la découverte démarrée
            
        Raises:
            APIValidationException: Si les paramètres sont invalides
            TopologyDiscoveryException: Si une erreur se produit lors de la découverte
        """
        # Validation des paramètres
        errors = {}
        if not network_id:
            errors["network_id"] = "L'ID du réseau est requis"
        
        if not discovery_params.get("ip_range"):
            errors["ip_range"] = "La plage d'adresses IP est requise"
            
        if errors:
            raise APIValidationException("DiscoveryParams", errors=errors)
            
        # Invalider le cache de topologie pour ce réseau
        cache_key = get_cache_key("network_topology", network_id)
        cache.delete(cache_key)
        
        try:
            return self.topology_repository.start_discovery(network_id, discovery_params)
        except Exception as e:
            raise TopologyDiscoveryException(
                message=f"Erreur lors du démarrage de la découverte: {str(e)}",
                details={"network_id": network_id}
            )


class SearchResourcesUseCase:
    """
    Cas d'utilisation pour rechercher des ressources.
    """
    
    def __init__(self, search_repository: APISearchRepository):
        self.search_repository = search_repository
    
    def execute(self, query: str, resource_types: List[str] = None,
               filters: Optional[Dict[str, Any]] = None,
               pagination: Optional[Dict[str, int]] = None) -> Dict[str, Any]:
        """
        Effectue une recherche dans les ressources.
        
        Args:
            query: Requête de recherche
            resource_types: Types de ressources à rechercher (optionnel)
            filters: Filtres supplémentaires (optionnel)
            pagination: Paramètres de pagination (optionnel)
            
        Returns:
            Résultats de la recherche
            
        Raises:
            InvalidSearchQueryException: Si la requête est invalide
        """
        # Validation de la requête
        errors = {}
        if not query or len(query) < 3:
            errors["query"] = "La requête doit contenir au moins 3 caractères"
            
        if errors:
            raise InvalidSearchQueryException(errors=errors)
            
        # Utiliser tous les types de ressources si non spécifiés
        resource_types = resource_types or ["devices", "networks", "alerts", "logs"]
        
        return self.search_repository.search(query, resource_types, filters, pagination)


class GetResourceDetailsUseCase:
    """
    Cas d'utilisation pour récupérer les détails d'une ressource.
    """
    
    def __init__(self, search_repository: APISearchRepository):
        self.search_repository = search_repository
    
    @cached_result(timeout=120, key_prefix="resource_details")
    def execute(self, resource_type: str, resource_id: str) -> Dict[str, Any]:
        """
        Récupère les détails d'une ressource.
        
        Args:
            resource_type: Type de ressource
            resource_id: ID de la ressource
            
        Returns:
            Détails de la ressource
            
        Raises:
            ResourceNotFoundException: Si la ressource n'existe pas
        """
        try:
            details = self.search_repository.get_resource_details(resource_type, resource_id)
            
            if not details:
                raise ResourceNotFoundException(resource_type, resource_id)
                
            return details
        except Exception as e:
            if isinstance(e, ResourceNotFoundException):
                raise
            raise ResourceNotFoundException(
                resource_type,
                resource_id,
                message=f"Erreur lors de la récupération de {resource_type} {resource_id}: {str(e)}"
            ) 