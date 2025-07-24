"""
Service d'intégration SDN pour la gestion centralisée QoS.

Ce module implémente l'intégration avec des contrôleurs SDN comme ONOS et OpenDaylight
pour appliquer des politiques QoS de manière centralisée via OpenFlow.
"""

import logging
import json
import requests
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from ..domain.interfaces import QoSConfigurationService

logger = logging.getLogger(__name__)


class SDNControllerType(str, Enum):
    """Types de contrôleurs SDN supportés."""
    ONOS = "onos"
    OPENDAYLIGHT = "opendaylight"
    RYU = "ryu"
    FLOODLIGHT = "floodlight"


class FlowPriority(int, Enum):
    """Priorités des flux OpenFlow."""
    EMERGENCY = 65000
    VOICE = 50000
    VIDEO = 40000
    INTERACTIVE = 30000
    BULK = 20000
    DEFAULT = 10000


@dataclass
class OpenFlowRule:
    """Règle OpenFlow pour QoS."""
    switch_id: str
    table_id: int = 0
    priority: int = FlowPriority.DEFAULT
    match_criteria: Dict[str, Any] = None
    actions: List[Dict[str, Any]] = None
    flow_id: Optional[str] = None
    
    def __post_init__(self):
        if self.match_criteria is None:
            self.match_criteria = {}
        if self.actions is None:
            self.actions = []


@dataclass
class QueueConfiguration:
    """Configuration de file d'attente SDN."""
    queue_id: int
    min_rate: int  # bps
    max_rate: int  # bps
    priority: int
    properties: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.properties is None:
            self.properties = {}


@dataclass
class SDNQoSPolicy:
    """Politique QoS pour SDN."""
    policy_id: str
    name: str
    description: str
    flows: List[OpenFlowRule]
    queues: List[QueueConfiguration]
    meters: List[Dict[str, Any]]
    switches: List[str]
    active: bool = True


