"""
Configuration pytest pour les tests api_clients.
"""

import pytest
from unittest.mock import patch, MagicMock
from django.test import TestCase
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.fixture
def test_user():
    """Utilisateur de test standard."""
    return User.objects.create_user(
        username="api_test_user",
        email="apitest@example.com",
        password="password123"
    )


@pytest.fixture
def admin_user():
    """Utilisateur administrateur pour les tests."""
    return User.objects.create_superuser(
        username="api_admin",
        email="apiadmin@example.com",
        password="admin123"
    )


@pytest.fixture
def authenticated_client(client, test_user):
    """Client authentifié pour les tests API."""
    client.force_login(test_user)
    return client


@pytest.fixture
def mock_http_response():
    """Mock d'une réponse HTTP standard."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"status": "success", "data": {}}
    mock_response.text = '{"status": "success"}'
    mock_response.headers = {"Content-Type": "application/json"}
    return mock_response


@pytest.fixture
def mock_circuit_breaker():
    """Mock du circuit breaker."""
    with patch('api_clients.infrastructure.circuit_breaker.CircuitBreaker') as mock:
        mock.return_value.call.side_effect = lambda func, *args, **kwargs: func(*args, **kwargs)
        yield mock


@pytest.fixture
def mock_retry_handler():
    """Mock du gestionnaire de retry."""
    with patch('api_clients.infrastructure.retry_handler.RetryHandler') as mock:
        mock.return_value.execute.side_effect = lambda func, *args, **kwargs: func(*args, **kwargs)
        yield mock


@pytest.fixture
def mock_cache():
    """Mock du système de cache."""
    with patch('api_clients.infrastructure.cache.ResponseCache') as mock:
        cache_instance = mock.return_value
        cache_instance.get.return_value = None
        cache_instance.set.return_value = True
        cache_instance.delete.return_value = True
        yield cache_instance


@pytest.fixture
def gns3_server_config():
    """Configuration serveur GNS3 pour tests."""
    return {
        'host': 'localhost',
        'port': 3080,
        'protocol': 'http',
        'username': 'admin',
        'password': 'admin'
    }


@pytest.fixture
def prometheus_config():
    """Configuration Prometheus pour tests."""
    return {
        'host': 'localhost',
        'port': 9090,
        'protocol': 'http',
        'timeout': 30
    }


@pytest.fixture
def snmp_config():
    """Configuration SNMP pour tests."""
    return {
        'host': 'localhost',
        'port': 161,
        'community': 'public',
        'version': '2c',
        'timeout': 5
    }


@pytest.fixture
def mock_docker_service():
    """Mock des services Docker."""
    with patch('api_clients.infrastructure.docker_integration.DockerService') as mock:
        service = mock.return_value
        service.get_status.return_value = {
            'status': 'running',
            'health': 'healthy',
            'uptime': '2 days'
        }
        service.start.return_value = {'success': True}
        service.stop.return_value = {'success': True}
        service.restart.return_value = {'success': True}
        yield service


@pytest.fixture
def sample_network_data():
    """Données réseau d'exemple pour les tests."""
    return {
        'topology': {
            'nodes': [
                {'id': '1', 'name': 'Router-1', 'type': 'router'},
                {'id': '2', 'name': 'Switch-1', 'type': 'switch'},
                {'id': '3', 'name': 'PC-1', 'type': 'vpcs'}
            ],
            'links': [
                {'source': '1', 'target': '2'},
                {'source': '2', 'target': '3'}
            ]
        },
        'metrics': {
            'cpu_usage': 45.2,
            'memory_usage': 67.8,
            'network_traffic': 1024000
        },
        'alerts': [
            {
                'id': 1,
                'severity': 'warning',
                'message': 'High CPU usage detected',
                'timestamp': '2025-07-11T10:30:00Z'
            }
        ]
    }