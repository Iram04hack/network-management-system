#!/bin/bash
#
# NMS Manager - Script principal pour gérer le Système de Gestion Réseau (NMS)
# Version: 1.3.0

# Obtenir le chemin du script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Importer les fonctions communes
source "${SCRIPT_DIR}/scripts/common.sh"

# Afficher le logo
show_logo() {
    echo -e "${BLUE}"
    echo "  _   _ __  __ ___    __  __                                   "
    echo " | \ | |  \/  / __|  |  \/  |__ _ _ _  __ _ __ _ ___ _ _      "
    echo " |  \| | |\/| \__ \  | |\/| / _\` | ' \/ _\` / _\` / -_) '_|  "
    echo " |_|\__|_|  |_|___/  |_|  |_\__,_|_||_\__,_\__, \___|_|       "
    echo "                                           |___/               "
    echo -e "${NC}"
}

# Fonctions pour gérer le frontend React
start_frontend() {
    title "Démarrage du frontend React"
    
    local FRONTEND_DIR="${SCRIPT_DIR}/web-interface/react_frontend"
    local FRONTEND_PID_FILE="${SCRIPT_DIR}/frontend.pid"
    
    # Vérifier si le frontend est déjà en cours d'exécution
    if [ -f "$FRONTEND_PID_FILE" ]; then
        local pid=$(cat "$FRONTEND_PID_FILE")
        if kill -0 "$pid" 2>/dev/null; then
            success "Frontend React déjà en cours d'exécution (PID: $pid)"
            info "Accessible sur: http://localhost:5173/"
            return 0
        else
            rm -f "$FRONTEND_PID_FILE"
        fi
    fi
    
    # Vérifier si le répertoire frontend existe
    if [ ! -d "$FRONTEND_DIR" ]; then
        error "Répertoire frontend introuvable: $FRONTEND_DIR"
        return 1
    fi
    
    # Vérifier si Node.js est installé
    if ! command -v node &> /dev/null; then
        error "Node.js n'est pas installé. Veuillez l'installer d'abord."
        return 1
    fi
    
    # Vérifier si npm est installé
    if ! command -v npm &> /dev/null; then
        error "npm n'est pas installé. Veuillez l'installer d'abord."
        return 1
    fi
    
    # Aller dans le répertoire frontend
    cd "$FRONTEND_DIR" || { error "Impossible d'accéder au répertoire frontend"; return 1; }
    
    # Vérifier si les dépendances sont installées
    if [ ! -d "node_modules" ]; then
        info "Installation des dépendances..."
        npm install || { error "Échec de l'installation des dépendances"; return 1; }
    fi
    
    # Démarrer le serveur de développement en arrière-plan
    info "Démarrage du serveur de développement..."
    nohup npm run dev > "${SCRIPT_DIR}/logs/frontend.log" 2>&1 &
    local frontend_pid=$!
    
    # Sauvegarder le PID
    echo $frontend_pid > "$FRONTEND_PID_FILE"
    
    # Attendre un peu pour vérifier que le serveur démarre
    sleep 3
    
    if kill -0 "$frontend_pid" 2>/dev/null; then
        success "Frontend React démarré avec succès (PID: $frontend_pid)"
        info "Accessible sur: http://localhost:5173/"
        info "Logs disponibles dans: ${SCRIPT_DIR}/logs/frontend.log"
    else
        error "Échec du démarrage du frontend React"
        rm -f "$FRONTEND_PID_FILE"
        return 1
    fi
}

stop_frontend() {
    title "Arrêt du frontend React"
    
    local FRONTEND_PID_FILE="${SCRIPT_DIR}/frontend.pid"
    
    if [ ! -f "$FRONTEND_PID_FILE" ]; then
        warning "Aucun processus frontend en cours d'exécution"
        return 0
    fi
    
    local pid=$(cat "$FRONTEND_PID_FILE")
    
    if kill -0 "$pid" 2>/dev/null; then
        info "Arrêt du processus frontend (PID: $pid)..."
        kill "$pid"
        
        # Attendre que le processus se termine
        local count=0
        while kill -0 "$pid" 2>/dev/null && [ $count -lt 10 ]; do
            sleep 1
            count=$((count + 1))
        done
        
        if kill -0 "$pid" 2>/dev/null; then
            warning "Arrêt forcé du processus frontend..."
            kill -9 "$pid"
        fi
        
        success "Frontend React arrêté"
    else
        warning "Processus frontend introuvable (PID: $pid)"
    fi
    
    rm -f "$FRONTEND_PID_FILE"
}

