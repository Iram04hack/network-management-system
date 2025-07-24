"""
Implémentation de base pour les clients API.

Ce module fournit une classe de base pour les clients API
conforme à l'architecture hexagonale et suivant les principes SOLID.
"""

import requests
import logging
from typing import Dict, Any, Optional, Union
import time

from ..domain.interfaces import APIClientInterface, CircuitBreakerInterface, APIResponseHandler
from ..domain.exceptions import (
    APIConnectionException, 
    APIRequestException, 
    APIResponseException, 
    APITimeoutException,
    AuthenticationException
)

logger = logging.getLogger(__name__)

class BaseAPIClientImpl(APIClientInterface):
    """
    Classe de base pour les implémentations de clients API.
    
    Cette classe implémente l'interface APIClientInterface et inclut
    des fonctionnalités communes à tous les clients API.
    """
    
    def __init__(self, base_url: str, 
                username: Optional[str] = None, 
                password: Optional[str] = None, 
                token: Optional[str] = None,
                verify_ssl: bool = True, 
                timeout: int = 10,
                response_handler: Optional[APIResponseHandler] = None,
                circuit_breaker: Optional[CircuitBreakerInterface] = None):
        """
        Initialise le client API.
        
        Args:
            base_url: URL de base du service
            username: Nom d'utilisateur pour l'authentification
            password: Mot de passe pour l'authentification
            token: Token d'API pour l'authentification
            verify_ssl: Vérifier les certificats SSL
            timeout: Délai d'attente en secondes
            response_handler: Gestionnaire de réponses personnalisé
            circuit_breaker: Circuit breaker personnalisé
        """
        self.base_url = base_url.rstrip('/')
        self.username = username
        self.password = password
        self.token = token
        self.verify_ssl = verify_ssl
        self.timeout = timeout
        self.response_handler = response_handler
        self.circuit_breaker = circuit_breaker
        
        # Créer une session HTTP
        self.session = self._create_session()
    
    def test_connection(self) -> bool:
        """
        Teste la connexion au service.
        
        Returns:
            True si la connexion est établie avec succès, False sinon
        """
        try:
            if self.circuit_breaker:
                return self.circuit_breaker.execute(self._test_connection_impl)
            return self._test_connection_impl()
        except Exception as e:
            logger.error(f"Erreur lors du test de connexion à {self.base_url}: {str(e)}")
            return False
    
    def _test_connection_impl(self) -> bool:
        """
        Implémentation du test de connexion.
        
        Returns:
            True si la connexion est établie avec succès
            
        Raises:
            APIConnectionException: Si la connexion échoue
        """
        # À implémenter dans les sous-classes
        raise NotImplementedError("Cette méthode doit être implémentée dans les sous-classes")
    
    def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Effectue une requête GET.
        
        Args:
            endpoint: Point de terminaison de l'API
            params: Paramètres de la requête
            
        Returns:
            Réponse du service
            
        Raises:
            APIConnectionException: Si la connexion échoue
            APIResponseException: Si la réponse contient une erreur
            APITimeoutException: Si le délai d'attente est dépassé
        """
        url = self._build_url(endpoint)
        
        try:
            if self.circuit_breaker:
                return self.circuit_breaker.execute(self._request, "GET", url, params=params)
            return self._request("GET", url, params=params)
        except Exception as e:
            # Propager les exceptions du domaine telles quelles
            if any(isinstance(e, exc_type) for exc_type in [
                APIConnectionException, APIRequestException, 
                APIResponseException, APITimeoutException
            ]):
                raise
            
            # Convertir les autres exceptions
            if isinstance(e, requests.exceptions.Timeout):
                raise APITimeoutException(
                    f"Délai d'attente dépassé lors de la requête GET vers {url}", 
                    timeout=self.timeout
                ) from e
            elif isinstance(e, requests.exceptions.ConnectionError):
                raise APIConnectionException(f"Erreur de connexion lors de la requête GET vers {url}") from e
            else:
                raise APIRequestException(f"Erreur lors de la requête GET vers {url}: {str(e)}") from e
    
    def post(self, endpoint: str, data: Optional[Dict[str, Any]] = None, 
            json_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Effectue une requête POST.
        
        Args:
            endpoint: Point de terminaison de l'API
            data: Données de formulaire
            json_data: Données JSON
            
        Returns:
            Réponse du service
            
        Raises:
            APIConnectionException: Si la connexion échoue
            APIResponseException: Si la réponse contient une erreur
            APITimeoutException: Si le délai d'attente est dépassé
        """
        url = self._build_url(endpoint)
        
        try:
            if self.circuit_breaker:
                return self.circuit_breaker.execute(self._request, "POST", url, data=data, json=json_data)
            return self._request("POST", url, data=data, json=json_data)
        except Exception as e:
            # Propager les exceptions du domaine telles quelles
            if any(isinstance(e, exc_type) for exc_type in [
                APIConnectionException, APIRequestException, 
                APIResponseException, APITimeoutException
            ]):
                raise
            
            # Convertir les autres exceptions
            if isinstance(e, requests.exceptions.Timeout):
                raise APITimeoutException(
                    f"Délai d'attente dépassé lors de la requête POST vers {url}", 
                    timeout=self.timeout
                ) from e
            elif isinstance(e, requests.exceptions.ConnectionError):
                raise APIConnectionException(f"Erreur de connexion lors de la requête POST vers {url}") from e
            else:
                raise APIRequestException(f"Erreur lors de la requête POST vers {url}: {str(e)}") from e
    
    def put(self, endpoint: str, data: Optional[Dict[str, Any]] = None, 
           json_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Effectue une requête PUT.
        
        Args:
            endpoint: Point de terminaison de l'API
            data: Données de formulaire
            json_data: Données JSON
            
        Returns:
            Réponse du service
            
        Raises:
            APIConnectionException: Si la connexion échoue
            APIResponseException: Si la réponse contient une erreur
            APITimeoutException: Si le délai d'attente est dépassé
        """
        url = self._build_url(endpoint)
        
        try:
            if self.circuit_breaker:
                return self.circuit_breaker.execute(self._request, "PUT", url, data=data, json=json_data)
            return self._request("PUT", url, data=data, json=json_data)
        except Exception as e:
            # Propager les exceptions du domaine telles quelles
            if any(isinstance(e, exc_type) for exc_type in [
                APIConnectionException, APIRequestException, 
                APIResponseException, APITimeoutException
            ]):
                raise
            
            # Convertir les autres exceptions
            if isinstance(e, requests.exceptions.Timeout):
                raise APITimeoutException(
                    f"Délai d'attente dépassé lors de la requête PUT vers {url}", 
                    timeout=self.timeout
                ) from e
            elif isinstance(e, requests.exceptions.ConnectionError):
                raise APIConnectionException(f"Erreur de connexion lors de la requête PUT vers {url}") from e
            else:
                raise APIRequestException(f"Erreur lors de la requête PUT vers {url}: {str(e)}") from e
    
    def delete(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Effectue une requête DELETE.
        
        Args:
            endpoint: Point de terminaison de l'API
            params: Paramètres de la requête
            
        Returns:
            Réponse du service
            
        Raises:
            APIConnectionException: Si la connexion échoue
            APIResponseException: Si la réponse contient une erreur
            APITimeoutException: Si le délai d'attente est dépassé
        """
        url = self._build_url(endpoint)
        
        try:
            if self.circuit_breaker:
                return self.circuit_breaker.execute(self._request, "DELETE", url, params=params)
            return self._request("DELETE", url, params=params)
        except Exception as e:
            # Propager les exceptions du domaine telles quelles
            if any(isinstance(e, exc_type) for exc_type in [
                APIConnectionException, APIRequestException, 
                APIResponseException, APITimeoutException
            ]):
                raise
            
            # Convertir les autres exceptions
            if isinstance(e, requests.exceptions.Timeout):
                raise APITimeoutException(
                    f"Délai d'attente dépassé lors de la requête DELETE vers {url}", 
                    timeout=self.timeout
                ) from e
            elif isinstance(e, requests.exceptions.ConnectionError):
                raise APIConnectionException(f"Erreur de connexion lors de la requête DELETE vers {url}") from e
            else:
                raise APIRequestException(f"Erreur lors de la requête DELETE vers {url}: {str(e)}") from e
    
    def _create_session(self) -> requests.Session:
        """
        Crée une session HTTP avec les paramètres appropriés.
        
        Returns:
            Session HTTP configurée
        """
        session = requests.Session()
        session.verify = self.verify_ssl
        
        # En-têtes par défaut
        session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
        
        # Configuration de l'authentification
        if self.token:
            session.headers.update({'Authorization': f'Bearer {self.token}'})
        elif self.username and self.password:
            session.auth = (self.username, self.password)
        
        return session
    
    def _build_url(self, endpoint: str) -> str:
        """
        Construit l'URL complète pour un endpoint.
        
        Args:
            endpoint: Point de terminaison de l'API
            
        Returns:
            URL complète
        """
        return f"{self.base_url}/{endpoint.lstrip('/')}"
    
    def _request(self, method: str, url: str, **kwargs) -> Dict[str, Any]:
        """
        Effectue une requête HTTP.
        
        Args:
            method: Méthode HTTP (GET, POST, PUT, DELETE)
            url: URL complète
            **kwargs: Arguments supplémentaires pour la requête
            
        Returns:
            Réponse traitée
            
        Raises:
            APIConnectionException: Si la connexion échoue
            APIResponseException: Si la réponse contient une erreur
            APITimeoutException: Si le délai d'attente est dépassé
        """
        # Ajouter le timeout par défaut s'il n'est pas spécifié
        if 'timeout' not in kwargs:
            kwargs['timeout'] = self.timeout
        
        start_time = time.time()
        try:
            response = self.session.request(method, url, **kwargs)
            # Mesurer le temps de réponse
            response_time = time.time() - start_time
            logger.debug(f"Requête {method} vers {url} effectuée en {response_time:.2f}s")
            
            # Traiter la réponse
            if self.response_handler:
                return self.response_handler.handle_response(response)
            else:
                # Traitement par défaut
                response.raise_for_status()
                try:
                    return response.json() if response.content else {}
                except ValueError:
                    return {"content": response.text}
                
        except requests.exceptions.HTTPError as e:
            status_code = e.response.status_code if hasattr(e, 'response') else None
            error_data = {}
            
            try:
                if hasattr(e, 'response') and e.response.content:
                    error_data = e.response.json()
            except Exception:
                if hasattr(e, 'response'):
                    error_data = {"content": e.response.text}
            
            # Gérer spécifiquement les erreurs d'authentification
            if status_code in (401, 403):
                raise AuthenticationException(
                    f"Erreur d'authentification lors de la requête {method} vers {url}"
                ) from e
            
            raise APIResponseException(
                f"Erreur HTTP {status_code} lors de la requête {method} vers {url}",
                response_data=error_data,
                status_code=status_code
            )
 