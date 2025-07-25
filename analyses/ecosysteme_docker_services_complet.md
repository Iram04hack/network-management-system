# Écosystème Docker Services Complet - Network Management System

## Vue d'ensemble

Le système de gestion de réseau (NMS) utilise une architecture microservices basée sur Docker avec quatre fichiers de composition principaux orchestrant différents aspects du système.

### Architecture générale
- **Services de base** : Base de données, cache, application Django
- **Services de monitoring** : Métriques, dashboards, surveillance réseau
- **Services de sécurité** : SIEM, IDS/IPS, protection contre les intrusions
- **Services de contrôle de trafic** : QoS, gestion de bande passante

---

## 1. docker-compose.yml - Services de Base

### Services Core

#### 1.1 PostgreSQL Database
- **Service** : `postgres`
- **Image** : `postgres:15-alpine`
- **Container** : `nms-postgres`
- **Ports** : `5432:5432`
- **Réseau** : `nms-backend`
- **Variables d'environnement** :
  - `POSTGRES_USER`: nms_user
  - `POSTGRES_PASSWORD`: nms_password
  - `POSTGRES_DB`: nms_db
- **Persistance** : `./data/postgres:/var/lib/postgresql/data`
- **Rôle** : Base de données principale pour toutes les données applicatives
- **Configuration** : Aucune santé check, redémarrage automatique

#### 1.2 Redis Cache & Message Broker
- **Service** : `redis`
- **Image** : `redis:7-alpine`
- **Container** : `nms-redis`
- **Ports** : `6379:6379`
- **Réseau** : `nms-backend`
- **Configuration** : `redis-server --appendonly yes`
- **Persistance** : `./data/redis:/data`
- **Rôle** : Cache applicatif et broker pour Celery
- **Fonctionnalités** : Persistance AOF activée

#### 1.3 Django Application
- **Service** : `django`
- **Image** : `network-management-system_django:latest`
- **Container** : `nms-django`
- **Ports** : `8000:8000`
- **Réseau** : `nms-backend`
- **Dépendances** : postgres, redis
- **Command** : `uvicorn nms_backend.asgi:application --host 0.0.0.0 --port 8000`
- **Variables d'environnement** :
  - `DEBUG`: true
  - `POSTGRES_HOST`: nms-postgres
  - `REDIS_HOST`: nms-redis
  - `GNS3_HOST`: 172.18.0.1
  - `GNS3_PORT`: 3080
  - `DJANGO_SUPERUSER_USERNAME`: admin
- **Volumes** :
  - Code source : `./web-interface/django__backend:/app`
  - Scripts : `./scripts:/scripts`
  - SSL : `./config/ssl:/app/ssl`
  - Docker socket : `/var/run/docker.sock:/var/run/docker.sock`
- **Rôle** : Application web principale avec interface admin

#### 1.4 Celery Worker
- **Service** : `celery`
- **Image** : `network-management-system_django:latest`  
- **Container** : `nms-celery`
- **Réseau** : `nms-backend`
- **Dépendances** : postgres, redis
- **Command** : `celery -A nms_backend worker -l info`
- **Variables d'environnement** :
  - `CELERY_BROKER_URL`: redis://nms-redis:6379/0
  - `CELERY_RESULT_BACKEND`: redis://nms-redis:6379/0
- **Rôle** : Traitement asynchrone des tâches
- **Configuration** : Script custom d'initialisation via `/fix_celery_deps.sh`

#### 1.5 Celery Beat Scheduler
- **Service** : `celery-beat`
- **Image** : `network-management-system_django:latest`
- **Container** : `nms-celery-beat`
- **Réseau** : `nms-backend`
- **Dépendances** : postgres, redis, celery
- **Command** : `celery -A nms_backend beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler`
- **Rôle** : Planificateur de tâches périodiques
- **Configuration** : Utilise Django Celery Beat pour la persistance

### Services d'Infrastructure

