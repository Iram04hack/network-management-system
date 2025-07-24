"""
Serializers DRF pour l'API Service Central GNS3.

Ce module fournit tous les serializers nécessaires pour valider et sérialiser
les données échangées avec l'API du service central GNS3.
"""

from rest_framework import serializers
from typing import Dict, Any, List, Optional


class GNS3ServiceStatusSerializer(serializers.Serializer):
    """Serializer pour le statut du service central GNS3."""
    
    service_name = serializers.CharField(read_only=True)
    version = serializers.CharField(read_only=True)
    status = serializers.ChoiceField(choices=['connected', 'disconnected'], read_only=True)
    
    # Statut du serveur GNS3
    gns3_server = serializers.DictField(read_only=True)
    
    # Monitoring
    monitoring = serializers.DictField(read_only=True)
    
    # Statistiques
    statistics = serializers.DictField(read_only=True)
    
    # Cache
    cache = serializers.DictField(read_only=True)
    
    # Callbacks
    callbacks = serializers.DictField(read_only=True)
    
    last_update = serializers.DateTimeField(read_only=True)


class GNS3NodeActionSerializer(serializers.Serializer):
    """Serializer pour les actions sur les nœuds (start/stop/restart)."""
    
    project_id = serializers.UUIDField(required=True, help_text="ID du projet contenant le nœud")
    node_id = serializers.UUIDField(required=True, help_text="ID du nœud à contrôler")


class GNS3NodeActionResponseSerializer(serializers.Serializer):
    """Serializer pour les réponses d'actions sur les nœuds."""
    
    success = serializers.BooleanField(read_only=True)
    node_id = serializers.UUIDField(read_only=True)
    project_id = serializers.UUIDField(read_only=True)
    old_status = serializers.CharField(read_only=True)
    new_status = serializers.CharField(read_only=True)
    timestamp = serializers.DateTimeField(read_only=True)
    error = serializers.CharField(read_only=True, required=False)


class GNS3RestartNodeResponseSerializer(serializers.Serializer):
    """Serializer pour la réponse de redémarrage d'un nœud."""
    
    success = serializers.BooleanField(read_only=True)
    action = serializers.CharField(read_only=True)
    stop_result = serializers.DictField(read_only=True)
    start_result = serializers.DictField(read_only=True)
    error = serializers.CharField(read_only=True, required=False)


class GNS3ProjectActionSerializer(serializers.Serializer):
    """Serializer pour les actions sur les projets."""
    
    project_id = serializers.UUIDField(required=True, help_text="ID du projet à contrôler")


class GNS3ProjectStartResponseSerializer(serializers.Serializer):
    """Serializer pour la réponse de démarrage d'un projet."""
    
    success = serializers.BooleanField(read_only=True)
    total_nodes = serializers.IntegerField(read_only=True)
    started_nodes = serializers.IntegerField(read_only=True)
    results = serializers.DictField(read_only=True)
    error = serializers.CharField(read_only=True, required=False)


class GNS3NodeSerializer(serializers.Serializer):
    """Serializer pour les informations d'un nœud GNS3."""
    
    node_id = serializers.UUIDField(read_only=True)
    name = serializers.CharField(read_only=True)
    status = serializers.ChoiceField(
        choices=['started', 'stopped', 'suspended'], 
        read_only=True
    )
    node_type = serializers.CharField(read_only=True)
    project_id = serializers.UUIDField(read_only=True)
    last_update = serializers.DateTimeField(read_only=True)
    x = serializers.IntegerField(read_only=True, help_text="Position X dans l'interface graphique")
    y = serializers.IntegerField(read_only=True, help_text="Position Y dans l'interface graphique")


class GNS3ProjectSerializer(serializers.Serializer):
    """Serializer pour les informations d'un projet GNS3."""
    
    project_id = serializers.UUIDField(read_only=True)
    name = serializers.CharField(read_only=True)
    status = serializers.CharField(read_only=True)
    path = serializers.CharField(read_only=True, required=False)
    nodes = serializers.DictField(read_only=True)


class GNS3TopologySerializer(serializers.Serializer):
    """Serializer pour la topologie complète du réseau GNS3."""
    
    projects = serializers.DictField(read_only=True)
    nodes = serializers.DictField(read_only=True)
    links = serializers.DictField(read_only=True)
    last_update = serializers.DateTimeField(read_only=True)
    server_status = serializers.CharField(read_only=True)


class GNS3RefreshTopologyResponseSerializer(serializers.Serializer):
    """Serializer pour la réponse de rafraîchissement de topologie."""
    
    success = serializers.BooleanField(read_only=True)
    topology = GNS3TopologySerializer(read_only=True)
    refresh_time = serializers.DateTimeField(read_only=True)
    error = serializers.CharField(read_only=True, required=False)


