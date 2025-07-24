"""
Cas d utilisation du module security_management.

Ce fichier contient les cas d'utilisation qui définissent les opérations
disponibles pour la gestion de la sécurité.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime

from ..domain.entities import (
    SecurityRule, SecurityAlert, EntityId, 
    RuleType, SeverityLevel, ActionType,
    SecurityPolicy, Vulnerability, ThreatIntelligence,
    IncidentResponseWorkflow, IncidentResponseExecution, SecurityReport
)
from ..domain.services import rule_validator_factory, RuleConflictDetector
from ..domain.exceptions import SecurityRuleValidationException, RuleConflictException


class RuleManagementUseCase:
    """Cas d'utilisation pour la gestion des règles de sécurité."""
    
    def __init__(self, rule_repository, conflict_detector=None):
        """Initialise le cas d'utilisation."""
        self.rule_repository = rule_repository
        self.conflict_detector = conflict_detector or RuleConflictDetector()
    
    def create_rule(self, rule_data: Dict[str, Any]) -> SecurityRule:
        """Crée une nouvelle règle de sécurité."""
        # Créer l'entité de règle à partir des données
        rule = self._create_rule_entity(rule_data)
        
        # Valider la règle
        validator = rule_validator_factory(rule.rule_type)
        is_valid, errors = validator.validate(rule)
        
        if not is_valid:
            raise SecurityRuleValidationException(
                reason="validation_error",
                message="La règle n'est pas valide",
                details=errors
            )
        
        # Vérifier les conflits potentiels
        existing_rules = self.rule_repository.find_all()
        conflicts = self.conflict_detector.detect_conflicts(rule, existing_rules)
        
        if conflicts:
            raise RuleConflictException(
                reason="rule_conflict",
                message="La règle entre en conflit avec des règles existantes",
                conflicts=conflicts
            )
        
        # Sauvegarder et retourner la règle
        return self.rule_repository.save(rule)
    
    def update_rule(self, rule_id: str, rule_data: Dict[str, Any]) -> SecurityRule:
        """Met à jour une règle existante."""
        # Récupérer la règle existante
        existing_rule = self.rule_repository.get_by_id(EntityId(rule_id))
        
        if not existing_rule:
            raise ValueError(f"La règle avec l'ID {rule_id} n'existe pas")
        
        # Mettre à jour les attributs de la règle
        updated_rule = self._update_rule_entity(existing_rule, rule_data)
        
        # Valider la règle
        validator = rule_validator_factory(updated_rule.rule_type)
        is_valid, errors = validator.validate(updated_rule)
        
        if not is_valid:
            raise SecurityRuleValidationException(
                reason="validation_error",
                message="La règle n'est pas valide",
                details=errors
            )
        
        # Sauvegarder et retourner la règle
        return self.rule_repository.save(updated_rule)
    
    def get_rule(self, rule_id: str) -> Optional[SecurityRule]:
        """Récupère une règle par son ID."""
        return self.rule_repository.get_by_id(EntityId(rule_id))
    
    def list_rules(self, filters: Dict[str, Any] = None) -> List[SecurityRule]:
        """Liste les règles selon des filtres optionnels."""
        if filters:
            return self.rule_repository.find_by_criteria(filters)
        else:
            return self.rule_repository.list_all()
    
    def delete_rule(self, rule_id: str) -> bool:
        """Supprime une règle de sécurité."""
        return self.rule_repository.delete(EntityId(rule_id))
    
    def toggle_rule_status(self, rule_id: str, enabled: bool) -> SecurityRule:
        """Active ou désactive une règle de sécurité."""
        rule = self.rule_repository.get_by_id(EntityId(rule_id))
        if not rule:
            raise ValueError(f"La règle avec l'ID {rule_id} n'existe pas")
        
        rule.enabled = enabled
        return self.rule_repository.save(rule)
    
    def _create_rule_entity(self, data: Dict[str, Any]) -> SecurityRule:
        """Crée une entité SecurityRule à partir de données brutes."""
        rule_type_str = data.get("rule_type")
        rule_type = RuleType(rule_type_str) if rule_type_str else None
        
        action_str = data.get("action")
        action = ActionType(action_str) if action_str else None
        
        return SecurityRule(
            id=None,
            name=data.get("name", ""),
            description=data.get("description"),
            rule_type=rule_type,
            content=data.get("content"),
            source_ip=data.get("source_ip"),
            destination_ip=data.get("destination_ip"),
            action=action,
            enabled=data.get("enabled", True)
        )
    
    def _update_rule_entity(self, rule: SecurityRule, data: Dict[str, Any]) -> SecurityRule:
        """Met à jour une entité SecurityRule avec de nouvelles données."""
        if "rule_type" in data:
            rule.rule_type = RuleType(data["rule_type"])
        
        if "action" in data:
            rule.action = ActionType(data["action"]) if data["action"] else None
        
        # Mettre à jour les autres attributs
        rule.name = data.get("name", rule.name)
        rule.description = data.get("description", rule.description)
        rule.content = data.get("content", rule.content)
        rule.source_ip = data.get("source_ip", rule.source_ip)
        rule.destination_ip = data.get("destination_ip", rule.destination_ip)
        rule.enabled = data.get("enabled", rule.enabled)
        
        return rule


