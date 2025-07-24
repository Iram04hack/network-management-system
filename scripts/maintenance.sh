#!/bin/bash

# Fonctions pour la maintenance du système NMS

# Obtenir le chemin du script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Importer les fonctions communes
source "${SCRIPT_DIR}/common.sh"

# Sauvegarde du système
backup_system() {
    title "Sauvegarde du système NMS"
    
    local backup_dir="${PROJECT_DIR}/backups/$(date +%Y%m%d_%H%M%S)"
    mkdir -p $backup_dir
    
    info "Sauvegarde des volumes de données..."
    
    # PostgreSQL
    info "Sauvegarde de PostgreSQL..."
    docker exec nms-postgres pg_dump -U ${POSTGRES_USER:-nms_user} ${POSTGRES_DB:-nms_db} > $backup_dir/postgres_dump.sql 2>/dev/null
    
    if [ $? -eq 0 ]; then
        success "Sauvegarde PostgreSQL réussie"
    else
        error "Échec de la sauvegarde PostgreSQL"
    fi
    
    # Elasticsearch (optionnel)
    info "Sauvegarde des configurations..."
    tar -czf $backup_dir/config_backup.tar.gz -C ${PROJECT_DIR} config/
    
    # Django
    info "Sauvegarde du backend Django..."
    tar -czf $backup_dir/django_backup.tar.gz -C ${PROJECT_DIR} web-interface/django_backend/
    
    success "Sauvegarde terminée: $backup_dir"
    
    # Afficher les fichiers sauvegardés
    ls -lh $backup_dir
}

# Restaurer une sauvegarde
restore_backup() {
    local backup_dir="$1"
    
    if [ -z "$backup_dir" ]; then
        error "Veuillez spécifier un répertoire de sauvegarde à restaurer"
        return 1
    fi
    
    if [ ! -d "$backup_dir" ]; then
        error "Le répertoire de sauvegarde $backup_dir n'existe pas"
        return 1
    fi
    
    title "Restauration de la sauvegarde: $backup_dir"
    
    # Arrêter les services
    source "${SCRIPT_DIR}/services.sh"
    stop_all_services
    
    # Restaurer PostgreSQL
    if [ -f "$backup_dir/postgres_dump.sql" ]; then
        info "Restauration de la base de données PostgreSQL..."
        
        # Démarrer uniquement PostgreSQL
        docker_compose_command "$COMPOSE_MAIN" "up -d postgres"
        sleep 10  # Attendre que PostgreSQL soit prêt
        
        # Restaurer la sauvegarde
        cat "$backup_dir/postgres_dump.sql" | docker exec -i nms-postgres psql -U ${POSTGRES_USER:-nms_user} ${POSTGRES_DB:-nms_db}
        
        if [ $? -eq 0 ]; then
            success "Restauration PostgreSQL réussie"
        else
            error "Échec de la restauration PostgreSQL"
        fi
        
        # Arrêter PostgreSQL
        docker_compose_command "$COMPOSE_MAIN" "stop postgres"
    fi
    
    # Restaurer les configurations
    if [ -f "$backup_dir/config_backup.tar.gz" ]; then
        info "Restauration des configurations..."
        tar -xzf "$backup_dir/config_backup.tar.gz" -C ${PROJECT_DIR}
        
        if [ $? -eq 0 ]; then
            success "Restauration des configurations réussie"
        else
            error "Échec de la restauration des configurations"
        fi
    fi
    
    # Restaurer le backend Django
    if [ -f "$backup_dir/django_backup.tar.gz" ]; then
        info "Restauration du backend Django..."
        tar -xzf "$backup_dir/django_backup.tar.gz" -C ${PROJECT_DIR}
        
        if [ $? -eq 0 ]; then
            success "Restauration du backend Django réussie"
        else
            error "Échec de la restauration du backend Django"
        fi
    fi
    
    # Redémarrer les services
    info "Redémarrage des services..."
    start_all_services
    
    success "Restauration terminée"
}

# Mettre à jour les images Docker
update_docker_images() {
    title "Mise à jour des images Docker"
    
    info "Téléchargement des nouvelles images..."
    docker_compose_command "$COMPOSE_MAIN" "pull"
    docker_compose_command "$COMPOSE_SECURITY" "pull"
    docker_compose_command "$COMPOSE_MONITORING" "pull"
    docker_compose_command "$COMPOSE_TRAFFIC" "pull"
    
    info "Reconstruction des images personnalisées..."
    docker_compose_command "$COMPOSE_MAIN" "build"
    docker_compose_command "$COMPOSE_SECURITY" "build"
    docker_compose_command "$COMPOSE_MONITORING" "build"
    docker_compose_command "$COMPOSE_TRAFFIC" "build"
    
    success "Images Docker mises à jour"
    
    info "Pour appliquer les mises à jour, redémarrez les services avec: ./nms-manager.sh restart"
}

# Nettoyer les ressources Docker non utilisées
clean_docker_system() {
    title "Nettoyage du système Docker"
    
    info "Suppression des conteneurs arrêtés..."
    docker container prune -f
    
    info "Suppression des images non utilisées..."
    docker image prune -f
    
    info "Suppression des volumes non utilisés..."
    docker volume prune -f
    
    info "Suppression des réseaux non utilisés..."
    docker network prune -f
    
    success "Nettoyage du système Docker terminé"
}

# Afficher les informations système
show_system_info() {
    title "Informations système NMS"
    
    echo -e "${CYAN}Version Docker:${NC}"
    docker --version
    
    echo -e "\n${CYAN}Version Docker Compose:${NC}"
    docker compose version
    
    echo -e "\n${CYAN}Espace disque:${NC}"
    df -h / | grep -v "Filesystem"
    
    echo -e "\n${CYAN}Mémoire:${NC}"
    free -h
    
    echo -e "\n${CYAN}Utilisation Docker:${NC}"
    docker system df
    
    echo -e "\n${CYAN}Images Docker:${NC}"
    docker images | grep "nms-"
}
