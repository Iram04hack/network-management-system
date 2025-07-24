"""
Initialisation du module de domaine pour le module security_management.

Ce fichier expose les principales classes et interfaces du domaine
pour faciliter leur importation depuis d'autres parties du code.
"""

# Importation et exposition des entités principales
from .entities import (
    SecurityRule, SecurityAlert, AuditLog, BannedIP, Jail, 
    TrafficBaseline, TrafficAnomaly, IPReputation, 
    CorrelationRule, CorrelationRuleMatch, EntityId,
    RuleType, SeverityLevel, ActionType, CategoryType, AlertStatus
)

# Importation et exposition des interfaces principales
from .interfaces import (
    SecurityDeviceRepository,
    SuricataService,
    Fail2BanService,
    FirewallService
)

# Importation et exposition des interfaces de repository

from .repository_interfaces import (
    SecurityRuleRepository,
    SecurityAlertRepository
)

# Importation et exposition des exceptions
from .exceptions import (
    SecurityManagementException,
    EntityNotFoundException, EntityValidationException, EntityAlreadyExistsException,
    SecurityRuleValidationException, RuleConflictException, RuleApplicationException,
    SuricataServiceException, Fail2BanServiceException, FirewallServiceException,
    CorrelationEngineException, ImpactAnalysisException,
    UseCaseValidationException, AuthorizationException, ConfigurationException
)

# Le fichier services.py sera importé plus tard quand il sera créé
# from .services import SecurityCorrelationEngine, AnomalyDetectionService

__all__ = [
    # Entités
    'SecurityRule', 'SecurityAlert', 'AuditLog', 'BannedIP', 'Jail',
    'TrafficBaseline', 'TrafficAnomaly', 'IPReputation',
    'CorrelationRule', 'CorrelationRuleMatch', 'EntityId',
    'RuleType', 'SeverityLevel', 'ActionType', 'CategoryType', 'AlertStatus',
    
    # Interfaces
    'SecurityDeviceRepository',
    'SuricataService', 'Fail2BanService', 'FirewallService',
    
    # Interfaces de repository
    'SecurityRuleRepository',
    'SecurityAlertRepository',
    
    # Exceptions
    'SecurityManagementException',
    'EntityNotFoundException', 'EntityValidationException', 'EntityAlreadyExistsException',
    'SecurityRuleValidationException', 'RuleConflictException', 'RuleApplicationException',
    'SuricataServiceException', 'Fail2BanServiceException', 'FirewallServiceException',
    'CorrelationEngineException', 'ImpactAnalysisException',
    'UseCaseValidationException', 'AuthorizationException', 'ConfigurationException'
    
    # Les services seront ajoutés plus tard
    # 'SecurityCorrelationEngine', 'AnomalyDetectionService'
] 