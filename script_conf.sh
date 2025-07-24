#!/bin/bash

# Script de configuration et vérification du système NMS
# Ce script s'assure que l'ensemble de l'architecture NMS est correctement configurée
# et prête pour le développement

set -e

# Couleurs pour l'affichage
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Fonction pour afficher des titres
display_header() {
    echo -e "\n${BLUE}==== $1 ====${NC}\n"
}

# Fonction pour les succès
display_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

# Fonction pour les avertissements
display_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

# Fonction pour les erreurs
display_error() {
    echo -e "${RED}✗ $1${NC}"
    if [ "$2" = "exit" ]; then
        exit 1
    fi
}

# Fonction pour afficher les informations
display_info() {
    echo -e "${CYAN}→ $1${NC}"
}

# Emplacement du projet
PROJECT_DIR="$(pwd)"

display_header "Vérification de l'environnement système"

# Vérifier que Docker est installé
if ! command -v docker &> /dev/null; then
    display_error "Docker n'est pas installé. Veuillez l'installer avant de continuer." "exit"
fi
display_success "Docker est installé"

# Vérifier que Docker Compose est installé
if ! command -v docker-compose &> /dev/null; then
    display_error "Docker Compose n'est pas installé. Veuillez l'installer avant de continuer." "exit"
fi
display_success "Docker Compose est installé"

display_header "Création des réseaux Docker"

# Créer les réseaux Docker nécessaires s'ils n'existent pas
for network in nms-backend nms-frontend nms-monitoring nms-gns3; do
    if ! docker network ls | grep -q $network; then
        display_info "Création du réseau $network..."
        docker network create $network
        display_success "Réseau $network créé"
    else
        display_success "Réseau $network existe déjà"
    fi
done

display_header "Vérification et création des dossiers de configuration"

# Créer les dossiers de configuration nécessaires
mkdir -p "${PROJECT_DIR}/config/elasticsearch"
mkdir -p "${PROJECT_DIR}/config/fail2ban/filter.d"
mkdir -p "${PROJECT_DIR}/config/haproxy"
mkdir -p "${PROJECT_DIR}/config/kibana"
mkdir -p "${PROJECT_DIR}/config/netdata"
mkdir -p "${PROJECT_DIR}/config/prometheus"
mkdir -p "${PROJECT_DIR}/config/suricata/rules"
mkdir -p "${PROJECT_DIR}/config/tc"
mkdir -p "${PROJECT_DIR}/config/grafana"

# Créer les dossiers de données nécessaires
mkdir -p "${PROJECT_DIR}/data/elasticsearch"
mkdir -p "${PROJECT_DIR}/data/grafana"
mkdir -p "${PROJECT_DIR}/data/kibana"
mkdir -p "${PROJECT_DIR}/data/netdata"
mkdir -p "${PROJECT_DIR}/data/ntopng"
mkdir -p "${PROJECT_DIR}/data/postgres"
mkdir -p "${PROJECT_DIR}/data/prometheus"
mkdir -p "${PROJECT_DIR}/data/redis"
mkdir -p "${PROJECT_DIR}/data/suricata"

# Créer le dossier de sauvegarde
mkdir -p "${PROJECT_DIR}/backups"

display_success "Dossiers de configuration et de données créés"

display_header "Vérification et correction des fichiers de configuration"

# Elasticsearch - Fichier de configuration de logging
if [ ! -f "${PROJECT_DIR}/config/elasticsearch/log4j2.properties" ]; then
    display_info "Création du fichier log4j2.properties pour Elasticsearch..."
    cat > "${PROJECT_DIR}/config/elasticsearch/log4j2.properties" << 'EOL'
status = error

appender.console.type = Console
appender.console.name = console
appender.console.layout.type = PatternLayout
appender.console.layout.pattern = [%d{ISO8601}][%-5p][%-25c{1.}] %marker%m%n

rootLogger.level = info
rootLogger.appenderRef.console.ref = console
EOL
    display_success "Fichier log4j2.properties créé"
else
    display_success "Fichier log4j2.properties existe déjà"
fi

# Elasticsearch - Fichier jvm.options
if [ ! -f "${PROJECT_DIR}/config/elasticsearch/jvm.options" ]; then
    display_info "Création du fichier jvm.options pour Elasticsearch..."
    cat > "${PROJECT_DIR}/config/elasticsearch/jvm.options" << 'EOL'
-Xms512m
-Xmx512m

-XX:+UseG1GC
-XX:G1ReservePercent=25
-XX:InitiatingHeapOccupancyPercent=30

-Djava.io.tmpdir=${ES_TMPDIR}

-XX:+HeapDumpOnOutOfMemoryError
-XX:HeapDumpPath=data

-XX:ErrorFile=logs/hs_err_pid%p.log

8-13:-XX:+UseConcMarkSweepGC
8-13:-XX:CMSInitiatingOccupancyFraction=75
8-13:-XX:+UseCMSInitiatingOccupancyOnly

14-:-XX:+UseG1GC

-Dlog4j2.formatMsgNoLookups=true
EOL
    display_success "Fichier jvm.options créé"
else
    display_success "Fichier jvm.options existe déjà"
fi

# Kibana - Fichier de configuration
if [ ! -f "${PROJECT_DIR}/config/kibana/kibana.yml" ]; then
    display_info "Création du fichier kibana.yml..."
    cat > "${PROJECT_DIR}/config/kibana/kibana.yml" << 'EOL'
server.port: 5601
server.host: "0.0.0.0"
elasticsearch.hosts: ["http://elasticsearch:9200"]
monitoring.ui.container.elasticsearch.enabled: true
EOL
    display_success "Fichier kibana.yml créé"
else
    display_success "Fichier kibana.yml existe déjà"
fi

# Grafana - Fichier de configuration
if [ ! -f "${PROJECT_DIR}/config/grafana/grafana.ini" ]; then
    display_info "Création du fichier grafana.ini..."
    cat > "${PROJECT_DIR}/config/grafana/grafana.ini" << 'EOL'
[server]
http_port = 3000
domain = localhost
root_url = %(protocol)s://%(domain)s:%(http_port)s/

[security]
admin_user = admin
admin_password = admin

[users]
allow_sign_up = false

[paths]
data = /var/lib/grafana
logs = /var/log/grafana
plugins = /var/lib/grafana/plugins
provisioning = /etc/grafana/provisioning

[analytics]
reporting_enabled = false
check_for_updates = true
EOL
    display_success "Fichier grafana.ini créé"
else
    display_success "Fichier grafana.ini existe déjà"
fi

# Suricata - Fichier de configuration
if [ ! -f "${PROJECT_DIR}/config/suricata/suricata.yaml" ]; then
    display_info "Création du fichier suricata.yaml..."
    cat > "${PROJECT_DIR}/config/suricata/suricata.yaml" << 'EOL'
%YAML 1.1
---
vars:
  address-groups:
    HOME_NET: "[192.168.0.0/16,10.0.0.0/8,172.16.0.0/12]"
    EXTERNAL_NET: "!$HOME_NET"
    
  port-groups:
    HTTP_PORTS: "80"
    HTTPS_PORTS: "443"
    SSH_PORTS: "22"
    DNS_PORTS: "53"

default-rule-path: /etc/suricata/rules
rule-files:
  - suricata.rules
  - local.rules

