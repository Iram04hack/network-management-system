"""
Conteneur d'injection de dépendances pour le module Reporting.

Ce module configure le conteneur d'injection de dépendances pour fournir
les implémentations concrètes des interfaces du domaine et les cas d'utilisation.
"""

from dependency_injector import containers, providers
import logging

from .domain.interfaces import (
    ReportRepository,
    ReportTemplateRepository,
    ScheduledReportRepository,
    ReportGenerationService,
    ScheduledReportService
)
from .domain.strategies import ReportDistributionStrategy

# Repositories
from .infrastructure.repositories import (
    DjangoReportRepository,
    DjangoReportTemplateRepository,
    DjangoScheduledReportRepository
)

# Services
from .infrastructure.services import (
    DjangoReportGenerator,
    DjangoNotificationService,
    ReportFormatterService,
    ReportStorageService
)

# Service de stockage avancé
from .infrastructure.advanced_services import (
    ReportStorageServiceImpl,
    VisualizationServiceImpl,
    AnalyticsServiceImpl,
    DataIntegrationServiceImpl,
    CacheServiceImpl
)

# Stratégies de distribution
from .infrastructure.distribution_strategies import (
    EmailDistributionStrategy,
    SlackDistributionStrategy,
    WebhookDistributionStrategy
)

# Cas d'utilisation
from .application.use_cases import (
    GenerateReportUseCase,
    GetReportUseCase,
    ListReportsUseCase,
    ScheduleReportUseCase,
    DeleteReportUseCase
)

# Cas d'utilisation de distribution
from .application.report_distribution_use_cases import (
    DistributeReportUseCase,
    ScheduleReportDistributionUseCase,
    CancelReportDistributionUseCase,
    ManageDistributionRecipientsUseCase
)

# Cas d'utilisation avancés
from .application.advanced_use_cases import (
    CreateVisualizationUseCase,
    CreateDashboardUseCase,
    AnalyzeDataUseCase,
    IntegrateDataUseCase,
    GenerateInsightsUseCase,
    OptimizeReportPerformanceUseCase
)

logger = logging.getLogger(__name__)

