"""
Tests pour les adaptateurs d'infrastructure du module reporting.

Ce module teste les adaptateurs qui permettent d'intégrer les services
existants avec le nouveau module reporting.
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from reporting.domain.entities import (
    Report, ReportTemplate, ScheduledReport,
    ReportFormat, ReportType, ReportStatus, Frequency
)
from reporting.domain.exceptions import (
    ReportNotFoundError, ReportGenerationError, 
    ReportValidationError
)
from reporting.infrastructure.adapters import LegacyReportServiceAdapter


class TestLegacyReportServiceAdapter:
    """Tests pour l'adaptateur du service legacy."""
    
    def setup_method(self):
        """Configure les mocks pour les tests."""
        # Mock pour le rapport legacy
        self.mock_legacy_report = Mock()
        self.mock_legacy_report.id = 1
        self.mock_legacy_report.title = "Test Report"
        self.mock_legacy_report.generated_at = datetime.now()
        
        # Mock pour les données JSON
        mock_json_file = Mock()
        mock_json_file.read.return_value = json.dumps({
            "key": "value",
            "data": [1, 2, 3]
        }).encode('utf-8')
        self.mock_legacy_report.data_json = mock_json_file
        
        # Mock pour le template
        self.mock_template = Mock()
        self.mock_template.report_type = "network_inventory"
        self.mock_legacy_report.template = self.mock_template
        
        # Mock pour le rapport planifié
        self.mock_scheduled_report = Mock()
        self.mock_scheduled_report.id = 1
        self.mock_scheduled_report.is_active = True
        self.mock_scheduled_report.last_run = datetime.now()
        self.mock_scheduled_report.next_run = datetime.now()
        self.mock_scheduled_report.recipients = ["1", "2", "user@example.com"]
    
    @patch('reporting.infrastructure.adapters.legacy_service_adapter.LegacyReportService')
    def test_generate_report(self, mock_legacy_service):
        """Teste la génération d'un rapport via l'adaptateur."""
        # Configuration du mock
        mock_legacy_service.generate_report.return_value = self.mock_legacy_report
        
        # Paramètres du test
        template_id = 1
        parameters = {"title": "Test Report", "date": "2023-01-01"}
        user_id = 1
        
        # Appel de la méthode testée
        result = LegacyReportServiceAdapter.generate_report(
            template_id=template_id,
            parameters=parameters,
            user_id=user_id
        )
        
        # Vérifications
        assert mock_legacy_service.generate_report.called
        assert mock_legacy_service.generate_report.call_args[1]['template_id'] == template_id
        assert mock_legacy_service.generate_report.call_args[1]['parameters'] == parameters
        
        # Vérification du résultat
        assert isinstance(result, Report)
        assert result.id == self.mock_legacy_report.id
        assert result.title == self.mock_legacy_report.title
        assert result.report_type == ReportType.NETWORK
        assert result.created_by == user_id
        assert isinstance(result.content, dict)
        assert "key" in result.content
    
    @patch('reporting.infrastructure.adapters.legacy_service_adapter.LegacyReportService')
    def test_generate_report_with_error(self, mock_legacy_service):
        """Teste la gestion des erreurs lors de la génération d'un rapport."""
        # Configuration du mock pour simuler une erreur
        mock_legacy_service.generate_report.side_effect = Exception("Test error")
        
        # Paramètres du test
        template_id = 1
        parameters = {"title": "Test Report"}
        user_id = 1
        
        # Vérifier que l'exception est bien levée
        with pytest.raises(ReportGenerationError):
            LegacyReportServiceAdapter.generate_report(
                template_id=template_id,
                parameters=parameters,
                user_id=user_id
            )
    
    @patch('reporting.infrastructure.adapters.legacy_service_adapter.LegacyReportService')
    def test_schedule_report(self, mock_legacy_service):
        """Teste la planification d'un rapport via l'adaptateur."""
        # Configuration du mock
        mock_legacy_service.schedule_report.return_value = self.mock_scheduled_report
        
        # Paramètres du test
        template_id = 1
        schedule_type = "daily"
        parameters = {"title": "Daily Report"}
        recipients = ["user@example.com"]
        
        # Appel de la méthode testée
        result = LegacyReportServiceAdapter.schedule_report(
            template_id=template_id,
            schedule_type=schedule_type,
            parameters=parameters,
            recipients=recipients
        )
        
        # Vérifications
        assert mock_legacy_service.schedule_report.called
        assert mock_legacy_service.schedule_report.call_args[1]['template_id'] == template_id
        assert mock_legacy_service.schedule_report.call_args[1]['schedule_type'] == schedule_type
        assert mock_legacy_service.schedule_report.call_args[1]['parameters'] == parameters
        assert mock_legacy_service.schedule_report.call_args[1]['recipients'] == recipients
        
        # Vérification du résultat
        assert isinstance(result, ScheduledReport)
        assert result.id == self.mock_scheduled_report.id
        assert result.frequency == Frequency.DAILY
        assert result.is_active == self.mock_scheduled_report.is_active
        assert result.template_id == template_id
        assert len(result.recipients) == 2  # Seuls les IDs numériques sont conservés
    
    @patch('reporting.infrastructure.adapters.legacy_service_adapter.LegacyReportService')
    def test_deliver_report(self, mock_legacy_service):
        """Teste la distribution d'un rapport via l'adaptateur."""
        # Configuration du mock
        mock_legacy_service.deliver_report.return_value = {"success": True}
        
        # Paramètres du test
        report_id = 1
        recipients = ["user1@example.com", "user2@example.com"]
        format_type = "pdf"
        
        # Appel de la méthode testée
        result = LegacyReportServiceAdapter.deliver_report(
            report_id=report_id,
            recipients=recipients,
            format_type=format_type
        )
        
        # Vérifications
        assert mock_legacy_service.deliver_report.called
        assert mock_legacy_service.deliver_report.call_args[1]['report_id'] == report_id
        assert mock_legacy_service.deliver_report.call_args[1]['recipients'] == recipients
        assert mock_legacy_service.deliver_report.call_args[1]['format_type'] == format_type
        
        # Vérification du résultat
        assert result is True
    
    @patch('reporting.infrastructure.adapters.legacy_service_adapter.LegacyReportService')
    def test_execute_scheduled_reports(self, mock_legacy_service):
        """Teste l'exécution des rapports planifiés via l'adaptateur."""
        # Configuration du mock
        mock_legacy_service.execute_scheduled_reports.return_value = {
            "success": True,
            "executed": 2,
            "failed": 0
        }
        
        # Appel de la méthode testée
        result = LegacyReportServiceAdapter.execute_scheduled_reports()
        
        # Vérifications
        assert mock_legacy_service.execute_scheduled_reports.called
        
        # Vérification du résultat
        assert result["success"] is True
        assert result["executed"] == 2
        assert result["failed"] == 0 