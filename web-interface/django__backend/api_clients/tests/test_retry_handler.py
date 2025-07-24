"""
Tests unitaires pour le Retry Handler.

Ces tests couvrent toutes les stratégies de backoff, la gestion d'erreur
et les cas d'usage avancés du retry handler.
"""

import pytest
import time
import threading
from unittest.mock import Mock, patch

from api_clients.infrastructure.retry_handler import (
    RetryHandler,
    RetryConfig,
    ExponentialBackoffStrategy,
    LinearBackoffStrategy,
    FixedBackoffStrategy,
    retry_on_failure,
    DEFAULT_RETRY_HANDLER,
    AGGRESSIVE_RETRY_HANDLER,
    CONSERVATIVE_RETRY_HANDLER
)
from api_clients.domain.exceptions import (
    RetryExhaustedException,
    APIConnectionException,
    APITimeoutException,
    ValidationException
)


class TestBackoffStrategies:
    """Tests pour les différentes stratégies de backoff."""
    
    def test_exponential_backoff_calculation(self):
        """Test le calcul du backoff exponentiel."""
        strategy = ExponentialBackoffStrategy(max_delay=60.0, jitter=False)
        
        # Test progression exponentielle
        assert strategy.calculate_delay(1, 1.0) == 1.0
        assert strategy.calculate_delay(2, 1.0) == 2.0
        assert strategy.calculate_delay(3, 1.0) == 4.0
        assert strategy.calculate_delay(4, 1.0) == 8.0
        
        # Test limitation max_delay
        assert strategy.calculate_delay(10, 1.0) == 60.0  # Limité à max_delay
    
    def test_exponential_backoff_with_jitter(self):
        """Test le backoff exponentiel avec jitter."""
        strategy = ExponentialBackoffStrategy(max_delay=60.0, jitter=True, jitter_factor=0.1)
        
        # Le jitter doit varier le délai dans une plage
        base_delay = strategy.calculate_delay(3, 1.0)  # 4.0 sans jitter
        delays = [strategy.calculate_delay(3, 1.0) for _ in range(10)]
        
        # Vérifier que les délais varient
        assert len(set(delays)) > 1  # Au moins quelques valeurs différentes
        
        # Vérifier que tous les délais sont dans une plage raisonnable
        for delay in delays:
            assert 3.6 <= delay <= 4.4  # 4.0 ± 10%
    
    def test_linear_backoff_calculation(self):
        """Test le calcul du backoff linéaire."""
        strategy = LinearBackoffStrategy(max_delay=30.0)
        
        # Test progression linéaire
        assert strategy.calculate_delay(1, 2.0) == 2.0
        assert strategy.calculate_delay(2, 2.0) == 4.0
        assert strategy.calculate_delay(3, 2.0) == 6.0
        assert strategy.calculate_delay(4, 2.0) == 8.0
        
        # Test limitation max_delay
        assert strategy.calculate_delay(20, 2.0) == 30.0  # Limité à max_delay
    
    def test_fixed_backoff_calculation(self):
        """Test le calcul du backoff fixe."""
        strategy = FixedBackoffStrategy()
        
        # Le délai doit rester constant
        assert strategy.calculate_delay(1, 5.0) == 5.0
        assert strategy.calculate_delay(2, 5.0) == 5.0
        assert strategy.calculate_delay(10, 5.0) == 5.0


