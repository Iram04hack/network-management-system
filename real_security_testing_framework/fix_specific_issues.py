#!/usr/bin/env python3
"""
Correction Spécifique des Problèmes GNS3 Identifiés
==================================================

Ce script corrige les problèmes spécifiques identifiés dans les logs :
1. Cloud1 arrêté ("Cloud1 (cloud): stopped")
2. Erreurs HTTP 409 lors des connexions
3. Connectivité limitée (2/15 équipements)
4. Serveurs QEMU non responsifs

Auteur: Claude Code (Investigation des logs du 2025-07-20)
"""

import requests
import time
import logging
import subprocess
import json
from typing import Dict, List, Optional, Tuple

# Configuration logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class GNS3SpecificFixer:
    def __init__(self):
        self.gns3_url = "http://localhost:3080/v2"
        self.project_id = "6b858ee5-4a49-4f72-b437-8dcd8d876bad"  # Projet hybrido
        self.session = requests.Session()
        self.cloud_node_id = None
        self.issues_fixed = []
        self.connectivity_results = {}
        
    def get_project_nodes(self) -> List[Dict]:
        """Récupère tous les nœuds du projet."""
        try:
            response = self.session.get(f"{self.gns3_url}/projects/{self.project_id}/nodes")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"❌ Erreur récupération nœuds: {e}")
            return []

    def get_project_links(self) -> List[Dict]:
        """Récupère tous les liens du projet."""
        try:
            response = self.session.get(f"{self.gns3_url}/projects/{self.project_id}/links")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"❌ Erreur récupération liens: {e}")
            return []

    def find_cloud_node(self, nodes: List[Dict]) -> Optional[Dict]:
        """Trouve le nœud Cloud1."""
        for node in nodes:
            if node.get('node_type') == 'cloud' and 'Cloud1' in node.get('name', ''):
                return node
        return None

    def fix_issue_1_cloud_stopped(self) -> bool:
        """Corrige le problème : Cloud1 arrêté."""
        logger.info("🔧 CORRECTION ISSUE #1: Cloud1 arrêté")
        
        try:
            nodes = self.get_project_nodes()
            cloud_node = self.find_cloud_node(nodes)
            
            if not cloud_node:
                logger.error("❌ Cloud1 non trouvé")
                return False
                
            self.cloud_node_id = cloud_node['node_id']
            current_status = cloud_node.get('status', 'unknown')
            
            logger.info(f"📊 Cloud1 status actuel: {current_status}")
            
            if current_status != 'started':
                logger.info("🚀 Démarrage de Cloud1...")
                
                # Démarrer Cloud1
                start_response = self.session.post(
                    f"{self.gns3_url}/projects/{self.project_id}/nodes/{self.cloud_node_id}/start"
                )
                
                if start_response.status_code == 200:
                    logger.info("✅ Cloud1 démarré avec succès")
                    self.issues_fixed.append("Cloud1 démarré")
                    
                    # Attendre la stabilisation
                    time.sleep(5)
                    return True
                else:
                    logger.error(f"❌ Erreur démarrage Cloud1: HTTP {start_response.status_code}")
                    logger.error(f"Response: {start_response.text}")
                    return False
            else:
                logger.info("✅ Cloud1 déjà démarré")
                return True
                
        except Exception as e:
            logger.error(f"❌ Erreur correction Cloud1: {e}")
            return False

    def fix_issue_2_http_409_conflicts(self) -> bool:
        """Corrige les erreurs HTTP 409 (conflits de connexions)."""
        logger.info("🔧 CORRECTION ISSUE #2: Erreurs HTTP 409 (conflits)")
        
        try:
            # Récupérer les liens existants
            links = self.get_project_links()
            logger.info(f"📊 {len(links)} liens existants dans le projet")
            
            # Identifier les liens problématiques vers Cloud1
            cloud_links = []
            for link in links:
                nodes_in_link = link.get('nodes', [])
                for node_info in nodes_in_link:
                    if node_info.get('node_id') == self.cloud_node_id:
                        cloud_links.append(link)
                        break
            
            logger.info(f"📊 {len(cloud_links)} liens existants vers Cloud1")
            
            # Supprimer tous les liens existants vers Cloud1 pour éviter les conflits
            deleted_links = 0
            for link in cloud_links:
                link_id = link.get('link_id')
                if link_id:
                    try:
                        delete_response = self.session.delete(
                            f"{self.gns3_url}/projects/{self.project_id}/links/{link_id}"
                        )
                        if delete_response.status_code == 204:
                            deleted_links += 1
                            logger.debug(f"🗑️ Lien supprimé: {link_id}")
                        else:
                            logger.warning(f"⚠️ Erreur suppression lien {link_id}: HTTP {delete_response.status_code}")
                    except Exception as e:
                        logger.warning(f"⚠️ Erreur suppression lien {link_id}: {e}")
            
            logger.info(f"🗑️ {deleted_links} liens supprimés pour éviter les conflits")
            
            # Attendre la stabilisation
            time.sleep(3)
            
            if deleted_links > 0:
                self.issues_fixed.append(f"{deleted_links} liens conflictuels supprimés")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur correction conflits HTTP 409: {e}")
            return False

    def fix_issue_3_create_clean_connections(self) -> bool:
        """Crée des connexions propres vers Cloud1."""
        logger.info("🔧 CORRECTION ISSUE #3: Création de connexions propres")
        
        # Équipements critiques à connecter (basé sur les logs)
        critical_equipment = {
            "PC1": {"port": 1, "target_network": "VLAN_20"},
            "Admin": {"port": 2, "target_network": "VLAN_41"}, 
            "Server-Web": {"port": 0, "target_network": "VLAN_10"},
            "Server-Mail": {"port": 0, "target_network": "VLAN_10"},
            "Server-DNS": {"port": 0, "target_network": "VLAN_10"},
            "Server-DB": {"port": 3, "target_network": "VLAN_30"},
            "PostTest": {"port": 3, "target_network": "VLAN_30"}
        }
        
        try:
            nodes = self.get_project_nodes()
            nodes_by_name = {node.get('name'): node for node in nodes}
            
            connections_created = 0
            
            for equipment_name, config in critical_equipment.items():
                if equipment_name not in nodes_by_name:
                    logger.warning(f"⚠️ Équipement {equipment_name} non trouvé")
                    continue
                
                equipment_node = nodes_by_name[equipment_name]
                equipment_id = equipment_node['node_id']
                cloud_port = config["port"]
                
                logger.info(f"🔌 Connexion {equipment_name} → Cloud1 (port {cloud_port})")
                
                # Créer le lien
                link_data = {
                    "nodes": [
                        {
                            "node_id": equipment_id,
                            "adapter_number": 0,
                            "port_number": 0
                        },
                        {
                            "node_id": self.cloud_node_id,
                            "adapter_number": 0,
                            "port_number": cloud_port
                        }
                    ]
                }
                
                try:
                    response = self.session.post(
                        f"{self.gns3_url}/projects/{self.project_id}/links",
                        json=link_data
                    )
                    
                    if response.status_code in [200, 201]:
                        logger.info(f"✅ {equipment_name} connecté au cloud (port {cloud_port})")
                        connections_created += 1
                    else:
                        logger.warning(f"⚠️ Échec connexion {equipment_name}: HTTP {response.status_code}")
                        logger.debug(f"Response: {response.text}")
                        
                except Exception as e:
                    logger.warning(f"⚠️ Erreur connexion {equipment_name}: {e}")
                
                time.sleep(1)  # Délai entre connexions
            
            logger.info(f"🔌 {connections_created} connexions créées")
            self.issues_fixed.append(f"{connections_created} nouvelles connexions au cloud")
            
            return connections_created > 0
            
        except Exception as e:
            logger.error(f"❌ Erreur création connexions: {e}")
            return False

    def fix_issue_4_qemu_servers(self) -> bool:
        """Corrige les problèmes des serveurs QEMU non responsifs."""
        logger.info("🔧 CORRECTION ISSUE #4: Serveurs QEMU non responsifs")
        
        # Serveurs QEMU problématiques (basé sur les logs)
        qemu_servers = ["Server-Mail", "Server-DNS", "Server-DB", "PostTest", "Server-Web", "Server-Fichiers"]
        
        try:
            nodes = self.get_project_nodes()
            nodes_by_name = {node.get('name'): node for node in nodes}
            
            restarted_servers = 0
            
            for server_name in qemu_servers:
                if server_name not in nodes_by_name:
                    logger.warning(f"⚠️ Serveur {server_name} non trouvé")
                    continue
                
                server_node = nodes_by_name[server_name]
                server_id = server_node['node_id']
                current_status = server_node.get('status', 'unknown')
                
                logger.info(f"🖥️ Redémarrage {server_name} (status: {current_status})")
                
                try:
                    # Arrêter le serveur
                    stop_response = self.session.post(
                        f"{self.gns3_url}/projects/{self.project_id}/nodes/{server_id}/stop"
                    )
                    
                    if stop_response.status_code in [200, 204]:
                        logger.debug(f"🛑 {server_name} arrêté")
                        time.sleep(3)
                        
                        # Redémarrer le serveur
                        start_response = self.session.post(
                            f"{self.gns3_url}/projects/{self.project_id}/nodes/{server_id}/start"
                        )
                        
                        if start_response.status_code == 200:
                            logger.info(f"✅ {server_name} redémarré")
                            restarted_servers += 1
                        else:
                            logger.warning(f"⚠️ Erreur redémarrage {server_name}: HTTP {start_response.status_code}")
                    else:
                        logger.warning(f"⚠️ Erreur arrêt {server_name}: HTTP {stop_response.status_code}")
                        
                except Exception as e:
                    logger.warning(f"⚠️ Erreur redémarrage {server_name}: {e}")
                
                time.sleep(2)  # Délai entre redémarrages
            
            logger.info(f"🖥️ {restarted_servers} serveurs QEMU redémarrés")
            
            if restarted_servers > 0:
                self.issues_fixed.append(f"{restarted_servers} serveurs QEMU redémarrés")
                
                # Attendre la stabilisation des serveurs
                logger.info("⏳ Attente stabilisation serveurs (30s)...")
                time.sleep(30)
            
            return restarted_servers > 0
            
        except Exception as e:
            logger.error(f"❌ Erreur correction serveurs QEMU: {e}")
            return False

    def configure_system_bridges(self) -> bool:
        """Configure les bridges système nécessaires."""
        logger.info("🔧 CORRECTION: Configuration des bridges système")
        
        bridges_config = [
            ("br-vlan10", "192.168.10.1"),
            ("br-vlan20", "192.168.20.1"),
            ("br-vlan41", "192.168.41.1"),
            ("br-vlan30", "192.168.30.1")
        ]
        
        configured_bridges = 0
        
        for bridge_name, ip_address in bridges_config:
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
                    
                    configured_bridges += 1
                    logger.info(f"✅ Bridge {bridge_name} créé avec IP {ip_address}")
                else:
                    logger.debug(f"✅ Bridge {bridge_name} existe déjà")
                    configured_bridges += 1
                    
            except Exception as e:
                logger.warning(f"⚠️ Erreur configuration bridge {bridge_name}: {e}")
        
        logger.info(f"🌉 {configured_bridges}/{len(bridges_config)} bridges configurés")
        
        if configured_bridges > 0:
            self.issues_fixed.append(f"{configured_bridges} bridges système configurés")
        
        return configured_bridges >= len(bridges_config) * 0.8  # 80% minimum

    def configure_cloud_ports(self) -> bool:
        """Configure les ports du Cloud1 pour pointer vers les bridges."""
        logger.info("🔧 CORRECTION: Configuration des ports Cloud1")
        
        try:
            # Configuration des ports Cloud1
            cloud_config = {
                "ports_mapping": [
                    {
                        "interface": "br-vlan10",
                        "name": "br-vlan10",
                        "port_number": 0,
                        "type": "ethernet"
                    },
                    {
                        "interface": "br-vlan20", 
                        "name": "br-vlan20",
                        "port_number": 1,
                        "type": "ethernet"
                    },
                    {
                        "interface": "br-vlan41",
                        "name": "br-vlan41", 
                        "port_number": 2,
                        "type": "ethernet"
                    },
                    {
                        "interface": "br-vlan30",
                        "name": "br-vlan30",
                        "port_number": 3,
                        "type": "ethernet"
                    }
                ]
            }
            
            # Envoyer la configuration
            response = self.session.put(
                f"{self.gns3_url}/projects/{self.project_id}/nodes/{self.cloud_node_id}",
                json=cloud_config
            )
            
            if response.status_code == 200:
                logger.info("✅ Configuration Cloud1 mise à jour")
                self.issues_fixed.append("Ports Cloud1 configurés vers bridges")
                return True
            else:
                logger.warning(f"⚠️ Échec configuration Cloud1: HTTP {response.status_code}")
                logger.debug(f"Response: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Erreur configuration Cloud1: {e}")
            return False

    def test_connectivity(self) -> Dict[str, bool]:
        """Teste la connectivité vers les équipements critiques."""
        logger.info("🔍 TEST DE CONNECTIVITÉ FINALE")
        
        # IPs à tester (basées sur les logs)
        test_targets = {
            "PC1": "192.168.20.10",
            "Admin": "192.168.41.10", 
            "Server-Web": "192.168.10.10",
            "Server-Mail": "192.168.10.11",
            "Server-DB": "192.168.30.10"
        }
        
        results = {}
        accessible_count = 0
        
        for name, ip in test_targets.items():
            try:
                result = subprocess.run(
                    ['ping', '-c', '2', '-W', '3', ip],
                    capture_output=True,
                    timeout=5
                )
                
                accessible = result.returncode == 0
                results[name] = accessible
                
                if accessible:
                    accessible_count += 1
                    logger.info(f"   ✅ {name} ({ip}) ACCESSIBLE")
                else:
                    logger.info(f"   ❌ {name} ({ip}) inaccessible")
                    
            except subprocess.TimeoutExpired:
                results[name] = False
                logger.info(f"   ❌ {name} ({ip}) timeout")
            except Exception as e:
                results[name] = False
                logger.warning(f"   ❌ {name} ({ip}) erreur: {e}")
        
        self.connectivity_results = results
        connectivity_rate = (accessible_count / len(test_targets)) * 100
        
        logger.info(f"📊 CONNECTIVITÉ FINALE: {accessible_count}/{len(test_targets)} ({connectivity_rate:.1f}%)")
        
        return results

    def run_complete_fix(self) -> Tuple[bool, Dict]:
        """Exécute la correction complète de tous les problèmes identifiés."""
        logger.info("🚀 CORRECTION COMPLÈTE DES PROBLÈMES GNS3 IDENTIFIÉS")
        logger.info("=" * 70)
        
        start_time = time.time()
        all_success = True
        results = {
            "issues_fixed": [],
            "connectivity_before": {},
            "connectivity_after": {},
            "success_rate": 0,
            "execution_time": 0
        }
        
        try:
            # Étape 1: Corriger Cloud1 arrêté
            logger.info("📋 ÉTAPE 1: Correction Cloud1 arrêté")
            if not self.fix_issue_1_cloud_stopped():
                logger.error("❌ Échec correction Cloud1")
                all_success = False
            
            # Étape 2: Corriger les conflits HTTP 409
            logger.info("📋 ÉTAPE 2: Correction conflits HTTP 409")
            if not self.fix_issue_2_http_409_conflicts():
                logger.error("❌ Échec correction conflits")
                all_success = False
            
            # Étape 3: Configurer les bridges système
            logger.info("📋 ÉTAPE 3: Configuration bridges système")
            if not self.configure_system_bridges():
                logger.error("❌ Échec configuration bridges")
                all_success = False
            
            # Étape 4: Configurer les ports Cloud1
            logger.info("📋 ÉTAPE 4: Configuration ports Cloud1")
            if not self.configure_cloud_ports():
                logger.error("❌ Échec configuration ports Cloud1")
                all_success = False
            
            # Étape 5: Créer les connexions propres
            logger.info("📋 ÉTAPE 5: Création connexions propres")
            if not self.fix_issue_3_create_clean_connections():
                logger.error("❌ Échec création connexions")
                all_success = False
            
            # Étape 6: Corriger les serveurs QEMU
            logger.info("📋 ÉTAPE 6: Correction serveurs QEMU")
            if not self.fix_issue_4_qemu_servers():
                logger.warning("⚠️ Correction partielle serveurs QEMU")
            
            # Étape 7: Test final de connectivité
            logger.info("📋 ÉTAPE 7: Test connectivité finale")
            connectivity = self.test_connectivity()
            
            # Calcul des résultats
            accessible_count = sum(1 for accessible in connectivity.values() if accessible)
            total_targets = len(connectivity)
            success_rate = (accessible_count / total_targets) * 100 if total_targets > 0 else 0
            
            execution_time = time.time() - start_time
            
            # Résultats finaux
            results.update({
                "issues_fixed": self.issues_fixed,
                "connectivity_after": connectivity,
                "success_rate": success_rate,
                "execution_time": execution_time
            })
            
            # Résumé final
            logger.info("📊 RÉSUMÉ DE LA CORRECTION")
            logger.info("=" * 70)
            logger.info(f"🔧 Corrections appliquées: {len(self.issues_fixed)}")
            for fix in self.issues_fixed:
                logger.info(f"   ✅ {fix}")
            
            logger.info(f"📊 Connectivité finale: {accessible_count}/{total_targets} ({success_rate:.1f}%)")
            logger.info(f"⏱️ Temps d'exécution: {execution_time:.1f}s")
            
            if success_rate >= 80:
                logger.info("🎉 CORRECTION RÉUSSIE: Connectivité excellente")
                return True, results
            elif success_rate >= 50:
                logger.info("✅ CORRECTION PARTIELLE: Connectivité acceptable")
                return True, results
            else:
                logger.warning("⚠️ CORRECTION LIMITÉE: Problèmes persistent")
                return False, results
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de la correction complète: {e}")
            results["execution_time"] = time.time() - start_time
            return False, results

def main():
    """Fonction principale."""
    logger.info("🚀 CORRECTION SPÉCIFIQUE DES PROBLÈMES GNS3 IDENTIFIÉS")
    logger.info("   Basé sur l'analyse des logs du 2025-07-20 12:12:04")
    
    fixer = GNS3SpecificFixer()
    
    try:
        success, results = fixer.run_complete_fix()
        
        if success:
            logger.info("🎉 CORRECTION TERMINÉE AVEC SUCCÈS")
            logger.info("💡 Les équipements devraient maintenant être accessibles")
            return 0
        else:
            logger.warning("⚠️ CORRECTION PARTIELLE - Vérification manuelle recommandée")
            return 1
            
    except Exception as e:
        logger.error(f"❌ Erreur critique: {e}")
        return 2

if __name__ == "__main__":
    exit(main())