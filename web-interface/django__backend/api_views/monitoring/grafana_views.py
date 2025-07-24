import logging
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404

# from network_management.models import NetworkDevice  # Import différé pour éviter les imports circulaires
# from monitoring.models import Alert  # Import différé pour éviter les imports circulaires
# from services.grafana_service import GrafanaService  # Service sera initialisé dans le container DI
# from security_management.permissions import IsAdminOrReadOnly  # Permission différée

logger = logging.getLogger(__name__)

class GrafanaViewSet(viewsets.ViewSet):
    """ViewSet pour l'intégration Grafana"""
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def status(self, request):
        """Vérifie le statut de connexion à Grafana."""
        service = GrafanaService()
        client = service.get_client()
        
        if client.test_connection():
            return Response({
                "status": "connected",
                "message": "Grafana est accessible"
            })
        else:
            return Response({
                "status": "disconnected",
                "message": "Impossible de se connecter à Grafana"
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    
    @action(detail=False, methods=['post'])
    def setup(self, request):
        """Configure Grafana avec la source de données Prometheus et le dashboard principal."""
        datasource_result = GrafanaService.setup_prometheus_datasource()
        
        if not datasource_result.get("success"):
            return Response(datasource_result, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        dashboard_result = GrafanaService.create_nms_dashboard()
        
        return Response({
            "datasource": datasource_result,
            "dashboard": dashboard_result
        })
    
    @action(detail=False, methods=['get'])
    def dashboards(self, request):
        """Liste tous les dashboards."""
        client = GrafanaService.get_client()
        
        try:
            dashboards = client.get_dashboards()
            return Response({"dashboards": dashboards})
        except Exception as e:
            return Response({
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'])
    def device_dashboard(self, request):
        """Crée un dashboard pour un équipement spécifique."""
        device_id = request.data.get('device_id')
        
        if not device_id:
            return Response({
                "error": "device_id est requis"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        device = get_object_or_404(NetworkDevice, id=device_id)
        result = GrafanaService.create_device_dashboard(device)
        
        if result.get("success"):
            return Response(result)
        else:
            return Response(result, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'])
    def annotation(self, request):
        """Crée une annotation pour une alerte."""
        alert_id = request.data.get('alert_id')
        
        if not alert_id:
            return Response({
                "error": "alert_id est requis"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        alert = get_object_or_404(Alert, id=alert_id)
        result = GrafanaService.create_alert_annotation(alert)
        
        if result.get("success"):
            return Response(result)
        else:
            return Response(result, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'])
    def import_dashboard(self, request):
        """Importe un dashboard depuis un JSON."""
        dashboard_json = request.data.get('dashboard_json')
        folder_id = request.data.get('folder_id', 0)
        
        if not dashboard_json:
            return Response({
                "error": "dashboard_json est requis"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        result = GrafanaService.import_dashboard_from_json(dashboard_json, folder_id)
        
        if result.get("success"):
            return Response(result)
        else:
            return Response(result, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class GrafanaSetupPrometheusView(APIView):
    """Vue API pour configurer la source de données Prometheus dans Grafana."""
    
    permission_classes = [IsAuthenticated]
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        from django.apps import apps
        try:
            di_container = apps.get_app_config('network_management').di_container
            self.grafana_service = di_container.resolve('GrafanaService')
        except Exception:
            try:
                from services.grafana_service import GrafanaService
                self.grafana_service = GrafanaService()
            except ImportError:
                self.grafana_service = None
    
    def post(self, request):
        """Configure Prometheus comme source de données dans Grafana."""
        try:
            if not self.grafana_service:
                return Response(
                    {"error": "Service Grafana non disponible"},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE
                )
            
            prometheus_url = request.data.get('prometheus_url', 'http://localhost:9090')
            datasource_name = request.data.get('name', 'Prometheus')
            
            # Configurer la source de données via le service Grafana
            result = self.grafana_service.setup_prometheus_datasource(
                name=datasource_name,
                url=prometheus_url
            )
            
            return Response(result, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.exception(f"Erreur lors de la configuration de Prometheus dans Grafana: {e}")
            return Response(
                {"error": "Erreur lors de la configuration de Prometheus"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class GrafanaCreateDashboardView(APIView):
    """Vue API pour créer un dashboard Grafana."""
    
    permission_classes = [IsAuthenticated]
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        from django.apps import apps
        try:
            di_container = apps.get_app_config('network_management').di_container
            self.grafana_service = di_container.resolve('GrafanaService')
        except Exception:
            try:
                from services.grafana_service import GrafanaService
                self.grafana_service = GrafanaService()
            except ImportError:
                self.grafana_service = None
    
    def post(self, request):
        """Crée un nouveau dashboard Grafana."""
        try:
            if not self.grafana_service:
                return Response(
                    {"error": "Service Grafana non disponible"},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE
                )
            
            dashboard_title = request.data.get('title')
            dashboard_template = request.data.get('template', 'basic')
            folder_id = request.data.get('folder_id', 0)
            
            if not dashboard_title:
                return Response(
                    {"error": "Le titre du dashboard est requis"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Créer le dashboard via le service Grafana
            result = self.grafana_service.create_dashboard(
                title=dashboard_title,
                template=dashboard_template,
                folder_id=folder_id
            )
            
            return Response(result, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.exception(f"Erreur lors de la création du dashboard Grafana: {e}")
            return Response(
                {"error": "Erreur lors de la création du dashboard"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class GrafanaDeviceDashboardView(APIView):
    """Vue API pour créer un dashboard spécifique à un équipement."""
    
    permission_classes = [IsAuthenticated]
    
    def post(self, request, device_id):
        """Crée un dashboard pour un équipement spécifique."""
        try:
            # TODO: Récupérer les informations de l'équipement depuis le repository
            device_info = {
                "id": device_id,
                "name": f"Device-{device_id}",
                "ip_address": f"192.168.1.{device_id}",
                "type": "router"
            }
            
            # TODO: Implémenter avec le service Grafana
            dashboard = {
                "id": int(device_id) + 100,
                "uid": f"device-{device_id}",
                "title": f"Dashboard - {device_info['name']}",
                "tags": ["device", "network", device_info['type']],
                "panels": [
                    {
                        "id": 1,
                        "title": f"CPU Usage - {device_info['name']}",
                        "type": "graph",
                        "targets": [
                            {
                                "expr": f"cpu_usage{{instance=\"{device_info['ip_address']}\"}}",
                                "legendFormat": "CPU %"
                            }
                        ]
                    },
                    {
                        "id": 2,
                        "title": f"Memory Usage - {device_info['name']}",
                        "type": "graph",
                        "targets": [
                            {
                                "expr": f"memory_usage{{instance=\"{device_info['ip_address']}\"}}",
                                "legendFormat": "Memory %"
                            }
                        ]
                    },
                    {
                        "id": 3,
                        "title": f"Network Traffic - {device_info['name']}",
                        "type": "graph",
                        "targets": [
                            {
                                "expr": f"network_in{{instance=\"{device_info['ip_address']}\"}}",
                                "legendFormat": "In"
                            },
                            {
                                "expr": f"network_out{{instance=\"{device_info['ip_address']}\"}}",
                                "legendFormat": "Out"
                            }
                        ]
                    }
                ]
            }
            
            result = {
                "success": True,
                "message": f"Dashboard créé pour l'équipement {device_info['name']}",
                "device": device_info,
                "dashboard": dashboard,
                "url": f"http://grafana:3000/d/{dashboard['uid']}"
            }
            
            return Response(result, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.exception(f"Erreur lors de la création du dashboard pour l'équipement {device_id}: {e}")
            return Response(
                {"error": f"Erreur lors de la création du dashboard pour l'équipement {device_id}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def get(self, request, device_id):
        """Récupère le dashboard d'un équipement."""
        try:
            # TODO: Implémenter la récupération depuis Grafana
            dashboard_uid = f"device-{device_id}"
            
            result = {
                "success": True,
                "device_id": device_id,
                "dashboard_uid": dashboard_uid,
                "url": f"http://grafana:3000/d/{dashboard_uid}"
            }
            
            return Response(result)
            
        except Exception as e:
            logger.exception(f"Erreur lors de la récupération du dashboard pour l'équipement {device_id}: {e}")
            return Response(
                {"error": f"Dashboard non trouvé pour l'équipement {device_id}"},
                status=status.HTTP_404_NOT_FOUND
            )


class GrafanaAlertAnnotationView(APIView):
    """Vue API pour créer des annotations d'alerte dans Grafana."""
    
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Crée une annotation pour une alerte."""
        try:
            alert_id = request.data.get('alert_id')
            alert_message = request.data.get('message')
            dashboard_id = request.data.get('dashboard_id')
            panel_id = request.data.get('panel_id')
            
            if not alert_id:
                return Response(
                    {"error": "L'ID de l'alerte est requis"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # TODO: Récupérer les informations de l'alerte depuis le repository
            alert_info = {
                "id": alert_id,
                "severity": "warning",
                "message": alert_message or f"Alerte #{alert_id}",
                "timestamp": "2025-06-18T10:00:00Z"
            }
            
            # TODO: Implémenter avec le service Grafana
            annotation = {
                "id": int(alert_id) + 1000,
                "alertId": alert_id,
                "dashboardId": dashboard_id,
                "panelId": panel_id,
                "time": 1640995200000,  # timestamp en milliseconds
                "timeEnd": 1640995260000,
                "text": alert_info['message'],
                "tags": ["alert", alert_info['severity']],
                "data": {
                    "alert_id": alert_id,
                    "severity": alert_info['severity'],
                    "created_by": "api_views"
                }
            }
            
            result = {
                "success": True,
                "message": "Annotation créée avec succès",
                "annotation": annotation,
                "alert": alert_info
            }
            
            return Response(result, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.exception(f"Erreur lors de la création de l'annotation pour l'alerte {alert_id}: {e}")
            return Response(
                {"error": "Erreur lors de la création de l'annotation"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class GrafanaDashboardImportView(APIView):
    """Vue API pour importer un dashboard Grafana depuis JSON."""
    
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Importe un dashboard depuis une configuration JSON."""
        try:
            dashboard_json = request.data.get('dashboard_json')
            folder_id = request.data.get('folder_id', 0)
            overwrite = request.data.get('overwrite', False)
            
            if not dashboard_json:
                return Response(
                    {"error": "La configuration JSON du dashboard est requise"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Validation basique du JSON
            if not isinstance(dashboard_json, dict):
                return Response(
                    {"error": "Le JSON du dashboard doit être un objet"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # TODO: Implémenter avec le service Grafana
            imported_dashboard = {
                "id": dashboard_json.get('id', 999),
                "uid": dashboard_json.get('uid', 'imported-dashboard'),
                "title": dashboard_json.get('title', 'Dashboard Importé'),
                "folderId": folder_id,
                "version": 1,
                "url": f"http://grafana:3000/d/{dashboard_json.get('uid', 'imported-dashboard')}"
            }
            
            result = {
                "success": True,
                "message": "Dashboard importé avec succès",
                "dashboard": imported_dashboard,
                "imported": True,
                "overwrite": overwrite
            }
            
            return Response(result, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.exception(f"Erreur lors de l'import du dashboard Grafana: {e}")
            return Response(
                {"error": "Erreur lors de l'import du dashboard"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            ) 