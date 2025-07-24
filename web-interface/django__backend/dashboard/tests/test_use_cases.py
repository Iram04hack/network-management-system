"""
Tests unitaires pour les cas d'utilisation du module dashboard.

Ces tests vérifient la logique métier des cas d'utilisation
indépendamment de l'infrastructure.
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timedelta
from django.utils import timezone

from dashboard.application.use_cases import (
    GetDashboardOverviewUseCase,
    GetSystemHealthMetricsUseCase,
    GetNetworkOverviewUseCase,
    GetIntegratedTopologyUseCase,
    GetDeviceHealthStatusUseCase,
    GetConnectionStatusUseCase
)
from dashboard.domain.entities import (
    DashboardOverview,
    SystemHealthMetrics,
    AlertInfo,
    AlertSeverity,
    DeviceStatus
)

pytestmark = pytest.mark.django_db


class TestGetDashboardOverviewUseCase:
    """Tests pour le cas d'utilisation GetDashboardOverviewUseCase."""
    
    def test_execute_success(self):
        """Test d'exécution réussie du cas d'utilisation."""
        # Arrange
        mock_service = Mock()
        mock_service.get_dashboard_overview.return_value = {
            'devices': {'total': 10, 'active': 8},
            'security_alerts': [],
            'system_alerts': [],
            'performance': {'cpu': 45.2},
            'health_metrics': {'system_health': 0.85},
            'timestamp': timezone.now()
        }
        
        use_case = GetDashboardOverviewUseCase(mock_service)
        
        # Act
        result = use_case.execute()
        
        # Assert
        assert result is not None
        assert 'devices' in result
        assert 'security_alerts' in result
        assert 'system_alerts' in result
        assert 'performance' in result
        assert 'health_metrics' in result
        assert 'timestamp' in result
        mock_service.get_dashboard_overview.assert_called_once()
    
    def test_execute_with_service_error(self):
        """Test de gestion d'erreur du service."""
        # Arrange
        mock_service = Mock()
        mock_service.get_dashboard_overview.side_effect = Exception("Service error")
        
        use_case = GetDashboardOverviewUseCase(mock_service)
        
        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            use_case.execute()
        
        assert "Service error" in str(exc_info.value)


class TestGetSystemHealthMetricsUseCase:
    """Tests pour le cas d'utilisation GetSystemHealthMetricsUseCase."""
    
    def test_execute_returns_health_metrics(self):
        """Test de récupération des métriques de santé."""
        # Arrange
        mock_service = Mock()
        expected_metrics = {
            'system_health': 0.85,
            'network_health': 0.90,
            'security_health': 0.75
        }
        mock_service.get_system_health_metrics.return_value = expected_metrics
        
        use_case = GetSystemHealthMetricsUseCase(mock_service)
        
        # Act
        result = use_case.execute()
        
        # Assert
        assert result == expected_metrics
        assert 'system_health' in result
        assert 'network_health' in result
        assert 'security_health' in result
        mock_service.get_system_health_metrics.assert_called_once()
    
    def test_execute_validates_metric_ranges(self):
        """Test de validation des plages de métriques."""
        # Arrange
        mock_service = Mock()
        mock_service.get_system_health_metrics.return_value = {
            'system_health': 0.85,
            'network_health': 0.90,
            'security_health': 0.75
        }
        
        use_case = GetSystemHealthMetricsUseCase(mock_service)
        
        # Act
        result = use_case.execute()
        
        # Assert
        for metric_name, value in result.items():
            assert 0 <= value <= 1, f"{metric_name} doit être entre 0 et 1"


class TestGetNetworkOverviewUseCase:
    """Tests pour le cas d'utilisation GetNetworkOverviewUseCase."""
    
    def test_execute_returns_network_data(self):
        """Test de récupération des données réseau."""
        # Arrange
        mock_service = Mock()
        expected_data = {
            'devices': {'total': 15, 'active': 12},
            'interfaces': {'total': 45, 'up': 40},
            'qos': {'policies': 5, 'active_policies': 3},
            'alerts': [],
            'timestamp': timezone.now()
        }
        mock_service.get_network_overview.return_value = expected_data
        
        use_case = GetNetworkOverviewUseCase(mock_service)
        
        # Act
        result = use_case.execute()
        
        # Assert
        assert result == expected_data
        assert 'devices' in result
        assert 'interfaces' in result
        assert 'qos' in result
        assert 'alerts' in result
        mock_service.get_network_overview.assert_called_once()


