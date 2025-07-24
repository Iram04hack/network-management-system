"""
Adaptateur pour le service de contrôle de trafic.

Ce module fournit une implémentation de l'interface TrafficControlService
du domaine QoS, en utilisant le service de contrôle de trafic de l'infrastructure.
"""

import logging
from typing import Dict, Any, Optional

from ..domain.interfaces import TrafficControlService
from ..domain.entities import QoSPolicy, TrafficClass, TrafficClassifier

logger = logging.getLogger(__name__)

class TrafficControlAdapter(TrafficControlService):
    """
    Adaptateur pour le service de contrôle de trafic.
    
    Cette classe implémente l'interface TrafficControlService du domaine QoS,
    en utilisant le service de contrôle de trafic de l'infrastructure.
    """
    
    def __init__(self):
        """
        Initialise l'adaptateur avec le service de contrôle de trafic.
        """
        self.active_policies = {}  # Cache des politiques actives
    
    def apply_policy(self, policy_data: Dict[str, Any], interface_name: str) -> Dict[str, Any]:
        """
        Applique une politique QoS à une interface réseau.
        
        Args:
            policy_data: Données de la politique QoS
            interface_name: Nom de l'interface réseau
            
        Returns:
            Résultat de l'opération
        """
        try:
            # Convertir les données de la politique en objets du domaine
            policy = self._map_policy_data(policy_data)
            
            # Valider les données de la politique
            validation_result = self.validate_policy(policy_data, interface_name)
            if not validation_result["success"]:
                return validation_result
            
            # Simuler l'application de la politique
            # Dans une vraie implémentation, ceci utiliserait tc (Traffic Control) Linux
            # ou des API spécifiques aux équipements réseau
            
            logger.info(f"Application de la politique QoS '{policy.name}' "
                       f"sur l'interface {interface_name}")
            
            # Sauvegarder la politique appliquée
            self.active_policies[interface_name] = {
                "policy_id": policy.id,
                "policy_name": policy.name,
                "policy_data": policy_data,
                "applied_at": "2025-07-07T20:00:00Z",
                "status": "active"
            }
            
            return {
                "success": True,
                "message": f"Politique QoS '{policy.name}' appliquée avec succès à l'interface {interface_name}",
                "policy_id": policy.id,
                "interface": interface_name,
                "direction": policy_data.get("direction", "egress"),
                "bandwidth_limit": policy.bandwidth_limit,
                "traffic_classes_count": len(policy.traffic_classes)
            }
                
        except Exception as e:
            logger.error(f"Erreur lors de l'application de la politique QoS: {str(e)}", exc_info=True)
            return {
                "success": False,
                "message": f"Erreur: {str(e)}",
                "interface": interface_name
            }
    
    def remove_policy(self, interface_name: str) -> Dict[str, Any]:
        """
        Supprime une politique QoS d'une interface réseau.
        
        Args:
            interface_name: Nom de l'interface réseau
            
        Returns:
            Résultat de l'opération
        """
        try:
            if interface_name not in self.active_policies:
                return {
                    "success": False,
                    "message": f"Aucune politique QoS active sur l'interface {interface_name}",
                    "interface": interface_name
                }
            
            # Récupérer les informations de la politique
            policy_info = self.active_policies[interface_name]
            policy_name = policy_info["policy_name"]
            
            logger.info(f"Suppression de la politique QoS '{policy_name}' "
                       f"de l'interface {interface_name}")
            
            # Simuler la suppression de la politique
            # Dans une vraie implémentation, ceci utiliserait tc (Traffic Control) Linux
            
            # Supprimer de la cache
            del self.active_policies[interface_name]
            
            return {
                "success": True,
                "message": f"Politique QoS '{policy_name}' supprimée avec succès de l'interface {interface_name}",
                "interface": interface_name,
                "removed_policy": policy_name
            }
                
        except Exception as e:
            logger.error(f"Erreur lors de la suppression de la politique QoS: {str(e)}", exc_info=True)
            return {
                "success": False,
                "message": f"Erreur: {str(e)}",
                "interface": interface_name
            }
    
    def get_statistics(self, interface_name: str) -> Dict[str, Any]:
        """
        Récupère les statistiques QoS d'une interface réseau.
        
        Args:
            interface_name: Nom de l'interface réseau
            
        Returns:
            Statistiques QoS
        """
        try:
            # Simuler la récupération de statistiques
            if interface_name not in self.active_policies:
                return {
                    "success": False,
                    "message": f"Aucune politique QoS active sur l'interface {interface_name}",
                    "interface": interface_name
                }
            
            policy_info = self.active_policies[interface_name]
            
            # Simuler des statistiques réalistes
            stats = {
                "interface": interface_name,
                "policy_name": policy_info["policy_name"],
                "policy_id": policy_info["policy_id"],
                "applied_at": policy_info["applied_at"],
                "status": policy_info["status"],
                "total_bytes": 1234567890,
                "total_packets": 987654,
                "dropped_bytes": 12345,
                "dropped_packets": 123,
                "traffic_classes": [
                    {
                        "name": "voice",
                        "bytes": 123456789,
                        "packets": 98765,
                        "drops": 0,
                        "bandwidth_used": 200000,  # bps
                        "bandwidth_limit": 500000  # bps
                    },
                    {
                        "name": "video",
                        "bytes": 456789012,
                        "packets": 345678,
                        "drops": 45,
                        "bandwidth_used": 800000,  # bps
                        "bandwidth_limit": 2000000  # bps
                    },
                    {
                        "name": "data",
                        "bytes": 654321987,
                        "packets": 543211,
                        "drops": 78,
                        "bandwidth_used": 1500000,  # bps
                        "bandwidth_limit": 5000000  # bps
                    }
                ]
            }
            
            return {
                "success": True,
                "interface": interface_name,
                "statistics": stats
            }
                
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des statistiques QoS: {str(e)}", exc_info=True)
            return {
                "success": False,
                "message": f"Erreur: {str(e)}",
                "interface": interface_name
            }
    
    def validate_policy(self, policy_data: Dict[str, Any], interface_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Valide une politique QoS pour une interface réseau.
        
        Args:
            policy_data: Données de la politique QoS
            interface_name: Nom de l'interface réseau (optionnel)
            
        Returns:
            Résultat de la validation
        """
        try:
            errors = []
            warnings = []
            
            # Valider les champs obligatoires
            if not policy_data.get("name"):
                errors.append("Le nom de la politique est obligatoire")
            
            # Valider la limite de bande passante
            bandwidth_limit = policy_data.get("bandwidth_limit", 0)
            if bandwidth_limit <= 0:
                errors.append("La limite de bande passante doit être supérieure à 0")
            
            # Valider les classes de trafic
            traffic_classes = policy_data.get("traffic_classes", [])
            if not traffic_classes:
                warnings.append("La politique ne contient aucune classe de trafic")
            
            # Valider chaque classe de trafic
            total_bandwidth = 0
            priorities = set()
            
            for i, tc in enumerate(traffic_classes):
                tc_name = tc.get("name", f"Class_{i}")
                
                # Vérifier le nom de la classe
                if not tc.get("name"):
                    errors.append(f"La classe de trafic #{i+1} doit avoir un nom")
                
                # Vérifier la priorité
                priority = tc.get("priority", 0)
                if priority in priorities:
                    errors.append(f"Priorité en double ({priority}) pour la classe '{tc_name}'")
                priorities.add(priority)
                
                # Vérifier la bande passante
                tc_bandwidth = tc.get("bandwidth", 0)
                if tc_bandwidth > 0:
                    total_bandwidth += tc_bandwidth
                
                # Valider les classificateurs
                classifiers = tc.get("classifiers", [])
                if not classifiers:
                    warnings.append(f"La classe '{tc_name}' ne contient aucun classificateur")
                
                for j, classifier in enumerate(classifiers):
                    # Valider les ports
                    src_start = classifier.get("source_port_start")
                    src_end = classifier.get("source_port_end")
                    if src_start is not None and src_end is not None:
                        if src_start > src_end:
                            errors.append(f"Port source invalide dans la classe '{tc_name}', classificateur #{j+1}")
                    
                    dst_start = classifier.get("destination_port_start")
                    dst_end = classifier.get("destination_port_end")
                    if dst_start is not None and dst_end is not None:
                        if dst_start > dst_end:
                            errors.append(f"Port destination invalide dans la classe '{tc_name}', classificateur #{j+1}")
            
            # Vérifier que la somme des bandes passantes ne dépasse pas la limite
            if total_bandwidth > bandwidth_limit:
                errors.append(f"La somme des bandes passantes des classes ({total_bandwidth}) "
                             f"dépasse la limite totale ({bandwidth_limit})")
            
            # Vérifier l'interface (si spécifiée)
            if interface_name:
                # Dans une vraie implémentation, vérifier que l'interface existe
                # et qu'elle supporte les politiques QoS
                if not self._interface_exists(interface_name):
                    errors.append(f"L'interface '{interface_name}' n'existe pas ou n'est pas accessible")
            
            # Construire le résultat
            result = {
                "success": len(errors) == 0,
                "errors": errors,
                "warnings": warnings,
                "validation_details": {
                    "total_traffic_classes": len(traffic_classes),
                    "total_allocated_bandwidth": total_bandwidth,
                    "bandwidth_limit": bandwidth_limit,
                    "utilization_percentage": (total_bandwidth / bandwidth_limit * 100) if bandwidth_limit > 0 else 0
                }
            }
            
            if errors:
                result["message"] = f"La politique QoS n'est pas valide ({len(errors)} erreur(s))"
            else:
                result["message"] = "La politique QoS est valide"
                if warnings:
                    result["message"] += f" ({len(warnings)} avertissement(s))"
            
            return result
                
        except Exception as e:
            logger.error(f"Erreur lors de la validation de la politique QoS: {str(e)}", exc_info=True)
            return {
                "success": False,
                "message": f"Erreur lors de la validation: {str(e)}",
                "errors": [str(e)]
            }
    
    def list_active_policies(self) -> Dict[str, Any]:
        """
        Liste toutes les politiques QoS actuellement actives.
        
        Returns:
            Liste des politiques actives
        """
        try:
            policies = []
            
            for interface_name, policy_info in self.active_policies.items():
                policies.append({
                    "interface": interface_name,
                    "policy_id": policy_info["policy_id"],
                    "policy_name": policy_info["policy_name"],
                    "applied_at": policy_info["applied_at"],
                    "status": policy_info["status"]
                })
            
            return {
                "success": True,
                "total_policies": len(policies),
                "active_policies": policies
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de la liste des politiques actives: {str(e)}", exc_info=True)
            return {
                "success": False,
                "message": f"Erreur: {str(e)}",
                "active_policies": []
            }
    
    def get_interface_status(self, interface_name: str) -> Dict[str, Any]:
        """
        Récupère le statut QoS d'une interface spécifique.
        
        Args:
            interface_name: Nom de l'interface
            
        Returns:
            Statut de l'interface
        """
        try:
            if interface_name in self.active_policies:
                policy_info = self.active_policies[interface_name]
                return {
                    "success": True,
                    "interface": interface_name,
                    "has_qos_policy": True,
                    "policy_info": policy_info
                }
            else:
                return {
                    "success": True,
                    "interface": interface_name,
                    "has_qos_policy": False,
                    "policy_info": None
                }
                
        except Exception as e:
            logger.error(f"Erreur lors de la récupération du statut de l'interface: {str(e)}", exc_info=True)
            return {
                "success": False,
                "message": f"Erreur: {str(e)}",
                "interface": interface_name
            }
    
    def _interface_exists(self, interface_name: str) -> bool:
        """
        Vérifie si une interface réseau existe.
        
        Args:
            interface_name: Nom de l'interface
            
        Returns:
            True si l'interface existe
        """
        try:
            # Dans une vraie implémentation, vérifier via /sys/class/net/
            # ou via des commandes système
            
            # Pour la simulation, accepter certains noms d'interface standard
            valid_interfaces = [
                "eth0", "eth1", "eth2",
                "enp0s3", "enp0s8",
                "wlan0", "wlan1",
                "br0", "br1",
                "lo"
            ]
            
            # Accepter aussi les interfaces qui commencent par certains préfixes
            valid_prefixes = ["eth", "enp", "wlan", "br", "veth", "docker", "virbr"]
            
            if interface_name in valid_interfaces:
                return True
            
            for prefix in valid_prefixes:
                if interface_name.startswith(prefix):
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Erreur lors de la vérification de l'interface: {str(e)}")
            return False
    
    def _map_policy_data(self, policy_data: Dict[str, Any]) -> QoSPolicy:
        """
        Convertit les données JSON d'une politique en objet du domaine.
        
        Args:
            policy_data: Données de la politique
            
        Returns:
            Objet QoSPolicy
        """
        policy = QoSPolicy(
            id=policy_data.get("id"),
            name=policy_data.get("name", ""),
            description=policy_data.get("description", ""),
            bandwidth_limit=policy_data.get("bandwidth_limit", 0),
            is_active=policy_data.get("is_active", True),
            priority=policy_data.get("priority", 0)
        )
        
        # Ajouter les classes de trafic
        for tc_data in policy_data.get("traffic_classes", []):
            traffic_class = TrafficClass(
                id=tc_data.get("id"),
                name=tc_data.get("name", ""),
                description=tc_data.get("description", ""),
                priority=tc_data.get("priority", 0),
                min_bandwidth=tc_data.get("min_bandwidth", 0),
                max_bandwidth=tc_data.get("max_bandwidth", 0),
                dscp=tc_data.get("dscp", "default"),
                burst=tc_data.get("burst", 0)
            )
            
            # Ajouter les classificateurs
            for cls_data in tc_data.get("classifiers", []):
                classifier = TrafficClassifier(
                    id=cls_data.get("id"),
                    protocol=cls_data.get("protocol", "any"),
                    source_ip=cls_data.get("source_ip"),
                    destination_ip=cls_data.get("destination_ip"),
                    source_port_start=cls_data.get("source_port_start"),
                    source_port_end=cls_data.get("source_port_end"),
                    destination_port_start=cls_data.get("destination_port_start"),
                    destination_port_end=cls_data.get("destination_port_end"),
                    dscp_marking=cls_data.get("dscp_marking"),
                    vlan=cls_data.get("vlan"),
                    name=cls_data.get("name", ""),
                    description=cls_data.get("description", "")
                )
                traffic_class.classifiers.append(classifier)
            
            policy.traffic_classes.append(traffic_class)
            
        return policy