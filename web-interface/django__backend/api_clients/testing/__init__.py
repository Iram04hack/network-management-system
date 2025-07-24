"""
Module de testing pour api_clients.
Contient tous les outils et utilitaires pour les tests et l'environnement de test.

Structure:
- environment_manager.py: Gestionnaire d'environnement de tests
- coverage_runner.py: Gestionnaire de couverture de tests
- test_config.py: Configuration pour les tests
- docker_manager.py: Gestionnaire des services Docker de test
"""

from .environment_manager import TestEnvironmentManager
from .coverage_runner import CoverageTestRunner
from .test_config import TestConfig

__all__ = [
    'TestEnvironmentManager',
    'CoverageTestRunner', 
    'TestConfig'
]
