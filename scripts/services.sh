#!/bin/bash

# Fonctions pour gérer les services Docker

# Obtenir le chemin du script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Importer les fonctions communes
source "${SCRIPT_DIR}/common.sh"

# Démarrer tous les services
start_all_services() {
    title "Démarrage de tous les services NMS"
    
    # Démarrer les services de base
    info "Démarrage des services de base..."
    docker_compose_command "$COMPOSE_MAIN" "up -d"
    
    # S'assurer que Django utilise Uvicorn pour ASGI
    info "Configuration de Django pour utiliser Uvicorn..."
    docker exec nms-django bash -c "if ps aux | grep -q '[p]ython manage.py runserver'; then pkill -f 'python manage.py runserver' && uvicorn nms_backend.asgi:application --host 0.0.0.0 --port 8000 --workers 4 --log-level info & fi" || warning "Impossible de configurer Uvicorn (conteneur peut-être pas démarré)"
    
    # Configurer HTTPS pour Django
    info "Configuration de HTTPS pour Django..."
    configure_https_for_django
    
    # Démarrer les services de sécurité
    info "Démarrage des services de sécurité..."
    docker_compose_command "$COMPOSE_SECURITY" "up -d"
    
    # Démarrer les services de monitoring
    info "Démarrage des services de monitoring..."
    docker_compose_command "$COMPOSE_MONITORING" "up -d"
    
    # Démarrer le service Traffic Control
    info "Démarrage du service Traffic Control..."
    docker_compose_command "$COMPOSE_TRAFFIC" "up -d"
    
    success "Services NMS démarrés avec succès."
    
    # Vérifier les services
    verify_services_started
    
    # Afficher les URLs des services
    show_service_urls
}

# Démarrer un groupe de services spécifique
start_services() {
    local service_type="$1"
    
    case "$service_type" in
        base)
            title "Démarrage des services de base"
            docker_compose_command "$COMPOSE_MAIN" "up -d"
            
            # S'assurer que Django utilise Uvicorn pour ASGI
            info "Configuration de Django pour utiliser Uvicorn..."
            docker exec nms-django bash -c "if ps aux | grep -q '[p]ython manage.py runserver'; then pkill -f 'python manage.py runserver' && uvicorn nms_backend.asgi:application --host 0.0.0.0 --port 8000 --workers 4 --log-level info & fi" || warning "Impossible de configurer Uvicorn dans le conteneur Django (peut-être qu'il n'est pas encore démarré)"
            
            # Configurer HTTPS pour Django automatiquement
            info "Configuration de HTTPS pour Django..."
            configure_https_for_django
            ;;
        security)
            title "Démarrage des services de sécurité"
            docker_compose_command "$COMPOSE_SECURITY" "up -d"
            ;;
        monitoring)
            title "Démarrage des services de monitoring"
            docker_compose_command "$COMPOSE_MONITORING" "up -d"
            ;;
        traffic)
            title "Démarrage du service Traffic Control"
            docker_compose_command "$COMPOSE_TRAFFIC" "up -d"
            ;;
        *)
            error "Type de service inconnu: $service_type"
            return 1
            ;;
    esac
    
    success "Services $service_type démarrés avec succès."
}

# Arrêter tous les services
stop_all_services() {
    title "Arrêt de tous les services NMS"
    
    # Arrêter les services Traffic Control
    info "Arrêt du service Traffic Control..."
    docker_compose_command "$COMPOSE_TRAFFIC" "down"
    
    # Arrêter les services de monitoring
    info "Arrêt des services de monitoring..."
    docker_compose_command "$COMPOSE_MONITORING" "down"
    
    # Arrêter les services de sécurité
    info "Arrêt des services de sécurité..."
    docker_compose_command "$COMPOSE_SECURITY" "down"
    
    # Arrêter les services de base
    info "Arrêt des services de base..."
    docker_compose_command "$COMPOSE_MAIN" "down"
    
    success "Tous les services NMS ont été arrêtés."
}

# Arrêter un groupe de services spécifique
stop_services() {
    local service_type="$1"
    
    case "$service_type" in
        base)
            title "Arrêt des services de base"
            docker_compose_command "$COMPOSE_MAIN" "down"
            ;;
        security)
            title "Arrêt des services de sécurité"
            docker_compose_command "$COMPOSE_SECURITY" "down"
            ;;
        monitoring)
            title "Arrêt des services de monitoring"
            docker_compose_command "$COMPOSE_MONITORING" "down"
            ;;
        traffic)
            title "Arrêt du service Traffic Control"
            docker_compose_command "$COMPOSE_TRAFFIC" "down"
            ;;
        *)
            error "Type de service inconnu: $service_type"
            return 1
            ;;
    esac
    
    success "Services $service_type arrêtés avec succès."
}

# Redémarrer tous les services
restart_all_services() {
    title "Redémarrage de tous les services NMS"
    
    stop_all_services
    start_all_services
    
    success "Tous les services ont été redémarrés."
}

# Vérifier que les services sont correctement démarrés
verify_services_started() {
    title "Vérification des services lancés"
    
    # Donner un peu de temps aux services pour démarrer
    info "Attente de 10 secondes pour laisser les services démarrer..."
    sleep 10
    
    # Liste des conteneurs essentiels
    essential_containers=("nms-django" "nms-postgres" "nms-redis" "nms-elasticsearch" "nms-kibana" "nms-netdata" "nms-suricata")
    
    echo "Vérification des conteneurs essentiels..."
    for container in "${essential_containers[@]}"; do
        status=$(docker ps --filter "name=$container" --format "{{.Status}}")
        if [ -z "$status" ]; then
            error "Le conteneur $container n'est pas en cours d'exécution!"
            echo "Vous pouvez consulter les logs avec: docker logs $container"
        else
            success "Le conteneur $container est en cours d'exécution: $status"
        fi
    done
}

# Afficher l'état de tous les services
show_services_status() {
    title "État des services NMS"
    
    echo -e "${CYAN}SERVICES DE BASE:${NC}"
    docker_compose_command "$COMPOSE_MAIN" "ps"
    
    echo -e "\n${CYAN}SERVICES DE SÉCURITÉ:${NC}"
    docker_compose_command "$COMPOSE_SECURITY" "ps"
    
    echo -e "\n${CYAN}SERVICES DE MONITORING:${NC}"
    docker_compose_command "$COMPOSE_MONITORING" "ps"
    
    echo -e "\n${CYAN}SERVICE TRAFFIC CONTROL:${NC}"
    docker_compose_command "$COMPOSE_TRAFFIC" "ps"
    
    echo -e "\n${CYAN}TOUS LES CONTENEURS NMS:${NC}"
    docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep "nms-"
}

# Afficher les logs
show_logs() {
    local service="$1"
    local follow="$2"
    local lines="${3:-100}"
    
    if [ -z "$service" ]; then
        title "Logs de tous les services NMS"
        
        if [ "$follow" == "follow" ]; then
            docker_compose_command "$COMPOSE_MAIN" "logs --tail=$lines -f"
        else
            docker_compose_command "$COMPOSE_MAIN" "logs --tail=$lines"
        fi
    else
        title "Logs du service: $service"
        
        # Vérifier le préfixe et ajouter nms- si nécessaire
        if [[ ! "$service" == nms-* ]]; then
            service="nms-$service"
        fi
        
        # Vérifier que le conteneur existe
        if ! docker ps -a --format "{{.Names}}" | grep -q "^$service$"; then
            error "Le service $service n'existe pas ou n'est pas en cours d'exécution."
            return 1
        fi
        
        if [ "$follow" == "follow" ]; then
            docker logs --tail=$lines -f $service
        else
            docker logs --tail=$lines $service
        fi
    fi
}

