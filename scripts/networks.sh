#!/bin/bash

# Fonctions pour la gestion des réseaux Docker

# Obtenir le chemin du script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Importer les fonctions communes
source "${SCRIPT_DIR}/common.sh"

# Créer les réseaux Docker nécessaires
create_networks() {
    title "Création des réseaux Docker"
    
    info "Création du réseau nms-backend (192.168.10.0/24)..."
    docker network inspect nms-backend >/dev/null 2>&1 || \
        docker network create --subnet=192.168.10.0/24 nms-backend
    
    info "Création du réseau nms-frontend (192.168.20.0/24)..."
    docker network inspect nms-frontend >/dev/null 2>&1 || \
        docker network create --subnet=192.168.20.0/24 nms-frontend
    
    info "Création du réseau nms-monitoring (192.168.30.0/24)..."
    docker network inspect nms-monitoring >/dev/null 2>&1 || \
        docker network create --subnet=192.168.30.0/24 nms-monitoring
    
    info "Création du réseau nms-gns3 (192.168.40.0/24)..."
    docker network inspect nms-gns3 >/dev/null 2>&1 || \
        docker network create --subnet=192.168.40.0/24 nms-gns3
    
    success "Réseaux Docker créés avec succès."
}

# Afficher les informations des réseaux
show_networks() {
    title "Réseaux Docker NMS"
    
    for network in nms-backend nms-frontend nms-monitoring nms-gns3; do
        echo -e "${CYAN}Réseau ${network}:${NC}"
        if docker network inspect $network >/dev/null 2>&1; then
            docker network inspect $network -f '{{range .IPAM.Config}}{{.Subnet}}{{end}}    {{.Name}}'
            docker network inspect $network -f '{{range .Containers}}{{.Name}}: {{.IPv4Address}}{{println}}{{end}}' | sort
            echo ""
        else
            warning "Le réseau $network n'existe pas."
            echo ""
        fi
    done
}

# Afficher les IP des services
show_services_ips() {
    title "Adresses IP des services"
    
    echo "Réseau nms-backend (192.168.10.0/24):"
    docker network inspect nms-backend -f '{{range .Containers}}{{.Name}}: {{.IPv4Address}}{{println}}{{end}}' 2>/dev/null | sort || warning "Réseau non disponible"
    
    echo -e "\nRéseau nms-frontend (192.168.20.0/24):"
    docker network inspect nms-frontend -f '{{range .Containers}}{{.Name}}: {{.IPv4Address}}{{println}}{{end}}' 2>/dev/null | sort || warning "Réseau non disponible"
    
    echo -e "\nRéseau nms-monitoring (192.168.30.0/24):"
    docker network inspect nms-monitoring -f '{{range .Containers}}{{.Name}}: {{.IPv4Address}}{{println}}{{end}}' 2>/dev/null | sort || warning "Réseau non disponible"
    
    echo -e "\nRéseau nms-gns3 (192.168.40.0/24):"
    docker network inspect nms-gns3 -f '{{range .Containers}}{{.Name}}: {{.IPv4Address}}{{println}}{{end}}' 2>/dev/null | sort || warning "Réseau non disponible"
}

# Nettoyer les réseaux non utilisés
clean_networks() {
    title "Nettoyage des réseaux Docker non utilisés"
    
    docker network prune -f
    
    success "Réseaux nettoyés."
}

# Diagnostic de connectivité réseau
diagnose_connectivity() {
    title "Diagnostic de connectivité"
    
    # Vérifier si le conteneur Django est en cours d'exécution
    if ! docker ps --filter "name=nms-django" --format "{{.Names}}" | grep -q "nms-django"; then
        warning "Le conteneur nms-django n'est pas en cours d'exécution. Les tests de connectivité ne peuvent pas être effectués."
        return
    fi
    
    echo "Vérification de la connectivité avec les services..."
    
    services=(
        "postgres:5432:PostgreSQL"
        "redis:6379:Redis"
        "elasticsearch:9200:Elasticsearch"
        "kibana:5601:Kibana"
        "netdata:19999:Netdata"
        "ntopng:3000:ntopng"
        "traffic-control:8003:Traffic Control"
    )
    
    for service in "${services[@]}"; do
        IFS=':' read -r host port name <<< "$service"
        
        # Tester la connectivité au service en utilisant le conteneur Django
        if [[ "$port" == "5432" || "$port" == "6379" ]]; then
            # Test TCP pour PostgreSQL et Redis
            if docker exec nms-django nc -z -w 5 $host $port >/dev/null 2>&1; then
                success "Connexion TCP établie avec $name ($host:$port)"
            else
                error "Impossible de se connecter à $name ($host:$port) via TCP"
            fi
        else
            # Test HTTP pour les autres services
            if docker exec nms-django curl -s -o /dev/null -w "%{http_code}" --connect-timeout 5 "http://$host:$port" >/dev/null 2>&1; then
                success "Connexion HTTP établie avec $name ($host:$port)"
            else
                error "Impossible de se connecter à $name ($host:$port) via HTTP"
            fi
        fi
    done
}
