# qos_management/models.py
from django.db import models
from network_management.infrastructure.models import NetworkDevice, NetworkInterface
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models import JSONField

class QoSPolicy(models.Model):
    """Modèle pour les politiques de QoS"""
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True, null=True)
    policy_type = models.CharField(max_length=50)
    priority = models.IntegerField(default=0)
    bandwidth_limit = models.PositiveIntegerField(null=True, blank=True)  # en kbps
    status = models.CharField(max_length=20, default='inactive')
    configuration = JSONField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        app_label = 'qos_management'
        verbose_name = "Politique QoS"
        verbose_name_plural = "Politiques QoS"
        ordering = ['-priority', 'name']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        # Valider la configuration
        if self.configuration:
            # Validation spécifique selon le type de politique
            if self.policy_type == 'htb' and 'classes' in self.configuration:
                total_bw = sum(cls.get('bandwidth', 0) for cls in self.configuration['classes'])
                if self.bandwidth_limit and total_bw > self.bandwidth_limit:
                    raise ValidationError(
                        f"La somme des bandes passantes ({total_bw}) dépasse la limite ({self.bandwidth_limit})"
                    )
        
        super().save(*args, **kwargs)

class TrafficClass(models.Model):
    """Modèle pour les classes de trafic"""
    policy = models.ForeignKey(QoSPolicy, on_delete=models.CASCADE, related_name='traffic_classes')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    priority = models.IntegerField(default=0)
    dscp = models.IntegerField(null=True, blank=True, 
                             validators=[MinValueValidator(0), MaxValueValidator(63)])
    bandwidth = models.PositiveIntegerField(default=0)  # en kbps
    bandwidth_percent = models.FloatField(default=0.0, 
                                        validators=[MinValueValidator(0), MaxValueValidator(100)])
    queue_limit = models.PositiveIntegerField(default=64)
    parameters = JSONField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        app_label = 'qos_management'
        ordering = ['policy', 'priority']
        unique_together = ('policy', 'name')
    
    def __str__(self):
        return f"{self.policy.name} - {self.name}"
    
    def calculate_effective_bandwidth(self):
        """Calcule la bande passante effective en fonction du pourcentage et de la limite de la politique."""
        if self.bandwidth > 0:
            return self.bandwidth
        
        if self.policy.bandwidth_limit and self.bandwidth_percent > 0:
            return int(self.policy.bandwidth_limit * self.bandwidth_percent / 100)
        
        return 0

class TrafficClassifier(models.Model):
    """Modèle pour les classificateurs de trafic"""
    traffic_class = models.ForeignKey(TrafficClass, on_delete=models.CASCADE, related_name='classifiers')
    description = models.CharField(max_length=255, blank=True, null=True)
    protocol = models.CharField(max_length=50, blank=True, null=True)
    source_ip = models.CharField(max_length=50, blank=True, null=True)
    destination_ip = models.CharField(max_length=50, blank=True, null=True)
    source_port_start = models.IntegerField(null=True, blank=True, 
                                          validators=[MinValueValidator(0), MaxValueValidator(65535)])
    source_port_end = models.IntegerField(null=True, blank=True, 
                                        validators=[MinValueValidator(0), MaxValueValidator(65535)])
    destination_port_start = models.IntegerField(null=True, blank=True, 
                                               validators=[MinValueValidator(0), MaxValueValidator(65535)])
    destination_port_end = models.IntegerField(null=True, blank=True, 
                                             validators=[MinValueValidator(0), MaxValueValidator(65535)])
    dscp = models.IntegerField(null=True, blank=True, 
                             validators=[MinValueValidator(0), MaxValueValidator(63)])
    vlan_id = models.IntegerField(null=True, blank=True, 
                                validators=[MinValueValidator(0), MaxValueValidator(4095)])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        app_label = 'qos_management'
        ordering = ['traffic_class', 'protocol']
    
    def __str__(self):
        protocols = self.protocol or "any"
        sources = self.source_ip or "any"
        destinations = self.destination_ip or "any"
        return f"{self.traffic_class.name} - {protocols} from {sources} to {destinations}"

