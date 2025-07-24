"""
Sérialiseurs pour les données de découverte de topologie.

Ce module contient les sérialiseurs spécialisés pour la validation et transformation
des données de découverte de topologie réseau.
"""

from typing import Dict, Any, List, Optional
from rest_framework import serializers
from rest_framework.exceptions import ValidationError as DRFValidationError

from .base_serializers import BaseAPISerializer, FilterSerializer


class TopologyRequestSerializer(BaseAPISerializer):
    """
    Sérialiseur pour les requêtes de découverte de topologie.
    """
    scan_type = serializers.ChoiceField(
        choices=[
            ('subnet', 'Scan de sous-réseau'),
            ('single_device', 'Appareil unique'),
            ('range', 'Plage d\'adresses'),
            ('import', 'Import de configuration'),
            ('manual', 'Définition manuelle')
        ],
        help_text="Type de scan à effectuer"
    )
    
    subnet = serializers.CharField(
        required=False,
        max_length=18,
        help_text="Sous-réseau à scanner (ex: 192.168.1.0/24)"
    )
    
    ip_start = serializers.IPAddressField(
        required=False,
        help_text="Adresse IP de début pour le scan de plage"
    )
    
    ip_end = serializers.IPAddressField(
        required=False,
        help_text="Adresse IP de fin pour le scan de plage"
    )
    
    target_ip = serializers.IPAddressField(
        required=False,
        help_text="Adresse IP cible pour scan d'appareil unique"
    )
    
    discovery_method = serializers.ChoiceField(
        choices=[
            ('ping_only', 'Ping seulement'),
            ('port_scan', 'Scan de ports'),
            ('snmp', 'SNMP Discovery'),
            ('lldp', 'LLDP Protocol'),
            ('cdp', 'CDP Protocol'),
            ('ping_and_port', 'Ping + Port scan'),
            ('full_discovery', 'Découverte complète')
        ],
        default='ping_and_port',
        help_text="Méthode de découverte à utiliser"
    )
    
    port_range = serializers.CharField(
        required=False,
        max_length=100,
        help_text="Plage de ports à scanner (ex: 22,80,443 ou 1-1000)"
    )
    
    timeout = serializers.IntegerField(
        min_value=5,
        max_value=300,
        default=30,
        help_text="Timeout en secondes pour les opérations"
    )
    
    max_devices = serializers.IntegerField(
        min_value=1,
        max_value=1000,
        default=100,
        help_text="Nombre maximum d'appareils à découvrir"
    )
    
    credentials = serializers.DictField(
        required=False,
        help_text="Identifiants pour l'accès aux appareils"
    )
    
    save_topology = serializers.BooleanField(
        default=True,
        help_text="Sauvegarder la topologie découverte"
    )
    
    topology_name = serializers.CharField(
        required=False,
        max_length=100,
        help_text="Nom à donner à la topologie sauvegardée"
    )
    
    def validate(self, data):
        """Validation cross-field pour les requêtes de topologie."""
        data = super().validate(data)
        
        scan_type = data.get('scan_type')
        
        # Validation selon le type de scan
        if scan_type == 'subnet':
            if not data.get('subnet'):
                raise DRFValidationError(
                    "Le champ 'subnet' est requis pour scan_type='subnet'"
                )
            
            # Valider le format du subnet
            subnet = data.get('subnet')
            if '/' not in subnet:
                raise DRFValidationError(
                    "Format de subnet invalide. Utilisez la notation CIDR (ex: 192.168.1.0/24)"
                )
        
        elif scan_type == 'range':
            if not data.get('ip_start') or not data.get('ip_end'):
                raise DRFValidationError(
                    "Les champs 'ip_start' et 'ip_end' sont requis pour scan_type='range'"
                )
            
            # Vérifier que ip_start < ip_end
            from ipaddress import ip_address
            if ip_address(data['ip_start']) >= ip_address(data['ip_end']):
                raise DRFValidationError(
                    "ip_start doit être inférieure à ip_end"
                )
        
        elif scan_type == 'single_device':
            if not data.get('target_ip'):
                raise DRFValidationError(
                    "Le champ 'target_ip' est requis pour scan_type='single_device'"
                )
        
        # Validation des identifiants
        credentials = data.get('credentials', {})
        if credentials:
            required_creds = ['username']
            for cred in required_creds:
                if cred not in credentials:
                    raise DRFValidationError(
                        f"Identifiant '{cred}' manquant dans credentials"
                    )
        
        # Validation de la plage de ports
        port_range = data.get('port_range')
        if port_range:
            if ',' in port_range:
                # Liste de ports
                try:
                    ports = [int(p.strip()) for p in port_range.split(',')]
                    for port in ports:
                        if not (1 <= port <= 65535):
                            raise ValueError(f"Port {port} hors plage")
                except ValueError as e:
                    raise DRFValidationError(f"Format de ports invalide: {e}")
            elif '-' in port_range:
                # Plage de ports
                try:
                    start, end = map(int, port_range.split('-'))
                    if start > end or start < 1 or end > 65535:
                        raise ValueError("Plage invalide")
                except ValueError:
                    raise DRFValidationError(
                        "Format de plage de ports invalide (attendu: 'start-end')"
                    )
        
        return data