#### 1.6 Elasticsearch
- **Service** : `elasticsearch`
- **Image** : `docker.elastic.co/elasticsearch/elasticsearch:8.9.0`
- **Container** : `nms-elasticsearch`
- **Ports** : `9200:9200`
- **Réseaux** : `nms-monitoring`, `nms-backend`
- **Variables d'environnement** :
  - `discovery.type`: single-node
  - `xpack.security.enabled`: false
  - `ES_JAVA_OPTS`: -Xms1g -Xmx1g
- **Health Check** : `curl -f http://localhost:9200/_cluster/health`
- **Persistance** : `./data/elasticsearch:/usr/share/elasticsearch/data`
- **Rôle** : Moteur de recherche et analytique pour logs et données
- **Configuration** : Mode single-node, sécurité désactivée

#### 1.7 SNMP Agent
- **Service** : `snmp-agent`
- **Image** : `polinux/snmpd:latest`
- **Container** : `nms-snmp-agent`
- **Ports** : `161:161/udp`, `162:162/udp`
- **Réseaux** : `nms-network`, `nms-backend`
- **Variables d'environnement** :
  - `SNMP_COMMUNITY`: public
  - `SNMP_RW_COMMUNITY`: private
  - `SNMP_LOCATION`: NMS Production Environment
- **Health Check** : `snmpget -v2c -c public localhost 1.3.6.1.2.1.1.1.0`
- **Configuration** : `./config/snmp/snmpd.conf:/etc/snmp/snmpd.conf`
- **Rôle** : Agent SNMP pour tests et surveillance réseau
- **Fonctionnalités** : Support SNMP v2c, traps SNMP

#### 1.8 Netflow Collector
- **Service** : `netflow-collector`
- **Image** : `nginx:alpine`
- **Container** : `nms-netflow-collector`
- **Ports** : `9995:80`
- **Réseaux** : `nms-network`, `nms-monitoring`
- **Dépendances** : elasticsearch
- **Health Check** : `wget --quiet --tries=1 --spider http://localhost/health`
- **Configuration** : `./config/netflow/nginx.conf:/etc/nginx/nginx.conf`
- **Rôle** : Collecteur de flux réseau avec API REST
- **Fonctionnalités** : Interface web pour analyse des flux

---

## 2. docker-compose.monitoring.yml - Services de Monitoring

### Services de Métriques

#### 2.1 Prometheus
- **Service** : `prometheus`
- **Image** : `prom/prometheus:latest`
- **Container** : `nms-prometheus`
- **Ports** : `9090:9090`
- **Réseaux** : `nms-backend`, `nms-frontend`
- **Configuration** :
  - Fichier config : `./config/prometheus:/etc/prometheus`
  - Rétention : 200h
  - Lifecycle API activée
- **Health Check** : `wget --no-verbose --tries=1 --spider http://localhost:9090/-/healthy`
- **Persistance** : `./data/prometheus:/prometheus`
- **Rôle** : Collecte et stockage des métriques système et applicatives
- **Fonctionnalités** : TSDB, API REST, interface web

#### 2.2 Grafana
- **Service** : `grafana`
- **Image** : `grafana/grafana:latest`
- **Container** : `nms-grafana`
- **Ports** : `3001:3000`
- **Réseaux** : `nms-backend`, `nms-frontend`
- **Dépendances** : prometheus
- **Variables d'environnement** :
  - `GF_SECURITY_ADMIN_USER`: admin
  - `GF_SECURITY_ADMIN_PASSWORD`: admin
  - `GF_USERS_ALLOW_SIGN_UP`: false
- **Health Check** : `curl -f http://localhost:3000/api/health`
- **Configuration** : `./config/grafana:/etc/grafana`
- **Persistance** : `./data/grafana:/var/lib/grafana`
- **Rôle** : Visualisation et dashboards de monitoring
- **Fonctionnalités** : Dashboards personnalisés, alertes

### Services de Surveillance Réseau

