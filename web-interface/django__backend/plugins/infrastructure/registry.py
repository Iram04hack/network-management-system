"""
Registre central pour les plugins du système.

Ce module contient l'implémentation du registre de plugins et du
décorateur pour l'enregistrement des plugins.
"""
from typing import Dict, Any, List, Type

class PluginRegistry:
    """Registre central pour les plugins du système"""
    _plugins: Dict[str, List[Any]] = {}
    
    @classmethod
    def register(cls, plugin_type: str, plugin_class: Any) -> Any:
        """
        Enregistre un plugin dans le registre.
        
        Args:
            plugin_type: Type de plugin (ex: 'alert_handlers', 'dashboard_widgets')
            plugin_class: Classe du plugin
            
        Returns:
            La classe du plugin (pour permettre l'utilisation comme décorateur)
        """
        if plugin_type not in cls._plugins:
            cls._plugins[plugin_type] = []
        
        cls._plugins[plugin_type].append(plugin_class)
        return plugin_class
    
    @classmethod
    def get_plugins(cls, plugin_type: str) -> List[Any]:
        """
        Récupère tous les plugins d'un type.
        
        Args:
            plugin_type: Type de plugin
            
        Returns:
            Liste des plugins enregistrés pour ce type
        """
        return cls._plugins.get(plugin_type, [])
    
    @classmethod
    def get_plugin(cls, plugin_type: str, plugin_name: str) -> Any:
        """
        Récupère un plugin spécifique par son nom.
        
        Args:
            plugin_type: Type de plugin
            plugin_name: Nom du plugin
            
        Returns:
            Plugin correspondant ou None
        """
        plugins = cls.get_plugins(plugin_type)
        for plugin in plugins:
            if hasattr(plugin, 'name') and plugin.name == plugin_name:
                return plugin
        return None


# Décorateur pour enregistrer un plugin
def register_plugin(plugin_type: str):
    """
    Décorateur pour enregistrer un plugin dans le système.
    
    Args:
        plugin_type: Type de plugin
    
    Returns:
        Décorateur qui enregistre la classe comme plugin
    
    Examples:
        ```python
        @register_plugin('alert_handlers')
        class MyAlertHandler(AlertHandlerPlugin):
            name = "my_handler"
            # ...
        ```
    """
    def decorator(plugin_class: Type) -> Type:
        return PluginRegistry.register(plugin_type, plugin_class)
    return decorator 