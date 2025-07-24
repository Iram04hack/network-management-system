"""
Vues API pour la gestion des documents.

Ce module contient les vues API pour créer, lire, mettre à jour et supprimer
des documents.
"""

import logging
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from ai_assistant.api.serializers import (
    DocumentSerializer,
    DocumentRequestSerializer,
    DocumentResponseSerializer,
    ErrorResponseSerializer,
)
from ai_assistant.domain.services import DocumentService
from ai_assistant.domain.exceptions import (
    DocumentNotFoundError,
    ValidationError,
)

logger = logging.getLogger(__name__)


class DocumentListView(APIView):
    """Vue pour lister et créer des documents."""
    
    permission_classes = [IsAuthenticated]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.document_service = DocumentService()
    
    def get(self, request):
        """
        Liste tous les documents de l'utilisateur.
        
        Args:
            request: Requête HTTP
            
        Returns:
            Response: Réponse HTTP contenant la liste des documents
        """
        try:
            user_id = str(request.user.id)
            documents = self.document_service.get_documents_by_user_id(user_id)
            
            # Sérialiser les documents
            serializer = DocumentSerializer(documents, many=True)
            
            return Response(serializer.data)
        
        except Exception as e:
            logger.exception("Erreur lors de la récupération des documents")
            error_serializer = ErrorResponseSerializer({
                'error': str(e),
                'error_type': e.__class__.__name__,
                'status_code': 500
            })
            return Response(error_serializer.data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def post(self, request):
        """
        Crée un nouveau document.
        
        Args:
            request: Requête HTTP
            
        Returns:
            Response: Réponse HTTP contenant le document créé
        """
        # Valider la requête
        serializer = DocumentRequestSerializer(data=request.data)
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
            title = serializer.validated_data['title']
            content = serializer.validated_data['content']
            metadata = serializer.validated_data.get('metadata', {})
            
            # Créer le document
            document = self.document_service.create_document(
                user_id=user_id,
                title=title,
                content=content,
                metadata=metadata
            )
            
            # Sérialiser la réponse
            response_serializer = DocumentResponseSerializer(document)
            
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        
        except ValidationError as e:
            logger.warning(f"Erreur de validation: {str(e)}")
            error_serializer = ErrorResponseSerializer({
                'error': str(e),
                'error_type': 'ValidationError',
                'status_code': 400
            })
            return Response(error_serializer.data, status=status.HTTP_400_BAD_REQUEST)
        
        except Exception as e:
            logger.exception("Erreur lors de la création d'un document")
            error_serializer = ErrorResponseSerializer({
                'error': str(e),
                'error_type': e.__class__.__name__,
                'status_code': 500
            })
            return Response(error_serializer.data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DocumentDetailView(APIView):
    """Vue pour récupérer, mettre à jour et supprimer un document."""
    
    permission_classes = [IsAuthenticated]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.document_service = DocumentService()
    
    def get(self, request, document_id):
        """
        Récupère un document par son ID.
        
        Args:
            request: Requête HTTP
            document_id: ID du document
            
        Returns:
            Response: Réponse HTTP contenant le document
        """
        try:
            user_id = str(request.user.id)
            document = self.document_service.get_document_by_id(
                document_id=document_id,
                user_id=user_id
            )
            
            # Sérialiser le document
            serializer = DocumentSerializer(document)
            
            return Response(serializer.data)
        
        except DocumentNotFoundError as e:
            logger.warning(f"Document non trouvé: {str(e)}")
            error_serializer = ErrorResponseSerializer({
                'error': str(e),
                'error_type': 'DocumentNotFoundError',
                'status_code': 404
            })
            return Response(error_serializer.data, status=status.HTTP_404_NOT_FOUND)
        
        except Exception as e:
            logger.exception("Erreur lors de la récupération d'un document")
            error_serializer = ErrorResponseSerializer({
                'error': str(e),
                'error_type': e.__class__.__name__,
                'status_code': 500
            })
            return Response(error_serializer.data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def put(self, request, document_id):
        """
        Met à jour un document.
        
        Args:
            request: Requête HTTP
            document_id: ID du document
            
        Returns:
            Response: Réponse HTTP contenant le document mis à jour
        """
        # Valider la requête
        serializer = DocumentRequestSerializer(data=request.data)
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
            title = serializer.validated_data['title']
            content = serializer.validated_data['content']
            metadata = serializer.validated_data.get('metadata', {})
            
            # Mettre à jour le document
            document = self.document_service.update_document(
                document_id=document_id,
                user_id=user_id,
                title=title,
                content=content,
                metadata=metadata
            )
            
            # Sérialiser la réponse
            response_serializer = DocumentResponseSerializer(document)
            
            return Response(response_serializer.data)
        
        except DocumentNotFoundError as e:
            logger.warning(f"Document non trouvé: {str(e)}")
            error_serializer = ErrorResponseSerializer({
                'error': str(e),
                'error_type': 'DocumentNotFoundError',
                'status_code': 404
            })
            return Response(error_serializer.data, status=status.HTTP_404_NOT_FOUND)
        
        except ValidationError as e:
            logger.warning(f"Erreur de validation: {str(e)}")
            error_serializer = ErrorResponseSerializer({
                'error': str(e),
                'error_type': 'ValidationError',
                'status_code': 400
            })
            return Response(error_serializer.data, status=status.HTTP_400_BAD_REQUEST)
        
        except Exception as e:
            logger.exception("Erreur lors de la mise à jour d'un document")
            error_serializer = ErrorResponseSerializer({
                'error': str(e),
                'error_type': e.__class__.__name__,
                'status_code': 500
            })
            return Response(error_serializer.data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def delete(self, request, document_id):
        """
        Supprime un document.
        
        Args:
            request: Requête HTTP
            document_id: ID du document
            
        Returns:
            Response: Réponse HTTP vide
        """
        try:
            user_id = str(request.user.id)
            self.document_service.delete_document(
                document_id=document_id,
                user_id=user_id
            )
            
            return Response(status=status.HTTP_204_NO_CONTENT)
        
        except DocumentNotFoundError as e:
            logger.warning(f"Document non trouvé: {str(e)}")
            error_serializer = ErrorResponseSerializer({
                'error': str(e),
                'error_type': 'DocumentNotFoundError',
                'status_code': 404
            })
            return Response(error_serializer.data, status=status.HTTP_404_NOT_FOUND)
        
        except Exception as e:
            logger.exception("Erreur lors de la suppression d'un document")
            error_serializer = ErrorResponseSerializer({
                'error': str(e),
                'error_type': e.__class__.__name__,
                'status_code': 500
            })
            return Response(error_serializer.data, status=status.HTTP_500_INTERNAL_SERVER_ERROR) 