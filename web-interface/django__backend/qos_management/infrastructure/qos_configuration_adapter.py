"""
Adaptateur pour le service de configuration QoS.

Ce module fournit une implémentation de l'interface QoSConfigurationService
permettant d'appliquer des configurations QoS aux équipements réseau.
"""

import logging
from typing import Dict, Any, List, Optional
import subprocess

from ..domain.interfaces import QoSConfigurationService

logger = logging.getLogger(__name__)


class NetworkDeviceQoSAdapter(QoSConfigurationService):
    """
    Adaptateur pour le service de configuration QoS sur des équipements réseau.
    
    Cette classe implémente l'interface QoSConfigurationService en utilisant
    différentes méthodes selon le type d'équipement (SSH, NETCONF, REST API, etc.)
    pour appliquer des politiques QoS.
    """
    
    def __init__(self, device_service=None, network_service=None):
        """
        Initialise l'adaptateur.
        
        Args:
            device_service: Service pour interagir avec les équipements
            network_service: Service pour gérer les connexions réseau
        """
        self.device_service = device_service
        self.network_service = network_service
    
    def apply_policy(self, device_id: int, interface_id: int, policy_id: int) -> bool:
        """
        Applique une politique QoS à une interface d'un équipement.
        
        Args:
            device_id: ID de l'équipement
            interface_id: ID de l'interface
            policy_id: ID de la politique
            
        Returns:
            True si l'application a réussi
        """
        try:
            # Récupérer les informations sur l'équipement, l'interface et la politique
            device_info = self._get_device_info(device_id)
            interface_info = self._get_interface_info(interface_id)
            policy_info = self._get_policy_info(policy_id)
            
            if not device_info or not interface_info or not policy_info:
                logger.error("Informations manquantes pour appliquer la politique QoS")
                return False
                
            # Appliquer la politique selon le type d'équipement
            device_type = device_info.get("type", "").lower()
            
            if "cisco" in device_type:
                return self._apply_cisco_policy(device_info, interface_info, policy_info)
            elif "juniper" in device_type:
                return self._apply_juniper_policy(device_info, interface_info, policy_info)
            else:
                # Méthode générique pour d'autres équipements
                return self._apply_generic_policy(device_info, interface_info, policy_info)
                
        except Exception as e:
            logger.error(f"Erreur lors de l'application de la politique QoS: {str(e)}", exc_info=True)
            return False
    
    def remove_policy(self, device_id: int, interface_id: int) -> bool:
        """
        Supprime la politique QoS d'une interface.
        
        Args:
            device_id: ID de l'équipement
            interface_id: ID de l'interface
            
        Returns:
            True si la suppression a réussi
        """
        try:
            # Récupérer les informations sur l'équipement et l'interface
            device_info = self._get_device_info(device_id)
            interface_info = self._get_interface_info(interface_id)
            
            if not device_info or not interface_info:
                logger.error("Informations manquantes pour supprimer la politique QoS")
                return False
            
            # Supprimer la politique selon le type d'équipement
            device_type = device_info.get("type", "").lower()
            
            if "cisco" in device_type:
                return self._remove_cisco_policy(device_info, interface_info)
            elif "juniper" in device_type:
                return self._remove_juniper_policy(device_info, interface_info)
            else:
                # Méthode générique pour d'autres équipements
                return self._remove_generic_policy(device_info, interface_info)
                
        except Exception as e:
            logger.error(f"Erreur lors de la suppression de la politique QoS: {str(e)}", exc_info=True)
            return False
    
    def get_applied_policies(self, device_id: int) -> Dict[str, Any]:
        """
        Récupère les politiques QoS appliquées sur un équipement.
        
        Args:
            device_id: ID de l'équipement
            
        Returns:
            Dictionnaire des politiques appliquées par interface
        """
        try:
            # Récupérer les informations sur l'équipement
            device_info = self._get_device_info(device_id)
            
            if not device_info:
                logger.error(f"Équipement non trouvé: {device_id}")
                return {}
            
            # Récupérer les politiques appliquées selon le type d'équipement
            device_type = device_info.get("type", "").lower()
            
            if "cisco" in device_type:
                return self._get_cisco_applied_policies(device_info)
            elif "juniper" in device_type:
                return self._get_juniper_applied_policies(device_info)
            else:
                # Méthode générique pour d'autres équipements
                return self._get_generic_applied_policies(device_info)
                
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des politiques QoS appliquées: {str(e)}", exc_info=True)
            return {}
    
    def _get_device_info(self, device_id: int) -> Optional[Dict[str, Any]]:
        """
        Récupère les informations sur un équipement.
        """
        # Simuler des données d'équipement pour la démonstration
        return {
            "id": device_id,
            "ip_address": f"192.168.1.{device_id}",
            "type": "cisco",
            "hostname": f"device-{device_id}",
            "credentials": {
                "username": "admin",
                "password": "password"
            }
        }
    
    def _get_interface_info(self, interface_id: int) -> Optional[Dict[str, Any]]:
        """
        Récupère les informations sur une interface.
        """
        # Simuler des données d'interface pour la démonstration
        return {
            "id": interface_id,
            "name": f"GigabitEthernet1/0/{interface_id}",
            "device_id": 1,
            "type": "ethernet",
            "status": "up"
        }
    
    def _get_policy_info(self, policy_id: int) -> Optional[Dict[str, Any]]:
        """
        Récupère les informations sur une politique QoS.
        """
        # Simuler des données de politique pour la démonstration
        return {
            "id": policy_id,
            "name": f"QoS_Policy_{policy_id}",
            "type": "class-based",
            "bandwidth_limit": 1000000,  # 1 Gbps
            "parameters": {
                "classes": [
                    {
                        "name": "voice",
                        "priority": 7,
                        "bandwidth": 200000,  # 200 Mbps
                        "dscp": "EF"
                    },
                    {
                        "name": "video",
                        "priority": 6,
                        "bandwidth": 500000,  # 500 Mbps
                        "dscp": "AF41"
                    },
                    {
                        "name": "data",
                        "priority": 4,
                        "bandwidth": 300000,  # 300 Mbps
                        "dscp": "AF21"
                    }
                ]
            }
        }
    
    def _apply_cisco_policy(self, device_info: Dict[str, Any], 
                          interface_info: Dict[str, Any], 
                          policy_info: Dict[str, Any]) -> bool:
        """
        Applique une politique QoS sur un équipement Cisco.
        """
        try:
            logger.info(f"Application de la politique QoS {policy_info['name']} "
                       f"sur l'interface {interface_info['name']} "
                       f"de l'équipement {device_info['ip_address']}")
            
            # Simuler l'application de la politique
            # Dans une vraie implémentation, utiliser SSH/NETCONF/REST API
            
            return True
        except Exception as e:
            logger.error(f"Erreur lors de l'application Cisco: {e}")
            return False
    
    def _apply_juniper_policy(self, device_info: Dict[str, Any], 
                            interface_info: Dict[str, Any], 
                            policy_info: Dict[str, Any]) -> bool:
        """
        Applique une politique QoS sur un équipement Juniper.
        """
        try:
            logger.info(f"Application de la politique QoS {policy_info['name']} "
                       f"sur l'interface {interface_info['name']} "
                       f"de l'équipement {device_info['ip_address']}")
            
            # Simuler l'application de la politique
            # Dans une vraie implémentation, utiliser NETCONF/REST API
            
            return True
        except Exception as e:
            logger.error(f"Erreur lors de l'application Juniper: {e}")
            return False
    
    def _apply_generic_policy(self, device_info: Dict[str, Any], 
                            interface_info: Dict[str, Any], 
                            policy_info: Dict[str, Any]) -> bool:
        """
        Applique une politique QoS sur un équipement générique.
        """
        try:
            logger.info(f"Application de la politique QoS {policy_info['name']} "
                       f"sur l'interface {interface_info['name']} "
                       f"de l'équipement {device_info['ip_address']}")
            
            # Simuler l'application de la politique
            return True
        except Exception as e:
            logger.error(f"Erreur lors de l'application générique: {e}")
            return False
    
    def _remove_cisco_policy(self, device_info: Dict[str, Any], 
                           interface_info: Dict[str, Any]) -> bool:
        """
        Supprime une politique QoS sur un équipement Cisco.
        """
        try:
            logger.info(f"Suppression de la politique QoS sur l'interface {interface_info['name']} "
                       f"de l'équipement {device_info['ip_address']}")
            
            # Simuler la suppression de la politique
            return True
        except Exception as e:
            logger.error(f"Erreur lors de la suppression Cisco: {e}")
            return False
    
    def _remove_juniper_policy(self, device_info: Dict[str, Any], 
                             interface_info: Dict[str, Any]) -> bool:
        """
        Supprime une politique QoS sur un équipement Juniper.
        """
        try:
            logger.info(f"Suppression de la politique QoS sur l'interface {interface_info['name']} "
                       f"de l'équipement {device_info['ip_address']}")
            
            # Simuler la suppression de la politique
            return True
        except Exception as e:
            logger.error(f"Erreur lors de la suppression Juniper: {e}")
            return False
    
    def _remove_generic_policy(self, device_info: Dict[str, Any], 
                             interface_info: Dict[str, Any]) -> bool:
        """
        Supprime une politique QoS sur un équipement générique.
        """
        try:
            logger.info(f"Suppression de la politique QoS sur l'interface {interface_info['name']} "
                       f"de l'équipement {device_info['ip_address']}")
            
            # Simuler la suppression de la politique
            return True
        except Exception as e:
            logger.error(f"Erreur lors de la suppression générique: {e}")
            return False
    
    def _get_cisco_applied_policies(self, device_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Récupère les politiques QoS appliquées sur un équipement Cisco.
        """
        # Simuler les politiques appliquées
        return {
            "device_id": device_info["id"],
            "device_ip": device_info["ip_address"],
            "interfaces": [
                {
                    "name": "GigabitEthernet1/0/1",
                    "policy_id": 1,
                    "policy_name": "QoS_Policy_1",
                    "direction": "output",
                    "status": "active"
                },
                {
                    "name": "GigabitEthernet1/0/2",
                    "policy_id": 2,
                    "policy_name": "QoS_Policy_2",
                    "direction": "output",
                    "status": "active"
                }
            ]
        }
    
    def _get_juniper_applied_policies(self, device_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Récupère les politiques QoS appliquées sur un équipement Juniper.
        """
        # Simuler les politiques appliquées
        return {
            "device_id": device_info["id"],
            "device_ip": device_info["ip_address"],
            "interfaces": [
                {
                    "name": "ge-0/0/0",
                    "policy_id": 3,
                    "policy_name": "QoS_Policy_3",
                    "direction": "output",
                    "status": "active"
                },
                {
                    "name": "ge-0/0/1",
                    "policy_id": 4,
                    "policy_name": "QoS_Policy_4",
                    "direction": "output",
                    "status": "active"
                }
            ]
        }
    
    def _get_generic_applied_policies(self, device_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Récupère les politiques QoS appliquées sur un équipement générique.
        """
        # Retourner une structure vide pour les équipements génériques
        return {
            "device_id": device_info["id"],
            "device_ip": device_info["ip_address"],
            "interfaces": []
        }