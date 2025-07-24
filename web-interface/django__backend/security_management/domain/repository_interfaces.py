"""
Interfaces de repository selon le pattern CQRS pour le module security_management.

Ce fichier définit les interfaces de repository suivant les principes du pattern
Command Query Responsibility Segregation (CQRS). Les interfaces sont séparées en:
- Readers: pour les opérations de lecture (queries)
- Writers: pour les opérations d'écriture (commands)
- QueryServices: pour les requêtes complexes et spécialisées
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, TypeVar, Generic, Protocol
from datetime import datetime

from .entities import (
    SecurityRule, SecurityAlert, EntityId,
    CorrelationRule, CorrelationRuleMatch,
    TrafficBaseline, TrafficAnomaly,
    IPReputation, RuleType, SeverityLevel, ActionType,
    SecurityPolicy, Vulnerability, ThreatIntelligence,
    IncidentResponseWorkflow, IncidentResponseExecution, SecurityReport,
    AlertStatus
)

# Types génériques
T = TypeVar('T')


class SecurityRuleRepository(ABC):
    """Interface pour le repository des règles de sécurité."""

    @abstractmethod
    def get_by_id(self, entity_id: EntityId) -> Optional[SecurityRule]:
        """
        Récupère une règle de sécurité par son ID.
        
        Args:
            entity_id: ID de l'entité à récupérer
            
        Returns:
            SecurityRule: L'entité trouvée ou None si non trouvée
        """
        pass

    @abstractmethod
    def get_all(self) -> List[SecurityRule]:
        """
        Récupère toutes les règles de sécurité.
        
        Returns:
            List[SecurityRule]: Liste des règles de sécurité
        """
        pass

    @abstractmethod
    def get_by_type(self, rule_type: RuleType) -> List[SecurityRule]:
        """
        Récupère les règles de sécurité par type.
        
        Args:
            rule_type: Le type de règle à rechercher
            
        Returns:
            List[SecurityRule]: Liste des règles de sécurité du type spécifié
        """
        pass

    @abstractmethod
    def get_enabled_rules(self) -> List[SecurityRule]:
        """
        Récupère les règles de sécurité activées.
        
        Returns:
            List[SecurityRule]: Liste des règles de sécurité activées
        """
        pass

    @abstractmethod
    def save(self, entity: SecurityRule) -> SecurityRule:
        """
        Sauvegarde une règle de sécurité.
        
        Args:
            entity: L'entité à sauvegarder
            
        Returns:
            SecurityRule: L'entité sauvegardée avec son ID mis à jour
        """
        pass

    @abstractmethod
    def delete(self, entity_id: EntityId) -> bool:
        """
        Supprime une règle de sécurité.
        
        Args:
            entity_id: ID de l'entité à supprimer
            
        Returns:
            bool: True si la suppression a réussi, False sinon
        """
        pass


class SecurityAlertRepository(ABC):
    """Interface pour le repository des alertes de sécurité."""

    @abstractmethod
    def get_by_id(self, entity_id: EntityId) -> Optional[SecurityAlert]:
        """
        Récupère une alerte de sécurité par son ID.
        
        Args:
            entity_id: ID de l'entité à récupérer
            
        Returns:
            SecurityAlert: L'entité trouvée ou None si non trouvée
        """
        pass

    @abstractmethod
    def get_by_status(self, status: AlertStatus) -> List[SecurityAlert]:
        """
        Récupère les alertes de sécurité par statut.
        
        Args:
            status: Le statut à rechercher
            
        Returns:
            List[SecurityAlert]: Liste des alertes de sécurité avec le statut spécifié
        """
        pass

    @abstractmethod
    def get_by_severity(self, severity: SeverityLevel) -> List[SecurityAlert]:
        """
        Récupère les alertes de sécurité par niveau de sévérité.
        
        Args:
            severity: Le niveau de sévérité à rechercher
            
        Returns:
            List[SecurityAlert]: Liste des alertes de sécurité avec le niveau de sévérité spécifié
        """
        pass

    @abstractmethod
    def get_by_ip(self, ip_address: str) -> List[SecurityAlert]:
        """
        Récupère les alertes de sécurité par adresse IP source.
        
        Args:
            ip_address: L'adresse IP à rechercher
            
        Returns:
            List[SecurityAlert]: Liste des alertes de sécurité avec l'adresse IP spécifiée
        """
        pass

    @abstractmethod
    def get_recent_alerts(self, hours: int = 24) -> List[SecurityAlert]:
        """
        Récupère les alertes de sécurité récentes.
        
        Args:
            hours: Nombre d'heures à considérer (par défaut 24)
            
        Returns:
            List[SecurityAlert]: Liste des alertes de sécurité récentes
        """
        pass

    @abstractmethod
    def save(self, entity: SecurityAlert) -> SecurityAlert:
        """
        Sauvegarde une alerte de sécurité.
        
        Args:
            entity: L'entité à sauvegarder
            
        Returns:
            SecurityAlert: L'entité sauvegardée avec son ID mis à jour
        """
        pass

    @abstractmethod
    def update_status(self, entity_id: EntityId, status: AlertStatus) -> Optional[SecurityAlert]:
        """
        Met à jour le statut d'une alerte de sécurité.
        
        Args:
            entity_id: ID de l'entité à mettre à jour
            status: Nouveau statut
            
        Returns:
            SecurityAlert: L'entité mise à jour ou None si non trouvée
        """
        pass


class CorrelationRuleRepository(ABC):
    """Interface pour le repository des règles de corrélation."""

    @abstractmethod
    def get_by_id(self, entity_id: EntityId) -> Optional[CorrelationRule]:
        """
        Récupère une règle de corrélation par son ID.
        
        Args:
            entity_id: ID de l'entité à récupérer
            
        Returns:
            CorrelationRule: L'entité trouvée ou None si non trouvée
        """
        pass

    @abstractmethod
    def get_all(self) -> List[CorrelationRule]:
        """
        Récupère toutes les règles de corrélation.
        
        Returns:
            List[CorrelationRule]: Liste des règles de corrélation
        """
        pass

    @abstractmethod
    def get_enabled_rules(self) -> List[CorrelationRule]:
        """
        Récupère les règles de corrélation activées.
        
        Returns:
            List[CorrelationRule]: Liste des règles de corrélation activées
        """
        pass

    @abstractmethod
    def save(self, entity: CorrelationRule) -> CorrelationRule:
        """
        Sauvegarde une règle de corrélation.
        
        Args:
            entity: L'entité à sauvegarder
            
        Returns:
            CorrelationRule: L'entité sauvegardée avec son ID mis à jour
        """
        pass

    @abstractmethod
    def delete(self, entity_id: EntityId) -> bool:
        """
        Supprime une règle de corrélation.
        
        Args:
            entity_id: ID de l'entité à supprimer
            
        Returns:
            bool: True si la suppression a réussi, False sinon
        """
        pass


class CorrelationMatchRepository(ABC):
    """Interface pour le repository des correspondances de règles de corrélation."""

    @abstractmethod
    def get_by_id(self, entity_id: EntityId) -> Optional[CorrelationRuleMatch]:
        """
        Récupère une correspondance de règle de corrélation par son ID.
        
        Args:
            entity_id: ID de l'entité à récupérer
            
        Returns:
            CorrelationRuleMatch: L'entité trouvée ou None si non trouvée
        """
        pass

    @abstractmethod
    def get_by_rule_id(self, rule_id: EntityId) -> List[CorrelationRuleMatch]:
        """
        Récupère les correspondances pour une règle de corrélation spécifique.
        
        Args:
            rule_id: ID de la règle de corrélation
            
        Returns:
            List[CorrelationRuleMatch]: Liste des correspondances pour la règle spécifiée
        """
        pass

    @abstractmethod
    def get_recent_matches(self, hours: int = 24) -> List[CorrelationRuleMatch]:
        """
        Récupère les correspondances récentes.
        
        Args:
            hours: Nombre d'heures à considérer (par défaut 24)
            
        Returns:
            List[CorrelationRuleMatch]: Liste des correspondances récentes
        """
        pass

    @abstractmethod
    def save(self, entity: CorrelationRuleMatch) -> CorrelationRuleMatch:
        """
        Sauvegarde une correspondance de règle de corrélation.
        
        Args:
            entity: L'entité à sauvegarder
            
        Returns:
            CorrelationRuleMatch: L'entité sauvegardée avec son ID mis à jour
        """
        pass


class TrafficBaselineRepository(ABC):
    """Interface pour le repository des lignes de base de trafic."""

    @abstractmethod
    def get_by_id(self, entity_id: EntityId) -> Optional[TrafficBaseline]:
        """
        Récupère une ligne de base de trafic par son ID.
        
        Args:
            entity_id: ID de l'entité à récupérer
            
        Returns:
            TrafficBaseline: L'entité trouvée ou None si non trouvée
        """
        pass

    @abstractmethod
    def get_all(self) -> List[TrafficBaseline]:
        """
        Récupère toutes les lignes de base de trafic.
        
        Returns:
            List[TrafficBaseline]: Liste des lignes de base de trafic
        """
        pass

    @abstractmethod
    def get_by_segment(self, network_segment: str) -> List[TrafficBaseline]:
        """
        Récupère les lignes de base de trafic pour un segment réseau spécifique.
        
        Args:
            network_segment: Le segment réseau à rechercher
            
        Returns:
            List[TrafficBaseline]: Liste des lignes de base de trafic pour le segment spécifié
        """
        pass

    @abstractmethod
    def get_by_service(self, service: str) -> List[TrafficBaseline]:
        """
        Récupère les lignes de base de trafic pour un service spécifique.
        
        Args:
            service: Le service à rechercher
            
        Returns:
            List[TrafficBaseline]: Liste des lignes de base de trafic pour le service spécifié
        """
        pass

    @abstractmethod
    def get_learning_baselines(self) -> List[TrafficBaseline]:
        """
        Récupère les lignes de base de trafic en phase d'apprentissage.
        
        Returns:
            List[TrafficBaseline]: Liste des lignes de base de trafic en phase d'apprentissage
        """
        pass

    @abstractmethod
    def save(self, entity: TrafficBaseline) -> TrafficBaseline:
        """
        Sauvegarde une ligne de base de trafic.
        
        Args:
            entity: L'entité à sauvegarder
            
        Returns:
            TrafficBaseline: L'entité sauvegardée avec son ID mis à jour
        """
        pass

    @abstractmethod
    def delete(self, entity_id: EntityId) -> bool:
        """
        Supprime une ligne de base de trafic.
        
        Args:
            entity_id: ID de l'entité à supprimer
            
        Returns:
            bool: True si la suppression a réussi, False sinon
        """
        pass


class AnomalyRepository(ABC):
    """Interface pour le repository des anomalies de trafic."""

    @abstractmethod
    def get_by_id(self, entity_id: EntityId) -> Optional[TrafficAnomaly]:
        """
        Récupère une anomalie de trafic par son ID.
        
        Args:
            entity_id: ID de l'entité à récupérer
            
        Returns:
            TrafficAnomaly: L'entité trouvée ou None si non trouvée
        """
        pass

    @abstractmethod
    def get_by_baseline_id(self, baseline_id: EntityId) -> List[TrafficAnomaly]:
        """
        Récupère les anomalies pour une ligne de base spécifique.
        
        Args:
            baseline_id: ID de la ligne de base
            
        Returns:
            List[TrafficAnomaly]: Liste des anomalies pour la ligne de base spécifiée
        """
        pass

    @abstractmethod
    def get_by_severity(self, severity: SeverityLevel) -> List[TrafficAnomaly]:
        """
        Récupère les anomalies par niveau de sévérité.
        
        Args:
            severity: Le niveau de sévérité à rechercher
            
        Returns:
            List[TrafficAnomaly]: Liste des anomalies avec le niveau de sévérité spécifié
        """
        pass

    @abstractmethod
    def get_recent_anomalies(self, hours: int = 24) -> List[TrafficAnomaly]:
        """
        Récupère les anomalies récentes.
        
        Args:
            hours: Nombre d'heures à considérer (par défaut 24)
            
        Returns:
            List[TrafficAnomaly]: Liste des anomalies récentes
        """
        pass

    @abstractmethod
    def save(self, entity: TrafficAnomaly) -> TrafficAnomaly:
        """
        Sauvegarde une anomalie de trafic.
        
        Args:
            entity: L'entité à sauvegarder
            
        Returns:
            TrafficAnomaly: L'entité sauvegardée avec son ID mis à jour
        """
        pass


class IPReputationRepository(ABC):
    """Interface pour le repository des réputations d'adresses IP."""

    @abstractmethod
    def get_by_id(self, entity_id: EntityId) -> Optional[IPReputation]:
        """
        Récupère une réputation d'adresse IP par son ID.
        
        Args:
            entity_id: ID de l'entité à récupérer
            
        Returns:
            IPReputation: L'entité trouvée ou None si non trouvée
        """
        pass

    @abstractmethod
    def get_by_ip(self, ip_address: str) -> Optional[IPReputation]:
        """
        Récupère une réputation d'adresse IP par son adresse.
        
        Args:
            ip_address: L'adresse IP à rechercher
            
        Returns:
            IPReputation: L'entité trouvée ou None si non trouvée
        """
        pass

    @abstractmethod
    def get_blacklisted_ips(self) -> List[IPReputation]:
        """
        Récupère les adresses IP sur liste noire.
        
        Returns:
            List[IPReputation]: Liste des adresses IP sur liste noire
        """
        pass

    @abstractmethod
    def get_whitelisted_ips(self) -> List[IPReputation]:
        """
        Récupère les adresses IP sur liste blanche.
        
        Returns:
            List[IPReputation]: Liste des adresses IP sur liste blanche
        """
        pass

    @abstractmethod
    def get_by_score_threshold(self, threshold: float, higher: bool = True) -> List[IPReputation]:
        """
        Récupère les adresses IP avec un score de réputation au-dessus ou en-dessous d'un seuil.
        
        Args:
            threshold: Le seuil de score
            higher: True pour récupérer les scores au-dessus du seuil, False pour en-dessous
            
        Returns:
            List[IPReputation]: Liste des adresses IP correspondant au critère
        """
        pass

    @abstractmethod
    def save(self, entity: IPReputation) -> IPReputation:
        """
        Sauvegarde une réputation d'adresse IP.
        
        Args:
            entity: L'entité à sauvegarder
            
        Returns:
            IPReputation: L'entité sauvegardée avec son ID mis à jour
        """
        pass


