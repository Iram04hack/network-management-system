"""
Tests pour les repositories du module security_management.
"""

import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta
from uuid import uuid4

from django.test import TestCase

from ..domain.entities import (
    SecurityPolicy, Vulnerability, ThreatIntelligence,
    IncidentResponseWorkflow, IncidentResponseExecution, SecurityReport,
    SeverityLevel, EntityId
)
from ..infrastructure.repositories import (
    DjangoSecurityPolicyRepository, DjangoVulnerabilityRepository,
    DjangoThreatIntelligenceRepository, DjangoIncidentResponseWorkflowRepository,
    DjangoIncidentResponseExecutionRepository, DjangoSecurityReportRepository
)
from ..infrastructure.models import (
    SecurityPolicyModel, VulnerabilityModel, ThreatIntelligenceModel,
    IncidentResponseWorkflowModel, IncidentResponseExecutionModel, SecurityReportModel
)


class TestDjangoSecurityPolicyRepository(TestCase):
    """Tests pour le repository DjangoSecurityPolicyRepository."""
    
    def setUp(self):
        """Initialise les données de test."""
        self.repository = DjangoSecurityPolicyRepository()
        
        # Créer une politique de sécurité pour les tests
        self.policy_model = SecurityPolicyModel.objects.create(
            name="Test Policy",
            description="Test description",
            rules={
                "password": {
                    "min_length": 8,
                    "require_uppercase": True
                }
            },
            is_active=True,
            created_by="test-user"
        )
        
    def test_get_by_id(self):
        """Teste la récupération d'une politique par ID."""
        policy = self.repository.get_by_id(self.policy_model.id)
        
        self.assertIsInstance(policy, SecurityPolicy)
        self.assertEqual(policy.id, EntityId(self.policy_model.id))
        self.assertEqual(policy.name, self.policy_model.name)
        self.assertEqual(policy.rules, self.policy_model.rules)
        
    def test_get_all(self):
        """Teste la récupération de toutes les politiques."""
        # Créer une deuxième politique
        SecurityPolicyModel.objects.create(
            name="Second Policy",
            description="Another test policy",
            rules={"access": {"max_attempts": 3}},
            is_active=True
        )
        
        policies = self.repository.get_all()
        
        self.assertEqual(len(policies), 2)
        self.assertIsInstance(policies[0], SecurityPolicy)
        
    def test_get_active_policies(self):
        """Teste la récupération des politiques actives."""
        # Créer une politique inactive
        SecurityPolicyModel.objects.create(
            name="Inactive Policy",
            description="An inactive policy",
            rules={},
            is_active=False
        )
        
        active_policies = self.repository.get_active_policies()
        
        self.assertEqual(len(active_policies), 1)
        self.assertEqual(active_policies[0].name, "Test Policy")
        
    def test_save_new_policy(self):
        """Teste la sauvegarde d'une nouvelle politique."""
        new_policy = SecurityPolicy(
            name="New Policy",
            description="A new security policy",
            rules={"network": {"allow_external": False}},
            is_active=True,
            created_by="admin"
        )
        
        saved_policy = self.repository.save(new_policy)
        
        self.assertIsNotNone(saved_policy.id)
        self.assertEqual(saved_policy.name, "New Policy")
        
        # Vérifier que la politique a bien été sauvegardée en base
        self.assertEqual(SecurityPolicyModel.objects.count(), 2)
        
    def test_save_existing_policy(self):
        """Teste la mise à jour d'une politique existante."""
        policy = self.repository.get_by_id(self.policy_model.id)
        policy.name = "Updated Policy"
        policy.rules["password"]["min_length"] = 10
        
        updated_policy = self.repository.save(policy)
        
        self.assertEqual(updated_policy.name, "Updated Policy")
        self.assertEqual(updated_policy.rules["password"]["min_length"], 10)
        
        # Vérifier que la politique a bien été mise à jour en base
        db_policy = SecurityPolicyModel.objects.get(id=self.policy_model.id)
        self.assertEqual(db_policy.name, "Updated Policy")
        self.assertEqual(db_policy.rules["password"]["min_length"], 10)
        
    def test_delete(self):
        """Teste la suppression d'une politique."""
        self.repository.delete(EntityId(self.policy_model.id))
        
        # Vérifier que la politique a bien été supprimée
        self.assertEqual(SecurityPolicyModel.objects.count(), 0)


