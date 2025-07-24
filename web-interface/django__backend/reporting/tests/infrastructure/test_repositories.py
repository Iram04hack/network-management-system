"""
Tests pour les repositories du module reporting.

Ces tests vérifient le bon fonctionnement des repositories Django.
"""

import pytest
from django.test import TestCase
from django.contrib.auth.models import User
from datetime import datetime

from reporting.domain.entities import (
    Report as ReportEntity,
    ReportTemplate as TemplateEntity,
    ScheduledReport as ScheduledEntity,
    ReportType,
    ReportStatus,
    Frequency
)
from reporting.models import Report, ReportTemplate, ScheduledReport
from reporting.infrastructure.repositories import (
    DjangoReportRepository,
    DjangoReportTemplateRepository,
    DjangoScheduledReportRepository
)


@pytest.mark.django_db
class TestDjangoReportRepository(TestCase):
    """Tests pour le repository des rapports."""
    
    def setUp(self):
        """Initialise les données de test."""
        # Créer un utilisateur pour les tests
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass'
        )
        
        # Créer un modèle de rapport Django
        self.report_model = Report.objects.create(
            title="Test Report",
            description="Test description",
            report_type="network",
            created_by=self.user,
            status="completed",
            content={"data": "test content"},
            parameters={"param1": "value1"},
            file_path="/path/to/report.pdf"
        )
        
        # Initialiser le repository
        self.repository = DjangoReportRepository()
    
    def test_get_by_id(self):
        """Teste la récupération d'un rapport par son ID."""
        # Récupérer le rapport
        report = self.repository.get_by_id(self.report_model.id)
        
        # Vérifier que le rapport est correctement récupéré
        assert report is not None
        assert isinstance(report, ReportEntity)
        assert report.id == self.report_model.id
        assert report.title == "Test Report"
        assert report.report_type == ReportType.NETWORK
        assert report.status == ReportStatus.COMPLETED
    
    def test_list(self):
        """Teste la liste des rapports."""
        # Créer un deuxième rapport
        Report.objects.create(
            title="Second Report",
            description="Another description",
            report_type="security",
            created_by=self.user,
            status="draft"
        )
        
        # Lister tous les rapports
        reports = self.repository.list()
        
        # Vérifier que les deux rapports sont listés
        assert len(reports) == 2
        assert all(isinstance(report, ReportEntity) for report in reports)
        
        # Tester les filtres
        security_reports = self.repository.list({'report_type': ReportType.SECURITY})
        assert len(security_reports) == 1
        assert security_reports[0].report_type == ReportType.SECURITY
        
        completed_reports = self.repository.list({'status': ReportStatus.COMPLETED})
        assert len(completed_reports) == 1
        assert completed_reports[0].status == ReportStatus.COMPLETED
    
    def test_create(self):
        """Teste la création d'un rapport."""
        # Créer une entité de rapport
        new_report = ReportEntity(
            title="New Report",
            description="New description",
            report_type=ReportType.SECURITY,
            created_by=self.user.id,
            status=ReportStatus.DRAFT,
            content={"new_data": "test"},
            parameters={"new_param": "test"},
            file_path="/path/to/new_report.pdf"
        )
        
        # Créer le rapport via le repository
        created_report = self.repository.create(new_report)
        
        # Vérifier que le rapport a été créé
        assert created_report is not None
        assert isinstance(created_report, ReportEntity)
        assert created_report.id is not None
        assert created_report.title == "New Report"
        assert created_report.report_type == ReportType.SECURITY
        
        # Vérifier que le rapport existe en base
        assert Report.objects.filter(title="New Report").exists()
    
    def test_update(self):
        """Teste la mise à jour d'un rapport."""
        # Récupérer le rapport
        report = self.repository.get_by_id(self.report_model.id)
        
        # Modifier le rapport
        report.title = "Updated Title"
        report.description = "Updated description"
        report.status = ReportStatus.FAILED
        
        # Mettre à jour via le repository
        updated_report = self.repository.update(report)
        
        # Vérifier que le rapport a été mis à jour
        assert updated_report.title == "Updated Title"
        assert updated_report.description == "Updated description"
        assert updated_report.status == ReportStatus.FAILED
        
        # Vérifier que les modifications sont en base
        db_report = Report.objects.get(pk=self.report_model.id)
        assert db_report.title == "Updated Title"
        assert db_report.status == "failed"
    
    def test_update_status(self):
        """Teste la mise à jour du statut d'un rapport."""
        # Mettre à jour le statut
        updated_report = self.repository.update_status(self.report_model.id, ReportStatus.PROCESSING)
        
        # Vérifier que le statut a été mis à jour
        assert updated_report.status == ReportStatus.PROCESSING
        
        # Vérifier en base
        db_report = Report.objects.get(pk=self.report_model.id)
        assert db_report.status == "processing"
    
    def test_update_content(self):
        """Teste la mise à jour du contenu d'un rapport."""
        # Nouveau contenu
        new_content = {"updated": "content", "version": 2}
        
        # Mettre à jour le contenu
        updated_report = self.repository.update_content(self.report_model.id, new_content)
        
        # Vérifier que le contenu a été mis à jour
        assert updated_report.content == new_content
        
        # Vérifier en base
        db_report = Report.objects.get(pk=self.report_model.id)
        assert db_report.content == new_content
    
    def test_delete(self):
        """Teste la suppression d'un rapport."""
        # Supprimer le rapport
        result = self.repository.delete(self.report_model.id)
        
        # Vérifier que la suppression a réussi
        assert result is True
        
        # Vérifier que le rapport n'existe plus en base
        assert not Report.objects.filter(pk=self.report_model.id).exists()