class SecurityPolicyRepository(ABC):
    """Interface pour le repository des politiques de sécurité."""

    @abstractmethod
    def get_by_id(self, entity_id: EntityId) -> Optional[SecurityPolicy]:
        """
        Récupère une politique de sécurité par son ID.
        
        Args:
            entity_id: ID de l'entité à récupérer
            
        Returns:
            SecurityPolicy: L'entité trouvée ou None si non trouvée
        """
        pass

    @abstractmethod
    def get_all(self) -> List[SecurityPolicy]:
        """
        Récupère toutes les politiques de sécurité.
        
        Returns:
            List[SecurityPolicy]: Liste des politiques de sécurité
        """
        pass

    @abstractmethod
    def get_active_policies(self) -> List[SecurityPolicy]:
        """
        Récupère les politiques de sécurité actives.
        
        Returns:
            List[SecurityPolicy]: Liste des politiques de sécurité actives
        """
        pass

    @abstractmethod
    def save(self, entity: SecurityPolicy) -> SecurityPolicy:
        """
        Sauvegarde une politique de sécurité.
        
        Args:
            entity: L'entité à sauvegarder
            
        Returns:
            SecurityPolicy: L'entité sauvegardée avec son ID mis à jour
        """
        pass

    @abstractmethod
    def delete(self, entity_id: EntityId) -> bool:
        """
        Supprime une politique de sécurité.
        
        Args:
            entity_id: ID de l'entité à supprimer
            
        Returns:
            bool: True si la suppression a réussi, False sinon
        """
        pass


