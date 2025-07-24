#!/usr/bin/env python3
"""
Analyseur de Logs GNS3/Framework
===============================

Analyse automatique des logs pour identifier les patterns d'erreur
et proposer des corrections spécifiques.
"""

import re
import logging
from typing import Dict, List, Tuple
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class LogAnalyzer:
    def __init__(self):
        self.error_patterns = {
            'cloud_stopped': r'Cloud1.*stopped',
            'http_409': r'HTTP 409|409.*Conflict',
            'connection_failed': r'⚠️.*Connexion.*échouée.*409',
            'server_unreachable': r'⚠️.*non accessible ou non fonctionnel',
            'ping_failed': r'✅ Ping.*→.*: 0\.0% succès',
            'timeout_error': r'Timeout.*20s',
            'vnc_failed': r'Configuration VNC partielle.*0/5 commandes',
            'connectivity_low': r'Connectivité:.*équipements accessibles.*13\.3%'
        }
        
        self.success_patterns = {
            'equipment_configured': r'✅ Configuration réussie pour.*',
            'bridge_exists': r'✅ Bridge.*existe déjà',
            'ping_success': r'✅ Ping.*→.*: 100\.0% succès',
            'connection_success': r'✅.*connecté au cloud'
        }
    
    def analyze_log_content(self, log_content: str) -> Dict:
        """Analyse le contenu des logs."""
        lines = log_content.split('\n')
        
        analysis = {
            'errors_found': {},
            'successes_found': {},
            'equipment_status': {},
            'connectivity_issues': [],
            'suggestions': [],
            'summary': {}
        }
        
        # Analyser les patterns d'erreur
        for error_type, pattern in self.error_patterns.items():
            matches = re.findall(pattern, log_content, re.IGNORECASE)
            if matches:
                analysis['errors_found'][error_type] = len(matches)
        
        # Analyser les succès
        for success_type, pattern in self.success_patterns.items():
            matches = re.findall(pattern, log_content, re.IGNORECASE)
            if matches:
                analysis['successes_found'][success_type] = len(matches)
        
        # Analyser l'état des équipements
        equipment_lines = [line for line in lines if '(cloud): stopped' in line or 
                          'accessible via console' in line or 'inaccessible' in line]
        
        for line in equipment_lines:
            if 'Cloud1 (cloud): stopped' in line:
                analysis['equipment_status']['Cloud1'] = 'stopped'
            elif 'accessible via console' in line:
                match = re.search(r'✅ (.*?) \(.*?\) accessible via console', line)
                if match:
                    analysis['equipment_status'][match.group(1)] = 'accessible'
            elif 'inaccessible' in line:
                match = re.search(r'❌ (.*?) \(.*?\) inaccessible', line)
                if match:
                    analysis['equipment_status'][match.group(1)] = 'inaccessible'
        
        # Identifier les problèmes de connectivité
        connectivity_lines = [line for line in lines if 'Ping' in line and '0.0% succès' in line]
        for line in connectivity_lines:
            match = re.search(r'Ping (.*?)→(.*?): 0\.0% succès', line)
            if match:
                analysis['connectivity_issues'].append({
                    'source': match.group(1).strip(),
                    'target': match.group(2).strip()
                })
        
        # Générer des suggestions
        analysis['suggestions'] = self._generate_suggestions(analysis)
        
        # Résumé
        analysis['summary'] = self._generate_summary(analysis)
        
        return analysis
    
    def _generate_suggestions(self, analysis: Dict) -> List[str]:
        """Génère des suggestions basées sur l'analyse."""
        suggestions = []
        errors = analysis['errors_found']
        equipment = analysis['equipment_status']
        
        # Suggestions basées sur les erreurs détectées
        if 'cloud_stopped' in errors:
            suggestions.append("🔧 Démarrer Cloud1 via l'API GNS3")
            suggestions.append("🔧 Vérifier la configuration des ports Cloud1")
        
        if 'http_409' in errors:
            suggestions.append("🔧 Supprimer les liens existants vers Cloud1 pour éviter les conflits")
            suggestions.append("🔧 Recréer les connexions une par une")
        
        if 'server_unreachable' in errors:
            suggestions.append("🔧 Redémarrer les serveurs QEMU problématiques")
            suggestions.append("🔧 Vérifier la configuration VNC des serveurs")
        
        if 'ping_failed' in errors:
            suggestions.append("🔧 Vérifier la configuration réseau inter-VLAN")
            suggestions.append("🔧 Configurer les bridges système manquants")
        
        if 'connectivity_low' in errors:
            suggestions.append("🔧 Exécuter le script fix_specific_issues.py")
            suggestions.append("🔧 Vérifier la topologie Cloud1 dans GNS3")
        
        # Suggestions basées sur l'état des équipements
        if equipment.get('Cloud1') == 'stopped':
            suggestions.append("⚠️ PRIORITÉ: Cloud1 doit être démarré en premier")
        
        inaccessible_count = sum(1 for status in equipment.values() if status == 'inaccessible')
        if inaccessible_count > 5:
            suggestions.append("⚠️ Problème de connectivité majeur - Vérifier la topologie complète")
        
        return suggestions
    
    def _generate_summary(self, analysis: Dict) -> Dict:
        """Génère un résumé de l'analyse."""
        errors = analysis['errors_found']
        equipment = analysis['equipment_status']
        connectivity = analysis['connectivity_issues']
        
        total_errors = sum(errors.values())
        
        accessible_equipment = sum(1 for status in equipment.values() if status == 'accessible')
        inaccessible_equipment = sum(1 for status in equipment.values() if status == 'inaccessible')
        total_equipment = len(equipment)
        
        connectivity_rate = (accessible_equipment / total_equipment * 100) if total_equipment > 0 else 0
        
        severity = "CRITIQUE" if total_errors > 10 or connectivity_rate < 20 else \
                  "MAJEUR" if total_errors > 5 or connectivity_rate < 50 else \
                  "MINEUR" if total_errors > 0 else "AUCUN"
        
        return {
            'total_errors': total_errors,
            'severity': severity,
            'equipment_accessible': accessible_equipment,
            'equipment_inaccessible': inaccessible_equipment,
            'connectivity_rate': round(connectivity_rate, 1),
            'connectivity_failures': len(connectivity),
            'cloud_status': equipment.get('Cloud1', 'unknown')
        }

