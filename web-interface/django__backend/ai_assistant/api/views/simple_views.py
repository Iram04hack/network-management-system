"""
Vues simplifiées pour corriger les erreurs d'intégration Phase 1.
Ces vues utilisent directement les modèles Django pour une intégration rapide.
"""

from rest_framework import viewsets, status, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from django.db.models import Q
import uuid

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from ai_assistant.models import Conversation, Message, AIModel, Command, KnowledgeBase


# ============================================================================
# SERIALIZERS POUR LA DOCUMENTATION SWAGGER
# ============================================================================

class ConversationSerializer(serializers.Serializer):
    """Serializer pour les conversations."""
    id = serializers.IntegerField(read_only=True)
    title = serializers.CharField(max_length=200)
    user = serializers.IntegerField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
    metadata = serializers.JSONField(required=False)


class MessageSerializer(serializers.Serializer):
    """Serializer pour les messages."""
    id = serializers.IntegerField(read_only=True)
    conversation = serializers.IntegerField()
    role = serializers.ChoiceField(choices=['user', 'assistant', 'system'])
    content = serializers.CharField()
    created_at = serializers.DateTimeField(read_only=True)
    processing_time = serializers.FloatField(read_only=True)
    token_count = serializers.IntegerField(read_only=True)
    metadata = serializers.JSONField(required=False)


class DocumentSerializer(serializers.Serializer):
    """Serializer pour les documents."""
    id = serializers.IntegerField(read_only=True)
    title = serializers.CharField(max_length=200)
    content = serializers.CharField()
    category = serializers.CharField(max_length=50)
    keywords = serializers.ListField(child=serializers.CharField())
    is_active = serializers.BooleanField()
    created_at = serializers.DateTimeField(read_only=True)


class CommandSerializer(serializers.Serializer):
    """Serializer pour les commandes."""
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(max_length=100)
    category = serializers.CharField(max_length=50)
    description = serializers.CharField()
    command_template = serializers.CharField()
    is_safe = serializers.BooleanField()
    status = serializers.CharField(max_length=20)


# ============================================================================
# VIEWSETS AVEC DOCUMENTATION SWAGGER
# ============================================================================

