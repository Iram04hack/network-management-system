"""
Tests unitaires pour le cache de réponses.

Ces tests couvrent toutes les stratégies d'éviction, TTL, thread-safety,
performance et cas d'usage avancés du cache.
"""

import pytest
import time
import threading
from unittest.mock import Mock, patch

from api_clients.infrastructure.response_cache import (
    ResponseCache,
    CacheConfig,
    CacheEntry,
    CacheStats,
    LRUEvictionStrategy,
    LFUEvictionStrategy,
    TTLEvictionStrategy,
    cached_response,
    generate_cache_key,
    DEFAULT_CACHE,
    LONG_LIVED_CACHE,
    SHORT_LIVED_CACHE
)
from api_clients.domain.exceptions import CacheException


class TestCacheEntry:
    """Tests pour les entrées de cache."""
    
    def test_cache_entry_creation(self):
        """Test la création d'une entrée de cache."""
        entry = CacheEntry(
            value="test_value",
            created_at=time.time(),
            last_accessed=time.time(),
            access_count=1,
            ttl=300.0
        )
        
        assert entry.value == "test_value"
        assert entry.access_count == 1
        assert entry.ttl == 300.0
    
    def test_cache_entry_expiration(self):
        """Test l'expiration des entrées de cache."""
        current_time = time.time()
        
        # Entrée non expirée
        entry_valid = CacheEntry(
            value="valid",
            created_at=current_time,
            last_accessed=current_time,
            access_count=1,
            ttl=300.0
        )
        assert not entry_valid.is_expired
        
        # Entrée expirée
        entry_expired = CacheEntry(
            value="expired",
            created_at=current_time - 400,  # Créée il y a 400 secondes
            last_accessed=current_time - 400,
            access_count=1,
            ttl=300.0  # TTL de 300 secondes
        )
        assert entry_expired.is_expired
        
        # Entrée sans TTL (jamais expirée)
        entry_no_ttl = CacheEntry(
            value="no_ttl",
            created_at=current_time - 1000,
            last_accessed=current_time - 1000,
            access_count=1,
            ttl=None
        )
        assert not entry_no_ttl.is_expired
    
    def test_cache_entry_touch(self):
        """Test la mise à jour d'accès d'une entrée."""
        entry = CacheEntry(
            value="test",
            created_at=time.time(),
            last_accessed=time.time() - 10,
            access_count=1
        )
        
        original_access_time = entry.last_accessed
        original_count = entry.access_count
        
        time.sleep(0.01)  # Petit délai pour s'assurer du changement de temps
        entry.touch()
        
        assert entry.last_accessed > original_access_time
        assert entry.access_count == original_count + 1
    
    def test_cache_entry_age(self):
        """Test le calcul de l'âge d'une entrée."""
        created_time = time.time() - 100  # Créée il y a 100 secondes
        entry = CacheEntry(
            value="test",
            created_at=created_time,
            last_accessed=created_time,
            access_count=1
        )
        
        age = entry.age
        assert 99 <= age <= 101  # Environ 100 secondes avec tolérance


class TestEvictionStrategies:
    """Tests pour les stratégies d'éviction."""
    
    def test_lru_eviction_strategy(self):
        """Test la stratégie d'éviction LRU."""
        strategy = LRUEvictionStrategy()
        
        # Créer des entrées avec différents temps d'accès
        current_time = time.time()
        entries = {
            'key1': CacheEntry("value1", current_time, current_time - 100, 1),
            'key2': CacheEntry("value2", current_time, current_time - 50, 1),
            'key3': CacheEntry("value3", current_time, current_time - 10, 1),
        }
        
        # L'entrée la moins récemment utilisée doit être sélectionnée
        evicted_key = strategy.select_for_eviction(entries)
        assert evicted_key == 'key1'  # La plus ancienne en accès
        
        # Test should_evict
        assert strategy.should_evict(entries['key1'], 10, 5)  # Cache plein
        assert not strategy.should_evict(entries['key1'], 3, 5)  # Cache pas plein
    
    def test_lfu_eviction_strategy(self):
        """Test la stratégie d'éviction LFU."""
        strategy = LFUEvictionStrategy()
        
        current_time = time.time()
        entries = {
            'key1': CacheEntry("value1", current_time, current_time, 1),
            'key2': CacheEntry("value2", current_time, current_time, 5),
            'key3': CacheEntry("value3", current_time, current_time, 3),
        }
        
        # L'entrée la moins fréquemment utilisée doit être sélectionnée
        evicted_key = strategy.select_for_eviction(entries)
        assert evicted_key == 'key1'  # Accès count = 1
    
    def test_ttl_eviction_strategy(self):
        """Test la stratégie d'éviction TTL."""
        strategy = TTLEvictionStrategy()
        
        current_time = time.time()
        entries = {
            'key1': CacheEntry("value1", current_time - 100, current_time, 1, ttl=50),  # Expirée
            'key2': CacheEntry("value2", current_time - 10, current_time, 1, ttl=300),  # Non expirée
            'key3': CacheEntry("value3", current_time - 200, current_time, 1, ttl=100), # Expirée
        }
        
        # Une entrée expirée doit être sélectionnée
        evicted_key = strategy.select_for_eviction(entries)
        assert evicted_key in ['key1', 'key3']  # Une des entrées expirées
        
        # Test should_evict avec entrée expirée
        assert strategy.should_evict(entries['key1'], 2, 5)  # Expirée
        assert not strategy.should_evict(entries['key2'], 2, 5)  # Non expirée et cache pas plein


