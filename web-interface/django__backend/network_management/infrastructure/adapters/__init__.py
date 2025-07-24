"""
Module des adaptateurs d'infrastructure pour network_management.

Ce module contient les adaptateurs qui permettent à l'application
de communiquer avec les systèmes externes (base de données, SNMP, etc.).
"""

from .django_device_repository import DjangoDeviceRepository
from .django_interface_repository import DjangoInterfaceRepository
from .django_configuration_repository import DjangoConfigurationRepository
from .pysnmp_client_adapter import PySnmpClientAdapter

__all__ = [
    'DjangoDeviceRepository',
    'DjangoInterfaceRepository',
    'DjangoConfigurationRepository',
    'PySnmpClientAdapter',
] 