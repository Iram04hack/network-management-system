"""
Tests unitaires pour le service d'alerte.
"""
from django.test import TestCase
from django.conf import settings
from unittest.mock import patch, MagicMock, call
import requests
# from security_management.models import SecurityAlert  # Module désactivé
from monitoring.models import Alert
from ...application.services import AlertService


class AlertServiceTestCase(TestCase):
    """Tests pour le service d'alerte."""
    
    def setUp(self):
        """Configuration initiale pour les tests."""
        # Créer une alerte de sécurité pour les tests
        self.security_alert = SecurityAlert.objects.create(
            severity="high",
            message="Test security alert",
            source="test",
            event_type="test_event",
            source_ip="192.168.1.1",
            destination_ip="192.168.1.2"
        )
        
        # Créer une alerte de monitoring pour les tests
        self.monitoring_alert = Alert.objects.create(
            severity="medium",
            message="Test monitoring alert"
        )
        
        # Configuration pour les tests
        self.test_settings = {
            'DEFAULT_ALERT_CHANNELS': ['email'],
            'ALERT_EMAIL_RECIPIENTS': ['admin@example.com'],
            'DEFAULT_FROM_EMAIL': 'nms@example.com',
            'ALERT_WEBHOOK_URL': 'https://example.com/webhook',
            'SLACK_WEBHOOK_URL': 'https://hooks.slack.com/services/test'
        }
        
        # Instancier le service
        self.alert_service = AlertService()
        
    @patch('django.core.mail.send_mail')
    @patch('requests.post')
    def test_notify_alert_security(self, mock_post, mock_send_mail):
        """Test de notification d'une alerte de sécurité par différents canaux."""
        # Configurer les mocks
        mock_post.return_value.raise_for_status.return_value = None
        
        # Exécuter avec plusieurs canaux
        with patch.multiple(settings, **self.test_settings):
            result = self.alert_service.notify_alert(
                self.security_alert, 
                channels=['email', 'webhook', 'slack']
            )
        
        # Vérifications
        self.assertIn('email', result)
        self.assertTrue(result['email'])
        self.assertIn('webhook', result)
        self.assertTrue(result['webhook'])
        self.assertIn('slack', result)
        self.assertTrue(result['slack'])
        
        # Vérifier que les méthodes ont été appelées
        mock_send_mail.assert_called_once()
        self.assertEqual(mock_post.call_count, 2)  # webhook + slack
    
    @patch('logging.Logger.error')
    def test_notify_alert_error(self, mock_logger):
        """Test de gestion d'erreur lors de la notification d'une alerte."""
        # Configurer une exception sur le canal email
        with patch.object(AlertService, 'send_email_alert', side_effect=Exception('Test error')):
            with patch.multiple(settings, **self.test_settings):
                result = self.alert_service.notify_alert(
                    self.security_alert, 
                    channels=['email']
                )
        
        # Vérifications
        self.assertIn('email', result)
        self.assertFalse(result['email'])
        mock_logger.assert_called_once()
    
    @patch('django.core.mail.send_mail')
    def test_send_email_alert(self, mock_send_mail):
        """Test d'envoi d'alerte par email."""
        # Préparer les données d'alerte
        alert_data = {
            'id': 1,
            'type': 'security',
            'severity': 'high',
            'message': 'Test message'
        }
        
        # Exécuter le service
        with patch.multiple(settings, **self.test_settings):
            result = self.alert_service.send_email_alert(alert_data)
        
        # Vérifications
        self.assertTrue(result)
        mock_send_mail.assert_called_once()
        
        # Vérifier les arguments de l'appel
        args = mock_send_mail.call_args[1]
        self.assertEqual(args['subject'], "Alerte Security - HIGH")
        self.assertEqual(args['from_email'], "nms@example.com")
        self.assertEqual(args['recipient_list'], ["admin@example.com"])
    
    def test_send_email_alert_no_recipients(self):
        """Test d'envoi d'alerte par email sans destinataires configurés."""
        # Préparer les données d'alerte
        alert_data = {
            'id': 1,
            'type': 'security',
            'severity': 'high',
            'message': 'Test message'
        }
        
        # Exécuter le service avec une configuration sans destinataires
        with patch.multiple(settings, ALERT_EMAIL_RECIPIENTS=[]):
            result = self.alert_service.send_email_alert(alert_data)
        
        # Vérifications
        self.assertFalse(result)
    
    @patch('requests.post')
    def test_send_webhook_alert(self, mock_post):
        """Test d'envoi d'alerte via webhook."""
        # Configurer le mock
        mock_post.return_value.raise_for_status.return_value = None
        
        # Préparer les données d'alerte
        alert_data = {
            'id': 1,
            'type': 'security',
            'severity': 'high',
            'message': 'Test message'
        }
        
        # Exécuter le service
        with patch.multiple(settings, ALERT_WEBHOOK_URL='https://example.com/webhook'):
            result = self.alert_service.send_webhook_alert(alert_data)
        
        # Vérifications
        self.assertTrue(result)
        mock_post.assert_called_once_with(
            'https://example.com/webhook',
            json=alert_data,
            headers={'Content-Type': 'application/json'},
            timeout=5
        )
    
    def test_send_webhook_alert_no_url(self):
        """Test d'envoi d'alerte webhook sans URL configurée."""
        # Préparer les données d'alerte
        alert_data = {
            'id': 1,
            'type': 'security',
            'severity': 'high',
            'message': 'Test message'
        }
        
        # Exécuter le service avec une configuration sans URL webhook
        with patch.multiple(settings, ALERT_WEBHOOK_URL=None):
            result = self.alert_service.send_webhook_alert(alert_data)
        
        # Vérifications
        self.assertFalse(result)
    
    @patch('requests.post')
    def test_send_webhook_alert_error(self, mock_post):
        """Test d'erreur lors de l'envoi d'alerte via webhook."""
        # Configurer le mock pour lever une exception
        mock_post.side_effect = requests.exceptions.RequestException("Test error")
        
        # Préparer les données d'alerte
        alert_data = {
            'id': 1,
            'type': 'security',
            'severity': 'high',
            'message': 'Test message'
        }
        
        # Exécuter le service
        with patch.multiple(settings, ALERT_WEBHOOK_URL='https://example.com/webhook'):
            result = self.alert_service.send_webhook_alert(alert_data)
        
        # Vérifications
        self.assertFalse(result)
    
    @patch('requests.post')
    def test_send_slack_alert(self, mock_post):
        """Test d'envoi d'alerte via Slack."""
        # Configurer le mock
        mock_post.return_value.raise_for_status.return_value = None
        
        # Préparer les données d'alerte pour le type Security
        alert_data = {
            'id': 1,
            'type': 'security',
            'severity': 'high',
            'message': 'Security test message',
            'timestamp': '2023-01-01T12:00:00',
            'source': 'firewall',
            'event_type': 'intrusion',
            'source_ip': '192.168.1.1',
            'destination_ip': '192.168.1.2'
        }
        
        # Exécuter le service
        with patch.multiple(settings, SLACK_WEBHOOK_URL='https://hooks.slack.com/services/test'):
            result = self.alert_service.send_slack_alert(alert_data)
        
        # Vérifications
        self.assertTrue(result)
        mock_post.assert_called_once()
        
        # Vérifier que le payload Slack contient les champs attendus
        payload = mock_post.call_args[1]['json']
        self.assertIn('blocks', payload)
        self.assertIn('text', payload)
        self.assertIn('Security', payload['text'])
        self.assertIn('HIGH', payload['text'])
        
        # Tester également avec une alerte de monitoring
        mock_post.reset_mock()
        alert_data = {
            'id': 2,
            'type': 'monitoring',
            'severity': 'medium',
            'message': 'Monitoring test message',
            'timestamp': '2023-01-01T12:00:00',
            'device': 'server1',
            'service_check': 'cpu_check',
            'metric': 'cpu_usage'
        }
        
        with patch.multiple(settings, SLACK_WEBHOOK_URL='https://hooks.slack.com/services/test'):
            result = self.alert_service.send_slack_alert(alert_data)
            
        self.assertTrue(result)
        mock_post.assert_called_once()
    
    def test_send_slack_alert_no_url(self):
        """Test d'envoi d'alerte Slack sans URL configurée."""
        # Préparer les données d'alerte
        alert_data = {
            'id': 1,
            'type': 'security',
            'severity': 'high',
            'message': 'Test message',
            'timestamp': '2023-01-01T12:00:00'
        }
        
        # Exécuter le service avec une configuration sans URL Slack
        with patch.multiple(settings, SLACK_WEBHOOK_URL=None):
            result = self.alert_service.send_slack_alert(alert_data)
        
        # Vérifications
        self.assertFalse(result) 