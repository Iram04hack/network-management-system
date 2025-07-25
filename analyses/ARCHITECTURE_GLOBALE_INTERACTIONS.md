# ANALYSE COMPLÈTE DE L'ARCHITECTURE GLOBALE - SYSTÈME NMS DJANGO

**Version:** 2.1.0  
**Date:** 25 juillet 2025  
**Type:** Architecture Distribuée - Event-Driven - Microservices Hybrides  

---

## 🏗️ 1. ARCHITECTURE SYSTÈME GLOBALE

### 1.1 Vue d'Ensemble Architecturale

Le système NMS Django implémente une **architecture distribuée hybride** combinant plusieurs patterns architecturaux avancés :

```ascii
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           NMS ARCHITECTURE GLOBALE                              │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐         │
│  │   PRESENTATION   │    │    APPLICATION    │    │  INFRASTRUCTURE  │         │
│  │      LAYER       │    │      LAYER        │    │      LAYER       │         │
│  │                  │    │                   │    │                  │         │
│  │ • React Frontend │◄──►│ • Django Backend  │◄──►│ • Docker Stack   │         │
│  │ • API Gateway    │    │ • WebSocket Layer │    │ • Redis/PostgreSQL│         │
│  │ • Swagger UI     │    │ • Event Bus       │    │ • Message Queues │         │
│  └──────────────────┘    └──────────────────┘    └──────────────────┘         │
│           │                        │                        │                   │
│           └────────────────────────┼────────────────────────┘                   │
│                                    │                                            │
│  ┌─────────────────────────────────┼─────────────────────────────────────────┐  │
│  │                    BUSINESS DOMAIN MODULES                               │  │
│  │                                 │                                         │  │
│  │  ┌─────────────┐  ┌─────────────┼─────────────┐  ┌─────────────────────┐  │  │
│  │  │   COMMON    │◄─┤             │             ├─►│     MONITORING      │  │  │
│  │  │  (HUB CORE) │  │             │             │  │   (OBSERVABILITY)   │  │  │
│  │  └─────────────┘  │    ┌────────▼────────┐    │  └─────────────────────┘  │  │
│  │                   │    │   AI_ASSISTANT   │    │                           │  │
│  │  ┌─────────────┐  │    │   (COGNITIVE)    │    │  ┌─────────────────────┐  │  │
│  │  │ GNS3_INTEG  │◄─┤    └─────────────────┘    ├─►│   SECURITY_MGMT     │  │  │
│  │  │(SIMULATION) │  │                           │  │  (CYBER DEFENSE)    │  │  │
│  │  └─────────────┘  │                           │  └─────────────────────┘  │  │
│  │                   │                           │                           │  │
│  │  ┌─────────────┐  │                           │  ┌─────────────────────┐  │  │
│  │  │NETWORK_MGMT │◄─┤                           ├─►│    QOS_MGMT         │  │  │
│  │  │(TOPOLOGY)   │  │                           │  │  (TRAFFIC CONTROL)  │  │  │
│  │  └─────────────┘  │                           │  └─────────────────────┘  │  │
│  │                   │                           │                           │  │
│  │  ┌─────────────┐  │                           │  ┌─────────────────────┐  │  │
│  │  │ API_CLIENTS │◄─┤                           ├─►│    REPORTING        │  │  │
│  │  │(EXTERNAL)   │  │                           │  │   (ANALYTICS)       │  │  │
│  │  └─────────────┘  │                           │  └─────────────────────┘  │  │
│  │                   │                           │                           │  │
│  │  ┌─────────────┐  │                           │  ┌─────────────────────┐  │  │
│  │  │ API_VIEWS   │◄─┤                           ├─►│    DASHBOARD        │  │  │
│  │  │(ENDPOINTS)  │  │                           │  │  (VISUALIZATION)    │  │  │
│  │  └─────────────┘  │                           │  └─────────────────────┘  │  │
│  │                   │                           │                           │  │
│  │  ┌─────────────┐  │                           │  ┌─────────────────────┐  │  │
│  │  │   PLUGINS   │◄─┤                           ├─►│      PLUGINS        │  │  │
│  │  │(EXTENSIBLE) │  │                           │  │   (MODULARITY)      │  │  │
│  │  └─────────────┘  └───────────────────────────┘  └─────────────────────┘  │  │
│  └─────────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 1.2 Patterns Architecturaux Dominants

#### **1.2.1 Architecture Hexagonale (Ports & Adapters)**
- **Cœur métier isolé :** Chaque module encapsule sa logique métier
- **Ports :** Interfaces définies dans `domain/interfaces.py`
- **Adapters :** Implémentations dans `infrastructure/`

#### **1.2.2 Domain-Driven Design (DDD)**
- **Bounded Contexts :** Chaque module = contexte métier distinct
- **Entities & Value Objects :** Modélisation dans `domain/entities.py`
- **Aggregates :** Racines d'agrégation cohérentes

#### **1.2.3 Event-Driven Architecture**
- **Event Bus Central :** Hub de communication centralisé
- **Event Sourcing :** Traçabilité des changements d'état
- **CQRS :** Séparation lecture/écriture pour performance

#### **1.2.4 Microservices Hybrides**
- **Services Docker :** 15+ services orchestrés
- **Inter-Module Communication :** Patterns synchrones/asynchrones
- **Service Discovery :** Auto-détection des services

### 1.3 Couches Système et Responsabilités

```ascii
┌─────────────────────────────────────────────────────────────────────────────────┐
│                            LAYERS ARCHITECTURE                                  │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│ 🌐 PRESENTATION LAYER                                                          │
│ ├─ React Frontend (Port 5173)                                                  │
│ ├─ Django REST API (Port 8000)                                                 │
│ ├─ WebSocket Gateway (ws://localhost:8000/ws/)                                 │
│ └─ Swagger Documentation (http://localhost:8000/swagger/)                      │
│                                                                                 │
│ ⚡ EVENT & MESSAGING LAYER                                                     │
│ ├─ Redis Pub/Sub (Real-time events)                                           │
│ ├─ Celery Task Queue (Asynchronous processing)                                │
│ ├─ Django Channels (WebSocket management)                                     │
│ └─ Inter-Module Communication Hub                                             │
│                                                                                 │
│ 🧠 APPLICATION SERVICES LAYER                                                 │
│ ├─ Use Cases (application/use_cases.py)                                       │
│ ├─ Application Services (application/services/)                               │
│ ├─ Workflow Orchestration                                                     │
│ └─ Business Logic Coordination                                                │
│                                                                                 │
│ 🏢 DOMAIN LAYER                                                               │
│ ├─ Domain Entities (domain/entities.py)                                       │
│ ├─ Domain Services (domain/services/)                                         │
│ ├─ Value Objects (domain/value_objects.py)                                    │
│ └─ Domain Events                                                              │
│                                                                                 │
│ 🔧 INFRASTRUCTURE LAYER                                                       │
│ ├─ Repository Implementations (infrastructure/repositories/)                   │
│ ├─ External Service Adapters (infrastructure/adapters/)                       │
│ ├─ Database Persistence (PostgreSQL/SQLite)                                   │
│ └─ External APIs Integration                                                  │
│                                                                                 │
│ 🐳 CONTAINER ORCHESTRATION LAYER                                              │
│ ├─ Docker Services (15+ containers)                                           │
│ ├─ Network Topology (3 networks Docker)                                       │
│ ├─ Volume Management (data persistence)                                       │
│ └─ Service Health Monitoring                                                  │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 📊 2. MATRICE D'INTERACTIONS INTER-MODULES

### 2.1 Matrice de Dépendances Complète

```ascii
┌──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                                    MATRICE D'INTERACTIONS INTER-MODULES                                                                 │
├─────────────┬────────────┬────────────┬────────────┬────────────┬────────────┬────────────┬────────────┬────────────┬────────────┬────────────┬────────────┤
│   MODULE    │   COMMON   │AI_ASSISTANT│API_CLIENTS │ DASHBOARD  │GNS3_INTEG  │MONITORING  │NETWORK_MGT │QOS_MGMT    │SECURITY_MGT│ REPORTING  │  PLUGINS   │
├─────────────┼────────────┼────────────┼────────────┼────────────┼────────────┼────────────┼────────────┼────────────┼────────────┼────────────┼────────────┤
│   COMMON    │     ■      │    ◄──►    │    ◄──►    │    ◄──►    │    ◄──►    │    ◄──►    │    ◄──►    │    ◄──►    │    ◄──►    │    ◄──►    │    ◄──►    │
│             │   (HUB)    │ EventBus   │ Discovery  │ Metrics    │ Topology   │ Alerts     │ Discovery  │ Policies   │ Incidents  │ Data Agg   │ Registry   │
├─────────────┼────────────┼────────────┼────────────┼────────────┼────────────┼────────────┼────────────┼────────────┼────────────┼────────────┼────────────┤
│AI_ASSISTANT │    ◄──►    │     ■      │    ◄──►    │    ──►     │    ◄──►    │    ◄──►    │    ◄──►    │    ──►     │    ◄──►    │    ◄──     │    ◄──     │
│             │ Context    │  (CORE)    │ API Data   │ Insights   │ Analysis   │ Anomalies  │ Topology   │ Recommend  │ Correlation│ Reports    │ AI Plugins │
├─────────────┼────────────┼────────────┼────────────┼────────────┼────────────┼────────────┼────────────┼────────────┼────────────┼────────────┼────────────┤
│API_CLIENTS  │    ◄──►    │    ◄──     │     ■      │    ──►     │    ◄──►    │    ◄──►    │    ◄──►    │    ◄──►    │    ◄──►    │    ◄──     │    ──►     │
│             │ Service    │ Responses  │  (GATEWAY) │ Widget Data│ GNS3 API   │ External   │ SNMP/API   │ Traffic    │ External   │ Data       │ Clients    │
├─────────────┼────────────┼────────────┼────────────┼────────────┼────────────┼────────────┼────────────────────────┼────────────┼────────────┼────────────┤
│  DASHBOARD  │    ◄──►    │    ◄──     │    ◄──     │     ■      │    ◄──►    │    ◄──►    │    ◄──►    │    ◄──►    │    ◄──►    │    ◄──►    │    ◄──     │
│             │ Widgets    │ Insights   │ Metrics    │ (CENTRAL)  │ Topology   │ Real-time  │ Network    │ QoS Views  │ Security   │ Charts     │ Dashboard  │
├─────────────┼────────────┼────────────┼────────────┼────────────┼────────────┼────────────┼────────────┼────────────┼────────────┼────────────┼────────────┤
│GNS3_INTEG   │    ◄──►    │    ◄──►    │    ◄──►    │    ──►     │     ■      │    ──►     │    ◄──►    │    ◄──►    │    ──►     │    ──►     │    ──►     │
│             │ Events     │ Simulation │ GNS3 API   │ Topology   │  (SOURCE)  │ Events     │ Sync       │ Traffic    │ Test Env   │ Lab Data   │ Lab Ext    │
├─────────────┼────────────┼────────────┼────────────┼────────────┼────────────┼────────────┼────────────┼────────────┼────────────┼────────────┼────────────┤
│ MONITORING  │    ◄──►    │    ◄──►    │    ◄──►    │    ──►     │    ◄──     │     ■      │    ◄──►    │    ◄──►    │    ◄──►    │    ──►     │    ◄──     │
│             │ Metrics    │ Anomalies  │ External   │ Real-time  │ Lab Events │ (OBSERVER) │ Device Mon │ QoS Metrics│ Sec Events │ Perf Data  │ Mon Ext    │
├─────────────┼────────────┼────────────┼────────────┼────────────┼────────────┼────────────┼────────────┼────────────┼────────────┼────────────┼────────────┤
│NETWORK_MGT  │    ◄──►    │    ◄──►    │    ◄──►    │    ──►     │    ◄──►    │    ──►     │     ■      │    ◄──►    │    ◄──►    │    ──►     │    ──►     │
│             │ Topology   │ Analysis   │ SNMP Data  │ Network    │ Sync       │ Status     │ (TOPOLOGY) │ Bandwidth  │ Network    │ Network    │ Net Ext    │
├─────────────┼────────────┼────────────┼────────────┼────────────┼────────────┼────────────┼────────────┼────────────┼────────────┼────────────┼────────────┤
│  QOS_MGMT   │    ◄──►    │    ◄──     │    ◄──►    │    ──►     │    ◄──►    │    ──►     │    ◄──►    │     ■      │    ◄──►    │    ──►     │    ──►     │
│             │ Policies   │ Recommend  │ Traffic    │ QoS Views  │ Lab Test   │ Metrics    │ Bandwidth  │ (CONTROL)  │ Security   │ QoS Data   │ QoS Ext    │
├─────────────┼────────────┼────────────┼────────────┼────────────┼────────────┼────────────┼────────────┼────────────┼────────────┼────────────┼────────────┤
│SECURITY_MGT │    ◄──►    │    ◄──►    │    ◄──►    │    ──►     │    ◄──     │    ──►     │    ◄──►    │    ◄──►    │     ■      │    ──►     │    ◄──     │
│             │ Incidents  │ Correlation│ External   │ Alerts     │ Test Sec   │ Events     │ Vulnerab   │ Sec Policies│ (DEFENSE)  │ Sec Reports│ Sec Ext    │
├─────────────┼────────────┼────────────┼────────────┼────────────┼────────────┼────────────┼────────────┼────────────┼────────────┼────────────┼────────────┤
│ REPORTING   │    ◄──►    │    ──►     │    ──►     │    ◄──►    │    ◄──     │    ◄──     │    ◄──     │    ◄──     │    ◄──     │     ■      │    ◄──     │
│             │ Data Agg   │ Insights   │ External   │ Dashboards │ Lab Data   │ Perf Data  │ Network    │ QoS Data   │ Sec Reports│ (ANALYTICS)│ Report Ext │
├─────────────┼────────────┼────────────┼────────────┼────────────┼────────────┼────────────┼────────────┼────────────┼────────────┼────────────┼────────────┤
│  PLUGINS    │    ◄──►    │    ──►     │    ◄──     │    ──►     │    ◄──     │    ──►     │    ◄──     │    ◄──     │    ──►     │    ──►     │     ■      │
│             │ Registry   │ AI Plugins │ Clients    │ Dashboard  │ Lab Ext    │ Mon Ext    │ Net Ext    │ QoS Ext    │ Sec Ext    │ Report Ext │ (EXTEND)   │
└─────────────┴────────────┴────────────┴────────────┴────────────┴────────────┴────────────┴────────────┴────────────┴────────────┴────────────┴────────────┘

LÉGENDE:
■ = Module principal        ◄──► = Communication bidirectionnelle
──► = Communication unidirectionnelle (sortie)   ◄── = Communication unidirectionnelle (entrée)
```

### 2.2 Flux de Données Critiques

#### **2.2.1 Flux d'Événements GNS3**
```
GNS3_INTEGRATION → COMMON (Event Hub) → [MONITORING, AI_ASSISTANT, DASHBOARD, NETWORK_MGT]
```

#### **2.2.2 Flux de Métriques de Performance**
```
MONITORING → COMMON → [DASHBOARD, REPORTING, AI_ASSISTANT] → NOTIFICATIONS
```

#### **2.2.3 Flux de Sécurité**
```
SECURITY_MGMT → COMMON → [AI_ASSISTANT, MONITORING, REPORTING] → INCIDENT_RESPONSE
```

---

## 🔄 3. FLUX DE DONNÉES GLOBAUX

### 3.1 Event Bus Central et Message Routing

```ascii
┌─────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                    EVENT BUS ARCHITECTURE                                                          │
├─────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                                                     │
│                                   ┌─────────────────────────┐                                                     │
│                                   │   CENTRALIZED EVENT     │                                                     │
│                                   │   COMMUNICATION HUB     │                                                     │
│                                   │                         │                                                     │
│  ┌─────────────────┐             │  ┌─────────────────────┐ │             ┌─────────────────┐                    │
│  │  GNS3_INTEG     │────EVENT────│  │   MESSAGE ROUTER    │ │────EVENT────│  MONITORING     │                    │
│  │                 │   PUBLISH   │  │                     │ │  DISTRIBUTE │                 │                    │
│  └─────────────────┘             │  │ • Priority Queue    │ │             └─────────────────┘                    │
│                                   │  │ • Event Filtering   │ │                                                     │
│  ┌─────────────────┐             │  │ • Retry Logic       │ │             ┌─────────────────┐                    │
│  │  SECURITY_MGMT  │────EVENT────│  │ • Circuit Breaker   │ │────EVENT────│  AI_ASSISTANT   │                    │
│  │                 │   PUBLISH   │  │ • Load Balancing    │ │  DISTRIBUTE │                 │                    │
│  └─────────────────┘             │  └─────────────────────┘ │             └─────────────────┘                    │
│                                   │                         │                                                     │
│  ┌─────────────────┐             │  ┌─────────────────────┐ │             ┌─────────────────┐                    │
│  │  NETWORK_MGT    │────EVENT────│  │   EVENT STORAGE     │ │────EVENT────│  DASHBOARD      │                    │
│  │                 │   PUBLISH   │  │                     │ │  DISTRIBUTE │                 │                    │
│  └─────────────────┘             │  │ • Event Sourcing    │ │             └─────────────────┘                    │
│                                   │  │ • Event History     │ │                                                     │
│  ┌─────────────────┐             │  │ • Replay Capability │ │             ┌─────────────────────────────────────┐ │
│  │   QOS_MGMT      │────EVENT────│  │ • Audit Trail       │ │────EVENT────│      NOTIFICATION SYSTEM        │ │
│  │                 │   PUBLISH   │  └─────────────────────┘ │  DISTRIBUTE │                                 │ │
│  └─────────────────┘             │                         │             │ • Email Notifications           │ │
│                                   └─────────────────────────┘             │ • Slack Webhooks               │ │
│                                                                           │ • Telegram Bot                 │ │
│                                            │                              │ • Ubuntu Desktop Notifications │ │
│                                            │                              └─────────────────────────────────────┘ │
│                                   ┌────────▼────────┐                                                             │
│                                   │  WEBSOCKET      │                                                             │
│                                   │  REAL-TIME      │                                                             │
│                                   │  DISTRIBUTION   │                                                             │
│                                   │                 │                                                             │
│                                   │ • Client Sub.   │                                                             │
│                                   │ • Event Filter  │                                                             │
│                                   │ • Connection    │                                                             │
│                                   │   Management    │                                                             │
│                                   └─────────────────┘                                                             │
│                                                                                                                     │
└─────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

### 3.2 Data Pipelines Inter-Modules

#### **3.2.1 Pipeline de Monitoring en Temps Réel**
```
SNMP/API Data → API_CLIENTS → MONITORING → Event Processing → DASHBOARD/AI_ASSISTANT
     ↓
  REDIS Cache ← Performance Metrics ← Statistical Analysis ← Historical Data Store
     ↓
WebSocket Push → Real-time UI Updates → User Notifications
```

#### **3.2.2 Pipeline de Détection de Sécurité**
```
Network Traffic → SECURITY_MGMT → Threat Analysis → AI_ASSISTANT (ML) → Risk Assessment
     ↓
  Alert Generation → Event Hub → MONITORING → Dashboard Alerts → Incident Response
     ↓
 REPORTING → Security Reports → Email/Slack Notifications → Management Dashboard
```

### 3.3 Synchronisation et Consistency Patterns

#### **3.3.1 Saga Pattern pour Workflows Complexes**
```python
# Exemple de workflow orchestré par le Communication Hub
security_testing_workflow = [
    'gns3_startup',           # Démarrage environnement
    'system_orchestration',   # Coordination globale
    'monitoring_activation',  # Activation surveillance
    'security_scanning',      # Tests de sécurité
    'ai_analysis',           # Analyse IA
    'report_generation'      # Génération rapport
]
```

#### **3.3.2 Event Sourcing pour Traçabilité**
- **Event Store :** Redis + PostgreSQL
- **Event Replay :** Capacité de rejeu pour debug
- **Audit Trail :** Traçabilité complète des actions

---

## 🐳 4. INTÉGRATION SERVICES DOCKER

### 4.1 Orchestration des 15 Services Docker

```ascii
┌─────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                     DOCKER SERVICES ARCHITECTURE                                                   │
├─────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                                                     │
│  ┌─────────────────────────────────────────────────────────────────────────────────────────────────────────────┐ │
│  │                                    CORE SERVICES                                                             │ │
│  │                                                                                                               │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                      │ │
│  │  │ PostgreSQL  │  │    Redis    │  │   Django    │  │   Celery    │  │ Celery-Beat │                      │ │
│  │  │   :5432     │  │   :6379     │  │   :8000     │  │   Worker    │  │  Scheduler  │                      │ │
│  │  │             │  │             │  │             │  │             │  │             │                      │ │
│  │  │ • Database  │  │ • Cache     │  │ • REST API  │  │ • Async     │  │ • Periodic  │                      │ │
│  │  │ • Persist   │  │ • Pub/Sub   │  │ • WebSocket │  │   Tasks     │  │   Tasks     │                      │ │
│  │  │ • ACID      │  │ • Sessions  │  │ • Admin     │  │ • Queue     │  │ • Cron Jobs │                      │ │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘                      │ │
│  └─────────────────────────────────────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                                                     │
│  ┌─────────────────────────────────────────────────────────────────────────────────────────────────────────────┐ │
│  │                                 MONITORING SERVICES                                                          │ │
│  │                                                                                                               │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                                        │ │
│  │  │Elasticsearch│  │   Netdata   │  │   ntopng    │  │   HAProxy   │                                        │ │
│  │  │   :9200     │  │   :19999    │  │   :3000     │  │   :80       │                                        │ │
│  │  │             │  │             │  │             │  │             │                                        │ │
│  │  │ • Search    │  │ • System    │  │ • Traffic   │  │ • Load      │                                        │ │
│  │  │ • Logs      │  │   Metrics   │  │   Analysis  │  │   Balancer  │                                        │ │
│  │  │ • AI Data   │  │ • Real-time │  │ • Flow Mon  │  │ • Health    │                                        │ │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘                                        │ │
│  └─────────────────────────────────────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                                                     │
│  ┌─────────────────────────────────────────────────────────────────────────────────────────────────────────────┐ │
│  │                                  SECURITY SERVICES                                                           │ │
│  │                                                                                                               │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                                                          │ │
│  │  │  Suricata   │  │   Fail2ban  │  │   Kibana    │                                                          │ │
│  │  │   :3000     │  │   daemon    │  │   :5601     │                                                          │ │
│  │  │             │  │             │  │             │                                                          │ │
│  │  │ • IDS/IPS   │  │ • Ban Mgmt  │  │ • Log Viz   │                                                          │ │
│  │  │ • Rules     │  │ • IP Filter │  │ • Dashboard │                                                          │ │
│  │  │ • Alerts    │  │ • Real-time │  │ • Analysis  │                                                          │ │
│  │  └─────────────┘  └─────────────┘  └─────────────┘                                                          │ │
│  └─────────────────────────────────────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                                                     │
│  ┌─────────────────────────────────────────────────────────────────────────────────────────────────────────────┐ │
│  │                                 NETWORK SERVICES                                                             │ │
│  │                                                                                                               │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                                                          │ │
│  │  │ SNMP Agent  │  │  Netflow    │  │ Traffic-    │                                                          │ │
│  │  │   :161      │  │ Collector   │  │ Control     │                                                          │ │
│  │  │             │  │   :9995     │  │   :8080     │                                                          │ │
│  │  │ • SNMP v2c  │  │ • Flow Data │  │ • QoS       │                                                          │ │
│  │  │ • MIB Walk  │  │ • Analysis  │  │ • Shaping   │                                                          │ │
│  │  │ • Traps     │  │ • Storage   │  │ • Policy    │                                                          │ │
│  │  └─────────────┘  └─────────────┘  └─────────────┘                                                          │ │
│  └─────────────────────────────────────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                                                     │
└─────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

### 4.2 Service Discovery et Health Checks

#### **4.2.1 Mécanisme de Découverte Automatique**
```python
# common/infrastructure/inter_module_service.py
docker_services = {
    'postgresql': {'host': 'nms-postgres', 'port': '5432', 'type': 'database'},
    'redis': {'host': 'nms-redis', 'port': '6379', 'type': 'cache'},
    'elasticsearch': {'host': 'nms-elasticsearch', 'port': '9200', 'type': 'search'},
    'suricata': {'host': 'nms-suricata', 'port': '3000', 'type': 'security'},
    # ... autres services
}
```

#### **4.2.2 Health Check Matrix**
```ascii
┌────────────────┬────────────┬─────────────────┬────────────────┬─────────────────┐
│    SERVICE     │    PORT    │  HEALTH CHECK   │   INTERVAL     │   RETRY LOGIC   │
├────────────────┼────────────┼─────────────────┼────────────────┼─────────────────┤
│ PostgreSQL     │    5432    │ pg_isready      │     30s        │      3x         │
│ Redis          │    6379    │ PING command    │     20s        │      3x         │
│ Elasticsearch  │    9200    │ /_cluster/health│     30s        │      5x         │
│ Django         │    8000    │ /admin/         │     15s        │      3x         │
│ Suricata       │    3000    │ Rule reload     │     60s        │      2x         │
│ Netdata        │   19999    │ /api/v1/info    │     30s        │      3x         │
│ HAProxy        │     80     │ /stats          │     20s        │      3x         │
└────────────────┴────────────┴─────────────────┴────────────────┴─────────────────┘
```

### 4.3 Network Topology Entre Conteneurs

```ascii
┌─────────────────────────────────────────────────────────────────────────────────┐
│                            DOCKER NETWORKS TOPOLOGY                             │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                          nms-backend                                    │   │
│  │                       (172.18.0.0/16)                                  │   │
│  │                                                                         │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐   │   │
│  │  │ PostgreSQL  │  │    Redis    │  │   Django    │  │   Celery    │   │   │
│  │  │ 172.18.0.10 │  │ 172.18.0.11 │  │ 172.18.0.12 │  │ 172.18.0.13 │   │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘   │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                                        │                                        │
│                                        │                                        │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                        nms-monitoring                                   │   │
│  │                       (172.19.0.0/16)                                  │   │
│  │                                                                         │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐   │   │
│  │  │Elasticsearch│  │   Netdata   │  │   ntopng    │  │   HAProxy   │   │   │
│  │  │ 172.19.0.10 │  │ 172.19.0.11 │  │ 172.19.0.12 │  │ 172.19.0.13 │   │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘   │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                                        │                                        │
│                                        │                                        │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                         nms-network                                     │   │
│  │                       (172.20.0.0/16)                                  │   │
│  │                                                                         │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐   │   │
│  │  │ SNMP Agent  │  │  Suricata   │  │  Fail2ban   │  │Traffic-Ctrl │   │   │
│  │  │ 172.20.0.10 │  │ 172.20.0.11 │  │ 172.20.0.12 │  │ 172.20.0.13 │   │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘   │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 🔧 5. PATTERNS D'INTÉGRATION

### 5.1 API Gateway Patterns

#### **5.1.1 Unified API Gateway**
```python
# nms_backend/urls.py - Point d'entrée unique
urlpatterns = [
    path('api/', api_root, name='api-root'),
    path('api/clients/', include('api_clients.urls')),
    path('api/monitoring/', include('monitoring.urls')),
    path('api/gns3/', include('gns3_integration.urls')),
    path('api/network/', include('network_management.api.urls')),
    path('api/ai/', include('ai_assistant.api.urls')),
    path('api/security/', include('security_management.api.urls')),
    path('api/qos/', include('qos_management.urls')),
    path('api/common/', include('common.urls')),
    path('swagger/', schema_view.with_ui('swagger')),
]
```

#### **5.1.2 Request/Response Pipeline**
```ascii
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   CLIENT    │───►│    NGINX    │───►│   DJANGO    │───►│   MODULE    │
│  Request    │    │ Load Balancer │    │ API Gateway │    │  Business   │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
       ▲                   │                   │                   │
       │                   ▼                   ▼                   ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  Response   │◄───│    Cache    │◄───│    Auth     │◄───│ Validation  │
│   Client    │    │   Layer     │    │ Middleware  │    │  & Logic    │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
```

### 5.2 Event-Driven Architecture Patterns

#### **5.2.1 Publish-Subscribe avec Event Hub**
```python
# Exemple d'utilisation du Communication Hub
from common.infrastructure.centralized_communication_hub import communication_hub

# Publication d'événement
event = RealtimeEvent(
    event_type='topology_changed',
    source='gns3_integration',
    data={'project_id': 'xxx', 'nodes': [...]}
)
await communication_hub.publish_event(event)

# Abonnement à des événements
communication_hub.register_module(
    module_name='monitoring',
    capabilities=['metric_collection', 'alerting'],
    health_check_callback=health_check_callback
)
```

#### **5.2.2 CQRS (Command Query Responsibility Segregation)**
```ascii
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              CQRS ARCHITECTURE                                  │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  WRITE SIDE (Commands)                    READ SIDE (Queries)                  │
│  ┌─────────────────────┐                 ┌─────────────────────┐              │
│  │                     │                 │                     │              │
│  │  ┌───────────────┐  │    Events       │  ┌───────────────┐  │              │
│  │  │   Commands    │  │ ─────────────► │  │   Read Models │  │              │
│  │  │               │  │                 │  │               │  │              │
│  │  │ • Create Node │  │                 │  │ • Dashboard   │  │              │
│  │  │ • Update Conf │  │                 │  │ • Reports     │  │              │
│  │  │ • Delete Rule │  │                 │  │ • Metrics     │  │              │
│  │  └───────────────┘  │                 │  └───────────────┘  │              │
│  │          │          │                 │          ▲          │              │
│  │          ▼          │                 │          │          │              │
│  │  ┌───────────────┐  │                 │  ┌───────────────┐  │              │
│  │  │  Domain Model │  │                 │  │  Query Models │  │              │
│  │  │               │  │                 │  │               │  │              │
│  │  │ • Aggregates  │  │                 │  │ • Views       │  │              │
│  │  │ • Entities    │  │                 │  │ • Projections │  │              │
│  │  │ • Validation  │  │                 │  │ • Cache       │  │              │
│  │  └───────────────┘  │                 │  └───────────────┘  │              │
│  │          │          │                 │                     │              │
│  │          ▼          │                 │                     │              │
│  │  ┌───────────────┐  │                 │                     │              │
│  │  │  Event Store  │  │                 │                     │              │
│  │  │               │  │                 │                     │              │
│  │  │ • PostgreSQL  │  │                 │                     │              │
│  │  │ • Redis       │  │                 │                     │              │
│  │  │ • Audit Trail │  │                 │                     │              │
│  │  └───────────────┘  │                 │                     │              │
│  └─────────────────────┘                 └─────────────────────┘              │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 5.3 Circuit Breakers et Resilience

#### **5.3.1 Circuit Breaker Implementation**
```python
# api_clients/infrastructure/circuit_breaker.py
class CircuitBreaker:
    def __init__(self, failure_threshold=5, recovery_timeout=60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = 'CLOSED'  # CLOSED, OPEN, HALF_OPEN

    async def call(self, func, *args, **kwargs):
        if self.state == 'OPEN':
            if self._should_attempt_reset():
                self.state = 'HALF_OPEN'
            else:
                raise CircuitOpenException()
                
        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise
```

#### **5.3.2 Service Mesh Considerations**
- **Load Balancing :** HAProxy pour distribution de charge
- **Service Discovery :** Enregistrement automatique des services
- **Health Checks :** Surveillance continue des services
- **Failover :** Basculement automatique en cas de panne

---

## 🌐 6. COMMUNICATION PROTOCOLS

### 6.1 REST APIs Entre Modules

#### **6.1.1 API Standards et Conventions**
```
GET    /api/{module}/          - Liste des ressources
GET    /api/{module}/{id}/     - Détail d'une ressource
POST   /api/{module}/          - Création d'une ressource
PUT    /api/{module}/{id}/     - Mise à jour complète
PATCH  /api/{module}/{id}/     - Mise à jour partielle
DELETE /api/{module}/{id}/     - Suppression
```

#### **6.1.2 API Response Standards**
```json
{
  "status": "success|error",
  "data": { /* payload */ },
  "message": "Human readable message",
  "timestamp": "2025-07-25T10:00:00Z",
  "request_id": "uuid-v4",
  "pagination": {
    "page": 1,
    "per_page": 10,
    "total": 100,
    "total_pages": 10
  }
}
```

### 6.2 WebSocket Temps Réel

#### **6.2.1 WebSocket Routing Structure**
```python
# nms_backend/routing.py
websocket_urlpatterns = [
    # Monitoring temps réel
    re_path(r'ws/monitoring/$', MonitoringWebSocketConsumer.as_asgi()),
    re_path(r'ws/monitoring/alerts/$', AlertsWebSocketConsumer.as_asgi()),
    
    # GNS3 events temps réel
    re_path(r'ws/gns3/events/$', GNS3WebSocketConsumer.as_asgi()),
    re_path(r'ws/gns3/topology/$', GNS3WebSocketConsumer.as_asgi()),
    
    # AI Assistant chat
    re_path(r'ws/ai/chat/$', ChatConsumer.as_asgi()),
    
    # Dashboard temps réel
    re_path(r'ws/dashboard/$', DashboardConsumer.as_asgi()),
]
```

#### **6.2.2 WebSocket Message Protocol**
```json
{
  "type": "event_type",
  "data": {
    "source": "module_name",
    "event_id": "uuid",
    "timestamp": "ISO-8601",
    "payload": { /* event data */ }
  },
  "subscription": ["filter1", "filter2"],
  "priority": "high|normal|low"
}
```

### 6.3 Celery Task Queues

#### **6.3.1 Task Organization par Priorité**
```python
# nms_backend/celery.py - Task scheduling
CELERY_ROUTES = {
    # Tâches critiques - haute priorité
    'monitoring.tasks.collect_metrics': {'queue': 'high_priority'},
    'security_management.tasks.monitor_security_alerts': {'queue': 'high_priority'},
    
    # Tâches normales
    'gns3_integration.tasks.sync_gns3_projects': {'queue': 'normal'},
    'network_management.tasks.discover_network_devices': {'queue': 'normal'},
    
    # Tâches de maintenance - basse priorité
    'common.tasks.cleanup_system_cache': {'queue': 'low_priority'},
    'reporting.tasks.cleanup_old_reports': {'queue': 'low_priority'},
}
```

#### **6.3.2 Task Coordination pour Workflows**
```python
# Exemple de workflow distribué avec Celery
from celery import chain, chord, group

# Workflow de tests de sécurité complets
security_workflow = chain(
    start_gns3_project.s(project_id),
    group(
        collect_metrics.s(),
        monitor_security.s(),
        analyze_topology.s()
    ),
    generate_security_report.s()
)
```

### 6.4 Redis Pub/Sub Messaging

#### **6.4.1 Channel Organization**
```
gns3_events:topology        - Changements de topologie GNS3
gns3_events:nodes          - Événements des nœuds
monitoring:alerts          - Alertes de monitoring
monitoring:metrics         - Métriques temps réel
security:incidents         - Incidents de sécurité
ai:analysis               - Résultats d'analyse IA
system:health             - État de santé du système
```

---

## 🔒 7. SÉCURITÉ TRANSVERSALE

### 7.1 Authentication et Authorization Globale

#### **7.1.1 Architecture de Sécurité**
```ascii
┌─────────────────────────────────────────────────────────────────────────────────┐
│                          SECURITY ARCHITECTURE                                  │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                        AUTHENTICATION LAYER                             │   │
│  │                                                                         │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐   │   │
│  │  │   Django    │  │   Session   │  │    JWT      │  │    API      │   │   │
│  │  │    Auth     │  │   Based     │  │   Tokens    │  │    Keys     │   │   │
│  │  │             │  │             │  │             │  │             │   │   │
│  │  │ • Users     │  │ • Session   │  │ • Stateless │  │ • API Rate  │   │   │
│  │  │ • Groups    │  │   Store     │  │ • Claims    │  │   Limiting  │   │   │
│  │  │ • Perms     │  │ • CSRF      │  │ • Expire    │  │ • Throttle  │   │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘   │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                                        │                                        │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                        AUTHORIZATION LAYER                              │   │
│  │                                                                         │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐   │   │
│  │  │    RBAC     │  │   Module    │  │   Resource  │  │   Action    │   │   │
│  │  │ Role-Based  │  │  Permissions│  │   Control   │  │   Control   │   │   │
│  │  │             │  │             │  │             │  │             │   │   │
│  │  │ • Admin     │  │ • Read      │  │ • Devices   │  │ • Create    │   │   │
│  │  │ • Operator  │  │ • Write     │  │ • Configs   │  │ • Read      │   │   │
│  │  │ • Viewer    │  │ • Execute   │  │ • Reports   │  │ • Update    │   │   │
│  │  │ • Guest     │  │ • Delete    │  │ • Alerts    │  │ • Delete    │   │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘   │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                                        │                                        │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                           SECURITY MONITORING                           │   │
│  │                                                                         │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐   │   │
│  │  │   Audit     │  │  Security   │  │   Threat    │  │   Incident  │   │   │
│  │  │    Trail    │  │   Events    │  │  Detection  │  │   Response  │   │   │
│  │  │             │  │             │  │             │  │             │   │   │
│  │  │ • All Acts  │  │ • Login     │  │ • Anomalies │  │ • Auto      │   │   │
│  │  │ • Changes   │  │ • Failed    │  │ • ML Based  │  │   Block     │   │   │
│  │  │ • Access    │  │ • Privilege │  │ • Patterns  │  │ • Alert     │   │   │
│  │  │ • Logs      │  │ • Elevate   │  │ • Behavior  │  │ • Forensic  │   │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘   │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 7.2 Security Policies Cross-Module

#### **7.2.1 Unified Security Configuration**
```python
# security_management/domain/policies.py
GLOBAL_SECURITY_POLICIES = {
    'authentication': {
        'session_timeout': 3600,  # 1 heure
        'max_login_attempts': 5,
        'lockout_duration': 300,  # 5 minutes
        'password_complexity': 'high',
        'mfa_required': False
    },
    'authorization': {
        'default_permissions': 'read_only',
        'admin_approval_required': ['delete', 'config_change'],
        'audit_all_actions': True,
        'resource_isolation': True
    },
    'data_protection': {
        'encryption_at_rest': True,
        'encryption_in_transit': True,
        'pii_anonymization': True,
        'data_retention_days': 365
    },
    'network_security': {
        'allowed_ip_ranges': ['192.168.0.0/16', '10.0.0.0/8'],
        'rate_limiting': True,
        'ddos_protection': True,
        'intrusion_detection': True
    }
}
```

### 7.3 Audit Trail Système Complet

#### **7.3.1 Unified Audit System**
```python
# common/infrastructure/audit_system.py
class AuditEvent:
    user_id: str
    action: str
    resource_type: str
    resource_id: str
    module: str
    timestamp: datetime
    ip_address: str
    user_agent: str
    result: str  # success, failure, partial
    details: Dict[str, Any]
    
# Exemples d'événements auditables
AUDITABLE_ACTIONS = [
    'user.login', 'user.logout', 'user.failed_login',
    'config.update', 'config.delete', 'config.backup',
    'device.add', 'device.remove', 'device.configure',
    'alert.create', 'alert.acknowledge', 'alert.resolve',
    'report.generate', 'report.export', 'report.share',
    'security.incident', 'security.rule_update', 'security.scan'
]
```

---

## ⚡ 8. PERFORMANCE ET SCALABILITÉ

### 8.1 Bottlenecks Architecture Globale

#### **8.1.1 Identification des Goulots d'Étranglement**
```ascii
┌─────────────────────────────────────────────────────────────────────────────────┐
│                          PERFORMANCE BOTTLENECKS                               │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌─────────────────────────────────────────────════════════════════════────┐   │
│  │                            DATABASE LAYER                               │   │
│  │                         ⚠️  POTENTIAL BOTTLENECK                       │   │
│  │                                                                         │   │
│  │  • PostgreSQL Single Instance                                          │   │
│  │  • No Read Replicas                                                     │   │
│  │  • High Write Load (Metrics, Events, Logs)                            │   │   
│  │  • Complex Joins Across Modules                                        │   │
│  │                                                                         │   │
│  │  📈 SOLUTIONS:                                                         │   │
│  │  • Read Replicas Implementation                                        │   │
│  │  • Database Sharding by Module                                         │   │
│  │  • Connection Pooling (PgBouncer)                                      │   │
│  │  • Query Optimization & Indexing                                       │   │
│  └─────────────────────────────────────────────────────────════════════────┘   │
│                                                                                 │
│  ┌─────────────────────────────────────────────────════════════════════════┐   │
│  │                           EVENT BUS LAYER                               │   │
│  │                         ⚠️  POTENTIAL BOTTLENECK                       │   │
│  │                                                                         │   │
│  │  • Single Redis Instance for All Events                                │   │
│  │  • High Event Volume (Real-time Monitoring)                           │   │
│  │  • Memory Pressure on Redis                                            │   │
│  │  • Event Processing Sequential                                         │   │
│  │                                                                         │   │
│  │  📈 SOLUTIONS:                                                         │   │
│  │  • Redis Cluster Setup                                                 │   │
│  │  • Event Partitioning by Priority                                      │   │
│  │  • Parallel Event Processing                                           │   │
│  │  • Event Buffering & Batching                                          │   │
│  └─────────────────────────────────────────────────════════════════════────┘   │
│                                                                                 │
│  ┌─────────────────────────────────────────────────════════════════════════┐   │
│  │                        CELERY TASK PROCESSING                           │   │
│  │                         ⚠️  POTENTIAL BOTTLENECK                       │   │
│  │                                                                         │   │
│  │  • Single Worker Instance                                              │   │
│  │  • Task Queue Congestion                                               │   │
│  │  • Long-Running Tasks Blocking                                         │   │
│  │  • No Priority-Based Processing                                        │   │
│  │                                                                         │   │
│  │  📈 SOLUTIONS:                                                         │   │
│  │  • Multi-Worker Deployment                                             │   │
│  │  • Priority-Based Task Queues                                          │   │
│  │  • Task Result Caching                                                 │   │
│  │  • Async Task Patterns                                                 │   │
│  └─────────────────────────────────────────────────────────════════════────┘   │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 8.2 Scalability Patterns

#### **8.2.1 Horizontal Scalability Plan**
```yaml
# docker-compose.scale.yml
version: '3.8'
services:
  django:
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '0.50'
          memory: 512M
        reservations:
          cpus: '0.25'
          memory: 256M
  
  celery:
    deploy:
      replicas: 5
      resources:
        limits:
          cpus: '1.00'
          memory: 1G
        reservations:
          cpus: '0.50'
          memory: 512M
  
  redis:
    deploy:
      replicas: 3  # Redis Cluster
      resources:
        limits:
          cpus: '0.25'
          memory: 256M
```

#### **8.2.2 Vertical Scalability Considerations**
```ascii
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           RESOURCE ALLOCATION MATRIX                            │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌───────────────┬─────────────┬─────────────┬─────────────┬─────────────────┐ │
│  │   SERVICE     │     CPU     │   MEMORY    │   STORAGE   │   NETWORK I/O   │ │
│  ├───────────────┼─────────────┼─────────────┼─────────────┼─────────────────┤ │
│  │ Django        │ 🔥🔥🔥       │ 🔥🔥         │ 🔥          │ 🔥🔥🔥           │ │
│  │ PostgreSQL    │ 🔥🔥         │ 🔥🔥🔥🔥     │ 🔥🔥🔥🔥     │ 🔥🔥             │ │
│  │ Redis         │ 🔥          │ 🔥🔥🔥       │ 🔥          │ 🔥🔥🔥           │ │
│  │ Elasticsearch │ 🔥🔥🔥       │ 🔥🔥🔥🔥     │ 🔥🔥🔥       │ 🔥🔥             │ │
│  │ Celery        │ 🔥🔥🔥🔥     │ 🔥🔥         │ 🔥          │ 🔥              │ │
│  │ Monitoring    │ 🔥          │ 🔥          │ 🔥🔥         │ 🔥🔥🔥🔥         │ │
│  │ AI Processing │ 🔥🔥🔥🔥🔥   │ 🔥🔥🔥🔥🔥   │ 🔥🔥         │ 🔥              │ │
│  └───────────────┴─────────────┴─────────────┴─────────────┴─────────────────┘ │
│                                                                                 │
│  🔥      = Low     🔥🔥    = Medium    🔥🔥🔥  = High    🔥🔥🔥🔥 = Very High     │
│  🔥🔥🔥🔥🔥 = Critical                                                          │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 8.3 Caching Strategies Multi-Niveaux

#### **8.3.1 Cache Architecture**
```ascii
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           MULTI-LEVEL CACHE STRATEGY                            │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌─ LEVEL 1: APPLICATION CACHE ─────────────────────────────────────────────┐  │
│  │                                                                           │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │  │
│  │  │   Django    │  │   Session   │  │  Template   │  │   Object    │     │  │
│  │  │    Cache    │  │    Cache    │  │    Cache    │  │   Cache     │     │  │
│  │  │             │  │             │  │             │  │             │     │  │
│  │  │ • Views     │  │ • User      │  │ • Rendered  │  │ • ORM       │     │  │
│  │  │ • API Resp  │  │   Sessions  │  │   Pages     │  │   Objects   │     │  │
│  │  │ • Queries   │  │ • Auth      │  │ • Fragments │  │ • Relations │     │  │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘     │  │
│  └───────────────────────────────────────────────────────────────────────────┘  │
│                                        │                                        │
│  ┌─ LEVEL 2: DISTRIBUTED CACHE ────────────────────────────────────────────┐  │
│  │                                                                           │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │  │
│  │  │   Redis     │  │   Events    │  │  Metrics    │  │  External   │     │  │
│  │  │   Cache     │  │   Cache     │  │   Cache     │  │    API      │     │  │
│  │  │             │  │             │  │             │  │   Cache     │     │  │
│  │  │ • Key-Value │  │ • Real-time │  │ • SNMP      │  │ • GNS3      │     │  │
│  │  │ • TTL Based │  │   Events    │  │   Data      │  │ • External  │     │  │
│  │  │ • Eviction  │  │ • WebSocket │  │ • Time      │  │   Services  │     │  │
│  │  │   Policy    │  │   Messages  │  │   Series    │  │ • REST APIs │     │  │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘     │  │
│  └───────────────────────────────────────────────────────────────────────────┘  │
│                                        │                                        │
│  ┌─ LEVEL 3: DATABASE CACHE ────────────────────────────────────────────────┐  │
│  │                                                                           │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │  │
│  │  │ PostgreSQL  │  │   Query     │  │ Materialized│  │   Index     │     │  │
│  │  │ Shared Buff │  │   Cache     │  │    Views    │  │   Cache     │     │  │
│  │  │             │  │             │  │             │  │             │     │  │
│  │  │ • Buffer    │  │ • Prepared  │  │ • Pre-      │  │ • B-Tree    │     │  │
│  │  │   Pool      │  │   Queries   │  │   computed  │  │ • Hash      │     │  │
│  │  │ • WAL       │  │ • Results   │  │ • Refresh   │  │ • Partial   │     │  │
│  │  │   Cache     │  │   Cache     │  │   Policies  │  │   Indexes   │     │  │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘     │  │
│  └───────────────────────────────────────────────────────────────────────────┘  │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 📊 9. OBSERVABILITÉ SYSTÈME

### 9.1 Distributed Tracing Implementation

#### **9.1.1 Trace Correlation Across Modules**
```python
# common/infrastructure/tracing.py
import uuid
from contextvars import ContextVar

# Context variable pour le trace ID
trace_id_var: ContextVar[str] = ContextVar('trace_id', default=None)

class DistributedTracer:
    def __init__(self):
        self.spans = {}
        
    def start_trace(self, operation_name: str) -> str:
        trace_id = str(uuid.uuid4())
        trace_id_var.set(trace_id)
        
        span = {
            'trace_id': trace_id,
            'span_id': str(uuid.uuid4()),
            'operation_name': operation_name,
            'start_time': timezone.now(),
            'parent_span_id': None,
            'tags': {},
            'logs': []
        }
        
        self.spans[trace_id] = [span]
        return trace_id
        
    def create_child_span(self, operation_name: str) -> str:
        trace_id = trace_id_var.get()
        if not trace_id:
            return self.start_trace(operation_name)
            
        parent_spans = self.spans.get(trace_id, [])
        parent_span_id = parent_spans[-1]['span_id'] if parent_spans else None
        
        span = {
            'trace_id': trace_id,
            'span_id': str(uuid.uuid4()),
            'operation_name': operation_name,
            'start_time': timezone.now(),
            'parent_span_id': parent_span_id,
            'tags': {},
            'logs': []
        }
        
        self.spans[trace_id].append(span)
        return span['span_id']
```

### 9.2 Metrics Aggregation Centralisée

#### **9.2.1 Métriques Système Globales**
```ascii
┌─────────────────────────────────────────────────────────────────────────────────┐
│                            METRICS COLLECTION FLOW                              │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                            METRIC SOURCES                               │   │
│  │                                                                         │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐   │   │
│  │  │  SYSTEM     │  │  APPLICATION│  │  BUSINESS   │  │  EXTERNAL   │   │   │
│  │  │  METRICS    │  │   METRICS   │  │   METRICS   │  │   METRICS   │   │   │
│  │  │             │  │             │  │             │  │             │   │   │
│  │  │ • CPU/RAM   │  │ • Requests  │  │ • Users     │  │ • GNS3 API  │   │   │
│  │  │ • Disk I/O  │  │ • Response  │  │ • Devices   │  │ • SNMP      │   │   │
│  │  │ • Network   │  │   Times     │  │ • Alerts    │  │ • External  │   │   │
│  │  │ • Load      │  │ • Errors    │  │ • Reports   │  │   Services  │   │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘   │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                                        │                                        │
│                                        ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                        METRIC AGGREGATION                               │   │
│  │                                                                         │   │
│  │  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐                │   │
│  │  │   COLLECT   │───►│  PROCESS    │───►│   STORE     │                │   │
│  │  │             │    │             │    │             │                │   │
│  │  │ • Periodic  │    │ • Aggregate │    │ • Time      │                │   │
│  │  │ • Event     │    │ • Calculate │    │   Series    │                │   │
│  │  │   Driven    │    │ • Filter    │    │ • Redis     │                │   │
│  │  │ • Pull/Push │    │ • Transform │    │ • PostgreSQL│                │   │
│  │  └─────────────┘    └─────────────┘    └─────────────┘                │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                                        │                                        │
│                                        ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                         METRIC CONSUMERS                                │   │
│  │                                                                         │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐   │   │
│  │  │  DASHBOARD  │  │   ALERTS    │  │  REPORTING  │  │ AI ANALYSIS │   │   │
│  │  │             │  │             │  │             │  │             │   │   │
│  │  │ • Real-time │  │ • Threshold │  │ • Historical│  │ • Anomaly   │   │   │
│  │  │   Charts    │  │   Based     │  │   Trends    │  │   Detection │   │   │
│  │  │ • Widgets   │  │ • ML Based  │  │ • SLA       │  │ • Predictive│   │   │
│  │  │ • KPIs      │  │ • Escalation│  │   Reports   │  │   Analysis  │   │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘   │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 9.3 Log Correlation Cross-Module

#### **9.3.1 Unified Logging Strategy**
```python
# common/infrastructure/logging_config.py
LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'detailed': {
            'format': '{levelname} {asctime} [{module}] {process:d} {thread:d} [trace:{trace_id}] {message}',
            'style': '{',
        },
        'json': {
            'format': '{"timestamp": "{asctime}", "level": "{levelname}", "module": "{module}", "trace_id": "{trace_id}", "message": "{message}"}',
            'style': '{',
        }
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'detailed',
        },
        'file': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/app/logs/nms.log',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5,
            'formatter': 'json',
        },
        'elasticsearch': {
            'level': 'INFO',
            'class': 'elasticsearch_logging.ElasticsearchHandler',
            'hosts': ['elasticsearch:9200'],
            'index': 'nms-logs',
            'formatter': 'json',
        }
    },
    'loggers': {
        'nms': {
            'handlers': ['console', 'file', 'elasticsearch'],
            'level': 'DEBUG',
            'propagate': False,
        }
    }
}
```

---

## 🚀 10. ÉVOLUTION ARCHITECTURALE

### 10.1 Migration Path vers Microservices

#### **10.1.1 Étapes de Migration**
```ascii
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         MICROSERVICES MIGRATION ROADMAP                         │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  PHASE 1: MODULAR MONOLITH (CURRENT STATE)                                     │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                        Single Django Application                         │   │
│  │                                                                         │   │
│  │  [COMMON] ←→ [AI_ASSISTANT] ←→ [MONITORING] ←→ [SECURITY]               │   │
│  │     ↕              ↕              ↕              ↕                      │   │
│  │  [GNS3] ←→ [NETWORK_MGT] ←→ [QOS_MGMT] ←→ [REPORTING]                  │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                                        │                                        │
│                                        ▼                                        │
│  PHASE 2: SERVICE EXTRACTION                                                   │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                     Extract High-Value Services                          │   │
│  │                                                                         │   │
│  │  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐                │   │
│  │  │ AI Service  │    │ Monitoring  │    │  Security   │                │   │
│  │  │    :8001    │    │  Service    │    │  Service    │                │   │
│  │  │             │    │   :8002     │    │   :8003     │                │   │
│  │  └─────────────┘    └─────────────┘    └─────────────┘                │   │
│  │                                                                         │   │
│  │            ┌─────────────────────────────────┐                         │   │
│  │            │      Core Django App            │                         │   │
│  │            │    (Gateway & Orchestrator)     │                         │   │
│  │            └─────────────────────────────────┘                         │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                                        │                                        │
│                                        ▼                                        │
│  PHASE 3: FULL MICROSERVICES                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                        Complete Service Mesh                            │   │
│  │                                                                         │   │
│  │  ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐               │   │
│  │  │    AI     │ │Monitoring │ │ Security  │ │   GNS3    │               │   │
│  │  │  :8001    │ │   :8002   │ │  :8003    │ │  :8004    │               │   │
│  │  └───────────┘ └───────────┘ └───────────┘ └───────────┘               │   │
│  │                                                                         │   │
│  │  ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐               │   │
│  │  │ Network   │ │    QoS    │ │ Reporting │ │ Dashboard │               │   │
│  │  │  :8005    │ │   :8006   │ │  :8007    │ │  :8008    │               │   │
│  │  └───────────┘ └───────────┘ └───────────┘ └───────────┘               │   │
│  │                                                                         │   │
│  │                    ┌─────────────────────┐                             │   │
│  │                    │   API Gateway       │                             │   │
│  │                    │   Load Balancer     │                             │   │
│  │                    │   Service Discovery │                             │   │
│  │                    └─────────────────────┘                             │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 10.2 Cloud-Native Readiness

