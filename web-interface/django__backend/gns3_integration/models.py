"""
Modèles pour l'intégration GNS3.

Ce module définit les modèles ORM Django pour persister les données de l'intégration GNS3
avec le système de gestion de réseau.
"""

from django.db import models
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password, check_password
from network_management.infrastructure.models import Topology
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _

class GNS3Config(models.Model):
    """Configuration globale pour l'intégration GNS3."""
    key = models.CharField(_("Clé"), max_length=255, unique=True)
    value = models.JSONField(_("Valeur"))
    description = models.TextField(_("Description"), blank=True)
    created_at = models.DateTimeField(_("Date de création"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Date de modification"), auto_now=True)
    
    def __str__(self):
        return f"{self.key}"
    
    class Meta:
        verbose_name = _("Configuration GNS3")
        verbose_name_plural = _("Configurations GNS3")
        ordering = ['key']

class Server(models.Model):
    """Serveur GNS3."""
    name = models.CharField(_("Nom"), max_length=255)
    host = models.CharField(_("Hôte"), max_length=255)
    port = models.PositiveIntegerField(
        _("Port"), 
        default=3080, 
        validators=[MinValueValidator(1), MaxValueValidator(65535)]
    )
    protocol = models.CharField(
        _("Protocole"), 
        max_length=5, 
        choices=[('http', 'HTTP'), ('https', 'HTTPS')], 
        default='http'
    )
    username = models.CharField(_("Nom d'utilisateur"), max_length=255, blank=True)
    password = models.CharField(_("Mot de passe"), max_length=255, blank=True)
    verify_ssl = models.BooleanField(_("Vérifier SSL"), default=True)
    is_active = models.BooleanField(_("Actif"), default=True)
    timeout = models.PositiveIntegerField(
        _("Timeout (secondes)"),
        default=30,
        validators=[MinValueValidator(1), MaxValueValidator(300)]
    )
    created_at = models.DateTimeField(_("Date de création"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Date de modification"), auto_now=True)
    
    def set_password(self, raw_password):
        """Hash le mot de passe avant de le stocker"""
        if raw_password:
            self.password = make_password(raw_password)
        
    def check_password(self, raw_password):
        """Vérifie si le mot de passe est correct"""
        if not self.password:
            return False
        return check_password(raw_password, self.password)
    
    def save(self, *args, **kwargs):
        if self._state.adding and self.password and not self.password.startswith('pbkdf2_'):
            # Si c'est une nouvelle instance avec un mot de passe non hashé
            self.set_password(self.password)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.name} ({self.host}:{self.port})"
    
    class Meta:
        verbose_name = _("Serveur GNS3")
        verbose_name_plural = _("Serveurs GNS3")
        ordering = ['name']

class Project(models.Model):
    """Projet GNS3."""
    STATUS_CHOICES = [
        ('open', _('Ouvert')),
        ('closed', _('Fermé')),
        ('suspended', _('Suspendu'))
    ]
    
    server = models.ForeignKey(
        Server, 
        verbose_name=_("Serveur"),
        on_delete=models.CASCADE, 
        related_name='projects'
    )
    name = models.CharField(_("Nom"), max_length=255)
    project_id = models.CharField(_("ID GNS3"), max_length=255, unique=True)
    status = models.CharField(
        _("Statut"),
        max_length=50, 
        choices=STATUS_CHOICES,
        default='closed'
    )
    description = models.TextField(_("Description"), blank=True)
    path = models.CharField(_("Chemin"), max_length=512, blank=True)
    filename = models.CharField(_("Nom de fichier"), max_length=255, blank=True)
    auto_start = models.BooleanField(_("Démarrage automatique"), default=False)
    auto_close = models.BooleanField(_("Fermeture automatique"), default=True)
    created_by = models.ForeignKey(
        User, 
        verbose_name=_("Créé par"),
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='gns3_projects'
    )
    created_at = models.DateTimeField(_("Date de création"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Date de modification"), auto_now=True)
    
    def __str__(self):
        return f"{self.name} ({self.project_id})"
    
    class Meta:
        verbose_name = _("Projet GNS3")
        verbose_name_plural = _("Projets GNS3")
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['project_id']),
            models.Index(fields=['name']),
        ]

class Template(models.Model):
    """Template d'appareil GNS3."""
    TEMPLATE_TYPES = [
        ('qemu', 'QEMU VM'),
        ('docker', 'Docker Container'),
        ('dynamips', 'Dynamips Router'),
        ('iou', 'IOU Device'),
        ('vpcs', 'VPCS'),
        ('cloud', 'Cloud'),
        ('ethernet_switch', 'Ethernet Switch'),
        ('ethernet_hub', 'Ethernet Hub'),
        ('nat', 'NAT'),
        ('custom', 'Custom')
    ]
    
    server = models.ForeignKey(
        Server, 
        verbose_name=_("Serveur"),
        on_delete=models.CASCADE, 
        related_name='templates'
    )
    name = models.CharField(_("Nom"), max_length=255)
    template_id = models.CharField(_("ID GNS3"), max_length=255)
    template_type = models.CharField(
        _("Type de template"), 
        max_length=50, 
        choices=TEMPLATE_TYPES
    )
    builtin = models.BooleanField(_("Template intégré"), default=False)
    symbol = models.CharField(_("Symbole"), max_length=255, blank=True)
    properties = models.JSONField(_("Propriétés"), default=dict)
    compute_id = models.CharField(_("ID de compute"), max_length=255, default="local")
    created_at = models.DateTimeField(_("Date de création"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Date de modification"), auto_now=True)
    
    def __str__(self):
        return f"{self.name} ({self.template_type})"
    
    class Meta:
        verbose_name = _("Template GNS3")
        verbose_name_plural = _("Templates GNS3")
        ordering = ['name']
        unique_together = [['server', 'template_id']]

class Node(models.Model):
    """Nœud (appareil) dans un projet GNS3."""
    STATUS_CHOICES = [
        ('started', _('Démarré')),
        ('stopped', _('Arrêté')),
        ('suspended', _('Suspendu')),
        ('unknown', _('Inconnu'))
    ]
    
    NODE_TYPES = [
        ('vpcs', 'VPCS'),
        ('qemu', 'QEMU VM'),
        ('docker', 'Docker Container'),
        ('dynamips', 'Dynamips Router'),
        ('iou', 'IOU Device'),
        ('ethernet_switch', 'Ethernet Switch'),
        ('ethernet_hub', 'Ethernet Hub'),
        ('cloud', 'Cloud'),
        ('nat', 'NAT'),
        ('custom', 'Custom')
    ]
    
    project = models.ForeignKey(
        Project, 
        verbose_name=_("Projet"),
        on_delete=models.CASCADE, 
        related_name='nodes'
    )
    name = models.CharField(_("Nom"), max_length=255)
    node_id = models.CharField(_("ID GNS3"), max_length=255)
    node_type = models.CharField(
        _("Type de nœud"), 
        max_length=50, 
        choices=NODE_TYPES
    )
    template = models.ForeignKey(
        Template, 
        verbose_name=_("Template"),
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='nodes'
    )
    status = models.CharField(
        _("Statut"),
        max_length=50, 
        choices=STATUS_CHOICES,
        default='stopped'
    )
    console_type = models.CharField(_("Type de console"), max_length=50, blank=True)
    console_port = models.IntegerField(_("Port console"), null=True, blank=True)
    x = models.IntegerField(_("Position X"), default=0)
    y = models.IntegerField(_("Position Y"), default=0)
    symbol = models.CharField(_("Symbole"), max_length=255, blank=True)
    properties = models.JSONField(_("Propriétés"), default=dict, blank=True)
    compute_id = models.CharField(_("ID de compute"), max_length=255, default="local")
    created_at = models.DateTimeField(_("Date de création"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Date de modification"), auto_now=True)
    
    def __str__(self):
        return f"{self.name} ({self.node_type}) - {self.project.name}"
    
    class Meta:
        verbose_name = _("Nœud GNS3")
        verbose_name_plural = _("Nœuds GNS3")
        ordering = ['project', 'name']
        unique_together = [['project', 'node_id']]
        indexes = [
            models.Index(fields=['node_id']),
            models.Index(fields=['status']),
        ]

class Link(models.Model):
    """Lien entre nœuds dans un projet GNS3."""
    STATUS_CHOICES = [
        ('started', _('Démarré')),
        ('stopped', _('Arrêté')),
        ('suspended', _('Suspendu')),
    ]
    
    LINK_TYPES = [
        ('ethernet', _('Ethernet')),
        ('serial', _('Série')),
        ('custom', _('Personnalisé')),
    ]
    
    project = models.ForeignKey(
        Project, 
        verbose_name=_("Projet"),
        on_delete=models.CASCADE, 
        related_name='links'
    )
    link_id = models.CharField(_("ID GNS3"), max_length=255, unique=True)
    link_type = models.CharField(
        _("Type de lien"), 
        max_length=50, 
        choices=LINK_TYPES,
        default='ethernet'
    )
    source_node = models.ForeignKey(
        Node, 
        verbose_name=_("Nœud source"),
        on_delete=models.CASCADE, 
        related_name='outgoing_links'
    )
    source_port = models.IntegerField(_("Port source"))
    destination_node = models.ForeignKey(
        Node, 
        verbose_name=_("Nœud destination"),
        on_delete=models.CASCADE, 
        related_name='incoming_links'
    )
    destination_port = models.IntegerField(_("Port destination"))
    status = models.CharField(
        _("Statut"),
        max_length=50, 
        choices=STATUS_CHOICES,
        default='started'
    )
    properties = models.JSONField(_("Propriétés"), default=dict, blank=True)
    created_at = models.DateTimeField(_("Date de création"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Date de modification"), auto_now=True)
    
    def __str__(self):
        return f"{self.source_node.name}:{self.source_port} -> {self.destination_node.name}:{self.destination_port}"
    
    class Meta:
        verbose_name = _("Lien GNS3")
        verbose_name_plural = _("Liens GNS3")
        ordering = ['project', 'source_node__name']
        indexes = [
            models.Index(fields=['link_id']),
        ]

class Snapshot(models.Model):
    """Snapshot d'un projet GNS3."""
    project = models.ForeignKey(
        Project, 
        verbose_name=_("Projet"),
        on_delete=models.CASCADE, 
        related_name='snapshots'
    )
    name = models.CharField(_("Nom"), max_length=255)
    snapshot_id = models.CharField(_("ID GNS3"), max_length=255)
    description = models.TextField(_("Description"), blank=True)
    created_by = models.ForeignKey(
        User, 
        verbose_name=_("Créé par"),
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='gns3_snapshots'
    )
    created_at = models.DateTimeField(_("Date de création"), auto_now_add=True)
    
    def __str__(self):
        return f"{self.name} ({self.project.name})"
    
    class Meta:
        verbose_name = _("Snapshot GNS3")
        verbose_name_plural = _("Snapshots GNS3")
        ordering = ['-created_at']
        unique_together = [['project', 'snapshot_id']]

class Script(models.Model):
    """Script d'automatisation pour GNS3."""
    SCRIPT_TYPES = [
        ('bash', 'Bash Shell'),
        ('python', 'Python'),
        ('expect', 'Expect Script'),
        ('cisco_ios', 'Cisco IOS Commands'),
        ('juniper_junos', 'Juniper JunOS Commands'),
        ('custom', 'Custom')
    ]
    
    name = models.CharField(_("Nom"), max_length=255)
    script_type = models.CharField(
        _("Type de script"), 
        max_length=50, 
        choices=SCRIPT_TYPES
    )
    content = models.TextField(_("Contenu"))
    description = models.TextField(_("Description"), blank=True)
    node_type_filter = models.CharField(
        _("Filtre de type de nœud"), 
        max_length=50, 
        blank=True, 
        help_text=_("Type de nœud sur lequel ce script peut être exécuté")
    )
    is_template = models.BooleanField(
        _("Template"), 
        default=False, 
        help_text=_("Script template avec variables à remplacer")
    )
    template_variables = models.JSONField(
        _("Variables de template"), 
        default=dict, 
        blank=True, 
        help_text=_("Variables disponibles dans le template")
    )
    created_by = models.ForeignKey(
        User, 
        verbose_name=_("Créé par"),
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='gns3_scripts'
    )
    created_at = models.DateTimeField(_("Date de création"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Date de modification"), auto_now=True)
    
    def __str__(self):
        return f"{self.name} ({self.script_type})"
    
    class Meta:
        verbose_name = _("Script GNS3")
        verbose_name_plural = _("Scripts GNS3")
        ordering = ['name']

class ScriptExecution(models.Model):
    """Exécution d'un script sur un nœud GNS3."""
    STATUS_CHOICES = [
        ('pending', _('En attente')),
        ('running', _('En cours')),
        ('completed', _('Terminé')),
        ('failed', _('Échoué')),
        ('cancelled', _('Annulé'))
    ]
    
    script = models.ForeignKey(
        Script, 
        verbose_name=_("Script"),
        on_delete=models.CASCADE, 
        related_name='executions'
    )
    project = models.ForeignKey(
        Project, 
        verbose_name=_("Projet"),
        on_delete=models.CASCADE, 
        related_name='script_executions'
    )
    node = models.ForeignKey(
        Node, 
        verbose_name=_("Nœud"),
        on_delete=models.CASCADE, 
        related_name='script_executions'
    )
    status = models.CharField(
        _("Statut"),
        max_length=50, 
        choices=STATUS_CHOICES,
        default='pending'
    )
    parameters = models.JSONField(_("Paramètres"), default=dict, blank=True)
    output = models.TextField(_("Sortie"), blank=True)
    error_message = models.TextField(_("Message d'erreur"), blank=True)
    start_time = models.DateTimeField(_("Heure de début"), null=True, blank=True)
    end_time = models.DateTimeField(_("Heure de fin"), null=True, blank=True)
    created_by = models.ForeignKey(
        User, 
        verbose_name=_("Créé par"),
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='script_executions'
    )
    created_at = models.DateTimeField(_("Date de création"), auto_now_add=True)
    
    def __str__(self):
        return f"{self.script.name} sur {self.node.name} ({self.status})"
    
    class Meta:
        verbose_name = _("Exécution de script")
        verbose_name_plural = _("Exécutions de scripts")
        ordering = ['-created_at']

class Workflow(models.Model):
    """Workflow d'automatisation GNS3."""
    name = models.CharField(_("Nom"), max_length=255)
    description = models.TextField(_("Description"), blank=True)
    steps = models.JSONField(_("Étapes"), help_text=_("Définition des étapes du workflow"))
    is_template = models.BooleanField(
        _("Template"), 
        default=False, 
        help_text=_("Workflow template avec variables à remplacer")
    )
    template_variables = models.JSONField(
        _("Variables de template"), 
        default=dict, 
        blank=True, 
        help_text=_("Variables disponibles dans le template")
    )
    created_by = models.ForeignKey(
        User, 
        verbose_name=_("Créé par"),
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='gns3_workflows'
    )
    created_at = models.DateTimeField(_("Date de création"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Date de modification"), auto_now=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = _("Workflow GNS3")
        verbose_name_plural = _("Workflows GNS3")
        ordering = ['name']

class WorkflowExecution(models.Model):
    """Exécution d'un workflow sur un projet GNS3."""
    STATUS_CHOICES = [
        ('pending', _('En attente')),
        ('running', _('En cours')),
        ('completed', _('Terminé')),
        ('failed', _('Échoué')),
        ('cancelled', _('Annulé'))
    ]
    
    workflow = models.ForeignKey(
        Workflow, 
        verbose_name=_("Workflow"),
        on_delete=models.CASCADE, 
        related_name='executions'
    )
    project = models.ForeignKey(
        Project, 
        verbose_name=_("Projet"),
        on_delete=models.CASCADE, 
        related_name='workflow_executions'
    )
    status = models.CharField(
        _("Statut"),
        max_length=50, 
        choices=STATUS_CHOICES,
        default='pending'
    )
    parameters = models.JSONField(_("Paramètres"), default=dict, blank=True)
    results = models.JSONField(_("Résultats"), default=dict, blank=True)
    current_step = models.IntegerField(_("Étape courante"), default=0)
    error_message = models.TextField(_("Message d'erreur"), blank=True)
    start_time = models.DateTimeField(_("Heure de début"), null=True, blank=True)
    end_time = models.DateTimeField(_("Heure de fin"), null=True, blank=True)
    created_by = models.ForeignKey(
        User, 
        verbose_name=_("Créé par"),
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='workflow_executions'
    )
    created_at = models.DateTimeField(_("Date de création"), auto_now_add=True)
    
    def __str__(self):
        return f"{self.workflow.name} sur {self.project.name} ({self.status})"
    
    class Meta:
        verbose_name = _("Exécution de workflow")
        verbose_name_plural = _("Exécutions de workflows")
        ordering = ['-created_at'] 