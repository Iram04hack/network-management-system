"""
Configuration globale pour les tests pytest avec Django.
"""

import os
import pytest
import django
from django.conf import settings
from datetime import datetime
from unittest.mock import Mock, MagicMock
from django.core.management import call_command
from django.db import connection

# Configurer les paramètres Django pour les tests
def pytest_configure():
    """Configure Django pour les tests."""
    
    # Définir le module de paramètres Django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'reporting.tests.settings')
    
    # Initialiser Django
    django.setup()

# Fixtures pour le module reporting
@pytest.fixture(scope='session')
def django_db_setup(django_db_setup, django_db_blocker):
    """Configure la base de données pour les tests."""
    with django_db_blocker.unblock():
        # Créer les tables nécessaires
        from reporting.tests.setup_test_db import setup_test_database
        setup_test_database()

@pytest.fixture
def db_access_without_rollback_and_truncate(request, django_db_setup, django_db_blocker):
    """Fixture pour accéder à la base de données sans rollback ni truncate."""
    with django_db_blocker.unblock():
        yield

@pytest.fixture
def report_entity():
    """Fixture pour créer une entité de rapport."""
    from reporting.domain.entities import Report, ReportType, ReportStatus
    return Report(
        id=1,
        title="Test Report",
        description="Test Description",
        report_type=ReportType.NETWORK,
        content={"data": "test"},
        status=ReportStatus.COMPLETED,
        created_by=1,
        created_at=datetime.now()
    )

@pytest.fixture
def report_template_entity():
    """Fixture pour créer une entité de modèle de rapport."""
    from reporting.domain.entities import ReportTemplate, ReportType
    return ReportTemplate(
        id=1,
        name="Test Template",
        description="Test Template Description",
        template_type=ReportType.NETWORK.value,
        content={"template": "data"},
        is_active=True,
        created_by=1,
        created_at=datetime.now()
    )

@pytest.fixture
def scheduled_report_entity(report_entity, report_template_entity):
    """Fixture pour créer une entité de rapport planifié."""
    from reporting.domain.entities import ScheduledReport, Frequency
    return ScheduledReport(
        id=1,
        frequency=Frequency.DAILY,
        is_active=True,
        template_id=report_template_entity.id,
        report_id=report_entity.id,
        last_run=datetime.now(),
        next_run=datetime.now(),
        recipients=[1, 2]
    )

@pytest.fixture
def mock_report_repository():
    """Fixture pour créer un mock de repository de rapport."""
    from reporting.domain.entities import Report, ReportType, ReportStatus
    repo = Mock()
    repo.get_by_id.return_value = Report(
        id=1,
        title="Test Report",
        description="Test Description",
        report_type=ReportType.NETWORK,
        content={"data": "test"},
        status=ReportStatus.COMPLETED,
        created_by=1,
        created_at=datetime.now()
    )
    repo.list.return_value = [
        Report(
            id=1,
            title="Test Report 1",
            description="Test Description 1",
            report_type=ReportType.NETWORK,
            content={"data": "test1"},
            status=ReportStatus.COMPLETED,
            created_by=1,
            created_at=datetime.now()
        ),
        Report(
            id=2,
            title="Test Report 2",
            description="Test Description 2",
            report_type=ReportType.SECURITY,
            content={"data": "test2"},
            status=ReportStatus.PROCESSING,
            created_by=2,
            created_at=datetime.now()
        )
    ]
    repo.create.return_value = Report(
        id=3,
        title="New Report",
        description="New Description",
        report_type=ReportType.NETWORK,
        content={"data": "new"},
        status=ReportStatus.COMPLETED,
        created_by=1,
        created_at=datetime.now()
    )
    repo.update.return_value = True
    repo.delete.return_value = True
    return repo

@pytest.fixture
def mock_report_service():
    """Fixture pour créer un mock de service de génération de rapports."""
    service = Mock()
    service.generate.return_value = {
        "id": 1,
        "title": "Generated Report",
        "content": {"data": "generated"}
    }
    service.get_supported_formats.return_value = ["pdf", "xlsx", "csv"]
    return service 