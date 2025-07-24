from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions
from .swagger_schemas import (
    dashboard_schema, device_schema, topology_schema, search_result_schema,
    prometheus_metric_schema, grafana_dashboard_schema, fail2ban_jail_schema,
    suricata_alert_schema, COMMON_RESPONSES
)

# Tags pour organiser les endpoints dans Swagger
API_TAGS = {
    'dashboards': {
        'name': 'views',
        'description': 'Tableaux de bord interactifs avec métriques temps réel, widgets personnalisables, et alerting intelligent pour supervision système, réseau et sécurité'
    },
    'devices': {
        'name': 'views', 
        'description': 'CRUD complet pour équipements réseau avec auto-discovery, configuration automatisée, monitoring SNMP, et lifecycle management'
    },
    'topology': {
        'name': 'views',
        'description': 'Cartographie automatique du réseau via SNMP/SSH/ICMP, analyse de connectivité, détection de dépendances, et exports multi-formats'
    },
    'search': {
        'name': 'views',
        'description': 'Moteur de recherche intelligent avec filtrage dynamique, suggestions IA, historique des requêtes, et analytics d\'usage'
    },
    'prometheus': {
        'name': 'views',
        'description': 'Intégration Prometheus avec collecte de métriques, requêtes PromQL, alerting rules, et fédération multi-cluster'
    },
    'grafana': {
        'name': 'views',
        'description': 'Gestion de dashboards Grafana avec auto-provisioning, templating, annotations, et exports programmatiques'
    },
    'security_fail2ban': {
        'name': 'views',
        'description': 'Protection anti-intrusion avec bannissement automatique, gestion de jails, whitelist/blacklist, et audit de sécurité'
    },
    'security_suricata': {
        'name': 'views',
        'description': 'Détection d\'intrusion temps réel avec signatures personnalisées, alerting multi-niveau, et intégration threat intelligence'
    },
    'testing': {
        'name': 'views',
        'description': 'Endpoints de validation pour vérifier l\'état des services, connectivity checks, et diagnostics système'
    }
}

# Paramètres communs pour la documentation
COMMON_PARAMETERS = {
    'page': openapi.Parameter(
        'page',
        openapi.IN_QUERY,
        description="Numéro de page pour la pagination",
        type=openapi.TYPE_INTEGER,
        default=1
    ),
    'page_size': openapi.Parameter(
        'page_size',
        openapi.IN_QUERY,
        description="Nombre d'éléments par page (max 100)",
        type=openapi.TYPE_INTEGER,
        default=20,
        maximum=100
    ),
    'search': openapi.Parameter(
        'search',
        openapi.IN_QUERY,
        description="Terme de recherche global",
        type=openapi.TYPE_STRING
    ),
    'ordering': openapi.Parameter(
        'ordering',
        openapi.IN_QUERY,
        description="Champ de tri (préfixer par '-' pour ordre décroissant)",
        type=openapi.TYPE_STRING
    ),
    'status': openapi.Parameter(
        'status',
        openapi.IN_QUERY,
        description="Filtrer par statut",
        type=openapi.TYPE_STRING,
        enum=['active', 'inactive', 'maintenance', 'error']
    ),
    'time_range': openapi.Parameter(
        'time_range',
        openapi.IN_QUERY,
        description="Plage temporelle pour les métriques",
        type=openapi.TYPE_STRING,
        enum=['5m', '1h', '6h', '24h', '7d', '30d'],
        default='1h'
    )
}

