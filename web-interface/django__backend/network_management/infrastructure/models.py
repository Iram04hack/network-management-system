"""
Modèles Django pour le module Network Management.

Ce module contient les modèles Django utilisés pour persister
les données du système de gestion de réseau dans une base de données.
"""

from django.db import models
from django.contrib.auth.models import User


class NetworkDevice(models.Model):
    """Modèle pour les équipements réseau - Structure adaptée à la base de données existante."""

    # Champs de base (correspondant à la structure DB existante)
    name = models.CharField(max_length=255, verbose_name="Nom")
    hostname = models.CharField(max_length=255, verbose_name="Nom d'hôte", blank=True)
    ip_address = models.GenericIPAddressField(verbose_name="Adresse IP")
    mac_address = models.CharField(max_length=17, verbose_name="Adresse MAC", blank=True)

    # Type et informations matérielles
    device_type = models.CharField(max_length=50, verbose_name="Type d'équipement")
    manufacturer = models.CharField(max_length=100, verbose_name="Fabricant", blank=True)
    vendor = models.CharField(max_length=100, verbose_name="Fabricant", blank=True)
    model = models.CharField(max_length=100, verbose_name="Modèle", blank=True)
    os = models.CharField(max_length=100, verbose_name="OS", blank=True)
    os_version = models.CharField(max_length=100, verbose_name="Version OS", blank=True)

    # Informations administratives
    location = models.CharField(max_length=255, verbose_name="Emplacement", blank=True)
    description = models.TextField(verbose_name="Description", blank=True)

    # Statut et données supplémentaires (structure DB existante)
    is_active = models.BooleanField(verbose_name="Actif", default=True)
    is_virtual = models.BooleanField(verbose_name="Virtuel", default=False)
    management_interface = models.CharField(max_length=255, verbose_name="Interface de gestion", blank=True)
    credentials = models.JSONField(verbose_name="Identifiants", null=True, blank=True)
    snmp_community = models.CharField(max_length=255, verbose_name="Communauté SNMP", blank=True)
    metadata = models.JSONField(verbose_name="Métadonnées", null=True, blank=True)

    # Découverte et synchronisation
    last_discovered = models.DateTimeField(verbose_name="Dernière découverte", null=True, blank=True)
    discovery_method = models.CharField(max_length=100, verbose_name="Méthode de découverte", blank=True)
    node_id = models.CharField(max_length=255, verbose_name="ID de nœud", blank=True)
    last_sync = models.DateTimeField(verbose_name="Dernière synchronisation", null=True, blank=True)

    # Relations
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Créé par")

    # Audit
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Date de mise à jour")
    
    class Meta:
        verbose_name = "Équipement réseau"
        verbose_name_plural = "Équipements réseau"
        ordering = ["name"]
    
    def __str__(self):
        return f"{self.name} ({self.ip_address})"


class NetworkInterface(models.Model):
    """Modèle pour les interfaces réseau."""
    
    # Relations
    device = models.ForeignKey(
        NetworkDevice,
        on_delete=models.CASCADE,
        related_name="interfaces",
        verbose_name="Équipement"
    )
    
    # Champs de base
    name = models.CharField(max_length=255, verbose_name="Nom")
    description = models.TextField(verbose_name="Description", blank=True)
    
    # Informations réseau
    mac_address = models.CharField(max_length=17, verbose_name="Adresse MAC", blank=True)
    ip_address = models.GenericIPAddressField(verbose_name="Adresse IP", null=True, blank=True)
    subnet_mask = models.CharField(max_length=15, verbose_name="Masque de sous-réseau", blank=True)
    interface_type = models.CharField(max_length=50, verbose_name="Type d'interface", blank=True)
    speed = models.BigIntegerField(verbose_name="Vitesse (bps)", null=True, blank=True)
    mtu = models.IntegerField(verbose_name="MTU", null=True, blank=True)
    
    # Statut et données supplémentaires
    status = models.CharField(max_length=50, verbose_name="Statut", default="unknown")
    extra_data = models.JSONField(verbose_name="Données supplémentaires", null=True, blank=True)
    
    # Audit
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Date de mise à jour")
    
    class Meta:
        verbose_name = "Interface réseau"
        verbose_name_plural = "Interfaces réseau"
        ordering = ["device", "name"]
        unique_together = ["device", "name"]
    
    def __str__(self):
        return f"{self.device.name} - {self.name}"


