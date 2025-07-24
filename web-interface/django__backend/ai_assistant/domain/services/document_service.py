"""
Service de gestion des documents.

Ce module contient le service pour gérer les documents
stockés dans le système.
"""

import uuid
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from ai_assistant.domain.models import Document
from ai_assistant.domain.exceptions import DocumentNotFoundError, ValidationError

logger = logging.getLogger(__name__)


class DocumentService:
    """Service pour gérer les documents."""
    
    def __init__(self):
        """Initialise le service de document."""
        # Stockage en mémoire pour le développement
        # En production, cela serait remplacé par une base de données
        self._documents: Dict[str, Document] = {}
    
    def create_document(
        self,
        user_id: str,
        title: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Document:
        """
        Crée un nouveau document.
        
        Args:
            user_id: ID de l'utilisateur
            title: Titre du document
            content: Contenu du document
            metadata: Métadonnées du document
            
        Returns:
            Document: Le document créé
            
        Raises:
            ValidationError: Si les données sont invalides
        """
        if not user_id:
            raise ValidationError("L'ID utilisateur est requis")
        
        if not title:
            raise ValidationError("Le titre du document est requis")
        
        if not content:
            raise ValidationError("Le contenu du document est requis")
        
        document_id = str(uuid.uuid4())
        document = Document(
            id=document_id,
            title=title,
            content=content,
            metadata={
                **(metadata or {}),
                "user_id": user_id,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
            }
        )
        
        self._documents[document_id] = document
        logger.info(f"Document créé: {document_id}")
        
        return document
    
    def get_document_by_id(self, document_id: str, user_id: str) -> Document:
        """
        Récupère un document par son ID.
        
        Args:
            document_id: ID du document
            user_id: ID de l'utilisateur
            
        Returns:
            Document: Le document trouvé
            
        Raises:
            DocumentNotFoundError: Si le document n'est pas trouvé
        """
        document = self._documents.get(document_id)
        
        if not document:
            raise DocumentNotFoundError(f"Document non trouvé: {document_id}")
        
        if document.metadata.get("user_id") != user_id:
            raise DocumentNotFoundError(f"Document non trouvé: {document_id}")
        
        return document
    
    def get_documents_by_user_id(self, user_id: str) -> List[Document]:
        """
        Récupère tous les documents d'un utilisateur.
        
        Args:
            user_id: ID de l'utilisateur
            
        Returns:
            List[Document]: Liste des documents de l'utilisateur
        """
        return [
            document for document in self._documents.values()
            if document.metadata.get("user_id") == user_id
        ]
    
    def update_document(
        self,
        document_id: str,
        user_id: str,
        title: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Document:
        """
        Met à jour un document.
        
        Args:
            document_id: ID du document
            user_id: ID de l'utilisateur
            title: Nouveau titre du document
            content: Nouveau contenu du document
            metadata: Nouvelles métadonnées du document
            
        Returns:
            Document: Le document mis à jour
            
        Raises:
            DocumentNotFoundError: Si le document n'est pas trouvé
            ValidationError: Si les données sont invalides
        """
        document = self.get_document_by_id(document_id, user_id)
        
        if not title:
            raise ValidationError("Le titre du document est requis")
        
        if not content:
            raise ValidationError("Le contenu du document est requis")
        
        # Mettre à jour le document
        document.title = title
        document.content = content
        
        # Mettre à jour les métadonnées
        if metadata:
            # Conserver l'ID utilisateur et les timestamps
            user_id = document.metadata.get("user_id")
            created_at = document.metadata.get("created_at")
            
            document.metadata = {
                **metadata,
                "user_id": user_id,
                "created_at": created_at,
                "updated_at": datetime.now().isoformat(),
            }
        else:
            document.metadata["updated_at"] = datetime.now().isoformat()
        
        logger.info(f"Document mis à jour: {document_id}")
        
        return document
    
    def delete_document(self, document_id: str, user_id: str) -> None:
        """
        Supprime un document.
        
        Args:
            document_id: ID du document
            user_id: ID de l'utilisateur
            
        Raises:
            DocumentNotFoundError: Si le document n'est pas trouvé
        """
        document = self.get_document_by_id(document_id, user_id)
        
        del self._documents[document_id]
        
        logger.info(f"Document supprimé: {document_id}")
    
    def search_documents(self, query: str, user_id: str, max_results: int = 5) -> List[Document]:
        """
        Recherche des documents par mots-clés.
        
        Args:
            query: Requête de recherche
            user_id: ID de l'utilisateur
            max_results: Nombre maximum de résultats à retourner
            
        Returns:
            List[Document]: Liste des documents correspondant à la requête
        """
        query_lower = query.lower()
        results = []
        
        for document in self.get_documents_by_user_id(user_id):
            # Recherche simple dans le titre et le contenu
            if query_lower in document.title.lower() or query_lower in document.content.lower():
                results.append(document)
        
        # Limiter le nombre de résultats
        return results[:max_results] 