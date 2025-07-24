"""
Tests pour la classe ApiClientMetrics.

Ce module contient les tests pour la classe ApiClientMetrics.
"""

import unittest
import time
from unittest.mock import patch, MagicMock

from api_clients.metrics import ApiClientMetrics


class ApiClientMetricsTests(unittest.TestCase):
    """
    Tests pour la classe ApiClientMetrics.
    """
    
    def setUp(self):
        """
        Configuration initiale pour les tests.
        """
        self.metrics = ApiClientMetrics()
    
    def test_initial_metrics(self):
        """
        Teste que les métriques initiales sont correctement initialisées.
        """
        metrics_data = self.metrics.get_metrics()
        
        self.assertEqual(metrics_data['requests']['total'], 0)
        self.assertEqual(metrics_data['requests']['success'], 0)
        self.assertEqual(metrics_data['requests']['error'], 0)
        self.assertEqual(metrics_data['response_time']['avg'], 0)
        self.assertIsNone(metrics_data['response_time']['min'])
        self.assertIsNone(metrics_data['response_time']['max'])
        self.assertEqual(metrics_data['clients'], {})
        self.assertIn('uptime', metrics_data)
    
    def test_record_request_success(self):
        """
        Teste l'enregistrement d'une requête réussie.
        """
        self.metrics.record_request('example', True, 0.1)
        
        metrics_data = self.metrics.get_metrics()
        self.assertEqual(metrics_data['requests']['total'], 1)
        self.assertEqual(metrics_data['requests']['success'], 1)
        self.assertEqual(metrics_data['requests']['error'], 0)
        self.assertEqual(metrics_data['response_time']['avg'], 0.1)
        self.assertEqual(metrics_data['response_time']['min'], 0.1)
        self.assertEqual(metrics_data['response_time']['max'], 0.1)
        self.assertIn('example', metrics_data['clients'])
        self.assertEqual(metrics_data['clients']['example']['requests']['total'], 1)
        self.assertEqual(metrics_data['clients']['example']['requests']['success'], 1)
        self.assertEqual(metrics_data['clients']['example']['requests']['error'], 0)
        self.assertEqual(metrics_data['clients']['example']['response_time']['avg'], 0.1)
        self.assertEqual(metrics_data['clients']['example']['response_time']['min'], 0.1)
        self.assertEqual(metrics_data['clients']['example']['response_time']['max'], 0.1)