#### **10.2.1 Kubernetes Deployment Strategy**
```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nms-django
  namespace: nms-system
spec:
  replicas: 3
  selector:
    matchLabels:
      app: nms-django
  template:
    metadata:
      labels:
        app: nms-django
        version: v2.1.0
    spec:
      containers:
      - name: django
        image: nms/django:2.1.0
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: nms-secrets
              key: database-url
        - name: REDIS_URL
          valueFrom:
            configMapKeyRef:
              name: nms-config
              key: redis-url
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health/
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready/
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
```

### 10.3 Disaster Recovery et Business Continuity

#### **10.3.1 High Availability Architecture**
```ascii
┌─────────────────────────────────────────────────────────────────────────────────┐
│                            HIGH AVAILABILITY SETUP                              │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                           GEOGRAPHIC DISTRIBUTION                        │   │
│  │                                                                         │   │
│  │  ┌─────────────────────┐              ┌─────────────────────┐           │   │
│  │  │    PRIMARY SITE     │              │   SECONDARY SITE    │           │   │
│  │  │     (ACTIVE)        │◄────────────►│      (STANDBY)      │           │   │
│  │  │                     │   Sync Rep   │                     │           │   │
│  │  │ ┌─────────────────┐ │              │ ┌─────────────────┐ │           │   │
│  │  │ │     Django      │ │              │ │     Django      │ │           │   │
│  │  │ │   Cluster x3    │ │              │ │   Cluster x2    │ │           │   │
│  │  │ └─────────────────┘ │              │ └─────────────────┘ │           │   │
│  │  │                     │              │                     │           │   │
│  │  │ ┌─────────────────┐ │              │ ┌─────────────────┐ │           │   │
│  │  │ │   PostgreSQL    │ │              │ │   PostgreSQL    │ │           │   │
│  │  │ │    Master       │ │──Streaming──►│ │    Replica      │ │           │   │
│  │  │ └─────────────────┘ │  Replication │ └─────────────────┘ │           │   │
│  │  │                     │              │                     │           │   │
│  │  │ ┌─────────────────┐ │              │ ┌─────────────────┐ │           │   │
│  │  │ │  Redis Cluster  │ │              │ │  Redis Cluster  │ │           │   │
│  │  │ │    (Master)     │ │──Async Rep──►│ │   (Replica)     │ │           │   │
│  │  │ └─────────────────┘ │              │ └─────────────────┘ │           │   │
│  │  └─────────────────────┘              └─────────────────────┘           │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                                        │                                        │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                            BACKUP STRATEGY                              │   │
│  │                                                                         │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐   │   │
│  │  │   HOURLY    │  │    DAILY    │  │   WEEKLY    │  │   MONTHLY   │   │   │
│  │  │   BACKUP    │  │   BACKUP    │  │   BACKUP    │  │   BACKUP    │   │   │
│  │  │             │  │             │  │             │  │             │   │   │
│  │  │ • Database  │  │ • Full      │  │ • Archive   │  │ • Long-term │   │   │
│  │  │   WAL       │  │   Snapshot  │  │   Backup    │  │   Storage   │   │   │
│  │  │ • Redis     │  │ • Config    │  │ • Disaster  │  │ • Compliance│   │   │
│  │  │   Snapshot  │  │   Files     │  │   Recovery  │  │   Archive   │   │   │
│  │  │ • Log Files │  │ • Code      │  │ • Test      │  │ • Audit     │   │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘   │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 📈 CONCLUSIONS ET RECOMMANDATIONS

### Strengths de l'Architecture Actuelle

1. **🏗️ Architecture Modulaire Solide**
   - Séparation claire des responsabilités
   - Patterns DDD et Hexagonal bien implémentés
   - Faible couplage entre modules

2. **⚡ Communication Hub Centralisé**
   - Event-driven architecture efficace
   - Gestion des workflows complexes
   - Observabilité et traçabilité excellentes

3. **🔒 Sécurité Transversale**
   - Audit trail complet
   - Monitoring de sécurité intégré
   - Gestion des incidents automatisée

4. **🚀 Scalabilité Préparée**
   - Patterns de mise à l'échelle identifiés
   - Infrastructure containerisée
   - Ready for Kubernetes

### Axes d'Amélioration Prioritaires

1. **🔧 Performance Optimization**
   - Implémentation de read replicas PostgreSQL
   - Redis clustering pour haute disponibilité
   - Optimisation des requêtes inter-modules

2. **📊 Observabilité Avancée**
   - Distributed tracing complet
   - Métriques business avancées
   - Alerting proactif intelligent

3. **☁️ Cloud-Native Evolution**
   - Migration progressive vers Kubernetes
   - Service mesh implementation (Istio)
   - Auto-scaling basé sur les métriques

4. **🤖 AI-Driven Operations**
   - Anomaly detection automatique
   - Predictive scaling
   - Auto-healing capabilities

### Roadmap Évolutionnaire Recommandée

**Phase 1 (3 mois) :** Optimisation Performance
- Database read replicas
- Redis clustering
- Cache optimization

**Phase 2 (6 mois) :** Microservices Migration
- Extraction services critiques
- API Gateway implementation
- Service mesh setup

**Phase 3 (12 mois) :** Cloud-Native
- Kubernetes deployment
- CI/CD automation
- Multi-region setup

L'architecture actuelle du système NMS Django constitue une base solide pour l'évolution vers une plateforme de gestion réseau enterprise-grade, avec des capacités d'intelligence artificielle avancées et une observabilité complète du système.

---

**Document généré le 25 juillet 2025**  
**Équipe Architecture NMS Django**