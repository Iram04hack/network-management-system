"""
Tests unitaires pour les utilitaires d'injection de dépendances.

Ces tests valident le bon fonctionnement des utilitaires d'injection
de dépendances définis dans application/di_helpers.py, notamment:
- La classe DIViewMixin pour l'injection dans les vues
- Le décorateur @inject pour l'injection automatique
- Les fonctions de résolution manuelle
- L'utilitaire de nommage d'attributs
"""
import unittest
from unittest import mock
from typing import Any, Dict, List, Optional

from common.application.di_helpers import (
    DIViewMixin, inject, resolve, _get_attribute_name, _create_lazy_property
)


# Services fictifs pour les tests
class Logger:
    def log(self, message: str) -> None:
        pass
        
class DatabaseService:
    def query(self, sql: str) -> List[Dict[str, Any]]:
        pass
        
class ConfigService:
    def get(self, key: str, default: Any = None) -> Any:
        pass
        
class IUserService:
    def get_user(self, user_id: str) -> Dict[str, Any]:
        pass


class TestGetAttributeName(unittest.TestCase):
    """Tests pour la fonction _get_attribute_name."""
    
    def test_simple_class_name(self):
        """Teste la conversion d'un nom de classe simple."""
        self.assertEqual(_get_attribute_name(Logger), "logger")
        self.assertEqual(_get_attribute_name(DatabaseService), "database_service")
        
    def test_camel_case_conversion(self):
        """Teste la conversion d'un nom en CamelCase."""
        class CamelCaseService:
            pass
            
        self.assertEqual(_get_attribute_name(CamelCaseService), "camel_case_service")
        
    def test_interface_prefix_removal(self):
        """Teste le retrait du préfixe I pour les interfaces."""
        self.assertEqual(_get_attribute_name(IUserService), "user_service")
        
    def test_single_letter_class(self):
        """Teste avec un nom de classe d'une seule lettre."""
        class A:
            pass
            
        self.assertEqual(_get_attribute_name(A), "a")


class TestDIViewMixin(unittest.TestCase):
    """
    Tests pour la classe DIViewMixin.
    
    Vérifie que les méthodes de résolution de dépendances fonctionnent
    correctement avec le conteneur global.
    """
    
    def setUp(self):
        """Configure les mocks et fixtures pour les tests."""
        # Mock du conteneur global
        self.container_mock = mock.MagicMock()
        self.container_patcher = mock.patch('common.application.di_helpers.get_container')
        self.get_container_mock = self.container_patcher.start()
        self.get_container_mock.return_value = self.container_mock
        
        # Instance de test
        self.mixin = DIViewMixin()
        
    def tearDown(self):
        """Nettoie les mocks après les tests."""
        self.container_patcher.stop()
        
    def test_resolve_single_dependency(self):
        """Teste la résolution d'une seule dépendance."""
        # Configure le mock pour retourner une instance spécifique
        logger_instance = Logger()
        self.container_mock.can_resolve.return_value = True
        self.container_mock.resolve.return_value = logger_instance
        
        # Appelle la méthode resolve
        result = self.mixin.resolve(Logger)
        
        # Vérifie que le conteneur a été appelé correctement
        self.container_mock.resolve.assert_called_once_with(Logger)
        
        # Vérifie que le résultat est correct
        self.assertIs(result, logger_instance)
        
    def test_resolve_cannot_resolve(self):
        """Teste le comportement quand une dépendance ne peut pas être résolue."""
        # Configure le mock pour indiquer que la dépendance n'est pas résolvable
        self.container_mock.can_resolve.return_value = False
        
        # Vérifie que l'exception appropriée est levée
        with self.assertRaises(ValueError) as cm:
            self.mixin.resolve(Logger)
            
        # Vérifie que l'exception contient des informations utiles
        self.assertIn("Impossible de résoudre l'interface Logger", str(cm.exception))
        
    def test_resolve_all(self):
        """Teste la résolution de plusieurs dépendances en une fois."""
        # Configure le mock pour retourner différentes instances
        logger_instance = Logger()
        db_instance = DatabaseService()
        
        def resolve_side_effect(cls):
            if cls is Logger:
                return logger_instance
            elif cls is DatabaseService:
                return db_instance
            raise ValueError("Classe inconnue")
            
        self.container_mock.resolve.side_effect = resolve_side_effect
        
        # Appelle la méthode resolve_all
        result = self.mixin.resolve_all(Logger, DatabaseService)
        
        # Vérifie que le résultat est un dictionnaire avec les bonnes clés
        self.assertEqual(len(result), 2)
        self.assertIs(result[Logger], logger_instance)
        self.assertIs(result[DatabaseService], db_instance)
        
    def test_resolve_multiple(self):
        """Teste la résolution de plusieurs dépendances avec unpacking."""
        # Configure le mock pour retourner différentes instances
        logger_instance = Logger()
        db_instance = DatabaseService()
        
        def resolve_side_effect(cls):
            if cls is Logger:
                return logger_instance
            elif cls is DatabaseService:
                return db_instance
            raise ValueError("Classe inconnue")
            
        self.container_mock.resolve.side_effect = resolve_side_effect
        
        # Appelle la méthode resolve_multiple
        result = self.mixin.resolve_multiple(Logger, DatabaseService)
        
        # Vérifie que le résultat est une liste dans le bon ordre
        self.assertEqual(len(result), 2)
        self.assertIs(result[0], logger_instance)
        self.assertIs(result[1], db_instance)
        
        # Test de l'unpacking
        logger, db = self.mixin.resolve_multiple(Logger, DatabaseService)
        self.assertIs(logger, logger_instance)
        self.assertIs(db, db_instance)