class GNS3ModuleInterfaceRequestSerializer(serializers.Serializer):
    """Serializer pour la création d'une interface module."""
    
    module_name = serializers.CharField(
        required=True,
        max_length=50,
        help_text="Nom unique du module (ex: 'monitoring', 'security', 'analysis')"
    )
    
    def validate_module_name(self, value):
        """Valide le nom du module."""
        if not value or not value.strip():
            raise serializers.ValidationError("Le nom du module ne peut pas être vide")
        
        # Caractères autorisés : lettres, chiffres, tirets et underscores
        import re
        if not re.match(r'^[a-zA-Z0-9_-]+$', value):
            raise serializers.ValidationError(
                "Le nom du module ne peut contenir que des lettres, chiffres, tirets et underscores"
            )
        
        return value.strip().lower()


class GNS3ModuleInterfaceResponseSerializer(serializers.Serializer):
    """Serializer pour la réponse de création d'interface module."""
    
    success = serializers.BooleanField(read_only=True)
    module_name = serializers.CharField(read_only=True)
    interface_created = serializers.BooleanField(read_only=True)
    available_methods = serializers.ListField(
        child=serializers.CharField(),
        read_only=True,
        help_text="Liste des méthodes disponibles sur l'interface"
    )
    error = serializers.CharField(read_only=True, required=False)


class GNS3EventTypeSerializer(serializers.Serializer):
    """Serializer pour les types d'événements GNS3."""
    
    NODE_CREATED = serializers.CharField(default="node.created", read_only=True)
    NODE_UPDATED = serializers.CharField(default="node.updated", read_only=True)
    NODE_DELETED = serializers.CharField(default="node.deleted", read_only=True)
    NODE_STARTED = serializers.CharField(default="node.started", read_only=True)
    NODE_STOPPED = serializers.CharField(default="node.stopped", read_only=True)
    NODE_SUSPENDED = serializers.CharField(default="node.suspended", read_only=True)
    PROJECT_OPENED = serializers.CharField(default="project.opened", read_only=True)
    PROJECT_CLOSED = serializers.CharField(default="project.closed", read_only=True)
    PROJECT_CREATED = serializers.CharField(default="project.created", read_only=True)
    PROJECT_DELETED = serializers.CharField(default="project.deleted", read_only=True)
    LINK_CREATED = serializers.CharField(default="link.created", read_only=True)
    LINK_DELETED = serializers.CharField(default="link.deleted", read_only=True)
    TOPOLOGY_CHANGED = serializers.CharField(default="topology.changed", read_only=True)


class GNS3EventStatsSerializer(serializers.Serializer):
    """Serializer pour les statistiques des événements GNS3."""
    
    total_events_processed = serializers.IntegerField(read_only=True)
    event_types_available = serializers.ListField(
        child=serializers.CharField(),
        read_only=True
    )
    registered_callbacks = serializers.IntegerField(read_only=True)
    last_event_time = serializers.DateTimeField(read_only=True, allow_null=True)
    events_per_type = serializers.DictField(read_only=True)
    
    # Métriques de performance
    performance_metrics = serializers.DictField(read_only=True)


class GNS3NetworkSummarySerializer(serializers.Serializer):
    """Serializer pour un résumé du réseau GNS3."""
    
    projects_count = serializers.IntegerField(read_only=True)
    nodes_count = serializers.IntegerField(read_only=True)
    links_count = serializers.IntegerField(read_only=True)
    status_distribution = serializers.DictField(read_only=True)
    type_distribution = serializers.DictField(read_only=True)
    last_update = serializers.DateTimeField(read_only=True)
    requested_by = serializers.CharField(read_only=True)
    error = serializers.CharField(read_only=True, required=False)


class GNS3NodeStatusQuerySerializer(serializers.Serializer):
    """Serializer pour les requêtes de statut de nœud."""
    
    node_id = serializers.UUIDField(
        required=True,
        help_text="ID du nœud dont obtenir le statut"
    )


class GNS3NodesFilterSerializer(serializers.Serializer):
    """Serializer pour filtrer les nœuds par statut ou type."""
    
    status = serializers.ChoiceField(
        choices=['started', 'stopped', 'suspended'],
        required=False,
        help_text="Filtrer les nœuds par statut"
    )
    node_type = serializers.CharField(
        required=False,
        max_length=50,
        help_text="Filtrer les nœuds par type (qemu, docker, dynamips, etc.)"
    )
    project_id = serializers.UUIDField(
        required=False,
        help_text="Filtrer les nœuds par projet"
    )


