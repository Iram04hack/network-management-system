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

from ..domain.interfaces.repositories import (
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
        self.repository = MetricsDefinitionRepository()
        self.use_case = MetricsDefinitionUseCase(self.repository)
    
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
    
    def retrieve(self, request: Request, pk=None) -> Response:
        """Récupère une définition de métrique par son ID."""
        try:
            metrics_definition = self.use_case.get_metrics_definition(int(pk))
            serializer = MetricsDefinitionSerializer(metrics_definition)
            return Response(serializer.data)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
    
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
        self.repository = DeviceMetricRepository()
        self.metrics_definition_repository = MetricsDefinitionRepository()
        self.use_case = DeviceMetricUseCase(self.repository, self.metrics_definition_repository)
    
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
    
    def retrieve(self, request: Request, pk=None) -> Response:
        """Récupère une métrique d'équipement par son ID."""
        try:
            device_metric = self.use_case.get_device_metric(int(pk))
            serializer = DeviceMetricSerializer(device_metric)
            return Response(serializer.data)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
    
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
        self.repository = MetricValueRepository()
        self.device_metric_repository = DeviceMetricRepository()
        self.metrics_analysis_service = MetricsAnalysisService()
        self.alert_service = AlertService()
        self.use_case = MetricValueUseCase(
            self.repository,
            self.device_metric_repository,
            self.metrics_analysis_service,
            self.alert_service
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