class TestInjectDecorator(unittest.TestCase):
    """
    Tests pour le décorateur @inject.
    
    Vérifie que le décorateur injecte correctement les dépendances
    dans les classes décorées.
    """
    
    def setUp(self):
        """Configure les mocks et fixtures pour les tests."""
        # Mock du conteneur global
        self.container_mock = mock.MagicMock()
        self.container_patcher = mock.patch('common.application.di_helpers.get_container')
        self.get_container_mock = self.container_patcher.start()
        self.get_container_mock.return_value = self.container_mock
        
        # Instances de test
        self.logger_instance = Logger()
        self.db_instance = DatabaseService()
        
    def tearDown(self):
        """Nettoie les mocks après les tests."""
        self.container_patcher.stop()
        
    def test_inject_single_dependency(self):
        """Teste l'injection d'une seule dépendance."""
        # Configure le mock
        self.container_mock.resolve.return_value = self.logger_instance
        
        # Classe avec décorateur
        @inject(Logger)
        class TestClass:
            def __init__(self, name):
                self.name = name
                
        # Crée une instance
        instance = TestClass("test")
        
        # Vérifie que l'attribut a bien été injecté
        self.assertEqual(instance.name, "test")  # L'initialisation originale fonctionne
        self.assertIs(instance.logger, self.logger_instance)  # L'injection a fonctionné
        
    def test_inject_multiple_dependencies(self):
        """Teste l'injection de plusieurs dépendances."""
        # Configure le mock
        def resolve_side_effect(cls):
            if cls is Logger:
                return self.logger_instance
            elif cls is DatabaseService:
                return self.db_instance
            raise ValueError("Classe inconnue")
            
        self.container_mock.resolve.side_effect = resolve_side_effect
        
        # Classe avec décorateur
        @inject(Logger, DatabaseService)
        class TestClass:
            def __init__(self):
                pass
                
        # Crée une instance
        instance = TestClass()
        
        # Vérifie que les attributs ont bien été injectés
        self.assertIs(instance.logger, self.logger_instance)
        self.assertIs(instance.database_service, self.db_instance)
        
    def test_inheritance_with_inject(self):
        """Teste l'injection sur une hiérarchie d'héritage."""
        # Configure le mock
        def resolve_side_effect(cls):
            if cls is Logger:
                return self.logger_instance
            elif cls is DatabaseService:
                return self.db_instance
            raise ValueError("Classe inconnue")
            
        self.container_mock.resolve.side_effect = resolve_side_effect
        
        # Classes avec héritage
        @inject(Logger)
        class BaseClass:
            def __init__(self):
                self.base_initialized = True
                
        @inject(DatabaseService)
        class DerivedClass(BaseClass):
            def __init__(self):
                super().__init__()
                self.derived_initialized = True
                
        # Crée une instance
        instance = DerivedClass()
        
        # Vérifie que les attributs ont bien été injectés
        self.assertTrue(instance.base_initialized)
        self.assertTrue(instance.derived_initialized)
        self.assertIs(instance.logger, self.logger_instance)
        self.assertIs(instance.database_service, self.db_instance)
        
    def test_lazy_injection(self):
        """Teste l'injection paresseuse qui ne résout les dépendances qu'à l'accès."""
        # Configure le mock
        self.container_mock.resolve.return_value = self.logger_instance
        
        # Classe avec décorateur en mode lazy
        @inject(Logger, lazy=True)
        class TestClass:
            def __init__(self):
                pass
                
        # Crée une instance
        instance = TestClass()
        
        # Vérifie que le conteneur n'a pas encore été appelé
        self.container_mock.resolve.assert_not_called()
        
        # Accède à la propriété
        logger = instance.logger
        
        # Vérifie que le conteneur a été appelé
        self.container_mock.resolve.assert_called_once_with(Logger)
        
        # Vérifie que la bonne instance a été retournée
        self.assertIs(logger, self.logger_instance)


class TestResolveFunction(unittest.TestCase):
    """
    Tests pour la fonction resolve.
    
    Vérifie que la fonction resolve permet de résoudre manuellement
    une dépendance en dehors d'une classe.
    """
    
    def setUp(self):
        """Configure les mocks et fixtures pour les tests."""
        # Mock du conteneur global
        self.container_mock = mock.MagicMock()
        self.container_patcher = mock.patch('common.application.di_helpers.get_container')
        self.get_container_mock = self.container_patcher.start()
        self.get_container_mock.return_value = self.container_mock
        
        # Instance de test
        self.logger_instance = Logger()
        
    def tearDown(self):
        """Nettoie les mocks après les tests."""
        self.container_patcher.stop()
        
    def test_resolve_function(self):
        """Teste la fonction resolve."""
        # Configure le mock
        self.container_mock.resolve.return_value = self.logger_instance
        
        # Utilise la fonction resolve
        result = resolve(Logger)
        
        # Vérifie que le conteneur a été appelé correctement
        self.container_mock.resolve.assert_called_once_with(Logger)
        
        # Vérifie que le résultat est correct
        self.assertIs(result, self.logger_instance)
        
    def test_resolve_function_error(self):
        """Teste le comportement en cas d'erreur."""
        # Configure le mock pour lever une exception
        self.container_mock.can_resolve.return_value = False
        
        # Vérifie que l'exception est correctement encapsulée
        with self.assertRaises(ValueError) as cm:
            resolve(Logger)
            
        # Vérifie que l'exception contient des informations utiles
        self.assertIn("Impossible de résoudre l'interface Logger", str(cm.exception))


if __name__ == '__main__':
    unittest.main() 