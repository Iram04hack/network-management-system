"""
Vues API pour la gestion des conversations.

Ce module contient les vues API pour créer, lire, mettre à jour et supprimer
des conversations, ainsi que pour envoyer des messages dans une conversation.
"""

import time
import logging
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from ai_assistant.api.serializers import (
    ConversationSerializer,
    MessageRequestSerializer,
    MessageResponseSerializer,
    ErrorResponseSerializer,
)
from ai_assistant.domain.services import ConversationService, AIService
from ai_assistant.domain.exceptions import (
    ConversationNotFoundError,
    AIServiceError,
    ValidationError,
)

logger = logging.getLogger(__name__)


class ConversationListView(APIView):
    """Vue pour lister et créer des conversations."""
    
    permission_classes = [IsAuthenticated]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.conversation_service = ConversationService()
    
    def get(self, request):
        """
        Liste toutes les conversations de l'utilisateur.
        
        Args:
            request: Requête HTTP
            
        Returns:
            Response: Réponse HTTP contenant la liste des conversations
        """
        try:
            user_id = str(request.user.id)
            conversations = self.conversation_service.get_conversations_by_user_id(user_id)
            
            # Sérialiser les conversations
            serializer = ConversationSerializer(conversations, many=True)
            
            return Response(serializer.data)
        
        except Exception as e:
            logger.exception("Erreur lors de la récupération des conversations")
            error_serializer = ErrorResponseSerializer({
                'error': str(e),
                'error_type': e.__class__.__name__,
                'status_code': 500
            })
            return Response(error_serializer.data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def post(self, request):
        """
        Crée une nouvelle conversation.
        
        Args:
            request: Requête HTTP
            
        Returns:
            Response: Réponse HTTP contenant la conversation créée
        """
        try:
            user_id = str(request.user.id)
            title = request.data.get('title', 'Nouvelle conversation')
            context = request.data.get('context', '')
            
            # Créer la conversation
            conversation = self.conversation_service.create_conversation(
                user_id=user_id,
                title=title,
                context=context
            )
            
            # Sérialiser la conversation
            serializer = ConversationSerializer(conversation)
            
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        except ValidationError as e:
            logger.warning(f"Erreur de validation: {str(e)}")
            error_serializer = ErrorResponseSerializer({
                'error': str(e),
                'error_type': 'ValidationError',
                'status_code': 400
            })
            return Response(error_serializer.data, status=status.HTTP_400_BAD_REQUEST)
        
        except Exception as e:
            logger.exception("Erreur lors de la création d'une conversation")
            error_serializer = ErrorResponseSerializer({
                'error': str(e),
                'error_type': e.__class__.__name__,
                'status_code': 500
            })
            return Response(error_serializer.data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ConversationDetailView(APIView):
    """Vue pour récupérer, mettre à jour et supprimer une conversation."""
    
    permission_classes = [IsAuthenticated]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.conversation_service = ConversationService()
    
    def get(self, request, conversation_id):
        """
        Récupère une conversation par son ID.
        
        Args:
            request: Requête HTTP
            conversation_id: ID de la conversation
            
        Returns:
            Response: Réponse HTTP contenant la conversation
        """
        try:
            user_id = str(request.user.id)
            conversation = self.conversation_service.get_conversation_by_id(
                conversation_id=conversation_id,
                user_id=user_id
            )
            
            # Sérialiser la conversation
            serializer = ConversationSerializer(conversation)
            
            return Response(serializer.data)
        
        except ConversationNotFoundError as e:
            logger.warning(f"Conversation non trouvée: {str(e)}")
            error_serializer = ErrorResponseSerializer({
                'error': str(e),
                'error_type': 'ConversationNotFoundError',
                'status_code': 404
            })
            return Response(error_serializer.data, status=status.HTTP_404_NOT_FOUND)
        
        except Exception as e:
            logger.exception("Erreur lors de la récupération d'une conversation")
            error_serializer = ErrorResponseSerializer({
                'error': str(e),
                'error_type': e.__class__.__name__,
                'status_code': 500
            })
            return Response(error_serializer.data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def put(self, request, conversation_id):
        """
        Met à jour une conversation.
        
        Args:
            request: Requête HTTP
            conversation_id: ID de la conversation
            
        Returns:
            Response: Réponse HTTP contenant la conversation mise à jour
        """
        try:
            user_id = str(request.user.id)
            title = request.data.get('title')
            context = request.data.get('context')
            
            # Mettre à jour la conversation
            conversation = self.conversation_service.update_conversation(
                conversation_id=conversation_id,
                user_id=user_id,
                title=title,
                context=context
            )
            
            # Sérialiser la conversation
            serializer = ConversationSerializer(conversation)
            
            return Response(serializer.data)
        
        except ConversationNotFoundError as e:
            logger.warning(f"Conversation non trouvée: {str(e)}")
            error_serializer = ErrorResponseSerializer({
                'error': str(e),
                'error_type': 'ConversationNotFoundError',
                'status_code': 404
            })
            return Response(error_serializer.data, status=status.HTTP_404_NOT_FOUND)
        
        except ValidationError as e:
            logger.warning(f"Erreur de validation: {str(e)}")
            error_serializer = ErrorResponseSerializer({
                'error': str(e),
                'error_type': 'ValidationError',
                'status_code': 400
            })
            return Response(error_serializer.data, status=status.HTTP_400_BAD_REQUEST)
        
        except Exception as e:
            logger.exception("Erreur lors de la mise à jour d'une conversation")
            error_serializer = ErrorResponseSerializer({
                'error': str(e),
                'error_type': e.__class__.__name__,
                'status_code': 500
            })
            return Response(error_serializer.data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def delete(self, request, conversation_id):
        """
        Supprime une conversation.
        
        Args:
            request: Requête HTTP
            conversation_id: ID de la conversation
            
        Returns:
            Response: Réponse HTTP vide
        """
        try:
            user_id = str(request.user.id)
            self.conversation_service.delete_conversation(
                conversation_id=conversation_id,
                user_id=user_id
            )
            
            return Response(status=status.HTTP_204_NO_CONTENT)
        
        except ConversationNotFoundError as e:
            logger.warning(f"Conversation non trouvée: {str(e)}")
            error_serializer = ErrorResponseSerializer({
                'error': str(e),
                'error_type': 'ConversationNotFoundError',
                'status_code': 404
            })
            return Response(error_serializer.data, status=status.HTTP_404_NOT_FOUND)
        
        except Exception as e:
            logger.exception("Erreur lors de la suppression d'une conversation")
            error_serializer = ErrorResponseSerializer({
                'error': str(e),
                'error_type': e.__class__.__name__,
                'status_code': 500
            })
            return Response(error_serializer.data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class MessageView(APIView):
    """Vue pour envoyer des messages dans une conversation."""
    
    permission_classes = [IsAuthenticated]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.conversation_service = ConversationService()
        self.ai_service = AIService()
    
    def post(self, request):
        """
        Envoie un message et reçoit une réponse de l'IA.
        
        Args:
            request: Requête HTTP
            
        Returns:
            Response: Réponse HTTP contenant la réponse de l'IA
        """
        # Valider la requête
        serializer = MessageRequestSerializer(data=request.data)
        if not serializer.is_valid():
            error_serializer = ErrorResponseSerializer({
                'error': "Données invalides",
                'error_type': 'ValidationError',
                'detail': serializer.errors,
                'status_code': 400
            })
            return Response(error_serializer.data, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user_id = str(request.user.id)
            content = serializer.validated_data['content']
            conversation_id = serializer.validated_data.get('conversation_id')
            
            # Obtenir ou créer une conversation
            if conversation_id:
                conversation = self.conversation_service.get_conversation_by_id(
                    conversation_id=conversation_id,
                    user_id=user_id
                )
            else:
                conversation = self.conversation_service.create_conversation(
                    user_id=user_id,
                    title="Nouvelle conversation"
                )
            
            # Ajouter le message de l'utilisateur
            self.conversation_service.add_message(
                conversation_id=conversation.id,
                role="user",
                content=content
            )
            
            # Obtenir une réponse de l'IA
            start_time = time.time()
            ai_response = self.ai_service.generate_response(
                conversation=conversation,
                user_message=content
            )
            processing_time = time.time() - start_time
            
            # Ajouter la réponse de l'IA à la conversation
            ai_message = self.conversation_service.add_message(
                conversation_id=conversation.id,
                role="assistant",
                content=ai_response.content,
                metadata=ai_response.metadata
            )
            
            # Mettre à jour le titre de la conversation si c'est la première interaction
            if len(conversation.messages) <= 2:
                suggested_title = self.ai_service.generate_title(conversation)
                self.conversation_service.update_conversation(
                    conversation_id=conversation.id,
                    user_id=user_id,
                    title=suggested_title
                )
                # Rafraîchir la conversation
                conversation = self.conversation_service.get_conversation_by_id(
                    conversation_id=conversation.id,
                    user_id=user_id
                )
            
            # Préparer la réponse
            response_data = {
                'message': ai_message,
                'conversation': conversation,
                'processing_time': processing_time,
                'model_info': ai_response.metadata.get('model_info', {})
            }
            
            # Sérialiser la réponse
            response_serializer = MessageResponseSerializer(response_data)
            
            return Response(response_serializer.data)
        
        except ConversationNotFoundError as e:
            logger.warning(f"Conversation non trouvée: {str(e)}")
            error_serializer = ErrorResponseSerializer({
                'error': str(e),
                'error_type': 'ConversationNotFoundError',
                'status_code': 404
            })
            return Response(error_serializer.data, status=status.HTTP_404_NOT_FOUND)
        
        except AIServiceError as e:
            logger.error(f"Erreur du service IA: {str(e)}")
            error_serializer = ErrorResponseSerializer({
                'error': str(e),
                'error_type': 'AIServiceError',
                'status_code': 500
            })
            return Response(error_serializer.data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        except Exception as e:
            logger.exception("Erreur lors du traitement du message")
            error_serializer = ErrorResponseSerializer({
                'error': str(e),
                'error_type': e.__class__.__name__,
                'status_code': 500
            })
            return Response(error_serializer.data, status=status.HTTP_500_INTERNAL_SERVER_ERROR) 