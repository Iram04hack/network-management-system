"""
Tests pour les cas d'utilisation du module security_management.
"""

import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta

from django.test import TestCase

from ..domain.entities import (
    SecurityPolicy, Vulnerability, ThreatIntelligence,
    IncidentResponseWorkflow, IncidentResponseExecution, SecurityReport,
    SeverityLevel, EntityId
)
from ..application.use_cases import (
    SecurityPolicyUseCase,
    VulnerabilityManagementUseCase,
    ThreatIntelligenceUseCase,
    IncidentResponseWorkflowUseCase,
    SecurityReportUseCase
)


class TestSecurityPolicyUseCase(TestCase):
    """Tests pour le cas d'utilisation SecurityPolicyUseCase."""
    
    def setUp(self):
        """Initialise les données de test."""
        self.repository = MagicMock()
        self.use_case = SecurityPolicyUseCase(self.repository)
        
        # Créer une politique de test
        self.test_policy = SecurityPolicy(
            id=EntityId(1),
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
        
    def test_create_policy(self):
        """Teste la création d'une politique."""
        # Configurer le mock
        self.repository.save.return_value = self.test_policy
        
        # Données pour la création
        policy_data = {
            "name": "Test Policy",
            "description": "Test description",
            "rules": {
                "password": {
                    "min_length": 8,
                    "require_uppercase": True
                }
            },
            "is_active": True,
            "created_by": "test-user"
        }
        
        # Appeler la méthode à tester
        result = self.use_case.create_policy(policy_data)
        
        # Vérifier les résultats
        self.repository.save.assert_called_once()
        self.assertEqual(result.name, "Test Policy")
        self.assertEqual(result.rules["password"]["min_length"], 8)
        
    def test_update_policy(self):
        """Teste la mise à jour d'une politique."""
        # Configurer les mocks
        self.repository.get_by_id.return_value = self.test_policy
        
        updated_policy = SecurityPolicy(
            id=EntityId(1),
            name="Updated Policy",
            description="Updated description",
            rules={
                "password": {
                    "min_length": 10,
                    "require_uppercase": True
                }
            },
            is_active=True,
            created_by="test-user"
        )
        self.repository.save.return_value = updated_policy
        
        # Données pour la mise à jour
        update_data = {
            "name": "Updated Policy",
            "description": "Updated description",
            "rules": {
                "password": {
                    "min_length": 10,
                    "require_uppercase": True
                }
            }
        }
        
        # Appeler la méthode à tester
        result = self.use_case.update_policy("1", update_data)
        
        # Vérifier les résultats
        self.repository.get_by_id.assert_called_once()
        self.repository.save.assert_called_once()
        self.assertEqual(result.name, "Updated Policy")
        self.assertEqual(result.rules["password"]["min_length"], 10)
        
    def test_get_policy(self):
        """Teste la récupération d'une politique."""
        # Configurer le mock
        self.repository.get_by_id.return_value = self.test_policy
        
        # Appeler la méthode à tester
        result = self.use_case.get_policy("1")
        
        # Vérifier les résultats
        self.repository.get_by_id.assert_called_once()
        self.assertEqual(result.name, "Test Policy")
        
    def test_list_policies(self):
        """Teste la liste des politiques."""
        # Configurer les mocks
        self.repository.get_all.return_value = [self.test_policy]
        self.repository.get_active_policies.return_value = [self.test_policy]
        
        # Appeler les méthodes à tester
        all_policies = self.use_case.list_policies()
        active_policies = self.use_case.list_policies(active_only=True)
        
        # Vérifier les résultats
        self.repository.get_all.assert_called_once()
        self.repository.get_active_policies.assert_called_once()
        self.assertEqual(len(all_policies), 1)
        self.assertEqual(len(active_policies), 1)
        
    def test_delete_policy(self):
        """Teste la suppression d'une politique."""
        # Configurer le mock
        self.repository.delete.return_value = True
        
        # Appeler la méthode à tester
        result = self.use_case.delete_policy("1")
        
        # Vérifier les résultats
        self.repository.delete.assert_called_once()
        self.assertTrue(result)


class TestVulnerabilityManagementUseCase(TestCase):
    """Tests pour le cas d'utilisation VulnerabilityManagementUseCase."""
    
    def setUp(self):
        """Initialise les données de test."""
        self.repository = MagicMock()
        self.use_case = VulnerabilityManagementUseCase(self.repository)
        
        # Créer une vulnérabilité de test
        self.test_vuln = Vulnerability(
            id=EntityId(1),
            cve_id="CVE-2023-12345",
            title="Test Vulnerability",
            description="A test vulnerability",
            severity=SeverityLevel.HIGH,
            cvss_score=7.5,
            status="identified",
            affected_systems=["server-1", "server-2"],
            priority=2
        )
        
    def test_create_vulnerability(self):
        """Teste la création d'une vulnérabilité."""
        # Configurer le mock
        self.repository.save.return_value = self.test_vuln
        
        # Données pour la création
        vuln_data = {
            "cve_id": "CVE-2023-12345",
            "title": "Test Vulnerability",
            "description": "A test vulnerability",
            "severity": "high",
            "cvss_score": 7.5,
            "status": "identified",
            "affected_systems": ["server-1", "server-2"],
            "priority": 2
        }
        
        # Appeler la méthode à tester
        result = self.use_case.create_vulnerability(vuln_data)
        
        # Vérifier les résultats
        self.repository.save.assert_called_once()
        self.assertEqual(result.title, "Test Vulnerability")
        self.assertEqual(result.cve_id, "CVE-2023-12345")
        
    def test_update_vulnerability(self):
        """Teste la mise à jour d'une vulnérabilité."""
        # Configurer les mocks
        self.repository.get_by_id.return_value = self.test_vuln
        
        updated_vuln = Vulnerability(
            id=EntityId(1),
            cve_id="CVE-2023-12345",
            title="Updated Vulnerability",
            description="An updated vulnerability",
            severity=SeverityLevel.CRITICAL,
            cvss_score=9.5,
            status="confirmed",
            affected_systems=["server-1", "server-2", "server-3"],
            priority=1
        )
        self.repository.save.return_value = updated_vuln
        
        # Données pour la mise à jour
        update_data = {
            "title": "Updated Vulnerability",
            "description": "An updated vulnerability",
            "severity": "critical",
            "cvss_score": 9.5,
            "status": "confirmed",
            "affected_systems": ["server-1", "server-2", "server-3"],
            "priority": 1
        }
        
        # Appeler la méthode à tester
        result = self.use_case.update_vulnerability("1", update_data)
        
        # Vérifier les résultats
        self.repository.get_by_id.assert_called_once()
        self.repository.save.assert_called_once()
        self.assertEqual(result.title, "Updated Vulnerability")
        self.assertEqual(result.status, "confirmed")
        
    def test_get_vulnerability(self):
        """Teste la récupération d'une vulnérabilité par ID."""
        # Configurer le mock
        self.repository.get_by_id.return_value = self.test_vuln
        
        # Appeler la méthode à tester
        result = self.use_case.get_vulnerability("1")
        
        # Vérifier les résultats
        self.repository.get_by_id.assert_called_once()
        self.assertEqual(result.title, "Test Vulnerability")
        
    def test_get_by_cve(self):
        """Teste la récupération d'une vulnérabilité par CVE ID."""
        # Configurer le mock
        self.repository.get_by_cve_id.return_value = self.test_vuln
        
        # Appeler la méthode à tester
        result = self.use_case.get_by_cve("CVE-2023-12345")
        
        # Vérifier les résultats
        self.repository.get_by_cve_id.assert_called_once_with("CVE-2023-12345")
        self.assertEqual(result.title, "Test Vulnerability")
        
    def test_list_vulnerabilities(self):
        """Teste la liste des vulnérabilités avec différents filtres."""
        # Configurer les mocks
        self.repository.get_all.return_value = [self.test_vuln]
        self.repository.get_by_severity.return_value = [self.test_vuln]
        self.repository.get_by_status.return_value = [self.test_vuln]
        self.repository.get_affecting_system.return_value = [self.test_vuln]
        
        # Appeler les méthodes à tester
        all_vulns = self.use_case.list_vulnerabilities()
        severity_vulns = self.use_case.list_vulnerabilities({"severity": "high"})
        status_vulns = self.use_case.list_vulnerabilities({"status": "identified"})
        system_vulns = self.use_case.list_vulnerabilities({"system": "server-1"})
        
        # Vérifier les résultats
        self.repository.get_all.assert_called_once()
        self.repository.get_by_severity.assert_called_once_with("high")
        self.repository.get_by_status.assert_called_once_with("identified")
        self.repository.get_affecting_system.assert_called_once_with("server-1")
        
        self.assertEqual(len(all_vulns), 1)
        self.assertEqual(len(severity_vulns), 1)
        self.assertEqual(len(status_vulns), 1)
        self.assertEqual(len(system_vulns), 1)


class TestThreatIntelligenceUseCase(TestCase):
    """Tests pour le cas d'utilisation ThreatIntelligenceUseCase."""
    
    def setUp(self):
        """Initialise les données de test."""
        self.repository = MagicMock()
        self.use_case = ThreatIntelligenceUseCase(self.repository)
        
        # Créer un indicateur de test
        self.test_indicator = ThreatIntelligence(
            id=EntityId(1),
            indicator_type="ip",
            indicator_value="192.168.1.100",
            threat_type="malware",
            confidence=0.8,
            severity=SeverityLevel.HIGH,
            title="Test Threat Intel",
            source="test-source",
            tags=["test", "malware"],
            is_active=True
        )
        
    def test_create_indicator(self):
        """Teste la création d'un indicateur de menace."""
        # Configurer le mock
        self.repository.save.return_value = self.test_indicator
        
        # Données pour la création
        indicator_data = {
            "indicator_type": "ip",
            "indicator_value": "192.168.1.100",
            "threat_type": "malware",
            "confidence": 0.8,
            "severity": "high",
            "title": "Test Threat Intel",
            "source": "test-source",
            "tags": ["test", "malware"]
        }
        
        # Appeler la méthode à tester
        result = self.use_case.create_indicator(indicator_data)
        
        # Vérifier les résultats
        self.repository.save.assert_called_once()
        self.assertEqual(result.indicator_value, "192.168.1.100")
        self.assertEqual(result.threat_type, "malware")
        
    def test_update_indicator(self):
        """Teste la mise à jour d'un indicateur de menace."""
        # Configurer les mocks
        self.repository.get_by_id.return_value = self.test_indicator
        
        updated_indicator = ThreatIntelligence(
            id=EntityId(1),
            indicator_type="ip",
            indicator_value="192.168.1.100",
            threat_type="malware",
            confidence=0.9,
            severity=SeverityLevel.CRITICAL,
            title="Updated Threat Intel",
            source="test-source",
            tags=["test", "malware", "updated"],
            is_active=True
        )
        self.repository.save.return_value = updated_indicator
        
        # Données pour la mise à jour
        update_data = {
            "title": "Updated Threat Intel",
            "confidence": 0.9,
            "severity": "critical",
            "tags": ["test", "malware", "updated"]
        }
        
        # Appeler la méthode à tester
        result = self.use_case.update_indicator("1", update_data)
        
        # Vérifier les résultats
        self.repository.get_by_id.assert_called_once()
        self.repository.save.assert_called_once()
        self.assertEqual(result.title, "Updated Threat Intel")
        self.assertEqual(result.confidence, 0.9)
        
    def test_get_indicator(self):
        """Teste la récupération d'un indicateur par ID."""
        # Configurer le mock
        self.repository.get_by_id.return_value = self.test_indicator
        
        # Appeler la méthode à tester
        result = self.use_case.get_indicator("1")
        
        # Vérifier les résultats
        self.repository.get_by_id.assert_called_once()
        self.assertEqual(result.indicator_value, "192.168.1.100")
        
    def test_get_by_value(self):
        """Teste la récupération d'un indicateur par type et valeur."""
        # Configurer le mock
        self.repository.get_by_indicator.return_value = self.test_indicator
        
        # Appeler la méthode à tester
        result = self.use_case.get_by_value("ip", "192.168.1.100")
        
        # Vérifier les résultats
        self.repository.get_by_indicator.assert_called_once_with("ip", "192.168.1.100")
        self.assertEqual(result.title, "Test Threat Intel")
        
    def test_list_indicators(self):
        """Teste la liste des indicateurs avec différents filtres."""
        # Configurer les mocks
        self.repository.get_active_indicators.return_value = [self.test_indicator]
        self.repository.get_by_threat_type.return_value = [self.test_indicator]
        
        # Appeler les méthodes à tester
        active_indicators = self.use_case.list_indicators()
        threat_type_indicators = self.use_case.list_indicators({"threat_type": "malware"})
        
        # Vérifier les résultats
        self.repository.get_active_indicators.assert_called_once()
        self.repository.get_by_threat_type.assert_called_once_with("malware")
        
        self.assertEqual(len(active_indicators), 1)
        self.assertEqual(len(threat_type_indicators), 1)


class TestIncidentResponseWorkflowUseCase(TestCase):
    """Tests pour le cas d'utilisation IncidentResponseWorkflowUseCase."""
    
    def setUp(self):
        """Initialise les données de test."""
        self.workflow_repository = MagicMock()
        self.execution_repository = MagicMock()
        self.use_case = IncidentResponseWorkflowUseCase(
            self.workflow_repository,
            self.execution_repository
        )
        
        # Créer un workflow de test
        self.test_workflow = IncidentResponseWorkflow(
            id=EntityId(1),
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
        
        # Créer une exécution de test
        self.test_execution = IncidentResponseExecution(
            id=EntityId(1),
            workflow_id=EntityId(1),
            status="pending",
            started_at=datetime.now()
        )
        
    def test_create_workflow(self):
        """Teste la création d'un workflow."""
        # Configurer le mock
        self.workflow_repository.save.return_value = self.test_workflow
        
        # Données pour la création
        workflow_data = {
            "name": "Test Workflow",
            "description": "A test workflow",
            "version": "1.0",
            "trigger_type": "alert_severity",
            "trigger_conditions": {"severity": "high"},
            "steps": [
                {"id": 1, "name": "Step 1", "action": "test_action"}
            ],
            "status": "active"
        }
        
        # Appeler la méthode à tester
        result = self.use_case.create_workflow(workflow_data)
        
        # Vérifier les résultats
        self.workflow_repository.save.assert_called_once()
        self.assertEqual(result.name, "Test Workflow")
        self.assertEqual(result.trigger_type, "alert_severity")
        
    def test_update_workflow(self):
        """Teste la mise à jour d'un workflow."""
        # Configurer les mocks
        self.workflow_repository.get_by_id.return_value = self.test_workflow
        
        updated_workflow = IncidentResponseWorkflow(
            id=EntityId(1),
            name="Updated Workflow",
            description="An updated workflow",
            version="1.1",
            trigger_type="alert_severity",
            trigger_conditions={"severity": "critical"},
            steps=[
                {"id": 1, "name": "Updated Step", "action": "updated_action"}
            ],
            status="active"
        )
        self.workflow_repository.save.return_value = updated_workflow
        
        # Données pour la mise à jour
        update_data = {
            "name": "Updated Workflow",
            "description": "An updated workflow",
            "version": "1.1",
            "trigger_conditions": {"severity": "critical"},
            "steps": [
                {"id": 1, "name": "Updated Step", "action": "updated_action"}
            ]
        }
        
        # Appeler la méthode à tester
        result = self.use_case.update_workflow("1", update_data)
        
        # Vérifier les résultats
        self.workflow_repository.get_by_id.assert_called_once()
        self.workflow_repository.save.assert_called_once()
        self.assertEqual(result.name, "Updated Workflow")
        self.assertEqual(result.version, "1.1")
        
    def test_get_workflow(self):
        """Teste la récupération d'un workflow par ID."""
        # Configurer le mock
        self.workflow_repository.get_by_id.return_value = self.test_workflow
        
        # Appeler la méthode à tester
        result = self.use_case.get_workflow("1")
        
        # Vérifier les résultats
        self.workflow_repository.get_by_id.assert_called_once()
        self.assertEqual(result.name, "Test Workflow")
        
    def test_list_workflows(self):
        """Teste la liste des workflows avec différents filtres."""
        # Configurer les mocks
        self.workflow_repository.get_all.return_value = [self.test_workflow]
        self.workflow_repository.get_by_status.return_value = [self.test_workflow]
        self.workflow_repository.get_by_trigger_type.return_value = [self.test_workflow]
        
        # Appeler les méthodes à tester
        all_workflows = self.use_case.list_workflows()
        status_workflows = self.use_case.list_workflows({"status": "active"})
        trigger_workflows = self.use_case.list_workflows({"trigger_type": "alert_severity"})
        
        # Vérifier les résultats
        self.workflow_repository.get_all.assert_called_once()
        self.workflow_repository.get_by_status.assert_called_once_with("active")
        self.workflow_repository.get_by_trigger_type.assert_called_once_with("alert_severity")
        
        self.assertEqual(len(all_workflows), 1)
        self.assertEqual(len(status_workflows), 1)
        self.assertEqual(len(trigger_workflows), 1)
        
    def test_execute_workflow(self):
        """Teste l'exécution d'un workflow."""
        # Configurer les mocks
        self.workflow_repository.get_by_id.return_value = self.test_workflow
        self.execution_repository.save.return_value = self.test_execution
        
        # Données pour le déclenchement
        trigger_data = {
            "alert_id": "123",
            "severity": "high"
        }
        
        # Appeler la méthode à tester
        result = self.use_case.execute_workflow("1", trigger_data)
        
        # Vérifier les résultats
        self.workflow_repository.get_by_id.assert_called_once()
        self.execution_repository.save.assert_called_once()
        self.workflow_repository.save.assert_called_once()
        self.assertEqual(result.status, "pending")
        self.assertEqual(result.workflow_id, EntityId(1))


class TestSecurityReportUseCase(TestCase):
    """Tests pour le cas d'utilisation SecurityReportUseCase."""
    
    def setUp(self):
        """Initialise les données de test."""
        self.repository = MagicMock()
        self.use_case = SecurityReportUseCase(self.repository)
        
        # Créer un rapport de test
        self.test_report = SecurityReport(
            id=EntityId(1),
            name="Test Report",
            report_type="vulnerability",
            parameters={"period": "weekly"},
            filters={"severity": ["high", "critical"]},
            format="pdf",
            status="scheduled",
            next_execution=datetime.now() + timedelta(days=7)
        )
        
    def test_create_report(self):
        """Teste la création d'un rapport."""
        # Configurer le mock
        self.repository.save.return_value = self.test_report
        
        # Données pour la création
        report_data = {
            "name": "Test Report",
            "report_type": "vulnerability",
            "parameters": {"period": "weekly"},
            "filters": {"severity": ["high", "critical"]},
            "format": "pdf",
            "status": "scheduled",
            "next_execution": datetime.now() + timedelta(days=7)
        }
        
        # Appeler la méthode à tester
        result = self.use_case.create_report(report_data)
        
        # Vérifier les résultats
        self.repository.save.assert_called_once()
        self.assertEqual(result.name, "Test Report")
        self.assertEqual(result.report_type, "vulnerability")
        
    def test_update_report(self):
        """Teste la mise à jour d'un rapport."""
        # Configurer les mocks
        self.repository.get_by_id.return_value = self.test_report
        
        updated_report = SecurityReport(
            id=EntityId(1),
            name="Updated Report",
            report_type="vulnerability",
            parameters={"period": "monthly"},
            filters={"severity": ["critical"]},
            format="html",
            status="scheduled",
            next_execution=datetime.now() + timedelta(days=30)
        )
        self.repository.save.return_value = updated_report
        
        # Données pour la mise à jour
        update_data = {
            "name": "Updated Report",
            "parameters": {"period": "monthly"},
            "filters": {"severity": ["critical"]},
            "format": "html",
            "next_execution": datetime.now() + timedelta(days=30)
        }
        
        # Appeler la méthode à tester
        result = self.use_case.update_report("1", update_data)
        
        # Vérifier les résultats
        self.repository.get_by_id.assert_called_once()
        self.repository.save.assert_called_once()
        self.assertEqual(result.name, "Updated Report")
        self.assertEqual(result.format, "html")
        
    def test_get_report(self):
        """Teste la récupération d'un rapport par ID."""
        # Configurer le mock
        self.repository.get_by_id.return_value = self.test_report
        
        # Appeler la méthode à tester
        result = self.use_case.get_report("1")
        
        # Vérifier les résultats
        self.repository.get_by_id.assert_called_once()
        self.assertEqual(result.name, "Test Report")
        
    def test_list_reports(self):
        """Teste la liste des rapports avec différents filtres."""
        # Configurer les mocks
        self.repository.get_all.return_value = [self.test_report]
        self.repository.get_by_report_type.return_value = [self.test_report]
        self.repository.get_scheduled_reports.return_value = [self.test_report]
        self.repository.get_pending_reports.return_value = [self.test_report]
        
        # Appeler les méthodes à tester
        all_reports = self.use_case.list_reports()
        type_reports = self.use_case.list_reports({"report_type": "vulnerability"})
        scheduled_reports = self.use_case.list_reports({"scheduled_only": True})
        pending_reports = self.use_case.list_reports({"pending_only": True})
        
        # Vérifier les résultats
        self.repository.get_all.assert_called_once()
        self.repository.get_by_report_type.assert_called_once_with("vulnerability")
        self.repository.get_scheduled_reports.assert_called_once()
        self.repository.get_pending_reports.assert_called_once()
        
        self.assertEqual(len(all_reports), 1)
        self.assertEqual(len(type_reports), 1)
        self.assertEqual(len(scheduled_reports), 1)
        self.assertEqual(len(pending_reports), 1)


if __name__ == '__main__':
    unittest.main() 