#### 2.3 Netdata
- **Service** : `netdata`
- **Image** : `netdata/netdata:latest`
- **Container** : `nms-netdata`
- **Ports** : `19999:19999`
- **Réseaux** : `nms-backend`, `nms-frontend`
- **Capacités** : `SYS_PTRACE`
- **Volumes système** :
  - `/proc:/host/proc:ro`
  - `/sys:/host/sys:ro`
  - `/var/run/docker.sock:/var/run/docker.sock:ro`
- **Health Check** : `curl -f http://localhost:19999/api/v1/info`
- **Configuration** : `./config/netdata:/etc/netdata`
- **Rôle** : Monitoring en temps réel des performances système
- **Fonctionnalités** : Dashboard interactif, métriques détaillées

#### 2.4 ntopng
- **Service** : `ntopng`
- **Image** : `ntop/ntopng:latest`
- **Container** : `nms-ntopng`
- **Ports** : `3000:3000`
- **Réseaux** : `nms-backend`, `nms-frontend`
- **Configuration** : `./config/ntopng:/etc/ntopng`
- **Health Check** : `curl -f http://localhost:3000/`
- **Persistance** : `./data/ntopng:/var/lib/ntopng`
- **Rôle** : Analyse du trafic réseau et surveillance de la bande passante
- **Fonctionnalités** : Interface web, analyse de flux, géolocalisation

### Load Balancer et Proxy

#### 2.5 HAProxy
- **Service** : `haproxy`
- **Image** : `haproxy:latest`
- **Container** : `nms-haproxy`
- **Ports** : `8080:8080`, `8443:8443`, `1936:1936`
- **Réseaux** : `nms-backend`, `nms-frontend`
- **Dépendances** : grafana, prometheus
- **Configuration** :
  - HAProxy : `./config/haproxy:/usr/local/etc/haproxy`
  - SSL : `./config/ssl:/etc/ssl/certs`
- **Health Check** : `curl -f http://localhost:1936/stats`
- **Rôle** : Load balancer et reverse proxy
- **Fonctionnalités** : SSL termination, stats interface, haute disponibilité

---

## 3. docker-compose.security.yml - Services de Sécurité

### SIEM et Analytics

#### 3.1 Elasticsearch (Sécurité)
- **Service** : `elasticsearch`
- **Image** : `docker.elastic.co/elasticsearch/elasticsearch:8.9.0`
- **Container** : `nms-elasticsearch`
- **Ports** : `9200:9200`, `9300:9300`
- **Réseau** : `nms-backend`
- **Variables d'environnement** :
  - `ES_JAVA_OPTS`: -Xms512m -Xmx512m (optimisé sécurité)
  - `xpack.security.enabled`: false
- **Health Check** : Vérifie le statut du cluster (green/yellow)
- **Configuration** : `./config/elasticsearch:/usr/share/elasticsearch/config/`
- **Rôle** : Stockage et indexation des logs de sécurité
- **Optimisation** : Mémoire réduite pour l'environnement sécurité

#### 3.2 Kibana
- **Service** : `kibana`
- **Image** : `docker.elastic.co/kibana/kibana:8.9.0`
- **Container** : `nms-kibana`
- **Ports** : `5601:5601`
- **Réseaux** : `nms-backend`, `nms-frontend`
- **Dépendances** : elasticsearch
- **Variables d'environnement** :
  - `ELASTICSEARCH_HOSTS`: http://elasticsearch:9200
- **Health Check** : `curl -s http://localhost:5601/api/status | grep -q 'available'`
- **Configuration** : `./config/kibana:/usr/share/kibana/config/`
- **Rôle** : Interface d'analyse et visualisation des logs de sécurité
- **Fonctionnalités** : Dashboards sécurité, recherche avancée

### Services de Protection

#### 3.3 Suricata IDS/IPS
- **Service** : `suricata`
- **Image** : `jasonish/suricata:latest`
- **Container** : `nms-suricata`
- **Ports** : `8068:8068`
- **Réseau** : `nms-backend`
- **Mode** : `privileged: true`
- **Variables d'environnement** :
  - `TZ`: Europe/Paris
