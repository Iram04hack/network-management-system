"""
Modèles pour les vérifications de service dans le système de surveillance.
"""

from django.db import models
from django.utils import timezone


class MonitoringTemplate(models.Model):
    """
    Modèle pour les templates de surveillance.
    """
    name = models.CharField(
        max_length=255,
        verbose_name='Nom'
    )
    description = models.TextField(
        blank=True,
        verbose_name='Description'
    )
    check_interval = models.IntegerField(
        default=300,  # En secondes
        verbose_name='Intervalle de vérification (secondes)'
    ) 
    retry_interval = models.IntegerField(
        default=60,  # En secondes
        verbose_name='Intervalle de réessai (secondes)'
    ) 
    max_check_attempts = models.IntegerField(
        default=3,
        verbose_name='Nombre maximum de tentatives'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='Actif'
    )
    notification_enabled = models.BooleanField(
        default=True,
        verbose_name='Notifications activées'
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
        verbose_name = "Template de surveillance"
        verbose_name_plural = "Templates de surveillance"
        ordering = ['name']


class ServiceCheck(models.Model):
    """
    Modèle pour les vérifications de services.
    """
    CHECK_TYPES = [
        ('ping', 'ICMP Ping'),
        ('tcp', 'TCP Port'),
        ('http', 'HTTP/HTTPS'),
        ('snmp', 'SNMP'),
        ('ssh', 'SSH'),
        ('dns', 'DNS'),
        ('ssl', 'Certificat SSL'),
        ('process', 'Processus'),
        ('disk', 'Espace disque'),
        ('memory', 'Mémoire'),
        ('cpu', 'CPU'),
        ('custom', 'Script personnalisé')
    ]
    
    name = models.CharField(
        max_length=255,
        verbose_name='Nom'
    )
    description = models.TextField(
        blank=True,
        verbose_name='Description'
    )
    check_type = models.CharField(
        max_length=20, 
        choices=CHECK_TYPES,
        verbose_name='Type de vérification'
    )
    check_command = models.CharField(
        max_length=255,
        verbose_name='Commande de vérification'
    )
    check_parameters = models.JSONField(
        null=True, 
        blank=True,
        verbose_name='Paramètres de la commande'
    )
    warning_threshold = models.CharField(
        max_length=255, 
        blank=True,
        verbose_name='Seuil d\'avertissement'
    )
    critical_threshold = models.CharField(
        max_length=255, 
        blank=True,
        verbose_name='Seuil critique'
    )
    template = models.ForeignKey(
        MonitoringTemplate, 
        null=True, 
        blank=True, 
        on_delete=models.SET_NULL, 
        related_name='service_checks',
        verbose_name='Template'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='Actif'
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
        return f"{self.name} ({self.check_type})"
    
    class Meta:
        verbose_name = "Vérification de service"
        verbose_name_plural = "Vérifications de service"
        ordering = ['name']


class DeviceServiceCheck(models.Model):
    """
    Relation entre équipements et vérifications de services.
    """
    device = models.ForeignKey(
        'network_management.NetworkDevice', 
        on_delete=models.CASCADE,
        verbose_name='Équipement'
    )
    service_check = models.ForeignKey(
        ServiceCheck, 
        on_delete=models.CASCADE,
        verbose_name='Vérification de service'
    )
    override_parameters = models.JSONField(
        null=True, 
        blank=True,
        verbose_name='Paramètres personnalisés'
    )  # Override des paramètres par défaut
    is_active = models.BooleanField(
        default=True,
        verbose_name='Actif'
    )
    last_check_time = models.DateTimeField(
        null=True, 
        blank=True,
        verbose_name='Dernière vérification'
    )
    next_check_time = models.DateTimeField(
        null=True, 
        blank=True,
        verbose_name='Prochaine vérification'
    )
    last_status = models.CharField(
        max_length=50, 
        default='unknown',
        verbose_name='Dernier statut'
    )
    last_check_output = models.TextField(
        blank=True, 
        null=True,
        verbose_name='Dernier résultat'
    )
    current_check_attempt = models.IntegerField(
        default=0,
        verbose_name='Tentative actuelle'
    )
    notification_enabled = models.BooleanField(
        default=True,
        verbose_name='Notifications activées'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Date de création'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Date de mise à jour'
    )
    
    class Meta:
        verbose_name = "Vérification de service d'équipement"
        verbose_name_plural = "Vérifications de service d'équipement"
        unique_together = ('device', 'service_check')

    def __str__(self):
        return f"{self.device.name} - {self.service_check.name}"
        
    def schedule_next_check(self, retry=False):
        """
        Planifie la prochaine vérification.
        
        Args:
            retry: Si True, utilise l'intervalle de réessai plutôt que l'intervalle de vérification
        """
        now = timezone.now()
        self.last_check_time = now
        
        interval = self.service_check.template.retry_interval if retry else self.service_check.template.check_interval
        
        if not interval:
            interval = 60  # Valeur par défaut en cas de problème
            
        self.next_check_time = now + timezone.timedelta(seconds=interval)
        self.save(update_fields=['last_check_time', 'next_check_time'])
    
    def reset_check_attempt(self):
        """
        Réinitialise le compteur de tentatives.
        """
        self.current_check_attempt = 0
        self.save(update_fields=['current_check_attempt'])
    
    def increment_check_attempt(self):
        """
        Incrémente le compteur de tentatives.
        """
        self.current_check_attempt += 1
        self.save(update_fields=['current_check_attempt'])
    
    def update_status(self, status, output):
        """
        Met à jour le statut de la vérification.
        
        Args:
            status: Nouveau statut
            output: Résultat de la vérification
        """
        self.last_status = status
        self.last_check_output = output
        self.save(update_fields=['last_status', 'last_check_output'])


class CheckResult(models.Model):
    """
    Résultats des vérifications de service.
    """
    STATUS_CHOICES = [
        ('ok', 'OK'),
        ('warning', 'Avertissement'),
        ('critical', 'Critique'),
        ('unknown', 'Inconnu')
    ]
    
    device_service_check = models.ForeignKey(
        DeviceServiceCheck, 
        on_delete=models.CASCADE, 
        related_name='results',
        verbose_name='Vérification de service'
    )
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES,
        verbose_name='Statut'
    )
    output = models.TextField(
        verbose_name='Résultat'
    )
    performance_data = models.JSONField(
        null=True, 
        blank=True,
        verbose_name='Données de performance'
    )
    execution_time = models.FloatField(
        default=0.0,
        verbose_name='Temps d\'exécution (secondes)'
    )
    timestamp = models.DateTimeField(
        default=timezone.now,
        verbose_name='Horodatage'
    )
    
    class Meta:
        verbose_name = "Résultat de vérification"
        verbose_name_plural = "Résultats de vérification"
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['device_service_check', '-timestamp']),
            models.Index(fields=['status']),
            models.Index(fields=['timestamp']),
        ]

    def __str__(self):
        return f"{self.device_service_check} - {self.status} ({self.timestamp.strftime('%Y-%m-%d %H:%M:%S')})" 