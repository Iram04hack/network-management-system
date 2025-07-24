"""
Serializers pour les clients API du module api_clients.

Ces serializers définissent la structure des données pour la documentation
Swagger et la validation des requêtes/réponses.
"""

from rest_framework import serializers


# ============================================================================
# SERIALIZERS POUR LES CLIENTS RÉSEAU
# ============================================================================

class GNS3ProjectSerializer(serializers.Serializer):
    """Serializer pour les projets GNS3."""
    project_id = serializers.CharField(help_text="ID unique du projet")
    name = serializers.CharField(help_text="Nom du projet")
    status = serializers.CharField(help_text="Statut du projet (opened, closed)")
    nodes_count = serializers.IntegerField(help_text="Nombre de nœuds dans le projet")
    created_at = serializers.DateTimeField(help_text="Date de création")


class GNS3NodeSerializer(serializers.Serializer):
    """Serializer pour les nœuds GNS3."""
    node_id = serializers.CharField(help_text="ID unique du nœud")
    name = serializers.CharField(help_text="Nom du nœud")
    node_type = serializers.CharField(help_text="Type de nœud (dynamips, qemu, etc.)")
    status = serializers.CharField(help_text="Statut du nœud (started, stopped)")
    x = serializers.IntegerField(help_text="Position X dans la topologie")
    y = serializers.IntegerField(help_text="Position Y dans la topologie")
    console = serializers.IntegerField(help_text="Port de console", required=False)


class SNMPRequestSerializer(serializers.Serializer):
    """Serializer pour les requêtes SNMP."""
    host = serializers.IPAddressField(help_text="Adresse IP du périphérique")
    oid = serializers.CharField(help_text="OID SNMP à interroger")
    community = serializers.CharField(default='public', help_text="Communauté SNMP")


class SNMPSetRequestSerializer(SNMPRequestSerializer):
    """Serializer pour les requêtes SNMP SET."""
    value = serializers.CharField(help_text="Nouvelle valeur à définir")
    type = serializers.ChoiceField(
        choices=['INTEGER', 'OCTET_STRING', 'OBJECT_IDENTIFIER', 'TIMETICKS'],
        help_text="Type de données SNMP"
    )


class SNMPResponseSerializer(serializers.Serializer):
    """Serializer pour les réponses SNMP."""
    oid = serializers.CharField(help_text="OID interrogé")
    value = serializers.CharField(help_text="Valeur retournée")
    type = serializers.CharField(help_text="Type de données")
    host = serializers.IPAddressField(help_text="Adresse IP du périphérique")
    timestamp = serializers.DateTimeField(help_text="Horodatage de la requête")


class NetflowAnalysisSerializer(serializers.Serializer):
    """Serializer pour l'analyse Netflow."""
    flows = serializers.ListField(
        child=serializers.DictField(),
        help_text="Liste des flux réseau"
    )
    total_flows = serializers.IntegerField(help_text="Nombre total de flux")
    total_bytes = serializers.IntegerField(help_text="Volume total en bytes")
    analysis_time = serializers.DateTimeField(help_text="Heure de l'analyse")


# ============================================================================
# SERIALIZERS POUR LES CLIENTS MONITORING
# ============================================================================

class PrometheusQuerySerializer(serializers.Serializer):
    """Serializer pour les requêtes Prometheus."""
    query = serializers.CharField(help_text="Requête PromQL")
    time = serializers.CharField(required=False, help_text="Timestamp (optionnel)")


class PrometheusResponseSerializer(serializers.Serializer):
    """Serializer pour les réponses Prometheus."""
    status = serializers.CharField(help_text="Statut de la requête")
    data = serializers.DictField(help_text="Données de réponse")


class GrafanaDashboardSerializer(serializers.Serializer):
    """Serializer pour les dashboards Grafana."""
    title = serializers.CharField(help_text="Titre du dashboard")
    panels = serializers.ListField(
        child=serializers.DictField(),
        help_text="Panneaux du dashboard"
    )
    tags = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        help_text="Tags du dashboard"
    )


class ElasticsearchQuerySerializer(serializers.Serializer):
    """Serializer pour les requêtes Elasticsearch."""
    index = serializers.CharField(help_text="Index Elasticsearch")
    query = serializers.DictField(help_text="Requête Elasticsearch DSL")
    size = serializers.IntegerField(default=10, help_text="Nombre de résultats")


