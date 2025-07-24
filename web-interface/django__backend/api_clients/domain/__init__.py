"""
Couche de domaine pour les clients API.

Ce package contient les interfaces et exceptions spécifiques au domaine des clients API.
"""

from .interfaces import (
    APIClientInterface,
    CircuitBreakerInterface,
    APIResponseHandler
)

from .exceptions import (
    APIClientException,
    APIConnectionException,
    APIRequestException,
    APIResponseException,
    APITimeoutException,
    AuthenticationException,
    APIClientDataException, 
    CircuitBreakerOpenException,
    RetryExhaustedException,
    ValidationException,
    CacheException,
    ConfigurationException
)

__all__ = [
    'APIClientInterface',
    'CircuitBreakerInterface',
    'APIResponseHandler',
    'APIClientException',
    'APIConnectionException',
    'APIRequestException',
    'APIResponseException',
    'APITimeoutException',
    'AuthenticationException',
    'APIClientDataException',
    'CircuitBreakerOpenException',
    'RetryExhaustedException',
    'ValidationException',
    'CacheException',
    'ConfigurationException'
] 