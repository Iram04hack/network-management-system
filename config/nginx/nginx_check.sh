#!/bin/bash
#
# Script de vérification et diagnostic pour la configuration Nginx avec HTTPS
# Version: 1.1.0

# Obtenir le répertoire du script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_DIR="$( cd "$SCRIPT_DIR/../.." &> /dev/null && pwd )"

# Codes couleur
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Fonctions utilitaires
error() {
    echo -e "${RED}[ERREUR]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[ATTENTION]${NC} $1"
}

info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

success() {
    echo -e "${GREEN}[SUCCÈS]${NC} $1"
}

title() {
    echo -e "\n${CYAN}=== $1 ===${NC}"
}

# Fonction d'aide
show_help() {
    echo "Usage: $0 [option]"
    echo ""
    echo "Options:"
    echo "  check       Vérifier la configuration Nginx"
    echo "  diagnose    Diagnostiquer les problèmes courants de Nginx et HTTPS"
    echo "  test        Tester l'accès à l'API Django via HTTPS"
    echo "  fix         Tenter de corriger les problèmes détectés automatiquement"
    echo "  help        Afficher cette aide"
    echo ""
    echo "Exemples:"
    echo "  $0 check      # Vérifier la configuration Nginx"
    echo "  $0 diagnose   # Diagnostiquer les problèmes"
}

# Fonction pour vérifier la configuration Nginx
check_nginx_config() {
    title "Vérification de la configuration Nginx"
    
    # Vérifier si Nginx est installé
    if ! command -v nginx &> /dev/null; then
        error "Nginx n'est pas installé."
        return 1
    else
        success "Nginx est installé: $(nginx -v 2>&1)"
    fi
    
    # Vérifier le fichier de configuration spécifique
    local config_file="${SCRIPT_DIR}/site.conf"
    if [ -f "$config_file" ]; then
        info "Vérification du fichier de configuration: $config_file"
        sudo nginx -t -c "$config_file" 2>&1
        
        if [ $? -eq 0 ]; then
            success "La syntaxe de la configuration est correcte."
        else
            error "La configuration contient des erreurs."
            return 1
        fi
        
        # Vérifier les chemins dans la configuration
        info "Vérification des chemins dans la configuration..."
        grep "proxy_pass" "$config_file"
        grep "alias" "$config_file"
    else
        error "Fichier de configuration non trouvé: $config_file"
        return 1
    fi
    
    # Vérifier les certificats SSL
    info "Vérification des certificats SSL..."
    if [ -f "/etc/ssl/certs/nms-cert.pem" ] && [ -f "/etc/ssl/private/nms-key.pem" ]; then
        success "Certificats SSL trouvés."
        
        # Vérifier la validité du certificat
        info "Informations sur le certificat:"
        sudo openssl x509 -in /etc/ssl/certs/nms-cert.pem -text -noout | grep -E "Subject:|Issuer:|Not Before:|Not After :" || error "Impossible de lire les informations du certificat"
        
        # Vérifier si le certificat est expiré
        local now=$(date +%s)
        local expiry=$(sudo openssl x509 -in /etc/ssl/certs/nms-cert.pem -enddate -noout | sed -e 's/.*=\(.*\)/\1/' | xargs -I{} date -d {} +%s)
        
        if [ "$expiry" -lt "$now" ]; then
            error "Le certificat SSL est expiré!"
        else
            local days_left=$(( ($expiry - $now) / 86400 ))
            success "Le certificat SSL est valide pour encore $days_left jours."
        fi
    else
        error "Certificats SSL non trouvés."
        warning "Exécutez 'sudo ${SCRIPT_DIR}/generate_ssl_certs.sh' pour générer les certificats."
        return 1
    fi
    
    # Vérifier si Nginx est en cours d'exécution
    info "Vérification de l'état de Nginx..."
    if pgrep -x "nginx" > /dev/null; then
        success "Nginx est en cours d'exécution:"
        ps aux | grep nginx | grep -v grep
        
        # Vérifier les ports sur lesquels Nginx écoute
        info "Ports Nginx:"
        sudo lsof -i -P -n | grep nginx | grep LISTEN || warning "Aucun port trouvé pour Nginx"
    else
        error "Nginx n'est pas en cours d'exécution."
        return 1
    fi
    
    return 0
}

