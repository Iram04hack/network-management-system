"""
Exceptions du domaine pour le module API Views.

Ce module définit les exceptions spécifiques au domaine
des vues API selon les principes de l'architecture hexagonale.
"""


class APIViewException(Exception):
    """Exception de base pour le module API Views."""
    
    def __init__(self, message: str = "Une erreur s'est produite dans les vues API"):
        self.message = message
        super().__init__(self.message)


# Alias pour compatibilité
APIViewsDomainException = APIViewException


class ValidationException(APIViewException):
    """Exception levée lors d'une erreur de validation."""
    
    def __init__(self, message: str = "Erreur de validation dans les vues API", errors=None):
        self.errors = errors or []
        super().__init__(message)


class ResourceNotFoundException(APIViewException):
    """Exception levée lorsqu'une ressource n'est pas trouvée."""
    
    def __init__(self, resource_id=None, resource_type=None, message=None):
        self.resource_id = resource_id
        self.resource_type = resource_type
        
        if message:
            self.message = message
        elif resource_id and resource_type:
            self.message = f"{resource_type} avec ID {resource_id} non trouvé(e)"
        elif resource_type:
            self.message = f"{resource_type} non trouvé(e)"
        else:
            self.message = "Ressource non trouvée"
            
        super().__init__(self.message)


class AuthorizationException(APIViewException):
    """Exception levée lorsqu'un utilisateur n'est pas autorisé."""
    
    def __init__(self, message: str = "Non autorisé à accéder à cette ressource"):
        super().__init__(message)


class RepositoryException(APIViewException):
    """Exception levée lors d'une erreur dans le repository."""
    
    def __init__(self, message: str = "Erreur dans le repository"):
        super().__init__(message)


class BusinessRuleException(APIViewException):
    """Exception levée lors d'une violation de règle métier."""
    
    def __init__(self, message: str = "Violation d'une règle métier"):
        super().__init__(message)


class ConflictException(APIViewException):
    """Exception levée lors d'un conflit (ex: ressource déjà existante)."""
    
    def __init__(self, message: str = "Conflit avec une ressource existante"):
        super().__init__(message)


class BadRequestException(APIViewException):
    """Exception levée lors d'une requête invalide."""
    
    def __init__(self, message: str = "Requête invalide"):
        super().__init__(message)


class ServiceUnavailableException(APIViewException):
    """Exception levée lorsqu'un service externe est indisponible."""
    
    def __init__(self, service_name=None, message=None):
        self.service_name = service_name
        
        if message:
            self.message = message
        elif service_name:
            self.message = f"Service {service_name} indisponible"
        else:
            self.message = "Service indisponible"
            
        super().__init__(self.message)


# Exceptions spécialisées pour les différents contextes

class SearchException(APIViewException):
    """Exception levée lors d'une erreur de recherche."""

    def __init__(self, message: str = "Erreur lors de la recherche", details=None):
        self.details = details or {}
        super().__init__(message)


class InvalidSearchQueryException(ValidationException):
    """Exception levée lors d'une requête de recherche invalide."""

    def __init__(self, query=None, message=None):
        self.query = query
        if message:
            super().__init__(message)
        elif query:
            super().__init__(f"Requête de recherche invalide : {query}")
        else:
            super().__init__("Requête de recherche invalide")


class APIValidationException(ValidationException):
    """Exception levée lors d'une erreur de validation API."""
    pass


class APIOperationException(APIViewException):
    """Exception levée lors d'une erreur d'opération API."""
    pass


class TopologyDiscoveryException(APIViewException):
    """Exception levée lors d'une erreur de découverte de topologie."""
    
    def __init__(self, message: str = "Erreur lors de la découverte de topologie", details=None):
        self.details = details or {}
        super().__init__(message)


class DashboardException(APIViewException):
    """Exception levée lors d'une erreur de dashboard."""
    
    def __init__(self, message: str = "Erreur dans le dashboard", details=None):
        self.details = details or {}
        super().__init__(message) 