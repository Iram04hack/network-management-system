"""
Tests d'intégration pour le flux complet de génération de rapports.

Ces tests vérifient l'intégration entre les différentes couches du module
pour s'assurer que le flux de génération de rapports fonctionne correctement
de bout en bout.
"""

import pytest
import tempfile
import os
from django.test import TestCase
from django.contrib.auth.models import User

from reporting.domain.entities import ReportType, ReportStatus, ReportFormat, Frequency
from reporting.models import Report, ReportTemplate, ScheduledReport
from reporting.di_container import DIContainer


@pytest.mark.django_db
class TestReportGenerationFlow(TestCase):
    """Tests pour le flux complet de génération de rapports."""
    
    def setUp(self):
        """Initialise les données de test."""
        # Créer un utilisateur pour les tests
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass'
        )
        
        # Créer un template de rapport
        self.template = ReportTemplate.objects.create(
            name="Network Status Template",
            description="Template for network status reports",
            template_type="network_status",
            created_by=self.user,
            content={
                "title": "{{title}}",
                "sections": [
                    {
                        "title": "Network Overview",
                        "content": "Status: {{status}}"
                    },
                    {
                        "title": "Devices",
                        "content": "Number of devices: {{device_count}}"
                    }
                ]
            },
            is_active=True
        )
        
        # Initialiser le conteneur DI
        self.container = DIContainer()
    
    def test_generate_and_export_report(self):
        """Teste la génération et l'exportation d'un rapport."""
        # Récupérer les cas d'utilisation
        report_use_cases = self.container.get_report_use_cases()
        template_use_cases = self.container.get_report_template_use_cases()
        export_use_cases = self.container.get_report_export_use_cases()
        
        # Vérifier que le template existe
        template = template_use_cases.get_template_by_id(self.template.id)
        assert template is not None
        
        # Paramètres pour le rapport
        parameters = {
            "title": "Integration Test Report",
            "status": "Operational",
            "device_count": 100,
        }
        
        # Générer un rapport
        report = report_use_cases.generate_report(
            template_id=self.template.id,
            parameters=parameters,
            user_id=self.user.id,
            report_type=ReportType.NETWORK
        )
        
        # Vérifier que le rapport a été créé
        assert report is not None
        assert report.title == "Integration Test Report"
        assert report.status == ReportStatus.COMPLETED
        
        # Exporter le rapport en JSON
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as temp_file:
            json_path = temp_file.name
        
        try:
            # Exporter en JSON
            json_result = export_use_cases.export_report(
                report_id=report.id,
                format=ReportFormat.JSON,
                output_path=json_path
            )
            
            # Vérifier que l'exportation a réussi
            assert json_result is True
            assert os.path.exists(json_path)
            assert os.path.getsize(json_path) > 0
            
        finally:
            # Nettoyer le fichier temporaire
            if os.path.exists(json_path):
                os.remove(json_path)
    
    def test_schedule_report_generation(self):
        """Teste la planification d'un rapport."""
        # Récupérer les cas d'utilisation
        report_use_cases = self.container.get_report_use_cases()
        scheduled_report_use_cases = self.container.get_scheduled_report_use_cases()
        
        # Paramètres pour le rapport
        parameters = {
            "title": "Scheduled Test Report",
            "status": "Operational",
            "device_count": 100,
        }
        
        # Générer un rapport
        report = report_use_cases.generate_report(
            template_id=self.template.id,
            parameters=parameters,
            user_id=self.user.id,
            report_type=ReportType.NETWORK
        )
        
        # Planifier le rapport
        scheduled = scheduled_report_use_cases.schedule_report(
            report_id=report.id,
            frequency=Frequency.WEEKLY,
            recipients=[self.user.id],
            format=ReportFormat.PDF
        )
        
        # Vérifier que la planification a été créée
        assert scheduled is not None
        assert scheduled.report_id == report.id
        assert scheduled.frequency == Frequency.WEEKLY
        assert scheduled.is_active is True
        assert len(scheduled.recipients) == 1
        assert scheduled.recipients[0] == self.user.id
        
        # Vérifier que la planification est dans la base de données
        db_scheduled = ScheduledReport.objects.get(pk=scheduled.id)
        assert db_scheduled is not None
        assert db_scheduled.frequency == "weekly"
        
        # Modifier la planification
        updated = scheduled_report_use_cases.update_schedule(
            schedule_id=scheduled.id,
            frequency=Frequency.MONTHLY,
            is_active=False
        )
        
        # Vérifier que la modification a été appliquée
        assert updated.frequency == Frequency.MONTHLY
        assert updated.is_active is False
        
        # Vérifier dans la base de données
        db_scheduled = ScheduledReport.objects.get(pk=scheduled.id)
        assert db_scheduled.frequency == "monthly"
        assert db_scheduled.is_active is False 