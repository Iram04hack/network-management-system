"""
ViewSets API pour les métriques.
Ces ViewSets gèrent les opérations CRUD pour les modèles de métriques.
"""

from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from django.db.models import Q
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from datetime import timedelta
import logging

from ..models import (
    MetricsDefinition, DeviceMetric, MetricValue, 
    MetricThreshold, MetricCalculation
)
from ..serializers.metrics_serializers import (
    MetricsDefinitionSerializer, DeviceMetricSerializer, 
    MetricValueSerializer
)
from ..serializers import MetricThresholdSerializer
from ..domain.interfaces.repositories import (
    IMetricsDefinitionRepository, IDeviceMetricRepository, 
    IMetricValueRepository
)

# Configuration du logger
logger = logging.getLogger(__name__)


class MetricsDefinitionViewSet(viewsets.ModelViewSet):
    """
    API ViewSet pour les définitions de métriques.
    """
    queryset = MetricsDefinition.objects.all()
    serializer_class = MetricsDefinitionSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['name', 'metric_type', 'collection_method']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at', 'updated_at']

    @swagger_auto_schema(
        operation_summary="Lister les définitions de métriques",
        operation_description="Récupère la liste des définitions de métriques avec filtres par type, méthode de collecte et catégorie",
        manual_parameters=[
            openapi.Parameter('category', openapi.IN_QUERY, 
                            description="Filtrer par catégorie de métrique", 
                            type=openapi.TYPE_STRING)
        ],
        responses={
            200: MetricsDefinitionSerializer(many=True)
        },
        tags=['Monitoring']
    )
    def list(self, request, *args, **kwargs):
        """Liste les définitions de métriques disponibles."""
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Créer une définition de métrique",
        operation_description="Crée une nouvelle définition de métrique avec configuration de collecte",
        request_body=MetricsDefinitionSerializer,
        responses={
            201: MetricsDefinitionSerializer,
            400: "Données invalides"
        },
        tags=['Monitoring']
    )
    def create(self, request, *args, **kwargs):
        """Crée une nouvelle définition de métrique."""
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Détails d'une définition de métrique",
        operation_description="Récupère les détails d'une définition de métrique spécifique",
        responses={
            200: MetricsDefinitionSerializer,
            404: "Définition non trouvée"
        },
        tags=['Monitoring']
    )
    def retrieve(self, request, *args, **kwargs):
        """Récupère les détails d'une définition de métrique."""
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Mettre à jour une définition de métrique",
        operation_description="Met à jour complètement une définition de métrique existante",
        request_body=MetricsDefinitionSerializer,
        responses={
            200: MetricsDefinitionSerializer,
            400: "Données invalides",
            404: "Définition non trouvée"
        },
        tags=['Monitoring']
    )
    def update(self, request, *args, **kwargs):
        """Met à jour une définition de métrique."""
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Supprimer une définition de métrique",
        operation_description="Supprime définitivement une définition de métrique",
        responses={
            204: "Définition supprimée avec succès",
            404: "Définition non trouvée"
        },
        tags=['Monitoring']
    )
    def destroy(self, request, *args, **kwargs):
        """Supprime une définition de métrique."""
        return super().destroy(request, *args, **kwargs)

    def get_queryset(self):
        """
        Filtre les métriques en fonction des paramètres de requête.
        """
        queryset = self.queryset
        category = self.request.query_params.get('category', None)
        if category:
            queryset = queryset.filter(category=category)
        return queryset

    @swagger_auto_schema(
        method='get',
        operation_summary="Seuils de métrique",
        operation_description="Récupère les seuils configurés pour une définition de métrique",
        responses={
            200: MetricThresholdSerializer(many=True)
        },
        tags=['Monitoring']
    )
    @action(detail=True, methods=['get'])
    def thresholds(self, request, pk=None):
        """
        Récupère les seuils configurés pour une définition de métrique.
        """
        metric = self.get_object()
        thresholds = MetricThreshold.objects.filter(metrics_definition=metric)
        serializer = MetricThresholdSerializer(thresholds, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(
        method='get',
        operation_summary="Métriques d'équipement",
        operation_description="Récupère les métriques d'équipement pour une définition de métrique",
        manual_parameters=[
            openapi.Parameter('device_id', openapi.IN_QUERY, description='ID équipement', type=openapi.TYPE_INTEGER)
        ],
        responses={
            200: DeviceMetricSerializer(many=True)
        },
        tags=['Monitoring']
    )
    @action(detail=True, methods=['get'])
    def device_metrics(self, request, pk=None):
        """
        Récupère les métriques d'équipement pour une définition de métrique.
        """
        metric = self.get_object()
        device_metrics = DeviceMetric.objects.filter(metric=metric)
        
        # Filtrer par équipement (optionnel)
        device_id = self.request.query_params.get('device_id', None)
        if device_id:
            device_metrics = device_metrics.filter(device_id=device_id)
        
        serializer = DeviceMetricSerializer(device_metrics, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(
        method='post',
        operation_summary="Configurer la collecte",
        operation_description="Met à jour la configuration de collecte pour une définition de métrique",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'collection_config': openapi.Schema(type=openapi.TYPE_OBJECT, description='Configuration de collecte')
            }
        ),
        responses={
            200: "Configuration mise à jour",
            400: "Configuration invalide"
        },
        tags=['Monitoring']
    )
    @action(detail=True, methods=['post'])
    def update_collection_config(self, request, pk=None):
        """
        Met à jour la configuration de collecte pour une définition de métrique.
        """
        metric = self.get_object()
        
        # Mise à jour de la configuration de collecte
        collection_config = request.data.get('collection_config', {})
        if not isinstance(collection_config, dict):
            return Response(
                {"error": "La configuration de collecte doit être un dictionnaire"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Fusionner avec la configuration existante
            if metric.collection_config:
                metric.collection_config.update(collection_config)
            else:
                metric.collection_config = collection_config
                
            metric.save()
            
            return Response({
                "message": "Configuration de collecte mise à jour",
                "collection_config": metric.collection_config
            })
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour de la configuration: {e}")
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class DeviceMetricViewSet(viewsets.ModelViewSet):
    """
    API ViewSet pour les métriques d'équipement.
    """
    queryset = DeviceMetric.objects.all()
    serializer_class = DeviceMetricSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['device', 'metric', 'is_active']
    search_fields = ['name', 'device__name', 'metric__name']
    ordering_fields = ['name', 'created_at', 'last_collection']

    @swagger_auto_schema(
        operation_summary="Lister les métriques d'équipement",
        operation_description="Récupère la liste des métriques d'équipement avec filtres par équipement, type, catégorie et statut de collecte",
        manual_parameters=[
            openapi.Parameter('device_id', openapi.IN_QUERY, 
                            description="Filtrer par ID d'équipement", 
                            type=openapi.TYPE_INTEGER),
            openapi.Parameter('metric_type', openapi.IN_QUERY, 
                            description="Filtrer par type de métrique", 
                            type=openapi.TYPE_STRING),
            openapi.Parameter('category', openapi.IN_QUERY, 
                            description="Filtrer par catégorie de métrique", 
                            type=openapi.TYPE_STRING),
            openapi.Parameter('collection_status', openapi.IN_QUERY, 
                            description="Filtrer par statut de collecte (success, failed, pending)", 
                            type=openapi.TYPE_STRING)
        ],
        responses={
            200: DeviceMetricSerializer(many=True)
        },
        tags=['Monitoring']
    )
    def list(self, request, *args, **kwargs):
        """Liste les métriques d'équipement avec filtres avancés."""
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Créer une métrique d'équipement",
        operation_description="Crée une nouvelle métrique d'équipement pour collecter des données spécifiques",
        request_body=DeviceMetricSerializer,
        responses={
            201: DeviceMetricSerializer,
            400: "Données invalides"
        },
        tags=['Monitoring']
    )
    def create(self, request, *args, **kwargs):
        """Crée une nouvelle métrique d'équipement."""
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Détails d'une métrique d'équipement",
        operation_description="Récupère les détails d'une métrique d'équipement spécifique",
        responses={
            200: DeviceMetricSerializer,
            404: "Métrique non trouvée"
        },
        tags=['Monitoring']
    )
    def retrieve(self, request, *args, **kwargs):
        """Récupère les détails d'une métrique d'équipement."""
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Mettre à jour une métrique d'équipement",
        operation_description="Met à jour complètement une métrique d'équipement existante",
        request_body=DeviceMetricSerializer,
        responses={
            200: DeviceMetricSerializer,
            400: "Données invalides",
            404: "Métrique non trouvée"
        },
        tags=['Monitoring']
    )
    def update(self, request, *args, **kwargs):
        """Met à jour une métrique d'équipement."""
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Supprimer une métrique d'équipement",
        operation_description="Supprime définitivement une métrique d'équipement",
        responses={
            204: "Métrique supprimée avec succès",
            404: "Métrique non trouvée"
        },
        tags=['Monitoring']
    )
    def destroy(self, request, *args, **kwargs):
        """Supprime une métrique d'équipement."""
        return super().destroy(request, *args, **kwargs)

    def get_queryset(self):
        """
        Filtre les métriques d'équipement en fonction des paramètres de requête.
        """
        queryset = self.queryset
        
        # Filtre par équipement
        device_id = self.request.query_params.get('device_id', None)
        if device_id:
            queryset = queryset.filter(device_id=device_id)
            
        # Filtre par type de métrique
        metric_type = self.request.query_params.get('metric_type', None)
        if metric_type:
            queryset = queryset.filter(metric__metric_type=metric_type)
            
        # Filtre par catégorie de métrique
        category = self.request.query_params.get('category', None)
        if category:
            queryset = queryset.filter(metric__category=category)
            
        # Filtre par statut de collecte
        collection_status = self.request.query_params.get('collection_status', None)
        if collection_status:
            if collection_status == 'success':
                queryset = queryset.filter(last_collection_success=True)
            elif collection_status == 'failed':
                queryset = queryset.filter(last_collection_success=False)
            elif collection_status == 'pending':
                queryset = queryset.filter(last_collection=None)
        
        return queryset

    @swagger_auto_schema(
        method='get',
        operation_summary="Valeurs historiques",
        operation_description="Récupère les valeurs historiques pour une métrique d'équipement",
        manual_parameters=[
            openapi.Parameter('from', openapi.IN_QUERY, description='Date de début (ISO 8601)', type=openapi.TYPE_STRING),
            openapi.Parameter('to', openapi.IN_QUERY, description='Date de fin (ISO 8601)', type=openapi.TYPE_STRING),
            openapi.Parameter('limit', openapi.IN_QUERY, description='Nombre maximum de valeurs (max 1000)', type=openapi.TYPE_INTEGER, default=100)
        ],
        responses={
            200: MetricValueSerializer(many=True),
            400: "Paramètres invalides"
        },
        tags=['Monitoring']
    )
    @action(detail=True, methods=['get'])
    def values(self, request, pk=None):
        """
        Récupère les valeurs historiques pour une métrique d'équipement.
        """
        device_metric = self.get_object()
        
        # Paramètres de requête pour la plage de temps
        from_time = request.query_params.get('from', None)
        to_time = request.query_params.get('to', None)
        limit = request.query_params.get('limit', 100)
        
        # Convertir les paramètres
        try:
            limit = int(limit)
        except (ValueError, TypeError):
            limit = 100
        
        # Limiter à 1000 maximum
        limit = min(limit, 1000)
        
        # Construire la requête
        values_query = MetricValue.objects.filter(device_metric=device_metric)
        
        if from_time:
            try:
                from_time = timezone.datetime.fromisoformat(from_time)
                values_query = values_query.filter(timestamp__gte=from_time)
            except ValueError:
                return Response(
                    {"error": "Format de date invalide pour 'from'. Utilisez ISO 8601."},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
        if to_time:
            try:
                to_time = timezone.datetime.fromisoformat(to_time)
                values_query = values_query.filter(timestamp__lte=to_time)
            except ValueError:
                return Response(
                    {"error": "Format de date invalide pour 'to'. Utilisez ISO 8601."},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Par défaut, obtenir les dernières 24 heures si aucune plage n'est spécifiée
        if not from_time and not to_time:
            from_time = timezone.now() - timedelta(days=1)
            values_query = values_query.filter(timestamp__gte=from_time)
        
        # Trier et limiter
        values = values_query.order_by('-timestamp')[:limit]
        
        serializer = MetricValueSerializer(values, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def collect(self, request, pk=None):
        """
        Déclenche la collecte de données pour une métrique d'équipement spécifique.
        """
        device_metric = self.get_object()
        
        try:
            from ..di_container import resolve
            collect_metric_use_case = resolve('CollectMetricUseCase')
            
            result = collect_metric_use_case.execute(device_metric_id=device_metric.id)
            
            if result.get('success', False):
                return Response({
                    "message": "Collecte déclenchée avec succès",
                    "result": result
                })
            else:
                return Response({
                    "error": "Échec de la collecte",
                    "details": result.get('error', 'Erreur inconnue')
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
        except Exception as e:
            logger.error(f"Erreur lors de la collecte de la métrique {device_metric.id}: {e}")
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class MetricValueViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API ViewSet pour les valeurs de métriques (lecture seule).
    """
    queryset = MetricValue.objects.all()
    serializer_class = MetricValueSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['device_metric']
    ordering_fields = ['timestamp', 'value']

    @swagger_auto_schema(
        operation_summary="Lister les valeurs de métriques",
        operation_description="Récupère les valeurs de métriques avec filtres par équipement, métrique et plage de temps (défaut: dernières 24h)",
        manual_parameters=[
            openapi.Parameter('device_metric_id', openapi.IN_QUERY, 
                            description="Filtrer par ID de métrique d'équipement", 
                            type=openapi.TYPE_INTEGER),
            openapi.Parameter('device_id', openapi.IN_QUERY, 
                            description="Filtrer par ID d'équipement", 
                            type=openapi.TYPE_INTEGER),
            openapi.Parameter('from', openapi.IN_QUERY, 
                            description="Date de début (ISO 8601)", 
                            type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME),
            openapi.Parameter('to', openapi.IN_QUERY, 
                            description="Date de fin (ISO 8601)", 
                            type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME),
            openapi.Parameter('limit', openapi.IN_QUERY, 
                            description="Nombre maximum de valeurs (défaut: 1000)", 
                            type=openapi.TYPE_INTEGER)
        ],
        responses={
            200: MetricValueSerializer(many=True)
        },
        tags=['Monitoring']
    )
    def list(self, request, *args, **kwargs):
        """Liste les valeurs de métriques avec filtres de plage temporelle."""
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Détails d'une valeur de métrique",
        operation_description="Récupère les détails d'une valeur de métrique spécifique",
        responses={
            200: MetricValueSerializer,
            404: "Valeur non trouvée"
        },
        tags=['Monitoring']
    )
    def retrieve(self, request, *args, **kwargs):
        """Récupère les détails d'une valeur de métrique."""
        return super().retrieve(request, *args, **kwargs)

    def get_queryset(self):
        """
        Filtre les valeurs de métriques en fonction des paramètres de requête.
        """
        queryset = self.queryset
        
        # Filtre par métrique d'équipement
        device_metric_id = self.request.query_params.get('device_metric_id', None)
        if device_metric_id:
            queryset = queryset.filter(device_metric_id=device_metric_id)
        
        # Filtre par équipement (via device_metric)
        device_id = self.request.query_params.get('device_id', None)
        if device_id:
            queryset = queryset.filter(device_metric__device_id=device_id)
        
        # Filtre par plage de temps
        from_time = self.request.query_params.get('from', None)
        if from_time:
            try:
                from_time = timezone.datetime.fromisoformat(from_time)
                queryset = queryset.filter(timestamp__gte=from_time)
            except ValueError:
                pass
                
        to_time = self.request.query_params.get('to', None)
        if to_time:
            try:
                to_time = timezone.datetime.fromisoformat(to_time)
                queryset = queryset.filter(timestamp__lte=to_time)
            except ValueError:
                pass
        
        # Par défaut, obtenir les dernières 24 heures si aucune plage n'est spécifiée
        if not from_time and not to_time:
            from_time = timezone.now() - timedelta(days=1)
            queryset = queryset.filter(timestamp__gte=from_time)
        
        # Limiter par défaut à 1000 résultats pour éviter les réponses trop volumineuses
        return queryset[:1000]

    @action(detail=False, methods=['get'])
    def aggregated(self, request):
        """
        Récupère des données agrégées pour une ou plusieurs métriques.
        """
        # TODO: Implémenter l'agrégation des données
        return Response({"message": "Fonctionnalité non implémentée"}, 
                       status=status.HTTP_501_NOT_IMPLEMENTED)

    @action(detail=False, methods=['post'])
    def batch_create(self, request):
        """
        Crée plusieurs valeurs de métriques en une seule requête.
        """
        values_data = request.data.get('values', [])
        
        if not isinstance(values_data, list):
            return Response(
                {"error": "Le champ 'values' doit être une liste"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Création des objets en masse
        try:
            from ..di_container import resolve
            value_repository = resolve('IMetricValueRepository')
            
            result = value_repository.batch_create(values_data)
            
            return Response({
                "message": f"{len(result)} valeurs créées avec succès"
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"Erreur lors de la création en masse de valeurs de métriques: {e}")
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            ) 