# Réponses communes standardisées
COMMON_RESPONSES = {
    400: openapi.Response(
        description="Requête invalide - données malformées ou paramètres manquants",
        schema=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'error': openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'code': openapi.Schema(type=openapi.TYPE_STRING, example='VALIDATION_ERROR'),
                        'message': openapi.Schema(type=openapi.TYPE_STRING, example='Données de requête invalides'),
                        'details': openapi.Schema(type=openapi.TYPE_OBJECT),
                        'timestamp': openapi.Schema(type=openapi.TYPE_STRING, format='datetime'),
                        'request_id': openapi.Schema(type=openapi.TYPE_STRING)
                    }
                )
            }
        )
    ),
    401: openapi.Response(
        description="Non authentifié - token manquant ou invalide",
        schema=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'detail': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    example="Token d'authentification requis"
                )
            }
        )
    ),
    403: openapi.Response(
        description="Non autorisé - permissions insuffisantes",
        schema=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'detail': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    example="Permissions insuffisantes pour cette action"
                )
            }
        )
    ),
    404: openapi.Response(
        description="Ressource non trouvée",
        schema=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'detail': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    example="Ressource demandée introuvable"
                ),
                'resource_type': openapi.Schema(type=openapi.TYPE_STRING),
                'resource_id': openapi.Schema(type=openapi.TYPE_STRING)
            }
        )
    ),
    429: openapi.Response(
        description="Limite de débit dépassée",
        schema=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'detail': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    example="Trop de requêtes - veuillez patienter"
                ),
                'retry_after': openapi.Schema(
                    type=openapi.TYPE_INTEGER,
                    description="Secondes à attendre avant nouvelle tentative"
                ),
                'limit': openapi.Schema(type=openapi.TYPE_INTEGER),
                'window': openapi.Schema(type=openapi.TYPE_INTEGER)
            }
        )
    ),
    500: openapi.Response(
        description="Erreur serveur interne",
        schema=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'error': openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING, example='Erreur interne du serveur'),
                        'request_id': openapi.Schema(type=openapi.TYPE_STRING),
                        'timestamp': openapi.Schema(type=openapi.TYPE_STRING, format='datetime')
                    }
                )
            }
        )
    )
}

# Schémas de données personnalisés
CUSTOM_SCHEMAS = {
    'DeviceDetail': openapi.Schema(
        type=openapi.TYPE_OBJECT,
        title="Détails d'Équipement",
        description="Informations complètes d'un équipement réseau",
        properties={
            'id': openapi.Schema(type=openapi.TYPE_INTEGER, description="Identifiant unique"),
            'name': openapi.Schema(type=openapi.TYPE_STRING, description="Nom de l'équipement"),
            'type': openapi.Schema(
                type=openapi.TYPE_STRING, 
                enum=['router', 'switch', 'firewall', 'server', 'access_point'],
                description="Type d'équipement"
            ),
            'ip_address': openapi.Schema(type=openapi.TYPE_STRING, format='ipv4'),
            'status': openapi.Schema(
                type=openapi.TYPE_STRING,
                enum=['online', 'offline', 'maintenance', 'error'],
                description="Statut operationnel"
            ),
            'location': openapi.Schema(type=openapi.TYPE_STRING, description="Localisation physique"),
            'vendor': openapi.Schema(type=openapi.TYPE_STRING, description="Fabricant"),
            'model': openapi.Schema(type=openapi.TYPE_STRING, description="Modèle"),
            'os_version': openapi.Schema(type=openapi.TYPE_STRING, description="Version OS"),
            'uptime': openapi.Schema(type=openapi.TYPE_STRING, description="Durée de fonctionnement"),
            'last_seen': openapi.Schema(type=openapi.TYPE_STRING, format='datetime'),
            'metrics': openapi.Schema(
                type=openapi.TYPE_OBJECT,
                description="Métriques temps réel",
                properties={
                    'cpu_usage': openapi.Schema(type=openapi.TYPE_NUMBER, format='float', minimum=0, maximum=100),
                    'memory_usage': openapi.Schema(type=openapi.TYPE_NUMBER, format='float', minimum=0, maximum=100),
                    'disk_usage': openapi.Schema(type=openapi.TYPE_NUMBER, format='float', minimum=0, maximum=100),
                    'temperature': openapi.Schema(type=openapi.TYPE_NUMBER, format='float')
                }
            ),
            'interfaces': openapi.Schema(
                type=openapi.TYPE_ARRAY,
                description="Interfaces réseau",
                items=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'name': openapi.Schema(type=openapi.TYPE_STRING),
                        'status': openapi.Schema(type=openapi.TYPE_STRING, enum=['up', 'down', 'admin-down']),
                        'ip': openapi.Schema(type=openapi.TYPE_STRING, format='ipv4'),
                        'mac': openapi.Schema(type=openapi.TYPE_STRING),
                        'speed': openapi.Schema(type=openapi.TYPE_STRING)
                    }
                )
            )
        },
        required=['id', 'name', 'type', 'ip_address', 'status']
    ),

    'DashboardData': openapi.Schema(
        type=openapi.TYPE_OBJECT,
        title="Données de Dashboard",
        description="Données structurées pour l'affichage de tableaux de bord",
        properties={
            'system_metrics': openapi.Schema(
                type=openapi.TYPE_OBJECT,
                description="Métriques système",
                properties={
                    'cpu_utilization': openapi.Schema(type=openapi.TYPE_NUMBER, format='float'),
                    'memory_utilization': openapi.Schema(type=openapi.TYPE_NUMBER, format='float'),
                    'disk_utilization': openapi.Schema(type=openapi.TYPE_NUMBER, format='float'),
                    'uptime': openapi.Schema(type=openapi.TYPE_STRING),
                    'services': openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'active': openapi.Schema(type=openapi.TYPE_INTEGER),
                            'inactive': openapi.Schema(type=openapi.TYPE_INTEGER)
                        }
                    )
                }
            ),
            'network_metrics': openapi.Schema(
                type=openapi.TYPE_OBJECT,
                description="Métriques réseau",
                properties={
                    'devices_count': openapi.Schema(type=openapi.TYPE_INTEGER),
                    'links_active': openapi.Schema(type=openapi.TYPE_INTEGER),
                    'bandwidth_usage': openapi.Schema(type=openapi.TYPE_NUMBER, format='float'),
                    'alerts_count': openapi.Schema(type=openapi.TYPE_INTEGER)
                }
            ),
            'security_metrics': openapi.Schema(
                type=openapi.TYPE_OBJECT,
                description="Métriques sécurité",
                properties={
                    'blocked_ips': openapi.Schema(type=openapi.TYPE_INTEGER),
                    'security_alerts': openapi.Schema(type=openapi.TYPE_INTEGER),
                    'failed_attempts': openapi.Schema(type=openapi.TYPE_INTEGER)
                }
            ),
            'timestamp': openapi.Schema(type=openapi.TYPE_STRING, format='datetime'),
            'refresh_interval': openapi.Schema(type=openapi.TYPE_INTEGER, description="Intervalle de rafraîchissement en secondes")
        }
    )
}

