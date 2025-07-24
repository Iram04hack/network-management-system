"""
ViewSet API pour les notifications de surveillance.
"""

from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q
from django.utils import timezone
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
import logging

from ..models import Notification, NotificationChannel, NotificationTemplate
from ..serializers import (
    NotificationSerializer, NotificationChannelSerializer, 
    NotificationTemplateSerializer
)

# Configuration du logger
logger = logging.getLogger(__name__)


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API ViewSet pour les notifications (lecture seule).
    """
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['channel__channel_type', 'status', 'alert']
    search_fields = ['message', 'channel__name']
    ordering_fields = ['created_at', 'updated_at']

    @swagger_auto_schema(
        operation_summary="Lister les notifications",
        operation_description="Récupère la liste des notifications avec filtres optionnels (canal, statut, alerte, date, etc.)",
        manual_parameters=[
            openapi.Parameter('user_only', openapi.IN_QUERY, 
                            description="Afficher seulement les notifications de l'utilisateur (défaut: true)", 
                            type=openapi.TYPE_BOOLEAN),
            openapi.Parameter('is_read', openapi.IN_QUERY, 
                            description="Filtrer par statut de lecture", 
                            type=openapi.TYPE_BOOLEAN),
            openapi.Parameter('from_date', openapi.IN_QUERY, 
                            description="Date de début (ISO format)", 
                            type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME),
            openapi.Parameter('to_date', openapi.IN_QUERY, 
                            description="Date de fin (ISO format)", 
                            type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME),
            openapi.Parameter('alert_severity', openapi.IN_QUERY, 
                            description="Filtrer par sévérité de l'alerte associée", 
                            type=openapi.TYPE_STRING)
        ],
        responses={
            200: NotificationSerializer(many=True)
        },
        tags=['Monitoring']
    )
    def list(self, request, *args, **kwargs):
        """Liste les notifications avec filtres avancés."""
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Détails d'une notification",
        operation_description="Récupère les détails d'une notification spécifique",
        responses={
            200: NotificationSerializer,
            404: "Notification non trouvée"
        },
        tags=['Monitoring']
    )
    def retrieve(self, request, *args, **kwargs):
        """Récupère les détails d'une notification."""
        return super().retrieve(request, *args, **kwargs)

    def get_queryset(self):
        """
        Filtre les notifications en fonction des permissions et paramètres.
        L'utilisateur ne peut voir que les notifications destinées à lui
        ou celles pour lesquelles il est configuré comme destinataire.
        """
        user = self.request.user
        queryset = self.queryset
        
        # Vérifier si on doit filtrer par utilisateur destinataire
        user_only = self.request.query_params.get('user_only', 'true')
        user_only = user_only.lower() in ['true', '1', 't', 'y', 'yes']
        
        if user_only:
            queryset = queryset.filter(
                Q(recipients__contains=user.email) |
                Q(user_recipients__contains=[user.id])
            )
        
        # Filtre par statut de lecture
        is_read = self.request.query_params.get('is_read')
        if is_read is not None:
            is_read = is_read.lower() in ['true', '1', 't', 'y', 'yes']
            if is_read:
                queryset = queryset.filter(read_by__contains=[user.id])
            else:
                queryset = queryset.exclude(read_by__contains=[user.id])
        
        # Filtre par date
        from_date = self.request.query_params.get('from_date')
        if from_date:
            try:
                from_date = timezone.datetime.fromisoformat(from_date)
                queryset = queryset.filter(created_at__gte=from_date)
            except ValueError:
                pass
                
        to_date = self.request.query_params.get('to_date')
        if to_date:
            try:
                to_date = timezone.datetime.fromisoformat(to_date)
                queryset = queryset.filter(created_at__lte=to_date)
            except ValueError:
                pass
        
        # Filtre par type d'alerte associée
        alert_severity = self.request.query_params.get('alert_severity')
        if alert_severity:
            queryset = queryset.filter(alert__severity=alert_severity)
        
        return queryset

    @swagger_auto_schema(
        method='post',
        operation_summary="Marquer comme lu",
        operation_description="Marque une notification comme lue par l'utilisateur actuel",
        responses={
            200: NotificationSerializer,
            403: "Accès non autorisé"
        },
        tags=['Monitoring']
    )
    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        """
        Marque une notification comme lue par l'utilisateur actuel.
        """
        notification = self.get_object()
        user = request.user
        
        # Vérifier si l'utilisateur est destinataire
        user_is_recipient = False
        if notification.recipients and user.email in notification.recipients:
            user_is_recipient = True
        elif notification.user_recipients and user.id in notification.user_recipients:
            user_is_recipient = True
        
        if not user_is_recipient:
            return Response(
                {"error": "Vous n'êtes pas destinataire de cette notification"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Ajouter l'utilisateur à la liste des lecteurs
        read_by = notification.read_by or []
        if user.id not in read_by:
            read_by.append(user.id)
            notification.read_by = read_by
            notification.save()
        
        serializer = self.get_serializer(notification)
        return Response(serializer.data)

    @swagger_auto_schema(
        method='post',
        operation_summary="Marquer toutes comme lues",
        operation_description="Marque toutes les notifications non lues comme lues pour l'utilisateur actuel",
        responses={
            200: openapi.Response("Notifications marquées comme lues", openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'message': openapi.Schema(type=openapi.TYPE_STRING)
                }
            ))
        },
        tags=['Monitoring']
    )
    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        """
        Marque toutes les notifications non lues comme lues pour l'utilisateur actuel.
        """
        user = request.user
        
        # Récupérer toutes les notifications non lues de l'utilisateur
        unread_notifications = Notification.objects.filter(
            Q(recipients__contains=user.email) |
            Q(user_recipients__contains=[user.id])
        ).exclude(read_by__contains=[user.id])
        
        # Marquer chaque notification comme lue
        updated_count = 0
        for notification in unread_notifications:
            read_by = notification.read_by or []
            if user.id not in read_by:
                read_by.append(user.id)
                notification.read_by = read_by
                notification.save()
                updated_count += 1
        
        return Response({
            "message": f"{updated_count} notifications marquées comme lues"
        })

    @swagger_auto_schema(
        method='get',
        operation_summary="Nombre de notifications non lues",
        operation_description="Récupère le nombre de notifications non lues pour l'utilisateur actuel",
        responses={
            200: openapi.Response("Nombre de notifications non lues", openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'count': openapi.Schema(type=openapi.TYPE_INTEGER)
                }
            ))
        },
        tags=['Monitoring']
    )
    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        """
        Récupère le nombre de notifications non lues pour l'utilisateur actuel.
        """
        user = request.user
        
        # Compter les notifications non lues
        count = Notification.objects.filter(
            Q(recipients__contains=user.email) |
            Q(user_recipients__contains=[user.id])
        ).exclude(read_by__contains=[user.id]).count()
        
        return Response({"count": count})


