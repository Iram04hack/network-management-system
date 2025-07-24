#!/bin/bash
#
# Script pour démarrer rapidement Django avec HTTPS
# Version: 1.1.0

# Obtenir le répertoire du script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_DIR="$( cd "$SCRIPT_DIR/../.." &> /dev/null && pwd )"

# Importer les fonctions utiles
source "${PROJECT_DIR}/scripts/common.sh" 2>/dev/null || {
    # Si common.sh n'est pas trouvé, définir quelques fonctions de base
    RED='\033[0;31m'
    GREEN='\033[0;32m'
    YELLOW='\033[1;33m'
    BLUE='\033[0;34m'
    CYAN='\033[0;36m'
    NC='\033[0m' # No Color
    
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
}

# Fonction pour afficher l'aide
show_help() {
    echo "Usage: $0 [option]"
    echo ""
    echo "Options:"
    echo "  start         Démarrer Django avec HTTPS"
    echo "  stop          Arrêter Django et Nginx"
    echo "  restart       Redémarrer Django et Nginx"
    echo "  status        Vérifier l'état de Django et Nginx"
    echo "  help          Afficher cette aide"
    echo ""
    echo "Exemples:"
    echo "  $0 start      # Démarrer Django avec HTTPS"
    echo "  $0 stop       # Arrêter Django et Nginx"
}

# Fonction pour démarrer Django avec HTTPS
start_django_https() {
    title "Démarrage de Django avec HTTPS"
    
    # Vérifier si Django est déjà en cours d'exécution
    if ps aux | grep -E "python.*runserver|uvicorn.*asgi" | grep -v grep > /dev/null; then
        info "Django est déjà en cours d'exécution:"
        ps aux | grep -E "python.*runserver|uvicorn.*asgi" | grep -v grep
    else
        info "Démarrage de Django..."
        
        # Déterminer le port à utiliser
        DJANGO_PORT=8000
        if lsof -i:8000 -t &> /dev/null; then
            warning "Le port 8000 est déjà utilisé. Utilisation du port 8001..."
            DJANGO_PORT=8001
        fi
        
        # Aller dans le répertoire du backend Django
        cd "${PROJECT_DIR}/web-interface/django_backend" || {
            error "Impossible d'accéder au répertoire ${PROJECT_DIR}/web-interface/django_backend"
            return 1
        }
        
        # Activer l'environnement virtuel si présent
        if [ -d "${PROJECT_DIR}/web-interface/django_backend/nms_env" ]; then
            info "Activation de l'environnement virtuel..."
            source "${PROJECT_DIR}/web-interface/django_backend/nms_env/bin/activate" || true
        fi
        
        # Démarrer Django avec Uvicorn
        info "Démarrage de Django avec Uvicorn sur le port $DJANGO_PORT..."
        if command -v uvicorn &> /dev/null; then
            uvicorn nms_backend.asgi:application --host 0.0.0.0 --port $DJANGO_PORT --workers 4 --log-level info &
            DJANGO_PID=$!
        else
            warning "Uvicorn n'est pas installé. Utilisation de runserver..."
            python manage.py runserver 0.0.0.0:$DJANGO_PORT &
            DJANGO_PID=$!
        fi
        
        # Vérifier que Django a bien démarré
        sleep 2
        if ! ps -p $DJANGO_PID > /dev/null; then
            error "Échec du démarrage de Django."
            return 1
        fi
        
        # Enregistrer le PID pour pouvoir l'arrêter plus tard
        echo $DJANGO_PID > "${PROJECT_DIR}/.django_pid"
        success "Django démarré avec PID $DJANGO_PID sur le port $DJANGO_PORT"
    fi
    
    # Configurer Nginx pour HTTPS
    info "Configuration de Nginx pour HTTPS..."
    
    # Vérifier si Nginx est déjà en cours d'exécution
    if pgrep -x "nginx" > /dev/null; then
        info "Nginx est déjà en cours d'exécution:"
        ps aux | grep nginx | grep -v grep
    fi
    
    # Appeler la fonction de configuration HTTPS
    if source "${PROJECT_DIR}/scripts/services.sh" && configure_https_for_django; then
        success "Django est maintenant accessible via HTTPS"
        echo -e "\n${BLUE}URLs importantes:${NC}"
        echo -e "Interface d'administration: ${YELLOW}https://localhost/admin/${NC}"
        echo -e "API REST:                   ${YELLOW}https://localhost/api/${NC}"
        echo -e "Documentation API:          ${YELLOW}https://localhost/api/swagger/${NC}"
        echo -e "${YELLOW}NOTE: Le certificat est auto-signé, vous devrez accepter l'avertissement de sécurité dans votre navigateur.${NC}"
    else
        warning "Configuration HTTPS échouée. Django est accessible via http://localhost:$DJANGO_PORT/ sans HTTPS"
    fi
}