# Détection d'interfaces réseau disponibles
af-packet:
  - interface: eth0
    cluster-id: 99
    cluster-type: cluster_flow
    defrag: yes

outputs:
  - fast:
      enabled: yes
      filename: fast.log
      append: yes
  - eve-log:
      enabled: yes
      filetype: regular
      filename: eve.json
      types:
        - alert
        - http
        - dns
        - tls
        - ssh

logging:
  default-log-level: notice
  outputs:
    - console:
        enabled: yes
    - file:
        enabled: yes
        filename: /var/log/suricata/suricata.log

app-layer:
  protocols:
    tls:
      enabled: yes
    http:
      enabled: yes
    ssh:
      enabled: yes
    dns:
      enabled: yes
EOL
    display_success "Fichier suricata.yaml créé"
else
    display_success "Fichier suricata.yaml existe déjà"
fi

# Fail2ban - Fichiers de configuration
if [ ! -f "${PROJECT_DIR}/config/fail2ban/jail.local" ]; then
    display_info "Création du fichier jail.local pour Fail2ban..."
    cat > "${PROJECT_DIR}/config/fail2ban/jail.local" << 'EOL'
[DEFAULT]
ignoreip = 127.0.0.1/8 ::1
bantime = 3600
findtime = 600
maxretry = 5
backend = auto

[sshd]
enabled = true
port = ssh
filter = sshd
logpath = /var/log/auth.log
maxretry = 3

[django-auth]
enabled = true
port = http,https
filter = django-auth
logpath = /var/log/django/auth.log
maxretry = 5
bantime = 7200
EOL
    display_success "Fichier jail.local créé"
else
    display_success "Fichier jail.local existe déjà"
fi

# Fail2ban - Fichier principal
if [ ! -f "${PROJECT_DIR}/config/fail2ban/fail2ban.conf" ]; then
    display_info "Création du fichier fail2ban.conf..."
    cat > "${PROJECT_DIR}/config/fail2ban/fail2ban.conf" << 'EOL'
[Definition]
loglevel = INFO
logtarget = /var/log/fail2ban.log
syslogsocket = auto
socket = /var/run/fail2ban/fail2ban.sock
pidfile = /var/run/fail2ban/fail2ban.pid
dbfile = /var/lib/fail2ban/fail2ban.sqlite3
dbpurgeage = 1d
EOL
    display_success "Fichier fail2ban.conf créé"
else
    display_success "Fichier fail2ban.conf existe déjà"
fi

# Fail2ban - Filtres
if [ ! -f "${PROJECT_DIR}/config/fail2ban/filter.d/common.conf" ]; then
    display_info "Création du fichier common.conf pour Fail2ban..."
    cat > "${PROJECT_DIR}/config/fail2ban/filter.d/common.conf" << 'EOL'
[INCLUDES]

[Definition]
_daemon = \S+

__prefix_line = (?:\A|\n)%(__date_pattern)s%(__hostname_pattern)s(?:%(_daemon)s(?:\[%(__pid_pattern)s\])?: )?

__date_pattern = (?:\w+\s+\d+\s+\d+:\d+:\d+|\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2}))
__hostname_pattern = \S+\s+
__pid_pattern = \d+
EOL
    display_success "Fichier common.conf créé"
else
    display_success "Fichier common.conf existe déjà"
fi

if [ ! -f "${PROJECT_DIR}/config/fail2ban/filter.d/sshd.conf" ]; then
    display_info "Création du fichier sshd.conf pour Fail2ban..."
    cat > "${PROJECT_DIR}/config/fail2ban/filter.d/sshd.conf" << 'EOL'
[INCLUDES]
before = common.conf

[Definition]
_daemon = sshd
failregex = ^%(__prefix_line)s(?:error: PAM: )?Authentication failure for .* from <HOST>( via \S+)?\s*$
            ^%(__prefix_line)s(?:error: PAM: )?User not known to the underlying authentication module for .* from <HOST>\s*$
            ^%(__prefix_line)sFailed \S+ for invalid user .* from <HOST>(?: port \d*)?(?: ssh\d*)?(: (ruser .* )?rhost .* user .*)?$
            ^%(__prefix_line)sFailed \S+ for .* from <HOST>(?: port \d*)?(?: ssh\d*)?(: (ruser .* )?rhost .*)?$
            ^%(__prefix_line)sROOT LOGIN REFUSED.* FROM <HOST>\s*$
            ^%(__prefix_line)s[iI](?:llegal|nvalid) user .* from <HOST>\s*$
ignoreregex = 
EOL
    display_success "Fichier sshd.conf créé"
else
    display_success "Fichier sshd.conf existe déjà"
fi

if [ ! -f "${PROJECT_DIR}/config/fail2ban/filter.d/django-auth.conf" ]; then
    display_info "Création du fichier django-auth.conf pour Fail2ban..."
    cat > "${PROJECT_DIR}/config/fail2ban/filter.d/django-auth.conf" << 'EOL'
[Definition]
failregex = ^.* Login failed for user .* from <HOST>$
            ^.* Login failed: .* from <HOST>$
ignoreregex = 
EOL
    display_success "Fichier django-auth.conf créé"
else
    display_success "Fichier django-auth.conf existe déjà"
fi

# HAProxy - Fichier de configuration
if [ ! -f "${PROJECT_DIR}/config/haproxy/haproxy.cfg" ]; then
    display_info "Création du fichier haproxy.cfg..."
    cat > "${PROJECT_DIR}/config/haproxy/haproxy.cfg" << 'EOL'
global
    log /dev/log    local0
    log /dev/log    local1 notice
    user haproxy
    group haproxy
    daemon

defaults
    log     global
    mode    http
    option  httplog
    timeout connect 5000
    timeout client  50000
    timeout server  50000

# Interface statistiques HAProxy
listen stats
    bind *:1936
    stats enable
    stats uri /
    stats refresh 10s
    stats auth admin:admin

# Frontend principal
frontend main
    bind *:80
    
    # ACLs pour le routage vers différents backends
    acl is_api path_beg /api/
    acl is_admin path_beg /admin/
    acl is_static path_beg /static/
    acl is_netdata path_beg /netdata/
    acl is_kibana path_beg /kibana/
    acl is_prometheus path_beg /prometheus/
    acl is_grafana path_beg /grafana/
    
    # Routage pour les différents backends
    use_backend django-servers if is_api or is_admin or is_static
    use_backend netdata-servers if is_netdata
    use_backend kibana-servers if is_kibana
    use_backend prometheus-servers if is_prometheus
    use_backend grafana-servers if is_grafana
    
    # Redirection par défaut vers Django
    default_backend django-servers

# Backend pour Django
backend django-servers
    mode http
    option forwardfor
    http-request set-header X-Forwarded-Proto https if { ssl_fc }
    server django1 nms-django:8000 check resolvers dns init-addr none

# Backend pour Netdata
backend netdata-servers
    mode http
    option forwardfor
    http-request set-header X-Forwarded-Proto https if { ssl_fc }
    http-request set-path %[path,regsub(^/netdata/,/)]
    server netdata1 nms-netdata:19999 check resolvers dns init-addr none

# Backend pour Kibana
backend kibana-servers
    mode http
    option forwardfor
    http-request set-header X-Forwarded-Proto https if { ssl_fc }
    http-request set-path %[path,regsub(^/kibana/,/)]
    server kibana1 nms-kibana:5601 check resolvers dns init-addr none

