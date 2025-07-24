"""
Vues API pour la gestion des notifications.
"""

from typing import List, Dict, Any

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from ..domain.interfaces.repositories import (
    NotificationRepository,
    NotificationChannelRepository,
    NotificationRuleRepository
)
from ..use_cases.notification_use_cases import (
    NotificationUseCase,
    NotificationChannelUseCase,
    NotificationRuleUseCase
)
from ..di_container import resolve
from ..serializers.notification_serializers import (
    NotificationSerializer,
    NotificationChannelSerializer,
    NotificationRuleSerializer
)


class NotificationViewSet(viewsets.ViewSet):
    """Vue API pour la gestion des notifications."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.repository = resolve("notification_repository")()
        self.use_case = NotificationUseCase(self.repository)
    
    @swagger_auto_schema(
        operation_summary="Liste des notifications",
        operation_description="Récupère la liste des notifications de l'utilisateur connecté.",
        tags=['Monitoring'],
        manual_parameters=[
            openapi.Parameter('user_id', openapi.IN_QUERY, description="Filtrer par ID utilisateur", type=openapi.TYPE_INTEGER),
            openapi.Parameter('read', openapi.IN_QUERY, description="Filtrer par statut de lecture", type=openapi.TYPE_BOOLEAN),
            openapi.Parameter('limit', openapi.IN_QUERY, description="Limite de résultats", type=openapi.TYPE_INTEGER),
        ],
        responses={
            200: openapi.Response(
                description='Liste des notifications',
                schema=NotificationSerializer
            ),
            401: "Non authentifié"
        }
    )
    def list(self, request: Request) -> Response:
        """Liste les notifications."""
        # Extraire les filtres de la requête
        filters = {}
        if 'user_id' in request.query_params:
            filters['user_id'] = int(request.query_params['user_id'])
        elif hasattr(request, 'user') and request.user.is_authenticated:
            filters['user_id'] = request.user.id
        
        if 'read' in request.query_params:
            filters['read'] = request.query_params['read'].lower() == 'true'
        
        if 'limit' in request.query_params:
            filters['limit'] = int(request.query_params['limit'])
        
        # Récupérer les notifications
        notifications = self.use_case.list_notifications(filters)
        
        # Sérialiser les résultats
        serializer = NotificationSerializer(notifications, many=True)
        
        return Response(serializer.data)
    
    @swagger_auto_schema(
        operation_summary="Détails d'une notification",
        operation_description="Récupère les détails d'une notification par son ID.",
        tags=['Monitoring'],
        responses={200: NotificationSerializer, 404: "Notification non trouvée", 401: "Non authentifié"}
    )
    def retrieve(self, request: Request, pk=None) -> Response:
        """Récupère une notification par son ID."""
        try:
            notification = self.use_case.get_notification(int(pk))
            serializer = NotificationSerializer(notification)
            return Response(serializer.data)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
    
    @swagger_auto_schema(
        operation_summary="Créer une notification",
        operation_description="Crée une nouvelle notification pour un utilisateur.",
        tags=['Monitoring'],
        request_body=NotificationSerializer,
        responses={
            201: openapi.Response(
                description='Notification créée avec succès',
                schema=NotificationSerializer
            ),
            400: "Données invalides",
            401: "Non authentifié"
        }
    )
    def create(self, request: Request) -> Response:
        """Crée une nouvelle notification."""
        # Valider les données d'entrée
        serializer = NotificationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        # Créer la notification
        try:
            notification = self.use_case.create_notification(
                user_id=serializer.validated_data['user_id'],
                title=serializer.validated_data['title'],
                message=serializer.validated_data['message'],
                notification_type=serializer.validated_data.get('notification_type', 'info'),
                source_type=serializer.validated_data.get('source_type'),
                source_id=serializer.validated_data.get('source_id'),
                link=serializer.validated_data.get('link')
            )
            
            # Sérialiser la réponse
            response_serializer = NotificationSerializer(notification)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @swagger_auto_schema(
        operation_summary="Mettre à jour une notification",
        operation_description="Met à jour les informations d'une notification existante.",
        tags=['Monitoring'],
        request_body=NotificationSerializer,
        responses={
            200: openapi.Response(
                description='Notification mise à jour avec succès',
                schema=NotificationSerializer
            ),
            400: "Données invalides",
            404: "Notification non trouvée",
            401: "Non authentifié"
        }
    )
    def update(self, request: Request, pk=None) -> Response:
        """Met à jour une notification."""
        # Valider les données d'entrée
        serializer = NotificationSerializer(data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        # Mettre à jour la notification
        try:
            notification = self.repository.update(int(pk), **serializer.validated_data)
            
            # Sérialiser la réponse
            response_serializer = NotificationSerializer(notification)
            return Response(response_serializer.data)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @swagger_auto_schema(
        operation_summary="Supprimer une notification",
        operation_description="Supprime définitivement une notification.",
        tags=['Monitoring'],
        responses={
            204: "Notification supprimée avec succès",
            404: "Notification non trouvée",
            401: "Non authentifié"
        }
    )
    def destroy(self, request: Request, pk=None) -> Response:
        """Supprime une notification."""
        try:
            result = self.repository.delete(int(pk))
            if result:
                return Response(status=status.HTTP_204_NO_CONTENT)
            else:
                return Response({"error": "Failed to delete notification"}, status=status.HTTP_400_BAD_REQUEST)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
    
    @swagger_auto_schema(
        method='post',
        operation_summary="Marquer comme lue",
        operation_description="Marque une notification comme lue.",
        tags=['Monitoring'],
        responses={
            200: openapi.Response(
                description='Notification marquée comme lue',
                schema=NotificationSerializer
            ),
            404: "Notification non trouvée",
            401: "Non authentifié"
        }
    )
    @action(detail=True, methods=['post'])
    def mark_read(self, request: Request, pk=None) -> Response:
        """Marque une notification comme lue."""
        try:
            notification = self.use_case.mark_as_read(int(pk))
            serializer = NotificationSerializer(notification)
            return Response(serializer.data)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
    
    @swagger_auto_schema(
        method='post',
        operation_summary="Marquer toutes comme lues",
        operation_description="Marque toutes les notifications d'un utilisateur comme lues.",
        tags=['Monitoring'],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'user_id': openapi.Schema(
                    type=openapi.TYPE_INTEGER,
                    description="ID de l'utilisateur (optionnel si connecté)"
                )
            }
        ),
        responses={
            200: openapi.Response(
                description='Notifications marquées comme lues',
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'marked_count': openapi.Schema(type=openapi.TYPE_INTEGER)
                    }
                )
            ),
            400: "Données invalides",
            401: "Non authentifié"
        }
    )
    @action(detail=False, methods=['post'])
    def mark_all_read(self, request: Request) -> Response:
        """Marque toutes les notifications d'un utilisateur comme lues."""
        user_id = request.data.get('user_id')
        if not user_id and hasattr(request, 'user') and request.user.is_authenticated:
            user_id = request.user.id
        
        if not user_id:
            return Response({"error": "User ID is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        count = self.use_case.mark_all_as_read(user_id)
        return Response({"marked_count": count})


class NotificationChannelViewSet(viewsets.ViewSet):
    """Vue API pour la gestion des canaux de notification."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.repository = resolve("notification_channel_repository")()
        self.use_case = NotificationChannelUseCase(self.repository)
    
    @swagger_auto_schema(
        operation_summary="Liste des canaux de notification",
        operation_description="Récupère la liste des canaux de notification avec filtres optionnels.",
        tags=['Monitoring'],
        manual_parameters=[
            openapi.Parameter('user_id', openapi.IN_QUERY, description="Filtrer par ID utilisateur", type=openapi.TYPE_INTEGER),
            openapi.Parameter('channel_type', openapi.IN_QUERY, description="Filtrer par type de canal", type=openapi.TYPE_STRING),
        ],
        responses={
            200: openapi.Response(
                description='Liste des canaux de notification',
                schema=NotificationChannelSerializer(many=True)
            ),
            401: "Non authentifié"
        }
    )
    def list(self, request: Request) -> Response:
        """Liste les canaux de notification."""
        # Extraire les filtres de la requête
        filters = {}
        if 'user_id' in request.query_params:
            filters['user_id'] = int(request.query_params['user_id'])
        elif hasattr(request, 'user') and request.user.is_authenticated:
            filters['user_id'] = request.user.id
        
        if 'channel_type' in request.query_params:
            filters['channel_type'] = request.query_params['channel_type']
        
        # Récupérer les canaux
        channels = self.use_case.list_channels(filters)
        
        # Sérialiser les résultats
        serializer = NotificationChannelSerializer(channels, many=True)
        
        return Response(serializer.data)
    
    @swagger_auto_schema(
        operation_summary="Récupérer un canal de notification",
        operation_description="Récupère les détails d'un canal de notification par son ID.",
        tags=['Monitoring'],
        responses={
            200: openapi.Response(
                description='Détails du canal de notification',
                schema=NotificationChannelSerializer
            ),
            404: "Canal non trouvé",
            401: "Non authentifié"
        }
    )
    def retrieve(self, request: Request, pk=None) -> Response:
        """Récupère un canal de notification par son ID."""
        try:
            channel = self.use_case.get_channel(int(pk))
            serializer = NotificationChannelSerializer(channel)
            return Response(serializer.data)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
    
    @swagger_auto_schema(
        operation_summary="Créer un canal de notification",
        operation_description="Crée un nouveau canal de notification (email, Slack, webhook, etc.).",
        tags=['Monitoring'],
        request_body=NotificationChannelSerializer,
        responses={
            201: openapi.Response(
                description='Canal créé avec succès',
                schema=NotificationChannelSerializer
            ),
            400: "Données invalides",
            401: "Non authentifié"
        }
    )
    def create(self, request: Request) -> Response:
        """Crée un nouveau canal de notification."""
        # Valider les données d'entrée
        serializer = NotificationChannelSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        # Créer le canal
        try:
            user_id = serializer.validated_data.get('user_id')
            if not user_id and hasattr(request, 'user') and request.user.is_authenticated:
                user_id = request.user.id
            
            if not user_id:
                return Response({"error": "User ID is required"}, status=status.HTTP_400_BAD_REQUEST)
            
            channel = self.use_case.create_channel(
                name=serializer.validated_data['name'],
                channel_type=serializer.validated_data['channel_type'],
                config=serializer.validated_data['config'],
                user_id=user_id,
                is_default=serializer.validated_data.get('is_default', False),
                is_enabled=serializer.validated_data.get('is_enabled', True)
            )
            
            # Sérialiser la réponse
            response_serializer = NotificationChannelSerializer(channel)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @swagger_auto_schema(
        operation_summary="Mettre à jour un canal de notification",
        operation_description="Met à jour les informations d'un canal de notification existant.",
        tags=['Monitoring'],
        request_body=NotificationChannelSerializer,
        responses={
            200: openapi.Response(
                description='Canal mis à jour avec succès',
                schema=NotificationChannelSerializer
            ),
            400: "Données invalides",
            404: "Canal non trouvé",
            401: "Non authentifié"
        }
    )
    def update(self, request: Request, pk=None) -> Response:
        """Met à jour un canal de notification."""
        # Valider les données d'entrée
        serializer = NotificationChannelSerializer(data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        # Mettre à jour le canal
        try:
            channel = self.repository.update(int(pk), **serializer.validated_data)
            
            # Sérialiser la réponse
            response_serializer = NotificationChannelSerializer(channel)
            return Response(response_serializer.data)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @swagger_auto_schema(
        operation_summary="Supprimer un canal de notification",
        operation_description="Supprime définitivement un canal de notification.",
        tags=['Monitoring'],
        responses={
            204: "Canal supprimé avec succès",
            404: "Canal non trouvé",
            401: "Non authentifié"
        }
    )
    def destroy(self, request: Request, pk=None) -> Response:
        """Supprime un canal de notification."""
        try:
            result = self.repository.delete(int(pk))
            if result:
                return Response(status=status.HTTP_204_NO_CONTENT)
            else:
                return Response({"error": "Failed to delete notification channel"}, status=status.HTTP_400_BAD_REQUEST)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
    
    @swagger_auto_schema(
        method='post',
        operation_summary="Tester un canal de notification",
        operation_description="Teste un canal de notification en envoyant un message de test.",
        tags=['Monitoring'],
        responses={
            200: openapi.Response(
                description='Test envoyé avec succès',
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'success': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                        'message': openapi.Schema(type=openapi.TYPE_STRING)
                    }
                )
            ),
            404: "Canal non trouvé",
            400: "Erreur lors du test",
            401: "Non authentifié"
        }
    )
    @action(detail=True, methods=['post'])
    def test(self, request: Request, pk=None) -> Response:
        """Teste un canal de notification."""
        try:
            result = self.use_case.test_channel(int(pk))
            return Response({"success": result, "message": "Test notification sent"})
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class NotificationRuleViewSet(viewsets.ViewSet):
    """Vue API pour la gestion des règles de notification."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.repository = resolve("notification_rule_repository")()
        self.channel_repository = resolve("notification_channel_repository")()
        self.use_case = NotificationRuleUseCase(self.repository, self.channel_repository)
    
    @swagger_auto_schema(
        operation_summary="Liste des règles de notification",
        operation_description="Récupère la liste des règles de notification avec filtres optionnels.",
        tags=['Monitoring'],
        manual_parameters=[
            openapi.Parameter('user_id', openapi.IN_QUERY, description="Filtrer par ID utilisateur", type=openapi.TYPE_INTEGER),
            openapi.Parameter('event_type', openapi.IN_QUERY, description="Filtrer par type d'événement", type=openapi.TYPE_STRING),
        ],
        responses={
            200: openapi.Response(
                description='Liste des règles de notification',
                schema=NotificationRuleSerializer(many=True)
            ),
            401: "Non authentifié"
        }
    )
    def list(self, request: Request) -> Response:
        """Liste les règles de notification."""
        # Extraire les filtres de la requête
        filters = {}
        if 'user_id' in request.query_params:
            filters['user_id'] = int(request.query_params['user_id'])
        elif hasattr(request, 'user') and request.user.is_authenticated:
            filters['user_id'] = request.user.id
        
        if 'event_type' in request.query_params:
            filters['event_type'] = request.query_params['event_type']
        
        # Récupérer les règles
        rules = self.use_case.list_rules(filters)
        
        # Sérialiser les résultats
        serializer = NotificationRuleSerializer(rules, many=True)
        
        return Response(serializer.data)
    
    @swagger_auto_schema(
        operation_summary="Récupérer une règle de notification",
        operation_description="Récupère les détails d'une règle de notification par son ID.",
        tags=['Monitoring'],
        responses={
            200: openapi.Response(
                description='Détails de la règle de notification',
                schema=NotificationRuleSerializer
            ),
            404: "Règle non trouvée",
            401: "Non authentifié"
        }
    )
    def retrieve(self, request: Request, pk=None) -> Response:
        """Récupère une règle de notification par son ID."""
        try:
            rule = self.use_case.get_rule(int(pk))
            serializer = NotificationRuleSerializer(rule)
            return Response(serializer.data)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
    
    @swagger_auto_schema(
        operation_summary="Créer une règle de notification",
        operation_description="Crée une nouvelle règle de notification avec conditions et canaux.",
        tags=['Monitoring'],
        request_body=NotificationRuleSerializer,
        responses={
            201: openapi.Response(
                description='Règle créée avec succès',
                schema=NotificationRuleSerializer
            ),
            400: "Données invalides",
            401: "Non authentifié"
        }
    )
    def create(self, request: Request) -> Response:
        """Crée une nouvelle règle de notification."""
        # Valider les données d'entrée
        serializer = NotificationRuleSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        # Créer la règle
        try:
            user_id = serializer.validated_data.get('user_id')
            if not user_id and hasattr(request, 'user') and request.user.is_authenticated:
                user_id = request.user.id
            
            if not user_id:
                return Response({"error": "User ID is required"}, status=status.HTTP_400_BAD_REQUEST)
            
            rule = self.use_case.create_rule(
                name=serializer.validated_data['name'],
                event_type=serializer.validated_data['event_type'],
                channel_ids=serializer.validated_data['channel_ids'],
                user_id=user_id,
                conditions=serializer.validated_data.get('conditions'),
                is_enabled=serializer.validated_data.get('is_enabled', True)
            )
            
            # Sérialiser la réponse
            response_serializer = NotificationRuleSerializer(rule)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @swagger_auto_schema(
        operation_summary="Mettre à jour une règle de notification",
        operation_description="Met à jour les informations d'une règle de notification existante.",
        tags=['Monitoring'],
        request_body=NotificationRuleSerializer,
        responses={
            200: openapi.Response(
                description='Règle mise à jour avec succès',
                schema=NotificationRuleSerializer
            ),
            400: "Données invalides",
            404: "Règle non trouvée",
            401: "Non authentifié"
        }
    )
    def update(self, request: Request, pk=None) -> Response:
        """Met à jour une règle de notification."""
        # Valider les données d'entrée
        serializer = NotificationRuleSerializer(data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        # Mettre à jour la règle
        try:
            rule = self.repository.update(int(pk), **serializer.validated_data)
            
            # Sérialiser la réponse
            response_serializer = NotificationRuleSerializer(rule)
            return Response(response_serializer.data)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @swagger_auto_schema(
        operation_summary="Supprimer une règle de notification",
        operation_description="Supprime définitivement une règle de notification.",
        tags=['Monitoring'],
        responses={
            204: "Règle supprimée avec succès",
            404: "Règle non trouvée",
            401: "Non authentifié"
        }
    )
    def destroy(self, request: Request, pk=None) -> Response:
        """Supprime une règle de notification."""
        try:
            result = self.repository.delete(int(pk))
            if result:
                return Response(status=status.HTTP_204_NO_CONTENT)
            else:
                return Response({"error": "Failed to delete notification rule"}, status=status.HTTP_400_BAD_REQUEST)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND) 