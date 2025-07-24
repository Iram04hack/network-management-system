"""
Tests pour les entités du domaine.

Ce module contient les tests unitaires pour les entités du module reporting.
"""

import unittest
from datetime import datetime
import pytest

from reporting.domain.entities import (
    Report, ReportTemplate, ScheduledReport, 
    ReportType, ReportStatus, ReportFormat, Frequency
)

class TestReportEntity(unittest.TestCase):
    """Tests pour l'entité Report."""
    
    def test_creation_valid_report(self):
        """Teste la création d'un rapport valide."""
        report = Report(
            title="Test Report",
            report_type=ReportType.NETWORK
        )
        self.assertEqual(report.title, "Test Report")
        self.assertEqual(report.report_type, ReportType.NETWORK)
        self.assertEqual(report.status, ReportStatus.DRAFT)
    
    def test_creation_invalid_report_without_title(self):
        """Teste la création d'un rapport sans titre (doit échouer)."""
        with self.assertRaises(ValueError):
            Report(
                title="",
                report_type=ReportType.NETWORK
            )
    
    def test_creation_invalid_report_with_long_title(self):
        """Teste la création d'un rapport avec un titre trop long (doit échouer)."""
        with self.assertRaises(ValueError):
            Report(
                title="x" * 256,  # Dépasse la limite de 255 caractères
                report_type=ReportType.NETWORK
            )
    
    def test_creation_invalid_report_type(self):
        """Teste la création d'un rapport avec un type invalide (doit échouer)."""
        with self.assertRaises(ValueError):
            Report(
                title="Test Report",
                report_type="invalid_type"  # Type non valide (pas une instance de ReportType)
            )
    
    def test_mark_as_processing(self):
        """Teste le changement de statut vers 'processing'."""
        report = Report(
            title="Test Report",
            report_type=ReportType.NETWORK
        )
        report.mark_as_processing()
        self.assertEqual(report.status, ReportStatus.PROCESSING)
    
    def test_mark_as_completed(self):
        """Teste le changement de statut vers 'completed'."""
        report = Report(
            title="Test Report",
            report_type=ReportType.NETWORK
        )
        report.mark_as_completed(file_path="/path/to/report.pdf")
        self.assertEqual(report.status, ReportStatus.COMPLETED)
        self.assertEqual(report.file_path, "/path/to/report.pdf")
    
    def test_mark_as_failed(self):
        """Teste le changement de statut vers 'failed'."""
        report = Report(
            title="Test Report",
            report_type=ReportType.NETWORK
        )
        report.mark_as_failed(error_message="An error occurred")
        self.assertEqual(report.status, ReportStatus.FAILED)
        self.assertEqual(report.content.get("error_message"), "An error occurred")
    
    def test_is_completed(self):
        """Teste la méthode is_completed."""
        report = Report(
            title="Test Report",
            report_type=ReportType.NETWORK
        )
        self.assertFalse(report.is_completed())
        report.mark_as_completed(file_path="/path/to/report.pdf")
        self.assertTrue(report.is_completed())
    
    def test_can_be_regenerated(self):
        """Teste la méthode can_be_regenerated."""
        report = Report(
            title="Test Report",
            report_type=ReportType.NETWORK
        )
        # Un rapport au statut 'draft' ne peut pas être régénéré
        self.assertFalse(report.can_be_regenerated())
        
        # Un rapport au statut 'processing' ne peut pas être régénéré
        report.mark_as_processing()
        self.assertFalse(report.can_be_regenerated())
        
        # Un rapport au statut 'completed' peut être régénéré
        report.mark_as_completed(file_path="/path/to/report.pdf")
        self.assertTrue(report.can_be_regenerated())
        
        # Un rapport au statut 'failed' peut être régénéré
        report = Report(
            title="Test Report",
            report_type=ReportType.NETWORK
        )
        report.mark_as_failed()
        self.assertTrue(report.can_be_regenerated())
    
    def test_to_dict(self):
        """Teste la conversion en dictionnaire."""
        report = Report(
            id=1,
            title="Test Report",
            report_type=ReportType.NETWORK,
            description="Test description",
            created_by=1,
            created_at=datetime(2023, 1, 1, 12, 0, 0),
            template_id=2
        )
        
        report_dict = report.to_dict()
        self.assertEqual(report_dict['id'], 1)
        self.assertEqual(report_dict['title'], "Test Report")
        self.assertEqual(report_dict['report_type'], "network")
        self.assertEqual(report_dict['description'], "Test description")
        self.assertEqual(report_dict['created_by'], 1)
        self.assertEqual(report_dict['created_at'], "2023-01-01T12:00:00")
        self.assertEqual(report_dict['template_id'], 2)