class InterfaceQoSPolicy(models.Model):
    """Application d'une politique QoS à une interface réseau"""
    policy = models.ForeignKey(QoSPolicy, on_delete=models.CASCADE, related_name='interface_associations')
    device_id = models.IntegerField()
    interface_id = models.IntegerField()
    interface_name = models.CharField(max_length=255)
    direction = models.CharField(max_length=10, choices=[('ingress', 'Entrée'), ('egress', 'Sortie')])
    parameters = JSONField(blank=True, null=True)
    applied_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.interface_name} - {self.policy.name} ({self.direction})"
    
    class Meta:
        app_label = 'qos_management'
        verbose_name = "Association Interface-Politique QoS"
        verbose_name_plural = "Associations Interface-Politique QoS"
        unique_together = ('interface_id', 'direction')

class SLAComplianceRecord(models.Model):
    """
    Modèle pour stocker les enregistrements de conformité SLA.
    """
    device_id = models.IntegerField()
    device_name = models.CharField(max_length=255, blank=True, null=True)
    timestamp = models.DateTimeField(default=timezone.now)
    period = models.CharField(max_length=10, help_text="Période de l'évaluation (ex: '24h', '7d')")
    overall_compliance = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(1)],
        help_text="Taux de conformité global (0-1)"
    )
    service_class_compliances = JSONField(
        blank=True, null=True,
        help_text="Taux de conformité par classe de service"
    )
    metrics = JSONField(
        blank=True, null=True,
        help_text="Métriques détaillées (latence, jitter, perte de paquets, etc.)"
    )
    issues = JSONField(
        blank=True, null=True,
        help_text="Problèmes détectés"
    )
    recommendations = JSONField(
        blank=True, null=True,
        help_text="Recommandations pour améliorer la conformité"
    )
    
    class Meta:
        verbose_name = "Enregistrement de conformité SLA"
        verbose_name_plural = "Enregistrements de conformité SLA"
        ordering = ['-timestamp', 'device_id']
        indexes = [
            models.Index(fields=['device_id', 'timestamp']),
            models.Index(fields=['timestamp']),
            models.Index(fields=['overall_compliance']),
        ]
    
    def __str__(self):
        device_info = self.device_name or f"Device #{self.device_id}"
        compliance_pct = int(self.overall_compliance * 100)
        return f"{device_info} - {compliance_pct}% conformité SLA ({self.timestamp.strftime('%Y-%m-%d %H:%M')})"
    
    @property
    def compliance_percentage(self):
        """Retourne le taux de conformité en pourcentage."""
        return int(self.overall_compliance * 100)
    
    @property
    def is_compliant(self):
        """Indique si l'enregistrement est conforme (>= 95%)."""
        return self.overall_compliance >= 0.95


class QoSStatistics(models.Model):
    """
    Modèle pour stocker les statistiques de trafic QoS collectées en temps réel.
    """
    interface_name = models.CharField(max_length=255)
    device_id = models.IntegerField(null=True, blank=True)
    timestamp = models.DateTimeField(default=timezone.now)
    
    # Statistiques Traffic Control
    bytes_sent = models.BigIntegerField(default=0)
    packets_sent = models.BigIntegerField(default=0)
    bytes_dropped = models.BigIntegerField(default=0)
    packets_dropped = models.BigIntegerField(default=0)
    overlimits = models.BigIntegerField(default=0)
    requeues = models.BigIntegerField(default=0)
    
    # Métriques de performance
    utilization_percentage = models.FloatField(default=0.0)
    congestion_level = models.CharField(
        max_length=20, 
        choices=[
            ('normal', 'Normal'),
            ('low', 'Faible'),
            ('medium', 'Moyen'),
            ('high', 'Élevé'),
            ('critical', 'Critique')
        ],
        default='normal'
    )
    
    # Données brutes du service traffic-control
    raw_tc_output = models.TextField(blank=True, null=True)
    additional_metrics = JSONField(blank=True, null=True)
    
    class Meta:
        app_label = 'qos_management'
        verbose_name = "Statistique QoS"
        verbose_name_plural = "Statistiques QoS"
        ordering = ['-timestamp', 'interface_name']
        indexes = [
            models.Index(fields=['interface_name', 'timestamp']),
            models.Index(fields=['timestamp']),
            models.Index(fields=['congestion_level']),
            models.Index(fields=['device_id', 'timestamp']),
        ]
    
    def __str__(self):
        return f"{self.interface_name} - {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')} ({self.congestion_level})"
    
    @property
    def is_congested(self):
        """Indique si l'interface montre des signes de congestion."""
        return self.congestion_level in ['high', 'critical'] or self.overlimits > 0 or self.packets_dropped > 0