class TestCacheStats:
    """Tests pour les statistiques de cache."""
    
    def test_cache_stats_initialization(self):
        """Test l'initialisation des statistiques."""
        stats = CacheStats()
        
        assert stats.hits == 0
        assert stats.misses == 0
        assert stats.evictions == 0
        assert stats.expired_entries == 0
        assert stats.total_requests == 0
        assert stats.hit_rate == 0.0
        assert stats.miss_rate == 1.0
    
    def test_cache_stats_recording(self):
        """Test l'enregistrement des statistiques."""
        stats = CacheStats()
        
        # Enregistrer quelques hits et misses
        stats.record_hit()
        stats.record_hit()
        stats.record_miss()
        stats.record_eviction()
        stats.record_expiration()
        
        assert stats.hits == 2
        assert stats.misses == 1
        assert stats.total_requests == 3
        assert stats.evictions == 1
        assert stats.expired_entries == 1
        assert stats.hit_rate == 2/3
        assert stats.miss_rate == 1/3
    
    def test_cache_stats_thread_safety(self):
        """Test la thread-safety des statistiques."""
        stats = CacheStats()
        
        def record_stats():
            for _ in range(100):
                stats.record_hit()
                stats.record_miss()
        
        # Lancer plusieurs threads
        threads = []
        for _ in range(10):
            t = threading.Thread(target=record_stats)
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join()
        
        # Vérifier la cohérence
        assert stats.hits == 1000
        assert stats.misses == 1000
        assert stats.total_requests == 2000
        assert stats.hit_rate == 0.5
    
    def test_cache_stats_to_dict(self):
        """Test la conversion des stats en dictionnaire."""
        stats = CacheStats()
        stats.record_hit()
        stats.record_miss()
        
        stats_dict = stats.to_dict()
        
        assert stats_dict['hits'] == 1
        assert stats_dict['misses'] == 1
        assert stats_dict['total_requests'] == 2
        assert stats_dict['hit_rate'] == 0.5
        assert stats_dict['miss_rate'] == 0.5


class TestCacheConfig:
    """Tests pour la configuration de cache."""
    
    def test_default_config(self):
        """Test la configuration par défaut."""
        config = CacheConfig()
        
        assert config.max_size == 1000
        assert config.default_ttl == 300.0
        assert isinstance(config.eviction_strategy, LRUEvictionStrategy)
        assert config.cleanup_interval == 60.0
        assert config.enable_stats is True
    
    def test_custom_config(self):
        """Test une configuration personnalisée."""
        custom_strategy = LFUEvictionStrategy()
        config = CacheConfig(
            max_size=500,
            default_ttl=600.0,
            eviction_strategy=custom_strategy,
            cleanup_interval=120.0,
            enable_stats=False
        )
        
        assert config.max_size == 500
        assert config.default_ttl == 600.0
        assert config.eviction_strategy is custom_strategy
        assert config.cleanup_interval == 120.0
        assert config.enable_stats is False


