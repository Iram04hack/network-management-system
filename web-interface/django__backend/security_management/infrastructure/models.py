"""
Modèles de données Django pour le module security_management.

Ce fichier contient les modèles de base de données utilisés par l'infrastructure
pour persister les entités du domaine.
"""

from django.db import models
from django.contrib.postgres.fields import ArrayField


class SecurityRuleModel(models.Model):
    """Modèle de règle de sécurité."""
    
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    rule_type = models.CharField(max_length=50)
    content = models.TextField(blank=True, null=True)
    source_ip = models.CharField(max_length=50, blank=True, null=True)
    destination_ip = models.CharField(max_length=50, blank=True, null=True)
    source_port = models.CharField(max_length=10, blank=True, null=True)
    destination_port = models.CharField(max_length=10, blank=True, null=True)
    protocol = models.CharField(max_length=10, blank=True, null=True)
    action = models.CharField(max_length=50, blank=True, null=True)
    enabled = models.BooleanField(default=True)
    priority = models.IntegerField(default=100)
    creation_date = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)
    trigger_count = models.IntegerField(default=0)
    tags = ArrayField(models.CharField(max_length=50), blank=True, null=True)
    
    class Meta:
        db_table = 'security_management_securityrule'
        verbose_name = "Règle de sécurité"
        verbose_name_plural = "Règles de sécurité"
        ordering = ["priority", "name"]
    
    def __str__(self):
        return f"{self.name} ({self.rule_type})"


class SecurityAlertModel(models.Model):
    """Modèle d'alerte de sécurité."""
    
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    source_ip = models.CharField(max_length=50, blank=True, null=True)
    destination_ip = models.CharField(max_length=50, blank=True, null=True)
    source_port = models.CharField(max_length=10, blank=True, null=True)
    destination_port = models.CharField(max_length=10, blank=True, null=True)
    protocol = models.CharField(max_length=10, blank=True, null=True)
    detection_time = models.DateTimeField()
    severity = models.CharField(max_length=20)
    status = models.CharField(max_length=50, default="new")
    source_rule = models.ForeignKey(
        SecurityRuleModel, on_delete=models.SET_NULL, 
        null=True, blank=True, related_name="alerts"
    )
    raw_data = models.JSONField(null=True, blank=True)
    false_positive = models.BooleanField(default=False)
    tags = ArrayField(models.CharField(max_length=50), blank=True, null=True)
    
    class Meta:
        verbose_name = "Alerte de sécurité"
        verbose_name_plural = "Alertes de sécurité"
        ordering = ["-detection_time"]
    
    def __str__(self):
        return f"{self.title} ({self.severity})"


class CorrelationRuleModel(models.Model):
    """Modèle de règle de corrélation."""
    
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    conditions = models.JSONField()
    time_window = models.IntegerField(help_text="Fenêtre de temps en secondes")
    aggregation_field = models.CharField(max_length=100, blank=True, null=True)
    threshold = models.IntegerField(default=1)
    severity = models.CharField(max_length=20, default="medium")
    enabled = models.BooleanField(default=True)
    creation_date = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)
    last_triggered = models.DateTimeField(null=True, blank=True)
    trigger_count = models.IntegerField(default=0)
    
    class Meta:
        verbose_name = "Règle de corrélation"
        verbose_name_plural = "Règles de corrélation"
        ordering = ["name"]
    
    def __str__(self):
        return f"{self.name} ({self.threshold} événements en {self.time_window}s)"


class CorrelationRuleMatchModel(models.Model):
    """Modèle de correspondance de règle de corrélation."""
    
    rule = models.ForeignKey(
        CorrelationRuleModel, on_delete=models.CASCADE,
        related_name="matches"
    )
    matched_at = models.DateTimeField()
    triggering_events = models.JSONField()
    context_data = models.JSONField(null=True, blank=True)
    
    class Meta:
        verbose_name = "Correspondance de règle de corrélation"
        verbose_name_plural = "Correspondances de règles de corrélation"
        ordering = ["-matched_at"]
    
    def __str__(self):
        return f"Match de {self.rule.name} à {self.matched_at}"


