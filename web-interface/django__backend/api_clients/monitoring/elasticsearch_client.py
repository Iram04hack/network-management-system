from ..base import BaseAPIClient
import logging
from typing import Dict, Any, Optional, List, Union

logger = logging.getLogger(__name__)

class ElasticsearchClient(BaseAPIClient):
    """Client pour interagir avec l'API REST d'Elasticsearch"""
    
    def __init__(self, base_url: str, username: Optional[str] = None,
                 password: Optional[str] = None, api_key: Optional[str] = None,
                 verify_ssl: bool = True, timeout: int = 10):
        """
        Initialise le client Elasticsearch.
        
        Args:
            base_url: URL de base de l'API Elasticsearch (ex: http://localhost:9200)
            username: Nom d'utilisateur pour l'authentification basique
            password: Mot de passe pour l'authentification basique
            api_key: Clé API pour l'authentification (format base64 'id:api_key')
            verify_ssl: Vérifier les certificats SSL
            timeout: Délai d'attente en secondes pour les requêtes
        """
        # Définir api_key AVANT d'appeler super().__init__
        self.api_key = api_key

        if api_key:
            token = None
            # Nous configurons l'API key dans _setup_session
        else:
            token = None

        super().__init__(base_url, username, password, token, verify_ssl, timeout)
    
    def _setup_session(self) -> None:
        """Configure la session HTTP avec les en-têtes et l'authentification par défaut"""
        super()._setup_session()
        
        # Si une clé API est fournie, configurer l'authentification avec cette clé
        if self.api_key:
            self.session.headers.update({
                'Authorization': f'ApiKey {self.api_key}'
            })
    
    def test_connection(self) -> bool:
        """
        Teste la connexion à l'API Elasticsearch.
        
        Returns:
            True si la connexion est établie avec succès, False sinon
        """
        response = self.get("")
        return response.get("success", False) and "name" in response
    
    def get_cluster_health(self) -> Dict[str, Any]:
        """
        Récupère l'état de santé du cluster.
        
        Returns:
            Informations sur l'état du cluster
        """
        return self.get("_cluster/health")
    
    def get_indices(self) -> Dict[str, Any]:
        """
        Récupère la liste des indices.
        
        Returns:
            Liste des indices
        """
        return self.get("_cat/indices?format=json")
    
    def create_index(self, index_name: str, settings: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crée un nouvel indice.
        
        Args:
            index_name: Nom de l'indice
            settings: Configuration de l'indice
            
        Returns:
            Résultat de la création
        """
        return self.put(index_name, json_data=settings)
    
    def delete_index(self, index_name: str) -> Dict[str, Any]:
        """
        Supprime un indice existant.
        
        Args:
            index_name: Nom de l'indice à supprimer
            
        Returns:
            Résultat de la suppression
        """
        return self.delete(index_name)
    
    def search(self, index: str, query: Dict[str, Any], size: int = 10) -> Dict[str, Any]:
        """
        Exécute une recherche sur un ou plusieurs indices.
        
        Args:
            index: Nom de l'indice ou pattern (ex: 'logs-*')
            query: Requête de recherche au format DSL Elasticsearch
            size: Nombre maximum de résultats à retourner
            
        Returns:
            Résultats de la recherche
        """
        params = {'size': size}
        return self.post(f"{index}/_search", json_data=query, params=params)
    
    def count(self, index: str, query: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compte le nombre de documents correspondant à une requête.
        
        Args:
            index: Nom de l'indice ou pattern (ex: 'logs-*')
            query: Requête de recherche au format DSL Elasticsearch
            
        Returns:
            Résultat du comptage (nombre de documents)
        """
        return self.post(f"{index}/_count", json_data=query)
    
    def get_document(self, index: str, doc_id: str) -> Dict[str, Any]:
        """
        Récupère un document par son ID.
        
        Args:
            index: Nom de l'indice
            doc_id: ID du document
            
        Returns:
            Document récupéré
        """
        return self.get(f"{index}/_doc/{doc_id}")
    
    def index_document(self, index: str, doc: Dict[str, Any], doc_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Indexe un document, avec création ou mise à jour.
        
        Args:
            index: Nom de l'indice
            doc: Contenu du document à indexer
            doc_id: ID du document (généré automatiquement si non fourni)
            
        Returns:
            Résultat de l'indexation
        """
        if doc_id:
            return self.put(f"{index}/_doc/{doc_id}", json_data=doc)
        else:
            return self.post(f"{index}/_doc", json_data=doc) 