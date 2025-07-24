"""
Module d'application pour la gestion de la QoS.

Ce module contient les cas d'utilisation de l'application QoS Management.
"""

# Imports pour les tests unitaires uniquement
# Les imports complets seront activés lorsque les modules externes seront disponibles
__all__ = [
    'QoSComplianceTestingUseCase',
    'QoSTestScenario',
    'TrafficProfile',
    'ExpectedMetrics',
    'QoSTestResult',
]

# Import des cas d'utilisation pour les tests
from .qos_compliance_testing_use_cases import (
    QoSComplianceTestingUseCase,
    QoSTestScenario,
    TrafficProfile,
    ExpectedMetrics,
    QoSTestResult,
)

# Ces imports seront activés lorsque les modules externes seront disponibles
"""
from .qos_policy_use_cases import ApplyQoSPolicyUseCase
from .qos_monitoring_use_cases import (
    MonitorQoSMetricsUseCase,
    AnalyzeQoSPerformanceUseCase,
    GenerateQoSReportUseCase
)
from .qos_configuration_use_cases import (
    ConfigureQoSInterfaceUseCase,
    GenerateQoSConfigurationUseCase,
    ValidateQoSConfigurationUseCase
)
from .qos_visualization_use_cases import (
    VisualizeQoSPolicyUseCase,
    VisualizeQoSPerformanceUseCase
)
"""

from .use_cases import (
    GetQoSPolicyUseCase,
    ListQoSPoliciesUseCase,
    CreateQoSPolicyUseCase,
    UpdateQoSPolicyUseCase,
    DeleteQoSPolicyUseCase,
    GetTrafficClassUseCase,
    ListTrafficClassesUseCase,
    CreateTrafficClassUseCase,
    ApplyPolicyToInterfaceUseCase,
    RemovePolicyFromInterfaceUseCase,
    GetQoSStatisticsUseCase,
    ListTrafficClassifiersUseCase,
    CreateTrafficClassifierUseCase
)
from .validate_and_apply_qos_config_use_case import ValidateAndApplyQoSConfigUseCase

__all__ = [
    # Cas d'utilisation pour les politiques QoS
    'GetQoSPolicyUseCase',
    'ListQoSPoliciesUseCase',
    'CreateQoSPolicyUseCase',
    'UpdateQoSPolicyUseCase',
    'DeleteQoSPolicyUseCase',
    
    # Cas d'utilisation pour les classes de trafic
    'GetTrafficClassUseCase',
    'ListTrafficClassesUseCase',
    'CreateTrafficClassUseCase',
    
    # Cas d'utilisation pour l'application QoS
    'ApplyPolicyToInterfaceUseCase',
    'RemovePolicyFromInterfaceUseCase',
    'ApplyQoSPolicyUseCase',
    'GetQoSStatisticsUseCase',
    'ValidateAndApplyQoSConfigUseCase',
    
    # Cas d'utilisation pour les classificateurs de trafic
    'ListTrafficClassifiersUseCase',
    'CreateTrafficClassifierUseCase'
] 