class TestResponseCache:
    """Tests pour le cache de réponses principal."""
    
    def test_cache_basic_operations(self):
        """Test les opérations de base du cache."""
        cache = ResponseCache(CacheConfig(max_size=10, default_ttl=300.0))
        
        # Test set/get
        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"
        
        # Test clé inexistante
        assert cache.get("nonexistent") is None
        
        # Test delete
        assert cache.delete("key1") is True
        assert cache.get("key1") is None
        assert cache.delete("nonexistent") is False
    
    def test_cache_ttl_expiration(self):
        """Test l'expiration TTL."""
        cache = ResponseCache(CacheConfig(max_size=10, default_ttl=0.1))  # TTL très court
        
        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"
        
        # Attendre l'expiration
        time.sleep(0.15)
        assert cache.get("key1") is None
    
    def test_cache_custom_ttl(self):
        """Test TTL personnalisé par entrée."""
        cache = ResponseCache(CacheConfig(max_size=10, default_ttl=300.0))
        
        # TTL personnalisé court
        cache.set("short_ttl", "value", ttl=0.1)
        cache.set("long_ttl", "value", ttl=300.0)
        
        assert cache.get("short_ttl") == "value"
        assert cache.get("long_ttl") == "value"
        
        time.sleep(0.15)
        
        assert cache.get("short_ttl") is None  # Expiré
        assert cache.get("long_ttl") == "value"  # Toujours valide
    
    def test_cache_eviction_lru(self):
        """Test l'éviction LRU."""
        cache = ResponseCache(CacheConfig(max_size=3, eviction_strategy=LRUEvictionStrategy()))
        
        # Remplir le cache
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")
        
        # Accéder à key1 pour le marquer comme récemment utilisé
        cache.get("key1")
        
        # Ajouter une nouvelle entrée - key2 devrait être évincé (LRU)
        cache.set("key4", "value4")
        
        assert cache.get("key1") == "value1"  # Toujours présent
        assert cache.get("key2") is None      # Évincé
        assert cache.get("key3") == "value3"  # Toujours présent
        assert cache.get("key4") == "value4"  # Nouvelle entrée
    
    def test_cache_cleanup_expired(self):
        """Test le nettoyage des entrées expirées."""
        cache = ResponseCache(CacheConfig(max_size=10, default_ttl=0.1, cleanup_interval=0))
        
        # Ajouter des entrées qui vont expirer
        cache.set("exp1", "value1")
        cache.set("exp2", "value2")
        cache.set("valid", "value_valid", ttl=300.0)  # TTL long
        
        time.sleep(0.15)
        
        # Nettoyage manuel
        cleaned_count = cache.cleanup_expired()
        
        assert cleaned_count == 2  # 2 entrées expirées nettoyées
        assert cache.get("exp1") is None
        assert cache.get("exp2") is None
        assert cache.get("valid") == "value_valid"
    
    def test_cache_clear(self):
        """Test le vidage complet du cache."""
        cache = ResponseCache(CacheConfig(max_size=10))
        
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        
        cache.clear()
        
        assert cache.get("key1") is None
        assert cache.get("key2") is None
    
    def test_cache_get_info(self):
        """Test la récupération d'informations sur le cache."""
        config = CacheConfig(max_size=5, default_ttl=300.0)
        cache = ResponseCache(config)
        
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        
        info = cache.get_info()
        
        assert info['size'] == 2
        assert info['max_size'] == 5
        assert info['config']['default_ttl'] == 300.0
        assert 'stats' in info  # Stats activées par défaut
    
    def test_cache_thread_safety(self):
        """Test la thread-safety du cache."""
        cache = ResponseCache(CacheConfig(max_size=100))
        
        results = []
        
        def cache_operations(thread_id):
            local_results = []
            for i in range(50):
                key = f"thread_{thread_id}_key_{i}"
                value = f"thread_{thread_id}_value_{i}"
                
                cache.set(key, value)
                retrieved = cache.get(key)
                local_results.append(retrieved == value)
            
            results.extend(local_results)
        
        # Lancer plusieurs threads
        threads = []
        for i in range(5):
            t = threading.Thread(target=cache_operations, args=(i,))
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join()
        
        # Tous les gets/sets devraient être cohérents
        assert all(results)
        assert len(results) == 250  # 5 threads * 50 opérations
    
    @patch('threading.Timer')
    def test_cache_periodic_cleanup(self, mock_timer):
        """Test le nettoyage périodique automatique."""
        config = CacheConfig(cleanup_interval=10.0)
        cache = ResponseCache(config)
        
        # Vérifier que le timer est configuré
        mock_timer.assert_called_once_with(10.0, cache._periodic_cleanup)
        mock_timer.return_value.start.assert_called_once()


