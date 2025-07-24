"""
Vues pour la recherche.

Ce module contient les vues qui exposent les fonctionnalités
de recherche via une API REST.
"""

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from ai_assistant.domain.services import SearchService
from ai_assistant.domain.exceptions import SearchError
from ai_assistant.api.serializers import SearchQuerySerializer, SearchResultSerializer


class SearchView(APIView):
    """Vue pour effectuer des recherches."""
    
    permission_classes = [IsAuthenticated]
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.search_service = SearchService()
    
    def get(self, request):
        """Effectue une recherche globale."""
        serializer = SearchQuerySerializer(data=request.query_params)
        
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user_id = str(request.user.id)
        query = serializer.validated_data['query']
        max_results = serializer.validated_data.get('max_results', 5)
        content_limit = serializer.validated_data.get('content_limit', 200)
        
        try:
            results = self.search_service.search(query, user_id, max_results)
            
            serializer = SearchResultSerializer(
                results,
                many=True,
                context={'content_limit': content_limit}
            )
            
            return Response({
                "query": query,
                "results_count": len(results),
                "results": serializer.data
            })
        
        except SearchError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        except Exception as e:
            return Response(
                {"error": f"Erreur lors de la recherche: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            ) 