class TestDjangoVulnerabilityRepository(TestCase):
    """Tests pour le repository DjangoVulnerabilityRepository."""
    
    def setUp(self):
        """Initialise les données de test."""
        self.repository = DjangoVulnerabilityRepository()
        
        # Créer une vulnérabilité pour les tests
        self.vuln_model = VulnerabilityModel.objects.create(
            cve_id="CVE-2023-12345",
            title="Test Vulnerability",
            description="A test vulnerability",
            severity="high",
            cvss_score=7.5,
            status="identified",
            affected_systems=["server-1", "server-2"],
            priority=2
        )
        
    def test_get_by_id(self):
        """Teste la récupération d'une vulnérabilité par ID."""
        vuln = self.repository.get_by_id(self.vuln_model.id)
        
        self.assertIsInstance(vuln, Vulnerability)
        self.assertEqual(vuln.id, EntityId(self.vuln_model.id))
        self.assertEqual(vuln.cve_id, self.vuln_model.cve_id)
        self.assertEqual(vuln.title, self.vuln_model.title)
        
    def test_get_by_cve_id(self):
        """Teste la récupération d'une vulnérabilité par CVE ID."""
        vuln = self.repository.get_by_cve_id("CVE-2023-12345")
        
        self.assertIsNotNone(vuln)
        self.assertEqual(vuln.title, "Test Vulnerability")
        
    def test_get_by_severity(self):
        """Teste la récupération des vulnérabilités par niveau de sévérité."""
        # Créer une autre vulnérabilité avec une sévérité différente
        VulnerabilityModel.objects.create(
            title="Low Severity Vuln",
            description="A low severity vulnerability",
            severity="low",
            status="identified"
        )
        
        high_vulns = self.repository.get_by_severity("high")
        
        self.assertEqual(len(high_vulns), 1)
        self.assertEqual(high_vulns[0].title, "Test Vulnerability")
        
    def test_get_by_status(self):
        """Teste la récupération des vulnérabilités par statut."""
        # Créer une vulnérabilité avec un statut différent
        VulnerabilityModel.objects.create(
            title="Patched Vuln",
            description="A patched vulnerability",
            severity="medium",
            status="patched"
        )
        
        identified_vulns = self.repository.get_by_status("identified")
        
        self.assertEqual(len(identified_vulns), 1)
        self.assertEqual(identified_vulns[0].title, "Test Vulnerability")
        
    def test_save_new_vulnerability(self):
        """Teste la sauvegarde d'une nouvelle vulnérabilité."""
        new_vuln = Vulnerability(
            cve_id="CVE-2023-67890",
            title="New Vulnerability",
            description="A new vulnerability",
            severity=SeverityLevel.CRITICAL,
            status="confirmed"
        )
        
        saved_vuln = self.repository.save(new_vuln)
        
        self.assertIsNotNone(saved_vuln.id)
        self.assertEqual(saved_vuln.title, "New Vulnerability")
        
        # Vérifier que la vulnérabilité a bien été sauvegardée en base
        self.assertEqual(VulnerabilityModel.objects.count(), 2)
        
    def test_get_affecting_system(self):
        """Teste la récupération des vulnérabilités affectant un système spécifique."""
        vulns = self.repository.get_affecting_system("server-1")
        
        self.assertEqual(len(vulns), 1)
        self.assertEqual(vulns[0].title, "Test Vulnerability")
        
        # Vérifier avec un système non affecté
        vulns = self.repository.get_affecting_system("non-existent-server")
        self.assertEqual(len(vulns), 0)