class PolicyApplicationLog(models.Model):
    """
    Modèle pour logger les applications automatiques de politiques QoS.
    """
    policy = models.ForeignKey(QoSPolicy, on_delete=models.CASCADE, related_name='application_logs')
    interface_name = models.CharField(max_length=255)
    device_id = models.IntegerField(null=True, blank=True)
    
    # Type d'action
    action_type = models.CharField(
        max_length=50,
        choices=[
            ('applied', 'Politique appliquée'),
            ('modified', 'Politique modifiée'),
            ('removed', 'Politique supprimée'),
            ('optimized', 'Politique optimisée'),
            ('failed', 'Application échouée')
        ]
    )
    
    # Déclencheur de l'action
    trigger_source = models.CharField(
        max_length=50,
        choices=[
            ('manual', 'Manuel'),
            ('automatic', 'Automatique'),
            ('congestion_detected', 'Congestion détectée'),
            ('compliance_violation', 'Violation conformité'),
            ('recommendation_engine', 'Moteur de recommandations'),
            ('scheduled_optimization', 'Optimisation planifiée')
        ],
        default='manual'
    )
    
    # Détails de l'application
    applied_at = models.DateTimeField(default=timezone.now)
    applied_by = models.CharField(max_length=255, blank=True, null=True)  # utilisateur ou 'system'
    success = models.BooleanField(default=True)
    error_message = models.TextField(blank=True, null=True)
    
    # Configuration appliquée
    applied_configuration = JSONField(blank=True, null=True)
    previous_configuration = JSONField(blank=True, null=True)
    
    # Résultats de l'application
    performance_before = JSONField(blank=True, null=True)
    performance_after = JSONField(blank=True, null=True)
    
    # Métadonnées
    execution_time_ms = models.IntegerField(default=0)
    celery_task_id = models.CharField(max_length=255, blank=True, null=True)
    additional_metadata = JSONField(blank=True, null=True)
    
    class Meta:
        app_label = 'qos_management'
        verbose_name = "Log d'application de politique QoS"
        verbose_name_plural = "Logs d'application de politiques QoS"
        ordering = ['-applied_at', 'interface_name']
        indexes = [
            models.Index(fields=['interface_name', 'applied_at']),
            models.Index(fields=['policy', 'applied_at']),
            models.Index(fields=['trigger_source', 'applied_at']),
            models.Index(fields=['success', 'applied_at']),
            models.Index(fields=['device_id', 'applied_at']),
        ]
    
    def __str__(self):
        status = "✅" if self.success else "❌"
        return f"{status} {self.get_action_type_display()} - {self.policy.name} sur {self.interface_name}"
    
    @property
    def duration_seconds(self):
        """Retourne la durée d'exécution en secondes."""
        return self.execution_time_ms / 1000 if self.execution_time_ms else 0
    
    def get_performance_improvement(self):
        """Calcule l'amélioration de performance si disponible."""
        if not (self.performance_before and self.performance_after):
            return None
        
        try:
            before_util = self.performance_before.get('utilization_percentage', 0)
            after_util = self.performance_after.get('utilization_percentage', 0)
            
            if before_util > 0:
                improvement = ((before_util - after_util) / before_util) * 100
                return round(improvement, 2)
        except (TypeError, ZeroDivisionError):
            pass
        
        return None


