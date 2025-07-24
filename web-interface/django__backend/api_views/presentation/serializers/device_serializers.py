"""
Sérialiseurs pour la gestion d'équipements réseau.

Ce module contient les sérialiseurs spécialisés pour la validation et transformation
des données de gestion d'équipements réseau.
"""

from typing import Dict, Any, List, Optional
from rest_framework import serializers
from rest_framework.exceptions import ValidationError as DRFValidationError

from .base_serializers import BaseAPISerializer, FilterSerializer


class DeviceCreationSerializer(BaseAPISerializer):
    """
    Sérialiseur pour la création d'équipements.
    """
    name = serializers.CharField(
        max_length=100,
        help_text="Nom de l'équipement"
    )
    
    ip_address = serializers.IPAddressField(
        help_text="Adresse IP de l'équipement"
    )
    
    device_type = serializers.ChoiceField(
        choices=[
            ('router', 'Routeur'),
            ('switch', 'Commutateur'),
            ('firewall', 'Pare-feu'),
            ('server', 'Serveur'),
            ('workstation', 'Poste de travail'),
            ('access_point', 'Point d\'accès WiFi'),
            ('printer', 'Imprimante'),
            ('storage', 'Stockage'),
            ('load_balancer', 'Répartiteur de charge'),
            ('other', 'Autre')
        ],
        help_text="Type d'équipement"
    )
    
    manufacturer = serializers.CharField(
        max_length=50,
        required=False,
        allow_blank=True,
        help_text="Fabricant de l'équipement"
    )
    
    model = serializers.CharField(
        max_length=50,
        required=False,
        allow_blank=True,
        help_text="Modèle de l'équipement"
    )
    
    serial_number = serializers.CharField(
        max_length=100,
        required=False,
        allow_blank=True,
        help_text="Numéro de série"
    )
    
    mac_address = serializers.CharField(
        max_length=17,
        required=False,
        allow_blank=True,
        help_text="Adresse MAC principale"
    )
    
    location = serializers.CharField(
        max_length=200,
        required=False,
        allow_blank=True,
        help_text="Emplacement physique"
    )
    
    description = serializers.CharField(
        max_length=500,
        required=False,
        allow_blank=True,
        help_text="Description de l'équipement"
    )
    
    hostname = serializers.CharField(
        max_length=100,
        required=False,
        allow_blank=True,
        help_text="Nom d'hôte"
    )
    
    os_name = serializers.CharField(
        max_length=50,
        required=False,
        allow_blank=True,
        help_text="Système d'exploitation"
    )
    
    os_version = serializers.CharField(
        max_length=50,
        required=False,
        allow_blank=True,
        help_text="Version du système d'exploitation"
    )
    
    credentials = serializers.DictField(
        required=False,
        help_text="Identifiants d'accès à l'équipement"
    )
    
    monitoring_enabled = serializers.BooleanField(
        default=True,
        help_text="Surveillance activée"
    )
    
    snmp_community = serializers.CharField(
        max_length=100,
        required=False,
        allow_blank=True,
        help_text="Communauté SNMP"
    )
    
    snmp_version = serializers.ChoiceField(
        choices=[('1', 'v1'), ('2c', 'v2c'), ('3', 'v3')],
        required=False,
        help_text="Version SNMP"
    )
    
    management_protocols = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        help_text="Protocoles de gestion supportés"
    )
    
    ports = serializers.ListField(
        child=serializers.DictField(),
        required=False,
        help_text="Configuration des ports"
    )
    
    tags = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        help_text="Tags pour la classification"
    )
    
    def validate_mac_address(self, value):
        """Valide le format de l'adresse MAC."""
        if not value:
            return value
            
        import re
        mac_pattern = r'^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$'
        if not re.match(mac_pattern, value):
            raise DRFValidationError(
                "Format d'adresse MAC invalide. Utilisez XX:XX:XX:XX:XX:XX ou XX-XX-XX-XX-XX-XX"
            )
        
        return value.upper()
    
    def validate_credentials(self, value):
        """Valide les identifiants."""
        if not value:
            return value
        
        if 'username' in value and not value['username']:
            raise DRFValidationError("Le nom d'utilisateur ne peut pas être vide")
        
        # Validation des protocoles requis
        if 'ssh' in value:
            ssh_config = value['ssh']
            if not isinstance(ssh_config, dict):
                raise DRFValidationError("Configuration SSH doit être un objet")
            
            if 'port' in ssh_config:
                port = ssh_config['port']
                if not isinstance(port, int) or not (1 <= port <= 65535):
                    raise DRFValidationError("Port SSH invalide")
        
        return value
    
    def validate_ports(self, value):
        """Valide la configuration des ports."""
        if not value:
            return value
        
        for i, port in enumerate(value):
            if 'number' not in port:
                raise DRFValidationError(f"Port {i}: numéro requis")
            
            port_num = port.get('number')
            if not isinstance(port_num, int) or port_num < 1:
                raise DRFValidationError(f"Port {i}: numéro invalide")
            
            if 'type' in port:
                valid_types = ['ethernet', 'serial', 'console', 'usb', 'fiber', 'wireless']
                if port['type'] not in valid_types:
                    raise DRFValidationError(
                        f"Port {i}: type '{port['type']}' invalide. "
                        f"Types autorisés: {valid_types}"
                    )
        
        return value