class AlertManagementUseCase:
    """Cas d'utilisation pour la gestion des alertes de sécurité."""
    
    def __init__(self, alert_repository):
        """Initialise le cas d'utilisation."""
        self.alert_repository = alert_repository
    
    def create_alert(self, alert_data: Dict[str, Any]) -> SecurityAlert:
        """Crée une nouvelle alerte de sécurité."""
        # Créer l'entité d'alerte à partir des données
        alert = self._create_alert_entity(alert_data)
        
        # Sauvegarder et retourner l'alerte
        return self.alert_repository.save(alert)
    
    def get_alert(self, alert_id: str) -> Optional[SecurityAlert]:
        """Récupère une alerte par son ID."""
        return self.alert_repository.get_by_id(EntityId(alert_id))
    
    def list_alerts(self, filters: Dict[str, Any] = None) -> List[SecurityAlert]:
        """Liste les alertes selon des filtres optionnels."""
        if filters:
            return self.alert_repository.find_by_criteria(filters)
        else:
            return self.alert_repository.list_all()
    
    def mark_as_processed(self, alert_id: str) -> bool:
        """Marque une alerte comme traitée."""
        alert = self.alert_repository.get_by_id(EntityId(alert_id))
        if not alert:
            return False
        alert.status = "processed"
        self.alert_repository.save(alert)
        return True
    
    def mark_as_false_positive(self, alert_id: str) -> bool:
        """Marque une alerte comme faux positif."""
        alert = self.alert_repository.get_by_id(EntityId(alert_id))
        if not alert:
            return False
        alert.status = "false_positive"
        alert.false_positive = True
        self.alert_repository.save(alert)
        return True
    
    def _create_alert_entity(self, data: Dict[str, Any]) -> SecurityAlert:
        """Crée une entité SecurityAlert à partir de données brutes."""
        severity_str = data.get("severity", "medium")
        severity = SeverityLevel(severity_str) if severity_str else SeverityLevel.MEDIUM
        
        source_rule_id = data.get("source_rule_id")
        if source_rule_id:
            source_rule_id = EntityId(source_rule_id)
        
        return SecurityAlert(
            id=None,
            title=data.get("title", ""),
            description=data.get("description"),
            source_ip=data.get("source_ip"),
            destination_ip=data.get("destination_ip"),
            detection_time=data.get("detection_time") or datetime.now(),
            severity=severity,
            status=data.get("status", "new"),
            false_positive=data.get("false_positive", False)
        )


