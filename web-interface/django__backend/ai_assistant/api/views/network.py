"""
Vues API pour l'analyse réseau.

Ce module contient les vues API pour effectuer des analyses
de topologie réseau, de performance et de sécurité.
"""

import time
import logging
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from ai_assistant.api.serializers import (
    NetworkAnalysisRequestSerializer,
    NetworkAnalysisResponseSerializer,
    ErrorResponseSerializer,
)
from ai_assistant.domain.services import NetworkService
from ai_assistant.domain.exceptions import (
    NetworkAnalysisError,
    ValidationError,
)

logger = logging.getLogger(__name__)


class NetworkAnalysisView(APIView):
    """Vue pour effectuer des analyses réseau."""
    
    permission_classes = [IsAuthenticated]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.network_service = NetworkService()
    
    def post(self, request):
        """
        Effectue une analyse réseau et renvoie les résultats.
        
        Args:
            request: Requête HTTP
            
        Returns:
            Response: Réponse HTTP contenant les résultats de l'analyse
        """
        # Valider la requête
        serializer = NetworkAnalysisRequestSerializer(data=request.data)
        if not serializer.is_valid():
            error_serializer = ErrorResponseSerializer({
                'error': "Données invalides",
                'error_type': 'ValidationError',
                'detail': serializer.errors,
                'status_code': 400
            })
            return Response(error_serializer.data, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            analysis_type = serializer.validated_data.get('analysis_type', 'topology')
            target_hosts = serializer.validated_data.get('target_hosts', [])
            
            # Effectuer l'analyse réseau
            start_time = time.time()
            
            if analysis_type == 'topology':
                results = self.network_service.analyze_topology(target_hosts)
            elif analysis_type == 'performance':
                results = self.network_service.analyze_performance(target_hosts)
            elif analysis_type == 'security':
                results = self.network_service.analyze_security(target_hosts)
            elif analysis_type == 'full':
                results = self.network_service.analyze_full(target_hosts)
            else:
                raise ValidationError(f"Type d'analyse non supporté: {analysis_type}")
            
            processing_time = time.time() - start_time
            
            # Ajouter le temps de traitement aux résultats
            results['processing_time'] = processing_time
            
            # Sérialiser la réponse
            response_serializer = NetworkAnalysisResponseSerializer(results)
            
            return Response(response_serializer.data)
        
        except NetworkAnalysisError as e:
            logger.error(f"Erreur d'analyse réseau: {str(e)}")
            error_serializer = ErrorResponseSerializer({
                'error': str(e),
                'error_type': 'NetworkAnalysisError',
                'status_code': 500
            })
            return Response(error_serializer.data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        except ValidationError as e:
            logger.warning(f"Erreur de validation: {str(e)}")
            error_serializer = ErrorResponseSerializer({
                'error': str(e),
                'error_type': 'ValidationError',
                'status_code': 400
            })
            return Response(error_serializer.data, status=status.HTTP_400_BAD_REQUEST)
        
        except Exception as e:
            logger.exception("Erreur lors de l'analyse réseau")
            error_serializer = ErrorResponseSerializer({
                'error': str(e),
                'error_type': e.__class__.__name__,
                'status_code': 500
            })
            return Response(error_serializer.data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class NetworkTopologyView(APIView):
    """Vue pour effectuer des analyses de topologie réseau."""
    
    permission_classes = [IsAuthenticated]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.network_service = NetworkService()
    
    def post(self, request):
        """
        Effectue une analyse de topologie réseau et renvoie les résultats.
        
        Args:
            request: Requête HTTP
            
        Returns:
            Response: Réponse HTTP contenant les résultats de l'analyse
        """
        # Valider la requête
        serializer = NetworkAnalysisRequestSerializer(data=request.data)
        if not serializer.is_valid():
            error_serializer = ErrorResponseSerializer({
                'error': "Données invalides",
                'error_type': 'ValidationError',
                'detail': serializer.errors,
                'status_code': 400
            })
            return Response(error_serializer.data, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            target_hosts = serializer.validated_data.get('target_hosts', [])
            
            # Effectuer l'analyse de topologie réseau
            start_time = time.time()
            results = self.network_service.analyze_topology(target_hosts)
            processing_time = time.time() - start_time
            
            # Ajouter le temps de traitement aux résultats
            results['processing_time'] = processing_time
            
            # Sérialiser la réponse
            response_serializer = NetworkAnalysisResponseSerializer(results)
            
            return Response(response_serializer.data)
        
        except NetworkAnalysisError as e:
            logger.error(f"Erreur d'analyse de topologie réseau: {str(e)}")
            error_serializer = ErrorResponseSerializer({
                'error': str(e),
                'error_type': 'NetworkAnalysisError',
                'status_code': 500
            })
            return Response(error_serializer.data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        except Exception as e:
            logger.exception("Erreur lors de l'analyse de topologie réseau")
            error_serializer = ErrorResponseSerializer({
                'error': str(e),
                'error_type': e.__class__.__name__,
                'status_code': 500
            })
            return Response(error_serializer.data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class NetworkPerformanceView(APIView):
    """Vue pour effectuer des analyses de performance réseau."""
    
    permission_classes = [IsAuthenticated]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.network_service = NetworkService()
    
    def post(self, request):
        """
        Effectue une analyse de performance réseau et renvoie les résultats.
        
        Args:
            request: Requête HTTP
            
        Returns:
            Response: Réponse HTTP contenant les résultats de l'analyse
        """
        # Valider la requête
        serializer = NetworkAnalysisRequestSerializer(data=request.data)
        if not serializer.is_valid():
            error_serializer = ErrorResponseSerializer({
                'error': "Données invalides",
                'error_type': 'ValidationError',
                'detail': serializer.errors,
                'status_code': 400
            })
            return Response(error_serializer.data, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            target_hosts = serializer.validated_data.get('target_hosts', [])
            
            # Effectuer l'analyse de performance réseau
            start_time = time.time()
            results = self.network_service.analyze_performance(target_hosts)
            processing_time = time.time() - start_time
            
            # Ajouter le temps de traitement aux résultats
            results['processing_time'] = processing_time
            
            # Sérialiser la réponse
            response_serializer = NetworkAnalysisResponseSerializer(results)
            
            return Response(response_serializer.data)
        
        except NetworkAnalysisError as e:
            logger.error(f"Erreur d'analyse de performance réseau: {str(e)}")
            error_serializer = ErrorResponseSerializer({
                'error': str(e),
                'error_type': 'NetworkAnalysisError',
                'status_code': 500
            })
            return Response(error_serializer.data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        except Exception as e:
            logger.exception("Erreur lors de l'analyse de performance réseau")
            error_serializer = ErrorResponseSerializer({
                'error': str(e),
                'error_type': e.__class__.__name__,
                'status_code': 500
            })
            return Response(error_serializer.data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class NetworkSecurityView(APIView):
    """Vue pour effectuer des analyses de sécurité réseau."""
    
    permission_classes = [IsAuthenticated]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.network_service = NetworkService()
    
    def post(self, request):
        """
        Effectue une analyse de sécurité réseau et renvoie les résultats.
        
        Args:
            request: Requête HTTP
            
        Returns:
            Response: Réponse HTTP contenant les résultats de l'analyse
        """
        # Valider la requête
        serializer = NetworkAnalysisRequestSerializer(data=request.data)
        if not serializer.is_valid():
            error_serializer = ErrorResponseSerializer({
                'error': "Données invalides",
                'error_type': 'ValidationError',
                'detail': serializer.errors,
                'status_code': 400
            })
            return Response(error_serializer.data, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            target_hosts = serializer.validated_data.get('target_hosts', [])
            
            # Effectuer l'analyse de sécurité réseau
            start_time = time.time()
            results = self.network_service.analyze_security(target_hosts)
            processing_time = time.time() - start_time
            
            # Ajouter le temps de traitement aux résultats
            results['processing_time'] = processing_time
            
            # Sérialiser la réponse
            response_serializer = NetworkAnalysisResponseSerializer(results)
            
            return Response(response_serializer.data)
        
        except NetworkAnalysisError as e:
            logger.error(f"Erreur d'analyse de sécurité réseau: {str(e)}")
            error_serializer = ErrorResponseSerializer({
                'error': str(e),
                'error_type': 'NetworkAnalysisError',
                'status_code': 500
            })
            return Response(error_serializer.data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        except Exception as e:
            logger.exception("Erreur lors de l'analyse de sécurité réseau")
            error_serializer = ErrorResponseSerializer({
                'error': str(e),
                'error_type': e.__class__.__name__,
                'status_code': 500
            })
            return Response(error_serializer.data, status=status.HTTP_500_INTERNAL_SERVER_ERROR) 