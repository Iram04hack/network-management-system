#!/usr/bin/env python3
"""
Injecteur de Trafic via Console GNS3
====================================

Module pour injecter du trafic RÉEL en exécutant des commandes
directement depuis les consoles des équipements GNS3 configurés.

Cette approche contourne les problèmes de routage en utilisant
les équipements dans les VLANs comme sources d'attaque.
"""

import telnetlib
import time
import logging
import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class ConsoleEquipment:
    """Équipement disponible pour injection via console."""
    name: str
    ip_address: str
    console_host: str
    console_port: int
    console_type: str
    vlan: str

class ConsoleTrafficInjector:
    """Injecteur de trafic via console des équipements GNS3."""
    
    def __init__(self, discovered_equipment=None):
        # Utiliser les équipements découverts par Django ou fallback
        if discovered_equipment:
            logger.info(f"🔌 Utilisation de {len(discovered_equipment)} équipements découverts par Django")
            self.available_equipment = self._convert_discovered_to_console_equipment(discovered_equipment)
        else:
            logger.warning("⚠️ Aucun équipement découvert, utilisation fallback VPCS uniquement")
            # Fallback minimal pour les VPCS uniquement  
            self.available_equipment = [
                ConsoleEquipment(
                    name="PC1", 
                    ip_address="192.168.20.10", 
                    console_host="192.168.122.95", 
                    console_port=5007,
                    console_type="telnet",
                    vlan="VLAN_20"
                ),
                ConsoleEquipment(
                    name="Admin", 
                    ip_address="192.168.41.10", 
                    console_host="192.168.122.95", 
                    console_port=5009,
                    console_type="telnet", 
                    vlan="VLAN_41"
                ),
                ConsoleEquipment(
                    name="PC2", 
                    ip_address="192.168.20.11", 
                    console_host="192.168.122.95", 
                    console_port=5008,
                    console_type="telnet",
                    vlan="VLAN_20"
                )
            ]
        
        logger.info(f"📡 {len(self.available_equipment)} équipements console configurés pour injection")
    
    def _convert_discovered_to_console_equipment(self, discovered_equipment):
        """Convertit les équipements découverts en équipements console."""
        console_equipment = []
        
        # Mapping des IPs prédéfinies pour les équipements
        predefined_ips = {
            "PC1": "192.168.20.10",
            "PC2": "192.168.20.11", 
            "Admin": "192.168.41.10",
            "Server-Web": "192.168.10.10",
            "Server-Mail": "192.168.10.11",
            "Server-DNS": "192.168.11.11",
            "Server-DB": "192.168.30.10",
            "Server-Fichiers": "192.168.31.10",
            "PostTest": "192.168.32.10"
        }
        
        for equipment in discovered_equipment:
            name = equipment.get('name')
            console_host = equipment.get('console_host')
            console_port = equipment.get('console_port')
            console_type = equipment.get('console_type')
            node_type = equipment.get('node_type')
            
            # Déterminer l'IP et le VLAN
            ip_address = predefined_ips.get(name)
            if not ip_address:
                continue  # Skip équipements sans IP prédéfinie
                
            # Déterminer le VLAN basé sur l'IP
            if ip_address.startswith("192.168.10."):
                vlan = "VLAN_10"
            elif ip_address.startswith("192.168.11."):
                vlan = "VLAN_11"
            elif ip_address.startswith("192.168.20."):
                vlan = "VLAN_20"
            elif ip_address.startswith("192.168.30."):
                vlan = "VLAN_30"
            elif ip_address.startswith("192.168.31."):
                vlan = "VLAN_31"
            elif ip_address.startswith("192.168.32."):
                vlan = "VLAN_32"
            elif ip_address.startswith("192.168.41."):
                vlan = "VLAN_41"
            else:
                vlan = "UNKNOWN"
            
            console_eq = ConsoleEquipment(
                name=name,
                ip_address=ip_address,
                console_host=console_host,
                console_port=console_port,
                console_type=console_type,
                vlan=vlan
            )
            
            console_equipment.append(console_eq)
            logger.debug(f"   📱 {name}: {ip_address} via {console_type}://{console_host}:{console_port}")
        
        return console_equipment
        
    def get_best_source_for_target(self, target_ip: str) -> Optional[ConsoleEquipment]:
        """Sélectionne le meilleur équipement source pour une cible."""
        # Logique simple : utiliser PC1 par défaut, Admin pour VLAN 41
        if target_ip.startswith("192.168.41."):
            return next((eq for eq in self.available_equipment if eq.name == "Admin"), None)
        else:
            return next((eq for eq in self.available_equipment if eq.name == "PC1"), None)
    
    def execute_ping_from_console(self, source: ConsoleEquipment, target_ip: str, count: int = 3) -> Dict:
        """Exécute un ping depuis un équipement via sa console."""
        try:
            logger.info(f"🔌 Ping depuis {source.name} vers {target_ip}")
            
            # Connexion telnet à la console
            tn = telnetlib.Telnet(source.console_host, source.console_port, timeout=10)
            
            # Attendre l'invite VPCS
            time.sleep(2)
            tn.read_very_eager()  # Nettoyer le buffer
            
            # Envoyer la commande ping
            ping_cmd = f"ping {target_ip} -c {count}\n"
            tn.write(ping_cmd.encode('ascii'))
            
            # Attendre la réponse
            time.sleep(max(3, count + 1))
            
            # Lire la réponse
            response = tn.read_very_eager().decode('ascii', errors='ignore')
            tn.close()
            
            # Parser la réponse
            result = self._parse_ping_response(response, target_ip)
            logger.info(f"✅ Ping {source.name}→{target_ip}: {result['success_rate']}% succès")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Erreur ping console {source.name}→{target_ip}: {e}")
            return {
                "success": False,
                "packets_sent": count,
                "packets_received": 0,
                "success_rate": 0,
                "target_alive": False,
                "error": str(e)
            }
    
    def execute_scan_from_console(self, source: ConsoleEquipment, target_network: str) -> Dict:
        """Exécute un scan réseau depuis un équipement via sa console."""
        try:
            logger.info(f"🔍 Scan réseau depuis {source.name} vers {target_network}")
            
            # Connexion telnet
            tn = telnetlib.Telnet(source.console_host, source.console_port, timeout=10)
            time.sleep(2)
            tn.read_very_eager()
            
            # Scanner quelques IPs du réseau (VPCS n'a pas nmap, on fait des pings)
            base_ip = target_network.split('/')[0].rsplit('.', 1)[0]
            alive_hosts = []
            
            for i in range(1, 21):  # Scanner .1 à .20
                test_ip = f"{base_ip}.{i}"
                
                # Ping rapide
                ping_cmd = f"ping {test_ip} -c 1\n"
                tn.write(ping_cmd.encode('ascii'))
                time.sleep(2)
                
                response = tn.read_very_eager().decode('ascii', errors='ignore')
                
                # Vérifier si l'hôte répond
                if "bytes from" in response.lower() or "reply from" in response.lower():
                    alive_hosts.append(test_ip)
                    logger.debug(f"   🎯 {test_ip} : VIVANT")
                else:
                    logger.debug(f"   💀 {test_ip} : MORT")
            
            tn.close()
            
            logger.info(f"✅ Scan {source.name}→{target_network}: {len(alive_hosts)} hôtes vivants")
            
            return {
                "success": True,
                "source": source.name,
                "target_network": target_network,
                "alive_hosts": alive_hosts,
                "total_scanned": 20,
                "alive_count": len(alive_hosts)
            }
            
        except Exception as e:
            logger.error(f"❌ Erreur scan console {source.name}→{target_network}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _parse_ping_response(self, response: str, target_ip: str) -> Dict:
        """Parse la réponse d'un ping VPCS."""
        try:
            # VPCS affiche directement les réponses sans statistiques finales
            # Format: "84 bytes from 192.168.20.1 icmp_seq=1 ttl=255 time=10.851 ms"
            
            # Compter les lignes de réponse réussies (format VPCS)
            # VPCS utilise: "192.168.20.10 icmp_seq=1 ttl=64 time=0.001 ms"
            vpcs_success_pattern = r'[0-9.]+\s+icmp_seq=\d+\s+ttl=\d+'
            success_lines = re.findall(vpcs_success_pattern, response)
            packets_received = len(success_lines)
            
            # VPCS envoie toujours le nombre demandé (défaut 3 dans notre cas)
            packets_sent = 3  # Par défaut dans notre implémentation
            
            # Vérifier si on a des réponses positives
            has_replies = packets_received > 0
            
            # Vérifier les erreurs communes VPCS
            has_errors = any(error in response.lower() for error in [
                "not reachable", "timeout", "host unreachable", 
                "communication administratively prohibited",
                "host not reachable", "network unreachable"
            ])
            
            success_rate = (packets_received / packets_sent * 100) if packets_sent > 0 else 0
            
            return {
                "success": packets_received > 0 and not has_errors,
                "target_ip": target_ip,
                "packets_sent": packets_sent,
                "packets_received": packets_received,
                "success_rate": success_rate,
                "target_alive": has_replies,
                "has_errors": has_errors,
                "raw_response": response[:500]  # Premiers 500 caractères
            }
            
        except Exception as e:
            logger.debug(f"Erreur parsing ping: {e}")
            return {
                "success": False,
                "target_ip": target_ip,
                "packets_sent": 3,
                "packets_received": 0,
                "success_rate": 0,
                "target_alive": False,
                "error": str(e)
            }
    
    def inject_traffic_to_targets(self, target_ips: List[str]) -> Dict:
        """Injecte du trafic vers une liste de cibles en utilisant les consoles."""
        results = {
            "total_targets": len(target_ips),
            "successful_pings": 0,
            "alive_targets": [],
            "failed_targets": [],
            "injection_details": []
        }
        
        for target_ip in target_ips:
            # Choisir le meilleur équipement source
            source = self.get_best_source_for_target(target_ip)
            
            if not source:
                logger.warning(f"⚠️ Aucun équipement source disponible pour {target_ip}")
                results["failed_targets"].append(target_ip)
                continue
            
            # Exécuter le ping
            ping_result = self.execute_ping_from_console(source, target_ip)
            
            results["injection_details"].append({
                "source": source.name,
                "target": target_ip,
                "result": ping_result
            })
            
            if ping_result["success"]:
                results["successful_pings"] += 1
                if ping_result.get("target_alive"):
                    results["alive_targets"].append(target_ip)
            else:
                results["failed_targets"].append(target_ip)
        
        logger.info(f"📡 Injection terminée: {results['successful_pings']}/{results['total_targets']} réussies")
        
        return results