# Fonction pour démarrer Django avec le service GNS3 intégré
start_django_gns3() {
    title "Démarrage de Django avec le service GNS3 intégré"
    
    local DJANGO_DIR="${SCRIPT_DIR}/web-interface/django__backend"
    local DJANGO_PID_FILE="${SCRIPT_DIR}/django-gns3.pid"
    
    # Vérifier si Django+GNS3 est déjà en cours d'exécution
    if [ -f "$DJANGO_PID_FILE" ]; then
        local pid=$(cat "$DJANGO_PID_FILE")
        if kill -0 "$pid" 2>/dev/null; then
            success "Django+GNS3 déjà en cours d'exécution (PID: $pid)"
            info "Documentation Swagger: http://localhost:8000/swagger/"
            info "API GNS3 Central: http://localhost:8000/api/common/"
            return 0
        else
            rm -f "$DJANGO_PID_FILE"
        fi
    fi
    
    # Vérifier si le répertoire Django existe
    if [ ! -d "$DJANGO_DIR" ]; then
        error "Répertoire Django introuvable: $DJANGO_DIR"
        return 1
    fi
    
    # Vérifier si l'environnement virtuel existe
    if [ ! -d "$DJANGO_DIR/nms_env" ]; then
        error "Environnement virtuel introuvable: $DJANGO_DIR/nms_env"
        return 1
    fi
    
    # Aller dans le répertoire Django
    cd "$DJANGO_DIR" || { error "Impossible d'accéder au répertoire Django"; return 1; }
    
    # Démarrer Django avec GNS3 en arrière-plan
    info "Démarrage de Django avec le service GNS3 intégré..."
    nohup bash -c "source nms_env/bin/activate && python manage.py start_django_with_gns3 --port 8000 --host 0.0.0.0" > "${SCRIPT_DIR}/logs/django-gns3.log" 2>&1 &
    local django_pid=$!
    
    # Sauvegarder le PID
    echo $django_pid > "$DJANGO_PID_FILE"
    
    # Attendre un peu pour vérifier que le serveur démarre
    sleep 5
    
    if kill -0 "$django_pid" 2>/dev/null; then
        success "Django+GNS3 démarré avec succès (PID: $django_pid)"
        info "Documentation Swagger: http://localhost:8000/swagger/"
        info "API Root: http://localhost:8000/api/"
        info "Service Central GNS3: http://localhost:8000/api/common/"
        info "WebSocket GNS3: ws://localhost:8000/ws/gns3/events/"
        info "Interface Admin: http://localhost:8000/admin/"
        info "Logs disponibles dans: ${SCRIPT_DIR}/logs/django-gns3.log"
    else
        error "Échec du démarrage de Django+GNS3"
        rm -f "$DJANGO_PID_FILE"
        return 1
    fi
}

# Fonction pour arrêter Django avec GNS3
stop_django_gns3() {
    title "Arrêt de Django avec le service GNS3"
    
    local DJANGO_PID_FILE="${SCRIPT_DIR}/django-gns3.pid"
    
    if [ ! -f "$DJANGO_PID_FILE" ]; then
        warning "Aucun processus Django+GNS3 en cours d'exécution"
        return 0
    fi
    
    local pid=$(cat "$DJANGO_PID_FILE")
    
    if kill -0 "$pid" 2>/dev/null; then
        info "Arrêt du processus Django+GNS3 (PID: $pid)..."
        kill "$pid"
        
        # Attendre que le processus se termine
        local count=0
        while kill -0 "$pid" 2>/dev/null && [ $count -lt 15 ]; do
            sleep 1
            count=$((count + 1))
        done
        
        if kill -0 "$pid" 2>/dev/null; then
            warning "Arrêt forcé du processus Django+GNS3..."
            kill -9 "$pid"
        fi
        
        success "Django+GNS3 arrêté"
    else
        warning "Processus Django+GNS3 introuvable (PID: $pid)"
    fi
    
    rm -f "$DJANGO_PID_FILE"
}

# Fonction pour afficher le statut de Django+GNS3
status_django_gns3() {
    local DJANGO_PID_FILE="${SCRIPT_DIR}/django-gns3.pid"
    
    if [ -f "$DJANGO_PID_FILE" ]; then
        local pid=$(cat "$DJANGO_PID_FILE")
        if kill -0 "$pid" 2>/dev/null; then
            echo -e "${GREEN}Django+GNS3: RUNNING${NC} (PID: $pid)"
            echo -e "  Documentation Swagger: http://localhost:8000/swagger/"
            echo -e "  API GNS3 Central: http://localhost:8000/api/common/"
            echo -e "  WebSocket GNS3: ws://localhost:8000/ws/gns3/events/"
        else
            echo -e "${RED}Django+GNS3: STOPPED${NC} (PID file exists but process not running)"
            rm -f "$DJANGO_PID_FILE"
        fi
    else
        echo -e "${RED}Django+GNS3: STOPPED${NC}"
    fi
}

status_frontend() {
    # Obtenir le chemin absolu du script
    local CURRENT_SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
    local FRONTEND_PID_FILE="${CURRENT_SCRIPT_DIR}/frontend.pid"

    if [ -f "$FRONTEND_PID_FILE" ]; then
        local pid=$(cat "$FRONTEND_PID_FILE")
        if kill -0 "$pid" 2>/dev/null; then
            echo -e "${GREEN}Frontend React: RUNNING${NC} (PID: $pid)"
            echo -e "  URL: http://localhost:5173/"
        else
            echo -e "${RED}Frontend React: STOPPED${NC} (PID file exists but process not running)"
            rm -f "$FRONTEND_PID_FILE"
        fi
    else
        echo -e "${RED}Frontend React: STOPPED${NC}"
    fi
}

