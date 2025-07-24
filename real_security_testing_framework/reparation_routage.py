#!/usr/bin/env python3
"""
Script de réparation du routage inter-VLAN
==========================================

Ce script diagnostique et corrige les problèmes de routage inter-VLAN
pour restaurer la connectivité entre les équipements.

Auteur: Claude Code
Date: 2025-07-20
"""

import logging
import sys
import time
from pathlib import Path

# Ajouter le répertoire parent au path pour les imports
sys.path.insert(0, str(Path(__file__).parent))

from auto_dhcp_configuration import DHCPConfigurationManager, ConsoleConnection

# Configuration logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_pc1_connectivity():
    """Test la connectivité depuis PC1"""
    try:
        logger.info("🔍 Test de connectivité depuis PC1...")
        
        config_manager = DHCPConfigurationManager()
        devices = config_manager.get_project_devices()
        
        # Trouver PC1
        pc1_device = None
        for device in devices:
            if device.name == "PC1":
                pc1_device = device
                break
        
        if not pc1_device:
            logger.error("❌ PC1 non trouvé")
            return False
        
        # Connexion à PC1
        console_conn = config_manager.connect_to_console(pc1_device)
        if not console_conn:
            logger.error("❌ Impossible de se connecter à PC1")
            return False
        
        try:
            # Vérifier configuration IP de PC1
            logger.info("📋 Vérification configuration PC1...")
            show_ip = console_conn.send_command("show ip\\n")
            logger.info(f"Configuration PC1: {show_ip}")
            
            # Test ping vers différentes cibles
            test_targets = [
                ("Gateway LAN", "192.168.20.1"),
                ("SW-LAN", "192.168.21.1"),
                ("Routeur Principal", "192.168.41.1"),
                ("Server-Web", "192.168.10.10")
            ]
            
            connectivity_results = {}
            
            for target_name, target_ip in test_targets:
                logger.info(f"🔌 Ping vers {target_name} ({target_ip})...")
                ping_result = console_conn.send_command(f"ping {target_ip}\\n")
                
                # Analyser le résultat
                if "host reachable" in ping_result.lower() or "bytes from" in ping_result.lower():
                    connectivity_results[target_name] = True
                    logger.info(f"   ✅ {target_name}: ACCESSIBLE")
                else:
                    connectivity_results[target_name] = False
                    logger.warning(f"   ❌ {target_name}: INACCESSIBLE")
                
                time.sleep(2)
            
            # Résumé
            accessible_count = sum(connectivity_results.values())
            total_count = len(connectivity_results)
            logger.info(f"📊 Connectivité PC1: {accessible_count}/{total_count} cibles accessibles")
            
            return accessible_count > 0
            
        finally:
            console_conn.close()
            
    except Exception as e:
        logger.error(f"❌ Erreur test connectivité PC1: {e}")
        return False

