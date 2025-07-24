# api_clients/base.py
import requests
import logging
import time
from datetime import datetime
from typing import Dict, Any, Optional, List, Union
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

class ResponseHandler:
    """
    Classe responsable du traitement des réponses HTTP
    
    Respecte le principe de responsabilité unique en séparant le traitement
    des réponses de la gestion des requêtes.
    """
    
    @staticmethod
    def handle_response(response: requests.Response) -> Dict[str, Any]:
        """
        Traite la réponse HTTP et gère les erreurs.
        
        Args:
            response: Objet réponse de la requête HTTP
            
        Returns:
            Dictionnaire contenant la réponse décodée ou les détails de l'erreur
        """
        try:
            response.raise_for_status()
            
            # Si la réponse est vide ou n'est pas du JSON
            if not response.content:
                return {"success": True}
            
            try:
                return response.json()
            except ValueError:
                return {"success": True, "content": response.content.decode('utf-8')}
                
        except requests.exceptions.HTTPError as e:
            logger.error(f"Erreur HTTP: {e}")
            error_data = {"success": False, "error": str(e), "status_code": response.status_code}
            
            # Tenter de récupérer les détails de l'erreur depuis la réponse
            try:
                error_data.update(response.json())
            except ValueError:
                if response.content:
                    error_data["content"] = response.content.decode('utf-8')
            
            return error_data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Erreur de requête: {e}")
            return {"success": False, "error": str(e)}