class SimpleConversationViewSet(viewsets.ModelViewSet):
    """Vue simplifiée pour les conversations."""

    permission_classes = [IsAuthenticated]
    serializer_class = ConversationSerializer

    def get_queryset(self):
        # Gérer le cas des utilisateurs anonymes pour la génération de schéma
        if getattr(self, 'swagger_fake_view', False):
            return Conversation.objects.none()
        return Conversation.objects.filter(user=self.request.user).order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @swagger_auto_schema(
        operation_summary="Liste des conversations",
        operation_description="Récupère toutes les conversations de l'utilisateur connecté avec pagination",
        manual_parameters=[
            openapi.Parameter('page', openapi.IN_QUERY, description="Numéro de page", type=openapi.TYPE_INTEGER, default=1),
            openapi.Parameter('page_size', openapi.IN_QUERY, description="Taille de page", type=openapi.TYPE_INTEGER, default=20),
        ],
        responses={
            200: openapi.Response(
                description="Liste des conversations récupérée avec succès",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'results': openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                                    'title': openapi.Schema(type=openapi.TYPE_STRING),
                                    'created_at': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME),
                                }
                            )
                        ),
                        'count': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'page': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'page_size': openapi.Schema(type=openapi.TYPE_INTEGER),
                    }
                )
            ),
            401: "Non authentifié"
        },
        tags=['AI Assistant']
    )
    def list(self, request):
        """Liste toutes les conversations de l'utilisateur."""
        conversations = self.get_queryset()
        
        # Pagination simple
        page_size = int(request.query_params.get('page_size', 20))
        page = int(request.query_params.get('page', 1))
        start = (page - 1) * page_size
        end = start + page_size
        
        paginated_conversations = conversations[start:end]
        
        data = []
        for conv in paginated_conversations:
            data.append({
                'id': conv.id,
                'title': conv.title,
                'user': conv.user.id,
                'created_at': conv.created_at.isoformat(),
                'updated_at': conv.updated_at.isoformat(),
                'metadata': conv.metadata or {}
            })
        
        return Response({
            'count': conversations.count(),
            'next': f"?page={page + 1}&page_size={page_size}" if end < conversations.count() else None,
            'previous': f"?page={page - 1}&page_size={page_size}" if page > 1 else None,
            'results': data
        })

    @swagger_auto_schema(
        operation_summary="Créer une conversation",
        operation_description="Crée une nouvelle conversation pour l'utilisateur connecté",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'title': openapi.Schema(type=openapi.TYPE_STRING, description="Titre de la conversation"),
                'description': openapi.Schema(type=openapi.TYPE_STRING, description="Description optionnelle"),
                'metadata': openapi.Schema(type=openapi.TYPE_OBJECT, description="Métadonnées additionnelles"),
            },
            required=['title']
        ),
        responses={
            201: openapi.Response(description="Conversation créée avec succès"),
            400: "Données invalides",
            401: "Non authentifié"
        },
        tags=['AI Assistant']
    )
    def create(self, request):
        """Crée une nouvelle conversation."""
        title = request.data.get('title', 'Nouvelle conversation')
        description = request.data.get('description', '')
        metadata = request.data.get('metadata', {})

        conversation = Conversation.objects.create(
            title=title,
            user=request.user,
            metadata={
                'description': description,
                **metadata
            }
        )

        return Response({
            'id': conversation.id,
            'title': conversation.title,
            'user': conversation.user.id,
            'created_at': conversation.created_at.isoformat(),
            'updated_at': conversation.updated_at.isoformat(),
            'metadata': conversation.metadata
        }, status=status.HTTP_201_CREATED)

    @swagger_auto_schema(
        operation_summary="Détails d'une conversation",
        operation_description="Récupère les détails d'une conversation spécifique",
        responses={
            200: openapi.Response(description="Détails de la conversation"),
            404: "Conversation non trouvée",
            401: "Non authentifié"
        },
        tags=['AI Assistant']
    )
    def retrieve(self, request, pk=None):
        """Récupère une conversation par son ID."""
        conversation = get_object_or_404(self.get_queryset(), pk=pk)
        
        return Response({
            'id': conversation.id,
            'title': conversation.title,
            'user': conversation.user.id,
            'created_at': conversation.created_at.isoformat(),
            'updated_at': conversation.updated_at.isoformat(),
            'metadata': conversation.metadata or {}
        })

    @swagger_auto_schema(
        operation_summary="Modifier une conversation",
        operation_description="Met à jour les informations d'une conversation",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'title': openapi.Schema(type=openapi.TYPE_STRING, description="Nouveau titre"),
                'metadata': openapi.Schema(type=openapi.TYPE_OBJECT, description="Métadonnées à fusionner"),
            }
        ),
        responses={
            200: openapi.Response(description="Conversation mise à jour"),
            404: "Conversation non trouvée",
            401: "Non authentifié"
        },
        tags=['AI Assistant']
    )
    def update(self, request, pk=None):
        """Met à jour une conversation."""
        conversation = get_object_or_404(self.get_queryset(), pk=pk)

        if 'title' in request.data:
            conversation.title = request.data['title']

        if 'metadata' in request.data:
            conversation.metadata = {
                **(conversation.metadata or {}),
                **request.data['metadata']
            }

        conversation.save()

        return Response({
            'id': conversation.id,
            'title': conversation.title,
            'user': conversation.user.id,
            'created_at': conversation.created_at.isoformat(),
            'updated_at': conversation.updated_at.isoformat(),
            'metadata': conversation.metadata or {}
        })

    @swagger_auto_schema(
        operation_summary="Supprimer une conversation",
        operation_description="Supprime définitivement une conversation et tous ses messages",
        responses={
            204: "Conversation supprimée avec succès",
            404: "Conversation non trouvée",
            401: "Non authentifié"
        },
        tags=['AI Assistant']
    )
    def destroy(self, request, pk=None):
        """Supprime une conversation."""
        conversation = get_object_or_404(self.get_queryset(), pk=pk)
        conversation.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @swagger_auto_schema(
        operation_summary="Modifier partiellement une conversation",
        operation_description="Met à jour partiellement une conversation (PATCH)",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'title': openapi.Schema(type=openapi.TYPE_STRING, description="Nouveau titre"),
                'metadata': openapi.Schema(type=openapi.TYPE_OBJECT, description="Métadonnées à mettre à jour"),
            }
        ),
        responses={
            200: openapi.Response(description="Conversation mise à jour partiellement"),
            404: "Conversation non trouvée",
            401: "Non authentifié"
        },
        tags=['AI Assistant']
    )
    def partial_update(self, request, pk=None):
        """Met à jour partiellement une conversation."""
        conversation = get_object_or_404(self.get_queryset(), pk=pk)

        if 'title' in request.data:
            conversation.title = request.data['title']

        if 'metadata' in request.data:
            # Fusionner les métadonnées existantes avec les nouvelles
            existing_metadata = conversation.metadata or {}
            new_metadata = request.data['metadata']
            existing_metadata.update(new_metadata)
            conversation.metadata = existing_metadata

        conversation.save()

        return Response({
            'id': conversation.id,
            'title': conversation.title,
            'created_at': conversation.created_at.isoformat(),
            'updated_at': conversation.updated_at.isoformat(),
            'metadata': conversation.metadata or {}
        })

    @swagger_auto_schema(
        methods=['get'],
        operation_summary="Messages de la conversation",
        operation_description="Récupère tous les messages d'une conversation",
        responses={
            200: openapi.Response(
                description="Messages récupérés avec succès",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'messages': openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                                    'content': openapi.Schema(type=openapi.TYPE_STRING),
                                    'role': openapi.Schema(type=openapi.TYPE_STRING),
                                    'created_at': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME),
                                }
                            )
                        ),
                        'count': openapi.Schema(type=openapi.TYPE_INTEGER),
                    }
                )
            ),
            404: "Conversation non trouvée",
            401: "Non authentifié"
        },
        tags=['AI Assistant']
    )
    @swagger_auto_schema(
        methods=['post'],
        operation_summary="Ajouter un message",
        operation_description="Ajoute un nouveau message à une conversation",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'role': openapi.Schema(type=openapi.TYPE_STRING, enum=['user', 'assistant'], description="Rôle du message"),
                'content': openapi.Schema(type=openapi.TYPE_STRING, description="Contenu du message"),
                'metadata': openapi.Schema(type=openapi.TYPE_OBJECT, description="Métadonnées du message"),
            },
            required=['role', 'content']
        ),
        responses={
            201: openapi.Response(description="Message créé avec succès"),
            404: "Conversation non trouvée",
            401: "Non authentifié"
        },
        tags=['AI Assistant']
    )
    @action(detail=True, methods=['get', 'post'])
    def messages(self, request, pk=None):
        """Gère les messages d'une conversation."""
        conversation = get_object_or_404(self.get_queryset(), pk=pk)
        
        if request.method == 'GET':
            messages = Message.objects.filter(conversation=conversation).order_by('created_at')
            
            data = []
            for msg in messages:
                data.append({
                    'id': msg.id,
                    'conversation': msg.conversation.id,
                    'role': msg.role,
                    'content': msg.content,
                    'created_at': msg.created_at.isoformat(),
                    'metadata': msg.metadata or {},
                    'actions_taken': msg.actions_taken or [],
                    'model_used': msg.model_used.id if msg.model_used else None,
                    'processing_time': msg.processing_time,
                    'token_count': msg.token_count
                })
            
            return Response({'results': data})
        
        elif request.method == 'POST':
            role = request.data.get('role', 'user')
            content = request.data.get('content', '')
            metadata = request.data.get('metadata', {})
            
            message = Message.objects.create(
                conversation=conversation,
                role=role,
                content=content,
                metadata=metadata
            )
            
            return Response({
                'id': message.id,
                'conversation': message.conversation.id,
                'role': message.role,
                'content': message.content,
                'created_at': message.created_at.isoformat(),
                'metadata': message.metadata or {},
                'actions_taken': message.actions_taken or [],
                'model_used': message.model_used.id if message.model_used else None,
                'processing_time': message.processing_time,
                'token_count': message.token_count
            }, status=status.HTTP_201_CREATED)


