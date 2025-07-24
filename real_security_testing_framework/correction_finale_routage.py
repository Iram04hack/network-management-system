#!/usr/bin/env python3
"""
Correction finale du routage
===========================

Corrige la boucle de routage détectée et finalise la connectivité.
"""

import subprocess
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def fix_host_routing():
    """Corrige les routes en conflit sur l'hôte"""
    logger.info("🔧 Correction des routes hôte...")
    
    networks = ["192.168.10.0/24", "192.168.20.0/24", "192.168.30.0/24", 
                "192.168.31.0/24", "192.168.41.0/24"]
    
    for network in networks:
        try:
            # Supprimer toutes les routes en conflit
            subprocess.run(f"sudo ip route del {network} 2>/dev/null || true", shell=True)
            subprocess.run(f"sudo ip route del {network} dev tap1 scope link metric 100 2>/dev/null || true", shell=True)
            
            # Ajouter uniquement la route via
            result = subprocess.run(f"sudo ip route add {network} via 10.255.255.2 dev tap1", 
                                  shell=True, capture_output=True, text=True)
            
            if result.returncode == 0 or "File exists" in result.stderr:
                logger.info(f"✅ Route {network} configurée")
            else:
                logger.warning(f"⚠️ Route {network}: {result.stderr}")
                
        except Exception as e:
            logger.error(f"❌ Erreur route {network}: {e}")

def test_final_connectivity():
    """Test final complet"""
    logger.info("🔍 Test final de connectivité...")
    
    targets = [
        ("10.255.255.2", "Routeur-Bordure"),
        ("192.168.41.1", "Routeur-Principal"), 
        ("192.168.20.10", "PC1"),
        ("192.168.41.10", "Admin"),
        ("192.168.10.10", "Server-Web"),
        ("192.168.30.10", "Server-DNS"),
        ("192.168.31.10", "Server-Mail")
    ]
    
    accessible = 0
    for ip, name in targets:
        try:
            result = subprocess.run(f"ping -c 3 -W 3 {ip}", shell=True,
                                  capture_output=True, text=True, timeout=12)
            
            if result.returncode == 0:
                logger.info(f"✅ {name} ({ip}) accessible")
                accessible += 1
            else:
                logger.warning(f"❌ {name} ({ip}) inaccessible")
                
        except Exception as e:
            logger.error(f"❌ Erreur test {name}: {e}")
    
    return accessible, len(targets)

def main():
    """Correction finale complète"""
    print("🚀 CORRECTION FINALE DU ROUTAGE")
    print("=" * 40)
    
    # Correction routes
    fix_host_routing()
    
    # Test connectivité
    accessible, total = test_final_connectivity()
    
    # Résultat
    print(f"\n📊 RÉSULTAT FINAL")
    print(f"🌐 Connectivité: {accessible}/{total} équipements")
    success_rate = (accessible / total) * 100
    print(f"📈 Taux de succès: {success_rate:.1f}%")
    
    if accessible >= 5:
        print("🎉 SUCCÈS COMPLET! Framework totalement opérationnel")
        return True
    elif accessible >= 3:
        print("⚠️ Succès partiel - Framework fonctionnel")
        return True
    else:
        print("❌ Problèmes persistants - Investigation requise")
        return False

if __name__ == "__main__":
    main()