class TestGetIntegratedTopologyUseCase:
    """Tests pour le cas d'utilisation GetIntegratedTopologyUseCase."""
    
    def test_execute_with_valid_topology_id(self):
        """Test avec un ID de topologie valide."""
        # Arrange
        topology_id = 123
        mock_service = Mock()
        expected_data = {
            'topology_id': topology_id,
            'name': 'Test Topology',
            'nodes': [{'id': 1, 'name': 'Device1'}],
            'connections': [{'from': 1, 'to': 2}],
            'health_summary': {'healthy': 5, 'warning': 1, 'critical': 0},
            'last_updated': timezone.now()
        }
        mock_service.get_integrated_topology.return_value = expected_data
        
        use_case = GetIntegratedTopologyUseCase(mock_service)
        
        # Act
        result = use_case.execute(topology_id)
        
        # Assert
        assert result == expected_data
        assert result['topology_id'] == topology_id
        mock_service.get_integrated_topology.assert_called_once_with(topology_id)
    
    def test_execute_with_invalid_topology_id(self):
        """Test avec un ID de topologie invalide."""
        # Arrange
        topology_id = 999
        mock_service = Mock()
        mock_service.get_integrated_topology.side_effect = ValueError("Topology not found")
        
        use_case = GetIntegratedTopologyUseCase(mock_service)
        
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            use_case.execute(topology_id)
        
        assert "Topology not found" in str(exc_info.value)


class TestGetDeviceHealthStatusUseCase:
    """Tests pour le cas d'utilisation GetDeviceHealthStatusUseCase."""
    
    @pytest.mark.parametrize("expected_status", [
        DeviceStatus.HEALTHY,
        DeviceStatus.WARNING,
        DeviceStatus.CRITICAL,
        DeviceStatus.INACTIVE,
        DeviceStatus.UNKNOWN
    ])
    def test_execute_returns_valid_status(self, expected_status):
        """Test de retour de statuts valides."""
        # Arrange
        device_id = 456
        mock_service = Mock()
        mock_service.get_device_health_status.return_value = expected_status
        
        use_case = GetDeviceHealthStatusUseCase(mock_service)
        
        # Act
        result = use_case.execute(device_id)
        
        # Assert
        assert result == expected_status
        assert result in [status.value for status in DeviceStatus]
        mock_service.get_device_health_status.assert_called_once_with(device_id)
    
    def test_execute_with_nonexistent_device(self):
        """Test avec un équipement inexistant."""
        # Arrange
        device_id = 999
        mock_service = Mock()
        mock_service.get_device_health_status.side_effect = ValueError("Device not found")
        
        use_case = GetDeviceHealthStatusUseCase(mock_service)
        
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            use_case.execute(device_id)
        
        assert "Device not found" in str(exc_info.value)


class TestGetConnectionStatusUseCase:
    """Tests pour le cas d'utilisation GetConnectionStatusUseCase."""
    
    def test_execute_returns_connection_status(self):
        """Test de récupération du statut de connexion."""
        # Arrange
        connection_id = 789
        expected_status = 'healthy'
        mock_service = Mock()
        mock_service.get_connection_status.return_value = expected_status
        
        use_case = GetConnectionStatusUseCase(mock_service)
        
        # Act
        result = use_case.execute(connection_id)
        
        # Assert
        assert result == expected_status
        mock_service.get_connection_status.assert_called_once_with(connection_id)
    
    def test_execute_with_invalid_connection(self):
        """Test avec une connexion invalide."""
        # Arrange
        connection_id = 999
        mock_service = Mock()
        mock_service.get_connection_status.side_effect = ValueError("Connection not found")
        
        use_case = GetConnectionStatusUseCase(mock_service)
        
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            use_case.execute(connection_id)
        
        assert "Connection not found" in str(exc_info.value)


class TestUseCasesIntegration:
    """Tests d'intégration entre les cas d'utilisation."""
    
    def test_dashboard_overview_includes_health_metrics(self):
        """Test que la vue d'ensemble inclut les métriques de santé."""
        # Arrange
        mock_dashboard_service = Mock()
        mock_dashboard_service.get_dashboard_overview.return_value = {
            'devices': {'total': 10},
            'security_alerts': [],
            'system_alerts': [],
            'performance': {},
            'health_metrics': {
                'system_health': 0.85,
                'network_health': 0.90,
                'security_health': 0.75
            },
            'timestamp': timezone.now()
        }
        
        dashboard_use_case = GetDashboardOverviewUseCase(mock_dashboard_service)
        health_use_case = GetSystemHealthMetricsUseCase(mock_dashboard_service)
        
        # Act
        dashboard_result = dashboard_use_case.execute()
        
        # Assert
        assert 'health_metrics' in dashboard_result
        health_metrics = dashboard_result['health_metrics']
        assert 'system_health' in health_metrics
        assert 'network_health' in health_metrics
        assert 'security_health' in health_metrics
    
    def test_error_handling_consistency(self):
        """Test de cohérence dans la gestion d'erreurs."""
        # Arrange
        mock_service = Mock()
        mock_service.get_dashboard_overview.side_effect = Exception("Database error")
        mock_service.get_system_health_metrics.side_effect = Exception("Database error")
        
        dashboard_use_case = GetDashboardOverviewUseCase(mock_service)
        health_use_case = GetSystemHealthMetricsUseCase(mock_service)
        
        # Act & Assert
        with pytest.raises(Exception) as dashboard_exc:
            dashboard_use_case.execute()
        
        with pytest.raises(Exception) as health_exc:
            health_use_case.execute()
        
        # Les deux doivent lever la même exception
        assert str(dashboard_exc.value) == str(health_exc.value)