class TrafficBaselineModel(models.Model):
    """Modèle de ligne de base de trafic."""
    
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    network_segment = models.CharField(max_length=50, blank=True, null=True)
    service = models.CharField(max_length=100, blank=True, null=True)
    avg_requests_per_minute = models.FloatField(null=True, blank=True)
    avg_bytes_per_minute = models.FloatField(null=True, blank=True)
    avg_connections_per_minute = models.FloatField(null=True, blank=True)
    request_threshold_pct = models.FloatField(default=50.0)
    byte_threshold_pct = models.FloatField(default=50.0)
    connection_threshold_pct = models.FloatField(default=50.0)
    is_learning = models.BooleanField(default=True)
    learning_period_end = models.DateTimeField(null=True, blank=True)
    creation_date = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Ligne de base de trafic"
        verbose_name_plural = "Lignes de base de trafic"
        ordering = ["name"]
    
    def __str__(self):
        return f"{self.name} ({self.network_segment or 'global'})"


class TrafficAnomalyModel(models.Model):
    """Modèle d'anomalie de trafic."""
    
    baseline = models.ForeignKey(
        TrafficBaselineModel, on_delete=models.CASCADE,
        related_name="anomalies"
    )
    anomaly_type = models.CharField(max_length=50)
    severity = models.CharField(max_length=20)
    current_value = models.FloatField()
    baseline_value = models.FloatField()
    deviation_percent = models.FloatField()
    timestamp = models.DateTimeField()
    source_ip = models.CharField(max_length=50, null=True, blank=True)
    
    class Meta:
        verbose_name = "Anomalie de trafic"
        verbose_name_plural = "Anomalies de trafic"
        ordering = ["-timestamp"]
    
    def __str__(self):
        return f"{self.anomaly_type} ({self.severity}) à {self.timestamp}"


class IPReputationModel(models.Model):
    """Modèle de réputation d'adresse IP."""
    
    ip_address = models.CharField(max_length=50, unique=True)
    reputation_score = models.FloatField(default=0.0)
    classification = models.CharField(max_length=50, blank=True, null=True)
    is_blacklisted = models.BooleanField(default=False)
    is_whitelisted = models.BooleanField(default=False)
    first_seen = models.DateTimeField(auto_now_add=True)
    last_seen = models.DateTimeField(auto_now=True)
    alert_count = models.IntegerField(default=0)
    tags = ArrayField(models.CharField(max_length=50), blank=True, null=True)
    
    class Meta:
        verbose_name = "Réputation d'IP"
        verbose_name_plural = "Réputations d'IP"
        ordering = ["ip_address"]
    
    def __str__(self):
        return f"{self.ip_address} (score: {self.reputation_score})"


class SecurityPolicyModel(models.Model):
    """Modèle pour les politiques de sécurité."""
    
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    rules = models.JSONField(default=dict, help_text="Règles de sécurité au format JSON")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.CharField(max_length=255, blank=True, null=True)
    
    class Meta:
        verbose_name = "Politique de sécurité"
        verbose_name_plural = "Politiques de sécurité"
        ordering = ["name"]
    
    def __str__(self):
        return self.name


