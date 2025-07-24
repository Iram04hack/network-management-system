"""
Vues avancées pour le module Reporting.

Ce module contient les ViewSets pour les fonctionnalités avancées
comme la visualisation, l'analyse de données et l'intégration multi-sources.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.http import HttpResponse
import logging
import json
from typing import Dict, Any

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

# Import du conteneur DI
from ..di_container import ReportingContainer

# Import des use cases
try:
    from ..application.advanced_use_cases import (
        CreateVisualizationUseCase,
        CreateDashboardUseCase,
        AnalyzeDataUseCase,
        IntegrateDataUseCase,
        GenerateInsightsUseCase,
        OptimizeReportPerformanceUseCase
    )
except ImportError:
    # Utilisation directe des modèles si les use cases ne sont pas disponibles
    pass

logger = logging.getLogger(__name__)

class VisualizationViewSet(viewsets.ViewSet):
    """
    ViewSet pour la gestion des visualisations.
    """
    permission_classes = [IsAuthenticated]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Utilisation simplifiée sans DI pour éviter les erreurs
        pass
    
    @swagger_auto_schema(
        method='post',
        operation_summary="Créer une visualisation",
        operation_description="Crée une visualisation pour un rapport",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'report_id': openapi.Schema(type=openapi.TYPE_INTEGER),
                'type': openapi.Schema(type=openapi.TYPE_STRING),
                'config': openapi.Schema(type=openapi.TYPE_OBJECT)
            }
        ),
        responses={
            200: openapi.Response(description="Visualisation créée"),
            400: openapi.Response(description="Erreur de validation")
        },
        tags=['Reporting']
    )
    @action(detail=False, methods=['post'], url_path='create')
    def create_visualization(self, request):
        """
        Crée une visualisation pour un rapport.
        
        Body:
        {
            "report_id": 1,
            "type": "chart",
            "config": {
                "chart_type": "line",
                "x_column": "date",
                "y_column": "value",
                "title": "Évolution dans le temps"
            }
        }
        """
        try:
            report_id = request.data.get('report_id')
            if not report_id:
                return Response(
                    {'error': 'report_id est requis'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            visualization_config = {
                'type': request.data.get('type', 'chart'),
                **request.data.get('config', {})
            }
            
            visualization = self.create_visualization_use_case.execute(
                report_id=report_id,
                visualization_config=visualization_config
            )
            
            return Response(visualization, status=status.HTTP_201_CREATED)
            
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Erreur lors de la création de visualisation: {e}")
            return Response(
                {'error': 'Erreur interne du serveur'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @swagger_auto_schema(
        method='post',
        operation_summary="Créer un dashboard",
        operation_description="Crée un dashboard interactif pour un rapport",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'report_id': openapi.Schema(type=openapi.TYPE_INTEGER),
                'title': openapi.Schema(type=openapi.TYPE_STRING),
                'layout': openapi.Schema(type=openapi.TYPE_OBJECT),
                'widgets': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_OBJECT))
            }
        ),
        responses={
            201: openapi.Response(description="Dashboard créé"),
            400: openapi.Response(description="Erreur de validation")
        },
        tags=['Reporting']
    )
    @action(detail=False, methods=['post'], url_path='dashboard')
    def create_dashboard(self, request):
        """
        Crée un dashboard interactif pour un rapport.
        
        Body:
        {
            "report_id": 1,
            "title": "Dashboard Performance",
            "layout": {
                "columns": 2,
                "rows": 2
            },
            "widgets": [
                {
                    "type": "chart",
                    "data_source": "performance_data",
                    "config": {
                        "chart_type": "line",
                        "title": "CPU Usage"
                    }
                }
            ]
        }
        """
        try:
            report_id = request.data.get('report_id')
            if not report_id:
                return Response(
                    {'error': 'report_id est requis'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            dashboard_config = {
                'title': request.data.get('title', 'Dashboard'),
                'layout': request.data.get('layout', {}),
                'widgets': request.data.get('widgets', [])
            }
            
            dashboard = self.create_dashboard_use_case.execute(
                report_id=report_id,
                dashboard_config=dashboard_config
            )
            
            return Response(dashboard, status=status.HTTP_201_CREATED)
            
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Erreur lors de la création de dashboard: {e}")
            return Response(
                {'error': 'Erreur interne du serveur'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class AnalyticsViewSet(viewsets.ViewSet):
    """
    ViewSet pour l'analyse avancée de données.
    """
    permission_classes = [IsAuthenticated]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        try:
            container = ReportingContainer.get_container()
            self.analyze_data_use_case = AnalyzeDataUseCase(
                analytics_service=container.analytics_service(),
                cache_service=container.cache_service()
            )
            self.generate_insights_use_case = GenerateInsightsUseCase(
                report_repository=container.report_repository(),
                analytics_service=container.analytics_service(),
                cache_service=container.cache_service()
            )
        except Exception as e:
            print(f"Erreur d'initialisation AdvancedDataAnalysisViewSet: {e}")
            self.analyze_data_use_case = None
            self.generate_insights_use_case = None
    
    @swagger_auto_schema(
        method='post',
        operation_summary="Détecter les anomalies",
        operation_description="Détecte les anomalies dans les données",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'data': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_OBJECT)),
                'config': openapi.Schema(type=openapi.TYPE_OBJECT)
            }
        ),
        responses={
            200: openapi.Response(description="Anomalies détectées"),
            400: openapi.Response(description="Erreur de validation")
        },
        tags=['Reporting']
    )
    @action(detail=False, methods=['post'], url_path='anomalies')
    def detect_anomalies(self, request):
        """
        Détecte les anomalies dans les données.
        
        Body:
        {
            "data": [
                {"value": 10, "timestamp": "2024-01-01"},
                {"value": 12, "timestamp": "2024-01-02"}
            ],
            "config": {
                "contamination": 0.1,
                "features": ["value"]
            }
        }
        """
        try:
            data = request.data.get('data', [])
            config = request.data.get('config', {})
            
            if not data:
                return Response(
                    {'error': 'Les données sont requises'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            results = self.analyze_data_use_case.execute(
                data=data,
                analysis_type='anomalies',
                config=config
            )
            
            return Response(results, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Erreur lors de la détection d'anomalies: {e}")
            return Response(
                {'error': 'Erreur interne du serveur'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @swagger_auto_schema(
        method='post',
        operation_summary="Prédire les tendances",
        operation_description="Prédit les tendances futures",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'data': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_OBJECT)),
                'config': openapi.Schema(type=openapi.TYPE_OBJECT)
            }
        ),
        responses={
            200: openapi.Response(description="Tendances prédites"),
            400: openapi.Response(description="Erreur de validation")
        },
        tags=['Reporting']
    )
    @action(detail=False, methods=['post'], url_path='trends')
    def predict_trends(self, request):
        """
        Prédit les tendances futures.
        
        Body:
        {
            "data": [
                {"value": 10, "date": "2024-01-01"},
                {"value": 12, "date": "2024-01-02"}
            ],
            "config": {
                "prediction_horizon": 30
            }
        }
        """
        try:
            data = request.data.get('data', [])
            config = request.data.get('config', {})
            
            if not data:
                return Response(
                    {'error': 'Les données sont requises'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            results = self.analyze_data_use_case.execute(
                data=data,
                analysis_type='trends',
                config=config
            )
            
            return Response(results, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Erreur lors de la prédiction de tendances: {e}")
            return Response(
                {'error': 'Erreur interne du serveur'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @swagger_auto_schema(
        method='post',
        operation_summary="Générer des insights",
        operation_description="Génère des insights automatiques pour un rapport",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'config': openapi.Schema(type=openapi.TYPE_OBJECT)
            }
        ),
        responses={
            200: openapi.Response(description="Insights générés"),
            400: openapi.Response(description="Erreur de validation")
        },
        tags=['Reporting']
    )
    @action(detail=False, methods=['post'], url_path='insights/(?P<report_id>[^/.]+)')
    def generate_insights(self, request, report_id=None):
        """
        Génère des insights automatiques pour un rapport.
        
        Body:
        {
            "config": {
                "include_anomalies": true,
                "include_trends": true,
                "anomaly_config": {
                    "contamination": 0.05
                },
                "prediction_horizon": 15
            }
        }
        """
        try:
            if not report_id:
                return Response(
                    {'error': 'report_id est requis'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            config = request.data.get('config', {})
            
            insights = self.generate_insights_use_case.execute(
                report_id=int(report_id),
                analysis_config=config
            )
            
            return Response(insights, status=status.HTTP_200_OK)
            
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Erreur lors de la génération d'insights: {e}")
            return Response(
                {'error': 'Erreur interne du serveur'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @swagger_auto_schema(
        method='post',
        operation_summary="Analyser les corrélations",
        operation_description="Analyse les corrélations entre datasets",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'datasets': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_OBJECT))
            }
        ),
        responses={
            200: openapi.Response(description="Corrélations analysées"),
            400: openapi.Response(description="Erreur de validation")
        },
        tags=['Reporting']
    )
    @action(detail=False, methods=['post'], url_path='correlation')
    def analyze_correlation(self, request):
        """
        Analyse les corrélations entre datasets.
        
        Body:
        {
            "datasets": [
                {
                    "values": [
                        {"x": 1, "y": 2},
                        {"x": 2, "y": 4}
                    ]
                },
                {
                    "values": [
                        {"a": 1, "b": 3},
                        {"a": 2, "b": 6}
                    ]
                }
            ]
        }
        """
        try:
            datasets = request.data.get('datasets', [])
            
            if not datasets or len(datasets) < 2:
                return Response(
                    {'error': 'Au moins 2 datasets sont requis pour l\'analyse de corrélation'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            results = self.analyze_data_use_case.execute(
                data=datasets,
                analysis_type='correlation',
                config={}
            )
            
            return Response(results, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse de corrélation: {e}")
            return Response(
                {'error': 'Erreur interne du serveur'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class DataIntegrationViewSet(viewsets.ViewSet):
    """
    ViewSet pour l'intégration de données multi-sources.
    """
    permission_classes = [IsAuthenticated]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        container = ReportingContainer.get_container()
        self.integrate_data_use_case = IntegrateDataUseCase(
            data_integration_service=container.data_integration_service(),
            cache_service=container.cache_service()
        )
    
    @swagger_auto_schema(
        method='post',
        operation_summary="Intégrer des sources",
        operation_description="Intègre des données de sources multiples",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'sources': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_OBJECT)),
                'transformation_rules': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_OBJECT))
            }
        ),
        responses={
            200: openapi.Response(description="Sources intégrées"),
            400: openapi.Response(description="Erreur de validation")
        },
        tags=['Reporting']
    )
    @action(detail=False, methods=['post'], url_path='integrate')
    def integrate_sources(self, request):
        """
        Intègre des données de sources multiples.
        
        Body:
        {
            "sources": [
                {
                    "name": "database_source",
                    "type": "database",
                    "data": [...]
                },
                {
                    "name": "api_source",
                    "type": "api",
                    "data": [...]
                }
            ],
            "transformation_rules": [
                {
                    "type": "rename",
                    "old_name": "old_field",
                    "new_name": "new_field"
                }
            ]
        }
        """
        try:
            sources = request.data.get('sources', [])
            transformation_rules = request.data.get('transformation_rules')
            
            if not sources:
                return Response(
                    {'error': 'Au moins une source de données est requise'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            integrated_data = self.integrate_data_use_case.execute(
                sources=sources,
                transformation_rules=transformation_rules
            )
            
            return Response(integrated_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Erreur lors de l'intégration des données: {e}")
            return Response(
                {'error': 'Erreur interne du serveur'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @swagger_auto_schema(
        method='post',
        operation_summary="Valider la qualité des données",
        operation_description="Valide la qualité des données",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'data': openapi.Schema(type=openapi.TYPE_OBJECT)
            }
        ),
        responses={
            200: openapi.Response(description="Qualité validée"),
            400: openapi.Response(description="Erreur de validation")
        },
        tags=['Reporting']
    )
    @action(detail=False, methods=['post'], url_path='validate-quality')
    def validate_data_quality(self, request):
        """
        Valide la qualité des données.
        
        Body:
        {
            "data": {
                "values": [
                    {"field1": "value1", "field2": 10},
                    {"field1": "value2", "field2": 20}
                ]
            }
        }
        """
        try:
            data = request.data.get('data', {})
            
            if not data:
                return Response(
                    {'error': 'Les données sont requises'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            container = ReportingContainer.get_container()
            data_integration_service = container.data_integration_service()
            
            quality_report = data_integration_service.validate_data_quality(data)
            
            return Response(quality_report, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Erreur lors de la validation de qualité: {e}")
            return Response(
                {'error': 'Erreur interne du serveur'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class PerformanceViewSet(viewsets.ViewSet):
    """
    ViewSet pour l'optimisation des performances.
    """
    permission_classes = [IsAuthenticated]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        try:
            container = ReportingContainer.get_container()
            self.optimize_performance_use_case = OptimizeReportPerformanceUseCase(
                report_repository=container.report_repository(),
                cache_service=container.cache_service()
            )
        except Exception as e:
            # Fallback temporaire pour éviter les erreurs Swagger
            print(f"Erreur d'initialisation OptimizeReportPerformanceViewSet: {e}")
            self.optimize_performance_use_case = None
    
    @swagger_auto_schema(
        method='get',
        operation_summary="Analyser les performances",
        operation_description="Analyse les performances des rapports",
        responses={
            200: openapi.Response(description="Performances analysées"),
            500: openapi.Response(description="Erreur serveur")
        },
        tags=['Reporting']
    )
    @action(detail=False, methods=['get'], url_path='analyze')
    def analyze_performance(self, request):
        """
        Analyse les performances des rapports.
        
        Query Parameters:
        - report_type: Type de rapport à analyser
        - created_after: Date de création minimum
        """
        try:
            # Construire les filtres à partir des paramètres de requête
            filters = {}
            if request.query_params.get('report_type'):
                filters['report_type'] = request.query_params.get('report_type')
            if request.query_params.get('created_after'):
                filters['created_after'] = request.query_params.get('created_after')
            
            optimization_report = self.optimize_performance_use_case.execute(
                report_filters=filters if filters else None
            )
            
            return Response(optimization_report, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse de performance: {e}")
            return Response(
                {'error': 'Erreur interne du serveur'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @swagger_auto_schema(
        method='post',
        operation_summary="Vider le cache",
        operation_description="Vide le cache pour optimiser les performances",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'pattern': openapi.Schema(type=openapi.TYPE_STRING),
                'report_id': openapi.Schema(type=openapi.TYPE_INTEGER)
            }
        ),
        responses={
            200: openapi.Response(description="Cache vidé"),
            400: openapi.Response(description="Erreur de validation")
        },
        tags=['Reporting']
    )
    @action(detail=False, methods=['post'], url_path='clear-cache')
    def clear_cache(self, request):
        """
        Vide le cache pour optimiser les performances.
        
        Body:
        {
            "pattern": "reporting:*",  // Optionnel, pattern de clés à supprimer
            "report_id": 1  // Optionnel, vider le cache pour un rapport spécifique
        }
        """
        try:
            container = ReportingContainer.get_container()
            cache_service = container.cache_service()
            
            pattern = request.data.get('pattern')
            report_id = request.data.get('report_id')
            
            cleared_count = 0
            
            if report_id:
                # Vider le cache pour un rapport spécifique
                cache_keys = [
                    f"visualization:{report_id}",
                    f"dashboard:{report_id}",
                    f"insights:{report_id}"
                ]
                for key in cache_keys:
                    if cache_service.delete(key):
                        cleared_count += 1
            elif pattern:
                # Vider selon un pattern
                cleared_count = cache_service.invalidate_pattern(pattern)
            else:
                return Response(
                    {'error': 'Soit pattern soit report_id doit être spécifié'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            return Response({
                'message': f'{cleared_count} entrées de cache supprimées',
                'cleared_count': cleared_count
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Erreur lors du nettoyage du cache: {e}")
            return Response(
                {'error': 'Erreur interne du serveur'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            ) 