class TestDjangoThreatIntelligenceRepository(TestCase):
    """Tests pour le repository DjangoThreatIntelligenceRepository."""
    
    def setUp(self):
        """Initialise les données de test."""
        self.repository = DjangoThreatIntelligenceRepository()
        
        # Créer un indicateur de menace pour les tests
        self.threat_model = ThreatIntelligenceModel.objects.create(
            indicator_type="ip",
            indicator_value="192.168.1.100",
            threat_type="malware",
            confidence=0.8,
            severity="high",
            title="Test Threat Intel",
            source="test-source",
            tags=["test", "malware"],
            is_active=True
        )
        
    def test_get_by_id(self):
        """Teste la récupération d'un indicateur par ID."""
        threat = self.repository.get_by_id(self.threat_model.id)
        
        self.assertIsInstance(threat, ThreatIntelligence)
        self.assertEqual(threat.id, EntityId(self.threat_model.id))
        self.assertEqual(threat.indicator_value, self.threat_model.indicator_value)
        
    def test_get_by_indicator(self):
        """Teste la récupération d'un indicateur par type et valeur."""
        threat = self.repository.get_by_indicator("ip", "192.168.1.100")
        
        self.assertIsNotNone(threat)
        self.assertEqual(threat.title, "Test Threat Intel")
        
    def test_get_active_indicators(self):
        """Teste la récupération des indicateurs actifs."""
        # Créer un indicateur inactif
        ThreatIntelligenceModel.objects.create(
            indicator_type="domain",
            indicator_value="inactive.example.com",
            threat_type="phishing",
            is_active=False
        )
        
        active_threats = self.repository.get_active_indicators()
        
        self.assertEqual(len(active_threats), 1)
        self.assertEqual(active_threats[0].indicator_value, "192.168.1.100")
        
    def test_get_by_threat_type(self):
        """Teste la récupération des indicateurs par type de menace."""
        # Créer un indicateur avec un type différent
        ThreatIntelligenceModel.objects.create(
            indicator_type="url",
            indicator_value="http://malicious.example.com",
            threat_type="phishing",
            is_active=True
        )
        
        malware_threats = self.repository.get_by_threat_type("malware")
        
        self.assertEqual(len(malware_threats), 1)
        self.assertEqual(malware_threats[0].indicator_value, "192.168.1.100")
        
    def test_save_new_indicator(self):
        """Teste la sauvegarde d'un nouvel indicateur."""
        new_threat = ThreatIntelligence(
            indicator_type="domain",
            indicator_value="malicious.example.com",
            threat_type="c2",
            confidence=0.9,
            severity=SeverityLevel.CRITICAL,
            title="New Threat Intel",
            is_active=True
        )
        
        saved_threat = self.repository.save(new_threat)
        
        self.assertIsNotNone(saved_threat.id)
        self.assertEqual(saved_threat.indicator_value, "malicious.example.com")
        
        # Vérifier que l'indicateur a bien été sauvegardé en base
        self.assertEqual(ThreatIntelligenceModel.objects.count(), 2)


