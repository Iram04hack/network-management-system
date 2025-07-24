"""
Implémentation de la base de connaissances avec Elasticsearch.

Ce module contient l'implémentation de l'interface KnowledgeBase
utilisant Elasticsearch comme moteur de stockage et de recherche.
"""

from typing import List, Optional, Dict, Any, Union
import logging
import time
import numpy as np
from datetime import datetime
from django.conf import settings
from django.core.cache import cache

from ..domain.interfaces import KnowledgeBase
from ..domain.entities import Document, SearchResult
from ..domain.exceptions import KnowledgeBaseException

logger = logging.getLogger(__name__)

# Configuration du cache
CACHE_TIMEOUT = getattr(settings, 'AI_ASSISTANT_CACHE_TIMEOUT', 3600)  # 1 heure par défaut
CACHE_ENABLED = getattr(settings, 'AI_ASSISTANT_CACHE_ENABLED', True)

# Configuration des embeddings
ENABLE_EMBEDDINGS = getattr(settings, 'AI_ASSISTANT_ENABLE_EMBEDDINGS', False)
EMBEDDING_MODEL = getattr(settings, 'AI_ASSISTANT_EMBEDDING_MODEL', 'text-embedding-ada-002')
EMBEDDING_DIMENSION = getattr(settings, 'AI_ASSISTANT_EMBEDDING_DIMENSION', 768)