# ⚠️ EXEMPLES DOCUMENTAIRES UNIQUEMENT - NE PAS UTILISER EN PRODUCTION
# Ces exemples sont destinés à la documentation API uniquement
# En production, les données réelles remplacent ces exemples
dashboard_response_example = {
    "_documentation_note": "⚠️ Exemple documentaire - Données réelles différentes en production",
    "system": {
        "cpu_usage": 45.2,
        "memory_usage": 67.8,
        "disk_usage": 52.3,
        "uptime": "4d 6h 23m",
        "services": {
            "active": 18,
            "inactive": 2
        }
    },
    "network": {
        "devices_count": 24,
        "links_active": 42,
        "bandwidth_usage": 850.4,
        "alerts": 2
    }
}

topology_discovery_example = {
    "_documentation_note": "⚠️ Exemple documentaire - Données réelles différentes en production",
    "id": 123,
    "name": "Main Network",
    "created_at": "2023-10-15T14:32:45Z",
    "updated_at": "2023-10-15T15:02:12Z",
    "nodes": [
        {"id": 1, "name": "Switch-01", "ip": "192.168.1.1", "type": "switch", "status": "active"},
        {"id": 2, "name": "Router-02", "ip": "192.168.1.2", "type": "router", "status": "active"},
        {"id": 3, "name": "Server-01", "ip": "192.168.1.10", "type": "server", "status": "active"}
    ],
    "links": [
        {"id": 1, "source": 1, "target": 2, "bandwidth": "1Gbps", "status": "up"},
        {"id": 2, "source": 2, "target": 3, "bandwidth": "1Gbps", "status": "up"}
    ]
}

