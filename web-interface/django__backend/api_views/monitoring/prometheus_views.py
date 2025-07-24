import logging
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404

# from network_management.models import NetworkDevice  # Import différé pour éviter les imports circulaires
# from services.prometheus_service import PrometheusService  # Service sera initialisé dans le container DI
# from security_management.permissions import IsAdminOrReadOnly  # Permission différée

logger = logging.getLogger(__name__)

class PrometheusViewSet(viewsets.ViewSet):
    """ViewSet pour interagir avec Prometheus."""
    
    permission_classes = [IsAuthenticated]
    
    def __init__(self, **kwargs):
        """Initialisation du ViewSet."""
        super().__init__(**kwargs)
        # Import des dépendances depuis le container DI
        from django.apps import apps
        try:
            # Tenter de récupérer le service depuis le container DI
            di_container = apps.get_app_config('network_management').di_container
            self.prometheus_service = di_container.resolve('PrometheusService')
        except Exception:
            # Fallback : tenter d'importer directement
            try:
                from services.prometheus_service import PrometheusService
                self.prometheus_service = PrometheusService()
            except ImportError:
                self.prometheus_service = None
    
    @action(detail=False, methods=['get'])
    def status(self, request):
        """Vérifier le statut de Prometheus."""
        return Response(self.prometheus_service.check_connection())
    
    @action(detail=False, methods=['get'])
    def metrics(self, request):
        """Récupérer des métriques spécifiques."""
        query = request.query_params.get('query', 'up')
        time = request.query_params.get('time')
        
        result = self.prometheus_service.query(query, time)
        return Response(result)
    
    @action(detail=False, methods=['get'])
    def range(self, request):
        """Récupérer des métriques sur une plage de temps."""
        query = request.query_params.get('query', 'up')
        start = request.query_params.get('start')
        end = request.query_params.get('end')
        step = request.query_params.get('step', '1h')
        
        if not start or not end:
            return Response({
                'success': False,
                'error': 'Les paramètres start et end sont requis'
            }, status=400)
        
        result = self.prometheus_service.query_range(query, start, end, step)
        return Response(result)
    
    @action(detail=False, methods=['get'])
    def targets(self, request):
        """Récupérer les cibles de scraping."""
        return Response(self.prometheus_service.get_targets())
    
    @action(detail=False, methods=['get'])
    def alerts(self, request):
        """Récupérer les alertes actives."""
        return Response(self.prometheus_service.get_alerts())
    
    @action(detail=False, methods=['get'])
    def rules(self, request):
        """Récupérer les règles configurées."""
        return Response(self.prometheus_service.get_rules())
    
    @action(detail=False, methods=['get'])
    def metadata(self, request):
        """Récupérer les métadonnées des métriques."""
        metric = request.query_params.get('metric')
        return Response(self.prometheus_service.get_metadata(metric))
    
    @action(detail=False, methods=['get'])
    def series(self, request):
        """Récupérer les séries correspondant aux sélecteurs."""
        match = request.query_params.getlist('match[]')
        start = request.query_params.get('start')
        end = request.query_params.get('end')
        
        if not match:
            return Response({
                'success': False,
                'error': 'Le paramètre match[] est requis'
            }, status=400)
        
        result = self.prometheus_service.get_series(match, start, end)
        return Response(result)
    
    @action(detail=False, methods=['get'])
    def label_values(self, request):
        """Récupérer les valeurs pour un label spécifique."""
        label = request.query_params.get('label')
        
        if not label:
            return Response({
                'success': False,
                'error': 'Le paramètre label est requis'
            }, status=400)
        
        result = self.prometheus_service.get_label_values(label)
        return Response(result)
    
    @action(detail=False, methods=['get'], url_path='metric-history')
    def metric_history(self, request):
        """Récupérer l'historique d'une métrique."""
        metric_name = request.query_params.get('metric')
        duration = request.query_params.get('duration', '1d')
        step = request.query_params.get('step', '1h')
        
        if not metric_name:
            return Response({
                'success': False,
                'error': 'Le paramètre metric est requis'
            }, status=400)
        
        result = self.prometheus_service.get_metric_history(metric_name, duration, step)
        return Response(result)
    
    @action(detail=False, methods=['get'], url_path='device-metrics')
    def device_metrics(self, request):
        """Récupérer les métriques pour un équipement spécifique."""
        device_ip = request.query_params.get('device_ip')
        metrics = request.query_params.getlist('metrics')
        
        if not device_ip:
            return Response({
                'success': False,
                'error': 'Le paramètre device_ip est requis'
            }, status=400)
        
        result = self.prometheus_service.get_device_metrics(device_ip, metrics if metrics else None)
        return Response(result)


