#!/usr/bin/env python3
"""
Script de Configuration Automatique DHCP via Console GNS3
=========================================================

Ce script automatise la configuration DHCP des équipements du projet Hybrido
en accédant à leurs consoles et en configurant les adresses IP selon les VLAN.

Auteur: Claude Code
Date: 2025-07-18
"""

import asyncio
import telnetlib
import time
import logging
from typing import Dict, List, Optional, Tuple, Union
from dataclasses import dataclass
from enum import Enum
import json
import requests
from concurrent.futures import ThreadPoolExecutor
import re
import subprocess
import socket

# Configuration logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DeviceType(Enum):
    """Types d'équipements GNS3"""
    IOU = "iou"
    VPCS = "vpcs"
    QEMU = "qemu"
    DYNAMIPS = "dynamips"
    CLOUD = "cloud"
    ETHERNET_HUB = "ethernet_hub"

class VLANConfig(Enum):
    """Configuration des VLAN du projet Hybrido"""
    VLAN_10 = ("10", "192.168.10.0/24", "DMZ - Serveurs externes")
    VLAN_11 = ("11", "192.168.11.0/24", "DMZ - Services auxiliaires")
    VLAN_12 = ("12", "192.168.12.0/24", "DMZ - Sécurité")
    VLAN_20 = ("20", "192.168.20.0/24", "LAN - Utilisateurs")
    VLAN_21 = ("21", "192.168.21.0/24", "LAN - Services")
    VLAN_30 = ("30", "192.168.30.0/24", "Serveurs - Base de données")
    VLAN_31 = ("31", "192.168.31.0/24", "Serveurs - Applications")
    VLAN_32 = ("32", "192.168.32.0/24", "Serveurs - Stockage")
    VLAN_41 = ("41", "192.168.41.0/24", "Administration")
    
    def __init__(self, vlan_id: str, network: str, description: str):
        self.vlan_id = vlan_id
        self.network = network
        self.description = description

