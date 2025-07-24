#!/usr/bin/env python3
"""
Configuration QEMU via SSH (remplacement de vncdo)
================================================

Script pour configurer les serveurs QEMU via SSH au lieu de VNC
car vncdo n'est plus disponible.

Auteur: Claude Code
Date: 2025-07-20
"""

import paramiko
import time
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class QEMUSSHConfigurator:
    """Configuration des serveurs QEMU via SSH"""
    
    def __init__(self):
        self.ssh_credentials = {
            "Server-Web": {"user": "user", "password": "password", "port": 22},
            "Server-Mail": {"user": "user", "password": "password", "port": 22},
            "Server-DNS": {"user": "user", "password": "password", "port": 22},
            "Server-DB": {"user": "user", "password": "password", "port": 22},
            "Server-Fichiers": {"user": "user", "password": "password", "port": 22},
            "PostTest": {"user": "user", "password": "password", "port": 22}
        }
    
    def configure_qemu_server(self, server_name: str, ip_address: str, netmask: str = "255.255.255.0", gateway: str = None) -> bool:
        """
        Configure un serveur QEMU via SSH
        
        Args:
            server_name: Nom du serveur
            ip_address: Adresse IP à configurer
            netmask: Masque de sous-réseau
            gateway: Passerelle par défaut
            
        Returns:
            bool: True si succès, False sinon
        """
        try:
            if server_name not in self.ssh_credentials:
                logger.warning(f"⚠️ Pas de configuration SSH pour {server_name}")
                return False
                
            creds = self.ssh_credentials[server_name]
            
            # Tentative de connexion SSH
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            # Essai de connexion directe via IP cible
            try:
                ssh.connect(ip_address, port=creds["port"], username=creds["user"], password=creds["password"], timeout=10)
                logger.info(f"✅ Connexion SSH réussie vers {server_name} ({ip_address})")
                
                # Configuration réseau
                commands = [
                    f"sudo ip addr add {ip_address}/{netmask.count('255')*8} dev eth0",
                    "sudo ip link set eth0 up"
                ]
                
                if gateway:
                    commands.append(f"sudo ip route add default via {gateway}")
                    
                for cmd in commands:
                    stdin, stdout, stderr = ssh.exec_command(cmd)
                    output = stdout.read().decode()
                    error = stderr.read().decode()
                    
                    if error and "File exists" not in error:
                        logger.warning(f"⚠️ SSH {server_name}: {error.strip()}")
                    else:
                        logger.info(f"✅ SSH {server_name}: {cmd}")
                
                ssh.close()
                return True
                
            except Exception as e:
                logger.warning(f"⚠️ Connexion SSH échouée pour {server_name}: {e}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Erreur configuration SSH {server_name}: {e}")
            return False
    
    def test_server_connectivity(self, server_name: str, ip_address: str) -> bool:
        """
        Test la connectivité d'un serveur QEMU
        
        Args:
            server_name: Nom du serveur
            ip_address: Adresse IP à tester
            
        Returns:
            bool: True si accessible, False sinon
        """
        try:
            import subprocess
            result = subprocess.run(['ping', '-c', '3', '-W', '2', ip_address], 
                                  capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                logger.info(f"✅ {server_name} ({ip_address}) accessible via ping")
                return True
            else:
                logger.warning(f"⚠️ {server_name} ({ip_address}) non accessible via ping")
                return False
                
        except Exception as e:
            logger.error(f"❌ Erreur test connectivité {server_name}: {e}")
            return False

# Configuration des serveurs QEMU par défaut
QEMU_DEFAULT_IPS = {
    "Server-Web": "192.168.10.10",
    "Server-Mail": "192.168.10.11", 
    "Server-DNS": "192.168.11.11",
    "Server-DB": "192.168.30.10",
    "Server-Fichiers": "192.168.31.10",
    "PostTest": "192.168.32.10"
}

def configure_all_qemu_servers() -> Dict[str, bool]:
    """
    Configure tous les serveurs QEMU
    
    Returns:
        Dict[str, bool]: Résultats de configuration par serveur
    """
    configurator = QEMUSSHConfigurator()
    results = {}
    
    for server_name, ip_address in QEMU_DEFAULT_IPS.items():
        # Extraction de la gateway depuis l'IP
        ip_parts = ip_address.split('.')
        gateway = f"{ip_parts[0]}.{ip_parts[1]}.{ip_parts[2]}.1"
        
        logger.info(f"🔧 Configuration SSH {server_name} → {ip_address}")
        success = configurator.configure_qemu_server(server_name, ip_address, gateway=gateway)
        results[server_name] = success
        
        if success:
            # Test de connectivité
            configurator.test_server_connectivity(server_name, ip_address)
    
    return results

if __name__ == "__main__":
    print("🔧 Configuration des serveurs QEMU via SSH...")
    results = configure_all_qemu_servers()
    
    success_count = sum(1 for success in results.values() if success)
    total_count = len(results)
    
    print(f"📊 Configuration terminée: {success_count}/{total_count} serveurs configurés")
    
    for server, success in results.items():
        status = "✅ SUCCÈS" if success else "❌ ÉCHEC"
        print(f"   {server}: {status}")