"""
Tests unitaires pour les tests de conformité QoS.
"""
import unittest
from unittest import mock

from qos_management.application.qos_compliance_testing_use_cases import (
    QoSComplianceTestingUseCase,
    QoSTestScenario,
    TrafficProfile,
    ExpectedMetrics,
    QoSTestResult
)
from qos_management.domain.entities import QoSPolicyEntity


class TrafficProfileTests(unittest.TestCase):
    """Tests pour la classe TrafficProfile."""
    
    def test_to_dict(self):
        """Teste la conversion en dictionnaire."""
        profile = TrafficProfile(
            name="VoIP Test",
            protocol="udp",
            port=5060,
            bandwidth=1000,
            packet_size=64,
            duration=10
        )
        
        result = profile.to_dict()
        
        self.assertEqual(result['name'], "VoIP Test")
        self.assertEqual(result['protocol'], "udp")
        self.assertEqual(result['port'], 5060)
        self.assertEqual(result['bandwidth'], 1000)
        self.assertEqual(result['packet_size'], 64)
        self.assertEqual(result['duration'], 10)


class ExpectedMetricsTests(unittest.TestCase):
    """Tests pour la classe ExpectedMetrics."""
    
    def test_to_dict(self):
        """Teste la conversion en dictionnaire."""
        metrics = ExpectedMetrics(
            max_latency=20.0,
            max_jitter=5.0,
            max_packet_loss=0.5,
            min_bandwidth=800
        )
        
        result = metrics.to_dict()
        
        self.assertEqual(result['max_latency'], 20.0)
        self.assertEqual(result['max_jitter'], 5.0)
        self.assertEqual(result['max_packet_loss'], 0.5)
        self.assertEqual(result['min_bandwidth'], 800)


class QoSTestScenarioTests(unittest.TestCase):
    """Tests pour la classe QoSTestScenario."""
    
    def setUp(self):
        """Configuration initiale pour les tests."""
        self.traffic_profile = TrafficProfile(
            name="VoIP Test",
            protocol="udp",
            port=5060,
            bandwidth=1000,
            packet_size=64,
            duration=10
        )
        
        self.expected_metrics = ExpectedMetrics(
            max_latency=20.0,
            max_jitter=5.0,
            max_packet_loss=0.5,
            min_bandwidth=800
        )
        
        self.scenario = QoSTestScenario(
            name="VoIP Conformity Test",
            traffic_profile=self.traffic_profile,
            expected_metrics=self.expected_metrics,
            description="Test de conformité pour le trafic VoIP"
        )
    
    def test_to_dict(self):
        """Teste la conversion en dictionnaire."""
        result = self.scenario.to_dict()
        
        self.assertEqual(result['name'], "VoIP Conformity Test")
        self.assertEqual(result['description'], "Test de conformité pour le trafic VoIP")
        self.assertEqual(result['traffic_profile'], self.traffic_profile.to_dict())
        self.assertEqual(result['expected_metrics'], self.expected_metrics.to_dict())


class QoSTestResultTests(unittest.TestCase):
    """Tests pour la classe QoSTestResult."""
    
    def setUp(self):
        """Configuration initiale pour les tests."""
        self.traffic_profile = TrafficProfile(
            name="VoIP Test",
            protocol="udp",
            port=5060,
            bandwidth=1000,
            packet_size=64,
            duration=10
        )
        
        self.expected_metrics = ExpectedMetrics(
            max_latency=20.0,
            max_jitter=5.0,
            max_packet_loss=0.5,
            min_bandwidth=800
        )
        
        self.scenario = QoSTestScenario(
            name="VoIP Conformity Test",
            traffic_profile=self.traffic_profile,
            expected_metrics=self.expected_metrics,
            description="Test de conformité pour le trafic VoIP"
        )
        
        self.actual_metrics = {
            'avg_latency': 10.0,
            'max_latency': 15.0,
            'avg_jitter': 2.0,
            'max_jitter': 3.0,
            'avg_packet_loss': 0.1,
            'max_packet_loss': 0.2,
            'avg_bandwidth': 950,
            'min_bandwidth': 900
        }
        
        self.details = {
            'latency': {'status': 'passed'},
            'jitter': {'status': 'passed'},
            'packet_loss': {'status': 'passed'},
            'bandwidth': {'status': 'passed'}
        }
        
        self.test_result = QoSTestResult(
            scenario=self.scenario,
            success=True,
            actual_metrics=self.actual_metrics,
            details=self.details
        )
    
    def test_to_dict(self):
        """Teste la conversion en dictionnaire."""
        result = self.test_result.to_dict()
        
        self.assertEqual(result['scenario'], self.scenario.to_dict())
        self.assertTrue(result['success'])
        self.assertEqual(result['actual_metrics'], self.actual_metrics)
        self.assertEqual(result['details'], self.details)