class TestReportTemplateEntity(unittest.TestCase):
    """Tests pour l'entité ReportTemplate."""
    
    def test_creation_valid_template(self):
        """Teste la création d'un template valide."""
        template = ReportTemplate(
            name="Network Status Template",
            template_type="network_status"
        )
        self.assertEqual(template.name, "Network Status Template")
        self.assertEqual(template.template_type, "network_status")
        self.assertTrue(template.is_active)
    
    def test_creation_invalid_template_without_name(self):
        """Teste la création d'un template sans nom (doit échouer)."""
        with self.assertRaises(ValueError):
            ReportTemplate(
                name="",
                template_type="network_status"
            )
    
    def test_creation_invalid_template_with_long_name(self):
        """Teste la création d'un template avec un nom trop long (doit échouer)."""
        with self.assertRaises(ValueError):
            ReportTemplate(
                name="x" * 256,  # Dépasse la limite de 255 caractères
                template_type="network_status"
            )
    
    def test_creation_invalid_template_without_type(self):
        """Teste la création d'un template sans type (doit échouer)."""
        with self.assertRaises(ValueError):
            ReportTemplate(
                name="Network Status Template",
                template_type=""
            )
    
    def test_activate_deactivate(self):
        """Teste les méthodes d'activation/désactivation du template."""
        template = ReportTemplate(
            name="Network Status Template",
            template_type="network_status",
            is_active=False
        )
        self.assertFalse(template.is_active)
        
        template.activate()
        self.assertTrue(template.is_active)
        
        template.deactivate()
        self.assertFalse(template.is_active)
    
    def test_update_content(self):
        """Teste la mise à jour du contenu du template."""
        template = ReportTemplate(
            name="Network Status Template",
            template_type="network_status"
        )
        self.assertEqual(template.content, {})
        
        new_content = {
            "sections": [
                {"title": "Network Overview", "type": "text"},
                {"title": "Performance Metrics", "type": "chart"}
            ]
        }
        template.update_content(new_content)
        self.assertEqual(template.content, new_content)
    
    def test_update_content_invalid(self):
        """Teste la mise à jour avec un contenu invalide (doit échouer)."""
        template = ReportTemplate(
            name="Network Status Template",
            template_type="network_status"
        )
        
        with self.assertRaises(ValueError):
            template.update_content("not a dict")
    
    def test_to_dict(self):
        """Teste la conversion en dictionnaire."""
        template = ReportTemplate(
            id=1,
            name="Network Status Template",
            template_type="network_status",
            description="Template for network status reports",
            created_by=1,
            created_at=datetime(2023, 1, 1, 12, 0, 0),
            is_active=True,
            metadata={"version": "1.0"}
        )
        
        template_dict = template.to_dict()
        self.assertEqual(template_dict['id'], 1)
        self.assertEqual(template_dict['name'], "Network Status Template")
        self.assertEqual(template_dict['template_type'], "network_status")
        self.assertEqual(template_dict['description'], "Template for network status reports")
        self.assertEqual(template_dict['created_by'], 1)
        self.assertEqual(template_dict['created_at'], "2023-01-01T12:00:00")
        self.assertTrue(template_dict['is_active'])
        self.assertEqual(template_dict['metadata'], {"version": "1.0"})