def repair_router_configuration():
    """Répare la configuration du routeur principal"""
    try:
        logger.info("🔧 RÉPARATION DE LA CONFIGURATION DU ROUTEUR PRINCIPAL")
        
        config_manager = DHCPConfigurationManager()
        devices = config_manager.get_project_devices()
        
        # Trouver le routeur principal
        router_device = None
        for device in devices:
            if device.name == "Routeur-Principal":
                router_device = device
                break
        
        if not router_device:
            logger.error("❌ Routeur principal non trouvé")
            return False
        
        # Connexion au routeur
        console_conn = config_manager.connect_to_console(router_device)
        if not console_conn:
            logger.error("❌ Impossible de se connecter au routeur principal")
            return False
        
        try:
            logger.info("🔧 Configuration complète du routage inter-VLAN...")
            
            # Entrer en mode configuration
            setup_commands = [
                "\\r\\n",
                "enable\\r\\n", 
                "configure terminal\\r\\n"
            ]
            
            for cmd in setup_commands:
                response = console_conn.send_command(cmd)
                logger.debug(f"Setup: {cmd.strip()} -> {response[:50]}...")
                time.sleep(1)
            
            # Configuration de l'interface principale
            main_interface_commands = [
                "interface FastEthernet0/0\\r\\n",
                "no ip address\\r\\n",
                "no shutdown\\r\\n",
                "exit\\r\\n"
            ]
            
            for cmd in main_interface_commands:
                response = console_conn.send_command(cmd)
                logger.debug(f"Main interface: {cmd.strip()}")
                time.sleep(1)
            
            # Configuration des sous-interfaces VLAN
            vlan_configs = [
                ("FastEthernet0/0.10", "10", "192.168.10.1"),   # DMZ Web
                ("FastEthernet0/0.11", "11", "192.168.11.1"),   # DMZ DNS  
                ("FastEthernet0/0.12", "12", "192.168.12.1"),   # DMZ Sécurité
                ("FastEthernet0/0.20", "20", "192.168.20.1"),   # LAN Utilisateurs
                ("FastEthernet0/0.21", "21", "192.168.21.1"),   # LAN Services
                ("FastEthernet0/0.30", "30", "192.168.30.1"),   # Serveurs DB
                ("FastEthernet0/0.31", "31", "192.168.31.1"),   # Serveurs Apps
                ("FastEthernet0/0.32", "32", "192.168.32.1"),   # Serveurs Storage
                ("FastEthernet0/0.41", "41", "192.168.41.1"),   # Administration
            ]
            
            for interface, vlan_id, gateway_ip in vlan_configs:
                logger.info(f"🔧 Configuration {interface} → VLAN {vlan_id} → {gateway_ip}")
                
                subinterface_commands = [
                    f"interface {interface}\\r\\n",
                    f"encapsulation dot1Q {vlan_id}\\r\\n",
                    f"ip address {gateway_ip} 255.255.255.0\\r\\n",
                    "no shutdown\\r\\n",
                    "exit\\r\\n"
                ]
                
                for cmd in subinterface_commands:
                    response = console_conn.send_command(cmd)
                    time.sleep(1)
            
            # Activer le routage IP et sauvegarder
            final_commands = [
                "ip routing\\r\\n",
                "end\\r\\n",
                "copy running-config startup-config\\r\\n",
                "\\r\\n"  # Confirmer
            ]
            
            for cmd in final_commands:
                response = console_conn.send_command(cmd)
                logger.debug(f"Final: {cmd.strip()}")
                time.sleep(2)
            
            logger.info("✅ Configuration du routeur terminée")
            
            # Vérification rapide
            time.sleep(5)
            verification = console_conn.send_command("show ip interface brief\\r\\n")
            logger.info(f"📋 Vérification interfaces: {len(verification)} caractères reçus")
            
            return True
            
        finally:
            console_conn.close()
            
    except Exception as e:
        logger.error(f"❌ Erreur réparation routeur: {e}")
        return False

def main():
    """Fonction principale de réparation"""
    logger.info("🔧 DÉMARRAGE DE LA RÉPARATION DU ROUTAGE INTER-VLAN")
    logger.info("=" * 60)
    
    try:
        # 1. Test initial de connectivité
        logger.info("📊 ÉTAPE 1: Test initial de connectivité PC1")
        initial_connectivity = test_pc1_connectivity()
        
        if initial_connectivity:
            logger.info("✅ PC1 a une connectivité partielle")
        else:
            logger.warning("⚠️ PC1 n'a aucune connectivité")
        
        # 2. Réparation du routeur
        logger.info("📊 ÉTAPE 2: Réparation de la configuration du routeur")
        router_repair_success = repair_router_configuration()
        
        if not router_repair_success:
            logger.error("❌ Échec de la réparation du routeur")
            return
        
        # 3. Attente de stabilisation
        logger.info("📊 ÉTAPE 3: Attente de stabilisation du réseau")
        time.sleep(30)
        
        # 4. Test final de connectivité
        logger.info("📊 ÉTAPE 4: Test final de connectivité PC1")
        final_connectivity = test_pc1_connectivity()
        
        # 5. Résumé
        logger.info("📊 ÉTAPE 5: Résumé de la réparation")
        logger.info("=" * 60)
        if final_connectivity and not initial_connectivity:
            logger.info("🎉 RÉPARATION RÉUSSIE: Connectivité restaurée")
        elif final_connectivity and initial_connectivity:
            logger.info("✅ AMÉLIORATION: Connectivité maintenue/améliorée")
        else:
            logger.warning("⚠️ PROBLÈME PERSISTANT: Connectivité non restaurée")
        
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"❌ Erreur lors de la réparation: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")

if __name__ == "__main__":
    main()