device_management_example = {
    "_documentation_note": "⚠️ Exemple documentaire - Données réelles différentes en production",
    "id": 42,
    "name": "Router-Core-01",
    "ip_address": "192.168.10.1",
    "type": "router",
    "vendor": "Cisco",
    "model": "ASR 9000",
    "location": "DC-Main",
    "status": "active",
    "uptime": "45d 3h 12m",
    "os_version": "IOS XR 7.1.2",
    "serial_number": "FTXY12345678",
    "last_seen": "2023-10-20T08:45:12Z",
    "interfaces": [
        {
            "id": 1, 
            "name": "GigabitEthernet0/0/0", 
            "ip": "192.168.10.1",
            "mac": "00:11:22:33:44:55", 
            "status": "up",
            "speed": "1Gbps"
        },
        {
            "id": 2, 
            "name": "GigabitEthernet0/0/1", 
            "ip": "10.0.1.1",
            "mac": "00:11:22:33:44:56", 
            "status": "up",
            "speed": "1Gbps"
        }
    ]
}

search_example = {
    "_documentation_note": "⚠️ Exemple documentaire - Données réelles différentes en production",
    "query": "router core",
    "results": [
        {
            "type": "device",
            "id": 42,
            "name": "Router-Core-01",
            "match": "name",
            "score": 0.95,
            "url": "/api/devices/42/"
        },
        {
            "type": "device",
            "id": 43,
            "name": "Router-Core-02",
            "match": "name",
            "score": 0.94,
            "url": "/api/devices/43/"
        },
        {
            "type": "log",
            "id": 12345,
            "content": "Warning: Router-Core-01 CPU usage high",
            "match": "content",
            "score": 0.85,
            "timestamp": "2023-10-19T15:23:42Z",
            "url": "/api/logs/12345/"
        }
    ],
    "total_results": 3,
    "query_time_ms": 42
}

prometheus_example = {
    "_documentation_note": "⚠️ Exemple documentaire - Données réelles différentes en production",
    "status": "success",
    "data": {
        "resultType": "vector",
        "result": [
            {
                "metric": {
                    "instance": "192.168.1.1:9100",
                    "job": "node",
                    "__name__": "node_cpu_seconds_total",
                    "cpu": "0",
                    "mode": "idle"
                },
                "value": [1634812345.123, "2345.6"]
            },
            {
                "metric": {
                    "instance": "192.168.1.1:9100",
                    "job": "node",
                    "__name__": "node_cpu_seconds_total",
                    "cpu": "0",
                    "mode": "user"
                },
                "value": [1634812345.123, "567.8"]
            }
        ]
    }
}

grafana_example = {
    "_documentation_note": "⚠️ Exemple documentaire - Données réelles différentes en production",
    "id": 12345,
    "uid": "abcdef",
    "title": "Network Overview",
    "tags": ["network", "overview"],
    "timezone": "browser",
    "schemaVersion": 16,
    "version": 1,
    "refresh": "30s",
    "panels": [
        {
            "id": 1,
            "type": "graph",
            "title": "CPU Usage",
            "gridPos": {"h": 8, "w": 12, "x": 0, "y": 0}
        },
        {
            "id": 2,
            "type": "graph",
            "title": "Memory Usage",
            "gridPos": {"h": 8, "w": 12, "x": 12, "y": 0}
        }
    ]
}

fail2ban_example = {
    "_documentation_note": "⚠️ Exemple documentaire - Données réelles différentes en production",
    "jails": [
        {
            "name": "sshd",
            "enabled": True,
            "currentlyBanned": 3,
            "totalBanned": 27,
            "bannedIPs": ["203.0.113.1", "198.51.100.2", "198.51.100.3"]
        },
        {
            "name": "nginx-http-auth",
            "enabled": True,
            "currentlyBanned": 1,
            "totalBanned": 12,
            "bannedIPs": ["203.0.113.5"]
        }
    ]
}

suricata_example = {
    "_documentation_note": "⚠️ Exemple documentaire - Données réelles différentes en production",
    "alerts": [
        {
            "id": 12345,
            "timestamp": "2023-10-20T14:52:23.123456",
            "src_ip": "203.0.113.1",
            "src_port": 54321,
            "dest_ip": "192.168.1.10",
            "dest_port": 80,
            "proto": "TCP",
            "severity": "high",
            "signature": "ET EXPLOIT Possible CVE-2023-12345 Attempt",
            "sid": 2034567
        },
        {
            "id": 12346,
            "timestamp": "2023-10-20T14:53:12.234567",
            "src_ip": "198.51.100.2",
            "src_port": 56789,
            "dest_ip": "192.168.1.20",
            "dest_port": 443,
            "proto": "TCP",
            "severity": "medium",
            "signature": "ET SCAN Potential SSH Scan",
            "sid": 2012345
        }
    ],
    "total": 2,
    "timespan": "5m"
}

