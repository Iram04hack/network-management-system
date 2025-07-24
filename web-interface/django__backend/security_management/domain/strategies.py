"""
Stratégies de validation des règles de sécurité avec intégration Docker.

Ce module contient les validateurs pour différents types de règles de sécurité,
utilisant les services Docker pour une validation en temps réel.
"""

import re
import json
import logging
import ipaddress
import requests
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass

from django.conf import settings
from .interfaces import DockerServiceConnector

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """
    Résultat d'une validation de règle de sécurité.
    """
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    suggestions: List[str]
    confidence_score: float = 1.0
    
    def add_error(self, message: str):
        """Ajoute une erreur au résultat."""
        self.errors.append(message)
        self.is_valid = False
    
    def add_warning(self, message: str):
        """Ajoute un avertissement au résultat."""
        self.warnings.append(message)
        if self.confidence_score > 0.8:
            self.confidence_score = 0.8
    
    def add_suggestion(self, message: str):
        """Ajoute une suggestion au résultat."""
        self.suggestions.append(message)


class RuleValidator(ABC):
    """
    Interface abstraite pour les validateurs de règles de sécurité.
    """
    
    @abstractmethod
    def validate(self, rule_content: str, rule_metadata: Optional[Dict[str, Any]] = None) -> ValidationResult:
        """
        Valide une règle de sécurité.
        
        Args:
            rule_content: Contenu de la règle à valider
            rule_metadata: Métadonnées supplémentaires sur la règle
            
        Returns:
            Résultat de la validation
        """
        pass
    
    @abstractmethod
    def get_rule_type(self) -> str:
        """
        Retourne le type de règle géré par ce validateur.
        
        Returns:
            Type de règle (firewall, ids, access_control, etc.)
        """
        pass


