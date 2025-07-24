#!/usr/bin/env python3
"""
Script de Lancement du Framework de Tests de Sécurité NMS - Version Finale
=========================================================================

Ce script lance le framework de tests de sécurité avec toutes les améliorations :
- Configuration automatique du réseau HOST
- Authentification VNC intégrée
- Workflow complet avec Django
- Structure nettoyée et optimisée

Usage:
    python3 start_security_framework.py [--mode auto|interactive]

Auteur: Claude Code
Version: 1.0 (Final)
"""

import sys
import asyncio
import logging
import argparse
from pathlib import Path

# Ajouter le répertoire courant au path Python
sys.path.insert(0, str(Path(__file__).parent))

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def parse_arguments():
    """Parse les arguments de ligne de commande."""
    parser = argparse.ArgumentParser(
        description="Framework de Tests de Sécurité NMS - Version Finale",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples d'utilisation:
  %(prog)s --mode auto      # Mode automatique (recommandé pour les tests)
  %(prog)s --mode interactive  # Mode interactif (sélection manuelle)
  %(prog)s                  # Mode interactif par défaut

Fonctionnalités intégrées:
  ✅ Configuration automatique du réseau HOST
  ✅ Authentification VNC (osboxes.org/osboxes)
  ✅ Démarrage automatique des équipements GNS3
  ✅ Injection de trafic réel adaptée
  ✅ Workflow Django complet automatique
  ✅ Rapports et notifications en temps réel
        """
    )
    
    parser.add_argument(
        '--mode',
        choices=['auto', 'interactive'],
        default='interactive',
        help='Mode d\'exécution (défaut: interactive)'
    )
    
    parser.add_argument(
        '--django-url',
        default=None,
        help='URL du serveur Django (auto-détecté par défaut)'
    )
    
    parser.add_argument(
        '--no-network-config',
        action='store_true',
        help='Désactiver la configuration automatique du réseau'
    )
    
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Activer le mode debug'
    )
    
    return parser.parse_args()

async def main():
    """Point d'entrée principal du framework de tests de sécurité."""
    args = parse_arguments()
    
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Affichage de bienvenue
    print("\n" + "="*80)
    print("🚀 FRAMEWORK DE TESTS DE SÉCURITÉ NMS - VERSION FINALE")
    print("="*80)
    print("🔧 Configuration automatique du réseau HOST intégrée")
    print("🔐 Authentification VNC: osboxes.org/osboxes")
    print("⚙️ Workflow Django automatique complet")
    print("🧹 Structure nettoyée et optimisée")
    print("="*80)
    print()
    
    try:
        # Importer le framework principal
        from core.real_security_framework import RealSecurityTestingFramework
        
        # Créer le framework
        auto_mode = (args.mode == 'auto')
        framework = RealSecurityTestingFramework(django_url=args.django_url)
        
        # Initialiser le framework
        logger.info("🔧 Initialisation du framework...")
        if not await framework.initialize():
            logger.error("❌ Échec de l'initialisation du framework")
            return 1
        
        # Configuration réseau HOST (si activée)
        if not args.no_network_config:
            logger.info("🌐 Pré-configuration du réseau HOST...")
            try:
                from network_auto_config import NetworkAutoConfigurator
                configurator = NetworkAutoConfigurator()
                config_result = configurator.run_full_network_configuration()
                
                if config_result["overall_success"]:
                    logger.info("✅ Configuration réseau HOST réussie")
                else:
                    logger.warning("⚠️ Configuration réseau HOST partielle")
            except Exception as e:
                logger.warning(f"⚠️ Erreur configuration réseau: {e}")
        
        # Configuration spéciale pour le projet hybrido si détecté
        if hasattr(framework, 'selected_project') and framework.selected_project:
            if 'hybrido' in framework.selected_project.name.lower():
                logger.info("🎯 Projet hybrido détecté - activation découverte IP optimisée")
                framework._use_real_console_addresses = True
        
        # Lancer le workflow complet
        logger.info(f"🚀 Lancement du workflow en mode {'AUTO' if auto_mode else 'INTERACTIF'}...")
        success = await framework.run_complete_workflow(auto_mode=auto_mode)
        
        # Affichage des résultats finaux
        print("\n" + "="*80)
        if success:
            print("🎉 FRAMEWORK DE TESTS DE SÉCURITÉ TERMINÉ AVEC SUCCÈS")
            print("="*80)
            print("✅ Tous les workflows ont été exécutés correctement")
            print("📊 Consultez les rapports générés pour les détails")
            print("📧 Les notifications ont été envoyées aux destinataires")
        else:
            print("⚠️ FRAMEWORK TERMINÉ AVEC DES AVERTISSEMENTS")
            print("="*80)
            print("🔍 Certains workflows ont rencontré des problèmes")
            print("📋 Consultez les logs pour plus de détails")
        print("="*80)
        
        return 0 if success else 1
        
    except KeyboardInterrupt:
        print("\n🛑 Framework interrompu par l'utilisateur")
        return 130
    except ImportError as e:
        logger.error(f"❌ Erreur d'import: {e}")
        logger.error("💡 Assurez-vous que tous les modules sont présents")
        return 1
    except Exception as e:
        logger.error(f"❌ Erreur fatale: {e}")
        if args.debug:
            import traceback
            traceback.print_exc()
        return 1

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except Exception as e:
        logger.error(f"❌ Erreur critique: {e}")
        sys.exit(1)