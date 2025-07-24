import unittest
import time
import random
import redis
from unittest.mock import MagicMock, patch

# Simulation des imports Django
class MockDjangoSettings:
    REDIS_HOST = "172.18.0.2"
    REDIS_PORT = 6379
    REDIS_DB = 0
    REDIS_PASSWORD = None
    CACHE_TTL = 3600

class TestBenchmarkOptimizations(unittest.TestCase):
    """Tests pour le benchmark des optimisations de l'assistant IA"""
    
    def setUp(self):
        """Configuration initiale pour les tests"""
        self.settings = MockDjangoSettings()
        self.redis_client = redis.Redis(
            host=self.settings.REDIS_HOST,
            port=self.settings.REDIS_PORT,
            db=self.settings.REDIS_DB,
            password=self.settings.REDIS_PASSWORD,
            decode_responses=True
        )
        # Nettoyage du cache Redis avant les tests
        self.redis_client.flushdb()
    
    def tearDown(self):
        """Nettoyage après les tests"""
        self.redis_client.flushdb()
        self.redis_client.close()
    
    def test_cache_performance(self):
        """Test de performance du cache Redis"""
        # Simulation d'une requête coûteuse
        def expensive_operation(query):
            time.sleep(0.5)  # Simulation d'une opération lente
            return f"Résultat pour: {query}"
        
        # Fonction qui utilise le cache
        def get_with_cache(key, operation, ttl=3600):
            result = self.redis_client.get(key)
            if result:
                return result, True  # Résultat du cache
            
            # Exécution de l'opération coûteuse
            result = operation(key)
            self.redis_client.setex(key, ttl, result)
            return result, False  # Nouveau résultat
        
        # Test avec une nouvelle requête
        query = f"test_query_{random.randint(1000, 9999)}"
        start_time = time.time()
        result1, from_cache1 = get_with_cache(query, expensive_operation)
        first_duration = time.time() - start_time
        
        # Test avec la même requête (devrait venir du cache)
        start_time = time.time()
        result2, from_cache2 = get_with_cache(query, expensive_operation)
        second_duration = time.time() - start_time
        
        # Vérifications
        self.assertEqual(result1, result2)
        self.assertFalse(from_cache1)
        self.assertTrue(from_cache2)
        self.assertLess(second_duration, first_duration / 2)
    
    @patch('redis.Redis')
    def test_redis_connection_error(self, mock_redis):
        """Test de la gestion des erreurs de connexion Redis"""
        # Configuration du mock pour simuler une erreur de connexion
        mock_instance = MagicMock()
        mock_instance.get.side_effect = redis.ConnectionError("Erreur de connexion simulée")
        mock_redis.return_value = mock_instance
        
        # Fonction qui gère les erreurs de connexion
        def safe_cache_get(key, default=None):
            try:
                client = redis.Redis(
                    host=self.settings.REDIS_HOST,
                    port=self.settings.REDIS_PORT,
                    db=self.settings.REDIS_DB,
                    password=self.settings.REDIS_PASSWORD,
                    decode_responses=True
                )
                return client.get(key)
            except redis.ConnectionError:
                return default
        
        # Vérification que l'erreur est correctement gérée
        result = safe_cache_get("test_key", "valeur_par_défaut")
        self.assertEqual(result, "valeur_par_défaut")
    
    def test_cache_ttl(self):
        """Test de la durée de vie du cache"""
        key = f"ttl_test_{random.randint(1000, 9999)}"
        value = "test_value"
        short_ttl = 1  # 1 seconde
        
        # Stockage avec un TTL court
        self.redis_client.setex(key, short_ttl, value)
        
        # Vérification immédiate
        self.assertEqual(self.redis_client.get(key), value)
        
        # Attente que le TTL expire
        time.sleep(1.5)
        
        # Vérification que la valeur a expiré
        self.assertIsNone(self.redis_client.get(key))

if __name__ == '__main__':
    unittest.main() 