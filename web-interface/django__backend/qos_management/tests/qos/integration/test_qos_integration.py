"""
Tests d'intégration pour le module QoS Management.

Ces tests vérifient l'intégration entre les différents composants
du module QoS Management.
"""
import json
from unittest import mock

from django.test import TestCase, Client
from django.urls import reverse

from qos_management.models import QoSPolicy, TrafficClass, QoSRule
from qos_management.domain.entities import QoSPolicyEntity
from qos_management.services.qos_policy_service import QoSPolicyService
from qos_management.services.qos_monitoring_service import QoSMonitoringService


class QoSPolicyIntegrationTests(TestCase):
    """Tests d'intégration pour les politiques QoS."""
    
    def setUp(self):
        """Configuration initiale pour les tests."""
        self.client = Client()
        
        # Créer une politique QoS pour les tests
        self.policy = QoSPolicy.objects.create(
            name="Test Policy",
            description="Test Description",
            bandwidth_limit=10000,
            is_active=True,
            priority=1
        )
        
        # Créer des classes de trafic pour la politique
        self.tc1 = TrafficClass.objects.create(
            policy=self.policy,
            name="Voix",
            priority=1,
            min_bandwidth=1000,
            max_bandwidth=2000,
            dscp="EF"
        )
        
        self.tc2 = TrafficClass.objects.create(
            policy=self.policy,
            name="Vidéo",
            priority=2,
            min_bandwidth=2000,
            max_bandwidth=5000,
            dscp="AF41"
        )
        
        # Créer des règles QoS pour les classes de trafic
        self.rule1 = QoSRule.objects.create(
            traffic_class=self.tc1,
            protocol="udp",
            destination_port_start=5060,
            destination_port_end=5061,
            name="SIP"
        )
        
        self.rule2 = QoSRule.objects.create(
            traffic_class=self.tc2,
            protocol="tcp",
            destination_port_start=80,
            destination_port_end=80,
            name="HTTP"
        )
    
    def test_policy_list_api(self):
        """Teste l'API de liste des politiques QoS."""
        response = self.client.get(reverse('qos_management:policy-list'))
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        
        # Vérifier qu'il y a une politique dans la liste
        self.assertEqual(len(data), 1)
        
        # Vérifier les attributs de la politique
        policy_data = data[0]
        self.assertEqual(policy_data['id'], self.policy.id)
        self.assertEqual(policy_data['name'], self.policy.name)
        self.assertEqual(policy_data['description'], self.policy.description)
        self.assertEqual(policy_data['bandwidth_limit'], self.policy.bandwidth_limit)
        self.assertEqual(policy_data['is_active'], self.policy.is_active)
        self.assertEqual(policy_data['priority'], self.policy.priority)
    
    def test_policy_detail_api(self):
        """Teste l'API de détail d'une politique QoS."""
        response = self.client.get(reverse('qos_management:policy-detail', args=[self.policy.id]))
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        
        # Vérifier les attributs de la politique
        self.assertEqual(data['id'], self.policy.id)
        self.assertEqual(data['name'], self.policy.name)
        self.assertEqual(data['description'], self.policy.description)
        self.assertEqual(data['bandwidth_limit'], self.policy.bandwidth_limit)
        self.assertEqual(data['is_active'], self.policy.is_active)
        self.assertEqual(data['priority'], self.policy.priority)
        
        # Vérifier les classes de trafic
        self.assertEqual(len(data['traffic_classes']), 2)
        
        # Vérifier la première classe
        tc1_data = next(tc for tc in data['traffic_classes'] if tc['id'] == self.tc1.id)
        self.assertEqual(tc1_data['name'], self.tc1.name)
        self.assertEqual(tc1_data['priority'], self.tc1.priority)
        self.assertEqual(tc1_data['min_bandwidth'], self.tc1.min_bandwidth)
        self.assertEqual(tc1_data['max_bandwidth'], self.tc1.max_bandwidth)
        self.assertEqual(tc1_data['dscp'], self.tc1.dscp)
        
        # Vérifier la deuxième classe
        tc2_data = next(tc for tc in data['traffic_classes'] if tc['id'] == self.tc2.id)
        self.assertEqual(tc2_data['name'], self.tc2.name)
        self.assertEqual(tc2_data['priority'], self.tc2.priority)
        self.assertEqual(tc2_data['min_bandwidth'], self.tc2.min_bandwidth)
        self.assertEqual(tc2_data['max_bandwidth'], self.tc2.max_bandwidth)
        self.assertEqual(tc2_data['dscp'], self.tc2.dscp)
    
    def test_create_policy_api(self):
        """Teste l'API de création d'une politique QoS."""
        policy_data = {
            'name': 'New Policy',
            'description': 'New Description',
            'bandwidth_limit': 20000,
            'is_active': True,
            'priority': 2,
            'traffic_classes': [
                {
                    'name': 'Données',
                    'priority': 3,
                    'min_bandwidth': 5000,
                    'max_bandwidth': 15000,
                    'dscp': 'AF21'
                }
            ]
        }
        
        response = self.client.post(
            reverse('qos_management:policy-list'),
            data=json.dumps(policy_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.content)
        
        # Vérifier que la politique a été créée
        self.assertIsNotNone(data['id'])
        self.assertEqual(data['name'], policy_data['name'])
        self.assertEqual(data['description'], policy_data['description'])
        self.assertEqual(data['bandwidth_limit'], policy_data['bandwidth_limit'])
        self.assertEqual(data['is_active'], policy_data['is_active'])
        self.assertEqual(data['priority'], policy_data['priority'])
        
        # Vérifier que la classe de trafic a été créée
        self.assertEqual(len(data['traffic_classes']), 1)
        tc_data = data['traffic_classes'][0]
        self.assertEqual(tc_data['name'], policy_data['traffic_classes'][0]['name'])
        self.assertEqual(tc_data['priority'], policy_data['traffic_classes'][0]['priority'])
        self.assertEqual(tc_data['min_bandwidth'], policy_data['traffic_classes'][0]['min_bandwidth'])
        self.assertEqual(tc_data['max_bandwidth'], policy_data['traffic_classes'][0]['max_bandwidth'])
        self.assertEqual(tc_data['dscp'], policy_data['traffic_classes'][0]['dscp'])


class QoSServiceIntegrationTests(TestCase):
    """Tests d'intégration pour les services QoS."""
    
    def setUp(self):
        """Configuration initiale pour les tests."""
        # Créer une politique QoS pour les tests
        self.policy = QoSPolicy.objects.create(
            name="Test Policy",
            description="Test Description",
            bandwidth_limit=10000,
            is_active=True,
            priority=1
        )
        
        # Créer des classes de trafic pour la politique
        self.tc1 = TrafficClass.objects.create(
            policy=self.policy,
            name="Voix",
            priority=1,
            min_bandwidth=1000,
            max_bandwidth=2000,
            dscp="EF"
        )
        
        # Mocker les services
        self.qos_configurer_service = mock.MagicMock()
        self.policy_service = QoSPolicyService(qos_configurer_service=self.qos_configurer_service)
        
        self.visualization_service = mock.MagicMock()
        self.monitoring_service = QoSMonitoringService(visualization_service=self.visualization_service)
    
    def test_policy_service_get_policy(self):
        """Teste la récupération d'une politique via le service."""
        # Récupérer la politique via le service
        policy_data = self.policy_service.get_policy(self.policy.id)
        
        # Vérifier les attributs de la politique
        self.assertEqual(policy_data['id'], self.policy.id)
        self.assertEqual(policy_data['name'], self.policy.name)
        self.assertEqual(policy_data['description'], self.policy.description)
        self.assertEqual(policy_data['bandwidth_limit'], self.policy.bandwidth_limit)
        self.assertEqual(policy_data['is_active'], self.policy.is_active)
        self.assertEqual(policy_data['priority'], self.policy.priority)
        
        # Vérifier les classes de trafic
        self.assertEqual(len(policy_data['traffic_classes']), 1)
        tc_data = policy_data['traffic_classes'][0]
        self.assertEqual(tc_data['id'], self.tc1.id)
        self.assertEqual(tc_data['name'], self.tc1.name)
        self.assertEqual(tc_data['priority'], self.tc1.priority)
        self.assertEqual(tc_data['min_bandwidth'], self.tc1.min_bandwidth)
        self.assertEqual(tc_data['max_bandwidth'], self.tc1.max_bandwidth)
        self.assertEqual(tc_data['dscp'], self.tc1.dscp)
    
    def test_policy_service_apply_policy(self):
        """Teste l'application d'une politique via le service."""
        # Configurer le mock
        self.qos_configurer_service.apply_policy.return_value = True
        
        # Appliquer la politique
        result = self.policy_service.apply_policy(self.policy.id, 1, 1)
        
        # Vérifier que le service d'infrastructure a été appelé
        self.qos_configurer_service.apply_policy.assert_called_once_with(1, 1, self.policy.id)
        
        # Vérifier le résultat
        self.assertTrue(result['success'])
        self.assertEqual(result['policy_id'], self.policy.id)
        self.assertEqual(result['device_id'], 1)
        self.assertEqual(result['interface_id'], 1)
    
    def test_monitoring_service_get_metrics(self):
        """Teste la récupération des métriques via le service."""
        # Appeler la méthode à tester
        metrics = self.monitoring_service.get_metrics(1, 1, '1h')
        
        # Vérifier les attributs de base des métriques
        self.assertEqual(metrics['device_id'], 1)
        self.assertEqual(metrics['interface_id'], 1)
        self.assertEqual(metrics['period'], '1h')
        
        # Vérifier les métriques spécifiques
        self.assertIn('metrics', metrics)
        self.assertIn('bandwidth_utilization', metrics['metrics'])
        self.assertIn('packet_loss', metrics['metrics'])
        self.assertIn('latency', metrics['metrics'])
        self.assertIn('jitter', metrics['metrics']) 