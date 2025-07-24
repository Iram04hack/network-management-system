"""
Client SNMP sécurisé pour la gestion des équipements réseau.

Ce module fournit un client SNMP robuste avec chiffrement des credentials,
validation des paramètres et support des versions SNMP v1, v2c et v3.
"""

import logging
import re
import ipaddress
from typing import Dict, Any, Optional, List, Union, Tuple
from dataclasses import dataclass
from enum import Enum

from ..base import BaseAPIClient
from ..infrastructure.input_validator import (
    IPAddressValidator,
    StringValidator,
    CompositeValidator,
    ValidationException
)
from ..domain.exceptions import (
    APIClientException,
    AuthenticationException,
    APIConnectionException
)
from ..monitoring.metrics.performance import measure_performance

logger = logging.getLogger(__name__)

class SNMPVersion(Enum):
    """Versions SNMP supportées."""
    V1 = "1"
    V2C = "2c"
    V3 = "3"

class SNMPSecurityLevel(Enum):
    """Niveaux de sécurité SNMP v3."""
    NO_AUTH_NO_PRIV = "noAuthNoPriv"
    AUTH_NO_PRIV = "authNoPriv"
    AUTH_PRIV = "authPriv"

class SNMPAuthProtocol(Enum):
    """Protocoles d'authentification SNMP v3."""
    MD5 = "MD5"
    SHA = "SHA"
    SHA224 = "SHA224"
    SHA256 = "SHA256"
    SHA384 = "SHA384"
    SHA512 = "SHA512"

class SNMPPrivProtocol(Enum):
    """Protocoles de chiffrement SNMP v3."""
    DES = "DES"
    AES128 = "AES128"
    AES192 = "AES192"
    AES256 = "AES256"

@dataclass
class SNMPCredentials:
    """Credentials SNMP avec gestion sécurisée."""
    version: SNMPVersion
    community: Optional[str] = None  # Pour v1/v2c
    username: Optional[str] = None   # Pour v3
    auth_protocol: Optional[SNMPAuthProtocol] = None
    auth_password: Optional[str] = None
    priv_protocol: Optional[SNMPPrivProtocol] = None
    priv_password: Optional[str] = None
    security_level: Optional[SNMPSecurityLevel] = None
    
    def __post_init__(self):
        """Validation post-initialisation."""
        if self.version in [SNMPVersion.V1, SNMPVersion.V2C]:
            if not self.community:
                raise ValidationException("Community string requis pour SNMP v1/v2c")
        elif self.version == SNMPVersion.V3:
            if not self.username:
                raise ValidationException("Username requis pour SNMP v3")
            if not self.security_level:
                self.security_level = SNMPSecurityLevel.NO_AUTH_NO_PRIV

