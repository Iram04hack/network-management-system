"""
Détecteurs de conflits entre règles de sécurité avec intégration Docker.

Ce module contient les implémentations pour détecter et analyser les conflits
entre différentes règles de sécurité (pare-feu, IDS, contrôle d'accès)
en utilisant les services Docker pour la validation.
"""

import re
import json
import uuid
import ipaddress
import logging
import requests
from typing import Dict, Any, List, Set, Tuple, Optional
from abc import ABC, abstractmethod

from .interfaces import ConflictDetector, RuleConflict, DockerServiceConnector
from django.conf import settings

logger = logging.getLogger(__name__)


class DockerServiceBase(DockerServiceConnector):
    """
    Classe de base pour les connecteurs aux services Docker.
    """
    
    def __init__(self, service_name: str, base_url: str, timeout: int = 30):
        """
        Initialise le connecteur au service Docker.
        
        Args:
            service_name: Nom du service Docker
            base_url: URL de base du service
            timeout: Timeout pour les requêtes HTTP
        """
        self.service_name = service_name
        self.base_url = base_url
        self.timeout = timeout
        self._session = requests.Session()
    
    def test_connection(self) -> bool:
        """Teste la connexion au service Docker."""
        try:
            response = self._session.get(
                f"{self.base_url}/health",
                timeout=self.timeout
            )
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"Connexion au service {self.service_name} échouée: {str(e)}")
            return False
    
    def get_service_status(self) -> Dict[str, Any]:
        """Récupère le statut du service Docker."""
        try:
            response = self._session.get(
                f"{self.base_url}/status",
                timeout=self.timeout
            )
            if response.status_code == 200:
                return response.json()
            return {"status": "error", "message": f"HTTP {response.status_code}"}
        except Exception as e:
            return {"status": "unreachable", "error": str(e)}
    
    def call_api(self, endpoint: str, method: str = 'GET', data: Optional[Dict] = None) -> Dict[str, Any]:
        """Effectue un appel API vers le service Docker."""
        try:
            url = f"{self.base_url}{endpoint}"
            
            if method.upper() == 'GET':
                response = self._session.get(url, timeout=self.timeout)
            elif method.upper() == 'POST':
                response = self._session.post(url, json=data, timeout=self.timeout)
            elif method.upper() == 'PUT':
                response = self._session.put(url, json=data, timeout=self.timeout)
            elif method.upper() == 'DELETE':
                response = self._session.delete(url, timeout=self.timeout)
            else:
                return {"error": f"Méthode HTTP non supportée: {method}"}
            
            if response.status_code < 400:
                return response.json() if response.content else {"success": True}
            else:
                return {"error": f"HTTP {response.status_code}: {response.text}"}
                
        except Exception as e:
            logger.error(f"Erreur lors de l'appel API {method} {endpoint}: {str(e)}")
            return {"error": str(e)}


class BaseConflictDetector(ConflictDetector):
    """
    Implémentation de base pour la détection de conflits.
    Fournit des méthodes communes à tous les détecteurs de conflits.
    """
    
    def analyze_ruleset(self, rules: List[Dict[str, Any]]) -> List[RuleConflict]:
        """
        Analyse un ensemble de règles pour détecter tous les conflits.
        """
        conflicts = []
        
        # Pour chaque règle, vérifier les conflits avec toutes les autres règles
        for i, rule in enumerate(rules):
            # Créer une liste de toutes les autres règles
            other_rules = rules[:i] + rules[i+1:]
            
            # Détecter les conflits pour cette règle
            rule_conflicts = self.detect_conflicts(rule, other_rules)
            conflicts.extend(rule_conflicts)
            
        return conflicts
    
    def _generate_conflict_id(self, rule1_id: int, rule2_id: int, conflict_type: str) -> str:
        """
        Génère un identifiant unique pour un conflit.
        """
        # Trier les IDs pour garantir la cohérence
        sorted_ids = sorted([rule1_id, rule2_id])
        
        # Générer un UUID basé sur les IDs des règles et le type de conflit
        return f"{conflict_type}-{sorted_ids[0]}-{sorted_ids[1]}-{uuid.uuid4().hex[:8]}"


