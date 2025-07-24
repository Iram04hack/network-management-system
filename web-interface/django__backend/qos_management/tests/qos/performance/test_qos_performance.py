"""
Tests de performance pour le module QoS Management.

Ces tests mesurent les performances des fonctionnalités clés du module QoS Management
pour s'assurer qu'elles respectent les exigences de performance.
"""
import time
import unittest
from unittest import mock

from django.test import TestCase
from django.test.client import Client
from django.urls import reverse

from qos_management.models import QoSPolicy, TrafficClass
from qos_management.services.qos_policy_service import QoSPolicyService
from qos_management.application.qos_compliance_testing_use_cases import (
    QoSComplianceTestingUseCase,
    QoSTestScenario,
    TrafficProfile,
    ExpectedMetrics
)


class QoSPolicyPerformanceTests(TestCase):
    """Tests de performance pour les politiques QoS."""
    
    def setUp(self):
        """Configuration initiale pour les tests."""
        self.client = Client()
        self.qos_configurer_service = mock.MagicMock()
        self.policy_service = QoSPolicyService(qos_configurer_service=self.qos_configurer_service)
        
        # Créer un grand nombre de politiques QoS pour les tests
        self.policies = []
        for i in range(100):
            policy = QoSPolicy.objects.create(
                name=f"Policy {i}",
                description=f"Description {i}",
                bandwidth_limit=10000,
                is_active=True,
                priority=i % 10
            )
            self.policies.append(policy)
            
            # Créer des classes de trafic pour chaque politique
            for j in range(5):
                TrafficClass.objects.create(
                    policy=policy,
                    name=f"Class {j} for Policy {i}",
                    priority=j,
                    min_bandwidth=1000 * (j + 1),
                    max_bandwidth=2000 * (j + 1),
                    dscp=f"CS{j}"
                )
    
    def test_policy_list_performance(self):
        """Teste les performances de l'API de liste des politiques QoS."""
        # Mesurer le temps d'exécution
        start_time = time.time()
        response = self.client.get(reverse('qos_management:policy-list'))
        end_time = time.time()
        
        # Vérifier le temps d'exécution (moins de 500ms)
        execution_time = (end_time - start_time) * 1000  # en millisecondes
        self.assertLess(execution_time, 500, f"L'API de liste des politiques est trop lente: {execution_time:.2f}ms")
        
        # Vérifier le statut de la réponse
        self.assertEqual(response.status_code, 200)
    
    def test_policy_detail_performance(self):
        """Teste les performances de l'API de détail d'une politique QoS."""
        # Choisir une politique avec beaucoup de classes
        policy = self.policies[0]
        
        # Mesurer le temps d'exécution
        start_time = time.time()
        response = self.client.get(reverse('qos_management:policy-detail', args=[policy.id]))
        end_time = time.time()
        
        # Vérifier le temps d'exécution (moins de 200ms)
        execution_time = (end_time - start_time) * 1000  # en millisecondes
        self.assertLess(execution_time, 200, f"L'API de détail d'une politique est trop lente: {execution_time:.2f}ms")
        
        # Vérifier le statut de la réponse
        self.assertEqual(response.status_code, 200)
    
    def test_policy_service_list_performance(self):
        """Teste les performances du service de liste des politiques QoS."""
        # Mesurer le temps d'exécution
        start_time = time.time()
        policies = self.policy_service.list_policies()
        end_time = time.time()
        
        # Vérifier le temps d'exécution (moins de 300ms)
        execution_time = (end_time - start_time) * 1000  # en millisecondes
        self.assertLess(execution_time, 300, f"Le service de liste des politiques est trop lent: {execution_time:.2f}ms")
        
        # Vérifier le nombre de politiques
        self.assertEqual(len(policies), 100)


class QoSComplianceTestingPerformanceTests(unittest.TestCase):
    """Tests de performance pour les tests de conformité QoS."""
    
    def setUp(self):
        """Configuration initiale pour les tests."""
        self.qos_monitoring_service = mock.MagicMock()
        self.use_case = QoSComplianceTestingUseCase(self.qos_monitoring_service)
        
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
        
        # Créer un scénario de test
        traffic_profile = TrafficProfile(
            name="VoIP Test",
            protocol="udp",
            port=5060,
            bandwidth=1000,  # 1 Mbps
            packet_size=64,
            duration=10
        )
        
        expected_metrics = ExpectedMetrics(
            max_latency=20.0,
            max_jitter=5.0,
            max_packet_loss=0.5,
            min_bandwidth=800
        )
        
        self.scenario = QoSTestScenario(
            name="VoIP Conformity Test",
            traffic_profile=traffic_profile,
            expected_metrics=expected_metrics,
            description="Test de conformité pour le trafic VoIP"
        )
        
        # Créer une politique QoS
        self.policy = mock.MagicMock()
    
    def test_compliance_testing_performance(self):
        """Teste les performances des tests de conformité QoS."""
        # Mesurer le temps d'exécution
        start_time = time.time()
        result = self.use_case.run_test(
            policy=self.policy,
            scenario=self.scenario,
            target_ip="192.168.1.1",
            interface_name="eth0"
        )
        end_time = time.time()
        
        # Vérifier le temps d'exécution (moins de 2 secondes)
        execution_time = end_time - start_time
        self.assertLess(execution_time, 2.0, f"Le test de conformité est trop lent: {execution_time:.2f}s")
        
        # Vérifier le résultat
        self.assertTrue(result.success)


if __name__ == '__main__':
    unittest.main() 