class ReportingContainer(containers.DeclarativeContainer):
    """Conteneur d'injection de dépendances pour le module reporting."""
    
    config = providers.Configuration()
    
    # Configuration des services externes
    email_config = providers.Dict({
        'from_email': config.email.from_email.as_str(),
        'reply_to': config.email.reply_to.as_str(),
    })
    
    slack_config = providers.Dict({
        'default_webhook_url': config.slack.webhook_url.as_str(),
    })
    
    # Repositories
    report_repository = providers.Singleton(
        DjangoReportRepository
    )
    
    report_template_repository = providers.Singleton(
        DjangoReportTemplateRepository
    )
    
    scheduled_report_repository = providers.Singleton(
        DjangoScheduledReportRepository
    )
    
    # Services de base
    report_storage_service = providers.Singleton(
        ReportStorageService
    )
    
    report_formatter_service = providers.Singleton(
        ReportFormatterService
    )
    
    report_generation_service = providers.Singleton(
        DjangoReportGenerator
    )
    
    notification_service = providers.Singleton(
        DjangoNotificationService
    )
    
    # Services avancés
    visualization_service = providers.Singleton(
        VisualizationServiceImpl
    )
    
    analytics_service = providers.Singleton(
        AnalyticsServiceImpl
    )
    
    data_integration_service = providers.Singleton(
        DataIntegrationServiceImpl
    )
    
    cache_service = providers.Singleton(
        CacheServiceImpl,
        cache_prefix=config.cache.prefix.as_str()
    )
    
    # Stratégies de distribution
    email_distribution_strategy = providers.Singleton(
        EmailDistributionStrategy
    )
    
    slack_distribution_strategy = providers.Singleton(
        SlackDistributionStrategy,
        webhook_url=slack_config.provided['default_webhook_url']
    )
    
    webhook_distribution_strategy = providers.Singleton(
        WebhookDistributionStrategy
    )
    
    # Dictionnaire des stratégies de distribution
    distribution_strategies = providers.Dict({
        'email': email_distribution_strategy,
        'slack': slack_distribution_strategy,
        'webhook': webhook_distribution_strategy
    })
    
    # Cas d'utilisation de base
    generate_report_use_case = providers.Factory(
        GenerateReportUseCase,
        report_repository=report_repository,
        report_generator=report_generation_service,
        report_storage=report_storage_service
    )
    
    get_report_use_case = providers.Factory(
        GetReportUseCase,
        report_repository=report_repository
    )
    
    list_reports_use_case = providers.Factory(
        ListReportsUseCase,
        report_repository=report_repository
    )
    
    schedule_report_use_case = providers.Factory(
        ScheduleReportUseCase,
        report_repository=report_repository
    )
    
    delete_report_use_case = providers.Factory(
        DeleteReportUseCase,
        report_repository=report_repository
    )
    
    # Cas d'utilisation pour la distribution
    distribute_report_use_case = providers.Factory(
        DistributeReportUseCase,
        report_repository=report_repository,
        distribution_strategies=distribution_strategies
    )
    
    schedule_report_distribution_use_case = providers.Factory(
        ScheduleReportDistributionUseCase,
        report_repository=report_repository,
        scheduled_report_repository=scheduled_report_repository
    )
    
    cancel_report_distribution_use_case = providers.Factory(
        CancelReportDistributionUseCase,
        scheduled_report_repository=scheduled_report_repository
    )
    
    manage_distribution_recipients_use_case = providers.Factory(
        ManageDistributionRecipientsUseCase,
        scheduled_report_repository=scheduled_report_repository
    )
    
    # Nouveaux cas d'utilisation avancés
    create_visualization_use_case = providers.Factory(
        CreateVisualizationUseCase,
        report_repository=report_repository,
        visualization_service=visualization_service,
        cache_service=cache_service
    )
    
    create_dashboard_use_case = providers.Factory(
        CreateDashboardUseCase,
        report_repository=report_repository,
        visualization_service=visualization_service,
        cache_service=cache_service
    )
    
    analyze_data_use_case = providers.Factory(
        AnalyzeDataUseCase,
        analytics_service=analytics_service,
        cache_service=cache_service
    )
    
    integrate_data_use_case = providers.Factory(
        IntegrateDataUseCase,
        data_integration_service=data_integration_service,
        cache_service=cache_service
    )
    
    generate_insights_use_case = providers.Factory(
        GenerateInsightsUseCase,
        report_repository=report_repository,
        analytics_service=analytics_service,
        cache_service=cache_service
    )
    
    optimize_performance_use_case = providers.Factory(
        OptimizeReportPerformanceUseCase,
        report_repository=report_repository,
        cache_service=cache_service
    )

    @classmethod
    def get_container(cls):
        """
        Obtient une instance configurée du conteneur.
    
    Returns:
            ReportingContainer: Instance configurée du conteneur
    """
        container = cls()
        
        # Configurer le conteneur avec les valeurs par défaut
        container.config.from_dict({
            'email': {
                'from_email': 'noreply@example.com',
                'reply_to': 'support@example.com',
            },
            'slack': {
                'webhook_url': 'https://hooks.slack.com/services/default',
            },
            'cache': {
                'prefix': 'reporting:',
            }
        })
        
        # Initialiser le conteneur
        container.init_resources()
        
        return container
    
    @classmethod
    def resolve(cls, interface_cls):
        """
        Résout une interface vers son implémentation concrète.
    
        Args:
            interface_cls: La classe d'interface à résoudre
            
        Returns:
            L'implémentation concrète de l'interface
        """
        container = cls.get_container()
        
        if interface_cls == ReportRepository:
            return container.report_repository()
        elif interface_cls == ReportTemplateRepository:
            return container.report_template_repository()
        elif interface_cls == ScheduledReportRepository:
            return container.scheduled_report_repository()
        elif interface_cls == ReportGenerationService:
            return container.report_generation_service()
        elif interface_cls == GetReportUseCase:
            return container.get_report_use_case()
        elif interface_cls == ListReportsUseCase:
            return container.list_reports_use_case()
        elif interface_cls == GenerateReportUseCase:
            return container.generate_report_use_case()
        elif interface_cls == ScheduleReportUseCase:
            return container.schedule_report_use_case()
        elif interface_cls == DeleteReportUseCase:
            return container.delete_report_use_case()
        elif interface_cls == DistributeReportUseCase:
            return container.distribute_report_use_case()
        elif interface_cls == ScheduleReportDistributionUseCase:
            return container.schedule_report_distribution_use_case()
        elif interface_cls == CancelReportDistributionUseCase:
            return container.cancel_report_distribution_use_case()
        elif interface_cls == ManageDistributionRecipientsUseCase:
            return container.manage_distribution_recipients_use_case()
        elif interface_cls == CreateVisualizationUseCase:
            return container.create_visualization_use_case()
        elif interface_cls == CreateDashboardUseCase:
            return container.create_dashboard_use_case()
        elif interface_cls == AnalyzeDataUseCase:
            return container.analyze_data_use_case()
        elif interface_cls == IntegrateDataUseCase:
            return container.integrate_data_use_case()
        elif interface_cls == GenerateInsightsUseCase:
            return container.generate_insights_use_case()
        elif interface_cls == OptimizeReportPerformanceUseCase:
            return container.optimize_report_performance_use_case()
        else:
            raise ValueError(f"Interface non reconnue: {interface_cls}")