# Backend pour Prometheus
backend prometheus-servers
    mode http
    option forwardfor
    http-request set-header X-Forwarded-Proto https if { ssl_fc }
    http-request set-path %[path,regsub(^/prometheus/,/)]
    server prometheus1 nms-prometheus:9090 check resolvers dns init-addr none

# Backend pour Grafana
backend grafana-servers
    mode http
    option forwardfor
    http-request set-header X-Forwarded-Proto https if { ssl_fc }
    http-request set-path %[path,regsub(^/grafana/,/)]
    server grafana1 nms-grafana:3000 check resolvers dns init-addr none

# Configuration des résolveurs DNS pour la résolution des noms d'hôtes
resolvers dns
    nameserver dns1 127.0.0.11:53
    resolve_retries 3
    timeout retry 1s
    hold valid 10s
EOL
    display_success "Fichier haproxy.cfg créé"
else
    display_success "Fichier haproxy.cfg existe déjà"
fi

# Prometheus - Fichier de configuration
if [ ! -f "${PROJECT_DIR}/config/prometheus/prometheus.yml" ]; then
    display_info "Création du fichier prometheus.yml..."
    cat > "${PROJECT_DIR}/config/prometheus/prometheus.yml" << 'EOL'
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  - job_name: 'django'
    metrics_path: '/api/metrics'
    static_configs:
      - targets: ['nms-django:8000']

  - job_name: 'netdata'
    metrics_path: '/api/v1/allmetrics'
    params:
      format: [prometheus]
    static_configs:
      - targets: ['nms-netdata:19999']

  - job_name: 'node'
    static_configs:
      - targets: ['node-exporter:9100']

  - job_name: 'traffic-control'
    static_configs:
      - targets: ['nms-traffic-control:5000']
EOL
    display_success "Fichier prometheus.yml créé"
else
    display_success "Fichier prometheus.yml existe déjà"
fi

# Traffic Control - Fichier de configuration
if [ ! -f "${PROJECT_DIR}/config/tc/rules.yaml" ]; then
    display_info "Création du fichier rules.yaml pour Traffic Control..."
    cat > "${PROJECT_DIR}/config/tc/rules.yaml" << 'EOL'
---
interfaces:
  - name: eth0
    qdisc:
      type: htb
      default: 10
    classes:
      - id: 1:10
        rate: 100mbit
        ceil: 100mbit
        priority: 1
        description: "Trafic standard"
      - id: 1:20
        rate: 50mbit
        ceil: 80mbit
        priority: 2
        description: "Trafic prioritaire (API)"
      - id: 1:30
        rate: 20mbit
        ceil: 50mbit
        priority: 3
        description: "Trafic haute priorité (Monitoring)"
    filters:
      - match: "dst port 8000"
        flowid: 1:20
        description: "API Django"
      - match: "dst port 19999"
        flowid: 1:30
        description: "Netdata"
      - match: "dst port 5601"
        flowid: 1:30
        description: "Kibana"

limits:
  - source: "192.168.10.0/24"
    dest_port: 8000
    rate: 10mbit
    burst: 5kb
    description: "Limitation backend vers API"
  - source: "192.168.20.0/24"
    dest: "192.168.30.0/24"
    rate: 20mbit
    burst: 10kb
    description: "Limitation frontend vers monitoring"

priorities:
  - pattern: "tos 0x10"
    priority: 1
    description: "Trafic prioritaire selon le TOS"
  - pattern: "icmp"
    priority: 0
    description: "ICMP prioritaire"
EOL
    display_success "Fichier rules.yaml créé"
else
    display_success "Fichier rules.yaml existe déjà"
fi

display_header "Vérification et configuration des services Docker"

# Vérification des fichiers docker-compose.yml
if [ ! -f "${PROJECT_DIR}/docker-compose.yml" ]; then
    display_info "Création du fichier docker-compose.yml principal..."
    cat > "${PROJECT_DIR}/docker-compose.yml" << 'EOL'
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    container_name: nms-postgres
    restart: unless-stopped
    environment:
      POSTGRES_USER: nms_user
      POSTGRES_PASSWORD: nms_password
      POSTGRES_DB: nms_db
    volumes:
      - ./data/postgres:/var/lib/postgresql/data
    networks:
      - nms-backend
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U nms_user -d nms_db"]
      interval: 30s
      timeout: 5s
      retries: 3

  redis:
    image: redis:7-alpine
    container_name: nms-redis
    restart: unless-stopped
    command: redis-server --appendonly yes
    volumes:
      - ./data/redis:/data
    networks:
      - nms-backend
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 30s
      timeout: 5s
      retries: 3

  django:
    build:
      context: ./web-interface/django_backend
      dockerfile: Dockerfile
    container_name: nms-django
    restart: unless-stopped
    depends_on:
      - postgres
      - redis
    volumes:
      - ./web-interface/django_backend:/app
      - ./config:/app/config
    networks:
      - nms-backend
      - nms-frontend
      - nms-monitoring
      - nms-gns3
    environment:
      - DJANGO_SETTINGS_MODULE=nms_backend.settings
      - POSTGRES_HOST=postgres
      - POSTGRES_PORT=5432
      - POSTGRES_USER=nms_user
      - POSTGRES_PASSWORD=nms_password
      - POSTGRES_DB=nms_db
      - REDIS_HOST=redis
      - REDIS_PORT=6379
      - DJANGO_SUPERUSER_USERNAME=admin
      - DJANGO_SUPERUSER_PASSWORD=admin
      - DJANGO_SUPERUSER_EMAIL=admin@example.com
    ports:
      - "8000:8000"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/health/"]
      interval: 30s
      timeout: 5s
      retries: 3
    command: ["uvicorn", "nms_backend.asgi:application", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]

  celery:
    build:
      context: ./web-interface/django_backend
      dockerfile: Dockerfile
    container_name: nms-celery
    restart: unless-stopped
    depends_on:
      - postgres
      - redis
      - django
    volumes:
      - ./web-interface/django_backend:/app
      - ./config:/app/config
    networks:
      - nms-backend
    environment:
      - DJANGO_SETTINGS_MODULE=nms_backend.settings
      - POSTGRES_HOST=postgres
      - POSTGRES_PORT=5432
      - POSTGRES_USER=nms_user
      - POSTGRES_PASSWORD=nms_password
      - POSTGRES_DB=nms_db
      - REDIS_HOST=redis
      - REDIS_PORT=6379
    command: ["python", "manage.py", "runserver", "0.0.0.0:8001"]

networks:
  nms-backend:
    external: true
  nms-frontend:
    external: true
  nms-monitoring:
    external: true
  nms-gns3:
    external: true
EOL
    display_success "Fichier docker-compose.yml créé"
else
    display_success "Fichier docker-compose.yml existe déjà"
fi

if [ ! -f "${PROJECT_DIR}/docker-compose.security.yml" ]; then
    display_info "Création du fichier docker-compose.security.yml..."
    cat > "${PROJECT_DIR}/docker-compose.security.yml" << 'EOL'
version: '3.8'