class DeviceUpdateSerializer(DeviceCreationSerializer):
    """
    Sérialiseur pour la mise à jour d'équipements.
    Hérite de DeviceCreationSerializer mais tous les champs sont optionnels.
    """
    name = serializers.CharField(
        max_length=100,
        required=False,
        help_text="Nom de l'équipement"
    )
    
    ip_address = serializers.IPAddressField(
        required=False,
        help_text="Adresse IP de l'équipement"
    )
    
    device_type = serializers.ChoiceField(
        choices=[
            ('router', 'Routeur'),
            ('switch', 'Commutateur'),
            ('firewall', 'Pare-feu'),
            ('server', 'Serveur'),
            ('workstation', 'Poste de travail'),
            ('access_point', 'Point d\'accès WiFi'),
            ('printer', 'Imprimante'),
            ('storage', 'Stockage'),
            ('load_balancer', 'Répartiteur de charge'),
            ('other', 'Autre')
        ],
        required=False,
        help_text="Type d'équipement"
    )


class DeviceDetailSerializer(BaseAPISerializer):
    """
    Sérialiseur pour les détails complets d'un équipement.
    """
    id = serializers.UUIDField(read_only=True)
    name = serializers.CharField()
    ip_address = serializers.IPAddressField()
    device_type = serializers.CharField()
    manufacturer = serializers.CharField(required=False)
    model = serializers.CharField(required=False)
    serial_number = serializers.CharField(required=False)
    mac_address = serializers.CharField(required=False)
    location = serializers.CharField(required=False)
    description = serializers.CharField(required=False)
    hostname = serializers.CharField(required=False)
    
    # Informations système
    os_name = serializers.CharField(required=False)
    os_version = serializers.CharField(required=False)
    firmware_version = serializers.CharField(required=False)
    uptime = serializers.IntegerField(required=False)
    
    # État et statut
    status = serializers.CharField()
    is_active = serializers.BooleanField()
    is_virtual = serializers.BooleanField()
    monitoring_enabled = serializers.BooleanField()
    last_seen = serializers.DateTimeField(required=False)
    
    # Configuration réseau
    interfaces = serializers.ListField(
        child=serializers.DictField(),
        required=False,
        help_text="Interfaces réseau"
    )
    
    routes = serializers.ListField(
        child=serializers.DictField(),
        required=False,
        help_text="Table de routage"
    )
    
    # Métriques en temps réel
    cpu_usage = serializers.FloatField(required=False)
    memory_usage = serializers.FloatField(required=False)
    disk_usage = serializers.FloatField(required=False)
    temperature = serializers.FloatField(required=False)
    
    # Configuration et historique
    configurations = serializers.ListField(
        child=serializers.DictField(),
        required=False,
        help_text="Historique des configurations"
    )
    
    alerts = serializers.ListField(
        child=serializers.DictField(),
        required=False,
        help_text="Alertes actives"
    )
    
    # Métadonnées
    tags = serializers.ListField(
        child=serializers.CharField(),
        required=False
    )
    
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
    created_by = serializers.CharField(read_only=True)
    
    class Meta:
        include_metadata = True


class DeviceListSerializer(BaseAPISerializer):
    """
    Sérialiseur pour la liste des équipements (vue simplifiée).
    """
    id = serializers.UUIDField(read_only=True)
    name = serializers.CharField()
    ip_address = serializers.IPAddressField()
    device_type = serializers.CharField()
    manufacturer = serializers.CharField(required=False)
    model = serializers.CharField(required=False)
    location = serializers.CharField(required=False)
    status = serializers.CharField()
    is_active = serializers.BooleanField()
    monitoring_enabled = serializers.BooleanField()
    last_seen = serializers.DateTimeField(required=False)
    
    # Métriques simples
    cpu_usage = serializers.FloatField(required=False)
    memory_usage = serializers.FloatField(required=False)
    alert_count = serializers.IntegerField(required=False)
    
    created_at = serializers.DateTimeField(read_only=True)