class RequestExecutor:
    """
    Classe responsable de l'exécution de requêtes HTTP
    
    Prend en charge la construction et l'exécution de requêtes HTTP,
    avec gestion des erreurs.
    """
    
    def __init__(self, session: requests.Session, base_url: str, timeout: int, max_retries: int = 3):
        """
        Initialise l'exécuteur de requêtes

        Args:
            session: Session HTTP à utiliser
            base_url: URL de base pour les requêtes
            timeout: Délai d'attente pour les requêtes
            max_retries: Nombre maximum de tentatives en cas d'échec
        """
        self.session = session
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.max_retries = max_retries
        self.response_handler = ResponseHandler()

    def _execute_with_retry(self, request_func, *args, **kwargs) -> Dict[str, Any]:
        """
        Exécute une requête avec logique de retry et backoff exponentiel.

        Args:
            request_func: Fonction de requête à exécuter
            *args, **kwargs: Arguments pour la fonction de requête

        Returns:
            Dictionnaire contenant la réponse ou les détails de l'erreur
        """
        last_exception = None

        for attempt in range(self.max_retries + 1):
            try:
                response = request_func(*args, **kwargs)
                return ResponseHandler.handle_response(response)
            except (requests.exceptions.ConnectionError,
                    requests.exceptions.Timeout,
                    requests.exceptions.RequestException) as e:
                last_exception = e

                if attempt < self.max_retries:
                    # Backoff exponentiel: 1s, 2s, 4s, 8s...
                    wait_time = 2 ** attempt
                    logger.warning(f"Tentative {attempt + 1}/{self.max_retries + 1} échouée: {e}. "
                                 f"Nouvelle tentative dans {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"Toutes les tentatives ont échoué: {e}")

        return {"success": False, "error": str(last_exception)}

    def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Exécute une requête GET
        
        Args:
            endpoint: Point de terminaison de l'API
            params: Paramètres de la requête
            
        Returns:
            Dictionnaire contenant la réponse ou les détails de l'erreur
        """
        url = self._build_url(endpoint)
        return self._execute_with_retry(
            self.session.get, url, params=params, timeout=self.timeout
        )
    
    def post(self, endpoint: str, data: Optional[Dict[str, Any]] = None, 
             json_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Exécute une requête POST
        
        Args:
            endpoint: Point de terminaison de l'API
            data: Données de formulaire pour la requête
            json_data: Données JSON pour la requête
            
        Returns:
            Dictionnaire contenant la réponse ou les détails de l'erreur
        """
        url = self._build_url(endpoint)
        return self._execute_with_retry(
            self.session.post, url, data=data, json=json_data, timeout=self.timeout
        )
    
    def put(self, endpoint: str, data: Optional[Dict[str, Any]] = None, 
            json_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Exécute une requête PUT
        
        Args:
            endpoint: Point de terminaison de l'API
            data: Données de formulaire pour la requête
            json_data: Données JSON pour la requête
            
        Returns:
            Dictionnaire contenant la réponse ou les détails de l'erreur
        """
        url = self._build_url(endpoint)
        return self._execute_with_retry(
            self.session.put, url, data=data, json=json_data, timeout=self.timeout
        )
    
    def delete(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Exécute une requête DELETE
        
        Args:
            endpoint: Point de terminaison de l'API
            params: Paramètres de la requête
            
        Returns:
            Dictionnaire contenant la réponse ou les détails de l'erreur
        """
        url = self._build_url(endpoint)
        return self._execute_with_retry(
            self.session.delete, url, params=params, timeout=self.timeout
        )
    
    def _build_url(self, endpoint: str) -> str:
        """
        Construit l'URL complète à partir de l'URL de base et du point de terminaison
        
        Args:
            endpoint: Point de terminaison de l'API
            
        Returns:
            URL complète
        """
        return f"{self.base_url}/{endpoint.lstrip('/')}"

class BaseAPIClient(ABC):
    """
    Classe de base pour tous les clients API
    
    Fournit une interface commune et des fonctionnalités partagées pour
    tous les clients API du système.
    """
    
    def __init__(self, base_url: str, username: Optional[str] = None,
                 password: Optional[str] = None, token: Optional[str] = None,
                 verify_ssl: bool = True, timeout: int = 10, max_retries: int = 3):
        """
        Initialise le client API avec les paramètres de connexion de base.

        Args:
            base_url: URL de base de l'API
            username: Nom d'utilisateur pour l'authentification
            password: Mot de passe pour l'authentification
            token: Token d'API pour l'authentification
            verify_ssl: Vérifier les certificats SSL
            timeout: Délai d'attente en secondes pour les requêtes
            max_retries: Nombre maximum de tentatives en cas d'échec
        """
        self.base_url = base_url.rstrip('/')
        self.username = username
        self.password = password
        self.token = token
        self.verify_ssl = verify_ssl
        self.timeout = timeout
        self.max_retries = max_retries
        self.session = requests.Session()
        self._setup_session()

        # Créer l'exécuteur de requêtes avec retry
        self.executor = RequestExecutor(self.session, self.base_url, self.timeout, max_retries)
    
    def _setup_session(self) -> None:
        """Configure la session HTTP avec les en-têtes et l'authentification par défaut"""
        self.session.verify = self.verify_ssl
        
        # En-têtes par défaut
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
        
        # Configuration de l'authentification si nécessaire
        if self.token:
            self.session.headers.update({'Authorization': f'Bearer {self.token}'})
        elif self.username and self.password:
            self.session.auth = (self.username, self.password)
    
    def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Effectue une requête GET vers l'API.
        
        Args:
            endpoint: Point de terminaison de l'API
            params: Paramètres de la requête
            
        Returns:
            Dictionnaire contenant la réponse ou les détails de l'erreur
        """
        return self.executor.get(endpoint, params)
    
    def post(self, endpoint: str, data: Optional[Dict[str, Any]] = None, 
             json_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Effectue une requête POST vers l'API.
        
        Args:
            endpoint: Point de terminaison de l'API
            data: Données de formulaire pour la requête
            json_data: Données JSON pour la requête
            
        Returns:
            Dictionnaire contenant la réponse ou les détails de l'erreur
        """
        return self.executor.post(endpoint, data, json_data)
    
    def put(self, endpoint: str, data: Optional[Dict[str, Any]] = None, 
            json_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Effectue une requête PUT vers l'API.
        
        Args:
            endpoint: Point de terminaison de l'API
            data: Données de formulaire pour la requête
            json_data: Données JSON pour la requête
            
        Returns:
            Dictionnaire contenant la réponse ou les détails de l'erreur
        """
        return self.executor.put(endpoint, data, json_data)
    
    def delete(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Effectue une requête DELETE vers l'API.
        
        Args:
            endpoint: Point de terminaison de l'API
            params: Paramètres de la requête
            
        Returns:
            Dictionnaire contenant la réponse ou les détails de l'erreur
        """
        return self.executor.delete(endpoint, params)
    
    @abstractmethod
    def test_connection(self) -> bool:
        """
        Teste la connexion à l'API.

        Returns:
            True si la connexion est établie avec succès, False sinon
        """
        pass

    def get_headers(self, custom_headers: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        """
        Récupère les en-têtes HTTP actuels de la session.

        Args:
            custom_headers: En-têtes personnalisés à fusionner

        Returns:
            Dictionnaire des en-têtes HTTP
        """
        headers = dict(self.session.headers)
        if custom_headers:
            headers.update(custom_headers)
        return headers

    def build_url(self, endpoint: str) -> str:
        """
        Construit l'URL complète à partir de l'URL de base et du point de terminaison.

        Args:
            endpoint: Point de terminaison de l'API

        Returns:
            URL complète
        """
        return self.executor._build_url(endpoint)

    def validate_config(self, config: Dict[str, Any]) -> bool:
        """
        Valide une configuration de client API.

        Args:
            config: Configuration à valider

        Returns:
            True si la configuration est valide

        Raises:
            ValidationException: Si la configuration est invalide
        """
        from .domain.exceptions import ValidationException

        required_fields = ['base_url']

        for field in required_fields:
            if field not in config or not config[field]:
                raise ValidationException(f"Champ requis manquant: {field}")

        # Validation du timeout
        if 'timeout' in config:
            try:
                timeout = int(config['timeout'])
                if timeout <= 0:
                    raise ValidationException("Le timeout doit être positif")
            except (ValueError, TypeError):
                raise ValidationException("Le timeout doit être un entier")

        return True

    def handle_error(self, error: Exception, operation: str) -> None:
        """
        Gère les erreurs en les transformant en exceptions appropriées.

        Args:
            error: Exception à traiter
            operation: Nom de l'opération qui a échoué

        Raises:
            APIClientException: Exception appropriée selon le type d'erreur
        """
        from .domain.exceptions import (
            APIClientException, APIConnectionException,
            APIRequestException, APITimeoutException
        )

        if isinstance(error, requests.exceptions.ConnectionError):
            raise APIConnectionException(f"Erreur de connexion lors de {operation}: {error}")
        elif isinstance(error, requests.exceptions.Timeout):
            raise APITimeoutException(f"Timeout lors de {operation}: {error}")
        elif isinstance(error, requests.exceptions.HTTPError):
            raise APIRequestException(f"Erreur HTTP lors de {operation}: {error}")
        else:
            raise APIClientException(f"Erreur lors de {operation}: {error}")

    def health_check(self) -> Dict[str, Any]:
        """
        Effectue un contrôle de santé de l'API.

        Returns:
            Dictionnaire contenant le statut de santé
        """
        try:
            # Essayer de se connecter à l'API
            connection_ok = self.test_connection()

            return {
                'status': 'healthy' if connection_ok else 'unhealthy',
                'connection': connection_ok,
                'base_url': self.base_url,
                'timestamp': str(datetime.now())
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'connection': False,
                'base_url': self.base_url,
                'error': str(e),
                'timestamp': str(datetime.now())
            }

    def __str__(self) -> str:
        """Représentation string du client API."""
        return f"APIClient(base_url={self.base_url})"

    def __repr__(self) -> str:
        """Représentation détaillée du client API."""
        return f"BaseAPIClient(base_url='{self.base_url}', timeout={self.timeout}, verify_ssl={self.verify_ssl})"
