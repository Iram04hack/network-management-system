"""
Vues pour les conversations et les messages.

Ce module contient les vues qui exposent les fonctionnalités
de gestion des conversations et des messages via une API REST.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404

from ai_assistant.domain.services import ConversationService, AIService
from ai_assistant.domain.exceptions import (
    ConversationNotFoundError,
    MessageNotFoundError,
    ValidationError,
    AIServiceError,
)
from ai_assistant.api.serializers import (
    ConversationSerializer,
    ConversationCreateSerializer,
    MessageSerializer,
    MessageCreateSerializer,
)


class ConversationViewSet(viewsets.ViewSet):
    """Vue pour gérer les conversations."""
    
    permission_classes = [IsAuthenticated]
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.conversation_service = ConversationService()
        self.ai_service = AIService()
    
    def list(self, request):
        """Liste toutes les conversations de l'utilisateur."""
        user_id = str(request.user.id)
        conversations = self.conversation_service.get_conversations_by_user_id(user_id)
        serializer = ConversationSerializer(conversations, many=True)
        return Response(serializer.data)
    
    def retrieve(self, request, pk=None):
        """Récupère une conversation par son ID."""
        user_id = str(request.user.id)
        
        try:
            conversation = self.conversation_service.get_conversation_by_id(pk, user_id)
            
            # Limiter le nombre de messages si demandé
            message_limit = request.query_params.get('message_limit')
            if message_limit:
                try:
                    message_limit = int(message_limit)
                except ValueError:
                    message_limit = None
            
            serializer = ConversationSerializer(
                conversation,
                context={'message_limit': message_limit}
            )
            return Response(serializer.data)
        
        except ConversationNotFoundError:
            return Response(
                {"error": "Conversation non trouvée"},
                status=status.HTTP_404_NOT_FOUND
            )
    
    def create(self, request):
        """Crée une nouvelle conversation."""
        serializer = ConversationCreateSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user_id = str(request.user.id)
        title = serializer.validated_data.get('title', "Nouvelle conversation")
        context = serializer.validated_data.get('context', "")
        initial_message = serializer.validated_data.get('initial_message')
        
        try:
            # Créer la conversation
            conversation = self.conversation_service.create_conversation(
                user_id=user_id,
                title=title,
                context=context
            )
            
            # Ajouter le message initial si fourni
            if initial_message:
                # Ajouter le message de l'utilisateur
                self.conversation_service.add_message(
                    conversation_id=conversation.id,
                    role="user",
                    content=initial_message
                )
                
                # Générer une réponse de l'IA
                ai_response = self.ai_service.generate_response(
                    conversation=conversation,
                    user_message=initial_message
                )
                
                # Ajouter la réponse de l'IA à la conversation
                self.conversation_service.add_message(
                    conversation_id=conversation.id,
                    role="assistant",
                    content=ai_response.content,
                    metadata=ai_response.metadata
                )
                
                # Générer un titre basé sur le message initial
                if title == "Nouvelle conversation":
                    new_title = self.ai_service.generate_title(conversation)
                    self.conversation_service.update_conversation(
                        conversation_id=conversation.id,
                        user_id=user_id,
                        title=new_title
                    )
                    conversation.title = new_title
            
            serializer = ConversationSerializer(conversation)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        except ValidationError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        except Exception as e:
            return Response(
                {"error": f"Erreur lors de la création de la conversation: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def update(self, request, pk=None):
        """Met à jour une conversation existante."""
        user_id = str(request.user.id)
        
        serializer = ConversationCreateSerializer(data=request.data, partial=True)
        
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Mettre à jour la conversation
            conversation = self.conversation_service.update_conversation(
                conversation_id=pk,
                user_id=user_id,
                title=serializer.validated_data.get('title'),
                context=serializer.validated_data.get('context')
            )
            
            serializer = ConversationSerializer(conversation)
            return Response(serializer.data)
        
        except ConversationNotFoundError:
            return Response(
                {"error": "Conversation non trouvée"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        except ValidationError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        except Exception as e:
            return Response(
                {"error": f"Erreur lors de la mise à jour de la conversation: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def destroy(self, request, pk=None):
        """Supprime une conversation."""
        user_id = str(request.user.id)
        
        try:
            self.conversation_service.delete_conversation(pk, user_id)
            return Response(status=status.HTTP_204_NO_CONTENT)
        
        except ConversationNotFoundError:
            return Response(
                {"error": "Conversation non trouvée"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        except Exception as e:
            return Response(
                {"error": f"Erreur lors de la suppression de la conversation: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class MessageViewSet(viewsets.ViewSet):
    """Vue pour gérer les messages dans une conversation."""
    
    permission_classes = [IsAuthenticated]
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.conversation_service = ConversationService()
        self.ai_service = AIService()
    
    def list(self, request, conversation_pk=None):
        """Liste tous les messages d'une conversation."""
        user_id = str(request.user.id)
        
        try:
            # Récupérer l'historique des messages
            messages = self.conversation_service.get_conversation_history(
                conversation_id=conversation_pk,
                user_id=user_id,
                max_messages=int(request.query_params.get('max_messages', 10))
            )
            
            serializer = MessageSerializer(messages, many=True)
            return Response(serializer.data)
        
        except ConversationNotFoundError:
            return Response(
                {"error": "Conversation non trouvée"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        except Exception as e:
            return Response(
                {"error": f"Erreur lors de la récupération des messages: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def retrieve(self, request, pk=None, conversation_pk=None):
        """Récupère un message par son ID."""
        user_id = str(request.user.id)
        
        try:
            message = self.conversation_service.get_message_by_id(
                conversation_id=conversation_pk,
                message_id=pk,
                user_id=user_id
            )
            
            serializer = MessageSerializer(message)
            return Response(serializer.data)
        
        except (ConversationNotFoundError, MessageNotFoundError):
            return Response(
                {"error": "Message non trouvé"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        except Exception as e:
            return Response(
                {"error": f"Erreur lors de la récupération du message: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def create(self, request, conversation_pk=None):
        """Ajoute un message à une conversation et génère une réponse de l'IA."""
        serializer = MessageCreateSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user_id = str(request.user.id)
        
        try:
            # Récupérer la conversation
            conversation = self.conversation_service.get_conversation_by_id(
                conversation_id=conversation_pk,
                user_id=user_id
            )
            
            # Ajouter le message de l'utilisateur
            user_message = self.conversation_service.add_message(
                conversation_id=conversation_pk,
                role=serializer.validated_data['role'],
                content=serializer.validated_data['content'],
                metadata=serializer.validated_data.get('metadata', {})
            )
            
            # Si le message est de l'utilisateur, générer une réponse de l'IA
            ai_message = None
            if user_message.role == "user":
                try:
                    # Générer une réponse de l'IA
                    ai_response = self.ai_service.generate_response(
                        conversation=conversation,
                        user_message=user_message.content
                    )
                    
                    # Ajouter la réponse de l'IA à la conversation
                    ai_message = self.conversation_service.add_message(
                        conversation_id=conversation_pk,
                        role="assistant",
                        content=ai_response.content,
                        metadata=ai_response.metadata
                    )
                except AIServiceError as e:
                    # En cas d'erreur, ajouter un message d'erreur
                    ai_message = self.conversation_service.add_message(
                        conversation_id=conversation_pk,
                        role="assistant",
                        content=f"Désolé, je n'ai pas pu générer une réponse. Erreur: {str(e)}",
                        metadata={"error": str(e)}
                    )
            
            # Préparer la réponse
            response_data = {
                "user_message": MessageSerializer(user_message).data
            }
            
            if ai_message:
                response_data["ai_message"] = MessageSerializer(ai_message).data
            
            return Response(response_data, status=status.HTTP_201_CREATED)
        
        except ConversationNotFoundError:
            return Response(
                {"error": "Conversation non trouvée"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        except ValidationError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        except Exception as e:
            return Response(
                {"error": f"Erreur lors de l'ajout du message: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            ) 