class NotificationChannelViewSet(viewsets.ModelViewSet):
    """
    API ViewSet pour les canaux de notification.
    """
    queryset = NotificationChannel.objects.all()
    serializer_class = NotificationChannelSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['channel_type', 'is_active']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']

    @swagger_auto_schema(
        operation_summary="Lister les canaux de notification",
        operation_description="Récupère la liste des canaux de notification avec filtres par type et statut",
        responses={
            200: NotificationChannelSerializer(many=True)
        },
        tags=['Monitoring']
    )
    def list(self, request, *args, **kwargs):
        """Liste les canaux de notification disponibles."""
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Créer un canal de notification",
        operation_description="Crée un nouveau canal de notification (email, Slack, webhook, etc.)",
        request_body=NotificationChannelSerializer,
        responses={
            201: NotificationChannelSerializer,
            400: "Données invalides"
        },
        tags=['Monitoring']
    )
    def create(self, request, *args, **kwargs):
        """Crée un nouveau canal de notification."""
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Détails d'un canal de notification",
        operation_description="Récupère les détails d'un canal de notification spécifique",
        responses={
            200: NotificationChannelSerializer,
            404: "Canal non trouvé"
        },
        tags=['Monitoring']
    )
    def retrieve(self, request, *args, **kwargs):
        """Récupère les détails d'un canal de notification."""
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Mettre à jour un canal de notification",
        operation_description="Met à jour complètement un canal de notification existant",
        request_body=NotificationChannelSerializer,
        responses={
            200: NotificationChannelSerializer,
            400: "Données invalides",
            404: "Canal non trouvé"
        },
        tags=['Monitoring']
    )
    def update(self, request, *args, **kwargs):
        """Met à jour un canal de notification."""
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Supprimer un canal de notification",
        operation_description="Supprime définitivement un canal de notification",
        responses={
            204: "Canal supprimé avec succès",
            404: "Canal non trouvé"
        },
        tags=['Monitoring']
    )
    def destroy(self, request, *args, **kwargs):
        """Supprime un canal de notification."""
        return super().destroy(request, *args, **kwargs)

    def get_queryset(self):
        """
        Filtre les canaux de notification en fonction des permissions.
        Les utilisateurs normaux ne peuvent voir que les canaux partagés et ceux qu'ils ont créés.
        """
        user = self.request.user
        
        # Les administrateurs peuvent tout voir
        if user.is_staff:
            return self.queryset
        
        # Les autres ne peuvent voir que les canaux partagés ou les leurs
        return NotificationChannel.objects.filter(
            Q(is_shared=True) | Q(created_by=user)
        )

    def perform_create(self, serializer):
        """
        Définit l'utilisateur courant comme créateur lors de la création.
        """
        serializer.save(created_by=self.request.user)

    @swagger_auto_schema(
        method='post',
        operation_summary="Tester le canal",
        operation_description="Teste le canal de notification en envoyant un message de test",
        responses={
            200: "Test envoyé avec succès",
            500: "Erreur lors du test"
        },
        tags=['Monitoring']
    )
    @action(detail=True, methods=['post'])
    def test_channel(self, request, pk=None):
        """
        Teste le canal de notification en envoyant un message de test.
        """
        channel = self.get_object()
        
        try:
            from ..di_container import resolve
            send_notification_use_case = resolve('SendNotificationUseCase')
            
            result = send_notification_use_case.execute(
                channel_id=channel.id,
                message="Ceci est un message de test pour vérifier la configuration du canal.",
                subject="Test de notification",
                alert_id=None,
                test_mode=True
            )
            
            if result.get('success', False):
                return Response({
                    "message": "Test envoyé avec succès",
                    "details": result
                })
            else:
                return Response({
                    "error": "Échec de l'envoi du test",
                    "details": result.get('error', 'Erreur inconnue')
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
        except Exception as e:
            logger.error(f"Erreur lors du test du canal {channel.id}: {e}")
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class NotificationTemplateViewSet(viewsets.ModelViewSet):
    """
    API ViewSet pour les modèles de notification.
    """
    queryset = NotificationTemplate.objects.all()
    serializer_class = NotificationTemplateSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['template_type', 'is_active']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']

    @swagger_auto_schema(
        operation_summary="Lister les modèles de notification",
        operation_description="Récupère la liste des modèles de notification avec filtres par type et statut",
        responses={
            200: NotificationTemplateSerializer(many=True)
        },
        tags=['Monitoring']
    )
    def list(self, request, *args, **kwargs):
        """Liste les modèles de notification disponibles."""
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Créer un modèle de notification",
        operation_description="Crée un nouveau modèle de notification avec contenu personnalisable",
        request_body=NotificationTemplateSerializer,
        responses={
            201: NotificationTemplateSerializer,
            400: "Données invalides"
        },
        tags=['Monitoring']
    )
    def create(self, request, *args, **kwargs):
        """Crée un nouveau modèle de notification."""
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Détails d'un modèle de notification",
        operation_description="Récupère les détails d'un modèle de notification spécifique",
        responses={
            200: NotificationTemplateSerializer,
            404: "Modèle non trouvé"
        },
        tags=['Monitoring']
    )
    def retrieve(self, request, *args, **kwargs):
        """Récupère les détails d'un modèle de notification."""
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Mettre à jour un modèle de notification",
        operation_description="Met à jour complètement un modèle de notification existant",
        request_body=NotificationTemplateSerializer,
        responses={
            200: NotificationTemplateSerializer,
            400: "Données invalides",
            404: "Modèle non trouvé"
        },
        tags=['Monitoring']
    )
    def update(self, request, *args, **kwargs):
        """Met à jour un modèle de notification."""
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Supprimer un modèle de notification",
        operation_description="Supprime définitivement un modèle de notification",
        responses={
            204: "Modèle supprimé avec succès",
            404: "Modèle non trouvé"
        },
        tags=['Monitoring']
    )
    def destroy(self, request, *args, **kwargs):
        """Supprime un modèle de notification."""
        return super().destroy(request, *args, **kwargs)

    def get_queryset(self):
        """
        Filtre les modèles de notification en fonction des permissions.
        Les utilisateurs normaux ne peuvent voir que les modèles partagés et ceux qu'ils ont créés.
        """
        user = self.request.user
        
        # Les administrateurs peuvent tout voir
        if user.is_staff:
            return self.queryset
        
        # Les autres ne peuvent voir que les modèles partagés ou les leurs
        return NotificationTemplate.objects.filter(
            Q(is_shared=True) | Q(created_by=user)
        )
        
    def perform_create(self, serializer):
        """
        Définit l'utilisateur courant comme créateur lors de la création.
        """
        serializer.save(created_by=self.request.user)

    @swagger_auto_schema(
        method='post',
        operation_summary="Prévisualiser le modèle",
        operation_description="Génère une prévisualisation du modèle avec des données exemple",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'sample_data': openapi.Schema(type=openapi.TYPE_OBJECT)
            }
        ),
        responses={
            200: openapi.Response("Prévisualisation générée", openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'rendered_content': openapi.Schema(type=openapi.TYPE_STRING)
                }
            )),
            500: "Erreur lors de la prévisualisation"
        },
        tags=['Monitoring']
    )
    @action(detail=True, methods=['post'])
    def preview(self, request, pk=None):
        """
        Génère une prévisualisation du modèle avec des données exemple.
        """
        template = self.get_object()
        
        # Récupérer les données exemple
        sample_data = request.data.get('sample_data', {})
        
        try:
            from ..domain.services.notification_service import NotificationService
            service = NotificationService()
            
            # Générer le contenu avec le modèle et les données exemple
            rendered_content = service.render_template_with_data(
                template.content,
                template.template_type,
                sample_data
            )
            
            return Response({
                "rendered_content": rendered_content
            })
        except Exception as e:
            logger.error(f"Erreur lors de la prévisualisation du modèle {template.id}: {e}")
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            ) 