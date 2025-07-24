"""
ViewSet pour les alertes.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.db.models import Q, Count
from django import models
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from ..models import Alert
from ..serializers import AlertSerializer, AlertDetailSerializer, AlertStatusUpdateSerializer


class AlertViewSet(viewsets.ModelViewSet):
    """
    API pour la gestion des alertes.
    
    retrieve:
    Retourne les détails d'une alerte spécifique.
    
    list:
    Retourne une liste d'alertes, avec possibilité de filtrer par statut, sévérité, équipement, etc.
    
    create:
    Crée une nouvelle alerte.
    
    update:
    Met à jour une alerte existante.
    
    partial_update:
    Met à jour partiellement une alerte existante.
    
    destroy:
    Supprime une alerte existante.
    """
    queryset = Alert.objects.all()
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        """Retourne le sérialiseur approprié selon l'action."""
        if self.action == 'retrieve':
            return AlertDetailSerializer
        return AlertSerializer
    
    @swagger_auto_schema(
        operation_summary="Liste des alertes",
        operation_description="Récupère la liste des alertes avec filtres par statut, sévérité, équipement, etc.",
        tags=['Monitoring'],
        manual_parameters=[
            openapi.Parameter('status', openapi.IN_QUERY, description="Filtrer par statut (active,acknowledged,resolved)", type=openapi.TYPE_STRING),
            openapi.Parameter('severity', openapi.IN_QUERY, description="Filtrer par sévérité (critical,high,medium,low)", type=openapi.TYPE_STRING),
            openapi.Parameter('device_id', openapi.IN_QUERY, description="Filtrer par ID équipement", type=openapi.TYPE_INTEGER),
            openapi.Parameter('start_date', openapi.IN_QUERY, description="Date de début (ISO format)", type=openapi.TYPE_STRING),
            openapi.Parameter('end_date', openapi.IN_QUERY, description="Date de fin (ISO format)", type=openapi.TYPE_STRING),
            openapi.Parameter('search', openapi.IN_QUERY, description="Recherche dans message ou équipement", type=openapi.TYPE_STRING),
        ],
        responses={
            200: openapi.Response(
                description='Liste des alertes',
                schema=AlertSerializer(many=True)
            ),
            401: "Non authentifié"
        }
    )
    def list(self, request, *args, **kwargs):
        """Liste les alertes avec filtres avancés."""
        return super().list(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_summary="Détails d'une alerte",
        operation_description="Récupère les détails complets d'une alerte spécifique.",
        tags=['Monitoring'],
        responses={
            200: openapi.Response(
                description='Détails de l\'alerte',
                schema=AlertDetailSerializer
            ),
            404: "Alerte non trouvée",
            401: "Non authentifié"
        }
    )
    def retrieve(self, request, *args, **kwargs):
        """Récupère les détails d'une alerte."""
        return super().retrieve(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_summary="Créer une alerte",
        operation_description="Crée une nouvelle alerte dans le système.",
        tags=['Monitoring'],
        request_body=AlertSerializer,
        responses={
            201: openapi.Response(
                description='Alerte créée avec succès',
                schema=AlertSerializer
            ),
            400: "Données invalides",
            401: "Non authentifié"
        }
    )
    def create(self, request, *args, **kwargs):
        """Crée une nouvelle alerte."""
        return super().create(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_summary="Mettre à jour une alerte",
        operation_description="Met à jour complètement une alerte existante.",
        tags=['Monitoring'],
        request_body=AlertSerializer,
        responses={
            200: openapi.Response(
                description='Alerte mise à jour avec succès',
                schema=AlertSerializer
            ),
            400: "Données invalides",
            404: "Alerte non trouvée",
            401: "Non authentifié"
        }
    )
    def update(self, request, *args, **kwargs):
        """Met à jour une alerte."""
        return super().update(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_summary="Supprimer une alerte",
        operation_description="Supprime définitivement une alerte du système.",
        tags=['Monitoring'],
        responses={
            204: "Alerte supprimée avec succès",
            404: "Alerte non trouvée",
            401: "Non authentifié"
        }
    )
    def destroy(self, request, *args, **kwargs):
        """Supprime une alerte."""
        return super().destroy(request, *args, **kwargs)
    
    def get_queryset(self):
        """
        Filtre les alertes selon les paramètres de requête.
        
        Paramètres de filtrage:
        - status: Statut des alertes ('active', 'acknowledged', 'resolved', etc.)
        - severity: Sévérité des alertes ('critical', 'high', 'medium', 'low')
        - device_id: ID de l'équipement
        - start_date: Date de début (format ISO)
        - end_date: Date de fin (format ISO)
        - search: Recherche dans le message ou l'équipement
        
        Returns:
            QuerySet des alertes filtrées
        """
        queryset = super().get_queryset()
        params = self.request.query_params
        
        # Filtrer par statut
        status = params.get('status')
        if status:
            if ',' in status:
                queryset = queryset.filter(status__in=status.split(','))
            else:
                queryset = queryset.filter(status=status)
        
        # Filtrer par sévérité
        severity = params.get('severity')
        if severity:
            if ',' in severity:
                queryset = queryset.filter(severity__in=severity.split(','))
            else:
                queryset = queryset.filter(severity=severity)
        
        # Filtrer par équipement
        device_id = params.get('device_id')
        if device_id:
            queryset = queryset.filter(device_id=device_id)
        
        # Filtrer par date
        start_date = params.get('start_date')
        if start_date:
            queryset = queryset.filter(created_at__gte=start_date)
            
        end_date = params.get('end_date')
        if end_date:
            queryset = queryset.filter(created_at__lte=end_date)
        
        # Recherche
        search = params.get('search')
        if search:
            queryset = queryset.filter(
                Q(message__icontains=search) | 
                Q(device__name__icontains=search)
            )
        
        return queryset
    
    @swagger_auto_schema(
        method='post',
        operation_summary="Prendre en compte une alerte",
        operation_description="Marque une alerte comme prise en compte par l'utilisateur.",
        tags=['Monitoring'],
        request_body=AlertStatusUpdateSerializer,
        responses={
            200: AlertDetailSerializer,
            400: "Données invalides ou statut incorrect",
            404: "Alerte non trouvée",
            401: "Non authentifié"
        }
    )
    @action(detail=True, methods=['post'])
    def acknowledge(self, request, pk=None):
        """
        Prend en compte une alerte.
        
        Args:
            request: Requête HTTP
            pk: ID de l'alerte
            
        Returns:
            Response avec les détails de l'alerte mise à jour
        """
        alert = self.get_object()
        serializer = AlertStatusUpdateSerializer(data=request.data)
        
        if serializer.is_valid():
            comment = serializer.validated_data.get('comment', '')
            
            if alert.status == 'active':
                alert.acknowledge(user=request.user, comment=comment)
                return Response(AlertDetailSerializer(alert).data)
            else:
                return Response(
                    {"detail": f"L'alerte ne peut pas être prise en compte car son statut est '{alert.status}'."},
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @swagger_auto_schema(
        method='post',
        operation_summary="Résoudre une alerte",
        operation_description="Marque une alerte comme résolue.",
        tags=['Monitoring'],
        request_body=AlertStatusUpdateSerializer,
        responses={
            200: AlertDetailSerializer,
            400: "Données invalides ou statut incorrect",
            404: "Alerte non trouvée",
            401: "Non authentifié"
        }
    )
    @action(detail=True, methods=['post'])
    def resolve(self, request, pk=None):
        """
        Résout une alerte.
        
        Args:
            request: Requête HTTP
            pk: ID de l'alerte
            
        Returns:
            Response avec les détails de l'alerte mise à jour
        """
        alert = self.get_object()
        serializer = AlertStatusUpdateSerializer(data=request.data)
        
        if serializer.is_valid():
            comment = serializer.validated_data.get('comment', '')
            
            if alert.status in ['active', 'acknowledged']:
                alert.resolve(user=request.user, comment=comment)
                return Response(AlertDetailSerializer(alert).data)
            else:
                return Response(
                    {"detail": f"L'alerte ne peut pas être résolue car son statut est '{alert.status}'."},
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
    @swagger_auto_schema(
        method='get',
        operation_summary="Statistiques des alertes",
        operation_description="Récupère les statistiques complètes sur les alertes (par statut, sévérité, tendances).",
        tags=['Monitoring'],
        responses={
            200: openapi.Response(
                description='Statistiques des alertes',
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'status_stats': openapi.Schema(type=openapi.TYPE_OBJECT),
                        'severity_stats': openapi.Schema(type=openapi.TYPE_OBJECT),
                        'devices_with_most_alerts': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_OBJECT)),
                        'trend': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_OBJECT)),
                        'total_count': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'active_count': openapi.Schema(type=openapi.TYPE_INTEGER)
                    }
                )
            ),
            401: "Non authentifié"
        }
    )
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """
        Retourne des statistiques sur les alertes.
        
        Returns:
            Response avec les statistiques
        """
        # Statistiques par statut
        status_stats = {}
        for status_type, _ in Alert.STATUS_CHOICES:
            status_stats[status_type] = Alert.objects.filter(status=status_type).count()
        
        # Statistiques par sévérité
        severity_stats = {}
        for severity_type, _ in Alert.SEVERITY_CHOICES:
            severity_stats[severity_type] = Alert.objects.filter(severity=severity_type).count()
        
        # Alertes actives par équipement (top 5)
        devices_with_most_alerts = Alert.objects.filter(status='active').values(
            'device__name', 'device_id'
        ).annotate(count=models.Count('id')).order_by('-count')[:5]
        
        # Tendance des alertes (7 derniers jours)
        from datetime import timedelta
        end_date = timezone.now()
        start_date = end_date - timedelta(days=7)
        
        trend_data = []
        current_date = start_date
        while current_date <= end_date:
            next_date = current_date + timedelta(days=1)
            count = Alert.objects.filter(
                created_at__gte=current_date,
                created_at__lt=next_date
            ).count()
            trend_data.append({
                'date': current_date.strftime('%Y-%m-%d'),
                'count': count
            })
            current_date = next_date
        
        return Response({
            'status_stats': status_stats,
            'severity_stats': severity_stats,
            'devices_with_most_alerts': devices_with_most_alerts,
            'trend': trend_data,
            'total_count': Alert.objects.count(),
            'active_count': Alert.objects.filter(status='active').count()
        }) 