"""
Package de domaine pour le module reporting.

Ce package contient les entités, interfaces et exceptions du domaine.
"""

from .entities import Report, ReportTemplate, ScheduledReport, ReportType, ReportStatus, ReportFormat, Frequency
from .interfaces import (
    ReportRepository, ReportTemplateRepository, ScheduledReportRepository,
    ReportGenerationService, ReportStorageService, ReportExportService,
    NotificationService
)
from .exceptions import ReportingException, ReportNotFoundError, ReportGenerationError, ReportValidationError

__all__ = [
    'Report', 'ReportTemplate', 'ScheduledReport',
    'ReportType', 'ReportStatus', 'ReportFormat', 'Frequency',
    'ReportRepository', 'ReportTemplateRepository', 'ScheduledReportRepository',
    'ReportGenerationService', 'ReportStorageService', 'ReportExportService',
    'NotificationService',
    'ReportingException', 'ReportNotFoundError', 'ReportGenerationError', 'ReportValidationError'
] 