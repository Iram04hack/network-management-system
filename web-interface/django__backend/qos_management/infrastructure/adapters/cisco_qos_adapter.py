"""
Adaptateur pour la configuration QoS sur les équipements Cisco.

Ce module implemente l'adaptateur permettant de configurer la QoS sur
les équipements réseau Cisco via CLI.
"""

import re
import logging
from typing import Dict, List, Any, Optional, Tuple

from ...domain.interfaces import QoSConfigurationService, QoSConfigurationResult
from ...domain.algorithms import (
    QueueParameters, 
    CongestionParameters, 
    QueueConfiguration,
    QueueAlgorithmType,
    CongestionAlgorithmType
)


logger = logging.getLogger(__name__)


class CiscoQoSAdapter(QoSConfigurationService):
    """
    Adaptateur pour configurer la QoS sur les équipements Cisco.
    
    Cette classe implémente l'interface QoSConfigurationService pour les
    équipements Cisco en générant des commandes CLI appropriées.
    """

    def __init__(self, network_connector):
        """
        Initialise l'adaptateur avec un connecteur réseau.
        
        Args:
            network_connector: Connecteur permettant d'exécuter des commandes
                              sur les équipements réseau.
        """
        self.network_connector = network_connector

    def apply_cbwfq_configuration(
        self, 
        device_id: int, 
        interface_name: str, 
        configuration: Dict[str, Any]
    ) -> QoSConfigurationResult:
        """
        Applique une configuration CBWFQ sur un équipement Cisco.
        
        Args:
            device_id: ID de l'équipement réseau
            interface_name: Nom de l'interface (ex: GigabitEthernet0/1)
            configuration: Dictionnaire contenant la configuration CBWFQ
            
        Returns:
            Résultat de l'opération de configuration
        """
        try:
            # Extraire les informations de configuration
            policy_name = configuration.get('policy_name', 'QoS-Policy')
            direction = configuration.get('direction', 'egress')
            queue_configs = configuration.get('queue_configurations', [])
            
            # Générer les commandes Cisco IOS
            commands = []
            
            # 1. Créer la policy-map
            commands.append(f"configure terminal")
            commands.append(f"class-map match-any default-class")
            commands.append(f"match any")
            
            # 2. Créer les class-maps pour chaque classe de trafic
            for i, qc in enumerate(queue_configs):
                tc = qc.traffic_class
                class_name = re.sub(r'[^a-zA-Z0-9_-]', '_', tc.name)
                
                commands.append(f"class-map match-all {class_name}")
                
                # Ajouter les critères de correspondance
                if tc.protocol:
                    commands.append(f"match protocol {tc.protocol}")
                
                if tc.dscp != 'default':
                    commands.append(f"match dscp {tc.dscp}")
                
                if tc.port_start and tc.port_end:
                    if tc.port_start == tc.port_end:
                        commands.append(f"match port {tc.port_start}")
                    else:
                        commands.append(f"match port range {tc.port_start} {tc.port_end}")
                
                # Ajouter des matchs supplémentaires si nécessaire
                for filter_key, filter_value in tc.filters.items():
                    if filter_key == 'ip_src':
                        commands.append(f"match source-address ip {filter_value}")
                    elif filter_key == 'ip_dst':
                        commands.append(f"match destination-address ip {filter_value}")
            
            # 3. Créer la policy-map
            commands.append(f"policy-map {policy_name}")
            
            # 4. Configurer chaque classe
            for i, qc in enumerate(queue_configs):
                tc = qc.traffic_class
                qp = qc.queue_params
                cp = qc.congestion_params
                
                class_name = re.sub(r'[^a-zA-Z0-9_-]', '_', tc.name)
                commands.append(f"class {class_name}")
                
                # Configurer la bande passante
                if qp.bandwidth_percent > 0:
                    commands.append(f"bandwidth percent {int(qp.bandwidth_percent)}")
                else:
                    commands.append(f"bandwidth {qp.service_rate}")
                
                # Configurer le paramètre de poids si nécessaire
                if qp.weight > 1.0:
                    commands.append(f"fair-queue {int(qp.queue_limit)} weight {int(qp.weight)}")
                else:
                    commands.append(f"fair-queue {int(qp.queue_limit)}")
                
                # Configurer la limite de la file
                commands.append(f"queue-limit {int(qp.queue_limit)}")
                
                # Configurer les mécanismes anti-congestion
                if cp and cp.algorithm == CongestionAlgorithmType.RED:
                    commands.append(f"random-detect")
                    commands.append(f"random-detect precedence 0 {cp.min_threshold} {cp.max_threshold} 1")
                elif cp and cp.algorithm == CongestionAlgorithmType.WRED:
                    commands.append(f"random-detect dscp-based")
                    
                    # Configurer WRED pour chaque DSCP si spécifié
                    if cp.dscp_weights:
                        for dscp, weight in cp.dscp_weights.items():
                            drop_prob = int(cp.drop_probability * 10)  # Convert to 1-10 scale
                            commands.append(
                                f"random-detect dscp {dscp} {cp.min_threshold} {cp.max_threshold} {drop_prob}"
                            )
                    else:
                        # Configuration par défaut
                        commands.append(
                            f"random-detect dscp-based {cp.min_threshold} {cp.max_threshold} 10"
                        )
            
            # Ajouter la classe default à la fin
            commands.append(f"class class-default")
            commands.append(f"fair-queue")
            
            # 5. Appliquer la service-policy à l'interface
            direction_cmd = "output" if direction == "egress" else "input"
            commands.append(f"interface {interface_name}")
            commands.append(f"service-policy {direction_cmd} {policy_name}")
            commands.append(f"exit")
            commands.append(f"end")
            
            # 6. Exécuter les commandes sur l'équipement
            success, message = self._execute_commands(device_id, commands)
            
            # 7. Retourner le résultat
            return QoSConfigurationResult(
                success=success,
                commands=commands,
                message=message
            )
            
        except Exception as e:
            logger.exception(f"Erreur lors de la configuration CBWFQ: {str(e)}")
            return QoSConfigurationResult(
                success=False,
                commands=[],
                message=f"Erreur lors de la configuration CBWFQ: {str(e)}"
            )

    def apply_llq_configuration(
        self, 
        device_id: int, 
        interface_name: str, 
        configuration: Dict[str, Any]
    ) -> QoSConfigurationResult:
        """
        Applique une configuration LLQ sur un équipement Cisco.
        
        Args:
            device_id: ID de l'équipement réseau
            interface_name: Nom de l'interface (ex: GigabitEthernet0/1)
            configuration: Dictionnaire contenant la configuration LLQ
            
        Returns:
            Résultat de l'opération de configuration
        """
        try:
            # Extraire les informations de configuration
            policy_name = configuration.get('policy_name', 'LLQ-Policy')
            direction = configuration.get('direction', 'egress')
            queue_configs = configuration.get('queue_configurations', [])
            
            # Trier les configs par niveau de priorité (décroissant)
            queue_configs.sort(key=lambda qc: qc.queue_params.priority_level, reverse=True)
            
            # Séparer les files prioritaires et standard
            priority_queues = [qc for qc in queue_configs if qc.queue_params.priority_level >= 5]
            standard_queues = [qc for qc in queue_configs if qc.queue_params.priority_level < 5]
            
            # Générer les commandes Cisco IOS
            commands = []
            
            # 1. Démarrer la configuration
            commands.append(f"configure terminal")
            
            # 2. Créer une classe par défaut
            commands.append(f"class-map match-any default-class")
            commands.append(f"match any")
            
            # 3. Créer les class-maps pour chaque classe de trafic
            for qc in queue_configs:
                tc = qc.traffic_class
                class_name = re.sub(r'[^a-zA-Z0-9_-]', '_', tc.name)
                
                commands.append(f"class-map match-all {class_name}")
                
                # Ajouter les critères de correspondance
                if tc.protocol:
                    commands.append(f"match protocol {tc.protocol}")
                
                if tc.dscp != 'default':
                    commands.append(f"match dscp {tc.dscp}")
                
                if tc.port_start and tc.port_end:
                    if tc.port_start == tc.port_end:
                        commands.append(f"match port {tc.port_start}")
                    else:
                        commands.append(f"match port range {tc.port_start} {tc.port_end}")
                
                # Ajouter des matchs supplémentaires si nécessaire
                for filter_key, filter_value in tc.filters.items():
                    if filter_key == 'ip_src':
                        commands.append(f"match source-address ip {filter_value}")
                    elif filter_key == 'ip_dst':
                        commands.append(f"match destination-address ip {filter_value}")
            
            # 4. Créer la policy-map
            commands.append(f"policy-map {policy_name}")
            
            # 5. Configurer les classes prioritaires avec la commande "priority"
            priority_levels = {}
            for qc in priority_queues:
                tc = qc.traffic_class
                qp = qc.queue_params
                
                class_name = re.sub(r'[^a-zA-Z0-9_-]', '_', tc.name)
                commands.append(f"class {class_name}")
                
                # Configurer la priorité stricte avec limite de bande passante
                commands.append(f"priority {qp.service_rate}")
                
                # Configurer les polices pour éviter la famine des autres classes
                # (La priorité stricte pourrait consommer toute la bande passante)
                commands.append(f"police {qp.service_rate * 1000} {tc.burst * 1000} conform-action transmit exceed-action drop")
                
                # Enregistrer le niveau de priorité pour cet ordre
                priority_level = qp.priority_level
                if priority_level not in priority_levels:
                    priority_levels[priority_level] = []
                priority_levels[priority_level].append(class_name)
            
            # 6. Configurer les classes standard avec CBWFQ
            for qc in standard_queues:
                tc = qc.traffic_class
                qp = qc.queue_params
                cp = qc.congestion_params
                
                class_name = re.sub(r'[^a-zA-Z0-9_-]', '_', tc.name)
                commands.append(f"class {class_name}")
                
                # Configurer la bande passante
                if qp.bandwidth_percent > 0:
                    commands.append(f"bandwidth percent {int(qp.bandwidth_percent)}")
                else:
                    commands.append(f"bandwidth {qp.service_rate}")
                
                # Configurer le paramètre de poids pour la répartition équitable
                if qp.weight > 1.0:
                    commands.append(f"fair-queue {int(qp.queue_limit)} weight {int(qp.weight)}")
                else:
                    commands.append(f"fair-queue {int(qp.queue_limit)}")
                
                # Configurer la limite de la file
                commands.append(f"queue-limit {int(qp.queue_limit)}")
                
                # Configurer les mécanismes anti-congestion
                if cp and cp.algorithm in (CongestionAlgorithmType.RED, CongestionAlgorithmType.WRED):
                    self._add_congestion_avoidance_commands(commands, cp)
            
            # 7. Ajouter la classe default à la fin
            commands.append(f"class class-default")
            commands.append(f"fair-queue")
            
            # 8. Appliquer la service-policy à l'interface
            direction_cmd = "output" if direction == "egress" else "input"
            commands.append(f"interface {interface_name}")
            commands.append(f"service-policy {direction_cmd} {policy_name}")
            commands.append(f"exit")
            commands.append(f"end")
            
            # 9. Exécuter les commandes sur l'équipement
            success, message = self._execute_commands(device_id, commands)
            
            # 10. Retourner le résultat
            return QoSConfigurationResult(
                success=success,
                commands=commands,
                message=message
            )
            
        except Exception as e:
            logger.exception(f"Erreur lors de la configuration LLQ: {str(e)}")
            return QoSConfigurationResult(
                success=False,
                commands=[],
                message=f"Erreur lors de la configuration LLQ: {str(e)}"
            )

    def apply_red_configuration(
        self,
        device_id: int,
        interface_name: str,
        queue_name: str,
        red_params: Dict[str, Any]
    ) -> QoSConfigurationResult:
        """
        Applique une configuration RED sur une file d'attente spécifique.
        
        Args:
            device_id: ID de l'équipement réseau
            interface_name: Nom de l'interface
            queue_name: Nom de la file d'attente
            red_params: Paramètres RED (min_threshold, max_threshold, drop_probability)
            
        Returns:
            Résultat de l'opération de configuration
        """
        try:
            # Extraire les paramètres RED
            min_threshold = red_params.get('min_threshold', 20)
            max_threshold = red_params.get('max_threshold', 40)
            max_probability = red_params.get('drop_probability', 0.1)
            
            # Convertir la probabilité en échelle Cisco (1-10)
            drop_prob_scale = int(max_probability * 10)
            drop_prob_scale = max(1, min(10, drop_prob_scale))
            
            # Générer les commandes
            commands = [
                f"configure terminal",
                f"policy-map {queue_name}",
                f"class class-default",
                f"random-detect",
                f"random-detect precedence 0 {min_threshold} {max_threshold} {drop_prob_scale}",
                f"exit",
                f"exit",
                f"interface {interface_name}",
                f"service-policy output {queue_name}",
                f"end"
            ]
            
            # Exécuter les commandes
            success, message = self._execute_commands(device_id, commands)
            
            return QoSConfigurationResult(
                success=success,
                commands=commands,
                message=message
            )
        
        except Exception as e:
            logger.exception(f"Erreur lors de la configuration RED: {str(e)}")
            return QoSConfigurationResult(
                success=False,
                commands=[],
                message=f"Erreur lors de la configuration RED: {str(e)}"
            )
    
    def _add_congestion_avoidance_commands(
        self,
        commands: List[str],
        congestion_params: CongestionParameters
    ) -> None:
        """
        Ajoute les commandes pour configurer l'évitement de congestion.
        
        Args:
            commands: Liste de commandes à compléter
            congestion_params: Paramètres d'évitement de congestion
        """
        if congestion_params.algorithm == CongestionAlgorithmType.RED:
            commands.append(f"random-detect")
            # Configuration par précédence
            drop_prob = int(congestion_params.drop_probability * 10)  # Sur une échelle de 1-10
            commands.append(f"random-detect precedence 0 {congestion_params.min_threshold} "
                           f"{congestion_params.max_threshold} {drop_prob}")
        
        elif congestion_params.algorithm == CongestionAlgorithmType.WRED:
            commands.append(f"random-detect dscp-based")
            
            # Configurer WRED pour chaque DSCP si spécifié
            if congestion_params.dscp_weights:
                for dscp, weight in congestion_params.dscp_weights.items():
                    drop_prob = int(congestion_params.drop_probability * 10)  # Sur une échelle de 1-10
                    min_th = congestion_params.min_threshold
                    max_th = congestion_params.max_threshold
                    
                    # Ajuster les seuils en fonction du poids DSCP
                    if weight > 0.5:  # Trafic prioritaire
                        # Augmenter les seuils pour réduire la probabilité de rejet
                        min_th = int(min_th * (1 + weight))
                        max_th = int(max_th * (1 + weight))
                    
                    commands.append(f"random-detect dscp {dscp} {min_th} {max_th} {drop_prob}")
            else:
                # Configuration par défaut
                commands.append(f"random-detect dscp-based "
                               f"{congestion_params.min_threshold} "
                               f"{congestion_params.max_threshold} 10")
    
    def _execute_commands(self, device_id: int, commands: List[str]) -> Tuple[bool, str]:
        """
        Exécute une liste de commandes sur un équipement réseau.
        
        Args:
            device_id: ID de l'équipement
            commands: Liste de commandes à exécuter
            
        Returns:
            Tuple (success, message)
        """
        try:
            # Utilisez le connecteur réseau pour exécuter les commandes
            response = self.network_connector.execute_commands(device_id, commands)
            
            # Vérifiez si les commandes ont réussi
            if response.get('success', False):
                return True, "Configuration appliquée avec succès"
            else:
                error_message = response.get('message', 'Erreur inconnue')
                return False, f"Échec de la configuration: {error_message}"
                
        except Exception as e:
            logger.exception(f"Erreur lors de l'exécution des commandes: {str(e)}")
            return False, f"Erreur lors de l'exécution des commandes: {str(e)}" 