class QoSComplianceTestingUseCaseTests(unittest.TestCase):
    """Tests pour la classe QoSComplianceTestingUseCase."""
    
    def setUp(self):
        """Configuration initiale pour les tests."""
        self.qos_monitoring_service = mock.MagicMock()
        self.use_case = QoSComplianceTestingUseCase(self.qos_monitoring_service)
        
        self.traffic_profile = TrafficProfile(
            name="VoIP Test",
            protocol="udp",
            port=5060,
            bandwidth=1000,
            packet_size=64,
            duration=1  # Durée courte pour les tests
        )
        
        self.expected_metrics = ExpectedMetrics(
            max_latency=20.0,
            max_jitter=5.0,
            max_packet_loss=0.5,
            min_bandwidth=800
        )
        
        self.scenario = QoSTestScenario(
            name="VoIP Conformity Test",
            traffic_profile=self.traffic_profile,
            expected_metrics=self.expected_metrics,
            description="Test de conformité pour le trafic VoIP"
        )
        
        self.policy = mock.MagicMock(spec=QoSPolicyEntity)
        
        # Configurer le mock pour simuler des métriques
        self.qos_monitoring_service.get_interface_metrics.return_value = {
            'success': True,
            'metrics': {
                'qos_stats': {
                    'latency': 10.0,
                    'jitter': 2.0,
                    'packet_loss': 0.1
                },
                'bandwidth': {
                    'tx': [{'value': 1000000}]  # 1 Mbps
                }
            }
        }
    
    def test_analyze_metrics(self):
        """Teste l'analyse des métriques collectées."""
        metrics_samples = [
            {
                'metrics': {
                    'qos_stats': {
                        'latency': 10.0,
                        'jitter': 2.0,
                        'packet_loss': 0.1
                    },
                    'bandwidth': {
                        'tx': [{'value': 1000000}]  # 1 Mbps
                    }
                }
            },
            {
                'metrics': {
                    'qos_stats': {
                        'latency': 15.0,
                        'jitter': 3.0,
                        'packet_loss': 0.2
                    },
                    'bandwidth': {
                        'tx': [{'value': 900000}]  # 0.9 Mbps
                    }
                }
            }
        ]
        
        result = self.use_case._analyze_metrics(metrics_samples)
        
        self.assertEqual(result['avg_latency'], 12.5)
        self.assertEqual(result['max_latency'], 15.0)
        self.assertEqual(result['avg_jitter'], 2.5)
        self.assertEqual(result['max_jitter'], 3.0)
        self.assertAlmostEqual(result['avg_packet_loss'], 0.15, places=5)
        self.assertEqual(result['max_packet_loss'], 0.2)
        self.assertEqual(result['avg_bandwidth'], 950.0)
        self.assertEqual(result['min_bandwidth'], 900.0)
    
    def test_check_compliance_success(self):
        """Teste la vérification de conformité avec succès."""
        actual_metrics = {
            'max_latency': 15.0,  # < 20.0
            'max_jitter': 3.0,    # < 5.0
            'max_packet_loss': 0.2,  # < 0.5
            'min_bandwidth': 900   # > 800
        }
        
        success, details = self.use_case._check_compliance(actual_metrics, self.expected_metrics)
        
        self.assertTrue(success)
        self.assertEqual(details['latency']['status'], 'passed')
        self.assertEqual(details['jitter']['status'], 'passed')
        self.assertEqual(details['packet_loss']['status'], 'passed')
        self.assertEqual(details['bandwidth']['status'], 'passed')
    
    def test_check_compliance_failure(self):
        """Teste la vérification de conformité avec échec."""
        actual_metrics = {
            'max_latency': 25.0,  # > 20.0 (échec)
            'max_jitter': 3.0,    # < 5.0 (succès)
            'max_packet_loss': 0.6,  # > 0.5 (échec)
            'min_bandwidth': 700   # < 800 (échec)
        }
        
        success, details = self.use_case._check_compliance(actual_metrics, self.expected_metrics)
        
        self.assertFalse(success)
        self.assertEqual(details['latency']['status'], 'failed')
        self.assertEqual(details['jitter']['status'], 'passed')
        self.assertEqual(details['packet_loss']['status'], 'failed')
        self.assertEqual(details['bandwidth']['status'], 'failed')
    
    @mock.patch('qos_management.application.qos_compliance_testing_use_cases.TrafficGenerator')
    def test_run_test_success(self, mock_traffic_generator):
        """Teste l'exécution d'un test de conformité avec succès."""
        # Configurer le mock du générateur de trafic
        mock_generator_instance = mock.MagicMock()
        mock_generator_instance.start.return_value = True
        mock_traffic_generator.return_value = mock_generator_instance
        
        # Exécuter le test
        result = self.use_case.run_test(
            policy=self.policy,
            scenario=self.scenario,
            target_ip="192.168.1.1",
            interface_name="eth0"
        )
        
        # Vérifier les résultats
        self.assertTrue(result.success)
        self.assertEqual(result.scenario, self.scenario)
        self.assertIn('max_latency', result.actual_metrics)
        self.assertIn('max_jitter', result.actual_metrics)
        self.assertIn('max_packet_loss', result.actual_metrics)
        self.assertIn('min_bandwidth', result.actual_metrics)
        
        # Vérifier que le générateur de trafic a été utilisé correctement
        mock_traffic_generator.assert_called_once_with("192.168.1.1", self.traffic_profile)
        mock_generator_instance.start.assert_called_once()
        mock_generator_instance.stop.assert_called_once()
    
    @mock.patch('qos_management.application.qos_compliance_testing_use_cases.TrafficGenerator')
    def test_run_test_generator_failure(self, mock_traffic_generator):
        """Teste l'échec du démarrage du générateur de trafic."""
        # Configurer le mock du générateur de trafic pour échouer
        mock_generator_instance = mock.MagicMock()
        mock_generator_instance.start.return_value = False
        mock_traffic_generator.return_value = mock_generator_instance
        
        # Exécuter le test
        result = self.use_case.run_test(
            policy=self.policy,
            scenario=self.scenario,
            target_ip="192.168.1.1",
            interface_name="eth0"
        )
        
        # Vérifier les résultats
        self.assertFalse(result.success)
        self.assertEqual(result.scenario, self.scenario)
        self.assertEqual(result.actual_metrics, {})
        self.assertIn('error', result.details)
        
        # Vérifier que le générateur de trafic a été utilisé correctement
        mock_traffic_generator.assert_called_once_with("192.168.1.1", self.traffic_profile)
        mock_generator_instance.start.assert_called_once()
        mock_generator_instance.stop.assert_not_called()


if __name__ == '__main__':
    unittest.main() 