class SimpleMessageViewSet(viewsets.ModelViewSet):
    """Vue simplifiée pour les messages."""

    permission_classes = [IsAuthenticated]
    serializer_class = MessageSerializer

    def get_queryset(self):
        # Gérer le cas des utilisateurs anonymes pour la génération de schéma
        if getattr(self, 'swagger_fake_view', False):
            return Message.objects.none()
        return Message.objects.filter(
            conversation__user=self.request.user
        ).order_by('-created_at')

    @swagger_auto_schema(
        operation_summary="Liste des messages",
        operation_description="Récupère tous les messages des conversations de l'utilisateur",
        manual_parameters=[
            openapi.Parameter('conversation_id', openapi.IN_QUERY, description="Filtrer par conversation", type=openapi.TYPE_INTEGER),
            openapi.Parameter('page', openapi.IN_QUERY, description="Numéro de page", type=openapi.TYPE_INTEGER, default=1),
            openapi.Parameter('page_size', openapi.IN_QUERY, description="Taille de page", type=openapi.TYPE_INTEGER, default=20),
        ],
        responses={
            200: openapi.Response(
                description="Messages récupérés avec succès",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'results': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                                    'content': openapi.Schema(type=openapi.TYPE_STRING),
                                    'created_at': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME),
                                }
                            )),
                        'count': openapi.Schema(type=openapi.TYPE_INTEGER),
                    }
                )
            ),
            401: "Non authentifié"
        },
        tags=['AI Assistant']
    )
    def list(self, request):
        """Liste tous les messages de l'utilisateur."""
        messages = self.get_queryset()
        
        # Pagination simple
        page_size = int(request.query_params.get('page_size', 20))
        page = int(request.query_params.get('page', 1))
        start = (page - 1) * page_size
        end = start + page_size
        
        paginated_messages = messages[start:end]
        
        data = []
        for msg in paginated_messages:
            data.append({
                'id': msg.id,
                'conversation': msg.conversation.id,
                'role': msg.role,
                'content': msg.content,
                'created_at': msg.created_at.isoformat(),
                'metadata': msg.metadata or {},
                'actions_taken': msg.actions_taken or [],
                'model_used': msg.model_used.id if msg.model_used else None,
                'processing_time': msg.processing_time,
                'token_count': msg.token_count
            })
        
        return Response({
            'count': messages.count(),
            'next': f"?page={page + 1}&page_size={page_size}" if end < messages.count() else None,
            'previous': f"?page={page - 1}&page_size={page_size}" if page > 1 else None,
            'results': data
        })
    
    @swagger_auto_schema(
        operation_summary="Créer un message",
        operation_description="Crée un nouveau message dans une conversation",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'conversation': openapi.Schema(type=openapi.TYPE_INTEGER, description="ID de la conversation"),
                'role': openapi.Schema(type=openapi.TYPE_STRING, enum=['user', 'assistant'], description="Rôle du message"),
                'content': openapi.Schema(type=openapi.TYPE_STRING, description="Contenu du message"),
                'metadata': openapi.Schema(type=openapi.TYPE_OBJECT, description="Métadonnées du message"),
            },
            required=['conversation', 'role', 'content']
        ),
        responses={
            201: openapi.Response(description="Message créé avec succès"),
            400: "Données invalides",
            401: "Non authentifié"
        },
        tags=['AI Assistant']
    )
    def create(self, request):
        """Crée un nouveau message."""
        # Cette méthode sera implémentée selon les besoins
        return Response({"message": "Création de message non implémentée"}, status=status.HTTP_501_NOT_IMPLEMENTED)

    @swagger_auto_schema(
        operation_summary="Détails d'un message",
        operation_description="Récupère les détails d'un message spécifique",
        responses={
            200: openapi.Response(description="Détails du message"),
            404: "Message non trouvé",
            401: "Non authentifié"
        },
        tags=['AI Assistant']
    )
    def retrieve(self, request, pk=None):
        """Récupère un message par son ID."""
        message = get_object_or_404(self.get_queryset(), pk=pk)
        
        return Response({
            'id': message.id,
            'conversation': message.conversation.id,
            'role': message.role,
            'content': message.content,
            'created_at': message.created_at.isoformat(),
            'metadata': message.metadata or {},
            'actions_taken': message.actions_taken or [],
            'model_used': message.model_used.id if message.model_used else None,
            'processing_time': message.processing_time,
            'token_count': message.token_count
        })

    @swagger_auto_schema(
        operation_summary="Modifier un message",
        operation_description="Met à jour complètement un message",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'content': openapi.Schema(type=openapi.TYPE_STRING, description="Nouveau contenu"),
                'metadata': openapi.Schema(type=openapi.TYPE_OBJECT, description="Métadonnées du message"),
            }
        ),
        responses={
            200: openapi.Response(description="Message mis à jour avec succès"),
            400: "Données invalides",
            404: "Message non trouvé",
            401: "Non authentifié"
        },
        tags=['AI Assistant']
    )
    def update(self, request, pk=None):
        """Met à jour un message."""
        message = get_object_or_404(self.get_queryset(), pk=pk)

        if 'content' in request.data:
            message.content = request.data['content']

        if 'metadata' in request.data:
            message.metadata = request.data['metadata']

        message.save()

        return Response({
            'id': message.id,
            'conversation': message.conversation.id,
            'role': message.role,
            'content': message.content,
            'created_at': message.created_at.isoformat(),
            'metadata': message.metadata or {}
        })

    @swagger_auto_schema(
        operation_summary="Modifier partiellement un message",
        operation_description="Met à jour partiellement un message (PATCH)",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'content': openapi.Schema(type=openapi.TYPE_STRING, description="Nouveau contenu"),
                'metadata': openapi.Schema(type=openapi.TYPE_OBJECT, description="Métadonnées à mettre à jour"),
            }
        ),
        responses={
            200: openapi.Response(description="Message mis à jour partiellement"),
            404: "Message non trouvé",
            401: "Non authentifié"
        },
        tags=['AI Assistant']
    )
    def partial_update(self, request, pk=None):
        """Met à jour partiellement un message."""
        message = get_object_or_404(self.get_queryset(), pk=pk)

        if 'content' in request.data:
            message.content = request.data['content']

        if 'metadata' in request.data:
            # Fusionner les métadonnées existantes avec les nouvelles
            existing_metadata = message.metadata or {}
            new_metadata = request.data['metadata']
            existing_metadata.update(new_metadata)
            message.metadata = existing_metadata

        message.save()

        return Response({
            'id': message.id,
            'conversation': message.conversation.id,
            'role': message.role,
            'content': message.content,
            'created_at': message.created_at.isoformat(),
            'metadata': message.metadata or {}
        })

    @swagger_auto_schema(
        operation_summary="Supprimer un message",
        operation_description="Supprime définitivement un message",
        responses={
            204: "Message supprimé avec succès",
            404: "Message non trouvé",
            401: "Non authentifié"
        },
        tags=['AI Assistant']
    )
    def destroy(self, request, pk=None):
        """Supprime un message."""
        message = get_object_or_404(self.get_queryset(), pk=pk)
        message.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class SimpleDocumentViewSet(viewsets.ModelViewSet):
    """Vue simplifiée pour les documents."""
    
    serializer_class = DocumentSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return KnowledgeBase.objects.filter(is_active=True).order_by('-created_at')
    
    @swagger_auto_schema(
        operation_summary="Liste des documents",
        operation_description="Récupère tous les documents de la base de connaissances",
        manual_parameters=[
            openapi.Parameter('page', openapi.IN_QUERY, description="Numéro de page", type=openapi.TYPE_INTEGER, default=1),
            openapi.Parameter('page_size', openapi.IN_QUERY, description="Taille de page", type=openapi.TYPE_INTEGER, default=20),
            openapi.Parameter('search', openapi.IN_QUERY, description="Recherche dans le titre et contenu", type=openapi.TYPE_STRING),
        ],
        responses={
            200: openapi.Response(
                description="Documents récupérés avec succès",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'results': openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                                    'title': openapi.Schema(type=openapi.TYPE_STRING),
                                    'content': openapi.Schema(type=openapi.TYPE_STRING),
                                    'created_at': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME),
                                }
                            )
                        ),
                        'count': openapi.Schema(type=openapi.TYPE_INTEGER),
                    }
                )
            ),
            401: "Non authentifié"
        },
        tags=['AI Assistant']
    )
    def list(self, request):
        """Liste tous les documents."""
        documents = self.get_queryset()
        
        # Pagination simple
        page_size = int(request.query_params.get('page_size', 20))
        page = int(request.query_params.get('page', 1))
        start = (page - 1) * page_size
        end = start + page_size
        
        paginated_docs = documents[start:end]
        
        data = []
        for doc in paginated_docs:
            data.append({
                'id': str(doc.id),
                'title': doc.title,
                'content': doc.content,
                'content_type': doc.content_type,
                'tags': doc.tags or [],
                'is_active': doc.is_active,
                'created_at': doc.created_at.isoformat(),
                'updated_at': doc.updated_at.isoformat()
            })
        
        return Response({
            'count': documents.count(),
            'next': f"?page={page + 1}&page_size={page_size}" if end < documents.count() else None,
            'previous': f"?page={page - 1}&page_size={page_size}" if page > 1 else None,
            'results': data
        })
    
    @swagger_auto_schema(
        operation_summary="Créer un document",
        operation_description="Crée un nouveau document dans la base de connaissances",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'title': openapi.Schema(type=openapi.TYPE_STRING, description="Titre du document"),
                'content': openapi.Schema(type=openapi.TYPE_STRING, description="Contenu du document"),
                'content_type': openapi.Schema(type=openapi.TYPE_STRING, description="Type de contenu", default="text/plain"),
                'tags': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_STRING), description="Tags du document"),
                'category': openapi.Schema(type=openapi.TYPE_STRING, description="Catégorie du document"),
            },
            required=['title', 'content']
        ),
        responses={
            201: openapi.Response(description="Document créé avec succès"),
            400: "Données invalides",
            401: "Non authentifié"
        },
        tags=['AI Assistant']
    )
    def create(self, request):
        """Crée un nouveau document."""
        title = request.data.get('title', 'Nouveau document')
        content = request.data.get('content', '')
        content_type = request.data.get('content_type', 'text/plain')
        tags = request.data.get('tags', [])
        
        document = KnowledgeBase.objects.create(
            title=title,
            content=content,
            content_type=content_type,
            tags=tags,
            is_active=True
        )
        
        return Response({
            'id': str(document.id),
            'title': document.title,
            'content': document.content,
            'content_type': document.content_type,
            'tags': document.tags or [],
            'is_active': document.is_active,
            'created_at': document.created_at.isoformat(),
            'updated_at': document.updated_at.isoformat()
        }, status=status.HTTP_201_CREATED)
    
    @swagger_auto_schema(
        operation_summary="Détails d'un document",
        operation_description="Récupère les détails d'un document spécifique",
        responses={
            200: openapi.Response(description="Détails du document"),
            404: "Document non trouvé",
            401: "Non authentifié"
        },
        tags=['AI Assistant']
    )
    def retrieve(self, request, pk=None):
        """Récupère un document par son ID."""
        try:
            document = get_object_or_404(self.get_queryset(), id=pk)
        except ValueError:
            # Si pk n'est pas un UUID valide
            return Response(
                {'error': 'Invalid document ID format'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return Response({
            'id': str(document.id),
            'title': document.title,
            'content': document.content,
            'content_type': document.content_type,
            'tags': document.tags or [],
            'is_active': document.is_active,
            'created_at': document.created_at.isoformat(),
            'updated_at': document.updated_at.isoformat()
        })

    @swagger_auto_schema(
        operation_summary="Modifier un document",
        operation_description="Met à jour complètement un document de la base de connaissances",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'title': openapi.Schema(type=openapi.TYPE_STRING, description="Nouveau titre"),
                'content': openapi.Schema(type=openapi.TYPE_STRING, description="Nouveau contenu"),
                'content_type': openapi.Schema(type=openapi.TYPE_STRING, description="Type de contenu"),
                'tags': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_STRING), description="Tags du document"),
            }
        ),
        responses={
            200: openapi.Response(description="Document mis à jour avec succès"),
            400: "Données invalides",
            404: "Document non trouvé",
            401: "Non authentifié"
        },
        tags=['AI Assistant']
    )
    def update(self, request, pk=None):
        """Met à jour un document."""
        try:
            document = get_object_or_404(self.get_queryset(), id=pk)
        except ValueError:
            return Response(
                {'error': 'Invalid document ID format'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if 'title' in request.data:
            document.title = request.data['title']

        if 'content' in request.data:
            document.content = request.data['content']

        if 'content_type' in request.data:
            document.content_type = request.data['content_type']

        if 'tags' in request.data:
            document.tags = request.data['tags']

        document.save()

        return Response({
            'id': str(document.id),
            'title': document.title,
            'content': document.content,
            'content_type': document.content_type,
            'tags': document.tags or [],
            'is_active': document.is_active,
            'created_at': document.created_at.isoformat(),
            'updated_at': document.updated_at.isoformat()
        })

    @swagger_auto_schema(
        operation_summary="Supprimer un document",
        operation_description="Supprime définitivement un document de la base de connaissances",
        responses={
            204: "Document supprimé avec succès",
            404: "Document non trouvé",
            401: "Non authentifié"
        },
        tags=['AI Assistant']
    )
    def destroy(self, request, pk=None):
        """Supprime un document."""
        try:
            document = get_object_or_404(self.get_queryset(), id=pk)
        except ValueError:
            return Response(
                {'error': 'Invalid document ID format'},
                status=status.HTTP_400_BAD_REQUEST
            )

        document.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    @swagger_auto_schema(
        operation_summary="Modifier partiellement un document",
        operation_description="Met à jour partiellement un document (PATCH)",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'title': openapi.Schema(type=openapi.TYPE_STRING, description="Nouveau titre"),
                'content': openapi.Schema(type=openapi.TYPE_STRING, description="Nouveau contenu"),
                'content_type': openapi.Schema(type=openapi.TYPE_STRING, description="Type de contenu"),
                'tags': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_STRING), description="Tags du document"),
            }
        ),
        responses={
            200: openapi.Response(description="Document mis à jour partiellement"),
            400: "Données invalides",
            404: "Document non trouvé",
            401: "Non authentifié"
        },
        tags=['AI Assistant']
    )
    def partial_update(self, request, pk=None):
        """Met à jour partiellement un document."""
        try:
            document = get_object_or_404(self.get_queryset(), id=pk)
        except ValueError:
            return Response(
                {'error': 'Invalid document ID format'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if 'title' in request.data:
            document.title = request.data['title']

        if 'content' in request.data:
            document.content = request.data['content']

        if 'content_type' in request.data:
            document.content_type = request.data['content_type']

        if 'tags' in request.data:
            document.tags = request.data['tags']

        document.save()

        return Response({
            'id': document.id,
            'title': document.title,
            'content': document.content[:200] + '...' if len(document.content) > 200 else document.content,
            'content_type': document.content_type,
            'tags': document.tags or [],
            'created_at': document.created_at.isoformat(),
            'updated_at': document.updated_at.isoformat()
        })

    @swagger_auto_schema(
        operation_summary="Rechercher des documents",
        operation_description="Recherche dans la base de connaissances",
        manual_parameters=[
            openapi.Parameter('q', openapi.IN_QUERY, description="Terme de recherche", type=openapi.TYPE_STRING, required=True),
            openapi.Parameter('limit', openapi.IN_QUERY, description="Limite de résultats", type=openapi.TYPE_INTEGER, default=20),
        ],
        responses={
            200: openapi.Response(
                description="Résultats de recherche",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'results': openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                                    'title': openapi.Schema(type=openapi.TYPE_STRING),
                                    'content': openapi.Schema(type=openapi.TYPE_STRING),
                                    'score': openapi.Schema(type=openapi.TYPE_NUMBER),
                                }
                            )
                        ),
                        'total': openapi.Schema(type=openapi.TYPE_INTEGER),
                    }
                )
            ),
            400: "Paramètre de recherche manquant",
            401: "Non authentifié"
        },
        tags=['AI Assistant']
    )
    @action(detail=False, methods=['get'])
    def search(self, request):
        """Recherche dans les documents."""
        query = request.query_params.get('q', '').strip()
        
        if not query:
            return Response(
                {'error': 'Query parameter "q" is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        documents = self.get_queryset().filter(
            Q(title__icontains=query) | Q(content__icontains=query)
        )
        
        limit = int(request.query_params.get('limit', 50))
        documents = documents[:limit]
        
        data = []
        for doc in documents:
            data.append({
                'id': str(doc.id),
                'title': doc.title,
                'content': doc.content[:200] + '...' if len(doc.content) > 200 else doc.content,
                'content_type': doc.content_type,
                'tags': doc.tags or [],
                'relevance_score': 0.8  # Score fictif pour la compatibilité
            })
        
        return Response({'results': data})


class SimpleCommandView(APIView):
    """Vue simplifiée pour l'exécution de commandes."""

    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Exécuter une commande",
        operation_description="Exécute une commande système via l'assistant IA",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'command': openapi.Schema(type=openapi.TYPE_STRING, description="Commande à exécuter"),
                'parameters': openapi.Schema(type=openapi.TYPE_OBJECT, description="Paramètres de la commande"),
                'safe_mode': openapi.Schema(type=openapi.TYPE_BOOLEAN, description="Mode sécurisé", default=True),
            },
            required=['command']
        ),
        responses={
            201: openapi.Response(description="Commande exécutée avec succès"),
            400: "Commande invalide",
            403: "Commande non autorisée",
            401: "Non authentifié"
        },
        tags=['AI Assistant']
    )
    def post(self, request):
        """Exécute une commande."""
        name = request.data.get('name', '').strip()

        if not name:
            return Response(
                {'error': 'Command name is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        parameters = request.data.get('parameters', {})
        metadata = request.data.get('metadata', {})

        # Générer un nom unique pour éviter les conflits
        import time
        unique_name = f"{name}_{int(time.time())}"

        # Exécuter la commande réelle de manière sécurisée
        import subprocess
        import time
        from django.conf import settings
        
        start_time = time.time()
        
        try:
            # Liste des commandes autorisées pour la sécurité
            allowed_commands = [
                'ping', 'traceroute', 'nslookup', 'dig', 'netstat', 
                'ss', 'ip', 'ifconfig', 'arp', 'route'
            ]
            
            if name not in allowed_commands:
                return Response(
                    {'error': f'Command "{name}" not allowed for security reasons'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Construire la commande avec paramètres
            cmd_args = [name]
            if 'target' in parameters:
                cmd_args.append(parameters['target'])
            if 'options' in parameters:
                cmd_args.extend(parameters['options'])
            
            # Exécuter la commande avec timeout
            result = subprocess.run(
                cmd_args, 
                capture_output=True, 
                text=True, 
                timeout=30,  # Timeout de 30 secondes
                check=False
            )
            
            execution_time = int((time.time() - start_time) * 1000)
            
            # Créer un enregistrement de commande avec résultat réel
            command = Command.objects.create(
                name=unique_name,
                category='system',
                description=f'Executed command: {name}',
                parameters=parameters,
                metadata=metadata,
                status='completed' if result.returncode == 0 else 'failed',
                result={
                    'stdout': result.stdout,
                    'stderr': result.stderr,
                    'return_code': result.returncode,
                    'execution_time_ms': execution_time
                }
            )
            
        except subprocess.TimeoutExpired:
            execution_time = int((time.time() - start_time) * 1000)
            command = Command.objects.create(
                name=unique_name,
                category='system',
                description=f'Executed command: {name} (timeout)',
                parameters=parameters,
                metadata=metadata,
                status='timeout',
                result={
                    'error': 'Command execution timed out',
                    'execution_time_ms': execution_time
                }
            )
        except Exception as e:
            execution_time = int((time.time() - start_time) * 1000)
            command = Command.objects.create(
                name=unique_name,
                category='system',
                description=f'Executed command: {name} (error)',
                parameters=parameters,
                metadata=metadata,
                status='error',
                result={
                    'error': str(e),
                    'execution_time_ms': execution_time
                }
            )

        return Response({
            'id': command.id,
            'name': command.name,
            'parameters': command.parameters,
            'status': command.status,
            'result': command.result,
            'created_at': command.created_at.isoformat(),
            'execution_time': command.result.get('execution_time_ms', 0)
        }, status=status.HTTP_201_CREATED)

    @swagger_auto_schema(
        operation_summary="Liste des commandes",
        operation_description="Récupère la liste des commandes disponibles",
        manual_parameters=[
            openapi.Parameter('category', openapi.IN_QUERY, description="Filtrer par catégorie", type=openapi.TYPE_STRING),
            openapi.Parameter('safe_only', openapi.IN_QUERY, description="Commandes sécurisées uniquement", type=openapi.TYPE_BOOLEAN, default=True),
        ],
        responses={
            200: openapi.Response(
                description="Liste des commandes récupérée avec succès",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'commands': openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                                    'name': openapi.Schema(type=openapi.TYPE_STRING),
                                    'description': openapi.Schema(type=openapi.TYPE_STRING),
                                    'category': openapi.Schema(type=openapi.TYPE_STRING),
                                    'is_safe': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                                }
                            )
                        ),
                        'count': openapi.Schema(type=openapi.TYPE_INTEGER),
                    }
                )
            ),
            401: "Non authentifié"
        },
        tags=['AI Assistant']
    )
    def get(self, request):
        """Liste les commandes disponibles."""
        commands = Command.objects.all().order_by('-created_at')[:10]

        data = []
        for cmd in commands:
            data.append({
                'id': cmd.id,
                'name': cmd.name,
                'parameters': cmd.parameters,
                'status': cmd.status,
                'result': cmd.result,
                'created_at': cmd.created_at.isoformat()
            })

        return Response({'results': data})