class SecurityPolicyUseCase:
    """Cas d'utilisation pour la gestion des politiques de sécurité."""
    
    def __init__(self, policy_repository):
        """Initialise le cas d'utilisation."""
        self.policy_repository = policy_repository
    
    def create_policy(self, policy_data: Dict[str, Any]) -> SecurityPolicy:
        """Crée une nouvelle politique de sécurité."""
        policy = self._create_policy_entity(policy_data)
        return self.policy_repository.save(policy)
    
    def update_policy(self, policy_id: str, policy_data: Dict[str, Any]) -> SecurityPolicy:
        """Met à jour une politique de sécurité existante."""
        existing_policy = self.policy_repository.get_by_id(EntityId(policy_id))
        
        if not existing_policy:
            raise ValueError(f"La politique avec l'ID {policy_id} n'existe pas")
        
        updated_policy = self._update_policy_entity(existing_policy, policy_data)
        return self.policy_repository.save(updated_policy)
    
    def get_policy(self, policy_id: str) -> Optional[SecurityPolicy]:
        """Récupère une politique par son ID."""
        return self.policy_repository.get_by_id(EntityId(policy_id))
    
    def list_policies(self, active_only: bool = False) -> List[SecurityPolicy]:
        """Liste les politiques de sécurité."""
        if active_only:
            return self.policy_repository.get_active_policies()
        return self.policy_repository.get_all()
    
    def delete_policy(self, policy_id: str) -> bool:
        """Supprime une politique de sécurité."""
        return self.policy_repository.delete(EntityId(policy_id))
    
    def _create_policy_entity(self, data: Dict[str, Any]) -> SecurityPolicy:
        """Crée une entité SecurityPolicy à partir de données brutes."""
        return SecurityPolicy(
            id=None,
            name=data.get("name", ""),
            description=data.get("description"),
            rules=data.get("rules", {}),
            is_active=data.get("is_active", True),
            created_by=data.get("created_by")
        )
    
    def _update_policy_entity(self, policy: SecurityPolicy, data: Dict[str, Any]) -> SecurityPolicy:
        """Met à jour une entité SecurityPolicy avec de nouvelles données."""
        policy.name = data.get("name", policy.name)
        policy.description = data.get("description", policy.description)
        policy.rules = data.get("rules", policy.rules)
        policy.is_active = data.get("is_active", policy.is_active)
        
        return policy


class VulnerabilityManagementUseCase:
    """Cas d'utilisation pour la gestion des vulnérabilités."""
    
    def __init__(self, vulnerability_repository):
        """Initialise le cas d'utilisation."""
        self.vulnerability_repository = vulnerability_repository
    
    def create_vulnerability(self, vuln_data: Dict[str, Any]) -> Vulnerability:
        """Crée une nouvelle vulnérabilité."""
        vulnerability = self._create_vulnerability_entity(vuln_data)
        return self.vulnerability_repository.save(vulnerability)
    
    def update_vulnerability(self, vuln_id: str, vuln_data: Dict[str, Any]) -> Vulnerability:
        """Met à jour une vulnérabilité existante."""
        existing_vuln = self.vulnerability_repository.get_by_id(EntityId(vuln_id))
        
        if not existing_vuln:
            raise ValueError(f"La vulnérabilité avec l'ID {vuln_id} n'existe pas")
        
        updated_vuln = self._update_vulnerability_entity(existing_vuln, vuln_data)
        return self.vulnerability_repository.save(updated_vuln)
    
    def get_vulnerability(self, vuln_id: str) -> Optional[Vulnerability]:
        """Récupère une vulnérabilité par son ID."""
        return self.vulnerability_repository.get_by_id(EntityId(vuln_id))
    
    def get_by_cve(self, cve_id: str) -> Optional[Vulnerability]:
        """Récupère une vulnérabilité par son identifiant CVE."""
        return self.vulnerability_repository.get_by_cve_id(cve_id)
    
    def list_vulnerabilities(self, filters: Dict[str, Any] = None) -> List[Vulnerability]:
        """Liste les vulnérabilités selon des filtres optionnels."""
        if not filters:
            return self.vulnerability_repository.get_all()
            
        if "severity" in filters:
            return self.vulnerability_repository.get_by_severity(filters["severity"])
        
        if "status" in filters:
            return self.vulnerability_repository.get_by_status(filters["status"])
        
        if "system" in filters:
            return self.vulnerability_repository.get_affecting_system(filters["system"])
            
        # Si aucun filtre spécifique n'est reconnu, retourner toutes les vulnérabilités
        return self.vulnerability_repository.get_all()
    
    def _create_vulnerability_entity(self, data: Dict[str, Any]) -> Vulnerability:
        """Crée une entité Vulnerability à partir de données brutes."""
        severity_str = data.get("severity", "medium")
        severity = SeverityLevel(severity_str) if severity_str else SeverityLevel.MEDIUM
        
        return Vulnerability(
            id=None,
            cve_id=data.get("cve_id"),
            title=data.get("title", ""),
            description=data.get("description", ""),
            severity=severity,
            cvss_score=data.get("cvss_score"),
            cvss_vector=data.get("cvss_vector"),
            cwe_id=data.get("cwe_id"),
            affected_systems=data.get("affected_systems", []),
            affected_software=data.get("affected_software"),
            affected_versions=data.get("affected_versions"),
            status=data.get("status", "identified"),
            discovered_date=data.get("discovered_date"),
            published_date=data.get("published_date"),
            patched_date=data.get("patched_date"),
            references=data.get("references", []),
            patch_available=data.get("patch_available", False),
            patch_info=data.get("patch_info", {}),
            assigned_to=data.get("assigned_to"),
            priority=data.get("priority", 3)
        )
    
    def _update_vulnerability_entity(self, vuln: Vulnerability, data: Dict[str, Any]) -> Vulnerability:
        """Met à jour une entité Vulnerability avec de nouvelles données."""
        if "severity" in data:
            severity_str = data["severity"]
            vuln.severity = SeverityLevel(severity_str) if severity_str else vuln.severity
        
        vuln.title = data.get("title", vuln.title)
        vuln.description = data.get("description", vuln.description)
        vuln.cvss_score = data.get("cvss_score", vuln.cvss_score)
        vuln.cvss_vector = data.get("cvss_vector", vuln.cvss_vector)
        vuln.affected_systems = data.get("affected_systems", vuln.affected_systems)
        vuln.status = data.get("status", vuln.status)
        vuln.patch_available = data.get("patch_available", vuln.patch_available)
        vuln.patch_info = data.get("patch_info", vuln.patch_info)
        vuln.assigned_to = data.get("assigned_to", vuln.assigned_to)
        vuln.priority = data.get("priority", vuln.priority)
        
        if "patched_date" in data:
            vuln.patched_date = data["patched_date"]
        
        return vuln


