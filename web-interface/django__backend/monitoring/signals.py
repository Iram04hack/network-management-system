"""
Signaux pour l'application monitoring.

Ce module contient les signaux et les gestionnaires de signaux pour l'application monitoring.
Les signaux permettent de réagir à certains événements, comme la création d'une alerte,
la mise à jour d'une métrique, etc.
"""

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.utils import timezone
from django.conf import settings

from .models import (
    Alert, Notification, DeviceServiceCheck, 
    ServiceCheck, DeviceMetric, MetricValue,
    CheckResult
)

import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Alert)
def alert_created_or_updated(sender, instance, created, **kwargs):
    """
    Signal déclenché lorsqu'une alerte est créée ou mise à jour.
    
    Args:
        sender: Le modèle qui a envoyé le signal
        instance: L'instance du modèle qui a été sauvegardée
        created: True si l'instance a été créée, False si elle a été mise à jour
        **kwargs: Arguments supplémentaires
    """
    from .tasks.notification_tasks import send_notification
    
    if created:
        logger.info(f"Nouvelle alerte créée: {instance}")
        
        # Envoyer l'alerte via WebSocket
        try:
            from .di_container import resolve
            websocket_service = resolve('WebSocketService')
            websocket_service.broadcast_alert({
                'id': instance.id,
                'device': instance.device.name,
                'message': instance.message,
                'severity': instance.severity,
                'status': instance.status,
                'created_at': instance.created_at.isoformat()
            })
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi WebSocket de l'alerte: {e}")
        
        # Enregistrer une notification pour les utilisateurs concernés
        try:
            # Dans une version plus complète, nous devrions déterminer les utilisateurs
            # concernés en fonction de leurs préférences et des règles de notification
            from django.contrib.auth import get_user_model
            User = get_user_model()
            
            # Pour l'exemple, nous notifions tous les superutilisateurs
            for user in User.objects.filter(is_superuser=True):
                Notification.objects.create(
                    user=user,
                    title=f"Nouvelle alerte: {instance.severity.upper()}",
                    message=instance.message,
                    level=instance.severity if instance.severity in ('info', 'warning', 'critical') else 'info',
                    source='monitoring',
                    alert=instance,
                    device=instance.device
                )
        except Exception as e:
            logger.error(f"Erreur lors de la création des notifications pour l'alerte: {e}")
    else:
        # Alerte mise à jour
        if instance.tracker.has_changed('status'):
            logger.info(f"Statut de l'alerte {instance.id} modifié: {instance.tracker.previous('status')} -> {instance.status}")
            
            # Envoyer la mise à jour via WebSocket
            try:
                from .di_container import resolve
                websocket_service = resolve('WebSocketService')
                websocket_service.send_event('alert_updated', {
                    'id': instance.id,
                    'status': instance.status,
                    'acknowledged_by': instance.acknowledged_by.username if instance.acknowledged_by else None,
                    'resolved_by': instance.resolved_by.username if instance.resolved_by else None,
                    'updated_at': timezone.now().isoformat()
                })
            except Exception as e:
                logger.error(f"Erreur lors de l'envoi WebSocket de la mise à jour d'alerte: {e}")


@receiver(post_save, sender=DeviceServiceCheck)
def update_service_check_schedule(sender, instance, created, **kwargs):
    """
    Met à jour la planification des vérifications de service.
    
    Args:
        sender: Modèle qui a envoyé le signal
        instance: Instance de la vérification de service
        created: True si la vérification vient d'être créée, False sinon
    """
    if created or not instance.next_check_time:
        # Planifier la première vérification
        try:
            now = timezone.now()
            # Si le service check est lié à un template, utiliser l'intervalle du template
            if instance.service_check.template:
                interval = instance.service_check.template.check_interval
            else:
                # Valeur par défaut
                interval = 300  # 5 minutes
                
            instance.next_check_time = now + timezone.timedelta(seconds=interval)
            instance.save(update_fields=['next_check_time'])
            logger.debug(f"Planification initiale de la vérification {instance} à {instance.next_check_time}")
        except Exception as e:
            logger.error(f"Erreur lors de la planification de la vérification {instance}: {e}")


