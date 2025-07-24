"""
Conteneur d'injection de dépendances (DI) pour le module security_management.

Ce fichier fournit un conteneur qui gère la création et l'injection des dépendances
pour les différentes couches de l'application.
"""

import logging
from .domain.services import RuleConflictDetector
from .infrastructure.repositories import (
    DjangoSecurityRuleRepository, 
    DjangoSecurityAlertRepository,
    DjangoSecurityPolicyRepository,
    DjangoVulnerabilityRepository,
    DjangoThreatIntelligenceRepository,
    DjangoIncidentResponseWorkflowRepository,
    DjangoIncidentResponseExecutionRepository,
    DjangoSecurityReportRepository
)
from .application.use_cases import (
    RuleManagementUseCase,
    AlertManagementUseCase,
    SecurityPolicyUseCase,
    VulnerabilityManagementUseCase,
    ThreatIntelligenceUseCase,
    IncidentResponseWorkflowUseCase,
    SecurityReportUseCase
)

logger = logging.getLogger(__name__)


class SecurityManagementContainer:
    """Conteneur d'injection de dépendances pour le module security_management."""
    
    def __init__(self):
        """Initialise le conteneur avec les dépendances par défaut."""
        # Initialiser les repositories
        self._rule_repository = None
        self._alert_repository = None
        self._policy_repository = None
        self._vulnerability_repository = None
        self._threat_repository = None
        self._workflow_repository = None
        self._execution_repository = None
        self._report_repository = None
        
        # Initialiser les services du domaine
        self._rule_conflict_detector = None
        
        # Initialiser les cas d'utilisation
        self._rule_management_use_case = None
        self._alert_management_use_case = None
        self._policy_use_case = None
        self._vulnerability_management_use_case = None
        self._threat_intelligence_use_case = None
        self._workflow_use_case = None
        self._report_use_case = None
    
    @property
    def rule_repository(self):
        """Repository pour les règles de sécurité."""
        if not self._rule_repository:
            self._rule_repository = DjangoSecurityRuleRepository()
        return self._rule_repository
    
    @property
    def alert_repository(self):
        """Repository pour les alertes de sécurité."""
        if not self._alert_repository:
            self._alert_repository = DjangoSecurityAlertRepository()
        return self._alert_repository
    
    @property
    def policy_repository(self):
        """Repository pour les politiques de sécurité."""
        if not self._policy_repository:
            self._policy_repository = DjangoSecurityPolicyRepository()
        return self._policy_repository
    
    @property
    def vulnerability_repository(self):
        """Repository pour les vulnérabilités."""
        if not self._vulnerability_repository:
            self._vulnerability_repository = DjangoVulnerabilityRepository()
        return self._vulnerability_repository
    
    @property
    def threat_repository(self):
        """Repository pour les indicateurs de menace."""
        if not self._threat_repository:
            self._threat_repository = DjangoThreatIntelligenceRepository()
        return self._threat_repository
    
    @property
    def workflow_repository(self):
        """Repository pour les workflows de réponse aux incidents."""
        if not self._workflow_repository:
            self._workflow_repository = DjangoIncidentResponseWorkflowRepository()
        return self._workflow_repository
    
    @property
    def execution_repository(self):
        """Repository pour les exécutions de workflows."""
        if not self._execution_repository:
            self._execution_repository = DjangoIncidentResponseExecutionRepository()
        return self._execution_repository
    
    @property
    def report_repository(self):
        """Repository pour les rapports de sécurité."""
        if not self._report_repository:
            self._report_repository = DjangoSecurityReportRepository()
        return self._report_repository
    
    @property
    def rule_conflict_detector(self):
        """Détecteur de conflits entre règles."""
        if not self._rule_conflict_detector:
            self._rule_conflict_detector = RuleConflictDetector()
        return self._rule_conflict_detector
    
    @property
    def rule_management_use_case(self):
        """Cas d'utilisation pour la gestion des règles."""
        if not self._rule_management_use_case:
            self._rule_management_use_case = RuleManagementUseCase(
                rule_repository=self.rule_repository,
                conflict_detector=self.rule_conflict_detector
            )
        return self._rule_management_use_case
    
    @property
    def alert_management_use_case(self):
        """Cas d'utilisation pour la gestion des alertes."""
        if not self._alert_management_use_case:
            self._alert_management_use_case = AlertManagementUseCase(
                alert_repository=self.alert_repository
            )
        return self._alert_management_use_case
    
    @property
    def policy_use_case(self):
        """Cas d'utilisation pour la gestion des politiques de sécurité."""
        if not self._policy_use_case:
            self._policy_use_case = SecurityPolicyUseCase(
                policy_repository=self.policy_repository
            )
        return self._policy_use_case
    
    @property
    def vulnerability_management_use_case(self):
        """Cas d'utilisation pour la gestion des vulnérabilités."""
        if not self._vulnerability_management_use_case:
            self._vulnerability_management_use_case = VulnerabilityManagementUseCase(
                vulnerability_repository=self.vulnerability_repository
            )
        return self._vulnerability_management_use_case
    
    @property
    def threat_intelligence_use_case(self):
        """Cas d'utilisation pour la gestion des indicateurs de menace."""
        if not self._threat_intelligence_use_case:
            self._threat_intelligence_use_case = ThreatIntelligenceUseCase(
                threat_repository=self.threat_repository
            )
        return self._threat_intelligence_use_case
    
    @property
    def workflow_use_case(self):
        """Cas d'utilisation pour la gestion des workflows de réponse aux incidents."""
        if not self._workflow_use_case:
            self._workflow_use_case = IncidentResponseWorkflowUseCase(
                workflow_repository=self.workflow_repository,
                execution_repository=self.execution_repository
            )
        return self._workflow_use_case
    
    @property
    def report_use_case(self):
        """Cas d'utilisation pour la gestion des rapports de sécurité."""
        if not self._report_use_case:
            self._report_use_case = SecurityReportUseCase(
                report_repository=self.report_repository
            )
        return self._report_use_case


# Singleton du conteneur pour l'accès global
container = SecurityManagementContainer()


def initialize_container():
    """
    Initialise le conteneur d'injection de dépendances.
    Cette fonction est appelée au démarrage de l'application.
    """
    try:
        # Accéder aux propriétés pour forcer leur initialisation
        container.rule_repository
        container.alert_repository
        container.policy_repository
        container.vulnerability_repository
        container.threat_repository
        container.workflow_repository
        container.execution_repository
        container.report_repository
        
        # Initialiser les cas d'utilisation
        container.rule_management_use_case
        container.alert_management_use_case
        container.policy_use_case
        container.vulnerability_management_use_case
        container.threat_intelligence_use_case
        container.workflow_use_case
        container.report_use_case
        
        logger.info("Conteneur d'injection de dépendances security_management initialisé avec succès")
        return True
    except Exception as e:
        logger.error(f"Erreur lors de l'initialisation du conteneur de sécurité: {str(e)}")
        logger.error(f"Détail de l'erreur:\n{e}", exc_info=True)
        return False
 