"""
Adaptateur pour la configuration QoS sur les équipements Juniper JUNOS.

Ce module implémente l'adaptateur permettant de configurer la QoS sur
les équipements réseau Juniper via CLI JUNOS.
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


class JuniperQoSAdapter(QoSConfigurationService):
    """
    Adaptateur pour configurer la QoS sur les équipements Juniper JUNOS.
    
    Cette classe implémente l'interface QoSConfigurationService pour les
    équipements Juniper en générant des commandes JUNOS appropriées.
    """

    def __init__(self, network_connector):
        """
        Initialise l'adaptateur avec un connecteur réseau.
        
        Args:
            network_connector: Connecteur permettant d'exécuter des commandes
                              sur les équipements Juniper.
        """
        self.network_connector = network_connector

    def apply_policy(self, device_id: int, interface_id: int, policy_id: int) -> bool:
        """
        Applique une politique QoS à une interface d'un équipement Juniper.
        
        Args:
            device_id: ID de l'équipement réseau
            interface_id: ID de l'interface
            policy_id: ID de la politique
            
        Returns:
            True si l'application a réussi
        """
        try:
            # Dans un vrai scénario, récupérer les infos depuis la DB
            interface_name = f"ge-0/0/{interface_id}"  # Format Juniper typique
            
            # Générer et appliquer la configuration
            config_result = self._apply_juniper_configuration(
                device_id, interface_name, policy_id
            )
            
            return config_result.success
            
        except Exception as e:
            logger.error(f"Erreur lors de l'application de la politique QoS Juniper: {str(e)}")
            return False

    def remove_policy(self, device_id: int, interface_id: int) -> bool:
        """
        Supprime la politique QoS d'une interface Juniper.
        
        Args:
            device_id: ID de l'équipement
            interface_id: ID de l'interface
            
        Returns:
            True si la suppression a réussi
        """
        try:
            interface_name = f"ge-0/0/{interface_id}"
            
            # Configuration pour supprimer la QoS
            commands = [
                "configure",
                f"delete interfaces {interface_name} unit 0 scheduler-map",
                f"delete interfaces {interface_name} unit 0 classifiers",
                "commit and-quit"
            ]
            
            success, message = self._execute_commands(device_id, commands)
            logger.info(f"Politique QoS supprimée de {interface_name}: {message}")
            return success
            
        except Exception as e:
            logger.error(f"Erreur lors de la suppression de la politique QoS Juniper: {str(e)}")
            return False

    def get_applied_policies(self, device_id: int) -> Dict[str, Any]:
        """
        Récupère les politiques QoS appliquées sur un équipement Juniper.
        
        Args:
            device_id: ID de l'équipement
            
        Returns:
            Dictionnaire des politiques appliquées par interface
        """
        try:
            # Commande pour afficher la configuration QoS
            commands = [
                "show configuration class-of-service | display set",
                "show configuration interfaces | display set | match scheduler-map"
            ]
            
            success, output = self._execute_commands(device_id, commands, capture_output=True)
            
            if success:
                return self._parse_juniper_qos_config(output)
            else:
                return {}
                
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des politiques Juniper: {str(e)}")
            return {}

    def apply_juniper_scheduler_configuration(
        self, 
        device_id: int,
        interface_name: str, 
        configuration: Dict[str, Any]
    ) -> QoSConfigurationResult:
        """
        Applique une configuration QoS complète sur un équipement Juniper.
        
        Args:
            device_id: ID de l'équipement Juniper
            interface_name: Nom de l'interface (ex: ge-0/0/0)
            configuration: Dictionnaire contenant la configuration QoS
            
        Returns:
            Résultat de l'opération de configuration
        """
        try:
            queue_configs = configuration.get('queue_configurations', [])
            policy_name = configuration.get('policy_name', 'QoS-Policy')
            
            commands = []
            
            # 1. Entrer en mode configuration
            commands.append("configure")
            
            # 2. Définir les traffic classes
            traffic_classes = self._generate_traffic_classes(queue_configs)
            commands.extend(traffic_classes)
            
            # 3. Définir les schedulers
            schedulers = self._generate_schedulers(queue_configs, policy_name)
            commands.extend(schedulers)
            
            # 4. Définir les scheduler maps
            scheduler_map = self._generate_scheduler_map(queue_configs, policy_name)
            commands.extend(scheduler_map)
            
            # 5. Définir les classifiers
            classifiers = self._generate_classifiers(queue_configs, policy_name)
            commands.extend(classifiers)
            
            # 6. Appliquer à l'interface
            interface_config = self._generate_interface_config(interface_name, policy_name)
            commands.extend(interface_config)
            
            # 7. Valider et appliquer
            commands.extend(["commit check", "commit", "exit"])
            
            # Exécuter les commandes
            success, message = self._execute_commands(device_id, commands)
            
            return QoSConfigurationResult(
                success=success,
                commands=commands,
                message=message
            )
            
        except Exception as e:
            error_msg = f"Erreur lors de la configuration QoS Juniper: {str(e)}"
            logger.error(error_msg)
            return QoSConfigurationResult(
                success=False,
                commands=[],
                message=error_msg
            )

    def _generate_traffic_classes(self, queue_configs: List[QueueConfiguration]) -> List[str]:
        """
        Génère les définitions de traffic classes JUNOS.
        
        Args:
            queue_configs: Configurations de files d'attente
            
        Returns:
            Liste de commandes JUNOS pour les traffic classes
        """
        commands = []
        
        # Traffic classes prédéfinies courantes dans JUNOS
        predefined_classes = ['best-effort', 'expedited-forwarding', 'assured-forwarding']
        
        for qc in queue_configs:
            tc = qc.traffic_class
            class_name = self._sanitize_name(tc.name)
            
            if class_name.lower() not in predefined_classes:
                commands.append(f"set class-of-service traffic-class {class_name}")
        
        return commands

    def _generate_schedulers(self, queue_configs: List[QueueConfiguration], policy_name: str) -> List[str]:
        """
        Génère les définitions de schedulers JUNOS.
        
        Args:
            queue_configs: Configurations de files d'attente
            policy_name: Nom de la politique
            
        Returns:
            Liste de commandes JUNOS pour les schedulers
        """
        commands = []
        
        for qc in queue_configs:
            tc = qc.traffic_class
            qp = qc.queue_params
            cp = qc.congestion_params
            
            class_name = self._sanitize_name(tc.name)
            scheduler_name = f"{policy_name}-{class_name}"
            
            # Définir le scheduler
            commands.append(f"set class-of-service schedulers {scheduler_name} transmit-rate {qp.service_rate}k")
            
            # Configurer la priorité
            if qp.priority_level >= 7:
                commands.append(f"set class-of-service schedulers {scheduler_name} priority high")
            elif qp.priority_level >= 4:
                commands.append(f"set class-of-service schedulers {scheduler_name} priority medium")
            else:
                commands.append(f"set class-of-service schedulers {scheduler_name} priority low")
            
            # Configurer le buffer
            if qp.buffer_size > 0:
                commands.append(f"set class-of-service schedulers {scheduler_name} buffer-size {qp.buffer_size}k")
            
            # Configurer l'évitement de congestion
            if cp:
                if cp.algorithm == CongestionAlgorithmType.RED:
                    commands.append(f"set class-of-service schedulers {scheduler_name} drop-profile-map loss-priority low protocol-drop-profile red-profile")
                elif cp.algorithm == CongestionAlgorithmType.WRED:
                    commands.append(f"set class-of-service schedulers {scheduler_name} drop-profile-map loss-priority low protocol-drop-profile wred-profile")
                    commands.append(f"set class-of-service schedulers {scheduler_name} drop-profile-map loss-priority high protocol-drop-profile wred-profile")
        
        return commands

    def _generate_scheduler_map(self, queue_configs: List[QueueConfiguration], policy_name: str) -> List[str]:
        """
        Génère la scheduler map JUNOS.
        
        Args:
            queue_configs: Configurations de files d'attente
            policy_name: Nom de la politique
            
        Returns:
            Liste de commandes JUNOS pour la scheduler map
        """
        commands = []
        scheduler_map_name = f"{policy_name}-sched-map"
        
        # Définir la scheduler map
        for i, qc in enumerate(queue_configs):
            tc = qc.traffic_class
            class_name = self._sanitize_name(tc.name)
            scheduler_name = f"{policy_name}-{class_name}"
            queue_num = i  # Numéro de file d'attente (0-7 généralement)
            
            commands.append(
                f"set class-of-service scheduler-maps {scheduler_map_name} "
                f"forwarding-class {class_name} scheduler {scheduler_name}"
            )
        
        return commands

    def _generate_classifiers(self, queue_configs: List[QueueConfiguration], policy_name: str) -> List[str]:
        """
        Génère les classifiers JUNOS pour identifier le trafic.
        
        Args:
            queue_configs: Configurations de files d'attente
            policy_name: Nom de la politique
            
        Returns:
            Liste de commandes JUNOS pour les classifiers
        """
        commands = []
        classifier_name = f"{policy_name}-classifier"
        
        # Créer un classifier DSCP
        commands.append(f"set class-of-service classifiers dscp {classifier_name} import default")
        
        # Mapper les valeurs DSCP aux forwarding classes
        dscp_mappings = {
            'AF11': 'assured-forwarding', 'AF12': 'assured-forwarding', 'AF13': 'assured-forwarding',
            'AF21': 'assured-forwarding', 'AF22': 'assured-forwarding', 'AF23': 'assured-forwarding',
            'AF31': 'assured-forwarding', 'AF32': 'assured-forwarding', 'AF33': 'assured-forwarding',
            'AF41': 'assured-forwarding', 'AF42': 'assured-forwarding', 'AF43': 'assured-forwarding',
            'EF': 'expedited-forwarding',
            'CS0': 'best-effort', 'CS1': 'best-effort', 'CS2': 'assured-forwarding',
            'CS3': 'assured-forwarding', 'CS4': 'assured-forwarding', 'CS5': 'expedited-forwarding',
            'CS6': 'network-control', 'CS7': 'network-control'
        }
        
        for qc in queue_configs:
            tc = qc.traffic_class
            if hasattr(tc, 'dscp') and tc.dscp and tc.dscp != 'default':
                class_name = self._sanitize_name(tc.name)
                dscp_value = self._get_dscp_code_point(tc.dscp)
                
                if dscp_value is not None:
                    commands.append(
                        f"set class-of-service classifiers dscp {classifier_name} "
                        f"forwarding-class {class_name} loss-priority low code-points {tc.dscp.lower()}"
                    )
        
        return commands

    def _generate_interface_config(self, interface_name: str, policy_name: str) -> List[str]:
        """
        Génère la configuration d'interface pour appliquer la QoS.
        
        Args:
            interface_name: Nom de l'interface
            policy_name: Nom de la politique
            
        Returns:
            Liste de commandes JUNOS pour l'interface
        """
        commands = []
        scheduler_map_name = f"{policy_name}-sched-map"
        classifier_name = f"{policy_name}-classifier"
        
        # Appliquer la scheduler map à l'interface
        commands.append(
            f"set interfaces {interface_name} unit 0 scheduler-map {scheduler_map_name}"
        )
        
        # Appliquer le classifier à l'interface
        commands.append(
            f"set interfaces {interface_name} unit 0 classifiers dscp {classifier_name}"
        )
        
        return commands

    def _generate_drop_profiles(self, queue_configs: List[QueueConfiguration]) -> List[str]:
        """
        Génère les profils de rejet (drop profiles) pour RED/WRED.
        
        Args:
            queue_configs: Configurations de files d'attente
            
        Returns:
            Liste de commandes JUNOS pour les drop profiles
        """
        commands = []
        
        # Profil RED générique
        commands.extend([
            "set class-of-service drop-profiles red-profile interpolate",
            "set class-of-service drop-profiles red-profile fill-level 50 drop-probability 10",
            "set class-of-service drop-profiles red-profile fill-level 75 drop-probability 50",
            "set class-of-service drop-profiles red-profile fill-level 90 drop-probability 90"
        ])
        
        # Profil WRED générique
        commands.extend([
            "set class-of-service drop-profiles wred-profile interpolate",
            "set class-of-service drop-profiles wred-profile fill-level 40 drop-probability 5",
            "set class-of-service drop-profiles wred-profile fill-level 60 drop-probability 20",
            "set class-of-service drop-profiles wred-profile fill-level 80 drop-probability 70"
        ])
        
        return commands

    def _sanitize_name(self, name: str) -> str:
        """
        Nettoie un nom pour qu'il soit compatible JUNOS.
        
        Args:
            name: Nom à nettoyer
            
        Returns:
            Nom nettoyé
        """
        # Remplacer les caractères non autorisés par des tirets
        sanitized = re.sub(r'[^a-zA-Z0-9_-]', '-', name)
        # Limiter la longueur
        return sanitized[:32]

    def _get_dscp_code_point(self, dscp: str) -> Optional[int]:
        """
        Convertit un nom DSCP en code point numérique.
        
        Args:
            dscp: Nom DSCP (ex: 'AF21', 'EF')
            
        Returns:
            Code point numérique ou None
        """
        dscp_map = {
            'AF11': 10, 'AF12': 12, 'AF13': 14,
            'AF21': 18, 'AF22': 20, 'AF23': 22,
            'AF31': 26, 'AF32': 28, 'AF33': 30,
            'AF41': 34, 'AF42': 36, 'AF43': 38,
            'EF': 46,
            'CS0': 0, 'CS1': 8, 'CS2': 16, 'CS3': 24,
            'CS4': 32, 'CS5': 40, 'CS6': 48, 'CS7': 56
        }
        return dscp_map.get(dscp.upper())

    def _execute_commands(self, device_id: int, commands: List[str], capture_output: bool = False):
        """
        Exécute une liste de commandes sur un équipement Juniper.
        
        Args:
            device_id: ID de l'équipement
            commands: Liste de commandes à exécuter
            capture_output: Si True, capture la sortie
            
        Returns:
            Tuple (success, output/message)
        """
        try:
            if self.network_connector:
                return self.network_connector.execute_commands(device_id, commands, capture_output)
            else:
                # Mode simulation pour les tests
                logger.info(f"Simulation d'exécution sur l'équipement {device_id}:")
                for cmd in commands:
                    logger.info(f"  {cmd}")
                
                if capture_output:
                    return True, "# Configuration simulée\nset class-of-service schedulers test..."
                else:
                    return True, "Commandes simulées avec succès"
                    
        except Exception as e:
            error_msg = f"Erreur lors de l'exécution des commandes Juniper: {str(e)}"
            logger.error(error_msg)
            return False, error_msg

    def _parse_juniper_qos_config(self, output: str) -> Dict[str, Any]:
        """
        Parse la sortie de configuration QoS Juniper.
        
        Args:
            output: Sortie de la commande show configuration
            
        Returns:
            Dictionnaire des politiques par interface
        """
        policies = {'interfaces': {}}
        
        try:
            lines = output.strip().split('\n')
            current_interface = None
            
            for line in lines:
                line = line.strip()
                
                # Détecter les interfaces avec scheduler-map
                if 'interfaces' in line and 'scheduler-map' in line:
                    parts = line.split()
                    for i, part in enumerate(parts):
                        if part == 'interfaces' and i + 1 < len(parts):
                            interface_part = parts[i + 1]
                            current_interface = interface_part
                            break
                    
                    if current_interface and 'scheduler-map' in line:
                        if current_interface not in policies['interfaces']:
                            policies['interfaces'][current_interface] = []
                        
                        # Extraire le nom de la scheduler map
                        scheduler_map = line.split('scheduler-map')[-1].strip()
                        policies['interfaces'][current_interface].append({
                            'type': 'scheduler-map',
                            'name': scheduler_map
                        })
                
                # Détecter les classifiers
                elif 'classifiers' in line and current_interface:
                    classifier_name = line.split('classifiers')[-1].strip()
                    policies['interfaces'][current_interface].append({
                        'type': 'classifier',
                        'name': classifier_name
                    })
                    
        except Exception as e:
            logger.error(f"Erreur lors du parsing de la configuration Juniper: {str(e)}")
        
        return policies

    def _apply_juniper_configuration(self, device_id: int, interface_name: str, policy_id: int) -> QoSConfigurationResult:
        """
        Applique une configuration QoS complète sur Juniper.
        
        Args:
            device_id: ID de l'équipement
            interface_name: Nom de l'interface
            policy_id: ID de la politique
            
        Returns:
            Résultat de la configuration
        """
        # Dans un vrai scénario, récupérer la politique et sa configuration
        # Ici, exemple de configuration basique
        sample_config = {
            'policy_name': f'Policy-{policy_id}',
            'queue_configurations': [
                # Simulation de configuration de base
            ]
        }
        
        return self.apply_juniper_scheduler_configuration(device_id, interface_name, sample_config) 