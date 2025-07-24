import logging
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

# from services.suricata_service import SuricataService  # Service sera initialisé dans le container DI
# from security_management.permissions import IsAdminOrReadOnly  # Permission différée

logger = logging.getLogger(__name__)

class SuricataViewSet(viewsets.ViewSet):
    """ViewSet pour l'intégration Suricata"""
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def status(self, request):
        """Vérifie le statut de connexion à Suricata."""
        service = SuricataService()
        client = service.get_client()
        
        if client.test_connection():
            return Response({
                "status": "connected",
                "message": "Suricata est accessible"
            })
        else:
            return Response({
                "status": "disconnected",
                "message": "Impossible de se connecter à Suricata"
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    
    @action(detail=False, methods=['get'])
    def alerts(self, request):
        """Récupère toutes les alertes Suricata."""
        limit = int(request.query_params.get('limit', 100))
        offset = int(request.query_params.get('offset', 0))
        severity = request.query_params.get('severity')
        
        result = SuricataService.get_alerts(limit, offset, severity)
        
        if result.get("success"):
            return Response(result)
        else:
            return Response(result, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'])
    def rules(self, request):
        """Récupère toutes les règles Suricata."""
        result = SuricataService.get_rules()
        
        if result.get("success"):
            return Response(result)
        else:
            return Response(result, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'])
    def add_rule(self, request):
        """Ajoute une nouvelle règle Suricata."""
        rule_content = request.data.get('rule_content')
        name = request.data.get('name', 'custom_rule')
        
        if not rule_content:
            return Response({
                "error": "rule_content est requis"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        result = SuricataService.add_rule(rule_content, name)
        
        if result.get("success"):
            return Response(result)
        else:
            return Response(result, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['post'])
    def toggle_rule(self, request, pk=None):
        """Active ou désactive une règle Suricata."""
        enabled = request.data.get('enabled')
        
        if enabled is None:
            return Response({
                "error": "enabled est requis (true/false)"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        result = SuricataService.toggle_rule(pk, enabled)
        
        if result.get("success"):
            return Response(result)
        else:
            return Response(result, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'])
    def reload(self, request):
        """Recharge les règles Suricata."""
        result = SuricataService.reload_rules()
        
        if result.get("success"):
            return Response(result)
        else:
            return Response(result, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SuricataAlertsView(APIView):
    """Vue API pour récupérer les alertes Suricata."""
    
    permission_classes = [IsAuthenticated]
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        from django.apps import apps
        try:
            di_container = apps.get_app_config('network_management').di_container
            self.suricata_service = di_container.resolve('SuricataService')
        except Exception:
            try:
                from services.suricata_service import SuricataService
                self.suricata_service = SuricataService()
            except ImportError:
                self.suricata_service = None
    
    def get(self, request):
        """Récupère les alertes Suricata avec filtrage."""
        try:
            if not self.suricata_service:
                return Response(
                    {"error": "Service Suricata non disponible"},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE
                )
            
            # Paramètres de filtrage
            filters = {
                'severity': request.query_params.get('severity'),
                'start_date': request.query_params.get('start_date'),
                'end_date': request.query_params.get('end_date'),
                'source_ip': request.query_params.get('source_ip'),
                'dest_ip': request.query_params.get('dest_ip'),
                'signature_id': request.query_params.get('signature_id'),
                'limit': int(request.query_params.get('limit', 100))
            }
            
            # Récupérer les alertes via le service Suricata
            result = self.suricata_service.get_alerts(filters)
            
            return Response(result)
            
        except Exception as e:
            logger.exception(f"Erreur lors de la récupération des alertes Suricata: {e}")
            return Response(
                {"error": "Erreur lors de la récupération des alertes Suricata"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class SuricataRulesView(APIView):
    """Vue API pour gérer les règles Suricata."""
    
    permission_classes = [IsAuthenticated]
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        from django.apps import apps
        try:
            di_container = apps.get_app_config('network_management').di_container
            self.suricata_service = di_container.resolve('SuricataService')
        except Exception:
            try:
                from services.suricata_service import SuricataService
                self.suricata_service = SuricataService()
            except ImportError:
                self.suricata_service = None
    
    def get(self, request):
        """Récupère la liste des règles Suricata."""
        try:
            if not self.suricata_service:
                return Response(
                    {"error": "Service Suricata non disponible"},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE
                )
            
            # Paramètres de filtrage
            filters = {
                'category': request.query_params.get('category'),
                'enabled_only': request.query_params.get('enabled_only', 'false').lower() == 'true',
                'search': request.query_params.get('search')
            }
            
            # Récupérer les règles via le service Suricata
            result = self.suricata_service.get_rules(filters)
            
            return Response(result)
            
        except Exception as e:
            logger.exception(f"Erreur lors de la récupération des règles Suricata: {e}")
            return Response(
                {"error": "Erreur lors de la récupération des règles Suricata"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class SuricataAddRuleView(APIView):
    """Vue API pour ajouter une nouvelle règle Suricata."""
    
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Ajoute une nouvelle règle Suricata."""
        try:
            rule_content = request.data.get('rule_content')
            name = request.data.get('name')
            category = request.data.get('category', 'custom')
            enabled = request.data.get('enabled', True)
            
            if not rule_content:
                return Response(
                    {"error": "Le contenu de la règle est requis"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if not name:
                return Response(
                    {"error": "Le nom de la règle est requis"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Validation basique de la règle Suricata
            if not rule_content.strip().startswith(('alert', 'drop', 'reject', 'pass')):
                return Response(
                    {"error": "La règle doit commencer par alert, drop, reject ou pass"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # TODO: Implémenter avec le service Suricata
            new_rule = {
                "id": 999,
                "sid": 9999999,  # SID généré pour les règles custom
                "category": category,
                "message": name,
                "rule": rule_content,
                "enabled": enabled,
                "source": "custom",
                "created_at": "2025-06-18T10:00:00Z",
                "created_by": request.user.username
            }
            
            result = {
                "success": True,
                "message": f"Règle '{name}' ajoutée avec succès",
                "rule": new_rule
            }
            
            return Response(result, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.exception(f"Erreur lors de l'ajout de la règle Suricata: {e}")
            return Response(
                {"error": "Erreur lors de l'ajout de la règle Suricata"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class SuricataToggleRuleView(APIView):
    """Vue API pour activer/désactiver une règle Suricata."""
    
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Active ou désactive une règle Suricata."""
        try:
            rule_id = request.data.get('rule_id')
            enabled = request.data.get('enabled')
            
            if rule_id is None:
                return Response(
                    {"error": "L'ID de la règle est requis"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if enabled is None:
                return Response(
                    {"error": "Le paramètre 'enabled' est requis (true/false)"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # TODO: Implémenter avec le service Suricata
            rule_info = {
                "id": rule_id,
                "sid": 2001219,
                "message": "ET SCAN Potential SSH Scan",
                "enabled": bool(enabled),
                "modified_at": "2025-06-18T10:00:00Z",
                "modified_by": request.user.username
            }
            
            action = "activée" if enabled else "désactivée"
            result = {
                "success": True,
                "message": f"Règle {rule_id} {action} avec succès",
                "rule": rule_info
            }
            
            return Response(result)
            
        except Exception as e:
            logger.exception(f"Erreur lors de la modification de la règle Suricata: {e}")
            return Response(
                {"error": "Erreur lors de la modification de la règle Suricata"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class SuricataReloadRulesView(APIView):
    """Vue API pour recharger les règles Suricata."""
    
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Recharge toutes les règles Suricata."""
        try:
            force = request.data.get('force', False)
            
            # TODO: Implémenter avec le service Suricata
            reload_result = {
                "success": True,
                "message": "Règles Suricata rechargées avec succès",
                "reload_started_at": "2025-06-18T10:00:00Z",
                "reload_completed_at": "2025-06-18T10:00:30Z",
                "duration": "30 seconds",
                "statistics": {
                    "total_rules": 25678,
                    "loaded_rules": 25650,
                    "failed_rules": 28,
                    "disabled_rules": 1234,
                    "custom_rules": 15
                },
                "warnings": [
                    "Rule SID 2001234 has syntax warning",
                    "Duplicate SID detected: 2001299"
                ],
                "errors": [
                    "Rule file /etc/suricata/rules/custom.rules not found"
                ]
            }
            
            return Response(reload_result)
            
        except Exception as e:
            logger.exception(f"Erreur lors du rechargement des règles Suricata: {e}")
            return Response(
                {"error": "Erreur lors du rechargement des règles Suricata"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            ) 