class NetdataMetricsSerializer(serializers.Serializer):
    """Serializer pour les métriques Netdata."""
    chart = serializers.CharField(help_text="Nom du graphique")
    dimensions = serializers.ListField(
        child=serializers.CharField(),
        help_text="Dimensions des métriques"
    )
    data = serializers.ListField(
        child=serializers.ListField(),
        help_text="Données des métriques"
    )
    timestamp = serializers.DateTimeField(help_text="Horodatage")


# ============================================================================
# SERIALIZERS POUR LES CLIENTS INFRASTRUCTURE
# ============================================================================

class HAProxyStatsSerializer(serializers.Serializer):
    """Serializer pour les statistiques HAProxy."""
    stats = serializers.DictField(help_text="Statistiques détaillées")
    timestamp = serializers.DateTimeField(help_text="Horodatage")


class Fail2BanActionSerializer(serializers.Serializer):
    """Serializer pour les actions Fail2Ban."""
    action = serializers.ChoiceField(
        choices=['ban', 'unban', 'status'],
        help_text="Action à effectuer"
    )
    ip = serializers.IPAddressField(help_text="Adresse IP")
    jail = serializers.CharField(default='sshd', help_text="Nom de la jail")


class SuricataRuleActionSerializer(serializers.Serializer):
    """Serializer pour les actions sur les règles Suricata."""
    action = serializers.ChoiceField(
        choices=['list', 'add', 'remove', 'reload'],
        help_text="Action à effectuer"
    )
    rule = serializers.CharField(required=False, help_text="Règle Suricata (pour add/remove)")
    rule_id = serializers.IntegerField(required=False, help_text="ID de la règle (pour remove)")


# ============================================================================
# SERIALIZERS GÉNÉRIQUES
# ============================================================================

class ClientHealthSerializer(serializers.Serializer):
    """Serializer pour la santé des clients."""
    clients = serializers.DictField(help_text="État de santé de chaque client")
    total_clients = serializers.IntegerField(help_text="Nombre total de clients")
    healthy_clients = serializers.IntegerField(help_text="Nombre de clients en bonne santé")


class ErrorResponseSerializer(serializers.Serializer):
    """Serializer pour les réponses d'erreur."""
    error = serializers.CharField(help_text="Message d'erreur")
    details = serializers.CharField(required=False, help_text="Détails supplémentaires")
    timestamp = serializers.DateTimeField(help_text="Horodatage de l'erreur")


class SuccessResponseSerializer(serializers.Serializer):
    """Serializer pour les réponses de succès."""
    status = serializers.CharField(default='success', help_text="Statut de l'opération")
    message = serializers.CharField(help_text="Message de confirmation")
    data = serializers.DictField(required=False, help_text="Données supplémentaires")
    timestamp = serializers.DateTimeField(help_text="Horodatage")


# ============================================================================
# SERIALIZERS SUPPLÉMENTAIRES POUR LES VIEWSETS
# ============================================================================

class ClientStatusSerializer(serializers.Serializer):
    """Serializer pour le statut d'un client."""
    name = serializers.CharField(help_text="Nom du client")
    type = serializers.CharField(help_text="Type de client")
    status = serializers.ChoiceField(
        choices=['available', 'unavailable', 'error'],
        help_text="Statut du client"
    )
    url = serializers.URLField(required=False, help_text="URL du service")
    host = serializers.CharField(required=False, help_text="Hôte du service")
    port = serializers.IntegerField(required=False, help_text="Port du service")
    error = serializers.CharField(required=False, help_text="Message d'erreur si applicable")
    description = serializers.CharField(help_text="Description du client")


class NetworkClientSerializer(serializers.Serializer):
    """Serializer pour les clients réseau."""
    success = serializers.BooleanField(help_text="Succès de l'opération")
    count = serializers.IntegerField(help_text="Nombre de clients")
    clients = ClientStatusSerializer(many=True, help_text="Liste des clients réseau")


class MonitoringClientSerializer(serializers.Serializer):
    """Serializer pour les clients de monitoring."""
    success = serializers.BooleanField(help_text="Succès de l'opération")
    count = serializers.IntegerField(help_text="Nombre de clients")
    clients = ClientStatusSerializer(many=True, help_text="Liste des clients de monitoring")


class InfrastructureClientSerializer(serializers.Serializer):
    """Serializer pour les clients d'infrastructure."""
    success = serializers.BooleanField(help_text="Succès de l'opération")
    count = serializers.IntegerField(help_text="Nombre de clients")
    clients = ClientStatusSerializer(many=True, help_text="Liste des clients d'infrastructure")


# ============================================================================
# SERIALIZERS POUR LES NOUVELLES FONCTIONNALITÉS
# ============================================================================

