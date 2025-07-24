"""
Modèles pour la gestion des alertes dans le système de surveillance.
"""

from django.db import models
from django.utils import timezone
from django.conf import settings


class Alert(models.Model):
    """
    Modèle pour les alertes de monitoring.
    """
    SEVERITY_CHOICES = [
        ('critical', 'Critique'),
        ('high', 'Haute'),
        ('medium', 'Moyenne'),
        ('low', 'Basse'),
        ('info', 'Information')
    ]
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('acknowledged', 'Prise en compte'),
        ('resolved', 'Résolue'),
        ('closed', 'Fermée'),
        ('false_positive', 'Faux positif')
    ]
    
    # Relations
    device = models.ForeignKey(
        'network_management.NetworkDevice',
        on_delete=models.CASCADE,
        related_name='monitoring_alerts',
        verbose_name='Équipement'
    )
    service_check = models.ForeignKey(
        'monitoring.ServiceCheck', 
        null=True, 
        blank=True, 
        on_delete=models.SET_NULL, 
        related_name='alerts',
        verbose_name='Vérification de service'
    )
    metric = models.ForeignKey(
        'monitoring.MetricsDefinition', 
        null=True, 
        blank=True, 
        on_delete=models.SET_NULL, 
        related_name='alerts',
        verbose_name='Métrique'
    )
    
    # Champs principaux
    severity = models.CharField(
        max_length=20, 
        choices=SEVERITY_CHOICES,
        verbose_name='Sévérité'
    )
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='active',
        verbose_name='Statut'
    )
    message = models.TextField(verbose_name='Message')
    value = models.CharField(
        max_length=255, 
        blank=True,
        verbose_name='Valeur'
    )
    
    # Champs temporels
    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name='Date de création'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Date de mise à jour'
    )
    resolved_at = models.DateTimeField(
        null=True, 
        blank=True,
        verbose_name='Date de résolution'
    )
    acknowledged_at = models.DateTimeField(
        null=True, 
        blank=True,
        verbose_name='Date de prise en compte'
    )
    
    # Champs utilisateurs
    acknowledged_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        null=True, 
        blank=True, 
        on_delete=models.SET_NULL, 
        related_name='acknowledged_alerts',
        verbose_name='Pris en compte par'
    )
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        null=True, 
        blank=True, 
        on_delete=models.SET_NULL, 
        related_name='resolved_alerts',
        verbose_name='Résolu par'
    )
    
    # Commentaires et informations supplémentaires
    acknowledgement_comment = models.TextField(
        blank=True, 
        null=True,
        verbose_name='Commentaire de prise en compte'
    )
    resolution_comment = models.TextField(
        blank=True, 
        null=True,
        verbose_name='Commentaire de résolution'
    )
    metadata = models.JSONField(
        default=dict, 
        blank=True,
        verbose_name='Métadonnées'
    )

    def __str__(self):
        return f"{self.device.name} - {self.message[:50]}"
    
    class Meta:
        verbose_name = "Alerte"
        verbose_name_plural = "Alertes"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['device']),
            models.Index(fields=['severity']),
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
            models.Index(fields=['device', 'status']),
            models.Index(fields=['status', 'severity']),
        ]
        
    def acknowledge(self, user=None, comment=None):
        """
        Acknowledger l'alerte.
        
        Args:
            user: Utilisateur qui prend en compte l'alerte
            comment: Commentaire optionnel
        
        Returns:
            self: L'alerte mise à jour
        """
        self.status = 'acknowledged'
        self.acknowledged_at = timezone.now()
        if user:
            self.acknowledged_by = user
        if comment:
            self.acknowledgement_comment = comment
        self.save()
        return self
    
    def resolve(self, user=None, comment=None):
        """
        Résoudre l'alerte.
        
        Args:
            user: Utilisateur qui résout l'alerte
            comment: Commentaire optionnel
            
        Returns:
            self: L'alerte mise à jour
        """
        self.status = 'resolved'
        self.resolved_at = timezone.now()
        if user:
            self.resolved_by = user
        if comment:
            self.resolution_comment = comment
        self.save()
        return self
        
    def close(self, user=None, comment=None):
        """
        Fermer l'alerte (état final).
        
        Args:
            user: Utilisateur qui ferme l'alerte
            comment: Commentaire optionnel
            
        Returns:
            self: L'alerte mise à jour
        """
        self.status = 'closed'
        self.resolved_at = timezone.now()
        if user:
            self.resolved_by = user
        if comment:
            self.resolution_comment = comment
        self.save()
        return self
        
    def mark_as_false_positive(self, user=None, comment=None):
        """
        Marquer l'alerte comme faux positif.
        
        Args:
            user: Utilisateur qui marque l'alerte
            comment: Commentaire optionnel
            
        Returns:
            self: L'alerte mise à jour
        """
        self.status = 'false_positive'
        self.resolved_at = timezone.now()
        if user:
            self.resolved_by = user
        if comment:
            self.resolution_comment = comment
        self.save()
        return self 


class AlertComment(models.Model):
    """
    Modèle pour les commentaires des alertes.
    """
    alert = models.ForeignKey(
        Alert,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Alerte'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='alert_comments',
        verbose_name='Utilisateur'
    )
    comment = models.TextField(verbose_name='Commentaire')
    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name='Date de création'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Date de mise à jour'
    )
    is_internal = models.BooleanField(
        default=False,
        verbose_name='Commentaire interne'
    )

    def __str__(self):
        return f"Commentaire de {self.user.username} sur {self.alert}"

    class Meta:
        verbose_name = "Commentaire d'alerte"
        verbose_name_plural = "Commentaires d'alerte"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['alert']),
            models.Index(fields=['user']),
            models.Index(fields=['created_at']),
        ]


class AlertHistory(models.Model):
    """
    Modèle pour l'historique des changements d'alertes.
    """
    ACTION_CHOICES = [
        ('created', 'Créée'),
        ('acknowledged', 'Prise en compte'),
        ('resolved', 'Résolue'),
        ('closed', 'Fermée'),
        ('reopened', 'Rouverte'),
        ('status_changed', 'Statut modifié'),
        ('severity_changed', 'Sévérité modifiée'),
        ('comment_added', 'Commentaire ajouté'),
        ('false_positive', 'Marquée faux positif'),
    ]

    alert = models.ForeignKey(
        Alert,
        on_delete=models.CASCADE,
        related_name='history',
        verbose_name='Alerte'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='alert_history',
        verbose_name='Utilisateur'
    )
    action = models.CharField(
        max_length=50,
        choices=ACTION_CHOICES,
        verbose_name='Action'
    )
    description = models.TextField(
        blank=True,
        verbose_name='Description'
    )
    old_value = models.JSONField(
        null=True,
        blank=True,
        verbose_name='Ancienne valeur'
    )
    new_value = models.JSONField(
        null=True,
        blank=True,
        verbose_name='Nouvelle valeur'
    )
    timestamp = models.DateTimeField(
        default=timezone.now,
        verbose_name='Horodatage'
    )
    metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='Métadonnées'
    )

    def __str__(self):
        return f"{self.action} sur {self.alert} par {self.user or 'Système'}"

    class Meta:
        verbose_name = "Historique d'alerte"
        verbose_name_plural = "Historiques d'alerte"
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['alert']),
            models.Index(fields=['user']),
            models.Index(fields=['action']),
            models.Index(fields=['timestamp']),
        ] 