class VulnerabilityModel(models.Model):
    """Modèle pour les vulnérabilités."""
    
    SEVERITY_CHOICES = [
        ('critical', 'Critique'),
        ('high', 'Haute'),
        ('medium', 'Moyenne'),
        ('low', 'Basse'),
    ]
    
    STATUS_CHOICES = [
        ('identified', 'Identifiée'),
        ('confirmed', 'Confirmée'),
        ('in_progress', 'En cours de traitement'),
        ('patched', 'Corrigée'),
        ('mitigated', 'Atténuée'),
        ('false_positive', 'Faux positif'),
        ('accepted_risk', 'Risque accepté'),
    ]
    
    cve_id = models.CharField(max_length=50, blank=True, null=True)
    title = models.CharField(max_length=255)
    description = models.TextField()
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default='medium')
    cvss_score = models.FloatField(null=True, blank=True)
    cvss_vector = models.CharField(max_length=200, blank=True, null=True)
    cwe_id = models.CharField(max_length=50, blank=True, null=True)
    affected_systems = models.JSONField(default=list)
    affected_software = models.CharField(max_length=255, blank=True, null=True)
    affected_versions = models.CharField(max_length=255, blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='identified')
    discovered_date = models.DateTimeField(auto_now_add=True)
    published_date = models.DateTimeField(null=True, blank=True)
    patched_date = models.DateTimeField(null=True, blank=True)
    references = models.JSONField(default=list)
    patch_available = models.BooleanField(default=False)
    patch_info = models.JSONField(default=dict, blank=True)
    assigned_to = models.CharField(max_length=255, blank=True, null=True)
    priority = models.IntegerField(default=3)
    
    class Meta:
        verbose_name = "Vulnérabilité"
        verbose_name_plural = "Vulnérabilités"
        ordering = ["-cvss_score", "-discovered_date"]
    
    def __str__(self):
        return f"{self.title} ({self.cve_id or 'Sans CVE'})"


class ThreatIntelligenceModel(models.Model):
    """Modèle pour l'intelligence de menaces."""
    
    INDICATOR_TYPES = [
        ('ip', 'Adresse IP'),
        ('domain', 'Nom de domaine'),
        ('url', 'URL'),
        ('hash_md5', 'Hash MD5'),
        ('hash_sha1', 'Hash SHA1'),
        ('hash_sha256', 'Hash SHA256'),
        ('email', 'Adresse email'),
        ('filename', 'Nom de fichier'),
        ('registry_key', 'Clé de registre'),
        ('mutex', 'Mutex'),
        ('user_agent', 'User-Agent'),
    ]
    
    THREAT_TYPES = [
        ('malware', 'Malware'),
        ('phishing', 'Phishing'),
        ('botnet', 'Botnet'),
        ('apt', 'APT'),
        ('ransomware', 'Ransomware'),
        ('spam', 'Spam'),
        ('fraud', 'Fraude'),
        ('exploit', 'Exploit'),
        ('c2', 'Command & Control'),
        ('other', 'Autre'),
    ]
    
    CONFIDENCE_LEVELS = [
        ('low', 'Faible'),
        ('medium', 'Moyen'),
        ('high', 'Élevé'),
        ('confirmed', 'Confirmé'),
    ]
    
    indicator_type = models.CharField(max_length=20, choices=INDICATOR_TYPES)
    indicator_value = models.CharField(max_length=500)
    threat_type = models.CharField(max_length=20, choices=THREAT_TYPES)
    confidence = models.FloatField(default=0.5)
    severity = models.CharField(max_length=20, choices=VulnerabilityModel.SEVERITY_CHOICES, default='medium')
    title = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    tags = ArrayField(models.CharField(max_length=50), blank=True, null=True)
    source = models.CharField(max_length=100, blank=True, null=True)
    source_reliability = models.CharField(max_length=20, choices=CONFIDENCE_LEVELS, default='medium')
    external_id = models.CharField(max_length=100, blank=True, null=True)
    first_seen = models.DateTimeField(auto_now_add=True)
    last_seen = models.DateTimeField(auto_now=True)
    valid_until = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_whitelisted = models.BooleanField(default=False)
    context = models.JSONField(default=dict, blank=True)
    
    class Meta:
        verbose_name = "Intelligence de menace"
        verbose_name_plural = "Intelligence de menaces"
        ordering = ["-last_seen"]
        unique_together = ['indicator_type', 'indicator_value']
    
    def __str__(self):
        return f"{self.indicator_type}: {self.indicator_value} ({self.threat_type})"