class TestScheduledReportEntity(unittest.TestCase):
    """Tests pour l'entité ScheduledReport."""
    
    def test_creation_valid_scheduled_report(self):
        """Teste la création d'un rapport planifié valide."""
        scheduled = ScheduledReport(
            frequency=Frequency.WEEKLY,
            report_id=1
        )
        self.assertEqual(scheduled.frequency, Frequency.WEEKLY)
        self.assertEqual(scheduled.report_id, 1)
        self.assertTrue(scheduled.is_active)
    
    def test_creation_invalid_frequency(self):
        """Teste la création avec une fréquence invalide (doit échouer)."""
        with self.assertRaises(ValueError):
            ScheduledReport(
                frequency="invalid",  # Pas une instance de Frequency
                report_id=1
            )
    
    def test_creation_without_report_or_template(self):
        """Teste la création sans rapport ni template (doit échouer)."""
        with self.assertRaises(ValueError):
            ScheduledReport(
                frequency=Frequency.WEEKLY
                # Pas de report_id ou template_id
            )
    
    def test_creation_with_both_report_and_template(self):
        """Teste la création avec rapport ET template (doit échouer)."""
        with self.assertRaises(ValueError):
            ScheduledReport(
                frequency=Frequency.WEEKLY,
                report_id=1,
                template_id=2  # Les deux sont fournis
            )
    
    def test_activate_deactivate(self):
        """Teste les méthodes d'activation/désactivation."""
        scheduled = ScheduledReport(
            frequency=Frequency.WEEKLY,
            report_id=1,
            is_active=False
        )
        self.assertFalse(scheduled.is_active)
        
        scheduled.activate()
        self.assertTrue(scheduled.is_active)
        
        scheduled.deactivate()
        self.assertFalse(scheduled.is_active)
    
    def test_add_remove_recipient(self):
        """Teste l'ajout et la suppression de destinataires."""
        scheduled = ScheduledReport(
            frequency=Frequency.WEEKLY,
            report_id=1
        )
        self.assertEqual(scheduled.recipients, [])
        
        # Ajouter un destinataire
        scheduled.add_recipient(101)
        self.assertEqual(scheduled.recipients, [101])
        
        # Ajouter un autre destinataire
        scheduled.add_recipient(102)
        self.assertEqual(scheduled.recipients, [101, 102])
        
        # Réajouter un destinataire existant (ne devrait pas le dupliquer)
        scheduled.add_recipient(101)
        self.assertEqual(scheduled.recipients, [101, 102])
        
        # Supprimer un destinataire
        scheduled.remove_recipient(101)
        self.assertEqual(scheduled.recipients, [102])
        
        # Supprimer un destinataire inexistant (ne devrait rien faire)
        scheduled.remove_recipient(999)
        self.assertEqual(scheduled.recipients, [102])
    
    def test_update_last_run(self):
        """Teste la mise à jour de la dernière exécution."""
        scheduled = ScheduledReport(
            frequency=Frequency.WEEKLY,
            report_id=1
        )
        self.assertIsNone(scheduled.last_run)
        
        timestamp = datetime(2023, 1, 1, 12, 0, 0)
        scheduled.update_last_run(timestamp)
        self.assertEqual(scheduled.last_run, timestamp)
    
    def test_should_run(self):
        """Teste la méthode should_run."""
        now = datetime(2023, 1, 1, 12, 0, 0)
        
        # Cas 1: is_active=False
        scheduled = ScheduledReport(
            frequency=Frequency.WEEKLY,
            report_id=1,
            is_active=False
        )
        self.assertFalse(scheduled.should_run(now))
        
        # Cas 2: start_date dans le futur
        scheduled = ScheduledReport(
            frequency=Frequency.WEEKLY,
            report_id=1,
            start_date=datetime(2023, 1, 2, 12, 0, 0)  # Jour suivant
        )
        self.assertFalse(scheduled.should_run(now))
        
        # Cas 3: next_run non défini
        scheduled = ScheduledReport(
            frequency=Frequency.WEEKLY,
            report_id=1
        )
        self.assertTrue(scheduled.should_run(now))
        
        # Cas 4: next_run dans le passé
        scheduled = ScheduledReport(
            frequency=Frequency.WEEKLY,
            report_id=1,
            next_run=datetime(2022, 12, 31, 12, 0, 0)  # Jour précédent
        )
        self.assertTrue(scheduled.should_run(now))
        
        # Cas 5: next_run dans le futur
        scheduled = ScheduledReport(
            frequency=Frequency.WEEKLY,
            report_id=1,
            next_run=datetime(2023, 1, 2, 12, 0, 0)  # Jour suivant
        )
        self.assertFalse(scheduled.should_run(now))
    
    def test_to_dict(self):
        """Teste la conversion en dictionnaire."""
        scheduled = ScheduledReport(
            id=1,
            frequency=Frequency.WEEKLY,
            report_id=2,
            is_active=True,
            recipients=[101, 102],
            start_date=datetime(2023, 1, 1, 12, 0, 0),
            next_run=datetime(2023, 1, 8, 12, 0, 0),
            last_run=datetime(2023, 1, 1, 12, 0, 0),
            parameters={"format": "pdf"}
        )
        
        scheduled_dict = scheduled.to_dict()
        self.assertEqual(scheduled_dict['id'], 1)
        self.assertEqual(scheduled_dict['frequency'], "weekly")
        self.assertEqual(scheduled_dict['report_id'], 2)
        self.assertTrue(scheduled_dict['is_active'])
        self.assertEqual(scheduled_dict['recipients'], [101, 102])
        self.assertEqual(scheduled_dict['start_date'], "2023-01-01T12:00:00")
        self.assertEqual(scheduled_dict['next_run'], "2023-01-08T12:00:00")
        self.assertEqual(scheduled_dict['last_run'], "2023-01-01T12:00:00")
        self.assertEqual(scheduled_dict['parameters'], {"format": "pdf"}) 