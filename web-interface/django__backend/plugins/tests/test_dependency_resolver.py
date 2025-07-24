"""
Tests pour le résolveur de dépendances des plugins.
"""
import pytest
from unittest.mock import Mock, MagicMock
from ..infrastructure.dependency_resolver import (
    PluginDependencyResolver,
    CircularDependencyError,
    MissingDependencyError
)


class TestPluginDependencyResolver:
    """Tests pour le résolveur de dépendances des plugins."""
    
    def setup_method(self):
        """Configuration des tests."""
        self.resolver = PluginDependencyResolver()
    
    def create_mock_plugin(self, plugin_id, dependencies=None):
        """Crée un mock de plugin avec des métadonnées."""
        if dependencies is None:
            dependencies = []
        
        plugin = Mock()
        metadata = MagicMock()
        metadata.id = plugin_id
        metadata.dependencies = dependencies
        plugin.get_metadata.return_value = metadata
        
        return plugin
    
    def test_resolve_dependencies_no_dependencies(self):
        """Test de résolution sans dépendances."""
        plugin1 = self.create_mock_plugin("plugin1")
        plugin2 = self.create_mock_plugin("plugin2")
        plugins = [plugin1, plugin2]
        
        sorted_plugins = self.resolver.resolve_dependencies(plugins)
        
        # Les deux plugins devraient être dans la liste
        assert len(sorted_plugins) == 2
        assert plugin1 in sorted_plugins
        assert plugin2 in sorted_plugins
    
    def test_resolve_dependencies_with_dependencies(self):
        """Test de résolution avec dépendances."""
        plugin1 = self.create_mock_plugin("plugin1")
        plugin2 = self.create_mock_plugin("plugin2", ["plugin1"])
        plugin3 = self.create_mock_plugin("plugin3", ["plugin2"])
        plugins = [plugin3, plugin1, plugin2]  # Ordre mélangé
        
        sorted_plugins = self.resolver.resolve_dependencies(plugins)
        
        # L'ordre doit respecter les dépendances
        assert len(sorted_plugins) == 3
        assert sorted_plugins.index(plugin1) < sorted_plugins.index(plugin2)
        assert sorted_plugins.index(plugin2) < sorted_plugins.index(plugin3)
    
    def test_circular_dependency(self):
        """Test de détection de dépendances circulaires."""
        plugin1 = self.create_mock_plugin("plugin1", ["plugin3"])
        plugin2 = self.create_mock_plugin("plugin2", ["plugin1"])
        plugin3 = self.create_mock_plugin("plugin3", ["plugin2"])
        plugins = [plugin1, plugin2, plugin3]
        
        with pytest.raises(CircularDependencyError):
            self.resolver.resolve_dependencies(plugins)
    
    def test_missing_dependency(self):
        """Test de détection de dépendances manquantes."""
        plugin1 = self.create_mock_plugin("plugin1")
        plugin2 = self.create_mock_plugin("plugin2", ["plugin3"])  # plugin3 n'existe pas
        plugins = [plugin1, plugin2]
        
        with pytest.raises(MissingDependencyError):
            self.resolver.resolve_dependencies(plugins)
    
    def test_get_dependent_plugins(self):
        """Test de récupération des plugins dépendants."""
        plugin1 = self.create_mock_plugin("plugin1")
        plugin2 = self.create_mock_plugin("plugin2", ["plugin1"])
        plugin3 = self.create_mock_plugin("plugin3", ["plugin1"])
        plugin4 = self.create_mock_plugin("plugin4", ["plugin2"])
        plugins = [plugin1, plugin2, plugin3, plugin4]
        
        # Plugins qui dépendent de plugin1
        dependents = self.resolver.get_dependent_plugins("plugin1", plugins)
        assert len(dependents) == 2
        assert plugin2 in dependents
        assert plugin3 in dependents
        assert plugin4 not in dependents
    
    def test_fallback_order(self):
        """Test de l'ordre de secours en cas d'erreur."""
        plugin1 = self.create_mock_plugin("plugin1", ["plugin4"])  # Dépendance manquante
        plugin2 = self.create_mock_plugin("plugin2", ["plugin1", "plugin3"])
        plugin3 = self.create_mock_plugin("plugin3")
        plugins = [plugin1, plugin2, plugin3]
        
        # Utiliser la méthode publique qui gère les erreurs
        sorted_plugins = self.resolver.get_plugin_order(plugins)
        
        # L'ordre devrait être par nombre croissant de dépendances
        assert len(sorted_plugins) == 3
        assert sorted_plugins[0] == plugin3  # 0 dépendance
        assert sorted_plugins[1] == plugin1  # 1 dépendance
        assert sorted_plugins[2] == plugin2  # 2 dépendances 