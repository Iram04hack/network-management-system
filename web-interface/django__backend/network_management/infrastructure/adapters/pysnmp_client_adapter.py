"""
Adaptateur SNMP utilisant la bibliothèque pysnmp.

Cet adaptateur implémente l'interface SNMPClientPort en utilisant
la bibliothèque pysnmp pour les opérations SNMP réelles.
"""

import logging
from typing import Dict, List, Optional, Any, Union

try:
    from pysnmp.hlapi import *
    from pysnmp.error import PySnmpError
    PYSNMP_AVAILABLE = True
except ImportError:
    PYSNMP_AVAILABLE = False

from ...domain.ports.snmp_client_port import (
    SNMPClientPort, SNMPCredentials, SNMPVersion, SNMPSecurityLevel,
    SNMPAuthProtocol, SNMPPrivProtocol, SNMPError, TimeoutError, AuthenticationError
)

logger = logging.getLogger(__name__)


class PySnmpClientAdapter(SNMPClientPort):
    """
    Adaptateur SNMP utilisant pysnmp.
    
    Implémente l'interface SNMPClientPort en utilisant la bibliothèque pysnmp
    pour effectuer les opérations SNMP réelles.
    """
    
    def __init__(self):
        """Initialise l'adaptateur SNMP."""
        if not PYSNMP_AVAILABLE:
            logger.warning("⚠️ pysnmp non disponible - fonctionnalités SNMP désactivées")
            self._available = False
        else:
            self._available = True
            logger.info("✅ Adaptateur SNMP pysnmp initialisé")
    
    def _check_availability(self):
        """Vérifie que pysnmp est disponible."""
        if not self._available:
            raise SNMPError("pysnmp n'est pas disponible. Installez-le avec: pip install pysnmp")
    
    def _build_auth_data(self, credentials: SNMPCredentials):
        """Construit les données d'authentification pour pysnmp."""
        if credentials.version == SNMPVersion.V1:
            return CommunityData(credentials.community, mpModel=0)
        elif credentials.version == SNMPVersion.V2C:
            return CommunityData(credentials.community, mpModel=1)
        elif credentials.version == SNMPVersion.V3:
            # Configuration SNMP v3
            auth_protocol = None
            priv_protocol = None
            
            if credentials.auth_protocol:
                auth_map = {
                    SNMPAuthProtocol.MD5: usmHMACMD5AuthProtocol,
                    SNMPAuthProtocol.SHA: usmHMACSHAAuthProtocol,
                }
                auth_protocol = auth_map.get(credentials.auth_protocol)
            
            if credentials.priv_protocol:
                priv_map = {
                    SNMPPrivProtocol.DES: usmDESPrivProtocol,
                    SNMPPrivProtocol.AES: usmAesCfb128Protocol,
                }
                priv_protocol = priv_map.get(credentials.priv_protocol)
            
            return UsmUserData(
                credentials.username or '',
                authKey=credentials.auth_password,
                privKey=credentials.priv_password,
                authProtocol=auth_protocol,
                privProtocol=priv_protocol
            )
        else:
            raise SNMPError(f"Version SNMP non supportée: {credentials.version}")
    
    def _build_transport_target(self, ip_address: str, port: int, timeout: int, retries: int):
        """Construit la cible de transport pour pysnmp."""
        return UdpTransportTarget((ip_address, port), timeout=timeout, retries=retries)
    
    def _handle_pysnmp_error(self, error):
        """Gère les erreurs pysnmp et les convertit en exceptions du domaine."""
        error_str = str(error).lower()
        
        if 'timeout' in error_str or 'no response' in error_str:
            raise TimeoutError(f"Timeout SNMP: {error}")
        elif 'authentication' in error_str or 'wrong digest' in error_str:
            raise AuthenticationError(f"Erreur d'authentification SNMP: {error}")
        else:
            raise SNMPError(f"Erreur SNMP: {error}")
    
    def get(self, ip_address: str, oid: str, credentials: SNMPCredentials, port: int = 161, timeout: int = 1, retries: int = 3) -> Any:
        """Récupère la valeur d'un OID via SNMP GET."""
        self._check_availability()
        
        try:
            auth_data = self._build_auth_data(credentials)
            transport_target = self._build_transport_target(ip_address, port, timeout, retries)
            
            for (errorIndication, errorStatus, errorIndex, varBinds) in getCmd(
                SnmpEngine(),
                auth_data,
                transport_target,
                ContextData(),
                ObjectType(ObjectIdentity(oid))
            ):
                if errorIndication:
                    self._handle_pysnmp_error(errorIndication)
                elif errorStatus:
                    self._handle_pysnmp_error(f"{errorStatus.prettyPrint()} at {errorIndex and varBinds[int(errorIndex) - 1][0] or '?'}")
                else:
                    # Succès - retourner la valeur
                    for varBind in varBinds:
                        return varBind[1].prettyPrint()
                    
        except PySnmpError as e:
            self._handle_pysnmp_error(e)
        except Exception as e:
            raise SNMPError(f"Erreur inattendue: {e}")
    
    def get_bulk(self, ip_address: str, oids: List[str], credentials: SNMPCredentials, port: int = 161, timeout: int = 1, retries: int = 3) -> Dict[str, Any]:
        """Récupère les valeurs de plusieurs OIDs via SNMP GET-BULK."""
        self._check_availability()
        
        try:
            auth_data = self._build_auth_data(credentials)
            transport_target = self._build_transport_target(ip_address, port, timeout, retries)
            
            object_types = [ObjectType(ObjectIdentity(oid)) for oid in oids]
            result = {}
            
            for (errorIndication, errorStatus, errorIndex, varBinds) in bulkCmd(
                SnmpEngine(),
                auth_data,
                transport_target,
                ContextData(),
                0, 50,  # nonRepeaters, maxRepetitions
                *object_types
            ):
                if errorIndication:
                    self._handle_pysnmp_error(errorIndication)
                elif errorStatus:
                    self._handle_pysnmp_error(f"{errorStatus.prettyPrint()} at {errorIndex and varBinds[int(errorIndex) - 1][0] or '?'}")
                else:
                    for varBind in varBinds:
                        oid_str = varBind[0].prettyPrint()
                        value = varBind[1].prettyPrint()
                        result[oid_str] = value
                        
            return result
                    
        except PySnmpError as e:
            self._handle_pysnmp_error(e)
        except Exception as e:
            raise SNMPError(f"Erreur inattendue: {e}")
    
    def walk(self, ip_address: str, oid_prefix: str, credentials: SNMPCredentials, port: int = 161, timeout: int = 1, retries: int = 3) -> Dict[str, Any]:
        """Parcourt une branche d'OIDs via SNMP WALK."""
        self._check_availability()
        
        try:
            auth_data = self._build_auth_data(credentials)
            transport_target = self._build_transport_target(ip_address, port, timeout, retries)
            
            result = {}
            
            for (errorIndication, errorStatus, errorIndex, varBinds) in nextCmd(
                SnmpEngine(),
                auth_data,
                transport_target,
                ContextData(),
                ObjectType(ObjectIdentity(oid_prefix)),
                lexicographicMode=False
            ):
                if errorIndication:
                    self._handle_pysnmp_error(errorIndication)
                elif errorStatus:
                    self._handle_pysnmp_error(f"{errorStatus.prettyPrint()} at {errorIndex and varBinds[int(errorIndex) - 1][0] or '?'}")
                else:
                    for varBind in varBinds:
                        oid_str = varBind[0].prettyPrint()
                        value = varBind[1].prettyPrint()
                        result[oid_str] = value
                        
            return result
                    
        except PySnmpError as e:
            self._handle_pysnmp_error(e)
        except Exception as e:
            raise SNMPError(f"Erreur inattendue: {e}")
    
    def set(self, ip_address: str, oid: str, value: Any, value_type: str, credentials: SNMPCredentials, port: int = 161, timeout: int = 1, retries: int = 3) -> bool:
        """Définit la valeur d'un OID via SNMP SET."""
        self._check_availability()
        
        try:
            auth_data = self._build_auth_data(credentials)
            transport_target = self._build_transport_target(ip_address, port, timeout, retries)
            
            # Conversion du type de valeur
            type_map = {
                'INTEGER': Integer,
                'OCTETSTR': OctetString,
                'IPADDRESS': IpAddress,
                'COUNTER32': Counter32,
                'GAUGE32': Gauge32,
                'TIMETICKS': TimeTicks,
            }
            
            value_class = type_map.get(value_type.upper(), OctetString)
            snmp_value = value_class(value)
            
            for (errorIndication, errorStatus, errorIndex, varBinds) in setCmd(
                SnmpEngine(),
                auth_data,
                transport_target,
                ContextData(),
                ObjectType(ObjectIdentity(oid), snmp_value)
            ):
                if errorIndication:
                    self._handle_pysnmp_error(errorIndication)
                elif errorStatus:
                    self._handle_pysnmp_error(f"{errorStatus.prettyPrint()} at {errorIndex and varBinds[int(errorIndex) - 1][0] or '?'}")
                else:
                    return True
                    
        except PySnmpError as e:
            self._handle_pysnmp_error(e)
        except Exception as e:
            raise SNMPError(f"Erreur inattendue: {e}")
        
        return False
    
    def test_connectivity(self, ip_address: str, credentials: SNMPCredentials, port: int = 161, timeout: int = 1, retries: int = 3) -> bool:
        """Teste la connectivité SNMP avec un équipement."""
        try:
            # Test avec sysDescr (1.3.6.1.2.1.1.1.0)
            result = self.get(ip_address, '1.3.6.1.2.1.1.1.0', credentials, port, timeout, retries)
            return result is not None
        except (SNMPError, TimeoutError, AuthenticationError):
            return False
    
    def get_sysinfo(self, ip_address: str, credentials: SNMPCredentials, port: int = 161, timeout: int = 1, retries: int = 3) -> Dict[str, Any]:
        """Récupère les informations système via SNMP."""
        system_oids = {
            'sysDescr': '1.3.6.1.2.1.1.1.0',
            'sysObjectID': '1.3.6.1.2.1.1.2.0',
            'sysUpTime': '1.3.6.1.2.1.1.3.0',
            'sysContact': '1.3.6.1.2.1.1.4.0',
            'sysName': '1.3.6.1.2.1.1.5.0',
            'sysLocation': '1.3.6.1.2.1.1.6.0',
            'sysServices': '1.3.6.1.2.1.1.7.0',
        }
        
        result = {}
        for name, oid in system_oids.items():
            try:
                value = self.get(ip_address, oid, credentials, port, timeout, retries)
                result[name] = value
            except SNMPError as e:
                logger.warning(f"Impossible de récupérer {name}: {e}")
                result[name] = None
                
        return result
    
    def get_interfaces(self, ip_address: str, credentials: SNMPCredentials, port: int = 161, timeout: int = 1, retries: int = 3) -> List[Dict[str, Any]]:
        """Récupère la liste des interfaces via SNMP."""
        # OIDs pour les interfaces (table ifTable)
        interface_oids = {
            'ifIndex': '1.3.6.1.2.1.2.2.1.1',
            'ifDescr': '1.3.6.1.2.1.2.2.1.2',
            'ifType': '1.3.6.1.2.1.2.2.1.3',
            'ifMtu': '1.3.6.1.2.1.2.2.1.4',
            'ifSpeed': '1.3.6.1.2.1.2.2.1.5',
            'ifPhysAddress': '1.3.6.1.2.1.2.2.1.6',
            'ifAdminStatus': '1.3.6.1.2.1.2.2.1.7',
            'ifOperStatus': '1.3.6.1.2.1.2.2.1.8',
            'ifName': '1.3.6.1.2.1.31.1.1.1.1',
        }
        
        interfaces_data = {}
        
        # Récupérer toutes les données des interfaces
        for field_name, base_oid in interface_oids.items():
            try:
                walk_result = self.walk(ip_address, base_oid, credentials, port, timeout, retries)
                for oid, value in walk_result.items():
                    # Extraire l'index de l'interface depuis l'OID
                    oid_parts = oid.split('.')
                    if len(oid_parts) > len(base_oid.split('.')):
                        interface_index = oid_parts[-1]
                        
                        if interface_index not in interfaces_data:
                            interfaces_data[interface_index] = {'ifIndex': interface_index}
                        
                        interfaces_data[interface_index][field_name] = value
                        
            except SNMPError as e:
                logger.warning(f"Impossible de récupérer {field_name}: {e}")
        
        # Convertir en liste de dictionnaires
        interfaces_list = list(interfaces_data.values())
        
        return interfaces_list 