# Ajout d'une section d'exemples pour les scénarios d'utilisation communs
usage_examples = {
    "authenticating": {
        "summary": "Authentification",
        "description": """
## Authentification à l'API

Pour accéder aux endpoints protégés, vous devez inclure un token JWT dans l'en-tête Authorization.

```bash
# Obtenir un token
curl -X POST "https://api.example.com/api/v1/auth/token/" \\
  -H "Content-Type: application/json" \\
  -d '{"username": "votre_utilisateur", "password": "votre_mot_de_passe"}'

# Exemple de réponse
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}

# Utiliser le token pour une requête
curl "https://api.example.com/api/v1/dashboards/system/" \\
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
```
        """
    },
    "dashboard_workflow": {
        "summary": "Flux de travail avec les tableaux de bord",
        "description": """
## Exemples d'utilisation des APIs de tableaux de bord

### 1. Récupérer les données du tableau de bord système

```bash
curl "https://api.example.com/api/v1/dashboards/system/" \\
  -H "Authorization: Bearer votre_token"
```

### 2. Récupérer les données avec une plage de temps spécifique

```bash
curl "https://api.example.com/api/v1/dashboards/network/?time_range=6h" \\
  -H "Authorization: Bearer votre_token"
```

### 3. Créer un tableau de bord personnalisé

```bash
curl -X POST "https://api.example.com/api/v1/dashboards/" \\
  -H "Authorization: Bearer votre_token" \\
  -H "Content-Type: application/json" \\
  -d '{
    "name": "Mon tableau de bord",
    "dashboard_type": "custom",
    "description": "Dashboard personnalisé pour le monitoring",
    "widgets": [
      {
        "id": "widget1",
        "type": "alerts",
        "title": "Alertes récentes",
        "position": {"x": 0, "y": 0},
        "size": {"width": 6, "height": 4},
        "config": {"severity": ["critical", "warning"]}
      },
      {
        "id": "widget2",
        "type": "device_status",
        "title": "Équipements",
        "position": {"x": 6, "y": 0},
        "size": {"width": 6, "height": 4},
        "config": {"types": ["router", "switch"]}
      }
    ]
  }'
```
        """
    },
    "topology_discovery": {
        "summary": "Découverte de topologie",
        "description": """
## Exemples d'utilisation des APIs de découverte de topologie

### 1. Démarrer une découverte de topologie

```bash
curl -X POST "https://api.example.com/api/v1/topology/discovery/" \\
  -H "Authorization: Bearer votre_token" \\
  -H "Content-Type: application/json" \\
  -d '{
    "network_id": "reseau-principal",
    "discovery_method": "snmp",
    "start_ip": "192.168.1.1",
    "end_ip": "192.168.1.254",
    "community_string": "public",
    "scan_interval": 3600,
    "depth": 2,
    "discover_vlans": true
  }'
```

### 2. Obtenir la carte du réseau

```bash
curl "https://api.example.com/api/v1/topology/network-map/?network_id=reseau-principal" \\
  -H "Authorization: Bearer votre_token"
```

### 3. Analyser les connexions entre équipements

```bash
curl "https://api.example.com/api/v1/topology/connections/?device_id=42" \\
  -H "Authorization: Bearer votre_token"
```

### 4. Découvrir les chemins réseau entre deux équipements

```bash
curl "https://api.example.com/api/v1/topology/path-discovery/?source_ip=192.168.1.1&destination_ip=192.168.1.100" \\
  -H "Authorization: Bearer votre_token"
```
        """
    },
    "monitoring_integration": {
        "summary": "Intégration avec les outils de monitoring",
        "description": """
## Exemples d'intégration avec le monitoring

### 1. Requête Prometheus

```bash
curl "https://api.example.com/api/v1/prometheus/query/?query=up" \\
  -H "Authorization: Bearer votre_token"
```

### 2. Requête avec plage temporelle

```bash
curl "https://api.example.com/api/v1/prometheus/range/?query=node_cpu_seconds_total&start=2022-01-01T00:00:00Z&end=2022-01-02T00:00:00Z&step=1h" \\
  -H "Authorization: Bearer votre_token"
```

### 3. Métriques d'un équipement spécifique

```bash
curl "https://api.example.com/api/v1/prometheus/device/192.168.1.1/metrics/?metrics=cpu,memory" \\
  -H "Authorization: Bearer votre_token"
```

### 4. Création d'un dashboard Grafana pour un équipement

```bash
curl -X POST "https://api.example.com/api/v1/grafana/device-dashboard/42/" \\
  -H "Authorization: Bearer votre_token"
```
        """
    },
    "security_management": {
        "summary": "Gestion de la sécurité",
        "description": """
## Exemples d'utilisation des APIs de sécurité

### 1. Obtenir l'état des bannissements Fail2ban

```bash
curl "https://api.example.com/api/v1/fail2ban/jail-status/" \\
  -H "Authorization: Bearer votre_token"
```

### 2. Bannir manuellement une adresse IP

```bash
curl -X POST "https://api.example.com/api/v1/fail2ban/ban-ip/" \\
  -H "Authorization: Bearer votre_token" \\
  -H "Content-Type: application/json" \\
  -d '{
    "ip": "203.0.113.1",
    "jail": "sshd",
    "reason": "Accès suspect",
    "duration": 3600
  }'
```

### 3. Récupérer les alertes Suricata

```bash
curl "https://api.example.com/api/v1/suricata/alerts/?severity=high" \\
  -H "Authorization: Bearer votre_token"
```

### 4. Ajouter une règle Suricata personnalisée

```bash
curl -X POST "https://api.example.com/api/v1/suricata/add-rule/" \\
  -H "Authorization: Bearer votre_token" \\
  -H "Content-Type: application/json" \\
  -d '{
    "rule": "alert tcp any any -> $HOME_NET 22 (msg:\"SSH tentative d'\''intrusion\"; flow:to_server; threshold: type threshold, track by_src, count 5, seconds 60; classtype:attempted-admin; sid:1000001; rev:1;)",
    "description": "Détecte les tentatives d'\''intrusion SSH",
    "enabled": true
  }'
```
        """
    },
    "error_handling": {
        "summary": "Gestion des erreurs",
        "description": """
## Codes d'erreur et gestion

### Structure des erreurs

Toutes les réponses d'erreur suivent le format standard suivant:

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Description détaillée de l'erreur",
    "details": {
      "field1": ["Message d'erreur spécifique au champ"],
      "field2": ["Autre message d'erreur"]
    }
  },
  "timestamp": "2023-10-25T14:30:15Z",
  "request_id": "req-123456-abcd"
}
```

### Codes d'erreur courants

- **AUTH_REQUIRED**: Authentification requise
- **INVALID_TOKEN**: Token d'authentification invalide ou expiré
- **PERMISSION_DENIED**: Permissions insuffisantes
- **VALIDATION_ERROR**: Données de requête invalides
- **RESOURCE_NOT_FOUND**: Ressource demandée introuvable
- **OPERATION_FAILED**: Échec de l'opération demandée
- **SERVICE_UNAVAILABLE**: Service temporairement indisponible
- **RATE_LIMIT_EXCEEDED**: Limite de débit dépassée

### Gestion des erreurs de validation

Pour les erreurs de validation, le champ `details` contiendra des informations spécifiques sur chaque champ en erreur:

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Données de requête invalides",
    "details": {
      "name": ["Ce champ est requis"],
      "ip_address": ["Adresse IP invalide"],
      "port": ["La valeur doit être comprise entre 1 et 65535"]
    }
  },
  "timestamp": "2023-10-25T14:30:15Z",
  "request_id": "req-123456-abcd"
}
```
        """
    }
}