class QoSRecommendation(models.Model):
    """
    Modèle pour stocker les recommandations QoS générées automatiquement.
    """
    interface_name = models.CharField(max_length=255, blank=True, null=True)
    device_id = models.IntegerField(null=True, blank=True)
    policy = models.ForeignKey(QoSPolicy, on_delete=models.CASCADE, null=True, blank=True, related_name='recommendations')
    
    # Type et priorité de la recommandation
    recommendation_type = models.CharField(
        max_length=50,
        choices=[
            ('bandwidth_optimization', 'Optimisation bande passante'),
            ('priority_adjustment', 'Ajustement priorités'),
            ('traffic_shaping', 'Traffic shaping'),
            ('voip_optimization', 'Optimisation VoIP'),
            ('video_optimization', 'Optimisation vidéo'),
            ('business_data_optimization', 'Optimisation données métier'),
            ('general_optimization', 'Optimisation générale'),
            ('compliance_fix', 'Correction conformité'),
            ('congestion_mitigation', 'Atténuation congestion')
        ]
    )
    
    priority = models.CharField(
        max_length=20,
        choices=[
            ('critical', 'Critique'),
            ('high', 'Élevée'),
            ('medium', 'Moyenne'),
            ('low', 'Faible')
        ],
        default='medium'
    )
    
    # Contenu de la recommandation
    title = models.CharField(max_length=255)
    description = models.TextField()
    recommended_action = models.CharField(max_length=100)
    expected_improvement = models.CharField(max_length=255, blank=True, null=True)
    
    # Configuration recommandée
    recommended_configuration = JSONField(blank=True, null=True)
    
    # Métadonnées de génération
    generated_at = models.DateTimeField(default=timezone.now)
    generated_by_engine = models.CharField(max_length=100, default='qos_ai_engine')
    confidence_score = models.FloatField(
        default=0.5,
        validators=[MinValueValidator(0), MaxValueValidator(1)],
        help_text="Score de confiance de la recommandation (0-1)"
    )
    
    # Données d'analyse utilisées
    analysis_data = JSONField(blank=True, null=True)
    traffic_patterns = JSONField(blank=True, null=True)
    
    # Statut de la recommandation
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'En attente'),
            ('applied', 'Appliquée'),
            ('rejected', 'Rejetée'),
            ('expired', 'Expirée'),
            ('superseded', 'Remplacée')
        ],
        default='pending'
    )
    
    applied_at = models.DateTimeField(null=True, blank=True)
    applied_by = models.CharField(max_length=255, blank=True, null=True)
    rejection_reason = models.TextField(blank=True, null=True)
    
    # Résultats après application
    effectiveness_score = models.FloatField(
        null=True, blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(1)],
        help_text="Score d'efficacité après application (0-1)"
    )
    
    class Meta:
        app_label = 'qos_management'
        verbose_name = "Recommandation QoS"
        verbose_name_plural = "Recommandations QoS"
        ordering = ['-generated_at', '-priority', 'interface_name']
        indexes = [
            models.Index(fields=['status', 'priority']),
            models.Index(fields=['device_id', 'generated_at']),
            models.Index(fields=['interface_name', 'generated_at']),
            models.Index(fields=['recommendation_type', 'priority']),
            models.Index(fields=['generated_at']),
        ]
    
    def __str__(self):
        priority_emoji = {
            'critical': '🔴',
            'high': '🟠', 
            'medium': '🟡',
            'low': '🟢'
        }.get(self.priority, '⚪')
        
        target = self.interface_name or f"Device {self.device_id}" or "Global"
        return f"{priority_emoji} {self.title} - {target}"
    
    @property
    def is_actionable(self):
        """Indique si la recommandation peut encore être appliquée."""
        return self.status == 'pending' and self.confidence_score >= 0.3
    
    @property
    def age_hours(self):
        """Retourne l'âge de la recommandation en heures."""
        return (timezone.now() - self.generated_at).total_seconds() / 3600
    
    def mark_as_applied(self, applied_by=None):
        """Marque la recommandation comme appliquée."""
        self.status = 'applied'
        self.applied_at = timezone.now()
        self.applied_by = applied_by or 'system'
        self.save(update_fields=['status', 'applied_at', 'applied_by'])
    
    def mark_as_rejected(self, reason=None):
        """Marque la recommandation comme rejetée."""
        self.status = 'rejected'
        self.rejection_reason = reason
        self.save(update_fields=['status', 'rejection_reason'])
