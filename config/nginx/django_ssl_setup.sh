#!/bin/bash

# Script pour configurer HTTPS pour Django avec Nginx
# Intégration avec le système NMS existant

# Répertoire du projet
PROJECT_DIR="/home/amir/network-management-system"
BACKEND_DIR="$PROJECT_DIR/web-interface/django_backend"
NGINX_CONFIG_DIR="$PROJECT_DIR/config/nginx"

# Importer les fonctions communes du système NMS
if [ -f "${PROJECT_DIR}/scripts/common.sh" ]; then
    source "${PROJECT_DIR}/scripts/common.sh"
else
    # Définir nos propres fonctions de couleur si le fichier common.sh n'est pas disponible
    RED='\033[0;31m'
    GREEN='\033[0;32m'
    YELLOW='\033[1;33m'
    BLUE='\033[0;34m'
    CYAN='\033[0;36m'
    NC='\033[0m' # No Color
    
    info() { echo -e "${BLUE}[INFO]${NC} $1"; }
    success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
    warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
    error() { echo -e "${RED}[ERROR]${NC} $1"; }
    title() { echo -e "\n${CYAN}=== $1 ===${NC}"; }
fi

title "Configuration HTTPS pour Django avec Nginx"

# Vérifier si nous sommes dans un environnement Docker
if command -v docker &> /dev/null && docker ps --filter name=nms-django --format "{{.Names}}" | grep -q nms-django; then
    info "Environnement Docker détecté avec le conteneur nms-django en cours d'exécution"
    RUNNING_IN_DOCKER=true
else
    info "Environnement local détecté (pas de conteneur nms-django trouvé)"
    RUNNING_IN_DOCKER=false
fi

# Vérifier si les certificats SSL existent, sinon les générer
if [ ! -f "/etc/ssl/certs/nms-cert.pem" ] || [ ! -f "/etc/ssl/private/nms-key.pem" ]; then
    info "Certificats SSL non trouvés. Génération des certificats..."
    $NGINX_CONFIG_DIR/generate_ssl_certs.sh
else
    success "Certificats SSL trouvés."
fi

# Arrêter les instances Nginx existantes
info "Arrêt des instances Nginx existantes..."
sudo systemctl stop nginx 2>/dev/null || true
sudo killall nginx 2>/dev/null || true

# Démarrer Nginx avec notre configuration
info "Démarrage de Nginx avec la configuration SSL..."
sudo nginx -c $NGINX_CONFIG_DIR/site.conf

# Vérifier que Nginx a démarré correctement
if [ $? -eq 0 ]; then
    success "Nginx démarré avec succès."
else
    error "Erreur lors du démarrage de Nginx."
    exit 1
fi

# Configuration du serveur Django
title "Configuration du backend Django"

# Modifier settings.py pour supporter le proxy HTTPS
if [ -f "$BACKEND_DIR/nms_backend/settings.py" ]; then
    info "Vérification des paramètres SSL dans settings.py..."
    
    # Vérifier si Django est configuré pour fonctionner derrière un proxy HTTPS
    if grep -q "SECURE_PROXY_SSL_HEADER" "$BACKEND_DIR/nms_backend/settings.py"; then
        success "Configuration HTTPS déjà présente dans settings.py"
    else
        error "Impossible de trouver la configuration HTTPS dans settings.py"
        info "Assurez-vous que les paramètres suivants sont présents dans settings.py:"
        echo -e "SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')"
        echo -e "SECURE_SSL_REDIRECT = True"
        echo -e "SESSION_COOKIE_SECURE = True"
        echo -e "CSRF_COOKIE_SECURE = True"
    fi
else
    error "Fichier settings.py non trouvé à $BACKEND_DIR/nms_backend/settings.py"
    exit 1
fi

# Démarrer ou redémarrer le serveur Django
title "Démarrage du backend Django"

if $RUNNING_IN_DOCKER; then
    # Utiliser le système de gestion Docker du NMS
    info "Redémarrage du service Django via Docker..."
    
    # Si le script services.sh existe et contient la fonction start_service
    if [ -f "${PROJECT_DIR}/scripts/services.sh" ] && grep -q "start_service()" "${PROJECT_DIR}/scripts/services.sh"; then
        source "${PROJECT_DIR}/scripts/services.sh" && start_service "django"
    else
        info "Redémarrage manuel du conteneur Django..."
        docker restart nms-django
        # Attendre que le conteneur soit prêt
        sleep 5
        # Configurer Uvicorn
        docker exec -d nms-django bash -c "pkill -f 'python manage.py runserver' || true; pkill -f 'uvicorn' || true; uvicorn nms_backend.asgi:application --host 0.0.0.0 --port 8000 --workers 4 --log-level info"
    fi
else
    # Mode de développement local
    info "Démarrage du serveur Django en local..."
    
    # Arrêter les processus existants
    pkill -f "python.*runserver" 2>/dev/null || true
    pkill -f "uvicorn.*asgi" 2>/dev/null || true
    
    # Aller dans le répertoire du backend
    cd $BACKEND_DIR
    
    # Activer l'environnement virtuel si présent
    if [ -d "$BACKEND_DIR/nms_env" ]; then
        info "Activation de l'environnement virtuel..."
        source $BACKEND_DIR/nms_env/bin/activate
    fi
    
    # Collecter les fichiers statiques
    info "Collecte des fichiers statiques..."
    python manage.py collectstatic --noinput
    
    # Démarrer avec Uvicorn pour le support ASGI
    info "Démarrage du serveur Django avec Uvicorn..."
    uvicorn nms_backend.asgi:application --host 0.0.0.0 --port 8000 --workers 4 --log-level info &
fi

sleep 3

# Vérification finale
title "Vérification finale"

# Vérifier que Nginx fonctionne
if pgrep -x "nginx" > /dev/null; then
    success "Nginx est en cours d'exécution."
else
    error "Nginx n'est pas en cours d'exécution."
fi

# Vérifier que Django est accessible
info "Test d'accès à l'API Django..."
curl -k https://localhost/api/ -o /dev/null -s -w "%{http_code}\n" | grep -q "200\|301\|302"
if [ $? -eq 0 ]; then
    success "L'API Django est accessible via HTTPS."
else
    warning "L'API Django n'est pas accessible via HTTPS. Vérifiez les journaux pour plus d'informations."
    info "Vous pouvez vérifier les journaux Nginx avec: sudo tail -f /var/log/nginx/error.log"
    info "Vous pouvez vérifier les journaux Django avec: tail -f $BACKEND_DIR/logs/nms.log"
fi

success "Configuration terminée!"
echo -e "${GREEN}Accédez à l'application via ${YELLOW}https://localhost/${NC}"
echo -e "${YELLOW}NOTE: Le certificat est auto-signé, vous devrez accepter l'avertissement de sécurité dans votre navigateur.${NC}"

# Informations supplémentaires
echo -e "\n${CYAN}URLs importantes:${NC}"
echo -e "Interface d'administration:  ${YELLOW}https://localhost/admin/${NC}"
echo -e "API REST:                    ${YELLOW}https://localhost/api/${NC}"
echo -e "Documentation API (Swagger): ${YELLOW}https://localhost/api/swagger/${NC}"
echo -e "Documentation API (ReDoc):   ${YELLOW}https://localhost/api/redoc/${NC}" 