class DockerValidationMixin:
    """
    Mixin pour ajouter des capacités de validation via services Docker.
    """
    
    def __init__(self, service_name: str, service_url: str):
        """
        Initialise le mixin avec les informations du service Docker.
        
        Args:
            service_name: Nom du service Docker
            service_url: URL du service Docker
        """
        self.service_name = service_name
        self.service_url = service_url
        self._session = requests.Session()
        self._session.timeout = 30
    
    def test_docker_connection(self) -> bool:
        """
        Teste la connexion au service Docker.
        
        Returns:
            True si la connexion est établie
        """
        try:
            response = self._session.get(f"{self.service_url}/health")
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"Connexion au service {self.service_name} échouée: {str(e)}")
            return False
    
    def call_docker_validation(self, endpoint: str, rule_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Effectue un appel de validation vers le service Docker.
        
        Args:
            endpoint: Point de terminaison de validation
            rule_data: Données de la règle à valider
            
        Returns:
            Résultat de la validation Docker
        """
        try:
            response = self._session.post(
                f"{self.service_url}{endpoint}",
                json=rule_data,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {
                    "valid": False,
                    "error": f"Erreur HTTP {response.status_code}: {response.text}"
                }
                
        except Exception as e:
            logger.error(f"Erreur lors de la validation Docker: {str(e)}")
            return {
                "valid": False,
                "error": f"Erreur de connexion: {str(e)}"
            }


class SuricataRuleValidator(RuleValidator, DockerValidationMixin):
    """
    Validateur pour les règles Suricata IDS avec intégration Docker.
    """
    
    def __init__(self):
        """Initialise le validateur Suricata."""
        service_url = getattr(settings, 'SURICATA_API_URL', 'http://nms-suricata:8068')
        DockerValidationMixin.__init__(self, 'suricata', service_url)
        
        # Patterns de validation Suricata
        self.action_pattern = re.compile(r'^(alert|drop|reject|pass)\s+')
        self.protocol_pattern = re.compile(r'(tcp|udp|icmp|ip)\s+')
        self.rule_pattern = re.compile(r'^(alert|drop|reject|pass)\s+(tcp|udp|icmp|ip)\s+([^\s]+)\s+([^\s]+)\s+->\s+([^\s]+)\s+([^\s]+)\s+\((.*)\)$')
        
        # Options Suricata connues
        self.known_options = {
            'msg', 'sid', 'rev', 'gid', 'classtype', 'reference', 'priority',
            'threshold', 'detection_filter', 'metadata', 'target', 'flow',
            'flowbits', 'flowint', 'content', 'nocase', 'rawbytes', 'depth',
            'offset', 'distance', 'within', 'isdataat', 'pcre', 'byte_test',
            'byte_jump', 'byte_extract', 'file_data', 'dce_iface', 'dce_opnum',
            'dce_stub_data', 'asn1', 'urilen', 'http_method', 'http_uri',
            'http_header', 'http_cookie', 'http_user_agent', 'http_client_body',
            'http_server_body', 'http_stat_code', 'http_stat_msg', 'ssl_version',
            'ssl_state', 'tls.version', 'tls.subject', 'tls.issuer', 'tls.fingerprint'
        }
    
    def get_rule_type(self) -> str:
        """Retourne le type de règle géré."""
        return "ids"
    
    def validate(self, rule_content: str, rule_metadata: Optional[Dict[str, Any]] = None) -> ValidationResult:
        """
        Valide une règle Suricata.
        
        Args:
            rule_content: Contenu de la règle Suricata
            rule_metadata: Métadonnées supplémentaires
            
        Returns:
            Résultat de la validation
        """
        result = ValidationResult(is_valid=True, errors=[], warnings=[], suggestions=[])
        
        # Validation syntaxique de base
        self._validate_basic_syntax(rule_content, result)
        
        if result.is_valid:
            # Validation des composants de la règle
            self._validate_rule_components(rule_content, result)
        
        if result.is_valid:
            # Validation des options
            self._validate_options(rule_content, result)
        
        # Validation via service Docker si disponible
        if result.is_valid and self.test_docker_connection():
            self._validate_via_docker(rule_content, result)
        
        return result
    
    def _validate_basic_syntax(self, rule_content: str, result: ValidationResult):
        """Valide la syntaxe de base de la règle."""
        rule_content = rule_content.strip()
        
        if not rule_content:
            result.add_error("La règle ne peut pas être vide")
            return
        
        # Vérifier le format général
        if not self.rule_pattern.match(rule_content):
            result.add_error("Format de règle Suricata invalide")
            return
        
        # Vérifier l'action
        if not self.action_pattern.match(rule_content):
            result.add_error("Action invalide. Actions supportées: alert, drop, reject, pass")
            return
        
        # Vérifier le protocole
        if not self.protocol_pattern.search(rule_content):
            result.add_error("Protocole invalide. Protocoles supportés: tcp, udp, icmp, ip")
            return
        
        # Vérifier la présence de parenthèses pour les options
        if '(' not in rule_content or ')' not in rule_content:
            result.add_error("Les options de la règle doivent être entre parenthèses")
            return
        
        # Vérifier que les parenthèses sont équilibrées
        open_count = rule_content.count('(')
        close_count = rule_content.count(')')
        if open_count != close_count:
            result.add_error("Parenthèses non équilibrées dans la règle")
    
    def _validate_rule_components(self, rule_content: str, result: ValidationResult):
        """Valide les composants de la règle (adresses, ports)."""
        match = self.rule_pattern.match(rule_content)
        if not match:
            return
        
        action, protocol, src_addr, src_port, dst_addr, dst_port, options = match.groups()
        
        # Valider les adresses IP
        self._validate_ip_address(src_addr, "source", result)
        self._validate_ip_address(dst_addr, "destination", result)
        
        # Valider les ports
        self._validate_port(src_port, "source", result)
        self._validate_port(dst_port, "destination", result)
        
        # Vérifications spécifiques au protocole
        if protocol == "icmp" and (src_port != "any" or dst_port != "any"):
            result.add_warning("Les ports ne sont généralement pas utilisés avec le protocole ICMP")
    
    def _validate_ip_address(self, addr: str, addr_type: str, result: ValidationResult):
        """Valide une adresse IP ou une plage."""
        if addr in ["any", "!any"]:
            return
        
        # Gérer les variables Suricata
        if addr.startswith('$') or addr.startswith('!$'):
            return
        
        # Gérer les listes d'adresses
        if addr.startswith('[') and addr.endswith(']'):
            addresses = addr[1:-1].split(',')
            for single_addr in addresses:
                self._validate_single_ip(single_addr.strip(), addr_type, result)
        else:
            self._validate_single_ip(addr, addr_type, result)
    
    def _validate_single_ip(self, addr: str, addr_type: str, result: ValidationResult):
        """Valide une adresse IP unique."""
        # Gérer la négation
        if addr.startswith('!'):
            addr = addr[1:]
        
        # Gérer les variables
        if addr.startswith('$'):
            return
        
        try:
            ipaddress.ip_network(addr, strict=False)
        except ValueError:
            result.add_error(f"Adresse IP {addr_type} invalide: {addr}")
    
    def _validate_port(self, port: str, port_type: str, result: ValidationResult):
        """Valide un port ou une plage de ports."""
        if port in ["any", "!any"]:
            return
        
        # Gérer les variables Suricata
        if port.startswith('$') or port.startswith('!$'):
            return
        
        # Gérer les listes de ports
        if port.startswith('[') and port.endswith(']'):
            ports = port[1:-1].split(',')
            for single_port in ports:
                self._validate_single_port(single_port.strip(), port_type, result)
        else:
            self._validate_single_port(port, port_type, result)
    
    def _validate_single_port(self, port: str, port_type: str, result: ValidationResult):
        """Valide un port unique."""
        # Gérer la négation
        if port.startswith('!'):
            port = port[1:]
        
        # Gérer les variables
        if port.startswith('$'):
            return
        
        # Gérer les plages
        if ':' in port:
            try:
                start, end = port.split(':')
                start_port = int(start) if start else 0
                end_port = int(end) if end else 65535
                
                if start_port < 0 or start_port > 65535:
                    result.add_error(f"Port {port_type} de début invalide: {start_port}")
                if end_port < 0 or end_port > 65535:
                    result.add_error(f"Port {port_type} de fin invalide: {end_port}")
                if start_port > end_port:
                    result.add_error(f"Plage de ports {port_type} invalide: {port}")
            except ValueError:
                result.add_error(f"Plage de ports {port_type} invalide: {port}")
        else:
            try:
                port_num = int(port)
                if port_num < 0 or port_num > 65535:
                    result.add_error(f"Port {port_type} invalide: {port_num}")
            except ValueError:
                result.add_error(f"Port {port_type} invalide: {port}")
    
    def _validate_options(self, rule_content: str, result: ValidationResult):
        """Valide les options de la règle."""
        # Extraire les options
        match = self.rule_pattern.match(rule_content)
        if not match:
            return
        
        options_str = match.group(7)
        
        # Vérifier la présence d'options obligatoires
        if 'msg:' not in options_str:
            result.add_error("L'option 'msg' est obligatoire")
        
        if 'sid:' not in options_str:
            result.add_error("L'option 'sid' est obligatoire")
        
        # Extraire et valider les options individuelles
        option_pattern = re.compile(r'(\w+)(?:\s*:\s*([^;]+))?;')
        options = option_pattern.findall(options_str)
        
        for option_name, option_value in options:
            self._validate_single_option(option_name, option_value, result)
    
    def _validate_single_option(self, option_name: str, option_value: str, result: ValidationResult):
        """Valide une option individuelle."""
        # Vérifier si l'option est connue
        if option_name not in self.known_options:
            result.add_warning(f"Option inconnue ou non standard: {option_name}")
        
        # Validations spécifiques
        if option_name == 'sid':
            try:
                sid = int(option_value)
                if sid <= 0:
                    result.add_error("Le SID doit être un entier positif")
                elif sid < 1000000:
                    result.add_suggestion("Utilisez un SID >= 1000000 pour les règles personnalisées")
            except ValueError:
                result.add_error("Le SID doit être un entier")
        
        elif option_name == 'rev':
            try:
                rev = int(option_value)
                if rev <= 0:
                    result.add_error("La révision doit être un entier positif")
            except ValueError:
                result.add_error("La révision doit être un entier")
        
        elif option_name == 'priority':
            try:
                priority = int(option_value)
                if priority < 1 or priority > 4:
                    result.add_error("La priorité doit être entre 1 et 4")
            except ValueError:
                result.add_error("La priorité doit être un entier")
        
        elif option_name == 'msg':
            if not option_value or not option_value.strip():
                result.add_error("Le message ne peut pas être vide")
            elif not (option_value.startswith('"') and option_value.endswith('"')):
                result.add_error("Le message doit être entre guillemets")
    
    def _validate_via_docker(self, rule_content: str, result: ValidationResult):
        """Valide la règle via le service Docker Suricata."""
        docker_result = self.call_docker_validation(
            "/validate/rule",
            {"rule": rule_content}
        )
        
        if not docker_result.get("valid", True):
            error_msg = docker_result.get("error", "Erreur de validation Docker")
            result.add_warning(f"Validation Docker: {error_msg}")
            result.confidence_score = min(result.confidence_score, 0.7)
        else:
            # Ajouter les suggestions du service Docker si disponibles
            docker_suggestions = docker_result.get("suggestions", [])
            for suggestion in docker_suggestions:
                result.add_suggestion(f"Docker: {suggestion}")


class FirewallRuleValidator(RuleValidator, DockerValidationMixin):
    """
    Validateur pour les règles de pare-feu (iptables) avec intégration Docker.
    """
    
    def __init__(self):
        """Initialise le validateur firewall."""
        service_url = getattr(settings, 'TRAFFIC_CONTROL_API_URL', 'http://nms-traffic-control:8003')
        DockerValidationMixin.__init__(self, 'traffic-control', service_url)
        
        # Chaînes iptables valides
        self.valid_chains = {'INPUT', 'OUTPUT', 'FORWARD', 'PREROUTING', 'POSTROUTING'}
        
        # Actions iptables valides
        self.valid_actions = {'ACCEPT', 'DROP', 'REJECT', 'LOG', 'RETURN', 'QUEUE', 'DNAT', 'SNAT', 'MASQUERADE'}
        
        # Protocoles valides
        self.valid_protocols = {'tcp', 'udp', 'icmp', 'esp', 'gre', 'ipv6-icmp', 'all'}
    
    def get_rule_type(self) -> str:
        """Retourne le type de règle géré."""
        return "firewall"
    
    def validate(self, rule_content: str, rule_metadata: Optional[Dict[str, Any]] = None) -> ValidationResult:
        """
        Valide une règle iptables.
        
        Args:
            rule_content: Contenu de la règle iptables
            rule_metadata: Métadonnées supplémentaires
            
        Returns:
            Résultat de la validation
        """
        result = ValidationResult(is_valid=True, errors=[], warnings=[], suggestions=[])
        
        # Validation syntaxique de base
        self._validate_basic_syntax(rule_content, result)
        
        if result.is_valid:
            # Validation des composants de la règle
            self._validate_rule_components(rule_content, result)
        
        # Validation via service Docker si disponible
        if result.is_valid and self.test_docker_connection():
            self._validate_via_docker(rule_content, result)
        
        return result
    
    def _validate_basic_syntax(self, rule_content: str, result: ValidationResult):
        """Valide la syntaxe de base de la règle iptables."""
        rule_content = rule_content.strip()
        
        if not rule_content:
            result.add_error("La règle ne peut pas être vide")
            return
        
        # Vérifier que la règle commence par iptables
        if not rule_content.startswith('iptables'):
            result.add_error("La règle doit commencer par 'iptables'")
            return
        
        # Vérifier la présence d'une action (-A, -I, -D)
        if not any(option in rule_content for option in ['-A', '-I', '-D']):
            result.add_error("La règle doit contenir une action (-A, -I, ou -D)")
            return
        
        # Vérifier la présence d'une cible (-j)
        if '-j' not in rule_content:
            result.add_error("La règle doit contenir une cible (-j)")
    
    def _validate_rule_components(self, rule_content: str, result: ValidationResult):
        """Valide les composants de la règle iptables."""
        parts = rule_content.split()
        
        # Valider la chaîne
        if '-A' in parts:
            chain_index = parts.index('-A') + 1
            if chain_index < len(parts):
                chain = parts[chain_index]
                if chain not in self.valid_chains:
                    result.add_warning(f"Chaîne non standard: {chain}")
        
        # Valider le protocole
        if '-p' in parts:
            proto_index = parts.index('-p') + 1
            if proto_index < len(parts):
                protocol = parts[proto_index]
                if protocol not in self.valid_protocols:
                    result.add_warning(f"Protocole non standard: {protocol}")
        
        # Valider l'action
        if '-j' in parts:
            action_index = parts.index('-j') + 1
            if action_index < len(parts):
                action = parts[action_index]
                if action not in self.valid_actions:
                    result.add_warning(f"Action non standard: {action}")
        
        # Valider les adresses IP
        self._validate_iptables_addresses(parts, result)
        
        # Valider les ports
        self._validate_iptables_ports(parts, result)
    
    def _validate_iptables_addresses(self, parts: List[str], result: ValidationResult):
        """Valide les adresses IP dans la règle iptables."""
        # Valider l'adresse source
        if '-s' in parts:
            src_index = parts.index('-s') + 1
            if src_index < len(parts):
                src_addr = parts[src_index]
                if not src_addr.startswith('-'):
                    self._validate_ip_address(src_addr, "source", result)
        
        # Valider l'adresse destination
        if '-d' in parts:
            dst_index = parts.index('-d') + 1
            if dst_index < len(parts):
                dst_addr = parts[dst_index]
                if not dst_addr.startswith('-'):
                    self._validate_ip_address(dst_addr, "destination", result)
    
    def _validate_iptables_ports(self, parts: List[str], result: ValidationResult):
        """Valide les ports dans la règle iptables."""
        # Valider le port source
        if '--sport' in parts:
            sport_index = parts.index('--sport') + 1
            if sport_index < len(parts):
                sport = parts[sport_index]
                if not sport.startswith('-'):
                    self._validate_port_range(sport, "source", result)
        
        # Valider le port destination
        if '--dport' in parts:
            dport_index = parts.index('--dport') + 1
            if dport_index < len(parts):
                dport = parts[dport_index]
                if not dport.startswith('-'):
                    self._validate_port_range(dport, "destination", result)
    
    def _validate_ip_address(self, addr: str, addr_type: str, result: ValidationResult):
        """Valide une adresse IP ou un réseau."""
        if addr == "anywhere" or addr == "0.0.0.0/0":
            return
        
        try:
            ipaddress.ip_network(addr, strict=False)
        except ValueError:
            result.add_error(f"Adresse IP {addr_type} invalide: {addr}")
    
    def _validate_port_range(self, port_str: str, port_type: str, result: ValidationResult):
        """Valide une plage de ports."""
        if ':' in port_str:
            try:
                start, end = port_str.split(':')
                start_port = int(start)
                end_port = int(end)
                
                if start_port < 1 or start_port > 65535:
                    result.add_error(f"Port {port_type} de début invalide: {start_port}")
                if end_port < 1 or end_port > 65535:
                    result.add_error(f"Port {port_type} de fin invalide: {end_port}")
                if start_port > end_port:
                    result.add_error(f"Plage de ports {port_type} invalide: {port_str}")
            except ValueError:
                result.add_error(f"Plage de ports {port_type} invalide: {port_str}")
        else:
            try:
                port = int(port_str)
                if port < 1 or port > 65535:
                    result.add_error(f"Port {port_type} invalide: {port}")
            except ValueError:
                result.add_error(f"Port {port_type} invalide: {port_str}")
    
    def _validate_via_docker(self, rule_content: str, result: ValidationResult):
        """Valide la règle via le service Docker Traffic Control."""
        docker_result = self.call_docker_validation(
            "/validate/firewall",
            {"rule": rule_content}
        )
        
        if not docker_result.get("valid", True):
            error_msg = docker_result.get("error", "Erreur de validation Docker")
            result.add_warning(f"Validation Docker: {error_msg}")
            result.confidence_score = min(result.confidence_score, 0.7)


class AccessControlRuleValidator(RuleValidator, DockerValidationMixin):
    """
    Validateur pour les règles de contrôle d'accès avec intégration Docker.
    """
    
    def __init__(self):
        """Initialise le validateur de contrôle d'accès."""
        service_url = getattr(settings, 'FAIL2BAN_API_URL', 'http://nms-fail2ban:5001')
        DockerValidationMixin.__init__(self, 'fail2ban', service_url)
        
        # Effets valides
        self.valid_effects = {'allow', 'deny', 'permit', 'reject'}
        
        # Actions valides
        self.valid_actions = {'read', 'write', 'execute', 'delete', 'all', '*'}
    
    def get_rule_type(self) -> str:
        """Retourne le type de règle géré."""
        return "access_control"
    
    def validate(self, rule_content: str, rule_metadata: Optional[Dict[str, Any]] = None) -> ValidationResult:
        """
        Valide une règle de contrôle d'accès (format JSON).
        
        Args:
            rule_content: Contenu de la règle en JSON
            rule_metadata: Métadonnées supplémentaires
            
        Returns:
            Résultat de la validation
        """
        result = ValidationResult(is_valid=True, errors=[], warnings=[], suggestions=[])
        
        # Validation du format JSON
        try:
            rule_data = json.loads(rule_content)
        except json.JSONDecodeError as e:
            result.add_error(f"JSON invalide: {str(e)}")
            return result
        
        # Validation des composants requis
        self._validate_required_fields(rule_data, result)
        
        if result.is_valid:
            # Validation des valeurs
            self._validate_field_values(rule_data, result)
        
        # Validation via service Docker si disponible
        if result.is_valid and self.test_docker_connection():
            self._validate_via_docker(rule_content, result)
        
        return result
    
    def _validate_required_fields(self, rule_data: Dict[str, Any], result: ValidationResult):
        """Valide la présence des champs requis."""
        required_fields = ['subject', 'resource', 'action', 'effect']
        
        for field in required_fields:
            if field not in rule_data:
                result.add_error(f"Champ requis manquant: {field}")
            elif not rule_data[field]:
                result.add_error(f"Champ requis vide: {field}")
    
    def _validate_field_values(self, rule_data: Dict[str, Any], result: ValidationResult):
        """Valide les valeurs des champs."""
        # Valider l'effet
        effect = rule_data.get('effect', '').lower()
        if effect and effect not in self.valid_effects:
            result.add_warning(f"Effet non standard: {effect}")
        
        # Valider l'action
        action = rule_data.get('action', '').lower()
        if action and action not in self.valid_actions:
            result.add_warning(f"Action non standard: {action}")
        
        # Valider les conditions si présentes
        conditions = rule_data.get('conditions', {})
        if conditions:
            self._validate_conditions(conditions, result)
    
    def _validate_conditions(self, conditions: Dict[str, Any], result: ValidationResult):
        """Valide les conditions de la règle."""
        # Valider les restrictions IP
        if 'ip_range' in conditions:
            ip_ranges = conditions['ip_range']
            if isinstance(ip_ranges, list):
                for ip_range in ip_ranges:
                    self._validate_ip_range(ip_range, result)
            else:
                self._validate_ip_range(ip_ranges, result)
        
        # Valider les restrictions temporelles
        if 'time' in conditions:
            time_restriction = conditions['time']
            self._validate_time_restriction(time_restriction, result)
    
    def _validate_ip_range(self, ip_range: str, result: ValidationResult):
        """Valide une plage d'adresses IP."""
        try:
            ipaddress.ip_network(ip_range, strict=False)
        except ValueError:
            result.add_error(f"Plage IP invalide: {ip_range}")
    
    def _validate_time_restriction(self, time_restriction: Dict[str, Any], result: ValidationResult):
        """Valide une restriction temporelle."""
        if not isinstance(time_restriction, dict):
            result.add_error("La restriction temporelle doit être un objet")
            return
        
        # Valider les heures
        if 'start_time' in time_restriction:
            self._validate_time_format(time_restriction['start_time'], "start_time", result)
        
        if 'end_time' in time_restriction:
            self._validate_time_format(time_restriction['end_time'], "end_time", result)
        
        # Valider les jours
        if 'days' in time_restriction:
            days = time_restriction['days']
            valid_days = {'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'}
            if isinstance(days, list):
                for day in days:
                    if day.lower() not in valid_days:
                        result.add_error(f"Jour invalide: {day}")
            else:
                if days.lower() not in valid_days:
                    result.add_error(f"Jour invalide: {days}")
    
    def _validate_time_format(self, time_str: str, field_name: str, result: ValidationResult):
        """Valide le format d'une heure (HH:MM)."""
        time_pattern = re.compile(r'^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$')
        if not time_pattern.match(time_str):
            result.add_error(f"Format d'heure invalide pour {field_name}: {time_str}")
    
    def _validate_via_docker(self, rule_content: str, result: ValidationResult):
        """Valide la règle via le service Docker Fail2Ban."""
        docker_result = self.call_docker_validation(
            "/validate/access_rule",
            {"rule": rule_content}
        )
        
        if not docker_result.get("valid", True):
            error_msg = docker_result.get("error", "Erreur de validation Docker")
            result.add_warning(f"Validation Docker: {error_msg}")
            result.confidence_score = min(result.confidence_score, 0.7)


class Fail2BanRuleValidator(RuleValidator, DockerValidationMixin):
    """
    Validateur pour les règles Fail2Ban avec intégration Docker.
    """
    
    def __init__(self):
        """Initialise le validateur Fail2Ban."""
        service_url = getattr(settings, 'FAIL2BAN_API_URL', 'http://nms-fail2ban:5001')
        DockerValidationMixin.__init__(self, 'fail2ban', service_url)
    
    def get_rule_type(self) -> str:
        """Retourne le type de règle géré."""
        return "fail2ban"
    
    def validate(self, rule_content: str, rule_metadata: Optional[Dict[str, Any]] = None) -> ValidationResult:
        """
        Valide une règle ou configuration Fail2Ban.
        
        Args:
            rule_content: Contenu de la règle/configuration
            rule_metadata: Métadonnées supplémentaires
            
        Returns:
            Résultat de la validation
        """
        result = ValidationResult(is_valid=True, errors=[], warnings=[], suggestions=[])
        
        # Validation de base
        if not rule_content.strip():
            result.add_error("La règle ne peut pas être vide")
            return result
        
        # Validation via service Docker si disponible
        if self.test_docker_connection():
            self._validate_via_docker(rule_content, result)
        else:
            result.add_warning("Service Fail2Ban non disponible pour validation")
        
        return result
    
    def _validate_via_docker(self, rule_content: str, result: ValidationResult):
        """Valide la règle via le service Docker Fail2Ban."""
        docker_result = self.call_docker_validation(
            "/validate/rule",
            {"rule": rule_content}
        )
        
        if not docker_result.get("valid", True):
            error_msg = docker_result.get("error", "Erreur de validation Docker")
            result.add_error(f"Validation Fail2Ban: {error_msg}")


class CompositeRuleValidator:
    """
    Validateur composite qui utilise le bon validateur selon le type de règle.
    """
    
    def __init__(self):
        """Initialise le validateur composite."""
        self.validators = {
            'firewall': FirewallRuleValidator(),
            'ids': SuricataRuleValidator(),
            'suricata': SuricataRuleValidator(),  # Alias pour IDS
            'access_control': AccessControlRuleValidator(),
            'fail2ban': Fail2BanRuleValidator(),
        }
    
    def validate(self, rule_type: str, rule_content: str, rule_metadata: Optional[Dict[str, Any]] = None) -> ValidationResult:
        """
        Valide une règle selon son type.
        
        Args:
            rule_type: Type de règle
            rule_content: Contenu de la règle
            rule_metadata: Métadonnées supplémentaires
            
        Returns:
            Résultat de la validation
        """
        rule_type = rule_type.lower()
        
        if rule_type not in self.validators:
            result = ValidationResult(is_valid=False, errors=[], warnings=[], suggestions=[])
            result.add_error(f"Type de règle non supporté: {rule_type}")
            return result
        
        validator = self.validators[rule_type]
        return validator.validate(rule_content, rule_metadata)
    
    def get_supported_rule_types(self) -> List[str]:
        """
        Retourne la liste des types de règles supportés.
        
        Returns:
            Liste des types de règles
        """
        return list(self.validators.keys())


# Instance globale du validateur composite
rule_validator = CompositeRuleValidator()