class GNS3SubscriptionTypeSerializer(serializers.Serializer):
    """Serializer pour les types d'abonnements aux événements."""
    
    NODE_STATUS = serializers.CharField(default="node_status", read_only=True)
    TOPOLOGY_CHANGES = serializers.CharField(default="topology_changes", read_only=True)
    PROJECT_EVENTS = serializers.CharField(default="project_events", read_only=True)
    ALL_EVENTS = serializers.CharField(default="all_events", read_only=True)


class GNS3EventSubscriptionSerializer(serializers.Serializer):
    """Serializer pour les abonnements aux événements GNS3."""
    
    module_name = serializers.CharField(required=True)
    subscription_types = serializers.ListField(
        child=serializers.CharField(),
        required=True,
        help_text="Types d'événements auxquels s'abonner"
    )
    
    def validate_subscription_types(self, value):
        """Valide les types d'abonnements."""
        valid_types = ['node_status', 'topology_changes', 'project_events', 'all_events']
        
        for sub_type in value:
            if sub_type not in valid_types:
                raise serializers.ValidationError(
                    f"Type d'abonnement invalide: {sub_type}. "
                    f"Types valides: {', '.join(valid_types)}"
                )
        
        return value


class ErrorResponseSerializer(serializers.Serializer):
    """Serializer pour les réponses d'erreur standardisées."""
    
    error = serializers.CharField(read_only=True)
    details = serializers.DictField(read_only=True, required=False)
    timestamp = serializers.DateTimeField(read_only=True, required=False)
    request_id = serializers.CharField(read_only=True, required=False)


class SuccessResponseSerializer(serializers.Serializer):
    """Serializer pour les réponses de succès standardisées."""
    
    success = serializers.BooleanField(read_only=True)
    message = serializers.CharField(read_only=True, required=False)
    data = serializers.DictField(read_only=True, required=False)
    timestamp = serializers.DateTimeField(read_only=True, required=False)


# Serializers pour les réponses complexes avec pagination
class GNS3PaginatedResponseSerializer(serializers.Serializer):
    """Serializer pour les réponses paginées."""
    
    count = serializers.IntegerField(read_only=True)
    next = serializers.URLField(read_only=True, allow_null=True)
    previous = serializers.URLField(read_only=True, allow_null=True)
    results = serializers.ListField(read_only=True)


class GNS3BulkOperationSerializer(serializers.Serializer):
    """Serializer pour les opérations en masse."""
    
    operation = serializers.ChoiceField(
        choices=['start', 'stop', 'restart'],
        required=True,
        help_text="Type d'opération à effectuer"
    )
    targets = serializers.ListField(
        child=serializers.DictField(),
        required=True,
        help_text="Liste des cibles (nœuds ou projets) pour l'opération"
    )
    options = serializers.DictField(
        required=False,
        help_text="Options supplémentaires pour l'opération"
    )


class GNS3BulkOperationResponseSerializer(serializers.Serializer):
    """Serializer pour les réponses d'opérations en masse."""
    
    operation = serializers.CharField(read_only=True)
    total_targets = serializers.IntegerField(read_only=True)
    successful_operations = serializers.IntegerField(read_only=True)
    failed_operations = serializers.IntegerField(read_only=True)
    results = serializers.DictField(read_only=True)
    execution_time = serializers.FloatField(read_only=True)


# Serializers pour la configuration avancée
class GNS3ServiceConfigSerializer(serializers.Serializer):
    """Serializer pour la configuration du service GNS3."""
    
    gns3_host = serializers.CharField(max_length=255, required=False)
    gns3_port = serializers.IntegerField(min_value=1, max_value=65535, required=False)
    gns3_protocol = serializers.ChoiceField(choices=['http', 'https'], required=False)
    cache_ttl = serializers.IntegerField(min_value=60, max_value=3600, required=False)
    websocket_enabled = serializers.BooleanField(required=False)
    event_retention_hours = serializers.IntegerField(min_value=1, max_value=168, required=False)


class GNS3HealthCheckSerializer(serializers.Serializer):
    """Serializer pour le contrôle de santé du service."""
    
    service_healthy = serializers.BooleanField(read_only=True)
    gns3_server_reachable = serializers.BooleanField(read_only=True)
    redis_cache_available = serializers.BooleanField(read_only=True)
    websocket_status = serializers.CharField(read_only=True)
    last_successful_api_call = serializers.DateTimeField(read_only=True, allow_null=True)
    error_rate_percent = serializers.FloatField(read_only=True)
    average_response_time_ms = serializers.FloatField(read_only=True)