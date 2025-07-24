"""
Factory pour la création de systèmes QoS complets.

Ce module fournit une fabrique qui permet de créer des systèmes QoS
intégrés avec tous les composants nécessaires pour leur fonctionnement.
"""

import logging
from typing import Dict, Any, Optional, List, Type

from ..domain.interfaces import (
    QoSConfigurationService,
    QoSMonitoringService,
    TrafficControlService,
    TrafficClassificationService
)
from ..domain.repository_interfaces import QoSPolicyRepository
from ..di_container import get_container

logger = logging.getLogger(__name__)

class QoSSystemFactory:
    """
    Fabrique pour la création de systèmes QoS complets.
    
    Cette classe permet de créer des systèmes QoS configurables
    avec différentes politiques, algorithmes et adaptateurs.
    """
    
    @staticmethod
    def create_system(config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Crée un système QoS complet basé sur la configuration fournie.
        
        Args:
            config: Configuration du système
            
        Returns:
            Dict contenant les composants du système
        """
        if config is None:
            config = {}
            
        di_container = get_container()
        
        # Obtenir les composants du système
        components = QoSSystemFactory._get_system_components(di_container, config)
        
        # Initialiser les services
        QoSSystemFactory._initialize_services(di_container, components, config)
        
        # Retourner le système
        return {
            'status': 'active',
            'configuration': config,
            'components': components,
            'version': '2.0.0'
        }
    
    @staticmethod
    def _get_system_components(di_container, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Obtient les composants du système QoS.
        
        Args:
            di_container: Conteneur d'injection de dépendances
            config: Configuration du système
            
        Returns:
            Dict contenant les composants du système
        """
        components = {
            'repositories': {
                'qos_policy': di_container.qos_policy_repository(),
                'traffic_class': di_container.traffic_class_repository(),
                'traffic_classifier': di_container.traffic_classifier_repository(),
                'interface_qos': di_container.interface_qos_repository()
            },
            'services': {
                'traffic_control': di_container.traffic_control_service(),
                'qos_configuration': di_container.qos_configuration_service(),
                'qos_monitoring': di_container.qos_monitoring_service(),
                'traffic_classification': di_container.traffic_classification_service()
            },
            'adapters': {
                # Les adaptateurs sont injectés dans les services
            },
            'use_cases': {
                'qos_policy': {
                    'get': di_container.get_qos_policy_use_case(),
                    'list': di_container.list_qos_policies_use_case(),
                    'create': di_container.create_qos_policy_use_case(),
                    'update': di_container.update_qos_policy_use_case(),
                    'delete': di_container.delete_qos_policy_use_case()
                },
                'traffic_class': {
                    'get': di_container.get_traffic_class_use_case(),
                    'list': di_container.list_traffic_classes_use_case(),
                    'create': di_container.create_traffic_class_use_case()
                },
                'traffic_classifier': {
                    'list': di_container.list_traffic_classifiers_use_case(),
                    'create': di_container.create_traffic_classifier_use_case()
                },
                'interface_qos': {
                    'apply': di_container.apply_policy_to_interface_use_case(),
                    'remove': di_container.remove_policy_from_interface_use_case(),
                    'statistics': di_container.get_qos_statistics_use_case()
                },
                'configuration': {
                    'validate_and_apply': di_container.validate_and_apply_qos_config_use_case(),
                    'configure_cbwfq': di_container.configure_cbwfq_use_case(),
                    'configure_llq': di_container.configure_llq_use_case()
                },
                'reporting': {
                    'sla_compliance': di_container.get_sla_compliance_report_use_case(),
                    'qos_performance': di_container.get_qos_performance_report_use_case(),
                    'sla_trends': di_container.analyze_sla_trends_use_case()
                }
            }
        }
        
        return components
    
    @staticmethod
    def _initialize_services(
        di_container,
        components: Dict[str, Any],
        config: Dict[str, Any]
    ) -> None:
        """
        Initialise les services du système QoS.
        
        Args:
            di_container: Conteneur d'injection de dépendances
            components: Composants du système
            config: Configuration du système
        """
        # Configuration des services
        if 'services' in config:
            if 'qos_monitoring' in config['services']:
                monitoring_config = config['services']['qos_monitoring']
                monitoring_service = components['services']['qos_monitoring']
                monitoring_service.configure(monitoring_config)
                
            if 'traffic_classification' in config['services']:
                classification_config = config['services']['traffic_classification']
                classification_service = components['services']['traffic_classification']
                classification_service.configure(classification_config)
                
            if 'qos_configuration' in config['services']:
                configuration_config = config['services']['qos_configuration']
                configuration_service = components['services']['qos_configuration']
                configuration_service.configure(configuration_config)
                
        # Initialisation des adaptateurs spécifiques aux vendeurs
        if 'adapters' in config:
            vendor_adapters = config.get('adapters', {}).get('supported_vendors', [])
            QoSSystemFactory._configure_vendor_adapters(
                components['services']['qos_configuration'],
                vendor_adapters
            )
            
        # Initialisation des adaptateurs SDN
        if 'adapters' in config and 'supported_controllers' in config['adapters']:
            sdn_controllers = config['adapters']['supported_controllers']
            # S'assurer que les adaptateurs SDN sont disponibles
            try:
                from ..infrastructure.sdn_integration_service import SDNIntegrationService
                sdn_service = SDNIntegrationService()
                sdn_service.initialize_controllers(sdn_controllers)
                logger.info(f"SDN Integration Service initialisé avec les contrôleurs: {sdn_controllers}")
            except ImportError:
                logger.warning("SDN Integration Service non disponible")
    
    @staticmethod
    def _configure_vendor_adapters(
        qos_configuration_service: QoSConfigurationService,
        vendor_adapters: List[str]
    ) -> None:
        """
        Configure les adaptateurs spécifiques aux vendeurs.
        
        Args:
            qos_configuration_service: Service de configuration QoS
            vendor_adapters: Liste des adaptateurs à configurer
        """
        for vendor in vendor_adapters:
            try:
                qos_configuration_service.register_vendor_adapter(vendor)
                logger.info(f"Adaptateur QoS pour {vendor} configuré avec succès")
            except Exception as e:
                logger.error(f"Erreur lors de la configuration de l'adaptateur {vendor}: {e}") 