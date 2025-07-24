#!/bin/bash

# Couleurs pour les messages
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Obtenir le chemin du projet
PROJECT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd .. && pwd )"

# Chemins des fichiers docker-compose
COMPOSE_MAIN="${PROJECT_DIR}/docker-compose.yml"
COMPOSE_SECURITY="${PROJECT_DIR}/docker-compose.security.yml"
COMPOSE_MONITORING="${PROJECT_DIR}/docker-compose.monitoring.yml"
COMPOSE_TRAFFIC="${PROJECT_DIR}/docker-compose.traffic-control.yml"

# Fonction pour afficher un titre
title() {
    echo -e "\n${BLUE}== $1 ==${NC}"
}

# Fonction pour afficher un message de succès
success() {
    echo -e "[${GREEN}SUCCESS${NC}] $1"
}

# Fonction pour afficher un message d'information
info() {
    echo -e "[${CYAN}INFO${NC}] $1"
}

# Fonction pour afficher un avertissement
warning() {
    echo -e "[${YELLOW}WARNING${NC}] $1"
}

# Fonction pour afficher une erreur
error() {
    echo -e "[${RED}ERROR${NC}] $1"
}

# Fonction pour exécuter une commande docker-compose
# Mise à jour pour utiliser "docker compose" au lieu de "docker-compose"
docker_compose_command() {
    local compose_file="$1"
    local command="$2"
    local service="$3"
    
    if [ -z "$compose_file" ]; then
        error "Fichier docker-compose non spécifié"
        return 1
    fi
    
    if [ ! -f "$compose_file" ]; then
        error "Fichier docker-compose introuvable: $compose_file"
        return 1
    fi
    
    if [ -z "$command" ]; then
        error "Commande docker compose non spécifiée"
        return 1
    fi
    
    if [ -n "$service" ]; then
        docker compose -f "$compose_file" $command $service
    else
        docker compose -f "$compose_file" $command
    fi
}

# Fonction pour vérifier l'environnement
check_environment() {
    # Vérifier que Docker est installé
    if ! command -v docker &> /dev/null; then
        error "Docker n'est pas installé. Veuillez l'installer avant de continuer."
        exit 1
    fi
    
    # Vérifier la disponibilité de "docker compose"
    if ! docker compose version &> /dev/null; then
        warning "La commande 'docker compose' n'est pas disponible. Assurez-vous d'utiliser Docker version 20.10.0 ou supérieure."
        warning "Vous pouvez également installer Docker Compose V2 séparément."
        warning "Voir: https://docs.docker.com/compose/install/"
        exit 1
    fi
}

# Fonction pour créer les dossiers nécessaires
create_directories() {
    info "Création des dossiers nécessaires..."
    
    # Dossiers de configuration
    mkdir -p "${PROJECT_DIR}/config/elasticsearch"
    mkdir -p "${PROJECT_DIR}/config/fail2ban/filter.d"
    mkdir -p "${PROJECT_DIR}/config/haproxy"
    mkdir -p "${PROJECT_DIR}/config/kibana"
    mkdir -p "${PROJECT_DIR}/config/netdata"
    mkdir -p "${PROJECT_DIR}/config/nginx"
    mkdir -p "${PROJECT_DIR}/config/prometheus"
    mkdir -p "${PROJECT_DIR}/config/suricata/rules"
    mkdir -p "${PROJECT_DIR}/config/tc"
    
    # Dossiers de données
    mkdir -p "${PROJECT_DIR}/data/elasticsearch"
    mkdir -p "${PROJECT_DIR}/data/grafana"
    mkdir -p "${PROJECT_DIR}/data/kibana"
    mkdir -p "${PROJECT_DIR}/data/netdata"
    mkdir -p "${PROJECT_DIR}/data/ntopng"
    mkdir -p "${PROJECT_DIR}/data/postgres"
    mkdir -p "${PROJECT_DIR}/data/prometheus"
    mkdir -p "${PROJECT_DIR}/data/redis"
    mkdir -p "${PROJECT_DIR}/data/suricata"
    
    # Dossier de sauvegarde
    mkdir -p "${PROJECT_DIR}/backups"
    
    success "Dossiers créés avec succès."
}

# Fonction pour fixer les permissions des fichiers
fix_permissions() {
    info "Fixing des permissions des fichiers..."
    
    # Rendre les scripts exécutables
    chmod +x "${PROJECT_DIR}/nms-manager.sh"
    chmod +x "${PROJECT_DIR}/scripts/"*.sh
    
    # Fixer les permissions des dossiers de données
    if command -v sudo &> /dev/null; then
        sudo chown -R 1000:1000 "${PROJECT_DIR}/data/elasticsearch"
        sudo chown -R 472:472 "${PROJECT_DIR}/data/grafana" "${PROJECT_DIR}/config/grafana"
        sudo chmod -R 777 "${PROJECT_DIR}/data/prometheus"
    else
        chown -R 1000:1000 "${PROJECT_DIR}/data/elasticsearch"
        chown -R 472:472 "${PROJECT_DIR}/data/grafana" "${PROJECT_DIR}/config/grafana"
        chmod -R 777 "${PROJECT_DIR}/data/prometheus"
    fi
    
    success "Permissions fixées avec succès."
}