# Afficher les URLs des services
show_service_urls() {
    echo ""
    echo -e "${CYAN}Interfaces web disponibles:${NC}"
    echo -e "Django Admin:        ${YELLOW}https://localhost:8000/admin/${NC}"
    echo -e "Django API:          ${YELLOW}https://localhost:8000/api/${NC}"
    echo -e "API Documentation:   ${YELLOW}https://localhost:8000/api/swagger/${NC}"
    echo -e "API Documentation:   ${YELLOW}https://localhost:8000/api/redoc/${NC}"
    echo -e "Kibana:              ${YELLOW}http://localhost:5601/${NC}"
    echo -e "Netdata:             ${YELLOW}http://localhost:19999/${NC}"
    echo -e "ntopng:              ${YELLOW}http://localhost:3000/${NC}"
    echo -e "HAProxy Stats:       ${YELLOW}http://localhost:1936/${NC} (admin:admin)"
    echo -e "HAProxy HTTP:        ${YELLOW}http://localhost:8080/${NC}"
    echo -e "HAProxy HTTPS:       ${YELLOW}https://localhost:8443/${NC}"
    echo -e "Traffic Control API: ${YELLOW}http://localhost:8003/${NC}"
    echo -e "Prometheus:          ${YELLOW}http://localhost:9090/${NC}"
    echo -e "Grafana:             ${YELLOW}http://localhost:3001/${NC} (admin:admin)"
    echo -e "${YELLOW}NOTE: Le certificat SSL pour HTTPS est auto-signé, vous devrez accepter l'avertissement de sécurité dans votre navigateur.${NC}"
}

# Vérifier et redémarrer les services arrêtés
check_and_restart_services() {
    title "Vérification et redémarrage des services arrêtés"
    
    # Liste des services essentiels
    declare -A service_compose_files
    service_compose_files["nms-django"]="$COMPOSE_MAIN"
    service_compose_files["nms-postgres"]="$COMPOSE_MAIN"
    service_compose_files["nms-redis"]="$COMPOSE_MAIN"
    service_compose_files["nms-celery"]="$COMPOSE_MAIN"
    service_compose_files["nms-elasticsearch"]="$COMPOSE_SECURITY"
    service_compose_files["nms-kibana"]="$COMPOSE_SECURITY"
    service_compose_files["nms-suricata"]="$COMPOSE_SECURITY"
    service_compose_files["nms-fail2ban"]="$COMPOSE_SECURITY"
    service_compose_files["nms-netdata"]="$COMPOSE_MONITORING"
    service_compose_files["nms-ntopng"]="$COMPOSE_MONITORING"
    service_compose_files["nms-haproxy"]="$COMPOSE_MONITORING"
    service_compose_files["nms-prometheus"]="$COMPOSE_MONITORING"
    service_compose_files["nms-grafana"]="$COMPOSE_MONITORING"
    service_compose_files["nms-traffic-control"]="$COMPOSE_TRAFFIC"
    
    # Vérifier chaque service
    for service in "${!service_compose_files[@]}"; do
        service_name=$(echo $service | sed 's/nms-//g')
        compose_file="${service_compose_files[$service]}"
        
        # Vérifier si le service est en cours d'exécution
        status=$(docker ps --filter "name=$service" --format "{{.Status}}")
        
        if [ -z "$status" ]; then
            warning "Le service $service n'est pas en cours d'exécution. Tentative de redémarrage..."
            
            # Si c'est le service Django, corriger les permissions avant de redémarrer
            if [ "$service" = "nms-django" ]; then
                fix_permissions
            fi
            
            # Redémarrer le service
            if [ -f "$compose_file" ]; then
                info "Redémarrage de $service_name avec $compose_file"
                docker_compose_command "$compose_file" "up -d --force-recreate" "$service_name"
                
                # Vérifier si le redémarrage a réussi
                sleep 5
                new_status=$(docker ps --filter "name=$service" --format "{{.Status}}")
                if [ -z "$new_status" ]; then
                    error "Échec du redémarrage de $service"
                    docker_compose_command "$compose_file" "logs" "$service_name" "--tail 20"
                else
                    success "Redémarrage réussi de $service: $new_status"
                    
                    # S'assurer que Django utilise Uvicorn après un redémarrage
                    if [ "$service" = "nms-django" ]; then
                        info "Configuration de Django pour utiliser Uvicorn après redémarrage..."
                        docker exec nms-django bash -c "if ps aux | grep -q '[p]ython manage.py runserver'; then pkill -f 'python manage.py runserver' && uvicorn nms_backend.asgi:application --host 0.0.0.0 --port 8000 --workers 4 --log-level info & fi" || warning "Impossible de configurer Uvicorn"
                    fi
                fi
            else
                error "Fichier docker-compose non trouvé pour $service: $compose_file"
            fi
        else
            success "$service est en cours d'exécution: $status"
        fi
    done
}

# Lancer Django avec un serveur spécifique
start_django_with_server() {
    local server_type="${1:-uvicorn}"
    local use_https="${2:-false}"
    
    title "Démarrage de Django avec $server_type"
    
    if ! docker ps --filter "name=nms-django" --format "{{.Names}}" | grep -q "nms-django"; then
        error "Le conteneur nms-django n'est pas en cours d'exécution."
        return 1
    fi
    
    # Arrêter tout serveur existant
    info "Arrêt des serveurs existants..."
    docker exec nms-django bash -c "pkill -f 'python manage.py runserver' || true; pkill -f 'daphne' || true; pkill -f 'uvicorn' || true"
    
    case "$server_type" in
        uvicorn)
            info "Démarrage d'Uvicorn..."
            docker exec -d nms-django bash -c "uvicorn nms_backend.asgi:application --host 0.0.0.0 --port 8000 --workers 4 --log-level info"
            ;;
        daphne)
            info "Démarrage de Daphne..."
            docker exec -d nms-django bash -c "daphne -b 0.0.0.0 -p 8000 nms_backend.asgi:application"
            ;;
        runserver)
            info "Démarrage du serveur de développement Django..."
            docker exec -d nms-django bash -c "python manage.py runserver 0.0.0.0:8000"
            ;;
        *)
            error "Type de serveur inconnu: $server_type"
            echo "Types disponibles: uvicorn, daphne, runserver"
            return 1
            ;;
    esac
    
    success "Django démarré avec $server_type"
    
    # Configurer HTTPS si demandé
    if [ "$use_https" = "true" ]; then
        configure_https_for_django
    fi
}

