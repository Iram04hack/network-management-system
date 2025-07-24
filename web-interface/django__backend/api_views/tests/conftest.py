"""
Configuration des fixtures pour les tests du module API Views.

Ce module fournit les fixtures communes utilisées par tous les tests
du module api_views.
"""

import os
import django
from django.conf import settings

# Configuration Django pour les tests
if not settings.configured:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nms_backend.settings')
    django.setup()

import pytest
from datetime import datetime, timedelta
from django.contrib.auth.models import User
from django.test import RequestFactory
from rest_framework.test import APIClient


@pytest.fixture
def api_client():
    """Client API pour les tests."""
    return APIClient()


@pytest.fixture
def request_factory():
    """Factory pour créer des requêtes HTTP."""
    return RequestFactory()


@pytest.fixture
def admin_user():
    """Utilisateur administrateur pour les tests."""
    return User.objects.create_user(
        username='admin_test',
        email='admin@test.com',
        password='testpass123',
        is_staff=True,
        is_superuser=True
    )


@pytest.fixture
def regular_user():
    """Utilisateur régulier pour les tests."""
    return User.objects.create_user(
        username='user_test',
        email='user@test.com',
        password='testpass123',
        is_staff=False,
        is_superuser=False
    )


@pytest.fixture
def sample_dashboard_data():
    """Données d'exemple pour les tests de dashboard."""
    return {
        'dashboard_type': 'system-overview',
        'time_range': '24h',
        'filters': {
            'severity': ['critical', 'warning'],
            'device_types': ['router', 'switch']
        },
        'refresh_interval': 300
    }


@pytest.fixture
def sample_widget_data():
    """Données d'exemple pour les tests de widget."""
    return {
        'id': 'widget-test-1',
        'type': 'alerts',
        'title': 'Test Alerts Widget',
        'position': {'x': 0, 'y': 0},
        'size': {'width': 6, 'height': 4},
        'configuration': {
            'severities': ['critical', 'warning'],
            'max_items': 10
        },
        'refresh_interval': 60
    }


@pytest.fixture
def sample_custom_dashboard():
    """Données d'exemple pour un dashboard personnalisé."""
    return {
        'name': 'Mon Dashboard Test',
        'description': 'Dashboard de test pour les tests unitaires',
        'layout': 'grid',
        'shared': False,
        'widgets': [
            {
                'id': 'widget-1',
                'type': 'alerts',
                'title': 'Alertes Critiques',
                'position': {'x': 0, 'y': 0},
                'size': {'width': 6, 'height': 4},
                'configuration': {
                    'severities': ['critical'],
                    'max_items': 5
                }
            },
            {
                'id': 'widget-2',
                'type': 'devices',
                'title': 'État des Équipements',
                'position': {'x': 6, 'y': 0},
                'size': {'width': 6, 'height': 4},
                'configuration': {
                    'device_types': ['router', 'switch'],
                    'status_filter': ['online', 'offline']
                }
            }
        ],
        'configuration': {
            'auto_refresh': True,
            'refresh_interval': 300,
            'theme': 'dark'
        }
    }


@pytest.fixture
def sample_device_data():
    """Données d'exemple pour les tests d'équipements."""
    return {
        'id': '123e4567-e89b-12d3-a456-426614174000',
        'name': 'Router-Test-01',
        'device_type': 'router',
        'ip_address': '192.168.1.1',
        'management_ip': '192.168.100.1',
        'status': 'online',
        'location': 'Datacenter-A',
        'vendor': 'Cisco',
        'model': 'ISR4331',
        'firmware_version': '16.09.04',
        'configuration': {
            'interfaces': [
                {
                    'name': 'GigabitEthernet0/0/0',
                    'ip': '192.168.1.1/24',
                    'status': 'up'
                }
            ],
            'routing': {
                'protocol': 'OSPF',
                'area': '0.0.0.0'
            }
        },
        'metrics': {
            'cpu_usage': 25.5,
            'memory_usage': 45.2,
            'uptime': '30 days, 5 hours',
            'last_seen': datetime.now().isoformat()
        }
    }


@pytest.fixture
def sample_search_data():
    """Données d'exemple pour les tests de recherche."""
    return {
        'query': 'router cisco',
        'resource_types': ['devices', 'configurations'],
        'filters': {
            'device_type': 'router',
            'vendor': 'cisco',
            'status': 'online'
        },
        'sort_by': 'name',
        'sort_order': 'asc',
        'page_size': 20
    }


@pytest.fixture
def sample_bulk_operation_data():
    """Données d'exemple pour les opérations en lot."""
    return {
        'operation': 'backup',
        'devices': [
            '123e4567-e89b-12d3-a456-426614174000',
            '123e4567-e89b-12d3-a456-426614174001'
        ],
        'parameters': {
            'backup_type': 'full',
            'compression': True,
            'encryption': True
        }
    }


@pytest.fixture
def sample_metrics_data():
    """Données d'exemple pour les métriques."""
    return {
        'device_id': '123e4567-e89b-12d3-a456-426614174000',
        'timestamp': datetime.now().isoformat(),
        'cpu_usage': 35.7,
        'memory_usage': 62.3,
        'disk_usage': 78.1,
        'network_io': {
            'bytes_in': 1024000,
            'bytes_out': 2048000,
            'packets_in': 1500,
            'packets_out': 1800
        },
        'uptime': '45 days, 12 hours, 30 minutes',
        'temperature': 42.5,
        'metrics': {
            'interface_utilization': {
                'GigabitEthernet0/0/0': 85.2,
                'GigabitEthernet0/0/1': 23.7
            },
            'routing_table_size': 150000,
            'arp_table_size': 2500
        }
    }
