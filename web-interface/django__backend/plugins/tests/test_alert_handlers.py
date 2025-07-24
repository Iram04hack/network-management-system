"""
Tests pour les handlers d'alertes.
"""
import pytest
from unittest.mock import patch, MagicMock
from django.conf import settings
from ..alert_handlers.email_handler import EmailAlertHandler
from ..alert_handlers.slack_handler import SlackAlertHandler


class TestEmailAlertHandler:
    """Tests pour le handler d'alertes par email."""
    
    def setup_method(self):
        """Configuration des tests."""
        self.handler = EmailAlertHandler()
        # Simuler les paramètres de configuration
        self.handler.recipients = ['test@example.com']
        self.handler.enabled = True
        self.handler.from_email = 'nms@example.com'
    
    def test_initialize(self):
        """Test de l'initialisation du handler."""
        assert self.handler.initialize() == True
        
        # Tester le cas où le handler est désactivé
        self.handler.enabled = False
        assert self.handler.initialize() == False
    
    def test_cleanup(self):
        """Test du nettoyage des ressources."""
        assert self.handler.cleanup() == True
    
    def test_get_metadata(self):
        """Test des métadonnées du plugin."""
        metadata = self.handler.get_metadata()
        assert metadata['id'] == 'email_alert_handler'
        assert metadata['name'] == 'email'
        assert isinstance(metadata['version'], str)
    
    def test_can_handle(self):
        """Test de la méthode can_handle."""
        # Le handler devrait pouvoir traiter les alertes s'il est activé
        assert self.handler.can_handle(MagicMock()) == True
        
        # Désactiver le handler
        self.handler.enabled = False
        assert self.handler.can_handle(MagicMock()) == False
    
    @patch('django.core.mail.send_mail')
    def test_handle_alert_security(self, mock_send_mail):
        """Test du traitement d'une alerte de sécurité."""
        # Créer un mock de SecurityAlert
        from security_management.models import SecurityAlert
        alert = MagicMock(spec=SecurityAlert)
        alert.severity = 'high'
        alert.source = 'firewall'
        alert.message = 'Test alert'
        alert.id = 123
        alert.timestamp.isoformat.return_value = '2023-01-01T12:00:00'
        
        # Tester le handler
        result = self.handler.handle_alert(alert)
        
        # Vérifier que send_mail a été appelé avec les bons arguments
        mock_send_mail.assert_called_once()
        args = mock_send_mail.call_args[1]
        assert 'Alerte de sécurité HIGH' in args['subject']
        assert args['from_email'] == 'nms@example.com'
        assert args['recipient_list'] == ['test@example.com']
        
        # Vérifier le résultat
        assert result['success'] == True
        assert result['recipients'] == 1


class TestSlackAlertHandler:
    """Tests pour le handler d'alertes par Slack."""
    
    def setup_method(self):
        """Configuration des tests."""
        self.handler = SlackAlertHandler()
        # Simuler les paramètres de configuration
        self.handler.webhook_url = 'https://hooks.slack.com/test'
        self.handler.enabled = True
    
    def test_initialize(self):
        """Test de l'initialisation du handler."""
        assert self.handler.initialize() == True
        
        # Tester le cas où le handler est désactivé
        self.handler.enabled = False
        assert self.handler.initialize() == False
    
    def test_cleanup(self):
        """Test du nettoyage des ressources."""
        assert self.handler.cleanup() == True
    
    def test_get_metadata(self):
        """Test des métadonnées du plugin."""
        metadata = self.handler.get_metadata()
        assert metadata['id'] == 'slack_alert_handler'
        assert metadata['name'] == 'slack'
        assert isinstance(metadata['version'], str)
    
    def test_can_handle(self):
        """Test de la méthode can_handle."""
        # Le handler devrait pouvoir traiter les alertes s'il est activé
        assert self.handler.can_handle(MagicMock()) == True
        
        # Désactiver le handler
        self.handler.enabled = False
        assert self.handler.can_handle(MagicMock()) == False
    
    @patch('requests.post')
    def test_handle_alert_security(self, mock_post):
        """Test du traitement d'une alerte de sécurité."""
        # Simuler une réponse réussie
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        # Créer un mock de SecurityAlert
        from security_management.models import SecurityAlert
        alert = MagicMock(spec=SecurityAlert)
        alert.severity = 'high'
        alert.source = 'firewall'
        alert.message = 'Test alert'
        alert.event_type = 'intrusion'
        alert.source_ip = '192.168.1.1'
        alert.destination_ip = '10.0.0.1'
        alert.status = 'open'
        alert.timestamp.isoformat.return_value = '2023-01-01T12:00:00'
        
        # Tester le handler
        result = self.handler.handle_alert(alert)
        
        # Vérifier que requests.post a été appelé avec les bons arguments
        mock_post.assert_called_once()
        args = mock_post.call_args
        assert args[0][0] == 'https://hooks.slack.com/test'
        assert 'json' in args[1]
        assert 'headers' in args[1]
        json_data = args[1]['json']
        assert 'Alerte de sécurité - HIGH' in json_data['text']
        
        # Vérifier le résultat
        assert result['success'] == True
        assert result['status_code'] == 200
    
    @patch('requests.post')
    def test_handle_alert_disabled(self, mock_post):
        """Test du traitement d'une alerte quand le handler est désactivé."""
        self.handler.enabled = False
        result = self.handler.handle_alert(MagicMock())
        
        # Vérifier que requests.post n'a pas été appelé
        mock_post.assert_not_called()
        
        # Vérifier le résultat
        assert result['success'] == False
        assert 'not configured' in result['error'] 