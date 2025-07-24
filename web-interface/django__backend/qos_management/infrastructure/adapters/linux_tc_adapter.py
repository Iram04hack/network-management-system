"""
Adaptateur pour la configuration QoS sur Linux via Traffic Control (tc).

Ce module implémente l'adaptateur permettant de configurer la QoS sur
les systèmes Linux via les commandes tc (iproute2).
"""

import logging
import subprocess
from typing import Dict, List, Any, Optional

from ...domain.interfaces import QoSConfigurationService, QoSConfigurationResult
from ...domain.algorithms import (
    QueueParameters, 
    CongestionParameters, 
    QueueConfiguration,
    QueueAlgorithmType,
    CongestionAlgorithmType
)

logger = logging.getLogger(__name__)


class LinuxTCAdapter(QoSConfigurationService):
    """
    Adaptateur pour configurer la QoS sur Linux avec Traffic Control.
    
    Cette classe implémente l'interface QoSConfigurationService pour les
    systèmes Linux en générant des commandes tc appropriées.
    """

    def __init__(self, ssh_connector=None):
        """
        Initialise l'adaptateur avec un connecteur SSH optionnel.
        
        Args:
            ssh_connector: Connecteur permettant d'exécuter des commandes
                          sur des systèmes distants (optionnel pour local).
        """
        self.ssh_connector = ssh_connector

    def apply_policy(self, device_id: int, interface_id: int, policy_id: int) -> bool:
        """
        Applique une politique QoS à une interface Linux.
        
        Args:
            device_id: ID de l'équipement (peut être local)
            interface_id: ID de l'interface
            policy_id: ID de la politique
            
        Returns:
            True si l'application a réussi
        """
        try:
            # Dans un vrai scénario, récupérer les infos depuis la DB
            interface_name = f"eth{interface_id}"  # Simplification
            
            # Générer et exécuter les commandes
            commands = self._generate_tc_commands(interface_name, policy_id)
            success, message = self._execute_commands(commands)
            
            logger.info(f"Politique QoS {policy_id} appliquée sur {interface_name}: {message}")
            return success
            
        except Exception as e:
            logger.error(f"Erreur lors de l'application de la politique QoS: {str(e)}")
            return False

    def remove_policy(self, device_id: int, interface_id: int) -> bool:
        """
        Supprime la politique QoS d'une interface Linux.
        
        Args:
            device_id: ID de l'équipement
            interface_id: ID de l'interface
            
        Returns:
            True si la suppression a réussi
        """
        try:
            interface_name = f"eth{interface_id}"  # Simplification
            
            # Commandes pour supprimer la QoS
            commands = [
                f"tc qdisc del dev {interface_name} root 2>/dev/null || true",
                f"tc qdisc del dev {interface_name} ingress 2>/dev/null || true"
            ]
            
            success, message = self._execute_commands(commands)
            logger.info(f"Politique QoS supprimée de {interface_name}: {message}")
            return success
            
        except Exception as e:
            logger.error(f"Erreur lors de la suppression de la politique QoS: {str(e)}")
            return False

    def get_applied_policies(self, device_id: int) -> Dict[str, Any]:
        """
        Récupère les politiques QoS appliquées sur un équipement Linux.
        
        Args:
            device_id: ID de l'équipement
            
        Returns:
            Dictionnaire des politiques appliquées par interface
        """
        try:
            # Commande pour lister les qdisc actifs
            commands = ["tc qdisc show"]
            success, output = self._execute_commands(commands, capture_output=True)
            
            if success:
                return self._parse_tc_output(output)
            else:
                return {}
                
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des politiques: {str(e)}")
            return {}

    def apply_htb_configuration(
        self, 
        interface_name: str, 
        configuration: Dict[str, Any]
    ) -> QoSConfigurationResult:
        """
        Applique une configuration HTB (Hierarchical Token Bucket) sur Linux.
        
        Args:
            interface_name: Nom de l'interface (ex: eth0, enp3s0)
            configuration: Dictionnaire contenant la configuration HTB
            
        Returns:
            Résultat de l'opération de configuration
        """
        try:
            total_bandwidth = configuration.get('total_bandwidth', 100000)  # 100 Mbps par défaut
            queue_configs = configuration.get('queue_configurations', [])
            
            commands = []
            
            # 1. Supprimer la configuration existante
            commands.append(f"tc qdisc del dev {interface_name} root 2>/dev/null || true")
            
            # 2. Créer la qdisc racine HTB
            commands.append(f"tc qdisc add dev {interface_name} root handle 1: htb default 30")
            
            # 3. Créer la classe racine
            commands.append(f"tc class add dev {interface_name} parent 1: classid 1:1 htb rate {total_bandwidth}kbit")
            
            # 4. Créer les classes pour chaque classe de trafic
            class_id = 10
            filter_handle = 1
            
            for qc in queue_configs:
                tc = qc.traffic_class
                qp = qc.queue_params
                cp = qc.congestion_params
                
                # Créer la classe HTB
                rate = qp.service_rate if qp.service_rate > 0 else 1000  # 1 Mbps minimum
                ceil = rate * 2  # Permettre le burst jusqu'à 2x le rate
                
                commands.append(
                    f"tc class add dev {interface_name} parent 1:1 classid 1:{class_id} "
                    f"htb rate {rate}kbit ceil {ceil}kbit"
                )
                
                # Ajouter une qdisc leaf selon le type d'évitement de congestion
                if cp and cp.algorithm == CongestionAlgorithmType.RED:
                    commands.append(
                        f"tc qdisc add dev {interface_name} parent 1:{class_id} handle {class_id}: "
                        f"red limit {qp.queue_limit} min {cp.min_threshold} max {cp.max_threshold} "
                        f"avpkt 1000 burst {qp.buffer_size}"
                    )
                elif cp and cp.algorithm == CongestionAlgorithmType.ECN:
                    # Utiliser FQ-CoDel pour ECN
                    commands.append(
                        f"tc qdisc add dev {interface_name} parent 1:{class_id} handle {class_id}: "
                        f"fq_codel limit {qp.queue_limit} target 5ms interval 100ms ecn"
                    )
                else:
                    # SFQ par défaut (Stochastic Fair Queuing)
                    commands.append(
                        f"tc qdisc add dev {interface_name} parent 1:{class_id} handle {class_id}: "
                        f"sfq perturb 10"
                    )
                
                # Ajouter les filtres pour classifier le trafic
                filters = self._generate_tc_filters(interface_name, tc, class_id, filter_handle)
                commands.extend(filters)
                
                class_id += 1
                filter_handle += 10
            
            # 5. Classe par défaut
            commands.append(
                f"tc class add dev {interface_name} parent 1:1 classid 1:30 "
                f"htb rate 1000kbit ceil {total_bandwidth}kbit"
            )
            commands.append(
                f"tc qdisc add dev {interface_name} parent 1:30 handle 30: sfq perturb 10"
            )
            
            # Exécuter les commandes
            success, message = self._execute_commands(commands)
            
            return QoSConfigurationResult(
                success=success,
                commands=commands,
                message=message
            )
            
        except Exception as e:
            error_msg = f"Erreur lors de la configuration HTB: {str(e)}"
            logger.error(error_msg)
            return QoSConfigurationResult(
                success=False,
                commands=[],
                message=error_msg
            )

    def apply_fq_codel_configuration(
        self,
        interface_name: str,
        configuration: Dict[str, Any]
    ) -> QoSConfigurationResult:
        """
        Applique une configuration FQ-CoDel sur Linux.
        
        Args:
            interface_name: Nom de l'interface
            configuration: Configuration FQ-CoDel
            
        Returns:
            Résultat de l'opération
        """
        try:
            queue_configs = configuration.get('queue_configurations', [])
            commands = []
            
            # Supprimer la configuration existante
            commands.append(f"tc qdisc del dev {interface_name} root 2>/dev/null || true")
            
            if len(queue_configs) == 1:
                # Configuration FQ-CoDel simple
                qc = queue_configs[0]
                qp = qc.queue_params
                cp = qc.congestion_params
                
                target = cp.min_threshold if cp else 5000  # 5ms par défaut
                interval = cp.max_threshold if cp else 100000  # 100ms par défaut
                limit = qp.queue_limit if qp else 1024
                
                commands.append(
                    f"tc qdisc add dev {interface_name} root fq_codel "
                    f"limit {limit} target {target}us interval {interval}us ecn"
                )
            else:
                # Configuration multi-classes avec HTB + FQ-CoDel
                total_bandwidth = configuration.get('total_bandwidth', 100000)
                commands.append(f"tc qdisc add dev {interface_name} root handle 1: htb default 30")
                commands.append(f"tc class add dev {interface_name} parent 1: classid 1:1 htb rate {total_bandwidth}kbit")
                
                class_id = 10
                for qc in queue_configs:
                    tc = qc.traffic_class
                    qp = qc.queue_params
                    cp = qc.congestion_params
                    
                    rate = qp.service_rate if qp.service_rate > 0 else 1000
                    commands.append(
                        f"tc class add dev {interface_name} parent 1:1 classid 1:{class_id} "
                        f"htb rate {rate}kbit"
                    )
                    
                    target = cp.min_threshold if cp else 5000
                    interval = cp.max_threshold if cp else 100000
                    limit = qp.queue_limit if qp else 1024
                    
                    commands.append(
                        f"tc qdisc add dev {interface_name} parent 1:{class_id} "
                        f"fq_codel limit {limit} target {target}us interval {interval}us ecn"
                    )
                    
                    class_id += 1
            
            success, message = self._execute_commands(commands)
            
            return QoSConfigurationResult(
                success=success,
                commands=commands,
                message=message
            )
            
        except Exception as e:
            error_msg = f"Erreur lors de la configuration FQ-CoDel: {str(e)}"
            logger.error(error_msg)
            return QoSConfigurationResult(
                success=False,
                commands=[],
                message=error_msg
            )

    def _generate_tc_commands(self, interface_name: str, policy_id: int) -> List[str]:
        """
        Génère les commandes tc pour une politique donnée.
        
        Args:
            interface_name: Nom de l'interface
            policy_id: ID de la politique
            
        Returns:
            Liste de commandes tc
        """
        # Dans un vrai scénario, récupérer la politique depuis la DB
        # Ici, exemple avec HTB basique
        return [
            f"tc qdisc del dev {interface_name} root 2>/dev/null || true",
            f"tc qdisc add dev {interface_name} root handle 1: htb default 30",
            f"tc class add dev {interface_name} parent 1: classid 1:1 htb rate 100mbit",
            f"tc class add dev {interface_name} parent 1:1 classid 1:10 htb rate 50mbit ceil 80mbit",
            f"tc class add dev {interface_name} parent 1:1 classid 1:20 htb rate 30mbit ceil 50mbit",
            f"tc class add dev {interface_name} parent 1:1 classid 1:30 htb rate 20mbit ceil 100mbit",
            f"tc qdisc add dev {interface_name} parent 1:10 handle 10: sfq perturb 10",
            f"tc qdisc add dev {interface_name} parent 1:20 handle 20: sfq perturb 10",
            f"tc qdisc add dev {interface_name} parent 1:30 handle 30: sfq perturb 10"
        ]

    def _generate_tc_filters(self, interface_name: str, traffic_class, class_id: int, handle_base: int) -> List[str]:
        """
        Génère les filtres tc pour classifier le trafic.
        
        Args:
            interface_name: Nom de l'interface
            traffic_class: Classe de trafic
            class_id: ID de la classe tc
            handle_base: Base pour les handles des filtres
            
        Returns:
            Liste de commandes de filtre tc
        """
        commands = []
        
        # Filtrer par port si spécifié
        if hasattr(traffic_class, 'port_start') and traffic_class.port_start:
            if traffic_class.port_start == traffic_class.port_end:
                commands.append(
                    f"tc filter add dev {interface_name} parent 1: protocol ip prio {handle_base} "
                    f"u32 match ip dport {traffic_class.port_start} 0xffff flowid 1:{class_id}"
                )
            else:
                # Pour les plages de ports, utiliser plusieurs filtres (simplification)
                commands.append(
                    f"tc filter add dev {interface_name} parent 1: protocol ip prio {handle_base} "
                    f"u32 match ip dport {traffic_class.port_start} 0xfff0 flowid 1:{class_id}"
                )
        
        # Filtrer par DSCP si spécifié
        if hasattr(traffic_class, 'dscp') and traffic_class.dscp and traffic_class.dscp != 'default':
            dscp_hex = self._dscp_to_hex(traffic_class.dscp)
            commands.append(
                f"tc filter add dev {interface_name} parent 1: protocol ip prio {handle_base + 1} "
                f"u32 match ip tos {dscp_hex} 0xfc flowid 1:{class_id}"
            )
        
        # Filtrer par protocole si spécifié
        if hasattr(traffic_class, 'protocol') and traffic_class.protocol and traffic_class.protocol != 'any':
            protocol_num = self._protocol_to_number(traffic_class.protocol)
            if protocol_num:
                commands.append(
                    f"tc filter add dev {interface_name} parent 1: protocol ip prio {handle_base + 2} "
                    f"u32 match ip protocol {protocol_num} 0xff flowid 1:{class_id}"
                )
        
        return commands

    def _dscp_to_hex(self, dscp: str) -> str:
        """
        Convertit un marquage DSCP en valeur hexadécimale pour tc.
        
        Args:
            dscp: Marquage DSCP (ex: 'AF21', 'EF')
            
        Returns:
            Valeur hexadécimale
        """
        dscp_map = {
            'AF11': '0x28', 'AF12': '0x30', 'AF13': '0x38',
            'AF21': '0x48', 'AF22': '0x50', 'AF23': '0x58',
            'AF31': '0x68', 'AF32': '0x70', 'AF33': '0x78',
            'AF41': '0x88', 'AF42': '0x90', 'AF43': '0x98',
            'EF': '0xb8',
            'CS1': '0x20', 'CS2': '0x40', 'CS3': '0x60',
            'CS4': '0x80', 'CS5': '0xa0', 'CS6': '0xc0', 'CS7': '0xe0'
        }
        return dscp_map.get(dscp, '0x00')

    def _protocol_to_number(self, protocol: str) -> Optional[int]:
        """
        Convertit un nom de protocole en numéro pour tc.
        
        Args:
            protocol: Nom du protocole
            
        Returns:
            Numéro du protocole ou None
        """
        protocol_map = {
            'tcp': 6,
            'udp': 17,
            'icmp': 1,
            'igmp': 2
        }
        return protocol_map.get(protocol.lower())

    def _execute_commands(self, commands: List[str], capture_output: bool = False):
        """
        Exécute une liste de commandes tc.
        
        Args:
            commands: Liste de commandes à exécuter
            capture_output: Si True, capture la sortie
            
        Returns:
            Tuple (success, output/message)
        """
        try:
            if self.ssh_connector:
                # Exécution distante via SSH
                return self.ssh_connector.execute_commands(commands, capture_output)
            else:
                # Exécution locale
                output = []
                for cmd in commands:
                    logger.debug(f"Exécution: {cmd}")
                    if capture_output:
                        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                        if result.returncode != 0:
                            logger.warning(f"Commande échouée: {cmd}, erreur: {result.stderr}")
                        output.append(result.stdout)
                    else:
                        result = subprocess.run(cmd, shell=True)
                        if result.returncode != 0:
                            logger.warning(f"Commande échouée: {cmd}")
                
                if capture_output:
                    return True, '\n'.join(output)
                else:
                    return True, "Commandes exécutées avec succès"
                    
        except Exception as e:
            error_msg = f"Erreur lors de l'exécution des commandes: {str(e)}"
            logger.error(error_msg)
            return False, error_msg

    def _parse_tc_output(self, output: str) -> Dict[str, Any]:
        """
        Parse la sortie de 'tc qdisc show' pour extraire les politiques.
        
        Args:
            output: Sortie de la commande tc
            
        Returns:
            Dictionnaire des politiques par interface
        """
        policies = {}
        
        try:
            lines = output.strip().split('\n')
            for line in lines:
                if 'qdisc' in line:
                    parts = line.split()
                    if len(parts) >= 5 and parts[0] == 'qdisc':
                        qdisc_type = parts[1]
                        interface = parts[4].rstrip(':')
                        
                        if interface not in policies:
                            policies[interface] = []
                        
                        policies[interface].append({
                            'type': qdisc_type,
                            'handle': parts[2] if len(parts) > 2 else '',
                            'parent': parts[3] if len(parts) > 3 else ''
                        })
        except Exception as e:
            logger.error(f"Erreur lors du parsing de la sortie tc: {str(e)}")
        
        return {'interfaces': policies} 