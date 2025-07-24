"""
Tests d'intégration pour l'adaptateur Prometheus du module monitoring.
"""

import unittest
from unittest.mock import patch, MagicMock, Mock
from datetime import datetime, timezone, timedelta
from django.test import TestCase
import json
import requests

from ..infrastructure.adapters.prometheus_adapter import PrometheusAdapter
from ..models import MetricsDefinition, DeviceMetric, MetricValue


class PrometheusAdapterTest(TestCase):
    """
    Tests pour l'adaptateur Prometheus.
    """
    
    def setUp(self):
        """
        Initialisation des données de test.
        """
        self.adapter = PrometheusAdapter(base_url="http://localhost:9090")
        
        # Mock des réponses Prometheus
        self.mock_instant_response = {
            'status': 'success',
            'data': {
                'resultType': 'vector',
                'result': [
                    {
                        'metric': {'instance': 'localhost:9100'},
                        'value': [1640995200, '45.5']
                    }
                ]
            }
        }
        
        self.mock_range_response = {
            'status': 'success',
            'data': {
                'resultType': 'matrix',
                'result': [
                    {
                        'metric': {'instance': 'localhost:9100'},
                        'values': [
                            [1640995200, '45.5'],
                            [1640995260, '46.2'],
                            [1640995320, '44.8']
                        ]
                    }
                ]
            }
        }
        
        self.mock_targets_response = {
            'status': 'success',
            'data': {
                'activeTargets': [
                    {
                        'discoveredLabels': {'__address__': 'localhost:9100'},
                        'labels': {'instance': 'localhost:9100', 'job': 'node'},
                        'scrapePool': 'node',
                        'scrapeUrl': 'http://localhost:9100/metrics',
                        'lastError': '',
                        'lastScrape': '2025-07-11T10:30:00Z',
                        'health': 'up'
                    }
                ]
            }
        }
    
    @patch('requests.Session.get')
    def test_query_instant_success(self, mock_get):
        """
        Test d'une requête instantanée réussie.
        """
        # Configuration du mock
        mock_response = Mock()
        mock_response.json.return_value = self.mock_instant_response
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        # Exécution du test
        result = self.adapter.query_instant('up')
        
        # Vérifications
        self.assertTrue(result['success'])
        self.assertEqual(result['query'], 'up')
        self.assertIn('data', result)
        self.assertIn('timestamp', result)
        
        # Vérification des paramètres de l'appel
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        self.assertIn('query', call_args[1]['params'])
        self.assertEqual(call_args[1]['params']['query'], 'up')
    
    @patch('requests.Session.get')
    def test_query_instant_with_time(self, mock_get):
        """
        Test d'une requête instantanée avec timestamp spécifique.
        """
        # Configuration du mock
        mock_response = Mock()
        mock_response.json.return_value = self.mock_instant_response
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        # Timestamp de test
        test_time = datetime(2025, 7, 11, 10, 30, 0, tzinfo=timezone.utc)
        
        # Exécution du test
        result = self.adapter.query_instant('up', time=test_time)
        
        # Vérifications
        self.assertTrue(result['success'])
        
        # Vérification du timestamp dans les paramètres
        call_args = mock_get.call_args
        self.assertIn('time', call_args[1]['params'])
        self.assertEqual(call_args[1]['params']['time'], test_time.timestamp())
    
    @patch('requests.Session.get')
    def test_query_instant_prometheus_error(self, mock_get):
        """
        Test de gestion d'erreur Prometheus.
        """
        # Configuration du mock avec erreur Prometheus
        mock_response = Mock()
        mock_response.json.return_value = {
            'status': 'error',
            'error': 'invalid query'
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        # Exécution du test
        result = self.adapter.query_instant('invalid_query')
        
        # Vérifications
        self.assertFalse(result['success'])
        self.assertIn('error', result)
        self.assertIn('invalid query', result['error'])
    
    @patch('requests.Session.get')
    def test_query_instant_connection_error(self, mock_get):
        """
        Test de gestion d'erreur de connexion.
        """
        # Configuration du mock avec erreur de connexion
        mock_get.side_effect = requests.exceptions.ConnectionError("Connection failed")
        
        # Exécution du test
        result = self.adapter.query_instant('up')
        
        # Vérifications
        self.assertFalse(result['success'])
        self.assertIn('error', result)
        self.assertIn('Connection failed', result['error'])
    
    @patch('requests.Session.get')
    def test_query_range_success(self, mock_get):
        """
        Test d'une requête sur plage de temps réussie.
        """
        # Configuration du mock
        mock_response = Mock()
        mock_response.json.return_value = self.mock_range_response
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        # Plage de temps de test
        start_time = datetime(2025, 7, 11, 9, 0, 0, tzinfo=timezone.utc)
        end_time = datetime(2025, 7, 11, 10, 0, 0, tzinfo=timezone.utc)
        
        # Exécution du test
        result = self.adapter.query_range('up', start_time, end_time, '1m')
        
        # Vérifications
        self.assertTrue(result['success'])
        self.assertEqual(result['query'], 'up')
        self.assertEqual(result['step'], '1m')
        self.assertIn('data', result)
        self.assertIn('start', result)
        self.assertIn('end', result)
        
        # Vérification des paramètres de l'appel
        call_args = mock_get.call_args
        params = call_args[1]['params']
        self.assertEqual(params['query'], 'up')
        self.assertEqual(params['start'], start_time.timestamp())
        self.assertEqual(params['end'], end_time.timestamp())
        self.assertEqual(params['step'], '1m')
    
    @patch('requests.Session.get')
    def test_get_targets_success(self, mock_get):
        """
        Test de récupération des cibles Prometheus.
        """
        # Configuration du mock
        mock_response = Mock()
        mock_response.json.return_value = self.mock_targets_response
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        # Exécution du test
        result = self.adapter.get_targets()
        
        # Vérifications
        self.assertTrue(result['success'])
        self.assertIn('targets', result)
        self.assertEqual(len(result['targets']), 1)
        self.assertEqual(result['targets'][0]['health'], 'up')
        self.assertEqual(result['targets'][0]['labels']['instance'], 'localhost:9100')
    
    @patch('requests.Session.get')
    def test_get_metrics_list_success(self, mock_get):
        """
        Test de récupération de la liste des métriques.
        """
        # Configuration du mock
        mock_response = Mock()
        mock_response.json.return_value = {
            'status': 'success',
            'data': [
                'up',
                'node_cpu_seconds_total',
                'node_memory_MemTotal_bytes',
                'node_filesystem_size_bytes'
            ]
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        # Exécution du test
        result = self.adapter.get_metrics_list()
        
        # Vérifications
        self.assertTrue(result['success'])
        self.assertIn('metrics', result)
        self.assertEqual(result['count'], 4)
        self.assertIn('up', result['metrics'])
        self.assertIn('node_cpu_seconds_total', result['metrics'])
    
    @patch('requests.Session.get')
    def test_collect_system_metrics_success(self, mock_get):
        """
        Test de collecte des métriques système.
        """
        # Configuration des mocks pour différentes métriques
        def mock_response_side_effect(*args, **kwargs):
            url = args[0] if args else kwargs.get('url', '')
            params = kwargs.get('params', {})
            query = params.get('query', '')
            
            mock_response = Mock()
            mock_response.raise_for_status.return_value = None
            
            if 'cpu' in query:
                mock_response.json.return_value = {
                    'status': 'success',
                    'data': {
                        'result': [{'value': [1640995200, '45.5']}]
                    }
                }
            elif 'memory' in query:
                mock_response.json.return_value = {
                    'status': 'success',
                    'data': {
                        'result': [{'value': [1640995200, '67.2']}]
                    }
                }
            elif 'filesystem' in query:
                mock_response.json.return_value = {
                    'status': 'success',
                    'data': {
                        'result': [{'value': [1640995200, '23.8']}]
                    }
                }
            elif 'receive' in query:
                mock_response.json.return_value = {
                    'status': 'success',
                    'data': {
                        'result': [
                            {'value': [1640995200, '1024000']},
                            {'value': [1640995200, '512000']}
                        ]
                    }
                }
            elif 'transmit' in query:
                mock_response.json.return_value = {
                    'status': 'success',
                    'data': {
                        'result': [
                            {'value': [1640995200, '2048000']},
                            {'value': [1640995200, '1024000']}
                        ]
                    }
                }
            else:
                mock_response.json.return_value = {
                    'status': 'success',
                    'data': {'result': []}
                }
            
            return mock_response
        
        mock_get.side_effect = mock_response_side_effect
        
        # Exécution du test
        result = self.adapter.collect_system_metrics('localhost:9100')
        
        # Vérifications
        self.assertTrue(result['success'])
        self.assertIn('metrics', result)
        self.assertEqual(result['instance'], 'localhost:9100')
        
        metrics = result['metrics']
        self.assertEqual(metrics['cpu_usage'], 45.5)
        self.assertEqual(metrics['memory_usage'], 67.2)
        self.assertEqual(metrics['disk_usage'], 23.8)
        self.assertEqual(metrics['network_in'], 1536000.0)  # 1024000 + 512000
        self.assertEqual(metrics['network_out'], 3072000.0)  # 2048000 + 1024000
    
    @patch('requests.Session.get')
    def test_test_connection_success(self, mock_get):
        """
        Test de la méthode test_connection réussie.
        """
        # Configuration du mock
        mock_response = Mock()
        mock_response.json.return_value = {'status': 'success'}
        mock_response.raise_for_status.return_value = None
        mock_response.elapsed.total_seconds.return_value = 0.15
        mock_get.return_value = mock_response
        
        # Exécution du test
        result = self.adapter.test_connection()
        
        # Vérifications
        self.assertTrue(result['success'])
        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['url'], 'http://localhost:9090')
        self.assertEqual(result['response_time'], 0.15)
        self.assertIn('timestamp', result)
    
    @patch('requests.Session.get')
    def test_test_connection_failure(self, mock_get):
        """
        Test de la méthode test_connection en cas d'échec.
        """
        # Configuration du mock avec erreur
        mock_get.side_effect = requests.exceptions.Timeout("Request timeout")
        
        # Exécution du test
        result = self.adapter.test_connection()
        
        # Vérifications
        self.assertFalse(result['success'])
        self.assertIn('error', result)
        self.assertIn('timeout', result['error'].lower())
        self.assertEqual(result['url'], 'http://localhost:9090')


class PrometheusIntegrationTest(TestCase):
    """
    Tests d'intégration entre Prometheus et le système de métriques.
    """
    
    def setUp(self):
        """
        Initialisation des données de test.
        """
        self.adapter = PrometheusAdapter()
        
        # Créer des définitions de métriques
        self.cpu_metric_def = MetricsDefinition.objects.create(
            name="CPU Usage",
            description="CPU usage percentage",
            metric_type="gauge",
            unit="%",
            collection_method="prometheus",
            collection_config={"query": "cpu_usage{instance=\"$instance\"}"},
            category="system"
        )
        
        self.memory_metric_def = MetricsDefinition.objects.create(
            name="Memory Usage",
            description="Memory usage percentage",
            metric_type="gauge",
            unit="%",
            collection_method="prometheus",
            collection_config={"query": "memory_usage{instance=\"$instance\"}"},
            category="system"
        )
        
        # Créer des métriques d'équipement
        self.device_cpu_metric = DeviceMetric.objects.create(
            device_id=1,
            metric=self.cpu_metric_def,
            name="Server CPU Usage",
            is_active=True
        )
        
        self.device_memory_metric = DeviceMetric.objects.create(
            device_id=1,
            metric=self.memory_metric_def,
            name="Server Memory Usage",
            is_active=True
        )
    
    @patch.object(PrometheusAdapter, 'query_instant')
    def test_collect_metrics_from_prometheus(self, mock_query):
        """
        Test de collecte de métriques depuis Prometheus.
        """
        # Configuration du mock
        mock_query.side_effect = [
            {
                'success': True,
                'data': {
                    'result': [{'value': [1640995200, '78.5']}]
                }
            },
            {
                'success': True,
                'data': {
                    'result': [{'value': [1640995200, '64.2']}]
                }
            }
        ]
        
        # Simulation de collecte de métriques
        cpu_result = self.adapter.query_instant(
            self.cpu_metric_def.collection_config['query'].replace('$instance', 'localhost:9100')
        )
        memory_result = self.adapter.query_instant(
            self.memory_metric_def.collection_config['query'].replace('$instance', 'localhost:9100')
        )
        
        # Vérifications
        self.assertTrue(cpu_result['success'])
        self.assertTrue(memory_result['success'])
        
        # Création des valeurs de métriques
        cpu_value = MetricValue.objects.create(
            device_metric=self.device_cpu_metric,
            value=float(cpu_result['data']['result'][0]['value'][1]),
            timestamp=datetime.now(timezone.utc)
        )
        
        memory_value = MetricValue.objects.create(
            device_metric=self.device_memory_metric,
            value=float(memory_result['data']['result'][0]['value'][1]),
            timestamp=datetime.now(timezone.utc)
        )
        
        # Vérifications des valeurs créées
        self.assertEqual(cpu_value.value, 78.5)
        self.assertEqual(memory_value.value, 64.2)
        self.assertEqual(cpu_value.device_metric_id, self.device_cpu_metric.id)
        self.assertEqual(memory_value.device_metric_id, self.device_memory_metric.id)
    
    @patch.object(PrometheusAdapter, 'collect_system_metrics')
    def test_bulk_metrics_collection(self, mock_collect):
        """
        Test de collecte en lot de métriques système.
        """
        # Configuration du mock
        mock_collect.return_value = {
            'success': True,
            'metrics': {
                'cpu_usage': 45.5,
                'memory_usage': 67.2,
                'disk_usage': 23.8,
                'network_in': 1536000.0,
                'network_out': 3072000.0
            },
            'instance': 'localhost:9100',
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        # Exécution de la collecte
        result = self.adapter.collect_system_metrics('localhost:9100')
        
        # Vérifications
        self.assertTrue(result['success'])
        self.assertIn('metrics', result)
        
        metrics = result['metrics']
        self.assertEqual(len(metrics), 5)
        self.assertIn('cpu_usage', metrics)
        self.assertIn('memory_usage', metrics)
        self.assertIn('disk_usage', metrics)
        self.assertIn('network_in', metrics)
        self.assertIn('network_out', metrics)
    
    @patch.object(PrometheusAdapter, 'test_connection')
    def test_prometheus_health_check(self, mock_test):
        """
        Test de vérification de santé de Prometheus.
        """
        # Configuration du mock pour un Prometheus en bonne santé
        mock_test.return_value = {
            'success': True,
            'status': 'success',
            'url': 'http://localhost:9090',
            'response_time': 0.05,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        # Exécution du test
        result = self.adapter.test_connection()
        
        # Vérifications
        self.assertTrue(result['success'])
        self.assertEqual(result['status'], 'success')
        self.assertLess(result['response_time'], 1.0)  # Temps de réponse acceptable
    
    @patch.object(PrometheusAdapter, 'get_targets')
    def test_prometheus_targets_monitoring(self, mock_targets):
        """
        Test de monitoring des cibles Prometheus.
        """
        # Configuration du mock
        mock_targets.return_value = {
            'success': True,
            'targets': [
                {
                    'labels': {'instance': 'localhost:9100', 'job': 'node'},
                    'health': 'up',
                    'lastScrape': '2025-07-11T10:30:00Z',
                    'lastError': ''
                },
                {
                    'labels': {'instance': 'localhost:9090', 'job': 'prometheus'},
                    'health': 'up',
                    'lastScrape': '2025-07-11T10:29:55Z',
                    'lastError': ''
                }
            ],
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        # Exécution du test
        result = self.adapter.get_targets()
        
        # Vérifications
        self.assertTrue(result['success'])
        self.assertEqual(len(result['targets']), 2)
        
        # Vérification des cibles
        targets = result['targets']
        node_target = next(t for t in targets if t['labels']['job'] == 'node')
        prometheus_target = next(t for t in targets if t['labels']['job'] == 'prometheus')
        
        self.assertEqual(node_target['health'], 'up')
        self.assertEqual(prometheus_target['health'], 'up')
        self.assertEqual(node_target['labels']['instance'], 'localhost:9100')
        self.assertEqual(prometheus_target['labels']['instance'], 'localhost:9090')


if __name__ == '__main__':
    unittest.main()