class TestCacheUtilities:
    """Tests pour les utilitaires de cache."""
    
    def test_generate_cache_key(self):
        """Test la génération de clés de cache."""
        # Clés identiques pour arguments identiques
        key1 = generate_cache_key("arg1", "arg2", kwarg1="value1", kwarg2="value2")
        key2 = generate_cache_key("arg1", "arg2", kwarg1="value1", kwarg2="value2")
        assert key1 == key2
        
        # Clés différentes pour arguments différents
        key3 = generate_cache_key("arg1", "arg3", kwarg1="value1", kwarg2="value2")
        assert key1 != key3
        
        # Ordre des kwargs ne doit pas affecter la clé
        key4 = generate_cache_key("arg1", "arg2", kwarg2="value2", kwarg1="value1")
        assert key1 == key4
        
        # La clé doit être une chaîne hexadécimale
        assert len(key1) == 64  # SHA256 en hex
        assert all(c in '0123456789abcdef' for c in key1)
    
    def test_cached_response_decorator(self):
        """Test le décorateur de mise en cache."""
        cache = ResponseCache(CacheConfig(max_size=10))
        
        call_count = 0
        
        @cached_response(cache, ttl=300.0)
        def expensive_function(x, y):
            nonlocal call_count
            call_count += 1
            return x + y
        
        # Premier appel - fonction exécutée
        result1 = expensive_function(1, 2)
        assert result1 == 3
        assert call_count == 1
        
        # Deuxième appel avec mêmes arguments - depuis cache
        result2 = expensive_function(1, 2)
        assert result2 == 3
        assert call_count == 1  # Pas d'appel supplémentaire
        
        # Appel avec arguments différents - fonction exécutée
        result3 = expensive_function(2, 3)
        assert result3 == 5
        assert call_count == 2
    
    def test_cached_response_decorator_custom_key(self):
        """Test le décorateur avec fonction de clé personnalisée."""
        cache = ResponseCache(CacheConfig(max_size=10))
        
        call_count = 0
        
        def custom_key_func(x, y):
            return f"custom_{x}_{y}"
        
        @cached_response(cache, key_func=custom_key_func)
        def func_with_custom_key(x, y):
            nonlocal call_count
            call_count += 1
            return x * y
        
        result1 = func_with_custom_key(3, 4)
        result2 = func_with_custom_key(3, 4)
        
        assert result1 == 12
        assert result2 == 12
        assert call_count == 1


class TestPredefinedCaches:
    """Tests pour les caches pré-définis."""
    
    def test_default_cache(self):
        """Test le cache par défaut."""
        assert DEFAULT_CACHE.config.max_size == 1000
        assert DEFAULT_CACHE.config.default_ttl == 300.0
    
    def test_long_lived_cache(self):
        """Test le cache longue durée."""
        assert LONG_LIVED_CACHE.config.max_size == 5000
        assert LONG_LIVED_CACHE.config.default_ttl == 3600.0
    
    def test_short_lived_cache(self):
        """Test le cache courte durée."""
        assert SHORT_LIVED_CACHE.config.max_size == 100
        assert SHORT_LIVED_CACHE.config.default_ttl == 60.0


