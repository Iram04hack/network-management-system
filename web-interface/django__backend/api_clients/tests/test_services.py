"""
Tests des services métier du module api_clients.
Remplace et consolide : test_base_client_complete.py, test_circuit_breaker.py, 
test_retry_handler.py, test_response_cache.py
"""

import unittest
from unittest.mock import patch, MagicMock, Mock
from django.test import TestCase
import time
import json
from datetime import datetime, timezone, timedelta

from ..infrastructure.circuit_breaker import CircuitBreaker
from ..infrastructure.retry_handler import RetryHandler
from ..infrastructure.response_cache import ResponseCache
from ..infrastructure.base_client import BaseClient


class CircuitBreakerTest(TestCase):
    """Tests pour le Circuit Breaker."""
    
    def setUp(self):
        """Configuration pour les tests."""
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=3,
            recovery_timeout=5,
            expected_exception=Exception
        )
    
    def test_circuit_breaker_closed_state(self):
        """Test du circuit breaker en état fermé (normal)."""
        # Fonction qui réussit
        def successful_function():
            return "success"
        
        # Exécuter plusieurs fois avec succès
        for _ in range(5):
            result = self.circuit_breaker.call(successful_function)
            self.assertEqual(result, "success")
        
        # Vérifier l'état du circuit
        self.assertEqual(self.circuit_breaker.state, "closed")
        self.assertEqual(self.circuit_breaker.failure_count, 0)
    
    def test_circuit_breaker_open_state(self):
        """Test du circuit breaker en état ouvert (échecs)."""
        # Fonction qui échoue
        def failing_function():
            raise Exception("Service unavailable")
        
        # Exécuter jusqu'à atteindre le seuil d'échec
        for i in range(3):
            with self.assertRaises(Exception):
                self.circuit_breaker.call(failing_function)
        
        # Le circuit doit maintenant être ouvert
        self.assertEqual(self.circuit_breaker.state, "open")
        self.assertEqual(self.circuit_breaker.failure_count, 3)
        
        # Les appels suivants doivent être bloqués
        with self.assertRaises(Exception) as context:
            self.circuit_breaker.call(failing_function)
        
        self.assertIn("Circuit breaker is open", str(context.exception))
    
    def test_circuit_breaker_half_open_state(self):
        """Test du circuit breaker en état semi-ouvert (récupération)."""
        # Fonction qui échoue initialement puis réussit
        self.call_count = 0
        
        def recovering_function():
            self.call_count += 1
            if self.call_count <= 3:
                raise Exception("Still failing")
            return "recovered"
        
        # Faire échouer le circuit
        for i in range(3):
            with self.assertRaises(Exception):
                self.circuit_breaker.call(recovering_function)
        
        # Simuler l'expiration du timeout
        self.circuit_breaker.last_failure_time = time.time() - 10
        
        # Maintenant la fonction réussit
        result = self.circuit_breaker.call(lambda: "success")
        self.assertEqual(result, "success")
        self.assertEqual(self.circuit_breaker.state, "closed")
    
    def test_circuit_breaker_with_different_exceptions(self):
        """Test du circuit breaker avec différents types d'exceptions."""
        # Circuit breaker spécifique pour ConnectionError
        cb = CircuitBreaker(
            failure_threshold=2,
            recovery_timeout=5,
            expected_exception=ConnectionError
        )
        
        # ConnectionError doit déclencher le circuit breaker
        def connection_error_func():
            raise ConnectionError("Network unreachable")
        
        for _ in range(2):
            with self.assertRaises(ConnectionError):
                cb.call(connection_error_func)
        
        self.assertEqual(cb.state, "open")
        
        # Autres exceptions ne déclenchent pas le circuit breaker
        def other_error_func():
            raise ValueError("Invalid value")
        
        with self.assertRaises(ValueError):
            cb.call(other_error_func)
        
        # L'état ne change pas
        self.assertEqual(cb.state, "open")


