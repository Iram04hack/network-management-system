#!/usr/bin/env python3
"""
Découverte des Vraies Adresses IP via Consoles GNS3
===================================================

Ce module se connecte aux consoles des équipements GNS3 pour récupérer
les vraies adresses IP via la commande 'dhcp', pas 'show ip'.

Fonctionnalités :
- Connexion aux consoles avec authentification
- Exécution de la commande 'dhcp' pour chaque équipement
- Récupération des vraies adresses IP selon les VLAN
- Gestion d'erreurs détaillée pour chaque équipement
- Support authentification (osboxes/osboxes.org)
"""

import telnetlib
import socket
import time
import logging
import re
import asyncio
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import concurrent.futures
from pathlib import Path

logger = logging.getLogger(__name__)

class EquipmentType(Enum):
    """Types d'équipements réseau."""
    ROUTER = "router"
    SWITCH = "switch"
    SERVER = "server"
    WORKSTATION = "workstation"
    UNKNOWN = "unknown"

@dataclass
class ConsoleConnection:
    """Informations de connexion console."""
    node_id: str
    node_name: str
    console_host: str
    console_port: int
    console_type: str
    equipment_type: EquipmentType
    auth_required: bool = False

@dataclass
class IPDiscoveryResult:
    """Résultat de découverte IP pour un équipement."""
    node_id: str
    node_name: str
    success: bool
    ip_addresses: List[str]
    vlan_info: Dict[str, str]
    dhcp_output: str
    error_message: Optional[str] = None
    execution_time: float = 0.0
    authentication_used: bool = False

@dataclass
class ConsoleCommand:
    """Commande à exécuter sur une console."""
    command: str
    expected_prompt: str
    timeout: int = 10
    description: str = ""

