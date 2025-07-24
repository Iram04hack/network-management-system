"""
Service pour gérer l'interaction avec les modèles de langage et l'IA conversationnelle.
"""
import logging
from typing import Dict, Any, List, Optional
from django.conf import settings

from ..domain.services.ai_service import AIService
from ..domain.services.conversation_service import ConversationService
from ..domain.services.search_service import SearchService
from ..infrastructure.repositories import AIAssistantRepository

logger = logging.getLogger(__name__)

class ChatbotService:
    """Service pour gérer les interactions du chatbot avec architecture améliorée"""
    
    def __init__(self):
        """Initialise le service chatbot avec ses dépendances"""
        self.ai_service = AIService()
        self.conversation_service = ConversationService()
        self.search_service = SearchService()
        self.repository = AIAssistantRepository()
    
    def get_answer(self, message: str, conversation_id: Optional[str] = None, 
                   context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Obtient une réponse du modèle de langage
        
        Args:
            message: Le message de l'utilisateur
            conversation_id: Identifiant de la conversation (optionnel)
            context: Contexte supplémentaire pour la requête
            
        Returns:
            La réponse du chatbot avec métadonnées
        """
        try:
            # Récupérer le contexte de la conversation si un ID est fourni
            conversation_context = []
            conv_id = None
            
            if conversation_id:
                try:
                    conv_id = int(conversation_id)
                    messages = self.repository.get_conversation_messages(conv_id, limit=10)
                    conversation_context = [f"{msg['role']}: {msg['content']}" for msg in messages]
                    logger.info(f"Contexte récupéré pour conversation {conversation_id}: {len(conversation_context)} messages")
                except Exception as e:
                    logger.warning(f"Erreur lors de la récupération du contexte: {e}")
            
            # Ajouter le contexte supplémentaire s'il est fourni
            if context and isinstance(context, dict) and 'previous_messages' in context:
                for msg in context['previous_messages']:
                    if 'role' in msg and 'content' in msg:
                        conversation_context.append(f"{msg['role']}: {msg['content']}")
            
            # Enrichir avec la base de connaissances via le service de recherche
            knowledge_results = self.get_knowledge_context(message)
            knowledge_context = []
            for kr in knowledge_results:
                if 'content' in kr:
                    knowledge_context.append(f"system: {kr['content']}")
            
            # Combiner tous les contextes
            full_context = conversation_context + knowledge_context
            
            # Générer la réponse via le service IA
            response_data = self.ai_service.generate_response(
                prompt=message,
                context=full_context,
                conversation_id=conv_id
            )
            
            # Enregistrer le message et la réponse si un ID de conversation est fourni
            if conv_id:
                try:
                    # Enregistrer le message utilisateur
                    self.repository.add_message(
                        conversation_id=conv_id,
                        role="user",
                        content=message
                    )
                    
                    # Enregistrer la réponse de l'assistant
                    self.repository.add_message(
                        conversation_id=conv_id,
                        role="assistant",
                        content=response_data.get('content', ''),
                        metadata={
                            'actions': response_data.get('actions', []),
                            'sources': response_data.get('sources', []),
                            'processing_time': response_data.get('processing_time', 0),
                            'confidence': response_data.get('confidence', 1.0)
                        }
                    )
                    logger.info(f"Messages enregistrés pour conversation {conversation_id}")
                except Exception as e:
                    logger.error(f"Erreur lors de l'enregistrement des messages: {e}")
            
            # Construire la réponse
            return {
                "success": True,
                "message": response_data.get('content', ''),
                "metadata": {
                    "conversation_id": conversation_id,
                    "model_used": response_data.get('model_used', 'default'),
                    "processing_time": response_data.get('processing_time', 0),
                    "confidence": response_data.get('confidence', 1.0),
                    "actions": response_data.get('actions', []),
                    "sources": response_data.get('sources', [])
                }
            }
        except Exception as e:
            logger.error(f"Erreur lors de la génération de réponse: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Je suis désolé, je n'ai pas pu traiter votre demande."
            }
    
    def get_knowledge_context(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """
        Récupère des informations depuis la base de connaissances
        
        Args:
            query: La requête pour la recherche
            max_results: Nombre maximum de résultats
            
        Returns:
            Liste de résultats pertinents
        """
        try:
            # Utiliser le service de recherche pour récupérer le contexte
            search_results = self.search_service.search_documentation(
                query=query,
                limit=max_results
            )
            
            # Transformer les résultats pour le format attendu
            formatted_results = []
            for result in search_results.get('results', []):
                formatted_results.append({
                    "source": result.get('title', 'documentation'),
                    "content": result.get('content', ''),
                    "relevance": result.get('score', 0.0),
                    "category": result.get('category', '')
                })
            
            logger.info(f"Recherche dans la base de connaissances pour '{query}': {len(formatted_results)} résultats")
            return formatted_results
        except Exception as e:
            logger.warning(f"Erreur lors de la recherche dans la base de connaissances: {e}")
            return []
    
    def execute_command(self, command: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Exécute une commande système ou action spécifique
        
        Args:
            command: Nom de la commande
            params: Paramètres de la commande
            
        Returns:
            Résultat de l'exécution
        """
        try:
            from ..domain.services.command_service import CommandService
            
            # Initialiser le service de commandes
            command_service = CommandService()
            
            # Construire la commande complète avec les paramètres
            full_command = command
            if params:
                # Ajouter les paramètres à la commande
                for key, value in params.items():
                    if isinstance(value, str):
                        full_command += f" --{key}={value}"
                    elif isinstance(value, bool) and value:
                        full_command += f" --{key}"
                    elif not isinstance(value, bool):
                        full_command += f" --{key}={value}"
            
            # Déterminer le type de commande
            command_type = params.get('type', 'system')
            
            # Exécuter la commande via le service
            user_id = params.get('user_id')
            result = command_service.execute_command(
                command=full_command,
                command_type=command_type,
                user_id=user_id
            )
            
            # Ajouter des informations supplémentaires au résultat
            result['command_name'] = command
            result['params'] = params
            
            logger.info(f"Commande exécutée: {command} avec résultat: {'succès' if result.get('success') else 'échec'}")
            return result
        except Exception as e:
            logger.error(f"Erreur lors de l'exécution de la commande {command}: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": f"Erreur lors de l'exécution de la commande: {str(e)}",
                "command_name": command,
                "params": params
            }
    
    def create_conversation(self, user_id: int, title: Optional[str] = None) -> Dict[str, Any]:
        """
        Crée une nouvelle conversation
        
        Args:
            user_id: ID de l'utilisateur
            title: Titre de la conversation (optionnel)
            
        Returns:
            Informations de la conversation créée
        """
        try:
            conversation = self.conversation_service.create_conversation(
                user_id=user_id,
                title=title or "Nouvelle conversation"
            )
            
            return {
                "success": True,
                "conversation": {
                    "id": conversation.id,
                    "title": conversation.title,
                    "created_at": conversation.created_at.isoformat(),
                    "user_id": conversation.user_id
                }
            }
        except Exception as e:
            logger.error(f"Erreur lors de la création de conversation: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Erreur lors de la création de la conversation"
            }
    
    def get_conversation_history(self, conversation_id: int) -> Dict[str, Any]:
        """
        Récupère l'historique d'une conversation
        
        Args:
            conversation_id: ID de la conversation
            
        Returns:
            Historique de la conversation
        """
        try:
            conversation = self.conversation_service.get_conversation(conversation_id)
            messages = self.conversation_service.get_conversation_messages(conversation_id)
            
            return {
                "success": True,
                "conversation": {
                    "id": conversation.id,
                    "title": conversation.title,
                    "created_at": conversation.created_at.isoformat(),
                    "updated_at": conversation.updated_at.isoformat(),
                    "user_id": conversation.user_id
                },
                "messages": [
                    {
                        "id": msg.id,
                        "role": msg.role,
                        "content": msg.content,
                        "timestamp": msg.timestamp.isoformat(),
                        "metadata": msg.metadata
                    }
                    for msg in messages
                ]
            }
        except Exception as e:
            logger.error(f"Erreur lors de la récupération de l'historique: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Erreur lors de la récupération de l'historique"
            }