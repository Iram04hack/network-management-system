"""
Implémentation des repositories avec Django.

Ce module contient les implémentations des interfaces de repository
utilisant Django ORM pour la persistance des données.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from ..domain.interfaces import AIAssistantRepository
from ..domain.entities import Conversation, Message, UserPreference
from ..models import Conversation as ConversationModel
from ..models import Message as MessageModel
from ..models import UserPreference as UserPreferenceModel

logger = logging.getLogger(__name__)


class DjangoAIAssistantRepository(AIAssistantRepository):
    """
    Implémentation du repository AIAssistant avec Django ORM.
    
    Cette classe fournit une implémentation concrète de l'interface AIAssistantRepository,
    utilisant Django ORM pour la persistance des données.
    """
    
    def create_conversation(
        self,
        title: Optional[str] = None,
        user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Crée une nouvelle conversation.
        
        Args:
            title: Titre de la conversation
            user_id: ID de l'utilisateur
            
        Returns:
            Conversation créée
        """
        try:
            # Création d'une nouvelle conversation
            conv_model = ConversationModel()
            
            # Mise à jour des champs
            conv_model.title = title or f"Conversation {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            conv_model.user_id = user_id
            conv_model.context = ""
            conv_model.metadata = {}
            
            # Sauvegarde
            conv_model.save()
            
            return {
                "id": conv_model.id,
                "title": conv_model.title,
                "user_id": conv_model.user_id,
                "context": conv_model.context,
                "metadata": conv_model.metadata,
                "created_at": conv_model.created_at.isoformat(),
                "updated_at": conv_model.updated_at.isoformat()
            }
        except Exception as e:
            logger.exception(f"Erreur lors de la création de la conversation: {e}")
            raise
    
    def get_conversation(self, conversation_id: int) -> Optional[Dict[str, Any]]:
        """
        Récupère une conversation par son identifiant.
        
        Args:
            conversation_id: L'identifiant de la conversation
            
        Returns:
            La conversation ou None si elle n'existe pas
        """
        try:
            # Récupération de la conversation
            conv_model = ConversationModel.objects.filter(id=conversation_id).first()
            if not conv_model:
                return None
                        
            # Conversion en dictionnaire
            conversation = {
                "id": conv_model.id,
                "title": conv_model.title,
                "user_id": conv_model.user_id,
                "context": conv_model.context,
                "metadata": conv_model.metadata,
                "created_at": conv_model.created_at.isoformat(),
                "updated_at": conv_model.updated_at.isoformat()
            }
            
            return conversation
        except Exception as e:
            logger.exception(f"Erreur lors de la récupération de la conversation: {e}")
            return None
    
    def get_user_conversations(self, user_id: int) -> List[Dict[str, Any]]:
        """
        Récupère toutes les conversations d'un utilisateur.
        
        Args:
            user_id: ID de l'utilisateur
            
        Returns:
            Liste des conversations
        """
        try:
            # Récupération des conversations de l'utilisateur
            conv_models = ConversationModel.objects.filter(user_id=user_id).order_by('-updated_at')
            
            # Conversion des conversations
            conversations = []
            for conv_model in conv_models:
                conversation = {
                    "id": conv_model.id,
                    "title": conv_model.title,
                    "user_id": conv_model.user_id,
                    "context": conv_model.context,
                    "metadata": conv_model.metadata,
                    "created_at": conv_model.created_at.isoformat(),
                    "updated_at": conv_model.updated_at.isoformat(),
                    "message_count": MessageModel.objects.filter(conversation=conv_model).count()
                }
                conversations.append(conversation)
            
            return conversations
        except Exception as e:
            logger.exception(f"Erreur lors de la récupération des conversations de l'utilisateur: {e}")
            return []
    
    def update_conversation(
        self,
        conversation_id: int,
        title: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Met à jour une conversation.
        
        Args:
            conversation_id: ID de la conversation
            title: Nouveau titre (optionnel)
            metadata: Nouvelles métadonnées (optionnel)
            
        Returns:
            Conversation mise à jour
        """
        try:
            # Récupération de la conversation
            conv_model = ConversationModel.objects.filter(id=conversation_id).first()
            if not conv_model:
                logger.warning(f"Conversation avec ID {conversation_id} non trouvée lors de la mise à jour")
                return {}
            
            # Mise à jour des champs
            if title is not None:
                conv_model.title = title
                
            if metadata is not None:
                conv_model.metadata = {**conv_model.metadata, **metadata}
            
            # Sauvegarde
            conv_model.save()
            
            return {
                "id": conv_model.id,
                "title": conv_model.title,
                "user_id": conv_model.user_id,
                "context": conv_model.context,
                "metadata": conv_model.metadata,
                "created_at": conv_model.created_at.isoformat(),
                "updated_at": conv_model.updated_at.isoformat()
            }
        except Exception as e:
            logger.exception(f"Erreur lors de la mise à jour de la conversation: {e}")
            return {}
    
    def delete_conversation(self, conversation_id: int) -> bool:
        """
        Supprime une conversation de la base de données.
        
        Args:
            conversation_id: L'identifiant de la conversation à supprimer
            
        Returns:
            True si la suppression a réussi, False sinon
        """
        try:
            # Récupération de la conversation
            conv_model = ConversationModel.objects.filter(id=conversation_id).first()
            if not conv_model:
                logger.warning(f"Conversation avec ID {conversation_id} non trouvée lors de la suppression")
                return False
            
            # Suppression des messages associés
            MessageModel.objects.filter(conversation=conv_model).delete()
            
            # Suppression de la conversation
            conv_model.delete()
            
            return True
        except Exception as e:
            logger.exception(f"Erreur lors de la suppression de la conversation: {e}")
            return False
    
    def add_message(
        self,
        conversation_id: int,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Ajoute un message à une conversation.
        
        Args:
            conversation_id: ID de la conversation
            role: Rôle du message (user, assistant, system)
            content: Contenu du message
            metadata: Métadonnées du message (optionnel)
            
        Returns:
            Message ajouté
        """
        try:
            # Récupération de la conversation
            conv_model = ConversationModel.objects.filter(id=conversation_id).first()
            if not conv_model:
                logger.warning(f"Conversation avec ID {conversation_id} non trouvée lors de l'ajout du message")
                return {}
            
            # Création du message
            msg_model = MessageModel()
            msg_model.conversation = conv_model
            msg_model.content = content
            msg_model.role = role
            msg_model.timestamp = datetime.now()
            msg_model.metadata = metadata or {}
            
            # Sauvegarde
            msg_model.save()
            
            # Mise à jour de la date de mise à jour de la conversation
            conv_model.updated_at = datetime.now()
            conv_model.save()
            
            return {
                "id": msg_model.id,
                "conversation_id": conversation_id,
                "content": msg_model.content,
                "role": msg_model.role,
                "timestamp": msg_model.timestamp.isoformat(),
                "metadata": msg_model.metadata
            }
        except Exception as e:
            logger.exception(f"Erreur lors de l'ajout du message: {e}")
            return {}
            
    def get_conversation_messages(
        self,
        conversation_id: int,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Récupère les messages d'une conversation.
        
        Args:
            conversation_id: ID de la conversation
            limit: Nombre maximum de messages à récupérer
            offset: Index de départ
            
        Returns:
            Liste des messages
        """
        try:
            # Récupération des messages
            msg_models = MessageModel.objects.filter(conversation_id=conversation_id).order_by('timestamp')[offset:offset+limit]
            
            # Conversion des messages
            messages = []
            for msg_model in msg_models:
                message = {
                    "id": msg_model.id,
                    "conversation_id": conversation_id,
                    "content": msg_model.content,
                    "role": msg_model.role,
                    "timestamp": msg_model.timestamp.isoformat(),
                    "metadata": msg_model.metadata
                }
                messages.append(message)
            
            return messages
        except Exception as e:
            logger.exception(f"Erreur lors de la récupération des messages: {e}")
            return []
    
    def delete_message(self, message_id: int) -> bool:
        """
        Supprime un message.
        
        Args:
            message_id: ID du message
            
        Returns:
            True si la suppression a réussi, False sinon
        """
        try:
            # Récupération du message
            msg_model = MessageModel.objects.filter(id=message_id).first()
            if not msg_model:
                logger.warning(f"Message avec ID {message_id} non trouvé lors de la suppression")
                return False
            
            # Suppression du message
            msg_model.delete()
            
            return True
        except Exception as e:
            logger.exception(f"Erreur lors de la suppression du message: {e}")
            return False
    
    def save_user_preference(self, preference: UserPreference) -> str:
        """
        Sauvegarde une préférence utilisateur dans la base de données.
        
        Args:
            preference: La préférence à sauvegarder
            
        Returns:
            L'identifiant de la préférence sauvegardée
        """
        try:
            # Création ou mise à jour de la préférence
            if preference.id:
                pref_model = UserPreferenceModel.objects.filter(id=preference.id).first()
                if not pref_model:
                    logger.warning(f"Préférence avec ID {preference.id} non trouvée, création d'une nouvelle")
                    pref_model = UserPreferenceModel()
            else:
                # Vérification si une préférence existe déjà pour cette clé et cet utilisateur
                pref_model = UserPreferenceModel.objects.filter(
                    user_id=preference.user_id,
                    key=preference.key
                ).first() or UserPreferenceModel()
            
            # Mise à jour des champs
            pref_model.user_id = preference.user_id
            pref_model.key = preference.key
            pref_model.value = preference.value
            
            # Sauvegarde
            pref_model.save()
            
            return str(pref_model.id)
        except Exception as e:
            logger.exception(f"Erreur lors de la sauvegarde de la préférence utilisateur: {e}")
            raise
    
    def get_user_preference(self, user_id: str, key: str) -> Optional[UserPreference]:
        """
        Récupère une préférence utilisateur par sa clé.
        
        Args:
            user_id: L'identifiant de l'utilisateur
            key: La clé de la préférence
            
        Returns:
            La préférence ou None si elle n'existe pas
        """
        try:
            # Récupération de la préférence
            pref_model = UserPreferenceModel.objects.filter(user_id=user_id, key=key).first()
            if not pref_model:
                return None
            
            # Conversion en objet UserPreference
            preference = UserPreference(
                id=str(pref_model.id),
                user_id=pref_model.user_id,
                key=pref_model.key,
                value=pref_model.value
            )
            
            return preference
        except Exception as e:
            logger.exception(f"Erreur lors de la récupération de la préférence utilisateur: {e}")
            return None
    
    def get_all_user_preferences(self, user_id: str) -> List[UserPreference]:
        """
        Récupère toutes les préférences d'un utilisateur.
        
        Args:
            user_id: L'identifiant de l'utilisateur
            
        Returns:
            Liste des préférences de l'utilisateur
        """
        try:
            # Récupération des préférences de l'utilisateur
            pref_models = UserPreferenceModel.objects.filter(user_id=user_id)
            
            # Conversion en objets UserPreference
            preferences = []
            for pref_model in pref_models:
                preference = UserPreference(
                    id=str(pref_model.id),
                    user_id=pref_model.user_id,
                    key=pref_model.key,
                    value=pref_model.value
                )
                preferences.append(preference)
            
            return preferences
        except Exception as e:
            logger.exception(f"Erreur lors de la récupération des préférences utilisateur: {e}")
            return []
    
    def delete_user_preference(self, user_id: str, key: str) -> bool:
        """
        Supprime une préférence utilisateur de la base de données.
        
        Args:
            user_id: L'identifiant de l'utilisateur
            key: La clé de la préférence à supprimer
            
        Returns:
            True si la suppression a réussi, False sinon
        """
        try:
            # Récupération de la préférence
            pref_model = UserPreferenceModel.objects.filter(user_id=user_id, key=key).first()
            if not pref_model:
                logger.warning(f"Préférence avec clé {key} pour l'utilisateur {user_id} non trouvée lors de la suppression")
                return False
            
            # Suppression
            pref_model.delete()
            return True
        except Exception as e:
            logger.exception(f"Erreur lors de la suppression de la préférence utilisateur: {e}")
            return False
