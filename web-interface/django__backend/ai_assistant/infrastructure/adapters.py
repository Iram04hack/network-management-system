"""
Adaptateurs pour l'injection de dépendances du module AI Assistant.

Ce module fournit les fonctions d'accès aux services principaux
avec leurs dépendances configurées.
"""

import logging
from typing import Optional

from ..application.ai_assistant_service import AIAssistantService
from ..config.di import get_ai_client, get_repository, get_knowledge_base, get_command_executor

logger = logging.getLogger(__name__)


def get_ai_assistant_service() -> AIAssistantService:
    """
    Crée et configure le service principal de l'assistant IA.
    
    Returns:
        Instance configurée du service AI Assistant
    """
    try:
        # Récupérer les dépendances
        ai_client = get_ai_client()
        repository = get_repository()
        knowledge_base = get_knowledge_base()
        command_executor = get_command_executor()
        
        # Créer le service avec toutes les dépendances
        service = AIAssistantService(
            ai_client=ai_client,
            repository=repository,
            knowledge_base=knowledge_base,
            command_executor=command_executor
        )
        
        logger.info("Service AI Assistant configuré avec intégration GNS3")
        return service
        
    except Exception as e:
        logger.error(f"Erreur lors de la configuration du service AI Assistant: {e}")
        raise