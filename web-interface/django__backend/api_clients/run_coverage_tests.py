#!/usr/bin/env python
"""
Script principal pour exécuter les tests de couverture api_clients.
Objectif: Atteindre ≥90% de couverture avec environnement optimisé.

Usage:
    python api_clients/run_coverage_tests.py
    
    ou depuis le répertoire django__backend:
    python -m api_clients.run_coverage_tests
"""

import sys
import os
from pathlib import Path

# Ajouter le chemin du module
current_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(current_dir.parent))

from api_clients.testing.coverage_runner import CoverageTestRunner
from api_clients.testing.environment_manager import TestEnvironmentManager
from api_clients.testing.test_config import TestConfig


def main():
    """Fonction principale d'exécution des tests de couverture."""
    print("🎯 TESTS DE COUVERTURE API_CLIENTS")
    print("Objectif: Atteindre ≥90% de couverture de tests")
    print("="*60)
    
    # Vérifier les arguments de ligne de commande
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "env":
            # Test de l'environnement uniquement
            print("🔧 Test de l'environnement de tests...")
            manager = TestEnvironmentManager()
            success = manager.setup_complete_environment()
            
            if success:
                status = manager.get_environment_status()
                print(f"\n📊 Statut de l'environnement:")
                for key, value in status.items():
                    print(f"   {key}: {value}")
                
                manager.cleanup_environment()
                print("\n✅ Test de l'environnement réussi!")
                return 0
            else:
                print("\n❌ Problème avec l'environnement de tests")
                return 1
        
        elif command == "config":
            # Afficher la configuration
            print("⚙️ Configuration des tests api_clients:")
            config = TestConfig()
            
            print(f"\n📊 Configuration de couverture:")
            coverage_config = config.get_coverage_config()
            for key, value in coverage_config.items():
                print(f"   {key}: {value}")
            
            print(f"\n🎯 Tests prioritaires:")
            priority_config = config.get_priority_tests_config()
            for name, details in priority_config.items():
                print(f"   {name}: {details['lines']} lignes, impact +{details['expected_impact']}%")
            
            print(f"\n🔧 Services de test:")
            for service, config_details in config.TEST_SERVICES.items():
                print(f"   {service}: {config_details}")
            
            return 0
        
        elif command == "help":
            # Afficher l'aide
            print("📋 Commandes disponibles:")
            print("   python api_clients/run_coverage_tests.py        - Exécuter tous les tests")
            print("   python api_clients/run_coverage_tests.py env    - Tester l'environnement")
            print("   python api_clients/run_coverage_tests.py config - Afficher la configuration")
            print("   python api_clients/run_coverage_tests.py help   - Afficher cette aide")
            return 0
        
        else:
            print(f"❌ Commande inconnue: {command}")
            print("Utilisez 'help' pour voir les commandes disponibles")
            return 1
    
    # Exécution complète des tests de couverture
    try:
        print("🚀 Démarrage des tests de couverture complets...")
        
        runner = CoverageTestRunner()
        success = runner.run_complete_coverage_tests()
        
        if success:
            print("\n🎉 SUCCÈS COMPLET!")
            print("✅ Objectif ≥90% de couverture atteint")
            print("✅ Contrainte 95.65% données réelles respectée")
            print("✅ Tests adaptatifs fonctionnels")
            print("\n📄 Consultez le rapport HTML pour les détails")
            return 0
        else:
            print("\n📋 OBJECTIF NON ATTEINT")
            print("⚠️ Progrès significatifs réalisés")
            print("📊 Consultez le rapport pour les prochaines étapes")
            return 1
            
    except KeyboardInterrupt:
        print("\n⚠️ Interruption par l'utilisateur")
        print("🧹 Nettoyage en cours...")
        
        # Nettoyage d'urgence
        try:
            manager = TestEnvironmentManager()
            manager.cleanup_environment()
        except:
            pass
        
        return 130  # Code de sortie pour interruption
        
    except Exception as e:
        print(f"\n❌ ERREUR CRITIQUE: {e}")
        import traceback
        traceback.print_exc()
        
        # Nettoyage d'urgence
        try:
            manager = TestEnvironmentManager()
            manager.cleanup_environment()
        except:
            pass
        
        return 1


if __name__ == "__main__":
    sys.exit(main())
