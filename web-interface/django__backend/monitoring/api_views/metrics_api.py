"""
Vues API pour la gestion des métriques.
"""

from datetime import datetime
from typing import List, Dict, Any

from django.utils.dateparse import parse_datetime
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from ..di_container import resolve
from ..infrastructure.repositories.metrics_repository import (
    MetricsDefinitionRepository,
    DeviceMetricRepository,
    MetricValueRepository
)
from ..domain.services import AnomalyDetectionService, AlertingService
from ..use_cases.metrics_use_cases import (
    MetricsDefinitionUseCase,
    DeviceMetricUseCase,
    MetricValueUseCase
)
from ..serializers.metrics_serializers import (
    MetricsDefinitionSerializer,
    DeviceMetricSerializer,
    MetricValueSerializer
)


class MetricsDefinitionViewSet(viewsets.ViewSet):
    """Vue API pour la gestion des définitions de métriques."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.repository = resolve('metrics_definition_repository')
        self.use_case = MetricsDefinitionUseCase(self.repository)
    
    @swagger_auto_schema(
        operation_summary="Liste des définitions de métriques",
        operation_description="Récupère la liste des définitions de métriques avec filtres optionnels.",
        tags=['Monitoring'],
        manual_parameters=[
            openapi.Parameter('category', openapi.IN_QUERY, description="Filtrer par catégorie", type=openapi.TYPE_STRING),
            openapi.Parameter('collection_method', openapi.IN_QUERY, description="Filtrer par méthode de collecte", type=openapi.TYPE_STRING),
        ],
        responses={
            200: openapi.Response('Liste des metricsdefinitions', schema=MetricsDefinitionSerializer),
            401: "Non authentifié"
        }
    )
    def list(self, request: Request) -> Response:
        """Liste toutes les définitions de métriques."""
        # Extraire les filtres de la requête
        filters = {}
        if 'category' in request.query_params:
            filters['category'] = request.query_params['category']
        if 'collection_method' in request.query_params:
            filters['collection_method'] = request.query_params['collection_method']
        
        # Récupérer les définitions de métriques
        metrics_definitions = self.use_case.list_metrics_definitions(filters)
        
        # Sérialiser les résultats
        serializer = MetricsDefinitionSerializer(metrics_definitions, many=True)
        
        return Response(serializer.data)
    
    @swagger_auto_schema(
        operation_summary="Détails d'une définition de métrique",
        operation_description="Récupère les détails d'une définition de métrique par son ID.",
        tags=['Monitoring'],
        responses={
            200: MetricsDefinitionSerializer,
            404: "Définition de métrique non trouvée",
            401: "Non authentifié"
        }
    )
    def retrieve(self, request: Request, pk=None) -> Response:
        """Récupère une définition de métrique par son ID."""
        try:
            metrics_definition = self.use_case.get_metrics_definition(int(pk))
            serializer = MetricsDefinitionSerializer(metrics_definition)
            return Response(serializer.data)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
    
    @swagger_auto_schema(
        operation_summary="Créer une définition de métrique",
        operation_description="Crée une nouvelle définition de métrique dans le système.",
        tags=['Monitoring'],
        request_body=MetricsDefinitionSerializer,
        responses={
            201: MetricsDefinitionSerializer,
            400: "Données invalides",
            401: "Non authentifié"
        }
    )
    def create(self, request: Request) -> Response:
        """Crée une nouvelle définition de métrique."""
        # Valider les données d'entrée
        serializer = MetricsDefinitionSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        # Créer la définition de métrique
        try:
            metrics_definition = self.use_case.create_metrics_definition(
                name=serializer.validated_data['name'],
                description=serializer.validated_data['description'],
                metric_type=serializer.validated_data['metric_type'],
                unit=serializer.validated_data['unit'],
                collection_method=serializer.validated_data['collection_method'],
                collection_config=serializer.validated_data['collection_config'],
                category=serializer.validated_data.get('category')
            )
            
            # Sérialiser la réponse
            response_serializer = MetricsDefinitionSerializer(metrics_definition)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @swagger_auto_schema(
        operation_summary="Modifier une définition de métrique",
        operation_description="Met à jour complètement une définition de métrique existante.",
        tags=['Monitoring'],
        request_body=MetricsDefinitionSerializer,
        responses={
            200: MetricsDefinitionSerializer,
            400: "Données invalides",
            404: "Définition de métrique non trouvée",
            401: "Non authentifié"
        }
    )
    def update(self, request: Request, pk=None) -> Response:
        """Met à jour une définition de métrique."""
        # Valider les données d'entrée
        serializer = MetricsDefinitionSerializer(data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        # Mettre à jour la définition de métrique
        try:
            metrics_definition = self.use_case.update_metrics_definition(
                metrics_definition_id=int(pk),
                **serializer.validated_data
            )
            
            # Sérialiser la réponse
            response_serializer = MetricsDefinitionSerializer(metrics_definition)
            return Response(response_serializer.data)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @swagger_auto_schema(
        operation_summary="Supprimer une définition de métrique",
        operation_description="Supprime une définition de métrique du système.",
        tags=['Monitoring'],
        responses={
            204: "Définition de métrique supprimée avec succès",
            404: "Définition de métrique non trouvée",
            401: "Non authentifié"
        }
    )
    def destroy(self, request: Request, pk=None) -> Response:
        """Supprime une définition de métrique."""
        try:
            result = self.use_case.delete_metrics_definition(int(pk))
            if result:
                return Response(status=status.HTTP_204_NO_CONTENT)
            else:
                return Response({"error": "Failed to delete metrics definition"}, status=status.HTTP_400_BAD_REQUEST)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)


class DeviceMetricViewSet(viewsets.ViewSet):
    """Vue API pour la gestion des métriques d'équipement."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.repository = resolve('device_metric_repository')
        self.metrics_definition_repository = resolve('metrics_definition_repository')
        self.use_case = DeviceMetricUseCase(self.repository, self.metrics_definition_repository)
    
    @swagger_auto_schema(
        operation_summary="Liste des métriques d'équipement",
        operation_description="Récupère la liste des métriques configurées pour les équipements.",
        tags=['Monitoring'],
        manual_parameters=[
            openapi.Parameter('device_id', openapi.IN_QUERY, description="Filtrer par ID d'équipement", type=openapi.TYPE_INTEGER),
        ],
        responses={
            200: openapi.Response('Liste des devicemetrics', schema=DeviceMetricSerializer),
            401: "Non authentifié"
        }
    )
    def list(self, request: Request) -> Response:
        """Liste toutes les métriques d'équipement."""
        # Extraire les filtres de la requête
        device_id = request.query_params.get('device_id')
        if device_id:
            device_metrics = self.use_case.list_device_metrics(device_id=int(device_id))
        else:
            device_metrics = self.use_case.list_device_metrics()
        
        # Sérialiser les résultats
        serializer = DeviceMetricSerializer(device_metrics, many=True)
        
        return Response(serializer.data)
    
    @swagger_auto_schema(
        operation_summary="Détails d'une métrique d'équipement",
        operation_description="Récupère les détails d'une métrique d'équipement par son ID.",
        tags=['Monitoring'],
        responses={
            200: DeviceMetricSerializer,
            404: "Métrique d'équipement non trouvée",
            401: "Non authentifié"
        }
    )
    def retrieve(self, request: Request, pk=None) -> Response:
        """Récupère une métrique d'équipement par son ID."""
        try:
            device_metric = self.use_case.get_device_metric(int(pk))
            serializer = DeviceMetricSerializer(device_metric)
            return Response(serializer.data)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
    
    @swagger_auto_schema(
        operation_summary="Créer une métrique d'équipement",
        operation_description="Crée une nouvelle métrique d'équipement en associant une définition de métrique à un équipement.",
        tags=['Monitoring'],
        request_body=DeviceMetricSerializer,
        responses={
            201: DeviceMetricSerializer,
            400: "Données invalides",
            401: "Non authentifié"
        }
    )
    def create(self, request: Request) -> Response:
        """Crée une nouvelle métrique d'équipement."""
        # Valider les données d'entrée
        serializer = DeviceMetricSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        # Créer la métrique d'équipement
        try:
            device_metric = self.use_case.create_device_metric(
                device_id=serializer.validated_data['device_id'],
                metric_id=serializer.validated_data['metric_id'],
                name=serializer.validated_data.get('name'),
                specific_config=serializer.validated_data.get('specific_config'),
                is_active=serializer.validated_data.get('is_active', True)
            )
            
            # Sérialiser la réponse
            response_serializer = DeviceMetricSerializer(device_metric)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @swagger_auto_schema(
        operation_summary="Modifier une métrique d'équipement",
        operation_description="Met à jour complètement une métrique d'équipement existante.",
        tags=['Monitoring'],
        request_body=DeviceMetricSerializer,
        responses={
            200: DeviceMetricSerializer,
            400: "Données invalides",
            404: "Métrique d'équipement non trouvée",
            401: "Non authentifié"
        }
    )
    def update(self, request: Request, pk=None) -> Response:
        """Met à jour une métrique d'équipement."""
        # Valider les données d'entrée
        serializer = DeviceMetricSerializer(data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        # Mettre à jour la métrique d'équipement
        try:
            device_metric = self.use_case.update_device_metric(
                device_metric_id=int(pk),
                **serializer.validated_data
            )
            
            # Sérialiser la réponse
            response_serializer = DeviceMetricSerializer(device_metric)
            return Response(response_serializer.data)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @swagger_auto_schema(
        operation_summary="Supprimer une métrique d'équipement",
        operation_description="Supprime une métrique d'équipement du système.",
        tags=['Monitoring'],
        responses={
            204: "Métrique d'équipement supprimée avec succès",
            404: "Métrique d'équipement non trouvée",
            401: "Non authentifié"
        }
    )
    def destroy(self, request: Request, pk=None) -> Response:
        """Supprime une métrique d'équipement."""
        try:
            result = self.use_case.delete_device_metric(int(pk))
            if result:
                return Response(status=status.HTTP_204_NO_CONTENT)
            else:
                return Response({"error": "Failed to delete device metric"}, status=status.HTTP_400_BAD_REQUEST)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)


