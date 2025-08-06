#!/bin/bash
#
# Script Helper pour les Outils d'Investigation GNS3
# =================================================
#
# Script wrapper pour simplifier l'utilisation des outils de diagnostic GNS3.
#
# Auteur: Équipe de développement NMS
# Date: 2025-07-20
#

# Couleurs pour l'affichage
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Répertoire des scripts
SCRIPT_DIR="/home/adjada/network-management-system/real_security_testing_framework"

# Fonction d'affichage du banner
show_banner() {
    echo -e "${CYAN}"
    echo "╔════════════════════════════════════════════════════════════════╗"
    echo "║                    🔧 GNS3 Investigation Helper               ║"
    echo "║                                                                ║"
    echo "║  Scripts de diagnostic et correction des problèmes GNS3       ║"
    echo "╚════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

# Fonction d'affichage du menu
show_menu() {
    echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${YELLOW}OPTIONS DISPONIBLES:${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}1.${NC} 🔍 Investigation automatique complète"
    echo -e "${GREEN}2.${NC} 🛠️  Dépannage avancé (interactif)"
    echo -e "${GREEN}3.${NC} 📊 Diagnostic de connectivité uniquement"
    echo -e "${GREEN}4.${NC} 🔧 Correction rapide de la topologie"
    echo -e "${GREEN}5.${NC} 📋 Afficher le dernier rapport d'investigation"
    echo -e "${GREEN}6.${NC} 🌉 Vérifier les bridges système"
    echo -e "${GREEN}7.${NC} 📚 Afficher la documentation"
    echo -e "${GREEN}8.${NC} 🚪 Quitter"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
}

# Fonction pour exécuter l'investigation automatique
run_investigation() {
    echo -e "${CYAN}🚀 Lancement de l'investigation automatique...${NC}"
    echo -e "${YELLOW}⏳ Cela peut prendre quelques minutes...${NC}"
    echo ""
    
    cd "$SCRIPT_DIR"
    echo "root" | sudo -S python3 investigate_gns3_issues.py
    
    local exit_code=$?
    echo ""
    
    case $exit_code in
        0)
            echo -e "${GREEN}✅ Investigation réussie ! Problèmes résolus.${NC}"
            ;;
        1)
            echo -e "${YELLOW}⚠️ Investigation partielle. Améliorations apportées.${NC}"
            echo -e "${YELLOW}💡 Considérez le dépannage avancé si nécessaire.${NC}"
            ;;
        2)
            echo -e "${RED}❌ Investigation limitée. Problèmes persistent.${NC}"
            echo -e "${RED}💡 Dépannage avancé recommandé.${NC}"
            ;;
        *)
            echo -e "${RED}❌ Erreur inattendue lors de l'investigation.${NC}"
            ;;
    esac
}

# Fonction pour le dépannage avancé
run_advanced_troubleshoot() {
    echo -e "${CYAN}🛠️ Lancement du dépannage avancé...${NC}"
    echo -e "${YELLOW}⚠️ Ces opérations peuvent affecter la topologie GNS3.${NC}"
    echo ""
    
    read -p "Continuer ? (y/N): " confirm
    if [[ $confirm =~ ^[Yy]$ ]]; then
        cd "$SCRIPT_DIR"
        echo "root" | sudo -S python3 gns3_advanced_troubleshoot.py
    else
        echo -e "${YELLOW}Operation annulée.${NC}"
    fi
}

# Fonction pour le diagnostic de connectivité
run_connectivity_diagnostic() {
    echo -e "${CYAN}📊 Diagnostic de connectivité...${NC}"
    echo ""
    
    cd "$SCRIPT_DIR"
    python3 diagnostic_connectivite.py
}

# Fonction pour la correction rapide
run_quick_fix() {
    echo -e "${CYAN}🔧 Correction rapide de la topologie...${NC}"
    echo ""
    
    cd "$SCRIPT_DIR"
    echo "root" | sudo -S python3 fix_gns3_topology.py
}