class DiscoveryStatusSerializer(BaseAPISerializer):
    """
    Sérialiseur pour le statut de découverte.
    """
    discovery_id = serializers.UUIDField(help_text="ID unique de la découverte")
    status = serializers.ChoiceField(
        choices=[
            ('pending', 'En attente'),
            ('running', 'En cours'),
            ('completed', 'Terminé'),
            ('failed', 'Échec'),
            ('cancelled', 'Annulé'),
            ('partial', 'Partiellement réussi')
        ],
        help_text="Statut actuel de la découverte"
    )
    
    progress = serializers.IntegerField(
        min_value=0,
        max_value=100,
        help_text="Pourcentage de progression"
    )
    
    devices_found = serializers.IntegerField(
        min_value=0,
        help_text="Nombre d'appareils découverts"
    )
    
    devices_scanned = serializers.IntegerField(
        min_value=0,
        help_text="Nombre d'appareils scannés"
    )
    
    total_targets = serializers.IntegerField(
        min_value=0,
        help_text="Nombre total de cibles à scanner"
    )
    
    started_at = serializers.DateTimeField(help_text="Heure de début")
    completed_at = serializers.DateTimeField(
        required=False,
        allow_null=True,
        help_text="Heure de fin"
    )
    
    error_message = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Message d'erreur en cas d'échec"
    )
    
    errors = serializers.ListField(
        child=serializers.DictField(),
        required=False,
        help_text="Liste des erreurs détaillées"
    )
    
    current_operation = serializers.CharField(
        required=False,
        help_text="Opération en cours"
    )


class NetworkMapSerializer(BaseAPISerializer):
    """
    Sérialiseur pour la carte réseau.
    """
    nodes = serializers.ListField(
        child=serializers.DictField(),
        help_text="Liste des nœuds (appareils) du réseau"
    )
    
    edges = serializers.ListField(
        child=serializers.DictField(),
        help_text="Liste des connexions entre nœuds"
    )
    
    metadata = serializers.DictField(
        required=False,
        help_text="Métadonnées de la carte"
    )
    
    layout_info = serializers.DictField(
        required=False,
        help_text="Informations de disposition visuelle"
    )
    
    def validate_nodes(self, value):
        """Valide la structure des nœuds."""
        required_fields = ['id', 'name', 'type']
        
        for i, node in enumerate(value):
            for field in required_fields:
                if field not in node:
                    raise DRFValidationError(
                        f"Nœud {i}: champ '{field}' requis"
                    )
            
            # Valider le type de nœud
            valid_types = ['router', 'switch', 'firewall', 'server', 'workstation', 'unknown']
            if node.get('type') not in valid_types:
                raise DRFValidationError(
                    f"Nœud {i}: type '{node.get('type')}' invalide. "
                    f"Types autorisés: {valid_types}"
                )
        
        return value
    
    def validate_edges(self, value):
        """Valide la structure des connexions."""
        required_fields = ['source', 'target']
        
        for i, edge in enumerate(value):
            for field in required_fields:
                if field not in edge:
                    raise DRFValidationError(
                        f"Connexion {i}: champ '{field}' requis"
                    )
        
        return value


class TopologyDiscoverySerializer(BaseAPISerializer):
    """
    Sérialiseur pour les résultats de découverte de topologie.
    """
    discovery_id = serializers.UUIDField(read_only=True)
    topology_name = serializers.CharField(max_length=100)
    discovery_method = serializers.CharField()
    status = serializers.CharField()
    
    devices = serializers.ListField(
        child=serializers.DictField(),
        help_text="Liste des appareils découverts"
    )
    
    connections = serializers.ListField(
        child=serializers.DictField(),
        help_text="Liste des connexions découvertes"
    )
    
    subnets = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        help_text="Liste des sous-réseaux découverts"
    )
    
    statistics = serializers.DictField(
        required=False,
        help_text="Statistiques de découverte"
    )
    
    discovery_params = serializers.DictField(
        help_text="Paramètres utilisés pour la découverte"
    )
    
    created_at = serializers.DateTimeField(read_only=True)
    completed_at = serializers.DateTimeField(required=False, allow_null=True)


