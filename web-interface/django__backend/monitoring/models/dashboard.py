"""
Modèles pour les tableaux de bord dans le système de surveillance.
"""

from django.db import models
from django.conf import settings


class Dashboard(models.Model):
    """
    Modèle pour les tableaux de bord de monitoring.
    """
    title = models.CharField(
        max_length=255,
        verbose_name='Titre'
    )
    description = models.TextField(
        blank=True,
        verbose_name='Description'
    )
    layout = models.JSONField(
        default=dict,
        verbose_name='Disposition'
    )  # Structure du tableau de bord
    is_default = models.BooleanField(
        default=False,
        verbose_name='Par défaut'
    )
    uid = models.CharField(
        max_length=100, 
        unique=True,
        verbose_name='Identifiant unique'
    )
    is_public = models.BooleanField(
        default=False,
        verbose_name='Public'
    )
    category = models.CharField(
        max_length=100, 
        blank=True, 
        null=True,
        verbose_name='Catégorie'
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='monitoring_dashboards',
        verbose_name='Propriétaire'
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
        return self.title
    
    class Meta:
        verbose_name = "Tableau de bord"
        verbose_name_plural = "Tableaux de bord"
        ordering = ['title']
        indexes = [
            models.Index(fields=['owner']),
            models.Index(fields=['is_default']),
            models.Index(fields=['is_public']),
        ]


class DashboardWidget(models.Model):
    """
    Widgets pour les tableaux de bord.
    """
    WIDGET_TYPES = [
        ('chart', 'Graphique'),
        ('gauge', 'Jauge'),
        ('table', 'Table'),
        ('status', 'Statut'),
        ('map', 'Carte'),
        ('text', 'Texte'),
        ('alert_list', 'Liste d\'alertes'),
        ('device_list', 'Liste d\'équipements'),
        ('metric_value', 'Valeur de métrique'),
        ('custom', 'Personnalisé')
    ]
    
    dashboard = models.ForeignKey(
        Dashboard, 
        on_delete=models.CASCADE, 
        related_name='widgets',
        verbose_name='Tableau de bord'
    )
    title = models.CharField(
        max_length=255,
        verbose_name='Titre'
    )
    widget_type = models.CharField(
        max_length=50, 
        choices=WIDGET_TYPES,
        verbose_name='Type de widget'
    )
    position = models.JSONField(
        default=dict,
        verbose_name='Position'
    )  # {"x": 0, "y": 0, "w": 6, "h": 4}
    config = models.JSONField(
        default=dict,
        verbose_name='Configuration'
    )
    data_source = models.JSONField(
        default=dict,
        verbose_name='Source de données'
    )  # Configuration de la source de données
    refresh_interval = models.IntegerField(
        default=60,  # En secondes
        verbose_name='Intervalle de rafraîchissement (secondes)'
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
        return f"{self.title} ({self.widget_type})"
    
    class Meta:
        verbose_name = "Widget de tableau de bord"
        verbose_name_plural = "Widgets de tableau de bord"
        ordering = ['dashboard', 'title']


class SavedView(models.Model):
    """
    Vues sauvegardées par les utilisateurs.
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
        related_name='saved_views',
        verbose_name='Utilisateur'
    )
    parameters = models.JSONField(
        default=dict,
        verbose_name='Paramètres'
    )
    view_type = models.CharField(
        max_length=50,
        verbose_name='Type de vue'
    )  # "devices", "alerts", "metrics", etc.
    is_default = models.BooleanField(
        default=False,
        verbose_name='Par défaut'
    )
    is_shared = models.BooleanField(
        default=False,
        verbose_name='Partagée'
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
        return f"{self.name} ({self.view_type})"
    
    class Meta:
        verbose_name = "Vue sauvegardée"
        verbose_name_plural = "Vues sauvegardées"
        ordering = ['user', 'name']
        unique_together = ('user', 'name', 'view_type')


class BusinessKPI(models.Model):
    """
    Indicateurs clés de performance métier.
    """
    name = models.CharField(
        max_length=255,
        verbose_name='Nom'
    )
    description = models.TextField(
        blank=True,
        verbose_name='Description'
    )
    formula = models.TextField(
        help_text="Expression pour calculer le KPI à partir de métriques",
        verbose_name='Formule'
    )
    target_value = models.FloatField(
        help_text="Valeur cible à atteindre",
        verbose_name='Valeur cible'
    )
    acceptable_range = models.FloatField(
        help_text="Plage acceptable autour de la valeur cible",
        verbose_name='Plage acceptable'
    )
    metrics_mapping = models.JSONField(
        default=dict, 
        help_text="Mapping entre variables et IDs de métriques",
        verbose_name='Mappage des métriques'
    )
    refresh_interval_seconds = models.IntegerField(
        default=300, 
        help_text="Intervalle de rafraîchissement en secondes",
        verbose_name='Intervalle de rafraîchissement (secondes)'
    )
    unit = models.CharField(
        max_length=50, 
        blank=True,
        verbose_name='Unité'
    )
    category = models.CharField(
        max_length=100, 
        blank=True,
        verbose_name='Catégorie'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='Actif'
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        null=True, 
        blank=True, 
        on_delete=models.SET_NULL, 
        related_name='business_kpis',
        verbose_name='Propriétaire'
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
        verbose_name = "KPI Métier"
        verbose_name_plural = "KPIs Métier"
        ordering = ['name']


class KPIHistory(models.Model):
    """
    Historique des valeurs calculées des KPIs.
    """
    STATUS_CHOICES = [
        ('excellent', 'Excellent'),
        ('good', 'Bon'),
        ('warning', 'Avertissement'),
        ('critical', 'Critique')
    ]
    
    kpi = models.ForeignKey(
        BusinessKPI, 
        on_delete=models.CASCADE, 
        related_name='history',
        verbose_name='KPI'
    )
    calculated_value = models.FloatField(
        verbose_name='Valeur calculée'
    )
    target_achievement = models.FloatField(
        help_text="Pourcentage d'atteinte de l'objectif",
        verbose_name='Atteinte de l\'objectif (%)'
    )
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES,
        verbose_name='Statut'
    )
    timestamp = models.DateTimeField(
        verbose_name='Horodatage'
    )
    calculation_details = models.JSONField(
        default=dict, 
        blank=True,
        verbose_name='Détails du calcul'
    )
    
    class Meta:
        verbose_name = "Historique KPI"
        verbose_name_plural = "Historiques KPI"
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['kpi', '-timestamp']),
            models.Index(fields=['timestamp']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.kpi.name}: {self.calculated_value} ({self.timestamp.strftime('%Y-%m-%d %H:%M:%S')})" 