# Fonction pour configurer HTTPS pour Django
configure_https_for_django() {
    title "Configuration HTTPS pour Django"
    
    # Chemin vers les fichiers de configuration
    local NGINX_CONFIG_DIR="${PROJECT_DIR}/config/nginx"
    
    # Définir le chemin complet du projet si pas déjà fait
    if [ -z "$PROJECT_DIR" ]; then
        PROJECT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." &> /dev/null && pwd )"
        NGINX_CONFIG_DIR="${PROJECT_DIR}/config/nginx"
    fi
    
    # Vérifier si les scripts nécessaires existent
    if [ ! -f "${NGINX_CONFIG_DIR}/generate_ssl_certs.sh" ]; then
        error "Le script de génération de certificats SSL n'a pas été trouvé: ${NGINX_CONFIG_DIR}/generate_ssl_certs.sh"
        warning "Création du script de génération de certificats automatiquement..."
        
        # Créer le répertoire config/nginx s'il n'existe pas
        mkdir -p "${NGINX_CONFIG_DIR}"
        
        # Créer le script de génération de certificats
        cat > "${NGINX_CONFIG_DIR}/generate_ssl_certs.sh" << 'EOF'
#!/bin/bash

# Script pour générer des certificats SSL auto-signés pour le développement

# Répertoire de sortie pour les certificats
CERT_DIR="/etc/ssl/certs"
KEY_DIR="/etc/ssl/private"

# Créer les répertoires si nécessaire
sudo mkdir -p $CERT_DIR
sudo mkdir -p $KEY_DIR

# Générer une clé privée
echo "Génération de la clé privée..."
sudo openssl genrsa -out $KEY_DIR/nms-key.pem 2048

# Générer un certificat auto-signé
echo "Génération du certificat auto-signé..."
sudo openssl req -x509 -new -nodes -key $KEY_DIR/nms-key.pem \
    -sha256 -days 365 -out $CERT_DIR/nms-cert.pem \
    -subj "/C=FR/ST=Paris/L=Paris/O=NMS/OU=Development/CN=localhost"

# Vérifier que les fichiers ont été créés
if [ -f "$CERT_DIR/nms-cert.pem" ] && [ -f "$KEY_DIR/nms-key.pem" ]; then
    echo "Certificats générés avec succès:"
    echo "Certificat: $CERT_DIR/nms-cert.pem"
    echo "Clé privée: $KEY_DIR/nms-key.pem"
    
    # Définir les permissions appropriées
    sudo chmod 644 $CERT_DIR/nms-cert.pem
    sudo chmod 600 $KEY_DIR/nms-key.pem
else
    echo "Erreur lors de la génération des certificats."
    exit 1
fi

echo "Vous pouvez maintenant configurer Nginx pour utiliser ces certificats."
echo "IMPORTANT: Ce certificat est auto-signé et destiné uniquement au développement."
EOF
        chmod +x "${NGINX_CONFIG_DIR}/generate_ssl_certs.sh"
        success "Script de génération de certificats créé avec succès."
    fi
    
    # Vérifier si le fichier de configuration Nginx existe
    if [ ! -f "${NGINX_CONFIG_DIR}/site.conf" ]; then
        error "Le fichier de configuration Nginx n'a pas été trouvé: ${NGINX_CONFIG_DIR}/site.conf"
        warning "Création du fichier de configuration Nginx automatiquement..."
        
        # Détecter le port Django
        DJANGO_PORT=8000
        if lsof -i:8000 -t &> /dev/null && ! lsof -i:8001 -t &> /dev/null; then
            DJANGO_PORT=8001
        elif lsof -i:8000 -t &> /dev/null && lsof -i:8001 -t &> /dev/null; then
            # Vérifier quel port est utilisé par Django
            if ps aux | grep "runserver.*8000" | grep -v grep > /dev/null || ps aux | grep "uvicorn.*--port 8000" | grep -v grep > /dev/null; then
                DJANGO_PORT=8000
            else
                DJANGO_PORT=8001
            fi
        fi
        
        # Créer le fichier de configuration Nginx
        cat > "${NGINX_CONFIG_DIR}/site.conf" << EOF
worker_processes 1;

events {
    worker_connections 1024;
}

http {
    include       /etc/nginx/mime.types;
    default_type  application/octet-stream;

    sendfile        on;
    keepalive_timeout  65;
    client_max_body_size 20M;

    # Compression
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;

    # Configuration SSL
    server {
        listen 80;
        server_name localhost;
        
        # Rediriger HTTP vers HTTPS
        return 301 https://\$host\$request_uri;
    }

    server {
        listen 443 ssl;
        server_name localhost;

        # Certificats SSL
        ssl_certificate     /etc/ssl/certs/nms-cert.pem;
        ssl_certificate_key /etc/ssl/private/nms-key.pem;

        # Paramètres de sécurité SSL
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_prefer_server_ciphers on;
        ssl_ciphers 'ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305';
        ssl_session_cache shared:SSL:10m;
        ssl_session_timeout 10m;
        add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

        # Fichiers statiques
        location /static/ {
            alias ${PROJECT_DIR}/web-interface/django__backend/staticfiles/;
            expires 30d;
            add_header Cache-Control "public, max-age=2592000";
        }

        location /media/ {
            alias ${PROJECT_DIR}/web-interface/django__backend/media/;
            expires 30d;
            add_header Cache-Control "public, max-age=2592000";
        }

        # Proxy pour le backend Django
        location / {
            proxy_pass http://localhost:${DJANGO_PORT};
            proxy_set_header Host \$host;
            proxy_set_header X-Real-IP \$remote_addr;
            proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto https;
            proxy_redirect off;
            
            # WebSocket support
            proxy_http_version 1.1;
            proxy_set_header Upgrade \$http_upgrade;
            proxy_set_header Connection "upgrade";
        }

        # Proxy pour les WebSockets
        location /ws/ {
            proxy_pass http://localhost:${DJANGO_PORT};
            proxy_http_version 1.1;
            proxy_set_header Upgrade \$http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_set_header Host \$host;
            proxy_set_header X-Real-IP \$remote_addr;
            proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto https;
        }
    }
}
EOF
        success "Fichier de configuration Nginx créé avec succès pour le port Django ${DJANGO_PORT}."
    else
        # Mise à jour du port Django dans la configuration existante si nécessaire
        DJANGO_PORT=8000
        if lsof -i:8000 -t &> /dev/null && ! lsof -i:8001 -t &> /dev/null; then
            DJANGO_PORT=8001
        elif lsof -i:8000 -t &> /dev/null && lsof -i:8001 -t &> /dev/null; then
            # Vérifier quel port est utilisé par Django
            if ps aux | grep "runserver.*8000" | grep -v grep > /dev/null || ps aux | grep "uvicorn.*--port 8000" | grep -v grep > /dev/null; then
                DJANGO_PORT=8000
            else
                DJANGO_PORT=8001
            fi
        fi
        
        # Vérifier si le port configuré est différent
        CONFIGURED_PORT=$(grep -o "proxy_pass http://localhost:[0-9]\+" "${NGINX_CONFIG_DIR}/site.conf" | head -1 | cut -d: -f3)
        if [ "$CONFIGURED_PORT" != "$DJANGO_PORT" ]; then
            info "Mise à jour du port Django dans la configuration Nginx: $CONFIGURED_PORT -> $DJANGO_PORT"
            sed -i "s/proxy_pass http:\/\/localhost:$CONFIGURED_PORT/proxy_pass http:\/\/localhost:$DJANGO_PORT/g" "${NGINX_CONFIG_DIR}/site.conf"
        fi
    fi
    
    # Vérifier et installer Nginx si nécessaire
    info "Vérification de Nginx et OpenSSL..."
    if ! command -v nginx &> /dev/null; then
        warning "Nginx n'est pas installé. Installation en cours..."
        sudo apt-get update && sudo apt-get install -y nginx
        if [ $? -ne 0 ]; then
            error "Impossible d'installer Nginx. Veuillez l'installer manuellement avec: sudo apt-get install -y nginx"
            return 1
        fi
    fi
    
    if ! command -v openssl &> /dev/null; then
        warning "OpenSSL n'est pas installé. Installation en cours..."
        sudo apt-get update && sudo apt-get install -y openssl
        if [ $? -ne 0 ]; then
            error "Impossible d'installer OpenSSL. Veuillez l'installer manuellement avec: sudo apt-get install -y openssl"
            return 1
        fi
    fi
    
    # Vérifier si les certificats SSL existent, sinon les générer
    if [ ! -f "/etc/ssl/certs/nms-cert.pem" ] || [ ! -f "/etc/ssl/private/nms-key.pem" ]; then
        info "Certificats SSL non trouvés. Génération des certificats..."
        sudo "${NGINX_CONFIG_DIR}/generate_ssl_certs.sh"
        if [ $? -ne 0 ]; then
            error "Échec de la génération des certificats SSL. Vérifiez les erreurs et réessayez."
            return 1
        fi
    else
        info "Certificats SSL trouvés."
    fi
    
    # Arrêter correctement les instances Nginx existantes
    info "Vérification des instances Nginx existantes..."
    if pgrep -x "nginx" > /dev/null; then
        info "Nginx est en cours d'exécution. Arrêt en cours..."
        sudo systemctl stop nginx 2>/dev/null || true
        sleep 1
        
        if pgrep -x "nginx" > /dev/null; then
            info "Tentative d'arrêt avec nginx -s stop..."
            sudo nginx -s stop 2>/dev/null || true
            sleep 2
            
            # Si Nginx est toujours en cours d'exécution, le tuer avec force
            if pgrep -x "nginx" > /dev/null; then
                warning "Nginx est toujours en cours d'exécution. Arrêt forcé..."
                sudo pkill -9 -x nginx 2>/dev/null || true
                sleep 2
                
                # Vérifier une dernière fois
                if pgrep -x "nginx" > /dev/null; then
                    error "Impossible d'arrêter Nginx. Vous devrez peut-être le faire manuellement avec: sudo pkill -9 nginx"
                    error "Processus Nginx restants:"
                    ps aux | grep nginx | grep -v grep
                    return 1
                fi
            fi
        fi
    fi
    
    # Vérifier si les ports 80 et 443 sont disponibles pour HAProxy
    info "Vérification de la disponibilité des ports pour HAProxy..."
    
    if sudo lsof -i :80 | grep LISTEN > /dev/null; then
        warning "Le port 80 est déjà utilisé par un autre processus (probablement Nginx)."
        warning "HAProxy utilisera les ports alternatifs 8080 (HTTP) et 8443 (HTTPS)."
        info "Configuration alternative activée pour éviter les conflits."
        
        # Modifier la configuration HAProxy pour utiliser des ports alternatifs
        export HAPROXY_HTTP_PORT=8080
        export HAPROXY_HTTPS_PORT=8443
    else
        export HAPROXY_HTTP_PORT=80
        export HAPROXY_HTTPS_PORT=443
    fi
    
    # Démarrer Nginx avec notre configuration
    info "Démarrage de Nginx avec la configuration SSL..."
    sudo nginx -c "${NGINX_CONFIG_DIR}/site.conf"
    
    # Vérifier que Nginx a démarré correctement
    if [ $? -eq 0 ]; then
        # Attendre un peu pour que Nginx démarre complètement
        sleep 2
        
        # Vérifier que Nginx est bien en écoute
        if sudo lsof -i :80 -i :443 | grep nginx | grep LISTEN > /dev/null; then
            success "Nginx démarré avec succès et écoute sur les ports 80 et 443."
        else
            error "Nginx ne semble pas écouter sur les ports 80 et 443. Vérifiez la configuration."
            sudo nginx -t -c "${NGINX_CONFIG_DIR}/site.conf"
            return 1
        fi
        
        echo -e "\n${CYAN}URLs importantes:${NC}"
        echo -e "Interface d'administration:  ${YELLOW}https://localhost/admin/${NC}"
        echo -e "API REST:                    ${YELLOW}https://localhost/api/${NC}"
        echo -e "Documentation API (Swagger): ${YELLOW}https://localhost/api/swagger/${NC}"
        echo -e "Documentation API (ReDoc):   ${YELLOW}https://localhost/api/redoc/${NC}"
        echo -e "${YELLOW}NOTE: Le certificat est auto-signé, vous devrez accepter l'avertissement de sécurité dans votre navigateur.${NC}"
        
        # Vérification de l'accès
        info "Test d'accès à l'API Django..."
        if command -v curl &> /dev/null; then
            sleep 2  # Attendre que le serveur soit prêt
            HTTP_CODE=$(curl -k -s -o /dev/null -w "%{http_code}" https://localhost/api/)
            if [[ "$HTTP_CODE" =~ ^(200|301|302)$ ]]; then
                success "L'API Django est accessible via HTTPS. Code HTTP: $HTTP_CODE"
            else
                warning "L'API Django n'est pas immédiatement accessible via HTTPS (Code HTTP: $HTTP_CODE). Elle devrait être disponible dans quelques instants."
            fi
        fi
        
        return 0
    else
        error "Erreur lors du démarrage de Nginx. Vérifiez la configuration."
        sudo nginx -t -c "${NGINX_CONFIG_DIR}/site.conf"
        warning "Vous pouvez également vérifier les journaux d'erreur avec: sudo tail -f /var/log/nginx/error.log"
        return 1
    fi
}

# Fonction pour démarrer un service spécifique
start_service() {
    local service="$1"
    local use_https="true"  # Toujours activer HTTPS par défaut
    
    title "Démarrage du service: $service"
    
    # Si c'est Django, vérifier s'il y a déjà des instances en cours
    if [ "$service" = "django" ]; then
        info "Vérification des instances Django existantes..."
        
        # Arrêter toutes les instances Django en cours d'exécution
        if ps aux | grep -E "python.*runserver|uvicorn.*asgi" | grep -v grep > /dev/null; then
            warning "Des instances Django sont déjà en cours d'exécution. Arrêt en cours..."
            
            # Arrêter les instances runserver
            sudo pkill -f "python.*runserver" || true
            
            # Arrêter les instances Uvicorn
            sudo pkill -f "uvicorn.*asgi" || true
            
            # Attendre que les processus se terminent
            sleep 2
        fi
    fi
    
    # Vérifier si le service est déjà en cours d'exécution
    if docker ps --filter "name=nms-$service" --format "{{.Names}}" | grep -q "nms-$service"; then
        warning "Le service $service est déjà en cours d'exécution."
        
        # Si c'est Django, configurer HTTPS même si déjà en cours d'exécution
        if [ "$service" = "django" ]; then
            info "Configuration HTTPS pour Django en cours d'exécution..."
            configure_https_for_django
        fi
        
        return 0
    fi
    
    # Déterminer le fichier compose et le service Docker
    local compose_file=""
    local docker_service=""
    
    case "$service" in
        django|postgres|redis|celery)
            compose_file="$COMPOSE_MAIN"
            docker_service="$service"
            ;;
        elasticsearch|kibana|suricata|fail2ban)
            compose_file="$COMPOSE_SECURITY"
            docker_service="$service"
            ;;
        netdata|ntopng|haproxy|prometheus|grafana)
            compose_file="$COMPOSE_MONITORING"
            docker_service="$service"
            ;;
        traffic-control)
            compose_file="$COMPOSE_TRAFFIC"
            docker_service="traffic-control"
            ;;
        *)
            error "Service inconnu: $service"
            return 1
            ;;
    esac
    
    # Démarrer le service
    info "Démarrage du service $service avec $compose_file"
    docker_compose_command "$compose_file" "up -d" "$docker_service"
    
    # Vérifier si le démarrage a réussi
    if docker ps --filter "name=nms-$service" --format "{{.Names}}" | grep -q "nms-$service"; then
        success "Le service $service a été démarré avec succès."
        
        # Actions post-démarrage spécifiques au service
        if [ "$service" = "django" ]; then
            # Arrêter toutes les instances en cours au cas où
            docker exec nms-django bash -c "pkill -f 'python manage.py runserver' || true; pkill -f 'uvicorn' || true"
            sleep 1
            
            # Démarrer Uvicorn
            info "Configuration de Django pour utiliser Uvicorn..."
            docker exec -d nms-django bash -c "uvicorn nms_backend.asgi:application --host 0.0.0.0 --port 8000 --workers 4 --log-level info"
            
            # Vérifier que Uvicorn a bien démarré
            sleep 2
            if ! docker exec nms-django bash -c "ps aux | grep -q '[u]vicorn.*asgi'"; then
                warning "Uvicorn ne semble pas avoir démarré. Tentative de démarrage avec runserver..."
                docker exec -d nms-django bash -c "python manage.py runserver 0.0.0.0:8000"
            fi
            
            # Configurer HTTPS automatiquement pour Django
            info "Configuration de HTTPS pour Django..."
            configure_https_for_django
        fi
        
        return 0
    else
        error "Échec du démarrage du service $service."
        return 1
    fi
}