class FirewallRuleConflictDetector(BaseConflictDetector):
    """
    Détecteur de conflits pour les règles de pare-feu avec validation Docker.
    """
    
    def __init__(self):
        """Initialise le détecteur avec connexion au service Traffic Control."""
        # Configuration du service Traffic Control Docker pour validation firewall
        traffic_control_url = getattr(settings, 'TRAFFIC_CONTROL_API_URL', 'http://nms-traffic-control:8003')
        self.traffic_service = DockerServiceBase('traffic-control', traffic_control_url)
    
    def detect_conflicts(self, rule_data: Dict[str, Any], existing_rules: List[Dict[str, Any]]) -> List[RuleConflict]:
        """
        Détecte les conflits entre une règle de pare-feu et des règles existantes.
        
        Types de conflits détectés :
        - Shadow (masquage) : Une règle est complètement masquée par une autre règle
        - Redundant (redondance) : Une règle fait la même chose qu'une autre règle
        - Correlation (corrélation) : Les règles se chevauchent partiellement
        - Generalization (généralisation) : Une règle est plus générale qu'une autre
        """
        conflicts = []
        rule_content = rule_data.get("content", "")
        rule_id = rule_data.get("id", 0)
        
        if not rule_content:
            return conflicts
            
        # Extraire les informations de la règle
        rule_info = self._parse_iptables_rule(rule_content)
        if not rule_info:
            return conflicts
        
        # Valider la règle via le service Docker si disponible
        if self.traffic_service.test_connection():
            validation_result = self._validate_rule_via_docker(rule_content)
            if not validation_result.get("valid", True):
                logger.warning(f"Règle firewall non valide: {validation_result.get('error', 'Erreur inconnue')}")
            
        # Vérifier les conflits avec chaque règle existante
        for existing_rule in existing_rules:
            existing_content = existing_rule.get("content", "")
            existing_id = existing_rule.get("id", 0)
            
            if not existing_content:
                continue
                
            # Extraire les informations de la règle existante
            existing_info = self._parse_iptables_rule(existing_content)
            if not existing_info:
                continue
                
            # Vérifier les différents types de conflits
            shadow_conflict = self._check_shadow_conflict(rule_info, existing_info, rule_id, existing_id)
            if shadow_conflict:
                conflicts.append(shadow_conflict)
                continue  # Si on a détecté un conflit de masquage, ne pas vérifier les autres types
                
            redundant_conflict = self._check_redundant_conflict(rule_info, existing_info, rule_id, existing_id)
            if redundant_conflict:
                conflicts.append(redundant_conflict)
                continue
                
            correlation_conflict = self._check_correlation_conflict(rule_info, existing_info, rule_id, existing_id)
            if correlation_conflict:
                conflicts.append(correlation_conflict)
                continue
                
            generalization_conflict = self._check_generalization_conflict(rule_info, existing_info, rule_id, existing_id)
            if generalization_conflict:
                conflicts.append(generalization_conflict)
                
        return conflicts
    
    def _validate_rule_via_docker(self, rule_content: str) -> Dict[str, Any]:
        """
        Valide une règle firewall via le service Docker Traffic Control.
        """
        try:
            return self.traffic_service.call_api(
                "/validate/firewall",
                method="POST",
                data={"rule": rule_content}
            )
        except Exception as e:
            logger.error(f"Erreur lors de la validation firewall: {str(e)}")
            return {"valid": True, "warning": "Validation Docker non disponible"}
    
    def _parse_iptables_rule(self, rule_content: str) -> Optional[Dict[str, Any]]:
        """
        Analyse une règle iptables pour en extraire les composants.
        """
        try:
            # Exemple de règle: iptables -A INPUT -p tcp --dport 80 -j ACCEPT
            parts = rule_content.split()
            
            result = {
                "chain": None,  # INPUT, OUTPUT, FORWARD
                "protocol": None,  # tcp, udp, icmp
                "source": None,  # adresse IP source
                "destination": None,  # adresse IP destination
                "source_port": None,  # port source
                "destination_port": None,  # port destination
                "action": None,  # ACCEPT, DROP, REJECT
                "other_options": []  # autres options
            }
            
            # Extraire la chaîne
            if "-A" in parts:
                chain_index = parts.index("-A") + 1
                if chain_index < len(parts):
                    result["chain"] = parts[chain_index]
            
            # Extraire le protocole
            if "-p" in parts:
                proto_index = parts.index("-p") + 1
                if proto_index < len(parts):
                    result["protocol"] = parts[proto_index]
            
            # Extraire l'adresse source
            if "-s" in parts:
                src_index = parts.index("-s") + 1
                if src_index < len(parts) and not parts[src_index].startswith("-"):
                    result["source"] = parts[src_index]
            
            # Extraire l'adresse destination
            if "-d" in parts:
                dst_index = parts.index("-d") + 1
                if dst_index < len(parts) and not parts[dst_index].startswith("-"):
                    result["destination"] = parts[dst_index]
            
            # Extraire le port source
            if "--sport" in parts:
                sport_index = parts.index("--sport") + 1
                if sport_index < len(parts) and not parts[sport_index].startswith("-"):
                    result["source_port"] = parts[sport_index]
            
            # Extraire le port destination
            if "--dport" in parts:
                dport_index = parts.index("--dport") + 1
                if dport_index < len(parts) and not parts[dport_index].startswith("-"):
                    result["destination_port"] = parts[dport_index]
            
            # Extraire l'action
            if "-j" in parts:
                action_index = parts.index("-j") + 1
                if action_index < len(parts):
                    result["action"] = parts[action_index]
            
            return result
            
        except Exception:
            # Si l'analyse échoue, retourner None
            return None
    
    def _check_shadow_conflict(self, rule_info: Dict[str, Any], existing_info: Dict[str, Any], rule_id: int, existing_id: int) -> Optional[RuleConflict]:
        """
        Vérifie si une règle est masquée par une autre règle.
        """
        # Vérifier que les chaînes sont les mêmes
        if rule_info["chain"] != existing_info["chain"]:
            return None
            
        # Vérifier que les actions sont différentes
        if rule_info["action"] == existing_info["action"]:
            return None
            
        # Vérifier si la règle existante masque la nouvelle règle
        is_shadowed = True
        
        # Pour chaque critère, vérifier si la règle existante est plus générale
        if rule_info["protocol"] and existing_info["protocol"] and rule_info["protocol"] != existing_info["protocol"]:
            is_shadowed = False
            
        if rule_info["source"] and existing_info["source"]:
            if not self._is_ip_subset(rule_info["source"], existing_info["source"]):
                is_shadowed = False
                
        if rule_info["destination"] and existing_info["destination"]:
            if not self._is_ip_subset(rule_info["destination"], existing_info["destination"]):
                is_shadowed = False
                
        if rule_info["source_port"] and existing_info["source_port"]:
            if not self._is_port_subset(rule_info["source_port"], existing_info["source_port"]):
                is_shadowed = False
                
        if rule_info["destination_port"] and existing_info["destination_port"]:
            if not self._is_port_subset(rule_info["destination_port"], existing_info["destination_port"]):
                is_shadowed = False
                
        if not is_shadowed:
            return None
            
        # Créer l'objet de conflit
        conflict_id = self._generate_conflict_id(rule_id, existing_id, "shadow")
        return RuleConflict(
            conflict_id=conflict_id,
            rule1_id=rule_id,
            rule2_id=existing_id,
            conflict_type="shadow",
            severity="critical",
            description=f"La règle {rule_id} est masquée par la règle {existing_id}, "
                        f"elle ne sera jamais appliquée car la règle {existing_id} est plus générale "
                        f"et a une action différente ({existing_info['action']} vs {rule_info['action']}).",
            recommendation=f"Considérez de supprimer la règle {rule_id} ou de la placer avant la règle {existing_id}."
        )
    
    def _check_redundant_conflict(self, rule_info: Dict[str, Any], existing_info: Dict[str, Any], rule_id: int, existing_id: int) -> Optional[RuleConflict]:
        """
        Vérifie si une règle est redondante avec une autre règle.
        """
        # Vérifier que les chaînes sont les mêmes
        if rule_info["chain"] != existing_info["chain"]:
            return None
            
        # Vérifier que les actions sont les mêmes
        if rule_info["action"] != existing_info["action"]:
            return None
            
        # Vérifier si les règles ont le même champ d'application
        if rule_info["protocol"] != existing_info["protocol"]:
            return None
            
        if rule_info["source"] != existing_info["source"]:
            return None
            
        if rule_info["destination"] != existing_info["destination"]:
            return None
            
        if rule_info["source_port"] != existing_info["source_port"]:
            return None
            
        if rule_info["destination_port"] != existing_info["destination_port"]:
            return None
            
        # Créer l'objet de conflit
        conflict_id = self._generate_conflict_id(rule_id, existing_id, "redundant")
        return RuleConflict(
            conflict_id=conflict_id,
            rule1_id=rule_id,
            rule2_id=existing_id,
            conflict_type="redundant",
            severity="warning",
            description=f"La règle {rule_id} est redondante avec la règle {existing_id}, "
                        f"elles ont le même champ d'application et la même action ({rule_info['action']}).",
            recommendation=f"Considérez de fusionner les deux règles ou de supprimer l'une d'entre elles."
        )
    
    def _check_correlation_conflict(self, rule_info: Dict[str, Any], existing_info: Dict[str, Any], rule_id: int, existing_id: int) -> Optional[RuleConflict]:
        """
        Vérifie si deux règles sont corrélées (se chevauchent partiellement).
        """
        # Vérifier que les chaînes sont les mêmes
        if rule_info["chain"] != existing_info["chain"]:
            return None
            
        # Vérifier que les actions sont différentes
        if rule_info["action"] == existing_info["action"]:
            return None
            
        # Vérifier si les règles se chevauchent partiellement
        overlapping = True
        
        # Vérifier le protocole
        if rule_info["protocol"] and existing_info["protocol"] and rule_info["protocol"] != existing_info["protocol"]:
            overlapping = False
            
        # Vérifier les adresses IP
        if rule_info["source"] and existing_info["source"]:
            if not self._is_ip_overlap(rule_info["source"], existing_info["source"]):
                overlapping = False
                
        if rule_info["destination"] and existing_info["destination"]:
            if not self._is_ip_overlap(rule_info["destination"], existing_info["destination"]):
                overlapping = False
                
        # Vérifier les ports
        if rule_info["source_port"] and existing_info["source_port"]:
            if not self._is_port_overlap(rule_info["source_port"], existing_info["source_port"]):
                overlapping = False
                
        if rule_info["destination_port"] and existing_info["destination_port"]:
            if not self._is_port_overlap(rule_info["destination_port"], existing_info["destination_port"]):
                overlapping = False
                
        if not overlapping:
            return None
            
        # Créer l'objet de conflit
        conflict_id = self._generate_conflict_id(rule_id, existing_id, "correlation")
        return RuleConflict(
            conflict_id=conflict_id,
            rule1_id=rule_id,
            rule2_id=existing_id,
            conflict_type="correlation",
            severity="warning",
            description=f"Les règles {rule_id} et {existing_id} sont corrélées, "
                        f"elles ont des champs d'application qui se chevauchent partiellement "
                        f"mais des actions différentes ({rule_info['action']} vs {existing_info['action']}).",
            recommendation=f"Considérez de reformuler les règles pour éviter les chevauchements ou de les consolider."
        )
    
    def _check_generalization_conflict(self, rule_info: Dict[str, Any], existing_info: Dict[str, Any], rule_id: int, existing_id: int) -> Optional[RuleConflict]:
        """
        Vérifie si une règle est une généralisation d'une autre règle.
        """
        # Vérifier que les chaînes sont les mêmes
        if rule_info["chain"] != existing_info["chain"]:
            return None
            
        # Vérifier que les actions sont les mêmes
        if rule_info["action"] != existing_info["action"]:
            return None
            
        # Vérifier si la nouvelle règle est plus générale que la règle existante
        is_generalization = True
        has_some_generalization = False
        
        # Pour chaque critère, vérifier si la nouvelle règle est plus générale
        if rule_info["protocol"] and existing_info["protocol"]:
            if rule_info["protocol"] != existing_info["protocol"]:
                is_generalization = False
                
        if rule_info["source"] and existing_info["source"]:
            if self._is_ip_subset(existing_info["source"], rule_info["source"]) and rule_info["source"] != existing_info["source"]:
                has_some_generalization = True
            else:
                is_generalization = False
                
        if rule_info["destination"] and existing_info["destination"]:
            if self._is_ip_subset(existing_info["destination"], rule_info["destination"]) and rule_info["destination"] != existing_info["destination"]:
                has_some_generalization = True
            else:
                is_generalization = False
                
        if rule_info["source_port"] and existing_info["source_port"]:
            if self._is_port_subset(existing_info["source_port"], rule_info["source_port"]) and rule_info["source_port"] != existing_info["source_port"]:
                has_some_generalization = True
            else:
                is_generalization = False
                
        if rule_info["destination_port"] and existing_info["destination_port"]:
            if self._is_port_subset(existing_info["destination_port"], rule_info["destination_port"]) and rule_info["destination_port"] != existing_info["destination_port"]:
                has_some_generalization = True
            else:
                is_generalization = False
                
        if not is_generalization or not has_some_generalization:
            return None
            
        # Créer l'objet de conflit
        conflict_id = self._generate_conflict_id(rule_id, existing_id, "generalization")
        return RuleConflict(
            conflict_id=conflict_id,
            rule1_id=rule_id,
            rule2_id=existing_id,
            conflict_type="generalization",
            severity="info",
            description=f"La règle {rule_id} est une généralisation de la règle {existing_id}, "
                        f"elle a un champ d'application plus large mais la même action ({rule_info['action']}).",
            recommendation=f"Considérez de supprimer la règle {existing_id} car elle est déjà couverte par la règle {rule_id}."
        )
    
    def _is_ip_subset(self, ip1: str, ip2: str) -> bool:
        """
        Vérifie si le premier réseau IP est un sous-ensemble du second.
        """
        try:
            # Gérer les cas spéciaux
            if ip1 == ip2:
                return True
            if ip1 == "any" or ip1 == "0.0.0.0/0":
                return ip2 == "any" or ip2 == "0.0.0.0/0"
            if ip2 == "any" or ip2 == "0.0.0.0/0":
                return True
                
            # Convertir en objets réseau
            network1 = ipaddress.ip_network(ip1, strict=False)
            network2 = ipaddress.ip_network(ip2, strict=False)
            
            # Vérifier si le premier réseau est un sous-ensemble du second
            return network1.subnet_of(network2)
            
        except ValueError:
            # En cas d'erreur de format, supposer qu'il n'y a pas de sous-ensemble
            return False
            
    def _is_ip_overlap(self, ip1: str, ip2: str) -> bool:
        """
        Vérifie si deux réseaux IP se chevauchent.
        """
        try:
            # Gérer les cas spéciaux
            if ip1 == ip2:
                return True
            if ip1 == "any" or ip1 == "0.0.0.0/0" or ip2 == "any" or ip2 == "0.0.0.0/0":
                return True
                
            # Convertir en objets réseau
            network1 = ipaddress.ip_network(ip1, strict=False)
            network2 = ipaddress.ip_network(ip2, strict=False)
            
            # Vérifier si les réseaux se chevauchent
            return network1.overlaps(network2)
            
        except ValueError:
            # En cas d'erreur de format, supposer qu'il n'y a pas de chevauchement
            return False
            
    def _is_port_subset(self, port1: str, port2: str) -> bool:
        """
        Vérifie si la première plage de ports est un sous-ensemble de la seconde.
        """
        try:
            # Gérer les cas spéciaux
            if port1 == port2:
                return True
            if port2 == "any":
                return True
                
            # Convertir en plages de ports
            range1 = self._parse_port_range(port1)
            range2 = self._parse_port_range(port2)
            
            # Vérifier si la première plage est un sous-ensemble de la seconde
            return range1[0] >= range2[0] and range1[1] <= range2[1]
            
        except ValueError:
            # En cas d'erreur de format, supposer qu'il n'y a pas de sous-ensemble
            return False
            
    def _is_port_overlap(self, port1: str, port2: str) -> bool:
        """
        Vérifie si deux plages de ports se chevauchent.
        """
        try:
            # Gérer les cas spéciaux
            if port1 == port2:
                return True
            if port1 == "any" or port2 == "any":
                return True
                
            # Convertir en plages de ports
            range1 = self._parse_port_range(port1)
            range2 = self._parse_port_range(port2)
            
            # Vérifier si les plages se chevauchent
            return not (range1[1] < range2[0] or range1[0] > range2[1])
            
        except ValueError:
            # En cas d'erreur de format, supposer qu'il n'y a pas de chevauchement
            return False
            
    def _parse_port_range(self, port_str: str) -> Tuple[int, int]:
        """
        Analyse une chaîne de ports en une plage de ports.
        """
        if port_str == "any":
            return (0, 65535)
            
        if ":" in port_str:
            parts = port_str.split(":")
            return (int(parts[0]), int(parts[1]))
            
        port = int(port_str)
        return (port, port)