class VulnerabilityRepository(ABC):
    """Interface pour le repository des vulnérabilités."""

    @abstractmethod
    def get_by_id(self, entity_id: EntityId) -> Optional[Vulnerability]:
        """
        Récupère une vulnérabilité par son ID.
        
        Args:
            entity_id: ID de l'entité à récupérer
            
        Returns:
            Vulnerability: L'entité trouvée ou None si non trouvée
        """
        pass

    @abstractmethod
    def get_by_cve_id(self, cve_id: str) -> Optional[Vulnerability]:
        """
        Récupère une vulnérabilité par son CVE ID.
        
        Args:
            cve_id: L'identifiant CVE à rechercher
            
        Returns:
            Vulnerability: L'entité trouvée ou None si non trouvée
        """
        pass

    @abstractmethod
    def get_by_severity(self, severity: str) -> List[Vulnerability]:
        """
        Récupère les vulnérabilités par niveau de sévérité.
        
        Args:
            severity: Le niveau de sévérité à rechercher
            
        Returns:
            List[Vulnerability]: Liste des vulnérabilités correspondantes
        """
        pass

    @abstractmethod
    def get_by_status(self, status: str) -> List[Vulnerability]:
        """
        Récupère les vulnérabilités par statut.
        
        Args:
            status: Le statut à rechercher
            
        Returns:
            List[Vulnerability]: Liste des vulnérabilités correspondantes
        """
        pass

    @abstractmethod
    def get_affecting_system(self, system_name: str) -> List[Vulnerability]:
        """
        Récupère les vulnérabilités affectant un système spécifique.
        
        Args:
            system_name: Le nom du système à rechercher
            
        Returns:
            List[Vulnerability]: Liste des vulnérabilités correspondantes
        """
        pass

    @abstractmethod
    def save(self, entity: Vulnerability) -> Vulnerability:
        """
        Sauvegarde une vulnérabilité.
        
        Args:
            entity: L'entité à sauvegarder
            
        Returns:
            Vulnerability: L'entité sauvegardée avec son ID mis à jour
        """
        pass


