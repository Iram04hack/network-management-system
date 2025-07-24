"""
Tests pour les vues API du module security_management.

Ce fichier contient des tests unitaires pour les vues API
du module de gestion de la sécurité.
"""

from unittest.mock import patch, MagicMock
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status

from ..domain.entities import SecurityRule, SecurityAlert, RuleType, ActionType, SeverityLevel


class SecurityRuleViewSetTests(TestCase):
    """
    Tests pour le SecurityRuleViewSet.
    """
    
    def setUp(self):
        """
        Configuration initiale pour les tests.
        """
        self.client = APIClient()
        
        # Créer un utilisateur pour l'authentification
        from django.contrib.auth import get_user_model
        User = get_user_model()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword'
        )
        
        # Authentifier le client
        self.client.force_authenticate(user=self.user)
        
        # Créer une règle de sécurité de test
        self.test_rule = SecurityRule(
            id='test-rule-1',
            name='Test Rule',
            description='A test security rule',
            rule_type=RuleType.FIREWALL,
            content='alert tcp any any -> any any (msg:"Test Rule"; sid:1000001;)',
            source_ip='192.168.1.0/24',
            destination_ip='any',
            protocol='tcp',
            action=ActionType.ALERT,
            enabled=True,
            priority=100,
            tags=['test', 'firewall']
        )
    
    @patch('security_management.di_container.container.rule_management_use_case')
    def test_list_rules(self, mock_use_case):
        """
        Test de la méthode list du SecurityRuleViewSet.
        """
        # Configurer le mock
        mock_use_case.list_rules.return_value = [self.test_rule]
        
        # Effectuer la requête
        url = reverse('security-rule-list')
        response = self.client.get(url)
        
        # Vérifier la réponse
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], 'Test Rule')
        self.assertEqual(response.data[0]['rule_type'], 'firewall')
        
        # Vérifier que le cas d'utilisation a été appelé correctement
        mock_use_case.list_rules.assert_called_once_with({})
    
    @patch('security_management.di_container.container.rule_management_use_case')
    def test_retrieve_rule(self, mock_use_case):
        """
        Test de la méthode retrieve du SecurityRuleViewSet.
        """
        # Configurer le mock
        mock_use_case.get_rule.return_value = self.test_rule
        
        # Effectuer la requête
        url = reverse('security-rule-detail', args=['test-rule-1'])
        response = self.client.get(url)
        
        # Vérifier la réponse
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], 'test-rule-1')
        self.assertEqual(response.data['name'], 'Test Rule')
        
        # Vérifier que le cas d'utilisation a été appelé correctement
        mock_use_case.get_rule.assert_called_once_with('test-rule-1')
    
    @patch('security_management.di_container.container.rule_management_use_case')
    def test_create_rule(self, mock_use_case):
        """
        Test de la méthode create du SecurityRuleViewSet.
        """
        # Configurer le mock
        mock_use_case.create_rule.return_value = self.test_rule
        
        # Données de la requête
        rule_data = {
            'name': 'Test Rule',
            'description': 'A test security rule',
            'rule_type': 'firewall',
            'content': 'alert tcp any any -> any any (msg:"Test Rule"; sid:1000001;)',
            'source_ip': '192.168.1.0/24',
            'destination_ip': 'any',
            'protocol': 'tcp',
            'action': 'alert',
            'enabled': True,
            'priority': 100,
            'tags': ['test', 'firewall']
        }
        
        # Effectuer la requête
        url = reverse('security-rule-list')
        response = self.client.post(url, rule_data, format='json')
        
        # Vérifier la réponse
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'Test Rule')
        
        # Vérifier que le cas d'utilisation a été appelé correctement
        mock_use_case.create_rule.assert_called_once()
    
    @patch('security_management.di_container.container.rule_management_use_case')
    def test_update_rule(self, mock_use_case):
        """
        Test de la méthode update du SecurityRuleViewSet.
        """
        # Configurer les mocks
        mock_use_case.get_rule.return_value = self.test_rule
        mock_use_case.update_rule.return_value = SecurityRule(
            id='test-rule-1',
            name='Updated Test Rule',
            description='An updated test security rule',
            rule_type=RuleType.FIREWALL,
            content='alert tcp any any -> any any (msg:"Updated Test Rule"; sid:1000001;)',
            source_ip='192.168.1.0/24',
            destination_ip='any',
            protocol='tcp',
            action=ActionType.ALERT,
            enabled=True,
            priority=100,
            tags=['test', 'firewall', 'updated']
        )
        
        # Données de la requête
        update_data = {
            'name': 'Updated Test Rule',
            'description': 'An updated test security rule',
            'content': 'alert tcp any any -> any any (msg:"Updated Test Rule"; sid:1000001;)',
            'tags': ['test', 'firewall', 'updated']
        }
        
        # Effectuer la requête
        url = reverse('security-rule-detail', args=['test-rule-1'])
        response = self.client.put(url, update_data, format='json')
        
        # Vérifier la réponse
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Updated Test Rule')
        self.assertEqual(response.data['description'], 'An updated test security rule')
        
        # Vérifier que le cas d'utilisation a été appelé correctement
        mock_use_case.update_rule.assert_called_once_with('test-rule-1', update_data)
    
    @patch('security_management.di_container.container.rule_management_use_case')
    def test_delete_rule(self, mock_use_case):
        """
        Test de la méthode destroy du SecurityRuleViewSet.
        """
        # Configurer le mock
        mock_use_case.delete_rule.return_value = True
        
        # Effectuer la requête
        url = reverse('security-rule-detail', args=['test-rule-1'])
        response = self.client.delete(url)
        
        # Vérifier la réponse
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        # Vérifier que le cas d'utilisation a été appelé correctement
        mock_use_case.delete_rule.assert_called_once_with('test-rule-1')
    
    @patch('security_management.di_container.container.rule_management_use_case')
    def test_toggle_rule_status(self, mock_use_case):
        """
        Test de la méthode toggle_status du SecurityRuleViewSet.
        """
        # Configurer le mock
        updated_rule = SecurityRule(
            id='test-rule-1',
            name='Test Rule',
            description='A test security rule',
            rule_type=RuleType.FIREWALL,
            content='alert tcp any any -> any any (msg:"Test Rule"; sid:1000001;)',
            source_ip='192.168.1.0/24',
            destination_ip='any',
            protocol='tcp',
            action=ActionType.ALERT,
            enabled=False,  # Désactivée
            priority=100,
            tags=['test', 'firewall']
        )
        mock_use_case.toggle_rule_status.return_value = updated_rule
        
        # Effectuer la requête
        url = reverse('security-rule-toggle-status', args=['test-rule-1'])
        response = self.client.patch(url, {'enabled': False}, format='json')
        
        # Vérifier la réponse
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['enabled'], False)
        
        # Vérifier que le cas d'utilisation a été appelé correctement
        mock_use_case.toggle_rule_status.assert_called_once_with('test-rule-1', False)


