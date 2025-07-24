#!/bin/bash

# Fonctions pour la gestion de la sécurité du système NMS

# Obtenir le chemin du script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Importer les fonctions communes
source "${SCRIPT_DIR}/common.sh"

# Vérifier les permissions des fichiers
check_file_permissions() {
    title "Vérification des permissions des fichiers"
    
    # Vérifier les scripts
    find "${PROJECT_DIR}/scripts" -name "*.sh" -not -perm -u=x -print | while read file; do
        warning "Le script $file n'est pas exécutable"
        chmod +x "$file"
        success "Permission corrigée: $file"
    done
    
    # Vérifier les fichiers sensibles
    find "${PROJECT_DIR}/config" -type f -name "*.key" -not -perm 0600 -print | while read file; do
        warning "Le fichier clé $file a des permissions incorrectes"
        chmod 0600 "$file"
        success "Permission corrigée: $file"
    done
    
    # Vérifier les répertoires de logs
    find "${PROJECT_DIR}/data" -type d -name "*log*" -not -perm -u=rwx,g=rx,o= -print | while read dir; do
        warning "Le répertoire de logs $dir a des permissions incorrectes"
        chmod 750 "$dir"
        success "Permission corrigée: $dir"
    done
    
    success "Vérification des permissions terminée"
}

# Vérifier Suricata
check_suricata() {
    title "Vérification de Suricata"
    
    # Vérifier si Suricata est en cours d'exécution
    if ! docker ps --filter "name=nms-suricata" --format "{{.Names}}" | grep -q "nms-suricata"; then
        error "Le conteneur nms-suricata n'est pas en cours d'exécution."
        return 1
    fi
    
    # Vérifier la version de Suricata
    info "Version de Suricata:"
    docker exec nms-suricata suricata --version
    
    # Vérifier les règles Suricata
    info "Règles Suricata chargées:"
    docker exec nms-suricata ls -la /etc/suricata/rules/
    
    # Vérifier les alertes récentes
    info "Alertes Suricata récentes:"
    docker exec nms-suricata tail -n 20 /var/log/suricata/fast.log 2>/dev/null || echo "Aucun fichier de log trouvé"
    
    success "Vérification de Suricata terminée"
}

# Vérifier Fail2ban
check_fail2ban() {
    title "Vérification de Fail2ban"
    
    # Vérifier si Fail2ban est en cours d'exécution
    if ! docker ps --filter "name=nms-fail2ban" --format "{{.Names}}" | grep -q "nms-fail2ban"; then
        error "Le conteneur nms-fail2ban n'est pas en cours d'exécution."
        return 1
    fi
    
    # Vérifier le statut de Fail2ban
    info "Statut de Fail2ban:"
    docker exec nms-fail2ban fail2ban-client status
    
    # Vérifier les jails actives
    info "Jails Fail2ban actives:"
    docker exec nms-fail2ban fail2ban-client status | grep "Jail list" | sed 's/`- Jail list://g' | tr ',' '\n' | while read jail; do
        if [ ! -z "$jail" ]; then
            echo -n "Jail $jail: "
            docker exec nms-fail2ban fail2ban-client status $jail | grep "Currently banned:" | sed 's/   |- Currently banned://g'
        fi
    done
    
    success "Vérification de Fail2ban terminée"
}

# Mettre à jour les règles Suricata
update_suricata_rules() {
    title "Mise à jour des règles Suricata"
    
    # Vérifier si Suricata est en cours d'exécution
    if ! docker ps --filter "name=nms-suricata" --format "{{.Names}}" | grep -q "nms-suricata"; then
        error "Le conteneur nms-suricata n'est pas en cours d'exécution."
        return 1
    fi
    
    info "Mise à jour des règles Suricata..."
    docker exec nms-suricata suricata-update
    
    # Recharger Suricata pour appliquer les nouvelles règles
    info "Rechargement de Suricata..."
    docker exec nms-suricata kill -USR2 $(docker exec nms-suricata pidof suricata)
    
    success "Règles Suricata mises à jour et appliquées"
}

# Ajouter une règle personnalisée à Suricata
add_custom_suricata_rule() {
    local rule="$1"
    
    if [ -z "$rule" ]; then
        error "Veuillez spécifier une règle Suricata à ajouter"
        echo "Exemple: ./nms-manager.sh add-suricata-rule \"alert http any any -> any any (msg:\"Test Rule\"; content:\"test\"; sid:1000001; rev:1;)\""
        return 1
    fi
    
    title "Ajout d'une règle Suricata personnalisée"
    
    # Vérifier si Suricata est en cours d'exécution
    if ! docker ps --filter "name=nms-suricata" --format "{{.Names}}" | grep -q "nms-suricata"; then
        error "Le conteneur nms-suricata n'est pas en cours d'exécution."
        return 1
    fi
    
    # Ajouter la règle à local.rules
    info "Ajout de la règle à local.rules..."
    echo "$rule" | docker exec -i nms-suricata tee -a /etc/suricata/rules/local.rules
    
    # Recharger Suricata pour appliquer la nouvelle règle
    info "Rechargement de Suricata..."
    docker exec nms-suricata kill -USR2 $(docker exec nms-suricata pidof suricata)
    
    success "Règle personnalisée ajoutée et appliquée"
}

# Vérifier l'intégrité du système
check_system_integrity() {
    title "Vérification de l'intégrité du système"
    
    info "Vérification des modifications des fichiers de configuration..."
    find "${PROJECT_DIR}/config" -type f -name "*.yml" -o -name "*.yaml" -o -name "*.conf" -o -name "*.cfg" | while read file; do
        if [ -f "${file}.orig" ]; then
            if ! diff -q "$file" "${file}.orig" >/dev/null; then
                warning "Le fichier $file a été modifié depuis sa version originale"
            fi
        else
            # Créer une copie originale si elle n'existe pas
            cp "$file" "${file}.orig"
        fi
    done
    
    info "Vérification des images Docker..."
    docker images --format "{{.Repository}}:{{.Tag}}" | grep "nms-" | while read image; do
        # Vérifier le digest de l'image
        docker inspect --format='{{.RepoDigests}}' "$image"
    done
    
    success "Vérification de l'intégrité terminée"
}

# Liste des bannissements actifs
list_active_bans() {
    title "Bannissements actifs"
    
    # Vérifier si Fail2ban est en cours d'exécution
    if ! docker ps --filter "name=nms-fail2ban" --format "{{.Names}}" | grep -q "nms-fail2ban"; then
        error "Le conteneur nms-fail2ban n'est pas en cours d'exécution."
        return 1
    fi
    
    info "Bannissements Fail2ban:"
    docker exec nms-fail2ban fail2ban-client status | grep "Jail list" | sed 's/`- Jail list://g' | tr ',' '\n' | while read jail; do
        if [ ! -z "$jail" ]; then
            echo -e "${YELLOW}Jail $jail:${NC}"
            docker exec nms-fail2ban fail2ban-client status $jail
            echo ""
        fi
    done
    
    # Vérifier également les bannissements iptables
    info "Règles iptables (bannissements):"
    docker exec nms-fail2ban iptables -L -n | grep DROP
    
    success "Liste des bannissements terminée"
}