class TestCachePerformance:
    """Tests de performance pour le cache."""
    
    @pytest.mark.performance
    def test_cache_performance_get_set(self):
        """Test de performance pour get/set."""
        cache = ResponseCache(CacheConfig(max_size=10000))
        
        # Test performance set
        start_time = time.time()
        for i in range(1000):
            cache.set(f"key_{i}", f"value_{i}")
        set_time = time.time() - start_time
        
        # Test performance get
        start_time = time.time()
        for i in range(1000):
            cache.get(f"key_{i}")
        get_time = time.time() - start_time
        
        # Les opérations devraient être rapides
        assert set_time < 0.5  # Moins de 0.5ms par set en moyenne
        assert get_time < 0.3   # Moins de 0.3ms par get en moyenne
    
    @pytest.mark.performance
    def test_cache_performance_under_pressure(self):
        """Test de performance sous pression (éviction fréquente)."""
        cache = ResponseCache(CacheConfig(max_size=100))  # Cache petit pour forcer éviction
        
        start_time = time.time()
        
        # Ajouter plus d'entrées que la capacité pour forcer évictions
        for i in range(500):
            cache.set(f"pressure_key_{i}", f"pressure_value_{i}")
        
        pressure_time = time.time() - start_time
        
        # Même avec évictions, ça doit rester raisonnable
        assert pressure_time < 2.0
        
        # Vérifier que le cache n'a pas dépassé sa taille max
        info = cache.get_info()
        assert info['size'] <= 100
    
    @pytest.mark.performance
    def test_cache_memory_usage(self):
        """Test l'usage mémoire du cache."""
        import sys
        
        cache = ResponseCache(CacheConfig(max_size=1000))
        
        # Mesurer la taille de base
        base_size = sys.getsizeof(cache)
        
        # Ajouter des entrées
        for i in range(100):
            cache.set(f"mem_key_{i}", f"mem_value_{i}" * 100)  # Valeurs plus grandes
        
        # La mémoire ne devrait pas exploser de manière déraisonnable
        current_size = sys.getsizeof(cache)
        
        # Test rudimentaire - dans la vraie vie, on utiliserait des outils plus sophistiqués
        assert current_size > base_size  # La mémoire a augmenté
        # Note: sys.getsizeof() ne capture pas tout, mais donne une indication


class TestCacheIntegration:
    """Tests d'intégration pour le cache."""
    
    def test_cache_with_real_data_types(self):
        """Test le cache avec différents types de données."""
        cache = ResponseCache(CacheConfig(max_size=10))
        
        # Types de données variés
        test_data = {
            'string': "test string",
            'integer': 42,
            'float': 3.14,
            'list': [1, 2, 3, "four"],
            'dict': {'nested': {'data': 'value'}},
            'tuple': (1, 2, 3),
            'boolean': True,
            'none': None
        }
        
        # Stocker et récupérer chaque type
        for key, value in test_data.items():
            cache.set(key, value)
            retrieved = cache.get(key)
            assert retrieved == value
            assert type(retrieved) == type(value)
    
    def test_cache_error_handling(self):
        """Test la gestion d'erreur du cache."""
        cache = ResponseCache(CacheConfig(max_size=1, enable_stats=True))
        
        # Cas d'erreur: clé None
        with pytest.raises(Exception):
            cache.get(None)
        
        # Cas d'erreur: éviction impossible (cache vide)
        strategy = LRUEvictionStrategy()
        with pytest.raises(CacheException):
            strategy.select_for_eviction({})
    
    def test_cache_workflow_simulation(self):
        """Test simulation d'un workflow réaliste de cache."""
        cache = ResponseCache(CacheConfig(
            max_size=50,
            default_ttl=1.0,  # TTL court pour simulation
            eviction_strategy=LRUEvictionStrategy()
        ))
        
        # Simulation d'une application qui fait de nombreuses requêtes
        access_pattern = []
        
        # Phase 1: Remplissage initial
        for i in range(30):
            key = f"data_{i}"
            cache.set(key, f"value_{i}")
            access_pattern.append(('set', key))
        
        # Phase 2: Accès avec localité temporelle
        for _ in range(20):
            for i in range(5, 15):  # Accès concentré sur un sous-ensemble
                key = f"data_{i}"
                value = cache.get(key)
                access_pattern.append(('get', key, value is not None))
        
        # Phase 3: Ajout de nouvelles données (force éviction)
        for i in range(30, 60):
            key = f"data_{i}"
            cache.set(key, f"value_{i}")
            access_pattern.append(('set', key))
        
        # Phase 4: Vérification que les données fréquemment accédées sont préservées
        frequently_accessed_present = 0
        for i in range(5, 15):
            if cache.get(f"data_{i}") is not None:
                frequently_accessed_present += 1
        
        # Au moins quelques-unes des données fréquemment accédées devraient être préservées
        assert frequently_accessed_present > 0
        
        # Obtenir les stats finales
        info = cache.get_info()
        assert info['size'] <= 50  # Respecte la limite
        
        if 'stats' in info:
            stats = info['stats']
            assert stats['total_requests'] > 0
            # Le hit rate devrait être raisonnable grâce à la localité temporelle
            assert stats['hit_rate'] >= 0.1  # Au moins 10% de hits 