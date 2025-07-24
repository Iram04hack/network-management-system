#!/usr/bin/env python3
"""
Test de connectivité depuis les routeurs
========================================

Teste la connectivité depuis les routeurs vers les équipements finaux.
"""

import telnetlib
import time
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_from_routeur_principal():
    """Test de connectivité depuis le Routeur-Principal"""
    logger.info("🔍 Test depuis Routeur-Principal...")
    
    targets = ["192.168.20.10", "192.168.10.10", "192.168.41.10", 
               "192.168.30.10", "192.168.31.10"]
    
    try:
        tn = telnetlib.Telnet("192.168.122.95", 5021, timeout=15)
        time.sleep(3)
        
        # Attendre le prompt
        tn.read_until(b"#", timeout=15)
        
        results = {}
        for target in targets:
            logger.info(f"Test ping vers {target}...")
            
            tn.write(f"ping {target} timeout 2\n".encode('ascii'))
            time.sleep(8)  # Attendre les pings
            
            response = tn.read_until(b"#", timeout=10).decode()
            
            if "Success rate is 0 percent" in response or "timed out" in response:
                logger.warning(f"❌ {target} inaccessible depuis Routeur-Principal")
                results[target] = False
            elif "Success rate" in response and not "0 percent" in response:
                logger.info(f"✅ {target} accessible depuis Routeur-Principal")  
                results[target] = True
            else:
                logger.warning(f"⚠️ {target} résultat incertain")
                results[target] = None
                
        tn.close()
        return results
        
    except Exception as e:
        logger.error(f"❌ Erreur test Routeur-Principal: {e}")
        return {}

def test_from_routeur_bordure():
    """Test de connectivité depuis le Routeur-Bordure"""
    logger.info("🔍 Test depuis Routeur-Bordure...")
    
    targets = ["192.168.41.1", "10.255.255.1"]  # Test vers Routeur-Principal et hôte
    
    try:
        tn = telnetlib.Telnet("192.168.122.95", 5024, timeout=15)
        time.sleep(3)
        
        # Attendre le prompt
        tn.read_until(b"#", timeout=15)
        
        results = {}
        for target in targets:
            logger.info(f"Test ping vers {target}...")
            
            tn.write(f"ping {target} timeout 2\n".encode('ascii'))
            time.sleep(8)
            
            response = tn.read_until(b"#", timeout=10).decode()
            
            if "Success rate is 0 percent" in response or "timed out" in response:
                logger.warning(f"❌ {target} inaccessible depuis Routeur-Bordure")
                results[target] = False
            elif "Success rate" in response and not "0 percent" in response:
                logger.info(f"✅ {target} accessible depuis Routeur-Bordure")
                results[target] = True
            else:
                logger.warning(f"⚠️ {target} résultat incertain")
                results[target] = None
                
        tn.close()
        return results
        
    except Exception as e:
        logger.error(f"❌ Erreur test Routeur-Bordure: {e}")
        return {}

def check_equipment_status():
    """Vérifie l'état des équipements dans GNS3"""
    logger.info("🔍 Vérification état équipements GNS3...")
    
    import subprocess
    import json
    
    try:
        result = subprocess.run(
            "curl -s http://localhost:3080/v2/projects/6b858ee5-4a49-4f72-b437-8dcd8d876bad/nodes",
            shell=True, capture_output=True, text=True
        )
        
        if result.returncode == 0:
            nodes = json.loads(result.stdout)
            
            equipment_status = {}
            target_names = ["PC1", "Admin", "Server-Web", "Server-DNS", "Server-Mail"]
            
            for node in nodes:
                name = node.get("name", "")
                if name in target_names:
                    status = node.get("status", "unknown")
                    equipment_status[name] = status
                    
                    if status == "started":
                        logger.info(f"✅ {name} : démarré")
                    else:
                        logger.warning(f"❌ {name} : {status}")
            
            return equipment_status
            
    except Exception as e:
        logger.error(f"❌ Erreur vérification GNS3: {e}")
        return {}

def main():
    """Test complet depuis les routeurs"""
    print("🚀 TEST CONNECTIVITÉ DEPUIS LES ROUTEURS")
    print("=" * 50)
    
    # Vérifier l'état des équipements
    equipment_status = check_equipment_status()
    
    # Test depuis Routeur-Bordure
    bordure_results = test_from_routeur_bordure()
    
    # Test depuis Routeur-Principal  
    principal_results = test_from_routeur_principal()
    
    # Résumé
    print(f"\n📊 RÉSUMÉ DES TESTS")
    print(f"🔧 Équipements GNS3: {len([s for s in equipment_status.values() if s == 'started'])}/{len(equipment_status)} démarrés")
    print(f"🔧 Routeur-Bordure: {len([r for r in bordure_results.values() if r])}/{len(bordure_results)} connexions")
    print(f"🔧 Routeur-Principal: {len([r for r in principal_results.values() if r])}/{len(principal_results)} connexions")
    
    if len([r for r in principal_results.values() if r]) >= 2:
        print("✅ Routeurs fonctionnels - Problème probablement dans équipements finaux")
    else:
        print("❌ Problème de routage entre routeurs")

if __name__ == "__main__":
    main()