# Créer la vue de schéma Swagger
schema_view = get_schema_view(
    openapi.Info(
        title="views",
        default_version='v2.0',
        description="""
# views - API Network Management

Interface unifiée pour la gestion des infrastructures réseau avec fonctionnalités CRUD complètes, 
pagination avancée, filtrage dynamique et intégrations enterprise.

## Architecture

Le module utilise une architecture orientée services avec :
- **ViewSets REST** : CRUD complet pour toutes les ressources
- **Pagination Avancée** : Cursor-based et offset pour les performances
- **Cache Intelligent** : Redis TTL configurables par endpoint
- **Filtrage Dynamique** : Multi-critères avec opérateurs booléens

## Authentification

Toutes les requêtes nécessitent une authentification :
```
Authorization: Bearer <votre_token>
```

## Démarrage Rapide

1. **Obtenir les métriques système :**
   ```bash
   GET /api/views/dashboards/system/
   ```

2. **Lister les équipements :**
   ```bash
   GET /api/views/device-management/
   ```

3. **Démarrer une découverte réseau :**
   ```bash
   POST /api/views/topology-discovery/
   ```

4. **Recherche globale :**
   ```bash
   GET /api/views/search/?q=router
   ```

## Fonctionnalités

- **CRUD complet** : Create, Read, Update, Delete sur toutes ressources
- **Pagination intelligente** : Cursor-based, offset, infinite scroll
- **Filtrage dynamique** : Multi-critères, tri, recherche textuelle
- **Cache Redis** : Performance optimisée, TTL configurables
- **Bulk operations** : Opérations massives optimisées
- **Permissions granulaires** : RBAC, ACL, resource-level
- **Export multi-format** : JSON, CSV, PDF, Excel
- **Rate limiting** : Protection charge, quotas utilisateur
- **Monitoring API** : Métriques utilisation, performance
- **Health checks** : Status services, dépendances

## Codes de Réponse Standards

| Code | Statut | Description |
|------|--------|-------------|
| **200** | OK | Opération réussie |
| **201** | Created | Ressource créée |
| **204** | No Content | Suppression réussie |
| **400** | Bad Request | Données invalides |
| **401** | Unauthorized | Authentification requise |
| **403** | Forbidden | Permissions insuffisantes |
| **404** | Not Found | Ressource inexistante |
| **409** | Conflict | Conflit ressource |
| **422** | Unprocessable | Validation échouée |
| **429** | Rate Limited | Débit dépassé |
| **500** | Server Error | Erreur interne |
| **503** | Unavailable | Service indisponible |
        
## Liens Utiles

- [Guide d'Intégration](../README.md)
- [Exemples de Code](../docs/examples/)
- [Schémas OpenAPI](./swagger_schemas.py)
        """,
        terms_of_service="https://nms.example.com/terms/",
        contact=openapi.Contact(
            name="Équipe Network Management Views",
            email="nms-api@example.com",
            url="https://nms.example.com/support/"
        ),
        license=openapi.License(
            name="MIT License",
            url="https://opensource.org/licenses/MIT"
        ),
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
    patterns=None,
    generator_class=None,
    authentication_classes=None,
)

# Exemples de requêtes pour la documentation
REQUEST_EXAMPLES = {
    'create_dashboard': {
        'summary': 'Créer un tableau de bord personnalisé',
        'value': {
            'name': 'Dashboard Réseau Principal',
            'type': 'network',
            'description': 'Vue d\'ensemble des équipements réseau critiques',
            'widgets': [
                {
                    'type': 'device_status',
                    'title': 'Statut Équipements',
                    'position': {'x': 0, 'y': 0},
                    'size': {'width': 6, 'height': 4},
                    'config': {
                        'device_types': ['router', 'switch'],
                        'show_offline': True
                    }
                },
                {
                    'type': 'network_topology',
                    'title': 'Topologie Réseau',
                    'position': {'x': 6, 'y': 0},
                    'size': {'width': 6, 'height': 4},
                    'config': {
                        'auto_layout': True,
                        'show_labels': True
                    }
                }
            ]
        }
    },
    'create_device': {
        'summary': 'Ajouter un nouvel équipement',
        'value': {
            'name': 'Router-Core-01',
            'type': 'router',
            'ip_address': '192.168.1.1',
            'location': 'DC-Main-Rack-01',
            'vendor': 'Cisco',
            'model': 'ASR 9000',
            'os_version': 'IOS XR 7.1.2',
            'description': 'Routeur principal datacenter',
            'snmp_community': 'public',
            'snmp_version': '2c',
            'monitoring_enabled': True,
            'backup_enabled': True
        }
    },
    'update_device': {
        'summary': 'Mettre à jour un équipement',
        'value': {
            'name': 'Router-Core-01-Updated',
            'location': 'DC-Backup-Rack-05',
            'os_version': 'IOS XR 7.2.1',
            'description': 'Routeur principal mis à niveau',
            'maintenance_window': '02:00-04:00',
            'contact_info': 'admin@network.local'
        }
    },
    'bulk_create_devices': {
        'summary': 'Création en masse d\'équipements',
        'value': {
            'devices': [
                {
                    'name': 'Switch-Access-01',
                    'type': 'switch',
                    'ip_address': '192.168.2.10',
                    'location': 'Etage-1-Bureau'
                },
                {
                    'name': 'Switch-Access-02',
                    'type': 'switch',
                    'ip_address': '192.168.2.11',
                    'location': 'Etage-2-Bureau'
                },
                {
                    'name': 'AP-WiFi-01',
                    'type': 'access_point',
                    'ip_address': '192.168.3.10',
                    'location': 'Etage-1-Couloir'
                }
            ]
        }
    },
    'start_topology_discovery': {
        'summary': 'Lancer une découverte de topologie',
        'value': {
            'name': 'Découverte Réseau Principal',
            'discovery_method': 'snmp',
            'start_ip': '192.168.1.1',
            'end_ip': '192.168.1.254',
            'snmp_community': 'public',
            'snmp_version': '2c',
            'discover_vlans': True,
            'discover_interfaces': True,
            'max_depth': 3,
            'timeout': 30,
            'parallel_scans': 10
        }
    },
    'global_search': {
        'summary': 'Recherche globale multi-critères',
        'value': {
            'query': 'router core online',
            'resource_types': ['device', 'alert', 'topology'],
            'filters': {
                'status': 'online',
                'location': 'DC-Main',
                'type': 'router'
            },
            'group_by_type': True,
            'max_per_type': 20,
            'use_cache': True,
            'include_suggestions': True
        }
    },
    'prometheus_query': {
        'summary': 'Requête métriques Prometheus',
        'value': {
            'query': 'rate(cpu_usage_total[5m])',
            'start': '2024-01-01T00:00:00Z',
            'end': '2024-01-01T23:59:59Z',
            'step': '1h',
            'timeout': '30s'
        }
    },
    'create_grafana_dashboard': {
        'summary': 'Créer un dashboard Grafana',
        'value': {
            'title': 'Monitoring Réseau - Vue d\'ensemble',
            'tags': ['network', 'monitoring', 'infrastructure'],
            'panels': [
                {
                    'title': 'CPU Usage',
                    'type': 'graph',
                    'targets': [
                        {
                            'expr': 'rate(cpu_usage_total[5m])',
                            'legendFormat': '{{instance}}'
                        }
                    ]
                },
                {
                    'title': 'Network Throughput',
                    'type': 'stat',
                    'targets': [
                        {
                            'expr': 'rate(network_bytes_total[5m])',
                            'legendFormat': 'Throughput'
                        }
                    ]
                }
            ],
            'time': {
                'from': 'now-1h',
                'to': 'now'
            },
            'refresh': '30s',
            'auto_refresh': True
        }
    },
    'security_ban_ip': {
        'summary': 'Bannir une adresse IP avec Fail2ban',
        'value': {
            'ip': '203.0.113.100',
            'jail': 'sshd',
            'reason': 'Tentatives de connexion suspectes',
            'duration': 3600,
            'notify_admin': True,
            'add_to_blacklist': True
        }
    },
    'create_suricata_rule': {
        'summary': 'Créer une règle Suricata personnalisée',
        'value': {
            'rule': 'alert tcp any any -> $HOME_NET 22 (msg:"SSH Brute Force Attempt"; flow:to_server; threshold: type threshold, track by_src, count 5, seconds 60; classtype:attempted-admin; sid:1000001; rev:1;)',
            'description': 'Détection de tentatives de force brute SSH',
            'category': 'brute-force',
            'severity': 'high',
            'enabled': True,
            'action': 'alert'
        }
    }
}

# Dictionnaire des exemples de réponses par endpoint
RESPONSE_EXAMPLES = {
    'dashboard_system': dashboard_response_example,
    'topology_discovery': topology_discovery_example,
    'device_management': device_management_example,
    'global_search': search_example,
    'prometheus_metrics': prometheus_example,
    'grafana_dashboard': grafana_example,
    'fail2ban_status': fail2ban_example,
    'suricata_alerts': suricata_example,
} 