# Fonction pour afficher le dernier rapport
show_last_report() {
    echo -e "${CYAN}📋 Recherche du dernier rapport...${NC}"
    echo ""
    
    local latest_report=$(ls -t /tmp/gns3_investigation_report_*.txt 2>/dev/null | head -1)
    
    if [[ -n "$latest_report" ]]; then
        echo -e "${GREEN}📄 Dernier rapport trouvé:${NC} $latest_report"
        echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
        cat "$latest_report"
        echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
    else
        echo -e "${YELLOW}⚠️ Aucun rapport d'investigation trouvé.${NC}"
        echo -e "${YELLOW}💡 Lancez d'abord une investigation automatique.${NC}"
    fi
}

# Fonction pour vérifier les bridges
check_bridges() {
    echo -e "${CYAN}🌉 Vérification des bridges système...${NC}"
    echo ""
    
    echo -e "${YELLOW}Bridges actuels:${NC}"
    sudo brctl show
    echo ""
    
    echo -e "${YELLOW}Configuration IP des bridges:${NC}"
    for bridge in br-vlan10 br-vlan20 br-vlan41 br-vlan30 br-vlan31; do
        if ip link show "$bridge" &>/dev/null; then
            local ip=$(ip addr show "$bridge" | grep 'inet ' | awk '{print $2}')
            if [[ -n "$ip" ]]; then
                echo -e "${GREEN}✅ $bridge: $ip${NC}"
            else
                echo -e "${RED}❌ $bridge: Pas d'IP configurée${NC}"
            fi
        else
            echo -e "${RED}❌ $bridge: N'existe pas${NC}"
        fi
    done
    echo ""
    
    echo -e "${YELLOW}Test de connectivité bridges:${NC}"
    for ip in 192.168.10.1 192.168.20.1 192.168.41.1 192.168.30.1 192.168.31.1; do
        if ping -c 1 -W 1 "$ip" &>/dev/null; then
            echo -e "${GREEN}✅ $ip accessible${NC}"
        else
            echo -e "${RED}❌ $ip inaccessible${NC}"
        fi
    done
}

# Fonction pour afficher la documentation
show_documentation() {
    echo -e "${CYAN}📚 Documentation des outils GNS3...${NC}"
    echo ""
    
    if [[ -f "$SCRIPT_DIR/README_GNS3_INVESTIGATION.md" ]]; then
        less "$SCRIPT_DIR/README_GNS3_INVESTIGATION.md"
    else
        echo -e "${RED}❌ Documentation non trouvée.${NC}"
    fi
}

# Fonction principale
main() {
    show_banner
    
    while true; do
        echo ""
        show_menu
        echo ""
        read -p "Choisissez une option (1-8): " choice
        echo ""
        
        case $choice in
            1)
                run_investigation
                ;;
            2)
                run_advanced_troubleshoot
                ;;
            3)
                run_connectivity_diagnostic
                ;;
            4)
                run_quick_fix
                ;;
            5)
                show_last_report
                ;;
            6)
                check_bridges
                ;;
            7)
                show_documentation
                ;;
            8)
                echo -e "${GREEN}👋 Au revoir !${NC}"
                exit 0
                ;;
            *)
                echo -e "${RED}❌ Option invalide. Veuillez choisir entre 1 et 8.${NC}"
                ;;
        esac
        
        echo ""
        read -p "Appuyez sur Entrée pour continuer..."
    done
}

# Vérification des prérequis
check_prerequisites() {
    # Vérifier que nous sommes dans le bon répertoire
    if [[ ! -d "$SCRIPT_DIR" ]]; then
        echo -e "${RED}❌ Répertoire des scripts non trouvé: $SCRIPT_DIR${NC}"
        exit 1
    fi
    
    # Vérifier que les scripts existent
    local required_scripts=(
        "investigate_gns3_issues.py"
        "gns3_advanced_troubleshoot.py"
        "diagnostic_connectivite.py"
        "fix_gns3_topology.py"
    )
    
    for script in "${required_scripts[@]}"; do
        if [[ ! -f "$SCRIPT_DIR/$script" ]]; then
            echo -e "${RED}❌ Script manquant: $script${NC}"
            exit 1
        fi
    done
    
    # Vérifier Python
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}❌ Python3 non trouvé${NC}"
        exit 1
    fi
    
    # Vérifier sudo
    if ! sudo -n true 2>/dev/null; then
        echo -e "${YELLOW}⚠️ Accès sudo requis pour certaines opérations${NC}"
    fi
}

# Point d'entrée
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    check_prerequisites
    main "$@"
fi