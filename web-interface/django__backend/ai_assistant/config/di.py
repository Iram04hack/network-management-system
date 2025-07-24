"""
Configuration de l'injection de dépendances pour l'assistant IA.

Ce fichier contient les fonctions de fabrique pour créer les instances
des différentes dépendances de l'assistant IA.
"""

import logging
from typing import Dict, Any

from ai_assistant.config import settings
from ai_assistant.domain.interfaces import AIClient, CommandExecutor, KnowledgeBase, AIAssistantRepository
from ai_assistant.infrastructure.ai_client_impl import DefaultAIClient
from ai_assistant.infrastructure.command_executor_impl import SafeCommandExecutor
from ai_assistant.infrastructure.knowledge_base_impl import ElasticsearchKnowledgeBase
from ai_assistant.infrastructure.repositories import DjangoAIAssistantRepository
from ai_assistant.domain.services.network_analysis_service import NetworkAnalysisService
from ai_assistant.application.use_cases import ConversationUseCase, CommandUseCase, KnowledgeUseCase
from ai_assistant.domain.exceptions import AIClientException, KnowledgeBaseException

logger = logging.getLogger(__name__)


# Instances singleton des dépendances
_ai_client_instance = None
_command_executor_instance = None
_knowledge_base_instance = None
_repository_instance = None
_ai_assistant_service_instance = None
_network_analysis_service_instance = None
_conversation_use_case_instance = None
_command_use_case_instance = None
_knowledge_use_case_instance = None

# Flag pour savoir si la configuration a été validée
_config_validated = False


def validate_configuration():
    """
    Valide la configuration au démarrage.
    Vérifie que les paramètres essentiels sont définis et que les 
    dépendances requises sont disponibles.
    
    Raises:
        Exception: Si la configuration est invalide
    """
    global _config_validated
    
    if _config_validated:
        return
        
    try:
        # Vérification de la configuration IA
        if settings.ENABLE_AI_CLIENT and not settings.DEFAULT_AI_API_KEY:
            if settings.DEFAULT_AI_PROVIDER == 'openai':
                logger.warning("Clé API OpenAI non définie. Définissez AI_API_KEY.")
            elif settings.DEFAULT_AI_PROVIDER == 'anthropic':
                logger.warning("Clé API Anthropic non définie. Définissez AI_API_KEY.")
        
        # Vérification de la configuration Elasticsearch
        if settings.ENABLE_KNOWLEDGE_BASE and settings.KNOWLEDGE_BASE_TYPE == 'elasticsearch':
            if settings.REQUIRE_ELASTICSEARCH:
                try:
                    import elasticsearch
                except ImportError:
                    raise Exception("La bibliothèque Elasticsearch est requise mais n'est pas installée.")
        
        # Vérification des commandes autorisées
        if settings.ENABLE_COMMAND_EXECUTION and settings.ALLOWED_COMMANDS is None:
            logger.warning("Aucune liste de commandes autorisées n'est définie. Par défaut, les commandes sûres seront utilisées.")
        
        _config_validated = True
        logger.info("Configuration d'IA Assistant validée avec succès.")
        
    except Exception as e:
        logger.error(f"Erreur de validation de la configuration: {e}")
        raise


def get_ai_client(model_name: str = None) -> AIClient:
    """
    Récupère l'instance du client IA.
    
    Args:
        model_name: Nom du modèle à utiliser (optionnel)
        
    Returns:
        Instance du client IA
    """
    global _ai_client_instance
    
    if not settings.ENABLE_AI_CLIENT:
        raise AIClientException("Le client IA est désactivé dans la configuration", "configuration")
        
    if _ai_client_instance is None:
        validate_configuration()
        _ai_client_instance = DefaultAIClient(model_name or settings.DEFAULT_AI_MODEL)
    
    return _ai_client_instance


def get_command_executor() -> CommandExecutor:
    """
    Récupère l'instance de l'exécuteur de commandes.
    
    Returns:
        Instance de l'exécuteur de commandes
    """
    global _command_executor_instance
    
    if not settings.ENABLE_COMMAND_EXECUTION:
        raise Exception("L'exécution de commandes est désactivée dans la configuration")
        
    if _command_executor_instance is None:
        validate_configuration()
        timeout = int(settings.COMMAND_TIMEOUT)
        _command_executor_instance = SafeCommandExecutor(
            allowed_commands=settings.ALLOWED_COMMANDS,
            timeout=timeout
        )
    
    return _command_executor_instance


