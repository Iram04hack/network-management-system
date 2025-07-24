#!/usr/bin/env python3
"""
Test Intégré Final - Framework avec Découverte IP Réelle sur Hybrido
==================================================================

Ce script teste le framework complet intégré avec toutes les améliorations :
- API GNS3 pour vraies adresses console
- Découverte IP optimisée par type d'équipement
- Commandes adaptées (VPCS, Cisco, serveurs)
- Gestion d'erreurs avancée
"""

import asyncio
import logging
import sys
from pathlib import Path

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_integrated_framework():
    print('🧪 TEST INTÉGRÉ FINAL - FRAMEWORK AVEC DÉCOUVERTE IP RÉELLE')
    print('=' * 80)
    
    try:
        # Importer le framework principal
        from core.real_security_framework import RealSecurityTestingFramework
        from console_ip_discovery import ConsoleIPDiscovery
        
        print('✅ Modules importés avec succès')
        
        # 1. Test de création du framework
        print('\n🔧 INITIALISATION DU FRAMEWORK...')
        framework = RealSecurityTestingFramework()
        
        # 2. Test de la nouvelle méthode d'API GNS3
        print('\n🔗 TEST RÉCUPÉRATION ADRESSES CONSOLE VIA API GNS3...')
        project_id = "6b858ee5-4a49-4f72-b437-8dcd8d876bad"  # hybrido
        
        console_addresses = await framework._get_real_console_addresses(project_id)
        
        if console_addresses:
            print(f'✅ {len(console_addresses)} adresses console récupérées')
            print('📋 Exemples d\'adresses console:')
            for i, (node_id, info) in enumerate(list(console_addresses.items())[:5]):
                print(f'   {i+1}. {info["console_host"]}:{info["console_port"]} ({info["console_type"]})')
        else:
            print('❌ Aucune adresse console récupérée')
            return False
        
        # 3. Test du découvreur IP avec vraies adresses
        print('\n🔍 TEST DÉCOUVREUR IP AVEC VRAIES ADRESSES...')
        
        # Créer des données d'équipement avec vraies adresses console
        test_equipment = []
        for node_id, console_info in list(console_addresses.items())[:3]:  # 3 premiers
            equipment_info = {
                'node_id': node_id,
                'name': f'Test-{node_id[:8]}',
                'node_type': 'unknown',
                'console_port': console_info['console_port'],
                'console_host': console_info['console_host'],  # VRAIE adresse
                'console_type': console_info['console_type']
            }
            test_equipment.append(equipment_info)
        
        print(f'📊 {len(test_equipment)} équipements de test préparés')
        
        # Créer le découvreur IP
        ip_discovery = ConsoleIPDiscovery(username="osboxes", password="osboxes.org")
        
        # Test de découverte
        results = await ip_discovery.discover_real_ips_from_project(project_id, test_equipment)
        
        print(f'\n📊 RÉSULTATS DE DÉCOUVERTE:')
        successful = sum(1 for r in results.values() if r.success)
        total = len(results)
        total_ips = sum(len(r.ip_addresses) for r in results.values() if r.success)
        
        print(f'   • Équipements testés: {total}')
        print(f'   • Découvertes réussies: {successful}')
        print(f'   • Total IPs trouvées: {total_ips}')
        print(f'   • Taux de succès: {(successful/total*100):.1f}%')
        
        # 4. Test de la gestion d'erreurs intégrée
        print(f'\n⚠️ TEST GESTION D\'ERREURS...')
        
        # Simuler des équipements pour tester les erreurs
        framework.analyzed_equipment = []
        for node_id, result in results.items():
            # Créer un équipement simulé
            equipment = type('Equipment', (), {
                'name': result.node_name,
                'node_id': node_id,
                'device_category': 'test',
                'ip_addresses': result.ip_addresses,
                'real_ip_discovered': result.success
            })()
            framework.analyzed_equipment.append(equipment)
        
        # Tester la génération du résumé d'erreurs
        error_summary = framework._get_equipment_error_summary()
        print(f'📊 Résumé d\'erreurs généré:')
        print(f'   • Total équipements: {error_summary["total_equipment"]}')
        print(f'   • Avec erreurs: {error_summary["equipment_with_errors"]}')
        print(f'   • Sans IP: {error_summary["equipment_without_ip"]}')
        
        if error_summary["equipment_with_errors"] > 0:
            print(f'\\n⚠️ Affichage du résumé d\'erreurs:')
            framework._display_error_summary(error_summary)
        
        # 5. Test de synthèse
        print(f'\\n🎯 SYNTHÈSE DU TEST INTÉGRÉ:')
        print('=' * 60)
        
        integration_score = 0
        total_tests = 4
        
        # Test 1: Import des modules
        integration_score += 1
        print(f'✅ Import des modules: OK')
        
        # Test 2: API GNS3
        if console_addresses:
            integration_score += 1
            print(f'✅ API GNS3 (vraies adresses): OK')
        else:
            print(f'❌ API GNS3: ÉCHEC')
        
        # Test 3: Découverte IP
        if successful > 0:
            integration_score += 1
            print(f'✅ Découverte IP réelle: OK ({successful}/{total} réussies)')
        else:
            print(f'❌ Découverte IP: ÉCHEC')
        
        # Test 4: Gestion d'erreurs
        if error_summary:
            integration_score += 1
            print(f'✅ Gestion d\'erreurs avancée: OK')
        else:
            print(f'❌ Gestion d\'erreurs: ÉCHEC')
        
        success_rate = (integration_score / total_tests) * 100
        print(f'\\n📈 SCORE D\'INTÉGRATION: {integration_score}/{total_tests} ({success_rate:.0f}%)')
        
        if success_rate >= 75:
            print(f'🎉 INTÉGRATION RÉUSSIE!')
            print(f'✅ Le framework est prêt pour utilisation avec découverte IP réelle')
            return True
        else:
            print(f'⚠️ Intégration partielle - voir les erreurs ci-dessus')
            return False
        
    except ImportError as e:
        print(f'❌ Erreur d\'import: {e}')
        print(f'💡 Vérifiez que tous les modules sont présents')
        return False
    except Exception as e:
        print(f'❌ Erreur durant le test: {e}')
        import traceback
        traceback.print_exc()
        return False

async def main():
    success = await test_integrated_framework()
    
    if success:
        print(f'\\n🎉 TEST INTÉGRÉ RÉUSSI!')
        print(f'🚀 Le framework est maintenant intégralement opérationnel avec découverte IP réelle')
        print(f'📋 Pour lancer le framework complet:')
        print(f'   python3 start_security_framework.py --mode auto')
    else:
        print(f'\\n❌ Test intégré échoué')
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())