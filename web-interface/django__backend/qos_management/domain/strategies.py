"""
Stratégies pour la classification du trafic QoS.

Ce module implémente le pattern Strategy pour la classification du trafic réseau
selon différents critères, permettant une extension facile des méthodes de correspondance.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Tuple, List
import ipaddress


class PacketMatchStrategy(ABC):
    """
    Interface abstraite pour les stratégies de correspondance de paquets.
    Cette interface définit le contrat que doivent respecter toutes les
    stratégies de correspondance.
    """
    
    @abstractmethod
    def matches(self, packet_data: Dict[str, Any], criteria: Any) -> bool:
        """
        Vérifie si un paquet correspond au critère spécifié.
        
        Args:
            packet_data: Données du paquet à vérifier
            criteria: Critère de correspondance spécifique à la stratégie
            
        Returns:
            True si le paquet correspond au critère, False sinon
        """
        pass


class ProtocolMatchStrategy(PacketMatchStrategy):
    """
    Stratégie pour la correspondance basée sur le protocole.
    """
    
    def matches(self, packet_data: Dict[str, Any], criteria: str) -> bool:
        """
        Vérifie si le protocole du paquet correspond au critère.
        
        Args:
            packet_data: Données du paquet contenant la clé 'protocol'
            criteria: Protocole à vérifier ('tcp', 'udp', etc.) ou 'any'
            
        Returns:
            True si le protocole correspond ou si le critère est 'any'
        """
        if criteria == 'any':
            return True
            
        protocol = packet_data.get('protocol')
        return protocol is not None and protocol == criteria


class IpMatchStrategy(PacketMatchStrategy):
    """
    Stratégie pour la correspondance basée sur les adresses IP.
    """
    
    def matches(self, packet_data: Dict[str, Any], criteria: Optional[str]) -> bool:
        """
        Vérifie si l'adresse IP du paquet correspond au critère.
        
        Args:
            packet_data: Données du paquet contenant la clé 'src_ip' ou 'dst_ip'
            criteria: Adresse IP ou CIDR à vérifier, ou None si pas de restriction
            
        Returns:
            True si l'IP correspond au critère ou si le critère est None
        """
        if criteria is None:
            return True
            
        ip = packet_data.get('ip')
        if not ip:
            return False
        
        try:
            if '/' in criteria:
                # Vérification CIDR
                network = ipaddress.ip_network(criteria, strict=False)
                ip_obj = ipaddress.ip_address(ip)
                return ip_obj in network
            else:
                # Vérification IP exacte
                return ip == criteria
        except ValueError:
            # En cas d'erreur de format IP, on considère qu'il n'y a pas de correspondance
            return False


class SourceIpMatchStrategy(IpMatchStrategy):
    """
    Stratégie pour la correspondance basée sur l'adresse IP source.
    """
    
    def matches(self, packet_data: Dict[str, Any], criteria: Optional[str]) -> bool:
        """
        Vérifie si l'adresse IP source du paquet correspond au critère.
        
        Args:
            packet_data: Données du paquet contenant la clé 'src_ip'
            criteria: Adresse IP source ou CIDR à vérifier, ou None si pas de restriction
            
        Returns:
            True si l'IP source correspond au critère ou si le critère est None
        """
        if criteria is None:
            return True
            
        packet_data_with_ip = {**packet_data, 'ip': packet_data.get('src_ip')}
        return super().matches(packet_data_with_ip, criteria)


class DestinationIpMatchStrategy(IpMatchStrategy):
    """
    Stratégie pour la correspondance basée sur l'adresse IP destination.
    """
    
    def matches(self, packet_data: Dict[str, Any], criteria: Optional[str]) -> bool:
        """
        Vérifie si l'adresse IP destination du paquet correspond au critère.
        
        Args:
            packet_data: Données du paquet contenant la clé 'dst_ip'
            criteria: Adresse IP destination ou CIDR à vérifier, ou None si pas de restriction
            
        Returns:
            True si l'IP destination correspond au critère ou si le critère est None
        """
        if criteria is None:
            return True
            
        packet_data_with_ip = {**packet_data, 'ip': packet_data.get('dst_ip')}
        return super().matches(packet_data_with_ip, criteria)


class PortMatchStrategy(PacketMatchStrategy):
    """
    Stratégie pour la correspondance basée sur le port.
    """
    
    def matches(self, packet_data: Dict[str, Any], criteria: int) -> bool:
        """
        Vérifie si le port du paquet correspond au critère.
        
        Args:
            packet_data: Données du paquet contenant la clé 'port'
            criteria: Port à vérifier ou 0 pour tous les ports
            
        Returns:
            True si le port correspond au critère ou si le critère est 0
        """
        if criteria == 0:
            # Si le critère est 0, cela signifie tous les ports
            return True
            
        port = packet_data.get('port')
        return port is not None and port == criteria


class PortRangeMatchStrategy(PacketMatchStrategy):
    """
    Stratégie pour la correspondance basée sur une plage de ports.
    """
    
    def matches(self, packet_data: Dict[str, Any], criteria: Tuple[int, int]) -> bool:
        """
        Vérifie si le port du paquet est dans la plage spécifiée.
        
        Args:
            packet_data: Données du paquet contenant la clé 'port'
            criteria: Tuple (port_début, port_fin) ou (0, 0) pour tous les ports
            
        Returns:
            True si le port est dans la plage ou si la plage est (0, 0)
        """
        start_port, end_port = criteria
        
        if start_port == 0 and end_port == 0:
            # Si la plage est (0, 0), cela signifie tous les ports
            return True
            
        port = packet_data.get('port')
        if port is None:
            return False
            
        return start_port <= port <= end_port


class SourcePortMatchStrategy(PortMatchStrategy):
    """
    Stratégie pour la correspondance basée sur le port source.
    """
    
    def matches(self, packet_data: Dict[str, Any], criteria: int) -> bool:
        """
        Vérifie si le port source du paquet correspond au critère.
        
        Args:
            packet_data: Données du paquet contenant la clé 'src_port'
            criteria: Port source à vérifier ou 0 pour tous les ports
            
        Returns:
            True si le port source correspond au critère ou si le critère est 0
        """
        if criteria == 0:
            return True
            
        packet_data_with_port = {**packet_data, 'port': packet_data.get('src_port')}
        return super().matches(packet_data_with_port, criteria)


class DestinationPortMatchStrategy(PortMatchStrategy):
    """
    Stratégie pour la correspondance basée sur le port destination.
    """
    
    def matches(self, packet_data: Dict[str, Any], criteria: int) -> bool:
        """
        Vérifie si le port destination du paquet correspond au critère.
        
        Args:
            packet_data: Données du paquet contenant la clé 'dst_port'
            criteria: Port destination à vérifier ou 0 pour tous les ports
            
        Returns:
            True si le port destination correspond au critère ou si le critère est 0
        """
        if criteria == 0:
            return True
            
        packet_data_with_port = {**packet_data, 'port': packet_data.get('dst_port')}
        return super().matches(packet_data_with_port, criteria)


class SourcePortRangeMatchStrategy(PortRangeMatchStrategy):
    """
    Stratégie pour la correspondance basée sur une plage de ports sources.
    """
    
    def matches(self, packet_data: Dict[str, Any], criteria: Tuple[int, int]) -> bool:
        """
        Vérifie si le port source du paquet est dans la plage spécifiée.
        
        Args:
            packet_data: Données du paquet contenant la clé 'src_port'
            criteria: Tuple (port_début, port_fin) ou (0, 0) pour tous les ports
            
        Returns:
            True si le port source est dans la plage ou si la plage est (0, 0)
        """
        start_port, end_port = criteria
        
        if start_port == 0 and end_port == 0:
            return True
            
        packet_data_with_port = {**packet_data, 'port': packet_data.get('src_port')}
        return super().matches(packet_data_with_port, criteria)


class DestinationPortRangeMatchStrategy(PortRangeMatchStrategy):
    """
    Stratégie pour la correspondance basée sur une plage de ports destinations.
    """
    
    def matches(self, packet_data: Dict[str, Any], criteria: Tuple[int, int]) -> bool:
        """
        Vérifie si le port destination du paquet est dans la plage spécifiée.
        
        Args:
            packet_data: Données du paquet contenant la clé 'dst_port'
            criteria: Tuple (port_début, port_fin) ou (0, 0) pour tous les ports
            
        Returns:
            True si le port destination est dans la plage ou si la plage est (0, 0)
        """
        start_port, end_port = criteria
        
        if start_port == 0 and end_port == 0:
            return True
            
        packet_data_with_port = {**packet_data, 'port': packet_data.get('dst_port')}
        return super().matches(packet_data_with_port, criteria)


class CompositeMatchStrategy(PacketMatchStrategy):
    """
    Stratégie composite qui combine plusieurs stratégies de correspondance.
    
    Cette stratégie implémente le pattern Composite pour permettre la composition
    de plusieurs stratégies de correspondance.
    """
    
    def __init__(self):
        """Initialise une stratégie composite vide."""
        self.strategies = []
        
    def add_strategy(self, strategy: PacketMatchStrategy, criteria: Any) -> None:
        """
        Ajoute une stratégie à la composition.
        
        Args:
            strategy: Stratégie à ajouter
            criteria: Critère associé à la stratégie
        """
        self.strategies.append((strategy, criteria))
        
    def matches(self, packet_data: Dict[str, Any], criteria: Any = None) -> bool:
        """
        Vérifie si le paquet correspond à toutes les stratégies.
        
        Args:
            packet_data: Données du paquet à vérifier
            criteria: Non utilisé, maintenu pour compatibilité
            
        Returns:
            True si le paquet correspond à toutes les stratégies, False sinon
        """
        # Si aucune stratégie n'est présente, on considère que ça correspond
        if not self.strategies:
            return True
            
        # Vérifier toutes les stratégies
        for strategy, criteria in self.strategies:
            if not strategy.matches(packet_data, criteria):
                return False
                
        return True


class DscpMatchStrategy(PacketMatchStrategy):
    """
    Stratégie pour la correspondance basée sur le marquage DSCP.
    """
    
    def matches(self, packet_data: Dict[str, Any], criteria: Optional[str]) -> bool:
        """
        Vérifie si le marquage DSCP du paquet correspond au critère.
        
        Args:
            packet_data: Données du paquet contenant la clé 'dscp'
            criteria: Valeur DSCP à vérifier (ex: 'AF21', 'EF'), ou None
            
        Returns:
            True si le DSCP correspond au critère ou si le critère est None
        """
        if criteria is None:
            return True
            
        dscp = packet_data.get('dscp')
        return dscp is not None and dscp == criteria


class VlanMatchStrategy(PacketMatchStrategy):
    """
    Stratégie pour la correspondance basée sur le VLAN ID.
    """
    
    def matches(self, packet_data: Dict[str, Any], criteria: Optional[int]) -> bool:
        """
        Vérifie si le VLAN ID du paquet correspond au critère.
        
        Args:
            packet_data: Données du paquet contenant la clé 'vlan'
            criteria: VLAN ID à vérifier, ou None
            
        Returns:
            True si le VLAN correspond au critère ou si le critère est None
        """
        if criteria is None:
            return True
            
        vlan = packet_data.get('vlan')
        return vlan is not None and vlan == criteria


class PacketMatchStrategyFactory:
    """
    Factory pour créer des stratégies de correspondance.
    """
    
    @staticmethod
    def create_strategy(strategy_type: str) -> PacketMatchStrategy:
        """
        Crée une stratégie de correspondance selon le type spécifié.
        
        Args:
            strategy_type: Type de stratégie à créer
            
        Returns:
            Stratégie de correspondance
            
        Raises:
            ValueError: Si le type de stratégie est invalide
        """
        if strategy_type == 'protocol':
            return ProtocolMatchStrategy()
        elif strategy_type == 'source_ip':
            return SourceIpMatchStrategy()
        elif strategy_type == 'destination_ip':
            return DestinationIpMatchStrategy()
        elif strategy_type == 'source_port':
            return SourcePortMatchStrategy()
        elif strategy_type == 'source_port_range':
            return SourcePortRangeMatchStrategy()
        elif strategy_type == 'destination_port':
            return DestinationPortMatchStrategy()
        elif strategy_type == 'destination_port_range':
            return DestinationPortRangeMatchStrategy()
        elif strategy_type == 'dscp':
            return DscpMatchStrategy()
        elif strategy_type == 'vlan':
            return VlanMatchStrategy()
        elif strategy_type == 'composite':
            return CompositeMatchStrategy()
        else:
            raise ValueError(f"Type de stratégie invalide: {strategy_type}")


def create_composite_strategy_from_classifier(classifier_data: Dict[str, Any]) -> CompositeMatchStrategy:
    """
    Crée une stratégie composite à partir des données d'un classificateur.
    
    Args:
        classifier_data: Données du classificateur
        
    Returns:
        Stratégie composite
    """
    composite = CompositeMatchStrategy()
    
    # Ajouter une stratégie pour chaque critère présent
    if 'protocol' in classifier_data and classifier_data['protocol']:
        composite.add_strategy(ProtocolMatchStrategy(), classifier_data['protocol'])
        
    if 'source_ip' in classifier_data and classifier_data['source_ip']:
        composite.add_strategy(SourceIpMatchStrategy(), classifier_data['source_ip'])
        
    if 'destination_ip' in classifier_data and classifier_data['destination_ip']:
        composite.add_strategy(DestinationIpMatchStrategy(), classifier_data['destination_ip'])
        
    # Gérer les ports
    if 'source_port_start' in classifier_data and classifier_data['source_port_start']:
        if 'source_port_end' in classifier_data and classifier_data['source_port_end']:
            # Plage de ports
            composite.add_strategy(
                SourcePortRangeMatchStrategy(),
                (classifier_data['source_port_start'], classifier_data['source_port_end'])
            )
        else:
            # Port unique
            composite.add_strategy(
                SourcePortMatchStrategy(),
                classifier_data['source_port_start']
            )
            
    if 'destination_port_start' in classifier_data and classifier_data['destination_port_start']:
        if 'destination_port_end' in classifier_data and classifier_data['destination_port_end']:
            # Plage de ports
            composite.add_strategy(
                DestinationPortRangeMatchStrategy(),
                (classifier_data['destination_port_start'], classifier_data['destination_port_end'])
            )
        else:
            # Port unique
            composite.add_strategy(
                DestinationPortMatchStrategy(),
                classifier_data['destination_port_start']
            )
            
    # Ajouter d'autres critères
    if 'dscp_marking' in classifier_data and classifier_data['dscp_marking']:
        composite.add_strategy(DscpMatchStrategy(), classifier_data['dscp_marking'])
        
    if 'vlan' in classifier_data and classifier_data['vlan']:
        composite.add_strategy(VlanMatchStrategy(), classifier_data['vlan'])
        
    return composite 