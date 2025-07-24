#!/usr/bin/env python3
"""
Diagnostic Rapide des Problèmes GNS3
====================================

Script de diagnostic rapide pour analyser l'état actuel avant correction.
"""

import requests
import subprocess
import logging
import json
from typing import Dict, List

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_gns3_api() -> bool:
    """Vérifie si l'API GNS3 est accessible."""
    try:
        response = requests.get("http://localhost:3080/v2/version", timeout=5)
        if response.status_code == 200:
            version = response.json().get('version', 'Unknown')
            logger.info(f"✅ GNS3 API accessible - Version: {version}")
            return True
        else:
            logger.error(f"❌ GNS3 API erreur: HTTP {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"❌ GNS3 API inaccessible: {e}")
        return False

def check_project_status() -> Dict:
    """Vérifie l'état du projet hybrido."""
    project_id = "6b858ee5-4a49-4f72-b437-8dcd8d876bad"
    
    try:
        # Informations du projet
        response = requests.get(f"http://localhost:3080/v2/projects/{project_id}")
        if response.status_code != 200:
            return {"error": f"Projet non accessible: HTTP {response.status_code}"}
        
        project_info = response.json()
        
        # Nœuds du projet
        nodes_response = requests.get(f"http://localhost:3080/v2/projects/{project_id}/nodes")
        nodes = nodes_response.json() if nodes_response.status_code == 200 else []
        
        # Liens du projet
        links_response = requests.get(f"http://localhost:3080/v2/projects/{project_id}/links")
        links = links_response.json() if links_response.status_code == 200 else []
        
        # Analyse des nœuds
        node_status = {}
        cloud_node = None
        
        for node in nodes:
            name = node.get('name', 'Unknown')
            status = node.get('status', 'unknown')
            node_type = node.get('node_type', 'unknown')
            
            node_status[name] = {
                'status': status,
                'type': node_type,
                'node_id': node.get('node_id')
            }
            
            if node_type == 'cloud' and 'Cloud1' in name:
                cloud_node = node
        
        return {
            "project_name": project_info.get('name'),
            "project_status": project_info.get('status'),
            "total_nodes": len(nodes),
            "total_links": len(links),
            "node_status": node_status,
            "cloud_node": cloud_node
        }
        
    except Exception as e:
        return {"error": str(e)}

def check_bridges() -> Dict:
    """Vérifie l'état des bridges système."""
    bridges_to_check = ["br-vlan10", "br-vlan20", "br-vlan41", "br-vlan30"]
    bridge_status = {}
    
    for bridge in bridges_to_check:
        try:
            result = subprocess.run(['ip', 'link', 'show', bridge], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                # Bridge existe, vérifier l'IP
                ip_result = subprocess.run(['ip', 'addr', 'show', bridge], 
                                         capture_output=True, text=True)
                
                bridge_status[bridge] = {
                    'exists': True,
                    'details': ip_result.stdout if ip_result.returncode == 0 else "Info non disponible"
                }
            else:
                bridge_status[bridge] = {'exists': False}
                
        except Exception as e:
            bridge_status[bridge] = {'exists': False, 'error': str(e)}
    
    return bridge_status

def test_basic_connectivity() -> Dict:
    """Teste la connectivité de base."""
    test_ips = [
        ("PC1", "192.168.20.10"),
        ("Admin", "192.168.41.10"),
        ("Server-Web", "192.168.10.10"),
        ("Server-Mail", "192.168.10.11"),
        ("Server-DB", "192.168.30.10")
    ]
    
    connectivity = {}
    
    for name, ip in test_ips:
        try:
            result = subprocess.run(['ping', '-c', '1', '-W', '2', ip], 
                                  capture_output=True, timeout=3)
            connectivity[name] = {
                'ip': ip,
                'accessible': result.returncode == 0
            }
        except:
            connectivity[name] = {
                'ip': ip,
                'accessible': False
            }
    
    return connectivity

def main():
    """Diagnostic complet."""
    logger.info("🔍 DIAGNOSTIC RAPIDE DES PROBLÈMES GNS3")
    logger.info("=" * 50)
    
    # 1. Vérifier l'API GNS3
    logger.info("📋 1. Vérification API GNS3")
    api_ok = check_gns3_api()
    
    if not api_ok:
        logger.error("❌ Impossible de continuer sans API GNS3")
        return 1
    
    # 2. Vérifier le projet
    logger.info("📋 2. Vérification projet hybrido")
    project_status = check_project_status()
    
    if "error" in project_status:
        logger.error(f"❌ Erreur projet: {project_status['error']}")
        return 1
    
    logger.info(f"✅ Projet: {project_status['project_name']} ({project_status['project_status']})")
    logger.info(f"📊 Nœuds: {project_status['total_nodes']}, Liens: {project_status['total_links']}")
    
    # Analyser Cloud1
    cloud_node = project_status.get('cloud_node')
    if cloud_node:
        logger.info(f"☁️ Cloud1: {cloud_node.get('status', 'unknown')} (ID: {cloud_node.get('node_id')})")
        if cloud_node.get('status') != 'started':
            logger.warning("⚠️ PROBLÈME IDENTIFIÉ: Cloud1 n'est pas démarré")
    else:
        logger.error("❌ PROBLÈME IDENTIFIÉ: Cloud1 non trouvé")
    
    # Analyser les nœuds
    logger.info("📋 3. Analyse des nœuds")
    node_status = project_status.get('node_status', {})
    stopped_nodes = [name for name, info in node_status.items() if info['status'] != 'started']
    
    if stopped_nodes:
        logger.warning(f"⚠️ Nœuds arrêtés: {', '.join(stopped_nodes)}")
    else:
        logger.info("✅ Tous les nœuds sont démarrés")
    
    # 3. Vérifier les bridges
    logger.info("📋 4. Vérification bridges système")
    bridges = check_bridges()
    
    missing_bridges = [bridge for bridge, info in bridges.items() if not info.get('exists')]
    if missing_bridges:
        logger.warning(f"⚠️ PROBLÈME IDENTIFIÉ: Bridges manquants: {', '.join(missing_bridges)}")
    else:
        logger.info("✅ Tous les bridges système existent")
    
    # 4. Test connectivité
    logger.info("📋 5. Test connectivité de base")
    connectivity = test_basic_connectivity()
    
    accessible = [name for name, info in connectivity.items() if info['accessible']]
    inaccessible = [name for name, info in connectivity.items() if not info['accessible']]
    
    logger.info(f"✅ Équipements accessibles: {', '.join(accessible) if accessible else 'Aucun'}")
    if inaccessible:
        logger.warning(f"❌ PROBLÈME IDENTIFIÉ: Équipements inaccessibles: {', '.join(inaccessible)}")
    
    # Résumé des problèmes
    logger.info("📋 6. RÉSUMÉ DES PROBLÈMES IDENTIFIÉS")
    problems = []
    
    if cloud_node and cloud_node.get('status') != 'started':
        problems.append("Cloud1 arrêté")
    if not cloud_node:
        problems.append("Cloud1 non trouvé")
    if stopped_nodes:
        problems.append(f"{len(stopped_nodes)} nœuds arrêtés")
    if missing_bridges:
        problems.append(f"{len(missing_bridges)} bridges manquants")
    if inaccessible:
        problems.append(f"{len(inaccessible)}/{len(connectivity)} équipements inaccessibles")
    
    if problems:
        logger.warning("⚠️ PROBLÈMES DÉTECTÉS:")
        for i, problem in enumerate(problems, 1):
            logger.warning(f"   {i}. {problem}")
        logger.info("🔧 Utilisez fix_specific_issues.py pour corriger ces problèmes")
        return 1
    else:
        logger.info("🎉 AUCUN PROBLÈME DÉTECTÉ")
        return 0

if __name__ == "__main__":
    exit(main())