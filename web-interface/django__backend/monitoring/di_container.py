"""
Container d'injection de dépendances pour le module monitoring.
Ce fichier permet de résoudre les dépendances des objets utilisés dans l'application
en utilisant le principe d'inversion de dépendance.
"""

from dependency_injector import containers, providers
import logging

# Import des repositories (implémentations réelles)
from .infrastructure.repositories import (
    AlertRepository,
    MetricsDefinitionRepository, 
    DeviceMetricRepository,
    MetricValueRepository,
    ServiceCheckRepository,
    DeviceServiceCheckRepository,
    CheckResultRepository,
    DashboardRepository,
    NotificationRepository,
    NotificationChannelRepository,
    NotificationRuleRepository
)

# Adaptateurs pour les services externes
from .infrastructure.adapters import (
    PrometheusAdapter,
    GrafanaAdapter,
    ElasticsearchAdapter,
    SNMPAdapter
)

# Service d'intégration externe
from .infrastructure.services.external_integration_service import ExternalIntegrationService

from .domain.interfaces.repositories import (
    AlertRepository as IAlertRepository,
    MetricsDefinitionRepository as IMetricsDefinitionRepository,
    DeviceMetricRepository as IDeviceMetricRepository,
    MetricValueRepository as IMetricValueRepository,
    ServiceCheckRepository as IServiceCheckRepository,
    DeviceServiceCheckRepository as IDeviceServiceCheckRepository,
    CheckResultRepository as ICheckResultRepository,
    DashboardRepository as IDashboardRepository,
    NotificationRepository as INotificationRepository
)

from .domain.services import (
    MetricCollectionService,
    AlertingService,
    ServiceCheckService,
    DashboardService,
    NotificationService,
    AnomalyDetectionService
)

from .application import (
    # Use cases pour les métriques
    CollectMetricsUseCase,
    CollectMetricUseCase,
    CreateMetricDefinitionUseCase,
    UpdateMetricUseCase,
    DeleteMetricUseCase,
    
    # Use cases pour les alertes
    CreateAlertUseCase,
    UpdateAlertUseCase,
    ResolveAlertUseCase,
    AcknowledgeAlertUseCase,
    
    # Use cases pour les vérifications de service
    CheckServicesUseCase,
    CheckServiceUseCase,
    CreateServiceCheckUseCase,
    UpdateServiceCheckUseCase,
    DeleteServiceCheckUseCase,
    
    # Use cases pour les tableaux de bord
    CreateDashboardUseCase,
    UpdateDashboardUseCase,
    DeleteDashboardUseCase,
    
    # Use cases pour les notifications
    SendNotificationUseCase,
    NotificationDeliveryUseCase,
    
    # Use cases pour les modèles de surveillance
    ApplyMonitoringTemplateUseCase,
    
    # Use cases pour l'analyse avancée
    DetectAnomaliesUseCase,
    PredictMetricTrendUseCase
)

# Configuration du logger
logger = logging.getLogger(__name__)


