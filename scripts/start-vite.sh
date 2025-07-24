#!/bin/bash
#
# Script simple pour démarrer Vite et surveiller les erreurs
#

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
FRONTEND_DIR="$PROJECT_ROOT/web-interface/react_frontend"
LOG_FILE="$PROJECT_ROOT/logs/vite-startup.log"
PID_FILE="$PROJECT_ROOT/frontend.pid"

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Créer le dossier logs
mkdir -p "$PROJECT_ROOT/logs"

echo -e "${BLUE}=== Démarrage du serveur Vite ===${NC}"

# Vérifier si Vite est déjà en cours
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if kill -0 "$PID" 2>/dev/null; then
        echo -e "${GREEN}✓ Serveur Vite déjà en cours (PID: $PID)${NC}"
        echo -e "${GREEN}✓ Accessible sur: http://localhost:5173/${NC}"
        exit 0
    else
        rm -f "$PID_FILE"
    fi
fi

# Aller dans le répertoire frontend
cd "$FRONTEND_DIR" || {
    echo -e "${RED}✗ Erreur: Impossible d'accéder à $FRONTEND_DIR${NC}"
    exit 1
}

# Vérifier les dépendances
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}⚠ Installation des dépendances...${NC}"
    npm install
fi

# Démarrer Vite en arrière-plan
echo -e "${BLUE}🚀 Démarrage du serveur Vite...${NC}"
npm run dev > "$LOG_FILE" 2>&1 &
VITE_PID=$!

# Sauvegarder le PID
echo "$VITE_PID" > "$PID_FILE"

echo -e "${BLUE}📋 PID du serveur: $VITE_PID${NC}"
echo -e "${BLUE}📝 Logs: $LOG_FILE${NC}"

# Attendre et surveiller le démarrage
echo -e "${BLUE}🔍 Surveillance du démarrage...${NC}"

SUCCESS=false
TIMEOUT=30
ELAPSED=0

while [ $ELAPSED -lt $TIMEOUT ]; do
    # Vérifier si le processus est toujours vivant
    if ! kill -0 "$VITE_PID" 2>/dev/null; then
        echo -e "${RED}✗ Le processus Vite s'est arrêté prématurément${NC}"
        break
    fi
    
    # Vérifier les logs pour le succès
    if grep -q "ready in" "$LOG_FILE" 2>/dev/null; then
        SUCCESS=true
        break
    fi
    
    # Vérifier les erreurs critiques
    if grep -E "(Error|ERROR|EADDRINUSE|Cannot resolve|Module not found)" "$LOG_FILE" 2>/dev/null; then
        echo -e "${RED}✗ Erreurs détectées dans les logs${NC}"
        break
    fi
    
    sleep 1
    ((ELAPSED++))
    
    # Afficher un point de progression toutes les 5 secondes
    if [ $((ELAPSED % 5)) -eq 0 ]; then
        echo -n "."
    fi
done

echo ""

if [ "$SUCCESS" = true ]; then
    echo -e "${GREEN}✓ Serveur Vite démarré avec succès !${NC}"
    
    # Extraire l'URL du log
    URL=$(grep -o "http://[^[:space:]]*" "$LOG_FILE" | head -1)
    if [ -n "$URL" ]; then
        echo -e "${GREEN}✓ Accessible sur: $URL${NC}"
    else
        echo -e "${GREEN}✓ Accessible sur: http://localhost:5173/${NC}"
    fi
    
    # Vérifier la connectivité
    sleep 2
    if curl -s --max-time 3 "http://localhost:5173" >/dev/null 2>&1; then
        echo -e "${GREEN}✓ Serveur répond correctement${NC}"
    else
        echo -e "${YELLOW}⚠ Serveur démarré mais ne répond pas encore${NC}"
    fi
else
    echo -e "${RED}✗ Échec du démarrage du serveur Vite${NC}"
    
    # Arrêter le processus si il est encore vivant
    if kill -0 "$VITE_PID" 2>/dev/null; then
        kill "$VITE_PID"
    fi
    rm -f "$PID_FILE"
fi

echo -e "\n${BLUE}=== Analyse des logs ===${NC}"

# Afficher les erreurs React/JavaScript
if grep -E "(Error|ERROR|Warning|WARN)" "$LOG_FILE" 2>/dev/null | head -10; then
    echo -e "${YELLOW}⚠ Erreurs/Avertissements détectés ci-dessus${NC}"
else
    echo -e "${GREEN}✓ Aucune erreur React détectée${NC}"
fi

# Afficher les dernières lignes du log
echo -e "\n${BLUE}=== Dernières lignes du log ===${NC}"
tail -n 10 "$LOG_FILE" 2>/dev/null || echo "Aucun log disponible"

echo -e "\n${BLUE}=== Commandes utiles ===${NC}"
echo "Voir les logs en temps réel: tail -f $LOG_FILE"
echo "Arrêter le serveur: kill $VITE_PID && rm -f $PID_FILE"
echo "Redémarrer: $0"

if [ "$SUCCESS" = true ]; then
    exit 0
else
    exit 1
fi