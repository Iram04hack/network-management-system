"""
Tests pour les entités de domaine du module security_management.
"""

import unittest
from datetime import datetime, timedelta
from uuid import uuid4

from ..domain.entities import (
    SecurityPolicy, Vulnerability, ThreatIntelligence, 
    IncidentResponseWorkflow, IncidentResponseExecution, SecurityReport,
    SeverityLevel, EntityId
)


class TestSecurityPolicyEntity(unittest.TestCase):
    """Tests pour l'entité SecurityPolicy."""

    def setUp(self):
        """Initialise les données de test."""
        self.policy = SecurityPolicy(
            id=EntityId(str(uuid4())),
            name="Politique de mots de passe",
            description="Définit les règles pour les mots de passe",
            rules={
                "password": {
                    "min_length": 8,
                    "require_uppercase": True,
                    "require_lowercase": True,
                    "require_numbers": True,
                    "require_special": True
                }
            },
            is_active=True,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            created_by="admin"
        )

    def test_validate_password_success(self):
        """Teste la validation d'un mot de passe valide."""
        valid_password = "Passw0rd!"
        self.assertTrue(self.policy.validate_password(valid_password))

    def test_validate_password_too_short(self):
        """Teste la validation d'un mot de passe trop court."""
        short_password = "Pw0rd!"
        self.assertFalse(self.policy.validate_password(short_password))

    def test_validate_password_no_uppercase(self):
        """Teste la validation d'un mot de passe sans majuscule."""
        no_upper_password = "passw0rd!"
        self.assertFalse(self.policy.validate_password(no_upper_password))

    def test_validate_password_no_lowercase(self):
        """Teste la validation d'un mot de passe sans minuscule."""
        no_lower_password = "PASSW0RD!"
        self.assertFalse(self.policy.validate_password(no_lower_password))

    def test_validate_password_no_number(self):
        """Teste la validation d'un mot de passe sans chiffre."""
        no_number_password = "Password!"
        self.assertFalse(self.policy.validate_password(no_number_password))

    def test_validate_password_no_special(self):
        """Teste la validation d'un mot de passe sans caractère spécial."""
        no_special_password = "Passw0rd"
        self.assertFalse(self.policy.validate_password(no_special_password))


class TestVulnerabilityEntity(unittest.TestCase):
    """Tests pour l'entité Vulnerability."""

    def setUp(self):
        """Initialise les données de test."""
        self.vulnerability = Vulnerability(
            id=EntityId(str(uuid4())),
            cve_id="CVE-2023-12345",
            title="Vulnérabilité XSS dans l'application web",
            description="Une vulnérabilité XSS a été découverte dans le formulaire de contact",
            severity=SeverityLevel.HIGH,
            cvss_score=7.5,
            cvss_vector="CVSS:3.1/AV:N/AC:L/PR:N/UI:R/S:U/C:H/I:H/A:H",
            cwe_id="CWE-79",
            affected_systems=["web-server-01", "web-server-02"],
            affected_software="WebApp v1.2.3",
            affected_versions="1.0.0 - 1.2.3",
            status="confirmed",
            discovered_date=datetime.now() - timedelta(days=5),
            published_date=datetime.now() - timedelta(days=2),
            patch_available=True,
            patch_info={"version": "1.2.4", "url": "https://example.com/patch"},
            priority=2
        )

    def test_get_exploitability_score_with_patch(self):
        """Teste le calcul du score d'exploitabilité avec patch disponible."""
        # Avec un patch disponible, le score devrait être réduit
        expected_score = self.vulnerability.cvss_score * 0.8
        self.assertEqual(self.vulnerability.get_exploitability_score(), expected_score)

    def test_get_exploitability_score_many_systems(self):
        """Teste le calcul du score d'exploitabilité avec beaucoup de systèmes affectés."""
        # Créer une vulnérabilité avec beaucoup de systèmes affectés
        self.vulnerability.affected_systems = [f"system-{i}" for i in range(15)]
        self.vulnerability.patch_available = False
        
        # Sans patch et avec beaucoup de systèmes, le score devrait être augmenté
        expected_score = self.vulnerability.cvss_score * 1.2
        self.assertEqual(self.vulnerability.get_exploitability_score(), expected_score)

    def test_get_exploitability_score_max_cap(self):
        """Teste que le score d'exploitabilité est plafonné à 10."""
        # Créer une vulnérabilité avec un score CVSS élevé
        self.vulnerability.cvss_score = 9.5
        self.vulnerability.affected_systems = [f"system-{i}" for i in range(15)]
        self.vulnerability.patch_available = False
        
        # Le score calculé serait 9.5 * 1.2 = 11.4, mais devrait être plafonné à 10
        self.assertEqual(self.vulnerability.get_exploitability_score(), 10.0)