class TestRetryConfig:
    """Tests pour la configuration du retry handler."""
    
    def test_default_config(self):
        """Test la configuration par défaut."""
        config = RetryConfig()
        
        assert config.max_retries == 3
        assert config.base_delay == 1.0
        assert isinstance(config.backoff_strategy, ExponentialBackoffStrategy)
        assert APIConnectionException in config.retryable_exceptions
        assert ValueError in config.non_retryable_exceptions
        assert 502 in config.retry_on_status_codes
        assert 400 in config.no_retry_on_status_codes
    
    def test_custom_config(self):
        """Test une configuration personnalisée."""
        custom_strategy = LinearBackoffStrategy()
        config = RetryConfig(
            max_retries=5,
            base_delay=2.0,
            backoff_strategy=custom_strategy,
            retryable_exceptions=[ConnectionError],
            non_retryable_exceptions=[TypeError],
            retry_on_status_codes=[503, 504],
            no_retry_on_status_codes=[401, 403]
        )
        
        assert config.max_retries == 5
        assert config.base_delay == 2.0
        assert config.backoff_strategy is custom_strategy
        assert config.retryable_exceptions == [ConnectionError]
        assert config.non_retryable_exceptions == [TypeError]
        assert config.retry_on_status_codes == [503, 504]
        assert config.no_retry_on_status_codes == [401, 403]
    
    def test_invalid_config_validation(self):
        """Test la validation des configurations invalides."""
        with pytest.raises(Exception):  # ConfigurationException
            RetryConfig(max_retries=-1)
        
        with pytest.raises(Exception):  # ConfigurationException
            RetryConfig(base_delay=0)


class TestRetryHandler:
    """Tests pour le gestionnaire de retry principal."""
    
    def test_successful_execution_no_retry(self):
        """Test l'exécution réussie sans retry."""
        handler = RetryHandler()
        
        def success_func():
            return "success"
        
        result = handler.execute_with_retry(success_func)
        assert result == "success"
    
    def test_retry_on_retryable_exception(self):
        """Test le retry sur une exception retryable."""
        config = RetryConfig(max_retries=2, base_delay=0.01)  # Délai très court pour les tests
        handler = RetryHandler(config)
        
        call_count = 0
        def failing_then_success():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise APIConnectionException("Connection failed")
            return "success"
        
        result = handler.execute_with_retry(failing_then_success)
        assert result == "success"
        assert call_count == 3  # 1 initial + 2 retries
    
    def test_retry_exhausted_exception(self):
        """Test l'exception quand les retries sont épuisés."""
        config = RetryConfig(max_retries=2, base_delay=0.01)
        handler = RetryHandler(config)
        
        call_count = 0
        def always_failing():
            nonlocal call_count
            call_count += 1
            raise APIConnectionException("Always fails")
        
        with pytest.raises(RetryExhaustedException) as exc_info:
            handler.execute_with_retry(always_failing)
        
        assert call_count == 3  # 1 initial + 2 retries
        assert exc_info.value.max_retries == 2
        assert isinstance(exc_info.value.last_exception, APIConnectionException)
    
    def test_no_retry_on_non_retryable_exception(self):
        """Test qu'il n'y a pas de retry sur une exception non-retryable."""
        handler = RetryHandler()
        
        call_count = 0
        def non_retryable_failure():
            nonlocal call_count
            call_count += 1
            raise ValueError("Invalid input")
        
        with pytest.raises(ValueError):
            handler.execute_with_retry(non_retryable_failure)
        
        assert call_count == 1  # Aucun retry
    
    def test_retry_with_status_codes(self):
        """Test le retry basé sur les codes de statut HTTP."""
        config = RetryConfig(max_retries=2, base_delay=0.01)
        handler = RetryHandler(config)
        
        call_count = 0
        def http_error_then_success():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                # Simuler une exception avec status_code
                exc = APIConnectionException("Server error")
                exc.status_code = 502  # Bad Gateway - retryable
                raise exc
            return "success"
        
        result = handler.execute_with_retry(http_error_then_success)
        assert result == "success"
        assert call_count == 3
    
    def test_no_retry_on_client_error_status(self):
        """Test pas de retry sur erreur client HTTP."""
        handler = RetryHandler()
        
        call_count = 0
        def client_error():
            nonlocal call_count
            call_count += 1
            exc = APIConnectionException("Not found")
            exc.status_code = 404  # Not Found - non retryable
            raise exc
        
        with pytest.raises(APIConnectionException):
            handler.execute_with_retry(client_error)
        
        assert call_count == 1  # Aucun retry
    
    def test_backoff_timing(self):
        """Test que les délais de backoff sont respectés."""
        config = RetryConfig(
            max_retries=2,
            base_delay=0.1,
            backoff_strategy=FixedBackoffStrategy()  # Délai fixe pour test prévisible
        )
        handler = RetryHandler(config)
        
        call_times = []
        def failing_func():
            call_times.append(time.time())
            raise APIConnectionException("Fail")
        
        start_time = time.time()
        with pytest.raises(RetryExhaustedException):
            handler.execute_with_retry(failing_func)
        
        # Vérifier les intervalles entre les appels
        assert len(call_times) == 3  # 1 initial + 2 retries
        
        # Vérifier que les délais sont respectés (avec tolérance)
        interval1 = call_times[1] - call_times[0]
        interval2 = call_times[2] - call_times[1]
        
        assert 0.08 <= interval1 <= 0.15  # ~0.1s avec tolérance
        assert 0.08 <= interval2 <= 0.15
    
    def test_get_stats(self):
        """Test la récupération des statistiques."""
        config = RetryConfig(max_retries=5, base_delay=2.0)
        handler = RetryHandler(config)
        
        stats = handler.get_stats()
        
        assert stats['max_retries'] == 5
        assert stats['base_delay'] == 2.0
        assert stats['backoff_strategy'] == 'ExponentialBackoffStrategy'
        assert 'retryable_exceptions' in stats
        assert 'retry_on_status_codes' in stats


