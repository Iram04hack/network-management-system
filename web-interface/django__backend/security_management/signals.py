"""
Signaux Django pour le module security_management.

Ce fichier définit les signaux Django et leurs gestionnaires pour le module
de gestion de la sécurité, permettant de réagir aux événements système.
"""

import logging
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver, Signal
from django.conf import settings

# Signaux personnalisés
security_alert_detected = Signal()  # Émis quand une nouvelle alerte de sécurité est détectée
security_rule_triggered = Signal()  # Émis quand une règle de sécurité est déclenchée
security_threat_detected = Signal()  # Émis quand une menace potentielle est détectée

logger = logging.getLogger(__name__)


@receiver(security_alert_detected)
def handle_security_alert(sender, **kwargs):
    """
    Gestionnaire pour le signal security_alert_detected.
    
    Ce gestionnaire est appelé lorsqu'une nouvelle alerte de sécurité est détectée.
    Il peut envoyer des notifications, mettre à jour des statistiques, etc.
    
    Args:
        sender: L'émetteur du signal
        **kwargs: Arguments supplémentaires, notamment 'alert' contenant l'alerte détectée
    """
    alert = kwargs.get('alert')
    if not alert:
        return
    
    logger.info(f"Nouvelle alerte de sécurité détectée: {alert.title} (Sévérité: {alert.severity})")
    
    # Notification par email pour les alertes critiques ou élevées
    if alert.severity in ['critical', 'high'] and hasattr(settings, 'SECURITY_ALERT_EMAILS'):
        from django.core.mail import send_mail
        
        try:
            send_mail(
                subject=f"[ALERTE SÉCURITÉ] {alert.title}",
                message=f"Une alerte de sécurité de niveau {alert.severity} a été détectée:\n\n"
                        f"{alert.description}\n\n"
                        f"Source IP: {alert.source_ip}\n"
                        f"Destination IP: {alert.destination_ip}\n"
                        f"Détectée à: {alert.detection_time}",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=settings.SECURITY_ALERT_EMAILS,
                fail_silently=True,
            )
            logger.info(f"Email d'alerte envoyé pour l'alerte {alert.id}")
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi de l'email d'alerte: {e}")


@receiver(security_rule_triggered)
def handle_security_rule_trigger(sender, **kwargs):
    """
    Gestionnaire pour le signal security_rule_triggered.
    
    Ce gestionnaire est appelé lorsqu'une règle de sécurité est déclenchée.
    Il met à jour les statistiques de déclenchement de la règle.
    
    Args:
        sender: L'émetteur du signal
        **kwargs: Arguments supplémentaires, notamment 'rule' contenant la règle déclenchée
                 et 'event_data' contenant les données de l'événement
    """
    from .di_container import container
    
    rule = kwargs.get('rule')
    event_data = kwargs.get('event_data', {})
    
    if not rule:
        return
    
    logger.info(f"Règle de sécurité déclenchée: {rule.name} (ID: {rule.id})")
    
    # Mettre à jour le compteur de déclenchements
    try:
        container.rule_management_use_case.increment_trigger_count(rule.id)
    except Exception as e:
        logger.error(f"Erreur lors de la mise à jour du compteur de déclenchements: {e}")


@receiver(security_threat_detected)
def handle_security_threat(sender, **kwargs):
    """
    Gestionnaire pour le signal security_threat_detected.
    
    Ce gestionnaire est appelé lorsqu'une menace de sécurité potentielle est détectée.
    Il peut déclencher des actions automatiques comme le blocage d'une IP.
    
    Args:
        sender: L'émetteur du signal
        **kwargs: Arguments supplémentaires, notamment 'threat_data' contenant les données de la menace
    """
    from .di_container import container
    
    threat_data = kwargs.get('threat_data', {})
    source_ip = threat_data.get('source_ip')
    threat_type = threat_data.get('threat_type')
    severity = threat_data.get('severity', 'medium')
    
    if not source_ip or not threat_type:
        return
    
    logger.warning(f"Menace de sécurité détectée: {threat_type} depuis {source_ip} (Sévérité: {severity})")
    
    # Action automatique pour les menaces critiques
    if severity == 'critical' and hasattr(settings, 'AUTO_BLOCK_CRITICAL_THREATS') and settings.AUTO_BLOCK_CRITICAL_THREATS:
        try:
            # Créer une règle de blocage temporaire
            container.rule_management_use_case.create_temporary_block_rule(
                source_ip=source_ip,
                reason=f"Blocage automatique suite à une menace {threat_type}",
                duration_minutes=60  # Blocage d'une heure par défaut
            )
            logger.info(f"Blocage automatique appliqué pour l'IP {source_ip} pendant 60 minutes")
        except Exception as e:
            logger.error(f"Erreur lors de l'application du blocage automatique: {e}") 