@receiver(post_save, sender=DeviceMetric)
def update_metric_collection_schedule(sender, instance, created, **kwargs):
    """
    Met à jour la planification de la collecte des métriques.
    
    Args:
        sender: Modèle qui a envoyé le signal
        instance: Instance de la métrique d'équipement
        created: True si la métrique vient d'être créée, False sinon
    """
    if created or not instance.next_collection:
        # Planifier la première collecte
        try:
            now = timezone.now()
            instance.next_collection = now + timezone.timedelta(seconds=instance.collection_interval)
            instance.save(update_fields=['next_collection'])
            logger.debug(f"Planification initiale de la collecte {instance} à {instance.next_collection}")
        except Exception as e:
            logger.error(f"Erreur lors de la planification de la collecte {instance}: {e}")


@receiver(post_save, sender=MetricValue)
def metric_value_created(sender, instance, created, **kwargs):
    """
    Signal déclenché lorsqu'une valeur de métrique est créée.
    
    Args:
        sender: Le modèle qui a envoyé le signal
        instance: L'instance du modèle qui a été sauvegardée
        created: True si l'instance a été créée, False si elle a été mise à jour
        **kwargs: Arguments supplémentaires
    """
    if created:
        # Mettre à jour la dernière valeur de la métrique d'équipement
        try:
            device_metric = instance.device_metric
            
            # Mettre à jour la date de dernière collecte
            device_metric.last_collection = instance.timestamp
            device_metric.save(update_fields=['last_collection'])
            
            # Vérifier les règles de seuil pour cette métrique
            from .domain.services.threshold_service import check_threshold_rules
            check_threshold_rules(device_metric, instance.value, instance.timestamp)
        except Exception as e:
            logger.error(f"Erreur lors du traitement de la nouvelle valeur de métrique {instance}: {e}")
        
        # Analyser la valeur pour détecter les anomalies
        from .tasks.metrics_tasks import analyze_metrics
        analyze_metrics.delay(instance.device_metric_id)


@receiver(post_save, sender=CheckResult)
def check_result_created(sender, instance, created, **kwargs):
    """
    Signal déclenché lorsqu'un résultat de vérification est créé.
    
    Args:
        sender: Le modèle qui a envoyé le signal
        instance: L'instance du modèle qui a été sauvegardée
        created: True si l'instance a été créée, False si elle a été mise à jour
        **kwargs: Arguments supplémentaires
    """
    if created:
        # Mettre à jour le statut de la vérification de service d'équipement
        pass
        
        # Créer une alerte si le statut est warning ou critical
        if instance.status in ["warning", "critical"]:
            # Créer une alerte
            pass


@receiver(post_delete, sender=Alert)
def cleanup_related_notifications(sender, instance, **kwargs):
    """
    Nettoie les notifications liées à une alerte supprimée.
    
    Args:
        sender: Modèle qui a envoyé le signal
        instance: Instance de l'alerte
    """
    try:
        Notification.objects.filter(alert_id=instance.id).delete()
        logger.debug(f"Notifications liées à l'alerte {instance.id} nettoyées")
    except Exception as e:
        logger.error(f"Erreur lors du nettoyage des notifications liées à l'alerte {instance.id}: {e}")


@receiver(post_save, sender=Notification)
def notification_created(sender, instance, created, **kwargs):
    """
    Signal déclenché lorsqu'une notification est créée.
    
    Args:
        sender: Le modèle qui a envoyé le signal
        instance: L'instance du modèle qui a été sauvegardée
        created: True si l'instance a été créée, False si elle a été mise à jour
        **kwargs: Arguments supplémentaires
    """
    if created and instance.status == "pending":
        # Envoyer la notification
        from .tasks.notification_tasks import send_notification
        send_notification.delay(instance.id)


# Importer d'autres signaux si nécessaire
# Si vous remarquez que les signaux deviennent trop nombreux,
# envisagez de les séparer en plusieurs fichiers dans un sous-package 'signals' 