# Fonction pour arrêter Django et Nginx
stop_django_https() {
    title "Arrêt de Django et Nginx"
    
    # Arrêter Nginx
    info "Arrêt de Nginx..."
    if pgrep -x "nginx" > /dev/null; then
        sudo systemctl stop nginx 2>/dev/null || true
        sudo nginx -s stop 2>/dev/null || true
        sudo pkill -9 -x nginx 2>/dev/null || true
        if ! pgrep -x "nginx" > /dev/null; then
            success "Nginx arrêté avec succès."
        else
            error "Nginx est toujours en cours d'exécution:"
            ps aux | grep nginx | grep -v grep
        fi
    else
        info "Nginx n'est pas en cours d'exécution."
    fi
    
    # Arrêter Django
    info "Arrêt de Django..."
    if ps aux | grep -E "python.*runserver|uvicorn.*asgi" | grep -v grep > /dev/null; then
        # Utiliser le PID enregistré si disponible
        if [ -f "${PROJECT_DIR}/.django_pid" ]; then
            DJANGO_PID=$(cat "${PROJECT_DIR}/.django_pid")
            info "Arrêt du processus Django avec PID $DJANGO_PID..."
            sudo kill -15 $DJANGO_PID 2>/dev/null || sudo kill -9 $DJANGO_PID 2>/dev/null
            rm "${PROJECT_DIR}/.django_pid"
        else
            # Sinon, tuer tous les processus Django
            ps aux | grep -E "python.*runserver|uvicorn.*asgi" | grep -v grep | awk '{print $2}' | while read pid; do
                info "Arrêt du processus Django avec PID $pid..."
                sudo kill -15 $pid 2>/dev/null || sudo kill -9 $pid 2>/dev/null
            done
        fi
        
        # Vérifier que tous les processus ont été arrêtés
        sleep 2
        if ! ps aux | grep -E "python.*runserver|uvicorn.*asgi" | grep -v grep > /dev/null; then
            success "Django arrêté avec succès."
        else
            error "Django est toujours en cours d'exécution:"
            ps aux | grep -E "python.*runserver|uvicorn.*asgi" | grep -v grep
        fi
    else
        info "Django n'est pas en cours d'exécution."
    fi
    
    # Vérifier les ports
    info "Vérification des ports 80, 443, 8000 et 8001..."
    sudo lsof -i :80 -i :443 -i :8000 -i :8001 | grep LISTEN || echo "Aucun service n'écoute sur les ports 80, 443, 8000 et 8001."
}

# Fonction pour vérifier l'état de Django et Nginx
check_status() {
    title "État de Django et Nginx"
    
    # Vérifier l'état de Django
    echo -e "${CYAN}État de Django:${NC}"
    if ps aux | grep -E "python.*runserver|uvicorn.*asgi" | grep -v grep > /dev/null; then
        echo -e "${GREEN}[EN COURS]${NC} Django est en cours d'exécution:"
        ps aux | grep -E "python.*runserver|uvicorn.*asgi" | grep -v grep
        
        # Déterminer le port Django
        if ps aux | grep "runserver.*8000" | grep -v grep > /dev/null || ps aux | grep "uvicorn.*--port 8000" | grep -v grep > /dev/null; then
            echo "Django écoute sur le port 8000"
        elif ps aux | grep "runserver.*8001" | grep -v grep > /dev/null || ps aux | grep "uvicorn.*--port 8001" | grep -v grep > /dev/null; then
            echo "Django écoute sur le port 8001"
        else
            echo "Port Django inconnu"
        fi
    else
        echo -e "${RED}[ARRÊTÉ]${NC} Django n'est pas en cours d'exécution."
    fi
    
    # Vérifier l'état de Nginx
    echo -e "\n${CYAN}État de Nginx:${NC}"
    if pgrep -x "nginx" > /dev/null; then
        echo -e "${GREEN}[EN COURS]${NC} Nginx est en cours d'exécution:"
        ps aux | grep nginx | grep -v grep
        
        # Vérifier les ports sur lesquels Nginx écoute
        echo -e "\nPorts Nginx:"
        sudo lsof -i -P -n | grep nginx | grep LISTEN || echo "Aucun port trouvé pour Nginx"
    else
        echo -e "${RED}[ARRÊTÉ]${NC} Nginx n'est pas en cours d'exécution."
    fi
    
    # Vérifier l'état des certificats SSL
    echo -e "\n${CYAN}État des certificats SSL:${NC}"
    if [ -f "/etc/ssl/certs/nms-cert.pem" ] && [ -f "/etc/ssl/private/nms-key.pem" ]; then
        echo -e "${GREEN}[OK]${NC} Certificats SSL trouvés:"
        echo "Certificat: /etc/ssl/certs/nms-cert.pem"
        echo "Clé privée: /etc/ssl/private/nms-key.pem"
        
        # Afficher les informations sur le certificat
        echo -e "\nInformations sur le certificat:"
        sudo openssl x509 -in /etc/ssl/certs/nms-cert.pem -text -noout | grep -E "Subject:|Issuer:|Not Before:|Not After :" || echo "Impossible de lire les informations du certificat"
    else
        echo -e "${RED}[MANQUANT]${NC} Certificats SSL non trouvés."
    fi
    
    # Afficher les ports en écoute
    echo -e "\n${CYAN}Ports en écoute:${NC}"
    sudo lsof -i :80 -i :443 -i :8000 -i :8001 | grep LISTEN || echo "Aucun service n'écoute sur les ports 80, 443, 8000 et 8001."
}

# Traitement des arguments
case "$1" in
    start)
        start_django_https
        ;;
    stop)
        stop_django_https
        ;;
    restart)
        stop_django_https
        sleep 2
        start_django_https
        ;;
    status)
        check_status
        ;;
    help|*)
        show_help
        ;;
esac 