# Fonction d'aide
show_help() {
    show_logo
    echo -e "${GREEN}Système de Gestion Réseau (NMS) - Script de gestion${NC}"
    echo ""
    echo "Usage: $0 [commande] [options]"
    echo ""
    echo "Commandes de base:"
    echo "  init                    - Initialise l'environnement (réseaux Docker, dossiers, etc.)"
    echo "  start [all|base|security|monitoring|traffic|frontend] - Démarre les services spécifiés ou tous"
    echo "  start-django-gns3       - Démarre Django avec le service GNS3 intégré (port 8000)"
    echo "  stop-django-gns3        - Arrête Django avec le service GNS3"
    echo "  start-https             - Démarre Django avec HTTPS directement sur le port 8000"
    echo "  standalone-django       - Démarre Django en mode standalone avec HTTPS"
    echo "  stop-https              - Arrête Django en mode HTTPS"
    echo "  generate-ssl            - Génère les certificats SSL pour HTTPS"
    echo "  stop [all|base|security|monitoring|traffic|frontend]  - Arrête les services spécifiés ou tous"
    echo "  restart                 - Redémarre tous les services"
    echo "  status                  - Affiche l'état des services"
    echo "  logs [service] [follow] - Affiche les logs d'un service (optionnel: suivi en temps réel)"
    echo ""
    echo "Commandes de service:"
    echo "  start-service [service] - Démarre un service spécifique"
    echo "  stop-service [service]  - Arrête un service spécifique"
    echo "  restart-service [service] - Redémarre un service spécifique"
    echo "  status-service [service] - Affiche l'état d'un service spécifique"
    echo ""
    echo "Commandes avancées:"
    echo "  backup                  - Crée une sauvegarde du système"
    echo "  health                  - Vérification de la santé des services"
    echo "  check-restart           - Vérifie et redémarre les services arrêtés"
    echo "  menu                    - Affiche le menu interactif"
    echo "  help                    - Affiche cette aide"
    echo ""
    echo "Exemples:"
    echo "  $0 init                 # Initialise l'environnement"
    echo "  $0 start                # Démarre tous les services"
    echo "  $0 start-django-gns3    # Démarre Django avec GNS3 (port 8000)"
    echo "  $0 start frontend       # Démarre uniquement le frontend React"
    echo "  $0 logs django follow   # Suit les logs du service Django"
}

