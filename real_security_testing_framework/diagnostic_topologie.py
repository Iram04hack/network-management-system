#!/usr/bin/env python3
"""
Diagnostic de topologie GNS3 et connectivité
===========================================

Script pour diagnostiquer les problèmes de connectivité dans le projet Hybrido
et proposer des corrections automatiques.

Auteur: Équipe de développement NMS  
Date: 2025-07-20
"""

import requests
import json
import subprocess
import logging
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

class GNS3TopologyDiagnostic:
    """Diagnostic de la topologie GNS3"""
    
    def __init__(self, gns3_host: str = "localhost", gns3_port: int = 3080):
        self.gns3_base_url = f"http://{gns3_host}:{gns3_port}/v2"
        self.project_id = None
        
    def find_hybrido_project(self) -> Optional[str]:
        """Trouve le projet Hybrido"""
        try:
            response = requests.get(f"{self.gns3_base_url}/projects", timeout=10)
            if response.status_code == 200:
                projects = response.json()
                for project in projects:
                    if project["name"].lower() == "hybrido":
                        self.project_id = project["project_id"]
                        logger.info(f"✅ Projet Hybrido trouvé: {self.project_id}")
                        return self.project_id
                        
            logger.error("❌ Projet Hybrido non trouvé")
            return None
            
        except Exception as e:
            logger.error(f"❌ Erreur accès API GNS3: {e}")
            return None
    
    def get_project_nodes(self) -> List[Dict]:
        """Récupère tous les nœuds du projet"""
        if not self.project_id:
            return []
            
        try:
            response = requests.get(f"{self.gns3_base_url}/projects/{self.project_id}/nodes", timeout=10)
            if response.status_code == 200:
                nodes = response.json()
                logger.info(f"✅ {len(nodes)} nœuds trouvés dans le projet")
                return nodes
            else:
                logger.error(f"❌ Erreur récupération nœuds: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"❌ Erreur récupération nœuds: {e}")
            return []
    
    def get_project_links(self) -> List[Dict]:
        """Récupère tous les liens du projet"""
        if not self.project_id:
            return []
            
        try:
            response = requests.get(f"{self.gns3_base_url}/projects/{self.project_id}/links", timeout=10)
            if response.status_code == 200:
                links = response.json()
                logger.info(f"✅ {len(links)} liens trouvés dans le projet")
                return links
            else:
                logger.error(f"❌ Erreur récupération liens: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"❌ Erreur récupération liens: {e}")
            return []
    
    def analyze_cloud_connections(self, nodes: List[Dict], links: List[Dict]) -> Dict:
        """Analyse les connexions vers Cloud1"""
        cloud_node = None
        for node in nodes:
            if node["name"] == "Cloud1":
                cloud_node = node
                break
                
        if not cloud_node:
            logger.error("❌ Cloud1 non trouvé dans la topologie")
            return {"cloud_found": False, "connections": []}
        
        logger.info(f"✅ Cloud1 trouvé: {cloud_node['node_id']}")
        
        # Analyse des liens vers Cloud1
        cloud_connections = []
        for link in links:
            for node_link in link["nodes"]:
                if node_link["node_id"] == cloud_node["node_id"]:
                    # Trouve l'autre nœud de ce lien
                    other_node = None
                    for node_link2 in link["nodes"]:
                        if node_link2["node_id"] != cloud_node["node_id"]:
                            other_node = node_link2
                            break
                    
                    if other_node:
                        # Trouve le nom du nœud
                        node_name = "Unknown"
                        for node in nodes:
                            if node["node_id"] == other_node["node_id"]:
                                node_name = node["name"]
                                break
                                
                        cloud_connections.append({
                            "node_name": node_name,
                            "node_id": other_node["node_id"],
                            "port": node_link["label"]["text"] if "label" in node_link else "unknown",
                            "cloud_port": node_link2["label"]["text"] if "label" in node_link2 else "unknown"
                        })
        
        logger.info(f"📊 Cloud1 connecté à {len(cloud_connections)} équipements")
        for conn in cloud_connections:
            logger.info(f"   🔗 {conn['node_name']} (port {conn['port']}) → Cloud1 (port {conn['cloud_port']})")
            
        return {"cloud_found": True, "connections": cloud_connections}
    
    def check_host_bridges(self) -> Dict:
        """Vérifie les bridges de l'hôte"""
        try:
            result = subprocess.run(['ip', 'link', 'show', 'type', 'bridge'], 
                                  capture_output=True, text=True, timeout=10)
            
            bridges = []
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if 'br-' in line and 'state UP' in line:
                        bridge_name = line.split(':')[1].strip().split('@')[0]
                        bridges.append(bridge_name)
            
            logger.info(f"📊 {len(bridges)} bridges actifs trouvés sur l'hôte")
            for bridge in bridges:
                logger.info(f"   🌉 {bridge}")
                
            return {"bridges": bridges, "count": len(bridges)}
            
        except Exception as e:
            logger.error(f"❌ Erreur vérification bridges: {e}")
            return {"bridges": [], "count": 0}
    
    def check_tap_interface(self) -> Dict:
        """Vérifie l'interface TAP"""
        try:
            result = subprocess.run(['ip', 'addr', 'show', 'tap1'], 
                                  capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0:
                logger.info("✅ Interface tap1 configurée")
                for line in result.stdout.split('\n'):
                    if 'inet ' in line:
                        ip = line.strip().split()[1]
                        logger.info(f"   📡 IP: {ip}")
                        return {"configured": True, "ip": ip}
                        
                return {"configured": True, "ip": "non configurée"}
            else:
                logger.warning("⚠️ Interface tap1 non trouvée")
                return {"configured": False, "ip": None}
                
        except Exception as e:
            logger.error(f"❌ Erreur vérification tap1: {e}")
            return {"configured": False, "ip": None}
    
    def run_full_diagnostic(self) -> Dict:
        """Lance un diagnostic complet"""
        logger.info("🔍 DIAGNOSTIC COMPLET DE LA TOPOLOGIE HYBRIDO")
        logger.info("=" * 60)
        
        diagnostic_results = {}
        
        # 1. Recherche du projet
        project_id = self.find_hybrido_project()
        diagnostic_results["project_found"] = project_id is not None
        
        if not project_id:
            return diagnostic_results
        
        # 2. Analyse des nœuds
        nodes = self.get_project_nodes()
        diagnostic_results["nodes_count"] = len(nodes)
        diagnostic_results["nodes"] = {node["name"]: node["status"] for node in nodes}
        
        # 3. Analyse des liens
        links = self.get_project_links()
        diagnostic_results["links_count"] = len(links)
        
        # 4. Analyse Cloud1
        cloud_analysis = self.analyze_cloud_connections(nodes, links)
        diagnostic_results["cloud_analysis"] = cloud_analysis
        
        # 5. Vérification bridges hôte
        bridge_analysis = self.check_host_bridges()
        diagnostic_results["host_bridges"] = bridge_analysis
        
        # 6. Vérification TAP
        tap_analysis = self.check_tap_interface()
        diagnostic_results["tap_interface"] = tap_analysis
        
        # 7. Recommandations
        recommendations = self.generate_recommendations(diagnostic_results)
        diagnostic_results["recommendations"] = recommendations
        
        return diagnostic_results
    
    def generate_recommendations(self, results: Dict) -> List[str]:
        """Génère des recommandations basées sur le diagnostic"""
        recommendations = []
        
        if not results.get("tap_interface", {}).get("configured", False):
            recommendations.append("🔧 Configurer l'interface tap1 avec le script network_setup.sh")
        
        cloud_connections = results.get("cloud_analysis", {}).get("connections", [])
        if len(cloud_connections) == 0:
            recommendations.append("🔗 Aucun équipement connecté à Cloud1 - ajouter des connexions dans GNS3")
        elif len(cloud_connections) < 3:
            recommendations.append("🔗 Peu d'équipements connectés à Cloud1 - vérifier la topologie")
        
        bridge_count = results.get("host_bridges", {}).get("count", 0)
        if bridge_count == 0:
            recommendations.append("🌉 Aucun bridge Docker trouvé - vérifier la configuration réseau")
        
        return recommendations

def main():
    """Fonction principale"""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    diagnostic = GNS3TopologyDiagnostic()
    results = diagnostic.run_full_diagnostic()
    
    # Affichage du résumé
    print("\n" + "=" * 60)
    print("📊 RÉSUMÉ DU DIAGNOSTIC")
    print("=" * 60)
    
    print(f"🎯 Projet trouvé: {'✅ Oui' if results.get('project_found') else '❌ Non'}")
    print(f"📱 Nœuds GNS3: {results.get('nodes_count', 0)}")
    print(f"🔗 Liens GNS3: {results.get('links_count', 0)}")
    
    cloud_connections = results.get('cloud_analysis', {}).get('connections', [])
    print(f"☁️ Connexions Cloud1: {len(cloud_connections)}")
    
    bridge_count = results.get('host_bridges', {}).get('count', 0)
    print(f"🌉 Bridges hôte: {bridge_count}")
    
    tap_configured = results.get('tap_interface', {}).get('configured', False)
    print(f"📡 Interface TAP: {'✅ Configurée' if tap_configured else '❌ Non configurée'}")
    
    # Recommandations
    recommendations = results.get('recommendations', [])
    if recommendations:
        print(f"\n💡 RECOMMANDATIONS ({len(recommendations)}):")
        for i, rec in enumerate(recommendations, 1):
            print(f"   {i}. {rec}")
    else:
        print("\n✅ Aucune recommandation - topologie semble correcte")

if __name__ == "__main__":
    main()