class ThreatIntelligenceUseCase:
    """Cas d'utilisation pour la gestion des indicateurs de menace."""
    
    def __init__(self, threat_repository):
        """Initialise le cas d'utilisation."""
        self.threat_repository = threat_repository
    
    def create_indicator(self, indicator_data: Dict[str, Any]) -> ThreatIntelligence:
        """Crée un nouvel indicateur de menace."""
        indicator = self._create_indicator_entity(indicator_data)
        return self.threat_repository.save(indicator)
    
    def update_indicator(self, indicator_id: str, indicator_data: Dict[str, Any]) -> ThreatIntelligence:
        """Met à jour un indicateur de menace existant."""
        existing_indicator = self.threat_repository.get_by_id(EntityId(indicator_id))
        
        if not existing_indicator:
            raise ValueError(f"L'indicateur avec l'ID {indicator_id} n'existe pas")
        
        updated_indicator = self._update_indicator_entity(existing_indicator, indicator_data)
        return self.threat_repository.save(updated_indicator)
    
    def get_indicator(self, indicator_id: str) -> Optional[ThreatIntelligence]:
        """Récupère un indicateur par son ID."""
        return self.threat_repository.get_by_id(EntityId(indicator_id))
    
    def get_by_value(self, indicator_type: str, value: str) -> Optional[ThreatIntelligence]:
        """Récupère un indicateur par son type et sa valeur."""
        return self.threat_repository.get_by_indicator(indicator_type, value)
    
    def list_indicators(self, filters: Dict[str, Any] = None) -> List[ThreatIntelligence]:
        """Liste les indicateurs selon des filtres optionnels."""
        if not filters:
            return self.threat_repository.get_active_indicators()
            
        if "threat_type" in filters:
            return self.threat_repository.get_by_threat_type(filters["threat_type"])
        
        # Par défaut, retourner les indicateurs actifs
        return self.threat_repository.get_active_indicators()
    
    def _create_indicator_entity(self, data: Dict[str, Any]) -> ThreatIntelligence:
        """Crée une entité ThreatIntelligence à partir de données brutes."""
        severity_str = data.get("severity", "medium")
        severity = SeverityLevel(severity_str) if severity_str else SeverityLevel.MEDIUM
        
        return ThreatIntelligence(
            id=None,
            indicator_type=data.get("indicator_type", ""),
            indicator_value=data.get("indicator_value", ""),
            threat_type=data.get("threat_type", ""),
            confidence=data.get("confidence", 0.5),
            severity=severity,
            title=data.get("title"),
            description=data.get("description"),
            tags=data.get("tags", []),
            source=data.get("source"),
            source_reliability=data.get("source_reliability", "medium"),
            external_id=data.get("external_id"),
            valid_until=data.get("valid_until"),
            is_active=data.get("is_active", True),
            is_whitelisted=data.get("is_whitelisted", False),
            context=data.get("context", {})
        )
    
    def _update_indicator_entity(self, indicator: ThreatIntelligence, data: Dict[str, Any]) -> ThreatIntelligence:
        """Met à jour une entité ThreatIntelligence avec de nouvelles données."""
        if "severity" in data:
            severity_str = data["severity"]
            indicator.severity = SeverityLevel(severity_str) if severity_str else indicator.severity
        
        indicator.title = data.get("title", indicator.title)
        indicator.description = data.get("description", indicator.description)
        indicator.confidence = data.get("confidence", indicator.confidence)
        indicator.tags = data.get("tags", indicator.tags)
        indicator.source_reliability = data.get("source_reliability", indicator.source_reliability)
        indicator.valid_until = data.get("valid_until", indicator.valid_until)
        indicator.is_active = data.get("is_active", indicator.is_active)
        indicator.is_whitelisted = data.get("is_whitelisted", indicator.is_whitelisted)
        indicator.context = data.get("context", indicator.context)
        
        # Mettre à jour la date de dernière observation
        indicator.last_seen = datetime.now()
        
        return indicator


