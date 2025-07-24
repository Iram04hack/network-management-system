"""
Signaux pour le module QoS Management.
Ce module définit les signaux Django pour le module QoS Management.
"""
import logging
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from .models import InterfaceQoSPolicy
from .services.integration_service import IntegrationService
from .di_container import qos_container

logger = logging.getLogger(__name__)

@receiver(post_save, sender=InterfaceQoSPolicy)
def interface_qos_policy_post_save(sender, instance, created, **kwargs):
    """
    Gestionnaire de signal pour les politiques QoS appliquées aux interfaces
    
    Lorsqu'une politique QoS est créée ou activée, elle est appliquée à l'interface.
    Lorsqu'elle est désactivée, elle est supprimée de l'interface.
    """
    try:
        if created or instance.is_active:
            # Appliquer la politique QoS
            logger.info(f"Application de la politique QoS {instance.policy.name} à l'interface {instance.interface}")
            IntegrationService.apply_qos_policy(instance)
        else:
            # Politique désactivée, la supprimer
            logger.info(f"Suppression de la politique QoS de l'interface {instance.interface} (désactivation)")
            IntegrationService.remove_qos_policy(instance)
    except Exception as e:
        logger.error(f"Erreur lors du traitement du signal post_save pour InterfaceQoSPolicy: {e}")
        # Notification d'erreur pour suivi
        try:
            notification_service = qos_container.get('notification_service')
            if notification_service:
                notification_service.send_error_notification(
                    "QoS Policy Application Error",
                    f"Failed to apply QoS policy {instance.policy.name} to interface {instance.interface}: {str(e)}"
                )
        except Exception as notification_error:
            logger.error(f"Erreur lors de l'envoi de notification: {notification_error}")

@receiver(post_delete, sender=InterfaceQoSPolicy)
def interface_qos_policy_post_delete(sender, instance, **kwargs):
    """
    Gestionnaire de signal après suppression pour les politiques QoS
    
    Lorsqu'une politique QoS est supprimée, elle est également supprimée de l'interface.
    """
    try:
        # Supprimer la politique QoS après la suppression de l'objet
        logger.info(f"Suppression de la politique QoS de l'interface {instance.interface} (suppression)")
        IntegrationService.remove_qos_policy(instance)
    except Exception as e:
        logger.error(f"Erreur lors du traitement du signal post_delete pour InterfaceQoSPolicy: {e}")
        # Notification d'erreur pour suivi
        try:
            notification_service = qos_container.get('notification_service')
            if notification_service:
                notification_service.send_error_notification(
                    "QoS Policy Removal Error",
                    f"Failed to remove QoS policy {instance.policy.name} from interface {instance.interface}: {str(e)}"
                )
        except Exception as notification_error:
            logger.error(f"Erreur lors de l'envoi de notification: {notification_error}")

logger.info("Module signals QoS chargé avec succès")