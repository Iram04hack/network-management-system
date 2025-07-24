"""
Tests pour les cas d'utilisation de base du module reporting.

Ce module contient les tests unitaires pour les cas d'utilisation
de base du module reporting.
"""

import pytest
from unittest.mock import MagicMock, patch

from reporting.application.use_cases import (
    GenerateReportUseCase, 
    GetReportUseCase,
    ListReportsUseCase,
    ScheduleReportUseCase,
    DeleteReportUseCase
)

class TestGenerateReportUseCase:
    """Tests pour le cas d'utilisation GenerateReportUseCase."""
    
    def test_execute_with_valid_data(self, mock_report_repository, 
                                     mock_report_service):
        """
        Teste l'exécution du cas d'utilisation avec des données valides.
        """
        # Arrange
        mock_storage = MagicMock()
        mock_storage.store.return_value = "/path/to/report.pdf"
        
        mock_report_generator = MagicMock()
        mock_report_generator.generate_report.return_value = {"data": "report content"}
        
        use_case = GenerateReportUseCase(
            report_repository=mock_report_repository,
            report_generator=mock_report_generator,
            report_storage=mock_storage
        )
        
        report_type = "network"
        parameters = {
            "title": "Network Status Report",
            "description": "Daily network status report",
            "format": "pdf"
        }
        user_id = 1
        
        # Act
        result = use_case.execute(report_type, parameters, user_id)
        
        # Assert
        mock_report_generator.generate_report.assert_called_once_with(report_type, parameters)
        mock_storage.store.assert_called_once()
        mock_report_repository.create.assert_called_once()
        assert result == mock_report_repository.create.return_value
    
    def test_execute_raises_error_with_invalid_type(self, mock_report_repository, 
                                                   mock_report_service):
        """
        Teste qu'une exception est levée si le type de rapport est invalide.
        """
        # Arrange
        mock_storage = MagicMock()
        mock_report_generator = MagicMock()
        
        use_case = GenerateReportUseCase(
            report_repository=mock_report_repository,
            report_generator=mock_report_generator,
            report_storage=mock_storage
        )
        
        report_type = ""  # Type invalide (vide)
        parameters = {"title": "Report", "format": "pdf"}
        user_id = 1
        
        # Act & Assert
        with pytest.raises(ValueError):
            use_case.execute(report_type, parameters, user_id)
            

class TestGetReportUseCase:
    """Tests pour le cas d'utilisation GetReportUseCase."""
    
    def test_execute_with_existing_report(self, mock_report_repository):
        """
        Teste la récupération d'un rapport existant.
        """
        # Arrange
        use_case = GetReportUseCase(report_repository=mock_report_repository)
        report_id = 1
        
        # Act
        result = use_case.execute(report_id)
        
        # Assert
        mock_report_repository.get_by_id.assert_called_once_with(report_id)
        assert result == mock_report_repository.get_by_id.return_value
    
    def test_execute_raises_error_with_nonexistent_report(self, mock_report_repository):
        """
        Teste qu'une exception est levée si le rapport n'existe pas.
        """
        # Arrange
        mock_report_repository.get_by_id.return_value = None
        
        use_case = GetReportUseCase(report_repository=mock_report_repository)
        report_id = 999  # ID inexistant
        
        # Act & Assert
        with pytest.raises(ValueError):
            use_case.execute(report_id)


class TestListReportsUseCase:
    """Tests pour le cas d'utilisation ListReportsUseCase."""
    
    def test_execute_without_filters(self, mock_report_repository):
        """
        Teste la récupération de tous les rapports sans filtres.
        """
        # Arrange
        use_case = ListReportsUseCase(report_repository=mock_report_repository)
        
        # Act
        result = use_case.execute()
        
        # Assert
        mock_report_repository.list.assert_called_once_with(None)
        assert result == mock_report_repository.list.return_value
    
    def test_execute_with_filters(self, mock_report_repository):
        """
        Teste la récupération des rapports avec filtres.
        """
        # Arrange
        use_case = ListReportsUseCase(report_repository=mock_report_repository)
        filters = {"report_type": "network", "status": "completed"}
        
        # Act
        result = use_case.execute(filters)
        
        # Assert
        mock_report_repository.list.assert_called_once_with(filters)
        assert result == mock_report_repository.list.return_value


class TestDeleteReportUseCase:
    """Tests pour le cas d'utilisation DeleteReportUseCase."""
    
    def test_execute_with_existing_report(self, mock_report_repository):
        """
        Teste la suppression d'un rapport existant.
        """
        # Arrange
        mock_report_repository.delete.return_value = True
        
        use_case = DeleteReportUseCase(report_repository=mock_report_repository)
        report_id = 1
        
        # Act
        result = use_case.execute(report_id)
        
        # Assert
        mock_report_repository.get_by_id.assert_called_once_with(report_id)
        mock_report_repository.delete.assert_called_once_with(report_id)
        assert result == True
    
    def test_execute_raises_error_with_nonexistent_report(self, mock_report_repository):
        """
        Teste qu'une exception est levée si le rapport n'existe pas.
        """
        # Arrange
        mock_report_repository.get_by_id.return_value = None
        
        use_case = DeleteReportUseCase(report_repository=mock_report_repository)
        report_id = 999  # ID inexistant
        
        # Act & Assert
        with pytest.raises(ValueError):
            use_case.execute(report_id)
            
    def test_execute_returns_false_on_delete_failure(self, mock_report_repository):
        """
        Teste que la méthode renvoie False si la suppression échoue.
        """
        # Arrange
        mock_report_repository.delete.return_value = False
        
        use_case = DeleteReportUseCase(report_repository=mock_report_repository)
        report_id = 1
        
        # Act
        result = use_case.execute(report_id)
        
        # Assert
        mock_report_repository.get_by_id.assert_called_once_with(report_id)
        mock_report_repository.delete.assert_called_once_with(report_id)
        assert result == False 