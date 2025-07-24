"""
Classe de base pour les vues API.

Ce module fournit une classe de base pour les vues API qui implémente
l'architecture hexagonale et utilise le framework de validation standardisé.
"""

from typing import Dict, Any, Type, Optional, List, Callable
import logging

from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.request import Request

from ..application.base_use_case import BaseUseCase, UseCaseResult
from ..application.validation import StandardValidator

logger = logging.getLogger(__name__)


class BaseAPIView(viewsets.ViewSet):
    """
    Classe de base pour les vues API suivant l'architecture hexagonale.
    
    Cette classe implémente le pattern Adapter de l'architecture hexagonale
    pour connecter les requêtes HTTP aux cas d'utilisation de l'application.
    """
    
    # Cas d'utilisation à injecter dans les sous-classes
    use_case_class: Optional[Type[BaseUseCase]] = None
    
    # Validateur à utiliser pour les requêtes
    validator: Optional[StandardValidator] = None
    
    def __init__(self, **kwargs):
        """
        Initialise la vue API.
        
        Args:
            **kwargs: Arguments supplémentaires
        """
        super().__init__(**kwargs)
        
        # Initialiser le cas d'utilisation si une classe est définie
        self.use_case = None
        if self.use_case_class:
            self.use_case = self.use_case_class()
    
    def handle_use_case_result(self, result: UseCaseResult) -> Response:
        """
        Convertit le résultat d'un cas d'utilisation en réponse HTTP.
        
        Args:
            result: Résultat du cas d'utilisation
            
        Returns:
            Réponse HTTP correspondante
        """
        # Gérer les erreurs de validation
        if not result.success and result.validation_errors:
            errors = {error.field: error.message for error in result.validation_errors}
            return Response(
                {"errors": errors, "detail": "Validation error"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Gérer les erreurs génériques
        if not result.success:
            return Response(
                {"error": result.error_message or "An error occurred"},
                status=result.status_code or status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        # Renvoyer les données en cas de succès
        return Response(
            result.data,
            status=result.status_code or status.HTTP_200_OK
        )
    
    def validate_request(self, data: Dict[str, Any]) -> Optional[Response]:
        """
        Valide les données de la requête.
        
        Args:
            data: Données à valider
            
        Returns:
            Réponse d'erreur en cas d'échec de validation, None sinon
        """
        if not self.validator:
            return None
        
        validation_result = self.validator.validate(data)
        
        if not validation_result.is_valid:
            errors = {error.field: error.message for error in validation_result.errors}
            return Response(
                {"errors": errors, "detail": "Validation error"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return None
    
    def execute_use_case(self, method_name: str, **kwargs) -> Response:
        """
        Exécute un cas d'utilisation et renvoie la réponse HTTP correspondante.
        
        Args:
            method_name: Nom de la méthode du cas d'utilisation à exécuter
            **kwargs: Arguments à passer au cas d'utilisation
            
        Returns:
            Réponse HTTP
        """
        if not self.use_case:
            return Response(
                {"error": "Use case not configured"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        try:
            # Vérifier si la méthode existe
            if not hasattr(self.use_case, method_name):
                return Response(
                    {"error": f"Method {method_name} not found in use case"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            # Exécuter le cas d'utilisation
            method = getattr(self.use_case, method_name)
            result = method(**kwargs)
            
            # Convertir le résultat en réponse HTTP
            return self.handle_use_case_result(result)
        except Exception as e:
            logger.exception(f"Error executing use case {method_name}: {e}")
            return Response(
                {"error": f"Internal server error: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class CRUDAPIView(BaseAPIView, viewsets.ModelViewSet):
    """
    Vue API pour les opérations CRUD suivant l'architecture hexagonale.
    
    Cette classe étend la classe de base pour fournir des fonctionnalités
    CRUD standard tout en suivant l'architecture hexagonale.
    """
    
    # Méthodes du cas d'utilisation à appeler pour chaque opération
    create_method: str = "create"
    retrieve_method: str = "get_by_id"
    update_method: str = "update"
    destroy_method: str = "delete"
    list_method: str = "get_all"
    
    def create(self, request: Request, *args, **kwargs) -> Response:
        """
        Crée une nouvelle ressource.
        
        Args:
            request: Requête HTTP
            
        Returns:
            Réponse HTTP
        """
        # Valider les données
        validation_error = self.validate_request(request.data)
        if validation_error:
            return validation_error
        
        # Exécuter le cas d'utilisation
        return self.execute_use_case(
            self.create_method,
            data=request.data,
            user_id=request.user.id if hasattr(request, "user") else None
        )
    
    def retrieve(self, request: Request, pk=None, *args, **kwargs) -> Response:
        """
        Récupère une ressource par son ID.
        
        Args:
            request: Requête HTTP
            pk: ID de la ressource
            
        Returns:
            Réponse HTTP
        """
        return self.execute_use_case(
            self.retrieve_method,
            id=pk,
            user_id=request.user.id if hasattr(request, "user") else None
        )
    
    def update(self, request: Request, pk=None, *args, **kwargs) -> Response:
        """
        Met à jour une ressource par son ID.
        
        Args:
            request: Requête HTTP
            pk: ID de la ressource
            
        Returns:
            Réponse HTTP
        """
        # Valider les données
        validation_error = self.validate_request(request.data)
        if validation_error:
            return validation_error
        
        # Exécuter le cas d'utilisation
        return self.execute_use_case(
            self.update_method,
            id=pk,
            data=request.data,
            user_id=request.user.id if hasattr(request, "user") else None
        )
    
    def destroy(self, request: Request, pk=None, *args, **kwargs) -> Response:
        """
        Supprime une ressource par son ID.
        
        Args:
            request: Requête HTTP
            pk: ID de la ressource
            
        Returns:
            Réponse HTTP
        """
        return self.execute_use_case(
            self.destroy_method,
            id=pk,
            user_id=request.user.id if hasattr(request, "user") else None
        )
    
    def list(self, request: Request, *args, **kwargs) -> Response:
        """
        Liste toutes les ressources.
        
        Args:
            request: Requête HTTP
            
        Returns:
            Réponse HTTP
        """
        filters = {}
        for param, value in request.query_params.items():
            filters[param] = value
            
        return self.execute_use_case(
            self.list_method,
            filters=filters,
            user_id=request.user.id if hasattr(request, "user") else None
        )
    
    @action(detail=False, methods=["get"])
    def count(self, request: Request, *args, **kwargs) -> Response:
        """
        Compte le nombre de ressources.
        
        Args:
            request: Requête HTTP
            
        Returns:
            Réponse HTTP
        """
        filters = {}
        for param, value in request.query_params.items():
            filters[param] = value
            
        return self.execute_use_case(
            "count",
            filters=filters,
            user_id=request.user.id if hasattr(request, "user") else None
        ) 