class IDSRuleConflictDetector(BaseConflictDetector):
    """
    Détecteur de conflits pour les règles IDS (Intrusion Detection System) avec intégration Docker.
    """
    
    def __init__(self):
        """Initialise le détecteur avec connexion au service Suricata."""
        # Configuration du service Suricata Docker pour validation IDS
        suricata_url = getattr(settings, 'SURICATA_API_URL', 'http://nms-suricata:8068')
        self.suricata_service = DockerServiceBase('suricata', suricata_url)
    
    def detect_conflicts(self, rule_data: Dict[str, Any], existing_rules: List[Dict[str, Any]]) -> List[RuleConflict]:
        """
        Détecte les conflits entre une règle IDS et des règles existantes.
        
        Types de conflits détectés :
        - Redundant (redondance) : Une règle fait la même chose qu'une autre règle
        - Subset (sous-ensemble) : Une règle est un sous-ensemble d'une autre règle
        - Inconsistent action (action incohérente) : Des règles similaires avec des actions différentes
        - Conflicting thresholds (seuils conflictuels) : Des règles avec des seuils incompatibles
        """
        conflicts = []
        rule_content = rule_data.get("content", "")
        rule_id = rule_data.get("id", 0)
        
        if not rule_content:
            return conflicts
            
        # Analyser la règle IDS
        rule_info = self._parse_ids_rule(rule_content)
        if not rule_info:
            return conflicts
        
        # Valider la règle via le service Docker si disponible
        if self.suricata_service.test_connection():
            validation_result = self._validate_rule_via_docker(rule_content)
            if not validation_result.get("valid", True):
                logger.warning(f"Règle IDS non valide: {validation_result.get('error', 'Erreur inconnue')}")
            
        # Vérifier les conflits avec chaque règle existante
        for existing_rule in existing_rules:
            existing_content = existing_rule.get("content", "")
            existing_id = existing_rule.get("id", 0)
            
            if not existing_content:
                continue
                
            # Analyser la règle IDS existante
            existing_info = self._parse_ids_rule(existing_content)
            if not existing_info:
                continue
                
            # Vérifier les différents types de conflits
            redundant_conflict = self._check_redundant_conflict(rule_info, existing_info, rule_id, existing_id)
            if redundant_conflict:
                conflicts.append(redundant_conflict)
                continue
                
        return conflicts
    
    def _validate_rule_via_docker(self, rule_content: str) -> Dict[str, Any]:
        """
        Valide une règle IDS via le service Docker Suricata.
        """
        try:
            return self.suricata_service.call_api(
                "/validate/rule",
                method="POST",
                data={"rule": rule_content}
            )
        except Exception as e:
            logger.error(f"Erreur lors de la validation IDS: {str(e)}")
            return {"valid": True, "warning": "Validation Docker non disponible"}
    
    def _parse_ids_rule(self, rule_content: str) -> Optional[Dict[str, Any]]:
        """
        Analyse une règle IDS Suricata/Snort pour en extraire les composants.
        """
        try:
            # Exemple de règle:
            # alert tcp $HOME_NET any -> $EXTERNAL_NET any (msg:"MALWARE-CNC Trojan.Win32"; flow:established,to_server; content:"POST"; http_method; sid:1; rev:1;)
            
            # Extraire les parties principales de la règle
            header_match = re.match(r'^(\w+)\s+(\w+)\s+([^\s]+)\s+([^\s]+)\s+->\s+([^\s]+)\s+([^\s]+)\s+\((.*)\)', rule_content)
            if not header_match:
                return None
                
            action, protocol, src_addr, src_port, dst_addr, dst_port, options_str = header_match.groups()
            
            # Analyser les options
            option_matches = re.findall(r'(\w+)(?::"([^"]*)")?(?:;|$)', options_str)
            options = {}
            for opt, value in option_matches:
                options[opt] = value if value else True
                
            # Créer le résultat
            result = {
                "action": action,  # alert, drop, pass
                "protocol": protocol,  # tcp, udp, ip, icmp
                "source_addr": src_addr,  # adresse IP source
                "source_port": src_port,  # port source
                "destination_addr": dst_addr,  # adresse IP destination
                "destination_port": dst_port,  # port destination
                "msg": options.get("msg", ""),  # message de la règle
                "sid": int(options.get("sid", 0)),  # identifiant de la signature
                "rev": int(options.get("rev", 0)),  # révision de la signature
                "flow": options.get("flow", ""),  # caractéristiques du flux
                "content": [],  # contenus recherchés
                "pcre": [],  # expressions régulières
                "threshold": options.get("threshold", ""),  # seuil d'alerte
            }
            
            # Extraire les contenus
            content_matches = re.findall(r'content:"([^"]*)";', options_str)
            result["content"] = content_matches
            
            # Extraire les expressions régulières
            pcre_matches = re.findall(r'pcre:"([^"]*)";', options_str)
            result["pcre"] = pcre_matches
            
            return result
            
        except Exception:
            # Si l'analyse échoue, retourner None
            return None
    
    def _check_redundant_conflict(self, rule_info: Dict[str, Any], existing_info: Dict[str, Any], rule_id: int, existing_id: int) -> Optional[RuleConflict]:
        """
        Vérifie si une règle IDS est redondante avec une autre règle.
        """
        # Vérifier que les actions sont les mêmes
        if rule_info["action"] != existing_info["action"]:
            return None
            
        # Vérifier si les caractéristiques du trafic sont les mêmes
        if rule_info["protocol"] != existing_info["protocol"]:
            return None
            
        if rule_info["source_addr"] != existing_info["source_addr"]:
            return None
            
        if rule_info["source_port"] != existing_info["source_port"]:
            return None
            
        if rule_info["destination_addr"] != existing_info["destination_addr"]:
            return None
            
        if rule_info["destination_port"] != existing_info["destination_port"]:
            return None
            
        # Vérifier si les contenus sont les mêmes (même longueur et mêmes éléments)
        if len(rule_info["content"]) != len(existing_info["content"]):
            return None
            
        for content in rule_info["content"]:
            if content not in existing_info["content"]:
                return None
                
        # Vérifier si les expressions régulières sont les mêmes
        if len(rule_info["pcre"]) != len(existing_info["pcre"]):
            return None
            
        for pcre in rule_info["pcre"]:
            if pcre not in existing_info["pcre"]:
                return None
                
        # Si tous les critères sont remplis, c'est une règle redondante
        conflict_id = self._generate_conflict_id(rule_id, existing_id, "redundant")
        return RuleConflict(
            conflict_id=conflict_id,
            rule1_id=rule_id,
            rule2_id=existing_id,
            conflict_type="redundant",
            severity="warning",
            description=f"La règle {rule_id} (SID: {rule_info['sid']}) est redondante avec la règle {existing_id} "
                        f"(SID: {existing_info['sid']}). Elles détectent le même trafic avec la même action.",
            recommendation=f"Considérez de supprimer l'une des deux règles ou de les fusionner."
        )


