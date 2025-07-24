"""
ViewSet API pour les tableaux de bord de surveillance.
"""

from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
import logging
import json

from ..models import Dashboard, DashboardWidget
from ..serializers import DashboardSerializer, DashboardWidgetSerializer

# Configuration du logger
logger = logging.getLogger(__name__)


class DashboardViewSet(viewsets.ModelViewSet):
    """
    API ViewSet pour les tableaux de bord.
    """
    queryset = Dashboard.objects.all()
    serializer_class = DashboardSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_public', 'is_default']
    search_fields = ['title', 'description']
    ordering_fields = ['title', 'created_at', 'updated_at']

    def get_queryset(self):
        """
        Filtre les tableaux de bord en fonction des permissions de l'utilisateur.
        L'utilisateur ne peut voir que les tableaux de bord publics et ceux qu'il a créés.
        """
        user = self.request.user
        return Dashboard.objects.filter(
            Q(is_public=True) | Q(owner=user)
        )

    def perform_create(self, serializer):
        """
        Définit l'utilisateur courant comme propriétaire lors de la création.
        """
        serializer.save(owner=self.request.user)

    @swagger_auto_schema(
        operation_summary="Widgets du tableau de bord",
        operation_description="Récupère les widgets associés à ce tableau de bord",
        responses={
            200: openapi.Response("Widgets du tableau de bord", DashboardWidgetSerializer(many=True)),
            404: "Tableau de bord non trouvé"
        },
        tags=['Monitoring']
    )
    @action(detail=True, methods=['get'])
    def widgets(self, request, pk=None):
        """
        Récupère les widgets associés à ce tableau de bord.
        """
        dashboard = self.get_object()
        widgets = dashboard.widgets.all()
        
        serializer = DashboardWidgetSerializer(widgets, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def add_widget(self, request, pk=None):
        """
        Ajoute un nouveau widget au tableau de bord.
        """
        dashboard = self.get_object()
        
        # Vérifier si l'utilisateur est le propriétaire
        if dashboard.owner != request.user:
            return Response(
                {"error": "Seul le propriétaire peut modifier le tableau de bord"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Récupérer les données du widget
        widget_data = request.data.copy()
        widget_data['dashboard'] = dashboard.id
        
        # Sérialiser et valider les données
        serializer = DashboardWidgetSerializer(data=widget_data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['put'])
    def update_layout(self, request, pk=None):
        """
        Met à jour la disposition des widgets dans le tableau de bord.
        """
        dashboard = self.get_object()
        
        # Vérifier si l'utilisateur est le propriétaire
        if dashboard.owner != request.user:
            return Response(
                {"error": "Seul le propriétaire peut modifier le tableau de bord"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Récupérer les données de layout
        layout_data = request.data.get('layout', [])
        if not isinstance(layout_data, list):
            return Response(
                {"error": "Le layout doit être une liste"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Mettre à jour chaque widget
        updated_widgets = []
        try:
            for item in layout_data:
                widget_id = item.get('id')
                position = item.get('position', {})
                
                if not widget_id:
                    continue
                    
                # Récupérer le widget
                try:
                    widget = DashboardWidget.objects.get(id=widget_id, dashboard=dashboard)
                except DashboardWidget.DoesNotExist:
                    continue
                
                # Mettre à jour la position
                if position:
                    widget.position = position
                    widget.save()
                    updated_widgets.append(widget_id)
            
            return Response({
                "message": f"{len(updated_widgets)} widgets mis à jour",
                "updated_widgets": updated_widgets
            })
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour du layout: {e}")
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'])
    def clone(self, request, pk=None):
        """
        Clone un tableau de bord existant.
        """
        dashboard = self.get_object()
        
        # Créer une copie du tableau de bord
        new_dashboard = Dashboard.objects.create(
            title=f"Copie de {dashboard.title}",
            description=dashboard.description,
            is_public=False,  # Par défaut, la copie est privée
            is_default=False,  # Jamais par défaut
            owner=request.user,
            layout_config=dashboard.layout_config
        )
        
        # Copier les widgets
        for widget in dashboard.widgets.all():
            DashboardWidget.objects.create(
                dashboard=new_dashboard,
                title=widget.title,
                widget_type=widget.widget_type,
                position=widget.position,
                size=widget.size,
                data_source=widget.data_source,
                config=widget.config
            )
        
        # Retourner le nouveau tableau de bord
        serializer = self.get_serializer(new_dashboard)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def set_default(self, request, pk=None):
        """
        Définit ce tableau de bord comme le tableau de bord par défaut de l'utilisateur.
        """
        dashboard = self.get_object()
        
        # Vérifier si l'utilisateur est le propriétaire
        if dashboard.owner != request.user:
            return Response(
                {"error": "Seul le propriétaire peut définir un tableau de bord par défaut"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Désactiver tous les tableaux de bord par défaut de l'utilisateur
        Dashboard.objects.filter(owner=request.user, is_default=True).update(is_default=False)
        
        # Définir ce tableau de bord comme par défaut
        dashboard.is_default = True
        dashboard.save()
        
        return Response({
            "message": f"Le tableau de bord '{dashboard.title}' est maintenant défini comme par défaut"
        })

    @action(detail=True, methods=['get'])
    def refresh_data(self, request, pk=None):
        """
        Rafraîchit les données pour tous les widgets du tableau de bord.
        """
        dashboard = self.get_object()
        
        # Récupérer tous les widgets
        widgets = dashboard.widgets.all()
        
        # Collecter les données pour chaque widget
        widget_data = {}
        
        for widget in widgets:
            # Obtenir les données en fonction du type de widget
            if widget.widget_type == 'metric_value':
                # Récupérer la dernière valeur de la métrique
                from ..models import MetricValue
                device_metric_id = widget.data_source.get('device_metric_id')
                if device_metric_id:
                    latest_value = MetricValue.objects.filter(
                        device_metric_id=device_metric_id
                    ).order_by('-timestamp').first()
                    
                    if latest_value:
                        widget_data[str(widget.id)] = {
                            'value': latest_value.value,
                            'timestamp': latest_value.timestamp.isoformat()
                        }
                    else:
                        widget_data[str(widget.id)] = {
                            'value': None,
                            'timestamp': None
                        }
            
            elif widget.widget_type == 'alert_list':
                # Récupérer les dernières alertes
                from ..models import Alert
                from ..serializers import AlertSerializer
                
                # Paramètres optionnels
                limit = widget.data_source.get('limit', 5)
                status_filter = widget.data_source.get('status')
                severity_filter = widget.data_source.get('severity')
                
                # Construire la requête
                alerts_query = Alert.objects.all()
                if status_filter:
                    alerts_query = alerts_query.filter(status=status_filter)
                if severity_filter:
                    alerts_query = alerts_query.filter(severity=severity_filter)
                
                # Récupérer les alertes
                alerts = alerts_query.order_by('-created_at')[:limit]
                
                # Sérialiser les alertes
                serializer = AlertSerializer(alerts, many=True)
                widget_data[str(widget.id)] = serializer.data
            
            elif widget.widget_type == 'check_results':
                # Récupérer les derniers résultats de vérification
                from ..models import CheckResult
                from ..serializers import CheckResultSerializer
                
                # Paramètres optionnels
                limit = widget.data_source.get('limit', 5)
                status_filter = widget.data_source.get('status')
                device_id = widget.data_source.get('device_id')
                check_id = widget.data_source.get('service_check_id')
                
                # Construire la requête
                results_query = CheckResult.objects.all()
                if status_filter:
                    results_query = results_query.filter(status=status_filter)
                if device_id:
                    results_query = results_query.filter(device_service_check__device_id=device_id)
                if check_id:
                    results_query = results_query.filter(device_service_check__service_check_id=check_id)
                
                # Récupérer les résultats
                results = results_query.order_by('-timestamp')[:limit]
                
                # Sérialiser les résultats
                serializer = CheckResultSerializer(results, many=True)
                widget_data[str(widget.id)] = serializer.data
            
            elif widget.widget_type == 'chart':
                # Récupérer les données pour un graphique
                from ..models import MetricValue
                from ..serializers.metrics_serializers import MetricValueSerializer
                
                # Paramètres du graphique
                device_metric_ids = widget.data_source.get('device_metric_ids', [])
                time_range = widget.data_source.get('time_range', '24h')
                
                # Déterminer la plage de temps
                from django.utils import timezone
                from datetime import timedelta
                
                if time_range == '1h':
                    start_time = timezone.now() - timedelta(hours=1)
                elif time_range == '6h':
                    start_time = timezone.now() - timedelta(hours=6)
                elif time_range == '24h':
                    start_time = timezone.now() - timedelta(days=1)
                elif time_range == '7d':
                    start_time = timezone.now() - timedelta(days=7)
                elif time_range == '30d':
                    start_time = timezone.now() - timedelta(days=30)
                else:
                    # Par défaut 24h
                    start_time = timezone.now() - timedelta(days=1)
                
                # Récupérer les données pour chaque métrique
                chart_data = {}
                for metric_id in device_metric_ids:
                    values = MetricValue.objects.filter(
                        device_metric_id=metric_id,
                        timestamp__gte=start_time
                    ).order_by('timestamp')
                    
                    serializer = MetricValueSerializer(values, many=True)
                    chart_data[str(metric_id)] = serializer.data
                
                widget_data[str(widget.id)] = chart_data
        
        return Response(widget_data) 