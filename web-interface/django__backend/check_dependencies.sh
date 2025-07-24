#!/bin/bash
# Script de vérification et installation des dépendances critiques
# Évite les problèmes de démarrage de Django dus aux dépendances manquantes

echo "🔍 Vérification des dépendances critiques..."

# Liste des dépendances critiques pour le fonctionnement
CRITICAL_DEPS=(
    "django-sslserver"
    "plotly" 
    "seaborn"
    "elasticsearch"
    "matplotlib"
    "pandas"
    "numpy"
)

MISSING_DEPS=()

# Vérifier chaque dépendance
for dep in "${CRITICAL_DEPS[@]}"; do
    if ! python -c "import ${dep//-/_}" 2>/dev/null; then
        echo "❌ Dépendance manquante : $dep"
        MISSING_DEPS+=("$dep")
    else
        echo "✅ $dep est disponible"
    fi
done

# Installer les dépendances manquantes
if [ ${#MISSING_DEPS[@]} -gt 0 ]; then
    echo "🔧 Installation des dépendances manquantes..."
    for dep in "${MISSING_DEPS[@]}"; do
        echo "📦 Installation de $dep..."
        pip install --no-cache-dir "$dep" || echo "⚠️  Échec de l'installation de $dep"
    done
    echo "✅ Installation terminée"
else
    echo "✅ Toutes les dépendances critiques sont présentes"
fi