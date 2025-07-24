"""
Module domain pour l'assistant IA.

Ce module contient les entités, interfaces et exceptions du domaine
selon les principes de l'architecture hexagonale.
"""

from .entities import (
    MessageRole,
    Message,
    Conversation,
    CommandRequest,
    CommandResult,
    KnowledgeDocument,
    AIResponse
)

from .interfaces import (
    AIClient,
    CommandExecutor,
    CommandExecutorInterface,
    KnowledgeBase,
    KnowledgeBaseInterface,
    AIAssistantRepository
)

from .exceptions import (
    AIAssistantException,
    ConversationNotFoundException,
    MessageNotFoundException,
    AIClientException,
    CommandExecutionException,
    CommandValidationException,
    KnowledgeBaseException,
    RepositoryException
)

__all__ = [
    # Entities
    'MessageRole',
    'Message',
    'Conversation',
    'CommandRequest',
    'CommandResult',
    'KnowledgeDocument',
    'AIResponse',
    
    # Interfaces
    'AIClient',
    'CommandExecutor',
    'CommandExecutorInterface',
    'KnowledgeBase',
    'KnowledgeBaseInterface',
    'AIAssistantRepository',
    
    # Exceptions
    'AIAssistantException',
    'ConversationNotFoundException',
    'MessageNotFoundException',
    'AIClientException',
    'CommandExecutionException',
    'CommandValidationException',
    'KnowledgeBaseException',
    'RepositoryException'
] 