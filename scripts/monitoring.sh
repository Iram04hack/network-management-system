#!/bin/bash

# Fonctions pour le monitoring du système NMS

# Obtenir le chemin du script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Importer les fonctions communes
source "${SCRIPT_DIR}/common.sh"

# Vérifier la santé des services
check_health() {
    title "Vérification de la santé des services NMS"
    
    local containers=$(docker ps --format "{{.Names}}" | grep "nms-")
    local total=0
    local healthy=0
    local unhealthy=0
    
    for container in $containers; do
        total=$((total+1))
        health_status=$(docker inspect --format="{{.State.Health.Status}}" $container 2>/dev/null)
        
        if [ -z "$health_status" ]; then
            echo -e "${YELLOW}[N/A]${NC} $container (pas de healthcheck configuré)"
        elif [ "$health_status" == "healthy" ]; then
            echo -e "${GREEN}[OK]${NC} $container"
            healthy=$((healthy+1))
        else
            echo -e "${RED}[ERROR]${NC} $container - Status: $health_status"
            unhealthy=$((unhealthy+1))
        fi
    done
    
    echo -e "\nRésumé: $total services, $healthy sains, $unhealthy problématiques"
    
    if [ $unhealthy -gt 0 ]; then
        warning "Certains services présentent des problèmes de santé. Vérifiez les logs pour plus de détails."
    else
        success "Tous les services semblent fonctionner correctement."
    fi
}

# Vérifier l'utilisation des ressources par les services
check_resources() {
    title "Utilisation des ressources par les services NMS"
    
    echo -e "${CYAN}UTILISATION CPU ET MÉMOIRE:${NC}"
    docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}" | grep "nms-"
}

# Vérifier les logs pour des erreurs
check_logs_for_errors() {
    title "Vérification des logs pour les erreurs"
    
    local containers=$(docker ps --format "{{.Names}}" | grep "nms-")
    local error_count=0
    
    for container in $containers; do
        local errors=$(docker logs $container --since 1h 2>&1 | grep -i "error\|exception\|fatal" | wc -l)
        
        if [ $errors -gt 0 ]; then
            error_count=$((error_count + errors))
            warning "$container: $errors erreurs trouvées dans la dernière heure"
            
            echo -e "${YELLOW}Dernières erreurs:${NC}"
            docker logs $container --since 1h 2>&1 | grep -i "error\|exception\|fatal" | tail -5
            echo ""
        else
            success "$container: Aucune erreur trouvée dans la dernière heure"
        fi
    done
    
    echo -e "\nTotal: $error_count erreurs trouvées"
}

# Vérifier l'état des connectivités entre services
check_service_connectivity() {
    title "Vérification des connectivités entre services"
    
    # Vérifier si le conteneur Django est disponible pour les tests
    if ! docker ps --filter "name=nms-django" --format "{{.Names}}" | grep -q "nms-django"; then
        error "Le conteneur nms-django n'est pas en cours d'exécution. Tests de connectivité impossible."
        return 1
    fi
    
    local services=(
        "nms-postgres:5432"
        "nms-redis:6379"
        "nms-elasticsearch:9200"
        "nms-kibana:5601"
        "nms-netdata:19999"
        "nms-ntopng:3000"
        "nms-traffic-control:8003"
    )
    
    for service in "${services[@]}"; do
        IFS=':' read -r host port <<< "$service"
        
        # Tester la connectivité TCP
        if docker exec nms-django nc -z -w 2 $host $port >/dev/null 2>&1; then
            success "Connectivité OK: $host:$port"
        else
            error "Connectivité ÉCHEC: $host:$port"
        fi
    done
}

# Vérifier la configuration HAProxy
check_haproxy_config() {
    title "Vérification de la configuration HAProxy"
    
    # Vérifier si HAProxy est en cours d'exécution
    if ! docker ps --filter "name=nms-haproxy" --format "{{.Names}}" | grep -q "nms-haproxy"; then
        error "Le conteneur nms-haproxy n'est pas en cours d'exécution."
        return 1
    fi
    
    # Vérifier le contenu de la configuration HAProxy
    info "Contenu de la configuration HAProxy:"
    docker exec nms-haproxy cat /usr/local/etc/haproxy/haproxy.cfg | grep -v "^#" | grep -v "^ *$"
    
    # Vérifier si la configuration est valide
    info "Validation de la configuration HAProxy:"
    if docker exec nms-haproxy haproxy -c -f /usr/local/etc/haproxy/haproxy.cfg; then
        success "La configuration HAProxy est valide"
    else
        error "La configuration HAProxy est invalide"
        
        # Proposer de corriger la configuration
        read -p "Voulez-vous corriger automatiquement la configuration HAProxy? (y/n): " fix_config
        if [ "$fix_config" = "y" ]; then
            fix_haproxy_config
        fi
    fi
}

