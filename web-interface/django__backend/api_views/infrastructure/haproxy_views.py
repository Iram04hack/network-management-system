import logging
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from services.haproxy_service import HAProxyService
from security_management.permissions import IsAdminOrReadOnly

logger = logging.getLogger(__name__)

class HAProxyViewSet(viewsets.ViewSet):
    """ViewSet pour l'intégration HAProxy"""
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def status(self, request):
        """Vérifie le statut de connexion à HAProxy."""
        service = HAProxyService()
        client = service.get_client()
        
        if client.test_connection():
            return Response({
                "status": "connected",
                "message": "HAProxy est accessible"
            })
        else:
            return Response({
                "status": "disconnected",
                "message": "Impossible de se connecter à HAProxy"
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Récupère les statistiques HAProxy."""
        result = HAProxyService.collect_stats()
        
        if result.get("success"):
            return Response(result)
        else:
            return Response(result, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'])
    def backends(self, request):
        """Liste tous les backends et leur état."""
        result = HAProxyService.check_backend_health()
        
        if result.get("success"):
            return Response(result)
        else:
            return Response(result, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'])
    def server(self, request):
        """Gère l'état d'un serveur (enable/disable)."""
        backend = request.data.get('backend')
        server = request.data.get('server')
        action = request.data.get('action')
        
        if not all([backend, server, action]):
            return Response({
                "error": "backend, server et action sont requis"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if action not in ['enable', 'disable']:
            return Response({
                "error": "action doit être 'enable' ou 'disable'"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        result = HAProxyService.manage_server(backend, server, action)
        
        if result.get("success"):
            return Response(result)
        else:
            return Response(result, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'])
    def sessions(self, request):
        """Récupère les métriques de sessions."""
        result = HAProxyService.get_session_metrics()
        
        if result.get("success"):
            return Response(result)
        else:
            return Response(result, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'])
    def bandwidth(self, request):
        """Récupère les métriques de bande passante."""
        result = HAProxyService.get_bandwidth_metrics()
        
        if result.get("success"):
            return Response(result)
        else:
            return Response(result, status=status.HTTP_500_INTERNAL_SERVER_ERROR) 