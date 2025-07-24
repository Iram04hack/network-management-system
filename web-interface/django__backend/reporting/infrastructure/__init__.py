"""
Package pour l'infrastructure du module reporting.

Ce package contient les implémentations concrètes des interfaces du domaine,
ainsi que les adaptateurs pour les services existants.
"""

from .services import (
    DjangoReportExporter,
    DjangoReportGenerator,
    DjangoNotificationService,
    ReportFormatterService,
    ReportStorageService
)
from .adapters import LegacyReportServiceAdapter

# Imports à implémenter dans les phases suivantes
# from .django_report_repository import DjangoReportRepository
# from .django_report_template_repository import DjangoReportTemplateRepository
# from .django_scheduled_report_repository import DjangoScheduledReportRepository
# from .report_generation_service_impl import ReportGenerationServiceImpl
# from .scheduled_report_service_impl import ScheduledReportServiceImpl

__all__ = [
    'DjangoReportExporter',
    'DjangoReportGenerator',
    'DjangoNotificationService',
    'ReportFormatterService',
    'ReportStorageService',
    'LegacyReportServiceAdapter',
    # À implémenter dans les phases suivantes
    # 'DjangoReportRepository',
    # 'DjangoReportTemplateRepository',
    # 'DjangoScheduledReportRepository',
    # 'ReportGenerationServiceImpl',
    # 'ScheduledReportServiceImpl',
] 