# Fonction pour arrêter un service spécifique
stop_service() {
    local service="$1"
    
    title "Arrêt du service: $service"
    
    # Cas spécial pour nginx (service système)
    if [ "$service" = "nginx" ]; then
        if pgrep -x "nginx" > /dev/null; then
            info "Arrêt du service système Nginx..."
            sudo systemctl stop nginx 2>/dev/null || true
            sleep 1
            
            if pgrep -x "nginx" > /dev/null; then
                info "Tentative d'arrêt avec nginx -s stop..."
                sudo nginx -s stop 2>/dev/null || true
                sleep 2
                
                # Si Nginx est toujours en cours d'exécution, le tuer avec force
                if pgrep -x "nginx" > /dev/null; then
                    warning "Nginx est toujours en cours d'exécution. Arrêt forcé..."
                    sudo pkill -9 -x nginx 2>/dev/null || true
                    sleep 2
                    
                    # Vérifier une dernière fois
                    if pgrep -x "nginx" > /dev/null; then
                        error "Impossible d'arrêter Nginx. Vous devrez peut-être le faire manuellement avec: sudo pkill -9 nginx"
                        error "Processus Nginx restants:"
                        ps aux | grep nginx | grep -v grep
                        return 1
                    fi
                fi
            fi
            
            success "Le service Nginx a été arrêté avec succès."
            return 0
        else
            warning "Le service $service n'est pas en cours d'exécution."
            return 0
        fi
    fi
    
    # Vérifier si le service est en cours d'exécution (pour les services Docker)
    if ! docker ps --filter "name=nms-$service" --format "{{.Names}}" | grep -q "nms-$service"; then
        warning "Le service $service n'est pas en cours d'exécution."
        return 0
    fi
    
    # Déterminer le fichier compose et le service Docker
    local compose_file=""
    local docker_service=""
    
    case "$service" in
        django|postgres|redis|celery)
            compose_file="$COMPOSE_MAIN"
            docker_service="$service"
            ;;
        elasticsearch|kibana|suricata|fail2ban)
            compose_file="$COMPOSE_SECURITY"
            docker_service="$service"
            ;;
        netdata|ntopng|haproxy|prometheus|grafana)
            compose_file="$COMPOSE_MONITORING"
            docker_service="$service"
            ;;
        traffic-control)
            compose_file="$COMPOSE_TRAFFIC"
            docker_service="traffic-control"
            ;;
        *)
            error "Service inconnu: $service"
            return 1
            ;;
    esac
    
    # Arrêter le service
    info "Arrêt du service $service avec $compose_file"
    docker_compose_command "$compose_file" "stop" "$docker_service"
    
    # Vérifier si l'arrêt a réussi
    if ! docker ps --filter "name=nms-$service" --format "{{.Names}}" | grep -q "nms-$service"; then
        success "Le service $service a été arrêté avec succès."
        return 0
    else
        error "Échec de l'arrêt du service $service."
        return 1
    fi
}