class SNMPClient(BaseAPIClient):
    """
    Client SNMP sécurisé pour la gestion des équipements réseau.
    
    Ce client supporte SNMP v1, v2c et v3 avec gestion sécurisée
    des credentials et validation des paramètres.
    """
    
    # OIDs standards couramment utilisés
    STANDARD_OIDS = {
        'system': {
            'sysDescr': '1.3.6.1.2.1.1.1.0',
            'sysObjectID': '1.3.6.1.2.1.1.2.0',
            'sysUpTime': '1.3.6.1.2.1.1.3.0',
            'sysContact': '1.3.6.1.2.1.1.4.0',
            'sysName': '1.3.6.1.2.1.1.5.0',
            'sysLocation': '1.3.6.1.2.1.1.6.0',
            'sysServices': '1.3.6.1.2.1.1.7.0'
        },
        'interfaces': {
            'ifNumber': '1.3.6.1.2.1.2.1.0',
            'ifTable': '1.3.6.1.2.1.2.2',
            'ifDescr': '1.3.6.1.2.1.2.2.1.2',
            'ifType': '1.3.6.1.2.1.2.2.1.3',
            'ifMtu': '1.3.6.1.2.1.2.2.1.4',
            'ifSpeed': '1.3.6.1.2.1.2.2.1.5',
            'ifPhysAddress': '1.3.6.1.2.1.2.2.1.6',
            'ifAdminStatus': '1.3.6.1.2.1.2.2.1.7',
            'ifOperStatus': '1.3.6.1.2.1.2.2.1.8',
            'ifInOctets': '1.3.6.1.2.1.2.2.1.10',
            'ifOutOctets': '1.3.6.1.2.1.2.2.1.16'
        },
        'ip': {
            'ipForwarding': '1.3.6.1.2.1.4.1.0',
            'ipDefaultTTL': '1.3.6.1.2.1.4.2.0',
            'ipInReceives': '1.3.6.1.2.1.4.3.0',
            'ipInDelivers': '1.3.6.1.2.1.4.9.0',
            'ipOutRequests': '1.3.6.1.2.1.4.10.0'
        },
        'snmp': {
            'snmpInPkts': '1.3.6.1.2.1.11.1.0',
            'snmpOutPkts': '1.3.6.1.2.1.11.2.0',
            'snmpInBadVersions': '1.3.6.1.2.1.11.3.0',
            'snmpInBadCommunityNames': '1.3.6.1.2.1.11.4.0'
        }
    }
    
    def __init__(
        self,
        host: str,
        port: int = 161,
        credentials: Optional[SNMPCredentials] = None,
        timeout: int = 10,
        retries: int = 3,
        base_url: Optional[str] = None  # Pour API SNMP REST si disponible
    ):
        """
        Initialise le client SNMP.
        
        Args:
            host: Adresse de l'équipement SNMP
            port: Port SNMP (défaut 161)
            credentials: Credentials SNMP sécurisés
            timeout: Délai d'attente en secondes
            retries: Nombre de tentatives
            base_url: URL API REST si disponible
        """
        # Valider l'adresse IP de l'hôte
        self._validate_host(host)
        
        self.host = host
        self.port = port
        self.credentials = credentials or SNMPCredentials(
            version=SNMPVersion.V2C,
            community="public"
        )
        self.timeout = timeout
        self.retries = retries
        
        # Initialiser le client de base si API REST disponible
        if base_url:
            super().__init__(base_url, timeout=timeout)
        else:
            self.base_url = None
        
        # Initialiser les validateurs
        self._init_validators()
        
        logger.info(f"SNMP client initialisé pour {host}:{port} (version {self.credentials.version.value})")
    
    def _validate_host(self, host: str):
        """Valide l'adresse de l'hôte."""
        try:
            # Essayer de parser comme adresse IP
            ipaddress.ip_address(host)
        except ValueError:
            # Vérifier que c'est un nom d'hôte valide
            if not re.match(r'^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$', host):
                raise ValidationException(f"Adresse d'hôte invalide: {host}")
    
    def _init_validators(self):
        """Initialise les validateurs pour les paramètres SNMP."""
        self.validators = CompositeValidator({
            'oid': StringValidator(
                min_length=1,
                max_length=200,
                pattern=re.compile(r'^\.?[0-9]+(\.[0-9]+)*$'),
                strip_whitespace=True
            ),
            'community': StringValidator(
                min_length=1,
                max_length=100,
                forbidden_chars='"\n\r\t',
                strip_whitespace=True
            ),
            'username': StringValidator(
                min_length=1,
                max_length=100,
                forbidden_chars='"\n\r\t',
                strip_whitespace=True
            )
        })
    
    def test_connection(self) -> bool:
        """
        Teste la connexion SNMP en récupérant sysDescr.
        
        Returns:
            True si la connexion SNMP fonctionne
        """
        try:
            result = self.get_system_info()
            return result.get("success", False) and "sysDescr" in result.get("data", {})
        except Exception as e:
            logger.error(f"Test de connexion SNMP échoué pour {self.host}: {e}")
            return False
    
    @measure_performance(endpoint_name="snmp_get")
    def get(self, oid: str) -> Dict[str, Any]:
        """
        Effectue un SNMP GET pour un OID spécifique.
        
        Args:
            oid: OID à récupérer
            
        Returns:
            Valeur de l'OID
        """
        try:
            # Valider l'OID
            validated_oid = self._validate_oid(oid)
            
            if self.base_url:
                # Utiliser l'API REST si disponible
                params = {
                    'host': self.host,
                    'port': self.port,
                    'oid': validated_oid,
                    'version': self.credentials.version.value,
                    'timeout': self.timeout
                }
                
                # Ajouter les credentials selon la version
                self._add_credentials_to_params(params)
                
                return super().get("snmp/get", params=params)
            else:
                # Utiliser SNMP direct (nécessiterait une lib comme pysnmp)
                return self._direct_snmp_get(validated_oid)
            
        except ValidationException as e:
            logger.warning(f"OID invalide pour SNMP GET: {e}")
            return {"success": False, "error": f"OID invalide: {e.message}"}
        except Exception as e:
            logger.error(f"Erreur lors du SNMP GET: {e}")
            return {"success": False, "error": str(e)}
    
    @measure_performance(endpoint_name="snmp_walk")
    def walk(self, oid: str) -> Dict[str, Any]:
        """
        Effectue un SNMP WALK pour un OID spécifique.
        
        Args:
            oid: OID de base pour le walk
            
        Returns:
            Valeurs des OIDs
        """
        try:
            # Valider l'OID
            validated_oid = self._validate_oid(oid)
            
            if self.base_url:
                params = {
                    'host': self.host,
                    'port': self.port,
                    'oid': validated_oid,
                    'version': self.credentials.version.value,
                    'timeout': self.timeout
                }
                
                self._add_credentials_to_params(params)
                
                return super().get("snmp/walk", params=params)
            else:
                return self._direct_snmp_walk(validated_oid)
            
        except ValidationException as e:
            logger.warning(f"OID invalide pour SNMP WALK: {e}")
            return {"success": False, "error": f"OID invalide: {e.message}"}
        except Exception as e:
            logger.error(f"Erreur lors du SNMP WALK: {e}")
            return {"success": False, "error": str(e)}
    
    @measure_performance(endpoint_name="snmp_set")
    def set(self, oid: str, value: Any, value_type: str = "string") -> Dict[str, Any]:
        """
        Effectue un SNMP SET pour un OID spécifique.
        
        Args:
            oid: OID à modifier
            value: Nouvelle valeur
            value_type: Type de la valeur
            
        Returns:
            Résultat de l'opération
        """
        try:
            # Valider l'OID
            validated_oid = self._validate_oid(oid)
            
            # Valider le type de valeur
            if value_type not in ['string', 'integer', 'oid', 'ipaddress', 'counter', 'gauge', 'timeticks']:
                raise ValidationException(f"Type de valeur SNMP invalide: {value_type}")
            
            if self.base_url:
                data = {
                    'host': self.host,
                    'port': self.port,
                    'oid': validated_oid,
                    'value': value,
                    'value_type': value_type,
                    'version': self.credentials.version.value,
                    'timeout': self.timeout
                }
                
                self._add_credentials_to_data(data)
                
                return super().post("snmp/set", json_data=data)
            else:
                return self._direct_snmp_set(validated_oid, value, value_type)
            
        except ValidationException as e:
            logger.warning(f"Paramètres SNMP SET invalides: {e}")
            return {"success": False, "error": f"Paramètres invalides: {e.message}"}
        except Exception as e:
            logger.error(f"Erreur lors du SNMP SET: {e}")
            return {"success": False, "error": str(e)}
    
    @measure_performance(endpoint_name="snmp_system_info")
    def get_system_info(self) -> Dict[str, Any]:
        """
        Récupère les informations système via SNMP.
        
        Returns:
            Informations système
        """
        try:
            system_info = {}
            
            # Récupérer les OIDs système standard
            for name, oid in self.STANDARD_OIDS['system'].items():
                result = self.get(oid)
                if result.get("success", True) and "value" in result:
                    system_info[name] = result["value"]
            
            return {
                "success": True,
                "data": system_info,
                "host": self.host
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des infos système: {e}")
            return {"success": False, "error": str(e)}
    
    @measure_performance(endpoint_name="snmp_interface_list")
    def get_interface_list(self) -> Dict[str, Any]:
        """
        Récupère la liste des interfaces réseau.
        
        Returns:
            Liste des interfaces
        """
        try:
            # Récupérer le nombre d'interfaces
            if_number_result = self.get(self.STANDARD_OIDS['interfaces']['ifNumber'])
            if not if_number_result.get("success", True):
                return if_number_result
            
            # Walk sur la table des interfaces
            if_table_result = self.walk(self.STANDARD_OIDS['interfaces']['ifTable'])
            if not if_table_result.get("success", True):
                return if_table_result
            
            # Parser les résultats pour structurer les interfaces
            interfaces = self._parse_interface_table(if_table_result.get("data", {}))
            
            return {
                "success": True,
                "data": {
                    "interface_count": if_number_result.get("value", 0),
                    "interfaces": interfaces
                },
                "host": self.host
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des interfaces: {e}")
            return {"success": False, "error": str(e)}
    
    def get_interface_stats(self, interface_index: int) -> Dict[str, Any]:
        """
        Récupère les statistiques d'une interface spécifique.
        
        Args:
            interface_index: Index de l'interface
            
        Returns:
            Statistiques de l'interface
        """
        try:
            if not isinstance(interface_index, int) or interface_index < 1:
                raise ValidationException("L'index d'interface doit être un entier positif")
            
            stats = {}
            
            # OIDs de statistiques d'interface
            stat_oids = {
                'ifDescr': f"{self.STANDARD_OIDS['interfaces']['ifDescr']}.{interface_index}",
                'ifType': f"{self.STANDARD_OIDS['interfaces']['ifType']}.{interface_index}",
                'ifMtu': f"{self.STANDARD_OIDS['interfaces']['ifMtu']}.{interface_index}",
                'ifSpeed': f"{self.STANDARD_OIDS['interfaces']['ifSpeed']}.{interface_index}",
                'ifAdminStatus': f"{self.STANDARD_OIDS['interfaces']['ifAdminStatus']}.{interface_index}",
                'ifOperStatus': f"{self.STANDARD_OIDS['interfaces']['ifOperStatus']}.{interface_index}",
                'ifInOctets': f"{self.STANDARD_OIDS['interfaces']['ifInOctets']}.{interface_index}",
                'ifOutOctets': f"{self.STANDARD_OIDS['interfaces']['ifOutOctets']}.{interface_index}"
            }
            
            # Récupérer chaque statistique
            for name, oid in stat_oids.items():
                result = self.get(oid)
                if result.get("success", True) and "value" in result:
                    stats[name] = result["value"]
            
            # Enrichir avec des informations dérivées
            if 'ifInOctets' in stats and 'ifOutOctets' in stats:
                try:
                    stats['totalOctets'] = int(stats['ifInOctets']) + int(stats['ifOutOctets'])
                except:
                    pass
            
            return {
                "success": True,
                "data": {
                    "interface_index": interface_index,
                    "statistics": stats
                },
                "host": self.host
            }
            
        except ValidationException as e:
            logger.warning(f"Index d'interface invalide: {e}")
            return {"success": False, "error": f"Index invalide: {e.message}"}
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des stats d'interface: {e}")
            return {"success": False, "error": str(e)}
    
    def discover_neighbors(self) -> Dict[str, Any]:
        """
        Découvre les voisins via LLDP/CDP (si supporté).
        
        Returns:
            Liste des voisins découverts
        """
        try:
            neighbors = {}
            
            # OIDs LLDP standards
            lldp_oids = {
                'lldpRemTable': '1.0.8802.1.1.2.1.4.1',
                'lldpRemChassisId': '1.0.8802.1.1.2.1.4.1.1.5',
                'lldpRemPortId': '1.0.8802.1.1.2.1.4.1.1.7',
                'lldpRemSysName': '1.0.8802.1.1.2.1.4.1.1.9'
            }
            
            # Essayer LLDP d'abord
            lldp_result = self.walk(lldp_oids['lldpRemTable'])
            if lldp_result.get("success", True) and lldp_result.get("data"):
                neighbors['lldp'] = self._parse_lldp_neighbors(lldp_result["data"])
            
            # Fallback sur CDP si disponible
            if not neighbors:
                cdp_oids = {
                    'cdpCacheTable': '1.3.6.1.4.1.9.9.23.1.2.1',
                    'cdpCacheDeviceId': '1.3.6.1.4.1.9.9.23.1.2.1.1.6',
                    'cdpCacheDevicePort': '1.3.6.1.4.1.9.9.23.1.2.1.1.7'
                }
                
                cdp_result = self.walk(cdp_oids['cdpCacheTable'])
                if cdp_result.get("success", True) and cdp_result.get("data"):
                    neighbors['cdp'] = self._parse_cdp_neighbors(cdp_result["data"])
            
            return {
                "success": True,
                "data": neighbors,
                "host": self.host
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de la découverte des voisins: {e}")
            return {"success": False, "error": str(e)}
    
    def _validate_oid(self, oid: str) -> str:
        """Valide et normalise un OID SNMP."""
        validated = self.validators.validate({'oid': oid})
        normalized_oid = validated['oid']
        
        # Ajouter le point initial si manquant
        if not normalized_oid.startswith('.'):
            normalized_oid = '.' + normalized_oid
        
        return normalized_oid
    
    def _add_credentials_to_params(self, params: Dict[str, Any]):
        """Ajoute les credentials aux paramètres de requête (GET)."""
        if self.credentials.version in [SNMPVersion.V1, SNMPVersion.V2C]:
            params['community'] = self.credentials.community
        elif self.credentials.version == SNMPVersion.V3:
            params['username'] = self.credentials.username
            params['security_level'] = self.credentials.security_level.value
            if self.credentials.auth_protocol:
                params['auth_protocol'] = self.credentials.auth_protocol.value
                # Note: Ne pas passer les mots de passe en paramètres GET
    
    def _add_credentials_to_data(self, data: Dict[str, Any]):
        """Ajoute les credentials aux données de requête (POST)."""
        if self.credentials.version in [SNMPVersion.V1, SNMPVersion.V2C]:
            data['community'] = self.credentials.community
        elif self.credentials.version == SNMPVersion.V3:
            data['username'] = self.credentials.username
            data['security_level'] = self.credentials.security_level.value
            if self.credentials.auth_protocol:
                data['auth_protocol'] = self.credentials.auth_protocol.value
                data['auth_password'] = self.credentials.auth_password
            if self.credentials.priv_protocol:
                data['priv_protocol'] = self.credentials.priv_protocol.value
                data['priv_password'] = self.credentials.priv_password
    
    def _direct_snmp_get(self, oid: str) -> Dict[str, Any]:
        """Implémentation directe SNMP GET (nécessiterait pysnmp)."""
        # Cette méthode nécessiterait une bibliothèque SNMP comme pysnmp
        # Pour l'instant, retourner une erreur explicative
        return {
            "success": False,
            "error": "SNMP direct non implémenté. Utilisez une API REST SNMP."
        }
    
    def _direct_snmp_walk(self, oid: str) -> Dict[str, Any]:
        """Implémentation directe SNMP WALK (nécessiterait pysnmp)."""
        return {
            "success": False,
            "error": "SNMP direct non implémenté. Utilisez une API REST SNMP."
        }
    
    def _direct_snmp_set(self, oid: str, value: Any, value_type: str) -> Dict[str, Any]:
        """Implémentation directe SNMP SET (nécessiterait pysnmp)."""
        return {
            "success": False,
            "error": "SNMP direct non implémenté. Utilisez une API REST SNMP."
        }
    
    def _parse_interface_table(self, if_table_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse les données de la table des interfaces."""
        interfaces = {}
        
        # Grouper les OIDs par index d'interface
        for oid, value in if_table_data.items():
            # Extraire l'index d'interface depuis l'OID
            parts = oid.split('.')
            if len(parts) >= 2:
                try:
                    if_index = int(parts[-1])
                    if if_index not in interfaces:
                        interfaces[if_index] = {'index': if_index}
                    
                    # Déterminer le type d'information
                    if '.2.' in oid:  # ifDescr
                        interfaces[if_index]['description'] = value
                    elif '.3.' in oid:  # ifType
                        interfaces[if_index]['type'] = value
                    elif '.4.' in oid:  # ifMtu
                        interfaces[if_index]['mtu'] = value
                    elif '.5.' in oid:  # ifSpeed
                        interfaces[if_index]['speed'] = value
                    elif '.7.' in oid:  # ifAdminStatus
                        interfaces[if_index]['admin_status'] = value
                    elif '.8.' in oid:  # ifOperStatus
                        interfaces[if_index]['oper_status'] = value
                    
                except ValueError:
                    continue
        
        return list(interfaces.values())
    
    def _parse_lldp_neighbors(self, lldp_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse les données des voisins LLDP."""
        neighbors = []
        
        # Grouper les données LLDP par neighbor
        neighbor_data = {}
        for oid, value in lldp_data.items():
            # Parser l'OID pour extraire les index
            parts = oid.split('.')
            if len(parts) >= 4:
                try:
                    neighbor_key = '.'.join(parts[-3:])  # Utiliser les 3 derniers comme clé
                    if neighbor_key not in neighbor_data:
                        neighbor_data[neighbor_key] = {}
                    
                    if '1.5.' in oid:  # Chassis ID
                        neighbor_data[neighbor_key]['chassis_id'] = value
                    elif '1.7.' in oid:  # Port ID
                        neighbor_data[neighbor_key]['port_id'] = value
                    elif '1.9.' in oid:  # System Name
                        neighbor_data[neighbor_key]['system_name'] = value
                        
                except:
                    continue
        
        # Convertir en liste
        for neighbor_info in neighbor_data.values():
            if neighbor_info:  # Seulement si on a des données
                neighbors.append(neighbor_info)
        
        return neighbors
    
    def _parse_cdp_neighbors(self, cdp_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse les données des voisins CDP."""
        neighbors = []
        
        # Grouper les données CDP par neighbor  
        neighbor_data = {}
        for oid, value in cdp_data.items():
            parts = oid.split('.')
            if len(parts) >= 2:
                try:
                    neighbor_key = parts[-1]  # Utiliser le dernier index comme clé
                    if neighbor_key not in neighbor_data:
                        neighbor_data[neighbor_key] = {}
                    
                    if '1.6.' in oid:  # Device ID
                        neighbor_data[neighbor_key]['device_id'] = value
                    elif '1.7.' in oid:  # Device Port
                        neighbor_data[neighbor_key]['device_port'] = value
                        
                except:
                    continue
        
        # Convertir en liste
        for neighbor_info in neighbor_data.values():
            if neighbor_info:
                neighbors.append(neighbor_info)
        
        return neighbors 