"""
Schémas OpenAPI détaillés pour la documentation Swagger.

Ce module définit les schémas OpenAPI pour une documentation complète
de toutes les APIs du système de gestion réseau.
"""

from drf_yasg import openapi

# Schémas de base réutilisables
error_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'success': openapi.Schema(type=openapi.TYPE_BOOLEAN, default=False),
        'error': openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'code': openapi.Schema(type=openapi.TYPE_STRING, description="Code d'erreur"),
                'message': openapi.Schema(type=openapi.TYPE_STRING, description="Message d'erreur"),
                'details': openapi.Schema(type=openapi.TYPE_OBJECT, description="Détails de l'erreur"),
            }
        ),
        'timestamp': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME),
        'request_id': openapi.Schema(type=openapi.TYPE_STRING, description="ID de la requête"),
    }
)

pagination_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'count': openapi.Schema(type=openapi.TYPE_INTEGER, description="Nombre total d'éléments"),
        'next': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_URI, description="URL page suivante"),
        'previous': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_URI, description="URL page précédente"),
        'page_size': openapi.Schema(type=openapi.TYPE_INTEGER, description="Taille de la page"),
        'current_page': openapi.Schema(type=openapi.TYPE_INTEGER, description="Page actuelle"),
    }
)

# Schémas Dashboard
dashboard_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'id': openapi.Schema(type=openapi.TYPE_INTEGER, description="Identifiant unique"),
        'name': openapi.Schema(type=openapi.TYPE_STRING, description="Nom du tableau de bord", max_length=255),
        'description': openapi.Schema(type=openapi.TYPE_STRING, description="Description"),
        'dashboard_type': openapi.Schema(
            type=openapi.TYPE_STRING, 
            enum=['system', 'network', 'security', 'monitoring', 'custom'],
            description="Type de tableau de bord"
        ),
        'widgets': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_OBJECT)),
        'created_at': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME),
        'updated_at': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME),
        'owner': openapi.Schema(type=openapi.TYPE_INTEGER, description="ID du propriétaire"),
        'is_public': openapi.Schema(type=openapi.TYPE_BOOLEAN, description="Visible publiquement"),
        'tags': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_STRING)),
    }
)

# Schémas Device Management
device_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'id': openapi.Schema(type=openapi.TYPE_INTEGER, description="Identifiant unique"),
        'name': openapi.Schema(type=openapi.TYPE_STRING, description="Nom de l'équipement", max_length=255),
        'ip_address': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_IPV4, description="Adresse IP"),
        'device_type': openapi.Schema(
            type=openapi.TYPE_STRING,
            enum=['router', 'switch', 'firewall', 'server', 'access_point', 'load_balancer'],
            description="Type d'équipement"
        ),
        'vendor': openapi.Schema(type=openapi.TYPE_STRING, description="Fabricant"),
        'model': openapi.Schema(type=openapi.TYPE_STRING, description="Modèle"),
        'location': openapi.Schema(type=openapi.TYPE_STRING, description="Localisation physique"),
        'status': openapi.Schema(
            type=openapi.TYPE_STRING,
            enum=['online', 'offline', 'maintenance', 'unknown'],
            description="Statut de l'équipement"
        ),
        'last_seen': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME),
        'uptime': openapi.Schema(type=openapi.TYPE_STRING, description="Temps de fonctionnement"),
        'os_version': openapi.Schema(type=openapi.TYPE_STRING, description="Version du système"),
        'serial_number': openapi.Schema(type=openapi.TYPE_STRING, description="Numéro de série"),
        'interfaces': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_OBJECT)),
        'metrics': openapi.Schema(type=openapi.TYPE_OBJECT, description="Métriques de performance"),
    }
)

# Schémas Topology Discovery
topology_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'id': openapi.Schema(type=openapi.TYPE_INTEGER, description="Identifiant unique"),
        'name': openapi.Schema(type=openapi.TYPE_STRING, description="Nom de la topologie"),
        'network_id': openapi.Schema(type=openapi.TYPE_STRING, description="Identifiant du réseau"),
        'discovery_method': openapi.Schema(
            type=openapi.TYPE_STRING,
            enum=['snmp', 'icmp', 'ssh', 'auto'],
            description="Méthode de découverte"
        ),
        'status': openapi.Schema(
            type=openapi.TYPE_STRING,
            enum=['pending', 'running', 'completed', 'failed', 'cancelled'],
            description="Statut de la découverte"
        ),
        'nodes': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_OBJECT)),
        'links': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_OBJECT)),
        'created_at': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME),
        'completed_at': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME),
        'devices_found': openapi.Schema(type=openapi.TYPE_INTEGER, description="Nombre d'équipements découverts"),
        'progress': openapi.Schema(type=openapi.TYPE_NUMBER, description="Progression en pourcentage"),
    }
)

# Schémas Search
search_result_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'query': openapi.Schema(type=openapi.TYPE_STRING, description="Requête de recherche"),
        'results': openapi.Schema(
            type=openapi.TYPE_ARRAY,
            items=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'type': openapi.Schema(type=openapi.TYPE_STRING, description="Type de ressource"),
                    'id': openapi.Schema(type=openapi.TYPE_INTEGER, description="Identifiant"),
                    'name': openapi.Schema(type=openapi.TYPE_STRING, description="Nom"),
                    'match': openapi.Schema(type=openapi.TYPE_STRING, description="Champ correspondant"),
                    'score': openapi.Schema(type=openapi.TYPE_NUMBER, description="Score de pertinence"),
                    'url': openapi.Schema(type=openapi.TYPE_STRING, description="URL de la ressource"),
                    'preview': openapi.Schema(type=openapi.TYPE_STRING, description="Aperçu du contenu"),
                }
            )
        ),
        'total_results': openapi.Schema(type=openapi.TYPE_INTEGER, description="Nombre total de résultats"),
        'query_time_ms': openapi.Schema(type=openapi.TYPE_INTEGER, description="Temps de requête en ms"),
        'facets': openapi.Schema(type=openapi.TYPE_OBJECT, description="Facettes de recherche"),
    }
)