class ConsoleIPDiscovery:
    """
    Découvreur d'adresses IP réelles via les consoles des équipements.
    
    Utilise la commande 'dhcp' pour obtenir les vraies adresses IP
    assignées selon les VLAN, pas celles affichées par 'show ip'.
    """
    
    def __init__(self, username: str = "osboxes", password: str = "osboxes.org"):
        """
        Initialise le découvreur IP.
        
        Args:
            username: Nom d'utilisateur pour l'authentification
            password: Mot de passe pour l'authentification
        """
        self.username = username
        self.password = password
        self.timeout = 30
        self.command_delay = 2
        self.discovery_results = {}
        self.connection_errors = {}
        
        # Commandes spécifiques par type d'équipement (MISES À JOUR avec tests réels)
        self.commands_by_type = {
            EquipmentType.ROUTER: [
                ConsoleCommand("show ip interface brief", "#", 10, "Interfaces IP Cisco"),
                ConsoleCommand("show ip route | include C", "#", 8, "Routes connectées"),
                ConsoleCommand("show interface | include line protocol", "#", 8, "État interfaces"),
            ],
            EquipmentType.SWITCH: [
                ConsoleCommand("show ip interface brief", "#", 10, "IPs management switch"),
                ConsoleCommand("show interface vlan", "#", 8, "Interfaces VLAN"),
                ConsoleCommand("show vlan brief", "#", 8, "Informations VLAN"),
            ],
            EquipmentType.SERVER: [
                ConsoleCommand("dhcp", "$", 15, "Récupération IP via DHCP"),
                ConsoleCommand("ifconfig", "$", 10, "Configuration interfaces"),
                ConsoleCommand("ip addr show", "$", 8, "Adresses IP système"),
            ],
            EquipmentType.WORKSTATION: [
                ConsoleCommand("show ip", ">", 5, "Configuration IP VPCS"),
                ConsoleCommand("show", ">", 5, "Informations générales VPCS"),
            ]
        }
        
        logger.info(f"🔍 Découvreur IP initialisé avec authentification {username}/**********")
    
    async def discover_real_ips_from_project(self, project_id: str, equipment_list: List[Dict]) -> Dict[str, IPDiscoveryResult]:
        """
        Découvre les vraies adresses IP de tous les équipements d'un projet.
        
        Args:
            project_id: ID du projet GNS3
            equipment_list: Liste des équipements découverts par Django
            
        Returns:
            Dictionnaire des résultats de découverte IP
        """
        logger.info(f"🔍 Début de la découverte IP réelle pour le projet {project_id}")
        logger.info(f"📊 {len(equipment_list)} équipements à analyser")
        
        # Convertir les équipements en connexions console
        console_connections = self._prepare_console_connections(equipment_list)
        
        if not console_connections:
            logger.warning("⚠️ Aucune connexion console disponible")
            return {}
        
        # Découvrir les IP en parallèle
        discovery_tasks = []
        for connection in console_connections:
            task = self._discover_equipment_ip(connection)
            discovery_tasks.append(task)
        
        # Attendre tous les résultats
        results = await asyncio.gather(*discovery_tasks, return_exceptions=True)
        
        # Traiter les résultats
        final_results = {}
        for i, result in enumerate(results):
            connection = console_connections[i]
            
            if isinstance(result, Exception):
                # Erreur lors de la découverte
                error_result = IPDiscoveryResult(
                    node_id=connection.node_id,
                    node_name=connection.node_name,
                    success=False,
                    ip_addresses=[],
                    vlan_info={},
                    dhcp_output="",
                    error_message=f"Exception: {str(result)}",
                    execution_time=0.0
                )
                final_results[connection.node_id] = error_result
            else:
                # Résultat normal
                final_results[connection.node_id] = result
        
        # Afficher le résumé
        successful_discoveries = sum(1 for r in final_results.values() if r.success)
        total_ips_found = sum(len(r.ip_addresses) for r in final_results.values())
        
        logger.info(f"✅ Découverte IP terminée: {successful_discoveries}/{len(equipment_list)} équipements")
        logger.info(f"🌐 {total_ips_found} adresses IP réelles découvertes")
        
        return final_results
    
    def _prepare_console_connections(self, equipment_list: List[Dict]) -> List[ConsoleConnection]:
        """
        Prépare les connexions console à partir de la liste d'équipements.
        
        Args:
            equipment_list: Liste des équipements de Django
            
        Returns:
            Liste des connexions console préparées
        """
        console_connections = []
        
        for equipment in equipment_list:
            node_id = equipment.get('node_id', '')
            node_name = equipment.get('name', 'Unknown')
            console_port = equipment.get('console_port')
            console_type = equipment.get('console_type', 'telnet')
            node_type = equipment.get('node_type', 'unknown')
            
            if not console_port:
                logger.debug(f"⚠️ {node_name}: Pas de port console, ignoré")
                continue
            
            # Déterminer le type d'équipement
            equipment_type = self._determine_equipment_type(node_name, node_type)
            
            # Déterminer si l'authentification est requise
            auth_required = self._requires_authentication(node_name, node_type)
            
            # Utiliser la vraie adresse console si fournie, sinon localhost
            console_host = equipment.get('console_host', 'localhost')
            
            connection = ConsoleConnection(
                node_id=node_id,
                node_name=node_name,
                console_host=console_host,  # Vraie adresse console de GNS3
                console_port=console_port,
                console_type=console_type,
                equipment_type=equipment_type,
                auth_required=auth_required
            )
            
            console_connections.append(connection)
            logger.debug(f"🔌 {node_name}: Console préparée {console_port} ({equipment_type.value})")
        
        return console_connections
    
    def _determine_equipment_type(self, node_name: str, node_type: str) -> EquipmentType:
        """Détermine le type d'équipement basé sur le nom et le type de nœud."""
        node_name_lower = node_name.lower()
        node_type_lower = node_type.lower()
        
        if 'router' in node_name_lower or node_type_lower in ['dynamips', 'c7200']:
            return EquipmentType.ROUTER
        elif 'switch' in node_name_lower or 'sw-' in node_name_lower or node_type_lower == 'iou':
            return EquipmentType.SWITCH
        elif 'server' in node_name_lower or node_type_lower == 'qemu':
            return EquipmentType.SERVER
        elif 'pc' in node_name_lower or 'client' in node_name_lower:
            return EquipmentType.WORKSTATION
        else:
            return EquipmentType.UNKNOWN
    
    def _requires_authentication(self, node_name: str, node_type: str) -> bool:
        """Détermine si l'équipement nécessite une authentification."""
        # Les serveurs/workstations QEMU nécessitent souvent une authentification
        node_type_lower = node_type.lower()
        node_name_lower = node_name.lower()
        
        if node_type_lower == 'qemu':
            return True
        if 'server' in node_name_lower or 'pc' in node_name_lower:
            return True
        
        return False
    
    async def _discover_equipment_ip(self, connection: ConsoleConnection) -> IPDiscoveryResult:
        """
        Découvre l'adresse IP d'un équipement via sa console.
        
        Args:
            connection: Informations de connexion console
            
        Returns:
            Résultat de la découverte IP
        """
        start_time = time.time()
        logger.info(f"🔍 Découverte IP pour {connection.node_name} (port {connection.console_port})")
        
        try:
            # Se connecter à la console
            console_client = await self._connect_to_console(connection)
            
            if not console_client:
                return IPDiscoveryResult(
                    node_id=connection.node_id,
                    node_name=connection.node_name,
                    success=False,
                    ip_addresses=[],
                    vlan_info={},
                    dhcp_output="",
                    error_message="Impossible de se connecter à la console",
                    execution_time=time.time() - start_time
                )
            
            # S'authentifier si nécessaire
            if connection.auth_required:
                auth_success = await self._authenticate_console(console_client, connection)
                if not auth_success:
                    console_client.close()
                    return IPDiscoveryResult(
                        node_id=connection.node_id,
                        node_name=connection.node_name,
                        success=False,
                        ip_addresses=[],
                        vlan_info={},
                        dhcp_output="",
                        error_message="Échec de l'authentification console",
                        execution_time=time.time() - start_time
                    )
            
            # Exécuter les commandes de découverte
            ip_result = await self._execute_ip_discovery_commands(console_client, connection)
            
            # Fermer la connexion
            console_client.close()
            
            execution_time = time.time() - start_time
            ip_result.execution_time = execution_time
            
            if ip_result.success:
                logger.info(f"✅ {connection.node_name}: {len(ip_result.ip_addresses)} IPs trouvées")
                for ip in ip_result.ip_addresses:
                    logger.info(f"   🌐 {ip}")
            else:
                logger.warning(f"⚠️ {connection.node_name}: {ip_result.error_message}")
            
            return ip_result
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"❌ {connection.node_name}: Erreur découverte IP - {e}")
            
            return IPDiscoveryResult(
                node_id=connection.node_id,
                node_name=connection.node_name,
                success=False,
                ip_addresses=[],
                vlan_info={},
                dhcp_output="",
                error_message=f"Exception: {str(e)}",
                execution_time=execution_time
            )
    
    async def _connect_to_console(self, connection: ConsoleConnection) -> Optional[telnetlib.Telnet]:
        """
        Se connecte à la console d'un équipement.
        
        Args:
            connection: Informations de connexion
            
        Returns:
            Client Telnet ou None en cas d'échec
        """
        try:
            logger.debug(f"📞 Connexion console {connection.node_name}:{connection.console_port}")
            
            # Créer la connexion Telnet
            tn = telnetlib.Telnet()
            tn.open(connection.console_host, connection.console_port, timeout=self.timeout)
            
            # Attendre un peu pour la stabilisation
            await asyncio.sleep(1)
            
            # Envoyer un Enter pour réveiller la console
            tn.write(b'\r\n')
            await asyncio.sleep(1)
            
            logger.debug(f"✅ Console connectée: {connection.node_name}")
            return tn
            
        except socket.timeout:
            logger.error(f"⏰ Timeout connexion console {connection.node_name}:{connection.console_port}")
            return None
        except ConnectionRefusedError:
            logger.error(f"🚫 Connexion refusée {connection.node_name}:{connection.console_port}")
            return None
        except Exception as e:
            logger.error(f"❌ Erreur connexion console {connection.node_name}: {e}")
            return None
    
    async def _authenticate_console(self, console_client: telnetlib.Telnet, connection: ConsoleConnection) -> bool:
        """
        S'authentifie sur la console si nécessaire.
        
        Args:
            console_client: Client Telnet connecté
            connection: Informations de connexion
            
        Returns:
            True si l'authentification réussit
        """
        try:
            logger.debug(f"🔐 Authentification console {connection.node_name}")
            
            # Lire la sortie initiale
            try:
                output = console_client.read_very_eager().decode('utf-8', errors='ignore')
                await asyncio.sleep(1)
            except:
                output = ""
            
            # Si on voit un prompt de login
            if any(keyword in output.lower() for keyword in ['login:', 'username:', 'user:']):
                logger.debug(f"👤 Envoi username: {self.username}")
                console_client.write(f"{self.username}\r\n".encode())
                await asyncio.sleep(2)
                
                # Attendre le prompt de mot de passe
                try:
                    output = console_client.read_very_eager().decode('utf-8', errors='ignore')
                except:
                    output = ""
                
                if any(keyword in output.lower() for keyword in ['password:', 'passwd:']):
                    logger.debug(f"🔑 Envoi mot de passe")
                    console_client.write(f"{self.password}\r\n".encode())
                    await asyncio.sleep(3)
                    
                    # Vérifier le succès de l'authentification
                    try:
                        output = console_client.read_very_eager().decode('utf-8', errors='ignore')
                        if any(prompt in output for prompt in ['$', '#', '>', 'osboxes@']):
                            logger.info(f"✅ Authentification réussie: {connection.node_name}")
                            return True
                        else:
                            logger.warning(f"⚠️ Authentification échouée: {connection.node_name}")
                            return False
                    except:
                        logger.warning(f"⚠️ Impossible de vérifier l'authentification: {connection.node_name}")
                        return False
            else:
                # Pas de prompt de login, authentification pas nécessaire
                logger.debug(f"ℹ️ Pas d'authentification requise: {connection.node_name}")
                return True
                
        except Exception as e:
            logger.error(f"❌ Erreur authentification {connection.node_name}: {e}")
            return False
        
        return True
    
    async def _execute_ip_discovery_commands(self, console_client: telnetlib.Telnet, connection: ConsoleConnection) -> IPDiscoveryResult:
        """
        Exécute les commandes de découverte IP sur la console.
        
        Args:
            console_client: Client Telnet connecté
            connection: Informations de connexion
            
        Returns:
            Résultat de la découverte IP
        """
        ip_addresses = []
        vlan_info = {}
        dhcp_output = ""
        error_messages = []
        
        try:
            # Récupérer les commandes appropriées pour ce type d'équipement
            commands = self.commands_by_type.get(connection.equipment_type, [])
            
            if not commands:
                # Commandes par défaut selon le type d'équipement détecté
                if connection.equipment_type == EquipmentType.WORKSTATION:
                    commands = [
                        ConsoleCommand("show ip", ">", 5, "Configuration IP VPCS"),
                    ]
                elif connection.equipment_type == EquipmentType.ROUTER:
                    commands = [
                        ConsoleCommand("show ip interface brief", "#", 10, "Interfaces IP Cisco"),
                    ]
                elif connection.equipment_type == EquipmentType.SWITCH:
                    commands = [
                        ConsoleCommand("show ip interface brief", "#", 10, "IPs management switch"),
                    ]
                else:
                    # Fallback pour serveurs ou équipements inconnus
                    commands = [
                        ConsoleCommand("ip", "$", 10, "Configuration IP basique"),
                        ConsoleCommand("ifconfig", "$", 8, "Interfaces réseau"),
                    ]
            
            for command in commands:
                try:
                    logger.debug(f"🔧 Exécution: {command.description} ({connection.node_name})")
                    
                    # Nettoyer le buffer
                    try:
                        console_client.read_very_eager()
                    except:
                        pass
                    
                    # Envoyer la commande
                    console_client.write(f"{command.command}\r\n".encode())
                    await asyncio.sleep(command.timeout)
                    
                    # Lire la réponse
                    try:
                        output = console_client.read_very_eager().decode('utf-8', errors='ignore')
                    except:
                        output = ""
                    
                    if command.command == "dhcp":
                        # Analyser la sortie DHCP pour extraire les IPs
                        dhcp_output += output
                        found_ips = self._extract_ips_from_dhcp_output(output)
                        ip_addresses.extend(found_ips)
                        
                        # Extraire les informations VLAN si présentes
                        vlan_data = self._extract_vlan_info_from_output(output)
                        vlan_info.update(vlan_data)
                        
                        logger.debug(f"📊 DHCP {connection.node_name}: {len(found_ips)} IPs trouvées")
                    
                    elif "show" in command.command or "ip addr" in command.command or "ifconfig" in command.command:
                        # Commandes de vérification - extraire IPs additionnelles
                        additional_ips = self._extract_ips_from_output(output)
                        for ip in additional_ips:
                            if ip not in ip_addresses:
                                ip_addresses.append(ip)
                    
                    elif "route" in command.command:
                        # Commandes de routes - utiliser extraction spécifique pour routes
                        route_ips = self._extract_ips_from_route_output(output)
                        for ip in route_ips:
                            if ip not in ip_addresses:
                                ip_addresses.append(ip)
                    
                except Exception as cmd_error:
                    error_msg = f"Erreur commande '{command.command}': {str(cmd_error)}"
                    error_messages.append(error_msg)
                    logger.warning(f"⚠️ {connection.node_name}: {error_msg}")
            
            # Filtrer les IPs valides
            valid_ips = [ip for ip in ip_addresses if self._is_valid_ip(ip)]
            
            success = len(valid_ips) > 0
            final_error_message = None if success else ("; ".join(error_messages) if error_messages else "Aucune IP trouvée")
            
            return IPDiscoveryResult(
                node_id=connection.node_id,
                node_name=connection.node_name,
                success=success,
                ip_addresses=valid_ips,
                vlan_info=vlan_info,
                dhcp_output=dhcp_output,
                error_message=final_error_message,
                authentication_used=connection.auth_required
            )
            
        except Exception as e:
            return IPDiscoveryResult(
                node_id=connection.node_id,
                node_name=connection.node_name,
                success=False,
                ip_addresses=[],
                vlan_info={},
                dhcp_output=dhcp_output,
                error_message=f"Erreur exécution commandes: {str(e)}",
                authentication_used=connection.auth_required
            )
    
    def _extract_ips_from_dhcp_output(self, output: str) -> List[str]:
        """
        Extrait les adresses IP de la sortie de la commande DHCP.
        
        Args:
            output: Sortie de la commande DHCP
            
        Returns:
            Liste des adresses IP trouvées
        """
        ips = []
        
        # Motifs de recherche pour différents formats testés avec succès
        ip_patterns = [
            # Format VPCS (testé avec succès) : "IP/MASK     : 192.168.20.10/24"
            r'IP/MASK\s*:\s*(\d+\.\d+\.\d+\.\d+)',
            # Format VPCS : "GATEWAY     : 192.168.20.1" 
            r'GATEWAY\s*:\s*(\d+\.\d+\.\d+\.\d+)',
            # Format Cisco (testé avec succès) : "FastEthernet0/0    192.168.41.2    YES"
            r'(\d+\.\d+\.\d+\.\d+)\s+YES',
            # Format Routes Cisco : "C    192.168.x.x"
            r'C\s+(\d+\.\d+\.\d+\.\d+)',
            # Format VLAN Switch : "Vlan12    192.168.12.1"
            r'Vlan\d+\s+(\d+\.\d+\.\d+\.\d+)',
            # Formats spéciaux pour routes connectées (CORRIGÉ pour Routeur-Principal)
            r'(\d+\.\d+\.\d+\.\d+)\s+is directly connected',  # Routes directly connected
            r'(\d+\.\d+\.\d+\.\d+)/\d+\s+is directly connected',  # Network/mask directly connected
            # Pattern amélioré pour extraction d'IP de routes connectées
            r'\b(\d+\.\d+\.\d+\.\d+)\b(?=.*directly connected|.*is subnetted|.*is variably)',
            # Formats génériques DHCP et autres
            r'IP Address[:\s]+(\d+\.\d+\.\d+\.\d+)',  # IP Address: x.x.x.x
            r'inet[:\s]+(\d+\.\d+\.\d+\.\d+)',       # inet x.x.x.x
            r'Address[:\s]+(\d+\.\d+\.\d+\.\d+)',    # Address x.x.x.x
            r'(\d+\.\d+\.\d+\.\d+)/\d+',             # x.x.x.x/24
            r'assigned[:\s]+(\d+\.\d+\.\d+\.\d+)',   # assigned x.x.x.x
        ]
        
        for pattern in ip_patterns:
            matches = re.findall(pattern, output, re.IGNORECASE)
            for match in matches:
                if self._is_valid_ip(match) and match not in ips:
                    ips.append(match)
        
        return ips
    
    def _extract_ips_from_route_output(self, output: str) -> List[str]:
        """
        Extrait les adresses IP spécifiquement des sorties de routes Cisco.
        
        Cette méthode est optimisée pour les sorties 'show ip route' où les IPs
        apparaissent dans des contextes comme "192.168.10.0/24 is subnetted".
        
        Args:
            output: Sortie de commande route Cisco
            
        Returns:
            Liste des adresses IP trouvées dans les routes
        """
        ips = []
        
        # Patterns spécifiques aux routes Cisco pour résoudre le problème Routeur-Principal
        route_patterns = [
            # "192.168.10.0/24 is subnetted, 1 subnets" -> extraire 192.168.10.x
            r'(\d+\.\d+\.\d+\.)0/\d+\s+is\s+subnetted',
            # "C    192.168.10.0/24 is directly connected" -> extraire réseau
            r'C\s+(\d+\.\d+\.\d+)\.\d+/\d+.*directly connected',
            # Pattern général pour toute IP dans les routes
            r'\b(\d+\.\d+\.\d+\.\d+)\b(?=.*connected|.*subnetted)'
        ]
        
        for pattern in route_patterns:
            matches = re.findall(pattern, output, re.IGNORECASE)
            for match in matches:
                # Si c'est un préfixe (ex: "192.168.10."), générer l'IP gateway
                if match.endswith('.'):
                    gateway_ip = f"{match}1"  # Assumer que .1 est la gateway
                    if self._is_valid_ip(gateway_ip):
                        ips.append(gateway_ip)
                else:
                    if self._is_valid_ip(match) and match not in ips:
                        ips.append(match)
        
        # Si aucune IP spécifique trouvée, utiliser pattern général sur toute la sortie
        if not ips:
            general_ip_pattern = r'\b(192\.168\.\d{1,3}\.\d{1,3}|10\.\d{1,3}\.\d{1,3}\.\d{1,3})\b'
            matches = re.findall(general_ip_pattern, output)
            for ip in matches:
                if (self._is_valid_ip(ip) and 
                    ip not in ips and 
                    not ip.endswith('.0') and 
                    not ip.endswith('.255')):
                    ips.append(ip)
        
        return ips
    
    def _extract_ips_from_output(self, output: str) -> List[str]:
        """Extrait les adresses IP de n'importe quelle sortie de commande."""
        # Pattern générique pour toute adresse IP
        ip_pattern = r'\b(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\b'
        matches = re.findall(ip_pattern, output)
        
        valid_ips = []
        for ip in matches:
            if self._is_valid_ip(ip):
                # Exclure les IPs communes non pertinentes
                if not any(exclude in ip for exclude in ['127.0.0.1', '0.0.0.0', '255.255.255']):
                    if ip not in valid_ips:
                        valid_ips.append(ip)
        
        return valid_ips
    
    def _extract_vlan_info_from_output(self, output: str) -> Dict[str, str]:
        """Extrait les informations VLAN de la sortie."""
        vlan_info = {}
        
        # Chercher des informations VLAN
        vlan_patterns = [
            r'VLAN[:\s]*(\d+)',  # VLAN: 10 ou VLAN 10
            r'vlan[:\s]*(\d+)',  # vlan: 10 ou vlan 10
        ]
        
        for pattern in vlan_patterns:
            matches = re.findall(pattern, output, re.IGNORECASE)
            for match in matches:
                vlan_info[f"vlan_{match}"] = f"VLAN {match} détecté"
        
        return vlan_info
    
    def _is_valid_ip(self, ip: str) -> bool:
        """Vérifie si une chaîne est une adresse IP valide."""
        try:
            import ipaddress
            ipaddress.ip_address(ip)
            return True
        except ValueError:
            return False
    
    def get_discovery_summary(self, results: Dict[str, IPDiscoveryResult]) -> Dict[str, Any]:
        """
        Génère un résumé de la découverte IP.
        
        Args:
            results: Résultats de découverte IP
            
        Returns:
            Résumé de la découverte
        """
        if not results:
            return {"error": "Aucun résultat de découverte"}
        
        successful_discoveries = sum(1 for r in results.values() if r.success)
        total_equipment = len(results)
        total_ips = sum(len(r.ip_addresses) for r in results.values())
        authenticated_equipment = sum(1 for r in results.values() if r.authentication_used)
        
        # Grouper par type d'équipement
        by_equipment_type = {}
        for result in results.values():
            # Déterminer le type à partir du nom
            if any(keyword in result.node_name.lower() for keyword in ['router', 'rt']):
                eq_type = "routers"
            elif any(keyword in result.node_name.lower() for keyword in ['switch', 'sw']):
                eq_type = "switches"
            elif any(keyword in result.node_name.lower() for keyword in ['server', 'srv']):
                eq_type = "servers"
            elif any(keyword in result.node_name.lower() for keyword in ['pc', 'client', 'workstation']):
                eq_type = "workstations"
            else:
                eq_type = "unknown"
            
            if eq_type not in by_equipment_type:
                by_equipment_type[eq_type] = {"count": 0, "ips_found": 0}
            
            by_equipment_type[eq_type]["count"] += 1
            by_equipment_type[eq_type]["ips_found"] += len(result.ip_addresses)
        
        # Erreurs rencontrées
        errors = []
        for result in results.values():
            if not result.success and result.error_message:
                errors.append({
                    "equipment": result.node_name,
                    "error": result.error_message
                })
        
        return {
            "total_equipment": total_equipment,
            "successful_discoveries": successful_discoveries,
            "success_rate": (successful_discoveries / total_equipment) * 100,
            "total_ips_found": total_ips,
            "authenticated_equipment": authenticated_equipment,
            "equipment_breakdown": by_equipment_type,
            "errors_encountered": len(errors),
            "error_details": errors[:5],  # Premières 5 erreurs
            "avg_execution_time": sum(r.execution_time for r in results.values()) / len(results)
        }

# Fonction utilitaire pour créer un découvreur
def create_ip_discovery_service(username: str = "osboxes", password: str = "osboxes.org") -> ConsoleIPDiscovery:
    """Crée et retourne un service de découverte IP configuré."""
    return ConsoleIPDiscovery(username=username, password=password)