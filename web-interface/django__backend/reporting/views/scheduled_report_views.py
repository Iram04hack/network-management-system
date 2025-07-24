from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth.models import User
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
import logging

from ..models import ScheduledReport
from ..serializers import ScheduledReportSerializer
# Architecture simplifiée - utilisation directe des modèles Django
from ..infrastructure.notification_service import ReportingNotificationService

logger = logging.getLogger(__name__)

class ScheduledReportViewSet(viewsets.ModelViewSet):
    """API ViewSet pour les rapports planifiés"""
    serializer_class = ScheduledReportSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Utilisation directe des modèles Django - architecture simplifiée
        self.notification_service = ReportingNotificationService()
    
    def get_queryset(self):
        """
        Récupère les rapports planifiés avec filtres.
        """
        # Gestion Swagger : retourner un queryset vide si c'est une vue factice
        if getattr(self, 'swagger_fake_view', False):
            return ScheduledReport.objects.none()
            
        queryset = ScheduledReport.objects.all()
        
        # Appliquer les filtres selon les paramètres de requête
        if self.request and 'report_type' in self.request.query_params:
            queryset = queryset.filter(report_type=self.request.query_params.get('report_type'))
            
        if self.request and 'frequency' in self.request.query_params:
            queryset = queryset.filter(frequency=self.request.query_params.get('frequency'))
            
        if self.request and 'is_active' in self.request.query_params:
            is_active = self.request.query_params.get('is_active')
            if is_active is not None:
                queryset = queryset.filter(is_active=is_active.lower() == 'true')
            
        if self.request and 'created_by' in self.request.query_params:
            queryset = queryset.filter(created_by_id=self.request.query_params.get('created_by'))
        
        return queryset.order_by('-created_at')
    
    @swagger_auto_schema(
        operation_summary="Lister les rapports planifiés",
        operation_description="Récupère la liste des rapports planifiés avec filtres optionnels",
        manual_parameters=[
            openapi.Parameter('report_type', openapi.IN_QUERY, description='Type de rapport', type=openapi.TYPE_STRING),
            openapi.Parameter('frequency', openapi.IN_QUERY, description='Fréquence', type=openapi.TYPE_STRING),
            openapi.Parameter('is_active', openapi.IN_QUERY, description='Actif', type=openapi.TYPE_BOOLEAN),
            openapi.Parameter('created_by', openapi.IN_QUERY, description='Créé par', type=openapi.TYPE_INTEGER)
        ],
        responses={
            200: ScheduledReportSerializer(many=True)
        },
        tags=['Reporting']
    )
    def list(self, request, *args, **kwargs):
        """Liste les rapports planifiés avec filtres optionnels."""
        return super().list(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_summary="Créer un rapport planifié",
        operation_description="Crée un nouveau rapport planifié",
        request_body=ScheduledReportSerializer,
        responses={
            201: ScheduledReportSerializer,
            400: "Données invalides"
        },
        tags=['Reporting']
    )
    def create(self, request, *args, **kwargs):
        """Crée un nouveau rapport planifié."""
        return super().create(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_summary="Détails d'un rapport planifié",
        operation_description="Récupère les détails d'un rapport planifié spécifique",
        responses={
            200: ScheduledReportSerializer,
            404: "Rapport non trouvé"
        },
        tags=['Reporting']
    )
    def retrieve(self, request, *args, **kwargs):
        """Récupère les détails d'un rapport planifié."""
        return super().retrieve(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_summary="Mettre à jour un rapport planifié",
        operation_description="Met à jour un rapport planifié existant",
        request_body=ScheduledReportSerializer,
        responses={
            200: ScheduledReportSerializer,
            404: "Rapport non trouvé",
            400: "Données invalides"
        },
        tags=['Reporting']
    )
    def update(self, request, *args, **kwargs):
        """Met à jour un rapport planifié."""
        return super().update(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_summary="Mettre à jour partiellement un rapport planifié",
        operation_description="Met à jour partiellement un rapport planifié existant",
        request_body=ScheduledReportSerializer,
        responses={
            200: ScheduledReportSerializer,
            404: "Rapport non trouvé",
            400: "Données invalides"
        },
        tags=['Reporting']
    )
    def partial_update(self, request, *args, **kwargs):
        """Met à jour partiellement un rapport planifié."""
        return super().partial_update(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_summary="Supprimer un rapport planifié",
        operation_description="Supprime définitivement un rapport planifié",
        responses={
            204: "Rapport supprimé avec succès",
            404: "Rapport non trouvé"
        },
        tags=['Reporting']
    )
    def destroy(self, request, *args, **kwargs):
        """Supprime un rapport planifié."""
        return super().destroy(request, *args, **kwargs)
    
    # Utilisation des méthodes par défaut du ModelViewSet pour retrieve
    
    def perform_create(self, serializer):
        """
        Crée un nouveau rapport planifié.
        """
        serializer.save(created_by=self.request.user)
    
    # Utilisation des méthodes par défaut du ModelViewSet pour update
    
    # Utilisation des méthodes par défaut du ModelViewSet pour destroy
    
    @swagger_auto_schema(
        method='post',
        operation_summary="Ajouter un destinataire",
        operation_description="Ajoute un destinataire au rapport planifié",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'user_id': openapi.Schema(type=openapi.TYPE_INTEGER)
            }
        ),
        responses={
            200: "Destinataire ajouté",
            400: "Données invalides"
        },
        tags=['Reporting']
    )
    @action(detail=True, methods=['post'])
    def add_recipient(self, request, pk=None):
        """
        Ajoute un destinataire au rapport planifié.
        """
        user_id = request.data.get('user_id')
        
        if not user_id:
            return Response({
                'message': 'L\'ID de l\'utilisateur est requis'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Récupérer le rapport planifié
            scheduled_report = self.get_object()
            
            # Vérifier que l'utilisateur existe
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                return Response({
                    'message': f'Utilisateur avec ID {user_id} non trouvé'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Ajouter le destinataire
            scheduled_report.recipients.add(user)
            
            return Response({
                'message': f'Utilisateur {user.username} ajouté comme destinataire'
            })
            
        except Exception as e:
            logger.exception(f"Erreur lors de l'ajout d'un destinataire: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @swagger_auto_schema(
        method='post',
        operation_summary="Retirer un destinataire",
        operation_description="Retire un destinataire du rapport planifié",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'user_id': openapi.Schema(type=openapi.TYPE_INTEGER)
            }
        ),
        responses={
            200: "Destinataire retiré",
            400: "Données invalides",
            404: "Utilisateur non trouvé"
        },
        tags=['Reporting']
    )
    @action(detail=True, methods=['post'])
    def remove_recipient(self, request, pk=None):
        """
        Retire un destinataire du rapport planifié.
        """
        user_id = request.data.get('user_id')
        
        if not user_id:
            return Response({
                'message': 'L\'ID de l\'utilisateur est requis'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Récupérer le rapport planifié
            scheduled_report = self.get_object()
            
            # Vérifier que l'utilisateur existe
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                return Response({
                    'message': f'Utilisateur avec ID {user_id} non trouvé'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Retirer le destinataire
            scheduled_report.recipients.remove(user)
            
            return Response({
                'message': f'Utilisateur {user.username} retiré des destinataires'
            })
            
        except Exception as e:
            logger.exception(f"Erreur lors du retrait d'un destinataire: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @swagger_auto_schema(
        method='post',
        operation_summary="Exécuter le rapport maintenant",
        operation_description="Exécute immédiatement un rapport planifié",
        responses={
            200: "Rapport exécuté avec succès",
            400: "Erreur lors de l'exécution"
        },
        tags=['Reporting']
    )
    @action(detail=True, methods=['post'])
    def run_now(self, request, pk=None):
        """
        Exécute immédiatement un rapport planifié.
        """
        try:
            # Récupérer le rapport planifié
            scheduled_report = self.get_object()
            
            # Exécuter le rapport (version simplifiée)
            # Ici on pourrait générer le rapport et envoyer les notifications
            notification_data = {
                'report_id': scheduled_report.id,
                'report_title': scheduled_report.title,
                'report_type': scheduled_report.report_type,
                'recipients': [user.email for user in scheduled_report.recipients.all()],
                'channels': ['email']  # Pour l'instant seulement email
            }
            
            # Envoyer la notification
            result = self.notification_service.send_report_notification(notification_data)
            
            if result.get('success'):
                return Response({
                    'message': 'Rapport planifié exécuté avec succès',
                    'notification_result': result
                })
            else:
                return Response({
                    'message': 'Erreur lors de l\'envoi des notifications',
                    'details': result
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            logger.exception(f"Erreur lors de l'exécution du rapport planifié {pk}: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR) 