# Corriger la configuration HAProxy
fix_haproxy_config() {
    info "Correction de la configuration HAProxy"
    
    # Créer une configuration HAProxy de base
    cat > /tmp/haproxy.cfg << 'EOL'
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
    timeout connect 8003
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
    server django1 nms-django:8000 check

# Backend pour Netdata
backend netdata-servers
    mode http
    option forwardfor
    http-request set-header X-Forwarded-Proto https if { ssl_fc }
    http-request set-path %[path,regsub(^/netdata/,/)]
    server netdata1 nms-netdata:19999 check

# Backend pour Kibana
backend kibana-servers
    mode http
    option forwardfor
    http-request set-header X-Forwarded-Proto https if { ssl_fc }
    http-request set-path %[path,regsub(^/kibana/,/)]
    server kibana1 nms-kibana:5601 check

# Backend pour Prometheus
backend prometheus-servers
    mode http
    option forwardfor
    http-request set-header X-Forwarded-Proto https if { ssl_fc }
    http-request set-path %[path,regsub(^/prometheus/,/)]
    server prometheus1 nms-prometheus:9090 check

# Backend pour Grafana
backend grafana-servers
    mode http
    option forwardfor
    http-request set-header X-Forwarded-Proto https if { ssl_fc }
    http-request set-path %[path,regsub(^/grafana/,/)]
    server grafana1 nms-grafana:3000 check
EOL

    # Copier la nouvelle configuration dans le conteneur
    docker cp /tmp/haproxy.cfg nms-haproxy:/usr/local/etc/haproxy/haproxy.cfg
    
    # Redémarrer HAProxy pour appliquer la nouvelle configuration
    docker_compose_command "$COMPOSE_MONITORING" "restart haproxy"
    
    # Vérifier si la correction a fonctionné
    if docker exec nms-haproxy haproxy -c -f /usr/local/etc/haproxy/haproxy.cfg; then
        success "Configuration HAProxy corrigée et service redémarré"
    else
        error "La correction de la configuration HAProxy a échoué"
    fi
    
    # Nettoyer
    rm /tmp/haproxy.cfg
}

# Générer un rapport de monitoring
generate_monitoring_report() {
    title "Génération du rapport de monitoring"
    
    local report_file="${PROJECT_DIR}/monitoring-report-$(date +%Y%m%d_%H%M%S).txt"
    
    # Rediriger la sortie vers le fichier de rapport
    {
        echo "=== RAPPORT DE MONITORING NMS ==="
        echo "Date: $(date)"
        echo ""
        
        echo "=== ÉTAT DES SERVICES ==="
        docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep "nms-"
        echo ""
        
        echo "=== UTILISATION DES RESSOURCES ==="
        docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}" | grep "nms-"
        echo ""
        
        echo "=== SANTÉ DES SERVICES ==="
        local containers=$(docker ps --format "{{.Names}}" | grep "nms-")
        for container in $containers; do
            health_status=$(docker inspect --format="{{.State.Health.Status}}" $container 2>/dev/null)
            echo "$container: ${health_status:-N/A}"
        done
        echo ""
        
        echo "=== ERREURS RÉCENTES ==="
        for container in $containers; do
            echo "--- $container ---"
            docker logs $container --since 1h 2>&1 | grep -i "error\|exception\|fatal" | tail -10 || echo "Aucune erreur trouvée"
            echo ""
        done
        
    } > "$report_file"
    
    success "Rapport de monitoring généré: $report_file"
}

