#!/usr/bin/env python3
"""
Script d'ouverture du projet Hybrido dans GNS3
============================================

Script pour ouvrir automatiquement le projet Hybrido dans GNS3
et vérifier son état.

Auteur: Équipe de développement NMS
Date: 2025-07-20
"""

import requests
import json
import logging
import time
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class GNS3ProjectManager:
    """Gestionnaire de projets GNS3"""
    
    def __init__(self, gns3_host: str = "192.168.122.95", gns3_port: int = 3080):
        self.gns3_base_url = f"http://{gns3_host}:{gns3_port}/v2"
        
        # ID du projet Hybrido connu depuis les logs
        self.hybrido_project_id = "6b858ee5-4a49-4f72-b437-8dcd8d876bad"
    
    def check_gns3_connection(self) -> bool:
        """Vérifie la connexion à GNS3"""
        try:
            response = requests.get(f"{self.gns3_base_url}/version", timeout=10)
            if response.status_code == 200:
                version_info = response.json()
                logger.info(f"✅ GNS3 accessible - Version: {version_info.get('version', 'Unknown')}")
                return True
            else:
                logger.error(f"❌ GNS3 inaccessible - Code: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Erreur connexion GNS3: {e}")
            return False
    
    def list_all_projects(self) -> List[Dict]:
        """Liste tous les projets GNS3 (ouverts et fermés)"""
        try:
            # Tentative de récupération des projets via l'endpoint principal
            response = requests.get(f"{self.gns3_base_url}/projects", timeout=10)
            
            projects = []
            if response.status_code == 200:
                try:
                    projects = response.json()
                except:
                    projects = []
            
            logger.info(f"📊 {len(projects)} projets trouvés via API")
            
            for project in projects:
                name = project.get("name", "Unknown")
                project_id = project.get("project_id", "Unknown")
                status = project.get("status", "Unknown")
                logger.info(f"   📁 {name} (ID: {project_id}) - Status: {status}")
            
            return projects
            
        except Exception as e:
            logger.error(f"❌ Erreur listage projets: {e}")
            return []
    
    def check_project_exists(self, project_id: str) -> Optional[Dict]:
        """Vérifie si un projet existe par son ID"""
        try:
            response = requests.get(f"{self.gns3_base_url}/projects/{project_id}", timeout=10)
            
            if response.status_code == 200:
                project_info = response.json()
                logger.info(f"✅ Projet {project_id} trouvé")
                return project_info
            elif response.status_code == 404:
                logger.warning(f"⚠️ Projet {project_id} non trouvé")
                return None
            else:
                logger.error(f"❌ Erreur vérification projet: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Erreur vérification projet {project_id}: {e}")
            return None
    
    def open_project(self, project_id: str) -> bool:
        """Ouvre un projet GNS3"""
        try:
            logger.info(f"🔄 Ouverture du projet {project_id}...")
            
            response = requests.post(f"{self.gns3_base_url}/projects/{project_id}/open", timeout=30)
            
            if response.status_code == 201:
                logger.info(f"✅ Projet {project_id} ouvert avec succès")
                return True
            elif response.status_code == 409:
                logger.info(f"✅ Projet {project_id} déjà ouvert")
                return True
            else:
                logger.error(f"❌ Erreur ouverture projet: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Erreur ouverture projet {project_id}: {e}")
            return False
    
    def get_project_nodes(self, project_id: str) -> List[Dict]:
        """Récupère les nœuds d'un projet"""
        try:
            response = requests.get(f"{self.gns3_base_url}/projects/{project_id}/nodes", timeout=10)
            
            if response.status_code == 200:
                nodes = response.json()
                logger.info(f"📱 {len(nodes)} nœuds trouvés dans le projet")
                
                # Affichage détaillé des nœuds
                for node in nodes:
                    name = node.get("name", "Unknown")
                    node_type = node.get("node_type", "Unknown")
                    status = node.get("status", "Unknown")
                    logger.info(f"   🔧 {name} ({node_type}) - Status: {status}")
                
                return nodes
            else:
                logger.error(f"❌ Erreur récupération nœuds: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"❌ Erreur récupération nœuds: {e}")
            return []
    
    def start_all_nodes(self, project_id: str) -> bool:
        """Démarre tous les nœuds d'un projet"""
        try:
            logger.info("🚀 Démarrage de tous les nœuds...")
            
            response = requests.post(f"{self.gns3_base_url}/projects/{project_id}/nodes/start", timeout=60)
            
            if response.status_code == 204:
                logger.info("✅ Tous les nœuds démarrés")
                return True
            else:
                logger.error(f"❌ Erreur démarrage nœuds: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Erreur démarrage nœuds: {e}")
            return False
    
    def manage_hybrido_project(self) -> bool:
        """Gère l'ouverture et le démarrage du projet Hybrido"""
        logger.info("🎯 GESTION DU PROJET HYBRIDO")
        logger.info("=" * 40)
        
        # 1. Vérification connexion GNS3
        if not self.check_gns3_connection():
            return False
        
        # 2. Listage des projets existants
        projects = self.list_all_projects()
        
        # 3. Recherche du projet Hybrido
        hybrido_found = False
        for project in projects:
            if project.get("name", "").lower() == "hybrido":
                hybrido_found = True
                current_id = project.get("project_id")
                if current_id != self.hybrido_project_id:
                    logger.warning(f"⚠️ ID projet Hybrido différent: {current_id} vs {self.hybrido_project_id}")
                    self.hybrido_project_id = current_id
                break
        
        if not hybrido_found:
            # Tentative avec l'ID connu
            logger.info(f"🔍 Tentative d'accès direct au projet {self.hybrido_project_id}")
            project_info = self.check_project_exists(self.hybrido_project_id)
            if not project_info:
                logger.error("❌ Projet Hybrido introuvable")
                return False
        
        # 4. Ouverture du projet
        if not self.open_project(self.hybrido_project_id):
            return False
        
        # 5. Vérification des nœuds
        nodes = self.get_project_nodes(self.hybrido_project_id)
        if not nodes:
            logger.error("❌ Aucun nœud trouvé dans le projet")
            return False
        
        # 6. Démarrage des nœuds
        if not self.start_all_nodes(self.hybrido_project_id):
            logger.warning("⚠️ Problème lors du démarrage des nœuds")
        
        # 7. Attente stabilisation
        logger.info("⏳ Attente de stabilisation (10s)...")
        time.sleep(10)
        
        # 8. Vérification finale
        final_nodes = self.get_project_nodes(self.hybrido_project_id)
        started_nodes = [n for n in final_nodes if n.get("status") == "started"]
        
        logger.info(f"📊 Résultat final: {len(started_nodes)}/{len(final_nodes)} nœuds démarrés")
        
        return len(started_nodes) > 0

def main():
    """Fonction principale"""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    manager = GNS3ProjectManager()
    
    print("🚀 OUVERTURE ET DÉMARRAGE DU PROJET HYBRIDO")
    print("=" * 60)
    
    success = manager.manage_hybrido_project()
    
    if success:
        print("\n✅ SUCCÈS: Projet Hybrido prêt pour les tests de sécurité")
        print("💡 Vous pouvez maintenant lancer le framework de tests")
    else:
        print("\n❌ ÉCHEC: Impossible de préparer le projet Hybrido")
        print("💡 Vérifiez que GNS3 est démarré avec le projet Hybrido")

if __name__ == "__main__":
    main()