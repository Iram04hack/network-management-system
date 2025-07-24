"""
Vues pour les documents.

Ce module contient les vues qui exposent les fonctionnalités
de gestion des documents via une API REST.
"""

from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action

from ai_assistant.domain.services import DocumentService, SearchService
from ai_assistant.domain.exceptions import DocumentNotFoundError, ValidationError
from ai_assistant.api.serializers import DocumentSerializer, DocumentCreateSerializer, SearchResultSerializer


class DocumentViewSet(viewsets.ViewSet):
    """Vue pour gérer les documents."""
    
    permission_classes = [IsAuthenticated]
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.document_service = DocumentService()
        self.search_service = SearchService()
    
    def list(self, request):
        """Liste tous les documents de l'utilisateur."""
        user_id = str(request.user.id)
        documents = self.document_service.get_documents_by_user_id(user_id)
        
        # Limiter la taille du contenu si demandé
        content_limit = request.query_params.get('content_limit')
        if content_limit:
            try:
                content_limit = int(content_limit)
            except ValueError:
                content_limit = None
        
        serializer = DocumentSerializer(
            documents,
            many=True,
            context={'content_limit': content_limit}
        )
        return Response(serializer.data)
    
    def retrieve(self, request, pk=None):
        """Récupère un document par son ID."""
        user_id = str(request.user.id)
        
        try:
            document = self.document_service.get_document_by_id(pk, user_id)
            serializer = DocumentSerializer(document)
            return Response(serializer.data)
        
        except DocumentNotFoundError:
            return Response(
                {"error": "Document non trouvé"},
                status=status.HTTP_404_NOT_FOUND
            )
    
    def create(self, request):
        """Crée un nouveau document."""
        serializer = DocumentCreateSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user_id = str(request.user.id)
        
        try:
            document = self.document_service.create_document(
                user_id=user_id,
                title=serializer.validated_data['title'],
                content=serializer.validated_data['content'],
                metadata=serializer.validated_data.get('metadata')
            )
            
            # Indexer le document pour la recherche
            self.search_service.index_document(document)
            
            serializer = DocumentSerializer(document)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        except ValidationError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        except Exception as e:
            return Response(
                {"error": f"Erreur lors de la création du document: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def update(self, request, pk=None):
        """Met à jour un document existant."""
        serializer = DocumentCreateSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user_id = str(request.user.id)
        
        try:
            document = self.document_service.update_document(
                document_id=pk,
                user_id=user_id,
                title=serializer.validated_data['title'],
                content=serializer.validated_data['content'],
                metadata=serializer.validated_data.get('metadata')
            )
            
            # Mettre à jour l'index de recherche
            self.search_service.index_document(document)
            
            serializer = DocumentSerializer(document)
            return Response(serializer.data)
        
        except DocumentNotFoundError:
            return Response(
                {"error": "Document non trouvé"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        except ValidationError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        except Exception as e:
            return Response(
                {"error": f"Erreur lors de la mise à jour du document: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def destroy(self, request, pk=None):
        """Supprime un document."""
        user_id = str(request.user.id)
        
        try:
            # Supprimer de l'index de recherche
            self.search_service.remove_document_from_index(pk)
            
            # Supprimer le document
            self.document_service.delete_document(pk, user_id)
            
            return Response(status=status.HTTP_204_NO_CONTENT)
        
        except DocumentNotFoundError:
            return Response(
                {"error": "Document non trouvé"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        except Exception as e:
            return Response(
                {"error": f"Erreur lors de la suppression du document: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def search(self, request):
        """Recherche dans les documents."""
        user_id = str(request.user.id)
        query = request.query_params.get('query', '')
        max_results = int(request.query_params.get('max_results', 5))
        
        if not query:
            return Response(
                {"error": "Le paramètre 'query' est requis"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            documents = self.document_service.search_documents(query, user_id, max_results)
            serializer = DocumentSerializer(documents, many=True)
            return Response(serializer.data)
        
        except Exception as e:
            return Response(
                {"error": f"Erreur lors de la recherche: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            ) 