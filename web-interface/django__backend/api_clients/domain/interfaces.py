"""
Interfaces du domaine pour les clients API.

Ce module définit les contrats d'interface pour les clients API
qui communiquent avec des services externes.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Union

class APIClientInterface(ABC):
    """Interface de base pour tous les clients API."""
    
    @abstractmethod
    def test_connection(self) -> bool:
        """
        Teste la connexion au service distant.
        
        Returns:
            True si la connexion est établie avec succès, False sinon
        """
        pass
    
    @abstractmethod
    def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Effectue une requête GET vers le service distant.
        
        Args:
            endpoint: Point de terminaison de l'API
            params: Paramètres de la requête
            
        Returns:
            Réponse du service distant
        """
        pass
    
    @abstractmethod
    def post(self, endpoint: str, data: Optional[Dict[str, Any]] = None, 
             json_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Effectue une requête POST vers le service distant.
        
        Args:
            endpoint: Point de terminaison de l'API
            data: Données de formulaire
            json_data: Données JSON
            
        Returns:
            Réponse du service distant
        """
        pass
    
    @abstractmethod
    def put(self, endpoint: str, data: Optional[Dict[str, Any]] = None, 
            json_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Effectue une requête PUT vers le service distant.
        
        Args:
            endpoint: Point de terminaison de l'API
            data: Données de formulaire
            json_data: Données JSON
            
        Returns:
            Réponse du service distant
        """
        pass
    
    @abstractmethod
    def delete(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Effectue une requête DELETE vers le service distant.
        
        Args:
            endpoint: Point de terminaison de l'API
            params: Paramètres de la requête
            
        Returns:
            Réponse du service distant
        """
        pass

class CircuitBreakerInterface(ABC):
    """
    Interface pour le pattern Circuit Breaker.
    
    Le circuit breaker permet de détecter les défaillances et d'éviter
    les requêtes inutiles vers un service défaillant.
    """
    
    @abstractmethod
    def execute(self, func, *args, **kwargs):
        """
        Exécute une fonction avec protection par circuit breaker.
        
        Args:
            func: Fonction à exécuter
            *args: Arguments de la fonction
            **kwargs: Arguments nommés de la fonction
            
        Returns:
            Résultat de la fonction
            
        Raises:
            CircuitBreakerOpenException: Si le circuit est ouvert
            Exception: Autres exceptions propagées depuis la fonction
        """
        pass
    
    @abstractmethod
    def reset(self):
        """Réinitialise l'état du circuit breaker."""
        pass
    
    @abstractmethod
    def get_state(self) -> str:
        """
        Retourne l'état actuel du circuit breaker.
        
        Returns:
            État du circuit ("OPEN", "CLOSED", "HALF-OPEN")
        """
        pass

class APIResponseHandler(ABC):
    """
    Interface pour le traitement des réponses API.
    
    Définit les contrats pour le traitement des réponses des services distants.
    """
    
    @abstractmethod
    def handle_response(self, response) -> Dict[str, Any]:
        """
        Traite une réponse d'API et gère les erreurs.
        
        Args:
            response: Réponse brute du service
            
        Returns:
            Données structurées de la réponse
            
        Raises:
            APIResponseException: Si la réponse contient des erreurs
        """
        pass
    
    @abstractmethod
    def handle_error(self, error) -> Dict[str, Any]:
        """
        Traite une erreur de requête API.
        
        Args:
            error: Exception ou erreur à traiter
            
        Returns:
            Données structurées de l'erreur
        """
        pass


class INetworkClient(APIClientInterface):
    """Interface pour les clients réseau (GNS3, SNMP, Netflow)."""

    @abstractmethod
    def get_network_status(self) -> Dict[str, Any]:
        """
        Récupère le statut du réseau.

        Returns:
            Statut du réseau
        """
        pass

    @abstractmethod
    def configure_network(self, config: Dict[str, Any]) -> bool:
        """
        Configure les paramètres réseau.

        Args:
            config: Configuration réseau

        Returns:
            True si la configuration a réussi
        """
        pass


class IMonitoringClient(APIClientInterface):
    """Interface pour les clients de monitoring (Prometheus, Grafana, Elasticsearch)."""

    @abstractmethod
    def get_metrics(self, query: str, timeframe: str = '1h') -> List[Dict[str, Any]]:
        """
        Récupère les métriques de monitoring.

        Args:
            query: Requête de métriques
            timeframe: Période de temps

        Returns:
            Liste des métriques
        """
        pass

    @abstractmethod
    def collect_data(self) -> Dict[str, Any]:
        """
        Collecte les données de monitoring.

        Returns:
            Données collectées
        """
        pass

    @abstractmethod
    def get_alerts(self) -> List[Dict[str, Any]]:
        """
        Récupère les alertes actives.

        Returns:
            Liste des alertes
        """
        pass


class IInfrastructureClient(APIClientInterface):
    """Interface pour les clients d'infrastructure (HAProxy, Traffic Control)."""

    @abstractmethod
    def deploy(self, config: Dict[str, Any]) -> bool:
        """
        Déploie une configuration d'infrastructure.

        Args:
            config: Configuration à déployer

        Returns:
            True si le déploiement a réussi
        """
        pass

    @abstractmethod
    def manage_resources(self, action: str, resources: List[str]) -> Dict[str, Any]:
        """
        Gère les ressources d'infrastructure.

        Args:
            action: Action à effectuer
            resources: Liste des ressources

        Returns:
            Résultat de l'action
        """
        pass

    @abstractmethod
    def get_infrastructure_status(self) -> Dict[str, Any]:
        """
        Récupère le statut de l'infrastructure.

        Returns:
            Statut de l'infrastructure
        """
        pass