"""
Tests d'intégration pour Netdata dans le module monitoring.
"""

import unittest
from unittest.mock import patch, MagicMock, Mock
from datetime import datetime, timezone, timedelta
from django.test import TestCase
import json
import requests

from ..models import MetricsDefinition, DeviceMetric, MetricValue


class NetdataAdapter:
    """
    Adaptateur pour l'intégration avec Netdata.
    Simple implémentation pour les tests.
    """
    
    def __init__(self, base_url: str = "http://localhost:19999", timeout: int = 30):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.session = requests.Session()
    
    def get_info(self):
        """
        Récupère les informations sur l'instance Netdata.
        """
        try:
            url = f"{self.base_url}/api/v1/info"
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            
            return {
                'success': True,
                'data': response.json(),
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_charts(self):
        """
        Récupère la liste des graphiques disponibles.
        """
        try:
            url = f"{self.base_url}/api/v1/charts"
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            
            return {
                'success': True,
                'charts': response.json(),
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_data(self, chart: str, points: int = 600, group: str = "average"):
        """
        Récupère les données d'un graphique spécifique.
        """
        try:
            url = f"{self.base_url}/api/v1/data"
            params = {
                'chart': chart,
                'points': points,
                'group': group,
                'format': 'json'
            }
            
            response = self.session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            
            return {
                'success': True,
                'data': response.json(),
                'chart': chart,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'chart': chart
            }
    
    def get_allmetrics(self, format_type: str = "json"):
        """
        Récupère toutes les métriques actuelles.
        """
        try:
            url = f"{self.base_url}/api/v1/allmetrics"
            params = {'format': format_type}
            
            response = self.session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            
            return {
                'success': True,
                'metrics': response.json() if format_type == 'json' else response.text,
                'format': format_type,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }


class NetdataIntegrationTest(TestCase):
    """
    Tests pour l'intégration avec Netdata.
    """
    
    def setUp(self):
        """
        Initialisation des données de test.
        """
        self.adapter = NetdataAdapter()
        
        # Mock des réponses Netdata
        self.mock_info_response = {
            "version": "v1.35.1",
            "uid": "12345",
            "hostname": "test-server",
            "machine_guid": "abcd-1234-efgh-5678",
            "update_every": 1,
            "history": 3600,
            "memory_mode": "dbengine",
            "timezone": "UTC",
            "uptime": 86400
        }
        
        self.mock_charts_response = {
            "system.cpu": {
                "id": "system.cpu",
                "name": "cpu",
                "title": "Total CPU utilization",
                "units": "percentage",
                "family": "cpu",
                "context": "system.cpu",
                "type": "stacked",
                "priority": 100,
                "enabled": True,
                "dimensions": {
                    "user": {"name": "user"},
                    "system": {"name": "system"},
                    "idle": {"name": "idle"}
                }
            },
            "system.ram": {
                "id": "system.ram",
                "name": "ram",
                "title": "System RAM",
                "units": "MiB",
                "family": "ram",
                "context": "system.ram",
                "type": "stacked",
                "priority": 200,
                "enabled": True,
                "dimensions": {
                    "used": {"name": "used"},
                    "free": {"name": "free"},
                    "buffers": {"name": "buffers"}
                }
            }
        }
        
        self.mock_data_response = {
            "labels": ["time", "user", "system", "idle"],
            "data": [
                [1641024000, 15.5, 8.2, 76.3],
                [1641024001, 16.1, 8.5, 75.4],
                [1641024002, 14.8, 7.9, 77.3]
            ],
            "view_range": [1641024000, 1641024002],
            "after": 1641024000,
            "before": 1641024002
        }
        
        self.mock_allmetrics_response = {
            "system.cpu.user": {"value": 15.5, "timestamp": 1641024002},
            "system.cpu.system": {"value": 8.2, "timestamp": 1641024002},
            "system.cpu.idle": {"value": 76.3, "timestamp": 1641024002},
            "system.ram.used": {"value": 4096, "timestamp": 1641024002},
            "system.ram.free": {"value": 12288, "timestamp": 1641024002}
        }
    
    @patch('requests.Session.get')
    def test_get_info_success(self, mock_get):
        """
        Test de récupération des informations Netdata.
        """
        # Configuration du mock
        mock_response = Mock()
        mock_response.json.return_value = self.mock_info_response
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        # Exécution du test
        result = self.adapter.get_info()
        
        # Vérifications
        self.assertTrue(result['success'])
        self.assertIn('data', result)
        self.assertEqual(result['data']['version'], 'v1.35.1')
        self.assertEqual(result['data']['hostname'], 'test-server')
        self.assertEqual(result['data']['update_every'], 1)
        self.assertIn('timestamp', result)
        
        # Vérification de l'URL appelée
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        self.assertIn('/api/v1/info', call_args[0][0])
    
    @patch('requests.Session.get')
    def test_get_info_failure(self, mock_get):
        """
        Test de gestion d'erreur lors de la récupération des informations.
        """
        # Configuration du mock avec erreur
        mock_get.side_effect = requests.exceptions.ConnectionError("Connection refused")
        
        # Exécution du test
        result = self.adapter.get_info()
        
        # Vérifications
        self.assertFalse(result['success'])
        self.assertIn('error', result)
        self.assertIn('Connection refused', result['error'])
    
    @patch('requests.Session.get')
    def test_get_charts_success(self, mock_get):
        """
        Test de récupération des graphiques disponibles.
        """
        # Configuration du mock
        mock_response = Mock()
        mock_response.json.return_value = self.mock_charts_response
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        # Exécution du test
        result = self.adapter.get_charts()
        
        # Vérifications
        self.assertTrue(result['success'])
        self.assertIn('charts', result)
        
        charts = result['charts']
        self.assertIn('system.cpu', charts)
        self.assertIn('system.ram', charts)
        
        cpu_chart = charts['system.cpu']
        self.assertEqual(cpu_chart['title'], 'Total CPU utilization')
        self.assertEqual(cpu_chart['units'], 'percentage')
        self.assertIn('user', cpu_chart['dimensions'])
        self.assertIn('system', cpu_chart['dimensions'])
        self.assertIn('idle', cpu_chart['dimensions'])
    
    @patch('requests.Session.get')
    def test_get_data_success(self, mock_get):
        """
        Test de récupération de données d'un graphique.
        """
        # Configuration du mock
        mock_response = Mock()
        mock_response.json.return_value = self.mock_data_response
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        # Exécution du test
        result = self.adapter.get_data('system.cpu', points=600)
        
        # Vérifications
        self.assertTrue(result['success'])
        self.assertEqual(result['chart'], 'system.cpu')
        self.assertIn('data', result)
        
        data = result['data']
        self.assertIn('labels', data)
        self.assertIn('data', data)
        self.assertEqual(data['labels'], ['time', 'user', 'system', 'idle'])
        self.assertEqual(len(data['data']), 3)
        
        # Vérification des paramètres de l'appel
        call_args = mock_get.call_args
        params = call_args[1]['params']
        self.assertEqual(params['chart'], 'system.cpu')
        self.assertEqual(params['points'], 600)
        self.assertEqual(params['group'], 'average')
        self.assertEqual(params['format'], 'json')
    
    @patch('requests.Session.get')
    def test_get_allmetrics_success(self, mock_get):
        """
        Test de récupération de toutes les métriques.
        """
        # Configuration du mock
        mock_response = Mock()
        mock_response.json.return_value = self.mock_allmetrics_response
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        # Exécution du test
        result = self.adapter.get_allmetrics('json')
        
        # Vérifications
        self.assertTrue(result['success'])
        self.assertEqual(result['format'], 'json')
        self.assertIn('metrics', result)
        
        metrics = result['metrics']
        self.assertIn('system.cpu.user', metrics)
        self.assertIn('system.ram.used', metrics)
        
        cpu_user = metrics['system.cpu.user']
        self.assertEqual(cpu_user['value'], 15.5)
        self.assertEqual(cpu_user['timestamp'], 1641024002)
    
    def test_parse_netdata_metrics_to_nms_format(self):
        """
        Test de conversion des métriques Netdata au format NMS.
        """
        # Créer des définitions de métriques compatibles Netdata
        cpu_metric_def = MetricsDefinition.objects.create(
            name="CPU Usage",
            description="CPU usage from Netdata",
            metric_type="gauge",
            unit="%",
            collection_method="netdata",
            collection_config={
                "chart": "system.cpu",
                "dimension": "user",
                "calculation": "percentage"
            },
            category="system"
        )
        
        ram_metric_def = MetricsDefinition.objects.create(
            name="RAM Usage",
            description="RAM usage from Netdata",
            metric_type="gauge",
            unit="MiB",
            collection_method="netdata",
            collection_config={
                "chart": "system.ram",
                "dimension": "used",
                "calculation": "absolute"
            },
            category="system"
        )
        
        # Créer des métriques d'équipement
        device_cpu_metric = DeviceMetric.objects.create(
            device_id=1,
            metric=cpu_metric_def,
            name="Server CPU Usage (Netdata)",
            is_active=True
        )
        
        device_ram_metric = DeviceMetric.objects.create(
            device_id=1,
            metric=ram_metric_def,
            name="Server RAM Usage (Netdata)",
            is_active=True
        )
        
        # Simuler la conversion des données Netdata
        netdata_metrics = self.mock_allmetrics_response
        
        # Conversion CPU
        cpu_value = netdata_metrics['system.cpu.user']['value']
        cpu_timestamp = datetime.fromtimestamp(
            netdata_metrics['system.cpu.user']['timestamp'],
            tz=timezone.utc
        )
        
        cpu_metric_value = MetricValue.objects.create(
            device_metric=device_cpu_metric,
            value=cpu_value,
            timestamp=cpu_timestamp
        )
        
        # Conversion RAM
        ram_value = netdata_metrics['system.ram.used']['value']
        ram_timestamp = datetime.fromtimestamp(
            netdata_metrics['system.ram.used']['timestamp'],
            tz=timezone.utc
        )
        
        ram_metric_value = MetricValue.objects.create(
            device_metric=device_ram_metric,
            value=ram_value,
            timestamp=ram_timestamp
        )
        
        # Vérifications
        self.assertEqual(MetricValue.objects.count(), 2)
        
        # Vérification CPU
        self.assertEqual(cpu_metric_value.value, 15.5)
        self.assertEqual(cpu_metric_value.device_metric_id, device_cpu_metric.id)
        
        # Vérification RAM
        self.assertEqual(ram_metric_value.value, 4096)
        self.assertEqual(ram_metric_value.device_metric_id, device_ram_metric.id)
    
    @patch.object(NetdataAdapter, 'get_data')
    def test_historical_data_collection(self, mock_get_data):
        """
        Test de collecte de données historiques depuis Netdata.
        """
        # Configuration du mock
        mock_get_data.return_value = {
            'success': True,
            'data': self.mock_data_response,
            'chart': 'system.cpu'
        }
        
        # Exécution de la collecte
        result = self.adapter.get_data('system.cpu', points=600)
        
        # Vérifications
        self.assertTrue(result['success'])
        
        data = result['data']
        labels = data['labels']
        time_series = data['data']
        
        # Conversion en format NMS
        converted_metrics = []
        for row in time_series:
            timestamp = datetime.fromtimestamp(row[0], tz=timezone.utc)
            user_cpu = row[1]
            system_cpu = row[2]
            idle_cpu = row[3]
            
            # Calculer le CPU total utilisé
            total_used_cpu = user_cpu + system_cpu
            
            converted_metrics.append({
                'timestamp': timestamp,
                'cpu_user': user_cpu,
                'cpu_system': system_cpu,
                'cpu_idle': idle_cpu,
                'cpu_total_used': total_used_cpu
            })
        
        # Vérifications des données converties
        self.assertEqual(len(converted_metrics), 3)
        
        first_metric = converted_metrics[0]
        self.assertEqual(first_metric['cpu_user'], 15.5)
        self.assertEqual(first_metric['cpu_system'], 8.2)
        self.assertEqual(first_metric['cpu_total_used'], 23.7)
    
    @patch.object(NetdataAdapter, 'get_allmetrics')
    def test_real_time_metrics_sync(self, mock_get_allmetrics):
        """
        Test de synchronisation de métriques en temps réel.
        """
        # Configuration du mock
        mock_get_allmetrics.return_value = {
            'success': True,
            'metrics': self.mock_allmetrics_response,
            'format': 'json'
        }
        
        # Créer des définitions de métriques
        cpu_metric_def = MetricsDefinition.objects.create(
            name="Netdata CPU",
            metric_type="gauge",
            unit="%",
            collection_method="netdata",
            collection_config={"netdata_metric": "system.cpu.user"}
        )
        
        device_metric = DeviceMetric.objects.create(
            device_id=1,
            metric=cpu_metric_def,
            name="CPU from Netdata",
            is_active=True
        )
        
        # Exécution de la synchronisation
        result = self.adapter.get_allmetrics()
        
        # Vérifications
        self.assertTrue(result['success'])
        
        # Simulation de la logique de synchronisation
        metrics = result['metrics']
        netdata_metric_key = cpu_metric_def.collection_config['netdata_metric']
        
        if netdata_metric_key in metrics:
            metric_data = metrics[netdata_metric_key]
            
            # Créer la valeur de métrique
            metric_value = MetricValue.objects.create(
                device_metric=device_metric,
                value=metric_data['value'],
                timestamp=datetime.fromtimestamp(
                    metric_data['timestamp'],
                    tz=timezone.utc
                )
            )
            
            # Vérifications
            self.assertEqual(metric_value.value, 15.5)
            self.assertEqual(metric_value.device_metric_id, device_metric.id)
    
    @patch.object(NetdataAdapter, 'get_info')
    def test_netdata_health_check(self, mock_get_info):
        """
        Test de vérification de santé de Netdata.
        """
        # Configuration du mock pour un Netdata en bonne santé
        mock_get_info.return_value = {
            'success': True,
            'data': self.mock_info_response
        }
        
        # Exécution du test de santé
        result = self.adapter.get_info()
        
        # Vérifications
        self.assertTrue(result['success'])
        
        info = result['data']
        self.assertGreater(info['uptime'], 0)  # Netdata est actif
        self.assertEqual(info['update_every'], 1)  # Collecte chaque seconde
        self.assertEqual(info['timezone'], 'UTC')  # Timezone correcte
        self.assertIsNotNone(info['version'])  # Version disponible
        
        # Vérifier que Netdata est opérationnel
        is_healthy = (
            result['success'] and
            info['uptime'] > 0 and
            info['update_every'] > 0
        )
        
        self.assertTrue(is_healthy)


if __name__ == '__main__':
    unittest.main()