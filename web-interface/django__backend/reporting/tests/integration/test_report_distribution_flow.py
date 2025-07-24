"""
Tests d'intégration pour le flux de distribution des rapports.

Ces tests vérifient l'intégration entre les différentes couches du module
pour s'assurer que le flux de distribution des rapports fonctionne correctement.
"""

import pytest
from unittest.mock import patch
from django.test import TestCase
from django.contrib.auth.models import User
from datetime import datetime, timedelta

from reporting.domain.entities import ReportType, ReportStatus, ReportFormat, Frequency
from reporting.models import Report, ReportTemplate, ScheduledReport
from reporting.di_container import DIContainer


@pytest.mark.django_db
class TestReportDistributionFlow(TestCase):
    """Tests pour le flux complet de distribution des rapports."""
    
    def setUp(self):
        """Initialise les données de test."""
        # Créer des utilisateurs pour les tests
        self.user1 = User.objects.create_user(
            username='user1',
            email='user1@example.com',
            password='pass1'
        )
        self.user2 = User.objects.create_user(
            username='user2',
            email='user2@example.com',
            password='pass2'
        )
        
        # Créer un rapport
        self.report = Report.objects.create(
            title="Test Report",
            description="Test description",
            report_type="network",
            created_by=self.user1,
            status="completed",
            content={"data": "test content"}
        )
        
        # Créer une planification de rapport
        self.scheduled = ScheduledReport.objects.create(
            report=self.report,
            frequency="weekly",
            is_active=True,
            next_run=datetime.now() - timedelta(days=1)  # Déjà due
        )
        self.scheduled.recipients.add(self.user1, self.user2)
        
        # Initialiser le conteneur DI
        self.container = DIContainer()
    
    @patch('reporting.infrastructure.services.DjangoNotificationService.notify_report_completion')
    @patch('reporting.infrastructure.services.DjangoReportExporter.export_report')
    def test_distribute_scheduled_reports(self, mock_export, mock_notify):
        """Teste la distribution des rapports planifiés."""
        # Configurer les mocks
        mock_export.return_value = True
        mock_notify.return_value = True
        
        # Récupérer le cas d'utilisation de distribution
        distribution_use_cases = self.container.get_report_distribution_use_cases()
        
        # Exécuter la distribution
        results = distribution_use_cases.process_due_scheduled_reports()
        
        # Vérifier que la planification a été traitée
        assert len(results) >= 1
        processed = next((r for r in results if r['schedule_id'] == self.scheduled.id), None)
        assert processed is not None
        assert processed['success'] is True
        
        # Vérifier que l'exportation a été appelée
        mock_export.assert_called()
        
        # Vérifier que la notification a été appelée
        mock_notify.assert_called()
        
        # Vérifier que next_run a été mis à jour
        db_scheduled = ScheduledReport.objects.get(pk=self.scheduled.id)
        assert db_scheduled.next_run > datetime.now()
    
    @patch('reporting.infrastructure.services.DjangoNotificationService.notify_report_completion')
    def test_manual_report_distribution(self, mock_notify):
        """Teste la distribution manuelle d'un rapport."""
        # Configurer le mock
        mock_notify.return_value = True
        
        # Récupérer le cas d'utilisation
        distribution_use_cases = self.container.get_report_distribution_use_cases()
        
        # Distribuer le rapport manuellement
        result = distribution_use_cases.distribute_report(
            report_id=self.report.id,
            recipients=[self.user1.id, self.user2.id],
            distribution_method="email"
        )
        
        # Vérifier que la distribution a réussi
        assert result is True
        
        # Vérifier que la notification a été appelée
        mock_notify.assert_called_with(
            report_id=self.report.id,
            recipients=[self.user1.id, self.user2.id]
        )
    
    @patch('reporting.infrastructure.services.DjangoNotificationService.notify_report_completion')
    def test_distribution_with_filters(self, mock_notify):
        """Teste la distribution avec filtrage des destinataires."""
        # Configurer le mock
        mock_notify.return_value = True
        
        # Créer un autre utilisateur avec un rôle spécifique
        self.user3 = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='adminpass',
            is_staff=True
        )
        
        # Ajouter l'utilisateur à la planification
        self.scheduled.recipients.add(self.user3)
        
        # Récupérer le cas d'utilisation
        distribution_use_cases = self.container.get_report_distribution_use_cases()
        
        # Distribuer le rapport avec filtre (uniquement aux admins)
        result = distribution_use_cases.distribute_report_with_filter(
            report_id=self.report.id,
            recipient_filter={"is_staff": True},
            distribution_method="email"
        )
        
        # Vérifier que la distribution a réussi
        assert result is True
        
        # Vérifier que la notification a été appelée uniquement pour l'admin
        mock_notify.assert_called_with(
            report_id=self.report.id,
            recipients=[self.user3.id]
        ) 