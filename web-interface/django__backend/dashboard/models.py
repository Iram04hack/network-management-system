"""
Modèles de données pour le module Dashboard.

Ce fichier définit les modèles de données pour stocker
les configurations et préréglages du tableau de bord.
"""

import logging
import uuid
from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

logger = logging.getLogger(__name__)
User = get_user_model()


class DashboardPreset(models.Model):
    """
    Préréglage de tableau de bord.
    
    Ce modèle définit un préréglage de tableau de bord qui peut être
    appliqué à plusieurs utilisateurs.
    """
    
    name = models.CharField(
        max_length=100,
        verbose_name=_("Nom"),
        help_text=_("Nom du préréglage")
    )
    
    description = models.TextField(
        blank=True,
        verbose_name=_("Description"),
        help_text=_("Description du préréglage")
    )
    
    theme = models.CharField(
        max_length=20,
        default="light",
        verbose_name=_("Thème"),
        help_text=_("Thème visuel du tableau de bord")
    )
    
    layout = models.CharField(
        max_length=20,
        default="grid",
        verbose_name=_("Disposition"),
        help_text=_("Type de disposition des widgets")
    )
    
    refresh_interval = models.PositiveIntegerField(
        default=60,
        verbose_name=_("Intervalle de rafraîchissement"),
        help_text=_("Intervalle de rafraîchissement en secondes")
    )
    
    is_default = models.BooleanField(
        default=False,
        verbose_name=_("Par défaut"),
        help_text=_("Indique si ce préréglage est le préréglage par défaut")
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Date de création")
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Date de mise à jour")
    )
    
    class Meta:
        verbose_name = _("Préréglage de tableau de bord")
        verbose_name_plural = _("Préréglages de tableau de bord")
        ordering = ['-is_default', 'name']
    
    def __str__(self):
        return f"{self.name}" + (" (défaut)" if self.is_default else "")
    
    def save(self, *args, **kwargs):
        """
        Surcharge de la méthode save pour assurer qu'il n'y a qu'un seul
        préréglage par défaut.
        """
        if self.is_default:
            # Mettre à jour tous les autres préréglages par défaut
            DashboardPreset.objects.filter(is_default=True).exclude(pk=self.pk).update(is_default=False)
        
        super().save(*args, **kwargs)


class UserDashboardConfig(models.Model):
    """
    Configuration du tableau de bord d'un utilisateur.
    
    Ce modèle stocke les préférences et la configuration du tableau
    de bord pour un utilisateur spécifique.
    """
    
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='dashboard_config',
        verbose_name=_("Utilisateur"),
        help_text=_("Utilisateur associé à cette configuration")
    )
    
    theme = models.CharField(
        max_length=20,
        default="light",
        verbose_name=_("Thème"),
        help_text=_("Thème visuel du tableau de bord")
    )
    
    layout = models.CharField(
        max_length=20,
        default="grid",
        verbose_name=_("Disposition"),
        help_text=_("Type de disposition des widgets")
    )
    
    refresh_interval = models.PositiveIntegerField(
        default=60,
        verbose_name=_("Intervalle de rafraîchissement"),
        help_text=_("Intervalle de rafraîchissement en secondes")
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Date de création")
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Date de mise à jour")
    )
    
    class Meta:
        verbose_name = _("Configuration de tableau de bord utilisateur")
        verbose_name_plural = _("Configurations de tableau de bord utilisateur")
    
    def __str__(self):
        return f"Configuration de {self.user.username}"


