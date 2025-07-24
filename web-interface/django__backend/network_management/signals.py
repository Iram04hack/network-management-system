"""
Signaux pour le module network_management.

Ce module contient les signaux Django utilisés pour déclencher
des actions automatiques lors de certains événements.
"""

import logging
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .infrastructure.models import NetworkDevice, NetworkInterface, NetworkConnection

logger = logging.getLogger(__name__)


@receiver(post_save, sender=NetworkDevice)
def device_saved(sender, instance, created, **kwargs):
    """Signal déclenché lors de la sauvegarde d'un équipement réseau."""
    if created:
        logger.info(f"✅ Nouvel équipement réseau créé: {instance.name} ({instance.device_type})")
        # Actions à effectuer lors de la création d'un nouvel équipement
        # Par exemple : démarrer une découverte automatique, configurer des alertes, etc.
    else:
        logger.info(f"🔄 Équipement réseau mis à jour: {instance.name}")
        # Actions à effectuer lors de la mise à jour d'un équipement existant


@receiver(post_delete, sender=NetworkDevice)
def device_deleted(sender, instance, **kwargs):
    """Signal déclenché lors de la suppression d'un équipement réseau."""
    logger.warning(f"🗑️ Équipement réseau supprimé: {instance.name}")
    # Actions de nettoyage : supprimer les interfaces, connexions, alertes associées


@receiver(post_save, sender=NetworkInterface)
def interface_saved(sender, instance, created, **kwargs):
    """Signal déclenché lors de la sauvegarde d'une interface réseau."""
    if created:
        logger.info(f"✅ Nouvelle interface créée: {instance.name} sur {instance.device.name}")
    else:
        logger.info(f"🔄 Interface mise à jour: {instance.name}")


@receiver(post_save, sender=NetworkConnection)
def connection_saved(sender, instance, created, **kwargs):
    """Signal déclenché lors de la sauvegarde d'une connexion réseau."""
    if created:
        logger.info(f"🔗 Nouvelle connexion créée: {instance.source_interface} <-> {instance.target_interface}")
        # Actions possibles : mise à jour de la topologie, recalcul des chemins, etc. 