class ElasticsearchKnowledgeBase(KnowledgeBase):
    """
    Implémentation de la base de connaissances utilisant Elasticsearch.
    
    Cette classe fournit une implémentation concrète de l'interface KnowledgeBase,
    permettant de stocker et rechercher des documents dans Elasticsearch.
    """
    
    def __init__(self, index_name: str = "network_knowledge"):
        """
        Initialise la base de connaissances Elasticsearch.
        
        Args:
            index_name: Nom de l'index Elasticsearch à utiliser
        """
        self.index_name = index_name
        self.client = None
        self.embedding_client = None
        self._initialize_client()
        if ENABLE_EMBEDDINGS:
            self._initialize_embedding_client()
    
    def _initialize_client(self):
        """Initialise le client Elasticsearch."""
        try:
            # Import ici pour éviter une dépendance au niveau du module
            from elasticsearch import Elasticsearch
            
            # Configuration du client Elasticsearch
            es_host = getattr(settings, 'ELASTICSEARCH_HOST', 'localhost')
            es_port = getattr(settings, 'ELASTICSEARCH_PORT', 9200)
            es_user = getattr(settings, 'ELASTICSEARCH_USER', '')
            es_password = getattr(settings, 'ELASTICSEARCH_PASSWORD', '')
            
            # Vérifier si Elasticsearch est requis
            require_elasticsearch = getattr(settings, 'REQUIRE_ELASTICSEARCH', False)
            
            # Construction de l'URL
            es_url = f"http://{es_host}:{es_port}"
            
            # Configuration de l'authentification si nécessaire
            if es_user and es_password:
                self.client = Elasticsearch(es_url, basic_auth=(es_user, es_password))
            else:
                self.client = Elasticsearch(es_url)
            
            # Vérification de la connexion
            if not self.client.ping():
                if require_elasticsearch:
                    raise KnowledgeBaseException(
                        "Elasticsearch est requis mais inaccessible. "
                        f"Vérifiez la connectivité à {es_url}",
                        "elasticsearch_required"
                    )
                else:
                    logger.warning(
                        "Impossible de se connecter à Elasticsearch (%s). "
                        "Les fonctionnalités de recherche seront limitées.",
                        es_url
                    )
                    self.client = None
            else:
                # Vérification de l'existence de l'index
                if not self.client.indices.exists(index=self.index_name):
                    # Création de l'index avec un mapping adapté
                    self._create_index()
                    
                logger.info(f"Connexion établie avec Elasticsearch à {es_url} sur l'index {self.index_name}")
        except ImportError:
            if require_elasticsearch:
                raise KnowledgeBaseException(
                    "Le package Elasticsearch est requis mais n'est pas installé. "
                    "Installez-le avec 'pip install elasticsearch'",
                    "elasticsearch_package"
                )
            else:
                logger.warning(
                    "La bibliothèque Elasticsearch n'est pas installée. "
                    "Les fonctionnalités de recherche seront limitées."
                )
                self.client = None
        except Exception as e:
            error_message = f"Erreur lors de l'initialisation du client Elasticsearch: {e}"
            logger.exception(error_message)
            
            if require_elasticsearch:
                raise KnowledgeBaseException(error_message, "elasticsearch_error")
            else:
                self.client = None
    
    def _initialize_embedding_client(self):
        """Initialise le client pour générer des embeddings."""
        if not ENABLE_EMBEDDINGS:
            return
            
        try:
            # Tentative d'import du client OpenAI pour les embeddings
            try:
                from openai import OpenAI
                
                # Récupération de la clé API
                api_key = getattr(settings, 'DEFAULT_AI_API_KEY', None)
                if not api_key:
                    logger.warning("Clé API manquante pour les embeddings. Les embeddings seront désactivés.")
                    return
                    
                self.embedding_client = OpenAI(api_key=api_key)
                logger.info("Client d'embeddings initialisé avec succès")
            except ImportError:
                logger.warning("La bibliothèque OpenAI n'est pas installée. Les embeddings seront désactivés.")
                
        except Exception as e:
            logger.exception(f"Erreur lors de l'initialisation du client d'embeddings: {e}")
    
    def _create_index(self):
        """Crée l'index avec le mapping approprié."""
        if not self.client:
            return
        
        try:
            # Définir le mapping avec support pour les embeddings
            mapping = {
                "mappings": {
                    "properties": {
                        "title": {"type": "text", "analyzer": "standard"},
                        "content": {"type": "text", "analyzer": "standard"},
                        "metadata": {"type": "object"},
                        "created_at": {"type": "date"},
                        "updated_at": {"type": "date"}
                    }
                },
                "settings": {
                    "number_of_shards": 1,
                    "number_of_replicas": 0,
                    "analysis": {
                        "analyzer": {
                            "standard": {
                                "type": "standard",
                                "stopwords": "_french_"
                            }
                        }
                    }
                }
            }
            
            # Ajouter le champ embedding si activé
            if ENABLE_EMBEDDINGS:
                mapping["mappings"]["properties"]["embedding"] = {
                    "type": "dense_vector",
                    "dims": EMBEDDING_DIMENSION
                }
            
            self.client.indices.create(index=self.index_name, body=mapping)
            logger.info("Index '%s' créé avec succès", self.index_name)
        except Exception as e:
            logger.exception("Erreur lors de la création de l'index: %s", e)
    
    def _generate_embedding(self, text: str) -> Optional[List[float]]:
        """
        Génère un embedding pour le texte donné.
        
        Args:
            text: Texte pour lequel générer un embedding
            
        Returns:
            Liste des valeurs de l'embedding ou None en cas d'erreur
        """
        if not ENABLE_EMBEDDINGS or not self.embedding_client:
            return None
            
        try:
            # Limiter la taille du texte pour éviter les dépassements de tokens
            max_text_length = 8000
            if len(text) > max_text_length:
                text = text[:max_text_length]
                
            # Générer l'embedding via l'API OpenAI
            response = self.embedding_client.embeddings.create(
                input=text,
                model=EMBEDDING_MODEL
            )
            
            # Extraire et retourner l'embedding
            return response.data[0].embedding
            
        except Exception as e:
            logger.exception(f"Erreur lors de la génération de l'embedding: {e}")
            return None
    
    def add_document(self, document: Document) -> str:
        """
        Ajoute un document à la base de connaissances.
        
        Args:
            document: Le document à ajouter
            
        Returns:
            L'identifiant du document ajouté
            
        Raises:
            KnowledgeBaseException: Si une erreur survient lors de l'ajout
        """
        if not self.client:
            raise KnowledgeBaseException("Client Elasticsearch non initialisé", "elasticsearch")
        
        try:
            # Préparation du document pour Elasticsearch
            doc = {
                "title": document.title,
                "content": document.content,
                "metadata": document.metadata,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            
            # Générer et ajouter l'embedding si activé
            if ENABLE_EMBEDDINGS:
                # Combiner le titre et le contenu pour l'embedding
                text_for_embedding = f"{document.title} {document.content}"
                embedding = self._generate_embedding(text_for_embedding)
                
                if embedding:
                    doc["embedding"] = embedding
            
            # Ajout du document à l'index
            response = self.client.index(index=self.index_name, document=doc)
            
            # Invalider le cache de recherche
            if CACHE_ENABLED:
                cache.delete_pattern("kb_search:*")
            
            return response["_id"]
        except Exception as e:
            logger.exception("Erreur lors de l'ajout du document: %s", e)
            raise KnowledgeBaseException(
                f"Erreur lors de l'ajout du document: {e}",
                "elasticsearch"
            ) from e
    
    def search(self, query: str, limit: int = 5, threshold: float = 0.7) -> List[Dict[str, Any]]:
        """
        Recherche des documents dans la base de connaissances.
        
        Args:
            query: La requête de recherche
            limit: Nombre maximum de résultats à retourner
            threshold: Seuil de pertinence minimal pour les résultats
            
        Returns:
            Liste des résultats de recherche sous forme de dictionnaires
            
        Raises:
            KnowledgeBaseException: Si une erreur survient lors de la recherche
        """
        if not self.client:
            raise KnowledgeBaseException("Client Elasticsearch non initialisé", "elasticsearch")
        
        # Vérifier si le résultat est en cache
        if CACHE_ENABLED:
            cache_key = f"kb_search:{query}:{limit}:{threshold}"
            cached_results = cache.get(cache_key)
            if cached_results:
                logger.debug(f"Résultats de recherche récupérés du cache pour '{query}'")
                return cached_results
        
        try:
            start_time = time.time()
            
            # Déterminer la méthode de recherche à utiliser
            if ENABLE_EMBEDDINGS and self.embedding_client:
                results = self._search_with_embeddings(query, limit, threshold)
            else:
                results = self._search_with_text(query, limit, threshold)
                
            # Mesurer le temps de recherche
            search_time = time.time() - start_time
            logger.debug(f"Recherche pour '{query}' effectuée en {search_time:.3f}s")
            
            # Mettre en cache les résultats
            if CACHE_ENABLED:
                cache.set(cache_key, results, CACHE_TIMEOUT)
            
            return results
        except Exception as e:
            logger.exception("Erreur lors de la recherche: %s", e)
            raise KnowledgeBaseException(
                f"Erreur lors de la recherche: {e}",
                "elasticsearch"
            ) from e
    
    def _search_with_text(self, query: str, limit: int, threshold: float) -> List[Dict[str, Any]]:
        """
        Recherche des documents par correspondance de texte.
        
        Args:
            query: La requête de recherche
            limit: Nombre maximum de résultats
            threshold: Seuil de pertinence
            
        Returns:
            Liste des résultats de recherche
        """
        # Construction de la requête Elasticsearch
        search_query = {
            "query": {
                "multi_match": {
                    "query": query,
                    "fields": ["title^2", "content"],
                    "fuzziness": "AUTO",
                    "operator": "or"
                }
            },
            "size": limit * 2,  # Récupérer plus de résultats pour filtrer par seuil
            "_source": ["title", "content", "metadata", "created_at", "updated_at"]
        }
        
        # Exécution de la recherche
        response = self.client.search(index=self.index_name, body=search_query)
        
        # Conversion et filtrage des résultats
        results = []
        for hit in response["hits"]["hits"]:
            score = hit["_score"]
            # Normaliser le score entre 0 et 1
            normalized_score = score / 10.0  # Ajuster selon les scores typiques d'Elasticsearch
            normalized_score = min(normalized_score, 1.0)
            
            # Application du seuil de pertinence
            if normalized_score < threshold:
                continue
                
            source = hit["_source"]
            result = {
                "id": hit["_id"],
                "title": source.get("title", ""),
                "content": source.get("content", ""),
                "metadata": source.get("metadata", {}),
                "score": normalized_score,
                "created_at": source.get("created_at"),
                "updated_at": source.get("updated_at")
            }
            results.append(result)
            
            # Limiter le nombre de résultats
            if len(results) >= limit:
                break
        
        return results
    
    def _search_with_embeddings(self, query: str, limit: int, threshold: float) -> List[Dict[str, Any]]:
        """
        Recherche des documents en utilisant des embeddings vectoriels.
        
        Args:
            query: La requête de recherche
            limit: Nombre maximum de résultats
            threshold: Seuil de pertinence
            
        Returns:
            Liste des résultats de recherche
        """
        # Générer l'embedding pour la requête
        query_embedding = self._generate_embedding(query)
        if not query_embedding:
            # Fallback vers la recherche textuelle si l'embedding échoue
            logger.warning("Impossible de générer un embedding pour la requête, utilisation de la recherche textuelle")
            return self._search_with_text(query, limit, threshold)
        
        # Construction de la requête avec script_score pour la similarité cosinus
        search_query = {
            "query": {
                "script_score": {
                    "query": {"match_all": {}},
                    "script": {
                        "source": "cosineSimilarity(params.query_vector, 'embedding') + 1.0",
                        "params": {"query_vector": query_embedding}
                    }
                }
            },
            "size": limit * 2,  # Récupérer plus de résultats pour filtrer par seuil
            "_source": ["title", "content", "metadata", "created_at", "updated_at"]
        }
        
        # Exécution de la recherche
        response = self.client.search(index=self.index_name, body=search_query)
        
        # Conversion et filtrage des résultats
        results = []
        for hit in response["hits"]["hits"]:
            # Le score est entre 0 et 2 (cosine similarity + 1.0)
            score = hit["_score"]
            normalized_score = (score - 1.0)  # Ramener entre 0 et 1
            
            # Application du seuil de pertinence
            if normalized_score < threshold:
                continue
                
            source = hit["_source"]
            result = {
                "id": hit["_id"],
                "title": source.get("title", ""),
                "content": source.get("content", ""),
                "metadata": source.get("metadata", {}),
                "score": normalized_score,
                "created_at": source.get("created_at"),
                "updated_at": source.get("updated_at")
            }
            results.append(result)
            
            # Limiter le nombre de résultats
            if len(results) >= limit:
                break
        
        return results
    
    def get_document(self, document_id: str) -> Optional[Document]:
        """
        Récupère un document par son identifiant.
        
        Args:
            document_id: L'identifiant du document
            
        Returns:
            Le document ou None s'il n'existe pas
            
        Raises:
            KnowledgeBaseException: Si une erreur survient lors de la récupération
        """
        if not self.client:
            raise KnowledgeBaseException("Client Elasticsearch non initialisé", "elasticsearch")
        
        try:
            # Vérifier si le document existe
            if not self.client.exists(index=self.index_name, id=document_id):
                return None
                
            # Récupération du document
            response = self.client.get(index=self.index_name, id=document_id)
            source = response["_source"]
            
            # Conversion en objet Document
            return Document(
                title=source.get("title", ""),
                content=source.get("content", ""),
                metadata=source.get("metadata", {})
            )
        except Exception as e:
            logger.exception("Erreur lors de la récupération du document: %s", e)
            raise KnowledgeBaseException(
                f"Erreur lors de la récupération du document: {e}",
                "elasticsearch"
            ) from e
    
    def update_document(self, document_id: str, document: Document) -> bool:
        """
        Met à jour un document existant.
        
        Args:
            document_id: L'identifiant du document à mettre à jour
            document: Le document avec les nouvelles valeurs
            
        Returns:
            True si la mise à jour a réussi, False sinon
            
        Raises:
            KnowledgeBaseException: Si une erreur survient lors de la mise à jour
        """
        if not self.client:
            raise KnowledgeBaseException("Client Elasticsearch non initialisé", "elasticsearch")
        
        try:
            # Vérifier si le document existe
            if not self.client.exists(index=self.index_name, id=document_id):
                logger.warning(f"Document {document_id} non trouvé pour la mise à jour")
                return False
                
            # Préparation du document pour la mise à jour
            doc = {
                "title": document.title,
                "content": document.content,
                "metadata": document.metadata,
                "updated_at": datetime.now().isoformat()
            }
            
            # Générer et ajouter l'embedding si activé
            if ENABLE_EMBEDDINGS:
                text_for_embedding = f"{document.title} {document.content}"
                embedding = self._generate_embedding(text_for_embedding)
                
                if embedding:
                    doc["embedding"] = embedding
            
            # Mise à jour du document
            self.client.update(
                index=self.index_name,
                id=document_id,
                doc=doc
            )
            
            # Invalider le cache de recherche
            if CACHE_ENABLED:
                cache.delete_pattern("kb_search:*")
            
            return True
        except Exception as e:
            logger.exception("Erreur lors de la mise à jour du document: %s", e)
            raise KnowledgeBaseException(
                f"Erreur lors de la mise à jour du document: {e}",
                "elasticsearch"
            ) from e
    
    def delete_document(self, document_id: str) -> bool:
        """
        Supprime un document.
        
        Args:
            document_id: L'identifiant du document à supprimer
            
        Returns:
            True si la suppression a réussi, False sinon
            
        Raises:
            KnowledgeBaseException: Si une erreur survient lors de la suppression
        """
        if not self.client:
            raise KnowledgeBaseException("Client Elasticsearch non initialisé", "elasticsearch")
        
        try:
            # Vérifier si le document existe
            if not self.client.exists(index=self.index_name, id=document_id):
                logger.warning(f"Document {document_id} non trouvé pour la suppression")
                return False
                
            # Suppression du document
            self.client.delete(
                index=self.index_name,
                id=document_id
            )
            
            # Invalider le cache de recherche
            if CACHE_ENABLED:
                cache.delete_pattern("kb_search:*")
            
            return True
        except Exception as e:
            logger.exception("Erreur lors de la suppression du document: %s", e)
            raise KnowledgeBaseException(
                f"Erreur lors de la suppression du document: {e}",
                "elasticsearch"
            ) from e
    
    def bulk_add_documents(self, documents: List[Document]) -> List[str]:
        """
        Ajoute plusieurs documents en une seule opération.
        
        Args:
            documents: Liste des documents à ajouter
            
        Returns:
            Liste des identifiants des documents ajoutés
            
        Raises:
            KnowledgeBaseException: Si une erreur survient lors de l'ajout
        """
        if not self.client:
            raise KnowledgeBaseException("Client Elasticsearch non initialisé", "elasticsearch")
        
        if not documents:
            return []
            
        try:
            # Préparation des actions pour l'opération bulk
            actions = []
            
            for document in documents:
                # Préparation du document
                doc = {
                    "title": document.title,
                    "content": document.content,
                    "metadata": document.metadata,
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat()
                }
                
                # Générer et ajouter l'embedding si activé
                if ENABLE_EMBEDDINGS:
                    text_for_embedding = f"{document.title} {document.content}"
                    embedding = self._generate_embedding(text_for_embedding)
                    
                    if embedding:
                        doc["embedding"] = embedding
                
                # Ajouter l'action d'indexation
                actions.append({"index": {"_index": self.index_name}})
                actions.append(doc)
            
            # Exécution de l'opération bulk
            response = self.client.bulk(body=actions, refresh=True)
            
            # Extraction des identifiants
            ids = []
            for item in response["items"]:
                if "index" in item and "_id" in item["index"]:
                    ids.append(item["index"]["_id"])
            
            # Invalider le cache de recherche
            if CACHE_ENABLED:
                cache.delete_pattern("kb_search:*")
            
            return ids
        except Exception as e:
            logger.exception("Erreur lors de l'ajout en masse de documents: %s", e)
            raise KnowledgeBaseException(
                f"Erreur lors de l'ajout en masse de documents: {e}",
                "elasticsearch"
            ) from e
