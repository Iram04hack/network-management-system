"""
Configuration des URLs enrichie pour l'application api_clients.

Ce module définit une API REST complète et unifiée pour tous les clients
avec une documentation Swagger enrichie et des fonctionnalités CRUD complètes.
"""

from django.urls import path, include
from rest_framework import permissions
from rest_framework.routers import DefaultRouter
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from . import views_enhanced as views

# Configuration enrichie de Swagger UI
schema_view = get_schema_view(
    openapi.Info(
        title="🚀 API Clients - Documentation Complète et Unifiée",
        default_version='v2.0',
        description="""
# 🎯 API de Gestion des Clients Réseau - Version Enrichie

Cette API fournit une interface **unifiée** et **complète** pour l'interaction avec tous les clients 
du système de gestion réseau. Elle a été conçue pour offrir une expérience développeur optimale 
avec une documentation automatique détaillée.

## 🏗️ Architecture et Organisation

### 📡 **Clients Réseau**
- **GNS3Client** - Gestion complète des topologies et simulations réseau
  - Projets : CRUD complet + opérations avancées (open/close/export)
  - Nœuds : CRUD complet + contrôle (start/stop/clone)
  - Simulations : Gestion des états et configurations
- **SNMPClient** - Interrogation avancée des équipements réseau
  - Requêtes GET/SET/WALK avec validation
  - Découverte automatique de voisins et interfaces
  - Surveillance des métriques système et réseau
- **NetflowClient** - Analyse sophistiquée des flux de trafic
  - Analyse en temps réel et historique
  - Détection d'anomalies et de comportements suspects
  - Matrices de trafic et top talkers

### 📊 **Clients Monitoring**
- **PrometheusClient** - Collecte de métriques et alertes
  - Requêtes PromQL avancées avec validation
  - Gestion complète des règles d'alerte
  - Fédération et agrégation de métriques
- **GrafanaClient** - Tableaux de bord et visualisations (CRUD complet)
  - Dashboards : Création/Modification/Suppression/Import/Export
  - Sources de données : Gestion complète avec tests de connexion
  - Alertes : Configuration avancée avec notifications
  - Utilisateurs : Gestion des permissions et rôles
- **ElasticsearchClient** - Indexation et recherche avancée (CRUD complet)
  - Indices : Création/Configuration/Suppression avec templates
  - Documents : Indexation/Recherche/Mise à jour/Suppression
  - Requêtes complexes avec agrégations
  - Gestion des alias et templates d'index
- **NetdataClient** - Monitoring temps réel des systèmes
  - Métriques système en temps réel
  - Alertes automatiques configurables
  - Dashboards interactifs
- **NtopngClient** - Analyse avancée du trafic réseau
  - Deep Packet Inspection (DPI)
  - Géolocalisation du trafic
  - Détection d'anomalies et menaces

### 🏢 **Clients Infrastructure**
- **HAProxyClient** - Load balancing et proxy avancé
  - Statistiques détaillées en temps réel
  - Gestion dynamique des serveurs et backends
  - Configuration des règles de routage
- **TrafficControlClient** - Gestion QoS Linux (tc)
  - Limitation de bande passante par interface
  - Priorisation du trafic par classes
  - Filtres avancés et politiques de QoS

### 🔒 **Clients Sécurité**
- **Fail2BanClient** - Protection contre les intrusions (CRUD complet)
  - Jails : Configuration/Gestion/Monitoring
  - Bannissements : Manuel/Automatique avec durées personnalisées
  - Logs et statistiques de sécurité
- **SuricataClient** - Détection d'intrusions IDS/IPS
  - Règles de sécurité : Gestion/Activation/Désactivation
  - Analyse des flux et détection d'anomalies
  - Alertes de sécurité en temps réel

## 🚀 **Fonctionnalités Avancées**

### 📦 **Opérations en Lot (Bulk Operations)**
- Exécution parallèle ou séquentielle
- Gestion des erreurs avec continue_on_error
- Statistiques détaillées d'exécution
- Support timeout et annulation

### 🏥 **Monitoring de Santé Complet**
- Vérification de connectivité en temps réel
- Métriques de performance et latence
- Tests fonctionnels spécifiques par client
- Alertes automatiques sur les dysfonctionnements

### 🔍 **Filtrage et Recherche Avancés**
- Filtres multiples sur tous les endpoints
- Recherche textuelle avec support wildcards
- Pagination automatique pour les grandes collections
- Tri dynamique sur tous les champs

### 📈 **Métriques et Analytics**
- Temps de réponse par endpoint
- Taux de succès/échec des opérations
- Utilisation des ressources par client
- Statistiques d'usage et tendances

## 💡 **Avantages de cette API**

### 🤖 **Documentation Automatique**
- ✅ Génération automatique par introspection du code
- ✅ Pas d'erreurs manuelles dans les schémas
- ✅ Mise à jour automatique lors des modifications
- ✅ Cohérence garantie entre code et documentation
- ✅ Exemples concrets pour chaque endpoint

### 🏷️ **Organisation Unifiée**
- ✅ Tag unique "Clients" pour une navigation simplifiée
- ✅ Structure cohérente sur tous les endpoints
- ✅ Conventions de nommage uniformes
- ✅ Codes de réponse standardisés

### 🔒 **Sécurité et Fiabilité**
- ✅ Validation robuste des paramètres d'entrée
- ✅ Gestion d'erreurs détaillée avec codes spécifiques
- ✅ Circuit breakers pour la résilience
- ✅ Retry automatique avec backoff exponentiel
- ✅ Logs détaillés pour le debugging

### ⚡ **Performance Optimisée**
- ✅ Cache intelligent pour les opérations coûteuses
- ✅ Connexions persistantes avec pooling
- ✅ Opérations asynchrones quand possible
- ✅ Compression automatique des réponses

## 📚 **Guide d'Utilisation**

### 🔗 **Endpoints Principaux**
- **GET** `/` - Accueil et métadonnées de l'API
- **GET** `/health/` - Santé globale de tous les clients
- **GET** `/network/` - Statut des clients réseau
- **GET** `/monitoring/` - Statut des clients monitoring
- **GET** `/security/` - Statut des clients sécurité
- **GET** `/infrastructure/` - Statut des clients infrastructure

### 🎯 **Exemples d'Utilisation**

#### Créer un projet GNS3
```bash
curl -X POST "https://localhost:8000/api/clients/network/gns3/projects/" \\
     -H "Content-Type: application/json" \\
     -d '{"name": "Mon Réseau", "path": "/opt/gns3/mon-reseau"}'
```

#### Bannir une IP avec Fail2Ban
```bash
curl -X POST "https://localhost:8000/api/clients/security/fail2ban/ban/" \\
     -H "Content-Type: application/json" \\
     -d '{"ip_address": "192.168.1.100", "jail_name": "sshd", "ban_time": 3600}'
```

#### Créer un indice Elasticsearch
```bash
curl -X POST "https://localhost:8000/api/clients/monitoring/elasticsearch/indices/" \\
     -H "Content-Type: application/json" \\
     -d '{"index_name": "logs-app", "settings": {"number_of_shards": 1}}'
```

#### Opération en lot sur GNS3
```bash
curl -X POST "https://localhost:8000/api/clients/bulk/gns3/" \\
     -H "Content-Type: application/json" \\
     -d '{"operation": "bulk_create_projects", "items": [{"name": "Projet1"}, {"name": "Projet2"}]}'
```

## 🆘 **Support et Contact**
- **Documentation** : Cette interface Swagger
- **Code Source** : Module `api_clients` du projet NMS
- **Logs** : Consultez les logs Django pour le debugging
- **Tests** : Utilisez l'interface "Try it out" ci-dessous

---

🎉 **Bonne utilisation de l'API !** Cette documentation est générée automatiquement 
et reste toujours à jour avec le code source.
        """,
        terms_of_service="https://www.nms.local/terms/",
        contact=openapi.Contact(email="admin@nms.local", name="Équipe NMS"),
        license=openapi.License(name="MIT License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
    patterns=[
        path('api/clients/', include('api_clients.urls')),
    ],
)

urlpatterns = [
    # ==================== DOCUMENTATION SWAGGER ENRICHIE ====================
    path('', schema_view.with_ui('swagger', cache_timeout=0), name='api-clients-home'),
    path('docs/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    path('swagger.json', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('openapi.yaml', schema_view.without_ui(cache_timeout=0), name='schema-yaml'),
    
    # ==================== STATUT DES CLIENTS ====================
    path('network/', views.network_clients, name='network-clients-status'),
    path('monitoring/', views.monitoring_clients, name='monitoring-clients-status'),
    path('infrastructure/', views.infrastructure_clients, name='infrastructure-clients-status'),
    path('security/', views.security_clients, name='security-clients-status'),
    
    # ==================== CLIENTS RÉSEAU - GNS3 ====================
    path('network/gns3/projects/', views.gns3_projects, name='gns3-projects-list'),
    path('network/gns3/projects/create/', views.create_gns3_project, name='gns3-projects-create'),
    path('network/gns3/projects/<str:project_id>/', views.get_gns3_project, name='gns3-project-detail'),
    path('network/gns3/projects/<str:project_id>/update/', views.update_gns3_project, name='gns3-project-update'),
    path('network/gns3/projects/<str:project_id>/delete/', views.delete_gns3_project, name='gns3-project-delete'),
    path('network/gns3/projects/<str:project_id>/open/', views.open_gns3_project, name='gns3-project-open'),
    path('network/gns3/projects/<str:project_id>/close/', views.close_gns3_project, name='gns3-project-close'),
    
    # Gestion des nœuds GNS3
    path('network/gns3/projects/<str:project_id>/nodes/', views.gns3_project_nodes, name='gns3-project-nodes'),
    path('network/gns3/projects/<str:project_id>/nodes/create/', views.create_gns3_node, name='gns3-node-create'),
    path('network/gns3/projects/<str:project_id>/nodes/<str:node_id>/', views.get_gns3_node, name='gns3-node-detail'),
    path('network/gns3/projects/<str:project_id>/nodes/<str:node_id>/update/', views.update_gns3_node, name='gns3-node-update'),
    path('network/gns3/projects/<str:project_id>/nodes/<str:node_id>/delete/', views.delete_gns3_node, name='gns3-node-delete'),
    path('network/gns3/projects/<str:project_id>/nodes/<str:node_id>/start/', views.start_gns3_node, name='gns3-node-start'),
    path('network/gns3/projects/<str:project_id>/nodes/<str:node_id>/stop/', views.stop_gns3_node, name='gns3-node-stop'),
    
    # ==================== CLIENTS RÉSEAU - SNMP ====================
    path('network/snmp/query/', views.snmp_query, name='snmp-query'),
    path('network/snmp/walk/', views.snmp_walk, name='snmp-walk'),
    path('network/snmp/set/', views.snmp_set, name='snmp-set'),
    path('network/snmp/system/', views.snmp_system_info, name='snmp-system-info'),
    path('network/snmp/interfaces/', views.snmp_interfaces, name='snmp-interfaces'),
    path('network/snmp/interfaces/<str:interface_index>/stats/', views.snmp_interface_stats, name='snmp-interface-stats'),
    path('network/snmp/discover/', views.snmp_discover_neighbors, name='snmp-discover-neighbors'),
    
    # ==================== CLIENTS RÉSEAU - NETFLOW ====================
    path('network/netflow/flows/', views.netflow_query_flows, name='netflow-query-flows'),
    path('network/netflow/top-talkers/', views.netflow_top_talkers, name='netflow-top-talkers'),
    path('network/netflow/protocols/', views.netflow_protocol_distribution, name='netflow-protocols'),
    path('network/netflow/anomalies/', views.netflow_detect_anomalies, name='netflow-anomalies'),
    path('network/netflow/matrix/', views.netflow_traffic_matrix, name='netflow-traffic-matrix'),
    path('network/netflow/config/', views.netflow_config, name='netflow-config'),
    path('network/netflow/exporters/', views.netflow_exporters, name='netflow-exporters'),
    path('network/netflow/exporters/create/', views.create_netflow_exporter, name='netflow-exporter-create'),
    path('network/netflow/exporters/<str:exporter_id>/delete/', views.delete_netflow_exporter, name='netflow-exporter-delete'),
    
    # ==================== CLIENTS MONITORING - PROMETHEUS ====================
    path('monitoring/prometheus/query/', views.prometheus_query, name='prometheus-query'),
    path('monitoring/prometheus/query-range/', views.prometheus_query_range, name='prometheus-query-range'),
    path('monitoring/prometheus/targets/', views.prometheus_targets, name='prometheus-targets'),
    path('monitoring/prometheus/alerts/', views.prometheus_alerts, name='prometheus-alerts'),
    path('monitoring/prometheus/rules/', views.prometheus_rules, name='prometheus-rules'),
    path('monitoring/prometheus/series/', views.prometheus_series, name='prometheus-series'),
    path('monitoring/prometheus/label-values/', views.prometheus_label_values, name='prometheus-label-values'),
    
    # ==================== CLIENTS MONITORING - GRAFANA ====================
    path('monitoring/grafana/dashboards/', views.grafana_dashboards, name='grafana-dashboards-list'),
    path('monitoring/grafana/dashboards/create/', views.create_grafana_dashboard, name='grafana-dashboard-create'),
    path('monitoring/grafana/dashboards/<str:uid>/', views.get_grafana_dashboard, name='grafana-dashboard-detail'),
    path('monitoring/grafana/dashboards/<str:uid>/update/', views.update_grafana_dashboard, name='grafana-dashboard-update'),
    path('monitoring/grafana/dashboards/<str:uid>/delete/', views.delete_grafana_dashboard, name='grafana-dashboard-delete'),
    path('monitoring/grafana/dashboards/<str:uid>/export/', views.export_grafana_dashboard, name='grafana-dashboard-export'),
    
    # Sources de données Grafana
    path('monitoring/grafana/datasources/', views.grafana_datasources, name='grafana-datasources-list'),
    path('monitoring/grafana/datasources/create/', views.create_grafana_datasource, name='grafana-datasource-create'),
    path('monitoring/grafana/datasources/<int:datasource_id>/', views.get_grafana_datasource, name='grafana-datasource-detail'),
    path('monitoring/grafana/datasources/<int:datasource_id>/update/', views.update_grafana_datasource, name='grafana-datasource-update'),
    path('monitoring/grafana/datasources/<int:datasource_id>/delete/', views.delete_grafana_datasource, name='grafana-datasource-delete'),
    path('monitoring/grafana/datasources/<int:datasource_id>/test/', views.test_grafana_datasource, name='grafana-datasource-test'),
    
    # Alertes Grafana
    path('monitoring/grafana/alerts/', views.grafana_alerts, name='grafana-alerts-list'),
    path('monitoring/grafana/alerts/create/', views.create_grafana_alert, name='grafana-alert-create'),
    path('monitoring/grafana/alerts/<int:alert_id>/', views.get_grafana_alert, name='grafana-alert-detail'),
    path('monitoring/grafana/alerts/<int:alert_id>/update/', views.update_grafana_alert, name='grafana-alert-update'),
    path('monitoring/grafana/alerts/<int:alert_id>/delete/', views.delete_grafana_alert, name='grafana-alert-delete'),
    
    # Utilisateurs Grafana
    path('monitoring/grafana/users/', views.grafana_users, name='grafana-users-list'),
    path('monitoring/grafana/users/current/', views.grafana_current_user, name='grafana-current-user'),
    
    # ==================== CLIENTS MONITORING - ELASTICSEARCH ====================
    path('monitoring/elasticsearch/indices/', views.elasticsearch_indices, name='elasticsearch-indices-list'),
    path('monitoring/elasticsearch/indices/create/', views.create_elasticsearch_index, name='elasticsearch-index-create'),
    path('monitoring/elasticsearch/indices/<str:index_name>/', views.get_elasticsearch_index, name='elasticsearch-index-detail'),
    path('monitoring/elasticsearch/indices/<str:index_name>/update/', views.update_elasticsearch_index, name='elasticsearch-index-update'),
    path('monitoring/elasticsearch/indices/<str:index_name>/delete/', views.delete_elasticsearch_index, name='elasticsearch-index-delete'),
    
    # Documents Elasticsearch
    path('monitoring/elasticsearch/search/', views.elasticsearch_search, name='elasticsearch-search'),
    path('monitoring/elasticsearch/count/', views.elasticsearch_count, name='elasticsearch-count'),
    path('monitoring/elasticsearch/indices/<str:index_name>/documents/', views.elasticsearch_documents, name='elasticsearch-documents-list'),
    path('monitoring/elasticsearch/indices/<str:index_name>/documents/create/', views.create_elasticsearch_document, name='elasticsearch-document-create'),
    path('monitoring/elasticsearch/indices/<str:index_name>/documents/<str:doc_id>/', views.get_elasticsearch_document, name='elasticsearch-document-detail'),
    path('monitoring/elasticsearch/indices/<str:index_name>/documents/<str:doc_id>/update/', views.update_elasticsearch_document, name='elasticsearch-document-update'),
    path('monitoring/elasticsearch/indices/<str:index_name>/documents/<str:doc_id>/delete/', views.delete_elasticsearch_document, name='elasticsearch-document-delete'),
    
    # Templates Elasticsearch
    path('monitoring/elasticsearch/templates/', views.elasticsearch_templates, name='elasticsearch-templates-list'),
    path('monitoring/elasticsearch/templates/create/', views.create_elasticsearch_template, name='elasticsearch-template-create'),
    path('monitoring/elasticsearch/templates/<str:template_name>/', views.get_elasticsearch_template, name='elasticsearch-template-detail'),
    path('monitoring/elasticsearch/templates/<str:template_name>/update/', views.update_elasticsearch_template, name='elasticsearch-template-update'),
    path('monitoring/elasticsearch/templates/<str:template_name>/delete/', views.delete_elasticsearch_template, name='elasticsearch-template-delete'),
    
    # ==================== CLIENTS MONITORING - NETDATA ====================
    path('monitoring/netdata/metrics/', views.netdata_metrics, name='netdata-metrics'),
    path('monitoring/netdata/charts/', views.netdata_charts, name='netdata-charts'),
    path('monitoring/netdata/alarms/', views.netdata_alarms, name='netdata-alarms'),
    path('monitoring/netdata/info/', views.netdata_info, name='netdata-info'),
    
    # ==================== CLIENTS MONITORING - NTOPNG ====================
    path('monitoring/ntopng/hosts/', views.ntopng_hosts, name='ntopng-hosts'),
    path('monitoring/ntopng/flows/', views.ntopng_flows, name='ntopng-flows'),
    path('monitoring/ntopng/interfaces/', views.ntopng_interfaces, name='ntopng-interfaces'),
    path('monitoring/ntopng/alerts/', views.ntopng_alerts, name='ntopng-alerts'),
    
    # ==================== CLIENTS INFRASTRUCTURE - HAPROXY ====================
    path('infrastructure/haproxy/stats/', views.haproxy_stats, name='haproxy-stats'),
    path('infrastructure/haproxy/info/', views.haproxy_info, name='haproxy-info'),
    path('infrastructure/haproxy/backends/', views.haproxy_backends, name='haproxy-backends'),
    path('infrastructure/haproxy/backends/<str:backend>/servers/', views.haproxy_backend_servers, name='haproxy-backend-servers'),
    path('infrastructure/haproxy/backends/<str:backend>/servers/<str:server>/enable/', views.enable_haproxy_server, name='haproxy-server-enable'),
    path('infrastructure/haproxy/backends/<str:backend>/servers/<str:server>/disable/', views.disable_haproxy_server, name='haproxy-server-disable'),
    path('infrastructure/haproxy/backends/<str:backend>/servers/<str:server>/state/', views.set_haproxy_server_state, name='haproxy-server-state'),
    
    # ==================== CLIENTS INFRASTRUCTURE - TRAFFIC CONTROL ====================
    path('infrastructure/traffic-control/interfaces/', views.traffic_control_interfaces, name='traffic-control-interfaces'),
    path('infrastructure/traffic-control/interfaces/<str:interface>/', views.traffic_control_interface_config, name='traffic-control-interface-config'),
    path('infrastructure/traffic-control/interfaces/<str:interface>/clear/', views.clear_traffic_control_interface, name='traffic-control-interface-clear'),
    path('infrastructure/traffic-control/interfaces/<str:interface>/bandwidth/', views.set_traffic_control_bandwidth, name='traffic-control-set-bandwidth'),
    path('infrastructure/traffic-control/interfaces/<str:interface>/prioritization/', views.set_traffic_control_prioritization, name='traffic-control-set-prioritization'),
    path('infrastructure/traffic-control/interfaces/<str:interface>/filters/', views.traffic_control_filters, name='traffic-control-filters'),
    path('infrastructure/traffic-control/interfaces/<str:interface>/filters/create/', views.add_traffic_control_filter, name='traffic-control-add-filter'),
    
    # ==================== CLIENTS SÉCURITÉ - FAIL2BAN ====================
    path('security/fail2ban/jails/', views.fail2ban_jails, name='fail2ban-jails-list'),
    path('security/fail2ban/jails/create/', views.create_fail2ban_jail, name='fail2ban-jail-create'),
    path('security/fail2ban/jails/<str:jail_name>/', views.get_fail2ban_jail, name='fail2ban-jail-detail'),
    path('security/fail2ban/jails/<str:jail_name>/update/', views.update_fail2ban_jail, name='fail2ban-jail-update'),
    path('security/fail2ban/jails/<str:jail_name>/delete/', views.delete_fail2ban_jail, name='fail2ban-jail-delete'),
    path('security/fail2ban/jails/<str:jail_name>/start/', views.start_fail2ban_jail, name='fail2ban-jail-start'),
    path('security/fail2ban/jails/<str:jail_name>/stop/', views.stop_fail2ban_jail, name='fail2ban-jail-stop'),
    path('security/fail2ban/jails/<str:jail_name>/banned-ips/', views.fail2ban_banned_ips, name='fail2ban-banned-ips'),
    path('security/fail2ban/jails/<str:jail_name>/logs/', views.fail2ban_jail_logs, name='fail2ban-jail-logs'),
    
    # Actions Fail2Ban
    path('security/fail2ban/ban/', views.ban_ip_fail2ban, name='fail2ban-ban-ip'),
    path('security/fail2ban/unban/', views.unban_ip_fail2ban, name='fail2ban-unban-ip'),
    path('security/fail2ban/config/', views.fail2ban_config, name='fail2ban-config'),
    path('security/fail2ban/config/update/', views.update_fail2ban_config, name='fail2ban-config-update'),
    path('security/fail2ban/reload/', views.reload_fail2ban_config, name='fail2ban-reload'),
    path('security/fail2ban/restart/', views.restart_fail2ban_service, name='fail2ban-restart'),
    
    # ==================== CLIENTS SÉCURITÉ - SURICATA ====================
    path('security/suricata/rules/', views.suricata_rules, name='suricata-rules-list'),
    path('security/suricata/rules/create/', views.create_suricata_rule, name='suricata-rule-create'),
    path('security/suricata/rules/<str:rule_id>/', views.get_suricata_rule, name='suricata-rule-detail'),
    path('security/suricata/rules/<str:rule_id>/update/', views.update_suricata_rule, name='suricata-rule-update'),
    path('security/suricata/rules/<str:rule_id>/delete/', views.delete_suricata_rule, name='suricata-rule-delete'),
    path('security/suricata/rules/<str:rule_id>/toggle/', views.toggle_suricata_rule, name='suricata-rule-toggle'),
    
    # Alertes et événements Suricata
    path('security/suricata/alerts/', views.suricata_alerts, name='suricata-alerts-list'),
    path('security/suricata/alerts/<str:alert_id>/', views.get_suricata_alert, name='suricata-alert-detail'),
    path('security/suricata/flows/', views.suricata_flows, name='suricata-flows'),
    path('security/suricata/events/search/', views.search_suricata_events, name='suricata-search-events'),
    
    # Configuration Suricata
    path('security/suricata/rulesets/', views.suricata_rulesets, name='suricata-rulesets'),
    path('security/suricata/rulesets/upload/', views.upload_suricata_ruleset, name='suricata-upload-ruleset'),
    path('security/suricata/config/', views.suricata_config, name='suricata-config'),
    path('security/suricata/config/update/', views.update_suricata_config, name='suricata-config-update'),
    
    # ==================== OPÉRATIONS EN LOT (BULK) ====================
    path('bulk/gns3/', views.bulk_operations_gns3, name='bulk-operations-gns3'),
    path('bulk/elasticsearch/', views.bulk_operations_elasticsearch, name='bulk-operations-elasticsearch'),
    path('bulk/fail2ban/', views.bulk_operations_fail2ban, name='bulk-operations-fail2ban'),
    path('bulk/grafana/', views.bulk_operations_grafana, name='bulk-operations-grafana'),
    
    # ==================== CONFIGURATION CENTRALISÉE ====================
    path('config/clients/', views.list_client_configs, name='client-configs-list'),
    path('config/clients/<str:client_type>/', views.get_client_config, name='client-config-detail'),
    path('config/clients/<str:client_type>/update/', views.update_client_config, name='client-config-update'),
    path('config/clients/<str:client_type>/test/', views.test_client_config, name='client-config-test'),
    path('config/clients/<str:client_type>/reset/', views.reset_client_config, name='client-config-reset'),
    
    # Configuration individuelle des clients (legacy)
    path('config/create/', views.create_client_config, name='client-config-create'),
    path('config/<str:client_name>/', views.update_client_config, name='client-config-update-legacy'),
    path('config/<str:client_name>/delete/', views.delete_client_config, name='client-config-delete'),
    
    # ==================== MÉTRIQUES ET MONITORING ====================
    path('metrics/performance/', views.performance_metrics, name='performance-metrics'),
    path('metrics/circuit-breakers/', views.circuit_breaker_metrics, name='circuit-breaker-metrics'),
    path('metrics/cache/', views.cache_metrics, name='cache-metrics'),
    path('metrics/errors/', views.error_metrics, name='error-metrics'),
    path('metrics/usage/', views.usage_metrics, name='usage-metrics'),
    
    # ==================== UTILITAIRES ET SANTÉ ====================
    path('health/', views.comprehensive_health_check, name='comprehensive-health-check'),
    path('utils/health/', views.comprehensive_health_check, name='global-health-check'),  # Alias pour compatibilité
    path('utils/status/', views.global_status, name='global-status'),
    path('utils/version/', views.api_version, name='api-version'),
    path('utils/capabilities/', views.api_capabilities, name='api-capabilities'),
    path('utils/reset/', views.reset_all_clients, name='reset-all-clients'),
    
    # ==================== DEBUGGING ET DIAGNOSTICS ====================
    path('debug/logs/', views.debug_logs, name='debug-logs'),
    path('debug/connections/', views.debug_connections, name='debug-connections'),
    path('debug/memory/', views.debug_memory_usage, name='debug-memory'),
    path('debug/cache/clear/', views.clear_cache, name='clear-cache'),
    path('debug/config/dump/', views.dump_config, name='dump-config'),
]