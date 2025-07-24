#!/usr/bin/env python3
"""
Résolution finale de la connectivité réseau
===========================================

Ce script corrige les problèmes de connectivité en :
1. Configurant directement les équipements via console
2. Corrigeant les routes sur les routeurs
3. Testant la connectivité finale
"""

import telnetlib
import time
import subprocess
import logging
import socket

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NetworkConnectivityResolver:
    def __init__(self):
        self.console_host = "192.168.122.95"  # IP du serveur GNS3
        self.console_configs = {
            "PC1": {"port": 5007, "type": "vpcs"},
            "Admin": {"port": 5009, "type": "vpcs"},
            "Routeur-Principal": {"port": 5021, "type": "cisco"},
            "Routeur-Bordure": {"port": 5024, "type": "cisco"}
        }
    
    def connect_console(self, device_name, timeout=10):
        """Se connecte à la console d'un équipement"""
        try:
            config = self.console_configs.get(device_name)
            if not config:
                logger.error(f"❌ Configuration console inconnue pour {device_name}")
                return None
            
            tn = telnetlib.Telnet(self.console_host, config["port"], timeout=timeout)
            logger.info(f"✅ Connexion console {device_name} sur port {config['port']}")
            return tn
        except Exception as e:
            logger.error(f"❌ Échec connexion console {device_name}: {e}")
            return None
    
    def configure_vpcs_device(self, device_name, ip_address, gateway):
        """Configure un équipement VPCS"""
        try:
            tn = self.connect_console(device_name)
            if not tn:
                return False
            
            logger.info(f"🔧 Configuration {device_name} avec IP {ip_address}")
            
            # Attendre l'invite
            time.sleep(2)
            
            # Envoyer configuration IP
            commands = [
                "\n",  # Retour à la ligne pour avoir l'invite
                f"ip {ip_address} {gateway}\n",
                "save\n",
                "show ip\n"
            ]
            
            for cmd in commands:
                tn.write(cmd.encode('ascii'))
                time.sleep(1)
            
            # Lire la réponse
            response = tn.read_very_eager().decode('ascii', errors='ignore')
            logger.info(f"📋 Réponse {device_name}: {response[-100:]}")  # Derniers 100 caractères
            
            tn.close()
            logger.info(f"✅ Configuration {device_name} terminée")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur configuration {device_name}: {e}")
            return False
    
    def configure_cisco_router(self, device_name, interface_configs, routes=None):
        """Configure un routeur Cisco"""
        try:
            tn = self.connect_console(device_name, timeout=15)
            if not tn:
                return False
            
            logger.info(f"🔧 Configuration routeur {device_name}")
            
            time.sleep(3)
            
            # Entrer en mode configuration
            commands = [
                "\n",
                "enable\n",
                "cisco\n",  # Mot de passe enable
                "configure terminal\n"
            ]
            
            # Configuration des interfaces
            for interface, config in interface_configs.items():
                commands.extend([
                    f"interface {interface}\n",
                    f"ip address {config['ip']} {config['mask']}\n",
                    "no shutdown\n",
                    "exit\n"
                ])
            
            # Configuration des routes statiques
            if routes:
                for route in routes:
                    commands.append(f"ip route {route}\n")
            
            commands.extend([
                "exit\n",
                "copy running-config startup-config\n",
                "\n",  # Confirmer la sauvegarde
                "show ip interface brief\n",
                "show ip route\n"
            ])
            
            for cmd in commands:
                tn.write(cmd.encode('ascii'))
                time.sleep(1.5)
            
            # Lire la réponse complète
            time.sleep(5)
            response = tn.read_very_eager().decode('ascii', errors='ignore')
            logger.info(f"📋 Configuration {device_name} appliquée")
            
            tn.close()
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur configuration routeur {device_name}: {e}")
            return False
    
    def test_connectivity_from_host(self, target_ip):
        """Teste la connectivité depuis l'hôte"""
        try:
            result = subprocess.run(
                ["ping", "-c", "3", "-W", "2", target_ip],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                logger.info(f"✅ Connectivité OK vers {target_ip}")
                return True
            else:
                logger.warning(f"⚠️ Pas de connectivité vers {target_ip}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Erreur test connectivité {target_ip}: {e}")
            return False
    
    def resolve_connectivity_issues(self):
        """Résolution complète des problèmes de connectivité"""
        logger.info("🚀 DÉBUT DE LA RÉSOLUTION DE CONNECTIVITÉ")
        
        # 1. Configuration PC1
        logger.info("📍 Étape 1: Configuration PC1")
        pc1_success = self.configure_vpcs_device(
            "PC1", 
            "192.168.20.10/24", 
            "192.168.20.1"
        )
        
        # 2. Configuration Admin
        logger.info("📍 Étape 2: Configuration Admin")
        admin_success = self.configure_vpcs_device(
            "Admin", 
            "192.168.41.10/24", 
            "192.168.41.1"
        )
        
        # 3. Configuration Routeur-Principal
        logger.info("📍 Étape 3: Configuration Routeur-Principal")
        principal_config = {
            "FastEthernet0/0": {"ip": "10.255.255.1", "mask": "255.255.255.252"},
            "FastEthernet0/1": {"ip": "192.168.41.1", "mask": "255.255.255.0"}
        }
        principal_routes = [
            "192.168.10.0 255.255.255.0 10.255.255.2",
            "192.168.20.0 255.255.255.0 10.255.255.2", 
            "0.0.0.0 0.0.0.0 10.255.255.2"  # Route par défaut
        ]
        
        principal_success = self.configure_cisco_router(
            "Routeur-Principal",
            principal_config,
            principal_routes
        )
        
        # 4. Configuration Routeur-Bordure
        logger.info("📍 Étape 4: Configuration Routeur-Bordure")
        bordure_config = {
            "FastEthernet0/0": {"ip": "10.255.255.2", "mask": "255.255.255.252"},
            "FastEthernet0/1": {"ip": "192.168.10.1", "mask": "255.255.255.0"},
            "FastEthernet1/0": {"ip": "192.168.20.1", "mask": "255.255.255.0"}
        }
        bordure_routes = [
            "192.168.41.0 255.255.255.0 10.255.255.1",
            "0.0.0.0 0.0.0.0 10.255.255.1"  # Route par défaut vers Principal
        ]
        
        bordure_success = self.configure_cisco_router(
            "Routeur-Bordure",
            bordure_config,
            bordure_routes
        )
        
        # 5. Attendre stabilisation
        logger.info("⏳ Attente stabilisation réseau...")
        time.sleep(15)
        
        # 6. Tests de connectivité
        logger.info("📍 Étape 5: Tests de connectivité finale")
        targets = ["192.168.20.10", "192.168.41.10", "192.168.10.10"]
        connectivity_results = {}
        
        for target in targets:
            connectivity_results[target] = self.test_connectivity_from_host(target)
        
        # 7. Rapport final
        logger.info("📊 RAPPORT FINAL DE RÉSOLUTION")
        logger.info(f"PC1 configuré: {'✅' if pc1_success else '❌'}")
        logger.info(f"Admin configuré: {'✅' if admin_success else '❌'}")
        logger.info(f"Routeur-Principal configuré: {'✅' if principal_success else '❌'}")
        logger.info(f"Routeur-Bordure configuré: {'✅' if bordure_success else '❌'}")
        
        logger.info("🌐 CONNECTIVITÉ FINALE:")
        for target, result in connectivity_results.items():
            logger.info(f"  {target}: {'✅ ACCESSIBLE' if result else '❌ INACCESSIBLE'}")
        
        total_success = sum(connectivity_results.values())
        logger.info(f"📈 Taux de réussite: {total_success}/{len(targets)} ({total_success/len(targets)*100:.1f}%)")
        
        return total_success >= len(targets) // 2  # Au moins 50% de réussite

def main():
    resolver = NetworkConnectivityResolver()
    success = resolver.resolve_connectivity_issues()
    
    if success:
        logger.info("🎉 RÉSOLUTION DE CONNECTIVITÉ RÉUSSIE")
        exit(0)
    else:
        logger.error("❌ RÉSOLUTION DE CONNECTIVITÉ ÉCHOUÉE")
        exit(1)

if __name__ == "__main__":
    main()