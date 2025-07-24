#!/usr/bin/env python3
"""
Script de dépannage avancé GNS3 - Interventions manuelles
=========================================================

Script complémentaire pour des interventions manuelles avancées
lorsque l'investigation automatique ne suffit pas.

Auteur: Claude Code
Date: 2025-07-20
"""

import logging
import sys
import time
import requests
import subprocess
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any

# Configuration logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class GNS3AdvancedTroubleshooter:
    """Dépanneur avancé pour les problèmes GNS3 complexes"""
    
    def __init__(self, gns3_url: str = "http://localhost:3080/v2", 
                 project_id: Optional[str] = None):
        self.gns3_url = gns3_url
        self.project_id = project_id or "6b858ee5-4a49-4f72-b437-8dcd8d876bad"
        self.session = requests.Session()
        self.session.timeout = 10
    
    def force_stop_all_nodes(self) -> bool:
        """Force l'arrêt de tous les nœuds du projet"""
        try:
            logger.info("🛑 Arrêt forcé de tous les nœuds...")
            
            response = self.session.get(f"{self.gns3_url}/projects/{self.project_id}/nodes")
            nodes = response.json()
            
            stopped_count = 0
            
            for node in nodes:
                if node.get('status') == 'started':
                    node_id = node['node_id']
                    node_name = node.get('name', node_id)
                    
                    stop_response = self.session.post(
                        f"{self.gns3_url}/projects/{self.project_id}/nodes/{node_id}/stop"
                    )
                    
                    if stop_response.status_code in [200, 204]:
                        logger.info(f"   ✅ {node_name} arrêté")
                        stopped_count += 1
                    else:
                        logger.warning(f"   ⚠️ Échec arrêt {node_name}")
                    
                    time.sleep(1)
            
            logger.info(f"✅ {stopped_count} nœud(s) arrêté(s)")
            return stopped_count > 0
            
        except Exception as e:
            logger.error(f"❌ Erreur arrêt forcé: {e}")
            return False
    
    def reset_project_topology(self) -> bool:
        """Remet à zéro la topologie du projet"""
        try:
            logger.info("🔄 Remise à zéro de la topologie...")
            
            # Arrêter tous les nœuds
            self.force_stop_all_nodes()
            time.sleep(5)
            
            # Supprimer tous les liens
            response = self.session.get(f"{self.gns3_url}/projects/{self.project_id}/links")
            links = response.json()
            
            removed_links = 0
            for link in links:
                link_id = link.get('link_id')
                if link_id:
                    delete_response = self.session.delete(
                        f"{self.gns3_url}/projects/{self.project_id}/links/{link_id}"
                    )
                    if delete_response.status_code == 204:
                        removed_links += 1
                        time.sleep(0.5)
            
            logger.info(f"✅ {removed_links} lien(s) supprimé(s)")
            
            # Fermer et rouvrir le projet
            close_response = self.session.post(f"{self.gns3_url}/projects/{self.project_id}/close")
            time.sleep(3)
            
            open_response = self.session.post(f"{self.gns3_url}/projects/{self.project_id}/open")
            
            if open_response.status_code in [200, 201]:
                logger.info("✅ Projet rouvert avec succès")
                return True
            else:
                logger.error("❌ Échec réouverture du projet")
                return False
                
        except Exception as e:
            logger.error(f"❌ Erreur remise à zéro: {e}")
            return False
    
    def recreate_cloud_node(self) -> bool:
        """Recrée le nœud Cloud1 à partir de zéro"""
        try:
            logger.info("☁️ Recréation du nœud Cloud1...")
            
            # Supprimer l'ancien Cloud1 s'il existe
            response = self.session.get(f"{self.gns3_url}/projects/{self.project_id}/nodes")
            nodes = response.json()
            
            for node in nodes:
                if node.get('node_type') == 'cloud' and 'Cloud1' in node.get('name', ''):
                    node_id = node['node_id']
                    
                    # Arrêter d'abord
                    self.session.post(f"{self.gns3_url}/projects/{self.project_id}/nodes/{node_id}/stop")
                    time.sleep(2)
                    
                    # Supprimer
                    delete_response = self.session.delete(
                        f"{self.gns3_url}/projects/{self.project_id}/nodes/{node_id}"
                    )
                    
                    if delete_response.status_code == 204:
                        logger.info("   ✅ Ancien Cloud1 supprimé")
                    
                    break
            
            time.sleep(3)
            
            # Créer un nouveau nœud Cloud
            cloud_config = {
                "name": "Cloud1",
                "node_type": "cloud",
                "compute_id": "local",
                "x": -300,
                "y": -150,
                "ports_mapping": [
                    {"interface": "br-vlan10", "name": "br-vlan10", "port_number": 0, "type": "ethernet"},
                    {"interface": "br-vlan20", "name": "br-vlan20", "port_number": 1, "type": "ethernet"},
                    {"interface": "br-vlan41", "name": "br-vlan41", "port_number": 2, "type": "ethernet"},
                    {"interface": "br-vlan30", "name": "br-vlan30", "port_number": 3, "type": "ethernet"}
                ]
            }
            
            create_response = self.session.post(
                f"{self.gns3_url}/projects/{self.project_id}/nodes",
                json=cloud_config
            )
            
            if create_response.status_code in [200, 201]:
                new_cloud = create_response.json()
                logger.info(f"✅ Nouveau Cloud1 créé: {new_cloud['node_id']}")
                
                # Démarrer le nouveau cloud
                time.sleep(2)
                start_response = self.session.post(
                    f"{self.gns3_url}/projects/{self.project_id}/nodes/{new_cloud['node_id']}/start"
                )
                
                if start_response.status_code in [200, 204]:
                    logger.info("✅ Nouveau Cloud1 démarré")
                    return True
                else:
                    logger.warning("⚠️ Nouveau Cloud1 créé mais pas démarré")
                    return False
            else:
                logger.error(f"❌ Échec création nouveau Cloud1: {create_response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Erreur recréation Cloud1: {e}")
            return False
    
    def repair_system_bridges(self) -> bool:
        """Répare et reconfigure les bridges système"""
        try:
            logger.info("🌉 Réparation des bridges système...")
            
            bridges_config = [
                ("br-vlan10", "192.168.10.1"),
                ("br-vlan20", "192.168.20.1"), 
                ("br-vlan41", "192.168.41.1"),
                ("br-vlan30", "192.168.30.1"),
                ("br-vlan31", "192.168.31.1")
            ]
            
            for bridge_name, ip_address in bridges_config:
                logger.info(f"🔧 Réparation {bridge_name}...")
                
                # Supprimer le bridge existant
                subprocess.run(['sudo', 'ip', 'link', 'set', bridge_name, 'down'], 
                             capture_output=True, input="root\n", text=True)
                subprocess.run(['sudo', 'brctl', 'delbr', bridge_name], 
                             capture_output=True, input="root\n", text=True)
                
                time.sleep(1)
                
                # Recréer le bridge
                subprocess.run(['sudo', 'brctl', 'addbr', bridge_name], 
                             check=True, input="root\n", text=True)
                subprocess.run(['sudo', 'ip', 'addr', 'add', f'{ip_address}/24', 'dev', bridge_name], 
                             check=True, input="root\n", text=True)
                subprocess.run(['sudo', 'ip', 'link', 'set', bridge_name, 'up'], 
                             check=True, input="root\n", text=True)
                
                # Configurer le forwarding
                subprocess.run(['sudo', 'sysctl', '-w', f'net.ipv4.conf.{bridge_name}.forwarding=1'], 
                             capture_output=True, input="root\n", text=True)
                
                logger.info(f"   ✅ {bridge_name} réparé")
            
            # Configuration globale du forwarding
            subprocess.run(['sudo', 'sysctl', '-w', 'net.ipv4.ip_forward=1'], 
                         capture_output=True, input="root\n", text=True)
            
            logger.info("✅ Bridges système réparés")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur réparation bridges: {e}")
            return False
    
    def restart_gns3_service(self) -> bool:
        """Redémarre le service GNS3"""
        try:
            logger.info("🔄 Redémarrage du service GNS3...")
            
            # Vérifier si GNS3 tourne en service systemd
            check_service = subprocess.run(['systemctl', 'is-active', 'gns3-server'], 
                                         capture_output=True, text=True)
            
            if check_service.returncode == 0:
                # Service systemd détecté
                subprocess.run(['sudo', 'systemctl', 'restart', 'gns3-server'], 
                             check=True, input="root\n", text=True)
                logger.info("✅ Service GNS3 systemd redémarré")
            else:
                # Redémarrage manuel
                logger.info("⚠️ Service systemd non détecté, redémarrage manuel requis")
                logger.info("💡 Veuillez redémarrer GNS3 manuellement")
                return False
            
            # Attendre que le service redémarre
            time.sleep(10)
            
            # Vérifier la connectivité
            test_response = self.session.get(f"{self.gns3_url}/version")
            if test_response.status_code == 200:
                logger.info("✅ Service GNS3 opérationnel")
                return True
            else:
                logger.error("❌ Service GNS3 non accessible après redémarrage")
                return False
                
        except Exception as e:
            logger.error(f"❌ Erreur redémarrage service: {e}")
            return False
    
    def full_recovery_procedure(self) -> bool:
        """Procédure de récupération complète"""
        logger.info("🚀 DÉMARRAGE DE LA PROCÉDURE DE RÉCUPÉRATION COMPLÈTE")
        logger.info("=" * 80)
        
        success_steps = 0
        total_steps = 5
        
        try:
            # Étape 1: Arrêt forcé
            logger.info("📊 ÉTAPE 1/5: Arrêt forcé des nœuds")
            if self.force_stop_all_nodes():
                success_steps += 1
                logger.info("✅ Étape 1 réussie")
            else:
                logger.error("❌ Étape 1 échouée")
            
            time.sleep(5)
            
            # Étape 2: Réparation des bridges
            logger.info("📊 ÉTAPE 2/5: Réparation des bridges système")
            if self.repair_system_bridges():
                success_steps += 1
                logger.info("✅ Étape 2 réussie")
            else:
                logger.error("❌ Étape 2 échouée")
            
            time.sleep(3)
            
            # Étape 3: Recréation de Cloud1
            logger.info("📊 ÉTAPE 3/5: Recréation de Cloud1")
            if self.recreate_cloud_node():
                success_steps += 1
                logger.info("✅ Étape 3 réussie")
            else:
                logger.error("❌ Étape 3 échouée")
            
            time.sleep(5)
            
            # Étape 4: Redémarrage du service (optionnel)
            logger.info("📊 ÉTAPE 4/5: Vérification du service GNS3")
            test_response = self.session.get(f"{self.gns3_url}/version")
            if test_response.status_code == 200:
                success_steps += 1
                logger.info("✅ Service GNS3 opérationnel")
            else:
                logger.warning("⚠️ Service GNS3 potentiellement défaillant")
            
            # Étape 5: Validation finale
            logger.info("📊 ÉTAPE 5/5: Validation de la récupération")
            response = self.session.get(f"{self.gns3_url}/projects/{self.project_id}/nodes")
            if response.status_code == 200:
                nodes = response.json()
                cloud_found = any(node.get('node_type') == 'cloud' for node in nodes)
                if cloud_found:
                    success_steps += 1
                    logger.info("✅ Topologie validée")
                else:
                    logger.error("❌ Cloud1 non trouvé après récupération")
            else:
                logger.error("❌ Impossible d'accéder au projet")
            
            # Résumé
            logger.info("📊 RÉSUMÉ DE LA RÉCUPÉRATION")
            logger.info("=" * 80)
            logger.info(f"✅ Étapes réussies: {success_steps}/{total_steps}")
            
            if success_steps >= 4:
                logger.info("🎉 RÉCUPÉRATION RÉUSSIE")
                logger.info("💡 Vous pouvez maintenant relancer l'investigation automatique")
                return True
            elif success_steps >= 2:
                logger.info("✅ RÉCUPÉRATION PARTIELLE")
                logger.info("💡 Intervention manuelle recommandée")
                return False
            else:
                logger.error("❌ RÉCUPÉRATION ÉCHOUÉE")
                logger.info("💡 Redémarrage complet de GNS3 requis")
                return False
                
        except Exception as e:
            logger.error(f"❌ Erreur critique lors de la récupération: {e}")
            return False

def main():
    """Fonction principale"""
    print("🔧 DÉPANNAGE AVANCÉ GNS3")
    print("=" * 50)
    print("1. Arrêt forcé de tous les nœuds")
    print("2. Remise à zéro de la topologie")
    print("3. Recréation de Cloud1") 
    print("4. Réparation des bridges système")
    print("5. Redémarrage du service GNS3")
    print("6. Procédure de récupération complète")
    print("=" * 50)
    
    try:
        choice = input("Choisissez une option (1-6): ").strip()
        
        troubleshooter = GNS3AdvancedTroubleshooter()
        
        if choice == "1":
            troubleshooter.force_stop_all_nodes()
        elif choice == "2":
            troubleshooter.reset_project_topology()
        elif choice == "3":
            troubleshooter.recreate_cloud_node()
        elif choice == "4":
            troubleshooter.repair_system_bridges()
        elif choice == "5":
            troubleshooter.restart_gns3_service()
        elif choice == "6":
            troubleshooter.full_recovery_procedure()
        else:
            print("❌ Option invalide")
            
    except KeyboardInterrupt:
        print("\n🛑 Opération interrompue")
    except Exception as e:
        print(f"❌ Erreur: {e}")

if __name__ == "__main__":
    main()