# Fonction pour surveiller le trafic réseau
monitor_network_traffic() {
    title "Surveillance du trafic réseau"
    
    # Vérifier si les outils nécessaires sont installés
    if ! command -v ifstat &> /dev/null; then
        warning "L'outil ifstat n'est pas installé. Installation en cours..."
        apt-get update && apt-get install -y ifstat || error "Impossible d'installer ifstat"
    fi
    
    # Afficher le débit réseau en temps réel
    echo -e "${CYAN}Débit réseau en temps réel (CTRL+C pour quitter):${NC}"
    ifstat -i eth0 -t 1 10
    
    # Obtenir des statistiques depuis ntopng si disponible
    if docker ps --filter "name=nms-ntopng" --format "{{.Names}}" | grep -q "nms-ntopng"; then
        echo -e "\n${CYAN}Statistiques ntopng:${NC}"
        curl -s http://localhost:3000/lua/rest/v1/get/host/data.lua | jq . 2>/dev/null || echo "Impossible d'obtenir les données de ntopng"
    fi
}

# Fonction pour surveiller la qualité de service
monitor_qos() {
    title "Surveillance de la qualité de service"
    
    # Vérifier si TC est disponible
    if ! command -v tc &> /dev/null; then
        warning "L'outil tc n'est pas installé. Installation en cours..."
        apt-get update && apt-get install -y iproute2 || error "Impossible d'installer iproute2"
    fi
    
    # Afficher les statistiques QoS
    echo -e "${CYAN}Statistiques QoS:${NC}"
    tc -s qdisc show
    
    echo -e "\n${CYAN}Classes QoS:${NC}"
    tc -s class show
    
    # Obtenir des statistiques depuis le service Traffic Control si disponible
    if docker ps --filter "name=nms-traffic-control" --format "{{.Names}}" | grep -q "nms-traffic-control"; then
        echo -e "\n${CYAN}Statistiques Traffic Control:${NC}"
        curl -s http://localhost:8003/stats | jq . 2>/dev/null || echo "Impossible d'obtenir les statistiques de Traffic Control"
    fi
}

# Fonction pour surveiller la latence réseau
monitor_network_latency() {
    title "Surveillance de la latence réseau"
    
    local hosts=(
        "localhost"
        "8.8.8.8"
        "1.1.1.1"
    )
    
    # Ajouter les hôtes des services NMS
    for container in $(docker ps --filter "name=nms-" --format "{{.Names}}"); do
        local ip=$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' $container)
        if [ -n "$ip" ]; then
            hosts+=("$ip")
        fi
    done
    
    echo -e "${CYAN}Test de latence:${NC}"
    for host in "${hosts[@]}"; do
        echo -n "Ping vers $host: "
        ping -c 3 -q $host | grep "avg" || echo "Échec"
    done
}

# Fonction pour générer un rapport de performance
generate_performance_report() {
    title "Génération du rapport de performance"
    
    local report_file="${PROJECT_DIR}/performance-report-$(date +%Y%m%d_%H%M%S).txt"
    
    # Rediriger la sortie vers le fichier de rapport
    {
        echo "=== RAPPORT DE PERFORMANCE NMS ==="
        echo "Date: $(date)"
        echo ""
        
        echo "=== UTILISATION DES RESSOURCES ==="
        docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}" | grep "nms-"
        echo ""
        
        echo "=== STATISTIQUES RÉSEAU ==="
        if command -v ifstat &> /dev/null; then
            ifstat -i eth0 -t 1 5
        else
            echo "L'outil ifstat n'est pas installé."
        fi
        echo ""
        
        echo "=== QUALITÉ DE SERVICE ==="
        if command -v tc &> /dev/null; then
            tc -s qdisc show
            echo ""
            tc -s class show
        else
            echo "L'outil tc n'est pas installé."
        fi
        echo ""
        
        echo "=== LATENCE RÉSEAU ==="
        for host in "localhost" "8.8.8.8" "1.1.1.1"; do
            echo -n "Ping vers $host: "
            ping -c 3 -q $host | grep "avg" || echo "Échec"
        done
        echo ""
        
        echo "=== STATISTIQUES TRAFIC CONTROL ==="
        if docker ps --filter "name=nms-traffic-control" --format "{{.Names}}" | grep -q "nms-traffic-control"; then
            curl -s http://localhost:8003/stats || echo "Impossible d'obtenir les statistiques de Traffic Control"
        else
            echo "Le service Traffic Control n'est pas en cours d'exécution."
        fi
        echo ""
        
    } > "$report_file"
    
    success "Rapport de performance généré: $report_file"
}