# Fonction pour redémarrer un service spécifique
restart_service() {
    local service="$1"
    
    title "Redémarrage du service: $service"
    
    stop_service "$service"
    start_service "$service"
}

# Fonction pour afficher l'état d'un service spécifique
show_service_status() {
    local service="$1"
    
    title "État du service: $service"
    
    # Vérifier si le service est en cours d'exécution
    local status=$(docker ps --filter "name=nms-$service" --format "{{.Status}}")
    
    if [ -z "$status" ]; then
        echo -e "${RED}[ARRÊTÉ]${NC} $service n'est pas en cours d'exécution."
    else
        echo -e "${GREEN}[EN COURS]${NC} $service: $status"
        
        # Afficher des informations supplémentaires spécifiques au service
        case "$service" in
            django)
                echo -e "\n${CYAN}Processus Django:${NC}"
                docker exec nms-django ps aux | grep -E 'python|uvicorn|daphne' | grep -v grep
                
                echo -e "\n${CYAN}URL Django:${NC}"
                echo -e "Admin:             ${YELLOW}https://localhost/admin/${NC}"
                echo -e "API:               ${YELLOW}https://localhost/api/${NC}"
                echo -e "API Documentation: ${YELLOW}https://localhost/api/swagger/${NC}"
                echo -e "API Documentation: ${YELLOW}https://localhost/api/redoc/${NC}"
                echo -e "${YELLOW}NOTE: Le certificat SSL est auto-signé, vous devrez accepter l'avertissement de sécurité.${NC}"
                ;;
            postgres)
                echo -e "\n${CYAN}Bases de données PostgreSQL:${NC}"
                docker exec nms-postgres psql -U nms_user -l 2>/dev/null || echo "Impossible de se connecter à PostgreSQL"
                ;;
            elasticsearch)
                echo -e "\n${CYAN}État Elasticsearch:${NC}"
                curl -s http://localhost:9200/_cluster/health | grep -v "^$" || echo "Impossible de se connecter à Elasticsearch"
                ;;
            kibana)
                echo -e "\n${CYAN}URL Kibana:${NC}"
                echo "http://localhost:5601/"
                ;;
            suricata)
                echo -e "\n${CYAN}État Suricata:${NC}"
                docker exec nms-suricata suricatasc -c uptime 2>/dev/null || echo "Impossible de se connecter à Suricata"
                ;;
            netdata)
                echo -e "\n${CYAN}URL Netdata:${NC}"
                echo "http://localhost:19999/"
                ;;
            prometheus)
                echo -e "\n${CYAN}URL Prometheus:${NC}"
                echo "http://localhost:9090/"
                ;;
            grafana)
                echo -e "\n${CYAN}URL Grafana:${NC}"
                echo "http://localhost:3001/"
                ;;
            traffic-control)
                echo -e "\n${CYAN}URL Traffic Control:${NC}"
                echo "http://localhost:8003/"
                
                echo -e "\n${CYAN}Règles TC actives:${NC}"
                if docker exec nms-traffic-control tc -s qdisc show 2>/dev/null; then
                    true
                else
                    echo "Impossible de récupérer les règles TC"
                fi
                ;;
        esac
    fi
}