class TestDjangoIncidentResponseWorkflowRepository(TestCase):
    """Tests pour le repository DjangoIncidentResponseWorkflowRepository."""
    
    def setUp(self):
        """Initialise les données de test."""
        self.repository = DjangoIncidentResponseWorkflowRepository()
        
        # Créer un workflow pour les tests
        self.workflow_model = IncidentResponseWorkflowModel.objects.create(
            name="Test Workflow",
            description="A test workflow",
            version="1.0",
            trigger_type="alert_severity",
            trigger_conditions={"severity": "high"},
            steps=[
                {"id": 1, "name": "Step 1", "action": "test_action"}
            ],
            status="active"
        )
        
    def test_get_by_id(self):
        """Teste la récupération d'un workflow par ID."""
        workflow = self.repository.get_by_id(self.workflow_model.id)
        
        self.assertIsInstance(workflow, IncidentResponseWorkflow)
        self.assertEqual(workflow.id, EntityId(self.workflow_model.id))
        self.assertEqual(workflow.name, self.workflow_model.name)
        
    def test_get_by_status(self):
        """Teste la récupération des workflows par statut."""
        # Créer un workflow avec un statut différent
        IncidentResponseWorkflowModel.objects.create(
            name="Draft Workflow",
            trigger_type="manual",
            steps=[],
            status="draft"
        )
        
        active_workflows = self.repository.get_by_status("active")
        
        self.assertEqual(len(active_workflows), 1)
        self.assertEqual(active_workflows[0].name, "Test Workflow")
        
    def test_get_by_trigger_type(self):
        """Teste la récupération des workflows par type de déclencheur."""
        # Créer un workflow avec un type de déclencheur différent
        IncidentResponseWorkflowModel.objects.create(
            name="Manual Workflow",
            trigger_type="manual",
            steps=[],
            status="active"
        )
        
        alert_workflows = self.repository.get_by_trigger_type("alert_severity")
        
        self.assertEqual(len(alert_workflows), 1)
        self.assertEqual(alert_workflows[0].name, "Test Workflow")
        
    def test_save_new_workflow(self):
        """Teste la sauvegarde d'un nouveau workflow."""
        new_workflow = IncidentResponseWorkflow(
            name="New Workflow",
            description="A new workflow",
            version="1.0",
            trigger_type="correlation_rule",
            steps=[
                {"id": 1, "name": "New Step", "action": "new_action"}
            ],
            status="draft"
        )
        
        saved_workflow = self.repository.save(new_workflow)
        
        self.assertIsNotNone(saved_workflow.id)
        self.assertEqual(saved_workflow.name, "New Workflow")
        
        # Vérifier que le workflow a bien été sauvegardé en base
        self.assertEqual(IncidentResponseWorkflowModel.objects.count(), 2)


class TestDjangoIncidentResponseExecutionRepository(TestCase):
    """Tests pour le repository DjangoIncidentResponseExecutionRepository."""
    
    def setUp(self):
        """Initialise les données de test."""
        self.repository = DjangoIncidentResponseExecutionRepository()
        
        # Créer un workflow pour les tests
        self.workflow_model = IncidentResponseWorkflowModel.objects.create(
            name="Test Workflow",
            trigger_type="alert_severity",
            steps=[]
        )
        
        # Créer une exécution pour les tests
        self.execution_model = IncidentResponseExecutionModel.objects.create(
            workflow=self.workflow_model,
            status="running",
            current_step=1,
            steps_log=[{"step_id": 1, "status": "running"}]
        )
        
    def test_get_by_id(self):
        """Teste la récupération d'une exécution par ID."""
        execution = self.repository.get_by_id(self.execution_model.id)
        
        self.assertIsInstance(execution, IncidentResponseExecution)
        self.assertEqual(execution.id, EntityId(self.execution_model.id))
        self.assertEqual(execution.status, self.execution_model.status)
        
    def test_get_by_workflow_id(self):
        """Teste la récupération des exécutions par ID de workflow."""
        executions = self.repository.get_by_workflow_id(EntityId(self.workflow_model.id))
        
        self.assertEqual(len(executions), 1)
        self.assertEqual(executions[0].id, EntityId(self.execution_model.id))
        
    def test_get_by_status(self):
        """Teste la récupération des exécutions par statut."""
        # Créer une exécution avec un statut différent
        IncidentResponseExecutionModel.objects.create(
            workflow=self.workflow_model,
            status="completed",
            current_step=2,
            steps_log=[{"step_id": 1, "status": "completed"}, {"step_id": 2, "status": "completed"}],
            completed_at=datetime.now()
        )
        
        running_executions = self.repository.get_by_status("running")
        
        self.assertEqual(len(running_executions), 1)
        self.assertEqual(running_executions[0].id, EntityId(self.execution_model.id))
        
    def test_save_new_execution(self):
        """Teste la sauvegarde d'une nouvelle exécution."""
        new_execution = IncidentResponseExecution(
            workflow_id=EntityId(self.workflow_model.id),
            status="pending",
            current_step=0,
            steps_log=[]
        )
        
        saved_execution = self.repository.save(new_execution)
        
        self.assertIsNotNone(saved_execution.id)
        self.assertEqual(saved_execution.status, "pending")
        
        # Vérifier que l'exécution a bien été sauvegardée en base
        self.assertEqual(IncidentResponseExecutionModel.objects.count(), 2)
        
    def test_update_execution_status(self):
        """Teste la mise à jour du statut d'une exécution."""
        execution = self.repository.get_by_id(self.execution_model.id)
        execution.status = "completed"
        execution.completed_at = datetime.now()
        
        updated_execution = self.repository.save(execution)
        
        self.assertEqual(updated_execution.status, "completed")
        self.assertIsNotNone(updated_execution.completed_at)
        
        # Vérifier que l'exécution a bien été mise à jour en base
        db_execution = IncidentResponseExecutionModel.objects.get(id=self.execution_model.id)
        self.assertEqual(db_execution.status, "completed")


