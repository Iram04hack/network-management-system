#!/usr/bin/env python3
"""
Script de correction automatique de la topologie GNS3
====================================================

Ce script reconfigure automatiquement la topologie GNS3 pour connecter
tous les équipements aux bridges hôte et les rendre accessibles.

Auteur: Claude Code
Date: 2025-07-20
"""

import logging
import sys
import time
import requests
import subprocess
from pathlib import Path

# Configuration logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class GNS3TopologyFixer:
    def __init__(self):
        self.gns3_url = "http://localhost:3080/v2"
        self.project_id = "6b858ee5-4a49-4f72-b437-8dcd8d876bad"
        self.session = requests.Session()
        
    def get_project_nodes(self):
        """Récupère tous les nœuds du projet"""
        try:
            response = self.session.get(f"{self.gns3_url}/projects/{self.project_id}/nodes")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"❌ Erreur récupération nœuds: {e}")
            return []
    
    def get_project_links(self):
        """Récupère tous les liens du projet"""
        try:
            response = self.session.get(f"{self.gns3_url}/projects/{self.project_id}/links")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"❌ Erreur récupération liens: {e}")
            return []
    
    def find_cloud_node(self, nodes):
        """Trouve le nœud Cloud1"""
        for node in nodes:
            if node.get('node_type') == 'cloud' and 'Cloud1' in node.get('name', ''):
                return node
        return None
    
    def find_node_by_name(self, nodes, name):
        """Trouve un nœud par nom"""
        for node in nodes:
            if node.get('name') == name:
                return node
        return None
    
    def create_bridge_if_needed(self, bridge_name, ip_address):
        """Crée un bridge s'il n'existe pas"""
        try:
            # Vérifier si le bridge existe
            result = subprocess.run(['ip', 'link', 'show', bridge_name], 
                                  capture_output=True, text=True)
            
            if result.returncode != 0:
                logger.info(f"🔧 Création du bridge {bridge_name}")
                
                # Créer le bridge
                subprocess.run(['sudo', 'brctl', 'addbr', bridge_name], check=True)
                subprocess.run(['sudo', 'ip', 'addr', 'add', f'{ip_address}/24', 'dev', bridge_name], check=True)
                subprocess.run(['sudo', 'ip', 'link', 'set', bridge_name, 'up'], check=True)
                
                logger.info(f"✅ Bridge {bridge_name} créé avec IP {ip_address}")
                return True
            else:
                logger.info(f"✅ Bridge {bridge_name} existe déjà")
                return True
                
        except Exception as e:
            logger.error(f"❌ Erreur création bridge {bridge_name}: {e}")
            return False
    
    def setup_bridges(self):
        """Configure tous les bridges nécessaires"""
        logger.info("🔧 CONFIGURATION DES BRIDGES SYSTÈME")
        
        bridges_config = [
            ("br-vlan10", "192.168.10.1"),
            ("br-vlan20", "192.168.20.1"), 
            ("br-vlan41", "192.168.41.1"),
            ("br-vlan30", "192.168.30.1"),
            ("br-vlan31", "192.168.31.1")
        ]
        
        successful_bridges = 0
        
        for bridge_name, ip_address in bridges_config:
            if self.create_bridge_if_needed(bridge_name, ip_address):
                successful_bridges += 1
        
        logger.info(f"📊 Bridges configurés: {successful_bridges}/{len(bridges_config)}")
        return successful_bridges >= 3
    
    def connect_equipment_to_cloud(self, equipment_node, cloud_node, port_mapping):
        """Connecte un équipement au cloud"""
        try:
            equipment_name = equipment_node.get('name')
            
            # Chercher un port libre sur l'équipement (port 0 généralement)
            equipment_port = 0
            
            # Déterminer le port cloud selon le VLAN
            if "192.168.10." in str(equipment_node):  # VLAN 10
                cloud_port = 0
            elif "192.168.20." in str(equipment_node):  # VLAN 20  
                cloud_port = 1
            elif "192.168.41." in str(equipment_node):  # VLAN 41
                cloud_port = 2
            else:
                cloud_port = 3  # Port par défaut
                
            # Utiliser le mapping fourni
            if equipment_name in port_mapping:
                cloud_port = port_mapping[equipment_name]
            
            # Créer le lien
            link_data = {
                "nodes": [
                    {
                        "node_id": equipment_node['node_id'],
                        "adapter_number": 0,
                        "port_number": equipment_port
                    },
                    {
                        "node_id": cloud_node['node_id'],
                        "adapter_number": 0,
                        "port_number": cloud_port
                    }
                ]
            }
            
            response = self.session.post(
                f"{self.gns3_url}/projects/{self.project_id}/links",
                json=link_data
            )
            
            if response.status_code in [200, 201]:
                logger.info(f"✅ {equipment_name} connecté au cloud (port {cloud_port})")
                return True
            else:
                logger.warning(f"⚠️ Connexion {equipment_name} échouée: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Erreur connexion {equipment_name}: {e}")
            return False
    
    def remove_existing_links(self, equipment_node):
        """Supprime les liens existants d'un équipement pour éviter les conflits"""
        try:
            links = self.get_project_links()
            equipment_id = equipment_node['node_id']
            
            for link in links:
                # Vérifier si ce lien concerne cet équipement
                nodes_in_link = link.get('nodes', [])
                for node_info in nodes_in_link:
                    if node_info.get('node_id') == equipment_id:
                        # Supprimer ce lien
                        link_id = link.get('link_id')
                        if link_id:
                            delete_response = self.session.delete(
                                f"{self.gns3_url}/projects/{self.project_id}/links/{link_id}"
                            )
                            if delete_response.status_code == 204:
                                logger.debug(f"🗑️ Lien supprimé pour {equipment_node.get('name')}")
                            
        except Exception as e:
            logger.debug(f"⚠️ Erreur suppression liens: {e}")
    
    def fix_topology(self):
        """Corrige la topologie complète"""
        logger.info("🚀 CORRECTION AUTOMATIQUE DE LA TOPOLOGIE GNS3")
        logger.info("=" * 60)
        
        try:
            # 1. Configuration des bridges système
            logger.info("📊 ÉTAPE 1: Configuration des bridges système")
            if not self.setup_bridges():
                logger.error("❌ Échec configuration bridges")
                return False
            
            # 2. Récupération des nœuds
            logger.info("📊 ÉTAPE 2: Analyse de la topologie actuelle")
            nodes = self.get_project_nodes()
            if not nodes:
                logger.error("❌ Impossible de récupérer les nœuds")
                return False
                
            cloud_node = self.find_cloud_node(nodes)
            if not cloud_node:
                logger.error("❌ Nœud Cloud1 non trouvé")
                return False
                
            logger.info(f"✅ Cloud1 trouvé: {cloud_node['node_id']}")
            
            # 3. Équipements critiques à connecter
            logger.info("📊 ÉTAPE 3: Connexion des équipements critiques")
            
            critical_equipment = [
                "PC1",           # Test client
                "Admin",         # Admin client  
                "Server-Web",    # Serveur web
                "Server-Mail",   # Serveur mail
                "Server-DNS",    # Serveur DNS
                "Server-DB",     # Serveur base de données
                "PostTest"       # Serveur de test
            ]
            
            # Mapping des équipements vers les ports cloud (bridges)
            port_mapping = {
                "PC1": 1,           # br-vlan20
                "Admin": 2,         # br-vlan41  
                "Server-Web": 0,    # br-vlan10
                "Server-Mail": 0,   # br-vlan10
                "Server-DNS": 0,    # br-vlan10
                "Server-DB": 3,     # br-vlan30
                "PostTest": 3       # br-vlan32
            }
            
            successful_connections = 0
            
            for equipment_name in critical_equipment:
                equipment_node = self.find_node_by_name(nodes, equipment_name)
                if equipment_node:
                    logger.info(f"🔧 Connexion {equipment_name}...")
                    
                    # Supprimer les liens existants pour éviter les conflits
                    self.remove_existing_links(equipment_node)
                    time.sleep(1)
                    
                    # Connecter au cloud
                    if self.connect_equipment_to_cloud(equipment_node, cloud_node, port_mapping):
                        successful_connections += 1
                    
                    time.sleep(2)  # Délai entre connexions
                else:
                    logger.warning(f"⚠️ Équipement {equipment_name} non trouvé")
            
            # 4. Test de connectivité
            logger.info("📊 ÉTAPE 4: Test de connectivité")
            time.sleep(10)  # Attendre que les connexions prennent effet
            
            connectivity_count = self.test_connectivity()
            
            # 5. Résumé
            logger.info("📊 ÉTAPE 5: Résumé de la correction")
            logger.info("=" * 60)
            logger.info(f"🔧 Équipements connectés: {successful_connections}/{len(critical_equipment)}")
            logger.info(f"🌐 Équipements accessibles: {connectivity_count}")
            
            if connectivity_count >= 3:
                logger.info("🎉 CORRECTION RÉUSSIE: Topologie fonctionnelle")
                return True
            elif successful_connections >= 4:
                logger.info("✅ CORRECTION PARTIELLE: Connexions établies")
                return True
            else:
                logger.warning("⚠️ CORRECTION LIMITÉE: Problèmes persistent")
                return False
                
        except Exception as e:
            logger.error(f"❌ Erreur correction topologie: {e}")
            return False
    
    def test_connectivity(self):
        """Teste la connectivité vers les équipements"""
        test_ips = [
            "192.168.20.10",  # PC1
            "192.168.41.10",  # Admin
            "192.168.10.10",  # Server-Web
            "192.168.10.11",  # Server-Mail
            "192.168.30.10"   # Server-DB
        ]
        
        accessible_count = 0
        
        for ip in test_ips:
            try:
                result = subprocess.run(
                    ['ping', '-c', '1', '-W', '2', ip],
                    capture_output=True,
                    timeout=3
                )
                if result.returncode == 0:
                    logger.info(f"   ✅ {ip} accessible")
                    accessible_count += 1
                else:
                    logger.info(f"   ❌ {ip} inaccessible")
            except:
                logger.info(f"   ❌ {ip} timeout")
        
        return accessible_count

def main():
    """Fonction principale"""
    logger.info("🚀 DÉMARRAGE DE LA CORRECTION TOPOLOGIE GNS3")
    
    fixer = GNS3TopologyFixer()
    
    try:
        success = fixer.fix_topology()
        
        if success:
            logger.info("🎉 CORRECTION TERMINÉE AVEC SUCCÈS")
            logger.info("💡 Les équipements devraient maintenant être accessibles pour les tests")
        else:
            logger.warning("⚠️ CORRECTION PARTIELLE - Vérification manuelle recommandée")
            
    except Exception as e:
        logger.error(f"❌ Erreur critique: {e}")
        return False
    
    return success

if __name__ == "__main__":
    main()