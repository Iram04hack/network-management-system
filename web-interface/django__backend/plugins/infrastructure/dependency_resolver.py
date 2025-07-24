"""
Implémentation du résolveur de dépendances pour les plugins.

Ce module contient l'implémentation concrète de l'interface DependencyResolver
pour gérer les dépendances entre plugins.
"""

from typing import Dict, Any, List, Set, Optional, Tuple
from collections import defaultdict
import logging

from ..domain.interfaces import BasePlugin, DependencyResolver

logger = logging.getLogger(__name__)


class CircularDependencyError(Exception):
    """Exception levée lorsqu'une dépendance circulaire est détectée."""
    pass


class MissingDependencyError(Exception):
    """Exception levée lorsqu'une dépendance est manquante."""
    pass


class PluginDependencyResolver(DependencyResolver):
    """
    Implémentation du résolveur de dépendances pour les plugins.
    
    Cette classe implémente l'algorithme de tri topologique pour résoudre
    les dépendances entre plugins.
    """
    
    def resolve_dependencies(self, plugins: List[BasePlugin]) -> List[BasePlugin]:
        """
        Résout les dépendances entre plugins et retourne une liste
        des plugins triés selon l'ordre de dépendance.
        
        Args:
            plugins: Liste des plugins à trier
            
        Returns:
            Liste des plugins triés selon l'ordre de dépendance
            
        Raises:
            CircularDependencyError: Si des dépendances circulaires sont détectées
            MissingDependencyError: Si des dépendances sont manquantes
        """
        # Vérifier les dépendances manquantes
        missing_dependencies = self._check_missing_dependencies(plugins)
        if missing_dependencies:
            raise MissingDependencyError(
                f"Dépendances manquantes: {', '.join(missing_dependencies)}"
            )
        
        # Construire le graphe de dépendances
        dependency_graph = self._build_dependency_graph(plugins)
        
        # Trier topologiquement les plugins
        sorted_plugins = []
        visited = set()
        temp_visited = set()
        
        # Fonction récursive pour le tri topologique
        def visit(plugin_id: str):
            if plugin_id in temp_visited:
                raise CircularDependencyError(
                    f"Dépendance circulaire détectée: {plugin_id}"
                )
            
            if plugin_id not in visited:
                temp_visited.add(plugin_id)
                
                # Visiter les dépendances de ce plugin
                for dependency_id in dependency_graph[plugin_id]["dependencies"]:
                    visit(dependency_id)
                
                temp_visited.remove(plugin_id)
                visited.add(plugin_id)
                
                # Ajouter le plugin à la liste triée
                if plugin_id in dependency_graph:
                    sorted_plugins.append(dependency_graph[plugin_id]["plugin"])
        
        # Visiter tous les plugins
        for plugin in plugins:
            plugin_id = plugin.get_metadata().id
            if plugin_id not in visited:
                visit(plugin_id)
        
        return sorted_plugins
    
    def check_dependencies(self, plugin: BasePlugin, available_plugins: List[BasePlugin]) -> List[str]:
        """
        Vérifie que toutes les dépendances d'un plugin sont satisfaites.
        
        Args:
            plugin: Plugin à vérifier
            available_plugins: Liste des plugins disponibles
            
        Returns:
            Liste des dépendances manquantes (vide si toutes les dépendances sont satisfaites)
        """
        plugin_metadata = plugin.get_metadata()
        dependencies = plugin_metadata.dependencies
        
        # Collecter les IDs des plugins disponibles
        available_plugin_ids = {p.get_metadata().id for p in available_plugins}
        
        # Vérifier les dépendances
        missing_dependencies = [
            dep_id for dep_id in dependencies
            if dep_id not in available_plugin_ids
        ]
        
        return missing_dependencies
    
    def get_dependent_plugins(self, plugin_id: str, all_plugins: List[BasePlugin]) -> List[BasePlugin]:
        """
        Récupère tous les plugins qui dépendent directement d'un plugin donné.
        
        Args:
            plugin_id: ID du plugin dont on veut connaître les dépendants
            all_plugins: Liste de tous les plugins disponibles
            
        Returns:
            Liste des plugins qui dépendent directement du plugin spécifié
        """
        dependent_plugins = []
        
        for plugin in all_plugins:
            metadata = plugin.get_metadata()
            if plugin_id in metadata.dependencies:
                dependent_plugins.append(plugin)
        
        return dependent_plugins
    
    def _check_missing_dependencies(self, plugins: List[BasePlugin]) -> List[str]:
        """
        Vérifie si des dépendances sont manquantes dans la liste de plugins.
        
        Args:
            plugins: Liste des plugins à vérifier
            
        Returns:
            Liste des dépendances manquantes
        """
        # Collecter tous les IDs de plugins disponibles
        available_plugin_ids = {plugin.get_metadata().id for plugin in plugins}
        
        # Collecter toutes les dépendances déclarées
        all_dependencies = set()
        for plugin in plugins:
            all_dependencies.update(plugin.get_metadata().dependencies)
        
        # Vérifier les dépendances manquantes
        missing_dependencies = all_dependencies - available_plugin_ids
        
        return list(missing_dependencies)
    
    def _build_dependency_graph(self, plugins: List[BasePlugin]) -> Dict[str, Dict[str, Any]]:
        """
        Construit un graphe de dépendances pour les plugins.
        
        Args:
            plugins: Liste des plugins
            
        Returns:
            Graphe de dépendances
        """
        dependency_graph = {}
        
        for plugin in plugins:
            plugin_id = plugin.get_metadata().id
            dependencies = plugin.get_metadata().dependencies
            
            dependency_graph[plugin_id] = {
                "plugin": plugin,
                "dependencies": dependencies
            }
        
        return dependency_graph
    
    def get_plugin_order(self, plugins: List[BasePlugin]) -> List[BasePlugin]:
        """
        Détermine l'ordre optimal de chargement des plugins.
        
        Args:
            plugins: Liste des plugins à trier
            
        Returns:
            Liste des plugins triés selon l'ordre optimal de chargement
        """
        try:
            return self.resolve_dependencies(plugins)
        except (CircularDependencyError, MissingDependencyError) as e:
            logger.error(f"Erreur lors de la résolution des dépendances: {e}")
            
            # En cas d'erreur, renvoyer les plugins sans dépendances d'abord
            return self._get_fallback_order(plugins)
    
    def _get_fallback_order(self, plugins: List[BasePlugin]) -> List[BasePlugin]:
        """
        Obtient un ordre de chargement de secours en cas d'erreur.
        
        Args:
            plugins: Liste des plugins à trier
            
        Returns:
            Liste des plugins triés selon un ordre simpliste
        """
        # Trier les plugins par nombre de dépendances
        return sorted(
            plugins,
            key=lambda p: len(p.get_metadata().dependencies)
        ) 