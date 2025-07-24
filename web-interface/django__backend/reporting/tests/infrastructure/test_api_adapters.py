"""
Tests pour les adaptateurs API du module reporting.

Ces tests vérifient la conversion correcte entre les représentations
API et les entités de domaine.
"""

import pytest
from django.test import TestCase
from django.contrib.auth.models import User
from datetime import datetime

from reporting.domain.entities import (
    Report as ReportEntity,
    ReportTemplate as ReportTemplateEntity,
    ScheduledReport as ScheduledReportEntity,
    ReportType,
    ReportStatus,
    Frequency,
    ReportFormat
)
from reporting.models import Report, ReportTemplate, ScheduledReport
from reporting.infrastructure.api_adapters import (
    ReportApiAdapter,
    ReportTemplateApiAdapter,
    ScheduledReportApiAdapter
)


@pytest.mark.django_db
class TestReportApiAdapter(TestCase):
    """Tests pour l'adaptateur API des rapports."""
    
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
        
        # Initialiser l'adaptateur
        self.adapter = ReportApiAdapter()
    
    def test_to_domain_entity(self):
        """Teste la conversion d'un modèle Django vers une entité de domaine."""
        # Convertir le modèle en entité
        entity = self.adapter.to_domain_entity(self.report_model)
        
        # Vérifier que l'entité a été correctement construite
        assert isinstance(entity, ReportEntity)
        assert entity.id == self.report_model.id
        assert entity.title == "Test Report"
        assert entity.description == "Test description"
        assert entity.report_type == ReportType.NETWORK
        assert entity.status == ReportStatus.COMPLETED
        assert entity.content == {"data": "test content"}
        assert entity.parameters == {"param1": "value1"}
        assert entity.file_path == "/path/to/report.pdf"
        assert entity.created_by == self.user.id
    
    def test_to_api_representation(self):
        """Teste la conversion d'une entité de domaine vers une représentation API."""
        # Créer une entité de domaine
        now = datetime.now()
        entity = ReportEntity(
            id=1,
            title="API Report",
            description="API description",
            report_type=ReportType.SECURITY,
            created_by=self.user.id,
            created_at=now,
            status=ReportStatus.DRAFT,
            content={"api_data": "test"},
            parameters={"api_param": "test"},
            file_path="/path/to/api_report.pdf"
        )
        
        # Convertir l'entité en représentation API
        api_rep = self.adapter.to_api_representation(entity)
        
        # Vérifier que la représentation API est correcte
        assert api_rep["id"] == 1
        assert api_rep["title"] == "API Report"
        assert api_rep["description"] == "API description"
        assert api_rep["report_type"] == "security"
        assert api_rep["status"] == "draft"
        assert api_rep["content"] == {"api_data": "test"}
        assert api_rep["parameters"] == {"api_param": "test"}
        assert api_rep["file_path"] == "/path/to/api_report.pdf"
        assert api_rep["created_by"] == self.user.id
    
    def test_from_api_representation(self):
        """Teste la conversion d'une représentation API vers une entité de domaine."""
        # Créer une représentation API
        api_data = {
            "title": "New Report",
            "description": "New description",
            "report_type": "performance",
            "status": "processing",
            "content": {"new_data": "test"},
            "parameters": {"new_param": "test"},
            "file_path": "/path/to/new_report.pdf",
            "created_by": self.user.id
        }
        
        # Convertir la représentation API en entité
        entity = self.adapter.from_api_representation(api_data)
        
        # Vérifier que l'entité est correcte
        assert entity.title == "New Report"
        assert entity.description == "New description"
        assert entity.report_type == ReportType.PERFORMANCE
        assert entity.status == ReportStatus.PROCESSING
        assert entity.content == {"new_data": "test"}
        assert entity.parameters == {"new_param": "test"}
        assert entity.file_path == "/path/to/new_report.pdf"
        assert entity.created_by == self.user.id