services:
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.9.0
    container_name: nms-elasticsearch
    restart: unless-stopped
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
      - "ES_JAVA_OPTS=-Xms512m -Xmx512m"
    volumes:
      - ./data/elasticsearch:/usr/share/elasticsearch/data
      - ./config/elasticsearch:/usr/share/elasticsearch/config/
    networks:
      - nms-backend
    healthcheck:
      test: ["CMD-SHELL", "curl -s http://localhost:9200/_cluster/health | grep -q '\"status\":\"green\"\\|\"status\":\"yellow\"'"]
      interval: 30s
      timeout: 5s
      retries: 3

  kibana:
    image: docker.elastic.co/kibana/kibana:8.9.0
    container_name: nms-kibana
    restart: unless-stopped
    depends_on:
      - elasticsearch
    environment:
      - ELASTICSEARCH_HOSTS=http://elasticsearch:9200
    volumes:
      - ./config/kibana:/usr/share/kibana/config/
    networks:
      - nms-backend
      - nms-frontend
    ports:
      - "5601:5601"
    healthcheck:
      test: ["CMD-SHELL", "curl -s http://localhost:5601/api/status | grep -q 'available'"]
      interval: 30s
      timeout: 5s
      retries: 3

  suricata:
    image: jasonish/suricata:latest
    container_name: nms-suricata
    restart: unless-stopped
    network_mode: host
    cap_add:
      - NET_ADMIN
      - NET_RAW
    volumes:
      - ./config/suricata:/etc/suricata
      - ./data/suricata:/var/log/suricata
    command: -i eth0 -F /etc/suricata/suricata.yaml
    healthcheck:
      test: ["CMD-SHELL", "pgrep suricata || exit 1"]
      interval: 30s
      timeout: 5s
      retries: 3

  fail2ban:
    image: crazymax/fail2ban:latest
    container_name: nms-fail2ban
    restart: unless-stopped
    network_mode: host
    cap_add:
      - NET_ADMIN
      - NET_RAW
    volumes:
      - ./config/fail2ban:/etc/fail2ban
      - /var/log:/var/log:ro
    environment:
      - F2B_DB_PURGE_AGE=7d
    healthcheck:
      test: ["CMD-SHELL", "fail2ban-client status || exit 1"]
      interval: 30s
      timeout: 5s
      retries: 3

networks:
  nms-backend:
    external: true
  nms-frontend:
    external: true
EOL
    display_success "Fichier docker-compose.security.yml créé"
else
    display_success "Fichier docker-compose.security.yml existe déjà"
fi

if [ ! -f "${PROJECT_DIR}/docker-compose.monitoring.yml" ]; then
    display_info "Création du fichier docker-compose.monitoring.yml..."
    cat > "${PROJECT_DIR}/docker-compose.monitoring.yml" << 'EOL'
version: '3.8'

services:
  netdata:
    image: netdata/netdata:latest
    container_name: nms-netdata
    restart: unless-stopped
    cap_add:
      - SYS_PTRACE
    security_opt:
      - apparmor:unconfined
    volumes:
      - ./config/netdata:/etc/netdata
      - ./data/netdata:/var/lib/netdata
      - /proc:/host/proc:ro
      - /sys:/host/sys:ro
      - /etc/os-release:/host/etc/os-release:ro
    environment:
      - NETDATA_CLAIM_TOKEN=
      - NETDATA_CLAIM_URL=https://app.netdata.cloud
    networks:
      - nms-monitoring
    ports:
      - "19999:19999"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:19999/api/v1/info"]
      interval: 30s
      timeout: 5s
      retries: 3

  ntopng:
    image: ntop/ntopng:latest
    container_name: nms-ntopng
    restart: unless-stopped
    network_mode: host
    environment:
      - INTERFACE=eth0
    volumes:
      - ./data/ntopng:/var/lib/ntopng
    command: --community
    healthcheck:
      test: ["CMD-SHELL", "curl -s http://localhost:3000 | grep -q 'ntopng'"]
      interval: 30s
      timeout: 5s
      retries: 3

  haproxy:
    image: haproxy:latest
    container_name: nms-haproxy
    restart: unless-stopped
    volumes:
      - ./config/haproxy:/usr/local/etc/haproxy
    networks:
      - nms-backend
      - nms-frontend
      - nms-monitoring
    ports:
      - "80:80"
      - "443:443"
      - "1936:1936"
    healthcheck:
      test: ["CMD-SHELL", "haproxy -c -f /usr/local/etc/haproxy/haproxy.cfg"]
      interval: 30s
      timeout: 5s
      retries: 3

  prometheus:
    image: prom/prometheus:latest
    container_name: nms-prometheus
    restart: unless-stopped
    user: "65534:65534"  # Utilisateur nobody
    volumes:
      - ./config/prometheus:/etc/prometheus
      - ./data/prometheus:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/usr/share/prometheus/console_libraries'
      - '--web.console.templates=/usr/share/prometheus/consoles'
      - '--query.lookback-delta=5m'
    networks:
      - nms-monitoring
    ports:
      - "9090:9090"
    healthcheck:
      test: ["CMD-SHELL", "wget -q -O- http://localhost:9090/-/healthy || exit 1"]
      interval: 30s
      timeout: 5s
      retries: 3

  grafana:
    image: grafana/grafana:latest
    container_name: nms-grafana
    restart: unless-stopped
    user: "472:472"  # Utilisateur grafana
    volumes:
      - ./config/grafana:/etc/grafana
      - ./data/grafana:/var/lib/grafana
    networks:
      - nms-monitoring
    ports:
      - "3001:3000"
    environment:
      - GF_SECURITY_ADMIN_USER=admin
      - GF_SECURITY_ADMIN_PASSWORD=admin
    healthcheck:
      test: ["CMD-SHELL", "wget -q -O- http://localhost:3000/api/health || exit 1"]
      interval: 30s
      timeout: 5s
      retries: 3

networks:
  nms-backend:
    external: true
  nms-frontend:
    external: true
  nms-monitoring:
    external: true
EOL
    display_success "Fichier docker-compose.monitoring.yml créé"
else
    display_success "Fichier docker-compose.monitoring.yml existe déjà"
fi

if [ ! -f "${PROJECT_DIR}/docker-compose.traffic-control.yml" ]; then
    display_info "Création du fichier docker-compose.traffic-control.yml..."
    cat > "${PROJECT_DIR}/docker-compose.traffic-control.yml" << 'EOL'
version: '3.8'

services:
  traffic-control:
    image: python:3.10-slim
    container_name: nms-traffic-control
    restart: unless-stopped
    privileged: true
    network_mode: host
    volumes:
      - ./services/traffic-control:/app
      - ./config/tc:/etc/tc
    working_dir: /app
    command: >
      bash -c "apt-get update && apt-get install -y iproute2 iptables net-tools ethtool curl procps && 
      pip install -r requirements.txt && 
      python app.py"
EOL
    display_success "Fichier docker-compose.traffic-control.yml créé"
else
    display_success "Fichier docker-compose.traffic-control.yml existe déjà"
fi

display_header "Vérification et configuration du service Traffic Control"

# Créer le répertoire pour le service Traffic Control
mkdir -p "${PROJECT_DIR}/services/traffic-control"

# Créer le fichier requirements.txt pour Traffic Control
if [ ! -f "${PROJECT_DIR}/services/traffic-control/requirements.txt" ]; then
    display_info "Création du fichier requirements.txt pour Traffic Control..."
    cat > "${PROJECT_DIR}/services/traffic-control/requirements.txt" << 'EOL'
Flask==2.2.3
Werkzeug==2.2.3
Flask-RESTful==0.3.10
pyroute2==0.7.9
requests==2.31.0
gunicorn==21.2.0
pyyaml==6.0.1
python-dotenv==1.0.0
EOL
    display_success "Fichier requirements.txt créé"
