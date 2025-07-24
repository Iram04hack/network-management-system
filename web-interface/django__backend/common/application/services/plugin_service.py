"""
Service de gestion des plugins pour le module Common.
"""
import logging
import importlib
import pkgutil
from typing import List, Dict, Any
from django.apps import apps
from ...domain.interfaces.plugin import PluginInterface
from plugins.infrastructure.registry import PluginRegistry

logger = logging.getLogger(__name__)

class PluginService(PluginInterface):
    """Implémentation du service de gestion des plugins."""
    
    def discover_plugins(self) -> Dict[str, int]:
        """
        Découvre et charge tous les plugins disponibles.
        
        Returns:
            Dict avec les types de plugins et le nombre de plugins découverts par type
        """
        stats = {}
        
        # Parcourir les packages de plugins
        plugin_packages = [
            'plugins.alert_handlers',
            'plugins.dashboard_widgets',
            'plugins.report_generators'
        ]
        
        for package_name in plugin_packages:
            try:
                # Importer le package
                package = importlib.import_module(package_name)
                plugin_type = package_name.split('.')[-1]
                
                # Parcourir les modules du package
                for _, name, is_pkg in pkgutil.iter_modules(package.__path__):
                    if not is_pkg:
                        # Importer le module pour déclencher les décorateurs @register_plugin
                        importlib.import_module(f"{package_name}.{name}")
                
                # Compter les plugins enregistrés pour ce type
                plugin_count = len(PluginRegistry.get_plugins(plugin_type))
                stats[plugin_type] = plugin_count
                logger.info(f"Découverte de {plugin_count} plugins pour {plugin_type}")
            except (ImportError, ModuleNotFoundError) as e:
                logger.warning(f"Impossible d'importer le package de plugins {package_name}: {e}")
                stats[package_name] = 0
        
        return stats
    
    def get_alert_handlers(self) -> List[Any]:
        """
        Récupère tous les handlers d'alertes enregistrés.
        
        Returns:
            Liste des instances de handlers d'alertes
        """
        handler_classes = PluginRegistry.get_plugins('alert_handlers')
        handlers = []
        
        for handler_class in handler_classes:
            try:
                handler = handler_class()
                handlers.append(handler)
            except Exception as e:
                logger.error(f"Erreur lors de l'initialisation du handler d'alerte {handler_class.__name__}: {e}")
        
        return handlers
    
    def handle_alert(self, alert: Any) -> Dict[str, Any]:
        """
        Traite une alerte avec tous les handlers appropriés.
        
        Args:
            alert: Objet d'alerte (SecurityAlert ou Alert)
            
        Returns:
            Dict avec les résultats par handler
        """
        handlers = self.get_alert_handlers()
        results = {}
        
        for handler in handlers:
            if handler.can_handle(alert):
                try:
                    handler_name = handler.name if hasattr(handler, 'name') else handler.__class__.__name__
                    results[handler_name] = handler.handle_alert(alert)
                    logger.info(f"Alerte {alert.id} traitée par {handler_name}: {results[handler_name]['success']}")
                except Exception as e:
                    logger.error(f"Erreur dans le handler d'alerte {handler.__class__.__name__}: {e}")
                    results[handler.__class__.__name__] = {"success": False, "error": str(e)}
        
        return results 