class NetworkConnection(models.Model):
    """Modèle pour les connexions réseau entre interfaces."""
    
    # Relations
    source_device = models.ForeignKey(
        NetworkDevice,
        on_delete=models.CASCADE,
        related_name="source_connections",
        verbose_name="Équipement source"
    )
    source_interface = models.ForeignKey(
        NetworkInterface,
        on_delete=models.CASCADE,
        related_name="source_connections",
        verbose_name="Interface source"
    )
    target_device = models.ForeignKey(
        NetworkDevice,
        on_delete=models.CASCADE,
        related_name="target_connections",
        verbose_name="Équipement cible"
    )
    target_interface = models.ForeignKey(
        NetworkInterface,
        on_delete=models.CASCADE,
        related_name="target_connections",
        verbose_name="Interface cible"
    )
    
    # Informations de connexion
    connection_type = models.CharField(max_length=50, verbose_name="Type de connexion", default="ethernet")
    status = models.CharField(max_length=50, verbose_name="Statut", default="unknown")
    description = models.TextField(verbose_name="Description", blank=True)
    
    # Données supplémentaires
    extra_data = models.JSONField(verbose_name="Données supplémentaires", null=True, blank=True)
    
    # Audit
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Date de mise à jour")
    
    class Meta:
        verbose_name = "Connexion réseau"
        verbose_name_plural = "Connexions réseau"
        ordering = ["source_device", "source_interface"]
        unique_together = ["source_interface", "target_interface"]
    
    def __str__(self):
        return f"{self.source_device.name}:{self.source_interface.name} -> {self.target_device.name}:{self.target_interface.name}"


class DeviceConfiguration(models.Model):
    """Modèle pour les configurations d'équipements."""
    
    # Relations
    device = models.ForeignKey(
        NetworkDevice,
        on_delete=models.CASCADE,
        related_name="configurations",
        verbose_name="Équipement"
    )
    parent = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="children",
        verbose_name="Configuration parent"
    )
    
    # Contenu de la configuration
    content = models.TextField(verbose_name="Contenu")
    version = models.CharField(max_length=50, verbose_name="Version", default="running")
    
    # Statut et métadonnées
    is_active = models.BooleanField(verbose_name="Active", default=False)
    status = models.CharField(max_length=50, verbose_name="Statut", default="draft")
    comment = models.TextField(verbose_name="Commentaire", blank=True)
    created_by = models.CharField(max_length=255, verbose_name="Créé par")
    applied_at = models.DateTimeField(verbose_name="Date d'application", null=True, blank=True)
    error = models.TextField(verbose_name="Erreur", blank=True)
    
    # Données supplémentaires
    extra_data = models.JSONField(verbose_name="Données supplémentaires", null=True, blank=True)
    
    # Audit
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Date de mise à jour")
    
    class Meta:
        verbose_name = "Configuration d'équipement"
        verbose_name_plural = "Configurations d'équipements"
        ordering = ["-created_at"]
    
    def __str__(self):
        return f"{self.device.name} - {self.version} ({self.created_at})"


class ConfigurationTemplate(models.Model):
    """Modèle pour les modèles de configuration."""
    
    # Champs de base
    name = models.CharField(max_length=255, verbose_name="Nom")
    description = models.TextField(verbose_name="Description", blank=True)
    content = models.TextField(verbose_name="Contenu")
    
    # Classification
    device_type = models.CharField(max_length=50, verbose_name="Type d'équipement")
    vendor = models.CharField(max_length=100, verbose_name="Fabricant", blank=True)
    os_version = models.CharField(max_length=100, verbose_name="Version OS", blank=True)
    
    # Métadonnées
    variables = models.JSONField(verbose_name="Variables", null=True, blank=True)
    tags = models.JSONField(verbose_name="Tags", null=True, blank=True)
    
    # Audit
    created_by = models.CharField(max_length=255, verbose_name="Créé par")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Date de mise à jour")
    
    class Meta:
        verbose_name = "Modèle de configuration"
        verbose_name_plural = "Modèles de configuration"
        ordering = ["name"]
    
    def __str__(self):
        return f"{self.name} ({self.device_type})"


class CompliancePolicy(models.Model):
    """Modèle pour les politiques de conformité."""
    
    # Champs de base
    name = models.CharField(max_length=255, verbose_name="Nom")
    description = models.TextField(verbose_name="Description", blank=True)
    
    # Classification
    device_type = models.CharField(max_length=50, verbose_name="Type d'équipement", blank=True)
    vendor = models.CharField(max_length=100, verbose_name="Fabricant", blank=True)
    
    # Règles et critères
    rules = models.JSONField(verbose_name="Règles")
    severity = models.CharField(max_length=50, verbose_name="Sévérité", default="medium")
    
    # Audit
    created_by = models.CharField(max_length=255, verbose_name="Créé par")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Date de mise à jour")
    
    class Meta:
        verbose_name = "Politique de conformité"
        verbose_name_plural = "Politiques de conformité"
        ordering = ["name"]
    
    def __str__(self):
        return self.name