class ThreatIntelligenceRepository(ABC):
    """Interface pour le repository des indicateurs de menace."""

    @abstractmethod
    def get_by_id(self, entity_id: EntityId) -> Optional[ThreatIntelligence]:
        """
        Récupère un indicateur de menace par son ID.
        
        Args:
            entity_id: ID de l'entité à récupérer
            
        Returns:
            ThreatIntelligence: L'entité trouvée ou None si non trouvée
        """
        pass

    @abstractmethod
    def get_by_indicator(self, indicator_type: str, indicator_value: str) -> Optional[ThreatIntelligence]:
        """
        Récupère un indicateur de menace par son type et sa valeur.
        
        Args:
            indicator_type: Le type d'indicateur
            indicator_value: La valeur de l'indicateur
            
        Returns:
            ThreatIntelligence: L'entité trouvée ou None si non trouvée
        """
        pass

    @abstractmethod
    def get_active_indicators(self) -> List[ThreatIntelligence]:
        """
        Récupère les indicateurs de menace actifs.
        
        Returns:
            List[ThreatIntelligence]: Liste des indicateurs de menace actifs
        """
        pass

    @abstractmethod
    def get_by_threat_type(self, threat_type: str) -> List[ThreatIntelligence]:
        """
        Récupère les indicateurs de menace par type de menace.
        
        Args:
            threat_type: Le type de menace à rechercher
            
        Returns:
            List[ThreatIntelligence]: Liste des indicateurs de menace correspondants
        """
        pass

    @abstractmethod
    def save(self, entity: ThreatIntelligence) -> ThreatIntelligence:
        """
        Sauvegarde un indicateur de menace.
        
        Args:
            entity: L'entité à sauvegarder
            
        Returns:
            ThreatIntelligence: L'entité sauvegardée avec son ID mis à jour
        """
        pass


