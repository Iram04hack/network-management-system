"""
Service d'analyse réseau.

Ce module contient le service pour analyser les données réseau
et générer des recommandations.
"""

import logging
import json
import subprocess
import re
from typing import Dict, Any, List, Optional

from ai_assistant.domain.exceptions import NetworkAnalysisError

logger = logging.getLogger(__name__)


class NetworkAnalysisService:
    """Service pour analyser les données réseau."""
    
    def __init__(self):
        """Initialise le service d'analyse réseau."""
        pass
    
    def analyze_device_performance(self, device_id: str) -> Dict[str, Any]:
        """
        Analyse les performances d'un appareil réseau.
        
        Args:
            device_id: ID de l'appareil à analyser
            
        Returns:
            Dict[str, Any]: Résultats de l'analyse
            
        Raises:
            NetworkAnalysisError: Si une erreur se produit lors de l'analyse
        """
        try:
            # Simuler une analyse de performance
            # En production, cela serait remplacé par une vraie analyse
            
            return {
                "device_id": device_id,
                "cpu_usage": {
                    "current": 45.2,
                    "average_1h": 42.8,
                    "average_24h": 38.5,
                    "status": "normal"
                },
                "memory_usage": {
                    "current": 68.7,
                    "average_1h": 67.2,
                    "average_24h": 65.9,
                    "status": "normal"
                },
                "interface_stats": {
                    "total": 8,
                    "up": 6,
                    "down": 2,
                    "errors": 1
                },
                "recommendations": [
                    "Vérifier l'interface GigabitEthernet0/2 qui présente des erreurs",
                    "Envisager une mise à niveau de la mémoire si l'utilisation continue d'augmenter"
                ]
            }
        
        except Exception as e:
            logger.exception(f"Erreur lors de l'analyse des performances de l'appareil: {device_id}")
            raise NetworkAnalysisError(f"Erreur lors de l'analyse des performances: {str(e)}")
    
    def analyze_network_traffic(self, network_id: str) -> Dict[str, Any]:
        """
        Analyse le trafic d'un réseau.
        
        Args:
            network_id: ID du réseau à analyser
            
        Returns:
            Dict[str, Any]: Résultats de l'analyse
            
        Raises:
            NetworkAnalysisError: Si une erreur se produit lors de l'analyse
        """
        try:
            # Simuler une analyse de trafic
            # En production, cela serait remplacé par une vraie analyse
            
            return {
                "network_id": network_id,
                "total_traffic": {
                    "inbound": "1.2 Gbps",
                    "outbound": "0.8 Gbps",
                    "peak_inbound": "1.8 Gbps",
                    "peak_outbound": "1.1 Gbps"
                },
                "protocol_distribution": {
                    "http": 35.2,
                    "https": 42.8,
                    "dns": 8.5,
                    "smtp": 5.2,
                    "other": 8.3
                },
                "top_talkers": [
                    {"ip": "192.168.1.15", "hostname": "server1.local", "traffic": "450 Mbps"},
                    {"ip": "192.168.1.22", "hostname": "server2.local", "traffic": "320 Mbps"},
                    {"ip": "192.168.1.5", "hostname": "workstation3.local", "traffic": "180 Mbps"}
                ],
                "anomalies": [
                    {"type": "traffic_spike", "source": "192.168.1.15", "destination": "external", "severity": "medium"},
                    {"type": "unusual_port", "source": "192.168.1.22", "port": 8080, "severity": "low"}
                ],
                "recommendations": [
                    "Surveiller le trafic sortant de 192.168.1.15 vers des destinations externes",
                    "Vérifier l'utilisation du port 8080 sur 192.168.1.22"
                ]
            }
        
        except Exception as e:
            logger.exception(f"Erreur lors de l'analyse du trafic réseau: {network_id}")
            raise NetworkAnalysisError(f"Erreur lors de l'analyse du trafic: {str(e)}")
    
    def analyze_security_posture(self, network_id: str) -> Dict[str, Any]:
        """
        Analyse la posture de sécurité d'un réseau.
        
        Args:
            network_id: ID du réseau à analyser
            
        Returns:
            Dict[str, Any]: Résultats de l'analyse
            
        Raises:
            NetworkAnalysisError: Si une erreur se produit lors de l'analyse
        """
        try:
            # Simuler une analyse de sécurité
            # En production, cela serait remplacé par une vraie analyse
            
            return {
                "network_id": network_id,
                "security_score": 72,  # Sur 100
                "vulnerabilities": {
                    "critical": 2,
                    "high": 5,
                    "medium": 12,
                    "low": 23
                },
                "firewall_status": {
                    "rules_count": 45,
                    "outdated_rules": 8,
                    "conflicting_rules": 3
                },
                "encryption_status": {
                    "unencrypted_services": 4,
                    "weak_ciphers": 2
                },
                "patch_status": {
                    "devices_up_to_date": 18,
                    "devices_outdated": 7,
                    "critical_patches_missing": 3
                },
                "recommendations": [
                    "Appliquer les correctifs critiques manquants sur 3 appareils",
                    "Résoudre les 2 vulnérabilités critiques identifiées",
                    "Mettre à jour ou supprimer les 8 règles de pare-feu obsolètes",
                    "Activer le chiffrement sur les 4 services non chiffrés"
                ]
            }
        
        except Exception as e:
            logger.exception(f"Erreur lors de l'analyse de la posture de sécurité: {network_id}")
            raise NetworkAnalysisError(f"Erreur lors de l'analyse de la sécurité: {str(e)}")
    
    def generate_optimization_recommendations(self, network_id: str) -> List[Dict[str, Any]]:
        """
        Génère des recommandations d'optimisation pour un réseau.
        
        Args:
            network_id: ID du réseau à analyser
            
        Returns:
            List[Dict[str, Any]]: Liste des recommandations
            
        Raises:
            NetworkAnalysisError: Si une erreur se produit lors de la génération des recommandations
        """
        try:
            # Simuler la génération de recommandations
            # En production, cela serait remplacé par une vraie analyse
            
            return [
                {
                    "id": "REC001",
                    "category": "performance",
                    "title": "Optimisation de la QoS",
                    "description": "Configurer la qualité de service (QoS) pour prioriser le trafic critique",
                    "impact": "high",
                    "effort": "medium",
                    "details": "Les applications critiques subissent des ralentissements aux heures de pointe. Mettre en place une stratégie QoS pour prioriser le trafic VoIP et les applications métier critiques."
                },
                {
                    "id": "REC002",
                    "category": "security",
                    "title": "Segmentation du réseau",
                    "description": "Implémenter des VLANs pour segmenter le réseau",
                    "impact": "high",
                    "effort": "high",
                    "details": "Le réseau actuel est plat, ce qui augmente les risques de propagation latérale des menaces. Segmenter le réseau en VLANs distincts pour isoler les différents services et limiter l'impact des incidents de sécurité."
                },
                {
                    "id": "REC003",
                    "category": "reliability",
                    "title": "Redondance des liens",
                    "description": "Ajouter des liens redondants entre les commutateurs principaux",
                    "impact": "medium",
                    "effort": "medium",
                    "details": "Actuellement, la topologie présente des points uniques de défaillance. Ajouter des liens redondants et configurer le protocole Spanning Tree pour améliorer la résilience du réseau."
                },
                {
                    "id": "REC004",
                    "category": "performance",
                    "title": "Mise à niveau des équipements",
                    "description": "Remplacer les commutateurs d'accès obsolètes",
                    "impact": "medium",
                    "effort": "high",
                    "details": "Certains commutateurs d'accès sont anciens et limitent les performances. Planifier le remplacement des équipements les plus anciens pour améliorer les performances et la fiabilité."
                },
                {
                    "id": "REC005",
                    "category": "management",
                    "title": "Centralisation des logs",
                    "description": "Mettre en place un serveur de logs centralisé",
                    "impact": "low",
                    "effort": "low",
                    "details": "La gestion actuelle des logs est dispersée sur chaque appareil. Centraliser la collecte et l'analyse des logs pour faciliter le dépannage et améliorer la détection des incidents."
                }
            ]
        
        except Exception as e:
            logger.exception(f"Erreur lors de la génération des recommandations d'optimisation: {network_id}")
            raise NetworkAnalysisError(f"Erreur lors de la génération des recommandations: {str(e)}")
    
    def analyze_configuration_compliance(self, device_id: str, compliance_template: Optional[str] = None) -> Dict[str, Any]:
        """
        Analyse la conformité de la configuration d'un appareil.
        
        Args:
            device_id: ID de l'appareil à analyser
            compliance_template: Template de conformité à utiliser (optionnel)
            
        Returns:
            Dict[str, Any]: Résultats de l'analyse
            
        Raises:
            NetworkAnalysisError: Si une erreur se produit lors de l'analyse
        """
        try:
            # Simuler une analyse de conformité
            # En production, cela serait remplacé par une vraie analyse
            
            return {
                "device_id": device_id,
                "compliance_score": 85,  # Sur 100
                "template_used": compliance_template or "default_template",
                "checks": [
                    {
                        "id": "SEC001",
                        "name": "Authentification forte",
                        "status": "pass",
                        "details": "L'authentification forte est correctement configurée"
                    },
                    {
                        "id": "SEC002",
                        "name": "Chiffrement des communications",
                        "status": "pass",
                        "details": "Le chiffrement est activé pour toutes les communications"
                    },
                    {
                        "id": "SEC003",
                        "name": "Gestion des mots de passe",
                        "status": "fail",
                        "details": "La politique de complexité des mots de passe n'est pas conforme"
                    },
                    {
                        "id": "SEC004",
                        "name": "Journalisation",
                        "status": "warning",
                        "details": "La journalisation est activée mais n'est pas envoyée à un serveur centralisé"
                    },
                    {
                        "id": "SEC005",
                        "name": "Contrôle d'accès",
                        "status": "pass",
                        "details": "Les listes de contrôle d'accès sont correctement configurées"
                    }
                ],
                "recommendations": [
                    "Mettre à jour la politique de complexité des mots de passe",
                    "Configurer l'envoi des journaux à un serveur centralisé"
                ]
            }
        
        except Exception as e:
            logger.exception(f"Erreur lors de l'analyse de la conformité de la configuration: {device_id}")
            raise NetworkAnalysisError(f"Erreur lors de l'analyse de la conformité: {str(e)}")
    
    def analyze_network_topology(self, network_id: str) -> Dict[str, Any]:
        """
        Analyse la topologie d'un réseau.
        
        Args:
            network_id: ID du réseau à analyser
            
        Returns:
            Dict[str, Any]: Résultats de l'analyse
            
        Raises:
            NetworkAnalysisError: Si une erreur se produit lors de l'analyse
        """
        try:
            # Simuler une analyse de topologie
            # En production, cela serait remplacé par une vraie analyse
            
            return {
                "network_id": network_id,
                "topology_type": "hierarchical",
                "layers": {
                    "core": {
                        "devices": 2,
                        "redundancy": "full",
                        "health": "good"
                    },
                    "distribution": {
                        "devices": 4,
                        "redundancy": "partial",
                        "health": "good"
                    },
                    "access": {
                        "devices": 12,
                        "redundancy": "none",
                        "health": "fair"
                    }
                },
                "critical_paths": [
                    {
                        "path": "core1 -> dist2 -> access5",
                        "status": "healthy",
                        "utilization": "medium"
                    },
                    {
                        "path": "core2 -> dist3 -> access8",
                        "status": "degraded",
                        "utilization": "high"
                    }
                ],
                "single_points_of_failure": [
                    {
                        "device": "dist4",
                        "impact": "medium",
                        "affected_devices": 3
                    }
                ],
                "recommendations": [
                    "Ajouter un lien redondant entre dist4 et core2",
                    "Réduire la charge sur le chemin core2 -> dist3 -> access8",
                    "Envisager l'ajout de redondance au niveau de la couche d'accès"
                ]
            }
        
        except Exception as e:
            logger.exception(f"Erreur lors de l'analyse de la topologie réseau: {network_id}")
            raise NetworkAnalysisError(f"Erreur lors de l'analyse de la topologie: {str(e)}")
    
    def get_network_health_summary(self, network_id: str) -> Dict[str, Any]:
        """
        Obtient un résumé de l'état de santé d'un réseau.
        
        Args:
            network_id: ID du réseau à analyser
            
        Returns:
            Dict[str, Any]: Résumé de l'état de santé
            
        Raises:
            NetworkAnalysisError: Si une erreur se produit lors de l'analyse
        """
        try:
            # Simuler un résumé de l'état de santé
            # En production, cela serait remplacé par une vraie analyse
            
            return {
                "network_id": network_id,
                "overall_health": {
                    "score": 82,  # Sur 100
                    "status": "good",
                    "trend": "stable"
                },
                "components": {
                    "devices": {
                        "total": 18,
                        "healthy": 15,
                        "warning": 2,
                        "critical": 1
                    },
                    "links": {
                        "total": 24,
                        "healthy": 22,
                        "warning": 1,
                        "critical": 1
                    },
                    "services": {
                        "total": 8,
                        "healthy": 7,
                        "warning": 1,
                        "critical": 0
                    }
                },
                "alerts": {
                    "critical": 1,
                    "warning": 3,
                    "info": 5
                },
                "performance": {
                    "bandwidth_utilization": "medium",
                    "latency": "low",
                    "packet_loss": "minimal"
                },
                "recent_issues": [
                    {
                        "timestamp": "2023-06-15T14:23:45",
                        "device": "router2",
                        "description": "Interface GigabitEthernet0/1 down",
                        "status": "resolved"
                    },
                    {
                        "timestamp": "2023-06-14T08:12:30",
                        "device": "switch5",
                        "description": "High CPU utilization",
                        "status": "ongoing"
                    }
                ],
                "recommendations": [
                    "Résoudre le problème critique sur le routeur principal",
                    "Surveiller l'utilisation du CPU sur switch5",
                    "Planifier une maintenance pour les 2 appareils en état d'avertissement"
                ]
            }
        
        except Exception as e:
            logger.exception(f"Erreur lors de l'obtention du résumé de l'état de santé: {network_id}")
            raise NetworkAnalysisError(f"Erreur lors de l'obtention du résumé de l'état de santé: {str(e)}")
    
    # Méthodes ajoutées pour les tests
    
    def analyze_ping(self, host: str) -> Dict[str, Any]:
        """
        Analyse le résultat d'une commande ping.
        
        Args:
            host: Hôte à pinger
            
        Returns:
            Dict[str, Any]: Résultats de l'analyse
            
        Raises:
            NetworkAnalysisError: Si une erreur se produit lors de l'analyse
        """
        try:
            # Exécuter la commande ping
            cmd = ["ping", "-c", "4", host]
            process = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            if process.returncode != 0:
                return {
                    "erreur": "Impossible de résoudre le nom d'hôte" if "Name or service not known" in process.stderr else process.stderr
                }
            
            # Analyser la sortie
            return self.analyze_ping_output(process.stdout)
            
        except Exception as e:
            logger.exception(f"Erreur lors de l'analyse ping pour l'hôte: {host}")
            raise NetworkAnalysisError(f"Erreur lors de l'analyse ping: {str(e)}")
    
    def analyze_ping_output(self, output: str) -> Dict[str, Any]:
        """
        Analyse la sortie d'une commande ping.
        
        Args:
            output: Sortie de la commande ping
            
        Returns:
            Dict[str, Any]: Résultats de l'analyse
        """
        # Extraire les statistiques
        stats_match = re.search(r'(\d+) packets transmitted, (\d+) received, (\d+(?:\.\d+)?)% packet loss', output)
        rtt_match = re.search(r'rtt min/avg/max/mdev = (\d+\.\d+)/(\d+\.\d+)/(\d+\.\d+)/(\d+\.\d+)', output)
        
        if not stats_match:
            return {"erreur": "Impossible d'analyser la sortie ping"}
        
        packets_transmitted = int(stats_match.group(1))
        packets_received = int(stats_match.group(2))
        packet_loss = float(stats_match.group(3))
        
        result = {
            "analyse": {
                "packets_transmitted": packets_transmitted,
                "packets_received": packets_received,
                "packet_loss": packet_loss
            }
        }
        
        if rtt_match:
            result["analyse"]["rtt_min"] = float(rtt_match.group(1))
            result["analyse"]["rtt_avg"] = float(rtt_match.group(2))
            result["analyse"]["rtt_max"] = float(rtt_match.group(3))
            result["analyse"]["rtt_mdev"] = float(rtt_match.group(4))
        
        return result
    
    def analyze_traceroute(self, host: str) -> Dict[str, Any]:
        """
        Analyse le résultat d'une commande traceroute.
        
        Args:
            host: Hôte à tracer
            
        Returns:
            Dict[str, Any]: Résultats de l'analyse
            
        Raises:
            NetworkAnalysisError: Si une erreur se produit lors de l'analyse
        """
        try:
            # Exécuter la commande traceroute
            cmd = ["traceroute", host]
            process = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if process.returncode != 0:
                return {
                    "erreur": "Impossible de résoudre le nom d'hôte" if "Name or service not known" in process.stderr else process.stderr
                }
            
            # Analyser la sortie
            return self.analyze_traceroute_output(process.stdout)
            
        except Exception as e:
            logger.exception(f"Erreur lors de l'analyse traceroute pour l'hôte: {host}")
            raise NetworkAnalysisError(f"Erreur lors de l'analyse traceroute: {str(e)}")
    
    def analyze_traceroute_output(self, output: str) -> Dict[str, Any]:
        """
        Analyse la sortie d'une commande traceroute.
        
        Args:
            output: Sortie de la commande traceroute
            
        Returns:
            Dict[str, Any]: Résultats de l'analyse
        """
        lines = output.strip().split('\n')
        hops = []
        
        # Ignorer la première ligne (entête)
        for i, line in enumerate(lines[1:], 1):
            # Extraire le numéro du saut, l'hôte et le temps
            hop_match = re.search(r'^\s*(\d+)\s+([^\s]+)?\s*\(([^\)]+)\)?\s+(\d+\.\d+)\s+ms', line)
            
            if hop_match:
                hop = {
                    "hop": int(hop_match.group(1)),
                    "host": hop_match.group(2) if hop_match.group(2) != hop_match.group(3) else "",
                    "ip": hop_match.group(3),
                    "time": float(hop_match.group(4))
                }
                hops.append(hop)
            elif "*" in line:
                # Saut non résolu
                hop_num_match = re.search(r'^\s*(\d+)', line)
                if hop_num_match:
                    hop = {
                        "hop": int(hop_num_match.group(1)),
                        "host": "",
                        "ip": "",
                        "time": None
                    }
                    hops.append(hop)
        
        return {
            "analyse": {
                "hops": hops
            }
        }
    
    def analyze_ifconfig(self) -> Dict[str, Any]:
        """
        Analyse le résultat d'une commande ifconfig.
        
        Returns:
            Dict[str, Any]: Résultats de l'analyse
            
        Raises:
            NetworkAnalysisError: Si une erreur se produit lors de l'analyse
        """
        try:
            # Exécuter la commande ifconfig
            cmd = ["ifconfig"]
            process = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            if process.returncode != 0:
                return {
                    "erreur": process.stderr
                }
            
            # Analyser la sortie
            return self.analyze_ifconfig_output(process.stdout)
            
        except Exception as e:
            logger.exception("Erreur lors de l'analyse ifconfig")
            raise NetworkAnalysisError(f"Erreur lors de l'analyse ifconfig: {str(e)}")
    
    def analyze_ifconfig_output(self, output: str) -> Dict[str, Any]:
        """
        Analyse la sortie d'une commande ifconfig.
        
        Args:
            output: Sortie de la commande ifconfig
            
        Returns:
            Dict[str, Any]: Résultats de l'analyse
        """
        interfaces = {}
        current_interface = None
        
        for line in output.split('\n'):
            # Nouvelle interface
            if not line.startswith(' ') and ':' in line:
                interface_name = line.split(':')[0]
                current_interface = interface_name
                interfaces[current_interface] = {
                    "ipv4": "",
                    "ipv6": "",
                    "mac": "",
                    "mtu": 0,
                    "rx_packets": 0,
                    "tx_packets": 0
                }
            
            # Adresse IPv4
            elif current_interface and "inet " in line:
                ipv4_match = re.search(r'inet (\d+\.\d+\.\d+\.\d+)', line)
                if ipv4_match:
                    interfaces[current_interface]["ipv4"] = ipv4_match.group(1)
            
            # Adresse IPv6
            elif current_interface and "inet6" in line:
                ipv6_match = re.search(r'inet6 ([0-9a-f:]+)', line)
                if ipv6_match:
                    interfaces[current_interface]["ipv6"] = ipv6_match.group(1)
            
            # Adresse MAC
            elif current_interface and "ether" in line:
                mac_match = re.search(r'ether ([0-9a-f:]+)', line)
                if mac_match:
                    interfaces[current_interface]["mac"] = mac_match.group(1)
            
            # MTU
            elif current_interface and "mtu" in line:
                mtu_match = re.search(r'mtu (\d+)', line)
                if mtu_match:
                    interfaces[current_interface]["mtu"] = int(mtu_match.group(1))
            
            # Statistiques RX
            elif current_interface and "RX packets" in line:
                rx_match = re.search(r'RX packets (\d+)', line)
                if rx_match:
                    interfaces[current_interface]["rx_packets"] = int(rx_match.group(1))
            
            # Statistiques TX
            elif current_interface and "TX packets" in line:
                tx_match = re.search(r'TX packets (\d+)', line)
                if tx_match:
                    interfaces[current_interface]["tx_packets"] = int(tx_match.group(1))
        
        return {
            "analyse": {
                "interfaces": interfaces
            }
        }
    
    def analyze_netstat(self) -> Dict[str, Any]:
        """
        Analyse le résultat d'une commande netstat.
        
        Returns:
            Dict[str, Any]: Résultats de l'analyse
            
        Raises:
            NetworkAnalysisError: Si une erreur se produit lors de l'analyse
        """
        try:
            # Exécuter la commande netstat
            cmd = ["netstat", "-tuln"]
            process = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            if process.returncode != 0:
                return {
                    "erreur": process.stderr
                }
            
            # Analyser la sortie
            return self.analyze_netstat_output(process.stdout)
            
        except Exception as e:
            logger.exception("Erreur lors de l'analyse netstat")
            raise NetworkAnalysisError(f"Erreur lors de l'analyse netstat: {str(e)}")
    
    def analyze_netstat_output(self, output: str) -> Dict[str, Any]:
        """
        Analyse la sortie d'une commande netstat.
        
        Args:
            output: Sortie de la commande netstat
            
        Returns:
            Dict[str, Any]: Résultats de l'analyse
        """
        connections = []
        lines = output.strip().split('\n')
        
        # Ignorer les deux premières lignes (entêtes)
        for line in lines[2:]:
            parts = line.split()
            if len(parts) >= 5:
                connection = {
                    "proto": parts[0],
                    "local_address": parts[3],
                    "foreign_address": parts[4],
                    "state": parts[5] if len(parts) > 5 else ""
                }
                connections.append(connection)
        
        return {
            "analyse": {
                "connections": connections
            }
        }
    
    def analyze_nmap(self, target: str) -> Dict[str, Any]:
        """
        Analyse le résultat d'une commande nmap.
        
        Args:
            target: Cible à scanner
            
        Returns:
            Dict[str, Any]: Résultats de l'analyse
            
        Raises:
            NetworkAnalysisError: Si une erreur se produit lors de l'analyse
        """
        try:
            # Exécuter la commande nmap
            cmd = ["nmap", "-F", target]  # -F pour un scan rapide
            process = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            if process.returncode != 0:
                return {
                    "erreur": process.stderr
                }
            
            # Analyser la sortie
            return self.analyze_nmap_output(process.stdout)
            
        except Exception as e:
            logger.exception(f"Erreur lors de l'analyse nmap pour la cible: {target}")
            raise NetworkAnalysisError(f"Erreur lors de l'analyse nmap: {str(e)}")
    
    def analyze_nmap_output(self, output: str) -> Dict[str, Any]:
        """
        Analyse la sortie d'une commande nmap.
        
        Args:
            output: Sortie de la commande nmap
            
        Returns:
            Dict[str, Any]: Résultats de l'analyse
        """
        hosts = []
        current_host = None
        current_ports = []
        
        lines = output.strip().split('\n')
        for line in lines:
            # Nouvelle cible
            if "Nmap scan report for" in line:
                if current_host:
                    current_host["ports"] = current_ports
                    hosts.append(current_host)
                
                host_match = re.search(r'Nmap scan report for ([^\s]+)(?:\s+\(([^\)]+)\))?', line)
                if host_match:
                    hostname = host_match.group(1)
                    ip = host_match.group(2) if host_match.group(2) else hostname
                    
                    current_host = {
                        "host": hostname,
                        "ip": ip,
                        "status": "unknown",
                        "latency": 0.0
                    }
                    current_ports = []
            
            # État de l'hôte
            elif "Host is" in line:
                status_match = re.search(r'Host is (\w+) \((\d+\.\d+)s latency\)', line)
                if status_match and current_host:
                    current_host["status"] = status_match.group(1)
                    current_host["latency"] = float(status_match.group(2))
            
            # Port
            elif re.match(r'^\d+/\w+', line):
                port_match = re.search(r'(\d+)/(\w+)\s+(\w+)\s+(\w+)', line)
                if port_match and current_host:
                    port = {
                        "port": int(port_match.group(1)),
                        "protocol": port_match.group(2),
                        "state": port_match.group(3),
                        "service": port_match.group(4)
                    }
                    current_ports.append(port)
        
        # Ajouter le dernier hôte
        if current_host:
            current_host["ports"] = current_ports
            hosts.append(current_host)
        
        return {
            "analyse": {
                "hosts": hosts
            }
        } 