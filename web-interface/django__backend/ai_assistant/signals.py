import logging
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from .models import Message, Conversation, ConversationMetrics, APIUsage

logger = logging.getLogger(__name__)

@receiver(post_save, sender=Message)
def update_conversation_metrics(sender, instance, created, **kwargs):
    """Met à jour les métriques de conversation quand un message est créé"""
    if created:
        try:
            conversation = instance.conversation
            metrics, created_metrics = ConversationMetrics.objects.get_or_create(
                conversation=conversation,
                defaults={
                    'total_messages': 0,
                    'total_tokens': 0,
                    'average_response_time': 0.0,
                    'successful_commands': 0,
                    'failed_commands': 0
                }
            )
            
            # Incrémenter le nombre de messages
            metrics.total_messages += 1
            
            # Ajouter les tokens si disponibles
            if instance.token_count:
                metrics.total_tokens += instance.token_count
            
            # Mettre à jour le temps de réponse moyen
            if instance.processing_time:
                current_avg = metrics.average_response_time
                new_avg = ((current_avg * (metrics.total_messages - 1)) + instance.processing_time) / metrics.total_messages
                metrics.average_response_time = new_avg
            
            # Compter les commandes réussies/échouées
            actions = instance.actions_taken
            if actions:
                for action in actions:
                    if isinstance(action, dict):
                        if action.get('type') == 'command':
                            if action.get('success', False):
                                metrics.successful_commands += 1
                            else:
                                metrics.failed_commands += 1
            
            metrics.save()
            
            # Mettre à jour le timestamp de la conversation
            conversation.save()  # Trigger auto update_at
            
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour des métriques: {e}")

@receiver(post_save, sender=Message)
def notify_websocket_new_message(sender, instance, created, **kwargs):
    """Envoie une notification WebSocket pour les nouveaux messages"""
    if created and instance.role == 'assistant':
        try:
            channel_layer = get_channel_layer()
            
            # Notifier l'utilisateur de la conversation
            user_id = instance.conversation.user.id
            
            async_to_sync(channel_layer.group_send)(
                f"chat_{user_id}",
                {
                    "type": "system_notification",
                    "message": "Nouveau message reçu",
                    "level": "info",
                    "data": {
                        "message_id": instance.id,
                        "conversation_id": instance.conversation.id,
                        "content": instance.content[:100] + "..." if len(instance.content) > 100 else instance.content
                    }
                }
            )
        except Exception as e:
            logger.error(f"Erreur lors de la notification WebSocket: {e}")

@receiver(post_save, sender=APIUsage)
def monitor_api_usage_limits(sender, instance, created, **kwargs):
    """Surveille les limites d'utilisation de l'API"""
    if created:
        try:
            # Vérifier les limites quotidiennes (exemple)
            daily_limit = 1000  # tokens par jour
            monthly_limit = 30000  # tokens par mois
            
            # Utilisation du jour
            daily_usage = APIUsage.objects.filter(
                user=instance.user,
                model=instance.model,
                date=instance.date
            ).aggregate(total_tokens=sum('token_count'))['total_tokens'] or 0
            
            # Notifications de limite
            channel_layer = get_channel_layer()
            
            if daily_usage >= daily_limit * 0.9:  # 90% de la limite
                async_to_sync(channel_layer.group_send)(
                    f"chat_{instance.user.id}",
                    {
                        "type": "system_notification",
                        "message": f"⚠️ Vous approchez de votre limite quotidienne d'utilisation de l'API ({daily_usage}/{daily_limit} tokens)",
                        "level": "warning"
                    }
                )
            
            if daily_usage >= daily_limit:
                async_to_sync(channel_layer.group_send)(
                    f"chat_{instance.user.id}",
                    {
                        "type": "system_notification",
                        "message": "🚫 Limite quotidienne d'utilisation de l'API atteinte",
                        "level": "error"
                    }
                )
                
        except Exception as e:
            logger.error(f"Erreur lors de la surveillance des limites API: {e}")

@receiver(post_save, sender=Conversation)
def auto_generate_conversation_title(sender, instance, created, **kwargs):
    """Génère automatiquement un titre pour la conversation"""
    if created:
        try:
            # Attendre que des messages soient ajoutés
            if not instance.title or instance.title == "Nouvelle conversation":
                first_message = instance.messages.filter(role='user').first()
                if first_message:
                    # Créer un titre basé sur le premier message
                    content = first_message.content
                    if len(content) > 50:
                        title = content[:47] + "..."
                    else:
                        title = content
                    
                    instance.title = title
                    instance.save()
                    
        except Exception as e:
            logger.error(f"Erreur lors de la génération du titre: {e}")

# Signaux pour intégration avec d'autres modules
try:
    # Import conditionnel pour éviter les erreurs si les modules ne sont pas installés
    # from security_management.models import SecurityAlert  # Temporairement désactivé
    pass
except ImportError:
    logger.info("Module security_management non disponible - signaux sécurité désactivés")

try:
    from monitoring.models import Alert
    
    @receiver(post_save, sender=Alert)
    def notify_chatbot_monitoring_alert(sender, instance, created, **kwargs):
        """Notifie le chatbot des nouvelles alertes de monitoring"""
        if created and instance.severity in ['warning', 'critical']:
            try:
                channel_layer = get_channel_layer()
                
                device_name = instance.device.name if hasattr(instance, 'device') and instance.device else "Système"
                
                async_to_sync(channel_layer.group_send)(
                    "network_monitoring",
                    {
                        "type": "alert_notification",
                        "message": f"📊 Alerte monitoring sur {device_name}: {instance.message}",
                        "severity": instance.severity
                    }
                )
            except Exception as e:
                logger.error(f"Erreur lors de la notification chatbot: {e}")
                
except ImportError:
    logger.info("Module monitoring non disponible - signaux monitoring désactivés")

@receiver(post_delete, sender=Conversation)
def cleanup_conversation_metrics(sender, instance, **kwargs):
    """Nettoie les métriques quand une conversation est supprimée"""
    try:
        # Les métriques sont automatiquement supprimées via CASCADE
        logger.info(f"Conversation {instance.id} et ses métriques supprimées")
    except Exception as e:
        logger.error(f"Erreur lors du nettoyage des métriques: {e}")