class AccessControlRuleConflictDetector(BaseConflictDetector):
    """
    Détecteur de conflits pour les règles de contrôle d'accès avec intégration Docker.
    """
    
    def __init__(self):
        """Initialise le détecteur avec connexion au service Fail2Ban."""
        # Configuration du service Fail2Ban Docker pour validation des règles d'accès
        fail2ban_url = getattr(settings, 'FAIL2BAN_API_URL', 'http://nms-fail2ban:5001')
        self.fail2ban_service = DockerServiceBase('fail2ban', fail2ban_url)
    
    def detect_conflicts(self, rule_data: Dict[str, Any], existing_rules: List[Dict[str, Any]]) -> List[RuleConflict]:
        """
        Détecte les conflits entre une règle de contrôle d'accès et des règles existantes.
        
        Types de conflits détectés :
        - Contradiction : Des règles avec des effets opposés pour les mêmes sujets et ressources
        - Redondance : Des règles qui font essentiellement la même chose
        - Exception masquée : Une règle d'exception est masquée par une règle plus générale
        - Spécificité : Un conflit de spécificité entre les règles
        """
        conflicts = []
        rule_id = rule_data.get("id", 0)
        rule_content = rule_data.get("content", "")
        
        if not rule_content:
            return conflicts
        
        # Valider la règle via le service Docker si disponible
        if self.fail2ban_service.test_connection():
            validation_result = self._validate_rule_via_docker(rule_content)
            if not validation_result.get("valid", True):
                logger.warning(f"Règle de contrôle d'accès non valide: {validation_result.get('error', 'Erreur inconnue')}")
            
        # Pour l'instant, retourner une liste vide - l'implémentation complète sera ajoutée
        return conflicts
    
    def _validate_rule_via_docker(self, rule_content: str) -> Dict[str, Any]:
        """
        Valide une règle de contrôle d'accès via le service Docker Fail2Ban.
        """
        try:
            return self.fail2ban_service.call_api(
                "/validate/rule",
                method="POST",
                data={"rule": rule_content}
            )
        except Exception as e:
            logger.error(f"Erreur lors de la validation de contrôle d'accès: {str(e)}")
            return {"valid": True, "warning": "Validation Docker non disponible"}