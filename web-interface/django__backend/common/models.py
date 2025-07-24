"""
Modèles de base pour le Service Central GNS3.

Ce module définit les modèles Django pour persister certaines données
critiques du service central GNS3 dans la base de données.
"""

from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
import uuid


class GNS3ServerConfig(models.Model):
    """Configuration des serveurs GNS3."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, help_text="Nom du serveur GNS3")
    host = models.CharField(max_length=255, help_text="Adresse IP ou nom d'hôte")
    port = models.IntegerField(default=3080, help_text="Port du serveur GNS3")
    protocol = models.CharField(
        max_length=10, 
        choices=[('http', 'HTTP'), ('https', 'HTTPS')], 
        default='http'
    )
    username = models.CharField(max_length=100, blank=True, help_text="Nom d'utilisateur (optionnel)")
    password = models.CharField(max_length=255, blank=True, help_text="Mot de passe (optionnel)")
    verify_ssl = models.BooleanField(default=True, help_text="Vérifier le certificat SSL")
    timeout = models.IntegerField(default=30, help_text="Timeout des requêtes en secondes")
    
    is_active = models.BooleanField(default=True, help_text="Serveur actif")
    is_default = models.BooleanField(default=False, help_text="Serveur par défaut")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_connection_test = models.DateTimeField(null=True, blank=True)
    connection_status = models.CharField(
        max_length=20,
        choices=[
            ('connected', 'Connecté'),
            ('disconnected', 'Déconnecté'),
            ('error', 'Erreur'),
            ('unknown', 'Inconnu')
        ],
        default='unknown'
    )
    
    class Meta:
        verbose_name = "Configuration Serveur GNS3"
        verbose_name_plural = "Configurations Serveurs GNS3"
        ordering = ['-is_default', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.host}:{self.port})"
    
    def get_connection_url(self):
        """Retourne l'URL de connexion complète."""
        return f"{self.protocol}://{self.host}:{self.port}"
    
    def save(self, *args, **kwargs):
        # S'assurer qu'il n'y a qu'un seul serveur par défaut
        if self.is_default:
            GNS3ServerConfig.objects.filter(is_default=True).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)


class GNS3EventLog(models.Model):
    """Log des événements GNS3 pour audit et debugging."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event_id = models.CharField(max_length=100, unique=True, help_text="ID unique de l'événement")
    event_type = models.CharField(max_length=50, help_text="Type d'événement GNS3")
    source = models.CharField(max_length=100, default="gns3_central_service")
    
    project_id = models.CharField(max_length=100, blank=True, help_text="ID du projet GNS3 concerné")
    node_id = models.CharField(max_length=100, blank=True, help_text="ID du nœud GNS3 concerné")
    
    data = models.JSONField(help_text="Données de l'événement")
    priority = models.CharField(
        max_length=20,
        choices=[
            ('critical', 'Critique'),
            ('high', 'Élevée'),
            ('normal', 'Normale'),
            ('low', 'Faible')
        ],
        default='normal'
    )
    
    delivery_status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'En attente'),
            ('delivered', 'Livré'),
            ('failed', 'Échoué'),
            ('retry', 'Retry')
        ],
        default='pending'
    )
    
    retry_count = models.IntegerField(default=0)
    target_modules = models.JSONField(default=list, blank=True, help_text="Modules cibles")
    correlation_id = models.CharField(max_length=100, blank=True, help_text="ID de corrélation")
    
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = "Log Événement GNS3"
        verbose_name_plural = "Logs Événements GNS3"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['event_type', 'created_at']),
            models.Index(fields=['project_id', 'created_at']),
            models.Index(fields=['node_id', 'created_at']),
            models.Index(fields=['correlation_id']),
        ]
    
    def __str__(self):
        return f"{self.event_type} - {self.created_at.strftime('%Y-%m-%d %H:%M:%S')}"


class GNS3ModuleSubscription(models.Model):
    """Abonnements des modules aux événements GNS3."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    module_name = models.CharField(max_length=50, help_text="Nom du module")
    subscription_types = models.JSONField(help_text="Types d'événements auxquels le module est abonné")
    
    is_active = models.BooleanField(default=True)
    callback_url = models.URLField(blank=True, help_text="URL de callback pour webhook (optionnel)")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_event_received = models.DateTimeField(null=True, blank=True)
    
    events_received_count = models.BigIntegerField(default=0)
    events_processed_count = models.BigIntegerField(default=0)
    events_failed_count = models.BigIntegerField(default=0)
    
    class Meta:
        verbose_name = "Abonnement Module GNS3"
        verbose_name_plural = "Abonnements Modules GNS3"
        unique_together = ['module_name']
        ordering = ['module_name']
    
    def __str__(self):
        return f"{self.module_name} - {len(self.subscription_types)} abonnements"
    
    def update_stats(self, event_processed=True, event_failed=False):
        """Met à jour les statistiques d'événements."""
        self.events_received_count += 1
        if event_processed:
            self.events_processed_count += 1
        if event_failed:
            self.events_failed_count += 1
        self.last_event_received = timezone.now()
        self.save(update_fields=['events_received_count', 'events_processed_count', 
                                'events_failed_count', 'last_event_received'])


