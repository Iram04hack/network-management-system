"""
Conteneur d'injection de dépendances pour le module api_views.

Ce module fournit un système d'injection de dépendances simple
pour découpler les composants du module api_views.
"""

from typing import Dict, Type, Any, Callable
import logging

logger = logging.getLogger(__name__)


class DIContainer:
    """
    Conteneur d'injection de dépendances simple.
    
    Permet d'enregistrer et de résoudre des dépendances
    pour les vues et les cas d'usage.
    """
    
    def __init__(self):
        self._services: Dict[str, Any] = {}
        self._factories: Dict[str, Callable] = {}
        self._singletons: Dict[str, Any] = {}
    
    def register(self, name: str, service: Any) -> None:
        """Enregistre un service par nom."""
        self._services[name] = service
        logger.debug(f"Service '{name}' enregistré")
    
    def register_factory(self, name: str, factory: Callable) -> None:
        """Enregistre une factory pour créer un service."""
        self._factories[name] = factory
        logger.debug(f"Factory '{name}' enregistrée")
    
    def register_singleton(self, name: str, factory: Callable) -> None:
        """Enregistre un singleton (instance unique)."""
        self._factories[name] = factory
        logger.debug(f"Singleton '{name}' enregistré")
    
    def get(self, name: str) -> Any:
        """Résout et retourne un service par nom."""
        # Vérifier d'abord les singletons
        if name in self._singletons:
            return self._singletons[name]
        
        # Vérifier les services directs
        if name in self._services:
            return self._services[name]
        
        # Vérifier les factories
        if name in self._factories:
            instance = self._factories[name]()
            # Si c'est un singleton, le stocker
            if name in self._singletons:
                self._singletons[name] = instance
            return instance
        
        raise ValueError(f"Service '{name}' non trouvé dans le conteneur DI")
    
    def has(self, name: str) -> bool:
        """Vérifie si un service est enregistré."""
        return (name in self._services or 
                name in self._factories or 
                name in self._singletons)
    
    def clear(self) -> None:
        """Vide le conteneur."""
        self._services.clear()
        self._factories.clear()
        self._singletons.clear()
        logger.debug("Conteneur DI vidé")


# Instance globale du conteneur
_container = DIContainer()


def get_container() -> DIContainer:
    """Retourne l'instance globale du conteneur DI."""
    return _container


def register_service(name: str, service: Any) -> None:
    """Raccourci pour enregistrer un service."""
    _container.register(name, service)


def register_factory(name: str, factory: Callable) -> None:
    """Raccourci pour enregistrer une factory."""
    _container.register_factory(name, factory)


def register_singleton(name: str, factory: Callable) -> None:
    """Raccourci pour enregistrer un singleton."""
    _container.register_singleton(name, factory)


def resolve(name: str) -> Any:
    """Raccourci pour résoudre un service."""
    return _container.get(name)


def configure_default_services():
    """Configure les services par défaut du module api_views."""
    try:
        # Enregistrer les cas d'usage
        from api_views.application.use_cases import (
            GetDashboardDataUseCase,
            SaveDashboardConfigurationUseCase,
            SearchResourcesUseCase,
            GetResourceDetailsUseCase
        )
        
        register_factory('dashboard_use_case', GetDashboardDataUseCase)
        register_factory('save_dashboard_use_case', SaveDashboardConfigurationUseCase)
        register_factory('search_use_case', SearchResourcesUseCase)
        register_factory('details_use_case', GetResourceDetailsUseCase)
        
        logger.info("Services par défaut configurés dans le conteneur DI")
        
    except ImportError as e:
        logger.warning(f"Impossible de configurer certains services: {e}")


# Configuration automatique au chargement du module
configure_default_services()
