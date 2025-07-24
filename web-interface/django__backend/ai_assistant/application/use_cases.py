"""
Cas d'utilisation de l'application pour l'assistant IA.

Ce module contient les cas d'utilisation de l'assistant IA
qui implémentent les fonctionnalités métier spécifiques.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from ..domain.interfaces import AIClient, CommandExecutor, KnowledgeBase, AIAssistantRepository
from ..domain.entities import Message, Conversation, MessageRole, Document, SearchResult, CommandResult
from ..domain.exceptions import AIClientException, CommandExecutionException, KnowledgeBaseException

logger = logging.getLogger(__name__)


class ConversationUseCase:
    """
    Cas d'utilisation pour la gestion des conversations.
    
    Cette classe implémente les cas d'utilisation liés aux conversations
    entre l'utilisateur et l'assistant IA.
    """
    
    def __init__(self, repository: AIAssistantRepository, ai_client: AIClient):
        """
        Initialise le cas d'utilisation pour les conversations.
        
        Args:
            repository: Repository pour la persistance
            ai_client: Client IA pour générer des réponses
        """
        self.repository = repository
        self.ai_client = ai_client
    
    def create_conversation(self, user_id: str, title: Optional[str] = None) -> Dict[str, Any]:
        """
        Crée une nouvelle conversation.
        
        Args:
            user_id: ID de l'utilisateur
            title: Titre de la conversation (optionnel)
            
        Returns:
            Dictionnaire contenant les informations de la conversation créée
        """
        try:
            # Création d'un titre par défaut si non fourni
            if not title:
                title = f"Nouvelle conversation ({datetime.now().strftime('%Y-%m-%d %H:%M')})"
            
            # Création de la conversation
            conversation = Conversation(
                id=None,
                title=title,
                user_id=user_id,
                messages=[],
                context="assistant IA pour la gestion de réseau",
                metadata={
                    'created_at': datetime.now().isoformat(),
                    'updated_at': datetime.now().isoformat()
                }
            )
            
            # Ajout d'un message système initial
            system_message = Message(
                id=None,
                role=MessageRole.SYSTEM,
                content="Je suis un assistant IA spécialisé dans la gestion de réseaux informatiques. Comment puis-je vous aider aujourd'hui?",
                timestamp=datetime.now()
            )
            conversation.messages.append(system_message)
            
            # Sauvegarde de la conversation
            conversation_id = self.repository.save_conversation(conversation)
            
            return {
                'id': conversation_id,
                'title': title,
                'created_at': conversation.metadata['created_at'],
                'updated_at': conversation.metadata['updated_at']
            }
        except Exception as e:
            logger.exception(f"Erreur lors de la création de la conversation: {e}")
            raise
    
    def get_conversation(self, conversation_id: str) -> Dict[str, Any]:
        """
        Récupère une conversation par son identifiant.
        
        Args:
            conversation_id: ID de la conversation
            
        Returns:
            Dictionnaire contenant les informations de la conversation
        """
        try:
            conversation = self.repository.get_conversation(conversation_id)
            if not conversation:
                raise ValueError(f"Conversation avec ID {conversation_id} non trouvée")
            
            # Conversion des messages en dictionnaires
            messages = []
            for msg in conversation.messages:
                messages.append({
                    'id': msg.id,
                    'role': msg.role.value,
                    'content': msg.content,
                    'timestamp': msg.timestamp.isoformat() if msg.timestamp else None,
                    'metadata': msg.metadata or {}
                })
            
            return {
                'id': conversation.id,
                'title': conversation.title,
                'user_id': conversation.user_id,
                'messages': messages,
                'context': conversation.context,
                'created_at': conversation.metadata.get('created_at', datetime.now().isoformat()),
                'updated_at': conversation.metadata.get('updated_at', datetime.now().isoformat())
            }
        except Exception as e:
            logger.exception(f"Erreur lors de la récupération de la conversation: {e}")
            raise
    
    def delete_conversation(self, conversation_id: str) -> bool:
        """
        Supprime une conversation.
        
        Args:
            conversation_id: ID de la conversation
            
        Returns:
            True si la suppression a réussi, False sinon
        """
        try:
            return self.repository.delete_conversation(conversation_id)
        except Exception as e:
            logger.exception(f"Erreur lors de la suppression de la conversation: {e}")
            return False
    
    def add_message(
        self,
        conversation_id: str,
        content: str,
        role: str = "user",
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Ajoute un message à une conversation et génère une réponse.
        
        Args:
            conversation_id: ID de la conversation
            content: Contenu du message
            role: Rôle du message (user, assistant, system)
            user_id: ID de l'utilisateur (requis si la conversation n'existe pas)
            
        Returns:
            Dictionnaire contenant la réponse générée
        """
        try:
            # Récupération ou création de la conversation
            conversation = self.repository.get_conversation(conversation_id)
            if not conversation:
                if not user_id:
                    raise ValueError("L'ID utilisateur est requis pour créer une nouvelle conversation")
                
                # Création d'une nouvelle conversation
                conversation = Conversation(
                    id=None,
                    title=f"Conversation {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                    user_id=user_id,
                    messages=[],
                    context="assistant IA pour la gestion de réseau",
                    metadata={
                        'created_at': datetime.now().isoformat(),
                        'updated_at': datetime.now().isoformat()
                    }
                )
                conversation_id = self.repository.save_conversation(conversation)
                conversation.id = conversation_id
            
            # Ajout du message utilisateur
            message_role = MessageRole.USER if role == "user" else (
                MessageRole.ASSISTANT if role == "assistant" else MessageRole.SYSTEM
            )
            user_message = Message(
                id=None,
                role=message_role,
                content=content,
                timestamp=datetime.now()
            )
            conversation.messages.append(user_message)
            
            # Mise à jour de la conversation
            conversation.metadata['updated_at'] = datetime.now().isoformat()
            self.repository.save_conversation(conversation)
            
            # Si le message est de l'utilisateur, générer une réponse
            if message_role == MessageRole.USER:
                # Préparation du contexte pour l'IA
                context = []
                if conversation.context:
                    context.append(f"system: {conversation.context}")
                
                # Ajout des messages précédents (limités aux 10 derniers)
                recent_messages = conversation.messages[-11:-1] if len(conversation.messages) > 11 else conversation.messages[:-1]
                for msg in recent_messages:
                    prefix = "user: " if msg.role == MessageRole.USER else (
                        "assistant: " if msg.role == MessageRole.ASSISTANT else "system: "
                    )
                    context.append(f"{prefix}{msg.content}")
                
                # Génération de la réponse
                ai_response = self.ai_client.generate_response(content, context)
                
                # Ajout de la réponse à la conversation
                assistant_message = Message(
                    id=None,
                    role=MessageRole.ASSISTANT,
                    content=ai_response['content'],
                    timestamp=datetime.now(),
                    metadata={
                        'processing_time': ai_response.get('processing_time', 0),
                        'model_info': ai_response.get('model_info', {})
                    }
                )
                conversation.messages.append(assistant_message)
                
                # Mise à jour de la conversation
                conversation.metadata['updated_at'] = datetime.now().isoformat()
                self.repository.save_conversation(conversation)
                
                return {
                    'user_message': {
                        'content': content,
                        'role': message_role.value,
                        'timestamp': user_message.timestamp.isoformat()
                    },
                    'assistant_message': {
                        'content': assistant_message.content,
                        'role': assistant_message.role.value,
                        'timestamp': assistant_message.timestamp.isoformat(),
                        'metadata': assistant_message.metadata
                    }
                }
            
            return {
                'message': {
                    'content': content,
                    'role': message_role.value,
                    'timestamp': user_message.timestamp.isoformat()
                }
            }
        except Exception as e:
            logger.exception(f"Erreur lors de l'ajout du message: {e}")
            raise


