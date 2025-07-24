"""
Définition de l'interface du client SNMP.

Ce module définit l'interface que doivent implémenter les adaptateurs SNMP.
C'est un port sortant selon la terminologie de l'architecture hexagonale.
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Dict, List, Optional, Any, Union


class SNMPVersion(Enum):
    """Versions du protocole SNMP supportées."""
    V1 = "1"
    V2C = "2c"
    V3 = "3"


class SNMPSecurityLevel(Enum):
    """Niveaux de sécurité pour SNMP v3."""
    NO_AUTH_NO_PRIV = "noAuthNoPriv"
    AUTH_NO_PRIV = "authNoPriv"
    AUTH_PRIV = "authPriv"


class SNMPAuthProtocol(Enum):
    """Protocoles d'authentification pour SNMP v3."""
    MD5 = "MD5"
    SHA = "SHA"
    SHA224 = "SHA224"
    SHA256 = "SHA256"
    SHA384 = "SHA384"
    SHA512 = "SHA512"


class SNMPPrivProtocol(Enum):
    """Protocoles de confidentialité pour SNMP v3."""
    DES = "DES"
    AES = "AES"
    AES128 = "AES128"
    AES192 = "AES192"
    AES256 = "AES256"


class SNMPCredentials:
    """Informations d'authentification pour SNMP."""
    
    def __init__(
        self, 
        version: SNMPVersion,
        community: str = "public",
        username: Optional[str] = None,
        auth_protocol: Optional[SNMPAuthProtocol] = None,
        auth_password: Optional[str] = None,
        priv_protocol: Optional[SNMPPrivProtocol] = None,
        priv_password: Optional[str] = None,
        security_level: Optional[SNMPSecurityLevel] = None
    ):
        self.version = version
        self.community = community
        self.username = username
        self.auth_protocol = auth_protocol
        self.auth_password = auth_password
        self.priv_protocol = priv_protocol
        self.priv_password = priv_password
        self.security_level = security_level


class SNMPError(Exception):
    """Erreur lors d'une opération SNMP."""
    pass


class TimeoutError(SNMPError):
    """Erreur de timeout lors d'une opération SNMP."""
    pass


class AuthenticationError(SNMPError):
    """Erreur d'authentification lors d'une opération SNMP."""
    pass


class SNMPClientPort(ABC):
    """
    Interface pour les clients SNMP.
    
    Cette interface définit les opérations que doit supporter un client SNMP
    pour être utilisé par le domaine.
    """
    
    @abstractmethod
    def get(self, ip_address: str, oid: str, credentials: SNMPCredentials, port: int = 161, timeout: int = 1, retries: int = 3) -> Any:
        """
        Récupère la valeur d'un OID via SNMP GET.
        
        Args:
            ip_address: Adresse IP de l'équipement
            oid: OID à récupérer
            credentials: Informations d'authentification
            port: Port SNMP
            timeout: Timeout en secondes
            retries: Nombre de tentatives
            
        Returns:
            Valeur de l'OID
            
        Raises:
            TimeoutError: En cas de timeout
            AuthenticationError: En cas d'erreur d'authentification
            SNMPError: Pour les autres erreurs SNMP
        """
        pass
    
    @abstractmethod
    def get_bulk(self, ip_address: str, oids: List[str], credentials: SNMPCredentials, port: int = 161, timeout: int = 1, retries: int = 3) -> Dict[str, Any]:
        """
        Récupère les valeurs de plusieurs OIDs via SNMP GET-BULK.
        
        Args:
            ip_address: Adresse IP de l'équipement
            oids: Liste d'OIDs à récupérer
            credentials: Informations d'authentification
            port: Port SNMP
            timeout: Timeout en secondes
            retries: Nombre de tentatives
            
        Returns:
            Dictionnaire {OID: valeur}
            
        Raises:
            TimeoutError: En cas de timeout
            AuthenticationError: En cas d'erreur d'authentification
            SNMPError: Pour les autres erreurs SNMP
        """
        pass
    
    @abstractmethod
    def walk(self, ip_address: str, oid_prefix: str, credentials: SNMPCredentials, port: int = 161, timeout: int = 1, retries: int = 3) -> Dict[str, Any]:
        """
        Parcourt une branche d'OIDs via SNMP WALK.
        
        Args:
            ip_address: Adresse IP de l'équipement
            oid_prefix: Préfixe d'OID à parcourir
            credentials: Informations d'authentification
            port: Port SNMP
            timeout: Timeout en secondes
            retries: Nombre de tentatives
            
        Returns:
            Dictionnaire {OID: valeur}
            
        Raises:
            TimeoutError: En cas de timeout
            AuthenticationError: En cas d'erreur d'authentification
            SNMPError: Pour les autres erreurs SNMP
        """
        pass
    
    @abstractmethod
    def set(self, ip_address: str, oid: str, value: Any, value_type: str, credentials: SNMPCredentials, port: int = 161, timeout: int = 1, retries: int = 3) -> bool:
        """
        Définit la valeur d'un OID via SNMP SET.
        
        Args:
            ip_address: Adresse IP de l'équipement
            oid: OID à définir
            value: Valeur à définir
            value_type: Type de la valeur (INTEGER, OCTETSTR, etc.)
            credentials: Informations d'authentification
            port: Port SNMP
            timeout: Timeout en secondes
            retries: Nombre de tentatives
            
        Returns:
            True si l'opération a réussi
            
        Raises:
            TimeoutError: En cas de timeout
            AuthenticationError: En cas d'erreur d'authentification
            SNMPError: Pour les autres erreurs SNMP
        """
        pass
    
    @abstractmethod
    def test_connectivity(self, ip_address: str, credentials: SNMPCredentials, port: int = 161, timeout: int = 1, retries: int = 3) -> bool:
        """
        Teste la connectivité SNMP avec un équipement.
        
        Args:
            ip_address: Adresse IP de l'équipement
            credentials: Informations d'authentification
            port: Port SNMP
            timeout: Timeout en secondes
            retries: Nombre de tentatives
            
        Returns:
            True si l'équipement est accessible
        """
        pass
    
    @abstractmethod
    def get_sysinfo(self, ip_address: str, credentials: SNMPCredentials, port: int = 161, timeout: int = 1, retries: int = 3) -> Dict[str, Any]:
        """
        Récupère les informations système via SNMP.
        
        Args:
            ip_address: Adresse IP de l'équipement
            credentials: Informations d'authentification
            port: Port SNMP
            timeout: Timeout en secondes
            retries: Nombre de tentatives
            
        Returns:
            Dictionnaire contenant les informations système
            
        Raises:
            TimeoutError: En cas de timeout
            AuthenticationError: En cas d'erreur d'authentification
            SNMPError: Pour les autres erreurs SNMP
        """
        pass
    
    @abstractmethod
    def get_interfaces(self, ip_address: str, credentials: SNMPCredentials, port: int = 161, timeout: int = 1, retries: int = 3) -> List[Dict[str, Any]]:
        """
        Récupère la liste des interfaces via SNMP.
        
        Args:
            ip_address: Adresse IP de l'équipement
            credentials: Informations d'authentification
            port: Port SNMP
            timeout: Timeout en secondes
            retries: Nombre de tentatives
            
        Returns:
            Liste de dictionnaires contenant les informations des interfaces
            
        Raises:
            TimeoutError: En cas de timeout
            AuthenticationError: En cas d'erreur d'authentification
            SNMPError: Pour les autres erreurs SNMP
        """
        pass 