@pytest.mark.django_db
class TestDjangoReportTemplateRepository(TestCase):
    """Tests pour le repository des templates de rapport."""
    
    def setUp(self):
        """Initialise les données de test."""
        # Créer un utilisateur pour les tests
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass'
        )
        
        # Créer un modèle de template Django
        self.template_model = ReportTemplate.objects.create(
            name="Test Template",
            description="Test description",
            template_type="network_status",
            created_by=self.user,
            content={"sections": []},
            is_active=True,
            metadata={"version": "1.0"}
        )
        
        # Initialiser le repository
        self.repository = DjangoReportTemplateRepository()
    
    def test_get_by_id(self):
        """Teste la récupération d'un template par son ID."""
        # Récupérer le template
        template = self.repository.get_by_id(self.template_model.id)
        
        # Vérifier que le template est correctement récupéré
        assert template is not None
        assert isinstance(template, TemplateEntity)
        assert template.id == self.template_model.id
        assert template.name == "Test Template"
        assert template.template_type == "network_status"
        assert template.is_active is True
    
    def test_list(self):
        """Teste la liste des templates."""
        # Créer un deuxième template
        ReportTemplate.objects.create(
            name="Second Template",
            description="Another description",
            template_type="security_audit",
            created_by=self.user,
            content={"sections": []},
            is_active=False
        )
        
        # Lister tous les templates
        templates = self.repository.list()
        
        # Vérifier que les deux templates sont listés
        assert len(templates) == 2
        assert all(isinstance(template, TemplateEntity) for template in templates)
        
        # Tester les filtres
        active_templates = self.repository.list({'is_active': True})
        assert len(active_templates) == 1
        assert active_templates[0].is_active is True
        
        security_templates = self.repository.list({'template_type': 'security_audit'})
        assert len(security_templates) == 1
        assert security_templates[0].template_type == 'security_audit'
    
    def test_create(self):
        """Teste la création d'un template."""
        # Créer une entité de template
        new_template = TemplateEntity(
            name="New Template",
            description="New description",
            template_type="custom",
            created_by=self.user.id,
            content={"new_sections": []},
            is_active=True,
            metadata={"version": "2.0"}
        )
        
        # Créer le template via le repository
        created_template = self.repository.create(new_template)
        
        # Vérifier que le template a été créé
        assert created_template is not None
        assert isinstance(created_template, TemplateEntity)
        assert created_template.id is not None
        assert created_template.name == "New Template"
        assert created_template.template_type == "custom"
        
        # Vérifier que le template existe en base
        assert ReportTemplate.objects.filter(name="New Template").exists()
    
    def test_update(self):
        """Teste la mise à jour d'un template."""
        # Récupérer le template
        template = self.repository.get_by_id(self.template_model.id)
        
        # Modifier le template
        template.name = "Updated Name"
        template.description = "Updated description"
        template.is_active = False
        
        # Mettre à jour via le repository
        updated_template = self.repository.update(template)
        
        # Vérifier que le template a été mis à jour
        assert updated_template.name == "Updated Name"
        assert updated_template.description == "Updated description"
        assert updated_template.is_active is False
        
        # Vérifier que les modifications sont en base
        db_template = ReportTemplate.objects.get(pk=self.template_model.id)
        assert db_template.name == "Updated Name"
        assert db_template.is_active is False
    
    def test_delete(self):
        """Teste la suppression d'un template."""
        # Supprimer le template
        result = self.repository.delete(self.template_model.id)
        
        # Vérifier que la suppression a réussi
        assert result is True
        
        # Vérifier que le template n'existe plus en base
        assert not ReportTemplate.objects.filter(pk=self.template_model.id).exists()