class NetworkTopologySerializer(BaseAPISerializer):
    """
    Sérialiseur pour la représentation complète d'une topologie réseau.
    """
    id = serializers.UUIDField(read_only=True)
    name = serializers.CharField(max_length=100)
    description = serializers.CharField(required=False, allow_blank=True)
    
    topology_type = serializers.ChoiceField(
        choices=[
            ('discovered', 'Découverte automatique'),
            ('manual', 'Créée manuellement'),
            ('imported', 'Importée'),
            ('template', 'Modèle')
        ],
        default='discovered'
    )
    
    devices = serializers.ListField(
        child=serializers.DictField(),
        help_text="Appareils de la topologie"
    )
    
    connections = serializers.ListField(
        child=serializers.DictField(),
        help_text="Connexions entre appareils"
    )
    
    layout = serializers.DictField(
        required=False,
        help_text="Informations de disposition"
    )
    
    metadata = serializers.DictField(
        required=False,
        help_text="Métadonnées de la topologie"
    )
    
    is_active = serializers.BooleanField(default=True)
    is_template = serializers.BooleanField(default=False)
    
    created_by = serializers.CharField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
    
    def validate_devices(self, value):
        """Valide la cohérence des appareils."""
        device_ids = []
        
        for device in value:
            device_id = device.get('id')
            if not device_id:
                raise DRFValidationError("Chaque appareil doit avoir un ID")
            
            if device_id in device_ids:
                raise DRFValidationError(f"ID d'appareil dupliqué: {device_id}")
            
            device_ids.append(device_id)
        
        return value
    
    def validate_connections(self, value):
        """Valide la cohérence des connexions."""
        for connection in value:
            source = connection.get('source')
            target = connection.get('target')
            
            if not source or not target:
                raise DRFValidationError(
                    "Chaque connexion doit avoir une source et une cible"
                )
            
            if source == target:
                raise DRFValidationError(
                    "Une connexion ne peut pas avoir la même source et cible"
                )
        
        return value


class TopologyDiscoveryRequestSerializer(BaseAPISerializer):
    """
    Serializer for topology discovery requests.
    """
    network_cidr = serializers.CharField(
        max_length=18,
        help_text="Network CIDR to discover (e.g., 192.168.1.0/24)"
    )
    
    scan_type = serializers.ChoiceField(
        choices=[('basic', 'Basic scan'), ('detailed', 'Detailed scan'), ('deep', 'Deep scan')],
        default='basic',
        help_text="Type of network scan to perform"
    )
    
    protocols = serializers.ListField(
        child=serializers.CharField(),
        default=['snmp', 'ssh'],
        help_text="Protocols to use for device discovery"
    )
    
    schedule = serializers.DictField(
        required=False,
        help_text="Optional scheduling configuration"
    )
    
    network_id = serializers.CharField(
        required=False,
        help_text="Network identifier"
    )


class ConnectionAnalysisSerializer(BaseAPISerializer):
    """
    Serializer for network connections analysis.
    """
    connections = serializers.ListField(
        child=serializers.DictField(),
        help_text="List of network connections"
    )
    
    redundant_paths = serializers.ListField(
        child=serializers.DictField(),
        help_text="Redundant connection paths"
    )
    
    bandwidth_utilization = serializers.DictField(
        help_text="Bandwidth utilization per link"
    )
    
    stp_topology = serializers.DictField(
        required=False,
        help_text="Spanning Tree Protocol topology information"
    )
    
    lldp_neighbors = serializers.DictField(
        required=False,
        help_text="LLDP neighbor discovery data"
    )


class DeviceDependencySerializer(BaseAPISerializer):
    """
    Serializer for device dependency analysis.
    """
    device_id = serializers.CharField(
        help_text="Device identifier"
    )
    
    upstream_dependencies = serializers.ListField(
        child=serializers.DictField(),
        help_text="Devices this device depends on"
    )
    
    downstream_dependencies = serializers.ListField(
        child=serializers.DictField(),
        help_text="Devices that depend on this device"
    )
    
    critical_path = serializers.ListField(
        child=serializers.CharField(),
        help_text="Critical path through the network"
    )
    
    impact_analysis = serializers.DictField(
        help_text="Impact analysis for device failure"
    )
    
    recovery_time_estimate = serializers.IntegerField(
        help_text="Estimated recovery time in minutes"
    )
    
    service_dependencies = serializers.ListField(
        child=serializers.DictField(),
        required=False,
        help_text="Service-level dependencies"
    )


class TopologyFilterSerializer(FilterSerializer):
    """
    Sérialiseur pour les filtres spécifiques aux topologies.
    """
    topology_type = serializers.CharField(
        required=False,
        help_text="Filtrer par type de topologie"
    )
    
    discovery_method = serializers.CharField(
        required=False,
        help_text="Filtrer par méthode de découverte"
    )
    
    device_count_min = serializers.IntegerField(
        required=False,
        min_value=0,
        help_text="Nombre minimum d'appareils"
    )
    
    device_count_max = serializers.IntegerField(
        required=False,
        min_value=1,
        help_text="Nombre maximum d'appareils"
    )
    
    created_after = serializers.DateTimeField(
        required=False,
        help_text="Créées après cette date"
    )
    
    created_before = serializers.DateTimeField(
        required=False,
        help_text="Créées avant cette date"
    )
    
    has_connections = serializers.BooleanField(
        required=False,
        help_text="Avoir des connexions ou non"
    )
    
    class Meta:
        ordering_fields = ['name', 'created_at', 'updated_at', 'device_count'] 