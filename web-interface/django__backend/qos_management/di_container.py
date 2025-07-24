"""
Conteneur d'injection de dépendances pour le module QoS Management.

Ce module configure les repositories, services et cas d'utilisation du module QoS Management
dans le conteneur d'injection de dépendances.
"""

import logging
from dependency_injector import containers, providers

from .domain.interfaces import (
    TrafficClassRepository,
    TrafficClassifierRepository,
    InterfaceQoSPolicyRepository,
    TrafficControlService,
    QoSConfigurationService,
    QoSMonitoringService,
    TrafficClassificationService
)
from .domain.repository_interfaces import (
    QoSPolicyReader,
    QoSPolicyWriter,
    QoSPolicyQueryService,
    QoSPolicyRepository
)
from .infrastructure.repositories import (
    DjangoTrafficClassRepository,
    DjangoTrafficClassifierRepository,
    DjangoInterfaceQoSPolicyRepository
)
from .infrastructure.qos_policy_repository import (
    DjangoQoSPolicyReader,
    DjangoQoSPolicyWriter,
    DjangoQoSPolicyQueryService,
    DjangoQoSPolicyRepository
)
from .infrastructure.traffic_control_adapter import TrafficControlAdapter
from .infrastructure.qos_configuration_adapter import NetworkDeviceQoSAdapter
from .infrastructure.monitoring_adapters import (
    PrometheusQoSMonitoringAdapter, 
    NetflowQoSMonitoringAdapter, 
    CompositeQoSMonitoringAdapter
)
from .infrastructure.traffic_classification_adapter import TrafficClassificationAdapter as MLTrafficClassificationAdapter

# Import des use cases
from .application.qos_policy_use_cases import (
    GetQoSPolicyUseCase,
    ListQoSPoliciesUseCase,
    CreateQoSPolicyUseCase,
    UpdateQoSPolicyUseCase,
    DeleteQoSPolicyUseCase
)
from .application.use_cases import (
    GetTrafficClassUseCase,
    ListTrafficClassesUseCase,
    CreateTrafficClassUseCase,
    ApplyPolicyToInterfaceUseCase,
    RemovePolicyFromInterfaceUseCase,
    GetQoSStatisticsUseCase,
    ListTrafficClassifiersUseCase,
    CreateTrafficClassifierUseCase,
    GetQoSRecommendationsUseCase,
    GetQoSVisualizationUseCase
)
from .application.validate_and_apply_qos_config_use_case import (
    ValidateAndApplyQoSConfigUseCase
)
from .application.configure_cbwfq_use_case import (
    ConfigureCBWFQUseCase,
    CalculateBandwidthAllocationUseCase
)
from .application.configure_llq_use_case import (
    ConfigureLLQUseCase
)
from .application.sla_compliance_use_cases import (
    GetSLAComplianceReportUseCase,
    GetQoSPerformanceReportUseCase,
    AnalyzeSLATrendsUseCase
)

logger = logging.getLogger(__name__)