@pytest.mark.django_db
class TestReportTemplateApiAdapter(TestCase):
    """Tests pour l'adaptateur API des templates de rapport."""
    
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
        
        # Initialiser l'adaptateur
        self.adapter = ReportTemplateApiAdapter()
    
    def test_to_domain_entity(self):
        """Teste la conversion d'un modèle Django vers une entité de domaine."""
        # Convertir le modèle en entité
        entity = self.adapter.to_domain_entity(self.template_model)
        
        # Vérifier que l'entité a été correctement construite
        assert isinstance(entity, ReportTemplateEntity)
        assert entity.id == self.template_model.id
        assert entity.name == "Test Template"
        assert entity.description == "Test description"
        assert entity.template_type == "network_status"
        assert entity.content == {"sections": []}
        assert entity.is_active is True
        assert entity.metadata == {"version": "1.0"}
        assert entity.created_by == self.user.id
    
    def test_to_api_representation(self):
        """Teste la conversion d'une entité de domaine vers une représentation API."""
        # Créer une entité de domaine
        now = datetime.now()
        entity = ReportTemplateEntity(
            id=1,
            name="API Template",
            description="API description",
            template_type="security_audit",
            created_by=self.user.id,
            created_at=now,
            content={"api_sections": []},
            is_active=False,
            metadata={"version": "2.0"}
        )
        
        # Convertir l'entité en représentation API
        api_rep = self.adapter.to_api_representation(entity)
        
        # Vérifier que la représentation API est correcte
        assert api_rep["id"] == 1
        assert api_rep["name"] == "API Template"
        assert api_rep["description"] == "API description"
        assert api_rep["template_type"] == "security_audit"
        assert api_rep["content"] == {"api_sections": []}
        assert api_rep["is_active"] is False
        assert api_rep["metadata"] == {"version": "2.0"}
        assert api_rep["created_by"] == self.user.id


@pytest.mark.django_db
class TestScheduledReportApiAdapter(TestCase):
    """Tests pour l'adaptateur API des rapports planifiés."""
    
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
        
        # Initialiser l'adaptateur
        self.adapter = ScheduledReportApiAdapter()
    
    def test_to_domain_entity(self):
        """Teste la conversion d'un modèle Django vers une entité de domaine."""
        # Convertir le modèle en entité
        entity = self.adapter.to_domain_entity(self.scheduled_model)
        
        # Vérifier que l'entité a été correctement construite
        assert isinstance(entity, ScheduledReportEntity)
        assert entity.id == self.scheduled_model.id
        assert entity.report_id == self.report.id
        assert entity.frequency == Frequency.DAILY
        assert entity.is_active is True
        assert entity.next_run == self.scheduled_model.next_run
        assert entity.last_run == self.scheduled_model.last_run
        assert entity.start_date == self.scheduled_model.start_date
        assert entity.parameters == {"param1": "value1"}
        assert len(entity.recipients) == 2
        assert self.user1.id in entity.recipients
        assert self.user2.id in entity.recipients
    
    def test_to_api_representation(self):
        """Teste la conversion d'une entité de domaine vers une représentation API."""
        # Créer une entité de domaine
        now = datetime.now()
        entity = ScheduledReportEntity(
            id=1,
            report_id=self.report.id,
            frequency=Frequency.WEEKLY,
            is_active=True,
            next_run=now,
            last_run=now,
            start_date=now,
            recipients=[self.user1.id, self.user2.id],
            parameters={"api_param": "test"}
        )
        
        # Convertir l'entité en représentation API
        api_rep = self.adapter.to_api_representation(entity)
        
        # Vérifier que la représentation API est correcte
        assert api_rep["id"] == 1
        assert api_rep["report_id"] == self.report.id
        assert api_rep["frequency"] == "weekly"
        assert api_rep["is_active"] is True
        assert api_rep["next_run"] == now.isoformat()
        assert api_rep["last_run"] == now.isoformat()
        assert api_rep["start_date"] == now.isoformat()
        assert api_rep["recipients"] == [self.user1.id, self.user2.id]
        assert api_rep["parameters"] == {"api_param": "test"} 