else
    display_success "Fichier requirements.txt existe déjà"
fi

# Créer le fichier app.py pour Traffic Control
if [ ! -f "${PROJECT_DIR}/services/traffic-control/app.py" ]; then
    display_info "Création du fichier app.py pour Traffic Control..."
    cat > "${PROJECT_DIR}/services/traffic-control/app.py" << 'EOL'
from flask import Flask, request, jsonify
from flask_restful import Api, Resource
import yaml
import subprocess
import os
import logging
import json

# Configuration du logger
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)
api = Api(app)

# Chemins des fichiers de configuration
CONFIG_FILE = '/etc/tc/rules.yaml'

def load_config():
    """Charge la configuration depuis le fichier YAML."""
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as file:
                return yaml.safe_load(file)
        else:
            logger.warning(f"Fichier de configuration {CONFIG_FILE} non trouvé. Utilisation de la configuration par défaut.")
            return {"interfaces": [], "limits": [], "priorities": []}
    except Exception as e:
        logger.error(f"Erreur lors du chargement de la configuration: {e}")
        return {"interfaces": [], "limits": [], "priorities": []}

def save_config(config):
    """Sauvegarde la configuration dans le fichier YAML."""
    try:
        # Créer le répertoire si nécessaire
        os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
        
        with open(CONFIG_FILE, 'w') as file:
            yaml.dump(config, file, default_flow_style=False)
        return True
    except Exception as e:
        logger.error(f"Erreur lors de la sauvegarde de la configuration: {e}")
        return False

def apply_tc_rules():
    """Applique les règles TC basées sur la configuration."""
    config = load_config()
    try:
        if not config or not config.get('interfaces'):
            logger.warning("Aucune interface configurée.")
            return False
            
        # Réinitialiser toutes les interfaces
        for interface in config.get('interfaces', []):
            iface_name = interface.get('name')
            if not iface_name:
                continue
                
            logger.info(f"Configuration de l'interface {iface_name}")
            
            # Supprimer les configurations existantes
            subprocess.run(['tc', 'qdisc', 'del', 'dev', iface_name, 'root'], 
                          stderr=subprocess.PIPE, stdout=subprocess.PIPE)
            
            # Créer le qdisc
            qdisc_type = interface.get('qdisc', {}).get('type', 'htb')
            default_class = interface.get('qdisc', {}).get('default', '10')
            
            subprocess.run(['tc', 'qdisc', 'add', 'dev', iface_name, 'root', 
                           'handle', '1:', qdisc_type, 
                           'default', default_class])
            
            # Créer les classes
            for cls in interface.get('classes', []):
                class_id = cls.get('id', '1:10')
                rate = cls.get('rate', '10mbit')
                ceil = cls.get('ceil', rate)
                priority = str(cls.get('priority', 1))
                
                subprocess.run(['tc', 'class', 'add', 'dev', iface_name, 
                               'parent', '1:', 'classid', class_id, 'htb', 
                               'rate', rate, 'ceil', ceil, 
                               'prio', priority])
            
            # Ajouter les filtres
            for idx, filter_rule in enumerate(interface.get('filters', []), 1):
                match = filter_rule.get('match', '')
                flowid = filter_rule.get('flowid', '1:10')
                
                if match:
                    subprocess.run(['tc', 'filter', 'add', 'dev', iface_name, 
                                  'protocol', 'ip', 'parent', '1:', 'prio', '1', 
                                  'u32', 'match', 'ip', match, 
                                  'flowid', flowid])
        
        # Appliquer les limites de bande passante
        for limit in config.get('limits', []):
            source = limit.get('source', '')
            dest = limit.get('dest', '')
            dest_port = limit.get('dest_port', '')
            rate = limit.get('rate', '10mbit')
            burst = limit.get('burst', '10kb')
            
            if not (source or dest or dest_port):
                continue
                
            cmd = ['tc', 'filter', 'add', 'dev', 'eth0', 'parent', '1:', 'protocol', 'ip', 
                  'prio', '2', 'u32']
            
            if source:
                cmd.extend(['match', 'ip', 'src', source])
            
            if dest:
                cmd.extend(['match', 'ip', 'dst', dest])
            
            if dest_port:
                cmd.extend(['match', 'ip', 'dport', str(dest_port), '0xffff'])
            
            cmd.extend(['police', 'rate', rate, 'burst', burst, 
                       'drop', 'flowid', '1:1'])
            
            subprocess.run(cmd)
        
        return True
    except Exception as e:
        logger.error(f"Erreur lors de l'application des règles TC: {e}")
        return False