class CommandUseCase:
    """
    Cas d'utilisation pour l'exécution de commandes.
    
    Cette classe implémente les cas d'utilisation liés à l'exécution
    de commandes système et réseau.
    """
    
    def __init__(self, command_executor: CommandExecutor, ai_client: AIClient):
        """
        Initialise le cas d'utilisation pour les commandes.
        
        Args:
            command_executor: Exécuteur de commandes
            ai_client: Client IA pour analyser les commandes
        """
        self.command_executor = command_executor
        self.ai_client = ai_client
    
    def execute_command(
        self,
        command: str,
        command_type: str = "shell",
        user_id: str = None,
        analyze_first: bool = True
    ) -> Dict[str, Any]:
        """
        Exécute une commande système.
        
        Args:
            command: Commande à exécuter
            command_type: Type de commande (shell, api, etc.)
            user_id: ID de l'utilisateur
            analyze_first: Si True, analyse la commande avant exécution
            
        Returns:
            Résultat de l'exécution de la commande
        """
        try:
            # Analyse de la commande si demandé
            if analyze_first:
                analysis = self.ai_client.analyze_command(command)
                if not analysis.get('is_valid', False):
                    return {
                        'success': False,
                        'command': command,
                        'error': f"Commande invalide: {analysis.get('reason', 'Non spécifié')}",
                        'safety_level': analysis.get('safety_level', 'unknown'),
                        'intent': analysis.get('intent', 'unknown')
                    }
                
                # Vérification du niveau de sécurité
                if analysis.get('safety_level') == "dangerous":
                    return {
                        'success': False,
                        'command': command,
                        'error': f"Commande dangereuse: {analysis.get('reason', 'Non spécifié')}",
                        'safety_level': "dangerous",
                        'intent': analysis.get('intent', 'unknown')
                    }
            
            # Validation de la commande
            validation = self.command_executor.validate(command, command_type)
            if not validation.get('is_valid', False):
                return {
                    'success': False,
                    'command': command,
                    'error': validation.get('reason', 'Commande invalide'),
                    'validated': False
                }
            
            # Exécution de la commande
            result = self.command_executor.execute(command, command_type, user_id)
            
            return {
                'success': result.get('success', False),
                'command': command,
                'output': result.get('output', ''),
                'error': result.get('error', ''),
                'exit_code': result.get('exit_code', -1),
                'execution_time': result.get('execution_time', 0)
            }
        except CommandExecutionException as e:
            logger.exception(f"Erreur lors de l'exécution de la commande: {e}")
            return {
                'success': False,
                'command': command,
                'error': str(e),
                'exception_type': e.error_type
            }
        except Exception as e:
            logger.exception(f"Erreur inattendue lors de l'exécution de la commande: {e}")
            return {
                'success': False,
                'command': command,
                'error': str(e),
                'exception_type': 'unexpected'
            }
    
    def get_allowed_commands(self) -> List[str]:
        """
        Récupère la liste des commandes autorisées.
        
        Returns:
            Liste des commandes autorisées
        """
        return self.command_executor.get_allowed_commands()