class DeviceManagementSerializer(BaseAPISerializer):
    """
    Sérialiseur pour les opérations de gestion d'équipements.
    """
    action = serializers.ChoiceField(
        choices=[
            ('restart', 'Redémarrer'),
            ('shutdown', 'Arrêter'),
            ('backup_config', 'Sauvegarder la configuration'),
            ('restore_config', 'Restaurer la configuration'),
            ('update_firmware', 'Mettre à jour le firmware'),
            ('scan_interfaces', 'Scanner les interfaces'),
            ('collect_metrics', 'Collecter les métriques'),
            ('test_connectivity', 'Tester la connectivité'),
            ('sync_time', 'Synchroniser l\'heure'),
            ('clear_logs', 'Vider les logs')
        ],
        help_text="Action à effectuer"
    )
    
    parameters = serializers.DictField(
        required=False,
        help_text="Paramètres pour l'action"
    )
    
    target_devices = serializers.ListField(
        child=serializers.UUIDField(),
        help_text="Liste des IDs d'équipements cibles"
    )
    
    schedule_at = serializers.DateTimeField(
        required=False,
        help_text="Programmer l'exécution à une heure spécifique"
    )
    
    force = serializers.BooleanField(
        default=False,
        help_text="Forcer l'exécution même en cas d'avertissements"
    )
    
    notification_email = serializers.EmailField(
        required=False,
        help_text="Email de notification des résultats"
    )
    
    def validate_parameters(self, value):
        """Valide les paramètres selon l'action."""
        if not value:
            return value
        
        action = self.initial_data.get('action')
        
        if action == 'restore_config':
            if 'config_id' not in value:
                raise DRFValidationError(
                    "Parameter 'config_id' requis pour restore_config"
                )
        
        elif action == 'update_firmware':
            required_params = ['firmware_url', 'version']
            for param in required_params:
                if param not in value:
                    raise DRFValidationError(
                        f"Parameter '{param}' requis pour update_firmware"
                    )
        
        elif action == 'backup_config':
            if 'backup_name' in value:
                name = value['backup_name']
                if not isinstance(name, str) or len(name.strip()) == 0:
                    raise DRFValidationError("backup_name doit être une chaîne non vide")
        
        return value
    
    def validate_target_devices(self, value):
        """Valide la liste des équipements cibles."""
        if not value:
            raise DRFValidationError("Au moins un équipement cible requis")
        
        if len(value) > 50:
            raise DRFValidationError("Maximum 50 équipements par opération")
        
        # Vérifier l'unicité
        if len(set(value)) != len(value):
            raise DRFValidationError("IDs d'équipements dupliqués")
        
        return value


class DeviceConfigurationSerializer(BaseAPISerializer):
    """
    Sérialiseur pour les configurations d'équipements.
    """
    id = serializers.UUIDField(read_only=True)
    device_id = serializers.UUIDField()
    name = serializers.CharField(max_length=100)
    description = serializers.CharField(required=False, allow_blank=True)
    version = serializers.CharField(max_length=20)
    
    configuration_type = serializers.ChoiceField(
        choices=[
            ('running', 'Configuration courante'),
            ('startup', 'Configuration de démarrage'),
            ('backup', 'Sauvegarde'),
            ('template', 'Modèle'),
            ('candidate', 'Configuration candidate')
        ],
        default='backup'
    )
    
    content = serializers.CharField(
        help_text="Contenu de la configuration"
    )
    
    format = serializers.ChoiceField(
        choices=[
            ('text', 'Texte brut'),
            ('json', 'JSON'),
            ('xml', 'XML'),
            ('yaml', 'YAML')
        ],
        default='text'
    )
    
    size = serializers.IntegerField(read_only=True)
    checksum = serializers.CharField(read_only=True)
    
    is_active = serializers.BooleanField(default=False)
    is_encrypted = serializers.BooleanField(default=False)
    
    created_at = serializers.DateTimeField(read_only=True)
    created_by = serializers.CharField(read_only=True)
    
    def validate_content(self, value):
        """Valide le contenu de la configuration."""
        if not value or not value.strip():
            raise DRFValidationError("Le contenu de configuration ne peut pas être vide")
        
        # Vérifier la taille (max 10MB)
        if len(value.encode('utf-8')) > 10 * 1024 * 1024:
            raise DRFValidationError("Configuration trop volumineuse (max 10MB)")
        
        return value