def get_tc_stats():
    """Récupère les statistiques TC pour toutes les interfaces."""
    config = load_config()
    stats = {}
    
    try:
        interfaces = [iface.get('name') for iface in config.get('interfaces', [])]
        if not interfaces:
            # Si aucune interface n'est configurée, utiliser eth0 par défaut
            interfaces = ['eth0']
            
        for iface in interfaces:
            # Statistiques du qdisc
            qdisc_proc = subprocess.run(['tc', '-s', 'qdisc', 'show', 'dev', iface], 
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # Statistiques des classes
            class_proc = subprocess.run(['tc', '-s', 'class', 'show', 'dev', iface], 
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # Statistiques des filtres
            filter_proc = subprocess.run(['tc', '-s', 'filter', 'show', 'dev', iface], 
                                     stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            stats[iface] = {
                'qdisc': qdisc_proc.stdout.decode('utf-8'),
                'class': class_proc.stdout.decode('utf-8'),
                'filter': filter_proc.stdout.decode('utf-8')
            }
        return stats
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des statistiques TC: {e}")
        return {}

# Routes de l'API
class Health(Resource):
    def get(self):
        return {"status": "ok"}

class RulesList(Resource):
    def get(self):
        config = load_config()
        return jsonify(config)
    
    def post(self):
        try:
            config = request.get_json()
            if save_config(config):
                if apply_tc_rules():
                    return {"message": "Configuration mise à jour et appliquée"}, 200
                else:
                    return {"message": "Configuration mise à jour mais erreur lors de l'application"}, 500
            else:
                return {"message": "Erreur lors de la mise à jour de la configuration"}, 500
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour des règles: {e}")
            return {"message": f"Erreur: {str(e)}"}, 500

class InterfaceRules(Resource):
    def get(self, interface):
        config = load_config()
        for iface in config.get('interfaces', []):
            if iface.get('name') == interface:
                return jsonify(iface)
        return {"message": f"Interface {interface} non trouvée"}, 404
    
    def put(self, interface):
        try:
            new_config = request.get_json()
            config = load_config()
            
            # Mettre à jour ou ajouter l'interface
            interface_found = False
            for i, iface in enumerate(config.get('interfaces', [])):
                if iface.get('name') == interface:
                    config['interfaces'][i] = new_config
                    interface_found = True
                    break
            
            if not interface_found:
                if 'interfaces' not in config:
                    config['interfaces'] = []
                config['interfaces'].append(new_config)
            
            if save_config(config):
                if apply_tc_rules():
                    return {"message": f"Configuration pour {interface} mise à jour et appliquée"}, 200
                else:
                    return {"message": f"Configuration pour {interface} mise à jour mais erreur lors de l'application"}, 500
            else:
                return {"message": f"Erreur lors de la mise à jour de la configuration pour {interface}"}, 500
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour des règles pour {interface}: {e}")
            return {"message": f"Erreur: {str(e)}"}, 500

class TCStats(Resource):
    def get(self):
        stats = get_tc_stats()
        return jsonify(stats)

# Enregistrement des ressources API
api.add_resource(Health, '/health')
api.add_resource(RulesList, '/rules')
api.add_resource(InterfaceRules, '/rules/interface/<string:interface>')
api.add_resource(TCStats, '/stats')

@app.route('/')
def index():
    return """
    <h1>API Traffic Control</h1>
    <p>API pour la gestion de la qualité de service (QoS) avec Traffic Control</p>
    <h2>Points d'accès disponibles:</h2>
    <ul>
        <li><a href="/health">Health Check</a></li>
        <li><a href="/rules">Liste des règles</a></li>
        <li><a href="/stats">Statistiques</a></li>
    </ul>
    """

if __name__ == '__main__':
    # Définir le mode de débogage en fonction de l'environnement
    debug_mode = os.environ.get('DEBUG', 'False').lower() == 'true'
    
    # Initialiser au démarrage
    logger.info("Initialisation du service Traffic Control...")
    apply_tc_rules()
    
    # Démarrer l'application
    app.run(host='0.0.0.0', port=5000, debug=debug_mode)
EOL
    display_success "Fichier app.py créé"
else
    display_success "Fichier app.py existe déjà"
fi

display_header "Vérification et configuration du backend Django"

# Créer les répertoires pour le backend Django
mkdir -p "${PROJECT_DIR}/web-interface/django_backend/nms_backend"
mkdir -p "${PROJECT_DIR}/web-interface/django_backend/static/css"
mkdir -p "${PROJECT_DIR}/web-interface/django_backend/static/js"
mkdir -p "${PROJECT_DIR}/web-interface/django_backend/static/img"
mkdir -p "${PROJECT_DIR}/web-interface/django_backend/templates"
mkdir -p "${PROJECT_DIR}/web-interface/django_backend/staticfiles"

# Créer le Dockerfile pour Django
if [ ! -f "${PROJECT_DIR}/web-interface/django_backend/Dockerfile" ]; then
    display_info "Création du Dockerfile pour Django..."
    cat > "${PROJECT_DIR}/web-interface/django_backend/Dockerfile" << 'EOL'
FROM python:3.10-slim

WORKDIR /app

# Installer les dépendances système
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    netcat-openbsd \
    curl \
    procps \
    && rm -rf /var/lib/apt/lists/*

# Copier les fichiers de dépendances
COPY requirements.txt .

# Installer les dépendances Python
RUN pip install --no-cache-dir -r requirements.txt

# Copier le code source
COPY . .

# Rendre le script entrypoint exécutable
RUN chmod +x entrypoint.sh

# Exposer le port
EXPOSE 8000

# Point d'entrée
ENTRYPOINT ["/app/entrypoint.sh"]

# Commande par défaut
CMD ["uvicorn", "nms_backend.asgi:application", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
EOL
    display_success "Dockerfile créé"
else
    display_success "Dockerfile existe déjà"
fi

# Créer le fichier entrypoint.sh pour Django
if [ ! -f "${PROJECT_DIR}/web-interface/django_backend/entrypoint.sh" ]; then
    display_info "Création du fichier entrypoint.sh pour Django..."
    cat > "${PROJECT_DIR}/web-interface/django_backend/entrypoint.sh" << 'EOL'
#!/bin/bash

# Attendre que PostgreSQL soit prêt
echo "Attente du démarrage de PostgreSQL..."
while ! nc -z postgres 5432; do
  sleep 0.1
done
echo "PostgreSQL démarré"

# Exécuter les migrations
echo "Application des migrations..."
python manage.py migrate

# Créer un superuser si nécessaire
if [ "$DJANGO_SUPERUSER_USERNAME" ] && [ "$DJANGO_SUPERUSER_PASSWORD" ] && [ "$DJANGO_SUPERUSER_EMAIL" ]; then
    python manage.py createsuperuser --noinput || echo "Le superutilisateur existe déjà"
fi

# Collecter les fichiers statiques
echo "Collecte des fichiers statiques..."
python manage.py collectstatic --noinput

# Exécuter la commande
exec "$@"
EOL
    chmod +x "${PROJECT_DIR}/web-interface/django_backend/entrypoint.sh"
    display_success "Fichier entrypoint.sh créé"
else
    display_success "Fichier entrypoint.sh existe déjà"
fi

# Créer le fichier requirements.txt pour Django
if [ ! -f "${PROJECT_DIR}/web-interface/django_backend/requirements.txt" ]; then
    display_info "Création du fichier requirements.txt pour Django..."
    cat > "${PROJECT_DIR}/web-interface/django_backend/requirements.txt" << 'EOL'
Django==4.2.8
djangorestframework==3.14.0
django-cors-headers==4.3.0
django-filter==23.3
psycopg2-binary==2.9.9
redis==5.0.1
channels==4.0.0
daphne==4.0.0
uvicorn==0.23.2
requests==2.31.0
python-dotenv==1.0.0
EOL
    display_success "Fichier requirements.txt créé"
else
    display_success "Fichier requirements.txt existe déjà"
fi

# Créer le fichier manage.py pour Django
if [ ! -f "${PROJECT_DIR}/web-interface/django_backend/manage.py" ]; then
    display_info "Création du fichier manage.py pour Django..."
    cat > "${PROJECT_DIR}/web-interface/django_backend/manage.py" << 'EOL'
#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys


def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nms_backend.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
EOL
    chmod +x "${PROJECT_DIR}/web-interface/django_backend/manage.py"
    display_success "Fichier manage.py créé"
else
    display_success "Fichier manage.py existe déjà"
fi

# Créer le fichier settings.py pour Django
if [ ! -f "${PROJECT_DIR}/web-interface/django_backend/nms_backend/settings.py" ]; then
    display_info "Création du fichier settings.py pour Django..."
    cat > "${PROJECT_DIR}/web-interface/django_backend/nms_backend/settings.py" << 'EOL'
import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-change-this-in-production'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['*']

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'corsheaders',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'nms_backend.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'nms_backend.wsgi.application'

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('POSTGRES_DB', 'nms_db'),
        'USER': os.environ.get('POSTGRES_USER', 'nms_user'),
        'PASSWORD': os.environ.get('POSTGRES_PASSWORD', 'nms_password'),
        'HOST': os.environ.get('POSTGRES_HOST', 'postgres'),
        'PORT': os.environ.get('POSTGRES_PORT', '5432'),
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'fr-fr'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# CORS settings
CORS_ALLOW_ALL_ORIGINS = True

# REST Framework settings
REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.BasicAuthentication',
    ],
}
EOL
    display_success "Fichier settings.py créé"
else
    display_success "Fichier settings.py existe déjà"
fi

# Créer le fichier urls.py pour Django
if [ ! -f "${PROJECT_DIR}/web-interface/django_backend/nms_backend/urls.py" ]; then
    display_info "Création du fichier urls.py pour Django..."
    cat > "${PROJECT_DIR}/web-interface/django_backend/nms_backend/urls.py" << 'EOL'
from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse
from django.shortcuts import render
from django.conf import settings
from django.conf.urls.static import static

def health_check(request):
    return JsonResponse({"status": "ok"})

def index(request):
    return render(request, 'index.html')

urlpatterns = [
    path('', index, name='index'),
    path('admin/', admin.site.urls),
    path('api/health/', health_check, name='health_check'),
]

# Ajouter les URLs pour servir les fichiers statiques en développement
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
EOL
    display_success "Fichier urls.py créé"
else
    display_success "Fichier urls.py existe déjà"
fi

# Créer le fichier wsgi.py pour Django
if [ ! -f "${PROJECT_DIR}/web-interface/django_backend/nms_backend/wsgi.py" ]; then
    display_info "Création du fichier wsgi.py pour Django..."
    cat > "${PROJECT_DIR}/web-interface/django_backend/nms_backend/wsgi.py" << 'EOL'
import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nms_backend.settings')
application = get_wsgi_application()
EOL
    display_success "Fichier wsgi.py créé"
else
    display_success "Fichier wsgi.py existe déjà"
fi

# Créer le fichier asgi.py pour Django
if [ ! -f "${PROJECT_DIR}/web-interface/django_backend/nms_backend/asgi.py" ]; then
    display_info "Création du fichier asgi.py pour Django..."
    cat > "${PROJECT_DIR}/web-interface/django_backend/nms_backend/asgi.py" << 'EOL'
import os
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nms_backend.settings')
application = get_asgi_application()
EOL
    display_success "Fichier asgi.py créé"
else
    display_success "Fichier asgi.py existe déjà"
fi

# Créer le fichier __init__.py pour Django
if [ ! -f "${PROJECT_DIR}/web-interface/django_backend/nms_backend/__init__.py" ]; then
    display_info "Création du fichier __init__.py pour Django..."
    cat > "${PROJECT_DIR}/web-interface/django_backend/nms_backend/__init__.py" << 'EOL'
# This file is intentionally empty
EOL
    display_success "Fichier __init__.py créé"
else
    display_success "Fichier __init__.py existe déjà"
fi

# Créer un fichier de template de base pour Django
if [ ! -f "${PROJECT_DIR}/web-interface/django_backend/templates/base.html" ]; then
    display_info "Création du fichier template de base pour Django..."
    cat > "${PROJECT_DIR}/web-interface/django_backend/templates/base.html" << 'EOL'
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}Système de Gestion Réseau{% endblock %}</title>
    {% load static %}
    <link rel="stylesheet" href="{% static 'css/main.css' %}">
    <link rel="icon" href="{% static 'img/favicon.ico' %}">
    {% block extra_css %}{% endblock %}
</head>
<body>
    <header>
        <div class="container">
            <h1>Système de Gestion Réseau (NMS)</h1>
        </div>
        <nav>
            <div class="container">
                <ul>
                    <li><a href="/">Tableau de bord</a></li>
                    <li><a href="/security/">Sécurité</a></li>
                    <li><a href="/monitoring/">Monitoring</a></li>
                    <li><a href="/qos/">QoS</a></li>
                    <li><a href="/network/">Réseau</a></li>
                    <li><a href="/admin/">Admin</a></li>
                </ul>
            </div>
        </nav>
    </header>

    <main class="container">
        {% if messages %}
            {% for message in messages %}
                <div class="alert alert-{{ message.tags }}">
                    <span class="close">&times;</span>
                    {{ message }}
                </div>
            {% endfor %}
        {% endif %}

        {% block content %}{% endblock %}
    </main>

    <footer>
        <div class="container">
            <p>&copy; 2025 Système de Gestion Réseau - Tous droits réservés</p>
        </div>
    </footer>

    <script src="{% static 'js/main.js' %}"></script>
    {% block extra_js %}{% endblock %}
</body>
</html>
EOL
    display_success "Fichier template de base créé"
else
    display_success "Fichier template de base existe déjà"
fi

# Créer un fichier de template d'index pour Django
if [ ! -f "${PROJECT_DIR}/web-interface/django_backend/templates/index.html" ]; then
    display_info "Création du fichier template d'index pour Django..."
    cat > "${PROJECT_DIR}/web-interface/django_backend/templates/index.html" << 'EOL'
{% extends 'base.html' %}

{% block title %}Tableau de bord - NMS{% endblock %}

{% block content %}
<div class="dashboard-container">
    <h1>Tableau de bord</h1>
    
    <div class="dashboard-grid">
        <div class="dashboard-card">
            <h2>Sécurité</h2>
            <p>Statut: <span class="status-badge status-good">Protégé</span></p>
            <p>Alertes: <span class="count">0</span> nouvelles alertes</p>
            <a href="/security/" class="btn">Gérer la sécurité</a>
        </div>
        
        <div class="dashboard-card">
            <h2>Monitoring</h2>
            <p>Services actifs: <span class="count">9</span>/10</p>
            <p>Dernière vérification: Il y a 5 minutes</p>
            <a href="/monitoring/" class="btn">Voir les métriques</a>
        </div>
        
        <div class="dashboard-card">
            <h2>Qualité de Service</h2>
            <p>Règles actives: <span class="count">5</span></p>
            <p>Bande passante utilisée: 45%</p>
            <a href="/qos/" class="btn">Gérer la QoS</a>
        </div>
        
        <div class="dashboard-card">
            <h2>Réseau</h2>
            <p>Appareils actifs: <span class="count">15</span></p>
            <p>Topologies: <span class="count">3</span></p>
            <a href="/network/" class="btn">Gérer le réseau</a>
        </div>
    </div>
</div>
{% endblock %}
EOL
    display_success "Fichier template d'index créé"
else
    display_success "Fichier template d'index existe déjà"
fi

# Créer un fichier CSS de base pour Django
if [ ! -f "${PROJECT_DIR}/web-interface/django_backend/static/css/main.css" ]; then
    display_info "Création du fichier CSS de base pour Django..."
    cat > "${PROJECT_DIR}/web-interface/django_backend/static/css/main.css" << 'EOL'
/* Style principal pour le NMS */
body {
    font-family: 'Arial', sans-serif;
    margin: 0;
    padding: 0;
    color: #333;
    background-color: #f4f4f4;
}

.container {
    width: 90%;
    margin: 0 auto;
    padding: 20px;
}

header {
    background-color: #2c3e50;
    color: white;
    padding: 20px 0;
    margin-bottom: 20px;
}

header h1 {
    margin: 0;
    padding: 0 20px;
}

nav {
    background-color: #34495e;
}

nav ul {
    list-style: none;
    padding: 0;
    margin: 0;
    display: flex;
}

nav li {
    padding: 15px 20px;
}

nav a {
    color: white;
    text-decoration: none;
}

nav a:hover {
    color: #3498db;
}

.dashboard-card {
    background: white;
    border-radius: 5px;
    box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    padding: 20px;
    margin-bottom: 20px;
}

.dashboard-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
    grid-gap: 20px;
}

.dashboard-card h2 {
    margin-top: 0;
    color: #2c3e50;
    border-bottom: 1px solid #eee;
    padding-bottom: 10px;
}

.status-badge {
    padding: 3px 8px;
    border-radius: 3px;
    font-weight: bold;
}

.status-good {
    background-color: #2ecc71;
    color: white;
}

.status-warning {
    background-color: #f39c12;
    color: white;
}

.status-danger {
    background-color: #e74c3c;
    color: white;
}

.count {
    font-weight: bold;
    color: #3498db;
}

footer {
    background-color: #2c3e50;
    color: white;
    text-align: center;
    padding: 20px 0;
    margin-top: 40px;
}

.btn {
    display: inline-block;
    padding: 8px 16px;
    background-color: #3498db;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    text-decoration: none;
}

.btn:hover {
    background-color: #2980b9;
}

.alert {
    padding: 15px;
    margin-bottom: 20px;
    border: 1px solid transparent;
    border-radius: 4px;
}

.alert-success {
    color: #3c763d;
    background-color: #dff0d8;
    border-color: #d6e9c6;
}

.alert-danger {
    color: #a94442;
    background-color: #f2dede;
    border-color: #ebccd1;
}

.alert-warning {
    color: #8a6d3b;
    background-color: #fcf8e3;
    border-color: #faebcc;
}

.alert-info {
    color: #31708f;
    background-color: #d9edf7;
    border-color: #bce8f1;
}
EOL
    display_success "Fichier CSS de base créé"
else
    display_success "Fichier CSS de base existe déjà"
fi

# Créer un fichier JavaScript de base pour Django
if [ ! -f "${PROJECT_DIR}/web-interface/django_backend/static/js/main.js" ]; then
    display_info "Création du fichier JavaScript de base pour Django..."
    cat > "${PROJECT_DIR}/web-interface/django_backend/static/js/main.js" << 'EOL'
// Script principal pour le NMS

document.addEventListener('DOMContentLoaded', function() {
    console.log('NMS Application chargée');
    
    // Fonction pour les notifications toast
    function showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.textContent = message;
        
        document.body.appendChild(notification);
        
        // Afficher la notification
        setTimeout(() => {
            notification.classList.add('show');
        }, 100);
        
        // Retirer la notification après 5 secondes
        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => {
                document.body.removeChild(notification);
            }, 300);
        }, 5000);
    }
    
    // Exposer la fonction de notification globalement
    window.showNotification = showNotification;
    
    // Gérer les requêtes AJAX
    function fetchData(url, options = {}) {
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            },
            credentials: 'same-origin'
        };
        
        return fetch(url, {...defaultOptions, ...options})
            .then(response => {
                if (!response.ok) {
                    throw new Error('Erreur réseau: ' + response.statusText);
                }
                return response.json();
            })
            .catch(error => {
                console.error('Erreur:', error);
                showNotification(error.message, 'error');
                throw error;
            });
    }
    
    // Exposer la fonction fetchData globalement
    window.fetchData = fetchData;
    
    // Initialiser les éléments interactifs
    const alertCloseBtns = document.querySelectorAll('.alert .close');
    alertCloseBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            const alert = this.parentElement;
            alert.style.opacity = '0';
            setTimeout(() => {
                alert.style.display = 'none';
            }, 300);
        });
    });
});
EOL
    display_success "Fichier JavaScript de base créé"