class QoSManagementContainer(containers.DeclarativeContainer):
    """
    Conteneur d'injection de dépendances pour le module QoS Management.
    
    Ce conteneur définit les dépendances entre les différentes couches
    du module QoS Management et permet d'injecter ces dépendances.
    """
    
    # Configuration
    config = providers.Configuration()
    
    # Repositories spécialisés pour les politiques QoS
    qos_policy_reader = providers.Singleton(DjangoQoSPolicyReader)
    qos_policy_writer = providers.Singleton(DjangoQoSPolicyWriter)
    qos_policy_query_service = providers.Singleton(DjangoQoSPolicyQueryService)
    
    # Repository composite pour la compatibilité
    qos_policy_repository = providers.Singleton(DjangoQoSPolicyRepository)
    
    # Autres repositories
    traffic_class_repository = providers.Singleton(DjangoTrafficClassRepository)
    traffic_classifier_repository = providers.Singleton(DjangoTrafficClassifierRepository)
    interface_qos_repository = providers.Singleton(DjangoInterfaceQoSPolicyRepository)
    
    # Services d'infrastructure
    traffic_control_service = providers.Singleton(TrafficControlAdapter)
    qos_configuration_service = providers.Singleton(NetworkDeviceQoSAdapter)
    
    # Services de monitoring QoS
    prometheus_qos_monitoring = providers.Singleton(
        PrometheusQoSMonitoringAdapter,
        prometheus_url=config.prometheus.url
    )
    
    netflow_qos_monitoring = providers.Singleton(
        NetflowQoSMonitoringAdapter,
        netflow_url=config.netflow.collector_url,
        prometheus_adapter=prometheus_qos_monitoring
    )
    
    qos_monitoring_service = providers.Singleton(
        CompositeQoSMonitoringAdapter,
        prometheus_adapter=prometheus_qos_monitoring,
        netflow_adapter=netflow_qos_monitoring
    )
    
    traffic_classification_service = providers.Singleton(MLTrafficClassificationAdapter)
    
    # Cas d'utilisation pour les politiques QoS
    get_qos_policy_use_case = providers.Factory(
        GetQoSPolicyUseCase,
        policy_reader=qos_policy_reader
    )
    list_qos_policies_use_case = providers.Factory(
        ListQoSPoliciesUseCase,
        policy_reader=qos_policy_reader,
        policy_query_service=qos_policy_query_service
    )
    create_qos_policy_use_case = providers.Factory(
        CreateQoSPolicyUseCase,
        policy_writer=qos_policy_writer
    )
    update_qos_policy_use_case = providers.Factory(
        UpdateQoSPolicyUseCase,
        policy_reader=qos_policy_reader,
        policy_writer=qos_policy_writer
    )
    delete_qos_policy_use_case = providers.Factory(
        DeleteQoSPolicyUseCase,
        policy_reader=qos_policy_reader,
        policy_writer=qos_policy_writer,
        policy_query_service=qos_policy_query_service
    )
    
    # Cas d'utilisation pour les classes de trafic
    get_traffic_class_use_case = providers.Factory(
        GetTrafficClassUseCase,
        traffic_class_repository=traffic_class_repository
    )
    list_traffic_classes_use_case = providers.Factory(
        ListTrafficClassesUseCase,
        traffic_class_repository=traffic_class_repository
    )
    create_traffic_class_use_case = providers.Factory(
        CreateTrafficClassUseCase,
        traffic_class_repository=traffic_class_repository,
        qos_policy_repository=qos_policy_repository
    )
    
    # Cas d'utilisation pour les classificateurs de trafic
    list_traffic_classifiers_use_case = providers.Factory(
        ListTrafficClassifiersUseCase,
        traffic_classifier_repository=traffic_classifier_repository,
        traffic_class_repository=traffic_class_repository
    )
    create_traffic_classifier_use_case = providers.Factory(
        CreateTrafficClassifierUseCase,
        traffic_classifier_repository=traffic_classifier_repository,
        traffic_class_repository=traffic_class_repository
    )
    
    # Cas d'utilisation pour l'application QoS
    apply_policy_to_interface_use_case = providers.Factory(
        ApplyPolicyToInterfaceUseCase,
        interface_qos_repository=interface_qos_repository,
        qos_policy_repository=qos_policy_repository,
        traffic_control_service=traffic_control_service
    )
    remove_policy_from_interface_use_case = providers.Factory(
        RemovePolicyFromInterfaceUseCase,
        interface_qos_repository=interface_qos_repository
    )
    get_qos_statistics_use_case = providers.Factory(
        GetQoSStatisticsUseCase,
        interface_qos_repository=interface_qos_repository,
        traffic_control_service=traffic_control_service
    )
    validate_and_apply_qos_config_use_case = providers.Factory(
        ValidateAndApplyQoSConfigUseCase,
        qos_policy_repository=qos_policy_repository,
        traffic_control_service=traffic_control_service
    )
    
    # Cas d'utilisation CBWFQ
    configure_cbwfq_use_case = providers.Factory(
        ConfigureCBWFQUseCase,
        policy_repository=qos_policy_repository,
        device_repository=providers.Object(None),  # Repository temporaire
        qos_configuration_service=qos_configuration_service
    )
    
    # Cas d'utilisation LLQ
    configure_llq_use_case = providers.Factory(
        ConfigureLLQUseCase,
        qos_policy_repository=qos_policy_repository,
        traffic_class_repository=traffic_class_repository,
        traffic_control_service=traffic_control_service
    )
    
    # Cas d'utilisation SLA et Rapports QoS
    get_sla_compliance_report_use_case = providers.Factory(
        GetSLAComplianceReportUseCase,
        qos_monitoring_service=qos_monitoring_service
    )
    
    get_qos_performance_report_use_case = providers.Factory(
        GetQoSPerformanceReportUseCase,
        qos_monitoring_service=qos_monitoring_service
    )
    
    analyze_sla_trends_use_case = providers.Factory(
        AnalyzeSLATrendsUseCase,
        qos_monitoring_service=qos_monitoring_service
    )
    
    # Cas d'utilisation pour les recommandations et visualisation QoS
    get_qos_recommendations_use_case = providers.Factory(
        GetQoSRecommendationsUseCase,
        qos_policy_repository=qos_policy_repository
    )
    
    get_qos_visualization_use_case = providers.Factory(
        GetQoSVisualizationUseCase,
        qos_policy_repository=qos_policy_repository
    )
    
    calculate_bandwidth_allocation_use_case = providers.Factory(
        CalculateBandwidthAllocationUseCase,
        policy_repository=qos_policy_repository
    )


