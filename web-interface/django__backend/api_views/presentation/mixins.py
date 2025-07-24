"""
Mixins pour les vues API du module api_views.

Ce module fournit des mixins réutilisables pour les vues API,
incluant l'injection de dépendances et d'autres fonctionnalités communes.
"""

from typing import Any, Type
import logging
from django.http import JsonResponse
from rest_framework.response import Response
from rest_framework import status

logger = logging.getLogger(__name__)


class DIViewMixin:
    """
    Mixin pour l'injection de dépendances dans les vues.
    
    Permet aux vues d'accéder facilement aux services
    enregistrés dans le conteneur DI.
    """
    
    def resolve(self, service_name: str) -> Any:
        """
        Résout un service depuis le conteneur DI.
        
        Args:
            service_name: Nom du service à résoudre
            
        Returns:
            Instance du service
            
        Raises:
            ValueError: Si le service n'est pas trouvé
        """
        try:
            from api_views.infrastructure.di_container import resolve
            return resolve(service_name)
        except ImportError:
            logger.warning("Conteneur DI non disponible")
            return None
        except ValueError as e:
            logger.error(f"Service '{service_name}' non trouvé: {e}")
            return None
    
    def resolve_use_case(self, use_case_class: Type) -> Any:
        """
        Résout un cas d'usage par sa classe.
        
        Args:
            use_case_class: Classe du cas d'usage
            
        Returns:
            Instance du cas d'usage
        """
        try:
            # Essayer de résoudre depuis le conteneur DI
            service_name = use_case_class.__name__.lower().replace('usecase', '_use_case')
            return self.resolve(service_name)
        except Exception:
            # Fallback: instanciation directe
            try:
                return use_case_class()
            except Exception as e:
                logger.error(f"Impossible d'instancier {use_case_class.__name__}: {e}")
                return None


class ErrorHandlingMixin:
    """
    Mixin pour la gestion d'erreurs standardisée.
    
    Fournit des méthodes pour retourner des réponses d'erreur
    formatées de manière cohérente.
    """
    
    def error_response(self, message: str, code: str = 'error', 
                      status_code: int = status.HTTP_400_BAD_REQUEST,
                      details: dict = None) -> Response:
        """
        Retourne une réponse d'erreur formatée.
        
        Args:
            message: Message d'erreur
            code: Code d'erreur
            status_code: Code de statut HTTP
            details: Détails supplémentaires
            
        Returns:
            Response avec l'erreur formatée
        """
        error_data = {
            'error': {
                'code': code,
                'message': message
            }
        }
        
        if details:
            error_data['error']['details'] = details
        
        return Response(error_data, status=status_code)
    
    def validation_error_response(self, errors: dict) -> Response:
        """
        Retourne une réponse d'erreur de validation.
        
        Args:
            errors: Dictionnaire des erreurs de validation
            
        Returns:
            Response avec les erreurs de validation
        """
        return self.error_response(
            message="Erreurs de validation",
            code="validation_error",
            status_code=status.HTTP_400_BAD_REQUEST,
            details=errors
        )
    
    def not_found_response(self, resource: str = "Ressource") -> Response:
        """
        Retourne une réponse 404.
        
        Args:
            resource: Nom de la ressource non trouvée
            
        Returns:
            Response 404
        """
        return self.error_response(
            message=f"{resource} non trouvée",
            code="not_found",
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    def permission_denied_response(self, message: str = "Accès refusé") -> Response:
        """
        Retourne une réponse 403.
        
        Args:
            message: Message d'erreur
            
        Returns:
            Response 403
        """
        return self.error_response(
            message=message,
            code="permission_denied",
            status_code=status.HTTP_403_FORBIDDEN
        )


class CachingMixin:
    """
    Mixin pour la gestion du cache dans les vues.
    
    Fournit des méthodes pour gérer le cache
    de manière cohérente.
    """
    
    def get_cache_key(self, *args, **kwargs) -> str:
        """
        Génère une clé de cache pour la vue.
        
        Returns:
            Clé de cache unique
        """
        view_name = self.__class__.__name__
        request_path = getattr(self.request, 'path', '')
        query_params = getattr(self.request, 'query_params', {})
        
        # Créer une clé basée sur la vue, le chemin et les paramètres
        key_parts = [view_name, request_path]
        
        if query_params:
            sorted_params = sorted(query_params.items())
            key_parts.extend([f"{k}={v}" for k, v in sorted_params])
        
        return ":".join(key_parts)
    
    def invalidate_cache(self, pattern: str = None) -> None:
        """
        Invalide le cache pour un motif donné.
        
        Args:
            pattern: Motif de clés à invalider
        """
        try:
            from api_views.infrastructure.cache_config import invalidate_cache_pattern
            if pattern:
                invalidate_cache_pattern(pattern)
            else:
                # Invalider le cache de cette vue
                view_pattern = f"{self.__class__.__name__}:*"
                invalidate_cache_pattern(view_pattern)
        except ImportError:
            logger.warning("Système de cache non disponible")


class PaginationMixin:
    """
    Mixin pour la pagination dans les vues.
    
    Fournit des méthodes utilitaires pour la pagination.
    """
    
    def get_paginated_response(self, data: list, total_count: int = None) -> Response:
        """
        Retourne une réponse paginée.
        
        Args:
            data: Données à paginer
            total_count: Nombre total d'éléments
            
        Returns:
            Response paginée
        """
        if hasattr(self, 'paginator') and self.paginator:
            page = self.paginate_queryset(data)
            if page is not None:
                return self.get_paginated_response(page)
        
        # Fallback sans pagination
        response_data = {
            'results': data,
            'count': len(data) if data else 0
        }
        
        if total_count is not None:
            response_data['total_count'] = total_count
        
        return Response(response_data)


class FilterValidationMixin:
    """
    Mixin pour la validation des filtres.
    
    Fournit des méthodes pour valider les paramètres
    de filtrage dans les requêtes.
    """
    
    def validate_filters(self, filters: dict) -> dict:
        """
        Valide et nettoie les filtres.
        
        Args:
            filters: Dictionnaire des filtres
            
        Returns:
            Filtres validés et nettoyés
        """
        validated_filters = {}
        
        for key, value in filters.items():
            # Nettoyer les valeurs vides
            if value is not None and value != '':
                validated_filters[key] = value
        
        return validated_filters
    
    def get_filter_params(self) -> dict:
        """
        Extrait les paramètres de filtrage de la requête.
        
        Returns:
            Dictionnaire des paramètres de filtrage
        """
        query_params = getattr(self.request, 'query_params', {})
        
        # Extraire les paramètres de filtrage (commençant par 'filter[')
        filter_params = {}
        for key, value in query_params.items():
            if key.startswith('filter[') and key.endswith(']'):
                filter_key = key[7:-1]  # Enlever 'filter[' et ']'
                filter_params[filter_key] = value
        
        return self.validate_filters(filter_params)


class APIViewMixin(DIViewMixin, ErrorHandlingMixin, CachingMixin, 
                   PaginationMixin, FilterValidationMixin):
    """
    Mixin principal qui combine tous les autres mixins.
    
    Fournit toutes les fonctionnalités communes
    pour les vues API du module api_views.
    """
    pass
