"""
Tests unitaires pour le service de notification.
"""
from django.test import TestCase
from django.contrib.auth.models import User
from monitoring.models import Notification
from unittest.mock import patch, MagicMock
from ...application.services import NotificationService


class NotificationServiceTestCase(TestCase):
    """Tests pour le service de notification."""
    
    def setUp(self):
        """Configuration initiale pour les tests."""
        # Créer des utilisateurs pour les tests
        self.user1 = User.objects.create_user(username='test_user1', password='password123')
        self.user2 = User.objects.create_user(username='test_user2', password='password123')
        self.admin = User.objects.create_user(username='admin', password='password123', is_staff=True)
        
        # Instancier le service
        self.notification_service = NotificationService()
        
    def test_send_notification_single_user(self):
        """Test d'envoi de notification à un seul utilisateur."""
        # Exécuter le service
        notifications = self.notification_service.send_notification(
            user_ids=self.user1.id,
            title="Test notification",
            message="This is a test message",
            level="info",
            source="test"
        )
        
        # Vérifications
        self.assertEqual(len(notifications), 1)
        self.assertEqual(notifications[0].user, self.user1)
        self.assertEqual(notifications[0].title, "Test notification")
        self.assertEqual(notifications[0].message, "This is a test message")
        self.assertEqual(notifications[0].level, "info")
        self.assertEqual(notifications[0].source, "test")
        
        # Vérifier en base de données
        db_notification = Notification.objects.filter(user=self.user1).first()
        self.assertIsNotNone(db_notification)
        self.assertEqual(db_notification.title, "Test notification")
        
    def test_send_notification_multiple_users(self):
        """Test d'envoi de notification à plusieurs utilisateurs."""
        # Exécuter le service
        notifications = self.notification_service.send_notification(
            user_ids=[self.user1.id, self.user2.id],
            title="Mass notification",
            message="This is a mass notification",
            level="warning",
            source="test"
        )
        
        # Vérifications
        self.assertEqual(len(notifications), 2)
        
        # Vérifier en base de données
        db_notifications = Notification.objects.filter(title="Mass notification")
        self.assertEqual(db_notifications.count(), 2)
        
        # Vérifier les utilisateurs notifiés
        notified_users = set([n.user for n in db_notifications])
        self.assertEqual(notified_users, {self.user1, self.user2})
        
    def test_send_notification_nonexistent_user(self):
        """Test d'envoi de notification à un utilisateur inexistant."""
        # Exécuter le service avec un ID inexistant
        notifications = self.notification_service.send_notification(
            user_ids=999999,  # ID inexistant
            title="Test notification",
            message="This should not be sent",
            level="info",
            source="test"
        )
        
        # Vérification qu'aucune notification n'a été créée
        self.assertEqual(len(notifications), 0)
        self.assertEqual(Notification.objects.count(), 0)
        
    @patch('logging.Logger.error')
    def test_send_notification_error(self, mock_logger):
        """Test de gestion d'erreur lors de l'envoi de notification."""
        with patch('monitoring.models.Notification.objects.create', side_effect=Exception("Test error")):
            # Exécuter le service avec une erreur simulée
            notifications = self.notification_service.send_notification(
                user_ids=self.user1.id,
                title="Error notification",
                message="This should cause an error",
                level="info",
                source="test"
            )
            
            # Vérifications
            self.assertEqual(len(notifications), 0)
            # Vérifier que l'erreur a été journalisée
            mock_logger.assert_called_once()
            
    def test_send_notification_to_admins(self):
        """Test d'envoi de notification aux administrateurs."""
        # Exécuter le service
        notifications = self.notification_service.send_notification_to_admins(
            title="Admin notification",
            message="This is for admins only",
            level="critical",
            source="system"
        )
        
        # Vérifications
        self.assertEqual(len(notifications), 1)  # Seulement l'admin doit recevoir
        self.assertEqual(notifications[0].user, self.admin)
        self.assertEqual(notifications[0].title, "Admin notification")
        
        # Vérifier en base de données pour s'assurer que seuls les admins reçoivent
        db_notifications = Notification.objects.filter(title="Admin notification")
        self.assertEqual(db_notifications.count(), 1)
        self.assertEqual(db_notifications[0].user, self.admin)
        
    def test_mark_as_read(self):
        """Test pour marquer une notification comme lue."""
        # Créer une notification pour le test
        notification = Notification.objects.create(
            user=self.user1,
            title="Read test",
            message="This will be marked as read",
            level="info"
        )
        
        # Vérifier que la notification est non lue au départ
        self.assertFalse(notification.is_read)
        
        # Marquer comme lue
        result = self.notification_service.mark_as_read(notification.id, self.user1.id)
        
        # Vérifications
        self.assertTrue(result)
        
        # Recharger depuis la base et vérifier
        notification.refresh_from_db()
        self.assertTrue(notification.is_read)
        
    def test_mark_as_read_nonexistent_notification(self):
        """Test pour marquer une notification inexistante comme lue."""
        # Tenter de marquer une notification inexistante
        result = self.notification_service.mark_as_read(999999, self.user1.id)
        
        # Vérifier que l'opération a échoué
        self.assertFalse(result)
        
    def test_mark_as_read_wrong_user(self):
        """Test pour marquer une notification d'un autre utilisateur comme lue."""
        # Créer une notification pour l'utilisateur 1
        notification = Notification.objects.create(
            user=self.user1,
            title="Wrong user test",
            message="User2 will try to mark this as read",
            level="info"
        )
        
        # Tenter de marquer comme lue avec l'utilisateur 2
        result = self.notification_service.mark_as_read(notification.id, self.user2.id)
        
        # Vérifier que l'opération a échoué
        self.assertFalse(result)
        
        # Recharger depuis la base et vérifier qu'elle reste non lue
        notification.refresh_from_db()
        self.assertFalse(notification.is_read) 