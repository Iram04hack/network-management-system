"""
Configuration Swagger avancée avec générateur personnalisé pour unifier les tags et améliorer l'expérience développeur.
"""

from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions

# Configuration Swagger avec description complète - générateur standard pour stabilité
schema_view = get_schema_view(
    openapi.Info(
        title="Network Management System (NMS) API",
        default_version='v1.0',
        description="""
# 🌐 Network Management System - API REST Complète

## 📋 Vue d'ensemble

Cette API REST fournit une interface complète et moderne pour la gestion d'infrastructure réseau d'entreprise, intégrant surveillance, sécurité, reporting, automatisation IA et virtualisation GNS3.

## 🎯 Modules principaux

### 🤖 AI Assistant
- **Chat intelligent** avec analyse contextuelle
- **Automation avancée** des tâches réseau 
- **Analyse prédictive** et recommandations
- **Intégration GNS3** pour topologies automatisées

### 🔌 API Clients
- **Intégration multi-services** : GNS3, SNMP, Netflow, Prometheus, Grafana
- **Clients sécurisés** : Fail2Ban, Suricata, HAProxy
- **Monitoring distribué** : Elasticsearch, Netdata
- **APIs unifiées** avec gestion d'erreurs robuste

### 👁️ API Views  
- **Vues métier sophistiquées** avec logique complexe
- **Recherche globale** multi-types avec filtrage avancé
- **Analytics temps réel** et métriques consolidées
- **Pagination intelligente** et optimisations performances

### 🏗️ Common - Infrastructure
- **Service Central GNS3** avec cache Redis et WebSocket
- **Communication inter-modules** via message bus
- **Hub centralisé** avec workflow engine
- **Auto-découverte** des équipements réseau
- **Monitoring SNMP** avec sessions persistantes

### 📊 Dashboard
- **Tableaux de bord interactifs** avec widgets personnalisables
- **Visualisations temps réel** des métriques système
- **Alertes contextuelles** et notifications intelligentes
- **Préréglages** et personnalisation utilisateur avancée

### 🔗 GNS3 Integration
- **Gestion complète** des serveurs, projets, nœuds et topologies
- **Synchronisation bidirectionnelle** avec serveurs GNS3
- **Automation scripts** et workflows personnalisés
- **Snapshots** et versioning des topologies
- **WebSocket temps réel** pour les événements réseau

### 👀 Monitoring
- **Surveillance multi-niveaux** : système, réseau, applications
- **Métriques avancées** avec agrégation et historisation
- **Alertes intelligentes** avec corrélation d'événements
- **Dashboards spécialisés** par type d'équipement
- **Intégration externe** (Prometheus, Grafana, Elasticsearch)

### 🌐 Network Management  
- **Découverte automatique** de topologies physiques et logiques
- **Gestion SNMP avancée** avec MIBs personnalisées
- **Configuration centralisée** des équipements
- **Monitoring état des liens** et interfaces
- **Cartographie réseau** interactive temps réel

### ⚡ QoS Management
- **Politiques QoS avancées** avec classes de trafic granulaires
- **Monitoring performances** et métriques de qualité
- **Optimisation automatique** basée sur l'analyse du trafic
- **Classification intelligente** des flux réseau
- **Rapports détaillés** sur la qualité de service

### 📈 Reporting
- **Système de rapports avancé** avec planification automatique
- **Visualisations riches** : graphiques, tableaux, cartes
- **Export multi-formats** : PDF, Excel, CSV, JSON
- **Rapports prédéfinis** et personnalisables
- **Analyse tendances** et détection d'anomalies

### 🔐 Security Management
- **Gestion centralisée** des règles de sécurité
- **Corrélation d'événements** multi-sources
- **Détection d'intrusions** avec ML/IA
- **Gestion des vulnérabilités** et patch management
- **Incidents de sécurité** avec workflow de réponse
- **Compliance** et audit automatisés

## 🔐 Authentification & Sécurité

- **Django Authentication** standard avec tokens
- **Permissions granulaires** par module et opération
- **Rate limiting** et protection anti-abus
- **Audit logs** complets des actions utilisateur
- **HTTPS obligatoire** en production

## 🚀 Performance & Scalabilité

- **Cache Redis** pour performances optimales
- **Pagination intelligente** avec curseurs
- **Compression gzip** automatique
- **Circuit breakers** pour résilience
- **Load balancing** ready
- **Monitoring performances** intégré

## 📡 Temps Réel

- **WebSocket** pour événements GNS3 temps réel
- **Server-Sent Events** pour notifications
- **Polling intelligent** avec backoff adaptatif
- **Message bus** pour communication inter-modules

## 🔧 DevOps & Intégration

- **API REST** conforme OpenAPI 3.0
- **Docker containerized** avec orchestration
- **Health checks** automatiques
- **Métriques Prometheus** exposées
- **Logs structurés** JSON
- **Configuration 12-factor**

## 📚 Documentation

- **Swagger UI interactif** avec tests en ligne
- **Exemples pratiques** pour chaque endpoint
- **Codes d'erreur** détaillés avec solutions
- **Guides d'intégration** par cas d'usage
- **SDK clients** disponibles

## 🎨 Expérience Développeur

- **API cohérente** avec conventions REST
- **Réponses standardisées** avec métadonnées
- **Gestion d'erreurs** uniforme et informative
- **Versioning** transparent et rétrocompatible
- **Environnements** de test et développement

---

💡 **Cas d'usage typiques** : Monitoring infrastructure, Automation réseau, Sécurité avancée, Reporting exécutif, Formation GNS3, Troubleshooting intelligent
        """,
        terms_of_service="https://networkmanagement.local/terms/",
        contact=openapi.Contact(
            name="Équipe NMS",
            email="admin@networkmanagement.local",
            url="https://networkmanagement.local/support/"
        ),
        license=openapi.License(
            name="MIT License",
            url="https://opensource.org/licenses/MIT"
        ),
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
)