@pytest.mark.django_db
class TestDjangoScheduledReportRepository(TestCase):
    """Tests pour le repository des rapports planifiés."""
    
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
        
        # Créer un rapport pour associer à la planification
        self.report = Report.objects.create(
            title="Test Report",
            description="Test description",
            report_type="network",
            created_by=self.user1,
            status="draft"
        )
        
        # Créer un modèle de rapport planifié Django
        now = datetime.now()
        self.scheduled_model = ScheduledReport.objects.create(
            report=self.report,
            frequency="daily",
            is_active=True,
            next_run=now,
            last_run=now,
            start_date=now,
            parameters={"param1": "value1"},
            format="pdf"
        )
        self.scheduled_model.recipients.add(self.user1, self.user2)
        
        # Initialiser le repository
        self.repository = DjangoScheduledReportRepository()
    
    def test_get_by_id(self):
        """Teste la récupération d'un rapport planifié par son ID."""
        # Récupérer le rapport planifié
        scheduled = self.repository.get_by_id(self.scheduled_model.id)
        
        # Vérifier que le rapport planifié est correctement récupéré
        assert scheduled is not None
        assert isinstance(scheduled, ScheduledEntity)
        assert scheduled.id == self.scheduled_model.id
        assert scheduled.report_id == self.report.id
        assert scheduled.frequency == Frequency.DAILY
        assert scheduled.is_active is True
        assert len(scheduled.recipients) == 2
    
    def test_list(self):
        """Teste la liste des rapports planifiés."""
        # Créer un deuxième rapport
        report2 = Report.objects.create(
            title="Second Report",
            description="Another description",
            report_type="security",
            created_by=self.user1,
            status="draft"
        )
        
        # Créer un deuxième rapport planifié
        scheduled2 = ScheduledReport.objects.create(
            report=report2,
            frequency="weekly",
            is_active=False
        )
        scheduled2.recipients.add(self.user1)
        
        # Lister tous les rapports planifiés
        scheduleds = self.repository.list()
        
        # Vérifier que les deux rapports planifiés sont listés
        assert len(scheduleds) == 2
        assert all(isinstance(scheduled, ScheduledEntity) for scheduled in scheduleds)
        
        # Tester les filtres
        active_scheduleds = self.repository.list({'is_active': True})
        assert len(active_scheduleds) == 1
        assert active_scheduleds[0].is_active is True
        
        weekly_scheduleds = self.repository.list({'frequency': Frequency.WEEKLY})
        assert len(weekly_scheduleds) == 1
        assert weekly_scheduleds[0].frequency == Frequency.WEEKLY
    
    def test_create(self):
        """Teste la création d'un rapport planifié."""
        # Créer un autre rapport
        report2 = Report.objects.create(
            title="Another Report",
            description="For scheduled test",
            report_type="security",
            created_by=self.user1,
            status="draft"
        )
        
        # Créer une entité de rapport planifié
        now = datetime.now()
        new_scheduled = ScheduledEntity(
            report_id=report2.id,
            frequency=Frequency.MONTHLY,
            is_active=True,
            next_run=now,
            recipients=[self.user1.id],
            parameters={"test": "value"}
        )
        
        # Créer le rapport planifié via le repository
        created_scheduled = self.repository.create(new_scheduled)
        
        # Vérifier que le rapport planifié a été créé
        assert created_scheduled is not None
        assert isinstance(created_scheduled, ScheduledEntity)
        assert created_scheduled.id is not None
        assert created_scheduled.report_id == report2.id
        assert created_scheduled.frequency == Frequency.MONTHLY
        assert len(created_scheduled.recipients) == 1
        
        # Vérifier que le rapport planifié existe en base
        assert ScheduledReport.objects.filter(report_id=report2.id).exists()
    
    def test_update(self):
        """Teste la mise à jour d'un rapport planifié."""
        # Récupérer le rapport planifié
        scheduled = self.repository.get_by_id(self.scheduled_model.id)
        
        # Modifier le rapport planifié
        scheduled.frequency = Frequency.WEEKLY
        scheduled.is_active = False
        scheduled.recipients = [self.user1.id]  # Supprimer user2
        
        # Mettre à jour via le repository
        updated_scheduled = self.repository.update(scheduled)
        
        # Vérifier que le rapport planifié a été mis à jour
        assert updated_scheduled.frequency == Frequency.WEEKLY
        assert updated_scheduled.is_active is False
        assert len(updated_scheduled.recipients) == 1
        assert self.user2.id not in updated_scheduled.recipients
        
        # Vérifier que les modifications sont en base
        db_scheduled = ScheduledReport.objects.get(pk=self.scheduled_model.id)
        assert db_scheduled.frequency == "weekly"
        assert db_scheduled.is_active is False
        assert db_scheduled.recipients.count() == 1
    
    def test_delete(self):
        """Teste la suppression d'un rapport planifié."""
        # Supprimer le rapport planifié
        result = self.repository.delete(self.scheduled_model.id)
        
        # Vérifier que la suppression a réussi
        assert result is True
        
        # Vérifier que le rapport planifié n'existe plus en base
        assert not ScheduledReport.objects.filter(pk=self.scheduled_model.id).exists()
    
    def test_add_recipient(self):
        """Teste l'ajout d'un destinataire à un rapport planifié."""
        # Créer un nouvel utilisateur
        user3 = User.objects.create_user(
            username='user3',
            email='user3@example.com',
            password='pass3'
        )
        
        # Ajouter le destinataire
        result = self.repository.add_recipient(self.scheduled_model.id, user3.id)
        
        # Vérifier que l'ajout a réussi
        assert result is True
        
        # Vérifier que le destinataire a été ajouté en base
        db_scheduled = ScheduledReport.objects.get(pk=self.scheduled_model.id)
        assert db_scheduled.recipients.filter(id=user3.id).exists()
        
        # Tester l'ajout d'un destinataire déjà présent
        result = self.repository.add_recipient(self.scheduled_model.id, self.user1.id)
        assert result is False
    
    def test_remove_recipient(self):
        """Teste la suppression d'un destinataire d'un rapport planifié."""
        # Supprimer un destinataire
        result = self.repository.remove_recipient(self.scheduled_model.id, self.user2.id)
        
        # Vérifier que la suppression a réussi
        assert result is True
        
        # Vérifier que le destinataire a été supprimé en base
        db_scheduled = ScheduledReport.objects.get(pk=self.scheduled_model.id)
        assert not db_scheduled.recipients.filter(id=self.user2.id).exists()
        
        # Tester la suppression d'un destinataire non présent
        user3 = User.objects.create_user(
            username='user3',
            email='user3@example.com',
            password='pass3'
        )
        result = self.repository.remove_recipient(self.scheduled_model.id, user3.id)
        assert result is False 