class PrometheusQueryView(APIView):
    """Vue API pour les requêtes Prometheus."""
    
    permission_classes = [IsAuthenticated]
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Initialiser le service Prometheus
        from django.apps import apps
        try:
            di_container = apps.get_app_config('network_management').di_container
            self.prometheus_service = di_container.resolve('PrometheusService')
        except Exception:
            try:
                from services.prometheus_service import PrometheusService
                self.prometheus_service = PrometheusService()
            except ImportError:
                self.prometheus_service = None
    
    def post(self, request):
        """Exécute une requête Prometheus."""
        try:
            if not self.prometheus_service:
                return Response(
                    {"error": "Service Prometheus non disponible"},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE
                )
            
            query = request.data.get('query')
            time_param = request.data.get('time')
            
            if not query:
                return Response(
                    {"error": "Le paramètre 'query' est requis"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Exécuter la requête via le service Prometheus
            result = self.prometheus_service.query(query, time_param)
            
            return Response(result)
            
        except Exception as e:
            logger.exception(f"Erreur lors de l'exécution de la requête Prometheus: {e}")
            return Response(
                {"error": "Erreur lors de l'exécution de la requête"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class PrometheusQueryRangeView(APIView):
    """Vue API pour les requêtes Prometheus sur une plage de temps."""
    
    permission_classes = [IsAuthenticated]
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        from django.apps import apps
        try:
            di_container = apps.get_app_config('network_management').di_container
            self.prometheus_service = di_container.resolve('PrometheusService')
        except Exception:
            try:
                from services.prometheus_service import PrometheusService
                self.prometheus_service = PrometheusService()
            except ImportError:
                self.prometheus_service = None
    
    def post(self, request):
        """Exécute une requête Prometheus sur une plage de temps."""
        try:
            if not self.prometheus_service:
                return Response(
                    {"error": "Service Prometheus non disponible"},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE
                )
            
            query = request.data.get('query')
            start = request.data.get('start')
            end = request.data.get('end')
            step = request.data.get('step', '15s')
            
            if not all([query, start, end]):
                return Response(
                    {"error": "Les paramètres 'query', 'start' et 'end' sont requis"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Exécuter la requête range via le service Prometheus
            result = self.prometheus_service.query_range(query, start, end, step)
            
            return Response(result)
            
        except Exception as e:
            logger.exception(f"Erreur lors de l'exécution de la requête range Prometheus: {e}")
            return Response(
                {"error": "Erreur lors de l'exécution de la requête range"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class PrometheusTargetsView(APIView):
    """Vue API pour récupérer les cibles Prometheus."""
    
    permission_classes = [IsAuthenticated]
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        from django.apps import apps
        try:
            di_container = apps.get_app_config('network_management').di_container
            self.prometheus_service = di_container.resolve('PrometheusService')
        except Exception:
            try:
                from services.prometheus_service import PrometheusService
                self.prometheus_service = PrometheusService()
            except ImportError:
                self.prometheus_service = None
    
    def get(self, request):
        """Récupère la liste des cibles Prometheus."""
        try:
            if not self.prometheus_service:
                return Response(
                    {"error": "Service Prometheus non disponible"},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE
                )
            
            # Récupérer les cibles via le service Prometheus
            targets = self.prometheus_service.get_targets()
            
            return Response(targets)
            
        except Exception as e:
            logger.exception(f"Erreur lors de la récupération des cibles Prometheus: {e}")
            return Response(
                {"error": "Erreur lors de la récupération des cibles"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class PrometheusAlertsView(APIView):
    """Vue API pour récupérer les alertes Prometheus."""
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Récupère la liste des alertes Prometheus."""
        try:
            # TODO: Implémenter avec le service Prometheus
            alerts = {
                "status": "success",
                "data": {
                    "alerts": [
                        {
                            "labels": {"alertname": "HighCPUUsage", "instance": "server1"},
                            "annotations": {"description": "CPU usage is above 80%"},
                            "state": "firing",
                            "activeAt": "2025-06-18T09:30:00Z",
                            "value": "85.2"
                        }
                    ]
                }
            }
            
            return Response(alerts)
            
        except Exception as e:
            logger.exception(f"Erreur lors de la récupération des alertes Prometheus: {e}")
            return Response(
                {"error": "Erreur lors de la récupération des alertes"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class PrometheusRulesView(APIView):
    """Vue API pour récupérer les règles Prometheus."""
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Récupère la liste des règles Prometheus."""
        try:
            # TODO: Implémenter avec le service Prometheus
            rules = {
                "status": "success",
                "data": {
                    "groups": [
                        {
                            "name": "system.rules",
                            "file": "/etc/prometheus/rules/system.yml",
                            "rules": [
                                {
                                    "name": "HighCPUUsage",
                                    "query": "cpu_usage > 80",
                                    "duration": "5m",
                                    "labels": {"severity": "warning"}
                                }
                            ]
                        }
                    ]
                }
            }
            
            return Response(rules)
            
        except Exception as e:
            logger.exception(f"Erreur lors de la récupération des règles Prometheus: {e}")
            return Response(
                {"error": "Erreur lors de la récupération des règles"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class PrometheusSeriesView(APIView):
    """Vue API pour récupérer les séries Prometheus."""
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Récupère les séries Prometheus correspondant aux sélecteurs."""
        try:
            match = request.query_params.getlist('match[]')
            
            if not match:
                return Response(
                    {"error": "Le paramètre 'match[]' est requis"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # TODO: Implémenter avec le service Prometheus
            series = {
                "status": "success",
                "data": [
                    {"__name__": "cpu_usage", "instance": "server1", "job": "node_exporter"},
                    {"__name__": "memory_usage", "instance": "server1", "job": "node_exporter"}
                ]
            }
            
            return Response(series)
            
        except Exception as e:
            logger.exception(f"Erreur lors de la récupération des séries Prometheus: {e}")
            return Response(
                {"error": "Erreur lors de la récupération des séries"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class PrometheusMetadataView(APIView):
    """Vue API pour récupérer les métadonnées Prometheus."""
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Récupère les métadonnées des métriques Prometheus."""
        try:
            metric = request.query_params.get('metric')
            
            # TODO: Implémenter avec le service Prometheus
            metadata = {
                "status": "success",
                "data": {
                    "cpu_usage": [
                        {
                            "type": "gauge",
                            "help": "CPU usage percentage",
                            "unit": "percent"
                        }
                    ],
                    "memory_usage": [
                        {
                            "type": "gauge", 
                            "help": "Memory usage in bytes",
                            "unit": "bytes"
                        }
                    ]
                }
            }
            
            if metric:
                metadata["data"] = {metric: metadata["data"].get(metric, [])}
            
            return Response(metadata)
            
        except Exception as e:
            logger.exception(f"Erreur lors de la récupération des métadonnées Prometheus: {e}")
            return Response(
                {"error": "Erreur lors de la récupération des métadonnées"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class PrometheusDeviceMetricsView(APIView):
    """Vue API pour récupérer les métriques d'un équipement spécifique."""
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request, device_ip):
        """Récupère les métriques pour un équipement spécifique."""
        try:
            metrics = request.query_params.getlist('metrics')
            
            # TODO: Implémenter avec le service Prometheus
            device_metrics = {
                "device_ip": device_ip,
                "timestamp": "2025-06-18T10:00:00Z",
                "metrics": {
                    "cpu_usage": {"value": 45.2, "unit": "percent"},
                    "memory_usage": {"value": 2147483648, "unit": "bytes"},
                    "disk_usage": {"value": 75.8, "unit": "percent"},
                    "network_in": {"value": 1024000, "unit": "bytes/sec"},
                    "network_out": {"value": 512000, "unit": "bytes/sec"}
                }
            }
            
            # Filtrer les métriques si spécifiées
            if metrics:
                filtered_metrics = {k: v for k, v in device_metrics["metrics"].items() if k in metrics}
                device_metrics["metrics"] = filtered_metrics
            
            return Response(device_metrics)
            
        except Exception as e:
            logger.exception(f"Erreur lors de la récupération des métriques de l'équipement {device_ip}: {e}")
            return Response(
                {"error": f"Erreur lors de la récupération des métriques de l'équipement {device_ip}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            ) 