class TestDjangoSecurityReportRepository(TestCase):
    """Tests pour le repository DjangoSecurityReportRepository."""
    
    def setUp(self):
        """Initialise les données de test."""
        self.repository = DjangoSecurityReportRepository()
        
        # Créer un rapport pour les tests
        self.report_model = SecurityReportModel.objects.create(
            name="Test Report",
            report_type="vulnerability",
            parameters={"period": "weekly"},
            filters={"severity": ["high", "critical"]},
            format="pdf",
            status="scheduled",
            next_execution=datetime.now() + timedelta(days=7)
        )
        
    def test_get_by_id(self):
        """Teste la récupération d'un rapport par ID."""
        report = self.repository.get_by_id(self.report_model.id)
        
        self.assertIsInstance(report, SecurityReport)
        self.assertEqual(report.id, EntityId(self.report_model.id))
        self.assertEqual(report.name, self.report_model.name)
        
    def test_get_by_report_type(self):
        """Teste la récupération des rapports par type."""
        # Créer un rapport avec un type différent
        SecurityReportModel.objects.create(
            name="Alert Report",
            report_type="alert_summary",
            format="pdf",
            status="scheduled"
        )
        
        vuln_reports = self.repository.get_by_report_type("vulnerability")
        
        self.assertEqual(len(vuln_reports), 1)
        self.assertEqual(vuln_reports[0].name, "Test Report")
        
    def test_get_scheduled_reports(self):
        """Teste la récupération des rapports programmés."""
        # Créer un rapport non programmé
        SecurityReportModel.objects.create(
            name="On-demand Report",
            report_type="custom",
            format="pdf",
            status="completed",
            is_scheduled=False
        )
        
        scheduled_reports = self.repository.get_scheduled_reports()
        
        self.assertEqual(len(scheduled_reports), 1)
        self.assertEqual(scheduled_reports[0].name, "Test Report")
        
    def test_get_pending_reports(self):
        """Teste la récupération des rapports en attente d'exécution."""
        # Créer un rapport avec une date d'exécution passée
        SecurityReportModel.objects.create(
            name="Past Report",
            report_type="vulnerability",
            format="pdf",
            status="scheduled",
            is_scheduled=True,
            next_execution=datetime.now() - timedelta(days=1)
        )
        
        pending_reports = self.repository.get_pending_reports()
        
        self.assertEqual(len(pending_reports), 1)
        self.assertTrue(pending_reports[0].next_execution > datetime.now())
        
    def test_save_new_report(self):
        """Teste la sauvegarde d'un nouveau rapport."""
        new_report = SecurityReport(
            name="New Report",
            report_type="compliance",
            parameters={"standard": "ISO27001"},
            format="html",
            status="scheduled"
        )
        
        saved_report = self.repository.save(new_report)
        
        self.assertIsNotNone(saved_report.id)
        self.assertEqual(saved_report.name, "New Report")
        
        # Vérifier que le rapport a bien été sauvegardé en base
        self.assertEqual(SecurityReportModel.objects.count(), 2)
        
    def test_update_report_status(self):
        """Teste la mise à jour du statut d'un rapport."""
        report = self.repository.get_by_id(self.report_model.id)
        report.status = "generating"
        
        updated_report = self.repository.save(report)
        
        self.assertEqual(updated_report.status, "generating")
        
        # Vérifier que le rapport a bien été mis à jour en base
        db_report = SecurityReportModel.objects.get(id=self.report_model.id)
        self.assertEqual(db_report.status, "generating")


if __name__ == '__main__':
    unittest.main() 