# Fonction pour le menu interactif
interactive_menu() {
    # Sauvegarde le chemin du script
    local MENU_SCRIPT_DIR="$SCRIPT_DIR"
    
    while true; do
        clear
        show_logo
        echo -e "${CYAN}SYSTÈME DE GESTION RÉSEAU - MENU PRINCIPAL${NC}"
        echo "------------------------------------------------"
        echo "1) Démarrer des services"
        echo "2) Arrêter des services"
        echo "3) Redémarrer tous les services"
        echo "4) Afficher l'état des services"
        echo "5) Afficher les logs"
        echo "6) Vérifier la santé des services"
        echo "7) Sauvegarde et restauration"
        echo "8) Maintenance du système"
        echo "9) Monitoring et diagnostic"
        echo "10) Sécurité"
        echo "11) Gestion des réseaux"
        echo "12) Gestion des configurations"
        echo "13) Démarrer Django avec HTTPS direct"
        echo "14) Démarrer Django en mode standalone avec HTTPS"
        echo "15) Démarrer Django avec service GNS3 intégré"
        echo "16) Arrêter Django HTTPS"
        echo "0) Quitter"
        echo "------------------------------------------------"
        read -p "Votre choix: " choice
        
        # Restaurer SCRIPT_DIR pour chaque choix de menu
        SCRIPT_DIR="$MENU_SCRIPT_DIR"
        
        case $choice in
            1)
                clear
                echo -e "${CYAN}Démarrage des services${NC}"
                echo "1) Tous les services"
                echo "2) Services de base (PostgreSQL, Redis, Django)"
                echo "3) Services de sécurité (Suricata, Elasticsearch, Kibana, Fail2ban)"
                echo "4) Services de monitoring (Netdata, ntopng, HAProxy)"
                echo "5) Service Traffic Control (QoS)"
                echo "6) Frontend React"
                echo "7) Service spécifique"
                echo "0) Retour"
                read -p "Votre choix: " start_choice
                
                case $start_choice in
                    1) source "${SCRIPT_DIR}/scripts/services.sh" && start_all_services ;;
                    2) source "${SCRIPT_DIR}/scripts/services.sh" && start_services "base" ;;
                    3) source "${SCRIPT_DIR}/scripts/services.sh" && start_services "security" ;;
                    4) source "${SCRIPT_DIR}/scripts/services.sh" && start_services "monitoring" ;;
                    5) source "${SCRIPT_DIR}/scripts/services.sh" && start_services "traffic" ;;
                    6) start_frontend ;;
                    7)
                        read -p "Nom du service (ex: django, postgres, elasticsearch): " service_name
                        # Ajouter une option pour HTTPS si c'est Django
                        if [ "$service_name" = "django" ]; then
                            read -p "Utiliser HTTPS? (o/n): " use_https
                            if [ "$use_https" = "o" ] || [ "$use_https" = "O" ]; then
                                source "${SCRIPT_DIR}/scripts/services.sh" && start_service "$service_name" "true"
                            else
                                source "${SCRIPT_DIR}/scripts/services.sh" && start_service "$service_name"
                            fi
                        else
                            source "${SCRIPT_DIR}/scripts/services.sh" && start_service "$service_name"
                        fi
                        ;;
                    0) continue ;;
                    *) error "Option invalide" ;;
                esac
                read -p "Appuyez sur Entrée pour continuer..."
                ;;
            2)
                clear
                echo -e "${CYAN}Arrêt des services${NC}"
                echo "1) Tous les services"
                echo "2) Services de base (PostgreSQL, Redis, Django)"
                echo "3) Services de sécurité (Suricata, Elasticsearch, Kibana, Fail2ban)"
                echo "4) Services de monitoring (Netdata, ntopng, HAProxy)"
                echo "5) Service Traffic Control (QoS)"
                echo "6) Frontend React"
                echo "7) Service spécifique"
                echo "0) Retour"
                read -p "Votre choix: " stop_choice
                
                case $stop_choice in
                    1) source "${SCRIPT_DIR}/scripts/services.sh" && stop_all_services ;;
                    2) source "${SCRIPT_DIR}/scripts/services.sh" && stop_services "base" ;;
                    3) source "${SCRIPT_DIR}/scripts/services.sh" && stop_services "security" ;;
                    4) source "${SCRIPT_DIR}/scripts/services.sh" && stop_services "monitoring" ;;
                    5) source "${SCRIPT_DIR}/scripts/services.sh" && stop_services "traffic" ;;
                    6) stop_frontend ;;
                    7)
                        read -p "Nom du service (ex: django, postgres, elasticsearch): " service_name
                        source "${SCRIPT_DIR}/scripts/services.sh" && stop_service "$service_name"
                        ;;
                    0) continue ;;
                    *) error "Option invalide" ;;
                esac
                read -p "Appuyez sur Entrée pour continuer..."
                ;;
            3)
                source "${SCRIPT_DIR}/scripts/services.sh" && restart_all_services
                read -p "Appuyez sur Entrée pour continuer..."
                ;;
            4)
                clear
                echo -e "${CYAN}Affichage de l'état des services${NC}"
                echo "1) Tous les services"
                echo "2) Service spécifique"
                echo "0) Retour"
                read -p "Votre choix: " status_choice
                
                case $status_choice in
                    1) source "${SCRIPT_DIR}/scripts/services.sh" && show_services_status ;;
                    2) 
                        read -p "Nom du service (ex: django, postgres, elasticsearch): " service_name
                        source "${SCRIPT_DIR}/scripts/services.sh" && show_service_status "$service_name"
                        ;;
                    0) continue ;;
                    *) error "Option invalide" ;;
                esac
                read -p "Appuyez sur Entrée pour continuer..."
                ;;
            5)
                clear
                echo -e "${CYAN}Affichage des logs${NC}"
                echo "1) Tous les services"
                echo "2) Service spécifique"
                echo "0) Retour"
                read -p "Votre choix: " logs_choice
                
                case $logs_choice in
                    1)
                        source "${SCRIPT_DIR}/scripts/services.sh" && show_logs ""
                        ;;
                    2)
                        read -p "Nom du service (sans préfixe nms-): " service_name
                        source "${SCRIPT_DIR}/scripts/services.sh" && show_logs "$service_name"
                        ;;
                    0)
                        continue
                        ;;
                    *)
                        error "Option invalide"
                        ;;
                esac
                read -p "Appuyez sur Entrée pour continuer..."
                ;;
            6)
                source "${SCRIPT_DIR}/scripts/monitoring.sh" && check_health
                read -p "Appuyez sur Entrée pour continuer..."
                ;;
            7)
                clear
                echo -e "${CYAN}Sauvegarde et restauration${NC}"
                echo "1) Créer une sauvegarde"
                echo "2) Restaurer une sauvegarde"
                echo "0) Retour"
                read -p "Votre choix: " backup_choice
                
                case $backup_choice in
                    1)
                        source "${SCRIPT_DIR}/scripts/maintenance.sh" && backup_system
                        ;;
                    2)
                        echo "Sauvegardes disponibles:"
                        ls -lt "${PROJECT_DIR}/backups/" | grep -v "^total" | head -10
                        read -p "Répertoire de sauvegarde à restaurer: " backup_dir
                        source "${SCRIPT_DIR}/scripts/maintenance.sh" && restore_backup "$backup_dir"
                        ;;
                    0)
                        continue
                        ;;
                    *)
                        error "Option invalide"
                        ;;
                esac
                read -p "Appuyez sur Entrée pour continuer..."
                ;;
            8)
                clear
                echo -e "${CYAN}Maintenance du système${NC}"
                echo "1) Mettre à jour les images Docker"
                echo "2) Nettoyer les ressources Docker"
                echo "3) Vérifier et redémarrer les services arrêtés"
                echo "4) Afficher les informations système"
                echo "0) Retour"
                read -p "Votre choix: " maintenance_choice
                
                case $maintenance_choice in
                    1)
                        source "${SCRIPT_DIR}/scripts/maintenance.sh" && update_docker_images
                        ;;
                    2)
                        source "${SCRIPT_DIR}/scripts/maintenance.sh" && clean_docker_system
                        ;;
                    3)
                        source "${SCRIPT_DIR}/scripts/services.sh" && check_and_restart_services
                        ;;
                    4)
                        source "${SCRIPT_DIR}/scripts/maintenance.sh" && show_system_info
                        ;;
                    0)
                        continue
                        ;;
                    *)
                        error "Option invalide"
                        ;;
                esac
                read -p "Appuyez sur Entrée pour continuer..."
                ;;
            9)
                clear
                echo -e "${CYAN}Monitoring et diagnostic${NC}"
                echo "1) Vérifier la santé des services"
                echo "2) Vérifier les ressources système"
                echo "3) Vérifier les logs pour les erreurs"
                echo "4) Vérifier la connectivité des services"
                echo "5) Générer un rapport de monitoring"
                echo "6) Monitoriser le trafic réseau"
                echo "7) Monitoriser la qualité de service"
                echo "8) Monitoriser la latence réseau"
                echo "9) Générer un rapport de performance"
                echo "0) Retour"
                read -p "Votre choix: " monitoring_choice
                
                case $monitoring_choice in
                    1)
                        source "${SCRIPT_DIR}/scripts/monitoring.sh" && check_health
                        ;;
                    2)
                        source "${SCRIPT_DIR}/scripts/monitoring.sh" && check_resources
                        ;;
                    3)
                        source "${SCRIPT_DIR}/scripts/monitoring.sh" && check_logs_for_errors
                        ;;
                    4)
                        source "${SCRIPT_DIR}/scripts/monitoring.sh" && check_service_connectivity
                        ;;
                    5)
                        source "${SCRIPT_DIR}/scripts/monitoring.sh" && generate_monitoring_report
                        ;;
                    6)
                        source "${SCRIPT_DIR}/scripts/monitoring.sh" && monitor_network_traffic
                        ;;
                    7)
                        source "${SCRIPT_DIR}/scripts/monitoring.sh" && monitor_qos
                        ;;
                    8)
                        source "${SCRIPT_DIR}/scripts/monitoring.sh" && monitor_network_latency
                        ;;
                    9)
                        source "${SCRIPT_DIR}/scripts/monitoring.sh" && generate_performance_report
                        ;;
                    0)
                        continue
                        ;;
                    *)
                        error "Option invalide"
                        ;;
                esac
                read -p "Appuyez sur Entrée pour continuer..."
                ;;
            10)
                clear
                echo -e "${CYAN}Sécurité${NC}"
                echo "1) Vérifier les permissions des fichiers"
                echo "2) Vérifier la configuration de Suricata"
                echo "3) Vérifier la configuration de Fail2ban"
                echo "4) Mettre à jour les règles de Suricata"
                echo "5) Ajouter une règle personnalisée à Suricata"
                echo "6) Lister les bans actifs"
                echo "0) Retour"
                read -p "Votre choix: " security_choice
                
                case $security_choice in
                    1)
                        source "${SCRIPT_DIR}/scripts/security.sh" && check_file_permissions
                        ;;
                    2)
                        source "${SCRIPT_DIR}/scripts/security.sh" && check_suricata
                        ;;
                    3)
                        source "${SCRIPT_DIR}/scripts/security.sh" && check_fail2ban
                        ;;
                    4)
                        source "${SCRIPT_DIR}/scripts/security.sh" && update_suricata_rules
                        ;;
                    5)
                        read -p "Nom de la règle personnalisée (ex: 1.2.3.4/32): " rule
                        source "${SCRIPT_DIR}/scripts/security.sh" && add_custom_suricata_rule "$rule"
                        ;;
                    6)
                        source "${SCRIPT_DIR}/scripts/security.sh" && list_active_bans
                        ;;
                    0)
                        continue
                        ;;
                    *)
                        error "Option invalide"
                        ;;
                esac
                read -p "Appuyez sur Entrée pour continuer..."
                ;;
            11)
                clear
                echo -e "${CYAN}Gestion des réseaux${NC}"
                echo "1) Créer les réseaux Docker"
                echo "2) Afficher les réseaux"
                echo "3) Afficher les adresses IP des services"
                echo "4) Diagnostic de connectivité"
                echo "5) Nettoyer les réseaux non utilisés"
                echo "0) Retour"
                read -p "Votre choix: " network_choice
                
                case $network_choice in
                    1)
                        source "${SCRIPT_DIR}/scripts/networks.sh" && create_networks
                        ;;
                    2)
                        source "${SCRIPT_DIR}/scripts/networks.sh" && show_networks
                        ;;
                    3)
                        source "${SCRIPT_DIR}/scripts/networks.sh" && show_services_ips
                        ;;
                    4)
                        source "${SCRIPT_DIR}/scripts/networks.sh" && diagnose_connectivity
                        ;;
                    5)
                        source "${SCRIPT_DIR}/scripts/networks.sh" && clean_networks
                        ;;
                    0)
                        continue
                        ;;
                    *)
                        error "Option invalide"
                        ;;
                esac
                read -p "Appuyez sur Entrée pour continuer..."
                ;;
            12)
                clear
                echo -e "${CYAN}Gestion des configurations${NC}"
                echo "1) Afficher la configuration d'un service"
                echo "2) Modifier la configuration d'un service"
                echo "3) Sauvegarder la configuration d'un service"
                echo "4) Restaurer la configuration d'un service"
                echo "0) Retour"
                read -p "Votre choix: " config_choice
                
                case $config_choice in
                    1)
                        read -p "Service (suricata, haproxy, netdata, fail2ban, tc): " service
                        manage_configs "show" "$service"
                        ;;
                    2)
                        read -p "Service (suricata, haproxy, netdata, fail2ban, tc): " service
                        manage_configs "edit" "$service"
                        ;;
                    3)
                        read -p "Service (suricata, haproxy, netdata, fail2ban, tc): " service
                        manage_configs "backup" "$service"
                        ;;
                    4)
                        read -p "Service (suricata, haproxy, netdata, fail2ban, tc): " service
                        ls -lt "${PROJECT_DIR}/backups/" | grep -v "^total" | grep "$service" | head -10
                        read -p "Fichier de sauvegarde: " backup_file
                        manage_configs "restore" "$service" "$backup_file"
                        ;;
                    0)
                        continue
                        ;;
                    *)
                        error "Option invalide"
                        ;;
                esac
                read -p "Appuyez sur Entrée pour continuer..."
                ;;
            13)
                source "${SCRIPT_DIR}/scripts/services.sh" && start_direct_https
                read -p "Appuyez sur Entrée pour continuer..."
                ;;
            14)
                source "${SCRIPT_DIR}/scripts/services.sh" && start_standalone_django
                read -p "Appuyez sur Entrée pour continuer..."
                ;;
            15)
                start_django_gns3
                read -p "Appuyez sur Entrée pour continuer..."
                ;;
            16)
                source "${SCRIPT_DIR}/scripts/services.sh" && stop_https
                read -p "Appuyez sur Entrée pour continuer..."
                ;;
            0)
                echo "Au revoir!"
                exit 0
                ;;
            *)
                error "Option invalide"
                read -p "Appuyez sur Entrée pour continuer..."
                ;;
        esac
    done
}

