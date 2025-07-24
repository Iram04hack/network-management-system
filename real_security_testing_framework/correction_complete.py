#!/usr/bin/env python3
"""
Script de correction complète de la connectivité
===============================================

Ce script corrige systématiquement tous les problèmes de connectivité
pour rendre tous les équipements accessibles.

Auteur: Claude Code
Date: 2025-07-20
"""

import logging
import sys
import time
from pathlib import Path

# Ajouter le répertoire parent au path pour les imports
sys.path.insert(0, str(Path(__file__).parent))

from auto_dhcp_configuration import DHCPConfigurationManager, ConsoleConnection, DeviceType

# Configuration logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def fix_pc1_configuration():
    """Corrige la configuration de PC1"""
    try:
        logger.info("🔧 CORRECTION DE LA CONFIGURATION PC1")
        
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
            logger.info("🔧 Configuration IP correcte pour PC1...")
            
            # Configuration VPCS correcte avec gateway appropriée
            commands = [
                "\\n",  # Retour chariot
                "ip 192.168.20.10 192.168.20.1\\n",  # IP avec gateway correcte
                "save\\n",  # Sauvegarder
                "show ip\\n"  # Vérifier
            ]
            
            for cmd in commands:
                logger.info(f"   Commande: {cmd.strip()}")
                response = console_conn.send_command(cmd)
                logger.info(f"   Réponse: {response[:100]}...")
                time.sleep(2)
            
            # Test de connectivité local
            logger.info("🔍 Test de connectivité local...")
            ping_gateway = console_conn.send_command("ping 192.168.20.1\\n")
            
            if "host reachable" in ping_gateway.lower():
                logger.info("✅ PC1 peut pinger sa gateway")
                return True
            else:
                logger.warning("⚠️ PC1 ne peut pas pinger sa gateway")
                logger.info(f"Réponse ping: {ping_gateway}")
                return False
                
        finally:
            console_conn.close()
            
    except Exception as e:
        logger.error(f"❌ Erreur correction PC1: {e}")
        return False

def fix_router_complete():
    """Configuration complète et systématique du routeur"""
    try:
        logger.info("🔧 CONFIGURATION COMPLÈTE DU ROUTEUR PRINCIPAL")
        
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
            logger.info("🔧 Reset et configuration complète...")
            
            # Reset de configuration puis reconfiguration complète
            reset_commands = [
                "\\r\\n",
                "enable\\r\\n", 
                "configure terminal\\r\\n",
                "no interface FastEthernet0/0.10\\r\\n",
                "no interface FastEthernet0/0.11\\r\\n", 
                "no interface FastEthernet0/0.12\\r\\n",
                "no interface FastEthernet0/0.20\\r\\n",
                "no interface FastEthernet0/0.21\\r\\n",
                "no interface FastEthernet0/0.30\\r\\n",
                "no interface FastEthernet0/0.31\\r\\n",
                "no interface FastEthernet0/0.32\\r\\n",
                "no interface FastEthernet0/0.41\\r\\n"
            ]
            
            logger.info("🗑️ Nettoyage des anciennes configurations...")
            for cmd in reset_commands:
                response = console_conn.send_command(cmd)
                time.sleep(1)
            
            # Configuration de l'interface principale
            main_config = [
                "interface FastEthernet0/0\\r\\n",
                "no ip address\\r\\n",
                "no shutdown\\r\\n",
                "exit\\r\\n"
            ]
            
            logger.info("🔧 Configuration interface principale...")
            for cmd in main_config:
                response = console_conn.send_command(cmd)
                time.sleep(1)
            
            # Configuration des sous-interfaces VLAN avec vérification
            vlan_configs = [
                ("FastEthernet0/0.10", "10", "192.168.10.1"),   # DMZ Web
                ("FastEthernet0/0.11", "11", "192.168.11.1"),   # DMZ DNS  
                ("FastEthernet0/0.12", "12", "192.168.12.1"),   # DMZ Sécurité
                ("FastEthernet0/0.20", "20", "192.168.20.1"),   # LAN Utilisateurs - CRITIQUE pour PC1
                ("FastEthernet0/0.21", "21", "192.168.21.1"),   # LAN Services
                ("FastEthernet0/0.30", "30", "192.168.30.1"),   # Serveurs DB
                ("FastEthernet0/0.31", "31", "192.168.31.1"),   # Serveurs Apps
                ("FastEthernet0/0.32", "32", "192.168.32.1"),   # Serveurs Storage
                ("FastEthernet0/0.41", "41", "192.168.41.1"),   # Administration
            ]
            
            successful_vlans = 0
            
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
                
                # Vérification immédiate de l'interface
                verify_cmd = f"show interface {interface}\\r\\n"
                verify_response = console_conn.send_command(verify_cmd)
                
                if "up" in verify_response.lower() and gateway_ip in verify_response:
                    logger.info(f"   ✅ Interface {interface} active")
                    successful_vlans += 1
                else:
                    logger.warning(f"   ⚠️ Interface {interface} problématique")
                
                time.sleep(2)
            
            # Activation globale du routage
            routing_commands = [
                "ip routing\\r\\n",
                "ip cef\\r\\n",  # Cisco Express Forwarding
                "end\\r\\n"
            ]
            
            logger.info("🔧 Activation du routage global...")
            for cmd in routing_commands:
                response = console_conn.send_command(cmd)
                time.sleep(2)
            
            # Sauvegarde
            save_commands = [
                "copy running-config startup-config\\r\\n",
                "\\r\\n"  # Confirmer
            ]
            
            logger.info("💾 Sauvegarde de la configuration...")
            for cmd in save_commands:
                response = console_conn.send_command(cmd)
                time.sleep(3)
            
            # Vérification finale
            logger.info("🔍 Vérification finale du routeur...")
            final_check = console_conn.send_command("show ip interface brief\\r\\n")
            
            # Compter les interfaces actives
            active_interfaces = final_check.count("up")
            logger.info(f"📊 Interfaces actives: {active_interfaces}")
            logger.info(f"📊 VLANs configurés avec succès: {successful_vlans}/9")
            
            return successful_vlans >= 7  # Au moins 7 VLANs doivent être OK
            
        finally:
            console_conn.close()
            
    except Exception as e:
        logger.error(f"❌ Erreur configuration routeur: {e}")
        return False

