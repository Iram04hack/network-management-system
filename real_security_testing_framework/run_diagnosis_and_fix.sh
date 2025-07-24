#!/bin/bash
"""
Script de Diagnostic et Correction GNS3
=======================================

Script principal pour diagnostiquer et corriger les problèmes GNS3 identifiés.
"""

# Couleurs pour l'affichage
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="/tmp/gns3_diagnosis_$(date +%Y%m%d_%H%M%S).log"

echo -e "${BLUE}🚀 DIAGNOSTIC ET CORRECTION GNS3${NC}"
echo -e "${BLUE}=================================${NC}"
echo ""
echo "Ce script va diagnostiquer et corriger les problèmes GNS3 identifiés."
echo "Logs sauvegardés dans: $LOG_FILE"
echo ""

# Fonction pour afficher et logger
log_and_display() {
    echo -e "$1"
    echo -e "$1" >> "$LOG_FILE"
}

# Fonction pour exécuter une étape
execute_step() {
    local step_name="$1"
    local script_name="$2"
    local description="$3"
    
    log_and_display "${BLUE}📋 ÉTAPE: $step_name${NC}"
    log_and_display "Description: $description"
    log_and_display "Script: $script_name"
    echo ""
    
    if [ -f "$SCRIPT_DIR/$script_name" ]; then
        echo "Exécution en cours..."
        
        # Exécuter le script et capturer le code de sortie
        cd "$SCRIPT_DIR"
        if python3 "$script_name" 2>&1 | tee -a "$LOG_FILE"; then
            local exit_code=${PIPESTATUS[0]}
            
            if [ $exit_code -eq 0 ]; then
                log_and_display "${GREEN}✅ $step_name: SUCCÈS${NC}"
                return 0
            else
                log_and_display "${YELLOW}⚠️ $step_name: SUCCÈS PARTIEL (code: $exit_code)${NC}"
                return $exit_code
            fi
        else
            log_and_display "${RED}❌ $step_name: ÉCHEC${NC}"
            return 1
        fi
    else
        log_and_display "${RED}❌ Script $script_name non trouvé${NC}"
        return 1
    fi
}

# Fonction pour demander confirmation
ask_confirmation() {
    local message="$1"
    echo -e "${YELLOW}$message${NC}"
    read -p "Continuer? (y/N): " -n 1 -r
    echo ""
    [[ $REPLY =~ ^[Yy]$ ]]
}

# Début du diagnostic
log_and_display "${BLUE}🔍 DÉBUT DU DIAGNOSTIC ET CORRECTION${NC}"
log_and_display "Date: $(date)"
log_and_display "Répertoire: $SCRIPT_DIR"
echo ""

# Étape 1: Analyse des logs
if ask_confirmation "Voulez-vous analyser les logs existants?"; then
    execute_step "ANALYSE DES LOGS" "analyze_logs.py" "Analyse automatique des patterns d'erreur dans les logs"
    echo ""
fi

# Étape 2: Diagnostic rapide
execute_step "DIAGNOSTIC RAPIDE" "quick_diagnostic.py" "Vérification de l'état actuel de GNS3 et du projet"
diagnostic_result=$?

echo ""
log_and_display "${BLUE}📊 RÉSULTAT DU DIAGNOSTIC${NC}"

if [ $diagnostic_result -eq 0 ]; then
    log_and_display "${GREEN}✅ AUCUN PROBLÈME DÉTECTÉ${NC}"
    log_and_display "Le système semble fonctionnel."
    
    if ask_confirmation "Voulez-vous quand même tester le framework de sécurité?"; then
        log_and_display "${BLUE}🧪 Test du framework de sécurité...${NC}"
        cd "$SCRIPT_DIR"
        python3 core/real_security_framework.py 2>&1 | tee -a "$LOG_FILE"
    fi
    
    exit 0
else
    log_and_display "${RED}❌ PROBLÈMES DÉTECTÉS${NC}"
    log_and_display "Des corrections sont nécessaires."
    echo ""
    
    if ask_confirmation "Voulez-vous appliquer les corrections automatiques?"; then
        # Étape 3: Correction spécifique
        execute_step "CORRECTION SPÉCIFIQUE" "fix_specific_issues.py" "Correction automatique des problèmes identifiés"
        fix_result=$?
        
        echo ""
        
        if [ $fix_result -eq 0 ]; then
            log_and_display "${GREEN}🎉 CORRECTIONS APPLIQUÉES AVEC SUCCÈS${NC}"
            
            # Étape 4: Vérification post-correction
            if ask_confirmation "Voulez-vous vérifier les corrections?"; then
                execute_step "VÉRIFICATION POST-CORRECTION" "quick_diagnostic.py" "Vérification après correction"
                verify_result=$?
                
                if [ $verify_result -eq 0 ]; then
                    log_and_display "${GREEN}✅ VÉRIFICATION RÉUSSIE${NC}"
                    
                    if ask_confirmation "Voulez-vous tester le framework de sécurité maintenant?"; then
                        log_and_display "${BLUE}🧪 Test du framework de sécurité...${NC}"
                        cd "$SCRIPT_DIR"
                        python3 core/real_security_framework.py 2>&1 | tee -a "$LOG_FILE"
                    fi
                else
                    log_and_display "${YELLOW}⚠️ Des problèmes persistent après correction${NC}"
                    log_and_display "Vérification manuelle recommandée."
                fi
            fi
        else
            log_and_display "${YELLOW}⚠️ CORRECTIONS PARTIELLES${NC}"
            log_and_display "Certains problèmes n'ont pas pu être résolus automatiquement."
            
            if ask_confirmation "Voulez-vous utiliser l'outil de dépannage avancé?"; then
                if [ -f "$SCRIPT_DIR/investigate_gns3_issues.py" ]; then
                    execute_step "DÉPANNAGE AVANCÉ" "investigate_gns3_issues.py" "Investigation approfondie et corrections avancées"
                else
                    log_and_display "${YELLOW}⚠️ Outil de dépannage avancé non disponible${NC}"
                fi
            fi
        fi
    else
        log_and_display "${BLUE}ℹ️ Corrections non appliquées${NC}"
        log_and_display "Vous pouvez appliquer les corrections manuellement plus tard."
    fi
fi

# Résumé final
echo ""
log_and_display "${BLUE}📋 RÉSUMÉ FINAL${NC}"
log_and_display "Logs détaillés: $LOG_FILE"

if [ -f "$SCRIPT_DIR/README_GNS3_INVESTIGATION.md" ]; then
    log_and_display "Documentation: $SCRIPT_DIR/README_GNS3_INVESTIGATION.md"
fi

echo ""
log_and_display "${BLUE}🔧 OUTILS DISPONIBLES${NC}"
log_and_display "• quick_diagnostic.py - Diagnostic rapide"
log_and_display "• fix_specific_issues.py - Corrections spécifiques"
log_and_display "• analyze_logs.py - Analyse des logs"
log_and_display "• investigate_gns3_issues.py - Investigation approfondie"

echo ""
log_and_display "${GREEN}✅ Diagnostic et correction terminés${NC}"

exit 0