#!/usr/bin/env python3
"""
Configuration des ports Cloud1 vers les bridges
===============================================

Ce script configure les ports du Cloud1 pour qu'ils pointent
vers les bridges créés, établissant la connectivité.

Auteur: Claude Code
Date: 2025-07-20
"""

import logging
import sys
import time
import requests
import subprocess

# Configuration logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def configure_cloud_ports():
    """Configure les ports du Cloud1 pour pointer vers les bridges"""
    try:
        logger.info("🔧 CONFIGURATION DES PORTS CLOUD1")
        logger.info("=" * 40)
        
        gns3_url = "http://localhost:3080/v2"
        project_id = "6b858ee5-4a49-4f72-b437-8dcd8d876bad"
        cloud_node_id = "9260b8fb-a80d-440a-b81a-18fa3e48fb44"
        
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
        session = requests.Session()
        response = session.put(
            f"{gns3_url}/projects/{project_id}/nodes/{cloud_node_id}",
            json=cloud_config
        )
        
        if response.status_code == 200:
            logger.info("✅ Configuration Cloud1 mise à jour")
            return True
        else:
            logger.warning(f"⚠️ Échec configuration Cloud1: {response.status_code}")
            logger.debug(f"Réponse: {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Erreur configuration Cloud1: {e}")
        return False

def test_bridge_connectivity():
    """Teste la connectivité via les bridges"""
    logger.info("🔍 TEST DE CONNECTIVITÉ VIA BRIDGES")
    
    # IPs à tester via les bridges
    test_cases = [
        ("br-vlan10", "192.168.10.10", "Server-Web"),
        ("br-vlan20", "192.168.20.10", "PC1"),
        ("br-vlan41", "192.168.41.10", "Admin"),
        ("br-vlan30", "192.168.30.10", "Server-DB")
    ]
    
    accessible_count = 0
    
    for bridge, ip, name in test_cases:
        try:
            # Test ping via le bridge spécifique
            result = subprocess.run([
                'ping', '-I', bridge, '-c', '1', '-W', '2', ip
            ], capture_output=True, timeout=3)
            
            if result.returncode == 0:
                logger.info(f"   ✅ {name} ({ip}) accessible via {bridge}")
                accessible_count += 1
            else:
                logger.info(f"   ❌ {name} ({ip}) inaccessible via {bridge}")
                
        except Exception as e:
            logger.info(f"   ❌ {name} ({ip}) timeout/erreur")
    
    return accessible_count

def setup_bridge_forwarding():
    """Active le forwarding sur les bridges"""
    try:
        logger.info("🔧 ACTIVATION DU FORWARDING SUR LES BRIDGES")
        
        bridges = ["br-vlan10", "br-vlan20", "br-vlan41", "br-vlan30"]
        
        for bridge in bridges:
            try:
                # Activer le forwarding
                subprocess.run([
                    'sudo', 'echo', '1'
                ], stdout=subprocess.PIPE, check=True)
                
                subprocess.run([
                    'sudo', 'tee', f'/proc/sys/net/ipv4/conf/{bridge}/forwarding'
                ], input=b'1', check=True)
                
                logger.info(f"   ✅ Forwarding activé sur {bridge}")
                
            except Exception as e:
                logger.debug(f"   ⚠️ Erreur forwarding {bridge}: {e}")
        
        # Forwarding global
        subprocess.run([
            'sudo', 'sysctl', 'net.ipv4.ip_forward=1'
        ], check=True)
        
        logger.info("✅ Forwarding IP global activé")
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur activation forwarding: {e}")
        return False

def add_routes_to_gns3():
    """Ajoute des routes vers les réseaux GNS3"""
    try:
        logger.info("🔧 AJOUT DES ROUTES VERS LES RÉSEAUX GNS3")
        
        routes = [
            ("192.168.10.0/24", "br-vlan10"),
            ("192.168.20.0/24", "br-vlan20"), 
            ("192.168.41.0/24", "br-vlan41"),
            ("192.168.30.0/24", "br-vlan30")
        ]
        
        for network, bridge in routes:
            try:
                # Ajouter la route
                subprocess.run([
                    'sudo', 'ip', 'route', 'add', network, 'dev', bridge
                ], check=True)
                
                logger.info(f"   ✅ Route {network} via {bridge}")
                
            except subprocess.CalledProcessError:
                # Route peut déjà exister
                logger.debug(f"   ⚠️ Route {network} existe déjà")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur ajout routes: {e}")
        return False

def test_final_connectivity():
    """Test final de connectivité"""
    logger.info("🔍 TEST FINAL DE CONNECTIVITÉ")
    
    # Test direct des équipements
    test_ips = [
        ("192.168.10.10", "Server-Web"),
        ("192.168.20.10", "PC1"),
        ("192.168.41.10", "Admin"),
        ("192.168.30.10", "Server-DB")
    ]
    
    accessible_count = 0
    accessible_devices = []
    
    for ip, name in test_ips:
        try:
            result = subprocess.run([
                'ping', '-c', '1', '-W', '2', ip
            ], capture_output=True, timeout=3)
            
            if result.returncode == 0:
                logger.info(f"   ✅ {name} ({ip}) ACCESSIBLE")
                accessible_count += 1
                accessible_devices.append(name)
            else:
                logger.info(f"   ❌ {name} ({ip}) inaccessible")
                
        except:
            logger.info(f"   ❌ {name} ({ip}) timeout")
    
    return accessible_count, accessible_devices

def main():
    """Fonction principale"""
    logger.info("🚀 CONFIGURATION BRIDGES CLOUD1")
    
    try:
        # 1. Configuration du Cloud1
        logger.info("📊 ÉTAPE 1: Configuration des ports Cloud1")
        cloud_success = configure_cloud_ports()
        
        # 2. Activation du forwarding
        logger.info("📊 ÉTAPE 2: Activation du forwarding")
        forwarding_success = setup_bridge_forwarding()
        
        # 3. Ajout des routes
        logger.info("📊 ÉTAPE 3: Configuration des routes")
        routes_success = add_routes_to_gns3()
        
        # 4. Attente stabilisation
        logger.info("📊 ÉTAPE 4: Attente stabilisation (15s)")
        time.sleep(15)
        
        # 5. Test final
        logger.info("📊 ÉTAPE 5: Test final de connectivité")
        accessible_count, accessible_devices = test_final_connectivity()
        
        # 6. Résumé
        logger.info("📊 RÉSUMÉ FINAL")
        logger.info("=" * 40)
        logger.info(f"🔧 Configuration Cloud1: {'✅' if cloud_success else '❌'}")
        logger.info(f"🔧 Forwarding activé: {'✅' if forwarding_success else '❌'}")
        logger.info(f"🔧 Routes configurées: {'✅' if routes_success else '❌'}")
        logger.info(f"🌐 Équipements accessibles: {accessible_count}/4")
        
        if accessible_devices:
            logger.info(f"✅ ACCESSIBLES: {', '.join(accessible_devices)}")
        
        if accessible_count >= 2:
            logger.info("🎉 SUCCÈS: Connectivité établie pour les tests!")
            return True
        else:
            logger.warning("⚠️ CONNECTIVITÉ LIMITÉE: Vérification manuelle nécessaire")
            return False
            
    except Exception as e:
        logger.error(f"❌ Erreur configuration: {e}")
        return False

if __name__ == "__main__":
    main()