class BulkOperationSerializer(BaseAPISerializer):
    """
    Sérialiseur pour les opérations en lot sur les équipements.
    """
    operation = serializers.ChoiceField(
        choices=[
            ('create', 'Créer'),
            ('update', 'Mettre à jour'),
            ('delete', 'Supprimer'),
            ('restart', 'Redémarrer'),
            ('backup', 'Sauvegarder'),
            ('configure', 'Configurer')
        ],
        help_text="Type d'opération à effectuer"
    )

    devices = serializers.ListField(
        child=serializers.UUIDField(),
        min_length=1,
        max_length=100,
        help_text="Liste des IDs d'équipements"
    )

    parameters = serializers.DictField(
        required=False,
        help_text="Paramètres spécifiques à l'opération"
    )

    def validate_devices(self, value):
        """Valide la liste des équipements."""
        if len(set(value)) != len(value):
            raise DRFValidationError("IDs d'équipements dupliqués")
        return value


class DeviceMetricsSerializer(BaseAPISerializer):
    """
    Sérialiseur pour les métriques d'équipements.
    """
    device_id = serializers.UUIDField()
    timestamp = serializers.DateTimeField()

    cpu_usage = serializers.FloatField(min_value=0, max_value=100)
    memory_usage = serializers.FloatField(min_value=0, max_value=100)
    disk_usage = serializers.FloatField(min_value=0, max_value=100)
    network_io = serializers.DictField()

    uptime = serializers.CharField()
    temperature = serializers.FloatField(required=False)

    metrics = serializers.DictField(
        help_text="Métriques spécifiques à l'équipement"
    )


class DeviceStatusSerializer(BaseAPISerializer):
    """
    Sérialiseur pour le statut d'équipements.
    """
    device_id = serializers.UUIDField()
    status = serializers.ChoiceField(
        choices=[
            ('online', 'En ligne'),
            ('offline', 'Hors ligne'),
            ('maintenance', 'Maintenance'),
            ('error', 'Erreur'),
            ('unknown', 'Inconnu')
        ]
    )

    last_seen = serializers.DateTimeField()
    uptime = serializers.CharField()

    connectivity = serializers.DictField(required=False)
    diagnostics = serializers.DictField(required=False)

    alerts_count = serializers.IntegerField(default=0)
    warnings_count = serializers.IntegerField(default=0)


class DeviceFilterSerializer(FilterSerializer):
    """
    Sérialiseur pour les filtres spécifiques aux équipements.
    """
    device_type = serializers.CharField(
        required=False,
        help_text="Filtrer par type d'équipement"
    )
    
    manufacturer = serializers.CharField(
        required=False,
        help_text="Filtrer par fabricant"
    )
    
    location = serializers.CharField(
        required=False,
        help_text="Filtrer par emplacement"
    )
    
    status = serializers.ChoiceField(
        choices=[
            ('active', 'Actif'),
            ('inactive', 'Inactif'),
            ('warning', 'Avertissement'),
            ('critical', 'Critique'),
            ('unknown', 'Inconnu')
        ],
        required=False,
        help_text="Filtrer par statut"
    )
    
    monitoring_enabled = serializers.BooleanField(
        required=False,
        help_text="Surveillance activée ou non"
    )
    
    is_virtual = serializers.BooleanField(
        required=False,
        help_text="Équipements virtuels ou physiques"
    )
    
    has_alerts = serializers.BooleanField(
        required=False,
        help_text="Avoir des alertes actives"
    )
    
    ip_range = serializers.CharField(
        required=False,
        help_text="Plage d'adresses IP (ex: 192.168.1.0/24)"
    )
    
    tags = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        help_text="Filtrer par tags"
    )
    
    last_seen_after = serializers.DateTimeField(
        required=False,
        help_text="Vu après cette date"
    )
    
    last_seen_before = serializers.DateTimeField(
        required=False,
        help_text="Vu avant cette date"
    )
    
    def validate_ip_range(self, value):
        """Valide la plage d'adresses IP."""
        if not value:
            return value
        
        try:
            from ipaddress import ip_network
            ip_network(value, strict=False)
        except ValueError as e:
            raise DRFValidationError(f"Plage IP invalide: {e}")
        
        return value
    
    class Meta:
        ordering_fields = ['name', 'ip_address', 'device_type', 'status', 'created_at', 'last_seen'] 