# Instance globale du conteneur
qos_container = QoSManagementContainer()


def init_di_container():
    """
    Initialise le conteneur d'injection de dépendances.
    
    Cette fonction initialise le conteneur avec les configurations par défaut
    et renvoie une instance du conteneur prête à être utilisée.
    
    Returns:
        Instance du conteneur QoSManagementContainer
    """
    # Configuration par défaut
    qos_container.config.prometheus.url.from_env('PROMETHEUS_URL', 'http://localhost:9090')
    qos_container.config.netflow.collector_url.from_env('NETFLOW_URL', 'http://localhost:8080')
    
    logger.info("Conteneur d'injection de dépendances QoS Management initialisé")
    return qos_container


def configure(config_dict):
    """
    Configure le conteneur avec les paramètres spécifiés.
    
    Args:
        config_dict: Dictionnaire de configuration
    """
    qos_container.config.from_dict(config_dict)
    logger.info("Conteneur d'injection de dépendances QoS Management configuré")


def resolve(dependency_type):
    """
    Résout une dépendance via le conteneur.
    
    Args:
        dependency_type: Type ou nom de la dépendance à résoudre
        
    Returns:
        Instance de la dépendance
    """
    try:
        # Si c'est une classe (type), chercher dans le mapping
        if hasattr(dependency_type, '__name__'):
            dependency_name = dependency_type.__name__
            
            # Mapping des classes vers les providers du conteneur
            class_mapping = {
                'GetQoSPolicyUseCase': 'get_qos_policy_use_case',
                'ListQoSPoliciesUseCase': 'list_qos_policies_use_case',
                'CreateQoSPolicyUseCase': 'create_qos_policy_use_case',
                'UpdateQoSPolicyUseCase': 'update_qos_policy_use_case',
                'DeleteQoSPolicyUseCase': 'delete_qos_policy_use_case',
                'GetTrafficClassUseCase': 'get_traffic_class_use_case',
                'ListTrafficClassesUseCase': 'list_traffic_classes_use_case',
                'CreateTrafficClassUseCase': 'create_traffic_class_use_case',
                'ListTrafficClassifiersUseCase': 'list_traffic_classifiers_use_case',
                'CreateTrafficClassifierUseCase': 'create_traffic_classifier_use_case',
                'ApplyPolicyToInterfaceUseCase': 'apply_policy_to_interface_use_case',
                'RemovePolicyFromInterfaceUseCase': 'remove_policy_from_interface_use_case',
                'GetQoSStatisticsUseCase': 'get_qos_statistics_use_case',
                'ValidateAndApplyQoSConfigUseCase': 'validate_and_apply_qos_config_use_case',
                'ConfigureCBWFQUseCase': 'configure_cbwfq_use_case',
                'ConfigureLLQUseCase': 'configure_llq_use_case',
                'GetSLAComplianceReportUseCase': 'get_sla_compliance_report_use_case',
                'GetQoSPerformanceReportUseCase': 'get_qos_performance_report_use_case',
                'AnalyzeSLATrendsUseCase': 'analyze_sla_trends_use_case',
                'GetQoSRecommendationsUseCase': 'get_qos_recommendations_use_case',
                'GetQoSVisualizationUseCase': 'get_qos_visualization_use_case',
                'CalculateBandwidthAllocationUseCase': 'calculate_bandwidth_allocation_use_case',
            }
            
            if dependency_name in class_mapping:
                provider_name = class_mapping[dependency_name]
                return getattr(qos_container, provider_name)()
        
        # Si c'est une chaîne, utiliser directement comme nom de provider
        if isinstance(dependency_type, str) and hasattr(qos_container, dependency_type):
            return getattr(qos_container, dependency_type)()
        
        # Fallback: créer une instance directement
        logger.warning(f"Dépendance non trouvée dans le conteneur: {dependency_type}. Création d'instance directe.")
        return dependency_type()
        
    except Exception as e:
        logger.error(f"Erreur lors de la résolution de dépendance {dependency_type}: {e}")
        # Fallback: créer une instance directement
        return dependency_type()