class GNS3ServiceMetrics(models.Model):
    """Métriques et statistiques du service central GNS3."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    # Métriques de base
    service_status = models.CharField(max_length=20, default='unknown')
    gns3_server_connected = models.BooleanField(default=False)
    redis_cache_available = models.BooleanField(default=False)
    websocket_connections_active = models.IntegerField(default=0)
    
    # Compteurs d'événements
    events_processed_total = models.BigIntegerField(default=0)
    events_processed_last_hour = models.IntegerField(default=0)
    events_failed_total = models.BigIntegerField(default=0)
    events_retried_total = models.BigIntegerField(default=0)
    
    # Métriques API
    api_calls_total = models.BigIntegerField(default=0)
    api_calls_last_hour = models.IntegerField(default=0)
    api_errors_total = models.BigIntegerField(default=0)
    average_response_time_ms = models.FloatField(default=0.0)
    
    # Métriques cache
    cache_hits_total = models.BigIntegerField(default=0)
    cache_misses_total = models.BigIntegerField(default=0)
    cache_hit_ratio = models.FloatField(default=0.0)
    
    # Métriques réseau
    nodes_total = models.IntegerField(default=0)
    nodes_running = models.IntegerField(default=0)
    projects_total = models.IntegerField(default=0)
    projects_active = models.IntegerField(default=0)
    
    # Informations système
    uptime_seconds = models.BigIntegerField(default=0)
    memory_usage_mb = models.FloatField(default=0.0)
    cpu_usage_percent = models.FloatField(default=0.0)
    
    class Meta:
        verbose_name = "Métrique Service GNS3"
        verbose_name_plural = "Métriques Service GNS3"
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['timestamp']),
            models.Index(fields=['service_status', 'timestamp']),
        ]
    
    def __str__(self):
        return f"Métriques {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"
    
    @classmethod
    def create_snapshot(cls, service_status_data):
        """Crée un snapshot des métriques actuelles."""
        from .infrastructure.gns3_central_service import gns3_central_service
        
        try:
            # Obtenir les données du service
            stats = service_status_data.get('statistics', {})
            cache_info = service_status_data.get('cache', {})
            gns3_server = service_status_data.get('gns3_server', {})
            
            # Calculer le ratio de cache hit
            cache_hits = stats.get('cache_hits', 0)
            cache_misses = stats.get('cache_misses', 0)
            total_cache_requests = cache_hits + cache_misses
            cache_hit_ratio = (cache_hits / total_cache_requests * 100) if total_cache_requests > 0 else 0
            
            # Obtenir les métriques réseau depuis le cache
            topology = gns3_central_service.get_cached_topology()
            nodes_total = len(topology.get('nodes', {})) if topology else 0
            projects_total = len(topology.get('projects', {})) if topology else 0
            
            # Compter les nœuds en cours d'exécution
            nodes_running = 0
            if topology:
                for node in topology.get('nodes', {}).values():
                    if node.get('status') == 'started':
                        nodes_running += 1
            
            # Créer le snapshot
            return cls.objects.create(
                service_status=service_status_data.get('status', 'unknown'),
                gns3_server_connected=gns3_server.get('connected', False),
                redis_cache_available=cache_info.get('network_state_cached', False),
                
                events_processed_total=stats.get('events_processed', 0),
                api_calls_total=stats.get('api_calls', 0),
                cache_hits_total=stats.get('cache_hits', 0),
                cache_misses_total=stats.get('cache_misses', 0),
                cache_hit_ratio=cache_hit_ratio,
                
                nodes_total=nodes_total,
                nodes_running=nodes_running,
                projects_total=projects_total,
                
                uptime_seconds=stats.get('uptime_seconds', 0),
            )
            
        except Exception as e:
            logger.error(f"Erreur lors de la création du snapshot de métriques: {e}")
            return None


class GNS3WebSocketConnection(models.Model):
    """Connexions WebSocket actives pour monitoring."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    connection_id = models.CharField(max_length=100, unique=True)
    channel_name = models.CharField(max_length=255)
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    client_ip = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    subscriptions = models.JSONField(default=list, help_text="Types d'événements auxquels la connexion est abonnée")
    
    connected_at = models.DateTimeField(auto_now_add=True)
    last_heartbeat = models.DateTimeField(auto_now=True)
    disconnected_at = models.DateTimeField(null=True, blank=True)
    
    events_sent = models.BigIntegerField(default=0)
    messages_received = models.BigIntegerField(default=0)
    
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = "Connexion WebSocket GNS3"
        verbose_name_plural = "Connexions WebSocket GNS3"
        ordering = ['-connected_at']
        indexes = [
            models.Index(fields=['connection_id']),
            models.Index(fields=['is_active', 'connected_at']),
        ]
    
    def __str__(self):
        return f"WebSocket {self.connection_id} - {self.connected_at.strftime('%Y-%m-%d %H:%M:%S')}"
    
    def update_heartbeat(self):
        """Met à jour le heartbeat de la connexion."""
        self.last_heartbeat = timezone.now()
        self.save(update_fields=['last_heartbeat'])
    
    def disconnect(self):
        """Marque la connexion comme déconnectée."""
        self.is_active = False
        self.disconnected_at = timezone.now()
        self.save(update_fields=['is_active', 'disconnected_at'])
    
    def increment_events_sent(self):
        """Incrémente le compteur d'événements envoyés."""
        self.events_sent += 1
        self.save(update_fields=['events_sent'])
    
    def increment_messages_received(self):
        """Incrémente le compteur de messages reçus."""
        self.messages_received += 1
        self.save(update_fields=['messages_received'])


