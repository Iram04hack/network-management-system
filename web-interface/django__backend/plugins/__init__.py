"""
Module plugins.

Ce module fournit un système de plugins extensible pour le système NMS.
"""

from .domain.interfaces import (
    BasePlugin,
    PluginMetadata,
    PluginRegistry as PluginRegistryInterface,
    DependencyResolver,
    AlertHandlerPlugin,
    DashboardWidgetPlugin,
    ReportGeneratorPlugin,
    PluginManager
)

from .infrastructure.dependency_resolver import PluginDependencyResolver
from .infrastructure.registry import PluginRegistry, register_plugin

__all__ = [
    # Interfaces du domaine
    'BasePlugin',
    'PluginMetadata',
    'PluginRegistryInterface',
    'DependencyResolver',
    'AlertHandlerPlugin',
    'DashboardWidgetPlugin',
    'ReportGeneratorPlugin',
    'PluginManager',
    
    # Implémentations de l'infrastructure
    'PluginDependencyResolver',
    'PluginRegistry',
    'register_plugin',
]
