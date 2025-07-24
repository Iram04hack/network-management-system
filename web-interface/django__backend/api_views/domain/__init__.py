"""
Package domain pour le module api_views.

Ce package contient les interfaces, entités et exceptions du domaine api_views.
"""

# Exceptions du domaine
from .exceptions import (
    APIViewsDomainException,
    ResourceNotFoundException,
    InvalidSearchQueryException,
    APIValidationException,
    APIOperationException,
    AuthorizationException,
    TopologyDiscoveryException,
    DashboardException
)

# Interfaces du domaine
from .interfaces import (
    DashboardRepository,
    TopologyDiscoveryRepository,
    APISearchRepository
)

__all__ = [
    # Exceptions
    'APIViewsDomainException',
    'ResourceNotFoundException',
    'InvalidSearchQueryException',
    'APIValidationException',
    'APIOperationException',
    'AuthorizationException',
    'TopologyDiscoveryException',
    'DashboardException',
    
    # Interfaces
    'DashboardRepository',
    'TopologyDiscoveryRepository',
    'APISearchRepository'
] 