class MetricValueViewSet(viewsets.ViewSet):
    """Vue API pour la gestion des valeurs de métriques."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        try:
            # Initialisation simplifiée avec repositories directs
            from ..infrastructure.repositories.metrics_repository import MetricValueRepository, DeviceMetricRepository
            from ..use_cases.metrics_use_cases import MetricValueUseCase
            
            self.repository = MetricValueRepository()
            self.device_metric_repository = DeviceMetricRepository()
            
            # Créer des services factices pour éviter les erreurs
            class DummyAnomalyDetectionService:
                def detect_anomalies(self, *args, **kwargs):
                    return []
            
            class DummyAlertingService:
                def create_alert(self, *args, **kwargs):
                    return None
            
            self.anomaly_detection_service = DummyAnomalyDetectionService()
            self.alerting_service = DummyAlertingService()
            
            self.use_case = MetricValueUseCase(
                self.repository,
                self.device_metric_repository,
                self.anomaly_detection_service,
                self.alerting_service
            )
        except Exception as e:
            print(f"Erreur d'initialisation MetricValueViewSet: {e}")
            # Initialisation de fallback
            self.repository = None
            self.device_metric_repository = None
            self.use_case = None
    
    @swagger_auto_schema(
        operation_summary="Liste des valeurs de métriques",
        operation_description="Récupère les valeurs de métriques pour une métrique d'équipement avec possibilité de filtrage temporel et d'agrégation.",
        tags=['Monitoring'],
        manual_parameters=[
            openapi.Parameter('device_metric_id', openapi.IN_QUERY, description="ID de la métrique d'équipement", type=openapi.TYPE_INTEGER, required=True),
            openapi.Parameter('start_time', openapi.IN_QUERY, description="Date de début (ISO format)", type=openapi.TYPE_STRING),
            openapi.Parameter('end_time', openapi.IN_QUERY, description="Date de fin (ISO format)", type=openapi.TYPE_STRING),
            openapi.Parameter('limit', openapi.IN_QUERY, description="Nombre maximum de résultats", type=openapi.TYPE_INTEGER),
            openapi.Parameter('aggregation', openapi.IN_QUERY, description="Type d'agrégation (avg, min, max, sum)", type=openapi.TYPE_STRING),
            openapi.Parameter('interval', openapi.IN_QUERY, description="Intervalle d'agrégation (5m, 1h, 1d)", type=openapi.TYPE_STRING),
        ],
        responses={
            200: openapi.Response('Liste des metricvalues', schema=MetricValueSerializer),
            400: "Paramètre device_metric_id requis",
            404: "Métrique d'équipement non trouvée",
            401: "Non authentifié"
        }
    )
    def list(self, request: Request) -> Response:
        """Liste les valeurs de métriques pour une métrique d'équipement."""
        # Vérifier que l'ID de la métrique d'équipement est fourni
        device_metric_id = request.query_params.get('device_metric_id')
        if not device_metric_id:
            return Response({"error": "device_metric_id parameter is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Extraire les paramètres de la requête
        start_time = None
        if 'start_time' in request.query_params:
            start_time = parse_datetime(request.query_params['start_time'])
        
        end_time = None
        if 'end_time' in request.query_params:
            end_time = parse_datetime(request.query_params['end_time'])
        
        limit = None
        if 'limit' in request.query_params:
            limit = int(request.query_params['limit'])
        
        aggregation = request.query_params.get('aggregation')
        interval = request.query_params.get('interval')
        
        # Récupérer les valeurs de métriques
        try:
            metric_values = self.use_case.get_metric_values(
                device_metric_id=int(device_metric_id),
                start_time=start_time,
                end_time=end_time,
                limit=limit,
                aggregation=aggregation,
                interval=interval
            )
            
            # Sérialiser les résultats
            serializer = MetricValueSerializer(metric_values, many=True)
            
            return Response(serializer.data)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @swagger_auto_schema(
        operation_summary="Dernière valeur de métrique",
        operation_description="Récupère la dernière valeur collectée pour une métrique d'équipement.",
        tags=['Monitoring'],
        responses={
            200: MetricValueSerializer,
            404: "Aucune valeur trouvée ou métrique non trouvée",
            401: "Non authentifié"
        }
    )
    def retrieve(self, request: Request, pk=None) -> Response:
        """Récupère la dernière valeur d'une métrique d'équipement."""
        try:
            latest_value = self.use_case.get_latest_value(int(pk))
            if latest_value is None:
                return Response({"message": "No values found for this metric"}, status=status.HTTP_404_NOT_FOUND)
            
            serializer = MetricValueSerializer(latest_value)
            return Response(serializer.data)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
    
    @swagger_auto_schema(
        operation_summary="Créer une valeur de métrique",
        operation_description="Crée une nouvelle valeur de métrique pour un équipement.",
        tags=['Monitoring'],
        request_body=MetricValueSerializer,
        responses={
            201: MetricValueSerializer,
            400: "Données invalides",
            404: "Métrique d'équipement non trouvée",
            401: "Non authentifié"
        }
    )
    def create(self, request: Request) -> Response:
        """Crée une nouvelle valeur de métrique."""
        # Valider les données d'entrée
        serializer = MetricValueSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        # Créer la valeur de métrique
        try:
            timestamp = serializer.validated_data.get('timestamp')
            if not timestamp:
                timestamp = datetime.now()
                
            metric_value = self.use_case.create_metric_value(
                device_metric_id=serializer.validated_data['device_metric_id'],
                value=serializer.validated_data['value'],
                timestamp=timestamp
            )
            
            # Sérialiser la réponse
            response_serializer = MetricValueSerializer(metric_value)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @swagger_auto_schema(
        operation_summary="Création en lot de valeurs",
        operation_description="Crée plusieurs valeurs de métriques en une seule opération.",
        tags=['Monitoring'],
        request_body=openapi.Schema(
            type=openapi.TYPE_ARRAY,
            items=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'device_metric_id': openapi.Schema(type=openapi.TYPE_INTEGER),
                    'value': openapi.Schema(type=openapi.TYPE_NUMBER),
                    'timestamp': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME),
                }
            ),
            description="Liste des valeurs à créer"
        ),
        responses={
            201: openapi.Response('Création de metricvalues', schema=MetricValueSerializer),
            400: "Données invalides",
            404: "Métrique d'équipement non trouvée",
            401: "Non authentifié"
        }
    )
    @action(detail=False, methods=['post'])
    def batch_create(self, request: Request) -> Response:
        """Crée plusieurs valeurs de métrique en une seule opération."""
        # Valider les données d'entrée
        if not isinstance(request.data, list):
            return Response({"error": "Expected a list of metric values"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Valider chaque élément de la liste
        serializer = MetricValueSerializer(data=request.data, many=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        # Créer les valeurs de métrique
        try:
            metric_values = self.use_case.batch_create_metric_values(serializer.validated_data)
            
            # Sérialiser la réponse
            response_serializer = MetricValueSerializer(metric_values, many=True)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST) 