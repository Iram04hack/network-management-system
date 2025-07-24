"""
Exceptions du domaine pour l'assistant IA.

Ce module définit les exceptions spécifiques au domaine de l'assistant IA.
"""

class AIAssistantException(Exception):
    """Exception de base pour le module AI Assistant."""
    
    def __init__(self, message: str, code: str = "error"):
        self.message = message
        self.code = code
        super().__init__(self.message)


class ConversationNotFoundException(AIAssistantException):
    """Exception levée lorsqu'une conversation n'est pas trouvée."""
    
    def __init__(self, conversation_id: str):
        message = f"Conversation non trouvée: {conversation_id}"
        super().__init__(message, "conversation_not_found")


class MessageNotFoundException(AIAssistantException):
    """Exception levée lorsqu'un message n'est pas trouvé."""
    
    def __init__(self, message_id: str):
        message = f"Message non trouvé: {message_id}"
        super().__init__(message, "message_not_found")


class AIClientException(AIAssistantException):
    """Exception levée lors d'erreurs avec le client IA."""
    
    def __init__(self, message: str, client_name: str = "unknown"):
        super().__init__(f"Erreur client IA ({client_name}): {message}", "ai_client_error")
        self.client_name = client_name


class CommandExecutionException(AIAssistantException):
    """Exception levée lors d'erreurs d'exécution de commandes."""
    
    def __init__(self, command: str, error: str):
        message = f"Erreur d'exécution de la commande '{command}': {error}"
        super().__init__(message, "command_execution_error")
        self.command = command
        self.error = error


class CommandValidationException(AIAssistantException):
    """Exception levée lors d'erreurs de validation de commandes."""
    
    def __init__(self, command: str, reason: str):
        message = f"Commande invalide '{command}': {reason}"
        super().__init__(message, "command_validation_error")
        self.command = command
        self.reason = reason


class KnowledgeBaseException(AIAssistantException):
    """Exception levée lors d'erreurs avec la base de connaissances."""
    
    def __init__(self, message: str, operation: str = "unknown"):
        super().__init__(f"Erreur base de connaissances ({operation}): {message}", "knowledge_base_error")
        self.operation = operation


class RepositoryException(AIAssistantException):
    """Exception levée lors d'erreurs avec le repository."""
    
    def __init__(self, message: str, operation: str = "unknown"):
        super().__init__(f"Erreur repository ({operation}): {message}", "repository_error")
        self.operation = operation 