# Fonction pour gérer la configuration des services
manage_configs() {
    local action="$1"
    local service="$2"
    
    case "$action" in
        show)
            if [ -z "$service" ]; then
                error "Veuillez spécifier un service (ex: suricata, haproxy, netdata)"
                return 1
            fi
            
            echo -e "${CYAN}Configuration de $service:${NC}"
            case "$service" in
                suricata)
                    cat "${PROJECT_DIR}/config/suricata/suricata.yaml" | grep -v "^#" | grep -v "^ *$"
                    ;;
                haproxy)
                    cat "${PROJECT_DIR}/config/haproxy/haproxy.cfg" | grep -v "^#" | grep -v "^ *$"
                    ;;
                netdata)
                    cat "${PROJECT_DIR}/config/netdata/netdata.conf" | grep -v "^#" | grep -v "^ *$"
                    ;;
                fail2ban)
                    cat "${PROJECT_DIR}/config/fail2ban/jail.local" | grep -v "^#" | grep -v "^ *$"
                    ;;
                tc)
                    cat "${PROJECT_DIR}/config/tc/rules.yaml" | grep -v "^#" | grep -v "^ *$"
                    ;;
                *)
                    error "Service inconnu: $service"
                    return 1
                    ;;
            esac
            ;;
        edit)
            if [ -z "$service" ]; then
                error "Veuillez spécifier un service (ex: suricata, haproxy, netdata)"
                return 1
            fi
            
            local config_file=""
            case "$service" in
                suricata)
                    config_file="${PROJECT_DIR}/config/suricata/suricata.yaml"
                    ;;
                haproxy)
                    config_file="${PROJECT_DIR}/config/haproxy/haproxy.cfg"
                    ;;
                netdata)
                    config_file="${PROJECT_DIR}/config/netdata/netdata.conf"
                    ;;
                fail2ban)
                    config_file="${PROJECT_DIR}/config/fail2ban/jail.local"
                    ;;
                tc)
                    config_file="${PROJECT_DIR}/config/tc/rules.yaml"
                    ;;
                *)
                    error "Service inconnu: $service"
                    return 1
                    ;;
            esac
            
            if [ -n "$EDITOR" ]; then
                $EDITOR "$config_file"
            elif [ -x "$(command -v nano)" ]; then
                nano "$config_file"
            elif [ -x "$(command -v vim)" ]; then
                vim "$config_file"
            else
                error "Aucun éditeur de texte trouvé. Définissez la variable EDITOR."
                return 1
            fi
            
            info "Configuration modifiée. Voulez-vous redémarrer le service $service ? (y/n)"
            read -r restart_service
            if [ "$restart_service" = "y" ]; then
                case "$service" in
                    suricata)
                        docker_compose_command "$COMPOSE_SECURITY" "restart suricata"
                        ;;
                    haproxy)
                        docker_compose_command "$COMPOSE_MONITORING" "restart haproxy"
                        ;;
                    netdata)
                        docker_compose_command "$COMPOSE_MONITORING" "restart netdata"
                        ;;
                    fail2ban)
                        docker_compose_command "$COMPOSE_SECURITY" "restart fail2ban"
                        ;;
                    tc)
                        docker_compose_command "$COMPOSE_TRAFFIC" "restart traffic-control"
                        ;;
                esac
                success "Service $service redémarré"
            fi
            ;;
        backup)
            if [ -z "$service" ]; then
                error "Veuillez spécifier un service (ex: suricata, haproxy, netdata)"
                return 1
            fi
            
            local config_dir=""
            case "$service" in
                suricata)
                    config_dir="${PROJECT_DIR}/config/suricata"
                    ;;
                haproxy)
                    config_dir="${PROJECT_DIR}/config/haproxy"
                    ;;
                netdata)
                    config_dir="${PROJECT_DIR}/config/netdata"
                    ;;
                fail2ban)
                    config_dir="${PROJECT_DIR}/config/fail2ban"
                    ;;
                tc)
                    config_dir="${PROJECT_DIR}/config/tc"
                    ;;
                *)
                    error "Service inconnu: $service"
                    return 1
                    ;;
            esac
            
            local backup_file="${PROJECT_DIR}/backups/${service}_config_$(date +%Y%m%d_%H%M%S).tar.gz"
            tar -czf "$backup_file" -C "$(dirname "$config_dir")" "$(basename "$config_dir")"
            
            if [ $? -eq 0 ]; then
                success "Configuration sauvegardée: $backup_file"
            else
                error "Échec de la sauvegarde"
                return 1
            fi
            ;;
        restore)
            if [ -z "$service" ]; then
                error "Veuillez spécifier un service (ex: suricata, haproxy, netdata)"
                return 1
            fi
            
            if [ -z "$3" ]; then
                error "Veuillez spécifier un fichier de sauvegarde"
                return 1
            fi
            
            local backup_file="$3"
            if [ ! -f "$backup_file" ]; then
                error "Fichier de sauvegarde introuvable: $backup_file"
                return 1
            fi
            
            local config_dir=""
            case "$service" in
                suricata)
                    config_dir="${PROJECT_DIR}/config/suricata"
                    ;;
                haproxy)
                    config_dir="${PROJECT_DIR}/config/haproxy"
                    ;;
                netdata)
                    config_dir="${PROJECT_DIR}/config/netdata"
                    ;;
                fail2ban)
                    config_dir="${PROJECT_DIR}/config/fail2ban"
                    ;;
                tc)
                    config_dir="${PROJECT_DIR}/config/tc"
                    ;;
                *)
                    error "Service inconnu: $service"
                    return 1
                    ;;
            esac
            
            # Sauvegarder la configuration actuelle
            local current_backup="${PROJECT_DIR}/backups/${service}_config_current_$(date +%Y%m%d_%H%M%S).tar.gz"
            tar -czf "$current_backup" -C "$(dirname "$config_dir")" "$(basename "$config_dir")"
            
            # Restaurer la sauvegarde
            rm -rf "$config_dir"
            mkdir -p "$(dirname "$config_dir")"
            tar -xzf "$backup_file" -C "$(dirname "$config_dir")"
            
            if [ $? -eq 0 ]; then
                success "Configuration restaurée"
                
                info "Voulez-vous redémarrer le service $service ? (y/n)"
                read -r restart_service
                if [ "$restart_service" = "y" ]; then
                    case "$service" in
                        suricata)
                            docker_compose_command "$COMPOSE_SECURITY" "restart suricata"
                            ;;
                        haproxy)
                            docker_compose_command "$COMPOSE_MONITORING" "restart haproxy"
                            ;;
                        netdata)
                            docker_compose_command "$COMPOSE_MONITORING" "restart netdata"
                            ;;
                        fail2ban)
                            docker_compose_command "$COMPOSE_SECURITY" "restart fail2ban"
                            ;;
                        tc)
                            docker_compose_command "$COMPOSE_TRAFFIC" "restart traffic-control"
                            ;;
                    esac
                    success "Service $service redémarré"
                fi
            else
                error "Échec de la restauration"
                return 1
            fi
            ;;
        *)
            error "Action inconnue: $action"
            echo "Actions disponibles: show, edit, backup, restore"
            return 1
            ;;
    esac
}