def analyze_provided_logs() -> Dict:
    """Analyse les logs fournis par l'utilisateur."""
    
    # Logs du framework fournis par l'utilisateur
    framework_log = """
2025-07-20 12:12:04,554 - __main__ - WARNING - ⚠️ Aucune détection réussie, utilisation par défaut: http://localhost:8000
2025-07-20 12:29:53,901 - auto_dhcp_configuration - WARNING - ❌ SW-DMZ (192.168.12.1) inaccessible
2025-07-20 12:29:53,901 - auto_dhcp_configuration - WARNING - ❌ Server-Mail (192.168.10.11) inaccessible
2025-07-20 12:29:53,901 - auto_dhcp_configuration - WARNING - ❌ Server-DNS (192.168.11.11) inaccessible
2025-07-20 12:29:53,901 - auto_dhcp_configuration - WARNING - ❌ SW-LAN (192.168.21.1) inaccessible
2025-07-20 12:29:53,901 - auto_dhcp_configuration - WARNING - ❌ SW-SERVER (192.168.31.1) inaccessible
2025-07-20 12:29:53,901 - auto_dhcp_configuration - WARNING - ❌ SW-ADMIN (192.168.41.1) inaccessible
2025-07-20 12:29:53,901 - auto_dhcp_configuration - WARNING - ❌ Server-DB (192.168.30.10) inaccessible
2025-07-20 12:29:53,901 - auto_dhcp_configuration - WARNING - ❌ Routeur-Principal (192.168.41.1) inaccessible
2025-07-20 12:29:53,901 - auto_dhcp_configuration - WARNING - ❌ Routeur-Bordure (192.168.41.2) inaccessible
2025-07-20 12:29:53,901 - auto_dhcp_configuration - INFO - ✅ PC1 (192.168.20.10) accessible via console
2025-07-20 12:29:53,901 - auto_dhcp_configuration - INFO - ✅ Admin (192.168.41.10) accessible via console
2025-07-20 12:29:53,901 - auto_dhcp_configuration - WARNING - ❌ PC2 (192.168.20.11) inaccessible
2025-07-20 12:29:53,901 - auto_dhcp_configuration - WARNING - ❌ PostTest (192.168.32.10) inaccessible
2025-07-20 12:29:53,901 - auto_dhcp_configuration - WARNING - ❌ Server-Web (192.168.10.10) inaccessible
2025-07-20 12:29:53,901 - auto_dhcp_configuration - WARNING - ❌ Server-Fichiers (192.168.31.10) inaccessible
2025-07-20 12:30:29,017 - __main__ - INFO - 📱 Cloud1 (cloud): stopped
2025-07-20 12:31:23,063 - traffic_generation.console_injector - INFO - ✅ Ping PC1→192.168.20.10: 100.0% succès
2025-07-20 12:31:35,079 - traffic_generation.console_injector - INFO - ✅ Ping Admin→192.168.41.10: 100.0% succès
2025-07-20 12:31:35,079 - traffic_generation.console_injector - INFO - ✅ Ping PC1→192.168.20.11: 0.0% succès
"""
    
    # Logs du fix_gns3_topology fournis par l'utilisateur
    fix_log = """
2025-07-20 12:17:31,211 - WARNING - ⚠️ Connexion PC1 échouée: 409
2025-07-20 12:17:38,280 - WARNING - ⚠️ Connexion Admin échouée: 409
2025-07-20 12:17:43,975 - INFO - ✅ Server-Web connecté au cloud (port 0)
2025-07-20 12:17:47,419 - WARNING - ⚠️ Connexion Server-Mail échouée: 409
2025-07-20 12:17:50,907 - WARNING - ⚠️ Connexion Server-DNS échouée: 409
2025-07-20 12:17:54,352 - WARNING - ⚠️ Connexion Server-DB échouée: 409
2025-07-20 12:18:00,728 - INFO - ✅ PostTest connecté au cloud (port 3)
2025-07-20 12:18:14,749 - INFO -    ❌ 192.168.20.10 inaccessible
2025-07-20 12:18:16,752 - INFO -    ❌ 192.168.41.10 inaccessible
2025-07-20 12:18:18,755 - INFO -    ❌ 192.168.10.10 inaccessible
2025-07-20 12:18:20,758 - INFO -    ❌ 192.168.10.11 inaccessible
2025-07-20 12:18:22,762 - INFO -    ❌ 192.168.30.10 inaccessible
"""
    
    combined_logs = framework_log + "\n" + fix_log
    
    analyzer = LogAnalyzer()
    return analyzer.analyze_log_content(combined_logs)