else
    display_success "Fichier JavaScript de base existe déjà"
fi

# Créer un favicon de base pour Django
if [ ! -f "${PROJECT_DIR}/web-interface/django_backend/static/img/favicon.ico" ]; then
    display_info "Création d'un favicon de base pour Django..."
    touch "${PROJECT_DIR}/web-interface/django_backend/static/img/favicon.ico"
    display_success "Favicon de base créé"
else
    display_success "Favicon de base existe déjà"
fi

display_header "Configuration des permissions des fichiers"

# Définir les permissions des dossiers de données
display_info "Configuration des permissions des dossiers de données..."
if command -v sudo &> /dev/null; then
    sudo chown -R 1000:1000 "${PROJECT_DIR}/data/elasticsearch"
    sudo chown -R 472:472 "${PROJECT_DIR}/data/grafana" "${PROJECT_DIR}/config/grafana"
    sudo chmod -R 777 "${PROJECT_DIR}/data/prometheus"
else
    chown -R 1000:1000 "${PROJECT_DIR}/data/elasticsearch"
    chown -R 472:472 "${PROJECT_DIR}/data/grafana" "${PROJECT_DIR}/config/grafana"
    chmod -R 777 "${PROJECT_DIR}/data/prometheus"
fi
display_success "Permissions configurées"