class DIContainer(containers.DeclarativeContainer):
    """
    Container d'injection de dépendances.
    """
    
    # Configuration
    config = providers.Configuration()
    
    # Adaptateurs pour les services externes
    prometheus_adapter = providers.Singleton(PrometheusAdapter)
    grafana_adapter = providers.Singleton(GrafanaAdapter)
    elasticsearch_adapter = providers.Singleton(ElasticsearchAdapter)
    snmp_adapter = providers.Singleton(SNMPAdapter)
    
    # Service d'intégration externe
    external_integration_service = providers.Singleton(
        ExternalIntegrationService
    )
    
    # Repositories
    alert_repository = providers.Singleton(AlertRepository)
    metrics_definition_repository = providers.Singleton(MetricsDefinitionRepository)
    device_metric_repository = providers.Singleton(DeviceMetricRepository)
    metric_value_repository = providers.Singleton(MetricValueRepository)
    service_check_repository = providers.Singleton(ServiceCheckRepository)
    device_service_check_repository = providers.Singleton(DeviceServiceCheckRepository)
    check_result_repository = providers.Singleton(CheckResultRepository)
    dashboard_repository = providers.Singleton(DashboardRepository)
    notification_repository = providers.Singleton(NotificationRepository)
    notification_channel_repository = providers.Singleton(NotificationChannelRepository)
    notification_rule_repository = providers.Singleton(NotificationRuleRepository)
    
    # Services
    metric_collection_service = providers.Factory(
        MetricCollectionService,
        device_metric_repository=device_metric_repository,
        metric_value_repository=metric_value_repository,
        external_integration_service=external_integration_service
    )
    
    alerting_service = providers.Factory(
        AlertingService,
        alert_repository=alert_repository,
        notification_service=providers.Dependency(),
        external_integration_service=external_integration_service
    )
    
    service_check_service = providers.Factory(
        ServiceCheckService,
        service_check_repository=service_check_repository,
        device_service_check_repository=device_service_check_repository,
        check_result_repository=check_result_repository,
        alerting_service=alerting_service
    )
    
    dashboard_service = providers.Factory(
        DashboardService,
        dashboard_repository=dashboard_repository,
        external_integration_service=external_integration_service
    )
    
    notification_service = providers.Factory(
        NotificationService,
        notification_repository=notification_repository
    )
    
    anomaly_detection_service = providers.Factory(
        AnomalyDetectionService,
        metric_value_repository=metric_value_repository,
        external_integration_service=external_integration_service
    )
    
    # Use cases pour les métriques
    collect_metrics_use_case = providers.Factory(
        CollectMetricsUseCase,
        metric_collection_service=metric_collection_service,
        device_metric_repository=device_metric_repository
    )
    
    collect_metric_use_case = providers.Factory(
        CollectMetricUseCase,
        metric_collection_service=metric_collection_service,
        device_metric_repository=device_metric_repository
    )
    
    create_metric_definition_use_case = providers.Factory(
        CreateMetricDefinitionUseCase,
        metrics_definition_repository=metrics_definition_repository
    )
    
    update_metric_use_case = providers.Factory(
        UpdateMetricUseCase,
        device_metric_repository=device_metric_repository
    )
    
    delete_metric_use_case = providers.Factory(
        DeleteMetricUseCase,
        device_metric_repository=device_metric_repository,
        metric_value_repository=metric_value_repository
    )
    
    # Use cases pour les alertes
    create_alert_use_case = providers.Factory(
        CreateAlertUseCase,
        alert_repository=alert_repository,
        notification_service=notification_service
    )
    
    update_alert_use_case = providers.Factory(
        UpdateAlertUseCase,
        alert_repository=alert_repository
    )
    
    resolve_alert_use_case = providers.Factory(
        ResolveAlertUseCase,
        alert_repository=alert_repository
    )
    
    acknowledge_alert_use_case = providers.Factory(
        AcknowledgeAlertUseCase,
        alert_repository=alert_repository
    )
    
    # Use cases pour les vérifications de service
    check_services_use_case = providers.Factory(
        CheckServicesUseCase,
        service_check_service=service_check_service,
        device_service_check_repository=device_service_check_repository
    )
    
    check_service_use_case = providers.Factory(
        CheckServiceUseCase,
        service_check_service=service_check_service,
        device_service_check_repository=device_service_check_repository
    )
    
    create_service_check_use_case = providers.Factory(
        CreateServiceCheckUseCase,
        service_check_repository=service_check_repository
    )
    
    update_service_check_use_case = providers.Factory(
        UpdateServiceCheckUseCase,
        service_check_repository=service_check_repository
    )
    
    delete_service_check_use_case = providers.Factory(
        DeleteServiceCheckUseCase,
        service_check_repository=service_check_repository,
        device_service_check_repository=device_service_check_repository,
        check_result_repository=check_result_repository
    )
    
    # Use cases pour les tableaux de bord
    create_dashboard_use_case = providers.Factory(
        CreateDashboardUseCase,
        dashboard_repository=dashboard_repository
    )
    
    update_dashboard_use_case = providers.Factory(
        UpdateDashboardUseCase,
        dashboard_repository=dashboard_repository
    )
    
    delete_dashboard_use_case = providers.Factory(
        DeleteDashboardUseCase,
        dashboard_repository=dashboard_repository
    )
    
    # Use cases pour les notifications
    send_notification_use_case = providers.Factory(
        SendNotificationUseCase,
        notification_service=notification_service
    )
    
    notification_delivery_use_case = providers.Factory(
        NotificationDeliveryUseCase,
        notification_service=notification_service,
        notification_repository=notification_repository
    )
    
    # Use cases pour les modèles de surveillance
    apply_monitoring_template_use_case = providers.Factory(
        ApplyMonitoringTemplateUseCase,
        service_check_repository=service_check_repository,
        device_service_check_repository=device_service_check_repository,
        metrics_definition_repository=metrics_definition_repository,
        device_metric_repository=device_metric_repository
    )
    
    # Use cases pour l'analyse avancée
    detect_anomalies_use_case = providers.Factory(
        DetectAnomaliesUseCase,
        anomaly_detection_service=anomaly_detection_service,
        metric_value_repository=metric_value_repository,
        device_metric_repository=device_metric_repository,
        alerting_service=alerting_service
    )
    
    predict_metric_trend_use_case = providers.Factory(
        PredictMetricTrendUseCase,
        anomaly_detection_service=anomaly_detection_service,
        metric_value_repository=metric_value_repository
    )


# Fonction pour résoudre une dépendance par son nom
def resolve(name):
    """
    Résout une dépendance par son nom.
    
    Args:
        name: Nom de la dépendance à résoudre
        
    Returns:
        L'instance de la dépendance résolue
    """
    global _container
    if _container is None:
        _container = initialize_container()
    
    try:
        return getattr(_container, name)
    except AttributeError:
        logger.warning(f"Dépendance '{name}' non trouvée dans le conteneur")
        # Retourner une factory lambda pour éviter les erreurs d'instanciation
        return lambda: None


# Instance du conteneur
_container = None

def initialize_container():
    """
    Initialise le conteneur d'injection de dépendances.
    
    Returns:
        L'instance du conteneur initialisé
    """
    global _container
    
    try:
        if _container is None:
            _container = DIContainer()
            
            # Configuration des dépendances circulaires
            _container.alerting_service.override(
                providers.Factory(
                    AlertingService,
                    alert_repository=_container.alert_repository,
                    notification_service=_container.notification_service
                )
            )
            
            logger.info("✅ Container d'injection de dépendances monitoring initialisé avec succès")
        
        return _container
    except Exception as e:
        logger.error(f"Erreur lors de l'initialisation du conteneur d'injection de dépendances: {str(e)}")
        logger.exception(e)
        raise 