"""
Vues API pour la gestion des notifications.
"""

from typing import List, Dict, Any

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response

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
from ..serializers.notification_serializers import (
    NotificationSerializer,
    NotificationChannelSerializer,
    NotificationRuleSerializer
)


class NotificationViewSet(viewsets.ViewSet):
    """Vue API pour la gestion des notifications."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.repository = NotificationRepository()
        self.use_case = NotificationUseCase(self.repository)
    
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
    
    def retrieve(self, request: Request, pk=None) -> Response:
        """Récupère une notification par son ID."""
        try:
            notification = self.use_case.get_notification(int(pk))
            serializer = NotificationSerializer(notification)
            return Response(serializer.data)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
    
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
    
    @action(detail=True, methods=['post'])
    def mark_read(self, request: Request, pk=None) -> Response:
        """Marque une notification comme lue."""
        try:
            notification = self.use_case.mark_as_read(int(pk))
            serializer = NotificationSerializer(notification)
            return Response(serializer.data)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
    
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
        self.repository = NotificationChannelRepository()
        self.use_case = NotificationChannelUseCase(self.repository)
    
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
    
    def retrieve(self, request: Request, pk=None) -> Response:
        """Récupère un canal de notification par son ID."""
        try:
            channel = self.use_case.get_channel(int(pk))
            serializer = NotificationChannelSerializer(channel)
            return Response(serializer.data)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
    
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
        self.repository = NotificationRuleRepository()
        self.channel_repository = NotificationChannelRepository()
        self.use_case = NotificationRuleUseCase(self.repository, self.channel_repository)
    
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
    
    def retrieve(self, request: Request, pk=None) -> Response:
        """Récupère une règle de notification par son ID."""
        try:
            rule = self.use_case.get_rule(int(pk))
            serializer = NotificationRuleSerializer(rule)
            return Response(serializer.data)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
    
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