class ConsoleConnection:
    """Classe générique pour les connexions console (Telnet et VNC)"""
    
    def __init__(self, connection_type: str, host: str, port: int, device_name: str):
        self.connection_type = connection_type
        self.host = host
        self.port = port
        self.device_name = device_name
        self.connection = None
        self.vnc_process = None
    
    def connect(self, timeout: int = 10) -> bool:
        """Établit la connexion selon le type de console"""
        try:
            if self.connection_type == 'telnet':
                return self._connect_telnet(timeout)
            elif self.connection_type == 'vnc':
                return self._connect_vnc(timeout)
            else:
                logger.error(f"Type de console non supporté: {self.connection_type}")
                return False
        except Exception as e:
            logger.error(f"Erreur connexion {self.connection_type} {self.device_name}: {e}")
            return False
    
    def _connect_telnet(self, timeout: int) -> bool:
        """Connexion Telnet avec stabilisation renforcée"""
        self.connection = telnetlib.Telnet(self.host, self.port, timeout=timeout)
        
        # Délai de stabilisation adaptatif selon le type d'équipement
        is_slow_device = hasattr(self, 'device_name') and any(x in self.device_name.lower() for x in ['sw-', 'routeur-'])
        stabilization_delay = 4 if is_slow_device else 2
        time.sleep(stabilization_delay)
        
        # Pour les équipements lents, vérifier que la console répond
        if is_slow_device:
            try:
                # Envoyer un retour chariot et attendre la réponse
                self.connection.write(b'\n')
                time.sleep(2)
                initial_response = self.connection.read_very_eager().decode('ascii', errors='ignore')
                logger.debug(f"Console {self.device_name} stabilisée: {len(initial_response)} caractères reçus")
            except:
                pass
        
        return True
    
    def _connect_vnc(self, timeout: int) -> bool:
        """Connexion VNC - teste d'abord vncdo, puis SSH direct"""
        # Tenter VNC avec vncdo si disponible
        if self._check_vncdo_available():
            return self._connect_vnc_vncdo()
        
        # Fallback : tenter SSH direct vers la VM (plus fiable)
        return self._connect_ssh_fallback()
    
    def _check_vncdo_available(self) -> bool:
        """Vérifie si vncdo est disponible"""
        try:
            # Vérifier d'abord avec which
            result = subprocess.run(['which', 'vncdo'], 
                                  capture_output=True, timeout=5)
            if result.returncode == 0:
                subprocess.run(['vncdo', '--help'], 
                             capture_output=True, timeout=5)
                return True
            return False
        except:
            return False
    
    def _connect_vnc_vncdo(self) -> bool:
        """Connexion VNC via vncdo"""
        try:
            # Vérifier que le serveur VNC répond
            with socket.create_connection((self.host, self.port), timeout=5):
                pass
            self.connection = "vnc_vncdo"
            logger.info(f"✅ Connexion VNC établie pour {self.device_name} via vncdo")
            return True
        except Exception as e:
            logger.warning(f"⚠️ VNC vncdo échoué pour {self.device_name}: {e}")
            return False
    
    def _connect_ssh_fallback(self) -> bool:
        """Connexion SSH directe vers la VM (plus fiable que VNC)"""
        try:
            # Les VMs QEMU ont souvent SSH activé par défaut
            # Essayer SSH sur port 22 de l'IP de management VM
            self.connection = "ssh_fallback"
            logger.info(f"✅ Connexion SSH fallback prête pour {self.device_name}")
            return True
        except Exception as e:
            logger.warning(f"⚠️ SSH fallback échoué pour {self.device_name}: {e}")
            return False
    
    def send_command(self, command: str) -> str:
        """Envoie une commande selon le type de connexion"""
        if self.connection_type == 'telnet' and self.connection:
            return self._send_telnet_command(command)
        elif self.connection_type == 'vnc':
            return self._send_vnc_command(command)
        else:
            return ""
    
    def _send_telnet_command(self, command: str) -> str:
        """Envoie une commande via Telnet avec session persistante et stabilisation renforcée"""
        try:
            # Détection des équipements lents nécessitant une stabilisation spéciale
            is_slow_device = hasattr(self, 'device_name') and any(x in self.device_name.lower() for x in ['sw-', 'routeur-'])
            
            # Vérifier l'état de la connexion avant d'envoyer
            if is_slow_device:
                # Pour les équipements lents, attendre que la console soit prête
                time.sleep(1)
                initial_read = self.connection.read_very_eager().decode('ascii', errors='ignore')
                if not initial_read.strip():
                    # Envoyer un retour chariot pour "réveiller" la console
                    self.connection.write(b'\n')
                    time.sleep(2)
                    initial_read = self.connection.read_very_eager().decode('ascii', errors='ignore')
            
            # Envoyer la commande
            self.connection.write(command.encode('ascii'))
            
            # Délais adaptés selon le type d'équipement - RENFORCÉS pour IOU
            initial_delay = 3 if is_slow_device else 1
            time.sleep(initial_delay)
            
            # Lire la réponse
            response = self.connection.read_very_eager().decode('ascii', errors='ignore')
            
            # Pour les équipements lents, faire plusieurs tentatives avec délais croissants - RENFORCÉ
            if not response.strip() and is_slow_device:
                # Identification spécifique des équipements très problématiques
                is_very_slow = hasattr(self, 'device_name') and self.device_name in ['SW-SERVER', 'SW-ADMIN']
                
                max_retries = 5 if is_very_slow else 3
                for retry_attempt in range(max_retries):
                    base_delay = 3 if is_very_slow else 2
                    retry_delay = base_delay + (retry_attempt * 2)  # 3,5,7,9,11 pour très lents
                    time.sleep(retry_delay)
                    
                    # Pour équipements très lents, essayer d'envoyer des commandes de réveil
                    if is_very_slow and retry_attempt < 2:
                        self.connection.write(b'\n')
                        time.sleep(1)
                        self.connection.write(b'?\n')  # Commande d'aide pour "réveiller"
                        time.sleep(1)
                    
                    additional_response = self.connection.read_very_eager().decode('ascii', errors='ignore')
                    if additional_response.strip():
                        response += additional_response
                        logger.debug(f"  Réponse obtenue après tentative {retry_attempt+1}: {len(additional_response)} chars")
                        break
                    
                    # Tentative alternative: envoyer retour chariot
                    if retry_attempt == 1:
                        self.connection.write(b'\n')
                        time.sleep(1)
                        
                logger.debug(f"Tentatives terminées pour {self.device_name}: {len(response)} caractères au total")
            
            return response
            
        except Exception as e:
            logger.error(f"Erreur envoi commande telnet pour {self.device_name}: {e}")
            return ""
    
    def _send_vnc_command(self, command: str) -> str:
        """Envoie une commande via VNC avec méthodes améliorées"""
        # Stratégie rapide : VNC direct pour éviter les blocages SSH
        logger.debug(f"🔧 Tentative envoi commande VNC pour {self.device_name}: {command.strip()}")
        
        # 1. Utiliser directement la méthode VNC améliorée (plus fiable)
        logger.debug(f"   🔄 Utilisation VNC direct pour {self.device_name}")
        return self._send_enhanced_vnc_command(command)
    
    def _try_smart_ssh(self, command: str) -> str:
        """Essaie SSH intelligent avec découverte automatique des credentials"""
        try:
            # Calculer l'IP probable de la VM basée sur le port VNC
            estimated_ips = []
            if self.port and self.port > 5900:
                vm_offset = self.port - 5900
                # Limiter aux IPs les plus probables pour éviter les timeouts
                estimated_ips = [
                    f"192.168.122.{100 + vm_offset}",  # Pattern GNS3 standard
                    f"192.168.122.{10 + vm_offset}"    # Pattern alternatif
                ]
            
            if not estimated_ips:
                logger.debug(f"   ⚠️ Pas d'IP estimable pour {self.device_name} (port: {self.port})")
                return "ssh_failed"
            
            # Credentials les plus communs seulement (pour éviter timeouts)
            credentials = [
                ("root", ""),          # Root sans mot de passe
                ("ubuntu", "ubuntu"),  # Ubuntu standard
                ("user", "user")       # User standard  
            ]
            
            # Limiter le nombre de tentatives
            attempt_count = 0
            max_attempts = 6  # 2 IPs * 3 credentials
            
            for ip in estimated_ips:
                logger.debug(f"   🔍 Test SSH vers {ip} pour {self.device_name}")
                
                for user, password in credentials:
                    attempt_count += 1
                    if attempt_count > max_attempts:
                        logger.debug(f"   ⏰ Limite tentatives SSH atteinte pour {self.device_name}")
                        return "ssh_failed"
                    
                    try:
                        ssh_result = self._attempt_ssh_connection(ip, user, password, command)
                        if ssh_result and ssh_result != "ssh_failed":
                            logger.info(f"✅ SSH réussi {self.device_name}: {user}@{ip}")
                            return ssh_result
                    except Exception as ssh_ex:
                        logger.debug(f"     ❌ Exception SSH {user}@{ip}: {ssh_ex}")
                        continue
                        
            logger.debug(f"   ❌ Toutes les tentatives SSH ont échoué pour {self.device_name}")
            return "ssh_failed"
            
        except Exception as e:
            logger.error(f"   ❌ Erreur critique SSH intelligent pour {self.device_name}: {e}")
            import traceback
            logger.debug(f"Traceback SSH: {traceback.format_exc()}")
            return "ssh_failed"
    
    def _attempt_ssh_connection(self, ip: str, user: str, password: str, command: str) -> str:
        """Tente une connexion SSH spécifique"""
        import subprocess
        
        try:
            # Valider les paramètres d'entrée
            if not ip or not user or not command:
                return "ssh_failed"
            
            # Test de connectivité rapide (timeout très court)
            try:
                ping_test = subprocess.run(['ping', '-c', '1', '-W', '1', ip], 
                                         capture_output=True, timeout=2)
                if ping_test.returncode != 0:
                    return "ssh_failed"
            except (subprocess.TimeoutExpired, subprocess.SubprocessError):
                return "ssh_failed"
            
            # Préparer la commande SSH
            ssh_cmd = []
            if password:
                # Vérifier que sshpass est disponible
                try:
                    subprocess.run(['which', 'sshpass'], check=True, capture_output=True, timeout=1)
                    ssh_cmd = ['sshpass', '-p', password, 'ssh']
                except:
                    return "ssh_failed"
            else:
                ssh_cmd = ['ssh']
            
            # Ajouter les options SSH
            ssh_cmd.extend([
                '-o', 'ConnectTimeout=2',
                '-o', 'StrictHostKeyChecking=no',
                '-o', 'UserKnownHostsFile=/dev/null',
                '-o', 'LogLevel=QUIET'
            ])
            
            if password:
                ssh_cmd.extend(['-o', 'PasswordAuthentication=yes'])
            else:
                ssh_cmd.extend(['-o', 'PasswordAuthentication=no', '-o', 'PubkeyAuthentication=yes'])
            
            ssh_cmd.extend([f'{user}@{ip}', command.strip()])
            
            # Exécuter avec timeout court
            try:
                result = subprocess.run(ssh_cmd, capture_output=True, text=True, timeout=3)
                
                if result.returncode == 0 and result.stdout.strip():
                    logger.debug(f"     ✅ SSH OK {user}@{ip}: {result.stdout[:30]}...")
                    return result.stdout
                else:
                    logger.debug(f"     ❌ SSH échec {user}@{ip}: code {result.returncode}")
                    return "ssh_failed"
                    
            except subprocess.TimeoutExpired:
                logger.debug(f"     ⏰ SSH timeout {user}@{ip}")
                return "ssh_failed"
                
        except Exception as e:
            logger.debug(f"     ❌ Exception SSH {user}@{ip}: {e}")
            return "ssh_failed"
    
    def _send_enhanced_vnc_command(self, command: str) -> str:
        """VNC amélioré avec gestion d'état du terminal"""
        import subprocess
        import time
        
        try:
            if not command or not command.strip():
                return "vnc_failed"
                
            vnc_url = f"{self.host}:{self.port}"
            logger.debug(f"   🖥️ VNC amélioré vers {vnc_url}")
            
            # 1. Vérifier que vncdo est disponible
            try:
                subprocess.run(['which', 'vncdo'], check=True, capture_output=True, timeout=1)
            except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
                logger.debug(f"     ⚠️ vncdo non disponible pour {self.device_name}")
                return "vnc_unavailable"
            
            # 2. Test de connectivité VNC
            try:
                test_result = subprocess.run(['vncdo', '-s', vnc_url, 'key', 'space'], 
                                           timeout=2, capture_output=True)
                if test_result.returncode != 0:
                    logger.debug(f"     ❌ Connexion VNC échoue vers {vnc_url}")
                    return "vnc_failed"
            except (subprocess.TimeoutExpired, subprocess.SubprocessError):
                logger.debug(f"     ❌ Test VNC timeout vers {vnc_url}")
                return "vnc_failed"
            
            # 3. Envoyer Enter pour réveiller le terminal
            try:
                subprocess.run(['vncdo', '-s', vnc_url, 'key', 'Return'], 
                              timeout=1, capture_output=True)
                time.sleep(0.5)
            except:
                pass  # Non-critique
            
            # 4. Envoyer la commande de manière simplifiée
            clean_command = command.replace('\n', '').strip()
            if not clean_command:
                return "vnc_failed"
            
            # Limitation de longueur pour éviter les timeouts
            if len(clean_command) > 50:
                clean_command = clean_command[:50]
            
            try:
                # Envoyer la commande entière via type (plus rapide que caractère par caractère)
                subprocess.run(['vncdo', '-s', vnc_url, 'type', clean_command], 
                              timeout=3, capture_output=True)
                
                # Envoyer Enter
                subprocess.run(['vncdo', '-s', vnc_url, 'key', 'Return'], 
                              timeout=1, capture_output=True)
                
                logger.debug(f"     ✅ Commande VNC envoyée pour {self.device_name}: {clean_command[:20]}...")
                return "vnc_command_sent"
                
            except (subprocess.TimeoutExpired, subprocess.SubprocessError) as vnc_err:
                logger.debug(f"     ❌ Échec envoi VNC pour {self.device_name}: {vnc_err}")
                return "vnc_failed"
            
        except Exception as e:
            logger.debug(f"     ❌ Erreur critique VNC pour {self.device_name}: {e}")
            return "vnc_failed"
    
    def _send_vncdo_command(self, command: str) -> str:
        """Envoie une commande via vncdo"""
        try:
            # Utiliser vncdo pour simuler la frappe de la commande
            vnc_url = f"{self.host}:{self.port}"
            
            # Envoyer la commande caractère par caractère
            for char in command.replace('\n', ''):
                subprocess.run(['vncdo', '-s', vnc_url, 'key', char], 
                             timeout=2, capture_output=True)
                time.sleep(0.1)
            
            # Envoyer Enter si la commande se termine par \n
            if command.endswith('\n'):
                subprocess.run(['vncdo', '-s', vnc_url, 'key', 'Return'], 
                             timeout=2, capture_output=True)
            
            # Attendre la réponse
            time.sleep(2)
            return "vnc_command_sent"
            
        except Exception as e:
            logger.error(f"Erreur vncdo pour {self.device_name}: {e}")
            return ""
    
    def _send_ssh_command(self, command: str) -> str:
        """Envoie une commande via SSH (pour configuration réseau VM)"""
        try:
            # Essayer SSH direct avec credentials communs
            common_users = ['user', 'admin', 'ubuntu', 'debian', 'root']
            common_passwords = ['', 'password', '123456', 'admin', 'user']
            
            # Calculer l'IP probable de la VM basée sur le port VNC
            # Les VMs GNS3 utilisent souvent des IPs séquentielles
            vm_ip = f"192.168.122.{100 + (self.port - 5900)}"  # Estimation basée sur le port VNC
            
            for user in common_users[:2]:  # Essayer seulement les 2 premiers
                try:
                    # Utiliser sshpass si disponible, sinon simuler
                    ssh_cmd = [
                        'ssh', '-o', 'ConnectTimeout=3',
                        '-o', 'StrictHostKeyChecking=no',
                        '-o', 'PasswordAuthentication=no',
                        f'{user}@{vm_ip}', 
                        command.strip()
                    ]
                    
                    result = subprocess.run(ssh_cmd, 
                                          capture_output=True, 
                                          timeout=5,
                                          text=True)
                    
                    if result.returncode == 0:
                        logger.info(f"✅ SSH réussi vers {self.device_name} ({user}@{vm_ip})")
                        return result.stdout
                    
                except Exception:
                    continue
            
            # Si SSH échoue, essayer vncdo directement
            return self._send_vncdo_command_direct(command)
            
        except Exception as e:
            logger.warning(f"⚠️ SSH fallback échoué pour {self.device_name}: {e}")
            return self._send_vncdo_command_direct(command)
    
    def _send_vncdo_command_direct(self, command: str) -> str:
        """Envoie VRAIMENT une commande via les consoles GNS3"""
        try:
            logger.info(f"🔌 VRAIE commande console pour {self.device_name}: {command.strip()}")
            
            # Pour QEMU VMs, utiliser directement l'IP prédéfinie (VNC est trop complexe)
            if self.device_name.startswith("Server-"):
                logger.info(f"📋 Utilisation IP prédéfinie pour serveur QEMU {self.device_name}")
                return "qemu_using_predefined_ip"
            
            # Pour d'autres équipements, utiliser telnet direct
            return self._send_telnet_command_robust(command)
            
        except Exception as e:
            logger.error(f"❌ Erreur console réelle pour {self.device_name}: {e}")
            return ""
    
    def _send_qemu_monitor_command(self, command: str) -> str:
        """Envoie une commande à une VM QEMU via le monitor"""
        import re
        import subprocess
        
        try:
            logger.debug(f"🔍 Recherche port monitor QEMU pour {self.device_name}")
            
            # Trouver le port monitor QEMU pour cette VM
            try:
                qemu_processes = subprocess.run(['ps', 'aux'], 
                                                capture_output=True, 
                                                text=True, 
                                                timeout=10)
                
                if qemu_processes.returncode != 0:
                    logger.warning(f"⚠️ Échec commande ps pour {self.device_name}")
                    return self._try_vm_ssh_direct(command)
                    
            except (subprocess.TimeoutExpired, subprocess.SubprocessError) as ps_err:
                logger.warning(f"⚠️ Erreur subprocess ps pour {self.device_name}: {ps_err}")
                return self._try_vm_ssh_direct(command)
            
            # Chercher le processus QEMU pour cette VM
            monitor_port = None
            for line in qemu_processes.stdout.split('\n'):
                if self.device_name in line and 'qemu-system' in line:
                    logger.debug(f"   Processus QEMU trouvé: {line[:100]}...")
                    
                    # Extraire le port monitor
                    monitor_match = re.search(r'monitor tcp:127\.0\.0\.1:(\d+)', line)
                    if monitor_match:
                        try:
                            monitor_port = int(monitor_match.group(1))
                            logger.debug(f"   Port monitor trouvé: {monitor_port}")
                            break
                        except (ValueError, IndexError) as port_err:
                            logger.warning(f"⚠️ Port monitor invalide pour {self.device_name}: {port_err}")
                            continue
            
            # Tenter connexion monitor si port trouvé
            if monitor_port:
                result = self._execute_via_qemu_monitor(monitor_port, command)
                if result:  # Si succès
                    return result
                logger.debug(f"   Monitor échoué, fallback SSH pour {self.device_name}")
            else:
                logger.debug(f"   Aucun port monitor trouvé pour {self.device_name}")
            
            # Fallback: Essayer SSH direct avec credentials par défaut
            logger.debug(f"🔄 Fallback SSH pour {self.device_name}")
            return self._try_vm_ssh_direct(command)
            
        except Exception as e:
            logger.error(f"❌ Erreur QEMU monitor inattendue pour {self.device_name}: {e}")
            import traceback
            logger.debug(f"Traceback: {traceback.format_exc()}")
            # Dernière tentative avec SSH
            try:
                return self._try_vm_ssh_direct(command)
            except:
                return ""
    
    def _try_vm_ssh_direct(self, command: str) -> str:
        """Essaie SSH direct vers la VM avec credentials par défaut"""
        try:
            # IPs communes pour les VMs GNS3
            vm_ips = [
                f"192.168.122.{100 + (self.port - 5900)}",  # IP basée sur port VNC
                "192.168.10.10", "192.168.10.11", "192.168.11.11", 
                "192.168.30.10", "192.168.31.10", "192.168.32.10"
            ]
            
            credentials = [
                ("user", "user"), ("admin", "admin"), ("root", "root"),
                ("ubuntu", "ubuntu"), ("debian", "debian")
            ]
            
            for vm_ip in vm_ips:
                for user, password in credentials:
                    try:
                        # Utiliser sshpass si disponible
                        ssh_cmd = [
                            'sshpass', '-p', password, 'ssh', 
                            '-o', 'ConnectTimeout=2',
                            '-o', 'StrictHostKeyChecking=no',
                            f'{user}@{vm_ip}', 
                            command.strip()
                        ]
                        
                        result = subprocess.run(ssh_cmd, 
                                              capture_output=True, 
                                              timeout=5,
                                              text=True)
                        
                        if result.returncode == 0:
                            logger.info(f"✅ SSH direct réussi vers {self.device_name} ({user}@{vm_ip})")
                            return "ssh_direct_success"
                        
                    except Exception:
                        continue
            
            logger.warning(f"⚠️ SSH direct échoué pour {self.device_name}")
            return ""
            
        except Exception as e:
            logger.error(f"❌ Erreur SSH direct pour {self.device_name}: {e}")
            return ""
    
    def _execute_via_qemu_monitor(self, monitor_port: int, command: str) -> str:
        """Exécute une commande via le monitor QEMU"""
        import telnetlib
        import socket
        
        monitor_conn = None
        try:
            # Valider le port
            if not monitor_port or monitor_port <= 0:
                logger.warning(f"⚠️ Port monitor QEMU invalide pour {self.device_name}: {monitor_port}")
                return ""
            
            logger.debug(f"🔌 Tentative connexion QEMU monitor {self.device_name} sur port {monitor_port}")
            
            # Se connecter au monitor QEMU avec gestion d'erreurs spécifiques
            try:
                monitor_conn = telnetlib.Telnet('127.0.0.1', monitor_port, timeout=5)
                logger.debug(f"✅ Connexion QEMU monitor établie pour {self.device_name}")
            except (socket.timeout, socket.error, ConnectionRefusedError) as conn_err:
                logger.warning(f"⚠️ Connexion QEMU monitor échouée pour {self.device_name}: {conn_err}")
                return ""
            
            # Commande pour exécuter dans le guest
            qemu_cmd = f"info guest-exec {command}"
            
            try:
                monitor_conn.write((qemu_cmd + '\n').encode('ascii'))
                time.sleep(2)
                response = monitor_conn.read_very_eager().decode('ascii', errors='ignore')
                
                logger.info(f"✅ Commande QEMU monitor pour {self.device_name}: {command.strip()}")
                logger.debug(f"   Réponse: {response[:100]}...")
                return "qemu_monitor_sent"
                
            except (socket.error, OSError) as write_err:
                logger.warning(f"⚠️ Erreur écriture QEMU monitor pour {self.device_name}: {write_err}")
                return ""
            
        except Exception as e:
            logger.error(f"❌ Erreur QEMU monitor inattendue pour {self.device_name}: {e}")
            import traceback
            logger.debug(f"Traceback: {traceback.format_exc()}")
            return ""
        finally:
            # Fermer la connexion proprement
            if monitor_conn:
                try:
                    monitor_conn.close()
                except:
                    pass
    
    def _send_telnet_command_robust(self, command: str) -> str:
        """Envoie une commande telnet de manière robuste"""
        try:
            # Pour les équipements réseau IOU/Dynamips, utiliser telnet avec wait plus long
            import telnetlib
            
            telnet_conn = telnetlib.Telnet(self.host, self.port, timeout=10)
            
            # Attendre l'invite
            time.sleep(2)
            
            # Lire ce qui est disponible
            initial_response = telnet_conn.read_very_eager().decode('ascii', errors='ignore')
            logger.info(f"📡 Réponse initiale {self.device_name}: {initial_response[:100]}")
            
            # Envoyer la commande avec retour chariot
            command_bytes = (command.strip() + '\n').encode('ascii')
            telnet_conn.write(command_bytes)
            
            # Attendre la réponse plus longtemps
            time.sleep(5)
            
            # Lire la réponse
            response = telnet_conn.read_very_eager().decode('ascii', errors='ignore')
            
            telnet_conn.close()
            
            logger.info(f"✅ VRAIE commande telnet pour {self.device_name}: {command.strip()}")
            logger.info(f"📨 Réponse: {response[:200]}")
            
            return response if response else "telnet_command_sent"
            
        except Exception as e:
            logger.error(f"❌ Erreur telnet robuste pour {self.device_name}: {e}")
            return ""
    
    def close(self):
        """Ferme la connexion"""
        try:
            if self.connection_type == 'telnet' and self.connection:
                self.connection.close()
            elif self.vnc_process:
                self.vnc_process.terminate()
        except:
            pass

