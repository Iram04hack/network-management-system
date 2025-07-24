"""
Package d'exceptions pour le domaine de l'assistant IA.

Ce package contient les exceptions spécifiques au domaine de l'assistant IA.
"""

class DomainError(Exception):
    """Exception de base pour toutes les erreurs du domaine."""
    pass


class ValidationError(DomainError):
    """Exception levée lorsqu'une validation échoue."""
    pass


class ConversationNotFoundError(DomainError):
    """Exception levée lorsqu'une conversation n'est pas trouvée."""
    pass


class MessageNotFoundError(DomainError):
    """Exception levée lorsqu'un message n'est pas trouvé."""
    pass


class DocumentNotFoundError(DomainError):
    """Exception levée lorsqu'un document n'est pas trouvé."""
    pass


class AIServiceError(DomainError):
    """Exception levée lorsqu'une erreur se produit dans le service d'IA."""
    pass


class CommandExecutionError(DomainError):
    """Exception levée lorsqu'une erreur se produit lors de l'exécution d'une commande."""
    pass


# Alias pour compatibilité
CommandExecutionException = CommandExecutionError


class SecurityError(DomainError):
    """Exception levée lorsqu'une opération est bloquée pour des raisons de sécurité."""
    pass


class SearchError(DomainError):
    """Exception levée lorsqu'une erreur se produit lors d'une recherche."""
    pass


class NetworkAnalysisError(DomainError):
    """Exception levée lorsqu'une erreur se produit lors d'une analyse réseau."""
    pass


class AIException(Exception):
    """Exception de base pour le module AI Assistant."""
    pass


class AIAssistantException(AIException):
    """Exception de base pour toutes les exceptions de l'assistant IA."""
    
    def __init__(self, message: str, error_type: str = None):
        """
        Initialise l'exception.
        
        Args:
            message: Message d'erreur
            error_type: Type d'erreur pour catégorisation
        """
        self.error_type = error_type
        super().__init__(message)


class AIClientException(AIException):
    """Exception levée lors d'une erreur avec le client AI."""
    
    def __init__(self, message: str, error_type: str = None):
        """
        Initialise l'exception.
        
        Args:
            message: Message d'erreur
            error_type: Type d'erreur pour catégorisation
        """
        self.error_type = error_type
        super().__init__(message)


class CommandExecutionException(AIException):
    """Exception levée lors d'une erreur d'exécution de commande."""
    
    def __init__(self, message: str, error_type: str = None):
        """
        Initialise l'exception.
        
        Args:
            message: Message d'erreur
            error_type: Type d'erreur pour catégorisation
        """
        self.error_type = error_type
        super().__init__(message)


class CommandValidationException(AIException):
    """Exception levée lors d'une erreur de validation de commande."""
    pass


class ConversationNotFoundException(AIException):
    """Exception levée lorsqu'une conversation n'est pas trouvée."""
    pass


class MessageNotFoundException(AIException):
    """Exception levée lorsqu'un message n'est pas trouvé."""
    pass


class RepositoryException(AIException):
    """Exception levée lors d'une erreur du repository."""
    pass


class KnowledgeBaseException(AIException):
    """Exception levée lors d'une erreur avec la base de connaissances."""
    
    def __init__(self, message: str, error_type: str = None):
        """
        Initialise l'exception.
        
        Args:
            message: Message d'erreur
            error_type: Type d'erreur pour catégorisation
        """
        self.error_type = error_type
        super().__init__(message) 