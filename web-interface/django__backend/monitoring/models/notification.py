"""
Modèles pour la gestion des notifications dans le système de surveillance.
"""

from django.db import models
from django.conf import settings


class Notification(models.Model):
    """
    Modèle pour les notifications système.
    """
    LEVELS = [
        ('info', 'Information'),
        ('warning', 'Avertissement'),
        ('critical', 'Critique'),
    ]
    
    # Champs principaux
    title = models.CharField(
        max_length=255,
        verbose_name='Titre'
    )
    message = models.TextField(
        verbose_name='Message'
    )
    level = models.CharField(
        max_length=20, 
        choices=LEVELS, 
        default='info',
        verbose_name='Niveau'
    )
    source = models.CharField(
        max_length=100,
        verbose_name='Source'
    )  # ex: 'monitoring', 'security', etc.
    
    # Statuts et relations
    is_read = models.BooleanField(
        default=False,
        verbose_name='Lu'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='notifications',
        verbose_name='Utilisateur'
    )
    
    # Liens optionnels
    alert = models.ForeignKey(
        'monitoring.Alert', 
        null=True, 
        blank=True, 
        on_delete=models.SET_NULL, 
        related_name='notifications',
        verbose_name='Alerte associée'
    )
    device = models.ForeignKey(
        'network_management.NetworkDevice', 
        null=True, 
        blank=True, 
        on_delete=models.SET_NULL, 
        related_name='notifications',
        verbose_name='Équipement associé'
    )
    
    # Actions
    action_url = models.URLField(
        blank=True, 
        null=True,
        verbose_name='URL d\'action'
    )
    action_text = models.CharField(
        max_length=100, 
        blank=True, 
        null=True,
        verbose_name='Texte d\'action'
    )
    
    # Métadonnées
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Date de création'
    )
    read_at = models.DateTimeField(
        null=True, 
        blank=True,
        verbose_name='Date de lecture'
    )
    metadata = models.JSONField(
        default=dict, 
        blank=True,
        verbose_name='Métadonnées'
    )
    
    def __str__(self):
        return f"{self.title} ({self.level})"
    
    class Meta:
        verbose_name = "Notification"
        verbose_name_plural = "Notifications"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['is_read']),
            models.Index(fields=['level']),
            models.Index(fields=['created_at']),
        ]
        
    def mark_as_read(self):
        """
        Marque la notification comme lue.
        
        Returns:
            self: La notification mise à jour
        """
        from django.utils import timezone
        self.is_read = True
        self.read_at = timezone.now()
        self.save(update_fields=['is_read', 'read_at'])
        return self


class NotificationChannel(models.Model):
    """
    Canaux de notification configurés pour les utilisateurs.
    """
    CHANNEL_TYPES = [
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('webhook', 'Webhook'),
        ('slack', 'Slack'),
        ('teams', 'Microsoft Teams'),
        ('telegram', 'Telegram'),
        ('pushover', 'Pushover'),
        ('custom', 'Personnalisé')
    ]
    
    NOTIFICATION_LEVELS = [
        ('info', 'Information'),
        ('warning', 'Avertissement'),
        ('critical', 'Critique'),
        ('all', 'Tous')
    ]
    
    name = models.CharField(
        max_length=255,
        verbose_name='Nom'
    )
    channel_type = models.CharField(
        max_length=50, 
        choices=CHANNEL_TYPES,
        verbose_name='Type de canal'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='notification_channels',
        verbose_name='Utilisateur'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='Actif'
    )
    config = models.JSONField(
        default=dict,
        verbose_name='Configuration'
    )
    min_level = models.CharField(
        max_length=20, 
        choices=NOTIFICATION_LEVELS, 
        default='warning',
        verbose_name='Niveau minimum'
    )
    schedule = models.JSONField(
        null=True, 
        blank=True,
        verbose_name='Planification'
    )  # Périodes pendant lesquelles les notifications sont autorisées
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Date de création'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Date de mise à jour'
    )
    
    def __str__(self):
        return f"{self.name} ({self.channel_type})"
    
    class Meta:
        verbose_name = "Canal de notification"
        verbose_name_plural = "Canaux de notification"
        ordering = ['name']
        unique_together = ('user', 'name')


class NotificationRule(models.Model):
    """
    Règles de notification pour automatiser l'envoi de notifications.
    """
    name = models.CharField(
        max_length=255,
        verbose_name='Nom'
    )
    description = models.TextField(
        blank=True,
        verbose_name='Description'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='notification_rules',
        verbose_name='Utilisateur'
    )
    channels = models.ManyToManyField(
        NotificationChannel, 
        related_name='rules',
        verbose_name='Canaux'
    )
    
    # Conditions de déclenchement
    alert_filter = models.JSONField(
        null=True, 
        blank=True,
        verbose_name='Filtre d\'alertes'
    )
    device_filter = models.JSONField(
        null=True, 
        blank=True,
        verbose_name='Filtre d\'équipements'
    )
    severity_threshold = models.CharField(
        max_length=20, 
        choices=Notification.LEVELS, 
        default='warning',
        verbose_name='Seuil de sévérité'
    )
    
    # Configuration
    is_active = models.BooleanField(
        default=True,
        verbose_name='Active'
    )
    quiet_period = models.IntegerField(
        default=0,  # En minutes
        verbose_name='Période de silence (minutes)'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Date de création'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Date de mise à jour'
    )
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Règle de notification"
        verbose_name_plural = "Règles de notification"
        ordering = ['name'] 