class IncidentResponseWorkflowRepository(ABC):
    """Interface pour le repository des workflows de réponse aux incidents."""

    @abstractmethod
    def get_by_id(self, entity_id: EntityId) -> Optional[IncidentResponseWorkflow]:
        """
        Récupère un workflow de réponse aux incidents par son ID.
        
        Args:
            entity_id: ID de l'entité à récupérer
            
        Returns:
            IncidentResponseWorkflow: L'entité trouvée ou None si non trouvée
        """
        pass

    @abstractmethod
    def get_by_status(self, status: str) -> List[IncidentResponseWorkflow]:
        """
        Récupère les workflows de réponse aux incidents par statut.
        
        Args:
            status: Le statut à rechercher
            
        Returns:
            List[IncidentResponseWorkflow]: Liste des workflows correspondants
        """
        pass

    @abstractmethod
    def get_by_trigger_type(self, trigger_type: str) -> List[IncidentResponseWorkflow]:
        """
        Récupère les workflows de réponse aux incidents par type de déclencheur.
        
        Args:
            trigger_type: Le type de déclencheur à rechercher
            
        Returns:
            List[IncidentResponseWorkflow]: Liste des workflows correspondants
        """
        pass

    @abstractmethod
    def save(self, entity: IncidentResponseWorkflow) -> IncidentResponseWorkflow:
        """
        Sauvegarde un workflow de réponse aux incidents.
        
        Args:
            entity: L'entité à sauvegarder
            
        Returns:
            IncidentResponseWorkflow: L'entité sauvegardée avec son ID mis à jour
        """
        pass