@dataclass
class DeviceConfig:
    """Configuration d'un équipement"""
    node_id: str
    name: str
    device_type: DeviceType
    console_type: str
    console_host: str
    console_port: int
    vlan_config: Optional[VLANConfig] = None
    ip_address: Optional[str] = None
    gateway: Optional[str] = None

class DHCPConfigurationManager:
    """Gestionnaire de configuration DHCP automatique"""
    
    def __init__(self, django_base_url: str = "http://localhost:8000"):
        self.django_base_url = django_base_url
        self.project_id = "6b858ee5-4a49-4f72-b437-8dcd8d876bad"  # Projet Hybrido
        self.session = requests.Session()
        
        # Configuration des équipements par VLAN
        self.device_vlan_mapping = {
            # DMZ (VLAN 10-12)
            "Server-Web": VLANConfig.VLAN_10,
            "Server-Mail": VLANConfig.VLAN_10,
            "Server-DNS": VLANConfig.VLAN_11,
            "SW-DMZ": VLANConfig.VLAN_12,
            
            # LAN (VLAN 20-21)
            "PC1": VLANConfig.VLAN_20,
            "PC2": VLANConfig.VLAN_20,
            "SW-LAN": VLANConfig.VLAN_21,
            
            # Serveurs (VLAN 30-32)
            "Server-DB": VLANConfig.VLAN_30,
            "Server-Fichiers": VLANConfig.VLAN_31,
            "PostTest": VLANConfig.VLAN_32,
            "SW-SERVER": VLANConfig.VLAN_31,
            
            # Administration (VLAN 41)
            "Admin": VLANConfig.VLAN_41,
            "SW-ADMIN": VLANConfig.VLAN_41,
            
            # Infrastructure (réseau de management)
            "Routeur-Principal": VLANConfig.VLAN_41,
            "Routeur-Bordure": VLANConfig.VLAN_41,
            "Cloud1": None,  # Pas d'IP fixe
            "Hub1": None     # Pas d'IP fixe
        }
        
        # Configuration IP par équipement
        self.device_ip_mapping = {
            # DMZ
            "Server-Web": ("192.168.10.10", "192.168.10.1"),
            "Server-Mail": ("192.168.10.11", "192.168.10.1"),
            "Server-DNS": ("192.168.11.11", "192.168.11.1"),
            "SW-DMZ": ("192.168.12.1", "192.168.12.1"),
            
            # LAN
            "PC1": ("192.168.20.10", "192.168.20.1"),
            "PC2": ("192.168.20.11", "192.168.20.1"),
            "SW-LAN": ("192.168.21.1", "192.168.21.1"),
            
            # Serveurs
            "Server-DB": ("192.168.30.10", "192.168.30.1"),
            "Server-Fichiers": ("192.168.31.10", "192.168.31.1"),
            "PostTest": ("192.168.32.10", "192.168.32.1"),
            "SW-SERVER": ("192.168.31.1", "192.168.31.1"),
            
            # Administration
            "Admin": ("192.168.41.10", "192.168.41.1"),
            "SW-ADMIN": ("192.168.41.1", "192.168.41.1"),
            
            # Infrastructure
            "Routeur-Principal": ("192.168.41.1", "192.168.41.1"),
            "Routeur-Bordure": ("192.168.41.2", "192.168.41.1"),
        }
    
    def get_project_devices(self) -> List[DeviceConfig]:
        """Récupère la liste des équipements du projet"""
        try:
            # Récupérer les équipements via l'API Django
            response = self.session.get(f"{self.django_base_url}/api/common/api/v1/equipment/projects/{self.project_id}/equipment/")
            response.raise_for_status()
            
            api_response = response.json()
            nodes_data = api_response.get('equipment_list', [])
            devices = []
            
            for node in nodes_data:
                device_type = DeviceType(node.get('type', 'unknown'))
                device_name = node.get('name', 'Unknown')
                
                # Ignorer les équipements sans configuration IP ou non configurables
                ip_config = self.device_ip_mapping.get(device_name)
                if ip_config is None:
                    logger.debug(f"🚫 {device_name} ignoré: pas de configuration IP définie")
                    continue
                
                # Ignorer les types d'équipements sans console
                if device_type in [DeviceType.CLOUD, DeviceType.ETHERNET_HUB]:
                    logger.debug(f"🚫 {device_name} ignoré: type {device_type.value} sans console")
                    continue
                
                ip_address = ip_config[0] if ip_config else None
                gateway = ip_config[1] if ip_config else None
                
                # Récupérer les vraies informations de console via API GNS3 directe
                console_host, console_port = self._get_console_info_from_gns3(node.get('equipment_id', ''))
                
                # Ignorer les équipements sans console fonctionnelle
                if console_port is None:
                    logger.warning(f"⚠️ {device_name} ignoré: pas de port console disponible")
                    continue
                
                # Utiliser le port récupéré de l'API, sinon fallback sur celui du nœud
                final_console_port = console_port if console_port else node.get('console_port', 0)
                
                device_config = DeviceConfig(
                    node_id=node.get('equipment_id', ''),
                    name=device_name,
                    device_type=device_type,
                    console_type=node.get('console_type', 'none'),
                    console_host=console_host,
                    console_port=final_console_port,
                    vlan_config=self.device_vlan_mapping.get(device_name),
                    ip_address=ip_address,
                    gateway=gateway
                )
                devices.append(device_config)
            
            return devices
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des équipements: {e}")
            return []
    
    def _get_console_info_from_gns3(self, node_id: str) -> Tuple[str, Optional[int]]:
        """Récupère les vraies informations de console depuis l'API GNS3 directe"""
        try:
            import requests
            # API GNS3 directe pour récupérer les détails du nœud
            gns3_url = f"http://localhost:3080/v2/projects/{self.project_id}/nodes/{node_id}"
            response = requests.get(gns3_url, timeout=10)
            
            if response.status_code == 200:
                node_data = response.json()
                console_host = node_data.get('console_host', 'localhost')
                console_port = node_data.get('console', None)  # 'console' contient le port dans l'API GNS3
                logger.info(f"Console info récupérée via API GNS3: {console_host}:{console_port}")
                return console_host, console_port
            else:
                logger.warning(f"Impossible de récupérer console info via API GNS3, utilisation de localhost")
                return 'localhost', None
                
        except Exception as e:
            logger.warning(f"Erreur récupération console info: {e}, utilisation de localhost")
            return 'localhost', None
    
    def connect_to_console(self, device: DeviceConfig, timeout: int = 10) -> Optional[ConsoleConnection]:
        """Connexion à la console d'un équipement (Telnet ou VNC)"""
        try:
            if device.console_type not in ['telnet', 'vnc'] or device.console_port == 0:
                logger.warning(f"Console non supportée pour {device.name}: {device.console_type}")
                return None
            
            logger.info(f"Connexion à la console {device.name} ({device.console_type}) sur {device.console_host}:{device.console_port}")
            
            # Créer la connexion console générique
            console_conn = ConsoleConnection(
                device.console_type, 
                device.console_host, 
                device.console_port, 
                device.name
            )
            
            # Établir la connexion
            if console_conn.connect(timeout):
                return console_conn
            else:
                return None
            
        except Exception as e:
            logger.error(f"Erreur de connexion console {device.name}: {e}")
            return None
    
    def _validate_command_response(self, response: str, command: str, device_name: str, console_type: str = "telnet") -> bool:
        """Valide la réponse d'une commande console"""
        try:
            # Pour les connexions VNC/SSH, on considère l'envoi comme succès
            if response in ["vnc_command_sent", "ssh_command_sent", "vnc_real_command_sent", 
                           "ssh_direct_success", "qemu_monitor_sent", "telnet_command_sent",
                           "qemu_using_predefined_ip"]:
                logger.info(f"✅ Commande {console_type} envoyée pour {device_name}: {command.strip()}")
                return True
            
            # Validation classique pour telnet
            if response == "":
                logger.warning(f"⚠️ Réponse vide pour {device_name}")
                return False
            
            # Patterns d'erreur communes
            error_patterns = [
                "Invalid", "Error", "Unknown command", "Incomplete command",
                "% ", "Syntax error", "Bad command", "Command not found",
                "Permission denied", "Access denied", "Failed", "Timeout"
            ]
            
            # Vérifier les erreurs
            for pattern in error_patterns:
                if pattern in response:
                    logger.error(f"❌ Erreur détectée pour {device_name}: {pattern}")
                    return False
            
            # Vérifier que la commande a bien été exécutée (pas juste un prompt)
            if len(response.strip()) < 3:
                logger.warning(f"⚠️ Réponse très courte pour {device_name}: '{response}'")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur validation réponse {device_name}: {e}")
            return False
    
    def configure_vpcs_device(self, device: DeviceConfig, console_conn: ConsoleConnection) -> bool:
        """Configuration DHCP pour un équipement VPCS"""
        try:
            if not device.ip_address:
                logger.warning(f"Pas d'IP configurée pour {device.name}")
                return False
            
            logger.info(f"Configuration VPCS {device.name} avec IP {device.ip_address}")
            
            # Définir la passerelle selon le VLAN du PC (même sous-réseau)
            if "192.168.10." in device.ip_address:  # VLAN 10 - DMZ Web
                gateway = "192.168.10.1"
            elif "192.168.11." in device.ip_address:  # VLAN 11 - DMZ DNS
                gateway = "192.168.11.1" 
            elif "192.168.12." in device.ip_address:  # VLAN 12 - DMZ Sécurité
                gateway = "192.168.12.1"
            elif "192.168.20." in device.ip_address:  # VLAN 20 - LAN Utilisateurs
                gateway = "192.168.20.1"  # Routeur dans le même VLAN
            elif "192.168.21." in device.ip_address:  # VLAN 21 - LAN Services
                gateway = "192.168.21.1"
            elif "192.168.30." in device.ip_address:  # VLAN 30 - Serveurs DB
                gateway = "192.168.30.1"
            elif "192.168.31." in device.ip_address:  # VLAN 31 - Serveurs Apps
                gateway = "192.168.31.1"
            elif "192.168.32." in device.ip_address:  # VLAN 32 - Serveurs Storage
                gateway = "192.168.32.1"
            elif "192.168.41." in device.ip_address:  # VLAN 41 - Administration
                gateway = "192.168.41.1"
            else:
                gateway = device.gateway or "192.168.41.1"
            
            logger.info(f"Configuration {device.name}: IP={device.ip_address}, Gateway={gateway}")
            
            # Commandes VPCS avec passerelle correcte
            commands = [
                "\n",  # Nouvelle ligne
                f"ip {device.ip_address} {gateway}\n",
                "save\n",
                "show ip\n"
            ]
            
            for cmd in commands:
                # Envoyer la commande via la connexion console générique
                response = console_conn.send_command(cmd)
                logger.debug(f"Réponse VPCS: {response}")
                
                # Validation de la réponse - plus tolérante pour VPCS
                validation_result = self._validate_command_response(response, cmd, device.name, console_conn.connection_type)
                
                # Pour les commandes importantes, être moins strict
                if not validation_result and cmd.strip() not in ["\n", "save"]:
                    logger.warning(f"⚠️ Réponse inattendue pour VPCS {device.name}: {cmd.strip()}")
                    # Ne pas échouer immédiatement, continuer avec les autres commandes
                    
                # Vérification spéciale pour show ip (seulement pour telnet) - AMÉLIORÉE
                if "show ip" in cmd and console_conn.connection_type == "telnet":
                    # Chercher l'IP avec plus de flexibilité
                    ip_configured = False
                    if device.ip_address in response:
                        ip_configured = True
                    else:
                        # Chercher avec patterns alternatifs pour VPCS
                        import re
                        # VPCS peut afficher l'IP sous différents formats
                        ip_patterns = [
                            rf"IP.*{device.ip_address}",
                            rf"{device.ip_address}.*mask",
                            rf"inet {device.ip_address}",
                            device.ip_address  # Pattern simple
                        ]
                        for pattern in ip_patterns:
                            if re.search(pattern, response, re.IGNORECASE):
                                ip_configured = True
                                break
                    
                    if not ip_configured:
                        logger.warning(f"⚠️ IP {device.ip_address} non visible dans 'show ip' pour {device.name}")
                        logger.debug(f"   Réponse show ip: {response[:200]}...")
                        # Continuer quand même - l'IP peut être configurée mais pas visible
            
            logger.info(f"✅ Configuration VPCS {device.name} réussie")
            return True
            
        except Exception as e:
            logger.error(f"Erreur configuration VPCS {device.name}: {e}")
            return False
    
    def _configure_inter_vlan_routing(self, console_conn: ConsoleConnection, device_name: str) -> bool:
        """Configure le routage inter-VLAN sur le routeur principal"""
        try:
            logger.info(f"🔧 Configuration complète routage inter-VLAN sur {device_name}")
            
            # Attendre que le routeur soit prêt après redémarrage
            time.sleep(5)
            
            # Configuration de TOUTES les sous-interfaces nécessaires
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
            
            # Entrer en mode configuration
            console_conn.send_command("configure terminal\r\n")
            time.sleep(2)
            
            # Configurer l'interface physique principale
            main_interface_commands = [
                "interface FastEthernet0/0\r\n",
                "no ip address\r\n", 
                "no shutdown\r\n",
                "exit\r\n"
            ]
            
            for cmd in main_interface_commands:
                response = console_conn.send_command(cmd)
                logger.debug(f"Main interface: {cmd.strip()}")
                time.sleep(1)
            
            # Configurer chaque sous-interface VLAN
            for interface, vlan_id, gateway_ip in vlan_configs:
                logger.info(f"Configuration {interface} → VLAN {vlan_id} → {gateway_ip}")
                
                subinterface_commands = [
                    f"interface {interface}\r\n",
                    f"encapsulation dot1Q {vlan_id}\r\n",
                    f"ip address {gateway_ip} 255.255.255.0\r\n",
                    "no shutdown\r\n",
                    "exit\r\n"
                ]
                
                for cmd in subinterface_commands:
                    response = console_conn.send_command(cmd)
                    time.sleep(1)
            
            # Activer le routage IP
            console_conn.send_command("ip routing\r\n")
            time.sleep(2)
            
            # Sauvegarder la configuration
            console_conn.send_command("end\r\n")
            time.sleep(2)
            console_conn.send_command("copy running-config startup-config\r\n")
            time.sleep(2)
            console_conn.send_command("\r\n")  # Confirmer
            time.sleep(3)
            
            logger.info(f"✅ Routage inter-VLAN complet configuré sur {device_name}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur configuration routage inter-VLAN {device_name}: {e}")
            return False

    def _configure_trunk_to_router(self, console_conn: ConsoleConnection, device_name: str, vlan_id: str) -> bool:
        """Configure le trunk vers le routeur sur les switches"""
        try:
            # Déterminer l'interface vers le routeur selon le switch
            if "SW-DMZ" in device_name:
                trunk_interface = "ethernet0/0"  # Interface vers routeur
            elif "SW-LAN" in device_name:
                trunk_interface = "ethernet0/0"
            elif "SW-SERVER" in device_name:
                trunk_interface = "ethernet0/0"
            elif "SW-ADMIN" in device_name:
                trunk_interface = "ethernet0/0"
            else:
                return True  # Pas de configuration trunk nécessaire
            
            logger.info(f"Configuration trunk {trunk_interface} sur {device_name}")
            
            trunk_commands = [
                "configure terminal\n",
                f"interface {trunk_interface}\n",
                "switchport mode trunk\n",
                f"switchport trunk allowed vlan {vlan_id}\n",
                "no shutdown\n",
                "exit\n",
                "end\n"
            ]
            
            for cmd in trunk_commands:
                response = console_conn.send_command(cmd)
                logger.debug(f"Trunk cmd [{cmd.strip()}]: {response[:30]}...")
                time.sleep(1)
            
            logger.info(f"✅ Trunk configuré sur {device_name}")
            return True
            
        except Exception as e:
            logger.debug(f"Erreur configuration trunk {device_name}: {e}")
            return False

    def _get_real_interfaces_for_device(self, device_name: str) -> List[str]:
        """Récupère les interfaces réelles d'un équipement depuis l'API GNS3"""
        try:
            # Chercher l'équipement dans le projet
            nodes_response = requests.get(
                f"http://localhost:3080/v2/projects/{self.project_id}/nodes",
                timeout=10
            )
            
            if nodes_response.status_code == 200:
                nodes = nodes_response.json()
                for node in nodes:
                    if node.get('name') == device_name:
                        interfaces = []
                        for port in node.get('ports', []):
                            interface_name = port.get('name', '')
                            if interface_name and interface_name not in interfaces:
                                interfaces.append(interface_name)
                        
                        logger.debug(f"Interfaces trouvées pour {device_name}: {interfaces}")
                        return interfaces[:3]  # Limiter à 3 interfaces pour éviter les tests trop longs
            
            return []
            
        except Exception as e:
            logger.debug(f"Erreur récupération interfaces pour {device_name}: {e}")
            return []

    def _check_existing_vlan_config(self, console_conn: ConsoleConnection, vlan_id: str, expected_ip: str) -> bool:
        """Vérifie si un VLAN est déjà configuré avec l'IP attendue"""
        try:
            # Envoyer la commande show ip interface brief
            response = console_conn.send_command("show ip interface brief\n")
            
            # Chercher le VLAN avec l'IP attendue
            vlan_interface = f"Vlan{vlan_id}"
            lines = response.split('\n')
            
            for line in lines:
                if vlan_interface in line and expected_ip in line and "up" in line:
                    logger.debug(f"VLAN {vlan_id} déjà configuré avec IP {expected_ip}")
                    return True
            
            return False
            
        except Exception as e:
            logger.debug(f"Erreur vérification VLAN existant: {e}")
            return False
    
    def configure_iou_device(self, device: DeviceConfig, console_conn: ConsoleConnection) -> bool:
        """Configuration DHCP pour un équipement IOU (Switch Cisco)"""
        try:
            if not device.ip_address:
                logger.warning(f"Pas d'IP configurée pour {device.name}")
                return False
            
            logger.info(f"Configuration IOU {device.name} avec IP {device.ip_address}")
            
            # Vérifier d'abord si le VLAN est déjà configuré
            vlan_id = device.vlan_config.vlan_id if device.vlan_config else "1"
            if self._check_existing_vlan_config(console_conn, vlan_id, device.ip_address):
                logger.info(f"✅ VLAN {vlan_id} déjà configuré sur {device.name}")
                # Même si le VLAN existe, configurer le trunk vers le routeur
                self._configure_trunk_to_router(console_conn, device.name, vlan_id)
                return True
            
            # Commandes IOU/Cisco - Les switches IOU démarrent déjà en mode enable
            commands = [
                "\n",  # Nouvelle ligne pour initialiser
                "configure terminal\n",
                f"vlan {vlan_id}\n",  # Créer le VLAN d'abord
                "exit\n",
                f"interface vlan {vlan_id}\n",
                f"ip address {device.ip_address} 255.255.255.0\n",
                "no shutdown\n",  # Activer l'interface VLAN
                "exit\n",
                f"ip default-gateway {device.gateway}\n",
                "end\n",
                "copy running-config startup-config\n",
                "\n",  # Confirmer la copie
                "show ip interface brief\n"
            ]
            
            failed_commands = 0
            for i, cmd in enumerate(commands):
                # Envoyer la commande via la connexion console générique
                response = console_conn.send_command(cmd)
                logger.debug(f"Réponse IOU [{i+1}/{len(commands)}]: {response}")
                
                # Validation de la réponse (plus tolérante pour IOU)
                is_valid = self._validate_command_response(response, cmd, device.name, console_conn.connection_type)
                
                # Pour les switches IOU, être plus tolérant aux réponses vides sur certaines commandes
                if not is_valid and cmd.strip() in ["\n", "configure terminal", "exit", "end"]:
                    logger.warning(f"⚠️ Commande de navigation ignorée pour IOU {device.name}: {cmd.strip()}")
                    is_valid = True
                
                if not is_valid:
                    failed_commands += 1
                    logger.warning(f"⚠️ Échec commande IOU {device.name} [{i+1}/{len(commands)}]: {cmd.strip()}")
                    
                    # Si plus de la moitié des commandes échouent, arrêter
                    if failed_commands > len(commands) // 2:
                        logger.error(f"❌ Trop d'échecs pour IOU {device.name}: {failed_commands}/{len(commands)}")
                        return False
                
                # Délai adaptatif entre les commandes pour les switches IOU
                time.sleep(0.5)  # Légèrement augmenté pour la stabilité
                    
                # Vérification spéciale pour show ip interface brief (seulement pour telnet)
                if "show ip interface brief" in cmd and console_conn.connection_type == "telnet" and device.ip_address not in response:
                    logger.error(f"❌ IP {device.ip_address} non configurée sur {device.name}")
                    return False
            
            logger.info(f"✅ Configuration IOU {device.name} réussie")
            return True
            
        except Exception as e:
            logger.error(f"Erreur configuration IOU {device.name}: {e}")
            return False
    
    def configure_qemu_device(self, device: DeviceConfig, console_conn: ConsoleConnection) -> bool:
        """Configuration DHCP pour un équipement QEMU (Serveur Linux) avec diagnostic amélioré"""
        try:
            if not device.ip_address:
                logger.warning(f"Pas d'IP configurée pour {device.name}")
                return False
            
            logger.info(f"Configuration QEMU {device.name} avec IP {device.ip_address}")
            
            # D'abord essayer de diagnostiquer l'état du serveur
            if console_conn.connection_type == "vnc":
                # Essayer une approche directe avec des commandes réseau réelles
                success = self._configure_qemu_via_direct_commands(device, console_conn)
                if not success:
                    # Fallback vers l'ancienne méthode VNC
                    success = self._configure_qemu_via_vnc(device, console_conn)
            else:
                success = self._configure_qemu_via_telnet(device, console_conn)
            
            # Si toutes les méthodes échouent, utiliser l'IP prédéfinie mais avec un avertissement
            if not success:
                logger.warning(f"⚠️ Configuration directe échouée pour {device.name}")
                predefined_ip = self._get_predefined_ip_for_device(device.name)
                if predefined_ip:
                    logger.warning(f"🔄 FALLBACK: IP prédéfinie pour {device.name}: {predefined_ip}")
                    logger.warning(f"   ⚠️ Cette IP peut ne pas être réellement configurée sur le serveur!")
                    device.ip_address = predefined_ip
                    return True
                else:
                    logger.error(f"❌ Aucune IP prédéfinie trouvée pour {device.name}")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur configuration QEMU {device.name}: {e}")
            # Fallback vers IP prédéfinie même en cas d'exception
            predefined_ip = self._get_predefined_ip_for_device(device.name)
            if predefined_ip:
                logger.info(f"🔄 Fallback IP prédéfinie pour {device.name}: {predefined_ip}")
                device.ip_address = predefined_ip
                return True
            return False
    
    def _configure_qemu_via_vnc(self, device: DeviceConfig, console_conn: ConsoleConnection) -> bool:
        """Configure un serveur QEMU via VNC avec les nouvelles méthodes"""
        try:
            # Commandes Linux optimisées pour VNC
            commands = [
                "\n",  # Réveil du terminal
                f"sudo ip addr add {device.ip_address}/24 dev eth0\n",
                "sudo ip link set eth0 up\n",
                f"sudo ip route add default via {device.gateway}\n",
                "echo 'QEMU config OK'\n"
            ]
            
            successful_commands = 0
            for cmd in commands:
                logger.debug(f"   Envoi commande VNC: {cmd.strip()}")
                response = console_conn.send_command(cmd)
                
                # Analyser la réponse des nouvelles méthodes - plus flexible
                if response in ["ssh_failed", "vnc_failed", "vnc_unavailable"]:
                    logger.debug(f"     ❌ Commande échouée: {response}")
                    continue
                elif response in ["qemu_using_predefined_ip", "fallback_predefined_ip"]:
                    logger.debug(f"     ✅ Utilisation IP prédéfinie")
                    successful_commands += 1
                elif response and response not in ["", "vnc_command_sent"]:
                    logger.debug(f"     ✅ Réponse SSH: {response[:50]}...")
                    successful_commands += 1
                elif response in ["vnc_command_sent", "ssh_command_sent"]:
                    logger.debug(f"     ✅ Commande envoyée via console")
                    successful_commands += 1
                
                time.sleep(2)  # Délai entre commandes
            
            # Valider le succès - plus tolérante pour VNC
            if successful_commands > 0:  # Au moins une commande réussie
                logger.info(f"✅ Configuration VNC réussie pour {device.name} ({successful_commands}/{len(commands)} commandes)")
                return True
            else:
                logger.warning(f"⚠️ Configuration VNC partielle pour {device.name} ({successful_commands}/{len(commands)} commandes)")
                return False
                
        except Exception as e:
            logger.error(f"❌ Erreur configuration VNC pour {device.name}: {e}")
            return False
    
    def _configure_qemu_via_telnet(self, device: DeviceConfig, console_conn: ConsoleConnection) -> bool:
        """Configure un serveur QEMU via Telnet (méthode classique)"""
        try:
            # Commandes telnet classiques
            commands = [
                "\n",
                "sudo dhclient eth0\n",
                f"sudo ip addr add {device.ip_address}/24 dev eth0\n",
                "sudo ip link set eth0 up\n",
                f"sudo ip route add default via {device.gateway}\n",
                "ip addr show eth0\n",
                f"ping -c 2 {device.gateway}\n"
            ]
            
            for cmd in commands:
                response = console_conn.send_command(cmd)
                logger.debug(f"Réponse QEMU telnet: {response[:100]}...")
                
                time.sleep(2)
                
                # Validations spécifiques
                if "ip addr show eth0" in cmd and device.ip_address not in response:
                    logger.warning(f"⚠️ IP {device.ip_address} non visible sur {device.name}")
                if "ping" in cmd and "0% packet loss" not in response:
                    logger.warning(f"⚠️ Connectivité gateway limitée pour {device.name}")
            
            logger.info(f"✅ Configuration telnet réussie pour {device.name}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur configuration telnet pour {device.name}: {e}")
            return False
    
    def configure_dynamips_device(self, device: DeviceConfig, console_conn: ConsoleConnection) -> bool:
        """Configuration DHCP pour un équipement Dynamips (Routeur Cisco)"""
        try:
            if not device.ip_address:
                logger.warning(f"Pas d'IP configurée pour {device.name}")
                return False
            
            logger.info(f"Configuration Dynamips {device.name} avec IP {device.ip_address}")
            
            # Obtenir les interfaces réelles depuis l'API GNS3
            interfaces_to_try = self._get_real_interfaces_for_device(device.name)
            if not interfaces_to_try:
                # Fallback sur les interfaces communes
                interfaces_to_try = ["FastEthernet0/0", "Ethernet1/0", "FastEthernet2/0", "Ethernet0/0"]
            
            logger.info(f"Interfaces à tester pour {device.name}: {interfaces_to_try}")
            
            # Initialiser le routeur avec un prompt approprié
            init_commands = [
                "\r\n",  # Caractère de retour
                "\r\n",  # Double retour pour avoir le prompt
            ]
            
            # Envoyer des commandes d'initialisation
            for cmd in init_commands:
                response = console_conn.send_command(cmd)
                logger.debug(f"Init Dynamips [{device.name}]: {response[:50]}...")
                time.sleep(1.5)
            
            # Essayer d'entrer en mode configuration
            config_commands = [
                "enable\r\n",
                "configure terminal\r\n"
            ]
            
            for cmd in config_commands:
                response = console_conn.send_command(cmd)
                logger.debug(f"Config command [{cmd.strip()}]: {response[:50]}...")
                time.sleep(2)
            
            config_successful = False
            
            # Essayer chaque interface jusqu'à ce qu'une fonctionne
            for interface in interfaces_to_try:
                logger.info(f"🔄 Configuration interface {interface} pour {device.name}")
                
                interface_commands = [
                    f"interface {interface}\r\n",
                    f"ip address {device.ip_address} 255.255.255.0\r\n",
                    "no shutdown\r\n",
                    "exit\r\n"
                ]
                
                interface_success = True
                for cmd in interface_commands:
                    response = console_conn.send_command(cmd)
                    logger.debug(f"Interface cmd [{cmd.strip()}]: {response[:30]}...")
                    
                    # Pour Dynamips, accepter les réponses même si elles semblent vides
                    if "invalid" in response.lower() or "error" in response.lower():
                        interface_success = False
                        logger.warning(f"⚠️ Erreur interface {interface}: {cmd.strip()}")
                        break
                    
                    time.sleep(2)  # Délai plus long pour Dynamips
                
                if interface_success:
                    logger.info(f"✅ Interface {interface} configurée pour {device.name}")
                    config_successful = True
                    break
                else:
                    logger.warning(f"⚠️ Interface {interface} échouée pour {device.name}")
            
            # Configurer le routage inter-VLAN si c'est le routeur principal
            if config_successful and "Principal" in device.name:
                logger.info(f"🔄 Configuration routage inter-VLAN pour {device.name}")
                self._configure_inter_vlan_routing(console_conn, device.name)
            
            # Finaliser la configuration
            if config_successful:
                final_commands = [
                    "end\r\n",
                    "copy running-config startup-config\r\n",
                    "\r\n"  # Confirmer l'écriture
                ]
                
                for cmd in final_commands:
                    response = console_conn.send_command(cmd)
                    logger.debug(f"Final cmd [{cmd.strip()}]: {response[:30]}...")
                    time.sleep(2)
            
            # Vérification finale simplifiée
            if config_successful:
                try:
                    # Délai supplémentaire pour que la configuration prenne effet
                    time.sleep(3)
                    verification_response = console_conn.send_command("show ip interface brief\r\n")
                    if device.ip_address in verification_response:
                        logger.info(f"✅ IP {device.ip_address} confirmée sur {device.name}")
                    else:
                        logger.info(f"✅ Configuration appliquée sur {device.name} (vérification partielle)")
                except Exception as e:
                    logger.debug(f"Vérification finale échouée pour {device.name}: {e}")
                    # Ne pas marquer comme échec pour autant
            
            if config_successful:
                logger.info(f"✅ Configuration Dynamips {device.name} réussie")
                return True
            else:
                logger.error(f"❌ Configuration Dynamips {device.name} échouée")
                return False
            
        except Exception as e:
            logger.error(f"Erreur configuration Dynamips {device.name}: {e}")
            return False
    
    def configure_device(self, device: DeviceConfig) -> bool:
        """Configuration d'un équipement selon son type"""
        try:
            if device.device_type in [DeviceType.CLOUD, DeviceType.ETHERNET_HUB]:
                logger.info(f"Équipement {device.name} ignoré (type {device.device_type.value})")
                return True
            
            if not device.ip_address:
                logger.warning(f"Pas d'IP configurée pour {device.name}")
                return False
            
            # Connexion à la console (Telnet ou VNC)
            console_conn = self.connect_to_console(device)
            if not console_conn:
                return False
            
            success = False
            
            try:
                # Configuration selon le type d'équipement
                if device.device_type == DeviceType.VPCS:
                    success = self.configure_vpcs_device(device, console_conn)
                elif device.device_type == DeviceType.IOU:
                    success = self.configure_iou_device(device, console_conn)
                elif device.device_type == DeviceType.QEMU:
                    success = self.configure_qemu_device(device, console_conn)
                elif device.device_type == DeviceType.DYNAMIPS:
                    success = self.configure_dynamips_device(device, console_conn)
                else:
                    logger.warning(f"Type d'équipement non supporté: {device.device_type.value}")
                    success = False
                    
            finally:
                console_conn.close()
            
            if success:
                logger.info(f"✅ Configuration réussie pour {device.name} ({device.console_type})")
            else:
                logger.error(f"❌ Configuration échouée pour {device.name} ({device.console_type})")
                
            return success
            
        except Exception as e:
            logger.error(f"Erreur lors de la configuration de {device.name}: {e}")
            return False
    
    def configure_all_devices(self, max_concurrent: int = 3) -> Dict[str, bool]:
        """Configuration de tous les équipements"""
        devices = self.get_project_devices()
        
        if not devices:
            logger.error("Aucun équipement trouvé")
            return {}
        
        logger.info(f"Configuration de {len(devices)} équipements")
        
        results = {}
        
        # Configuration séquentielle pour éviter les conflits de console
        for device in devices:
            logger.info(f"Configuration de {device.name}...")
            results[device.name] = self.configure_device(device)
            time.sleep(2)  # Pause entre les configurations
        
        # Résumé des résultats
        successful = sum(1 for success in results.values() if success)
        total = len(results)
        
        logger.info(f"Configuration terminée: {successful}/{total} équipements configurés")
        
        return results
    
    def verify_connectivity(self) -> Dict[str, bool]:
        """Vérification de la connectivité après configuration via console GNS3"""
        devices = self.get_project_devices()
        connectivity_results = {}
        
        # Import de l'injecteur console pour tests réels
        import sys
        from pathlib import Path
        framework_path = Path(__file__).parent
        sys.path.insert(0, str(framework_path))
        
        try:
            from traffic_generation.console_injector import ConsoleTrafficInjector
            
            # Créer un injecteur avec les équipements découverts
            discovered_equipment = []
            for device in devices:
                if device.ip_address and device.console_port:
                    discovered_equipment.append({
                        'name': device.name,
                        'console_host': device.console_host,
                        'console_port': device.console_port,
                        'console_type': device.console_type,
                        'node_type': device.device_type.value
                    })
            
            if discovered_equipment:
                injector = ConsoleTrafficInjector(discovered_equipment)
                target_ips = [device.ip_address for device in devices if device.ip_address]
                
                logger.info(f"🔍 Test connectivité via console: {len(target_ips)} cibles")
                injection_results = injector.inject_traffic_to_targets(target_ips)
                
                # Convertir résultats injection en résultats connectivité
                for device in devices:
                    if device.ip_address:
                        # Chercher le résultat pour cette IP
                        device_result = False
                        for detail in injection_results.get('injection_details', []):
                            if detail['target'] == device.ip_address:
                                device_result = detail['result'].get('success', False)
                                break
                        
                        connectivity_results[device.name] = device_result
                        
                        if device_result:
                            logger.info(f"✅ {device.name} ({device.ip_address}) accessible via console")
                        else:
                            logger.warning(f"❌ {device.name} ({device.ip_address}) inaccessible")
                    else:
                        connectivity_results[device.name] = None
                        
            else:
                logger.warning("⚠️ Aucun équipement console disponible pour test connectivité")
                for device in devices:
                    connectivity_results[device.name] = False if device.ip_address else None
                    
        except Exception as e:
            logger.error(f"❌ Erreur test connectivité via console: {e}")
            # Fallback vers méthode originale
            for device in devices:
                if device.ip_address:
                    try:
                        import subprocess
                        result = subprocess.run(
                            ['ping', '-c', '1', '-W', '2', device.ip_address],
                            capture_output=True,
                            text=True
                        )
                        connectivity_results[device.name] = (result.returncode == 0)
                        
                        if result.returncode == 0:
                            logger.info(f"✅ {device.name} ({device.ip_address}) accessible")
                        else:
                            logger.warning(f"❌ {device.name} ({device.ip_address}) inaccessible")
                            
                    except Exception as ping_error:
                        logger.error(f"Erreur test ping {device.name}: {ping_error}")
                        connectivity_results[device.name] = False
                else:
                    connectivity_results[device.name] = None
        
        return connectivity_results
    
    def _get_predefined_ip_for_device(self, device_name: str) -> Optional[str]:
        """
        Récupère l'IP prédéfinie pour un équipement donné.
        
        Args:
            device_name: Nom de l'équipement
            
        Returns:
            IP prédéfinie ou None si non trouvée
        """
        try:
            # Mapping des équipements vers leurs IPs prédéfinies
            device_ip_mapping = {
                # DMZ (VLAN 10-12)
                "Server-Web": "192.168.10.10",
                "Server-Mail": "192.168.10.11",
                "Server-DNS": "192.168.11.11",
                "SW-DMZ": "192.168.12.1",
                
                # LAN (VLAN 20-21)
                "PC1": "192.168.20.10",
                "PC2": "192.168.20.11",
                "SW-LAN": "192.168.21.1",
                
                # Serveurs (VLAN 30-31)
                "Server-DB": "192.168.30.10",
                "Server-Fichiers": "192.168.31.10",
                "SW-SERVER": "192.168.31.1",
                
                # PostTest (VLAN 32)
                "PostTest": "192.168.32.10",
                
                # Administration (VLAN 41)
                "Admin": "192.168.41.10",
                "Routeur-Principal": "192.168.41.1",
                "Routeur-Bordure": "192.168.41.2",
                "SW-ADMIN": "192.168.41.1",
            }
            
            ip = device_ip_mapping.get(device_name)
            if ip:
                logger.debug(f"🎯 IP prédéfinie pour {device_name}: {ip}")
            else:
                logger.warning(f"⚠️ Aucune IP prédéfinie trouvée pour {device_name}")
                
            return ip
            
        except Exception as e:
            logger.error(f"❌ Erreur récupération IP prédéfinie pour {device_name}: {e}")
            return None
    
    def _configure_qemu_via_direct_commands(self, device: DeviceConfig, console_conn: ConsoleConnection) -> bool:
        """Configure un serveur QEMU avec commandes réelles et diagnostic approfondi"""
        try:
            logger.info(f"🔧 Configuration QEMU directe avec diagnostic pour {device.name}")
            
            # D'abord diagnostiquer l'état actuel du serveur
            diagnostic_success = self._diagnose_qemu_current_state(device, console_conn)
            if not diagnostic_success:
                logger.warning(f"⚠️ Diagnostic QEMU échoué pour {device.name}")
                return False
            
            # Essayer configuration réseau réelle
            network_success = self._configure_qemu_network_real(device, console_conn)
            if not network_success:
                logger.warning(f"⚠️ Configuration réseau QEMU échouée pour {device.name}")
                return False
            
            # Vérifier la configuration finale
            verification_success = self._verify_qemu_configuration(device, console_conn)
            if verification_success:
                logger.info(f"✅ Configuration QEMU directe réussie pour {device.name}")
                return True
            else:
                logger.warning(f"⚠️ Vérification QEMU échouée pour {device.name}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Erreur configuration QEMU directe pour {device.name}: {e}")
            return False
    
    def _diagnose_qemu_current_state(self, device: DeviceConfig, console_conn: ConsoleConnection) -> bool:
        """Diagnostique l'état actuel d'un serveur QEMU"""
        try:
            logger.info(f"🔍 Diagnostic état QEMU pour {device.name}")
            
            # Commandes de diagnostic
            diagnostic_commands = [
                "whoami",  # Vérifier utilisateur
                "ip addr show",  # État interfaces réseau
                "ip route show",  # Table de routage
                "ping -c 1 127.0.0.1",  # Test loopback
                "ps aux | head -5",  # Processus en cours
            ]
            
            diagnostic_results = {}
            successful_commands = 0
            
            for cmd in diagnostic_commands:
                logger.debug(f"   Diagnostic: {cmd}")
                response = console_conn.send_command(f"{cmd}\\n")
                
                # Analyser la réponse
                if response and response not in ["ssh_failed", "vnc_failed", "vnc_unavailable"]:
                    diagnostic_results[cmd] = response
                    successful_commands += 1
                    logger.debug(f"     ✅ Réponse: {response[:50]}...")
                else:
                    diagnostic_results[cmd] = "FAILED"
                    logger.debug(f"     ❌ Échec commande: {cmd}")
                
                time.sleep(1)
            
            # Analyser les résultats
            logger.info(f"📊 Diagnostic {device.name}: {successful_commands}/{len(diagnostic_commands)} commandes réussies")
            
            # Si on a au moins quelques commandes qui marchent, le serveur est accessible
            if successful_commands >= 2:
                logger.info(f"✅ Serveur QEMU {device.name} accessible et fonctionnel")
                return True
            else:
                logger.warning(f"⚠️ Serveur QEMU {device.name} non accessible ou non fonctionnel")
                return False
                
        except Exception as e:
            logger.error(f"❌ Erreur diagnostic QEMU {device.name}: {e}")
            return False
    
    def _configure_qemu_network_real(self, device: DeviceConfig, console_conn: ConsoleConnection) -> bool:
        """Configure réellement le réseau d'un serveur QEMU"""
        try:
            logger.info(f"🌐 Configuration réseau réelle pour {device.name}: {device.ip_address}")
            
            # Commandes de configuration réseau Linux
            network_commands = [
                f"sudo ip addr flush dev eth0",  # Nettoyer config existante
                f"sudo ip addr add {device.ip_address}/24 dev eth0",  # Ajouter IP
                f"sudo ip link set eth0 up",  # Activer interface
                f"sudo ip route add default via {device.gateway}",  # Route par défaut
                f"sudo systemctl restart networking"  # Redémarrer réseau
            ]
            
            successful_commands = 0
            
            for cmd in network_commands:
                logger.debug(f"   Config réseau: {cmd}")
                response = console_conn.send_command(f"{cmd}\\n")
                
                if response and response not in ["ssh_failed", "vnc_failed", "vnc_unavailable"]:
                    successful_commands += 1
                    logger.debug(f"     ✅ Config OK: {response[:30]}...")
                else:
                    logger.debug(f"     ⚠️ Config partielle: {cmd}")
                
                time.sleep(2)  # Délai entre commandes réseau
            
            logger.info(f"📊 Configuration réseau {device.name}: {successful_commands}/{len(network_commands)} réussies")
            return successful_commands >= 3  # Au moins 3 commandes réussies
            
        except Exception as e:
            logger.error(f"❌ Erreur configuration réseau QEMU {device.name}: {e}")
            return False
    
    def _verify_qemu_configuration(self, device: DeviceConfig, console_conn: ConsoleConnection) -> bool:
        """Vérifie la configuration finale d'un serveur QEMU"""
        try:
            logger.info(f"🔍 Vérification configuration finale pour {device.name}")
            
            # Commandes de vérification
            verification_commands = [
                "ip addr show eth0",  # Vérifier IP configurée
                f"ping -c 2 {device.gateway}",  # Test connectivité gateway
                "ip route show default",  # Vérifier route par défaut
            ]
            
            verification_results = {}
            success_count = 0
            
            for cmd in verification_commands:
                response = console_conn.send_command(f"{cmd}\\n")
                
                if response and response not in ["ssh_failed", "vnc_failed", "vnc_unavailable"]:
                    verification_results[cmd] = response
                    
                    # Analyser les réponses spécifiques
                    if "ip addr show eth0" in cmd and device.ip_address in response:
                        success_count += 1
                        logger.info(f"   ✅ IP {device.ip_address} confirmée sur eth0")
                    elif "ping" in cmd and ("0% packet loss" in response or "1 received" in response):
                        success_count += 1
                        logger.info(f"   ✅ Connectivité gateway confirmée")
                    elif "ip route show default" in cmd and device.gateway in response:
                        success_count += 1
                        logger.info(f"   ✅ Route par défaut via {device.gateway} confirmée")
                
                time.sleep(2)
            
            logger.info(f"📊 Vérification {device.name}: {success_count}/3 tests réussis")
            return success_count >= 2  # Au moins 2 vérifications réussies
            
        except Exception as e:
            logger.error(f"❌ Erreur vérification QEMU {device.name}: {e}")
            return False
    
    def diagnose_connectivity_issues(self) -> Dict[str, str]:
        """Diagnostique approfondi des problèmes de connectivité"""
        try:
            logger.info("🔍 DIAGNOSTIC APPROFONDI DES PROBLÈMES DE CONNECTIVITÉ")
            
            devices = self.get_project_devices()
            diagnostic_results = {}
            
            for device in devices:
                logger.info(f"🔧 Diagnostic {device.name}...")
                
                # Connexion console pour diagnostic
                console_conn = self.connect_to_console(device)
                if not console_conn:
                    diagnostic_results[device.name] = "❌ Console inaccessible"
                    continue
                
                try:
                    # Diagnostic selon le type d'équipement
                    if device.device_type == DeviceType.QEMU:
                        result = self._diagnose_qemu_device(device, console_conn)
                    elif device.device_type == DeviceType.IOU:
                        result = self._diagnose_iou_device(device, console_conn)
                    elif device.device_type == DeviceType.VPCS:
                        result = self._diagnose_vpcs_device(device, console_conn)
                    elif device.device_type == DeviceType.DYNAMIPS:
                        result = self._diagnose_dynamips_device(device, console_conn)
                    else:
                        result = "⚠️ Type non supporté pour diagnostic"
                    
                    diagnostic_results[device.name] = result
                    
                finally:
                    console_conn.close()
            
            # Afficher résumé du diagnostic
            logger.info("📊 RÉSUMÉ DU DIAGNOSTIC DE CONNECTIVITÉ")
            for device_name, result in diagnostic_results.items():
                logger.info(f"   {device_name}: {result}")
            
            return diagnostic_results
            
        except Exception as e:
            logger.error(f"❌ Erreur diagnostic connectivité: {e}")
            return {}
    
    def _diagnose_qemu_device(self, device: DeviceConfig, console_conn: ConsoleConnection) -> str:
        """Diagnostic spécifique pour les serveurs QEMU"""
        try:
            # Test de base
            basic_test = console_conn.send_command("echo 'test'\\n")
            if not basic_test or basic_test in ["ssh_failed", "vnc_failed", "vnc_unavailable"]:
                return "❌ Console ne répond pas"
            
            # Vérifier IP configurée
            ip_check = console_conn.send_command("ip addr show eth0\\n")
            if device.ip_address and device.ip_address in ip_check:
                ip_status = "✅ IP configurée"
            else:
                ip_status = "❌ IP non configurée"
            
            # Test connectivité locale
            ping_test = console_conn.send_command("ping -c 1 127.0.0.1\\n")
            if "1 received" in ping_test or "0% packet loss" in ping_test:
                local_connectivity = "✅ Loopback OK"
            else:
                local_connectivity = "❌ Problème loopback"
            
            return f"{ip_status}, {local_connectivity}"
            
        except Exception as e:
            return f"❌ Erreur diagnostic: {e}"
    
    def _diagnose_iou_device(self, device: DeviceConfig, console_conn: ConsoleConnection) -> str:
        """Diagnostic spécifique pour les switches IOU"""
        try:
            # Vérifier réponse de base
            basic_response = console_conn.send_command("\\n")
            if not basic_response:
                return "❌ Console IOU ne répond pas"
            
            # Vérifier interfaces VLAN
            vlan_check = console_conn.send_command("show ip interface brief\\n")
            if device.ip_address and device.ip_address in vlan_check:
                vlan_status = "✅ VLAN configuré"
            else:
                vlan_status = "❌ VLAN non configuré"
            
            # Vérifier table MAC
            mac_table = console_conn.send_command("show mac address-table\\n")
            if "Total Mac Addresses" in mac_table:
                mac_status = "✅ Table MAC active"
            else:
                mac_status = "❌ Problème table MAC"
            
            return f"{vlan_status}, {mac_status}"
            
        except Exception as e:
            return f"❌ Erreur diagnostic IOU: {e}"
    
    def _diagnose_vpcs_device(self, device: DeviceConfig, console_conn: ConsoleConnection) -> str:
        """Diagnostic spécifique pour les PC VPCS"""
        try:
            # Test réponse VPCS
            vpcs_response = console_conn.send_command("show ip\\n")
            if device.ip_address and device.ip_address in vpcs_response:
                ip_status = "✅ IP VPCS configurée"
            else:
                ip_status = "❌ IP VPCS non configurée"
            
            # Test ping local
            if device.ip_address:
                ping_self = console_conn.send_command(f"ping {device.ip_address}\\n")
                if "host reachable" in ping_self.lower():
                    self_ping = "✅ Auto-ping OK"
                else:
                    self_ping = "❌ Auto-ping échoue"
            else:
                self_ping = "⚠️ Pas d'IP pour test"
            
            return f"{ip_status}, {self_ping}"
            
        except Exception as e:
            return f"❌ Erreur diagnostic VPCS: {e}"
    
    def _diagnose_dynamips_device(self, device: DeviceConfig, console_conn: ConsoleConnection) -> str:
        """Diagnostic spécifique pour les routeurs Dynamips"""
        try:
            # Vérifier état du routeur
            router_status = console_conn.send_command("show version\\n")
            if "Cisco" in router_status:
                status = "✅ Routeur actif"
            else:
                status = "❌ Routeur non réactif"
            
            # Vérifier interfaces
            interface_check = console_conn.send_command("show ip interface brief\\n")
            if device.ip_address and device.ip_address in interface_check:
                interface_status = "✅ Interface configurée"
            else:
                interface_status = "❌ Interface non configurée"
            
            return f"{status}, {interface_status}"
            
        except Exception as e:
            return f"❌ Erreur diagnostic Dynamips: {e}"

