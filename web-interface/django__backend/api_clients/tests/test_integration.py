"""
Tests d'intégration consolidés pour le module api_clients.
Remplace et consolide : test_integration_network_clients.py, test_gns3_client_complete.py, 
test_snmp_client_complete.py, test_netflow_client_complete.py
"""

import unittest
from unittest.mock import patch, MagicMock, Mock
from django.test import TestCase
import requests
import json
from datetime import datetime, timezone

from ..network.gns3_client import GNS3Client
from ..network.snmp_client import SNMPClient
from ..monitoring.prometheus_client import PrometheusClient


class NetworkClientsIntegrationTest(TestCase):
    """Tests d'intégration pour tous les clients réseau."""
    
    def setUp(self):
        """Configuration commune pour les tests."""
        self.gns3_config = {
            'host': 'localhost',
            'port': 3080,
            'protocol': 'http',
            'timeout': 10
        }
        
        self.snmp_config = {
            'host': 'localhost',
            'port': 161,
            'community': 'public',
            'version': '2c',
            'timeout': 5
        }
        
        self.prometheus_config = {
            'host': 'localhost',
            'port': 9090,
            'protocol': 'http',
            'timeout': 30
        }
    
    @patch('requests.Session.get')
    def test_gns3_client_integration(self, mock_get):
        """Test d'intégration complète du client GNS3."""
        # Configuration du mock pour la version
        mock_response = Mock()
        mock_response.json.return_value = {
            'version': '2.2.46',
            'local_server': True
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        # Test de connexion
        client = GNS3Client(**self.gns3_config)
        version_info = client.get_version()
        
        self.assertIn('version', version_info)
        self.assertEqual(version_info['version'], '2.2.46')
        
        # Vérification de l'URL appelée
        expected_url = f"{self.gns3_config['protocol']}://{self.gns3_config['host']}:{self.gns3_config['port']}/v2/version"
        mock_get.assert_called_with(expected_url, timeout=self.gns3_config['timeout'])
    
    @patch('requests.Session.get')
    @patch('requests.Session.post')
    def test_gns3_project_workflow(self, mock_post, mock_get):
        """Test du workflow complet de gestion de projet GNS3."""
        # Mock pour création de projet
        mock_post.return_value.json.return_value = {
            'project_id': 'test-project-123',
            'name': 'Test Project',
            'status': 'opened'
        }
        mock_post.return_value.raise_for_status.return_value = None
        
        # Mock pour récupération de projet
        mock_get.return_value.json.return_value = {
            'project_id': 'test-project-123',
            'name': 'Test Project',
            'nodes': [],
            'links': []
        }
        mock_get.return_value.raise_for_status.return_value = None
        
        client = GNS3Client(**self.gns3_config)
        
        # Créer un projet
        project_data = {'name': 'Test Project'}
        created_project = client.create_project(project_data)
        
        self.assertEqual(created_project['project_id'], 'test-project-123')
        self.assertEqual(created_project['name'], 'Test Project')
        
        # Récupérer le projet
        project_info = client.get_project('test-project-123')
        
        self.assertEqual(project_info['project_id'], 'test-project-123')
        self.assertIn('nodes', project_info)
        self.assertIn('links', project_info)
    
    @patch('pysnmp.hlapi.getCmd')
    def test_snmp_client_integration(self, mock_snmp_get):
        """Test d'intégration du client SNMP."""
        # Configuration du mock SNMP
        mock_snmp_get.return_value = iter([
            (None, None, None, [
                ('1.3.6.1.2.1.1.1.0', 'Test Device Description'),
                ('1.3.6.1.2.1.1.5.0', 'test-device')
            ])
        ])
        
        client = SNMPClient(**self.snmp_config)
        
        # Test de récupération d'informations système
        result = client.get_system_info(self.snmp_config['host'])
        
        self.assertIn('description', result)
        self.assertIn('hostname', result)
        self.assertEqual(result['description'], 'Test Device Description')
        self.assertEqual(result['hostname'], 'test-device')
    
    @patch('pysnmp.hlapi.nextCmd')
    def test_snmp_interface_discovery(self, mock_snmp_walk):
        """Test de découverte d'interfaces SNMP."""
        # Mock pour découverte d'interfaces
        mock_snmp_walk.return_value = iter([
            (None, None, None, [
                ('1.3.6.1.2.1.2.2.1.2.1', 'FastEthernet0/0'),
                ('1.3.6.1.2.1.2.2.1.2.2', 'FastEthernet0/1'),
                ('1.3.6.1.2.1.2.2.1.8.1', 1),  # up
                ('1.3.6.1.2.1.2.2.1.8.2', 2),  # down
            ])
        ])
        
        client = SNMPClient(**self.snmp_config)
        interfaces = client.discover_interfaces(self.snmp_config['host'])\n        \n        self.assertEqual(len(interfaces), 2)\n        self.assertEqual(interfaces[0]['name'], 'FastEthernet0/0')\n        self.assertEqual(interfaces[0]['status'], 'up')\n        self.assertEqual(interfaces[1]['name'], 'FastEthernet0/1')\n        self.assertEqual(interfaces[1]['status'], 'down')\n    \n    @patch('requests.Session.get')\n    def test_prometheus_client_integration(self, mock_get):\n        \"\"\"Test d'intégration du client Prometheus.\"\"\"\n        # Mock pour requête Prometheus\n        mock_response = Mock()\n        mock_response.json.return_value = {\n            'status': 'success',\n            'data': {\n                'resultType': 'vector',\n                'result': [\n                    {\n                        'metric': {'instance': 'localhost:9100'},\n                        'value': [1641024000, '45.5']\n                    }\n                ]\n            }\n        }\n        mock_response.raise_for_status.return_value = None\n        mock_get.return_value = mock_response\n        \n        client = PrometheusClient(**self.prometheus_config)\n        \n        # Test de requête instantanée\n        result = client.query_instant('up')\n        \n        self.assertTrue(result['success'])\n        self.assertEqual(result['data']['status'], 'success')\n        self.assertEqual(len(result['data']['data']['result']), 1)\n        \n        # Vérification de l'URL\n        expected_url = f\"{self.prometheus_config['protocol']}://{self.prometheus_config['host']}:{self.prometheus_config['port']}/api/v1/query\"\n        mock_get.assert_called_once()\n        call_args = mock_get.call_args\n        self.assertEqual(call_args[0][0], expected_url)\n    \n    @patch('requests.Session.get')\n    def test_prometheus_metrics_collection(self, mock_get):\n        \"\"\"Test de collecte de métriques Prometheus.\"\"\"\n        # Mock pour récupération de métriques\n        mock_response = Mock()\n        mock_response.json.return_value = {\n            'status': 'success',\n            'data': [\n                'up',\n                'node_cpu_seconds_total',\n                'node_memory_MemTotal_bytes'\n            ]\n        }\n        mock_response.raise_for_status.return_value = None\n        mock_get.return_value = mock_response\n        \n        client = PrometheusClient(**self.prometheus_config)\n        \n        # Test de récupération de la liste des métriques\n        result = client.get_metrics_list()\n        \n        self.assertTrue(result['success'])\n        self.assertIn('up', result['metrics'])\n        self.assertIn('node_cpu_seconds_total', result['metrics'])\n        self.assertEqual(len(result['metrics']), 3)\n\n\nclass ClientsResillienceTest(TestCase):\n    \"\"\"Tests de résilience pour tous les clients API.\"\"\"\n    \n    def setUp(self):\n        \"\"\"Configuration pour les tests de résilience.\"\"\"\n        self.clients_config = {\n            'gns3': {\n                'host': 'localhost',\n                'port': 3080,\n                'timeout': 5\n            },\n            'prometheus': {\n                'host': 'localhost', \n                'port': 9090,\n                'timeout': 5\n            }\n        }\n    \n    @patch('requests.Session.get')\n    def test_connection_timeout_handling(self, mock_get):\n        \"\"\"Test de gestion des timeouts de connexion.\"\"\"\n        # Simuler un timeout\n        mock_get.side_effect = requests.exceptions.Timeout(\"Connection timeout\")\n        \n        client = GNS3Client(**self.clients_config['gns3'])\n        \n        # Le client doit gérer gracieusement le timeout\n        result = client.get_version()\n        \n        # Vérifier que l'erreur est bien gérée\n        self.assertFalse(result.get('success', True))\n        self.assertIn('error', result)\n        self.assertIn('timeout', result['error'].lower())\n    \n    @patch('requests.Session.get')\n    def test_connection_error_handling(self, mock_get):\n        \"\"\"Test de gestion des erreurs de connexion.\"\"\"\n        # Simuler une erreur de connexion\n        mock_get.side_effect = requests.exceptions.ConnectionError(\"Connection refused\")\n        \n        client = PrometheusClient(**self.clients_config['prometheus'])\n        \n        # Test de gestion d'erreur\n        result = client.query_instant('up')\n        \n        self.assertFalse(result['success'])\n        self.assertIn('error', result)\n        self.assertIn('connection', result['error'].lower())\n    \n    @patch('requests.Session.get')\n    def test_http_error_handling(self, mock_get):\n        \"\"\"Test de gestion des erreurs HTTP.\"\"\"\n        # Simuler une erreur HTTP 500\n        mock_response = Mock()\n        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(\"500 Internal Server Error\")\n        mock_get.return_value = mock_response\n        \n        client = GNS3Client(**self.clients_config['gns3'])\n        \n        # Test de gestion d'erreur HTTP\n        result = client.get_projects()\n        \n        self.assertFalse(result.get('success', True))\n        self.assertIn('error', result)\n    \n    @patch('pysnmp.hlapi.getCmd')\n    def test_snmp_timeout_handling(self, mock_snmp):\n        \"\"\"Test de gestion des timeouts SNMP.\"\"\"\n        # Simuler un timeout SNMP\n        mock_snmp.side_effect = Exception(\"SNMP timeout\")\n        \n        client = SNMPClient(\n            host='localhost',\n            community='public',\n            timeout=1  # Timeout court pour forcer l'erreur\n        )\n        \n        result = client.get_system_info('unreachable-host')\n        \n        self.assertFalse(result.get('success', True))\n        self.assertIn('error', result)\n\n\nclass ClientsPerformanceTest(TestCase):\n    \"\"\"Tests de performance pour les clients API.\"\"\"\n    \n    @patch('requests.Session.get')\n    def test_concurrent_requests_performance(self, mock_get):\n        \"\"\"Test de performance des requêtes concurrentes.\"\"\"\n        import threading\n        import time\n        \n        # Mock réponse rapide\n        mock_response = Mock()\n        mock_response.json.return_value = {'status': 'success'}\n        mock_response.raise_for_status.return_value = None\n        mock_get.return_value = mock_response\n        \n        client = PrometheusClient(host='localhost', port=9090)\n        \n        # Fonction pour exécuter des requêtes\n        results = []\n        \n        def make_request():\n            start_time = time.time()\n            result = client.query_instant('up')\n            end_time = time.time()\n            results.append({\n                'success': result.get('success', False),\n                'duration': end_time - start_time\n            })\n        \n        # Lancer 10 requêtes concurrentes\n        threads = []\n        for _ in range(10):\n            thread = threading.Thread(target=make_request)\n            threads.append(thread)\n            thread.start()\n        \n        # Attendre la fin de toutes les requêtes\n        for thread in threads:\n            thread.join()\n        \n        # Vérifications\n        self.assertEqual(len(results), 10)\n        successful_requests = [r for r in results if r['success']]\n        self.assertEqual(len(successful_requests), 10)\n        \n        # Vérifier que toutes les requêtes ont été rapides (< 1 seconde)\n        avg_duration = sum(r['duration'] for r in results) / len(results)\n        self.assertLess(avg_duration, 1.0)\n    \n    @patch('requests.Session.get')\n    def test_large_response_handling(self, mock_get):\n        \"\"\"Test de gestion des réponses volumineuses.\"\"\"\n        # Simuler une réponse volumineuse\n        large_data = {\n            'status': 'success',\n            'data': {\n                'result': [\n                    {\n                        'metric': {'instance': f'host-{i}'},\n                        'value': [1641024000 + i, str(50 + i)]\n                    }\n                    for i in range(1000)  # 1000 métriques\n                ]\n            }\n        }\n        \n        mock_response = Mock()\n        mock_response.json.return_value = large_data\n        mock_response.raise_for_status.return_value = None\n        mock_get.return_value = mock_response\n        \n        client = PrometheusClient(host='localhost', port=9090)\n        \n        # Test avec une requête qui retourne beaucoup de données\n        start_time = time.time()\n        result = client.query_instant('node_cpu_seconds_total')\n        end_time = time.time()\n        \n        # Vérifications\n        self.assertTrue(result['success'])\n        self.assertEqual(len(result['data']['data']['result']), 1000)\n        \n        # Le traitement doit rester rapide même avec beaucoup de données\n        processing_time = end_time - start_time\n        self.assertLess(processing_time, 2.0)\n\n\nif __name__ == '__main__':\n    unittest.main()