class TestThreatIntelligenceEntity(unittest.TestCase):
    """Tests pour l'entité ThreatIntelligence."""

    def setUp(self):
        """Initialise les données de test."""
        self.now = datetime.now()
        self.threat_intel = ThreatIntelligence(
            id=EntityId(str(uuid4())),
            indicator_type="ip",
            indicator_value="192.168.1.100",
            threat_type="malware",
            confidence=0.8,
            severity=SeverityLevel.HIGH,
            title="Indicateur de C&C Emotet",
            description="Adresse IP associée à l'infrastructure C&C d'Emotet",
            tags=["emotet", "c2", "malware"],
            source="threatfeed",
            source_reliability="high",
            external_id="TF-123456",
            first_seen=self.now - timedelta(days=10),
            last_seen=self.now - timedelta(days=1),
            valid_until=self.now + timedelta(days=30),
            is_active=True
        )

    def test_is_expired_not_expired(self):
        """Teste qu'un indicateur non expiré est correctement identifié."""
        self.assertFalse(self.threat_intel.is_expired())

    def test_is_expired_expired(self):
        """Teste qu'un indicateur expiré est correctement identifié."""
        self.threat_intel.valid_until = datetime.now() - timedelta(days=1)
        self.assertTrue(self.threat_intel.is_expired())

    def test_is_expired_no_expiry(self):
        """Teste qu'un indicateur sans date d'expiration n'expire pas."""
        self.threat_intel.valid_until = None
        self.assertFalse(self.threat_intel.is_expired())

    def test_post_init_sets_dates(self):
        """Teste que __post_init__ initialise correctement les dates."""
        # Créer un nouvel indicateur sans dates
        new_threat = ThreatIntelligence(
            indicator_type="domain",
            indicator_value="malicious.example.com",
            threat_type="phishing"
        )
        
        # Vérifier que les dates ont été initialisées
        self.assertIsNotNone(new_threat.first_seen)
        self.assertIsNotNone(new_threat.last_seen)


class TestIncidentResponseWorkflowEntity(unittest.TestCase):
    """Tests pour l'entité IncidentResponseWorkflow."""

    def setUp(self):
        """Initialise les données de test."""
        self.workflow = IncidentResponseWorkflow(
            id=EntityId(str(uuid4())),
            name="Réponse aux attaques DDoS",
            description="Workflow pour répondre aux attaques DDoS",
            version="1.0",
            trigger_type="alert_severity",
            trigger_conditions={"severity": "high", "category": "ddos"},
            steps=[
                {"id": 1, "name": "Isoler le système", "action": "isolate", "params": {"target": "{{affected_system}}"}},
                {"id": 2, "name": "Notifier l'équipe", "action": "notify", "params": {"team": "security", "message": "Attaque DDoS détectée"}}
            ],
            auto_execute=False,
            requires_approval=True,
            timeout_minutes=120,
            assigned_team="security-ops",
            execution_count=10,
            success_count=8
        )

    def test_get_success_rate(self):
        """Teste le calcul du taux de réussite."""
        expected_rate = 8 / 10
        self.assertEqual(self.workflow.get_success_rate(), expected_rate)

    def test_get_success_rate_no_executions(self):
        """Teste le calcul du taux de réussite sans exécutions."""
        self.workflow.execution_count = 0
        self.workflow.success_count = 0
        self.assertEqual(self.workflow.get_success_rate(), 0.0)

    def test_post_init_sets_dates(self):
        """Teste que __post_init__ initialise correctement les dates."""
        # Créer un nouveau workflow sans dates
        new_workflow = IncidentResponseWorkflow(
            name="Nouveau workflow",
            trigger_type="manual"
        )
        
        # Vérifier que les dates ont été initialisées
        self.assertIsNotNone(new_workflow.created_at)
        self.assertIsNotNone(new_workflow.updated_at)


