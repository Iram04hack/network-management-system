#!/usr/bin/env python3
"""
Configuration automatique des routeurs Cisco
==========================================

Script pour configurer automatiquement le routage sur les routeurs
Cisco Dynamips du projet Hybrido.

Auteur: Claude Code
Date: 2025-07-21
"""

import telnetlib
import time
import logging

logger = logging.getLogger(__name__)

class CiscoRouterConfigurator:
    """Configurateur de routeurs Cisco"""
    
    def __init__(self):
        self.routers = {
            "Routeur-Bordure": {
                "host": "192.168.122.95",
                "port": 5024,
                "interfaces": {
                    "f1/0": "10.255.255.2 255.255.255.0",  # Vers Cloud1/tap1
                    "f0/0": "192.168.41.2 255.255.255.0"   # Vers Routeur-Principal
                },
                "routes": [
                    "ip route 192.168.10.0 255.255.255.0 192.168.41.1",
                    "ip route 192.168.11.0 255.255.255.0 192.168.41.1", 
                    "ip route 192.168.12.0 255.255.255.0 192.168.41.1",
                    "ip route 192.168.20.0 255.255.255.0 192.168.41.1",
                    "ip route 192.168.21.0 255.255.255.0 192.168.41.1",
                    "ip route 192.168.30.0 255.255.255.0 192.168.41.1",
                    "ip route 192.168.31.0 255.255.255.0 192.168.41.1",
                    "ip route 192.168.32.0 255.255.255.0 192.168.41.1"
                ]
            },
            "Routeur-Principal": {
                "host": "192.168.122.95", 
                "port": 5021,
                "routes": [
                    "ip route 0.0.0.0 0.0.0.0 192.168.41.2",  # Route par défaut vers Routeur-Bordure
                    "ip route 10.255.255.0 255.255.255.0 192.168.41.2"  # Route vers tap1
                ]
            }
        }
    
    def connect_to_router(self, host: str, port: int, timeout: int = 10) -> telnetlib.Telnet:
        """Se connecte à un routeur via telnet"""
        try:
            tn = telnetlib.Telnet(host, port, timeout)
            time.sleep(2)
            
            # Attendre le prompt
            tn.read_until(b"#", timeout=5)
            logger.info(f"✅ Connecté au routeur {host}:{port}")
            return tn
            
        except Exception as e:
            logger.error(f"❌ Erreur connexion {host}:{port}: {e}")
            return None
    
    def send_command(self, tn: telnetlib.Telnet, command: str, wait_for: str = "#") -> str:
        """Envoie une commande au routeur"""
        try:
            tn.write(command.encode('ascii') + b"\n")
            time.sleep(1)
            response = tn.read_until(wait_for.encode('ascii'), timeout=10)
            return response.decode('ascii', errors='ignore')
        except Exception as e:
            logger.error(f"❌ Erreur commande '{command}': {e}")
            return ""
    
    def configure_router_interfaces(self, tn: telnetlib.Telnet, interfaces: dict) -> bool:
        """Configure les interfaces d'un routeur"""
        try:
            # Mode configuration
            self.send_command(tn, "configure terminal")
            
            for interface, ip_config in interfaces.items():
                logger.info(f"🔧 Configuration interface {interface}: {ip_config}")
                
                self.send_command(tn, f"interface {interface}")
                self.send_command(tn, f"ip address {ip_config}")
                self.send_command(tn, "no shutdown")
                self.send_command(tn, "exit")
                time.sleep(1)
            
            self.send_command(tn, "end")
            logger.info("✅ Interfaces configurées")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur configuration interfaces: {e}")
            return False
    
    def configure_router_routes(self, tn: telnetlib.Telnet, routes: list) -> bool:
        """Configure les routes statiques d'un routeur"""
        try:
            # Mode configuration
            self.send_command(tn, "configure terminal")
            
            for route in routes:
                logger.info(f"🛣️ Configuration route: {route}")
                self.send_command(tn, route)
                time.sleep(1)
            
            self.send_command(tn, "end")
            
            # Sauvegarde
            logger.info("💾 Sauvegarde de la configuration...")
            self.send_command(tn, "copy running-config startup-config")
            self.send_command(tn, "")  # Confirmation
            
            logger.info("✅ Routes configurées et sauvegardées")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur configuration routes: {e}")
            return False
    
    def verify_router_config(self, tn: telnetlib.Telnet, router_name: str) -> bool:
        """Vérifie la configuration d'un routeur"""
        try:
            logger.info(f"🔍 Vérification configuration {router_name}")
            
            # Affichage des interfaces
            result = self.send_command(tn, "show ip interface brief")
            logger.info(f"📊 Interfaces {router_name}:")
            for line in result.split('\n')[2:8]:  # Limiter l'affichage
                if line.strip():
                    logger.info(f"   {line.strip()}")
            
            # Affichage des routes
            result = self.send_command(tn, "show ip route")
            logger.info(f"🛣️ Routes {router_name}:")
            route_lines = [line for line in result.split('\n') if '192.168.' in line or '10.255.' in line]
            for line in route_lines[:10]:  # Limiter l'affichage
                if line.strip():
                    logger.info(f"   {line.strip()}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur vérification {router_name}: {e}")
            return False
    
    def configure_router(self, router_name: str) -> bool:
        """Configure un routeur complet"""
        logger.info(f"🎯 Configuration de {router_name}")
        
        router_config = self.routers.get(router_name)
        if not router_config:
            logger.error(f"❌ Configuration inconnue pour {router_name}")
            return False
        
        # Connexion
        tn = self.connect_to_router(router_config["host"], router_config["port"])
        if not tn:
            return False
        
        try:
            # Configuration des interfaces si définies
            if "interfaces" in router_config:
                if not self.configure_router_interfaces(tn, router_config["interfaces"]):
                    return False
            
            # Configuration des routes
            if "routes" in router_config:
                if not self.configure_router_routes(tn, router_config["routes"]):
                    return False
            
            # Vérification
            self.verify_router_config(tn, router_name)
            
            # Déconnexion
            tn.close()
            
            logger.info(f"✅ {router_name} configuré avec succès")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur configuration {router_name}: {e}")
            if tn:
                tn.close()
            return False
    
    def configure_all_routers(self) -> dict:
        """Configure tous les routeurs"""
        logger.info("🚀 CONFIGURATION DE TOUS LES ROUTEURS")
        logger.info("=" * 50)
        
        results = {}
        
        for router_name in self.routers.keys():
            try:
                success = self.configure_router(router_name)
                results[router_name] = success
                
                if success:
                    logger.info(f"✅ {router_name}: Configuration réussie")
                else:
                    logger.error(f"❌ {router_name}: Configuration échouée")
                
                time.sleep(2)  # Pause entre les routeurs
                
            except Exception as e:
                logger.error(f"❌ Erreur {router_name}: {e}")
                results[router_name] = False
        
        return results

def main():
    """Fonction principale"""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    configurator = CiscoRouterConfigurator()
    
    print("🚀 CONFIGURATION AUTOMATIQUE DES ROUTEURS CISCO")
    print("=" * 60)
    
    results = configurator.configure_all_routers()
    
    # Résumé final
    print("\n📊 RÉSUMÉ DE LA CONFIGURATION")
    print("=" * 40)
    
    success_count = sum(1 for success in results.values() if success)
    total_count = len(results)
    
    for router, success in results.items():
        status = "✅ SUCCÈS" if success else "❌ ÉCHEC"
        print(f"   {router:20} : {status}")
    
    print(f"\n🎯 RÉSULTAT GLOBAL: {success_count}/{total_count} routeurs configurés")
    
    if success_count == total_count:
        print("✅ Tous les routeurs sont configurés!")
        print("💡 Testez la connectivité: ping 192.168.20.10")
    elif success_count > 0:
        print("⚠️ Configuration partielle")
        print("💡 Vérifiez les routeurs en échec")
    else:
        print("❌ Aucun routeur configuré")
        print("💡 Vérifiez la connectivité des consoles")

if __name__ == "__main__":
    main()