def main():
    """Analyse principale des logs."""
    logger.info("🔍 ANALYSE DES LOGS GNS3/FRAMEWORK")
    logger.info("=" * 50)
    
    # Analyser les logs fournis
    analysis = analyze_provided_logs()
    
    # Afficher les résultats
    logger.info("📋 RÉSUMÉ DE L'ANALYSE")
    summary = analysis['summary']
    logger.info(f"Sévérité: {summary['severity']}")
    logger.info(f"Erreurs totales: {summary['total_errors']}")
    logger.info(f"État Cloud1: {summary['cloud_status']}")
    logger.info(f"Équipements accessibles: {summary['equipment_accessible']}")
    logger.info(f"Équipements inaccessibles: {summary['equipment_inaccessible']}")
    logger.info(f"Taux de connectivité: {summary['connectivity_rate']}%")
    
    # Erreurs détectées
    if analysis['errors_found']:
        logger.info("\n📋 ERREURS DÉTECTÉES")
        for error_type, count in analysis['errors_found'].items():
            logger.warning(f"❌ {error_type}: {count} occurrences")
    
    # État des équipements
    if analysis['equipment_status']:
        logger.info("\n📋 ÉTAT DES ÉQUIPEMENTS")
        for equipment, status in analysis['equipment_status'].items():
            if status == 'accessible':
                logger.info(f"✅ {equipment}: {status}")
            elif status == 'stopped':
                logger.error(f"🛑 {equipment}: {status}")
            else:
                logger.warning(f"❌ {equipment}: {status}")
    
    # Problèmes de connectivité
    if analysis['connectivity_issues']:
        logger.info(f"\n📋 PROBLÈMES DE CONNECTIVITÉ ({len(analysis['connectivity_issues'])})")
        for issue in analysis['connectivity_issues'][:5]:  # Afficher les 5 premiers
            logger.warning(f"❌ {issue['source']} → {issue['target']}")
        if len(analysis['connectivity_issues']) > 5:
            logger.info(f"... et {len(analysis['connectivity_issues']) - 5} autres")
    
    # Suggestions de correction
    if analysis['suggestions']:
        logger.info("\n📋 SUGGESTIONS DE CORRECTION")
        for i, suggestion in enumerate(analysis['suggestions'], 1):
            logger.info(f"{i}. {suggestion}")
    
    # Recommandations finales
    logger.info("\n📋 RECOMMANDATIONS")
    if summary['severity'] == 'CRITIQUE':
        logger.error("🚨 SITUATION CRITIQUE - Action immédiate requise")
        logger.info("1. Exécuter quick_diagnostic.py pour un état détaillé")
        logger.info("2. Exécuter fix_specific_issues.py pour correction automatique")
        logger.info("3. Vérifier manuellement Cloud1 dans GNS3")
    elif summary['severity'] == 'MAJEUR':
        logger.warning("⚠️ PROBLÈMES MAJEURS - Correction recommandée")
        logger.info("1. Exécuter fix_specific_issues.py")
        logger.info("2. Vérifier les logs après correction")
    else:
        logger.info("✅ Problèmes mineurs ou résolus")
    
    return 0 if summary['severity'] in ['AUCUN', 'MINEUR'] else 1

if __name__ == "__main__":
    exit(main())