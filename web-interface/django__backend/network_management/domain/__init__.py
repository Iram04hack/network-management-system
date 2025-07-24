"""
Package domain pour le module network_management.

Ce package contient les interfaces et exceptions du domaine network_management.
"""

# Exceptions du domaine
from .exceptions import (
    NetworkDomainException,
    NetworkDeviceNotFoundException,
    NetworkInterfaceNotFoundException,
    NetworkConnectionNotFoundException,
    DeviceConfigurationNotFoundException,
    NetworkValidationException,
    NetworkConnectionException,
    SNMPException,
    SSHException,
    ConfigurationException,
    TopologyException,
    DiscoveryException
)

# Interfaces du domaine
from .interfaces import (
    NetworkDeviceRepository,
    NetworkInterfaceRepository,
    NetworkConnectionRepository,
    DeviceConfigurationRepository,
    EventBus
)

__all__ = [
    # Exceptions
    'NetworkDomainException',
    'NetworkDeviceNotFoundException',
    'NetworkInterfaceNotFoundException',
    'NetworkConnectionNotFoundException',
    'DeviceConfigurationNotFoundException',
    'NetworkValidationException',
    'NetworkConnectionException',
    'SNMPException',
    'SSHException',
    'ConfigurationException',
    'TopologyException',
    'DiscoveryException',
    
    # Interfaces
    'NetworkDeviceRepository',
    'NetworkInterfaceRepository',
    'NetworkConnectionRepository',
    'DeviceConfigurationRepository',
    'EventBus'
] 