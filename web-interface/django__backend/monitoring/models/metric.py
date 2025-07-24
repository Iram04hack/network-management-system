"""
Modèles pour la gestion des métriques dans le système de surveillance.
"""

from django.db import models
from django.utils import timezone


class MetricsDefinition(models.Model):
    """
    Définition des métriques à collecter.
    """
    METRIC_TYPES = [
        ('counter', 'Compteur'),
        ('gauge', 'Gauge'),
        ('histogram', 'Histogramme'),
        ('summary', 'Résumé'),
        ('text', 'Texte'),
        ('boolean', 'Booléen')
    ]
    
    name = models.CharField(
        max_length=255,
        verbose_name='Nom'
    )
    description = models.TextField(
        blank=True,
        verbose_name='Description'
    )
    metric_type = models.CharField(
        max_length=20, 
        choices=METRIC_TYPES,
        verbose_name='Type de métrique'
    )
    collection_method = models.CharField(
        max_length=100,
        verbose_name='Méthode de collecte'
    )  # snmp, api, script, etc.
    collection_parameters = models.JSONField(
        null=True, 
        blank=True,
        verbose_name='Paramètres de collecte'
    )
    unit = models.CharField(
        max_length=50, 
        blank=True,
        verbose_name='Unité'
    )  # %, Mbps, etc.
    is_active = models.BooleanField(
        default=True,
        verbose_name='Active'
    )
    retention_days = models.IntegerField(
        default=30,
        verbose_name='Jours de rétention'
    )
    warning_threshold = models.CharField(
        max_length=50, 
        null=True, 
        blank=True,
        verbose_name='Seuil d\'avertissement'
    )
    critical_threshold = models.CharField(
        max_length=50, 
        null=True, 
        blank=True,
        verbose_name='Seuil critique'
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
        verbose_name = "Définition de métrique"
        verbose_name_plural = "Définitions de métriques"
        ordering = ['name']


class MetricThreshold(models.Model):
    """
    Seuils pour les définitions de métriques.
    """
    THRESHOLD_TYPES = [
        ('static', 'Statique'),
        ('dynamic', 'Dynamique'),
        ('baseline', 'Baseline')
    ]
    
    COMPARISON_CHOICES = [
        ('gt', 'Supérieur à'),
        ('lt', 'Inférieur à'),
        ('eq', 'Égal à'),
        ('ne', 'Différent de'),
        ('ge', 'Supérieur ou égal à'),
        ('le', 'Inférieur ou égal à')
    ]
    
    metrics_definition = models.ForeignKey(
        MetricsDefinition, 
        on_delete=models.CASCADE, 
        related_name='thresholds',
        verbose_name='Définition de métrique'
    )
    threshold_type = models.CharField(
        max_length=20, 
        choices=THRESHOLD_TYPES,
        verbose_name='Type de seuil'
    )
    warning_value = models.FloatField(
        null=True, 
        blank=True,
        verbose_name='Valeur d\'avertissement'
    )
    critical_value = models.FloatField(
        null=True, 
        blank=True,
        verbose_name='Valeur critique'
    )
    comparison = models.CharField(
        max_length=2, 
        choices=COMPARISON_CHOICES, 
        default='gt',
        verbose_name='Comparaison'
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
        return f"{self.metrics_definition.name} - {self.get_threshold_type_display()}"
    
    class Meta:
        verbose_name = "Seuil de métrique"
        verbose_name_plural = "Seuils de métriques"
        ordering = ['metrics_definition', 'threshold_type']


class DeviceMetric(models.Model):
    """
    Association des métriques aux équipements.
    """
    device = models.ForeignKey(
        'network_management.NetworkDevice',
        on_delete=models.CASCADE,
        related_name='monitoring_metrics',
        verbose_name='Équipement'
    )
    metric = models.ForeignKey(
        MetricsDefinition, 
        on_delete=models.CASCADE,
        verbose_name='Métrique'
    )
    interface = models.ForeignKey(
        'network_management.NetworkInterface',
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='monitoring_metrics',
        verbose_name='Interface'
    )
    collection_interval = models.IntegerField(
        default=60,
        verbose_name='Intervalle de collecte (secondes)'
    )
    last_collection = models.DateTimeField(
        null=True, 
        blank=True,
        verbose_name='Dernière collecte'
    )
    next_collection = models.DateTimeField(
        null=True, 
        blank=True,
        verbose_name='Prochaine collecte'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='Active'
    )
    custom_parameters = models.JSONField(
        default=dict, 
        blank=True,
        verbose_name='Paramètres personnalisés'
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
        verbose_name = "Métrique d'équipement"
        verbose_name_plural = "Métriques d'équipement"
        unique_together = ('device', 'metric', 'interface')

    def __str__(self):
        if self.interface:
            return f"{self.device.name} - {self.interface.name} - {self.metric.name}"
        return f"{self.device.name} - {self.metric.name}"

    def schedule_next_collection(self):
        """
        Planifie la prochaine collecte basée sur l'intervalle.
        """
        now = timezone.now()
        self.last_collection = now
        self.next_collection = now + timezone.timedelta(seconds=self.collection_interval)
        self.save(update_fields=['last_collection', 'next_collection'])


class MetricValue(models.Model):
    """
    Valeurs de métriques (séries temporelles).
    """
    device_metric = models.ForeignKey(
        DeviceMetric, 
        on_delete=models.CASCADE, 
        related_name='values',
        verbose_name='Métrique d\'équipement'
    )
    value = models.FloatField(
        verbose_name='Valeur'
    )
    timestamp = models.DateTimeField(
        verbose_name='Horodatage'
    )
    metadata = models.JSONField(
        default=dict, 
        blank=True,
        verbose_name='Métadonnées'
    )
    
    class Meta:
        verbose_name = "Valeur de métrique"
        verbose_name_plural = "Valeurs de métriques"
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['device_metric', '-timestamp']),
            models.Index(fields=['timestamp']),
            models.Index(fields=['device_metric', 'timestamp']),
        ]

    def __str__(self):
        return f"{self.device_metric} = {self.value} ({self.timestamp.strftime('%Y-%m-%d %H:%M:%S')})"


class ThresholdRule(models.Model):
    """
    Règles de seuil d'alerte.
    """
    COMPARISON_OPERATORS = [
        ('>', 'Supérieur'),
        ('<', 'Inférieur'),
        ('>=', 'Supérieur ou égal'),
        ('<=', 'Inférieur ou égal'),
        ('==', 'Égal'),
        ('!=', 'Différent')
    ]
    
    device_metric = models.ForeignKey(
        DeviceMetric, 
        on_delete=models.CASCADE, 
        related_name='threshold_rules',
        verbose_name='Métrique d\'équipement'
    )
    name = models.CharField(
        max_length=255,
        verbose_name='Nom'
    )
    description = models.TextField(
        blank=True,
        verbose_name='Description'
    )
    warning_threshold = models.FloatField(
        null=True, 
        blank=True,
        verbose_name='Seuil d\'avertissement'
    )
    critical_threshold = models.FloatField(
        null=True, 
        blank=True,
        verbose_name='Seuil critique'
    )
    comparison_operator = models.CharField(
        max_length=10, 
        choices=COMPARISON_OPERATORS, 
        default='>',
        verbose_name='Opérateur de comparaison'
    )
    duration_seconds = models.IntegerField(
        default=0, 
        help_text="Durée en secondes pour déclencher l'alerte",
        verbose_name='Durée (secondes)'
    )
    recovery_threshold = models.FloatField(
        null=True, 
        blank=True, 
        help_text="Seuil pour considérer l'alerte résolue",
        verbose_name='Seuil de récupération'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='Active'
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
        return f"{self.name} ({self.device_metric})"
    
    class Meta:
        verbose_name = "Règle de seuil"
        verbose_name_plural = "Règles de seuil"
        ordering = ['name']


class AnomalyDetectionConfig(models.Model):
    """
    Configuration pour la détection d'anomalies.
    """
    ALGORITHMS = [
        ('isolation_forest', 'Isolation Forest'),
        ('z_score', 'Z-Score'),
        ('moving_average', 'Moyenne Mobile'),
        ('lstm', 'LSTM Neural Network'),
        ('arima', 'ARIMA'),
        ('auto', 'Auto-détection')
    ]
    
    device_metric = models.ForeignKey(
        DeviceMetric, 
        on_delete=models.CASCADE, 
        related_name='anomaly_configs',
        verbose_name='Métrique d\'équipement'
    )
    name = models.CharField(
        max_length=255,
        verbose_name='Nom'
    )
    description = models.TextField(
        blank=True,
        verbose_name='Description'
    )
    algorithm = models.CharField(
        max_length=50, 
        choices=ALGORITHMS,
        verbose_name='Algorithme'
    )
    sensitivity = models.FloatField(
        default=0.5, 
        help_text="Sensibilité de 0.0 à 1.0",
        verbose_name='Sensibilité'
    )
    training_window_days = models.IntegerField(
        default=30, 
        help_text="Jours de données historiques pour l'entraînement",
        verbose_name='Fenêtre d\'entraînement (jours)'
    )
    parameters = models.JSONField(
        default=dict, 
        blank=True, 
        help_text="Paramètres spécifiques à l'algorithme",
        verbose_name='Paramètres'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='Active'
    )
    last_training = models.DateTimeField(
        null=True, 
        blank=True,
        verbose_name='Dernier entraînement'
    )
    model_accuracy = models.FloatField(
        null=True, 
        blank=True,
        verbose_name='Précision du modèle'
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
        return f"{self.name} ({self.algorithm})"
    
    class Meta:
        verbose_name = "Configuration de détection d'anomalies"
        verbose_name_plural = "Configurations de détection d'anomalies"
        ordering = ['name'] 