class ComplianceCheck(models.Model):
    """Modèle pour les vérifications de conformité."""
    
    # Relations
    device = models.ForeignKey(
        NetworkDevice,
        on_delete=models.CASCADE,
        related_name="compliance_checks",
        verbose_name="Équipement"
    )
    policy = models.ForeignKey(
        CompliancePolicy,
        on_delete=models.CASCADE,
        related_name="compliance_checks",
        verbose_name="Politique"
    )
    configuration = models.ForeignKey(
        DeviceConfiguration,
        on_delete=models.CASCADE,
        related_name="compliance_checks",
        verbose_name="Configuration"
    )
    
    # Résultats
    is_compliant = models.BooleanField(verbose_name="Conforme")
    results = models.JSONField(verbose_name="Résultats")
    
    # Audit
    checked_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de vérification")
    checked_by = models.CharField(max_length=255, verbose_name="Vérifié par")
    
    class Meta:
        verbose_name = "Vérification de conformité"
        verbose_name_plural = "Vérifications de conformité"
        ordering = ["-checked_at"]
    
    def __str__(self):
        return f"{self.device.name} - {self.policy.name} ({self.checked_at})"


class Alert(models.Model):
    """Modèle pour les alertes."""
    
    # Relations
    device = models.ForeignKey(
        NetworkDevice,
        on_delete=models.CASCADE,
        related_name="network_alerts",
        verbose_name="Équipement",
        null=True,
        blank=True
    )
    interface = models.ForeignKey(
        NetworkInterface,
        on_delete=models.CASCADE,
        related_name="alerts",
        verbose_name="Interface",
        null=True,
        blank=True
    )
    
    # Informations d'alerte
    title = models.CharField(max_length=255, verbose_name="Titre")
    message = models.TextField(verbose_name="Message")
    severity = models.CharField(max_length=50, verbose_name="Sévérité", default="medium")
    status = models.CharField(max_length=50, verbose_name="Statut", default="active")
    
    # Métadonnées
    source = models.CharField(max_length=100, verbose_name="Source")
    category = models.CharField(max_length=100, verbose_name="Catégorie")
    details = models.JSONField(verbose_name="Détails", null=True, blank=True)
    
    # Gestion de l'alerte
    acknowledged = models.BooleanField(verbose_name="Acquittée", default=False)
    acknowledged_by = models.CharField(max_length=255, verbose_name="Acquittée par", blank=True)
    acknowledged_at = models.DateTimeField(verbose_name="Date d'acquittement", null=True, blank=True)
    acknowledgement_comment = models.TextField(verbose_name="Commentaire d'acquittement", blank=True)
    
    # Audit
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Date de mise à jour")
    
    class Meta:
        verbose_name = "Alerte"
        verbose_name_plural = "Alertes"
        ordering = ["-created_at"]
    
    def __str__(self):
        return f"{self.title} ({self.severity}) - {self.created_at}"


class Metric(models.Model):
    """Modèle pour les métriques."""
    
    # Relations
    device = models.ForeignKey(
        NetworkDevice,
        on_delete=models.CASCADE,
        related_name="network_metrics",
        verbose_name="Équipement",
        null=True,
        blank=True
    )
    interface = models.ForeignKey(
        NetworkInterface,
        on_delete=models.CASCADE,
        related_name="network_metrics",
        verbose_name="Interface",
        null=True,
        blank=True
    )
    
    # Informations de métrique
    name = models.CharField(max_length=100, verbose_name="Nom")
    value = models.FloatField(verbose_name="Valeur")
    unit = models.CharField(max_length=50, verbose_name="Unité", blank=True)
    
    # Métadonnées
    category = models.CharField(max_length=100, verbose_name="Catégorie")
    tags = models.JSONField(verbose_name="Tags", null=True, blank=True)
    
    # Horodatage
    timestamp = models.DateTimeField(verbose_name="Horodatage")
    
    class Meta:
        verbose_name = "Métrique"
        verbose_name_plural = "Métriques"
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["device", "name", "timestamp"]),
            models.Index(fields=["interface", "name", "timestamp"]),
        ]
    
    def __str__(self):
        return f"{self.name}: {self.value} {self.unit} ({self.timestamp})"


