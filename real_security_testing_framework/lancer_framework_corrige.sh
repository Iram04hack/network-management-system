#!/bin/bash

# Script de lancement du framework de tests de sécurité CORRIGÉ
# Utilise l'orchestrateur principal pour résoudre automatiquement les problèmes
# 
# Auteur: Équipe de développement NMS
# Date: 2025-07-21

cd /home/adjada/network-management-system/real_security_testing_framework

echo "🚀 FRAMEWORK DE TESTS DE SÉCURITÉ NMS - VERSION CORRIGÉE"
echo "=========================================================="
echo ""
echo "🎯 Ce script va:"
echo "   1. Vérifier et corriger la configuration réseau"
echo "   2. Diagnostiquer la topologie GNS3" 
echo "   3. Configurer les serveurs QEMU via SSH"
echo "   4. Lancer le framework de tests"
echo ""

# Vérification de l'environnement virtuel
if [[ "$VIRTUAL_ENV" != *"nms_env"* ]]; then
    echo "🔧 Activation de l'environnement virtuel nms_env..."
    source /home/adjada/network-management-system/web-interface/django__backend/nms_env/bin/activate
    
    if [[ "$VIRTUAL_ENV" != *"nms_env"* ]]; then
        echo "❌ Impossible d'activer l'environnement virtuel"
        echo "💡 Activez manuellement avec:"
        echo "   source /home/adjada/network-management-system/web-interface/django__backend/nms_env/bin/activate"
        exit 1
    fi
    echo "✅ Environnement virtuel activé"
else
    echo "✅ Environnement virtuel nms_env déjà actif"
fi

# Vérification que les scripts existent
scripts_requis=(
    "orchestrateur_corrections.py"
    "diagnostic_topologie.py" 
    "qemu_ssh_config.py"
    "core/real_security_framework.py"
)

for script in "${scripts_requis[@]}"; do
    if [[ ! -f "$script" ]]; then
        echo "❌ Script manquant: $script"
        exit 1
    fi
done

echo "✅ Tous les scripts requis sont présents"
echo ""

# 1. PHASE DE CORRECTION AUTOMATIQUE
echo "🔧 PHASE 1: CORRECTIONS AUTOMATIQUES"
echo "====================================="

python3 orchestrateur_corrections.py

if [ $? -eq 0 ]; then
    echo "✅ Corrections appliquées avec succès"
elif [ $? -eq 1 ]; then
    echo "⚠️ Corrections partielles - on continue"
else
    echo "❌ Échec des corrections"
    echo "💡 Vérifiez les prérequis:"
    echo "   - GNS3 démarré avec projet hybrido"
    echo "   - Django démarré (./nms-manager.sh)"
    echo "   - Permissions sudo disponibles"
    exit 1
fi

echo ""

# 2. PHASE DE LANCEMENT DU FRAMEWORK
echo "🚀 PHASE 2: LANCEMENT DU FRAMEWORK DE TESTS"
echo "============================================"

echo "🔍 Vérification finale des services..."

# Vérification GNS3
curl -s http://localhost:3080/v2/version >/dev/null
if [ $? -eq 0 ]; then
    echo "✅ GNS3 accessible"
else
    echo "❌ GNS3 non accessible"
    exit 1
fi

# Vérification Django
curl -s http://localhost:8000 >/dev/null
if [ $? -eq 0 ]; then
    echo "✅ Django accessible"
else
    echo "⚠️ Django potentiellement inaccessible - on continue"
fi

echo ""
echo "🎯 Lancement du framework de tests de sécurité..."
echo "📊 Les corrections automatiques ont été appliquées"
echo "🔍 Surveillance en cours des équipements configurés"
echo ""

# Lancement du framework principal
python3 core/real_security_framework.py

framework_exit_code=$?

echo ""
echo "📊 RÉSUMÉ DE L'EXÉCUTION"
echo "========================"

if [ $framework_exit_code -eq 0 ]; then
    echo "✅ Framework de tests terminé avec succès"
    echo "📋 Consultez les logs pour les résultats détaillés"
else
    echo "⚠️ Framework terminé avec des avertissements (code: $framework_exit_code)"
    echo "🔍 Vérifiez les logs pour identifier les problèmes restants"
fi

echo ""
echo "💡 PROCHAINES ÉTAPES:"
echo "   - Analysez les résultats de tests de sécurité"
echo "   - Vérifiez les rapports générés par les modules Django"
echo "   - En cas de problème, relancez avec des corrections supplémentaires"
echo ""

exit $framework_exit_code