display_header "Vérification finale et instructions"

# Vérifier que toutes les configurations nécessaires sont en place
display_info "Vérification des configurations essentielles..."

missing_configs=0

check_file() {
    if [ ! -f "$1" ]; then
        display_error "Fichier manquant : $1"
        missing_configs=$((missing_configs + 1))
    fi
}

check_file "${PROJECT_DIR}/docker-compose.yml"
check_file "${PROJECT_DIR}/docker-compose.security.yml"
check_file "${PROJECT_DIR}/docker-compose.monitoring.yml"
check_file "${PROJECT_DIR}/docker-compose.traffic-control.yml"
check_file "${PROJECT_DIR}/web-interface/django_backend/Dockerfile"
check_file "${PROJECT_DIR}/web-interface/django_backend/requirements.txt"
check_file "${PROJECT_DIR}/web-interface/django_backend/manage.py"
check_file "${PROJECT_DIR}/web-interface/django_backend/nms_backend/settings.py"
check_file "${PROJECT_DIR}/web-interface/django_backend/nms_backend/urls.py"
check_file "${PROJECT_DIR}/config/elasticsearch/jvm.options"
check_file "${PROJECT_DIR}/config/elasticsearch/log4j2.properties"
check_file "${PROJECT_DIR}/config/suricata/suricata.yaml"
check_file "${PROJECT_DIR}/config/fail2ban/jail.local"
check_file "${PROJECT_DIR}/config/haproxy/haproxy.cfg"
check_file "${PROJECT_DIR}/services/traffic-control/app.py"

if [ $missing_configs -eq 0 ]; then
    display_success "Toutes les configurations essentielles sont en place"
else
    display_warning "$missing_configs fichier(s) de configuration manquant(s)"
fi

display_header "Résumé de la configuration"

echo -e "${CYAN}Architecture NMS configurée avec succès.${NC}"
echo ""
echo -e "${GREEN}Groupes de services configurés:${NC}"
echo "1. Services de base: PostgreSQL, Redis, Django, Celery"
echo "2. Services de sécurité: Elasticsearch, Kibana, Suricata, Fail2ban"
echo "3. Services de monitoring: Netdata, ntopng, HAProxy, Prometheus, Grafana"
echo "4. Service Traffic Control: API QoS"
echo ""
echo -e "${GREEN}Pour démarrer tous les services:${NC}"
echo "./nms-manager.sh start"
echo ""
echo -e "${GREEN}Pour vérifier l'état des services:${NC}"
echo "./nms-manager.sh status"
echo ""
echo -e "${GREEN}Pour accéder aux interfaces web:${NC}"
echo "- Django Admin: http://localhost:8000/admin/ (admin/admin)"
echo "- Kibana: http://localhost:5601/"
echo "- Netdata: http://localhost:19999/"
echo "- HAProxy Stats: http://localhost:1936/ (admin/admin)"
echo "- Prometheus: http://localhost:9090/"
echo "- Grafana: http://localhost:3001/ (admin/admin)"
echo "- Traffic Control API: http://localhost:5000/"
echo ""
echo -e "${YELLOW}Note importante:${NC}"
echo "Assurez-vous d'avoir un script nms-manager.sh pour gérer facilement les services."
echo "Si vous n'en avez pas encore, créez-le en vous basant sur les exemples du document."
echo ""
echo -e "${BLUE}L'architecture est prête pour le développement des fonctionnalités NMS.${NC}"
