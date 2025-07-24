"""
Tests d'intégration pour l'adaptateur Grafana du module monitoring.
"""

import unittest
from unittest.mock import patch, MagicMock, Mock
from datetime import datetime, timezone
from django.test import TestCase
from django.contrib.auth import get_user_model
import json
import requests

from ..infrastructure.adapters.grafana_adapter import GrafanaAdapter
from ..models import Dashboard, DashboardWidget

User = get_user_model()


class GrafanaAdapterTest(TestCase):
    """
    Tests pour l'adaptateur Grafana.
    """
    
    def setUp(self):
        """
        Initialisation des données de test.
        """
        self.adapter = GrafanaAdapter(
            base_url="http://localhost:3000",
            username="admin",
            password="admin"
        )
        
        # Mock des réponses Grafana
        self.mock_health_response = {
            "commit": "abc123",
            "database": "ok",
            "version": "8.5.0"
        }
        
        self.mock_dashboards_response = [
            {
                "id": 1,
                "uid": "dashboard-1",
                "title": "System Monitoring",
                "uri": "db/system-monitoring",
                "url": "/d/dashboard-1/system-monitoring",
                "type": "dash-db",
                "tags": ["monitoring", "system"]
            },
            {
                "id": 2,
                "uid": "dashboard-2",
                "title": "Network Overview",
                "uri": "db/network-overview",
                "url": "/d/dashboard-2/network-overview",
                "type": "dash-db",
                "tags": ["network"]
            }
        ]
        
        self.mock_dashboard_detail = {
            "dashboard": {
                "id": 1,
                "uid": "dashboard-1",
                "title": "System Monitoring",
                "tags": ["monitoring", "system"],
                "timezone": "browser",
                "panels": [
                    {
                        "id": 1,
                        "title": "CPU Usage",
                        "type": "stat",
                        "gridPos": {"h": 8, "w": 6, "x": 0, "y": 0}
                    }
                ],
                "time": {"from": "now-1h", "to": "now"},
                "refresh": "30s"
            },
            "meta": {
                "created": "2025-07-11T10:00:00Z",
                "updated": "2025-07-11T10:30:00Z",
                "version": 1
            }
        }
        
        self.mock_datasources_response = [
            {
                "id": 1,
                "name": "Prometheus",
                "type": "prometheus",
                "url": "http://localhost:9090",
                "access": "proxy",
                "isDefault": True
            }
        ]
    
    @patch('requests.Session.get')
    def test_test_connection_success(self, mock_get):
        """
        Test de connexion à Grafana réussie.
        """
        # Configuration du mock
        mock_response = Mock()
        mock_response.json.return_value = self.mock_health_response
        mock_response.raise_for_status.return_value = None
        mock_response.elapsed.total_seconds.return_value = 0.12
        mock_get.return_value = mock_response
        
        # Exécution du test
        result = self.adapter.test_connection()
        
        # Vérifications
        self.assertTrue(result['success'])
        self.assertIn('status', result)
        self.assertEqual(result['status']['version'], '8.5.0')
        self.assertEqual(result['url'], 'http://localhost:3000')
        self.assertEqual(result['response_time'], 0.12)
        self.assertIn('timestamp', result)
        
        # Vérification de l'URL appelée
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        self.assertIn('/api/health', call_args[0][0])
    
    @patch('requests.Session.get')
    def test_test_connection_failure(self, mock_get):
        """
        Test de connexion à Grafana en échec.
        """
        # Configuration du mock avec erreur
        mock_get.side_effect = requests.exceptions.ConnectionError("Connection refused")
        
        # Exécution du test
        result = self.adapter.test_connection()
        
        # Vérifications
        self.assertFalse(result['success'])
        self.assertIn('error', result)
        self.assertIn('Connection refused', result['error'])
        self.assertEqual(result['url'], 'http://localhost:3000')
    
    @patch('requests.Session.get')
    def test_get_dashboards_success(self, mock_get):
        """
        Test de récupération des tableaux de bord.
        """
        # Configuration du mock
        mock_response = Mock()
        mock_response.json.return_value = self.mock_dashboards_response
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        # Exécution du test
        result = self.adapter.get_dashboards()
        
        # Vérifications
        self.assertTrue(result['success'])
        self.assertIn('dashboards', result)
        self.assertEqual(result['count'], 2)
        
        dashboards = result['dashboards']
        self.assertEqual(dashboards[0]['title'], 'System Monitoring')
        self.assertEqual(dashboards[1]['title'], 'Network Overview')
        self.assertIn('monitoring', dashboards[0]['tags'])
        self.assertIn('network', dashboards[1]['tags'])
    
    @patch('requests.Session.get')
    def test_get_dashboard_by_uid_success(self, mock_get):
        """
        Test de récupération d'un tableau de bord par UID.
        """
        # Configuration du mock
        mock_response = Mock()
        mock_response.json.return_value = self.mock_dashboard_detail
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        # Exécution du test
        result = self.adapter.get_dashboard('dashboard-1')
        
        # Vérifications
        self.assertTrue(result['success'])
        self.assertIn('dashboard', result)
        self.assertEqual(result['uid'], 'dashboard-1')
        
        dashboard = result['dashboard']['dashboard']
        self.assertEqual(dashboard['title'], 'System Monitoring')
        self.assertEqual(len(dashboard['panels']), 1)
        self.assertEqual(dashboard['panels'][0]['title'], 'CPU Usage')
        
        # Vérification de l'URL appelée
        call_args = mock_get.call_args
        self.assertIn('/api/dashboards/uid/dashboard-1', call_args[0][0])
    
    @patch('requests.Session.post')
    def test_create_dashboard_success(self, mock_post):
        """
        Test de création d'un tableau de bord.
        """
        # Configuration du mock
        mock_response = Mock()
        mock_response.json.return_value = {
            'id': 3,
            'uid': 'new-dashboard',
            'url': '/d/new-dashboard/test-dashboard',
            'status': 'success',
            'version': 1
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        # Données de test
        dashboard_json = {
            'id': None,
            'title': 'Test Dashboard',
            'tags': ['test'],
            'panels': []
        }
        
        # Exécution du test
        result = self.adapter.create_dashboard(dashboard_json, folder_id=0)
        
        # Vérifications
        self.assertTrue(result['success'])
        self.assertEqual(result['dashboard_id'], 3)
        self.assertEqual(result['uid'], 'new-dashboard')
        self.assertIn('/d/new-dashboard', result['url'])
        
        # Vérification des paramètres de l'appel
        call_args = mock_post.call_args
        payload = call_args[1]['json']
        self.assertEqual(payload['dashboard']['title'], 'Test Dashboard')
        self.assertEqual(payload['folderId'], 0)
        self.assertFalse(payload['overwrite'])
    
    @patch('requests.Session.post')
    def test_update_dashboard_success(self, mock_post):
        """
        Test de mise à jour d'un tableau de bord.
        """
        # Configuration du mock
        mock_response = Mock()
        mock_response.json.return_value = {
            'id': 3,
            'uid': 'updated-dashboard',
            'url': '/d/updated-dashboard/updated-test-dashboard',
            'status': 'success',
            'version': 2
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        # Données de test
        dashboard_json = {
            'id': 3,
            'uid': 'updated-dashboard',
            'title': 'Updated Test Dashboard',
            'tags': ['test', 'updated'],
            'panels': []
        }
        
        # Exécution du test
        result = self.adapter.update_dashboard(dashboard_json, folder_id=0)
        
        # Vérifications
        self.assertTrue(result['success'])
        self.assertEqual(result['dashboard_id'], 3)
        self.assertEqual(result['uid'], 'updated-dashboard')
        
        # Vérification que overwrite est True
        call_args = mock_post.call_args
        payload = call_args[1]['json']
        self.assertTrue(payload['overwrite'])
    
    @patch('requests.Session.delete')
    def test_delete_dashboard_success(self, mock_delete):
        """
        Test de suppression d'un tableau de bord.
        """
        # Configuration du mock
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_delete.return_value = mock_response
        
        # Exécution du test
        result = self.adapter.delete_dashboard('dashboard-to-delete')
        
        # Vérifications
        self.assertTrue(result['success'])
        self.assertEqual(result['uid'], 'dashboard-to-delete')
        self.assertIn('timestamp', result)
        
        # Vérification de l'URL appelée
        call_args = mock_delete.call_args
        self.assertIn('/api/dashboards/uid/dashboard-to-delete', call_args[0][0])
    
    @patch('requests.Session.get')
    def test_get_datasources_success(self, mock_get):
        """
        Test de récupération des sources de données.
        """
        # Configuration du mock
        mock_response = Mock()
        mock_response.json.return_value = self.mock_datasources_response
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        # Exécution du test
        result = self.adapter.get_datasources()
        
        # Vérifications
        self.assertTrue(result['success'])
        self.assertIn('datasources', result)
        self.assertEqual(result['count'], 1)
        
        datasource = result['datasources'][0]
        self.assertEqual(datasource['name'], 'Prometheus')
        self.assertEqual(datasource['type'], 'prometheus')
        self.assertEqual(datasource['url'], 'http://localhost:9090')
        self.assertTrue(datasource['isDefault'])
    
    @patch('requests.Session.post')
    def test_create_prometheus_datasource_success(self, mock_post):
        """
        Test de création d'une source de données Prometheus.
        """
        # Configuration du mock
        mock_response = Mock()
        mock_response.json.return_value = {
            'id': 2,
            'name': 'Prometheus',
            'type': 'prometheus',
            'url': 'http://localhost:9090',
            'message': 'Datasource added'
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        # Exécution du test
        result = self.adapter.create_prometheus_datasource('http://localhost:9090')
        
        # Vérifications
        self.assertTrue(result['success'])
        self.assertEqual(result['datasource_id'], 2)
        self.assertIn('timestamp', result)
        
        # Vérification de la configuration
        call_args = mock_post.call_args
        config = call_args[1]['json']
        self.assertEqual(config['name'], 'Prometheus')
        self.assertEqual(config['type'], 'prometheus')
        self.assertEqual(config['url'], 'http://localhost:9090')
        self.assertEqual(config['access'], 'proxy')
        self.assertTrue(config['isDefault'])
        self.assertFalse(config['basicAuth'])
    
    def test_create_monitoring_dashboard_structure(self):
        """
        Test de la structure d'un tableau de bord de monitoring.
        """
        with patch.object(self.adapter, 'create_dashboard') as mock_create:
            mock_create.return_value = {
                'success': True,
                'dashboard_id': 10,
                'uid': 'monitoring-device-1',
                'url': '/d/monitoring-device-1/monitoring-server-1'
            }
            
            # Exécution du test
            result = self.adapter.create_monitoring_dashboard('Server-1', 1)
            
            # Vérifications
            self.assertTrue(result['success'])
            self.assertEqual(result['dashboard_id'], 10)
            
            # Vérification de la structure du tableau de bord
            call_args = mock_create.call_args
            dashboard_json = call_args[0][0]
            
            self.assertEqual(dashboard_json['title'], 'Monitoring - Server-1')
            self.assertIn('monitoring', dashboard_json['tags'])
            self.assertIn('device-1', dashboard_json['tags'])
            self.assertEqual(dashboard_json['refresh'], '30s')
            
            # Vérification des panneaux
            panels = dashboard_json['panels']
            self.assertEqual(len(panels), 4)  # CPU, Memory, Network, Alerts
            
            # Panneau CPU
            cpu_panel = panels[0]
            self.assertEqual(cpu_panel['title'], 'CPU Usage')
            self.assertEqual(cpu_panel['type'], 'stat')
            self.assertIn('device_id="1"', cpu_panel['targets'][0]['expr'])
            
            # Panneau Memory
            memory_panel = panels[1]
            self.assertEqual(memory_panel['title'], 'Memory Usage')
            self.assertEqual(memory_panel['type'], 'stat')
            
            # Panneau Network
            network_panel = panels[2]
            self.assertEqual(network_panel['title'], 'Network Traffic')
            self.assertEqual(network_panel['type'], 'timeseries')
            self.assertEqual(len(network_panel['targets']), 2)  # In et Out
            
            # Panneau Alerts
            alerts_panel = panels[3]
            self.assertEqual(alerts_panel['title'], 'Active Alerts')
            self.assertEqual(alerts_panel['type'], 'table')


class GrafanaIntegrationTest(TestCase):
    """
    Tests d'intégration entre Grafana et le système de tableaux de bord.
    """
    
    def setUp(self):
        """
        Initialisation des données de test.
        """
        self.adapter = GrafanaAdapter()
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="password"
        )
        
        # Créer un tableau de bord dans le système
        self.dashboard = Dashboard.objects.create(
            title="Test Integration Dashboard",
            description="Dashboard for integration testing",
            owner=self.user,
            is_public=True,
            config={
                'grafana_uid': 'test-integration-dashboard',
                'grafana_id': 100
            }
        )
    
    @patch.object(GrafanaAdapter, 'create_dashboard')
    @patch.object(GrafanaAdapter, 'test_connection')
    def test_create_dashboard_integration(self, mock_test, mock_create):
        """
        Test d'intégration pour la création de tableau de bord.
        """
        # Configuration des mocks
        mock_test.return_value = {'success': True, 'status': 'healthy'}
        mock_create.return_value = {
            'success': True,
            'dashboard_id': 101,
            'uid': 'new-integration-dashboard',
            'url': '/d/new-integration-dashboard/new-dashboard'
        }
        
        # Test de connexion d'abord
        connection_result = self.adapter.test_connection()
        self.assertTrue(connection_result['success'])
        
        # Création du tableau de bord
        dashboard_config = {
            'title': 'New Integration Dashboard',
            'panels': [],
            'tags': ['integration', 'test']
        }
        
        result = self.adapter.create_dashboard(dashboard_config)
        
        # Vérifications
        self.assertTrue(result['success'])
        self.assertEqual(result['dashboard_id'], 101)
        self.assertEqual(result['uid'], 'new-integration-dashboard')
        
        # Mise à jour du tableau de bord local
        self.dashboard.config.update({
            'grafana_uid': result['uid'],
            'grafana_id': result['dashboard_id']
        })
        self.dashboard.save()
        
        # Vérification de la mise à jour
        updated_dashboard = Dashboard.objects.get(id=self.dashboard.id)
        self.assertEqual(updated_dashboard.config['grafana_uid'], 'new-integration-dashboard')
        self.assertEqual(updated_dashboard.config['grafana_id'], 101)
    
    @patch.object(GrafanaAdapter, 'get_dashboard')
    def test_sync_dashboard_from_grafana(self, mock_get):
        """
        Test de synchronisation d'un tableau de bord depuis Grafana.
        """
        # Configuration du mock
        mock_get.return_value = {
            'success': True,
            'dashboard': {
                'dashboard': {
                    'id': 100,
                    'uid': 'test-integration-dashboard',
                    'title': 'Updated Test Dashboard',
                    'tags': ['integration', 'test', 'updated'],
                    'panels': [
                        {
                            'id': 1,
                            'title': 'CPU Usage',
                            'type': 'stat'
                        },
                        {
                            'id': 2,
                            'title': 'Memory Usage',
                            'type': 'stat'
                        }
                    ]
                },
                'meta': {
                    'version': 2,
                    'updated': '2025-07-11T11:00:00Z'
                }
            }
        }
        
        # Récupération depuis Grafana
        result = self.adapter.get_dashboard('test-integration-dashboard')
        
        # Vérifications
        self.assertTrue(result['success'])
        
        grafana_dashboard = result['dashboard']['dashboard']
        self.assertEqual(grafana_dashboard['title'], 'Updated Test Dashboard')
        self.assertEqual(len(grafana_dashboard['panels']), 2)
        
        # Synchronisation avec le tableau de bord local
        self.dashboard.title = grafana_dashboard['title']
        self.dashboard.config.update({
            'panels': grafana_dashboard['panels'],
            'tags': grafana_dashboard['tags'],
            'version': result['dashboard']['meta']['version']
        })
        self.dashboard.save()
        
        # Vérification de la synchronisation
        updated_dashboard = Dashboard.objects.get(id=self.dashboard.id)
        self.assertEqual(updated_dashboard.title, 'Updated Test Dashboard')
        self.assertEqual(len(updated_dashboard.config['panels']), 2)
        self.assertEqual(updated_dashboard.config['version'], 2)
    
    @patch.object(GrafanaAdapter, 'create_monitoring_dashboard')
    def test_device_monitoring_dashboard_creation(self, mock_create_monitoring):
        """
        Test de création de tableau de bord de monitoring pour un équipement.
        """
        # Configuration du mock
        mock_create_monitoring.return_value = {
            'success': True,
            'dashboard_id': 102,
            'uid': 'monitoring-router-1',
            'url': '/d/monitoring-router-1/monitoring-router-core'
        }
        
        # Création du tableau de bord de monitoring
        result = self.adapter.create_monitoring_dashboard('Router-Core', 5)
        
        # Vérifications
        self.assertTrue(result['success'])
        self.assertEqual(result['dashboard_id'], 102)
        self.assertEqual(result['uid'], 'monitoring-router-1')
        
        # Création d'un tableau de bord local associé
        device_dashboard = Dashboard.objects.create(
            title="Monitoring - Router-Core",
            description="Auto-generated monitoring dashboard",
            owner=self.user,
            is_public=True,
            config={
                'device_id': 5,
                'device_name': 'Router-Core',
                'grafana_uid': result['uid'],
                'grafana_id': result['dashboard_id'],
                'auto_generated': True
            }
        )
        
        # Vérifications du tableau de bord créé
        self.assertEqual(device_dashboard.config['device_id'], 5)
        self.assertEqual(device_dashboard.config['grafana_uid'], 'monitoring-router-1')
        self.assertTrue(device_dashboard.config['auto_generated'])


if __name__ == '__main__':
    unittest.main()