"""
Signaux pour l'API de l'assistant IA.

Ce module contient les signaux Django pour l'API de l'assistant IA.
"""

import logging
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth import get_user_model

from ai_assistant.domain.models import Conversation, Message, Document
from ai_assistant.domain.services import SearchService

logger = logging.getLogger(__name__)
User = get_user_model()


@receiver(post_save, sender=Message)
def index_message(sender, instance, created, **kwargs):
    """
    Indexe un message dans le moteur de recherche lorsqu'il est créé ou mis à jour.
    
    Args:
        sender: Modèle qui a envoyé le signal
        instance: Instance du modèle qui a été sauvegardée
        created: Booléen indiquant si l'instance a été créée
        **kwargs: Arguments supplémentaires
    """
    try:
        if created and instance.role == 'assistant':
            # Indexer uniquement les messages de l'assistant
            search_service = SearchService()
            search_service.index_message(instance)
            logger.debug(f"Message {instance.id} indexé avec succès")
    except Exception as e:
        logger.error(f"Erreur lors de l'indexation du message {instance.id}: {str(e)}")


@receiver(post_save, sender=Document)
def index_document(sender, instance, created, **kwargs):
    """
    Indexe un document dans le moteur de recherche lorsqu'il est créé ou mis à jour.
    
    Args:
        sender: Modèle qui a envoyé le signal
        instance: Instance du modèle qui a été sauvegardée
        created: Booléen indiquant si l'instance a été créée
        **kwargs: Arguments supplémentaires
    """
    try:
        search_service = SearchService()
        search_service.index_document(instance)
        logger.debug(f"Document {instance.id} indexé avec succès")
    except Exception as e:
        logger.error(f"Erreur lors de l'indexation du document {instance.id}: {str(e)}")


@receiver(post_delete, sender=Document)
def remove_document_from_index(sender, instance, **kwargs):
    """
    Supprime un document du moteur de recherche lorsqu'il est supprimé.
    
    Args:
        sender: Modèle qui a envoyé le signal
        instance: Instance du modèle qui a été supprimée
        **kwargs: Arguments supplémentaires
    """
    try:
        search_service = SearchService()
        search_service.remove_document_from_index(instance.id)
        logger.debug(f"Document {instance.id} supprimé de l'index avec succès")
    except Exception as e:
        logger.error(f"Erreur lors de la suppression du document {instance.id} de l'index: {str(e)}")


@receiver(post_delete, sender=Conversation)
def cleanup_conversation_resources(sender, instance, **kwargs):
    """
    Nettoie les ressources associées à une conversation lorsqu'elle est supprimée.
    
    Args:
        sender: Modèle qui a envoyé le signal
        instance: Instance du modèle qui a été supprimée
        **kwargs: Arguments supplémentaires
    """
    try:
        # Supprimer les messages de l'index de recherche
        search_service = SearchService()
        for message in instance.messages:
            if message.role == 'assistant':
                search_service.remove_message_from_index(message.id)
        
        logger.debug(f"Ressources de la conversation {instance.id} nettoyées avec succès")
    except Exception as e:
        logger.error(f"Erreur lors du nettoyage des ressources de la conversation {instance.id}: {str(e)}")


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Crée un profil utilisateur lorsqu'un nouvel utilisateur est créé.
    
    Args:
        sender: Modèle qui a envoyé le signal
        instance: Instance du modèle qui a été sauvegardée
        created: Booléen indiquant si l'instance a été créée
        **kwargs: Arguments supplémentaires
    """
    if created:
        try:
            # Créer une conversation de bienvenue pour le nouvel utilisateur
            from ai_assistant.domain.services import ConversationService, AIService
            
            conversation_service = ConversationService()
            ai_service = AIService()
            
            # Créer une nouvelle conversation
            conversation = conversation_service.create_conversation(
                user_id=str(instance.id),
                title="Bienvenue sur l'Assistant IA"
            )
            
            # Ajouter un message de bienvenue
            conversation_service.add_message(
                conversation_id=conversation.id,
                role="assistant",
                content=(
                    f"Bonjour {instance.username} ! Je suis votre assistant IA pour la gestion de réseau. "
                    "Je peux vous aider à analyser votre réseau, exécuter des commandes, rechercher des informations "
                    "et bien plus encore. N'hésitez pas à me poser des questions ou à me demander de l'aide pour "
                    "n'importe quelle tâche liée à la gestion de réseau."
                )
            )
            
            logger.debug(f"Profil et conversation de bienvenue créés pour l'utilisateur {instance.id}")
        except Exception as e:
            logger.error(f"Erreur lors de la création du profil utilisateur {instance.id}: {str(e)}") 