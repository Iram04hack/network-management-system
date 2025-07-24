"""
Module QoS Management - Système complet de gestion de la Qualité de Service.

Ce module fournit une solution complète pour la gestion QoS incluant :
- Gestion des politiques QoS avec architecture hexagonale
- Algorithmes QoS avancés (HTB, FQ-CoDel, DRR, etc.)
- Adaptateurs pour différents équipements réseau (Cisco, Juniper, Linux)
- Reconnaissance d'applications avec DPI
- Tests de conformité et monitoring
- Intégration SDN avec OpenFlow
"""

# Version du module
__version__ = "2.0.0"

# Configuration des composants par défaut
DEFAULT_COMPONENTS = {
    'algorithms': {
        'queue_algorithms': [
            'HTB',
            'FQ_CODEL',
            'DRR',
            'CBWFQ'
        ],
        'congestion_algorithms': [
            'RED',
            'WRED',
            'CODEL'
        ]
    },
    'adapters': {
        'supported_vendors': ['cisco', 'juniper', 'linux'],
        'supported_controllers': ['onos', 'opendaylight', 'ryu']
    }
}

# Fonctions utilitaires
def get_module_info():
    """
    Retourne les informations sur le module QoS Management.
    
    Returns:
        Dict contenant les informations du module
    """
    return {
        'name': 'QoS Management Module',
        'version': __version__,
        'description': __doc__.strip(),
        'components': DEFAULT_COMPONENTS,
        'capabilities': [
            'Policy Management',
            'Advanced Algorithms',
            'Multi-vendor Support',
            'Application Recognition',
            'Compliance Testing',
            'SDN Integration'
        ]
    }

def create_qos_system(config=None):
    """
    Crée et configure un système QoS complet.
    
    Args:
        config: Configuration optionnelle du système
        
    Returns:
        Instance configurée du système QoS
    """
    from .application.qos_system_factory import QoSSystemFactory
    
    if config is None:
        config = DEFAULT_COMPONENTS
    
    return QoSSystemFactory.create_system(config)

def get_models():
    """
    Retourne les modèles principaux du module.
    Cette fonction permet d'éviter les importations circulaires.
    
    Returns:
        Dict contenant les classes de modèles
    """
    from .models import (
        QoSPolicy,
        QoSRule,
        TrafficClass,
        BandwidthAllocation,
        QoSMetrics
    )
    
    return {
        'QoSPolicy': QoSPolicy,
        'QoSRule': QoSRule,
        'TrafficClass': TrafficClass,
        'BandwidthAllocation': BandwidthAllocation,
        'QoSMetrics': QoSMetrics
    }

def get_domain_entities():
    """
    Retourne les entités de domaine.
    Cette fonction permet d'éviter les importations circulaires.
    
    Returns:
        Dict contenant les classes d'entités
    """
    from .domain.entities import (
        QoSPolicyEntity,
        QoSRuleEntity,
        TrafficClassEntity
    )
    
    return {
        'QoSPolicyEntity': QoSPolicyEntity,
        'QoSRuleEntity': QoSRuleEntity,
        'TrafficClassEntity': TrafficClassEntity
    }

def get_algorithms():
    """
    Retourne les algorithmes disponibles.
    Cette fonction permet d'éviter les importations circulaires.
    
    Returns:
        Dict contenant les classes d'algorithmes
    """
    from .domain.algorithms import (
        QueueAlgorithmType,
        CongestionAlgorithmType,
        HTBAlgorithm,
        FQCoDelAlgorithm,
        DeficitRoundRobinAlgorithm,
        QueueAlgorithmFactory,
        CongestionAlgorithmFactory
    )
    
    return {
        'QueueAlgorithmType': QueueAlgorithmType,
        'CongestionAlgorithmType': CongestionAlgorithmType,
        'HTBAlgorithm': HTBAlgorithm,
        'FQCoDelAlgorithm': FQCoDelAlgorithm,
        'DeficitRoundRobinAlgorithm': DeficitRoundRobinAlgorithm,
        'QueueAlgorithmFactory': QueueAlgorithmFactory,
        'CongestionAlgorithmFactory': CongestionAlgorithmFactory
    }

def get_use_cases():
    """
    Retourne les cas d'utilisation disponibles.
    Cette fonction permet d'éviter les importations circulaires.
    
    Returns:
        Dict contenant les classes de cas d'utilisation
    """
    from .application.use_cases import (
        QoSPolicyCreationUseCase,
        QoSPolicyApplicationUseCase,
        QoSMonitoringUseCase,
        QoSValidationUseCase
    )
    
    from .application.qos_compliance_testing_use_cases import (
        QoSComplianceTestingUseCase,
        QoSTestScenario,
        QoSTestResult,
        TrafficProfile
    )
    
    return {
        'QoSPolicyCreationUseCase': QoSPolicyCreationUseCase,
        'QoSPolicyApplicationUseCase': QoSPolicyApplicationUseCase,
        'QoSMonitoringUseCase': QoSMonitoringUseCase,
        'QoSValidationUseCase': QoSValidationUseCase,
        'QoSComplianceTestingUseCase': QoSComplianceTestingUseCase,
        'QoSTestScenario': QoSTestScenario,
        'QoSTestResult': QoSTestResult,
        'TrafficProfile': TrafficProfile
    }

def get_infrastructure_components():
    """
    Retourne les composants d'infrastructure disponibles.
    Cette fonction permet d'éviter les importations circulaires.
    
    Returns:
        Dict contenant les classes d'infrastructure
    """
    from .infrastructure.adapters import (
        NetworkDeviceAdapterFactory,
        CiscoQoSAdapter,
        LinuxTCAdapter,
        JuniperQoSAdapter
    )
    
    from .infrastructure.application_recognition_service import (
        ApplicationRecognitionService,
        ApplicationSignature,
        TrafficFlow
    )
    
    from .infrastructure.sdn_integration_service import (
        SDNIntegrationService,
        SDNControllerType,
        OpenFlowRule,
        SDNQoSPolicy
    )
    
    return {
        'NetworkDeviceAdapterFactory': NetworkDeviceAdapterFactory,
        'CiscoQoSAdapter': CiscoQoSAdapter,
        'LinuxTCAdapter': LinuxTCAdapter,
        'JuniperQoSAdapter': JuniperQoSAdapter,
        'ApplicationRecognitionService': ApplicationRecognitionService,
        'ApplicationSignature': ApplicationSignature,
        'TrafficFlow': TrafficFlow,
        'SDNIntegrationService': SDNIntegrationService,
        'SDNControllerType': SDNControllerType,
        'OpenFlowRule': OpenFlowRule,
        'SDNQoSPolicy': SDNQoSPolicy
    }

# Exports principaux
__all__ = [
    # Version
    '__version__',
    
    # Fonctions utilitaires
    'get_module_info',
    'create_qos_system',
    'get_models',
    'get_domain_entities',
    'get_algorithms',
    'get_use_cases',
    'get_infrastructure_components',
    
    # Configuration
    'DEFAULT_COMPONENTS',
]

# Configuration par défaut de l'application Django
default_app_config = 'qos_management.apps.QoSManagementConfig' 