def fix_switches_trunk():
    """Configure les trunks sur les switches vers le routeur"""
    try:
        logger.info("🔧 CONFIGURATION DES TRUNKS SUR LES SWITCHES")
        
        config_manager = DHCPConfigurationManager()
        devices = config_manager.get_project_devices()
        
        # Switches à configurer
        switches_config = {
            "SW-DMZ": ("12", "ethernet0/0"),
            "SW-LAN": ("21", "ethernet0/0"), 
            "SW-SERVER": ("31", "ethernet0/0"),
            "SW-ADMIN": ("41", "ethernet0/0")
        }
        
        successful_switches = 0
        
        for switch_name, (vlan_id, trunk_interface) in switches_config.items():
            logger.info(f"🔧 Configuration trunk {switch_name} (VLAN {vlan_id})...")
            
            # Trouver le switch
            switch_device = None
            for device in devices:
                if device.name == switch_name:
                    switch_device = device
                    break
            
            if not switch_device:
                logger.warning(f"⚠️ Switch {switch_name} non trouvé")
                continue
            
            # Connexion au switch
            console_conn = config_manager.connect_to_console(switch_device)
            if not console_conn:
                logger.warning(f"⚠️ Connexion {switch_name} échouée")
                continue
            
            try:
                # Configuration trunk + VLAN
                trunk_commands = [
                    "\\n",
                    "configure terminal\\n",
                    f"vlan {vlan_id}\\n",
                    "exit\\n",
                    f"interface vlan {vlan_id}\\n",
                    f"ip address {switch_device.ip_address} 255.255.255.0\\n",
                    "no shutdown\\n",
                    "exit\\n",
                    f"interface {trunk_interface}\\n",
                    "switchport mode trunk\\n",
                    f"switchport trunk allowed vlan {vlan_id}\\n",
                    "no shutdown\\n",
                    "exit\\n",
                    f"ip default-gateway {switch_device.gateway}\\n",
                    "end\\n",
                    "copy running-config startup-config\\n",
                    "\\n"
                ]
                
                for cmd in trunk_commands:
                    response = console_conn.send_command(cmd)
                    time.sleep(1)
                
                # Vérification
                verify_response = console_conn.send_command("show ip interface brief\\n")
                if switch_device.ip_address in verify_response:
                    logger.info(f"   ✅ {switch_name} configuré avec succès")
                    successful_switches += 1
                else:
                    logger.warning(f"   ⚠️ {switch_name} configuration incertaine")
                
            finally:
                console_conn.close()
                
            time.sleep(2)
        
        logger.info(f"📊 Switches configurés: {successful_switches}/{len(switches_config)}")
        return successful_switches >= 2
        
    except Exception as e:
        logger.error(f"❌ Erreur configuration switches: {e}")
        return False