class SecurityAlertViewSetTests(TestCase):
    """
    Tests pour le SecurityAlertViewSet.
    """
    
    def setUp(self):
        """
        Configuration initiale pour les tests.
        """
        self.client = APIClient()
        
        # Créer un utilisateur pour l'authentification
        from django.contrib.auth import get_user_model
        User = get_user_model()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword'
        )
        
        # Authentifier le client
        self.client.force_authenticate(user=self.user)
        
        # Créer une alerte de sécurité de test
        self.test_alert = SecurityAlert(
            id='test-alert-1',
            title='Test Alert',
            description='A test security alert',
            source_ip='192.168.1.100',
            destination_ip='10.0.0.1',
            source_port='12345',
            destination_port='80',
            protocol='tcp',
            detection_time='2023-06-15T14:30:00Z',
            severity=SeverityLevel.HIGH,
            status='new',
            source_rule_id='test-rule-1',
            raw_data={'packet_data': 'test data'},
            false_positive=False,
            tags=['test', 'suspicious']
        )
    
    @patch('security_management.di_container.container.alert_management_use_case')
    def test_list_alerts(self, mock_use_case):
        """
        Test de la méthode list du SecurityAlertViewSet.
        """
        # Configurer le mock
        mock_use_case.list_alerts.return_value = [self.test_alert]
        
        # Effectuer la requête
        url = reverse('security-alert-list')
        response = self.client.get(url)
        
        # Vérifier la réponse
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['title'], 'Test Alert')
        self.assertEqual(response.data[0]['severity'], 'high')
        
        # Vérifier que le cas d'utilisation a été appelé correctement
        mock_use_case.list_alerts.assert_called_once_with({})
    
    @patch('security_management.di_container.container.alert_management_use_case')
    def test_retrieve_alert(self, mock_use_case):
        """
        Test de la méthode retrieve du SecurityAlertViewSet.
        """
        # Configurer le mock
        mock_use_case.get_alert.return_value = self.test_alert
        
        # Effectuer la requête
        url = reverse('security-alert-detail', args=['test-alert-1'])
        response = self.client.get(url)
        
        # Vérifier la réponse
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], 'test-alert-1')
        self.assertEqual(response.data['title'], 'Test Alert')
        
        # Vérifier que le cas d'utilisation a été appelé correctement
        mock_use_case.get_alert.assert_called_once_with('test-alert-1')
    
    @patch('security_management.di_container.container.alert_management_use_case')
    def test_mark_processed(self, mock_use_case):
        """
        Test de la méthode mark_processed du SecurityAlertViewSet.
        """
        # Configurer les mocks
        mock_use_case.mark_as_processed.return_value = True
        
        updated_alert = SecurityAlert(
            id='test-alert-1',
            title='Test Alert',
            description='A test security alert',
            source_ip='192.168.1.100',
            destination_ip='10.0.0.1',
            protocol='tcp',
            detection_time='2023-06-15T14:30:00Z',
            severity=SeverityLevel.HIGH,
            status='processed',  # Statut mis à jour
            source_rule_id='test-rule-1',
            false_positive=False
        )
        mock_use_case.get_alert.return_value = updated_alert
        
        # Effectuer la requête
        url = reverse('security-alert-mark-processed', args=['test-alert-1'])
        response = self.client.patch(url)
        
        # Vérifier la réponse
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'processed')
        
        # Vérifier que les cas d'utilisation ont été appelés correctement
        mock_use_case.mark_as_processed.assert_called_once_with('test-alert-1')
        mock_use_case.get_alert.assert_called_once_with('test-alert-1')
    
    @patch('security_management.di_container.container.alert_management_use_case')
    def test_mark_false_positive(self, mock_use_case):
        """
        Test de la méthode mark_false_positive du SecurityAlertViewSet.
        """
        # Configurer les mocks
        mock_use_case.mark_as_false_positive.return_value = True
        
        updated_alert = SecurityAlert(
            id='test-alert-1',
            title='Test Alert',
            description='A test security alert',
            source_ip='192.168.1.100',
            destination_ip='10.0.0.1',
            protocol='tcp',
            detection_time='2023-06-15T14:30:00Z',
            severity=SeverityLevel.HIGH,
            status='false_positive',  # Statut mis à jour
            source_rule_id='test-rule-1',
            false_positive=True  # Marqué comme faux positif
        )
        mock_use_case.get_alert.return_value = updated_alert
        
        # Effectuer la requête
        url = reverse('security-alert-mark-false-positive', args=['test-alert-1'])
        response = self.client.patch(url)
        
        # Vérifier la réponse
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['false_positive'], True)
        self.assertEqual(response.data['status'], 'false_positive')
        
        # Vérifier que les cas d'utilisation ont été appelés correctement
        mock_use_case.mark_as_false_positive.assert_called_once_with('test-alert-1')
        mock_use_case.get_alert.assert_called_once_with('test-alert-1') 