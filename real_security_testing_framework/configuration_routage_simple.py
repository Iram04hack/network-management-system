#!/usr/bin/env python3
"""
Configuration routage simplifiée
===============================

Script simplifié pour configurer rapidement le routage essential.

Auteur: Claude Code
Date: 2025-07-21
"""

import subprocess
import logging
import time

logger = logging.getLogger(__name__)

def configure_host_routes():
    """Configure les routes sur l'hôte Linux"""
    logger.info("🔧 Configuration des routes hôte...")
    
    routes = [
        "ip route add 192.168.10.0/24 via 10.255.255.2 dev tap1",
        "ip route add 192.168.20.0/24 via 10.255.255.2 dev tap1", 
        "ip route add 192.168.30.0/24 via 10.255.255.2 dev tap1",
        "ip route add 192.168.31.0/24 via 10.255.255.2 dev tap1",
        "ip route add 192.168.41.0/24 via 10.255.255.2 dev tap1"
    ]
    
    for route in routes:
        try:
            result = subprocess.run(f"sudo {route}", shell=True, 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0 or "File exists" in result.stderr:
                logger.info(f"✅ Route ajoutée: {route.split('add ')[1]}")
            else:
                logger.warning(f"⚠️ Route échouée: {result.stderr.strip()}")
        except Exception as e:
            logger.error(f"❌ Erreur route: {e}")

def test_connectivity():
    """Test la connectivité vers les équipements"""
    logger.info("🔍 Test de connectivité...")
    
    targets = [
        ("10.255.255.2", "Routeur-Bordure"),
        ("192.168.20.10", "PC1"),
        ("192.168.41.10", "Admin"),
        ("192.168.10.10", "Server-Web")
    ]
    
    results = {}
    
    for ip, name in targets:
        try:
            result = subprocess.run(f"ping -c 2 -W 3 {ip}", shell=True,
                                  capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                logger.info(f"✅ {name} ({ip}) accessible")
                results[name] = True
            else:
                logger.warning(f"❌ {name} ({ip}) inaccessible")
                results[name] = False
                
        except Exception as e:
            logger.error(f"❌ Erreur test {name}: {e}")
            results[name] = False
    
    return results

def configure_simple_router_routes():
    """Configuration simplifiée des routes routeur via CLI rapide"""
    logger.info("🚀 Configuration routeur simplifiée...")
    
    # Configuration Routeur-Bordure via commandes directes
    commands = [
        "configure terminal",
        "ip route 192.168.10.0 255.255.255.0 192.168.41.1",
        "ip route 192.168.20.0 255.255.255.0 192.168.41.1", 
        "ip route 192.168.30.0 255.255.255.0 192.168.41.1",
        "ip route 192.168.31.0 255.255.255.0 192.168.41.1",
        "ip route 192.168.41.0 255.255.255.0 192.168.41.1",
        "end",
        "write memory"
    ]
    
    # Utilisation d'expect pour automatiser
    expect_script = f'''#!/usr/bin/expect -f
set timeout 30
spawn telnet 192.168.122.95 5024
expect "#"
{"".join([f'send "{cmd}\\r"; expect "#"; ' for cmd in commands])}
send "exit\\r"
expect eof
'''
    
    with open("/tmp/router_config.exp", "w") as f:
        f.write(expect_script)
    
    try:
        result = subprocess.run("chmod +x /tmp/router_config.exp && /tmp/router_config.exp", 
                              shell=True, capture_output=True, text=True, timeout=60)
        
        if "error" not in result.stderr.lower():
            logger.info("✅ Configuration routeur terminée")
            return True
        else:
            logger.warning("⚠️ Configuration routeur partielle")
            return False
            
    except Exception as e:
        logger.error(f"❌ Erreur configuration routeur: {e}")
        return False

def main():
    """Fonction principale"""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    print("🎯 CONFIGURATION ROUTAGE SIMPLIFIÉE")
    print("=" * 50)
    
    # 1. Configuration routes hôte
    configure_host_routes()
    time.sleep(2)
    
    # 2. Configuration routeur (si expect disponible)
    try:
        subprocess.run("which expect", shell=True, check=True, capture_output=True)
        configure_simple_router_routes()
    except:
        logger.warning("⚠️ expect non disponible - configuration routeur manuelle requise")
    
    # 3. Test de connectivité
    print("\n📊 TEST DE CONNECTIVITÉ")
    print("=" * 30)
    
    results = test_connectivity()
    
    success_count = sum(1 for success in results.values() if success)
    total_count = len(results)
    
    print(f"\n🎯 RÉSULTAT: {success_count}/{total_count} équipements accessibles")
    
    if success_count >= 3:
        print("✅ Connectivité largement améliorée!")
        print("💡 Le framework de tests peut maintenant fonctionner")
    elif success_count >= 1:
        print("⚠️ Connectivité partiellement rétablie")
        print("💡 Quelques équipements restent inaccessibles")
    else:
        print("❌ Problèmes de connectivité persistent")
        print("💡 Vérification manuelle des routeurs nécessaire")

if __name__ == "__main__":
    main()