# Initialiser l'environnement
init() {
    title "Initialisation de l'environnement NMS"
    
    # Vérifier l'environnement
    check_environment
    
    # Créer les réseaux Docker
    source "${SCRIPT_DIR}/scripts/networks.sh" && create_networks
    
    # Créer les dossiers nécessaires
    create_directories
    
    # Créer le dossier logs pour le frontend
    mkdir -p "${SCRIPT_DIR}/logs"
    
    # Fixer les permissions des scripts
    fix_permissions
    
    success "Environnement NMS initialisé avec succès."
    
    info "Vous pouvez maintenant démarrer les services avec: ./nms-manager.sh start"
}

# Rendre les scripts exécutables
chmod +x "${SCRIPT_DIR}/scripts/"*.sh

# Traiter les arguments de la ligne de commande
if [ $# -eq 0 ]; then
    # Aucun argument, afficher le menu interactif
    interactive_menu
    exit 0
fi

# Traiter les commandes
case "$1" in
    init)
        init
        ;;
    start)
        if [ "$2" = "all" ] || [ -z "$2" ]; then
            source "${SCRIPT_DIR}/scripts/services.sh" && start_all_services
        elif [ "$2" = "frontend" ]; then
            start_frontend
        else
            source "${SCRIPT_DIR}/scripts/services.sh" && start_services "$2"
        fi
        ;;
    start-django-gns3)
        start_django_gns3
        ;;
    stop-django-gns3)
        stop_django_gns3
        ;;
    start-https)
        source "${SCRIPT_DIR}/scripts/services.sh" && start_direct_https
        ;;
    standalone-django)
        source "${SCRIPT_DIR}/scripts/services.sh" && start_standalone_django
        ;;
    stop-https)
        source "${SCRIPT_DIR}/scripts/services.sh" && stop_https
        ;;
    stop)
        if [ "$2" = "all" ] || [ -z "$2" ]; then
            source "${SCRIPT_DIR}/scripts/services.sh" && stop_all_services
        elif [ "$2" = "frontend" ]; then
            stop_frontend
        else
            source "${SCRIPT_DIR}/scripts/services.sh" && stop_services "$2"
        fi
        ;;
    restart)
        source "${SCRIPT_DIR}/scripts/services.sh" && restart_all_services
        ;;
    status)
        source "${SCRIPT_DIR}/scripts/services.sh" && show_services_status
        echo ""
        status_frontend
        echo ""
        status_django_gns3
        ;;
    frontend-status)
        status_frontend
        ;;
    logs)
        source "${SCRIPT_DIR}/scripts/services.sh" && show_logs "$2" "$3"
        ;;
    backup)
        source "${SCRIPT_DIR}/scripts/maintenance.sh" && backup_system
        ;;
    restore)
        source "${SCRIPT_DIR}/scripts/maintenance.sh" && restore_backup "$2"
        ;;
    update)
        source "${SCRIPT_DIR}/scripts/maintenance.sh" && update_docker_images
        ;;
    clean)
        source "${SCRIPT_DIR}/scripts/maintenance.sh" && clean_docker_system
        ;;
    health)
        source "${SCRIPT_DIR}/scripts/monitoring.sh" && check_health
        ;;
    resources)
        source "${SCRIPT_DIR}/scripts/monitoring.sh" && check_resources
        ;;
    check-errors)
        source "${SCRIPT_DIR}/scripts/monitoring.sh" && check_logs_for_errors
        ;;
    connectivity)
        source "${SCRIPT_DIR}/scripts/monitoring.sh" && check_service_connectivity
        ;;
    report)
        source "${SCRIPT_DIR}/scripts/monitoring.sh" && generate_monitoring_report
        ;;
    monitor-traffic)
        source "${SCRIPT_DIR}/scripts/monitoring.sh" && monitor_network_traffic
        ;;
    monitor-qos)
        source "${SCRIPT_DIR}/scripts/monitoring.sh" && monitor_qos
        ;;
    monitor-latency)
        source "${SCRIPT_DIR}/scripts/monitoring.sh" && monitor_network_latency
        ;;
    performance-report)
        source "${SCRIPT_DIR}/scripts/monitoring.sh" && generate_performance_report
        ;;
    check-permissions)
        source "${SCRIPT_DIR}/scripts/security.sh" && check_file_permissions
        ;;
    check-suricata)
        source "${SCRIPT_DIR}/scripts/security.sh" && check_suricata
        ;;
    check-fail2ban)
        source "${SCRIPT_DIR}/scripts/security.sh" && check_fail2ban
        ;;
    update-rules)
        source "${SCRIPT_DIR}/scripts/security.sh" && update_suricata_rules
        ;;
    add-rule)
        source "${SCRIPT_DIR}/scripts/security.sh" && add_custom_suricata_rule "$2"
        ;;
    show-bans)
        source "${SCRIPT_DIR}/scripts/security.sh" && list_active_bans
        ;;
    networks)
        source "${SCRIPT_DIR}/scripts/networks.sh" && show_networks
        ;;
    show-ips)
        source "${SCRIPT_DIR}/scripts/networks.sh" && show_services_ips
        ;;
    check-restart)
        source "${SCRIPT_DIR}/scripts/services.sh" && check_and_restart_services
        ;;
    start-service)
        source "${SCRIPT_DIR}/scripts/services.sh" && start_service "$2"
        ;;
    stop-service)
        source "${SCRIPT_DIR}/scripts/services.sh" && stop_service "$2"
        ;;
    restart-service)
        source "${SCRIPT_DIR}/scripts/services.sh" && restart_service "$2"
        ;;
    status-service)
        source "${SCRIPT_DIR}/scripts/services.sh" && show_service_status "$2"
        ;;
    config-show)
        manage_configs "show" "$2"
        ;;
    config-edit)
        manage_configs "edit" "$2"
        ;;
    config-backup)
        manage_configs "backup" "$2"
        ;;
    config-restore)
        manage_configs "restore" "$2" "$3"
        ;;
    generate-ssl)
        title "Génération des certificats SSL"
        "${SCRIPT_DIR}/scripts/generate_ssl_local.sh"
        ;;
    menu)
        interactive_menu
        ;;
    help|*)
        show_help
        ;;
esac
