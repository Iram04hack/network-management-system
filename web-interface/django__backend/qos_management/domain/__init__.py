"""
Package domain pour le module qos_management.

Ce package contient les interfaces et exceptions du domaine qos_management.
"""

# Exceptions du domaine
from .exceptions import (
    QoSDomainException,
    QoSPolicyNotFoundException,
    TrafficClassNotFoundException,
    TrafficClassifierNotFoundException,
    InterfaceQoSPolicyNotFoundException,
    QoSValidationException,
    QoSPolicyApplicationException,
    TrafficControlException,
    BandwidthLimitExceededException,
    QoSConfigurationException
)

# Interfaces du domaine
from .interfaces import (
    QoSPolicyRepository,
    TrafficClassRepository,
    TrafficClassifierRepository,
    InterfaceQoSPolicyRepository,
    TrafficControlService
)

# Entités du domaine
from .entities import (
    TrafficClassifier,
    TrafficClass,
    QoSPolicy,
    InterfaceQoSPolicy
)

# Stratégies de correspondance
from .strategies import (
    PacketMatchStrategy,
    ProtocolMatchStrategy,
    SourceIpMatchStrategy,
    DestinationIpMatchStrategy,
    SourcePortMatchStrategy,
    DestinationPortMatchStrategy,
    DscpMatchStrategy,
    VlanMatchStrategy,
    CompositeMatchStrategy,
    PacketMatchStrategyFactory
)

__all__ = [
    # Exceptions
    'QoSDomainException',
    'QoSPolicyNotFoundException',
    'TrafficClassNotFoundException',
    'TrafficClassifierNotFoundException',
    'InterfaceQoSPolicyNotFoundException',
    'QoSValidationException',
    'QoSPolicyApplicationException',
    'TrafficControlException',
    'BandwidthLimitExceededException',
    'QoSConfigurationException',
    
    # Interfaces
    'QoSPolicyRepository',
    'TrafficClassRepository',
    'TrafficClassifierRepository',
    'InterfaceQoSPolicyRepository',
    'TrafficControlService',
    
    # Entités
    'TrafficClassifier',
    'TrafficClass',
    'QoSPolicy',
    'InterfaceQoSPolicy',
    
    # Stratégies
    'PacketMatchStrategy',
    'ProtocolMatchStrategy',
    'SourceIpMatchStrategy',
    'DestinationIpMatchStrategy',
    'SourcePortMatchStrategy',
    'DestinationPortMatchStrategy',
    'DscpMatchStrategy',
    'VlanMatchStrategy',
    'CompositeMatchStrategy',
    'PacketMatchStrategyFactory'
] 