# Fonction pour diagnostiquer les problèmes courants
diagnose_problems() {
    title "Diagnostic des problèmes de Nginx et HTTPS"
    
    # 1. Vérifier les processus en cours d'exécution
    info "Vérification des processus en cours d'exécution..."
    ps aux | grep -E "nginx|runserver|uvicorn" | grep -v grep || echo "Aucun processus pertinent trouvé."
    
    # 2. Vérifier les ports utilisés
    info "Vérification des ports utilisés..."
    
    # Vérifier le port 80
    if sudo lsof -i :80 | grep LISTEN > /dev/null; then
        info "Port 80 en cours d'utilisation:"
        sudo lsof -i :80 | grep LISTEN
    else
        warning "Port 80 non utilisé. Nginx devrait écouter sur ce port."
    fi
    
    # Vérifier le port 443
    if sudo lsof -i :443 | grep LISTEN > /dev/null; then
        info "Port 443 en cours d'utilisation:"
        sudo lsof -i :443 | grep LISTEN
    else
        warning "Port 443 non utilisé. Nginx devrait écouter sur ce port pour HTTPS."
    fi
    
    # Vérifier les ports 8000/8001 (Django)
    if sudo lsof -i :8000 | grep LISTEN > /dev/null; then
        info "Port 8000 en cours d'utilisation:"
        sudo lsof -i :8000 | grep LISTEN
    else
        warning "Port 8000 non utilisé. Django pourrait utiliser ce port."
    fi
    
    if sudo lsof -i :8001 | grep LISTEN > /dev/null; then
        info "Port 8001 en cours d'utilisation:"
        sudo lsof -i :8001 | grep LISTEN
    else
        warning "Port 8001 non utilisé. Django pourrait utiliser ce port si 8000 est occupé."
    fi
    
    # 3. Vérifier les journaux Nginx
    info "Vérification des journaux Nginx récents..."
    if [ -f "/var/log/nginx/error.log" ]; then
        sudo tail -n 20 /var/log/nginx/error.log || warning "Impossible de lire les journaux d'erreur Nginx."
    else
        warning "Fichier journal d'erreur Nginx non trouvé."
    fi
    
    # 4. Vérifier les problèmes de certificats
    info "Vérification des problèmes de certificats..."
    if [ ! -f "/etc/ssl/certs/nms-cert.pem" ] || [ ! -f "/etc/ssl/private/nms-key.pem" ]; then
        error "Certificats SSL manquants. Vous devez les générer."
    else
        # Vérifier les permissions
        info "Permissions des certificats:"
        sudo ls -l /etc/ssl/certs/nms-cert.pem /etc/ssl/private/nms-key.pem
        
        # Si les permissions sont incorrectes
        if [ "$(sudo stat -c '%a' /etc/ssl/certs/nms-cert.pem)" != "644" ]; then
            warning "Les permissions du certificat devraient être 644."
        fi
        
        if [ "$(sudo stat -c '%a' /etc/ssl/private/nms-key.pem)" != "600" ]; then
            warning "Les permissions de la clé privée devraient être 600."
        fi
    fi
    
    # 5. Vérifier la configuration actuelle de Django
    info "Vérification de la configuration de Django..."
    DJANGO_PORT=""
    if ps aux | grep "runserver.*8000" | grep -v grep > /dev/null || ps aux | grep "uvicorn.*--port 8000" | grep -v grep > /dev/null; then
        DJANGO_PORT="8000"
    elif ps aux | grep "runserver.*8001" | grep -v grep > /dev/null || ps aux | grep "uvicorn.*--port 8001" | grep -v grep > /dev/null; then
        DJANGO_PORT="8001"
    fi
    
    if [ -n "$DJANGO_PORT" ]; then
        info "Django écoute sur le port $DJANGO_PORT."
        
        # Vérifier si le port dans la configuration Nginx correspond
        if [ -f "${SCRIPT_DIR}/site.conf" ]; then
            NGINX_PORT=$(grep -o "proxy_pass http://localhost:[0-9]\+" "${SCRIPT_DIR}/site.conf" | head -1 | cut -d: -f3)
            
            if [ "$NGINX_PORT" != "$DJANGO_PORT" ]; then
                error "Discordance de port: Django écoute sur $DJANGO_PORT mais Nginx est configuré pour le port $NGINX_PORT."
                warning "Vous devriez mettre à jour la configuration Nginx ou redémarrer Django sur le port $NGINX_PORT."
            else
                success "Les ports Django et Nginx correspondent."
            fi
        fi
    else
        warning "Aucune instance Django détectée."
    fi
    
    # 6. Test de connexion HTTP simple
    info "Test de connexion HTTP simple..."
    if command -v curl &> /dev/null; then
        # Test HTTP
        HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost/ 2>/dev/null)
        if [[ "$HTTP_CODE" =~ ^(200|301|302)$ ]]; then
            success "Connexion HTTP réussie (code: $HTTP_CODE)"
        else
            warning "Connexion HTTP échouée (code: $HTTP_CODE)"
        fi
        
        # Test HTTPS
        HTTPS_CODE=$(curl -k -s -o /dev/null -w "%{http_code}" https://localhost/ 2>/dev/null)
        if [[ "$HTTPS_CODE" =~ ^(200|301|302)$ ]]; then
            success "Connexion HTTPS réussie (code: $HTTPS_CODE)"
        else
            warning "Connexion HTTPS échouée (code: $HTTPS_CODE)"
        fi
    else
        warning "curl n'est pas installé. Impossible de tester la connexion."
    fi
}