class IncidentResponseWorkflowUseCase:
    """Cas d'utilisation pour la gestion des workflows de réponse aux incidents."""
    
    def __init__(self, workflow_repository, execution_repository=None):
        """Initialise le cas d'utilisation."""
        self.workflow_repository = workflow_repository
        self.execution_repository = execution_repository
    
    def create_workflow(self, workflow_data: Dict[str, Any]) -> IncidentResponseWorkflow:
        """Crée un nouveau workflow de réponse aux incidents."""
        workflow = self._create_workflow_entity(workflow_data)
        return self.workflow_repository.save(workflow)
    
    def update_workflow(self, workflow_id: str, workflow_data: Dict[str, Any]) -> IncidentResponseWorkflow:
        """Met à jour un workflow existant."""
        existing_workflow = self.workflow_repository.get_by_id(EntityId(workflow_id))
        
        if not existing_workflow:
            raise ValueError(f"Le workflow avec l'ID {workflow_id} n'existe pas")
        
        updated_workflow = self._update_workflow_entity(existing_workflow, workflow_data)
        return self.workflow_repository.save(updated_workflow)
    
    def get_workflow(self, workflow_id: str) -> Optional[IncidentResponseWorkflow]:
        """Récupère un workflow par son ID."""
        return self.workflow_repository.get_by_id(EntityId(workflow_id))
    
    def list_workflows(self, filters: Dict[str, Any] = None) -> List[IncidentResponseWorkflow]:
        """Liste les workflows selon des filtres optionnels."""
        if not filters:
            return self.workflow_repository.get_all()
            
        if "status" in filters:
            return self.workflow_repository.get_by_status(filters["status"])
        
        if "trigger_type" in filters:
            return self.workflow_repository.get_by_trigger_type(filters["trigger_type"])
        
        # Par défaut, retourner tous les workflows
        return self.workflow_repository.get_all()
    
    def execute_workflow(self, workflow_id: str, trigger_data: Dict[str, Any]) -> Optional[IncidentResponseExecution]:
        """Exécute un workflow de réponse aux incidents."""
        if not self.execution_repository:
            raise ValueError("Le repository d'exécution n'est pas configuré")
        
        workflow = self.workflow_repository.get_by_id(EntityId(workflow_id))
        if not workflow:
            raise ValueError(f"Le workflow avec l'ID {workflow_id} n'existe pas")
        
        # Créer une nouvelle exécution
        execution = IncidentResponseExecution(
            workflow_id=workflow.id,
            status="pending",
            triggered_by_event=trigger_data,
            started_at=datetime.now()
        )
        
        # Sauvegarder l'exécution
        saved_execution = self.execution_repository.save(execution)
        
        # Mettre à jour les compteurs du workflow
        workflow.execution_count += 1
        workflow.last_executed = datetime.now()
        self.workflow_repository.save(workflow)
        
        return saved_execution
    
    def _create_workflow_entity(self, data: Dict[str, Any]) -> IncidentResponseWorkflow:
        """Crée une entité IncidentResponseWorkflow à partir de données brutes."""
        return IncidentResponseWorkflow(
            id=None,
            name=data.get("name", ""),
            description=data.get("description"),
            version=data.get("version", "1.0"),
            trigger_type=data.get("trigger_type", ""),
            trigger_conditions=data.get("trigger_conditions", {}),
            steps=data.get("steps", []),
            auto_execute=data.get("auto_execute", False),
            requires_approval=data.get("requires_approval", True),
            timeout_minutes=data.get("timeout_minutes", 60),
            assigned_team=data.get("assigned_team"),
            escalation_rules=data.get("escalation_rules", {}),
            status=data.get("status", "draft"),
            created_by=data.get("created_by")
        )
    
    def _update_workflow_entity(self, workflow: IncidentResponseWorkflow, data: Dict[str, Any]) -> IncidentResponseWorkflow:
        """Met à jour une entité IncidentResponseWorkflow avec de nouvelles données."""
        workflow.name = data.get("name", workflow.name)
        workflow.description = data.get("description", workflow.description)
        workflow.version = data.get("version", workflow.version)
        workflow.trigger_type = data.get("trigger_type", workflow.trigger_type)
        workflow.trigger_conditions = data.get("trigger_conditions", workflow.trigger_conditions)
        workflow.steps = data.get("steps", workflow.steps)
        workflow.auto_execute = data.get("auto_execute", workflow.auto_execute)
        workflow.requires_approval = data.get("requires_approval", workflow.requires_approval)
        workflow.timeout_minutes = data.get("timeout_minutes", workflow.timeout_minutes)
        workflow.assigned_team = data.get("assigned_team", workflow.assigned_team)
        workflow.escalation_rules = data.get("escalation_rules", workflow.escalation_rules)
        workflow.status = data.get("status", workflow.status)
        
        return workflow