# Schémas Monitoring
prometheus_metric_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'status': openapi.Schema(type=openapi.TYPE_STRING, enum=['success', 'error']),
        'data': openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'resultType': openapi.Schema(type=openapi.TYPE_STRING, enum=['matrix', 'vector', 'scalar', 'string']),
                'result': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_OBJECT)),
            }
        ),
        'warnings': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_STRING)),
    }
)

grafana_dashboard_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'id': openapi.Schema(type=openapi.TYPE_INTEGER, description="ID Grafana"),
        'uid': openapi.Schema(type=openapi.TYPE_STRING, description="UID unique"),
        'title': openapi.Schema(type=openapi.TYPE_STRING, description="Titre du dashboard"),
        'tags': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_STRING)),
        'timezone': openapi.Schema(type=openapi.TYPE_STRING, description="Fuseau horaire"),
        'panels': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_OBJECT)),
        'time': openapi.Schema(type=openapi.TYPE_OBJECT, description="Configuration temporelle"),
        'refresh': openapi.Schema(type=openapi.TYPE_STRING, description="Intervalle de rafraîchissement"),
    }
)

# Schémas Security
fail2ban_jail_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'name': openapi.Schema(type=openapi.TYPE_STRING, description="Nom de la jail"),
        'enabled': openapi.Schema(type=openapi.TYPE_BOOLEAN, description="Statut actif"),
        'filter': openapi.Schema(type=openapi.TYPE_STRING, description="Filtre appliqué"),
        'action': openapi.Schema(type=openapi.TYPE_STRING, description="Action de bannissement"),
        'currently_banned': openapi.Schema(type=openapi.TYPE_INTEGER, description="IPs actuellement bannies"),
        'total_banned': openapi.Schema(type=openapi.TYPE_INTEGER, description="Total des bannissements"),
        'banned_ips': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_STRING)),
        'max_retry': openapi.Schema(type=openapi.TYPE_INTEGER, description="Tentatives maximales"),
        'ban_time': openapi.Schema(type=openapi.TYPE_INTEGER, description="Durée du bannissement"),
        'find_time': openapi.Schema(type=openapi.TYPE_INTEGER, description="Fenêtre de détection"),
    }
)

suricata_alert_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'id': openapi.Schema(type=openapi.TYPE_INTEGER, description="Identifiant unique"),
        'timestamp': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME),
        'src_ip': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_IPV4, description="IP source"),
        'src_port': openapi.Schema(type=openapi.TYPE_INTEGER, description="Port source"),
        'dest_ip': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_IPV4, description="IP destination"),
        'dest_port': openapi.Schema(type=openapi.TYPE_INTEGER, description="Port destination"),
        'proto': openapi.Schema(type=openapi.TYPE_STRING, enum=['TCP', 'UDP', 'ICMP'], description="Protocole"),
        'severity': openapi.Schema(
            type=openapi.TYPE_STRING,
            enum=['low', 'medium', 'high', 'critical'],
            description="Niveau de sévérité"
        ),
        'signature': openapi.Schema(type=openapi.TYPE_STRING, description="Signature de l'alerte"),
        'sid': openapi.Schema(type=openapi.TYPE_INTEGER, description="ID de signature"),
        'classification': openapi.Schema(type=openapi.TYPE_STRING, description="Classification de l'attaque"),
        'payload': openapi.Schema(type=openapi.TYPE_STRING, description="Charge utile capturée"),
    }
)

# Réponses communes
COMMON_RESPONSES = {
    200: openapi.Response(description="Opération réussie"),
    201: openapi.Response(description="Ressource créée avec succès"),
    400: openapi.Response(description="Requête invalide", schema=error_schema),
    401: openapi.Response(description="Authentification requise", schema=error_schema),
    403: openapi.Response(description="Permissions insuffisantes", schema=error_schema),
    404: openapi.Response(description="Ressource non trouvée", schema=error_schema),
    409: openapi.Response(description="Conflit de ressource", schema=error_schema),
    429: openapi.Response(description="Limite de débit dépassée", schema=error_schema),
    500: openapi.Response(description="Erreur serveur interne", schema=error_schema),
    503: openapi.Response(description="Service temporairement indisponible", schema=error_schema),
}

# Paramètres de pagination standards
PAGINATION_PARAMETERS = [
    openapi.Parameter('page', openapi.IN_QUERY, description="Numéro de page", type=openapi.TYPE_INTEGER, default=1),
    openapi.Parameter('page_size', openapi.IN_QUERY, description="Éléments par page", type=openapi.TYPE_INTEGER, default=20),
    openapi.Parameter('ordering', openapi.IN_QUERY, description="Champ de tri", type=openapi.TYPE_STRING),
]

# Paramètres de filtrage standards
FILTER_PARAMETERS = [
    openapi.Parameter('search', openapi.IN_QUERY, description="Recherche textuelle", type=openapi.TYPE_STRING),
    openapi.Parameter('created_after', openapi.IN_QUERY, description="Créé après", type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME),
    openapi.Parameter('created_before', openapi.IN_QUERY, description="Créé avant", type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME),
]