# Fonction pour démarrer Django en mode non-conteneurisé
start_standalone_django() {
    title "Démarrage de Django en mode standalone"
    
    # Définir le chemin du backend Django
    local BACKEND_DIR="${PROJECT_DIR}/web-interface/django__backend"

    # Définir le chemin complet du projet si pas déjà fait
    if [ -z "$PROJECT_DIR" ]; then
        PROJECT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." &> /dev/null && pwd )"
        BACKEND_DIR="${PROJECT_DIR}/web-interface/django__backend"
    fi
    
    # Arrêter toutes les instances Django en cours d'exécution
    info "Vérification des instances Django existantes..."
    local django_instances=$(ps aux | grep -E "python.*runserver|uvicorn.*asgi" | grep -v grep)
    if [ ! -z "$django_instances" ]; then
        warning "Des instances Django sont déjà en cours d'exécution. Arrêt en cours..."
        
        # Afficher les instances en cours
        echo "$django_instances"
        
        # Arrêter les instances une par une
        ps aux | grep -E "python.*runserver|uvicorn.*asgi" | grep -v grep | awk '{print $2}' | while read pid; do
            info "Arrêt du processus Django avec PID $pid..."
            sudo kill -15 $pid || sudo kill -9 $pid
        done
        
        # Attendre un peu pour que les processus se terminent
        sleep 3
        
        # Vérifier à nouveau
        if ps aux | grep -E "python.*runserver|uvicorn.*asgi" | grep -v grep > /dev/null; then
            error "Impossible d'arrêter toutes les instances Django. Certaines instances sont encore en cours d'exécution:"
            ps aux | grep -E "python.*runserver|uvicorn.*asgi" | grep -v grep
            error "Veuillez les arrêter manuellement avant de continuer."
            return 1
        else
            success "Toutes les instances Django ont été arrêtées."
        fi
    fi
    
    # Aller dans le répertoire du backend
    cd "$BACKEND_DIR" || {
        error "Impossible d'accéder au répertoire $BACKEND_DIR"
        return 1
    }
    
    # Activer l'environnement virtuel si présent
    if [ -d "$BACKEND_DIR/nms_env" ]; then
        info "Activation de l'environnement virtuel..."
        source "$BACKEND_DIR/nms_env/bin/activate" || true
        success "Environnement virtuel activé"
    else
        warning "Environnement virtuel non trouvé dans $BACKEND_DIR/nms_env"
    fi

    # Vérification et démarrage automatique de PostgreSQL
    info "Vérification de PostgreSQL..."
    if docker ps | grep -q "nms-postgres"; then
        success "PostgreSQL est déjà démarré"
    else
        warning "PostgreSQL n'est pas démarré. Démarrage automatique en cours..."
        cd "$PROJECT_DIR"
        docker-compose up -d postgres redis
        if [ $? -eq 0 ]; then
            success "PostgreSQL et Redis démarrés avec succès"
            sleep 5  # Attendre que les services soient prêts
        else
            error "Échec du démarrage de PostgreSQL. Vérifiez Docker et docker-compose."
            return 1
        fi
        cd "$BACKEND_DIR"
    fi

    # Configuration des variables d'environnement pour PostgreSQL
    export POSTGRES_HOST=localhost
    export REDIS_HOST=localhost
    info "Variables d'environnement configurées pour PostgreSQL local"

    # Test de connexion à la base de données
    info "Test de connexion à la base de données..."
    if python manage.py check --database default > /dev/null 2>&1; then
        success "Connexion à la base de données PostgreSQL OK"
    else
        warning "Problème de connexion à PostgreSQL. Vérification des services..."
        # Attendre un peu plus et réessayer
        sleep 5
        if python manage.py check --database default > /dev/null 2>&1; then
            success "Connexion à la base de données PostgreSQL OK (après attente)"
        else
            error "Impossible de se connecter à PostgreSQL. Vérifiez que les services sont démarrés."
            return 1
        fi
    fi

    # Application des migrations si nécessaire
    info "Vérification des migrations..."
    if python manage.py showmigrations --plan 2>/dev/null | grep -q "\[ \]"; then
        warning "Migrations non appliquées détectées. Application en cours..."
        python manage.py migrate
        if [ $? -eq 0 ]; then
            success "Migrations appliquées avec succès"
        else
            warning "Certaines migrations ont échoué, mais Django peut démarrer"
        fi
    else
        success "Toutes les migrations sont à jour"
    fi

    # Collecte des fichiers statiques
    info "Collecte des fichiers statiques..."
    python manage.py collectstatic --noinput > /dev/null 2>&1 || true
    success "Fichiers statiques collectés"
    
    # Vérifier les dépendances nécessaires
    if ! command -v uvicorn &> /dev/null; then
        warning "Uvicorn n'est pas installé. Installation en cours..."
        pip install uvicorn || {
            error "Impossible d'installer Uvicorn. Installation de Uvicorn manuelle requise: pip install uvicorn"
            error "Tentative de démarrage avec runserver..."
            python manage.py runserver 0.0.0.0:8000 &
            local django_pid=$!
            info "Django démarré avec PID $django_pid"
        }
    fi
    
    # Vérifier si le port 8000 est déjà utilisé
    if lsof -i:8000 -t &> /dev/null; then
        warning "Le port 8000 est déjà utilisé. Utilisation du port 8001..."
        PORT=8001
    else
        PORT=8000
    fi
    
    # Démarrer Django avec Uvicorn et HTTPS
    info "Démarrage de Django avec Uvicorn HTTPS sur le port $PORT..."
    
    # Vérifier si les certificats SSL existent
    if [ -f "$BACKEND_DIR/ssl/django.crt" ] && [ -f "$BACKEND_DIR/ssl/django.key" ]; then
        info "Certificats SSL trouvés. Démarrage avec HTTPS..."
        uvicorn nms_backend.asgi:application --host 0.0.0.0 --port $PORT --workers 4 --log-level info \
            --ssl-keyfile ssl/django.key --ssl-certfile ssl/django.crt &
    else
        warning "Certificats SSL non trouvés. Démarrage en HTTP..."
        uvicorn nms_backend.asgi:application --host 0.0.0.0 --port $PORT --workers 4 --log-level info &
    fi
    DJANGO_PID=$!
    
    # Vérifier que Uvicorn a bien démarré
    sleep 3
    if ! ps -p $DJANGO_PID > /dev/null; then
        warning "Uvicorn ne semble pas avoir démarré. Tentative de démarrage avec runserver..."
        python manage.py runserver 0.0.0.0:$PORT &
        DJANGO_PID=$!
        
        # Vérifier que runserver a bien démarré
        sleep 3
        if ! ps -p $DJANGO_PID > /dev/null; then
            error "Impossible de démarrer Django."
            return 1
        fi
    fi
    
    # Enregistrer le PID de Django dans un fichier pour pouvoir l'arrêter plus tard
    echo $DJANGO_PID > "${PROJECT_DIR}/.django_pid"
    success "Django démarré en mode standalone avec PID $DJANGO_PID sur le port $PORT"

    # Messages informatifs pour l'utilisateur
    echo ""
    success "🎉 Django Network Management System démarré avec succès !"
    echo ""
    
    # Afficher les bonnes URLs selon le protocole utilisé
    if [ -f "$BACKEND_DIR/ssl/django.crt" ] && [ -f "$BACKEND_DIR/ssl/django.key" ]; then
        info "📊 Accès aux interfaces (HTTPS) :"
        info "   • Interface administrateur : https://localhost:$PORT/admin/"
        info "   • Documentation API Swagger : https://localhost:$PORT/swagger/"
        info "   • API Dashboard : https://localhost:$PORT/api/dashboard/"
    else
        info "📊 Accès aux interfaces (HTTP) :"
        info "   • Interface administrateur : http://localhost:$PORT/admin/"
        info "   • Documentation API Swagger : http://localhost:$PORT/swagger/"
        info "   • API Dashboard : http://localhost:$PORT/api/dashboard/"
    fi
    echo ""
    info "👤 Utilisateurs disponibles :"
    info "   • admin (mot de passe existant)"
    info "   • nmsadmin / admin123"
    echo ""
    info "🗄️  Base de données : PostgreSQL (localhost:5432)"
    info "🔧 Environnement virtuel : Activé"
    echo ""

    # Configurer HTTPS pour Django
    info "Configuration de HTTPS pour Django..."
    configure_https_for_django
    if [ $? -ne 0 ]; then
        warning "Configuration HTTPS échouée. Django est accessible via HTTP uniquement"
        info "🌐 URL principale : http://localhost:$PORT/"
    else
        success "Configuration HTTPS réussie"
        info "🔒 URL sécurisée : https://localhost/"
        info "🌐 URL alternative : http://localhost:$PORT/"
    fi
}

