"""
Exceptions du domaine pour le module Reporting.

Ce module définit les exceptions métier spécifiques au domaine des rapports.
"""

class ReportingException(Exception):
    """Exception de base pour le module reporting."""
    pass

class ReportValidationError(ReportingException):
    """Erreur de validation d'un rapport."""
    pass

class ReportNotFoundError(ReportingException):
    """Erreur quand un rapport n'est pas trouvé."""
    pass

class ReportGenerationError(ReportingException):
    """Erreur lors de la génération d'un rapport."""
    pass

class ReportTemplateError(ReportingException):
    """Erreur liée aux templates de rapport."""
    pass

class ReportDistributionError(ReportingException):
    """Erreur lors de la distribution d'un rapport."""
    pass

class ReportStorageError(ReportingException):
    """Erreur de stockage des rapports."""
    pass

class DataIntegrationError(ReportingException):
    """Erreur lors de l'intégration de données."""
    pass

class VisualizationError(ReportingException):
    """Erreur lors de la création de visualisations."""
    pass

class AnalyticsError(ReportingException):
    """Erreur lors de l'analyse de données."""
    pass

class CacheError(ReportingException):
    """Erreur de cache."""
    pass

class PermissionDeniedError(ReportingException):
    """Erreur d'autorisation."""
    pass

class ConfigurationError(ReportingException):
    """Erreur de configuration."""
    pass

class InvalidFormatError(ReportingException):
    """Erreur de format de données invalide."""
    pass

class ServiceUnavailableError(ReportingException):
    """Erreur quand un service n'est pas disponible."""
    pass

# Exceptions supplémentaires nécessaires pour l'infrastructure
class UnsupportedReportTypeException(ReportingException):
    """Exception levée quand un type de rapport n'est pas supporté."""
    def __init__(self, report_type, supported_types=None):
        self.report_type = report_type
        self.supported_types = supported_types or []
        message = f"Type de rapport non supporté: {report_type}"
        if supported_types:
            message += f". Types supportés: {', '.join(supported_types)}"
        super().__init__(message)

class UnsupportedDistributionChannelException(ReportingException):
    """Exception levée quand un canal de distribution n'est pas supporté."""
    def __init__(self, channel, supported_channels=None):
        self.channel = channel
        self.supported_channels = supported_channels or []
        message = f"Canal de distribution non supporté: {channel}"
        if supported_channels:
            message += f". Canaux supportés: {', '.join(supported_channels)}"
        super().__init__(message)

class ReportGenerationFailedException(ReportingException):
    """Exception levée quand la génération d'un rapport échoue."""
    def __init__(self, report_type, reason=None):
        self.report_type = report_type
        self.reason = reason
        message = f"Échec de la génération du rapport de type {report_type}"
        if reason:
            message += f": {reason}"
        super().__init__(message)

class ReportDistributionFailedException(ReportingException):
    """Exception levée quand la distribution d'un rapport échoue."""
    def __init__(self, report_id, channel, reason=None):
        self.report_id = report_id
        self.channel = channel
        self.reason = reason
        message = f"Échec de la distribution du rapport {report_id} via {channel}"
        if reason:
            message += f": {reason}"
        super().__init__(message)

class ReportValidationException(ReportingException):
    """Exception levée quand la validation d'un rapport échoue."""
    def __init__(self, errors=None):
        self.errors = errors or {}
        message = "Validation du rapport échouée"
        if errors:
            message += f": {errors}"
        super().__init__(message) 