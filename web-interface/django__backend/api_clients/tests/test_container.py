"""
Tests pour la classe APIClientContainer.

Ce module contient les tests pour la classe APIClientContainer.
"""

import unittest
from unittest.mock import patch, MagicMock

from api_clients.container import APIClientContainer


class APIClientContainerTests(unittest.TestCase):
    """
    Tests pour la classe APIClientContainer.
    """
    
    def setUp(self):
        """
        Configuration initiale pour les tests.
        """
        self.container = APIClientContainer()
    
    def test_get_client(self):
        """
        Teste la récupération d'un client.
        """
        # Test avec un client existant
        example_client = self.container.get_client('example')
        self.assertIsNotNone(example_client)
        self.assertEqual(example_client.__class__.__name__, 'ExampleAPIClient')
        
        # Test avec un client non existant
        nonexistent_client = self.container.get_client('nonexistent')
        self.assertIsNone(nonexistent_client)
    
    def test_get_all_clients(self):
        """
        Teste la récupération de tous les clients.
        """
        clients = self.container.get_all_clients()
        self.assertIsNotNone(clients)
        self.assertIsInstance(clients, dict)
        self.assertIn('example', clients)
        self.assertIn('network', clients)
        self.assertEqual(clients['example'].__class__.__name__, 'ExampleAPIClient')
        self.assertEqual(clients['network'].__class__.__name__, 'NetworkAPIClient')