# Fonction pour démarrer Django directement avec HTTPS
start_direct_https() {
    title "Démarrage de Django directement avec HTTPS"
    
    # Vérifier si Django est en cours d'exécution dans un conteneur Docker
    if docker ps --filter "name=nms-django" --format "{{.Names}}" | grep -q "nms-django"; then
        info "Django est en cours d'exécution dans un conteneur Docker."
        info "Configuration du serveur Django pour utiliser HTTPS..."
        
        # Collecter les fichiers statiques dans le conteneur
        info "Collecte des fichiers statiques dans le conteneur..."
        docker exec nms-django bash -c "python manage.py collectstatic --noinput"
        
        # Vérifier si le dossier ssl existe dans le répertoire du backend Django
        if [ ! -d "${PROJECT_DIR}/web-interface/django__backend/ssl" ]; then
            info "Création du répertoire SSL pour Django..."
            mkdir -p "${PROJECT_DIR}/web-interface/django__backend/ssl"
        fi

        # Vérifier si les certificats existent dans config/ssl
        if [ -f "${PROJECT_DIR}/config/ssl/django.crt" ] && [ -f "${PROJECT_DIR}/config/ssl/django.key" ]; then
            info "Certificats SSL trouvés dans config/ssl. Copie vers le répertoire Django..."
            cp "${PROJECT_DIR}/config/ssl/django.crt" "${PROJECT_DIR}/web-interface/django__backend/ssl/"
            cp "${PROJECT_DIR}/config/ssl/django.key" "${PROJECT_DIR}/web-interface/django__backend/ssl/"
            chmod 644 "${PROJECT_DIR}/web-interface/django__backend/ssl/django.crt"
            chmod 600 "${PROJECT_DIR}/web-interface/django__backend/ssl/django.key"
        else
            # Générer les certificats s'ils n'existent pas
            info "Génération des certificats SSL..."
            mkdir -p "${PROJECT_DIR}/config/ssl"
            openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
              -keyout "${PROJECT_DIR}/config/ssl/django.key" \
              -out "${PROJECT_DIR}/config/ssl/django.crt" \
              -subj "/C=FR/ST=Paris/L=Paris/O=NMS/CN=localhost"
            
            # Copier les certificats vers le répertoire Django
            cp "${PROJECT_DIR}/config/ssl/django.crt" "${PROJECT_DIR}/web-interface/django__backend/ssl/"
            cp "${PROJECT_DIR}/config/ssl/django.key" "${PROJECT_DIR}/web-interface/django__backend/ssl/"
            chmod 644 "${PROJECT_DIR}/web-interface/django__backend/ssl/django.crt"
            chmod 600 "${PROJECT_DIR}/web-interface/django__backend/ssl/django.key"
        fi
        
        # Configurer Nginx pour servir les fichiers statiques
        info "Configuration de Nginx pour servir les fichiers statiques..."
        configure_nginx_for_static_files
        
        # Arrêter les processus existants dans le conteneur
        info "Arrêt des serveurs existants dans le conteneur..."
        docker exec nms-django bash -c "pkill -f 'python manage.py runserver' || true; pkill -f 'daphne' || true; pkill -f 'uvicorn' || true"
        
        # Démarrer Uvicorn avec HTTPS dans le conteneur
        info "Démarrage d'Uvicorn avec HTTPS dans le conteneur..."
        docker exec -d nms-django bash -c "cd /app && DJANGO_USE_SSL=true uvicorn nms_backend.asgi:application --host 0.0.0.0 --port 8000 --ssl-keyfile=/app/ssl/django.key --ssl-certfile=/app/ssl/django.crt --workers 4 --log-level info"
        
        # Vérifier que le serveur a démarré
        sleep 3
        if docker exec nms-django bash -c "ps aux | grep -q '[u]vicorn.*asgi'"; then
            success "Django démarré avec HTTPS dans le conteneur sur le port 8000."
            echo -e "${YELLOW}Accédez à l'application via ${CYAN}https://localhost:8000/${NC}"
        else
            error "Échec du démarrage d'Uvicorn avec HTTPS dans le conteneur."
            return 1
        fi
    else
        # Django n'est pas en cours d'exécution dans un conteneur Docker
        info "Django n'est pas en cours d'exécution dans un conteneur Docker."
        info "Démarrage de Django en mode standalone avec HTTPS..."
        
        # Définir le chemin du backend Django
        local BACKEND_DIR="${PROJECT_DIR}/web-interface/django__backend"
        
        # Arrêter tous les processus Django existants
        info "Arrêt des instances Django existantes..."
        ps aux | grep -E "python.*runserver|uvicorn.*asgi" | grep -v grep | awk '{print $2}' | while read pid; do
            info "Arrêt du processus Django avec PID $pid..."
            kill -15 $pid 2>/dev/null || kill -9 $pid 2>/dev/null
        done
        sleep 2
        
        # Collecter les fichiers statiques en mode standalone
        info "Collecte des fichiers statiques..."
        cd "$BACKEND_DIR" && python manage.py collectstatic --noinput
        
        # Vérifier le dossier ssl dans le répertoire du backend Django
        if [ ! -d "${BACKEND_DIR}/ssl" ]; then
            info "Création du répertoire SSL pour Django..."
            mkdir -p "${BACKEND_DIR}/ssl"
        fi
        
        # Vérifier si les certificats existent dans config/ssl
        if [ -f "${PROJECT_DIR}/config/ssl/django.crt" ] && [ -f "${PROJECT_DIR}/config/ssl/django.key" ]; then
            info "Certificats SSL trouvés dans config/ssl. Copie vers le répertoire Django..."
            cp "${PROJECT_DIR}/config/ssl/django.crt" "${BACKEND_DIR}/ssl/"
            cp "${PROJECT_DIR}/config/ssl/django.key" "${BACKEND_DIR}/ssl/"
            chmod 644 "${BACKEND_DIR}/ssl/django.crt"
            chmod 600 "${BACKEND_DIR}/ssl/django.key"
        else
            # Générer les certificats s'ils n'existent pas
            info "Génération des certificats SSL..."
            mkdir -p "${PROJECT_DIR}/config/ssl"
            openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
              -keyout "${PROJECT_DIR}/config/ssl/django.key" \
              -out "${PROJECT_DIR}/config/ssl/django.crt" \
              -subj "/C=FR/ST=Paris/L=Paris/O=NMS/CN=localhost"
            
            # Copier les certificats vers le répertoire Django
            cp "${PROJECT_DIR}/config/ssl/django.crt" "${BACKEND_DIR}/ssl/"
            cp "${PROJECT_DIR}/config/ssl/django.key" "${BACKEND_DIR}/ssl/"
            chmod 644 "${BACKEND_DIR}/ssl/django.crt"
            chmod 600 "${BACKEND_DIR}/ssl/django.key"
        fi
        
        # Configurer Nginx pour servir les fichiers statiques
        info "Configuration de Nginx pour servir les fichiers statiques..."
        configure_nginx_for_static_files
        
        # Aller dans le répertoire du backend
        cd "$BACKEND_DIR" || {
            error "Impossible d'accéder au répertoire $BACKEND_DIR"
            return 1
        }
        
        # Activer l'environnement virtuel si présent
        if [ -d "$BACKEND_DIR/nms_env" ]; then
            info "Activation de l'environnement virtuel..."
            source "$BACKEND_DIR/nms_env/bin/activate" || true
        fi
        
        # Démarrer Django avec Uvicorn et HTTPS
        info "Démarrage de Django avec Uvicorn et HTTPS..."
        export DJANGO_USE_SSL=true
        nohup uvicorn nms_backend.asgi:application --host 0.0.0.0 --port 8000 --ssl-keyfile="${BACKEND_DIR}/ssl/django.key" --ssl-certfile="${BACKEND_DIR}/ssl/django.crt" --workers 4 --log-level info > "${BACKEND_DIR}/logs/django_https.log" 2>&1 &
        DJANGO_PID=$!
        
        # Enregistrer le PID de Django dans un fichier pour pouvoir l'arrêter plus tard
        echo $DJANGO_PID > "${PROJECT_DIR}/.django_https_pid"
        
        # Vérifier que le serveur a démarré
        sleep 3
        if ps -p $DJANGO_PID > /dev/null; then
            success "Django démarré en mode standalone avec HTTPS sur le port 8000."
            echo -e "${YELLOW}Accédez à l'application via ${CYAN}https://localhost:8000/${NC}"
            echo -e "${YELLOW}PID: ${CYAN}$DJANGO_PID${NC}"
            
            # Information sur les fichiers statiques
            echo -e "\n${CYAN}Fichiers statiques:${NC}"
            echo -e "Les fichiers statiques sont servis par Nginx depuis ${YELLOW}${BACKEND_DIR}/staticfiles/${NC}"
            echo -e "L'URL de base pour les fichiers statiques est ${YELLOW}https://localhost/static/${NC}"
        else
            error "Échec du démarrage de Django avec HTTPS. Vérifiez le fichier de log: ${BACKEND_DIR}/logs/django_https.log"
            return 1
        fi
    fi
}

