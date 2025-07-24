"""
Container d'injection de dépendances pour le module network_management.

Ce module fournit un conteneur d'injection de dépendances pour
le module network_management, permettant de gérer les dépendances
entre les différentes couches de l'architecture hexagonale.
"""

import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# Conteneur global
_container: Dict[str, Any] = {}


def init_container() -> None:
    """
    Initialise le conteneur d'injection de dépendances.
    
    Cette fonction est appelée au démarrage de l'application pour
    configurer toutes les dépendances nécessaires au module.
    """
    global _container
    
    try:
        # Importation des adaptateurs (repositories implémentant les ports de sortie)
        from .infrastructure.adapters import (
            DjangoDeviceRepository,
            DjangoInterfaceRepository,
            PySnmpClientAdapter
        )
        
        # Importation des use cases
        from .application.use_cases import (
            NetworkDeviceUseCasesImpl,
            NetworkInterfaceUseCasesImpl,
        )
        
        # Configuration des adaptateurs
        snmp_client = PySnmpClientAdapter()
        
        # Configuration des repositories
        device_repository = DjangoDeviceRepository()
        interface_repository = DjangoInterfaceRepository()
        
        # Configuration des use cases
        device_use_cases = NetworkDeviceUseCasesImpl(device_repository)
        interface_use_cases = NetworkInterfaceUseCasesImpl(interface_repository)
        
        # Enregistrement dans le conteneur
        _container["snmp_client"] = snmp_client
        _container["device_repository"] = device_repository
        _container["interface_repository"] = interface_repository
        _container["device_use_cases"] = device_use_cases
        _container["interface_use_cases"] = interface_use_cases
        
        logger.info("Conteneur DI network_management initialisé avec succès")
    except Exception as e:
        logger.error(f"❌ ERREUR CRITIQUE: Échec initialisation DI container network_management: {str(e)}")
        raise


def get_container() -> Dict[str, Any]:
    """
    Récupère le conteneur d'injection de dépendances.
    
    Returns:
        Dict[str, Any]: Le conteneur d'injection de dépendances.
    """
    return _container


def get(key: str) -> Optional[Any]:
    """
    Récupère une dépendance du conteneur par sa clé.
    
    Args:
        key (str): La clé de la dépendance à récupérer.
        
    Returns:
        Any: La dépendance demandée, ou None si elle n'existe pas.
    """
    return _container.get(key)