class SecurityClientSerializer(serializers.Serializer):
    """Serializer pour les clients de sécurité."""
    fail2ban = serializers.DictField(help_text="Statut du client Fail2Ban")
    suricata = serializers.DictField(help_text="Statut du client Suricata")


class TrafficControlSerializer(serializers.Serializer):
    """Serializer pour le contrôle du trafic."""
    interface = serializers.CharField(help_text="Interface réseau")
    rate_limit = serializers.CharField(help_text="Limite de débit")
    burst = serializers.CharField(required=False, help_text="Taille de burst")
    success = serializers.BooleanField(help_text="Succès de l'opération")
    output = serializers.CharField(help_text="Sortie de la commande")


class MetricsSerializer(serializers.Serializer):
    """Serializer pour les métriques de performance."""
    endpoint = serializers.CharField(help_text="Endpoint API")
    count = serializers.IntegerField(help_text="Nombre total d'appels")
    success_count = serializers.IntegerField(help_text="Nombre d'appels réussis")
    failure_count = serializers.IntegerField(help_text="Nombre d'appels échoués")
    success_rate = serializers.FloatField(help_text="Taux de succès")
    min_response_time = serializers.FloatField(help_text="Temps de réponse minimum (ms)")
    max_response_time = serializers.FloatField(help_text="Temps de réponse maximum (ms)")
    avg_response_time = serializers.FloatField(help_text="Temps de réponse moyen (ms)")
    p95_response_time = serializers.FloatField(help_text="95e percentile du temps de réponse (ms)")
    p99_response_time = serializers.FloatField(help_text="99e percentile du temps de réponse (ms)")


class CircuitBreakerSerializer(serializers.Serializer):
    """Serializer pour l'état du circuit breaker."""
    state = serializers.ChoiceField(
        choices=['closed', 'open', 'half_open'],
        help_text="État actuel du circuit breaker"
    )
    failure_count = serializers.IntegerField(help_text="Nombre d'échecs consécutifs")
    success_count = serializers.IntegerField(help_text="Nombre de succès")
    total_calls = serializers.IntegerField(help_text="Nombre total d'appels")
    last_failure_time = serializers.FloatField(required=False, help_text="Timestamp du dernier échec")
    last_success_time = serializers.FloatField(required=False, help_text="Timestamp du dernier succès")
    time_to_next_attempt = serializers.FloatField(help_text="Temps avant la prochaine tentative (s)")
    recent_transitions = serializers.ListField(
        child=serializers.DictField(),
        help_text="Transitions d'état récentes"
    )
    config = serializers.DictField(help_text="Configuration du circuit breaker")


class CacheStatsSerializer(serializers.Serializer):
    """Serializer pour les statistiques du cache."""
    size = serializers.IntegerField(help_text="Nombre d'entrées dans le cache")
    max_size = serializers.IntegerField(help_text="Taille maximum du cache")
    hit_rate = serializers.FloatField(help_text="Taux de cache hit")
    miss_rate = serializers.FloatField(help_text="Taux de cache miss")
    hits = serializers.IntegerField(help_text="Nombre de cache hits")
    misses = serializers.IntegerField(help_text="Nombre de cache misses")
    evictions = serializers.IntegerField(help_text="Nombre d'évictions")
    expired_entries = serializers.IntegerField(help_text="Nombre d'entrées expirées")
    total_requests = serializers.IntegerField(help_text="Nombre total de requêtes")
    uptime = serializers.FloatField(help_text="Temps de fonctionnement (s)")


class ServiceDetectionSerializer(serializers.Serializer):
    """Serializer pour la détection de services."""
    detected_services = serializers.DictField(help_text="Services détectés")
    summary = serializers.DictField(help_text="Résumé de la détection")
    scan_timestamp = serializers.CharField(help_text="Horodatage du scan")


class ServiceInfoSerializer(serializers.Serializer):
    """Serializer pour les informations d'un service."""
    name = serializers.CharField(help_text="Nom du service")
    host = serializers.CharField(help_text="Hôte du service")
    port = serializers.IntegerField(help_text="Port du service")
    status = serializers.ChoiceField(
        choices=['available', 'unavailable', 'partial', 'unknown'],
        help_text="Statut du service"
    )
    version = serializers.CharField(required=False, help_text="Version du service")
    response_time = serializers.FloatField(required=False, help_text="Temps de réponse (s)")
    capabilities = serializers.ListField(
        child=serializers.CharField(),
        help_text="Capacités du service"
    )
    error_message = serializers.CharField(required=False, help_text="Message d'erreur si applicable")
