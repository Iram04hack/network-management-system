"""
Exceptions spécifiques au domaine pour le module security_management.

Ce module définit les exceptions personnalisées qui peuvent être levées
par les différentes couches du module security_management.
"""

class SecurityManagementException(Exception):
    """
    Exception de base pour toutes les exceptions du module security_management.
    """
    pass


# Exceptions liées aux entités du domaine

class EntityNotFoundException(SecurityManagementException):
    """
    Exception levée lorsqu'une entité demandée n'est pas trouvée.
    """
    def __init__(self, entity_type: str, entity_id=None, message=None):
        self.entity_type = entity_type
        self.entity_id = entity_id
        self.message = message or f"{entity_type} avec l'ID {entity_id} non trouvé"
        super().__init__(self.message)


class EntityValidationException(SecurityManagementException):
    """
    Exception levée lorsqu'une entité ne peut pas être validée.
    """
    def __init__(self, entity_type: str, errors=None, message=None):
        self.entity_type = entity_type
        self.errors = errors or {}
        self.message = message or f"Validation échouée pour {entity_type}: {errors}"
        super().__init__(self.message)


class EntityAlreadyExistsException(SecurityManagementException):
    """
    Exception levée lorsqu'on tente de créer une entité qui existe déjà.
    """
    def __init__(self, entity_type: str, identifier=None, message=None):
        self.entity_type = entity_type
        self.identifier = identifier
        self.message = message or f"{entity_type} avec identifiant {identifier} existe déjà"
        super().__init__(self.message)


# Exceptions liées aux règles de sécurité

class SecurityRuleValidationException(SecurityManagementException):
    """
    Exception levée lorsqu'une règle de sécurité n'est pas valide.
    """
    def __init__(self, rule_id=None, rule_name=None, errors=None, message=None):
        self.rule_id = rule_id
        self.rule_name = rule_name
        self.errors = errors or []
        self.message = message or f"Règle de sécurité {rule_name or rule_id} non valide: {errors}"
        super().__init__(self.message)


class RuleConflictException(SecurityManagementException):
    """
    Exception levée lorsqu'une règle est en conflit avec une autre.
    """
    def __init__(self, rule_id=None, conflicting_rule_id=None, message=None, conflict_details=None):
        self.rule_id = rule_id
        self.conflicting_rule_id = conflicting_rule_id
        self.conflict_details = conflict_details or {}
        self.message = message or (
            f"Conflit entre la règle {rule_id} et la règle {conflicting_rule_id}: {conflict_details}"
        )
        super().__init__(self.message)


class RuleApplicationException(SecurityManagementException):
    """
    Exception levée lorsqu'une règle ne peut pas être appliquée à un système.
    """
    def __init__(self, rule_id=None, target_system=None, reason=None, message=None):
        self.rule_id = rule_id
        self.target_system = target_system
        self.reason = reason
        self.message = message or f"Impossible d'appliquer la règle {rule_id} à {target_system}: {reason}"
        super().__init__(self.message)


# Exceptions liées aux services externes

class ExternalServiceException(SecurityManagementException):
    """
    Exception de base pour les erreurs liées aux services externes.
    """
    pass


class SuricataServiceException(ExternalServiceException):
    """
    Exception levée lors d'erreurs avec le service Suricata.
    """
    def __init__(self, operation=None, reason=None, message=None):
        self.operation = operation
        self.reason = reason
        self.message = message or f"Erreur Suricata pendant l'opération {operation}: {reason}"
        super().__init__(self.message)


class Fail2BanServiceException(ExternalServiceException):
    """
    Exception levée lors d'erreurs avec le service Fail2Ban.
    """
    def __init__(self, operation=None, reason=None, message=None):
        self.operation = operation
        self.reason = reason
        self.message = message or f"Erreur Fail2Ban pendant l'opération {operation}: {reason}"
        super().__init__(self.message)


class FirewallServiceException(ExternalServiceException):
    """
    Exception levée lors d'erreurs avec le service Firewall.
    """
    def __init__(self, operation=None, reason=None, message=None):
        self.operation = operation
        self.reason = reason
        self.message = message or f"Erreur Firewall pendant l'opération {operation}: {reason}"
        super().__init__(self.message)


# Exceptions liées à la corrélation d'événements

class CorrelationEngineException(SecurityManagementException):
    """
    Exception levée lors d'erreurs dans le moteur de corrélation.
    """
    def __init__(self, rule_id=None, reason=None, message=None):
        self.rule_id = rule_id
        self.reason = reason
        self.message = message or f"Erreur de corrélation pour la règle {rule_id}: {reason}"
        super().__init__(self.message)


# Exceptions liées à l'analyse d'impact

class ImpactAnalysisException(SecurityManagementException):
    """
    Exception levée lors d'erreurs dans l'analyse d'impact d'une règle.
    """
    def __init__(self, rule_id=None, reason=None, message=None):
        self.rule_id = rule_id
        self.reason = reason
        self.message = message or f"Erreur d'analyse d'impact pour la règle {rule_id}: {reason}"
        super().__init__(self.message)


# Exceptions liées aux cas d'utilisation

class UseCaseValidationException(SecurityManagementException):
    """
    Exception levée lorsque les entrées d'un cas d'utilisation ne sont pas valides.
    """
    def __init__(self, use_case=None, errors=None, message=None):
        self.use_case = use_case
        self.errors = errors or {}
        self.message = message or f"Validation échouée pour le cas d'utilisation {use_case}: {errors}"
        super().__init__(self.message)


class AuthorizationException(SecurityManagementException):
    """
    Exception levée lorsqu'un utilisateur n'est pas autorisé à effectuer une action.
    """
    def __init__(self, user=None, action=None, resource=None, message=None):
        self.user = user
        self.action = action
        self.resource = resource
        self.message = message or f"Utilisateur {user} non autorisé pour {action} sur {resource}"
        super().__init__(self.message)


# Exceptions liées à la configuration

class ConfigurationException(SecurityManagementException):
    """
    Exception levée lors de problèmes avec la configuration du module.
    """
    def __init__(self, component=None, reason=None, message=None):
        self.component = component
        self.reason = reason
        self.message = message or f"Erreur de configuration pour {component}: {reason}"
        super().__init__(self.message) 