class RetryHandlerTest(TestCase):
    """Tests pour le gestionnaire de retry."""
    
    def setUp(self):
        """Configuration pour les tests."""
        self.retry_handler = RetryHandler(
            max_attempts=3,
            backoff_factor=1,
            retry_exceptions=(ConnectionError, TimeoutError)
        )
    
    def test_retry_handler_success_first_attempt(self):
        """Test de succès au premier essai."""
        def successful_function():
            return "success"
        
        result = self.retry_handler.execute(successful_function)
        self.assertEqual(result, "success")
    
    def test_retry_handler_success_after_retries(self):
        """Test de succès après plusieurs tentatives."""
        self.attempt_count = 0
        
        def retry_then_success():
            self.attempt_count += 1
            if self.attempt_count < 3:
                raise ConnectionError("Temporary failure")
            return "success after retries"
        
        result = self.retry_handler.execute(retry_then_success)
        self.assertEqual(result, "success after retries")
        self.assertEqual(self.attempt_count, 3)
    
    def test_retry_handler_max_attempts_exceeded(self):
        """Test d'échec après épuisement des tentatives."""
        def always_failing_function():
            raise ConnectionError("Always fails")
        
        with self.assertRaises(ConnectionError):
            self.retry_handler.execute(always_failing_function)
    
    def test_retry_handler_non_retryable_exception(self):
        """Test avec une exception non-retryable."""
        def value_error_function():
            raise ValueError("Invalid input")
        
        # ValueError n'est pas dans retry_exceptions, donc pas de retry
        with self.assertRaises(ValueError):
            self.retry_handler.execute(value_error_function)
    
    @patch('time.sleep')
    def test_retry_handler_backoff(self, mock_sleep):
        """Test du backoff exponentiel."""
        self.attempt_count = 0
        
        def failing_function():
            self.attempt_count += 1
            raise TimeoutError("Timeout")
        
        with self.assertRaises(TimeoutError):
            self.retry_handler.execute(failing_function)
        
        # Vérifier les appels de sleep (backoff)
        expected_calls = [
            unittest.mock.call(1),  # Premier retry: 1 seconde
            unittest.mock.call(2),  # Deuxième retry: 2 secondes
        ]
        mock_sleep.assert_has_calls(expected_calls)


class ResponseCacheTest(TestCase):
    """Tests pour le cache de réponses."""
    
    def setUp(self):
        """Configuration pour les tests."""
        self.cache = ResponseCache(
            default_ttl=300,  # 5 minutes
            max_size=1000
        )
    
    def test_cache_set_and_get(self):
        """Test de stockage et récupération du cache."""
        key = "test_key"
        value = {"data": "test_value", "timestamp": time.time()}
        
        # Stocker dans le cache
        self.cache.set(key, value)
        
        # Récupérer du cache
        cached_value = self.cache.get(key)
        self.assertEqual(cached_value, value)
    
    def test_cache_expiration(self):
        """Test de l'expiration du cache."""
        key = "expiring_key"
        value = {"data": "will_expire"}
        
        # Stocker avec un TTL court
        self.cache.set(key, value, ttl=0.1)  # 0.1 seconde
        
        # Immédiatement disponible
        self.assertEqual(self.cache.get(key), value)
        
        # Attendre l'expiration
        time.sleep(0.2)
        
        # Doit être expiré
        self.assertIsNone(self.cache.get(key))
    
    def test_cache_delete(self):
        """Test de suppression du cache."""
        key = "delete_key"
        value = {"data": "to_delete"}
        
        # Stocker et vérifier
        self.cache.set(key, value)
        self.assertEqual(self.cache.get(key), value)
        
        # Supprimer
        self.cache.delete(key)
        
        # Ne doit plus être disponible
        self.assertIsNone(self.cache.get(key))
    
    def test_cache_clear(self):
        """Test de vidage complet du cache."""
        # Stocker plusieurs éléments
        for i in range(5):
            self.cache.set(f"key_{i}", {"data": f"value_{i}"})
        
        # Vérifier qu'ils sont stockés
        for i in range(5):
            self.assertIsNotNone(self.cache.get(f"key_{i}"))
        
        # Vider le cache
        self.cache.clear()
        
        # Vérifier que tout est supprimé
        for i in range(5):
            self.assertIsNone(self.cache.get(f"key_{i}"))
    
    def test_cache_size_limit(self):
        """Test de la limite de taille du cache."""
        # Cache avec taille limitée
        small_cache = ResponseCache(max_size=3)
        
        # Ajouter plus d'éléments que la limite
        for i in range(5):
            small_cache.set(f"key_{i}", {"data": f"value_{i}"})
        
        # Vérifier que seuls les derniers éléments sont conservés
        # (stratégie LRU - Least Recently Used)
        self.assertIsNone(small_cache.get("key_0"))
        self.assertIsNone(small_cache.get("key_1"))
        self.assertIsNotNone(small_cache.get("key_2"))
        self.assertIsNotNone(small_cache.get("key_3"))
        self.assertIsNotNone(small_cache.get("key_4"))
    
    def test_cache_with_custom_key_generator(self):
        """Test du cache avec générateur de clés personnalisé."""
        def custom_key_generator(method, url, params=None):
            key_parts = [method, url]
            if params:
                key_parts.append(json.dumps(params, sort_keys=True))
            return ":".join(key_parts)
        
        cache = ResponseCache(key_generator=custom_key_generator)
        
        # Test avec différents paramètres
        key1 = cache.generate_key("GET", "/api/test", {"param1": "value1"})
        key2 = cache.generate_key("GET", "/api/test", {"param1": "value2"})
        key3 = cache.generate_key("GET", "/api/test", {"param1": "value1"})
        
        # Les clés doivent être différentes pour des paramètres différents
        self.assertNotEqual(key1, key2)
        # Mais identiques pour les mêmes paramètres
        self.assertEqual(key1, key3)