def get_knowledge_base() -> KnowledgeBase:
    """
    Récupère l'instance de la base de connaissances.
    
    Returns:
        Instance de la base de connaissances
    """
    global _knowledge_base_instance
    
    if not settings.ENABLE_KNOWLEDGE_BASE:
        raise KnowledgeBaseException("La base de connaissances est désactivée dans la configuration", "configuration")
        
    if _knowledge_base_instance is None:
        validate_configuration()
        
        if settings.KNOWLEDGE_BASE_TYPE.lower() == 'elasticsearch':
            _knowledge_base_instance = ElasticsearchKnowledgeBase(
                index_name=settings.ELASTICSEARCH_INDEX
            )
        else:
            logger.warning(f"Type de base de connaissances non supporté: {settings.KNOWLEDGE_BASE_TYPE}")
            # Fallback sur Elasticsearch
            _knowledge_base_instance = ElasticsearchKnowledgeBase(
                index_name=settings.ELASTICSEARCH_INDEX
            )
    
    return _knowledge_base_instance


def get_repository() -> AIAssistantRepository:
    """
    Récupère l'instance du repository.
    
    Returns:
        Instance du repository
    """
    global _repository_instance
    if _repository_instance is None:
        _repository_instance = DjangoAIAssistantRepository()
    return _repository_instance


def get_ai_assistant_service():
    """
    Récupère l'instance du service d'assistant IA.
    
    Returns:
        Instance du service d'assistant IA
    """
    global _ai_assistant_service_instance
    if _ai_assistant_service_instance is None:
        # Import ici pour éviter les imports circulaires
        from ai_assistant.application.ai_assistant_service import AIAssistantService
        _ai_assistant_service_instance = AIAssistantService(
            ai_client=get_ai_client(),
            repository=get_repository(),
            knowledge_base=get_knowledge_base(),
            command_executor=get_command_executor()
        )
    return _ai_assistant_service_instance


def get_network_analysis_service() -> NetworkAnalysisService:
    """
    Récupère l'instance du service d'analyse réseau.
    
    Returns:
        Instance du service d'analyse réseau
    """
    global _network_analysis_service_instance
    if _network_analysis_service_instance is None:
        _network_analysis_service_instance = NetworkAnalysisService()
    return _network_analysis_service_instance


def get_conversation_use_case() -> ConversationUseCase:
    """
    Récupère l'instance du cas d'utilisation des conversations.
    
    Returns:
        Instance du cas d'utilisation des conversations
    """
    global _conversation_use_case_instance
    if _conversation_use_case_instance is None:
        _conversation_use_case_instance = ConversationUseCase(
            repository=get_repository(),
            ai_client=get_ai_client()
        )
    return _conversation_use_case_instance


def get_command_use_case() -> CommandUseCase:
    """
    Récupère l'instance du cas d'utilisation des commandes.
    
    Returns:
        Instance du cas d'utilisation des commandes
    """
    global _command_use_case_instance
    if _command_use_case_instance is None:
        _command_use_case_instance = CommandUseCase(
            command_executor=get_command_executor(),
            ai_client=get_ai_client()
        )
    return _command_use_case_instance


def get_knowledge_use_case() -> KnowledgeUseCase:
    """
    Récupère l'instance du cas d'utilisation de la base de connaissances.
    
    Returns:
        Instance du cas d'utilisation de la base de connaissances
    """
    global _knowledge_use_case_instance
    if _knowledge_use_case_instance is None:
        _knowledge_use_case_instance = KnowledgeUseCase(
            knowledge_base=get_knowledge_base()
        )
    return _knowledge_use_case_instance


def reset_dependencies():
    """
    Réinitialise toutes les dépendances.
    Utile pour les tests ou pour forcer le rechargement des instances.
    """
    global _ai_client_instance, _command_executor_instance, _knowledge_base_instance
    global _repository_instance, _ai_assistant_service_instance, _network_analysis_service_instance
    global _conversation_use_case_instance, _command_use_case_instance, _knowledge_use_case_instance
    
    _ai_client_instance = None
    _command_executor_instance = None
    _knowledge_base_instance = None
    _repository_instance = None
    _ai_assistant_service_instance = None
    _network_analysis_service_instance = None
    _conversation_use_case_instance = None
    _command_use_case_instance = None
    _knowledge_use_case_instance = None
    
    logger.info("Dépendances réinitialisées")
