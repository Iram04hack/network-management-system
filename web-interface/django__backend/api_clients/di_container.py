"""
Module de conteneur d'injection de dépendances pour les clients API.

Ce module définit le conteneur d'injection de dépendances pour les clients API
qui permettent d'interagir avec les différents services externes.
"""

import logging
from typing import Any, Dict, Optional, Type

from dependency_injector import containers, providers

from api_clients.http_client import HttpClient
from api_clients.response_handler import ResponseHandler

from .domain.interfaces import (
    APIClientInterface,
    CircuitBreakerInterface,
    APIResponseHandler
)

from .infrastructure.circuit_breaker import DefaultCircuitBreaker

logger = logging.getLogger(__name__)

class APIClientsContainer(containers.DeclarativeContainer):
    """
    Conteneur d'injection de dépendances pour les clients API.
    
    Ce conteneur fournit des clients pour interagir avec différentes API externes,
    organisés par domaine fonctionnel.
    """
    
    config = providers.Configuration()
    
    # Client de base pour les requêtes HTTP
    http_client = providers.Factory(
        HttpClient,
        base_url=config.base_url,
        timeout=config.timeout,
        verify_ssl=config.verify_ssl
    )
    
    # Clients API organisés par domaine fonctionnel
    network_clients = providers.Dict()
    security_clients = providers.Dict()
    monitoring_clients = providers.Dict()
    qos_clients = providers.Dict()
    
    # Composants d'infrastructure communs
    circuit_breaker_config = providers.Factory(
        lambda f, r, h: __import__('api_clients.infrastructure.circuit_breaker', fromlist=['CircuitBreakerConfig']).CircuitBreakerConfig(
            failure_threshold=f,
            reset_timeout=r,
            half_open_success_threshold=h
        ),
        f=config.circuit_breaker.failure_threshold.as_int(),
        r=config.circuit_breaker.reset_timeout.as_float(),
        h=config.circuit_breaker.half_open_success_threshold.as_int()
    )
    
    circuit_breaker_factory = providers.Factory(
        DefaultCircuitBreaker,
        config=circuit_breaker_config
    )
    
    response_handler = providers.Singleton(
        ResponseHandler
    )
    
    # Fonction utilitaire pour enregistrer un client API
    def register_client(self, client_type, implementation_class):
        """
        Enregistre un nouveau client API dans le conteneur.
        
        Args:
            client_type: Type d'interface du client
            implementation_class: Classe d'implémentation
        """
        setattr(self, client_type.__name__, providers.Singleton(implementation_class))


# Instance globale du conteneur
_container = None

def get_container():
    """
    Récupère l'instance globale du conteneur d'injection de dépendances.
    
    Returns:
        Instance du conteneur d'injection de dépendances
    """
    global _container
    
    if _container is None:
        # Charger la configuration depuis les paramètres Django
        from django.conf import settings
        
        _container = APIClientsContainer()
        _container.config.from_dict({
            'circuit_breaker': {
                'failure_threshold': getattr(settings, 'API_CLIENT_FAILURE_THRESHOLD', 5),
                'reset_timeout': getattr(settings, 'API_CLIENT_RESET_TIMEOUT', 60.0),
                'half_open_success_threshold': getattr(settings, 'API_CLIENT_HALF_OPEN_SUCCESS_THRESHOLD', 3),
            }
        })
        
        logger.info("Conteneur d'injection de dépendances pour les clients API initialisé")
    
    return _container

def resolve(cls, *args, **kwargs):
    """
    Résout une classe en utilisant le conteneur d'injection de dépendances.
    
    Args:
        cls: Classe à résoudre
        *args, **kwargs: Arguments à passer au constructeur
        
    Returns:
        Instance de la classe résolue
    """
    container = get_container()
    
    # Mapper les types abstraits aux fournisseurs concrets
    if hasattr(container, cls.__name__):
        provider = getattr(container, cls.__name__)
        return provider(*args, **kwargs)
    
    # Pour les interfaces connues
    if cls == CircuitBreakerInterface:
        return container.circuit_breaker_factory(*args, **kwargs)
    
    if cls == APIResponseHandler:
        return container.response_handler()
    
    raise ValueError(f"Type non géré: {cls.__name__}")
    
# Fonction utilitaire pour créer un circuit breaker nommé
def create_circuit_breaker(service_name: str):
    """
    Crée un circuit breaker pour un service spécifique.
    
    Args:
        service_name: Nom du service pour lequel créer un circuit breaker
        
    Returns:
        Instance de CircuitBreaker configurée
    """
    container = get_container()
    circuit_breaker = container.circuit_breaker_factory()
    circuit_breaker.service_name = service_name
    return circuit_breaker 