class BaseClientTest(TestCase):
    """Tests pour le client de base."""
    
    def setUp(self):
        """Configuration pour les tests."""
        self.base_client = BaseClient(
            base_url="http://localhost:8080",
            timeout=30,
            use_circuit_breaker=True,
            use_retry=True,
            use_cache=True
        )
    
    @patch('requests.Session.get')
    def test_base_client_get_request(self, mock_get):
        """Test de requête GET de base."""
        # Configuration du mock
        mock_response = Mock()
        mock_response.json.return_value = {"status": "success", "data": {}}
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        # Exécuter la requête
        result = self.base_client.get("/api/test")
        
        # Vérifications
        self.assertEqual(result["status"], "success")
        mock_get.assert_called_once()
    
    @patch('requests.Session.post')
    def test_base_client_post_request(self, mock_post):
        """Test de requête POST de base."""
        # Configuration du mock
        mock_response = Mock()
        mock_response.json.return_value = {"id": 123, "created": True}
        mock_response.status_code = 201
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        # Données à envoyer
        data = {"name": "Test Item", "value": 42}
        
        # Exécuter la requête
        result = self.base_client.post("/api/items", data=data)
        
        # Vérifications
        self.assertEqual(result["id"], 123)
        self.assertTrue(result["created"])
        mock_post.assert_called_once()
    
    @patch('requests.Session.get')
    def test_base_client_with_cache(self, mock_get):
        """Test du client avec cache activé."""
        # Configuration du mock
        mock_response = Mock()
        mock_response.json.return_value = {"cached": "data"}
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        # Premier appel
        result1 = self.base_client.get("/api/cached", use_cache=True)
        
        # Deuxième appel (doit utiliser le cache)
        result2 = self.base_client.get("/api/cached", use_cache=True)
        
        # Vérifications
        self.assertEqual(result1, result2)
        # La requête HTTP ne doit être faite qu'une seule fois
        mock_get.assert_called_once()
    
    @patch('requests.Session.get')
    def test_base_client_error_handling(self, mock_get):
        """Test de gestion d'erreurs du client de base."""
        # Simuler une erreur HTTP
        mock_get.side_effect = ConnectionError("Network unreachable")
        
        # Le client doit gérer l'erreur gracieusement
        result = self.base_client.get("/api/unreachable")
        
        # Vérifier que l'erreur est encapsulée
        self.assertFalse(result.get('success', True))
        self.assertIn('error', result)
    
    def test_base_client_url_building(self):
        """Test de construction d'URLs."""
        # Test avec chemin simple
        url1 = self.base_client._build_url("/api/test")
        self.assertEqual(url1, "http://localhost:8080/api/test")
        
        # Test avec paramètres
        url2 = self.base_client._build_url("/api/search", {"q": "test", "limit": 10})
        self.assertIn("q=test", url2)
        self.assertIn("limit=10", url2)
        
        # Test avec caractères spéciaux
        url3 = self.base_client._build_url("/api/items", {"name": "test item"})
        self.assertIn("name=test%20item", url3)


if __name__ == '__main__':
    unittest.main()