class KnowledgeUseCase:
    """
    Cas d'utilisation pour la gestion de la base de connaissances.
    
    Cette classe implémente les cas d'utilisation liés à la recherche
    et à la gestion des documents dans la base de connaissances.
    """
    
    def __init__(self, knowledge_base: KnowledgeBase):
        """
        Initialise le cas d'utilisation pour la base de connaissances.
        
        Args:
            knowledge_base: Base de connaissances
        """
        self.knowledge_base = knowledge_base
    
    def search(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Recherche des documents dans la base de connaissances.
        
        Args:
            query: Requête de recherche
            limit: Nombre maximum de résultats
            
        Returns:
            Liste des résultats de recherche
        """
        try:
            results = self.knowledge_base.search(query, limit)
            
            # Conversion des résultats en dictionnaires
            formatted_results = []
            for result in results:
                formatted_results.append({
                    'id': result.id,
                    'title': result.title,
                    'content': result.content,
                    'metadata': result.metadata,
                    'score': result.score
                })
            
            return formatted_results
        except KnowledgeBaseException as e:
            logger.exception(f"Erreur lors de la recherche dans la base de connaissances: {e}")
            return []
        except Exception as e:
            logger.exception(f"Erreur inattendue lors de la recherche: {e}")
            return []
    
    def add_document(
        self,
        title: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Ajoute un document à la base de connaissances.
        
        Args:
            title: Titre du document
            content: Contenu du document
            metadata: Métadonnées du document
            
        Returns:
            Informations sur le document ajouté
        """
        try:
            # Création du document
            document = Document(
                title=title,
                content=content,
                metadata=metadata or {}
            )
            
            # Ajout du document à la base de connaissances
            document_id = self.knowledge_base.add_document(document)
            
            return {
                'id': document_id,
                'title': title,
                'content_preview': content[:100] + '...' if len(content) > 100 else content,
                'metadata': metadata or {}
            }
        except KnowledgeBaseException as e:
            logger.exception(f"Erreur lors de l'ajout du document: {e}")
            raise
        except Exception as e:
            logger.exception(f"Erreur inattendue lors de l'ajout du document: {e}")
            raise
    
    def get_document(self, document_id: str) -> Dict[str, Any]:
        """
        Récupère un document par son identifiant.
        
        Args:
            document_id: ID du document
            
        Returns:
            Informations sur le document
        """
        try:
            document = self.knowledge_base.get_document(document_id)
            if not document:
                raise ValueError(f"Document avec ID {document_id} non trouvé")
            
            return {
                'id': document_id,
                'title': document.title,
                'content': document.content,
                'metadata': document.metadata
            }
        except KnowledgeBaseException as e:
            logger.exception(f"Erreur lors de la récupération du document: {e}")
            raise
        except Exception as e:
            logger.exception(f"Erreur inattendue lors de la récupération du document: {e}")
            raise
    
    def update_document(
        self,
        document_id: str,
        title: Optional[str] = None,
        content: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Met à jour un document existant.
        
        Args:
            document_id: ID du document
            title: Nouveau titre (optionnel)
            content: Nouveau contenu (optionnel)
            metadata: Nouvelles métadonnées (optionnel)
            
        Returns:
            Informations sur le document mis à jour
        """
        try:
            # Récupération du document existant
            existing_document = self.knowledge_base.get_document(document_id)
            if not existing_document:
                raise ValueError(f"Document avec ID {document_id} non trouvé")
            
            # Mise à jour des champs
            updated_document = Document(
                title=title if title is not None else existing_document.title,
                content=content if content is not None else existing_document.content,
                metadata=metadata if metadata is not None else existing_document.metadata
            )
            
            # Mise à jour du document
            success = self.knowledge_base.update_document(document_id, updated_document)
            
            if not success:
                raise KnowledgeBaseException("Échec de la mise à jour du document", "update")
            
            return {
                'id': document_id,
                'title': updated_document.title,
                'content_preview': updated_document.content[:100] + '...' if len(updated_document.content) > 100 else updated_document.content,
                'metadata': updated_document.metadata
            }
        except KnowledgeBaseException as e:
            logger.exception(f"Erreur lors de la mise à jour du document: {e}")
            raise
        except Exception as e:
            logger.exception(f"Erreur inattendue lors de la mise à jour du document: {e}")
            raise
    
    def delete_document(self, document_id: str) -> bool:
        """
        Supprime un document de la base de connaissances.
        
        Args:
            document_id: ID du document
            
        Returns:
            True si la suppression a réussi, False sinon
        """
        try:
            return self.knowledge_base.delete_document(document_id)
        except KnowledgeBaseException as e:
            logger.exception(f"Erreur lors de la suppression du document: {e}")
            return False
        except Exception as e:
            logger.exception(f"Erreur inattendue lors de la suppression du document: {e}")
            return False
