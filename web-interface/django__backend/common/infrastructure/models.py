"""
Modèles abstraits de base pour standardiser la persistance des données dans le système.

Ce module définit des classes de base abstraites qui seront utilisées 
comme parents par les modèles concrets dans les différents modules du système.
Ces modèles fournissent des champs communs et des comportements standardisés.
"""
from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _


class BaseModel(models.Model):
    """
    Modèle de base avec des champs communs pour l'audit et les timestamps.
    
    Ce modèle abstrait fournit des champs pour suivre la création et les modifications
    des objets, ainsi que les utilisateurs qui ont effectué ces actions.
    """
    created_at = models.DateTimeField(
        _('Date de création'),
        auto_now_add=True,
        help_text=_('Date et heure de création de cet enregistrement')
    )
    updated_at = models.DateTimeField(
        _('Date de modification'),
        auto_now=True,
        help_text=_('Date et heure de dernière modification de cet enregistrement')
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='%(class)s_created',
        verbose_name=_('Créé par'),
        help_text=_('Utilisateur ayant créé cet enregistrement')
    )
    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='%(class)s_updated',
        verbose_name=_('Modifié par'),
        help_text=_('Utilisateur ayant modifié en dernier cet enregistrement')
    )

    class Meta:
        abstract = True
        ordering = ['-created_at']
        verbose_name = _('Entité de base')
        verbose_name_plural = _('Entités de base')
        
    def save(self, *args, **kwargs):
        """
        Méthode de sauvegarde surchargée pour assurer la cohérence 
        des champs de modification lors des mises à jour.
        """
        # L'utilisateur courant sera généralement passé par le code appelant
        # via le paramètre updated_by
        super().save(*args, **kwargs)
        
    def __str__(self):
        """Représentation textuelle par défaut basée sur l'ID."""
        return f"{self._meta.verbose_name} #{self.id}"


class BaseDeviceModel(BaseModel):
    """
    Modèle de base pour les équipements réseau.
    
    Ce modèle abstrait étend BaseModel en ajoutant les champs 
    spécifiques aux équipements réseau et autres dispositifs.
    """
    name = models.CharField(
        _('Nom'),
        max_length=255,
        help_text=_('Nom de l\'équipement')
    )
    description = models.TextField(
        _('Description'),
        blank=True,
        help_text=_('Description détaillée de l\'équipement')
    )
    is_active = models.BooleanField(
        _('Actif'),
        default=True,
        help_text=_('Indique si l\'équipement est actif dans le système')
    )
    ip_address = models.GenericIPAddressField(
        _('Adresse IP'),
        null=True, 
        blank=True,
        help_text=_('Adresse IP principale de l\'équipement')
    )
    location = models.CharField(
        _('Emplacement'),
        max_length=255,
        blank=True,
        help_text=_('Emplacement physique de l\'équipement')
    )

    class Meta:
        abstract = True
        ordering = ['name']
        verbose_name = _('Équipement de base')
        verbose_name_plural = _('Équipements de base')
        
    def __str__(self):
        """Représentation textuelle basée sur le nom."""
        return self.name


class AuditLogEntry(BaseModel):
    """
    Modèle pour enregistrer les actions importantes dans le système.
    
    Ce modèle permet de journaliser les actions des utilisateurs
    pour maintenir une piste d'audit complète.
    """
    ACTION_TYPES = [
        ('create', _('Création')),
        ('update', _('Modification')),
        ('delete', _('Suppression')),
        ('view', _('Consultation')),
        ('login', _('Connexion')),
        ('logout', _('Déconnexion')),
        ('other', _('Autre'))
    ]
    
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='audit_logs',
        verbose_name=_('Utilisateur')
    )
    action = models.CharField(
        _('Action'),
        max_length=50,
        choices=ACTION_TYPES
    )
    object_type = models.CharField(
        _('Type d\'objet'),
        max_length=255
    )
    object_id = models.CharField(
        _('ID de l\'objet'),
        max_length=50,
        blank=True
    )
    details = models.JSONField(
        _('Détails'),
        null=True,
        blank=True
    )
    ip_address = models.GenericIPAddressField(
        _('Adresse IP'),
        null=True, 
        blank=True
    )
    
    class Meta:
        verbose_name = _('Entrée de journal d\'audit')
        verbose_name_plural = _('Entrées de journal d\'audit')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'action']),
            models.Index(fields=['object_type', 'object_id']),
            models.Index(fields=['created_at'])
        ]
        
    def __str__(self):
        """Représentation textuelle détaillée."""
        action_dict = dict(self.ACTION_TYPES)
        action_label = action_dict.get(self.action, self.action)
        return f"{self.user.username if self.user else 'Système'} - {action_label} - {self.object_type} - {self.created_at}" 