class DashboardWidget(models.Model):
    """
    Widget de tableau de bord.
    
    Ce modèle définit un widget qui peut être placé sur le tableau de bord
    d'un utilisateur ou dans un préréglage.
    """
    
    WIDGET_TYPES = [
        ('system_health', _('Santé du système')),
        ('network_overview', _('Aperçu réseau')),
        ('alerts', _('Alertes')),
        ('device_status', _('État des équipements')),
        ('interface_status', _('État des interfaces')),
        ('performance_chart', _('Graphique de performance')),
        ('topology', _('Topologie')),
        ('custom_chart', _('Graphique personnalisé')),
    ]
    
    config = models.ForeignKey(
        UserDashboardConfig,
        on_delete=models.CASCADE,
        related_name='widgets',
        null=True,
        blank=True,
        verbose_name=_("Configuration utilisateur"),
        help_text=_("Configuration utilisateur associée à ce widget")
    )
    
    preset = models.ForeignKey(
        DashboardPreset,
        on_delete=models.CASCADE,
        related_name='widgets',
        null=True,
        blank=True,
        verbose_name=_("Préréglage"),
        help_text=_("Préréglage associé à ce widget")
    )
    
    widget_type = models.CharField(
        max_length=50,
        choices=WIDGET_TYPES,
        verbose_name=_("Type de widget"),
        help_text=_("Type de widget à afficher")
    )
    
    position_x = models.PositiveSmallIntegerField(
        default=0,
        verbose_name=_("Position X"),
        help_text=_("Position horizontale du widget")
    )
    
    position_y = models.PositiveSmallIntegerField(
        default=0,
        verbose_name=_("Position Y"),
        help_text=_("Position verticale du widget")
    )
    
    width = models.PositiveSmallIntegerField(
        default=1,
        verbose_name=_("Largeur"),
        help_text=_("Largeur du widget en unités de grille")
    )
    
    height = models.PositiveSmallIntegerField(
        default=1,
        verbose_name=_("Hauteur"),
        help_text=_("Hauteur du widget en unités de grille")
    )
    
    settings = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_("Paramètres"),
        help_text=_("Paramètres spécifiques au widget")
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Actif"),
        help_text=_("Indique si le widget est actif")
    )

    class Meta:
        verbose_name = _("Widget de tableau de bord")
        verbose_name_plural = _("Widgets de tableau de bord")
        ordering = ['position_y', 'position_x']
    
    def __str__(self):
        widget_type_display = dict(self.WIDGET_TYPES).get(self.widget_type, self.widget_type)
        return f"{widget_type_display} ({self.position_x}, {self.position_y})"
    
    def clean(self):
        """
        Valide que le widget est associé soit à une configuration utilisateur,
        soit à un préréglage, mais pas aux deux.
        """
        from django.core.exceptions import ValidationError
        
        if self.config is None and self.preset is None:
            raise ValidationError(_("Le widget doit être associé à une configuration utilisateur ou à un préréglage."))
        
        if self.config is not None and self.preset is not None:
            raise ValidationError(_("Le widget ne peut pas être associé à la fois à une configuration utilisateur et à un préréglage."))


class CustomDashboard(models.Model):
    """Modèle pour les tableaux de bord personnalisés par l'utilisateur."""
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name=_("Identifiant")
    )
    
    name = models.CharField(
        max_length=100,
        verbose_name=_("Nom")
    )
    
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name=_("Description")
    )
    
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='dashboards',
        verbose_name=_("Propriétaire")
    )
    
    layout = models.JSONField(
        default=dict,
        verbose_name=_("Mise en page")
    )
    
    is_default = models.BooleanField(
        default=False,
        verbose_name=_("Tableau de bord par défaut")
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Date de création")
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Dernière mise à jour")
    )
    
    is_public = models.BooleanField(
        default=False,
        verbose_name=_("Public")
    )
    
    class Meta:
        verbose_name = _("Tableau de bord personnalisé")
        verbose_name_plural = _("Tableaux de bord personnalisés")
        ordering = ['-updated_at']
    
    def __str__(self):
        return f"{self.name} ({self.owner.username})"
    
    def save(self, *args, **kwargs):
        """Validation et sauvegarde avec gestion des tableaux par défaut."""
        if self.is_default:
            # S'assurer qu'il n'y a qu'un seul tableau de bord par défaut par utilisateur
            CustomDashboard.objects.filter(
                owner=self.owner,
                is_default=True
            ).update(is_default=False)
        
        super().save(*args, **kwargs)
    
    def to_dict(self):
        """Convertit le modèle en dictionnaire pour l'API."""
        return {
            'id': str(self.id),
            'name': self.name,
            'description': self.description,
            'owner': self.owner.username,
            'layout': self.layout,
            'is_default': self.is_default,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'is_public': self.is_public,
        }


class DashboardViewLog(models.Model):
    """
    Journal des vues des tableaux de bord.
    
    Ce modèle enregistre chaque vue de tableau de bord
    pour l'analyse d'utilisation et les statistiques.
    """
    
    id = models.BigAutoField(
        primary_key=True,
        verbose_name=_("Identifiant")
    )
    
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='dashboard_views',
        verbose_name=_("Utilisateur")
    )
    
    dashboard = models.ForeignKey(
        CustomDashboard,
        on_delete=models.SET_NULL,
        null=True,
        related_name='view_logs',
        verbose_name=_("Tableau de bord")
    )
    
    timestamp = models.DateTimeField(
        default=timezone.now,
        verbose_name=_("Horodatage")
    )
    
    session_id = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name=_("Identifiant de session")
    )
    
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name=_("Adresse IP")
    )
    
    user_agent = models.TextField(
        null=True,
        blank=True,
        verbose_name=_("User Agent")
    )
    
    duration = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_("Durée (secondes)")
    )
    
    class Meta:
        verbose_name = _("Journal de vue de tableau de bord")
        verbose_name_plural = _("Journal des vues de tableaux de bord")
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['-timestamp']),
            models.Index(fields=['user']),
            models.Index(fields=['dashboard']),
            models.Index(fields=['session_id']),
        ]
    
    def __str__(self):
        user = self.user.username if self.user else 'Anonymous'
        dashboard = self.dashboard.name if self.dashboard else 'Custom'
        return f"{user} - {dashboard} - {self.timestamp}" 