class TestIncidentResponseExecutionEntity(unittest.TestCase):
    """Tests pour l'entité IncidentResponseExecution."""

    def setUp(self):
        """Initialise les données de test."""
        self.workflow_id = EntityId(str(uuid4()))
        self.alert_id = EntityId(str(uuid4()))
        self.start_time = datetime.now() - timedelta(minutes=30)
        
        self.execution = IncidentResponseExecution(
            id=EntityId(str(uuid4())),
            workflow_id=self.workflow_id,
            triggered_by_alert_id=self.alert_id,
            triggered_by_event={"alert_id": str(self.alert_id), "severity": "high"},
            status="running",
            started_at=self.start_time,
            current_step=1,
            steps_log=[
                {"step_id": 1, "name": "Isoler le système", "status": "completed", "start_time": self.start_time.isoformat(), "end_time": (self.start_time + timedelta(minutes=5)).isoformat()}
            ],
            assigned_to="security-analyst"
        )

    def test_get_duration_not_completed(self):
        """Teste que la durée est None pour une exécution non terminée."""
        self.assertIsNone(self.execution.get_duration())

    def test_get_duration_completed(self):
        """Teste le calcul de la durée pour une exécution terminée."""
        # Terminer l'exécution
        complete_time = self.start_time + timedelta(minutes=45)
        self.execution.status = "completed"
        self.execution.completed_at = complete_time
        
        # Calculer la durée attendue en secondes
        expected_duration = (complete_time - self.start_time).total_seconds()
        self.assertEqual(self.execution.get_duration(), expected_duration)

    def test_complete_success(self):
        """Teste la méthode complete avec succès."""
        output_data = {"result": "success", "actions_taken": ["system_isolated", "team_notified"]}
        
        self.execution.complete(success=True, output_data=output_data)
        
        self.assertEqual(self.execution.status, "completed")
        self.assertIsNotNone(self.execution.completed_at)
        self.assertEqual(self.execution.output_data, output_data)
        self.assertIsNone(self.execution.error_message)

    def test_complete_failure(self):
        """Teste la méthode complete avec échec."""
        error_message = "Impossible d'isoler le système: timeout"
        
        self.execution.complete(success=False, error_message=error_message)
        
        self.assertEqual(self.execution.status, "failed")
        self.assertIsNotNone(self.execution.completed_at)
        self.assertEqual(self.execution.error_message, error_message)

    def test_post_init_sets_start_time(self):
        """Teste que __post_init__ initialise correctement la date de début."""
        # Créer une nouvelle exécution sans date de début
        new_execution = IncidentResponseExecution(
            workflow_id=self.workflow_id,
            status="pending"
        )
        
        # Vérifier que la date de début a été initialisée
        self.assertIsNotNone(new_execution.started_at)


class TestSecurityReportEntity(unittest.TestCase):
    """Tests pour l'entité SecurityReport."""

    def setUp(self):
        """Initialise les données de test."""
        self.report = SecurityReport(
            id=EntityId(str(uuid4())),
            name="Rapport mensuel de vulnérabilités",
            report_type="vulnerability",
            description="Rapport détaillant les vulnérabilités découvertes ce mois-ci",
            parameters={"period": "monthly", "include_patched": True},
            filters={"severity": ["critical", "high"]},
            format="pdf",
            is_scheduled=True,
            schedule_frequency="monthly",
            next_execution=datetime.now() + timedelta(days=30),
            status="scheduled",
            created_by="security-admin",
            recipients=["security@example.com", "ciso@example.com"],
            auto_send=True
        )

    def test_post_init_sets_created_at(self):
        """Teste que __post_init__ initialise correctement la date de création."""
        # Créer un nouveau rapport sans date de création
        new_report = SecurityReport(
            name="Nouveau rapport",
            report_type="custom"
        )
        
        # Vérifier que la date de création a été initialisée
        self.assertIsNotNone(new_report.created_at)


if __name__ == '__main__':
    unittest.main() 