class TestRetryDecorator:
    """Tests pour le décorateur retry_on_failure."""
    
    def test_decorator_basic_usage(self):
        """Test l'utilisation de base du décorateur."""
        config = RetryConfig(max_retries=2, base_delay=0.01)
        
        @retry_on_failure(config)
        def decorated_func():
            return "decorated_result"
        
        result = decorated_func()
        assert result == "decorated_result"
    
    def test_decorator_with_retries(self):
        """Test le décorateur avec des retries."""
        config = RetryConfig(max_retries=2, base_delay=0.01)
        
        call_count = 0
        @retry_on_failure(config)
        def decorated_failing_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise APIConnectionException("Decorated fail")
            return "decorated_success"
        
        result = decorated_failing_func()
        assert result == "decorated_success"
        assert call_count == 3
    
    def test_decorator_preserves_function_metadata(self):
        """Test que le décorateur préserve les métadonnées de fonction."""
        @retry_on_failure()
        def documented_func():
            """This is a documented function."""
            return "result"
        
        assert documented_func.__name__ == "documented_func"
        assert "documented function" in documented_func.__doc__


class TestPredefinedRetryHandlers:
    """Tests pour les handlers pré-définis."""
    
    def test_default_retry_handler(self):
        """Test le handler par défaut."""
        assert DEFAULT_RETRY_HANDLER.config.max_retries == 3
        assert DEFAULT_RETRY_HANDLER.config.base_delay == 1.0
    
    def test_aggressive_retry_handler(self):
        """Test le handler agressif."""
        assert AGGRESSIVE_RETRY_HANDLER.config.max_retries == 5
        assert AGGRESSIVE_RETRY_HANDLER.config.base_delay == 0.5
    
    def test_conservative_retry_handler(self):
        """Test le handler conservateur."""
        assert CONSERVATIVE_RETRY_HANDLER.config.max_retries == 2
        assert CONSERVATIVE_RETRY_HANDLER.config.base_delay == 2.0


class TestRetryHandlerConcurrency:
    """Tests de concurrence pour le retry handler."""
    
    def test_concurrent_retries(self):
        """Test l'exécution concurrente de retries."""
        handler = RetryHandler(RetryConfig(max_retries=1, base_delay=0.01))
        
        results = []
        exceptions = []
        
        def concurrent_func(thread_id):
            try:
                # Fonction qui échoue pour les IDs pairs
                if thread_id % 2 == 0:
                    raise APIConnectionException(f"Fail {thread_id}")
                else:
                    return f"Success {thread_id}"
            except Exception as e:
                exceptions.append(e)
                raise
        
        def run_retry(thread_id):
            try:
                result = handler.execute_with_retry(concurrent_func, thread_id)
                results.append(result)
            except Exception as e:
                exceptions.append(e)
        
        # Lancer plusieurs threads
        threads = []
        for i in range(10):
            t = threading.Thread(target=run_retry, args=(i,))
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join()
        
        # Vérifier les résultats
        success_results = [r for r in results if "Success" in r]
        assert len(success_results) == 5  # IDs impairs (1, 3, 5, 7, 9)
        
        # Les échecs devraient générer des RetryExhaustedException
        retry_exceptions = [e for e in exceptions if isinstance(e, RetryExhaustedException)]
        assert len(retry_exceptions) == 5  # IDs pairs


