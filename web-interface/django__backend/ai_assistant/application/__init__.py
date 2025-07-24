"""
Module application pour l'assistant IA.

Ce module contient les services et cas d'utilisation de l'assistant IA
selon les principes de l'architecture hexagonale.
"""

from .ai_assistant_service import AIAssistantService
from .services import NetworkAnalysisService
from .use_cases import ConversationUseCase, CommandUseCase, KnowledgeUseCase

__all__ = [
    'AIAssistantService',
    'NetworkAnalysisService',
    'ConversationUseCase',
    'CommandUseCase',
    'KnowledgeUseCase'
]
