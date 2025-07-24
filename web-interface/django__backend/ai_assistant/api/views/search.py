"""
Vues API pour la recherche.

Ce module contient les vues API pour effectuer des recherches
dans les documents et les conversations.
"""

import time
import logging
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from ai_assistant.api.serializers import (
    SearchRequestSerializer,
    SearchResponseSerializer,
    ErrorResponseSerializer,
)
from ai_assistant.domain.services import SearchService
from ai_assistant.domain.exceptions import (
    SearchError,
    ValidationError,
)

logger = logging.getLogger(__name__)


class SearchView(APIView):
    """Vue pour effectuer des recherches."""
    
    permission_classes = [IsAuthenticated]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.search_service = SearchService()
    
    def post(self, request):
        """
        Effectue une recherche et renvoie les résultats.
        
        Args:
            request: Requête HTTP
            
        Returns:
            Response: Réponse HTTP contenant les résultats de la recherche
        """
        # Valider la requête
        serializer = SearchRequestSerializer(data=request.data)
        if not serializer.is_valid():
            error_serializer = ErrorResponseSerializer({
                'error': "Données invalides",
                'error_type': 'ValidationError',
                'detail': serializer.errors,
                'status_code': 400
            })
            return Response(error_serializer.data, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user_id = str(request.user.id)
            query = serializer.validated_data['query']
            max_results = serializer.validated_data.get('max_results', 5)
            
            # Effectuer la recherche
            start_time = time.time()
            results = self.search_service.search(
                query=query,
                user_id=user_id,
                max_results=max_results
            )
            processing_time = time.time() - start_time
            
            # Préparer la réponse
            response_data = {
                'results': results,
                'query': query,
                'total_results': len(results),
                'processing_time': processing_time
            }
            
            # Sérialiser la réponse
            response_serializer = SearchResponseSerializer(response_data)
            
            return Response(response_serializer.data)
        
        except SearchError as e:
            logger.error(f"Erreur de recherche: {str(e)}")
            error_serializer = ErrorResponseSerializer({
                'error': str(e),
                'error_type': 'SearchError',
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
            logger.exception("Erreur lors de la recherche")
            error_serializer = ErrorResponseSerializer({
                'error': str(e),
                'error_type': e.__class__.__name__,
                'status_code': 500
            })
            return Response(error_serializer.data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DocumentSearchView(APIView):
    """Vue pour effectuer des recherches dans les documents."""
    
    permission_classes = [IsAuthenticated]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.search_service = SearchService()
    
    def post(self, request):
        """
        Effectue une recherche dans les documents et renvoie les résultats.
        
        Args:
            request: Requête HTTP
            
        Returns:
            Response: Réponse HTTP contenant les résultats de la recherche
        """
        # Valider la requête
        serializer = SearchRequestSerializer(data=request.data)
        if not serializer.is_valid():
            error_serializer = ErrorResponseSerializer({
                'error': "Données invalides",
                'error_type': 'ValidationError',
                'detail': serializer.errors,
                'status_code': 400
            })
            return Response(error_serializer.data, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user_id = str(request.user.id)
            query = serializer.validated_data['query']
            max_results = serializer.validated_data.get('max_results', 5)
            
            # Effectuer la recherche dans les documents
            start_time = time.time()
            results = self.search_service.search_documents(
                query=query,
                user_id=user_id,
                max_results=max_results
            )
            processing_time = time.time() - start_time
            
            # Préparer la réponse
            response_data = {
                'results': results,
                'query': query,
                'total_results': len(results),
                'processing_time': processing_time
            }
            
            # Sérialiser la réponse
            response_serializer = SearchResponseSerializer(response_data)
            
            return Response(response_serializer.data)
        
        except SearchError as e:
            logger.error(f"Erreur de recherche: {str(e)}")
            error_serializer = ErrorResponseSerializer({
                'error': str(e),
                'error_type': 'SearchError',
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
            logger.exception("Erreur lors de la recherche dans les documents")
            error_serializer = ErrorResponseSerializer({
                'error': str(e),
                'error_type': e.__class__.__name__,
                'status_code': 500
            })
            return Response(error_serializer.data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ConversationSearchView(APIView):
    """Vue pour effectuer des recherches dans les conversations."""
    
    permission_classes = [IsAuthenticated]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.search_service = SearchService()
    
    def post(self, request):
        """
        Effectue une recherche dans les conversations et renvoie les résultats.
        
        Args:
            request: Requête HTTP
            
        Returns:
            Response: Réponse HTTP contenant les résultats de la recherche
        """
        # Valider la requête
        serializer = SearchRequestSerializer(data=request.data)
        if not serializer.is_valid():
            error_serializer = ErrorResponseSerializer({
                'error': "Données invalides",
                'error_type': 'ValidationError',
                'detail': serializer.errors,
                'status_code': 400
            })
            return Response(error_serializer.data, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user_id = str(request.user.id)
            query = serializer.validated_data['query']
            max_results = serializer.validated_data.get('max_results', 5)
            
            # Effectuer la recherche dans les conversations
            start_time = time.time()
            results = self.search_service.search_conversations(
                query=query,
                user_id=user_id,
                max_results=max_results
            )
            processing_time = time.time() - start_time
            
            # Préparer la réponse
            response_data = {
                'results': results,
                'query': query,
                'total_results': len(results),
                'processing_time': processing_time
            }
            
            # Sérialiser la réponse
            response_serializer = SearchResponseSerializer(response_data)
            
            return Response(response_serializer.data)
        
        except SearchError as e:
            logger.error(f"Erreur de recherche: {str(e)}")
            error_serializer = ErrorResponseSerializer({
                'error': str(e),
                'error_type': 'SearchError',
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
            logger.exception("Erreur lors de la recherche dans les conversations")
            error_serializer = ErrorResponseSerializer({
                'error': str(e),
                'error_type': e.__class__.__name__,
                'status_code': 500
            })
            return Response(error_serializer.data, status=status.HTTP_500_INTERNAL_SERVER_ERROR) 