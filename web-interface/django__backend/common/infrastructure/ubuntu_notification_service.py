"""
Service de notification Ubuntu 24.04 pour le NMS.
"""
import logging
import subprocess
import os
from typing import Dict, List, Any, Optional
from django.conf import settings

logger = logging.getLogger(__name__)

class UbuntuNotificationService:
    """
    Service pour envoyer des notifications système Ubuntu 24.04.
    """
    
    def __init__(self):
        self.app_name = "Network Management System"
        self.default_icon = "network-workgroup"
        self.notification_history = []
        self.max_history = 100
        
        # Vérifier si notify-send est disponible
        self.notify_send_available = self._check_notify_send()
        
    def _check_notify_send(self) -> bool:
        """
        Vérifie si notify-send est disponible sur le système.
        
        Returns:
            True si notify-send est disponible
        """
        try:
            # Vérifier si notify-send existe
            result = subprocess.run(['which', 'notify-send'], 
                                  capture_output=True, text=True, timeout=5)
            
            if result.returncode != 0:
                logger.warning("notify-send non installé - notifications Ubuntu désactivées")
                return False
            
            # Initialiser dbus pour l'environnement Docker
            try:
                # Créer un socket dbus session si nécessaire
                os.environ.setdefault('DISPLAY', ':99')  # Display virtuel pour Docker
                subprocess.run(['dbus-launch', '--sh-syntax'], 
                             capture_output=True, timeout=10)
            except Exception:
                pass  # Ignore les erreurs d'initialisation dbus
            
            # Test simple de notify-send
            test_result = subprocess.run(['notify-send', '--version'], 
                                       capture_output=True, text=True, timeout=5)
            
            if test_result.returncode == 0:
                logger.info("✅ notify-send disponible et fonctionnel pour les notifications Ubuntu")
                return True
            else:
                logger.warning("notify-send installé mais non fonctionnel - notifications Ubuntu désactivées")
                return False
                
        except Exception as e:
            logger.error(f"Erreur lors de la vérification de notify-send: {e}")
            return False
            
    def send_notification(self, title: str, message: str, 
                         urgency: str = 'normal', 
                         category: str = 'network',
                         icon: Optional[str] = None,
                         timeout: int = 5000) -> bool:
        """
        Envoie une notification système Ubuntu.
        
        Args:
            title: Titre de la notification
            message: Message de la notification
            urgency: Urgence (low, normal, critical)
            category: Catégorie de la notification
            icon: Icône à utiliser (None pour l'icône par défaut)
            timeout: Durée d'affichage en millisecondes
            
        Returns:
            True si la notification a été envoyée avec succès
        """
        if not self.notify_send_available:
            logger.debug("notify-send non disponible - notification ignorée")
            return False
            
        try:
            # Préparer la commande
            cmd = [
                'notify-send',
                '--app-name', self.app_name,
                '--icon', icon or self.default_icon,
                '--category', category,
                '--urgency', urgency,
                '--expire-time', str(timeout),
                title,
                message
            ]
            
            # Exécuter la commande
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            success = result.returncode == 0
            
            if success:
                logger.info(f"Notification Ubuntu envoyée: {title}")
                
                # Ajouter à l'historique
                self._add_to_history({
                    'title': title,
                    'message': message,
                    'urgency': urgency,
                    'category': category,
                    'icon': icon or self.default_icon,
                    'timestamp': self._get_timestamp(),
                    'success': True
                })
            else:
                logger.error(f"Échec de l'envoi de notification: {result.stderr}")
                self._add_to_history({
                    'title': title,
                    'message': message,
                    'error': result.stderr,
                    'timestamp': self._get_timestamp(),
                    'success': False
                })
                
            return success
            
        except subprocess.TimeoutExpired:
            logger.error("Timeout lors de l'envoi de la notification")
            return False
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi de la notification: {e}")
            return False
            
    def send_gns3_detection_notification(self, gns3_info: Dict[str, Any]) -> bool:
        """
        Envoie une notification spécifique pour la détection GNS3.
        
        Args:
            gns3_info: Informations sur la détection GNS3
            
        Returns:
            True si la notification a été envoyée avec succès
        """
        if gns3_info.get('available'):
            title = "🌐 Serveur GNS3 détecté"
            message = (f"Serveur GNS3 v{gns3_info.get('version', 'Inconnue')} "
                      f"disponible sur {gns3_info.get('host')}:{gns3_info.get('port')}\n"
                      f"Projets détectés: {gns3_info.get('projects_count', 0)}")
            urgency = 'normal'
            icon = 'network-server'
        else:
            title = "⚠️ Serveur GNS3 indisponible"
            message = (f"Impossible de se connecter au serveur GNS3\n"
                      f"Host: {gns3_info.get('host')}:{gns3_info.get('port')}\n"
                      f"Erreur: {gns3_info.get('error', 'Inconnue')}")
            urgency = 'critical'
            icon = 'network-error'
            
        return self.send_notification(
            title=title,
            message=message,
            urgency=urgency,
            category='network.gns3',
            icon=icon,
            timeout=8000
        )
        
    def send_security_alert(self, alert_type: str, details: str) -> bool:
        """
        Envoie une notification d'alerte de sécurité.
        
        Args:
            alert_type: Type d'alerte
            details: Détails de l'alerte
            
        Returns:
            True si la notification a été envoyée avec succès
        """
        return self.send_notification(
            title=f"🚨 Alerte de sécurité: {alert_type}",
            message=details,
            urgency='critical',
            category='security',
            icon='security-high',
            timeout=10000
        )
        
    def send_network_event(self, event_type: str, details: str) -> bool:
        """
        Envoie une notification d'événement réseau.
        
        Args:
            event_type: Type d'événement
            details: Détails de l'événement
            
        Returns:
            True si la notification a été envoyée avec succès
        """
        return self.send_notification(
            title=f"🔗 Événement réseau: {event_type}",
            message=details,
            urgency='normal',
            category='network',
            icon='network-transmit-receive',
            timeout=6000
        )
        
    def send_monitoring_alert(self, metric: str, value: str, threshold: str) -> bool:
        """
        Envoie une notification d'alerte de monitoring.
        
        Args:
            metric: Métrique concernée
            value: Valeur actuelle
            threshold: Seuil dépassé
            
        Returns:
            True si la notification a été envoyée avec succès
        """
        return self.send_notification(
            title=f"📊 Alerte monitoring: {metric}",
            message=f"Valeur: {value}\nSeuil: {threshold}",
            urgency='normal',
            category='monitoring',
            icon='utilities-system-monitor',
            timeout=7000
        )
        
    def send_service_status(self, service_name: str, status: str, details: str = "") -> bool:
        """
        Envoie une notification de changement de statut de service.
        
        Args:
            service_name: Nom du service
            status: Nouveau statut
            details: Détails supplémentaires
            
        Returns:
            True si la notification a été envoyée avec succès
        """
        status_icons = {
            'started': 'media-playback-start',
            'stopped': 'media-playback-stop',
            'error': 'dialog-error',
            'warning': 'dialog-warning',
            'ok': 'dialog-information'
        }
        
        status_urgency = {
            'started': 'normal',
            'stopped': 'normal',
            'error': 'critical',
            'warning': 'normal',
            'ok': 'low'
        }
        
        message = f"Service: {service_name}\nStatut: {status}"
        if details:
            message += f"\n{details}"
            
        return self.send_notification(
            title=f"🔧 Service {status}",
            message=message,
            urgency=status_urgency.get(status, 'normal'),
            category='system',
            icon=status_icons.get(status, 'system-run'),
            timeout=5000
        )
        
    def _add_to_history(self, notification_data: Dict[str, Any]):
        """
        Ajoute une notification à l'historique.
        
        Args:
            notification_data: Données de la notification
        """
        self.notification_history.append(notification_data)
        
        # Limiter la taille de l'historique
        if len(self.notification_history) > self.max_history:
            self.notification_history = self.notification_history[-self.max_history:]
            
    def _get_timestamp(self) -> str:
        """
        Récupère un timestamp formaté.
        
        Returns:
            Timestamp au format ISO
        """
        from django.utils import timezone
        return timezone.now().isoformat()
        
    def get_notification_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Récupère l'historique des notifications.
        
        Args:
            limit: Nombre maximum de notifications à retourner
            
        Returns:
            Liste des notifications récentes
        """
        return self.notification_history[-limit:]
        
    def test_notification(self) -> bool:
        """
        Envoie une notification de test.
        
        Returns:
            True si la notification de test a été envoyée avec succès
        """
        return self.send_notification(
            title="🧪 Test de notification NMS",
            message="Ceci est une notification de test du Network Management System",
            urgency='low',
            category='test',
            icon='applications-system',
            timeout=3000
        )
        
    def get_status(self) -> Dict[str, Any]:
        """
        Récupère le statut du service de notification.
        
        Returns:
            Statut du service
        """
        return {
            'notify_send_available': self.notify_send_available,
            'app_name': self.app_name,
            'default_icon': self.default_icon,
            'notification_history_size': len(self.notification_history),
            'max_history_size': self.max_history,
            'last_notification': self.notification_history[-1] if self.notification_history else None
        }

# Instance globale du service
ubuntu_notification_service = UbuntuNotificationService()