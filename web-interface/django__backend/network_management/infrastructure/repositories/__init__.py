"""
Package repositories pour le module Network Management.

Ce package contient les classes de repository qui permettent
d'accéder aux données persistées dans la base de données.
"""

from .device_repository import DeviceRepository as DjangoNetworkDeviceRepository
from .interface_repository import InterfaceRepository as DjangoNetworkInterfaceRepository
from .connection_repository import ConnectionRepository
from .configuration_repository import ConfigurationRepository
from .template_repository import TemplateRepository
from .compliance_repository import ComplianceRepository
from .alert_repository import AlertRepository
from .metric_repository import MetricRepository
from .log_repository import LogRepository
from .topology_repository import TopologyRepository

__all__ = [
    'DjangoNetworkDeviceRepository',
    'DjangoNetworkInterfaceRepository',
    'ConnectionRepository',
    'ConfigurationRepository',
    'TemplateRepository',
    'ComplianceRepository',
    'AlertRepository',
    'MetricRepository',
    'LogRepository',
    'TopologyRepository',
] 