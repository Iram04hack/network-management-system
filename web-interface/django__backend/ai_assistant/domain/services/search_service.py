"""
Service de recherche.

Ce module contient le service pour effectuer des recherches
dans les documents et les conversations.
"""

import logging
import re
import requests
from typing import List, Dict, Any, Optional
from datetime import datetime

from ai_assistant.domain.models import SearchResult, Document, Message, Conversation
from ai_assistant.domain.exceptions import SearchError

logger = logging.getLogger(__name__)


class SearchService:
    """Service pour effectuer des recherches."""
    
    def __init__(self):
        """Initialise le service de recherche."""
        # Stockage en mémoire pour le développement
        # En production, cela serait remplacé par une base de données
        # ou un moteur de recherche comme Elasticsearch
        self._document_index: Dict[str, Document] = {}
        self._message_index: Dict[str, Message] = {}
    
    def search(self, query: str, user_id: str, max_results: int = 5) -> List[SearchResult]:
        """
        Effectue une recherche globale dans les documents et les conversations.
        
        Args:
            query: Requête de recherche
            user_id: ID de l'utilisateur
            max_results: Nombre maximum de résultats à retourner
            
        Returns:
            List[SearchResult]: Liste des résultats de recherche
            
        Raises:
            SearchError: Si une erreur se produit lors de la recherche
        """
        try:
            # Rechercher dans les documents
            document_results = self.search_documents(query, user_id, max_results)
            
            # Rechercher dans les conversations
            conversation_results = self.search_conversations(query, user_id, max_results)
            
            # Fusionner et trier les résultats par score
            all_results = document_results + conversation_results
            all_results.sort(key=lambda x: x.score, reverse=True)
            
            # Limiter le nombre de résultats
            return all_results[:max_results]
        
        except Exception as e:
            logger.exception(f"Erreur lors de la recherche: {query}")
            raise SearchError(f"Erreur lors de la recherche: {str(e)}")
    
    def search_documents(self, query: str, user_id: str, max_results: int = 5) -> List[SearchResult]:
        """
        Effectue une recherche dans les documents.
        
        Args:
            query: Requête de recherche
            user_id: ID de l'utilisateur
            max_results: Nombre maximum de résultats à retourner
            
        Returns:
            List[SearchResult]: Liste des résultats de recherche
            
        Raises:
            SearchError: Si une erreur se produit lors de la recherche
        """
        try:
            results = []
            
            # Rechercher dans les documents indexés
            for document_id, document in self._document_index.items():
                # Vérifier que le document appartient à l'utilisateur
                if document.metadata.get("user_id") != user_id:
                    continue
                
                # Calculer un score de pertinence simple
                score = self._calculate_relevance_score(query, document.title, document.content)
                
                if score > 0:
                    results.append(SearchResult(
                        id=document_id,
                        title=document.title,
                        content=document.content,
                        score=score,
                        metadata={
                            **document.metadata,
                            "type": "document"
                        }
                    ))
            
            # Trier les résultats par score
            results.sort(key=lambda x: x.score, reverse=True)
            
            # Limiter le nombre de résultats
            return results[:max_results]
        
        except Exception as e:
            logger.exception(f"Erreur lors de la recherche dans les documents: {query}")
            raise SearchError(f"Erreur lors de la recherche dans les documents: {str(e)}")
    
    def search_documentation(self, query: str, user_id: str, max_results: int = 5) -> List[SearchResult]:
        """
        Effectue une recherche dans la documentation.
        Cette méthode est un alias pour search_documents pour la compatibilité avec les tests.
        
        Args:
            query: Requête de recherche
            user_id: ID de l'utilisateur
            max_results: Nombre maximum de résultats à retourner
            
        Returns:
            List[SearchResult]: Liste des résultats de recherche
            
        Raises:
            SearchError: Si une erreur se produit lors de la recherche
        """
        return self.search_documents(query, user_id, max_results)
    
    def search_online(self, query: str, max_results: int = 5) -> List[Dict[str, str]]:
        """
        Effectue une recherche en ligne.
        
        Args:
            query: Requête de recherche
            max_results: Nombre maximum de résultats à retourner
            
        Returns:
            List[Dict[str, str]]: Liste des résultats de recherche
            
        Raises:
            SearchError: Si une erreur se produit lors de la recherche
        """
        try:
            # URL de l'API de recherche (simulée)
            api_url = "https://api.search.example.com/search"
            
            # Paramètres de la requête
            params = {
                "q": query,
                "limit": max_results
            }
            
            # Effectuer la requête
            response = requests.get(api_url, params=params)
            
            # Vérifier le code de statut
            if response.status_code != 200:
                raise SearchError(f"Erreur lors de la recherche en ligne: {response.status_code}")
            
            # Analyser la réponse
            data = response.json()
            
            # Extraire les résultats
            results = []
            for item in data.get("items", []):
                results.append({
                    "title": item.get("title", ""),
                    "url": item.get("link", ""),
                    "snippet": item.get("snippet", "")
                })
            
            return results[:max_results]
        
        except Exception as e:
            logger.exception(f"Erreur lors de la recherche en ligne: {query}")
            raise SearchError(f"Erreur lors de la recherche en ligne: {str(e)}")
    
    def search_conversations(self, query: str, user_id: str, max_results: int = 5) -> List[SearchResult]:
        """
        Effectue une recherche dans les conversations.
        
        Args:
            query: Requête de recherche
            user_id: ID de l'utilisateur
            max_results: Nombre maximum de résultats à retourner
            
        Returns:
            List[SearchResult]: Liste des résultats de recherche
            
        Raises:
            SearchError: Si une erreur se produit lors de la recherche
        """
        try:
            results = []
            
            # Rechercher dans les messages indexés
            for message_id, message in self._message_index.items():
                # Vérifier que le message appartient à l'utilisateur
                if message.metadata.get("user_id") != user_id:
                    continue
                
                # Calculer un score de pertinence simple
                score = self._calculate_relevance_score(query, "", message.content)
                
                if score > 0:
                    # Récupérer le titre de la conversation
                    conversation_id = message.metadata.get("conversation_id", "")
                    conversation_title = message.metadata.get("conversation_title", "Conversation")
                    
                    results.append(SearchResult(
                        id=message_id,
                        title=f"{conversation_title} - Message",
                        content=message.content,
                        score=score,
                        metadata={
                            **message.metadata,
                            "type": "message",
                            "conversation_id": conversation_id,
                            "role": message.role,
                            "timestamp": message.timestamp.isoformat() if hasattr(message, "timestamp") else datetime.now().isoformat()
                        }
                    ))
            
            # Trier les résultats par score
            results.sort(key=lambda x: x.score, reverse=True)
            
            # Limiter le nombre de résultats
            return results[:max_results]
        
        except Exception as e:
            logger.exception(f"Erreur lors de la recherche dans les conversations: {query}")
            raise SearchError(f"Erreur lors de la recherche dans les conversations: {str(e)}")
    
    def index_document(self, document: Document) -> None:
        """
        Indexe un document pour la recherche.
        
        Args:
            document: Document à indexer
        """
        if not document.id:
            return
        
        self._document_index[document.id] = document
        logger.debug(f"Document indexé: {document.id}")
    
    def index_message(self, message: Message) -> None:
        """
        Indexe un message pour la recherche.
        
        Args:
            message: Message à indexer
        """
        if not message.id:
            return
        
        self._message_index[message.id] = message
        logger.debug(f"Message indexé: {message.id}")
    
    def remove_document_from_index(self, document_id: str) -> None:
        """
        Supprime un document de l'index.
        
        Args:
            document_id: ID du document à supprimer
        """
        if document_id in self._document_index:
            del self._document_index[document_id]
            logger.debug(f"Document supprimé de l'index: {document_id}")
    
    def remove_message_from_index(self, message_id: str) -> None:
        """
        Supprime un message de l'index.
        
        Args:
            message_id: ID du message à supprimer
        """
        if message_id in self._message_index:
            del self._message_index[message_id]
            logger.debug(f"Message supprimé de l'index: {message_id}")
    
    def _calculate_relevance_score(self, query: str, title: str, content: str) -> float:
        """
        Calcule un score de pertinence simple pour une requête et un contenu.
        
        Args:
            query: Requête de recherche
            title: Titre du document ou du message
            content: Contenu du document ou du message
            
        Returns:
            float: Score de pertinence entre 0 et 1
        """
        # Normaliser la requête et le contenu
        query_lower = query.lower()
        title_lower = title.lower()
        content_lower = content.lower()
        
        # Diviser la requête en mots
        query_words = re.findall(r'\w+', query_lower)
        
        if not query_words:
            return 0.0
        
        # Compter les occurrences des mots de la requête dans le titre et le contenu
        title_matches = sum(1 for word in query_words if word in title_lower)
        content_matches = sum(1 for word in query_words if word in content_lower)
        
        # Calculer le score
        title_score = title_matches / len(query_words) * 0.6  # Le titre a un poids plus important
        content_score = content_matches / len(query_words) * 0.4
        
        # Bonus pour les correspondances exactes
        if query_lower in title_lower:
            title_score += 0.3
        
        if query_lower in content_lower:
            content_score += 0.2
        
        # Score final
        return min(title_score + content_score, 1.0) 