class Log(models.Model):
    """Modèle pour les logs."""
    
    # Relations
    device = models.ForeignKey(
        NetworkDevice,
        on_delete=models.CASCADE,
        related_name="logs",
        verbose_name="Équipement",
        null=True,
        blank=True
    )
    
    # Informations de log
    level = models.CharField(max_length=50, verbose_name="Niveau")
    message = models.TextField(verbose_name="Message")
    source = models.CharField(max_length=100, verbose_name="Source")
    
    # Métadonnées
    details = models.JSONField(verbose_name="Détails", null=True, blank=True)
    
    # Horodatage
    timestamp = models.DateTimeField(verbose_name="Horodatage")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date d'enregistrement")
    
    class Meta:
        verbose_name = "Log"
        verbose_name_plural = "Logs"
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["device", "level", "timestamp"]),
            models.Index(fields=["source", "timestamp"]),
        ]
    
    def __str__(self):
        return f"{self.level}: {self.message} ({self.timestamp})"


class Topology(models.Model):
    """Modèle pour les topologies réseau."""
    
    # Champs de base
    name = models.CharField(max_length=255, verbose_name="Nom")
    description = models.TextField(verbose_name="Description", blank=True)
    
    # Données de topologie
    layout = models.JSONField(verbose_name="Disposition", null=True, blank=True)
    devices = models.JSONField(verbose_name="Équipements", null=True, blank=True)
    connections = models.JSONField(verbose_name="Connexions", null=True, blank=True)
    
    # Métadonnées
    is_auto_discovered = models.BooleanField(verbose_name="Découverte automatique", default=False)
    tags = models.JSONField(verbose_name="Tags", null=True, blank=True)
    
    # Audit
    created_by = models.CharField(max_length=255, verbose_name="Créé par")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Date de mise à jour")
    
    class Meta:
        verbose_name = "Topologie"
        verbose_name_plural = "Topologies"
        ordering = ["name"]
    
    def __str__(self):
        return self.name


class DashboardConfiguration(models.Model):
    """Modèle pour les configurations de tableau de bord."""
    
    # Relations
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="dashboard_configurations",
        verbose_name="Utilisateur",
        null=True,
        blank=True
    )
    
    # Champs de base
    dashboard_type = models.CharField(max_length=100, verbose_name="Type de tableau de bord")
    configuration = models.JSONField(verbose_name="Configuration")
    
    # Métadonnées
    is_active = models.BooleanField(verbose_name="Active", default=True)
    is_default = models.BooleanField(verbose_name="Par défaut", default=False)
    
    # Audit
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Date de mise à jour")
    
    class Meta:
        verbose_name = "Configuration de tableau de bord"
        verbose_name_plural = "Configurations de tableaux de bord"
        ordering = ["-updated_at"]
        unique_together = ["dashboard_type", "user"]
    
    def __str__(self):
        user_name = self.user.username if self.user else "Global"
        return f"{self.dashboard_type} - {user_name}"


class NetworkTopology(models.Model):
    """Modèle pour les topologies réseau."""
    
    # Informations de base
    name = models.CharField(max_length=255, verbose_name="Nom de la topologie")
    description = models.TextField(verbose_name="Description", blank=True)
    topology_type = models.CharField(
        max_length=50, 
        verbose_name="Type de topologie",
        choices=[
            ('physical', 'Physique'),
            ('logical', 'Logique'),
            ('gns3_imported', 'Importé de GNS3'),
            ('custom', 'Personnalisé')
        ],
        default='physical'
    )
    
    # Relations
    devices = models.ManyToManyField(
        NetworkDevice,
        related_name="topologies",
        verbose_name="Équipements",
        blank=True
    )
    
    # Métadonnées de synchronisation
    gns3_project_id = models.CharField(max_length=255, verbose_name="ID Projet GNS3", blank=True)
    last_sync = models.DateTimeField(verbose_name="Dernière synchronisation", null=True, blank=True)
    is_active = models.BooleanField(verbose_name="Active", default=True)
    
    # Données de la topologie
    topology_data = models.JSONField(verbose_name="Données de topologie", null=True, blank=True)
    layout_data = models.JSONField(verbose_name="Données de mise en page", null=True, blank=True)
    
    # Audit
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Date de mise à jour")
    created_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        verbose_name="Créé par"
    )
    
    class Meta:
        verbose_name = "Topologie réseau"
        verbose_name_plural = "Topologies réseau"
        ordering = ["-updated_at"]
    
    def __str__(self):
        return f"{self.name} ({self.topology_type})" 