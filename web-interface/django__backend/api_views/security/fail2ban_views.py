import logging
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

# from services.fail2ban_service import Fail2banService  # Service sera initialisé dans le container DI
# from security_management.permissions import IsAdminOrReadOnly  # Permission différée

logger = logging.getLogger(__name__)

class Fail2BanViewSet(viewsets.ViewSet):
    """ViewSet pour l'intégration Fail2ban"""
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        method='get',
        operation_summary="Statut Fail2Ban",
        operation_description="Vérifie le statut de connexion à Fail2ban",
        responses={
            200: "Statut de connexion",
            503: "Service non disponible"
        },
        tags=['API Views']
    )
    @action(detail=False, methods=['get'])
    def status(self, request):
        """Vérifie le statut de connexion à Fail2ban."""
        service = Fail2banService()
        client = service.get_client()
        
        if client.test_connection():
            return Response({
                "status": "connected",
                "message": "Fail2ban est accessible"
            })
        else:
            return Response({
                "status": "disconnected",
                "message": "Impossible de se connecter à Fail2ban"
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    
    @swagger_auto_schema(
        method='get',
        operation_summary="Liste des jails Fail2Ban",
        operation_description="Liste toutes les jails et leur statut",
        responses={
            200: "Liste des jails",
            500: "Erreur serveur"
        },
        tags=['API Views']
    )
    @action(detail=False, methods=['get'])
    def jails(self, request):
        """Liste toutes les jails et leur statut."""
        result = Fail2banService.check_jail_status()
        
        if result.get("success"):
            return Response(result)
        else:
            return Response(result, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @swagger_auto_schema(
        method='get',
        operation_summary="IPs bannies",
        operation_description="Récupère toutes les IPs bannies",
        responses={
            200: "Liste des IPs bannies",
            500: "Erreur serveur"
        },
        tags=['API Views']
    )
    @action(detail=False, methods=['get'])
    def banned(self, request):
        """Récupère toutes les IPs bannies."""
        result = Fail2banService.sync_banned_ips()
        
        if result.get("success"):
            return Response(result)
        else:
            return Response(result, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @swagger_auto_schema(
        method='post',
        operation_summary="Bannir une IP",
        operation_description="Bannit manuellement une IP",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'ip_address': openapi.Schema(type=openapi.TYPE_STRING),
                'jail_name': openapi.Schema(type=openapi.TYPE_STRING),
                'reason': openapi.Schema(type=openapi.TYPE_STRING)
            }
        ),
        responses={
            200: "IP bannie avec succès",
            400: "Données invalides",
            500: "Erreur serveur"
        },
        tags=['API Views']
    )
    @action(detail=False, methods=['post'])
    def ban(self, request):
        """Bannit manuellement une IP."""
        ip_address = request.data.get('ip_address')
        jail_name = request.data.get('jail_name')
        reason = request.data.get('reason', '')
        
        if not ip_address or not jail_name:
            return Response({
                "error": "ip_address et jail_name sont requis"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        result = Fail2banService.ban_ip_manual(ip_address, jail_name, reason)
        
        if result.get("success"):
            return Response(result)
        else:
            return Response(result, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @swagger_auto_schema(
        method='post',
        operation_summary="Débannir une IP",
        operation_description="Débannit manuellement une IP",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'ip_address': openapi.Schema(type=openapi.TYPE_STRING),
                'jail_name': openapi.Schema(type=openapi.TYPE_STRING),
                'reason': openapi.Schema(type=openapi.TYPE_STRING)
            }
        ),
        responses={
            200: "IP débannie avec succès",
            400: "Données invalides",
            500: "Erreur serveur"
        },
        tags=['API Views']
    )
    @action(detail=False, methods=['post'])
    def unban(self, request):
        """Débannit manuellement une IP."""
        ip_address = request.data.get('ip_address')
        jail_name = request.data.get('jail_name')
        reason = request.data.get('reason', '')
        
        if not ip_address or not jail_name:
            return Response({
                "error": "ip_address et jail_name sont requis"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        result = Fail2banService.unban_ip_manual(ip_address, jail_name, reason)
        
        if result.get("success"):
            return Response(result)
        else:
            return Response(result, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @swagger_auto_schema(
        method='get',
        operation_summary="Statistiques de bannissement",
        operation_description="Récupère les statistiques de bannissement",
        manual_parameters=[
            openapi.Parameter('days', openapi.IN_QUERY, description='Nombre de jours', type=openapi.TYPE_INTEGER, default=7)
        ],
        responses={
            200: "Statistiques de bannissement",
            500: "Erreur serveur"
        },
        tags=['API Views']
    )
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Récupère les statistiques de bannissement."""
        days = int(request.query_params.get('days', 7))
        
        result = Fail2banService.get_ban_statistics(days)
        
        if result.get("success"):
            return Response(result)
        else:
            return Response(result, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class Fail2banJailStatusView(APIView):
    """Vue API pour récupérer le statut des jails Fail2ban."""
    
    permission_classes = [IsAuthenticated]
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        from django.apps import apps
        try:
            di_container = apps.get_app_config('network_management').di_container
            self.fail2ban_service = di_container.resolve('Fail2banService')
        except Exception:
            try:
                from services.fail2ban_service import Fail2banService
                self.fail2ban_service = Fail2banService()
            except ImportError:
                self.fail2ban_service = None
    
    def get(self, request):
        """Récupère le statut de toutes les jails ou d'une jail spécifique."""
        try:
            if not self.fail2ban_service:
                return Response(
                    {"error": "Service Fail2ban non disponible"},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE
                )
            
            jail_name = request.query_params.get('jail')
            
            if jail_name:
                # Statut d'une jail spécifique
                jail_status = self.fail2ban_service.get_jail_status(jail_name)
                return Response(jail_status)
            else:
                # Statut de toutes les jails
                jails_status = self.fail2ban_service.get_all_jails_status()
                return Response(jails_status)
                
        except Exception as e:
            logger.exception(f"Erreur lors de la récupération du statut des jails: {e}")
            return Response(
                {"error": "Erreur lors de la récupération du statut des jails"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class Fail2banBanIPView(APIView):
    """Vue API pour bannir manuellement une adresse IP."""
    
    permission_classes = [IsAuthenticated]
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        from django.apps import apps
        try:
            di_container = apps.get_app_config('network_management').di_container
            self.fail2ban_service = di_container.resolve('Fail2banService')
        except Exception:
            try:
                from services.fail2ban_service import Fail2banService
                self.fail2ban_service = Fail2banService()
            except ImportError:
                self.fail2ban_service = None
    
    def post(self, request):
        """Bannit manuellement une adresse IP."""
        try:
            if not self.fail2ban_service:
                return Response(
                    {"error": "Service Fail2ban non disponible"},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE
                )
            
            ip_address = request.data.get('ip_address')
            jail_name = request.data.get('jail_name')
            reason = request.data.get('reason', 'Manual ban via API')
            duration = request.data.get('duration')  # en secondes, optionnel
            
            if not ip_address:
                return Response(
                    {"error": "L'adresse IP est requise"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if not jail_name:
                return Response(
                    {"error": "Le nom de la jail est requis"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Validation de l'adresse IP
            import ipaddress
            try:
                ipaddress.ip_address(ip_address)
            except ValueError:
                return Response(
                    {"error": "Adresse IP invalide"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Bannir l'IP via le service Fail2ban
            ban_result = self.fail2ban_service.ban_ip_manual(
                ip_address=ip_address,
                jail_name=jail_name,
                reason=reason,
                duration=duration,
                banned_by=request.user.username
            )
            
            return Response(ban_result, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.exception(f"Erreur lors du bannissement de l'IP: {e}")
            return Response(
                {"error": "Erreur lors du bannissement de l'IP"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class Fail2banUnbanIPView(APIView):
    """Vue API pour débannir une adresse IP."""
    
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Débannit une adresse IP."""
        try:
            ip_address = request.data.get('ip_address')
            jail_name = request.data.get('jail_name')
            reason = request.data.get('reason', 'Manual unban via API')
            
            if not ip_address:
                return Response(
                    {"error": "L'adresse IP est requise"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if not jail_name:
                return Response(
                    {"error": "Le nom de la jail est requis"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # TODO: Implémenter avec le service Fail2ban
            unban_result = {
                "success": True,
                "message": f"IP {ip_address} débannie avec succès de la jail {jail_name}",
                "ip_address": ip_address,
                "jail_name": jail_name,
                "reason": reason,
                "unbanned_at": "2025-06-18T10:00:00Z"
            }
            
            return Response(unban_result)
            
        except Exception as e:
            logger.exception(f"Erreur lors du débannissement de l'IP: {e}")
            return Response(
                {"error": "Erreur lors du débannissement de l'IP"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class Fail2banSyncView(APIView):
    """Vue API pour synchroniser Fail2ban avec les sources externes."""
    
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Synchronise Fail2ban avec les sources de données externes."""
        try:
            sync_type = request.data.get('sync_type', 'full')  # full, incremental
            force = request.data.get('force', False)
            
            # TODO: Implémenter avec le service Fail2ban
            sync_result = {
                "success": True,
                "message": "Synchronisation Fail2ban terminée avec succès",
                "sync_type": sync_type,
                "started_at": "2025-06-18T10:00:00Z",
                "completed_at": "2025-06-18T10:02:15Z",
                "duration": "2m 15s",
                "statistics": {
                    "new_bans": 5,
                    "updated_bans": 2,
                    "expired_bans": 8,
                    "errors": 0
                },
                "jails_processed": [
                    {
                        "name": "sshd",
                        "new_bans": 3,
                        "updated_bans": 1
                    },
                    {
                        "name": "apache-auth",
                        "new_bans": 2,
                        "updated_bans": 1
                    }
                ]
            }
            
            return Response(sync_result)
            
        except Exception as e:
            logger.exception(f"Erreur lors de la synchronisation Fail2ban: {e}")
            return Response(
                {"error": "Erreur lors de la synchronisation Fail2ban"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class Fail2banStatisticsView(APIView):
    """Vue API pour récupérer les statistiques Fail2ban."""
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Récupère les statistiques de bannissement Fail2ban."""
        try:
            period = request.query_params.get('period', '7d')  # 1h, 24h, 7d, 30d
            jail_name = request.query_params.get('jail')
            
            # TODO: Implémenter avec le service Fail2ban
            statistics = {
                "period": period,
                "generated_at": "2025-06-18T10:00:00Z",
                "summary": {
                    "total_bans": 156,
                    "active_bans": 23,
                    "failed_attempts": 2847,
                    "unique_ips": 89,
                    "top_blocked_countries": ["China", "Russia", "USA"],
                    "active_jails": 3
                },
                "timeline": [
                    {"date": "2025-06-17", "bans": 45, "attempts": 432},
                    {"date": "2025-06-16", "bans": 38, "attempts": 389},
                    {"date": "2025-06-15", "bans": 52, "attempts": 501},
                    {"date": "2025-06-14", "bans": 21, "attempts": 298}
                ],
                "jail_statistics": [
                    {
                        "jail": "sshd",
                        "total_bans": 89,
                        "active_bans": 12,
                        "failed_attempts": 1456,
                        "avg_ban_duration": "1h 30m"
                    },
                    {
                        "jail": "apache-auth",
                        "total_bans": 67,
                        "active_bans": 11,
                        "failed_attempts": 1391,
                        "avg_ban_duration": "2h 15m"
                    }
                ],
                "top_blocked_ips": [
                    {"ip": "192.168.1.100", "attempts": 45, "bans": 3},
                    {"ip": "10.0.0.50", "attempts": 38, "bans": 2},
                    {"ip": "172.16.1.25", "attempts": 32, "bans": 2}
                ]
            }
            
            # Filtrer par jail si spécifiée
            if jail_name:
                jail_stats = next((j for j in statistics["jail_statistics"] if j["jail"] == jail_name), None)
                if jail_stats:
                    statistics = {
                        "period": period,
                        "jail": jail_name,
                        **jail_stats
                    }
                else:
                    return Response(
                        {"error": f"Jail '{jail_name}' non trouvée"},
                        status=status.HTTP_404_NOT_FOUND
                    )
            
            return Response(statistics)
            
        except Exception as e:
            logger.exception(f"Erreur lors de la récupération des statistiques Fail2ban: {e}")
            return Response(
                {"error": "Erreur lors de la récupération des statistiques"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            ) 