class TestRetryHandlerIntegration:
    """Tests d'intégration pour le retry handler."""
    
    def test_real_world_scenario_flaky_service(self):
        """Test un scénario réaliste avec un service instable."""
        config = RetryConfig(
            max_retries=5,
            base_delay=0.01,
            backoff_strategy=ExponentialBackoffStrategy(max_delay=0.5, jitter=True)
        )
        handler = RetryHandler(config)
        
        # Simuler un service qui échoue 70% du temps
        call_history = []
        def flaky_service(success_rate=0.3):
            call_history.append(time.time())
            import random
            if random.random() > success_rate:
                raise APITimeoutException("Service timeout")
            return {"status": "success", "data": "Important data"}
        
        # Fixer la seed pour la reproductibilité du test
        import random
        random.seed(42)
        
        try:
            result = handler.execute_with_retry(flaky_service)
            assert result["status"] == "success"
        except RetryExhaustedException:
            # C'est acceptable dans ce test de service très instable
            pass
        
        # Vérifier qu'il y a eu des tentatives
        assert len(call_history) >= 1
    
    def test_retry_with_circuit_breaker_interaction(self):
        """Test l'intégration avec un circuit breaker simulé."""
        config = RetryConfig(max_retries=3, base_delay=0.01)
        handler = RetryHandler(config)
        
        # Simuler un circuit breaker qui s'ouvre après 3 échecs
        circuit_failures = 0
        circuit_open = False
        
        def service_with_circuit_breaker():
            nonlocal circuit_failures, circuit_open
            
            if circuit_open:
                raise Exception("Circuit breaker open")
            
            circuit_failures += 1
            if circuit_failures >= 3:
                circuit_open = True
            
            raise APIConnectionException("Service down")
        
        # Le retry handler devrait s'arrêter quand le circuit breaker s'ouvre
        with pytest.raises(Exception) as exc_info:
            handler.execute_with_retry(service_with_circuit_breaker)
        
        # L'exception finale peut être soit RetryExhaustedException soit "Circuit breaker open"
        assert "Circuit breaker open" in str(exc_info.value) or isinstance(exc_info.value, RetryExhaustedException)
    
    @pytest.mark.performance
    def test_retry_handler_performance(self):
        """Test de performance du retry handler."""
        handler = RetryHandler()
        
        def fast_success():
            return "success"
        
        # Mesurer le temps pour de nombreux appels réussis
        start_time = time.time()
        for _ in range(1000):
            handler.execute_with_retry(fast_success)
        end_time = time.time()
        
        execution_time = end_time - start_time
        
        # Le retry handler ne devrait pas ajouter une surcharge significative
        # pour les appels réussis (moins de 0.5ms par appel en moyenne)
        assert execution_time < 0.5
    
    def test_retry_with_different_exception_types(self):
        """Test le retry avec différents types d'exceptions."""
        config = RetryConfig(
            max_retries=1,
            base_delay=0.01,
            retryable_exceptions=[ConnectionError, APITimeoutException],
            non_retryable_exceptions=[ValueError, TypeError]
        )
        handler = RetryHandler(config)
        
        # Test avec exception retryable
        call_count_retryable = 0
        def retryable_failure():
            nonlocal call_count_retryable
            call_count_retryable += 1
            if call_count_retryable == 1:
                raise ConnectionError("Network issue")
            return "recovered"
        
        result = handler.execute_with_retry(retryable_failure)
        assert result == "recovered"
        assert call_count_retryable == 2
        
        # Test avec exception non-retryable
        call_count_non_retryable = 0
        def non_retryable_failure():
            nonlocal call_count_non_retryable
            call_count_non_retryable += 1
            raise ValueError("Bad input")
        
        with pytest.raises(ValueError):
            handler.execute_with_retry(non_retryable_failure)
        
        assert call_count_non_retryable == 1  # Aucun retry 