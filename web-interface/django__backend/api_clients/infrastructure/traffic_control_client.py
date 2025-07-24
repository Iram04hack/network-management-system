# api_clients/infrastructure/traffic_control_client.py
from ..base import BaseAPIClient
import logging
import os
import subprocess
from typing import Dict, Any, Optional, List, Union

logger = logging.getLogger(__name__)

class TrafficControlClient(BaseAPIClient):
    """Client pour interagir avec les fonctionnalités de Traffic Control (tc) de Linux"""
    
    def __init__(self, base_url: Optional[str] = None, sudo_required: bool = True,
                 username: Optional[str] = None, password: Optional[str] = None, 
                 verify_ssl: bool = True, timeout: int = 10):
        """
        Initialise le client Traffic Control.
        
        Args:
            base_url: URL de base de l'API (si disponible)
            sudo_required: Si True, les commandes tc seront exécutées avec sudo
            username: Nom d'utilisateur pour l'authentification API
            password: Mot de passe pour l'authentification API
            verify_ssl: Vérifier les certificats SSL
            timeout: Délai d'attente en secondes pour les requêtes
        """
        self.api_available = bool(base_url)
        self.sudo_required = sudo_required
        
        if self.api_available:
            super().__init__(base_url, username, password, None, verify_ssl, timeout)
    
    def _execute_command(self, command: List[str]) -> Dict[str, Any]:
        """
        Exécute une commande tc.
        
        Args:
            command: Liste des arguments de la commande
            
        Returns:
            Résultat de la commande
        """
        full_command = ["tc"]
        
        if self.sudo_required:
            full_command.insert(0, "sudo")
            
        full_command.extend(command)
        
        try:
            result = subprocess.run(
                full_command,
                capture_output=True,
                text=True,
                check=True
            )
            
            return {
                "success": True,
                "output": result.stdout.strip(),
                "command": " ".join(full_command)
            }
        except subprocess.CalledProcessError as e:
            logger.error(f"Erreur lors de l'exécution de la commande {' '.join(full_command)}: {e}")
            return {
                "success": False,
                "error": str(e),
                "stderr": e.stderr.strip() if e.stderr else "",
                "command": " ".join(full_command)
            }
        except Exception as e:
            logger.error(f"Exception lors de l'exécution de la commande {' '.join(full_command)}: {e}")
            return {"success": False, "error": str(e), "command": " ".join(full_command)}
    
    def test_connection(self) -> bool:
        """
        Vérifie si les commandes tc peuvent être exécutées.
        
        Returns:
            True si les commandes tc peuvent être exécutées, False sinon
        """
        if not self.api_available:
            result = self._execute_command(["help"])
            return result.get("success", False)
        
        response = self.get("status")
        return response.get("success", False)
    
    def get_interface_config(self, interface: str) -> Dict[str, Any]:
        """
        Récupère la configuration Traffic Control d'une interface.
        
        Args:
            interface: Nom de l'interface réseau
            
        Returns:
            Configuration Traffic Control de l'interface
        """
        if not self.api_available:
            qdisc_result = self._execute_command(["qdisc", "show", "dev", interface])
            class_result = self._execute_command(["class", "show", "dev", interface])
            filter_result = self._execute_command(["filter", "show", "dev", interface])
            
            return {
                "success": qdisc_result.get("success", False) and class_result.get("success", False),
                "qdisc": qdisc_result.get("output", ""),
                "class": class_result.get("output", ""),
                "filter": filter_result.get("output", ""),
                "interface": interface
            }
        
        return self.get(f"interface/{interface}")
    
    def clear_interface(self, interface: str) -> Dict[str, Any]:
        """
        Supprime toutes les configurations Traffic Control d'une interface.
        
        Args:
            interface: Nom de l'interface réseau
            
        Returns:
            Résultat de l'opération
        """
        if not self.api_available:
            return self._execute_command(["qdisc", "del", "dev", interface, "root"])
        
        return self.delete(f"interface/{interface}")
    
    def set_bandwidth_limit(self, interface: str, rate_limit: str, burst: Optional[str] = None) -> Dict[str, Any]:
        """
        Limite la bande passante d'une interface.
        
        Args:
            interface: Nom de l'interface réseau
            rate_limit: Limite de débit (ex: "1mbit")
            burst: Taille de burst (ex: "15k")
            
        Returns:
            Résultat de l'opération
        """
        if not self.api_available:
            # Supprimer la configuration existante
            self._execute_command(["qdisc", "del", "dev", interface, "root"])
            
            # Construire la commande
            command = ["qdisc", "add", "dev", interface, "root", "tbf", "rate", rate_limit]
            
            if burst:
                command.extend(["burst", burst])
                
            command.extend(["latency", "50ms"])
            
            return self._execute_command(command)
        
        json_data = {"rate_limit": rate_limit}
        if burst:
            json_data["burst"] = burst
            
        return self.post(f"interface/{interface}/bandwidth", json_data=json_data)
    
    def set_traffic_prioritization(self, interface: str, classes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Configure la priorisation du trafic sur une interface.
        
        Args:
            interface: Nom de l'interface réseau
            classes: Liste des classes de trafic avec leurs propriétés
                (ex: [{"id": "1:10", "rate": "10mbit", "priority": 1}, ...])
            
        Returns:
            Résultat de l'opération
        """
        if not self.api_available:
            # Supprimer la configuration existante
            self._execute_command(["qdisc", "del", "dev", interface, "root"])
            
            # Ajouter le qdisc HTB (Hierarchical Token Bucket)
            qdisc_result = self._execute_command([
                "qdisc", "add", "dev", interface, "root", "handle", "1:", "htb", "default", "99"
            ])
            
            if not qdisc_result.get("success", False):
                return qdisc_result
            
            # Ajouter la classe racine
            root_class_result = self._execute_command([
                "class", "add", "dev", interface, "parent", "1:", "classid", "1:1", 
                "htb", "rate", "1000mbit"  # Classe racine avec débit élevé
            ])
            
            if not root_class_result.get("success", False):
                return root_class_result
            
            # Ajouter les classes spécifiées
            class_results = []
            for cls in classes:
                class_id = cls.get("id", "")
                rate = cls.get("rate", "")
                ceil = cls.get("ceil", rate)  # Par défaut, ceil = rate
                prio = cls.get("priority", "0")
                
                result = self._execute_command([
                    "class", "add", "dev", interface, "parent", "1:1", "classid", class_id,
                    "htb", "rate", rate, "ceil", ceil, "prio", str(prio)
                ])
                
                class_results.append(result)
                
                if not result.get("success", False):
                    return result
            
            # Ajouter la classe par défaut
            default_class_result = self._execute_command([
                "class", "add", "dev", interface, "parent", "1:1", "classid", "1:99",
                "htb", "rate", "1mbit", "ceil", "10mbit", "prio", "9"
            ])
            
            return {
                "success": all(result.get("success", False) for result in class_results + [default_class_result]),
                "interface": interface,
                "classes": [cls.get("id", "") for cls in classes],
                "message": "Configuration de priorisation du trafic appliquée avec succès"
            }
        
        return self.post(f"interface/{interface}/prioritization", json_data={"classes": classes})
    
    def add_traffic_filter(self, interface: str, target_class: str, protocol: str = "ip", 
                          src_ip: Optional[str] = None, dst_ip: Optional[str] = None,
                          src_port: Optional[int] = None, dst_port: Optional[int] = None,
                          priority: int = 1) -> Dict[str, Any]:
        """
        Ajoute un filtre de trafic sur une interface.
        
        Args:
            interface: Nom de l'interface réseau
            target_class: ID de la classe cible (ex: "1:10")
            protocol: Protocole (ip, tcp, udp, etc.)
            src_ip: Adresse IP source (avec masque optionnel, ex: "192.168.1.0/24")
            dst_ip: Adresse IP destination
            src_port: Port source
            dst_port: Port destination
            priority: Priorité du filtre
            
        Returns:
            Résultat de l'opération
        """
        if not self.api_available:
            # Construire la commande de base
            command = [
                "filter", "add", "dev", interface, "protocol", protocol,
                "parent", "1:", "prio", str(priority), "u32"
            ]
            
            # Construire les conditions de correspondance
            match_conditions = []
            
            if src_ip:
                # Convertir l'adresse IP en format u32
                if "/" in src_ip:
                    ip, mask = src_ip.split("/")
                    match_conditions.extend(["match", "ip", "src", ip, "mask", mask])
                else:
                    match_conditions.extend(["match", "ip", "src", src_ip])
                    
            if dst_ip:
                if "/" in dst_ip:
                    ip, mask = dst_ip.split("/")
                    match_conditions.extend(["match", "ip", "dst", ip, "mask", mask])
                else:
                    match_conditions.extend(["match", "ip", "dst", dst_ip])
            
            # Pour les ports, nous avons besoin de spécifier le protocole TCP/UDP
            if (src_port is not None or dst_port is not None) and protocol.lower() in ("tcp", "udp"):
                if src_port is not None:
                    match_conditions.extend([
                        "match", protocol.lower(), "sport", str(src_port), "0xffff"
                    ])
                
                if dst_port is not None:
                    match_conditions.extend([
                        "match", protocol.lower(), "dport", str(dst_port), "0xffff"
                    ])
            
            # Ajouter les conditions de correspondance à la commande
            command.extend(match_conditions)
            
            # Ajouter l'action (flowid = classe cible)
            command.extend(["flowid", target_class])
            
            return self._execute_command(command)
        
        # Construire le payload pour l'API
        json_data = {
            "target_class": target_class,
            "protocol": protocol,
            "priority": priority
        }
        
        if src_ip:
            json_data["src_ip"] = src_ip
        if dst_ip:
            json_data["dst_ip"] = dst_ip
        if src_port is not None:
            json_data["src_port"] = src_port
        if dst_port is not None:
            json_data["dst_port"] = dst_port
            
        return self.post(f"interface/{interface}/filter", json_data=json_data)
    
    def get_interfaces(self) -> Dict[str, Any]:
        """
        Récupère la liste des interfaces réseau disponibles.
        
        Returns:
            Liste des interfaces réseau
        """
        if not self.api_available:
            try:
                # Utiliser la commande ip pour lister les interfaces
                result = subprocess.run(
                    ["ip", "link", "show"],
                    capture_output=True,
                    text=True,
                    check=True
                )
                
                # Parser la sortie pour extraire les noms d'interfaces
                interfaces = []
                lines = result.stdout.strip().split('\n')
                for line in lines:
                    if ': ' in line and not line.startswith(' '):
                        # Format: idx: interface_name: ...
                        parts = line.split(': ')
                        if len(parts) >= 2:
                            interfaces.append(parts[1])
                
                return {"success": True, "interfaces": interfaces}
            except Exception as e:
                logger.error(f"Erreur lors de la récupération des interfaces réseau: {e}")
                return {"success": False, "error": str(e)}
        
        return self.get("interfaces") 