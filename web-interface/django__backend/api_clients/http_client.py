"""
Module client HTTP pour les requêtes API externes.

Ce module fournit une classe HttpClient qui encapsule les fonctionnalités
de requêtes HTTP vers des API externes.
"""

import logging
import requests
from typing import Any, Dict, Optional, Union
from requests.exceptions import RequestException

logger = logging.getLogger(__name__)

class HttpClient:
    """
    Client HTTP pour les requêtes API externes.
    
    Cette classe encapsule les fonctionnalités de requêtes HTTP vers des API externes,
    avec gestion des erreurs, des timeouts et des options SSL.
    """
    
    def __init__(
        self, 
        base_url: str = "", 
        timeout: int = 30, 
        verify_ssl: bool = True,
        headers: Optional[Dict[str, str]] = None
    ):
        """
        Initialise un nouveau client HTTP.
        
        Args:
            base_url: URL de base pour toutes les requêtes
            timeout: Timeout en secondes pour les requêtes
            verify_ssl: Si True, vérifie les certificats SSL
            headers: En-têtes HTTP par défaut à inclure dans toutes les requêtes
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.verify_ssl = verify_ssl
        self.headers = headers or {}
        
    def _build_url(self, endpoint: str) -> str:
        """
        Construit l'URL complète pour un endpoint donné.
        
        Args:
            endpoint: Endpoint API relatif ou absolu
            
        Returns:
            URL complète
        """
        if endpoint.startswith(('http://', 'https://')):
            return endpoint
        
        endpoint = endpoint.lstrip('/')
        return f"{self.base_url}/{endpoint}" if self.base_url else endpoint
    
    def _handle_request_exception(self, method: str, url: str, exception: Exception) -> None:
        """
        Gère les exceptions de requête HTTP.
        
        Args:
            method: Méthode HTTP utilisée
            url: URL de la requête
            exception: Exception levée
        """
        logger.error(f"Erreur lors de la requête {method} vers {url}: {str(exception)}")
        raise exception
    
    def get(
        self, 
        endpoint: str, 
        params: Optional[Dict[str, Any]] = None, 
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[int] = None
    ) -> requests.Response:
        """
        Effectue une requête GET.
        
        Args:
            endpoint: Endpoint API
            params: Paramètres de requête
            headers: En-têtes HTTP supplémentaires
            timeout: Timeout spécifique pour cette requête
            
        Returns:
            Réponse HTTP
            
        Raises:
            RequestException: En cas d'erreur de requête
        """
        url = self._build_url(endpoint)
        merged_headers = {**self.headers, **(headers or {})}
        
        try:
            return requests.get(
                url,
                params=params,
                headers=merged_headers,
                timeout=timeout or self.timeout,
                verify=self.verify_ssl
            )
        except RequestException as e:
            self._handle_request_exception('GET', url, e)
    
    def post(
        self, 
        endpoint: str, 
        data: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[int] = None
    ) -> requests.Response:
        """
        Effectue une requête POST.
        
        Args:
            endpoint: Endpoint API
            data: Données de formulaire
            json: Données JSON
            headers: En-têtes HTTP supplémentaires
            timeout: Timeout spécifique pour cette requête
            
        Returns:
            Réponse HTTP
            
        Raises:
            RequestException: En cas d'erreur de requête
        """
        url = self._build_url(endpoint)
        merged_headers = {**self.headers, **(headers or {})}
        
        try:
            return requests.post(
                url,
                data=data,
                json=json,
                headers=merged_headers,
                timeout=timeout or self.timeout,
                verify=self.verify_ssl
            )
        except RequestException as e:
            self._handle_request_exception('POST', url, e)
    
    def put(
        self, 
        endpoint: str, 
        data: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[int] = None
    ) -> requests.Response:
        """
        Effectue une requête PUT.
        
        Args:
            endpoint: Endpoint API
            data: Données de formulaire
            json: Données JSON
            headers: En-têtes HTTP supplémentaires
            timeout: Timeout spécifique pour cette requête
            
        Returns:
            Réponse HTTP
            
        Raises:
            RequestException: En cas d'erreur de requête
        """
        url = self._build_url(endpoint)
        merged_headers = {**self.headers, **(headers or {})}
        
        try:
            return requests.put(
                url,
                data=data,
                json=json,
                headers=merged_headers,
                timeout=timeout or self.timeout,
                verify=self.verify_ssl
            )
        except RequestException as e:
            self._handle_request_exception('PUT', url, e)
    
    def delete(
        self, 
        endpoint: str, 
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[int] = None
    ) -> requests.Response:
        """
        Effectue une requête DELETE.
        
        Args:
            endpoint: Endpoint API
            params: Paramètres de requête
            headers: En-têtes HTTP supplémentaires
            timeout: Timeout spécifique pour cette requête
            
        Returns:
            Réponse HTTP
            
        Raises:
            RequestException: En cas d'erreur de requête
        """
        url = self._build_url(endpoint)
        merged_headers = {**self.headers, **(headers or {})}
        
        try:
            return requests.delete(
                url,
                params=params,
                headers=merged_headers,
                timeout=timeout or self.timeout,
                verify=self.verify_ssl
            )
        except RequestException as e:
            self._handle_request_exception('DELETE', url, e) 