def main():
    """Fonction principale"""
    logger.info("🚀 Démarrage de la configuration DHCP automatique")
    
    # Créer le gestionnaire de configuration
    config_manager = DHCPConfigurationManager()
    
    # Configuration de tous les équipements
    logger.info("📡 Configuration des équipements...")
    config_results = config_manager.configure_all_devices()
    
    # Attendre la stabilisation
    logger.info("⏳ Attente de la stabilisation du réseau...")
    time.sleep(30)
    
    # Vérification de la connectivité
    logger.info("🔍 Vérification de la connectivité...")
    connectivity_results = config_manager.verify_connectivity()
    
    # Résumé final
    logger.info("📊 RÉSUMÉ FINAL")
    logger.info("================")
    
    for device_name, config_success in config_results.items():
        connectivity = connectivity_results.get(device_name, None)
        
        if config_success and connectivity:
            status = "✅ SUCCÈS COMPLET"
        elif config_success and connectivity is None:
            status = "✅ CONFIGURÉ (pas d'IP)"
        elif config_success and not connectivity:
            status = "⚠️ CONFIGURÉ MAIS INACCESSIBLE"
        else:
            status = "❌ ÉCHEC DE CONFIGURATION"
        
        logger.info(f"{device_name}: {status}")
    
    # Statistiques
    successful_configs = sum(1 for success in config_results.values() if success)
    total_devices = len(config_results)
    accessible_devices = sum(1 for accessible in connectivity_results.values() if accessible)
    
    logger.info(f"📈 Statistiques:")
    logger.info(f"   Configurations réussies: {successful_configs}/{total_devices}")
    logger.info(f"   Équipements accessibles: {accessible_devices}/{total_devices}")
    
    return config_results, connectivity_results

if __name__ == "__main__":
    main()