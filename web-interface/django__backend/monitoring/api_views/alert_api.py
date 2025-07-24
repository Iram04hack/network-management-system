"""
Vues API pour la gestion des alertes.
"""

from typing import List, Dict, Any

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response

from ..domain.interfaces.repositories import (
    AlertRepository,
    AlertCommentRepository,
    AlertHistoryRepository
)
from ..domain.services import NotificationService
from ..use_cases.alert_use_cases import AlertUseCase
from ..serializers.alert_serializers import (
    AlertSerializer,
    AlertCommentSerializer,
    AlertHistorySerializer
)


class AlertViewSet(viewsets.ViewSet):
    """Vue API pour la gestion des alertes."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.repository = AlertRepository()
        self.notification_service = NotificationService()
        self.use_case = AlertUseCase(self.repository, self.notification_service)
    
    def list(self, request: Request) -> Response:
        """Liste toutes les alertes."""
        # Extraire les filtres de la requête
        filters = {}
        if 'status' in request.query_params:
            filters['status'] = request.query_params['status']
        if 'severity' in request.query_params:
            filters['severity'] = request.query_params['severity']
        if 'device_id' in request.query_params:
            filters['device_id'] = int(request.query_params['device_id'])
        
        # Récupérer les alertes
        alerts = self.use_case.list_alerts(filters)
        
        # Sérialiser les résultats
        serializer = AlertSerializer(alerts, many=True)
        
        return Response(serializer.data)
    
    def retrieve(self, request: Request, pk=None) -> Response:
        """Récupère une alerte par son ID."""
        try:
            alert = self.use_case.get_alert(int(pk))
            serializer = AlertSerializer(alert)
            return Response(serializer.data)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
    
    def create(self, request: Request) -> Response:
        """Crée une nouvelle alerte."""
        # Valider les données d'entrée
        serializer = AlertSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        # Créer l'alerte
        try:
            alert = self.use_case.create_alert(
                title=serializer.validated_data['title'],
                severity=serializer.validated_data['severity'],
                status=serializer.validated_data.get('status', 'active'),
                description=serializer.validated_data.get('description'),
                source_type=serializer.validated_data.get('source_type'),
                source_id=serializer.validated_data.get('source_id'),
                device_id=serializer.validated_data.get('device_id'),
                details=serializer.validated_data.get('details')
            )
            
            # Sérialiser la réponse
            response_serializer = AlertSerializer(alert)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    def update(self, request: Request, pk=None) -> Response:
        """Met à jour une alerte."""
        # Valider les données d'entrée
        serializer = AlertSerializer(data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        # Mettre à jour l'alerte
        try:
            # Si le statut est mis à jour, utiliser la méthode spécifique
            if 'status' in serializer.validated_data:
                user_id = request.user.id if hasattr(request, 'user') and request.user.is_authenticated else None
                comment = serializer.validated_data.get('comment')
                
                alert = self.use_case.update_status(
                    alert_id=int(pk),
                    status=serializer.validated_data['status'],
                    user_id=user_id,
                    comment=comment
                )
                
                # Supprimer status pour ne pas le mettre à jour deux fois
                validated_data = dict(serializer.validated_data)
                validated_data.pop('status')
                if 'comment' in validated_data:
                    validated_data.pop('comment')
                
                # Mettre à jour les autres champs si nécessaire
                if validated_data:
                    alert = self.repository.update(int(pk), **validated_data)
            else:
                # Mise à jour standard
                alert = self.repository.update(int(pk), **serializer.validated_data)
            
            # Sérialiser la réponse
            response_serializer = AlertSerializer(alert)
            return Response(response_serializer.data)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    def destroy(self, request: Request, pk=None) -> Response:
        """Supprime une alerte."""
        try:
            result = self.use_case.delete_alert(int(pk))
            if result:
                return Response(status=status.HTTP_204_NO_CONTENT)
            else:
                return Response({"error": "Failed to delete alert"}, status=status.HTTP_400_BAD_REQUEST)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=True, methods=['post'])
    def acknowledge(self, request: Request, pk=None) -> Response:
        """Reconnaît une alerte."""
        try:
            user_id = request.user.id if hasattr(request, 'user') and request.user.is_authenticated else None
            comment = request.data.get('comment')
            
            if not user_id:
                return Response({"error": "User authentication required"}, status=status.HTTP_401_UNAUTHORIZED)
            
            alert = self.use_case.acknowledge_alert(
                alert_id=int(pk),
                user_id=user_id,
                comment=comment
            )
            
            serializer = AlertSerializer(alert)
            return Response(serializer.data)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def resolve(self, request: Request, pk=None) -> Response:
        """Résout une alerte."""
        try:
            user_id = request.user.id if hasattr(request, 'user') and request.user.is_authenticated else None
            comment = request.data.get('comment')
            
            if not user_id:
                return Response({"error": "User authentication required"}, status=status.HTTP_401_UNAUTHORIZED)
            
            alert = self.use_case.resolve_alert(
                alert_id=int(pk),
                user_id=user_id,
                comment=comment
            )
            
            serializer = AlertSerializer(alert)
            return Response(serializer.data)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def summary(self, request: Request) -> Response:
        """Récupère un résumé des alertes."""
        summary = self.use_case.get_alerts_summary()
        return Response(summary)
    
    @action(detail=False, methods=['post'])
    def bulk_update(self, request: Request) -> Response:
        """Met à jour plusieurs alertes en une seule opération."""
        # Valider les données d'entrée
        if not isinstance(request.data, dict) or 'alert_ids' not in request.data or 'status' not in request.data:
            return Response({"error": "Expected alert_ids and status in request data"}, status=status.HTTP_400_BAD_REQUEST)
        
        alert_ids = request.data['alert_ids']
        status_value = request.data['status']
        user_id = request.user.id if hasattr(request, 'user') and request.user.is_authenticated else None
        comment = request.data.get('comment')
        
        try:
            updated_alerts = self.use_case.bulk_update_status(
                alert_ids=alert_ids,
                status=status_value,
                user_id=user_id,
                comment=comment
            )
            
            serializer = AlertSerializer(updated_alerts, many=True)
            return Response(serializer.data)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class AlertCommentViewSet(viewsets.ViewSet):
    """Vue API pour la gestion des commentaires d'alerte."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.repository = resolve("alert_repository")
    
    def list(self, request: Request) -> Response:
        """Liste les commentaires d'une alerte."""
        alert_id = request.query_params.get('alert_id')
        if not alert_id:
            return Response({"error": "alert_id parameter is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Récupérer l'alerte avec ses commentaires
        try:
            alert = self.repository.get_by_id(int(alert_id))
            if not alert:
                return Response({"error": "Alert not found"}, status=status.HTTP_404_NOT_FOUND)
            
            # Utiliser les commentaires de l'alerte Django directement
            comments = alert.comments.all()
        serializer = AlertCommentSerializer(comments, many=True)
        return Response(serializer.data)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    def retrieve(self, request: Request, pk=None) -> Response:
        """Récupère un commentaire par son ID."""
        try:
            # Utiliser directement le modèle Django
            from ...models import AlertComment
            comment = AlertComment.objects.filter(id=int(pk)).first()
            if comment is None:
                return Response({"error": "Comment not found"}, status=status.HTTP_404_NOT_FOUND)
            
            serializer = AlertCommentSerializer(comment)
            return Response(serializer.data)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    def create(self, request: Request) -> Response:
        """Crée un nouveau commentaire."""
        # Valider les données d'entrée
        serializer = AlertCommentSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        # Créer le commentaire
        try:
            user_id = serializer.validated_data.get('user_id')
            if not user_id and hasattr(request, 'user') and request.user.is_authenticated:
                user_id = request.user.id
            
            if not user_id:
                return Response({"error": "User ID is required"}, status=status.HTTP_400_BAD_REQUEST)
            
            # Utiliser directement le modèle Django
            from ...models import AlertComment
            comment = AlertComment.objects.create(
                alert_id=serializer.validated_data['alert_id'],
                user_id=user_id,
                comment=serializer.validated_data['comment'],
                is_internal=serializer.validated_data.get('is_internal', False)
            )
            
            response_serializer = AlertCommentSerializer(comment)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    def destroy(self, request: Request, pk=None) -> Response:
        """Supprime un commentaire."""
        try:
            # Utiliser directement le modèle Django
            from ...models import AlertComment
            comment = AlertComment.objects.filter(id=int(pk)).first()
            if comment is None:
                return Response({"error": "Comment not found"}, status=status.HTTP_404_NOT_FOUND)
            
            if hasattr(request, 'user') and request.user.is_authenticated:
                if comment.user_id != request.user.id and not request.user.is_staff:
                    return Response({"error": "You are not authorized to delete this comment"}, status=status.HTTP_403_FORBIDDEN)
            
            comment.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class AlertHistoryViewSet(viewsets.ViewSet):
    """Vue API pour la gestion de l'historique des alertes."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.repository = resolve("alert_repository")
    
    def list(self, request: Request) -> Response:
        """Liste l'historique d'une alerte."""
        alert_id = request.query_params.get('alert_id')
        if not alert_id:
            return Response({"error": "alert_id parameter is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Récupérer l'alerte avec son historique
        try:
            alert = self.repository.get_by_id(int(alert_id))
            if not alert:
                return Response({"error": "Alert not found"}, status=status.HTTP_404_NOT_FOUND)
            
            # Utiliser l'historique de l'alerte Django directement
            history = alert.history.all()
        serializer = AlertHistorySerializer(history, many=True)
        return Response(serializer.data)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    def retrieve(self, request: Request, pk=None) -> Response:
        """Récupère un élément d'historique par son ID."""
        try:
            # Utiliser directement le modèle Django
            from ...models import AlertHistory
            history_item = AlertHistory.objects.filter(id=int(pk)).first()
            if history_item is None:
                return Response({"error": "History item not found"}, status=status.HTTP_404_NOT_FOUND)
            
            serializer = AlertHistorySerializer(history_item)
            return Response(serializer.data)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST) 