# Classe DIContainer pour les tests d'intégration
class DIContainer:
    """
    Conteneur d'injection de dépendances pour les tests d'intégration.
    Cette classe sert d'adaptateur pour les tests d'intégration existants.
    """
    
    def __init__(self):
        """Initialise le conteneur."""
        self.container = ReportingContainer.get_container()
        
        # Initialiser les repositories
        self.report_repository = self.container.report_repository()
        self.template_repository = self.container.report_template_repository()
        self.scheduled_repository = self.container.scheduled_report_repository()
        
        # Initialiser les services
        self.report_generator = self.container.report_generation_service()
        self.notification_service = self.container.notification_service()
        self.formatter_service = self.container.report_formatter_service()
        self.storage_service = self.container.report_storage_service()
        
        # Initialiser les cas d'utilisation
        self.generate_report_use_case = self.container.generate_report_use_case()
        self.get_report_use_case = self.container.get_report_use_case()
        self.list_reports_use_case = self.container.list_reports_use_case()
        self.schedule_report_use_case = self.container.schedule_report_use_case()
        self.delete_report_use_case = self.container.delete_report_use_case()
        
        # Cas d'utilisation de distribution
        self.distribute_report_use_case = self.container.distribute_report_use_case()
        self.schedule_report_distribution_use_case = self.container.schedule_report_distribution_use_case()
        self.cancel_report_distribution_use_case = self.container.cancel_report_distribution_use_case()
        self.manage_distribution_recipients_use_case = self.container.manage_distribution_recipients_use_case()
    
    def get_report_use_cases(self):
        """
        Retourne un objet avec les cas d'utilisation des rapports.
        
        Returns:
            Un objet avec les cas d'utilisation des rapports
        """
        return self
    
    def get_report_template_use_cases(self):
        """
        Retourne un objet avec les cas d'utilisation des templates de rapport.
        
        Returns:
            Un objet avec les cas d'utilisation des templates de rapport
        """
        return self
    
    def get_scheduled_report_use_cases(self):
        """
        Retourne un objet avec les cas d'utilisation des rapports planifiés.
        
        Returns:
            Un objet avec les cas d'utilisation des rapports planifiés
        """
        return self
    
    def get_report_distribution_use_cases(self):
        """
        Retourne un objet avec les cas d'utilisation de distribution des rapports.
        
        Returns:
            Un objet avec les cas d'utilisation de distribution des rapports
        """
        return self
    
    def get_report_export_use_cases(self):
        """
        Retourne un objet avec les cas d'utilisation d'exportation des rapports.
        
        Returns:
            Un objet avec les cas d'utilisation d'exportation des rapports
        """
        return self
    
    # Méthodes de cas d'utilisation des rapports
    def generate_report(self, template_id, parameters, user_id, report_type):
        """Génère un rapport."""
        return self.generate_report_use_case.execute(template_id, parameters, user_id, report_type)
    
    def get_report_by_id(self, report_id):
        """Récupère un rapport par son ID."""
        return self.get_report_use_case.execute(report_id)
    
    def list_reports(self, filters=None):
        """Liste les rapports."""
        return self.list_reports_use_case.execute(filters)
    
    def delete_report(self, report_id):
        """Supprime un rapport."""
        return self.delete_report_use_case.execute(report_id)
    
    # Méthodes de cas d'utilisation des templates
    def get_template_by_id(self, template_id):
        """Récupère un template par son ID."""
        return self.template_repository.get_by_id(template_id)
    
    def list_templates(self, filters=None):
        """Liste les templates."""
        return self.template_repository.list(filters)
    
    # Méthodes de cas d'utilisation des rapports planifiés
    def schedule_report(self, report_id, frequency, recipients, format=None):
        """Planifie un rapport."""
        return self.schedule_report_use_case.execute(report_id, frequency, recipients, format)
    
    def update_schedule(self, schedule_id, frequency=None, is_active=None):
        """Met à jour une planification."""
        scheduled = self.scheduled_repository.get_by_id(schedule_id)
        if frequency is not None:
            scheduled.frequency = frequency
        if is_active is not None:
            scheduled.is_active = is_active
        return self.scheduled_repository.update(scheduled)
    
    # Méthodes de cas d'utilisation de distribution
    def distribute_report(self, report_id, recipients, distribution_method):
        """Distribue un rapport."""
        return self.distribute_report_use_case.execute(report_id, recipients, distribution_method)
    
    def distribute_report_with_filter(self, report_id, recipient_filter, distribution_method):
        """Distribue un rapport avec filtre."""
        # Simuler un filtrage simple pour les tests
        from django.contrib.auth.models import User
        users = User.objects.filter(**recipient_filter)
        recipients = [user.id for user in users]
        return self.distribute_report(report_id, recipients, distribution_method)
    
    def process_due_scheduled_reports(self):
        """Traite les rapports planifiés dus."""
        # Simuler le traitement des rapports planifiés pour les tests
        from reporting.models import ScheduledReport
        from datetime import datetime, timedelta
        
        results = []
        due_schedules = ScheduledReport.objects.filter(is_active=True, next_run__lte=datetime.now())
        
        for schedule in due_schedules:
            try:
                # Exporter le rapport
                self.export_report(schedule.report.id, format="pdf")
                
                # Notifier les destinataires
                recipients = [user.id for user in schedule.recipients.all()]
                self.notification_service.notify_report_completion(schedule.report.id, recipients)
                
                # Mettre à jour next_run
                schedule.next_run = datetime.now() + timedelta(days=7)  # Simuler weekly
                schedule.save()
                
                results.append({
                    "schedule_id": schedule.id,
                    "report_id": schedule.report.id,
                    "success": True
                })
            except Exception as e:
                results.append({
                    "schedule_id": schedule.id,
                    "report_id": schedule.report.id if schedule.report else None,
                    "success": False,
                    "error": str(e)
                })
        
        return results
    
    # Méthodes de cas d'utilisation d'exportation
    def export_report(self, report_id, format, output_path=None):
        """Exporte un rapport."""
        from reporting.domain.entities import ReportFormat
        
        # Convertir le format en enum
        format_enum = None
        if format == "pdf":
            format_enum = ReportFormat.PDF
        elif format == "xlsx":
            format_enum = ReportFormat.XLSX
        elif format == "csv":
            format_enum = ReportFormat.CSV
        elif format == "json":
            format_enum = ReportFormat.JSON
        elif format == "html":
            format_enum = ReportFormat.HTML
        else:
            format_enum = format  # Supposer que c'est déjà un enum
        
        # Exporter le rapport
        return self.storage_service.store(
            report=self.get_report_by_id(report_id),
            content=self.formatter_service.format_report(self.get_report_by_id(report_id), format_enum),
            format=format_enum
        ) is not None


# Fonction pour résoudre une dépendance
def resolve(interface_cls):
    """
    Résout une interface vers son implémentation concrète.
    
    Args:
        interface_cls: La classe d'interface à résoudre
        
    Returns:
        L'implémentation concrète de l'interface
    """
    return ReportingContainer.resolve(interface_cls)


# Fonction globale pour obtenir le conteneur (compatibilité)
def get_container():
    """
    Obtient une instance configurée du conteneur.
    
    Returns:
        DIContainer: Instance configurée du conteneur pour les tests
    """
    return DIContainer() 