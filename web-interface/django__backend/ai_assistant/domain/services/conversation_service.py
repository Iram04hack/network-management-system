"""
Service de gestion des conversations.

Ce module contient le service pour gérer les conversations entre
l'utilisateur et l'assistant IA.
"""

import uuid
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from django.contrib.auth.models import User

from ai_assistant.models import Conversation as ConversationModel, Message as MessageModel
from ai_assistant.domain.entities import Conversation, Message, MessageRole
from ai_assistant.domain.exceptions import (
    ConversationNotFoundError,
    MessageNotFoundError,
    ValidationError,
)

logger = logging.getLogger(__name__)


class ConversationService:
    """Service pour gérer les conversations avec base de données PostgreSQL."""

    def __init__(self):
        """Initialise le service de conversation."""
        # Utilisation de la base de données PostgreSQL pour le stockage persistant
        pass
    
    def create_conversation(self, user_id: str, title: str = "Nouvelle conversation", context: str = "") -> Conversation:
        """
        Crée une nouvelle conversation dans la base de données PostgreSQL.

        Args:
            user_id: ID de l'utilisateur
            title: Titre de la conversation
            context: Contexte de la conversation

        Returns:
            Conversation: La conversation créée

        Raises:
            ValidationError: Si les données sont invalides
        """
        if not user_id:
            raise ValidationError("L'ID utilisateur est requis")

        if not title:
            title = "Nouvelle conversation"

        try:
            # Récupérer l'utilisateur Django
            user = User.objects.get(id=int(user_id))

            # Créer la conversation dans la base de données
            conversation_model = ConversationModel.objects.create(
                title=title,
                user=user,
                metadata={
                    "context": context,  # Stocker le contexte dans les métadonnées
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat(),
                }
            )

            # Convertir en entité domain
            conversation = self._model_to_entity(conversation_model)

            logger.info(f"Conversation créée en base de données: {conversation.id}")

            return conversation

        except User.DoesNotExist:
            raise ValidationError(f"Utilisateur non trouvé: {user_id}")
        except Exception as e:
            logger.error(f"Erreur lors de la création de conversation: {e}")
            raise ValidationError(f"Erreur lors de la création: {str(e)}")

    def _model_to_entity(self, conversation_model: ConversationModel) -> Conversation:
        """
        Convertit un modèle Django en entité domain.

        Args:
            conversation_model: Modèle Django de conversation

        Returns:
            Conversation: Entité domain
        """
        # Récupérer les messages associés
        messages = []
        for message_model in conversation_model.messages.all().order_by('created_at'):
            # Convertir le rôle string en MessageRole
            role = MessageRole.USER if message_model.role == 'user' else \
                   MessageRole.ASSISTANT if message_model.role == 'assistant' else \
                   MessageRole.SYSTEM

            message = Message(
                id=str(message_model.id),
                role=role,
                content=message_model.content,
                timestamp=message_model.created_at,
                metadata=message_model.metadata or {},
                actions_taken=message_model.actions_taken or []
            )
            messages.append(message)

        conversation = Conversation(
            id=str(conversation_model.id),
            title=conversation_model.title,
            user_id=str(conversation_model.user.id),
            messages=messages,
            metadata=conversation_model.metadata or {}
        )

        # Le contexte est stocké dans les métadonnées, pas comme attribut direct
        return conversation
    
    def get_conversation_by_id(self, conversation_id: str, user_id: str) -> Conversation:
        """
        Récupère une conversation par son ID depuis la base de données.

        Args:
            conversation_id: ID de la conversation
            user_id: ID de l'utilisateur

        Returns:
            Conversation: La conversation trouvée

        Raises:
            ConversationNotFoundError: Si la conversation n'est pas trouvée
        """
        try:
            conversation_model = ConversationModel.objects.get(
                id=int(conversation_id),
                user_id=int(user_id)
            )
            return self._model_to_entity(conversation_model)
        except ConversationModel.DoesNotExist:
            raise ConversationNotFoundError(f"Conversation non trouvée: {conversation_id}")
        except ValueError:
            raise ConversationNotFoundError(f"ID de conversation invalide: {conversation_id}")
    
    def get_conversations_by_user_id(self, user_id: str) -> List[Conversation]:
        """
        Récupère toutes les conversations d'un utilisateur depuis la base de données.

        Args:
            user_id: ID de l'utilisateur

        Returns:
            List[Conversation]: Liste des conversations de l'utilisateur
        """
        try:
            conversation_models = ConversationModel.objects.filter(
                user_id=int(user_id)
            ).order_by('-created_at')

            return [self._model_to_entity(model) for model in conversation_models]
        except ValueError:
            logger.error(f"ID utilisateur invalide: {user_id}")
            return []
    
    def update_conversation(
        self,
        conversation_id: str,
        user_id: str,
        title: Optional[str] = None,
        context: Optional[str] = None
    ) -> Conversation:
        """
        Met à jour une conversation.
        
        Args:
            conversation_id: ID de la conversation
            user_id: ID de l'utilisateur
            title: Nouveau titre de la conversation
            context: Nouveau contexte de la conversation
            
        Returns:
            Conversation: La conversation mise à jour
            
        Raises:
            ConversationNotFoundError: Si la conversation n'est pas trouvée
            ValidationError: Si les données sont invalides
        """
        conversation = self.get_conversation_by_id(conversation_id, user_id)
        
        if title is not None:
            conversation.title = title
        
        if context is not None:
            conversation.metadata["context"] = context
        
        conversation.metadata["updated_at"] = datetime.now().isoformat()
        
        logger.info(f"Conversation mise à jour: {conversation_id}")
        
        return conversation
    
    def delete_conversation(self, conversation_id: str, user_id: str) -> None:
        """
        Supprime une conversation de la base de données.

        Args:
            conversation_id: ID de la conversation
            user_id: ID de l'utilisateur

        Raises:
            ConversationNotFoundError: Si la conversation n'est pas trouvée
        """
        try:
            conversation_model = ConversationModel.objects.get(
                id=int(conversation_id),
                user_id=int(user_id)
            )
            conversation_model.delete()
            logger.info(f"Conversation supprimée de la base de données: {conversation_id}")
        except ConversationModel.DoesNotExist:
            raise ConversationNotFoundError(f"Conversation non trouvée: {conversation_id}")
        except ValueError:
            raise ConversationNotFoundError(f"ID de conversation invalide: {conversation_id}")
    
    def add_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Message:
        """
        Ajoute un message à une conversation dans la base de données.

        Args:
            conversation_id: ID de la conversation
            role: Rôle de l'émetteur du message (user ou assistant)
            content: Contenu du message
            metadata: Métadonnées du message

        Returns:
            Message: Le message ajouté

        Raises:
            ConversationNotFoundError: Si la conversation n'est pas trouvée
            ValidationError: Si les données sont invalides
        """
        if role not in ["user", "assistant", "system"]:
            raise ValidationError(f"Rôle invalide: {role}")

        if not content:
            raise ValidationError("Le contenu du message est requis")

        try:
            # Récupérer la conversation depuis la base de données
            conversation_model = ConversationModel.objects.get(id=int(conversation_id))

            # Créer le message dans la base de données
            message_model = MessageModel.objects.create(
                conversation=conversation_model,
                role=role,
                content=content,
                metadata=metadata or {},
                actions_taken=[]
            )

            # Mettre à jour les métadonnées de la conversation
            conversation_model.metadata = conversation_model.metadata or {}
            conversation_model.metadata["updated_at"] = datetime.now().isoformat()
            conversation_model.metadata["message_count"] = conversation_model.messages.count()
            conversation_model.save()

            # Convertir en entité domain
            role = MessageRole.USER if message_model.role == 'user' else \
                   MessageRole.ASSISTANT if message_model.role == 'assistant' else \
                   MessageRole.SYSTEM

            message = Message(
                id=str(message_model.id),
                role=role,
                content=message_model.content,
                timestamp=message_model.created_at,
                metadata=message_model.metadata or {},
                actions_taken=message_model.actions_taken or []
            )

            logger.info(f"Message ajouté à la conversation {conversation_id}: {message.id}")

            return message

        except ConversationModel.DoesNotExist:
            raise ConversationNotFoundError(f"Conversation non trouvée: {conversation_id}")
        except ValueError:
            raise ConversationNotFoundError(f"ID de conversation invalide: {conversation_id}")
    
    def get_message_by_id(self, conversation_id: str, message_id: str, user_id: str) -> Message:
        """
        Récupère un message par son ID.
        
        Args:
            conversation_id: ID de la conversation
            message_id: ID du message
            user_id: ID de l'utilisateur
            
        Returns:
            Message: Le message trouvé
            
        Raises:
            ConversationNotFoundError: Si la conversation n'est pas trouvée
            MessageNotFoundError: Si le message n'est pas trouvé
        """
        conversation = self.get_conversation_by_id(conversation_id, user_id)
        
        for message in conversation.messages:
            if message.id == message_id:
                return message
        
        raise MessageNotFoundError(f"Message non trouvé: {message_id}")
    
    def get_conversation_history(self, conversation_id: str, user_id: str, max_messages: int = 10) -> List[Message]:
        """
        Récupère l'historique des messages d'une conversation.
        
        Args:
            conversation_id: ID de la conversation
            user_id: ID de l'utilisateur
            max_messages: Nombre maximum de messages à récupérer
            
        Returns:
            List[Message]: Liste des messages de la conversation
            
        Raises:
            ConversationNotFoundError: Si la conversation n'est pas trouvée
        """
        conversation = self.get_conversation_by_id(conversation_id, user_id)
        
        # Récupérer les derniers messages
        return conversation.messages[-max_messages:] if conversation.messages else [] 