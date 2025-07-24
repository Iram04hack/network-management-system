"""
Interfaces de base pour les cas d'utilisation.

Ce module définit les interfaces de base pour les cas d'utilisation
selon l'architecture hexagonale.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass
from rest_framework import status


@dataclass
class ValidationError:
    """Erreur de validation."""
    
    field: str
    message: str
    code: str = "invalid"


@dataclass
class ValidationResult:
    """Résultat d'une validation."""
    
    is_valid: bool
    errors: List[ValidationError] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []


class BaseValidator(ABC):
    """Interface de base pour tous les validateurs."""
    
    @abstractmethod
    def validate(self, data: Dict[str, Any]) -> ValidationResult:
        """
        Valide les données d'entrée.
        
        Args:
            data: Données à valider
            
        Returns:
            Résultat de la validation
        """
        pass


@dataclass
class UseCaseResult:
    """Résultat d'un cas d'utilisation."""
    
    success: bool
    data: Optional[Any] = None
    error_message: Optional[str] = None
    validation_errors: List[ValidationError] = None
    status_code: Optional[int] = None
    
    def __post_init__(self):
        if self.validation_errors is None:
            self.validation_errors = []


class BaseUseCase(ABC):
    """
    Interface de base pour tous les cas d'utilisation.
    
    Les cas d'utilisation représentent les actions que l'application peut effectuer.
    Ils encapsulent la logique métier et sont indépendants de l'infrastructure.
    """
    
    def __init__(self):
        """Initialise le cas d'utilisation."""
        self.validator = None
    
    def set_validator(self, validator: BaseValidator) -> None:
        """
        Définit le validateur à utiliser.
        
        Args:
            validator: Validateur à utiliser
        """
        self.validator = validator
    
    def validate(self, data: Dict[str, Any]) -> ValidationResult:
        """
        Valide les données d'entrée.
        
        Args:
            data: Données à valider
            
        Returns:
            Résultat de la validation
        """
        if self.validator:
            return self.validator.validate(data)
        
        # Par défaut, considérer les données comme valides
        return ValidationResult(is_valid=True)
    
    def success(self, data: Any = None, status_code: int = status.HTTP_200_OK) -> UseCaseResult:
        """
        Crée un résultat de succès.
        
        Args:
            data: Données à renvoyer
            status_code: Code de statut HTTP
            
        Returns:
            Résultat du cas d'utilisation
        """
        return UseCaseResult(
            success=True,
            data=data,
            status_code=status_code
        )
    
    def created(self, data: Any = None) -> UseCaseResult:
        """
        Crée un résultat de création réussie.
        
        Args:
            data: Données à renvoyer
            
        Returns:
            Résultat du cas d'utilisation
        """
        return self.success(data, status_code=status.HTTP_201_CREATED)
    
    def failure(
        self, 
        error_message: str, 
        validation_errors: List[ValidationError] = None,
        status_code: int = status.HTTP_400_BAD_REQUEST
    ) -> UseCaseResult:
        """
        Crée un résultat d'échec.
        
        Args:
            error_message: Message d'erreur
            validation_errors: Erreurs de validation
            status_code: Code de statut HTTP
            
        Returns:
            Résultat du cas d'utilisation
        """
        return UseCaseResult(
            success=False,
            error_message=error_message,
            validation_errors=validation_errors or [],
            status_code=status_code
        )
    
    def validation_failure(self, validation_errors: List[ValidationError]) -> UseCaseResult:
        """
        Crée un résultat d'échec de validation.
        
        Args:
            validation_errors: Erreurs de validation
            
        Returns:
            Résultat du cas d'utilisation
        """
        return self.failure(
            error_message="Validation error",
            validation_errors=validation_errors,
            status_code=status.HTTP_400_BAD_REQUEST
        )
    
    def not_found(self, message: str = "Resource not found") -> UseCaseResult:
        """
        Crée un résultat de ressource non trouvée.
        
        Args:
            message: Message d'erreur
            
        Returns:
            Résultat du cas d'utilisation
        """
        return self.failure(
            error_message=message,
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    def server_error(self, message: str = "Internal server error") -> UseCaseResult:
        """
        Crée un résultat d'erreur serveur.
        
        Args:
            message: Message d'erreur
            
        Returns:
            Résultat du cas d'utilisation
        """
        return self.failure(
            error_message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


class BaseInputDTO:
    """
    Classe de base pour les objets de transfert de données d'entrée.
    
    Cette classe peut être étendue pour définir des structures spécifiques
    pour les données d'entrée des cas d'utilisation.
    """
    pass


class BaseOutputDTO:
    """
    Classe de base pour les objets de transfert de données de sortie.
    
    Cette classe peut être étendue pour définir des structures spécifiques
    pour les données de sortie des cas d'utilisation.
    """
    pass 