class SimpleSearchView(APIView):
    """Vue simplifiée pour la recherche globale."""

    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Recherche globale",
        operation_description="Effectue une recherche dans toutes les données de l'assistant IA",
        manual_parameters=[
            openapi.Parameter('q', openapi.IN_QUERY, description="Terme de recherche", type=openapi.TYPE_STRING, required=True),
            openapi.Parameter('type', openapi.IN_QUERY, description="Type de recherche", type=openapi.TYPE_STRING,
                            enum=['all', 'conversations', 'messages', 'documents'], default='all'),
            openapi.Parameter('limit', openapi.IN_QUERY, description="Limite de résultats", type=openapi.TYPE_INTEGER, default=50),
        ],
        responses={
            200: openapi.Response(
                description="Résultats de recherche récupérés avec succès",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'results': openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    'type': openapi.Schema(type=openapi.TYPE_STRING),
                                    'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                                    'title': openapi.Schema(type=openapi.TYPE_STRING),
                                    'content': openapi.Schema(type=openapi.TYPE_STRING),
                                    'score': openapi.Schema(type=openapi.TYPE_NUMBER),
                                }
                            )
                        ),
                        'total': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'query': openapi.Schema(type=openapi.TYPE_STRING),
                    }
                )
            ),
            400: "Paramètre de recherche manquant",
            401: "Non authentifié"
        },
        tags=['AI Assistant']
    )
    def get(self, request):
        """Effectue une recherche globale."""
        query = request.query_params.get('q', '').strip()

        if not query:
            return Response(
                {'error': 'Query parameter "q" is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        search_type = request.query_params.get('type', 'all')
        limit = int(request.query_params.get('limit', 50))

        results = []

        # Recherche dans les conversations
        if search_type in ['all', 'conversations']:
            conversations = Conversation.objects.filter(
                user=request.user,
                title__icontains=query
            )[:limit//2]

            for conv in conversations:
                results.append({
                    'type': 'conversation',
                    'id': conv.id,
                    'title': conv.title,
                    'content': conv.title,
                    'created_at': conv.created_at.isoformat(),
                    'relevance_score': 0.9
                })

        # Recherche dans les documents
        if search_type in ['all', 'documents']:
            documents = KnowledgeBase.objects.filter(
                Q(title__icontains=query) | Q(content__icontains=query),
                is_active=True
            )[:limit//2]

            for doc in documents:
                results.append({
                    'type': 'document',
                    'id': str(doc.id),
                    'title': doc.title,
                    'content': doc.content[:200] + '...' if len(doc.content) > 200 else doc.content,
                    'created_at': doc.created_at.isoformat(),
                    'relevance_score': 0.8
                })

        return Response({
            'results': results,
            'query': query,
            'total_results': len(results),
            'search_types': [search_type] if search_type != 'all' else ['conversations', 'documents']
        })


class SimpleNetworkAnalysisView(APIView):
    """Vue simplifiée pour l'analyse réseau."""

    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Analyse réseau",
        operation_description="Lance une analyse réseau via l'assistant IA",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'target': openapi.Schema(type=openapi.TYPE_STRING, description="Cible de l'analyse (IP, domaine, etc.)"),
                'analysis_type': openapi.Schema(type=openapi.TYPE_STRING,
                                              enum=['ping', 'traceroute', 'port_scan', 'full'],
                                              description="Type d'analyse", default='ping'),
                'options': openapi.Schema(type=openapi.TYPE_OBJECT, description="Options d'analyse"),
            },
            required=['target']
        ),
        responses={
            201: openapi.Response(
                description="Analyse réseau lancée avec succès",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'analysis_id': openapi.Schema(type=openapi.TYPE_STRING),
                        'target': openapi.Schema(type=openapi.TYPE_STRING),
                        'status': openapi.Schema(type=openapi.TYPE_STRING),
                        'results': openapi.Schema(type=openapi.TYPE_OBJECT),
                    }
                )
            ),
            400: "Cible invalide",
            401: "Non authentifié"
        },
        tags=['AI Assistant']
    )
    def post(self, request):
        """Lance une analyse réseau."""
        target = request.data.get('target', '').strip()

        if not target:
            return Response(
                {'error': 'Target is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        analysis_type = request.data.get('analysis_type', 'ping')
        metadata = request.data.get('metadata', {})

        # Analyse réseau réelle avec ping, traceroute et nmap
        import subprocess
        import json
        import re
        from datetime import datetime
        
        analysis_result = {
            'target': target,
            'analysis_type': analysis_type,
            'status': 'in_progress',
            'results': {},
            'recommendations': [],
            'metadata': metadata,
            'analysis_timestamp': datetime.now().isoformat()
        }
        
        try:
            if analysis_type == 'ping':
                # Test de ping réel
                ping_cmd = ['ping', '-c', '4', '-W', '3', target]
                ping_result = subprocess.run(ping_cmd, capture_output=True, text=True, timeout=15)
                
                if ping_result.returncode == 0:
                    # Parser les résultats du ping
                    ping_output = ping_result.stdout
                    
                    # Extraire le temps de réponse moyen
                    rtt_match = re.search(r'avg = ([\d.]+)', ping_output)
                    avg_time = float(rtt_match.group(1)) if rtt_match else 0
                    
                    # Extraire la perte de paquets
                    loss_match = re.search(r'(\d+)% packet loss', ping_output)
                    packet_loss = int(loss_match.group(1)) if loss_match else 0
                    
                    analysis_result['results'] = {
                        'reachable': True,
                        'response_time': avg_time,
                        'packet_loss': packet_loss,
                        'raw_output': ping_output
                    }
                    
                    if avg_time < 50:
                        analysis_result['recommendations'].append('Excellent connectivity')
                    elif avg_time < 100:
                        analysis_result['recommendations'].append('Good connectivity')
                    else:
                        analysis_result['recommendations'].append('High latency detected')
                        
                    if packet_loss > 0:
                        analysis_result['recommendations'].append(f'Packet loss detected: {packet_loss}%')
                else:
                    analysis_result['results'] = {
                        'reachable': False,
                        'error': ping_result.stderr,
                        'raw_output': ping_result.stdout
                    }
                    analysis_result['recommendations'].append('Target unreachable')
                    
            elif analysis_type == 'traceroute':
                # Traceroute réel
                trace_cmd = ['traceroute', '-m', '15', target]
                trace_result = subprocess.run(trace_cmd, capture_output=True, text=True, timeout=30)
                
                if trace_result.returncode == 0:
                    hops = len([line for line in trace_result.stdout.split('\n') if line.strip() and not line.startswith('traceroute')])
                    analysis_result['results'] = {
                        'reachable': True,
                        'hops': max(0, hops - 1),  # Exclure la ligne d'en-tête
                        'raw_output': trace_result.stdout
                    }
                    analysis_result['recommendations'].append(f'Route found with {hops} hops')
                else:
                    analysis_result['results'] = {
                        'reachable': False,
                        'error': trace_result.stderr,
                        'raw_output': trace_result.stdout
                    }
                    
            elif analysis_type == 'port_scan':
                # Scan de ports avec nmap (scan basique seulement)
                nmap_cmd = ['nmap', '-sT', '-p', '22,23,25,53,80,110,143,443,993,995', '--host-timeout', '10s', target]
                nmap_result = subprocess.run(nmap_cmd, capture_output=True, text=True, timeout=30)
                
                if nmap_result.returncode == 0:
                    analysis_result['results'] = {
                        'reachable': True,
                        'scan_results': nmap_result.stdout,
                        'raw_output': nmap_result.stdout
                    }
                    
                    # Compter les ports ouverts
                    open_ports = len(re.findall(r'\d+/tcp\s+open', nmap_result.stdout))
                    analysis_result['recommendations'].append(f'Found {open_ports} open ports')
                else:
                    analysis_result['results'] = {
                        'reachable': False,
                        'error': nmap_result.stderr
                    }
            
            analysis_result['status'] = 'completed'
            
        except subprocess.TimeoutExpired:
            analysis_result['status'] = 'timeout'
            analysis_result['results'] = {'error': 'Analysis timed out'}
            analysis_result['recommendations'].append('Analysis timed out - target may be unreachable')
            
        except Exception as e:
            analysis_result['status'] = 'error'
            analysis_result['results'] = {'error': str(e)}
            analysis_result['recommendations'].append('Analysis failed due to error')

        return Response(analysis_result, status=status.HTTP_201_CREATED)
