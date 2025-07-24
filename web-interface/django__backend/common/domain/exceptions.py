"""
Hiérarchie d'exceptions standardisée pour le système NMS.

Ce module définit une structure complète et cohérente d'exceptions
qui peuvent être levées à travers l'ensemble du système pour signaler
différents types d'erreurs de manière uniforme.

L'utilisation d'exceptions spécialisées facilite:
- Le traitement spécifique selon le type d'erreur
- La conversion en codes HTTP appropriés dans les API
- La journalisation adaptée selon le niveau de gravité
- L'affichage de messages d'erreur cohérents
"""
from typing import Dict, Any, Optional


class NMSException(Exception):
    """
    Exception de base pour toutes les exceptions spécifiques au NMS.
    
    Toutes les exceptions du système héritent de cette classe pour
    garantir un comportement cohérent et une structure commune.
    
    Attributes:
        message (str): Message d'erreur détaillé
        code (str): Code d'erreur unique pour identification précise
        details (dict): Détails supplémentaires liés à l'exception
    """
    default_message = "Une erreur inattendue s'est produite."
    default_code = "error"
    
    def __init__(self, message: Optional[str] = None, code: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        """
        Initialise l'exception avec les informations nécessaires.
        
        Args:
            message: Message d'erreur explicatif
            code: Code d'erreur pour identification
            details: Détails supplémentaires liés à l'exception
        """
        self.message = message or self.default_message
        self.code = code or self.default_code
        self.details = details or {}
        super().__init__(self.message)
    
    def __str__(self) -> str:
        """Représentation sous forme de chaîne pour le débogage."""
        if self.details:
            return f"{self.message} [Code: {self.code}, Details: {self.details}]"
        return f"{self.message} [Code: {self.code}]"


# ========== Exceptions liées aux services externes ==========

class ServiceException(NMSException):
    """Exception de base pour les problèmes liés aux services externes."""
    default_message = "Erreur lors de l'interaction avec un service."
    default_code = "service_error"


class ServiceUnavailableException(ServiceException):
    """Le service est actuellement indisponible."""
    default_message = "Le service est actuellement indisponible."
    default_code = "service_unavailable"


class ServiceTimeoutException(ServiceException):
    """Le service n'a pas répondu dans le délai imparti."""
    default_message = "Le service n'a pas répondu dans le délai imparti."
    default_code = "service_timeout"


class ServiceAuthenticationException(ServiceException):
    """Échec d'authentification auprès du service externe."""
    default_message = "Échec d'authentification auprès du service."
    default_code = "service_authentication_error"


class ServiceCommunicationException(ServiceException):
    """Problème de communication avec le service (format, encodage, etc.)."""
    default_message = "Erreur de communication avec le service."
    default_code = "service_communication_error"


# ========== Exceptions liées à la validation ==========

class ValidationException(NMSException):
    """Exception de base pour les erreurs de validation."""
    default_message = "Erreur de validation."
    default_code = "validation_error"


class InvalidInputException(ValidationException):
    """Les données d'entrée sont invalides."""
    default_message = "Les données d'entrée sont invalides."
    default_code = "invalid_input"


class MissingRequiredFieldException(ValidationException):
    """Un champ requis est manquant."""
    default_message = "Un champ requis est manquant."
    default_code = "missing_required_field"


class InvalidFormatException(ValidationException):
    """Le format des données est invalide."""
    default_message = "Le format des données est invalide."
    default_code = "invalid_format"


class ValidationConstraintException(ValidationException):
    """Une contrainte de validation n'est pas respectée."""
    default_message = "Une contrainte de validation n'est pas respectée."
    default_code = "validation_constraint"


# ========== Exceptions liées aux permissions ==========

class PermissionException(NMSException):
    """Exception de base pour les problèmes de permission."""
    default_message = "Vous n'avez pas la permission d'effectuer cette action."
    default_code = "permission_denied"


class AdminRequiredException(PermissionException):
    """Cette action nécessite des privilèges d'administrateur."""
    default_message = "Cette action nécessite des privilèges d'administrateur."
    default_code = "admin_required"


class UnauthorizedException(PermissionException):
    """L'utilisateur n'est pas authentifié."""
    default_message = "Authentification requise pour accéder à cette ressource."
    default_code = "unauthorized"


class InsufficientPrivilegesException(PermissionException):
    """L'utilisateur n'a pas les privilèges nécessaires."""
    default_message = "Privilèges insuffisants pour effectuer cette action."
    default_code = "insufficient_privileges"


# ========== Exceptions liées aux ressources ==========

class ResourceException(NMSException):
    """Exception de base pour les problèmes liés aux ressources."""
    default_message = "Erreur liée à une ressource."
    default_code = "resource_error"


class NotFoundException(ResourceException):
    """La ressource demandée n'a pas été trouvée."""
    default_message = "La ressource demandée n'a pas été trouvée."
    default_code = "not_found"


class ResourceExistsException(ResourceException):
    """La ressource existe déjà."""
    default_message = "La ressource existe déjà."
    default_code = "resource_exists"


class ResourceLockedException(ResourceException):
    """La ressource est verrouillée et ne peut pas être modifiée."""
    default_message = "La ressource est verrouillée et ne peut pas être modifiée."
    default_code = "resource_locked"


# ========== Exceptions liées aux opérations réseau ==========

class NetworkException(NMSException):
    """Exception de base pour les problèmes réseau."""
    default_message = "Erreur réseau."
    default_code = "network_error"


class DeviceConnectionException(NetworkException):
    """Impossible de se connecter à l'équipement réseau."""
    default_message = "Impossible de se connecter à l'équipement réseau."
    default_code = "device_connection_error"


class ConfigurationApplyException(NetworkException):
    """Échec de l'application de la configuration sur l'équipement."""
    default_message = "Échec de l'application de la configuration sur l'équipement."
    default_code = "configuration_apply_error"


class NetworkDiscoveryException(NetworkException):
    """Erreur lors de la découverte du réseau."""
    default_message = "Erreur lors de la découverte du réseau."
    default_code = "network_discovery_error"


class DeviceCommandException(NetworkException):
    """Erreur lors de l'exécution d'une commande sur un équipement."""
    default_message = "Erreur lors de l'exécution d'une commande sur l'équipement."
    default_code = "device_command_error"


# ========== Exceptions liées à la sécurité ==========

class SecurityException(NMSException):
    """Exception de base pour les problèmes de sécurité."""
    default_message = "Erreur de sécurité."
    default_code = "security_error"


class RuleDeploymentException(SecurityException):
    """Échec du déploiement de la règle de sécurité."""
    default_message = "Échec du déploiement de la règle de sécurité."
    default_code = "rule_deployment_error"


class InvalidRuleException(SecurityException):
    """La règle de sécurité est invalide."""
    default_message = "La règle de sécurité est invalide."
    default_code = "invalid_rule"


class SecurityViolationException(SecurityException):
    """Violation de sécurité détectée."""
    default_message = "Violation de sécurité détectée."
    default_code = "security_violation"


class CertificateException(SecurityException):
    """Problème avec un certificat SSL/TLS."""
    default_message = "Erreur liée à un certificat SSL/TLS."
    default_code = "certificate_error"


# ========== Exceptions liées au monitoring ==========

class MonitoringException(NMSException):
    """Exception de base pour les erreurs de monitoring."""
    default_message = "Erreur lors d'une opération de monitoring."
    default_code = "monitoring_error"


class AlertConfigException(MonitoringException):
    """Erreur dans la configuration d'une alerte."""
    default_message = "Erreur dans la configuration d'une alerte."
    default_code = "alert_config_error"


class MetricCollectionException(MonitoringException):
    """Erreur lors de la collecte de métriques."""
    default_message = "Erreur lors de la collecte de métriques."
    default_code = "metric_collection_error"


class MonitoringServiceException(MonitoringException):
    """Problème avec un service de monitoring externe."""
    default_message = "Problème avec un service de monitoring externe."
    default_code = "monitoring_service_error"


class ThresholdException(MonitoringException):
    """Erreur liée à un seuil de déclenchement."""
    default_message = "Erreur liée à un seuil de déclenchement."
    default_code = "threshold_error"


# ========== Exceptions liées à la QoS ==========

class QoSException(NMSException):
    """Exception de base pour les erreurs de Qualité de Service."""
    default_message = "Erreur lors d'une opération liée à la QoS."
    default_code = "qos_error"


class PolicyDeploymentException(QoSException):
    """Erreur lors du déploiement d'une politique QoS."""
    default_message = "Erreur lors du déploiement d'une politique QoS."
    default_code = "policy_deployment_error"


class QoSConfigurationException(QoSException):
    """Erreur dans la configuration QoS."""
    default_message = "Erreur dans la configuration QoS."
    default_code = "qos_config_error"


class BandwidthException(QoSException):
    """Problème lié à la gestion de la bande passante."""
    default_message = "Problème lié à la gestion de la bande passante."
    default_code = "bandwidth_error"


class TrafficClassException(QoSException):
    """Erreur liée à une classe de trafic."""
    default_message = "Erreur liée à une classe de trafic."
    default_code = "traffic_class_error"


# ========== Exceptions liées à l'automatisation ==========

class AutomationException(NMSException):
    """Exception de base pour les erreurs d'automatisation."""
    default_message = "Erreur lors d'une opération automatisée."
    default_code = "automation_error"


class SchedulerException(AutomationException):
    """Erreur avec le planificateur de tâches."""
    default_message = "Erreur avec le planificateur de tâches."
    default_code = "scheduler_error"


class ScriptExecutionException(AutomationException):
    """Erreur lors de l'exécution d'un script."""
    default_message = "Erreur lors de l'exécution d'un script."
    default_code = "script_execution_error"


class TaskException(AutomationException):
    """Erreur liée à une tâche automatisée."""
    default_message = "Erreur liée à une tâche automatisée."
    default_code = "task_error"


class ConflictException(NMSException):
    """Exception levée en cas de conflit (ex: ressource déjà existante)."""
    default_message = "La ressource est en conflit avec une ressource existante."
    default_code = "conflict"


class RateLimitedException(NMSException):
    """Exception levée lorsque le taux de requêtes est dépassé."""
    default_message = "Trop de requêtes. Veuillez réessayer plus tard."
    default_code = "rate_limited"


class TimeoutException(NMSException):
    """Exception levée lorsqu'une opération prend trop de temps."""
    default_message = "L'opération a expiré."
    default_code = "timeout" 