class SDNIntegrationService(QoSConfigurationService):
    """
    Service d'intégration SDN pour la gestion QoS centralisée.
    """
    
    def __init__(
        self,
        controller_type: SDNControllerType,
        controller_url: str,
        username: str = "admin",
        password: str = "admin"
    ):
        self.controller_type = controller_type
        self.controller_url = controller_url.rstrip('/')
        self.username = username
        self.password = password
        self.session = requests.Session()
        self.session.auth = (username, password)
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
        
        # Cache des politiques actives
        self.active_policies = {}
        self.topology_cache = {}
    
    def apply_policy(self, device_id: int, interface_id: int, policy_id: int) -> bool:
        """
        Applique une politique QoS via SDN.
        
        Args:
            device_id: ID de l'équipement (switch SDN)
            interface_id: ID de l'interface
            policy_id: ID de la politique
            
        Returns:
            True si l'application a réussi
        """
        try:
            # Convertir les IDs en identifiants SDN
            switch_id = self._device_id_to_switch_id(device_id)
            port_number = interface_id
            
            # Créer la politique SDN
            sdn_policy = self._create_sdn_policy(policy_id, switch_id, port_number)
            
            # Appliquer la politique via le contrôleur
            success = self._install_sdn_policy(sdn_policy)
            
            if success:
                self.active_policies[f"{switch_id}_{port_number}"] = sdn_policy
                logger.info(f"Politique SDN {policy_id} appliquée sur {switch_id}:{port_number}")
            
            return success
            
        except Exception as e:
            logger.error(f"Erreur lors de l'application de la politique SDN: {str(e)}")
            return False
    
    def remove_policy(self, device_id: int, interface_id: int) -> bool:
        """
        Supprime une politique QoS via SDN.
        
        Args:
            device_id: ID de l'équipement
            interface_id: ID de l'interface
            
        Returns:
            True si la suppression a réussi
        """
        try:
            switch_id = self._device_id_to_switch_id(device_id)
            port_number = interface_id
            policy_key = f"{switch_id}_{port_number}"
            
            if policy_key in self.active_policies:
                policy = self.active_policies[policy_key]
                success = self._uninstall_sdn_policy(policy)
                
                if success:
                    del self.active_policies[policy_key]
                    logger.info(f"Politique SDN supprimée de {switch_id}:{port_number}")
                
                return success
            
            return True  # Aucune politique à supprimer
            
        except Exception as e:
            logger.error(f"Erreur lors de la suppression de la politique SDN: {str(e)}")
            return False
    
    def get_applied_policies(self, device_id: int) -> Dict[str, Any]:
        """
        Récupère les politiques QoS appliquées sur un switch SDN.
        
        Args:
            device_id: ID de l'équipement
            
        Returns:
            Dictionnaire des politiques appliquées
        """
        try:
            switch_id = self._device_id_to_switch_id(device_id)
            
            # Récupérer les flux depuis le contrôleur
            flows = self._get_flows_from_controller(switch_id)
            
            # Récupérer les queues
            queues = self._get_queues_from_controller(switch_id)
            
            # Récupérer les meters
            meters = self._get_meters_from_controller(switch_id)
            
            return {
                'switch_id': switch_id,
                'flows': flows,
                'queues': queues,
                'meters': meters,
                'active_policies': [
                    policy.policy_id for policy in self.active_policies.values()
                    if switch_id in policy.switches
                ]
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des politiques SDN: {str(e)}")
            return {}
    
    def create_traffic_engineering_policy(
        self,
        policy_name: str,
        traffic_classes: List[Dict[str, Any]],
        path_constraints: Dict[str, Any]
    ) -> SDNQoSPolicy:
        """
        Crée une politique d'ingénierie de trafic SDN.
        
        Args:
            policy_name: Nom de la politique
            traffic_classes: Classes de trafic avec leurs exigences
            path_constraints: Contraintes de chemin (latence, bande passante)
            
        Returns:
            Politique SDN créée
        """
        policy_id = f"te_{policy_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        flows = []
        queues = []
        meters = []
        
        # Créer les queues pour chaque classe de trafic
        queue_id = 1
        for tc in traffic_classes:
            queue = QueueConfiguration(
                queue_id=queue_id,
                min_rate=tc.get('min_bandwidth', 1000000),  # 1 Mbps par défaut
                max_rate=tc.get('max_bandwidth', 10000000), # 10 Mbps par défaut
                priority=tc.get('priority', 1),
                properties={
                    'name': tc.get('name', f'queue_{queue_id}'),
                    'dscp': tc.get('dscp', 0)
                }
            )
            queues.append(queue)
            queue_id += 1
        
        # Créer les meters pour le contrôle de débit
        meter_id = 1
        for tc in traffic_classes:
            meter = {
                'meter_id': meter_id,
                'bands': [
                    {
                        'type': 'drop',
                        'rate': tc.get('max_bandwidth', 10000000),
                        'burst_size': tc.get('burst_size', 1000000)
                    }
                ]
            }
            meters.append(meter)
            meter_id += 1
        
        # Créer les flux pour classifier et diriger le trafic
        for i, tc in enumerate(traffic_classes):
            priority = self._map_priority_to_openflow(tc.get('priority', 1))
            
            # Flux de classification
            flow = OpenFlowRule(
                switch_id="*",  # Applicable à tous les switches
                priority=priority,
                match_criteria=self._create_match_criteria(tc),
                actions=[
                    {'type': 'set_queue', 'queue_id': i + 1},
                    {'type': 'meter', 'meter_id': i + 1},
                    {'type': 'output', 'port': 'controller'}
                ]
            )
            flows.append(flow)
        
        return SDNQoSPolicy(
            policy_id=policy_id,
            name=policy_name,
            description=f"Politique d'ingénierie de trafic - {policy_name}",
            flows=flows,
            queues=queues,
            meters=meters,
            switches=[]  # À remplir lors de l'application
        )
    
    def deploy_qos_policy_to_topology(
        self,
        policy: SDNQoSPolicy,
        target_switches: Optional[List[str]] = None
    ) -> bool:
        """
        Déploie une politique QoS sur toute la topologie ou sur des switches spécifiques.
        
        Args:
            policy: Politique QoS à déployer
            target_switches: Liste des switches cibles (optionnel)
            
        Returns:
            True si le déploiement a réussi
        """
        try:
            # Découvrir la topologie si pas de switches spécifiés
            if not target_switches:
                topology = self._discover_topology()
                target_switches = list(topology.get('switches', {}).keys())
            
            logger.info(f"Déploiement de la politique {policy.policy_id} sur {len(target_switches)} switches")
            
            success_count = 0
            
            for switch_id in target_switches:
                # Installer les queues
                for queue in policy.queues:
                    if self._install_queue(switch_id, queue):
                        logger.debug(f"Queue {queue.queue_id} installée sur {switch_id}")
                
                # Installer les meters
                for meter in policy.meters:
                    if self._install_meter(switch_id, meter):
                        logger.debug(f"Meter {meter['meter_id']} installé sur {switch_id}")
                
                # Installer les flux
                for flow in policy.flows:
                    flow_copy = OpenFlowRule(
                        switch_id=switch_id,
                        table_id=flow.table_id,
                        priority=flow.priority,
                        match_criteria=flow.match_criteria.copy(),
                        actions=flow.actions.copy()
                    )
                    
                    if self._install_flow(flow_copy):
                        logger.debug(f"Flux installé sur {switch_id}")
                        success_count += 1
            
            # Mettre à jour la politique avec les switches déployés
            policy.switches = target_switches
            self.active_policies[policy.policy_id] = policy
            
            success_rate = success_count / (len(target_switches) * len(policy.flows))
            logger.info(f"Déploiement terminé. Taux de succès: {success_rate:.2%}")
            
            return success_rate > 0.8  # Considérer comme succès si >80% des déploiements réussissent
            
        except Exception as e:
            logger.error(f"Erreur lors du déploiement de la politique: {str(e)}")
            return False
    
    def monitor_qos_performance(self, policy_id: str) -> Dict[str, Any]:
        """
        Surveille les performances d'une politique QoS déployée.
        
        Args:
            policy_id: ID de la politique à surveiller
            
        Returns:
            Métriques de performance
        """
        try:
            if policy_id not in self.active_policies:
                return {'error': 'Politique non trouvée'}
            
            policy = self.active_policies[policy_id]
            performance_data = {
                'policy_id': policy_id,
                'switches': {},
                'overall_stats': {
                    'total_flows': 0,
                    'active_flows': 0,
                    'total_bytes': 0,
                    'total_packets': 0
                }
            }
            
            for switch_id in policy.switches:
                switch_stats = self._get_switch_statistics(switch_id)
                performance_data['switches'][switch_id] = switch_stats
                
                # Agréger les statistiques
                performance_data['overall_stats']['total_flows'] += switch_stats.get('flow_count', 0)
                performance_data['overall_stats']['total_bytes'] += switch_stats.get('bytes', 0)
                performance_data['overall_stats']['total_packets'] += switch_stats.get('packets', 0)
            
            return performance_data
            
        except Exception as e:
            logger.error(f"Erreur lors de la surveillance de la politique: {str(e)}")
            return {'error': str(e)}
    
    def _device_id_to_switch_id(self, device_id: int) -> str:
        """Convertit un ID d'équipement en identifiant de switch SDN."""
        # Dans un vrai système, mapper depuis une base de données
        return f"of:00000000000000{device_id:02d}"
    
    def _create_sdn_policy(self, policy_id: int, switch_id: str, port_number: int) -> SDNQoSPolicy:
        """Crée une politique SDN à partir d'un ID de politique."""
        # Dans un vrai système, récupérer depuis la base de données
        # Ici, création d'exemple
        
        flows = [
            OpenFlowRule(
                switch_id=switch_id,
                priority=FlowPriority.VOICE,
                match_criteria={
                    'in_port': port_number,
                    'eth_type': '0x800',  # IPv4
                    'ip_proto': 17,       # UDP
                    'udp_dst': 5060       # SIP
                },
                actions=[
                    {'type': 'set_queue', 'queue_id': 1},
                    {'type': 'output', 'port': 'normal'}
                ]
            )
        ]
        
        queues = [
            QueueConfiguration(
                queue_id=1,
                min_rate=1000000,   # 1 Mbps
                max_rate=10000000,  # 10 Mbps
                priority=7
            )
        ]
        
        return SDNQoSPolicy(
            policy_id=f"policy_{policy_id}",
            name=f"Politique {policy_id}",
            description=f"Politique QoS automatique {policy_id}",
            flows=flows,
            queues=queues,
            meters=[],
            switches=[switch_id]
        )
    
    def _install_sdn_policy(self, policy: SDNQoSPolicy) -> bool:
        """Installe une politique SDN sur le contrôleur."""
        try:
            for switch_id in policy.switches:
                # Installer les queues
                for queue in policy.queues:
                    if not self._install_queue(switch_id, queue):
                        return False
                
                # Installer les flows
                for flow in policy.flows:
                    if not self._install_flow(flow):
                        return False
            
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de l'installation de la politique SDN: {str(e)}")
            return False
    
    def _uninstall_sdn_policy(self, policy: SDNQoSPolicy) -> bool:
        """Désinstalle une politique SDN."""
        try:
            for switch_id in policy.switches:
                # Supprimer les flows
                for flow in policy.flows:
                    self._remove_flow(switch_id, flow.flow_id)
                
                # Supprimer les queues (optionnel, peut être partagé)
                # for queue in policy.queues:
                #     self._remove_queue(switch_id, queue.queue_id)
            
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de la désinstallation de la politique SDN: {str(e)}")
            return False
    
    def _install_flow(self, flow: OpenFlowRule) -> bool:
        """Installe un flux OpenFlow."""
        try:
            if self.controller_type == SDNControllerType.ONOS:
                return self._install_flow_onos(flow)
            elif self.controller_type == SDNControllerType.OPENDAYLIGHT:
                return self._install_flow_odl(flow)
            else:
                logger.warning(f"Type de contrôleur non supporté: {self.controller_type}")
                return False
                
        except Exception as e:
            logger.error(f"Erreur lors de l'installation du flux: {str(e)}")
            return False
    
    def _install_flow_onos(self, flow: OpenFlowRule) -> bool:
        """Installe un flux via ONOS."""
        url = f"{self.controller_url}/onos/v1/flows/{flow.switch_id}"
        
        flow_data = {
            'priority': flow.priority,
            'timeout': 0,
            'isPermanent': True,
            'deviceId': flow.switch_id,
            'tableId': flow.table_id,
            'selector': {
                'criteria': self._convert_match_to_onos(flow.match_criteria)
            },
            'treatment': {
                'instructions': self._convert_actions_to_onos(flow.actions)
            }
        }
        
        response = self.session.post(url, json=flow_data)
        return response.status_code in [200, 201]
    
    def _install_flow_odl(self, flow: OpenFlowRule) -> bool:
        """Installe un flux via OpenDaylight."""
        # Simplification - implémentation basique
        url = f"{self.controller_url}/restconf/config/opendaylight-inventory:nodes/node/{flow.switch_id}/table/{flow.table_id}/flow"
        
        flow_data = {
            'flow': [{
                'id': f"flow_{flow.priority}",
                'priority': flow.priority,
                'table_id': flow.table_id,
                'match': flow.match_criteria,
                'instructions': {
                    'instruction': self._convert_actions_to_odl(flow.actions)
                }
            }]
        }
        
        response = self.session.put(url, json=flow_data)
        return response.status_code in [200, 201]
    
    def _install_queue(self, switch_id: str, queue: QueueConfiguration) -> bool:
        """Installe une queue sur un switch."""
        try:
            if self.controller_type == SDNControllerType.ONOS:
                # ONOS gère les queues via les ports
                url = f"{self.controller_url}/onos/v1/devices/{switch_id}/ports"
                # Implémentation spécifique à ONOS pour les queues
                return True  # Simplification
            else:
                logger.warning("Installation de queue non implémentée pour ce contrôleur")
                return True  # Assumer succès pour la démo
                
        except Exception as e:
            logger.error(f"Erreur lors de l'installation de la queue: {str(e)}")
            return False
    
    def _install_meter(self, switch_id: str, meter: Dict[str, Any]) -> bool:
        """Installe un meter sur un switch."""
        try:
            if self.controller_type == SDNControllerType.ONOS:
                url = f"{self.controller_url}/onos/v1/meters/{switch_id}"
                response = self.session.post(url, json=meter)
                return response.status_code in [200, 201]
            else:
                return True  # Simplification
                
        except Exception as e:
            logger.error(f"Erreur lors de l'installation du meter: {str(e)}")
            return False
    
    def _get_flows_from_controller(self, switch_id: str) -> List[Dict[str, Any]]:
        """Récupère les flux depuis le contrôleur."""
        try:
            if self.controller_type == SDNControllerType.ONOS:
                url = f"{self.controller_url}/onos/v1/flows/{switch_id}"
                response = self.session.get(url)
                if response.status_code == 200:
                    return response.json().get('flows', [])
            
            return []
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des flux: {str(e)}")
            return []
    
    def _get_queues_from_controller(self, switch_id: str) -> List[Dict[str, Any]]:
        """Récupère les queues depuis le contrôleur."""
        # Simplification - retourner des données d'exemple
        return [
            {'queue_id': 1, 'port': 1, 'properties': {'min-rate': 1000000, 'max-rate': 10000000}}
        ]
    
    def _get_meters_from_controller(self, switch_id: str) -> List[Dict[str, Any]]:
        """Récupère les meters depuis le contrôleur."""
        try:
            if self.controller_type == SDNControllerType.ONOS:
                url = f"{self.controller_url}/onos/v1/meters/{switch_id}"
                response = self.session.get(url)
                if response.status_code == 200:
                    return response.json().get('meters', [])
            
            return []
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des meters: {str(e)}")
            return []
    
    def _discover_topology(self) -> Dict[str, Any]:
        """Découvre la topologie réseau via le contrôleur SDN."""
        try:
            if self.controller_type == SDNControllerType.ONOS:
                # Récupérer les devices
                devices_url = f"{self.controller_url}/onos/v1/devices"
                devices_response = self.session.get(devices_url)
                
                # Récupérer les liens
                links_url = f"{self.controller_url}/onos/v1/links"
                links_response = self.session.get(links_url)
                
                if devices_response.status_code == 200 and links_response.status_code == 200:
                    topology = {
                        'switches': {
                            device['id']: device 
                            for device in devices_response.json().get('devices', [])
                        },
                        'links': links_response.json().get('links', [])
                    }
                    
                    self.topology_cache = topology
                    return topology
            
            return {'switches': {}, 'links': []}
            
        except Exception as e:
            logger.error(f"Erreur lors de la découverte de topologie: {str(e)}")
            return {'switches': {}, 'links': []}
    
    def _get_switch_statistics(self, switch_id: str) -> Dict[str, Any]:
        """Récupère les statistiques d'un switch."""
        try:
            if self.controller_type == SDNControllerType.ONOS:
                url = f"{self.controller_url}/onos/v1/statistics/flows/{switch_id}"
                response = self.session.get(url)
                if response.status_code == 200:
                    stats = response.json()
                    return {
                        'flow_count': len(stats.get('flows', [])),
                        'bytes': sum(flow.get('bytes', 0) for flow in stats.get('flows', [])),
                        'packets': sum(flow.get('packets', 0) for flow in stats.get('flows', []))
                    }
            
            # Données d'exemple
            return {
                'flow_count': 10,
                'bytes': 1000000,
                'packets': 1000
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des statistiques: {str(e)}")
            return {}
    
    def _convert_match_to_onos(self, match_criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Convertit les critères de correspondance au format ONOS."""
        criteria = []
        
        for key, value in match_criteria.items():
            if key == 'in_port':
                criteria.append({'type': 'IN_PORT', 'port': value})
            elif key == 'eth_type':
                criteria.append({'type': 'ETH_TYPE', 'ethType': value})
            elif key == 'ip_proto':
                criteria.append({'type': 'IP_PROTO', 'protocol': value})
            elif key == 'udp_dst':
                criteria.append({'type': 'UDP_DST', 'udpPort': value})
            elif key == 'tcp_dst':
                criteria.append({'type': 'TCP_DST', 'tcpPort': value})
        
        return criteria
    
    def _convert_actions_to_onos(self, actions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Convertit les actions au format ONOS."""
        instructions = []
        
        for action in actions:
            if action['type'] == 'output':
                instructions.append({
                    'type': 'OUTPUT',
                    'port': action['port']
                })
            elif action['type'] == 'set_queue':
                instructions.append({
                    'type': 'QUEUE',
                    'queueId': action['queue_id']
                })
            elif action['type'] == 'meter':
                instructions.append({
                    'type': 'METER',
                    'meterId': action['meter_id']
                })
        
        return instructions
    
    def _convert_actions_to_odl(self, actions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Convertit les actions au format OpenDaylight."""
        instructions = []
        
        for i, action in enumerate(actions):
            instruction = {
                'order': i,
                'apply-actions': {
                    'action': []
                }
            }
            
            if action['type'] == 'output':
                instruction['apply-actions']['action'].append({
                    'order': 0,
                    'output-action': {
                        'output-node-connector': action['port']
                    }
                })
            
            instructions.append(instruction)
        
        return instructions
    
    def _create_match_criteria(self, traffic_class: Dict[str, Any]) -> Dict[str, Any]:
        """Crée les critères de correspondance à partir d'une classe de trafic."""
        match = {}
        
        # Port source/destination
        if 'port_start' in traffic_class:
            if traffic_class['protocol'] == 'tcp':
                match['tcp_dst'] = traffic_class['port_start']
            elif traffic_class['protocol'] == 'udp':
                match['udp_dst'] = traffic_class['port_start']
        
        # Protocole
        if 'protocol' in traffic_class:
            match['eth_type'] = '0x800'  # IPv4
            if traffic_class['protocol'] == 'tcp':
                match['ip_proto'] = 6
            elif traffic_class['protocol'] == 'udp':
                match['ip_proto'] = 17
        
        # DSCP
        if 'dscp' in traffic_class and traffic_class['dscp'] != 'default':
            match['ip_dscp'] = self._dscp_to_value(traffic_class['dscp'])
        
        return match
    
    def _dscp_to_value(self, dscp: str) -> int:
        """Convertit un marquage DSCP en valeur numérique."""
        dscp_map = {
            'AF11': 10, 'AF12': 12, 'AF13': 14,
            'AF21': 18, 'AF22': 20, 'AF23': 22,
            'AF31': 26, 'AF32': 28, 'AF33': 30,
            'AF41': 34, 'AF42': 36, 'AF43': 38,
            'EF': 46,
            'CS0': 0, 'CS1': 8, 'CS2': 16, 'CS3': 24,
            'CS4': 32, 'CS5': 40, 'CS6': 48, 'CS7': 56
        }
        return dscp_map.get(dscp.upper(), 0)
    
    def _map_priority_to_openflow(self, qos_priority: int) -> int:
        """Mappe une priorité QoS vers une priorité OpenFlow."""
        priority_map = {
            7: FlowPriority.VOICE,
            6: FlowPriority.VIDEO,
            5: FlowPriority.VIDEO,
            4: FlowPriority.INTERACTIVE,
            3: FlowPriority.INTERACTIVE,
            2: FlowPriority.BULK,
            1: FlowPriority.BULK,
            0: FlowPriority.DEFAULT
        }
        return priority_map.get(qos_priority, FlowPriority.DEFAULT)
    
    def _remove_flow(self, switch_id: str, flow_id: Optional[str]) -> bool:
        """Supprime un flux du contrôleur."""
        try:
            if not flow_id:
                return True
            
            if self.controller_type == SDNControllerType.ONOS:
                url = f"{self.controller_url}/onos/v1/flows/{switch_id}/{flow_id}"
                response = self.session.delete(url)
                return response.status_code in [200, 204]
            
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de la suppression du flux: {str(e)}")
            return False