- **Configuration** :
  - Config : `./config/suricata:/etc/suricata`
  - Logs : `./data/suricata/logs:/var/log/suricata`
  - Règles : `./data/suricata/rules:/etc/suricata/rules`
- **Command** : `suricata -c /etc/suricata/suricata.yaml -i eth0 -v`
- **Rôle** : Système de détection et prévention d'intrusion
- **Fonctionnalités** : Analyse de paquets, détection de menaces, logging

#### 3.4 Fail2Ban
- **Service** : `fail2ban`
- **Image** : `crazymax/fail2ban:latest`
- **Container** : `nms-fail2ban`
- **Ports** : `5001:5001`
- **Réseaux** : `nms-backend`, `nms-frontend`
- **Capacités** : `NET_ADMIN`, `NET_RAW`
- **Variables d'environnement** :
  - `TZ`: Europe/Paris
  - `F2B_LOG_LEVEL`: INFO
  - `F2B_API_PORT`: 5001
- **Configuration** :
  - Config : `./config/fail2ban:/data`
  - Logs : `./data/fail2ban:/var/log/fail2ban`
  - Logs système : `/var/log:/var/log/host:ro`
- **Rôle** : Protection contre les attaques par force brute
- **Fonctionnalités** : API REST, bannissement automatique, monitoring

---

## 4. docker-compose.traffic-control.yml - Services de Contrôle de Trafic

### QoS et Gestion de Bande Passante

#### 4.1 Traffic Control Service
- **Service** : `traffic-control`
- **Image** : `python:3.10-slim`
- **Container** : `nms-traffic-control`
- **Ports** : `8003:8003`
- **Réseau** : `nms-backend`
- **Mode** : `privileged: true`
- **Variables d'environnement** :
  - `REDIS_HOST`: nms-redis
  - `REDIS_PORT`: 6379
- **Configuration** :
  - Application : `./services/traffic-control:/app`
  - Config TC : `./config/tc:/etc/tc`
- **Outils installés** :
  - `iproute2` : Gestion des interfaces réseau
  - `iptables` : Règles de pare-feu
  - `net-tools` : Utilitaires réseau
  - `ethtool` : Configuration des interfaces
- **Command** : Installation des dépendances + démarrage de l'application Python
- **Rôle** : Contrôle de trafic réseau et mise en œuvre de politiques QoS
- **Fonctionnalités** : API REST, intégration Redis, contrôle de bande passante

---

## Architecture Réseau

### Réseaux Docker

#### Réseaux Principaux
1. **nms-backend** : Réseau principal pour les services core
   - Services : postgres, redis, django, celery, elasticsearch, etc.
   - Type : bridge
   - Communication inter-services

2. **nms-frontend** : Réseau pour les interfaces utilisateur
   - Services : grafana, haproxy, kibana, ntopng, netdata
   - Type : bridge externe
   - Exposition des interfaces web

3. **nms-monitoring** : Réseau dédié au monitoring
   - Services : elasticsearch, netflow-collector
   - Type : bridge
   - Isolation du trafic de monitoring

4. **nms-network** : Réseau pour les services réseau
   - Services : snmp-agent, netflow-collector
   - Type : bridge
   - Simulation d'environnement réseau

### Volumes Persistants

#### Volumes de Données
- `static_content` : Contenu statique Django
- `media_content` : Fichiers média Django
- `prometheus_data` : Métriques Prometheus
- `grafana_data` : Configuration et dashboards Grafana
- `netdata_data` : Données Netdata
- `ntopng_data` : Données ntopng
- `suricata_logs` : Logs Suricata
- `fail2ban_data` : Configuration Fail2Ban

#### Répertoires Montés
- `./data/` : Persistance principale des données
- `./config/` : Configurations des services
- `./web-interface/django__backend` : Code source Django
- `./scripts/` : Scripts d'administration
- `/var/run/docker.sock` : Socket Docker pour contrôle des conteneurs

