"""
Package d'adaptateurs pour différents équipements réseau.

Ce package contient les adaptateurs permettant de configurer la QoS
sur différents types d'équipements réseau.
"""

from .cisco_qos_adapter import CiscoQoSAdapter
from .linux_tc_adapter import LinuxTCAdapter
from .juniper_adapter import JuniperQoSAdapter


class NetworkDeviceAdapterFactory:
    """
    Factory pour créer les adaptateurs d'équipements réseau appropriés.
    """
    
    @classmethod
    def create_adapter(cls, device_type: str, **kwargs):
        """
        Crée un adaptateur selon le type d'équipement.
        
        Args:
            device_type: Type d'équipement ('cisco', 'juniper', 'linux', etc.)
            **kwargs: Arguments supplémentaires pour l'adaptateur
            
        Returns:
            Instance d'adaptateur approprié
            
        Raises:
            ValueError: Si le type d'équipement n'est pas supporté
        """
        device_type = device_type.lower()
        
        if device_type in ('cisco', 'ios', 'ios-xe', 'nexus'):
            network_connector = kwargs.get('network_connector')
            return CiscoQoSAdapter(network_connector)
            
        elif device_type in ('juniper', 'junos', 'mx', 'ex', 'qfx'):
            network_connector = kwargs.get('network_connector')
            return JuniperQoSAdapter(network_connector)
            
        elif device_type in ('linux', 'ubuntu', 'centos', 'debian'):
            ssh_connector = kwargs.get('ssh_connector')
            return LinuxTCAdapter(ssh_connector)
            
        else:
            raise ValueError(f"Type d'équipement non supporté: {device_type}")
    
    @classmethod
    def get_supported_device_types(cls) -> list:
        """
        Retourne la liste des types d'équipements supportés.
        
        Returns:
            Liste des types d'équipements supportés
        """
        return [
            'cisco', 'ios', 'ios-xe', 'nexus',
            'juniper', 'junos', 'mx', 'ex', 'qfx',
            'linux', 'ubuntu', 'centos', 'debian'
        ]


__all__ = [
    'CiscoQoSAdapter',
    'LinuxTCAdapter', 
    'JuniperQoSAdapter',
    'NetworkDeviceAdapterFactory'
]