class IncidentResponseWorkflowModel(models.Model):
    """Modèle pour les workflows de réponse aux incidents."""
    
    TRIGGER_TYPES = [
        ('alert_severity', 'Sévérité d\'alerte'),
        ('alert_source', 'Source d\'alerte'),
        ('ioc_match', 'Correspondance IOC'),
        ('vulnerability_score', 'Score de vulnérabilité'),
        ('correlation_rule', 'Règle de corrélation'),
        ('manual', 'Déclenchement manuel'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Actif'),
        ('inactive', 'Inactif'),
        ('draft', 'Brouillon'),
        ('archived', 'Archivé'),
    ]
    
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    version = models.CharField(max_length=20, default='1.0')
    trigger_type = models.CharField(max_length=30, choices=TRIGGER_TYPES)
    trigger_conditions = models.JSONField(default=dict)
    steps = models.JSONField(default=list)
    auto_execute = models.BooleanField(default=False)
    requires_approval = models.BooleanField(default=True)
    timeout_minutes = models.IntegerField(default=60)
    assigned_team = models.CharField(max_length=100, blank=True, null=True)
    escalation_rules = models.JSONField(default=dict, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    created_by = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    execution_count = models.IntegerField(default=0)
    success_count = models.IntegerField(default=0)
    last_executed = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = "Workflow de réponse aux incidents"
        verbose_name_plural = "Workflows de réponse aux incidents"
        ordering = ["-created_at"]
    
    def __str__(self):
        return f"{self.name} v{self.version} ({self.status})"


class IncidentResponseExecutionModel(models.Model):
    """Modèle pour l'exécution d'un workflow de réponse aux incidents."""
    
    EXECUTION_STATUS = [
        ('pending', 'En attente'),
        ('running', 'En cours'),
        ('completed', 'Terminé'),
        ('failed', 'Échoué'),
        ('cancelled', 'Annulé'),
        ('timeout', 'Timeout'),
    ]
    
    workflow = models.ForeignKey(
        IncidentResponseWorkflowModel, 
        on_delete=models.CASCADE, 
        related_name='executions'
    )
    triggered_by_alert = models.ForeignKey(
        SecurityAlertModel, 
        on_delete=models.SET_NULL, 
        null=True, blank=True,
        related_name='incident_responses'
    )
    triggered_by_event = models.JSONField(default=dict, blank=True)
    status = models.CharField(max_length=20, choices=EXECUTION_STATUS, default='pending')
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    current_step = models.IntegerField(default=0)
    steps_log = models.JSONField(default=list)
    assigned_to = models.CharField(max_length=255, blank=True, null=True)
    approved_by = models.CharField(max_length=255, blank=True, null=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    output_data = models.JSONField(default=dict, blank=True)
    error_message = models.TextField(blank=True, null=True)
    
    class Meta:
        verbose_name = "Exécution de workflow"
        verbose_name_plural = "Exécutions de workflows"
        ordering = ["-started_at"]
    
    def __str__(self):
        return f"Exécution de {self.workflow.name} ({self.status})"


class SecurityReportModel(models.Model):
    """Modèle pour les rapports de sécurité."""
    
    REPORT_TYPES = [
        ('vulnerability', 'Rapport de vulnérabilités'),
        ('threat_intelligence', 'Rapport d\'intelligence de menaces'),
        ('incident_response', 'Rapport de réponse aux incidents'),
        ('compliance', 'Rapport de conformité'),
        ('security_posture', 'Rapport de posture de sécurité'),
        ('alert_summary', 'Résumé des alertes'),
        ('custom', 'Rapport personnalisé'),
    ]
    
    FORMAT_CHOICES = [
        ('pdf', 'PDF'),
        ('json', 'JSON'),
        ('csv', 'CSV'),
        ('html', 'HTML'),
        ('excel', 'Excel'),
    ]
    
    STATUS_CHOICES = [
        ('generating', 'En cours de génération'),
        ('completed', 'Terminé'),
        ('failed', 'Échoué'),
        ('scheduled', 'Programmé'),
    ]
    
    name = models.CharField(max_length=255)
    report_type = models.CharField(max_length=30, choices=REPORT_TYPES)
    description = models.TextField(blank=True, null=True)
    parameters = models.JSONField(default=dict)
    filters = models.JSONField(default=dict)
    format = models.CharField(max_length=10, choices=FORMAT_CHOICES, default='pdf')
    is_scheduled = models.BooleanField(default=False)
    schedule_frequency = models.CharField(max_length=20, blank=True, null=True)
    next_execution = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    generated_at = models.DateTimeField(null=True, blank=True)
    file_path = models.CharField(max_length=500, blank=True, null=True)
    file_size = models.BigIntegerField(null=True, blank=True)
    created_by = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    recipients = models.JSONField(default=list)
    auto_send = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = "Rapport de sécurité"
        verbose_name_plural = "Rapports de sécurité"
        ordering = ["-created_at"]
    
    def __str__(self):
        return f"{self.name} ({self.report_type})"


class AuditLogModel(models.Model):
    """Modèle pour les journaux d'audit."""
    
    user = models.CharField(max_length=255, blank=True, null=True)
    action = models.CharField(max_length=100)
    entity_type = models.CharField(max_length=100)
    entity_id = models.CharField(max_length=255)
    timestamp = models.DateTimeField(auto_now_add=True)
    details = models.JSONField(default=dict, blank=True)
    ip_address = models.CharField(max_length=50, blank=True, null=True)
    user_agent = models.CharField(max_length=500, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Journal d'audit"
        verbose_name_plural = "Journaux d'audit"
        ordering = ["-timestamp"]
    
    def __str__(self):
        return f"{self.user or 'Système'} - {self.action} - {self.entity_type}:{self.entity_id}"


class SuricataAlert(models.Model):
    """Modèle pour stocker les alertes Suricata avec déclenchement automatique."""
    
    SEVERITY_CHOICES = [
        (1, 'Critical'),
        (2, 'High'),
        (3, 'Medium'),
        (4, 'Low'),
    ]
    
    alert_id = models.CharField(max_length=255, unique=True, db_index=True)
    signature = models.TextField()
    category = models.CharField(max_length=255, default='Unknown')
    severity = models.IntegerField(choices=SEVERITY_CHOICES, default=3)
    
    source_ip = models.GenericIPAddressField()
    destination_ip = models.GenericIPAddressField()
    source_port = models.IntegerField(default=0)
    destination_port = models.IntegerField(default=0)
    protocol = models.CharField(max_length=10, default='')
    
    timestamp = models.DateTimeField(db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Données brutes de l'alerte
    raw_data = models.JSONField(default=dict)
    
    # Statut de traitement pour déclencheurs automatiques
    processed = models.BooleanField(default=False)
    processed_at = models.DateTimeField(null=True, blank=True)
    
    # Rapport automatique associé
    auto_report_triggered = models.BooleanField(default=False)
    auto_report_session_id = models.CharField(max_length=100, blank=True)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['timestamp', 'severity']),
            models.Index(fields=['source_ip', 'destination_ip']),
            models.Index(fields=['processed', 'timestamp']),
            models.Index(fields=['auto_report_triggered', 'timestamp']),
        ]
    
    def __str__(self):
        return f"Alert {self.alert_id}: {self.signature[:50]}..."
    
    def get_severity_display_text(self):
        """Retourne la sévérité en texte."""
        severity_map = {1: 'critical', 2: 'high', 3: 'medium', 4: 'low'}
        return severity_map.get(self.severity, 'unknown')
    
    def mark_as_processed(self):
        """Marque l'alerte comme traitée."""
        from django.utils import timezone
        self.processed = True
        self.processed_at = timezone.now()
        self.save(update_fields=['processed', 'processed_at'])
    
    def mark_report_triggered(self, session_id: str):
        """Marque qu'un rapport automatique a été déclenché."""
        self.auto_report_triggered = True
        self.auto_report_session_id = session_id
        self.save(update_fields=['auto_report_triggered', 'auto_report_session_id'])


class SecurityEvent(models.Model):
    """Modèle pour stocker les événements de sécurité génériques avec corrélation."""
    
    EVENT_TYPES = [
        ('intrusion_detection', 'Détection d\'intrusion'),
        ('malware_detection', 'Détection de malware'),
        ('suspicious_activity', 'Activité suspecte'),
        ('policy_violation', 'Violation de politique'),
        ('authentication_failure', 'Échec d\'authentification'),
        ('privilege_escalation', 'Escalade de privilèges'),
        ('data_exfiltration', 'Exfiltration de données'),
        ('ddos_attack', 'Attaque DDoS'),
        ('brute_force', 'Attaque par force brute'),
        ('sql_injection', 'Injection SQL'),
        ('xss_attack', 'Attaque XSS'),
        ('automatic_detection', 'Détection automatique'),
        ('other', 'Autre'),
    ]
    
    SEVERITY_CHOICES = [
        ('critical', 'Critique'),
        ('high', 'Élevée'),
        ('medium', 'Moyenne'),
        ('low', 'Faible'),
        ('info', 'Information'),
    ]
    
    event_type = models.CharField(max_length=50, choices=EVENT_TYPES)
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default='medium')
    
    source_ip = models.GenericIPAddressField(null=True, blank=True)
    destination_ip = models.GenericIPAddressField(null=True, blank=True)
    source_port = models.IntegerField(null=True, blank=True)
    destination_port = models.IntegerField(null=True, blank=True)
    
    title = models.CharField(max_length=255)
    description = models.TextField()
    
    # Données d'événement pour corrélation
    event_data = models.JSONField(default=dict)
    
    # Métadonnées temporelles
    detected_at = models.DateTimeField(db_index=True)
    processed_at = models.DateTimeField(auto_now_add=True)
    
    # Corrélation avec alertes Suricata
    related_alert = models.ForeignKey(
        SuricataAlert, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='security_events'
    )
    
    # Corrélation avec alertes existantes
    related_security_alert = models.ForeignKey(
        SecurityAlertModel,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='correlated_events'
    )
    
    class Meta:
        ordering = ['-detected_at']
        indexes = [
            models.Index(fields=['detected_at', 'severity']),
            models.Index(fields=['event_type', 'severity']),
            models.Index(fields=['source_ip', 'destination_ip']),
        ]
    
    def __str__(self):
        return f"{self.get_severity_display()} - {self.title}"


class AutoSecurityReport(models.Model):
    """Modèle pour stocker les rapports de sécurité générés automatiquement."""
    
    REPORT_TYPES = [
        ('automatic', 'Automatique'),
        ('scheduled', 'Planifié'),
        ('manual', 'Manuel'),
        ('incident', 'Incident'),
        ('real_time', 'Temps réel'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'En attente'),
        ('generating', 'En cours de génération'),
        ('completed', 'Terminé'),
        ('failed', 'Échoué'),
        ('sent', 'Envoyé'),
        ('notification_sent', 'Notifications envoyées'),
    ]
    
    session_id = models.CharField(max_length=100, unique=True, db_index=True)
    report_type = models.CharField(max_length=20, choices=REPORT_TYPES, default='automatic')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    
    # Statistiques du rapport
    total_alerts = models.IntegerField(default=0)
    critical_alerts = models.IntegerField(default=0)
    high_alerts = models.IntegerField(default=0)
    medium_alerts = models.IntegerField(default=0)
    low_alerts = models.IntegerField(default=0)
    
    # Métriques de performance
    detection_rate = models.FloatField(default=100.0)
    response_time_minutes = models.FloatField(default=0.0)
    
    # Fichier de rapport
    report_file_path = models.CharField(max_length=500, blank=True)
    report_file_size = models.BigIntegerField(default=0)
    
    # Notifications automatiques
    email_sent = models.BooleanField(default=False)
    telegram_sent = models.BooleanField(default=False)
    notification_details = models.JSONField(default=dict)
    
    # Déclencheur du rapport
    trigger_source = models.CharField(max_length=100, default='automatic_monitoring')
    trigger_data = models.JSONField(default=dict)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    generated_at = models.DateTimeField(null=True, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    
    # Alertes incluses dans ce rapport
    included_alerts = models.ManyToManyField(
        SuricataAlert,
        through='AutoReportAlert',
        related_name='auto_reports'
    )
    
    # Tâches Celery associées
    generation_task_id = models.CharField(max_length=100, blank=True)
    notification_task_id = models.CharField(max_length=100, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['created_at', 'status']),
            models.Index(fields=['report_type', 'status']),
            models.Index(fields=['session_id', 'status']),
        ]
    
    def __str__(self):
        return f"Rapport Auto {self.session_id} - {self.get_status_display()}"
    
    def mark_as_completed(self, file_path: str = None, file_size: int = 0):
        """Marque le rapport comme terminé."""
        from django.utils import timezone
        self.status = 'completed'
        self.generated_at = timezone.now()
        if file_path:
            self.report_file_path = file_path
        if file_size:
            self.report_file_size = file_size
        self.save(update_fields=['status', 'generated_at', 'report_file_path', 'report_file_size'])
    
    def mark_as_sent(self, email_success: bool = False, telegram_success: bool = False, details: dict = None):
        """Marque le rapport comme envoyé."""
        from django.utils import timezone
        self.status = 'notification_sent'
        self.sent_at = timezone.now()
        self.email_sent = email_success
        self.telegram_sent = telegram_success
        if details:
            self.notification_details = details
        self.save(update_fields=['status', 'sent_at', 'email_sent', 'telegram_sent', 'notification_details'])


class AutoReportAlert(models.Model):
    """Table de liaison entre rapports automatiques et alertes Suricata."""
    
    report = models.ForeignKey(AutoSecurityReport, on_delete=models.CASCADE)
    alert = models.ForeignKey(SuricataAlert, on_delete=models.CASCADE)
    included_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['report', 'alert']
        indexes = [
            models.Index(fields=['report', 'included_at']),
        ]


class SecurityMonitoringMetrics(models.Model):
    """Modèle pour stocker les métriques du monitoring automatique."""
    
    # Métadonnées de scan
    scan_timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    scan_duration_seconds = models.FloatField(default=0.0)
    
    # Résultats de scan
    alerts_scanned = models.IntegerField(default=0)
    new_alerts_found = models.IntegerField(default=0)
    critical_alerts = models.IntegerField(default=0)
    high_alerts = models.IntegerField(default=0)
    medium_alerts = models.IntegerField(default=0)
    low_alerts = models.IntegerField(default=0)
    
    # Déclencheurs automatiques
    reports_triggered = models.IntegerField(default=0)
    notifications_sent = models.IntegerField(default=0)
    
    # Statut de santé
    elasticsearch_available = models.BooleanField(default=False)
    suricata_running = models.BooleanField(default=False)
    celery_worker_available = models.BooleanField(default=False)
    
    # Erreurs rencontrées
    scan_errors = models.JSONField(default=list)
    
    # Performance
    average_response_time = models.FloatField(default=0.0)
    
    class Meta:
        ordering = ['-scan_timestamp']
        indexes = [
            models.Index(fields=['scan_timestamp']),
            models.Index(fields=['new_alerts_found', 'scan_timestamp']),
        ]
    
    def __str__(self):
        return f"Scan {self.scan_timestamp}: {self.new_alerts_found} nouvelles alertes"


 