---

## Matrice des Dépendances

### Services Core
- **Django** → postgres, redis
- **Celery** → postgres, redis
- **Celery-beat** → postgres, redis, celery
- **Netflow-collector** → elasticsearch

### Services Monitoring
- **Grafana** → prometheus
- **HAProxy** → grafana, prometheus

### Services Sécurité  
- **Kibana** → elasticsearch

### Intégrations Inter-Services
- **Redis** : Broker Celery + Cache Django + Traffic Control
- **Elasticsearch** : Logs (monitoring + sécurité) + AI Assistant
- **PostgreSQL** : Données Django + Celery Beat
- **Docker Socket** : Django + Celery (contrôle conteneurs)

---

## Ports et Accès

### Ports d'Administration
- **8000** : Django (API + Admin)
- **9090** : Prometheus
- **3001** : Grafana
- **5601** : Kibana
- **1936** : HAProxy Stats

### Ports de Services
- **5432** : PostgreSQL
- **6379** : Redis
- **9200** : Elasticsearch
- **19999** : Netdata
- **3000** : ntopng

### Ports Réseau
- **161/UDP** : SNMP Agent
- **162/UDP** : SNMP Traps
- **9995** : Netflow Collector API

### Ports de Sécurité
- **8068** : Suricata
- **5001** : Fail2Ban API
- **8003** : Traffic Control API

---

## Health Checks et Surveillance

### Services avec Health Checks
1. **Elasticsearch** : Vérifie l'état du cluster
2. **SNMP Agent** : Test SNMP GET
3. **Netflow Collector** : Endpoint /health
4. **Prometheus** : Endpoint /-/healthy
5. **Grafana** : API /api/health
6. **Netdata** : API /api/v1/info
7. **ntopng** : Page d'accueil
8. **HAProxy** : Stats interface
9. **Kibana** : API status
10. **Suricata** : Aucun health check défini
11. **Fail2Ban** : Aucun health check défini
12. **Traffic Control** : Aucun health check défini

### Configuration des Health Checks
- **Intervalle** : 30s (standard)
- **Timeout** : 5-10s selon le service
- **Retries** : 3-5 tentatives

---

## Recommandations d'Utilisation

### Ordre de Démarrage Recommandé
1. **Services de base** : `docker-compose up -d`
2. **Services de monitoring** : `docker-compose -f docker-compose.monitoring.yml up -d`
3. **Services de sécurité** : `docker-compose -f docker-compose.security.yml up -d`
4. **Services de trafic** : `docker-compose -f docker-compose.traffic-control.yml up -d`

### Gestion des Ressources
- **Elasticsearch** : 1GB RAM (base) / 512MB (sécurité)
- **Services privilégiés** : Suricata, Traffic Control, Netdata
- **Monitoring intensif** : Netdata, Prometheus, ntopng

### Sécurité
- **Accès externe** : Utiliser HAProxy comme point d'entrée unique
- **Authentification** : Grafana (admin/admin), Kibana via Elasticsearch
- **SSL** : Configuration dans ./config/ssl/
- **Fail2Ban** : Protection automatique contre les attaques

---

## Conclusion

L'écosystème Docker du NMS offre une architecture complète et modulaire avec :
- **15 services** répartis sur 4 compositions
- **Architecture microservices** avec séparation des responsabilités
- **Monitoring complet** : métriques, logs, performance, réseau
- **Sécurité avancée** : IDS/IPS, SIEM, protection anti-intrusion
- **Contrôle de trafic** : QoS et gestion de bande passante
- **Haute disponibilité** : Health checks, redémarrage automatique
- **Persistance** : Volumes dédiés pour toutes les données critiques

Cette architecture permet une surveillance complète, une sécurité renforcée et un contrôle fin du trafic réseau, tout en maintenant une séparation claire des responsabilités entre les différents composants du système.