# Signaux pour maintenir la cohérence
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=GNS3ServerConfig)
def update_gns3_service_config(sender, instance, created, **kwargs):
    """Met à jour la configuration du service GNS3 lors de la modification d'un serveur."""
    if instance.is_default:
        # Mettre à jour la configuration du service central
        from .infrastructure.gns3_central_service import gns3_central_service
        
        try:
            # Reconfigurer le client GNS3 avec les nouveaux paramètres
            gns3_central_service.gns3_config.update({
                'host': instance.host,
                'port': instance.port,
                'protocol': instance.protocol,
                'username': instance.username,
                'password': instance.password,
                'verify_ssl': instance.verify_ssl,
                'timeout': instance.timeout
            })
            
            logger.info(f"Configuration du service GNS3 mise à jour avec le serveur {instance.name}")
            
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour de configuration GNS3: {e}")


@receiver(pre_delete, sender=GNS3WebSocketConnection)
def cleanup_websocket_connection(sender, instance, **kwargs):
    """Nettoie les ressources lors de la suppression d'une connexion WebSocket."""
    try:
        # Nettoyer le cache Redis si nécessaire
        from django.core.cache import cache
        cache.delete(f"gns3_websocket_connection:{instance.connection_id}")
        
        logger.debug(f"Nettoyage de la connexion WebSocket {instance.connection_id}")
        
    except Exception as e:
        logger.error(f"Erreur lors du nettoyage de connexion WebSocket: {e}")