class IncidentResponseExecutionRepository(ABC):
    """Interface pour le repository des exécutions de workflows de réponse aux incidents."""

    @abstractmethod
    def get_by_id(self, entity_id: EntityId) -> Optional[IncidentResponseExecution]:
        """
        Récupère une exécution de workflow par son ID.
        
        Args:
            entity_id: ID de l'entité à récupérer
            
        Returns:
            IncidentResponseExecution: L'entité trouvée ou None si non trouvée
        """
        pass

    @abstractmethod
    def get_by_workflow_id(self, workflow_id: EntityId) -> List[IncidentResponseExecution]:
        """
        Récupère les exécutions d'un workflow spécifique.
        
        Args:
            workflow_id: ID du workflow
            
        Returns:
            List[IncidentResponseExecution]: Liste des exécutions correspondantes
        """
        pass

    @abstractmethod
    def get_by_status(self, status: str) -> List[IncidentResponseExecution]:
        """
        Récupère les exécutions par statut.
        
        Args:
            status: Le statut à rechercher
            
        Returns:
            List[IncidentResponseExecution]: Liste des exécutions correspondantes
        """
        pass

    @abstractmethod
    def save(self, entity: IncidentResponseExecution) -> IncidentResponseExecution:
        """
        Sauvegarde une exécution de workflow.
        
        Args:
            entity: L'entité à sauvegarder
            
        Returns:
            IncidentResponseExecution: L'entité sauvegardée avec son ID mis à jour
        """
        pass


class SecurityReportRepository(ABC):
    """Interface pour le repository des rapports de sécurité."""

    @abstractmethod
    def get_by_id(self, entity_id: EntityId) -> Optional[SecurityReport]:
        """
        Récupère un rapport de sécurité par son ID.
        
        Args:
            entity_id: ID de l'entité à récupérer
            
        Returns:
            SecurityReport: L'entité trouvée ou None si non trouvée
        """
        pass

    @abstractmethod
    def get_by_report_type(self, report_type: str) -> List[SecurityReport]:
        """
        Récupère les rapports de sécurité par type.
        
        Args:
            report_type: Le type de rapport à rechercher
            
        Returns:
            List[SecurityReport]: Liste des rapports correspondants
        """
        pass

    @abstractmethod
    def get_scheduled_reports(self) -> List[SecurityReport]:
        """
        Récupère les rapports programmés.
        
        Returns:
            List[SecurityReport]: Liste des rapports programmés
        """
        pass

    @abstractmethod
    def get_pending_reports(self) -> List[SecurityReport]:
        """
        Récupère les rapports en attente d'exécution.
        
        Returns:
            List[SecurityReport]: Liste des rapports en attente
        """
        pass

    @abstractmethod
    def save(self, entity: SecurityReport) -> SecurityReport:
        """
        Sauvegarde un rapport de sécurité.
        
        Args:
            entity: L'entité à sauvegarder
            
        Returns:
            SecurityReport: L'entité sauvegardée avec son ID mis à jour
        """
        pass 