# Fonction pour configurer Nginx afin de servir les fichiers statiques
configure_nginx_for_static_files() {
    local NGINX_CONFIG_DIR="${PROJECT_DIR}/config/nginx"
    local BACKEND_DIR="${PROJECT_DIR}/web-interface/django__backend"

    # Définir le chemin complet du projet si pas déjà fait
    if [ -z "$PROJECT_DIR" ]; then
        PROJECT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." &> /dev/null && pwd )"
        NGINX_CONFIG_DIR="${PROJECT_DIR}/config/nginx"
        BACKEND_DIR="${PROJECT_DIR}/web-interface/django__backend"
    fi
    
    # Créer le répertoire config/nginx s'il n'existe pas
    mkdir -p "${NGINX_CONFIG_DIR}"
    
    info "Création ou mise à jour de la configuration Nginx pour les fichiers statiques..."
    
    # Créer ou mettre à jour la configuration Nginx pour servir les fichiers statiques
    cat > "${NGINX_CONFIG_DIR}/nginx_static.conf" << EOF
# Configuration Nginx pour servir les fichiers statiques de Django

server {
    listen 80;
    server_name localhost;
    
    # Rediriger HTTP vers HTTPS
    return 301 https://\$host\$request_uri;
}

server {
    listen 443 ssl;
    server_name localhost;
    
    # Certificats SSL
    ssl_certificate     /etc/ssl/certs/nms-cert.pem;
    ssl_certificate_key /etc/ssl/private/nms-key.pem;
    
    # Paramètres de sécurité SSL
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers on;
    ssl_ciphers 'ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305';
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    
    # Fichiers statiques - Point principal
    location /static/ {
        alias ${BACKEND_DIR}/staticfiles/;
        expires 30d;
        access_log off;
        add_header Cache-Control "public, max-age=2592000";
    }
    
    # Fichiers media
    location /media/ {
        alias ${BACKEND_DIR}/media/;
        expires 30d;
        access_log off;
        add_header Cache-Control "public, max-age=2592000";
    }
    
    # Fichiers admin et rest_framework
    location /static/admin/ {
        alias ${BACKEND_DIR}/staticfiles/admin/;
        expires 30d;
        access_log off;
    }
    
    location /static/rest_framework/ {
        alias ${BACKEND_DIR}/staticfiles/rest_framework/;
        expires 30d;
        access_log off;
    }
    
    # Proxy pour le backend Django
    location / {
        proxy_pass https://localhost:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto https;
        proxy_redirect off;
        
        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
EOF
    
    # Vérifier si les certificats SSL existent, sinon les générer
    if [ ! -f "/etc/ssl/certs/nms-cert.pem" ] || [ ! -f "/etc/ssl/private/nms-key.pem" ]; then
        info "Certificats SSL non trouvés. Génération des certificats..."
        sudo "${NGINX_CONFIG_DIR}/generate_ssl_certs.sh"
        if [ $? -ne 0 ]; then
            error "Échec de la génération des certificats SSL. Vérifiez les erreurs et réessayez."
            return 1
        fi
    fi
    
    # Arrêter les instances Nginx existantes
    if pgrep -x "nginx" > /dev/null; then
        info "Arrêt des instances Nginx existantes..."
        sudo systemctl stop nginx 2>/dev/null || true
        sudo nginx -s stop 2>/dev/null || true
        sleep 2
    fi
    
    # Démarrer Nginx avec la nouvelle configuration
    info "Démarrage de Nginx avec la configuration pour les fichiers statiques..."
    sudo nginx -c "${NGINX_CONFIG_DIR}/nginx_static.conf"
    
    # Vérifier que Nginx a démarré correctement
    if [ $? -eq 0 ] && sudo lsof -i :443 | grep -q nginx; then
        success "Nginx démarré avec succès pour servir les fichiers statiques."
        return 0
    else
        error "Erreur lors du démarrage de Nginx pour servir les fichiers statiques."
        sudo nginx -t -c "${NGINX_CONFIG_DIR}/nginx_static.conf"
        return 1
    fi
}

# Fonction pour arrêter HTTPS et Django
stop_https() {
    title "Arrêt de HTTPS et de Django"
    
    # Arrêter Nginx - gérer correctement les instances existantes
    info "Vérification des instances Nginx existantes..."
    if pgrep -x "nginx" > /dev/null; then
        info "Nginx est en cours d'exécution. Arrêt en cours..."
        # Essayer d'abord avec systemctl
        sudo systemctl stop nginx 2>/dev/null || true
        
        # Si toujours en cours d'exécution, essayer avec nginx -s stop
        if pgrep -x "nginx" > /dev/null; then
            sudo nginx -s stop 2>/dev/null || true
            sleep 2
            
            # Si Nginx est toujours en cours d'exécution, le tuer avec force
            if pgrep -x "nginx" > /dev/null; then
                warning "Nginx est toujours en cours d'exécution. Arrêt forcé..."
                sudo pkill -9 -x nginx 2>/dev/null || true
                sleep 2
                
                # Vérifier une dernière fois
                if pgrep -x "nginx" > /dev/null; then
                    error "Impossible d'arrêter Nginx. Vous devrez peut-être le faire manuellement avec: sudo pkill -9 nginx"
                    error "Processus Nginx restants:"
                    ps aux | grep nginx | grep -v grep
                    return 1
                fi
            fi
        fi
    else
        info "Aucune instance Nginx n'est en cours d'exécution."
    fi
    
    # Arrêter les instances Django
    info "Vérification des instances Django..."
    local django_instances=$(ps aux | grep -E "python.*runserver|uvicorn.*asgi" | grep -v grep)
    if [ ! -z "$django_instances" ]; then
        info "Instances Django trouvées. Arrêt en cours..."
        echo "$django_instances"
        
        # Arrêter les instances une par une
        ps aux | grep -E "python.*runserver|uvicorn.*asgi" | grep -v grep | awk '{print $2}' | while read pid; do
            info "Arrêt du processus Django avec PID $pid..."
            sudo kill -15 $pid 2>/dev/null || sudo kill -9 $pid 2>/dev/null
        done
        
        # Attendre un peu pour que les processus se terminent
        sleep 3
        
        # Vérifier à nouveau
        if ps aux | grep -E "python.*runserver|uvicorn.*asgi" | grep -v grep > /dev/null; then
            warning "Certaines instances Django sont encore en cours d'exécution:"
            ps aux | grep -E "python.*runserver|uvicorn.*asgi" | grep -v grep
        else
            success "Toutes les instances Django ont été arrêtées."
        fi
    else
        info "Aucune instance Django n'est en cours d'exécution."
    fi
    
    # Supprimer les fichiers PID s'ils existent
    if [ -f "${PROJECT_DIR}/.django_pid" ]; then
        rm "${PROJECT_DIR}/.django_pid"
    fi
    if [ -f "${PROJECT_DIR}/.django_https_pid" ]; then
        rm "${PROJECT_DIR}/.django_https_pid"
    fi
    
    info "Vérification des ports 80, 443, 8000 et 8001..."
    sudo lsof -i :80 -i :443 -i :8000 -i :8001 | grep LISTEN || echo "Aucun service n'écoute sur les ports 80, 443, 8000 et 8001."
}