class SecurityReportUseCase:
    """Cas d'utilisation pour la gestion des rapports de sécurité."""
    
    def __init__(self, report_repository):
        """Initialise le cas d'utilisation."""
        self.report_repository = report_repository
    
    def create_report(self, report_data: Dict[str, Any]) -> SecurityReport:
        """Crée un nouveau rapport de sécurité."""
        report = self._create_report_entity(report_data)
        return self.report_repository.save(report)
    
    def update_report(self, report_id: str, report_data: Dict[str, Any]) -> SecurityReport:
        """Met à jour un rapport existant."""
        existing_report = self.report_repository.get_by_id(EntityId(report_id))
        
        if not existing_report:
            raise ValueError(f"Le rapport avec l'ID {report_id} n'existe pas")
        
        updated_report = self._update_report_entity(existing_report, report_data)
        return self.report_repository.save(updated_report)
    
    def get_report(self, report_id: str) -> Optional[SecurityReport]:
        """Récupère un rapport par son ID."""
        return self.report_repository.get_by_id(EntityId(report_id))
    
    def list_reports(self, filters: Dict[str, Any] = None) -> List[SecurityReport]:
        """Liste les rapports selon des filtres optionnels."""
        if not filters:
            return self.report_repository.get_all()
            
        if "report_type" in filters:
            return self.report_repository.get_by_report_type(filters["report_type"])
        
        if filters.get("scheduled_only", False):
            return self.report_repository.get_scheduled_reports()
        
        if filters.get("pending_only", False):
            return self.report_repository.get_pending_reports()
        
        # Par défaut, retourner tous les rapports
        return self.report_repository.get_all()
    
    def _create_report_entity(self, data: Dict[str, Any]) -> SecurityReport:
        """Crée une entité SecurityReport à partir de données brutes."""
        return SecurityReport(
            id=None,
            name=data.get("name", ""),
            report_type=data.get("report_type", ""),
            description=data.get("description"),
            parameters=data.get("parameters", {}),
            filters=data.get("filters", {}),
            format=data.get("format", "pdf"),
            is_scheduled=data.get("is_scheduled", False),
            schedule_frequency=data.get("schedule_frequency"),
            next_execution=data.get("next_execution"),
            status=data.get("status", "scheduled"),
            created_by=data.get("created_by"),
            recipients=data.get("recipients", []),
            auto_send=data.get("auto_send", False)
        )
    
    def _update_report_entity(self, report: SecurityReport, data: Dict[str, Any]) -> SecurityReport:
        """Met à jour une entité SecurityReport avec de nouvelles données."""
        report.name = data.get("name", report.name)
        report.description = data.get("description", report.description)
        report.parameters = data.get("parameters", report.parameters)
        report.filters = data.get("filters", report.filters)
        report.format = data.get("format", report.format)
        report.is_scheduled = data.get("is_scheduled", report.is_scheduled)
        report.schedule_frequency = data.get("schedule_frequency", report.schedule_frequency)
        report.next_execution = data.get("next_execution", report.next_execution)
        report.status = data.get("status", report.status)
        report.recipients = data.get("recipients", report.recipients)
        report.auto_send = data.get("auto_send", report.auto_send)
        
        return report
 