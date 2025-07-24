"""
Configuration des URLs unifiée pour l'application api_clients.

Ce module définit une API REST complète et unifiée pour tous les clients
avec une documentation Swagger cohérente et des tags "Clients" unifiés.
"""

from django.urls import path, include
from rest_framework import permissions
from rest_framework.routers import DefaultRouter
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from . import views

# Configuration unifiée de Swagger UI avec tag unique "Clients"
schema_view = get_schema_view(
    openapi.Info(
        title="🚀 API Clients - Documentation Unifiée",
        default_version='v2.0',
        description="""
# 🎯 API de Gestion des Clients Réseau - Version Unifiée

Cette API fournit une interface **unifiée** et **complète** pour l'interaction avec tous les clients 
du système de gestion réseau. Tous les endpoints sont organisés sous le tag unique **"Clients"** 
pour une navigation simplifiée.

## 🏗️ Architecture Unifiée

### 📡 **Clients Réseau**
- **GNS3Client** - Gestion complète des topologies et simulations réseau
- **SNMPClient** - Interrogation avancée des équipements réseau
- **NetflowClient** - Analyse sophistiquée des flux de trafic

### 📊 **Clients Monitoring**
- **PrometheusClient** - Collecte de métriques et alertes
- **GrafanaClient** - Tableaux de bord et visualisations
- **ElasticsearchClient** - Indexation et recherche avancée
- **NetdataClient** - Monitoring temps réel des systèmes
- **NtopngClient** - Analyse avancée du trafic réseau

### 🏢 **Clients Infrastructure**
- **HAProxyClient** - Load balancing et proxy avancé
- **TrafficControlClient** - Gestion QoS Linux (tc)

### 🔒 **Clients Sécurité**
- **Fail2BanClient** - Protection contre les intrusions
- **SuricataClient** - Détection d'intrusions IDS/IPS

## 💡 **Avantages de cette API Unifiée**

### 🏷️ **Tag Unique "Clients"**
- ✅ Navigation simplifiée avec un seul tag
- ✅ Structure cohérente sur tous les endpoints
- ✅ Documentation unifiée et facile à parcourir

### 🤖 **Documentation Automatique**
- ✅ Génération automatique par introspection du code
- ✅ Pas d'erreurs manuelles dans les schémas
- ✅ Mise à jour automatique lors des modifications
- ✅ Cohérence garantie entre code et documentation

### 🔒 **Sécurité et Fiabilité**
- ✅ Validation robuste des paramètres d'entrée
- ✅ Gestion d'erreurs détaillée avec codes spécifiques
- ✅ Logs détaillés pour le debugging

## 🚀 **Endpoints Disponibles**

### 🔗 **Endpoints Principaux**
- **GET** `/network/` - Statut des clients réseau
- **GET** `/monitoring/` - Statut des clients monitoring
- **GET** `/infrastructure/` - Statut des clients infrastructure (placeholder)
- **GET** `/security/` - Statut des clients sécurité (placeholder)

### 📊 **GNS3 - Gestion des Projets**
- **GET** `/network/gns3/projects/` - Liste des projets
- **POST** `/network/gns3/projects/create/` - Créer un projet (placeholder)
- **PUT** `/network/gns3/projects/{project_id}/` - Modifier un projet (placeholder)
- **DELETE** `/network/gns3/projects/{project_id}/delete/` - Supprimer un projet (placeholder)

### 🔍 **Elasticsearch - Gestion des Indices**
- **GET** `/monitoring/elasticsearch/indices/` - Liste des indices
- **POST** `/monitoring/elasticsearch/indices/create/` - Créer un indice

### 📈 **Grafana - Gestion des Dashboards**
- **GET** `/monitoring/grafana/dashboards/` - Liste des dashboards

### 🔒 **Fail2Ban - Gestion de la Sécurité**
- **GET** `/security/fail2ban/jails/` - Liste des jails
- **POST** `/security/fail2ban/ban/` - Bannir une IP

### 🏥 **Monitoring et Santé**
- **GET** `/health/` - Vérification complète de santé
- **POST** `/bulk/gns3/` - Opérations en lot sur GNS3

### ⚙️ **Configuration des Clients**
- **POST** `/config/create/` - Configurer un nouveau client (placeholder)
- **PUT** `/config/{client_name}/` - Modifier configuration (placeholder)
- **DELETE** `/config/{client_name}/delete/` - Supprimer configuration (placeholder)

## 🎯 **Guide d'Utilisation**

### Vérifier la santé globale
```bash
curl -X GET "https://localhost:8000/api/clients/health/" \\
     -H "Accept: application/json"
```

### Lister les projets GNS3
```bash
curl -X GET "https://localhost:8000/api/clients/network/gns3/projects/" \\
     -H "Accept: application/json"
```

### Créer un indice Elasticsearch
```bash
curl -X POST "https://localhost:8000/api/clients/monitoring/elasticsearch/indices/create/" \\
     -H "Content-Type: application/json" \\
     -d '{"index_name": "logs-app", "settings": {"number_of_shards": 1}}'
```

### Bannir une IP avec Fail2Ban
```bash
curl -X POST "https://localhost:8000/api/clients/security/fail2ban/ban/" \\
     -H "Content-Type: application/json" \\
     -d '{"ip_address": "192.168.1.100", "jail_name": "sshd"}'
```

---

🎉 **Documentation générée automatiquement et toujours à jour !** 
Tous les endpoints utilisent le tag unifié **"Clients"** pour une expérience simplifiée.
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
    # ==================== DOCUMENTATION SWAGGER UNIFIÉE ====================
    path('', schema_view.with_ui('swagger', cache_timeout=0), name='api-clients-home'),
    path('docs/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    path('swagger.json', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('openapi.yaml', schema_view.without_ui(cache_timeout=0), name='schema-yaml'),
    
    # ==================== STATUT DES CLIENTS (Fonctionnels) ====================
    path('network/', views.network_clients, name='network-clients-status'),
    path('monitoring/', views.monitoring_clients, name='monitoring-clients-status'),
    path('infrastructure/', views.infrastructure_clients, name='infrastructure-clients-status'),
    path('security/', views.security_clients, name='security-clients-status'),
    
    # ==================== GNS3 - GESTION DES PROJETS (Fonctionnels) ====================
    path('network/gns3/projects/', views.gns3_projects, name='gns3-projects-list'),
    path('network/gns3/projects/create/', views.create_gns3_project, name='gns3-projects-create'),
    path('network/gns3/projects/<str:project_id>/', views.update_gns3_project, name='gns3-projects-update'),
    path('network/gns3/projects/<str:project_id>/delete/', views.delete_gns3_project, name='gns3-projects-delete'),
    
    # ==================== SNMP - REQUÊTES RÉSEAU (Placeholder) ====================
    path('network/snmp/query/', views.snmp_query, name='snmp-query'),
    
    # ==================== PROMETHEUS - MÉTRIQUES (Placeholder) ====================
    path('monitoring/prometheus/query/', views.prometheus_query, name='prometheus-query'),
    
    # ==================== GRAFANA - DASHBOARDS (Fonctionnel) ====================
    path('monitoring/grafana/dashboards/', views.grafana_dashboards, name='grafana-dashboards-list'),
    
    # ==================== ELASTICSEARCH - INDICES (Fonctionnels) ====================
    path('monitoring/elasticsearch/indices/', views.elasticsearch_indices, name='elasticsearch-indices-list'),
    path('monitoring/elasticsearch/indices/create/', views.create_elasticsearch_index, name='elasticsearch-index-create'),
    
    # ==================== FAIL2BAN - SÉCURITÉ (Fonctionnels) ====================
    path('security/fail2ban/jails/', views.fail2ban_jails, name='fail2ban-jails-list'),
    path('security/fail2ban/ban/', views.ban_ip_fail2ban, name='fail2ban-ban-ip'),
    
    # ==================== OPÉRATIONS EN LOT (Fonctionnel) ====================
    path('bulk/gns3/', views.bulk_operations_gns3, name='bulk-operations-gns3'),
    
    # ==================== CONFIGURATION DES CLIENTS (Placeholders) ====================
    path('config/create/', views.create_client_config, name='client-config-create'),
    path('config/<str:client_name>/', views.update_client_config, name='client-config-update'),
    path('config/<str:client_name>/delete/', views.delete_client_config, name='client-config-delete'),
    
    # ==================== SANTÉ ET MONITORING (Fonctionnel) ====================
    path('health/', views.comprehensive_health_check, name='comprehensive-health-check'),
]