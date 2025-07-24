"""
Handler d'alertes par email.

Ce module fournit un handler qui envoie des notifications par email
lorsque des alertes sont déclenchées.
"""
import logging
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.utils.html import strip_tags
from ..infrastructure.registry import register_plugin
from ...domain.interfaces import AlertHandlerPlugin

logger = logging.getLogger(__name__)

@register_plugin('alert_handlers')
class EmailAlertHandler(AlertHandlerPlugin):
    """Handler pour envoyer des alertes par e-mail"""
    name = "email"
    
    def __init__(self):
        self.recipients = getattr(settings, 'ALERT_EMAIL_RECIPIENTS', [])
        self.enabled = bool(self.recipients)
        self.from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'nms@example.com')
    
    def initialize(self) -> bool:
        """Initialise le plugin."""
        return self.enabled
    
    def cleanup(self) -> bool:
        """Nettoie les ressources utilisées par le plugin."""
        return True
    
    def get_metadata(self):
        """Retourne les métadonnées du plugin."""
        return {
            'id': 'email_alert_handler',
            'name': self.name,
            'version': '1.0.0',
            'description': 'Envoie des alertes par e-mail',
            'author': 'Équipe NMS',
            'dependencies': [],
            'provides': ['alert_notification']
        }
    
    def can_handle(self, alert):
        """Vérifie si ce handler peut traiter cette alerte"""
        return self.enabled
    
    def handle_alert(self, alert):
        """
        Envoie une alerte par e-mail.
        
        Args:
            alert: Objet SecurityAlert ou Alert
            
        Returns:
            Dict avec le résultat de l'opération
        """
        if not self.enabled:
            return {"success": False, "error": "Email integration not configured"}
        
        try:
            # Importer ici pour éviter l'import circulaire
            from security_management.models import SecurityAlert
            from monitoring.models import Alert
            
            # Déterminer le type d'alerte
            if isinstance(alert, SecurityAlert):
                return self._handle_security_alert(alert)
            elif isinstance(alert, Alert):
                return self._handle_monitoring_alert(alert)
            else:
                return {"success": False, "error": f"Unsupported alert type: {type(alert).__name__}"}
        except Exception as e:
            logger.error(f"Error sending alert email: {e}")
            return {"success": False, "error": str(e)}
    
    def _handle_security_alert(self, alert):
        """Traite une alerte de sécurité"""
        subject = f"[NMS] Alerte de sécurité {alert.severity.upper()} - {alert.source}"
        
        # Préparer le contexte pour le template
        context = {
            'alert': alert,
            'alert_type': 'security',
            'url': settings.BASE_URL + f'/security/alerts/{alert.id}' if hasattr(settings, 'BASE_URL') else ''
        }
        
        # Rendre le template
        html_message = render_to_string('emails/security_alert.html', context)
        plain_message = strip_tags(html_message)
        
        # Envoyer l'e-mail
        send_mail(
            subject=subject,
            message=plain_message,
            html_message=html_message,
            from_email=self.from_email,
            recipient_list=self.recipients,
            fail_silently=False
        )
        
        return {"success": True, "recipients": len(self.recipients)}
    
    def _handle_monitoring_alert(self, alert):
        """Traite une alerte de monitoring"""
        device_name = alert.device.name if alert.device else "N/A"
        subject = f"[NMS] Alerte de monitoring {alert.severity.upper()} - {device_name}"
        
        # Préparer le contexte pour le template
        context = {
            'alert': alert,
            'alert_type': 'monitoring',
            'device_name': device_name,
            'service_name': alert.service_check.name if alert.service_check else "N/A",
            'url': settings.BASE_URL + f'/monitoring/alerts/{alert.id}' if hasattr(settings, 'BASE_URL') else ''
        }
        
        # Rendre le template
        html_message = render_to_string('emails/monitoring_alert.html', context)
        plain_message = strip_tags(html_message)
        
        # Envoyer l'e-mail
        send_mail(
            subject=subject,
            message=plain_message,
            html_message=html_message,
            from_email=self.from_email,
            recipient_list=self.recipients,
            fail_silently=False
        )
        
        return {"success": True, "recipients": len(self.recipients)} 