# Fonction pour tester l'accès à l'API Django via HTTPS
test_django_api() {
    title "Test d'accès à l'API Django via HTTPS"
    
    if ! command -v curl &> /dev/null; then
        error "curl n'est pas installé. Veuillez l'installer pour effectuer le test."
        return 1
    fi
    
    # Test d'accès à la page d'accueil
    info "Test d'accès à la page d'accueil..."
    HOME_CODE=$(curl -k -s -o /dev/null -w "%{http_code}" https://localhost/ 2>/dev/null)
    if [[ "$HOME_CODE" =~ ^(200|301|302)$ ]]; then
        success "Accès à la page d'accueil réussi (code: $HOME_CODE)"
    else
        error "Accès à la page d'accueil échoué (code: $HOME_CODE)"
    fi
    
    # Test d'accès à l'API
    info "Test d'accès à l'API..."
    API_CODE=$(curl -k -s -o /dev/null -w "%{http_code}" https://localhost/api/ 2>/dev/null)
    if [[ "$API_CODE" =~ ^(200|301|302)$ ]]; then
        success "Accès à l'API réussi (code: $API_CODE)"
        
        # Afficher la réponse de l'API
        echo -e "\nRéponse de l'API:"
        curl -k -s https://localhost/api/ | head -20
    else
        error "Accès à l'API échoué (code: $API_CODE)"
    fi
    
    # Test d'accès à la documentation Swagger
    info "Test d'accès à la documentation Swagger..."
    SWAGGER_CODE=$(curl -k -s -o /dev/null -w "%{http_code}" https://localhost/api/swagger/ 2>/dev/null)
    if [[ "$SWAGGER_CODE" =~ ^(200|301|302)$ ]]; then
        success "Accès à la documentation Swagger réussi (code: $SWAGGER_CODE)"
    else
        error "Accès à la documentation Swagger échoué (code: $SWAGGER_CODE)"
    fi
    
    # Test d'accès à l'admin Django
    info "Test d'accès à l'admin Django..."
    ADMIN_CODE=$(curl -k -s -o /dev/null -w "%{http_code}" https://localhost/admin/ 2>/dev/null)
    if [[ "$ADMIN_CODE" =~ ^(200|301|302)$ ]]; then
        success "Accès à l'admin Django réussi (code: $ADMIN_CODE)"
    else
        error "Accès à l'admin Django échoué (code: $ADMIN_CODE)"
    fi
}

# Fonction pour tenter de corriger les problèmes détectés automatiquement
fix_problems() {
    title "Tentative de correction des problèmes"
    
    # 1. Vérifier et corriger les certificats SSL
    info "Vérification des certificats SSL..."
    if [ ! -f "/etc/ssl/certs/nms-cert.pem" ] || [ ! -f "/etc/ssl/private/nms-key.pem" ]; then
        warning "Certificats SSL manquants. Génération en cours..."
        if [ -f "${SCRIPT_DIR}/generate_ssl_certs.sh" ]; then
            sudo "${SCRIPT_DIR}/generate_ssl_certs.sh"
        else
            error "Script de génération de certificats non trouvé."
            return 1
        fi
    else
        # Corriger les permissions si nécessaire
        if [ "$(sudo stat -c '%a' /etc/ssl/certs/nms-cert.pem)" != "644" ]; then
            warning "Correction des permissions du certificat..."
            sudo chmod 644 /etc/ssl/certs/nms-cert.pem
        fi
        
        if [ "$(sudo stat -c '%a' /etc/ssl/private/nms-key.pem)" != "600" ]; then
            warning "Correction des permissions de la clé privée..."
            sudo chmod 600 /etc/ssl/private/nms-key.pem
        fi
    fi
    
    # 2. Arrêter toutes les instances Nginx
    info "Arrêt de toutes les instances Nginx..."
    if pgrep -x "nginx" > /dev/null; then
        sudo systemctl stop nginx 2>/dev/null || true
        sleep 1
        
        if pgrep -x "nginx" > /dev/null; then
            sudo nginx -s stop 2>/dev/null || true
            sleep 2
            
            if pgrep -x "nginx" > /dev/null; then
                warning "Arrêt forcé de Nginx..."
                sudo pkill -9 -x nginx 2>/dev/null || true
                sleep 2
            fi
        fi
    fi
    
    # 3. Vérifier les ports Django et mettre à jour la configuration Nginx si nécessaire
    info "Vérification de la configuration Django..."
    DJANGO_PORT=""
    if ps aux | grep "runserver.*8000" | grep -v grep > /dev/null || ps aux | grep "uvicorn.*--port 8000" | grep -v grep > /dev/null; then
        DJANGO_PORT="8000"
    elif ps aux | grep "runserver.*8001" | grep -v grep > /dev/null || ps aux | grep "uvicorn.*--port 8001" | grep -v grep > /dev/null; then
        DJANGO_PORT="8001"
    fi
    
    if [ -n "$DJANGO_PORT" ]; then
        info "Django écoute sur le port $DJANGO_PORT."
        
        # Mettre à jour la configuration Nginx si nécessaire
        if [ -f "${SCRIPT_DIR}/site.conf" ]; then
            CONFIGURED_PORT=$(grep -o "proxy_pass http://localhost:[0-9]\+" "${SCRIPT_DIR}/site.conf" | head -1 | cut -d: -f3)
            
            if [ "$CONFIGURED_PORT" != "$DJANGO_PORT" ]; then
                warning "Mise à jour du port Django dans la configuration Nginx: $CONFIGURED_PORT -> $DJANGO_PORT"
                sudo sed -i "s/proxy_pass http:\/\/localhost:$CONFIGURED_PORT/proxy_pass http:\/\/localhost:$DJANGO_PORT/g" "${SCRIPT_DIR}/site.conf"
            fi
        fi
    else
        warning "Aucune instance Django détectée. Impossible de mettre à jour la configuration Nginx."
    fi
    
    # 4. Vérifier que les ports 80 et 443 sont disponibles
    info "Vérification de la disponibilité des ports 80 et 443..."
    local ports_used=false
    if sudo lsof -i :80 | grep LISTEN > /dev/null; then
        warning "Le port 80 est déjà utilisé."
        ports_used=true
    fi
    
    if sudo lsof -i :443 | grep LISTEN > /dev/null; then
        warning "Le port 443 est déjà utilisé."
        ports_used=true
    fi
    
    if [ "$ports_used" = true ]; then
        warning "Tentative de libération des ports..."
        sudo lsof -i :80 -i :443 | grep LISTEN | awk '{print $2}' | while read pid; do
            warning "Arrêt du processus avec PID $pid qui utilise les ports 80/443..."
            sudo kill -15 $pid 2>/dev/null || sudo kill -9 $pid 2>/dev/null
        done
        sleep 2
        
        if sudo lsof -i :80 -i :443 | grep LISTEN > /dev/null; then
            error "Impossible de libérer les ports 80/443."
            return 1
        fi
    fi
    
    # 5. Démarrer Nginx avec la configuration
    info "Démarrage de Nginx avec la configuration SSL..."
    sudo nginx -c "${SCRIPT_DIR}/site.conf"
    
    if [ $? -eq 0 ]; then
        success "Nginx démarré avec succès."
        
        # Vérifier que Nginx écoute sur les ports 80 et 443
        if sudo lsof -i :80 -i :443 | grep nginx | grep LISTEN > /dev/null; then
            success "Nginx écoute sur les ports 80 et 443."
        else
            error "Nginx ne semble pas écouter sur les ports 80 et 443."
            return 1
        fi
    else
        error "Échec du démarrage de Nginx."
        return 1
    fi
    
    # 6. Effectuer un test simple
    info "Test d'accès à l'API Django..."
    if command -v curl &> /dev/null; then
        sleep 2
        HTTP_CODE=$(curl -k -s -o /dev/null -w "%{http_code}" https://localhost/api/ 2>/dev/null)
        if [[ "$HTTP_CODE" =~ ^(200|301|302)$ ]]; then
            success "L'API Django est accessible via HTTPS (code: $HTTP_CODE)"
        else
            warning "L'API Django n'est pas immédiatement accessible via HTTPS (code: $HTTP_CODE)"
        fi
    fi
    
    success "Correction des problèmes terminée."
}

# Traitement des arguments
case "$1" in
    check)
        check_nginx_config
        ;;
    diagnose)
        diagnose_problems
        ;;
    test)
        test_django_api
        ;;
    fix)
        fix_problems
        ;;
    help|*)
        show_help
        ;;
esac 