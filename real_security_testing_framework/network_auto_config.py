#!/usr/bin/env python3
"""
Configuration Automatique du Réseau - NMS Security Testing Framework
====================================================================

Ce script configure automatiquement le réseau lors du démarrage des équipements GNS3
pour résoudre les problèmes de configuration et assurer la connectivité.

Commandes exécutées automatiquement :
- sudo ip a
- sudo ifconfig tap1 10.255.255.1 netmask 255.255.255.0 up
- sudo ifconfig
- sudo iptables -t nat -A POSTROUTING -o wlp2s0 -j MASQUERADE
- echo 1 | sudo tee /proc/sys/net/ipv4/ip_forward

Mot de passe sudo : root
"""

import subprocess
import logging
import time
import os
import sys
from typing import List, Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class NetworkAutoConfigurator:
    """
    Configurateur automatique du réseau pour le framework de tests de sécurité.
    
    Exécute automatiquement toutes les commandes nécessaires pour configurer
    le réseau et assurer la connectivité entre les équipements GNS3.
    """
    
    def __init__(self, sudo_password: str = "root"):
        """
        Initialise le configurateur.
        
        Args:
            sudo_password: Mot de passe sudo (par défaut: 'root')
        """
        self.sudo_password = sudo_password
        self.commands_executed = []
        self.errors_encountered = []
        
        logger.info("🔧 Configurateur automatique du réseau initialisé")
    
    def execute_sudo_command(self, command: str, description: str = "") -> Dict[str, Any]:
        """
        Exécute une commande avec privilèges sudo.
        
        Args:
            command: Commande à exécuter
            description: Description de la commande
            
        Returns:
            Résultat de l'exécution
        """
        try:
            logger.info(f"🔧 Exécution: {description or command}")
            
            # Créer la commande complète avec echo du mot de passe
            full_command = f'echo "{self.sudo_password}" | sudo -S {command}'
            
            # Exécuter la commande
            result = subprocess.run(
                full_command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            execution_result = {
                "command": command,
                "description": description,
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "return_code": result.returncode
            }
            
            if result.returncode == 0:
                logger.info(f"✅ {description or command} - Succès")
                self.commands_executed.append(execution_result)
            else:
                logger.error(f"❌ {description or command} - Échec: {result.stderr}")
                self.errors_encountered.append(execution_result)
            
            return execution_result
            
        except subprocess.TimeoutExpired:
            error_result = {
                "command": command,
                "description": description,
                "success": False,
                "error": "Timeout après 30 secondes"
            }
            logger.error(f"⏰ Timeout pour: {description or command}")
            self.errors_encountered.append(error_result)
            return error_result
            
        except Exception as e:
            error_result = {
                "command": command,
                "description": description,
                "success": False,
                "error": str(e)
            }
            logger.error(f"❌ Erreur pour {description or command}: {e}")
            self.errors_encountered.append(error_result)
            return error_result
    
    def configure_network_interfaces(self) -> bool:
        """
        Configure les interfaces réseau nécessaires.
        
        Returns:
            True si la configuration réussit
        """
        logger.info("🌐 Configuration des interfaces réseau...")
        
        success = True
        
        # 1. Afficher la configuration IP actuelle
        result = self.execute_sudo_command(
            "ip a",
            "Affichage de la configuration IP actuelle"
        )
        
        # 2. Configurer l'interface tap1
        result = self.execute_sudo_command(
            "ifconfig tap1 10.255.255.1 netmask 255.255.255.0 up",
            "Configuration de l'interface tap1"
        )
        if not result["success"]:
            # Essayer de créer l'interface tap1 si elle n'existe pas
            logger.warning("Interface tap1 introuvable, tentative de création...")
            create_result = self.execute_sudo_command(
                "ip tuntap add dev tap1 mode tap",
                "Création de l'interface tap1"
            )
            if create_result["success"]:
                # Réessayer la configuration
                result = self.execute_sudo_command(
                    "ifconfig tap1 10.255.255.1 netmask 255.255.255.0 up",
                    "Configuration de l'interface tap1 (seconde tentative)"
                )
        
        success &= result["success"]
        
        # 3. Vérifier la configuration avec ifconfig
        result = self.execute_sudo_command(
            "ifconfig",
            "Vérification de la configuration des interfaces"
        )
        
        return success
    
    def configure_iptables_and_forwarding(self) -> bool:
        """
        Configure iptables et l'IP forwarding.
        
        Returns:
            True si la configuration réussit
        """
        logger.info("🔥 Configuration d'iptables et IP forwarding...")
        
        success = True
        
        # 1. Configurer iptables MASQUERADE
        result = self.execute_sudo_command(
            "iptables -t nat -A POSTROUTING -o wlp2s0 -j MASQUERADE",
            "Configuration iptables MASQUERADE sur wlp2s0"
        )
        
        # Si wlp2s0 n'existe pas, essayer avec d'autres interfaces communes
        if not result["success"]:
            common_interfaces = ["eth0", "enp0s3", "wlan0", "ens33"]
            for interface in common_interfaces:
                logger.info(f"Tentative avec l'interface {interface}...")
                result = self.execute_sudo_command(
                    f"iptables -t nat -A POSTROUTING -o {interface} -j MASQUERADE",
                    f"Configuration iptables MASQUERADE sur {interface}"
                )
                if result["success"]:
                    logger.info(f"✅ Configuration réussie avec l'interface {interface}")
                    break
        
        success &= result["success"]
        
        # 2. Activer l'IP forwarding
        result = self.execute_sudo_command(
            "bash -c 'echo 1 > /proc/sys/net/ipv4/ip_forward'",
            "Activation de l'IP forwarding"
        )
        success &= result["success"]
        
        # 3. Vérifier l'état de l'IP forwarding
        self.execute_sudo_command(
            "cat /proc/sys/net/ipv4/ip_forward",
            "Vérification de l'IP forwarding"
        )
        
        return success
    
    def configure_additional_network_settings(self) -> bool:
        """
        Configure des paramètres réseau additionnels pour améliorer la connectivité.
        
        Returns:
            True si la configuration réussit
        """
        logger.info("⚙️ Configuration des paramètres réseau additionnels...")
        
        success = True
        
        # 1. Configurer les routes par défaut pour les interfaces tap
        result = self.execute_sudo_command(
            "ip route add 192.168.0.0/16 dev tap1 2>/dev/null || true",
            "Ajout de route pour le réseau 192.168.0.0/16"
        )
        
        # 2. Configurer les paramètres de bridge si nécessaire
        result = self.execute_sudo_command(
            "modprobe bridge 2>/dev/null || true",
            "Chargement du module bridge"
        )
        
        # 3. Configurer les paramètres de connectivité
        result = self.execute_sudo_command(
            "sysctl -w net.bridge.bridge-nf-call-iptables=0 2>/dev/null || true",
            "Configuration des paramètres de bridge"
        )
        
        return success
    
    def run_full_network_configuration(self) -> Dict[str, Any]:
        """
        Exécute la configuration complète du réseau.
        
        Returns:
            Résultat détaillé de la configuration
        """
        start_time = time.time()
        
        logger.info("🚀 DÉBUT DE LA CONFIGURATION AUTOMATIQUE DU RÉSEAU")
        logger.info("=" * 60)
        
        # 1. Configuration des interfaces
        interfaces_success = self.configure_network_interfaces()
        
        # 2. Configuration iptables et forwarding
        iptables_success = self.configure_iptables_and_forwarding()
        
        # 3. Configuration additionnelle
        additional_success = self.configure_additional_network_settings()
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Résumé final
        overall_success = interfaces_success and iptables_success
        successful_commands = len(self.commands_executed)
        failed_commands = len(self.errors_encountered)
        
        result = {
            "overall_success": overall_success,
            "execution_time_seconds": execution_time,
            "successful_commands": successful_commands,
            "failed_commands": failed_commands,
            "commands_executed": self.commands_executed,
            "errors_encountered": self.errors_encountered,
            "interfaces_configured": interfaces_success,
            "iptables_configured": iptables_success,
            "additional_settings": additional_success
        }
        
        # Affichage du résumé
        logger.info("📊 RÉSUMÉ DE LA CONFIGURATION")
        logger.info("=" * 60)
        logger.info(f"Statut global: {'✅ SUCCÈS' if overall_success else '❌ ÉCHEC PARTIEL'}")
        logger.info(f"Temps d'exécution: {execution_time:.2f} secondes")
        logger.info(f"Commandes réussies: {successful_commands}")
        logger.info(f"Commandes échouées: {failed_commands}")
        logger.info(f"Interfaces réseau: {'✅' if interfaces_success else '❌'}")
        logger.info(f"IPTables/Forwarding: {'✅' if iptables_success else '❌'}")
        
        if self.errors_encountered:
            logger.warning("⚠️ ERREURS RENCONTRÉES:")
            for error in self.errors_encountered:
                logger.warning(f"   - {error['description']}: {error.get('error', error.get('stderr', 'Erreur inconnue'))}")
        
        logger.info("=" * 60)
        
        return result
    
    def verify_network_configuration(self) -> Dict[str, Any]:
        """
        Vérifie que la configuration réseau est correcte.
        
        Returns:
            Résultat de la vérification
        """
        logger.info("🔍 Vérification de la configuration réseau...")
        
        verification_results = {}
        
        # 1. Vérifier l'existence de l'interface tap1
        result = self.execute_sudo_command(
            "ip link show tap1",
            "Vérification de l'interface tap1"
        )
        verification_results["tap1_exists"] = result["success"]
        
        # 2. Vérifier l'IP forwarding
        result = self.execute_sudo_command(
            "cat /proc/sys/net/ipv4/ip_forward",
            "Vérification de l'IP forwarding"
        )
        verification_results["ip_forward_enabled"] = (
            result["success"] and "1" in result.get("stdout", "")
        )
        
        # 3. Vérifier les règles iptables
        result = self.execute_sudo_command(
            "iptables -t nat -L POSTROUTING",
            "Vérification des règles iptables"
        )
        verification_results["iptables_configured"] = (
            result["success"] and "MASQUERADE" in result.get("stdout", "")
        )
        
        # 4. Test de connectivité basique
        result = self.execute_sudo_command(
            "ping -c 1 127.0.0.1",
            "Test de connectivité basique"
        )
        verification_results["basic_connectivity"] = result["success"]
        
        return verification_results

def main():
    """Point d'entrée principal du script."""
    # Configuration du logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    try:
        # Créer le configurateur
        configurator = NetworkAutoConfigurator()
        
        # Exécuter la configuration complète
        result = configurator.run_full_network_configuration()
        
        # Vérifier la configuration
        verification = configurator.verify_network_configuration()
        
        print("\n" + "="*60)
        print("🎯 CONFIGURATION AUTOMATIQUE DU RÉSEAU TERMINÉE")
        print("="*60)
        print(f"Statut: {'✅ SUCCÈS' if result['overall_success'] else '❌ ÉCHEC PARTIEL'}")
        print(f"Commandes réussies: {result['successful_commands']}")
        print(f"Commandes échouées: {result['failed_commands']}")
        print(f"Temps d'exécution: {result['execution_time_seconds']:.2f}s")
        print("\n🔍 VÉRIFICATIONS:")
        for check, status in verification.items():
            print(f"   {check}: {'✅' if status else '❌'}")
        print("="*60)
        
        # Code de sortie
        exit_code = 0 if result['overall_success'] else 1
        sys.exit(exit_code)
        
    except KeyboardInterrupt:
        print("\n🛑 Configuration interrompue par l'utilisateur")
        sys.exit(130)
    except Exception as e:
        logger.error(f"❌ Erreur fatale: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()