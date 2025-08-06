#!/usr/bin/env python3
"""
Workflow Complet de Démarrage et Configuration GNS3
==================================================

Ce script automatise le workflow complet :
1. Allumage du projet GNS3
2. Démarrage des nœuds
3. Configuration DHCP automatique
4. Vérification de la connectivité
5. Découverte des IPs pour les tests de sécurité

Auteur: Équipe de développement NMS  
Date: 2025-07-18
"""

import asyncio
import time
import logging
import requests
from typing import Dict, List, Optional, Tuple
import json
from dataclasses import dataclass
from datetime import datetime
import subprocess
import sys
import os

# Ajouter le répertoire courant au path pour les imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import du script de configuration DHCP
from auto_dhcp_configuration import DHCPConfigurationManager, DeviceConfig

# Configuration logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class WorkflowResult:
    """Résultat du workflow complet"""
    startup_success: bool
    nodes_started: int
    nodes_total: int
    dhcp_configured: int
    devices_accessible: int
    ips_discovered: List[str]
    execution_time: float
    errors: List[str]

class CompleteStartupWorkflow:
    """Gestionnaire du workflow complet de démarrage"""
    
    def __init__(self, django_base_url: str = "http://localhost:8000"):
        self.django_base_url = django_base_url
        self.project_id = "6b858ee5-4a49-4f72-b437-8dcd8d876bad"  # Projet Hybrido
        self.session = requests.Session()
        self.dhcp_manager = DHCPConfigurationManager(django_base_url)
        self.errors = []
        
    def log_error(self, error: str):
        """Ajouter une erreur au log"""
        self.errors.append(error)
        logger.error(error)
    
    def log_info(self, message: str):
        """Log d'information"""
        logger.info(message)
    
    def check_gns3_connectivity(self) -> bool:
        """Vérifier la connectivité avec GNS3"""
        try:
            response = self.session.get(f"{self.django_base_url}/api/gns3/server/status/")
            if response.status_code == 200:
                server_info = response.json()
                self.log_info(f"✅ GNS3 Server connecté: {server_info.get('version', 'Unknown')}")
                return True
            else:
                self.log_error(f"❌ Erreur connectivité GNS3: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log_error(f"❌ Erreur connexion GNS3: {e}")
            return False
    
    def start_project(self) -> bool:
        """Démarrage du projet GNS3"""
        try:
            self.log_info("🚀 Démarrage du projet Hybrido...")
            
            # Utiliser l'API de démarrage complet
            response = self.session.post(
                f"{self.django_base_url}/api/gns3/startup-status/{self.project_id}/start_complete/",
                json={"wait_for_completion": True, "max_wait_time": 120}
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success', False):
                    self.log_info("✅ Projet démarré avec succès")
                    return True
                else:
                    self.log_error(f"❌ Échec démarrage projet: {result.get('message', 'Unknown')}")
                    return False
            else:
                self.log_error(f"❌ Erreur API démarrage: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log_error(f"❌ Erreur démarrage projet: {e}")
            return False
    
    def wait_for_nodes_ready(self, timeout: int = 120) -> Tuple[int, int]:
        """Attendre que les nœuds soient prêts"""
        try:
            self.log_info("⏳ Attente de la stabilisation des nœuds...")
            
            start_time = time.time()
            
            while time.time() - start_time < timeout:
                try:
                    # Vérifier le statut des nœuds
                    response = self.session.get(f"{self.django_base_url}/api/gns3/projects/{self.project_id}/nodes/")
                    if response.status_code == 200:
                        nodes = response.json()
                        started_nodes = sum(1 for node in nodes if node.get('status') == 'started')
                        total_nodes = len(nodes)
                        
                        self.log_info(f"📊 Nœuds démarrés: {started_nodes}/{total_nodes}")
                        
                        if started_nodes >= total_nodes * 0.8:  # 80% des nœuds démarrés
                            self.log_info("✅ Majorité des nœuds démarrés")
                            return started_nodes, total_nodes
                        
                        time.sleep(5)
                    else:
                        self.log_error(f"❌ Erreur vérification nœuds: HTTP {response.status_code}")
                        time.sleep(5)
                        
                except Exception as e:
                    self.log_error(f"❌ Erreur vérification nœuds: {e}")
                    time.sleep(5)
            
            # Timeout atteint
            self.log_error("❌ Timeout atteint pour l'attente des nœuds")
            return 0, 0
            
        except Exception as e:
            self.log_error(f"❌ Erreur attente nœuds: {e}")
            return 0, 0
    
    def configure_dhcp_all_devices(self) -> Dict[str, bool]:
        """Configuration DHCP de tous les équipements"""
        try:
            self.log_info("🔧 Configuration DHCP des équipements...")
            
            # Attendre un peu pour la stabilisation
            time.sleep(10)
            
            # Utiliser le gestionnaire DHCP
            config_results = self.dhcp_manager.configure_all_devices(max_concurrent=2)
            
            successful = sum(1 for success in config_results.values() if success)
            total = len(config_results)
            
            self.log_info(f"📊 Configuration DHCP: {successful}/{total} équipements configurés")
            
            return config_results
            
        except Exception as e:
            self.log_error(f"❌ Erreur configuration DHCP: {e}")
            return {}
    
    def verify_network_connectivity(self) -> Dict[str, bool]:
        """Vérification de la connectivité réseau"""
        try:
            self.log_info("🔍 Vérification de la connectivité réseau...")
            
            # Attendre la stabilisation du réseau
            time.sleep(15)
            
            # Vérifier la connectivité
            connectivity_results = self.dhcp_manager.verify_connectivity()
            
            accessible = sum(1 for accessible in connectivity_results.values() if accessible)
            total = len([r for r in connectivity_results.values() if r is not None])
            
            self.log_info(f"📊 Connectivité: {accessible}/{total} équipements accessibles")
            
            return connectivity_results
            
        except Exception as e:
            self.log_error(f"❌ Erreur vérification connectivité: {e}")
            return {}
    
    def discover_ips_for_security_tests(self) -> List[str]:
        """Découverte des IPs pour les tests de sécurité"""
        try:
            self.log_info("🔍 Découverte des IPs pour les tests de sécurité...")
            
            # Utiliser l'API de découverte améliorée
            response = self.session.post(
                f"{self.django_base_url}/api/common/api/v1/equipment/projects/{self.project_id}/test-discovery/",
                json={"max_concurrent": 3, "include_full_details": True}
            )
            
            if response.status_code == 200:
                discovery_result = response.json()
                
                # Extraire toutes les IPs découvertes
                all_ips = []
                for device in discovery_result.get('devices', []):
                    ips = device.get('discovered_ips', [])
                    all_ips.extend(ips)
                
                # Éliminer les doublons
                unique_ips = list(set(all_ips))
                
                self.log_info(f"📊 IPs découvertes: {len(unique_ips)} adresses uniques")
                
                for ip in unique_ips:
                    self.log_info(f"   - {ip}")
                
                return unique_ips
                
            else:
                self.log_error(f"❌ Erreur découverte IPs: HTTP {response.status_code}")
                return []
                
        except Exception as e:
            self.log_error(f"❌ Erreur découverte IPs: {e}")
            return []
    
    def trigger_security_framework(self, discovered_ips: List[str]) -> bool:
        """Déclenchement du framework de sécurité"""
        try:
            if not discovered_ips:
                self.log_error("❌ Aucune IP découverte pour les tests de sécurité")
                return False
            
            self.log_info(f"🚀 Déclenchement du framework de sécurité avec {len(discovered_ips)} cibles")
            
            # Déclencher le workflow de sécurité via Celery
            response = self.session.post(
                f"{self.django_base_url}/api/common/api/v1/celery/trigger-security-workflow/",
                json={
                    "project_id": self.project_id,
                    "target_ips": discovered_ips,
                    "test_level": "intermediate",
                    "intensity": "medium"
                }
            )
            
            if response.status_code == 200:
                self.log_info("✅ Framework de sécurité déclenché")
                return True
            else:
                self.log_error(f"❌ Erreur déclenchement framework: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log_error(f"❌ Erreur déclenchement framework: {e}")
            return False
    
    def run_complete_workflow(self) -> WorkflowResult:
        """Exécution du workflow complet"""
        start_time = time.time()
        
        self.log_info("🎯 DÉMARRAGE DU WORKFLOW COMPLET DE DÉMARRAGE ET CONFIGURATION")
        self.log_info("=" * 80)
        
        # Étape 1: Vérifier la connectivité GNS3
        self.log_info("📋 Étape 1: Vérification de la connectivité GNS3...")
        if not self.check_gns3_connectivity():
            return WorkflowResult(
                startup_success=False,
                nodes_started=0,
                nodes_total=0,
                dhcp_configured=0,
                devices_accessible=0,
                ips_discovered=[],
                execution_time=time.time() - start_time,
                errors=self.errors
            )
        
        # Étape 2: Démarrage du projet
        self.log_info("📋 Étape 2: Démarrage du projet GNS3...")
        if not self.start_project():
            return WorkflowResult(
                startup_success=False,
                nodes_started=0,
                nodes_total=0,
                dhcp_configured=0,
                devices_accessible=0,
                ips_discovered=[],
                execution_time=time.time() - start_time,
                errors=self.errors
            )
        
        # Étape 3: Attente de la stabilisation des nœuds
        self.log_info("📋 Étape 3: Attente de la stabilisation des nœuds...")
        nodes_started, nodes_total = self.wait_for_nodes_ready()
        
        # Étape 4: Configuration DHCP
        self.log_info("📋 Étape 4: Configuration DHCP des équipements...")
        dhcp_results = self.configure_dhcp_all_devices()
        dhcp_configured = sum(1 for success in dhcp_results.values() if success)
        
        # Étape 5: Vérification de la connectivité
        self.log_info("📋 Étape 5: Vérification de la connectivité réseau...")
        connectivity_results = self.verify_network_connectivity()
        devices_accessible = sum(1 for accessible in connectivity_results.values() if accessible)
        
        # Étape 6: Découverte des IPs
        self.log_info("📋 Étape 6: Découverte des IPs pour les tests de sécurité...")
        discovered_ips = self.discover_ips_for_security_tests()
        
        # Étape 7: Déclenchement du framework de sécurité
        self.log_info("📋 Étape 7: Déclenchement du framework de sécurité...")
        security_triggered = self.trigger_security_framework(discovered_ips)
        
        # Résultat final
        execution_time = time.time() - start_time
        
        result = WorkflowResult(
            startup_success=True,
            nodes_started=nodes_started,
            nodes_total=nodes_total,
            dhcp_configured=dhcp_configured,
            devices_accessible=devices_accessible,
            ips_discovered=discovered_ips,
            execution_time=execution_time,
            errors=self.errors
        )
        
        # Résumé final
        self.log_info("📊 RÉSUMÉ DU WORKFLOW COMPLET")
        self.log_info("=" * 80)
        self.log_info(f"✅ Projet démarré: {result.startup_success}")
        self.log_info(f"📊 Nœuds démarrés: {result.nodes_started}/{result.nodes_total}")
        self.log_info(f"🔧 DHCP configuré: {result.dhcp_configured} équipements")
        self.log_info(f"🌐 Connectivité: {result.devices_accessible} équipements accessibles")
        self.log_info(f"🔍 IPs découvertes: {len(result.ips_discovered)} adresses")
        self.log_info(f"🚀 Framework sécurité: {'✅ Déclenché' if security_triggered else '❌ Non déclenché'}")
        self.log_info(f"⏱️ Temps d'exécution: {result.execution_time:.2f}s")
        self.log_info(f"⚠️ Erreurs: {len(result.errors)}")
        
        if result.errors:
            self.log_info("📋 Erreurs rencontrées:")
            for error in result.errors:
                self.log_info(f"   - {error}")
        
        return result

def main():
    """Fonction principale"""
    workflow = CompleteStartupWorkflow()
    result = workflow.run_complete_workflow()
    
    # Code de sortie basé sur le succès
    if result.startup_success and len(result.ips_discovered) > 0:
        print(f"✅ Workflow terminé avec succès - {len(result.ips_discovered)} IPs découvertes")
        sys.exit(0)
    else:
        print(f"❌ Workflow terminé avec des erreurs - {len(result.errors)} erreurs")
        sys.exit(1)

if __name__ == "__main__":
    main()