def fix_vpcs_devices():
    """Corrige la configuration de tous les PCs VPCS"""
    try:
        logger.info("🔧 CORRECTION DES ÉQUIPEMENTS VPCS")
        
        config_manager = DHCPConfigurationManager()
        devices = config_manager.get_project_devices()
        
        # PCs VPCS à configurer
        vpcs_configs = {
            "PC1": ("192.168.20.10", "192.168.20.1"),
            "PC2": ("192.168.20.11", "192.168.20.1"),
            "Admin": ("192.168.41.10", "192.168.41.1")
        }
        
        successful_pcs = 0
        
        for pc_name, (ip_address, gateway) in vpcs_configs.items():
            logger.info(f"🔧 Configuration {pc_name}: {ip_address} via {gateway}")
            
            # Trouver le PC
            pc_device = None
            for device in devices:
                if device.name == pc_name:
                    pc_device = device
                    break
            
            if not pc_device:
                logger.warning(f"⚠️ PC {pc_name} non trouvé")
                continue
            
            # Connexion au PC
            console_conn = config_manager.connect_to_console(pc_device)
            if not console_conn:
                logger.warning(f"⚠️ Connexion {pc_name} échouée")
                continue
            
            try:
                # Configuration VPCS
                vpcs_commands = [
                    "\\n",
                    f"ip {ip_address} {gateway}\\n",
                    "save\\n",
                    "show ip\\n"
                ]
                
                for cmd in vpcs_commands:
                    response = console_conn.send_command(cmd)
                    logger.debug(f"   {pc_name}: {cmd.strip()} -> {response[:50]}...")
                    time.sleep(2)
                
                # Test ping vers gateway
                ping_response = console_conn.send_command(f"ping {gateway}\\n")
                if "host reachable" in ping_response.lower():
                    logger.info(f"   ✅ {pc_name} peut pinger sa gateway")
                    successful_pcs += 1
                else:
                    logger.warning(f"   ⚠️ {pc_name} ne peut pas pinger sa gateway")
                
            finally:
                console_conn.close()
                
            time.sleep(2)
        
        logger.info(f"📊 PCs configurés: {successful_pcs}/{len(vpcs_configs)}")
        return successful_pcs >= 2
        
    except Exception as e:
        logger.error(f"❌ Erreur configuration PCs: {e}")
        return False

def test_complete_connectivity():
    """Test de connectivité complète entre tous les équipements"""
    try:
        logger.info("🔍 TEST DE CONNECTIVITÉ COMPLÈTE")
        
        config_manager = DHCPConfigurationManager()
        
        # Test via framework existant
        connectivity_results = config_manager.verify_connectivity()
        
        accessible_count = sum(1 for accessible in connectivity_results.values() if accessible)
        total_count = len(connectivity_results)
        
        logger.info(f"🌐 Résultat global: {accessible_count}/{total_count} équipements accessibles")
        
        # Détail par équipement
        for device_name, accessible in connectivity_results.items():
            status = "✅" if accessible else "❌"
            logger.info(f"   {status} {device_name}")
        
        success_rate = (accessible_count / total_count) * 100
        logger.info(f"📈 Taux de succès: {success_rate:.1f}%")
        
        return success_rate >= 80.0  # 80% minimum requis
        
    except Exception as e:
        logger.error(f"❌ Erreur test connectivité: {e}")
        return False

def main():
    """Fonction principale de correction complète"""
    logger.info("🚀 DÉMARRAGE DE LA CORRECTION COMPLÈTE DE CONNECTIVITÉ")
    logger.info("=" * 80)
    
    results = {}
    
    try:
        # Étape 1: Configuration PC1 (critique pour les tests)
        logger.info("📊 ÉTAPE 1: Correction configuration PC1")
        results["pc1_fix"] = fix_pc1_configuration()
        
        # Étape 2: Configuration complète du routeur
        logger.info("📊 ÉTAPE 2: Configuration complète du routeur principal")
        results["router_fix"] = fix_router_complete()
        
        # Attente stabilisation
        logger.info("⏳ Attente stabilisation réseau (30s)...")
        time.sleep(30)
        
        # Étape 3: Configuration des switches
        logger.info("📊 ÉTAPE 3: Configuration des trunks sur les switches")
        results["switches_fix"] = fix_switches_trunk()
        
        # Étape 4: Configuration des PCs VPCS
        logger.info("📊 ÉTAPE 4: Configuration de tous les PCs VPCS")
        results["vpcs_fix"] = fix_vpcs_devices()
        
        # Attente stabilisation finale
        logger.info("⏳ Attente stabilisation finale (20s)...")
        time.sleep(20)
        
        # Étape 5: Test de connectivité complète
        logger.info("📊 ÉTAPE 5: Test de connectivité complète")
        results["connectivity_test"] = test_complete_connectivity()
        
        # Résumé final
        logger.info("📊 RÉSUMÉ DE LA CORRECTION COMPLÈTE")
        logger.info("=" * 80)
        
        successful_steps = sum(results.values())
        total_steps = len(results)
        
        for step_name, success in results.items():
            status = "✅" if success else "❌"
            logger.info(f"   {status} {step_name.replace('_', ' ').title()}")
        
        logger.info(f"📈 Étapes réussies: {successful_steps}/{total_steps}")
        
        if successful_steps >= 4:
            logger.info("🎉 CORRECTION RÉUSSIE: Réseau opérationnel pour les tests")
        elif successful_steps >= 2:
            logger.info("⚠️ CORRECTION PARTIELLE: Certains problèmes résolus")
        else:
            logger.warning("❌ CORRECTION ÉCHOUÉE: Problèmes majeurs persistent")
        
        logger.info("=" * 80)
        
        return successful_steps >= 4
        
    except Exception as e:
        logger.error(f"❌ Erreur lors de la correction complète: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    main()