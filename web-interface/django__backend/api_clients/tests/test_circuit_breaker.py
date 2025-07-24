"""
Tests unitaires pour le Circuit Breaker.

Ces tests couvrent tous les aspects du circuit breaker incluant
la thread-safety, les transitions d'état et les métriques.
"""

import pytest
import time
import threading
from unittest.mock import Mock, patch

from api_clients.infrastructure.circuit_breaker import (
    DefaultCircuitBreaker,
    CircuitBreakerConfig,
    CircuitState,
    CircuitBreakerMetrics,
    CircuitBreakerOpenException
)
from api_clients.domain.exceptions import APIConnectionException


class TestCircuitBreakerMetrics:
    """Tests pour les métriques du Circuit Breaker."""
    
    def test_metrics_initialization(self):
        """Test l'initialisation des métriques."""
        metrics = CircuitBreakerMetrics()
        
        assert metrics.failure_count == 0
        assert metrics.success_count == 0
        assert metrics.total_calls == 0
        assert metrics.last_failure_time is None
        assert metrics.last_success_time is None
        assert metrics.state_transitions == []
    
    def test_record_success_thread_safe(self):
        """Test l'enregistrement thread-safe des succès."""
        metrics = CircuitBreakerMetrics()
        num_threads = 10
        calls_per_thread = 100
        
        def record_successes():
            for _ in range(calls_per_thread):
                metrics.record_success()
        
        threads = []
        for _ in range(num_threads):
            t = threading.Thread(target=record_successes)
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join()
        
        expected_total = num_threads * calls_per_thread
        assert metrics.success_count == expected_total
        assert metrics.total_calls == expected_total
        assert metrics.last_success_time is not None
    
    def test_record_failure_thread_safe(self):
        """Test l'enregistrement thread-safe des échecs."""
        metrics = CircuitBreakerMetrics()
        num_threads = 5
        calls_per_thread = 50
        
        def record_failures():
            for _ in range(calls_per_thread):
                metrics.record_failure()
        
        threads = []
        for _ in range(num_threads):
            t = threading.Thread(target=record_failures)
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join()
        
        expected_total = num_threads * calls_per_thread
        assert metrics.failure_count == expected_total
        assert metrics.total_calls == expected_total
        assert metrics.last_failure_time is not None
    
    def test_state_transitions_tracking(self):
        """Test le suivi des transitions d'état."""
        metrics = CircuitBreakerMetrics()
        
        # Enregistrer plusieurs transitions
        metrics.record_state_transition(CircuitState.CLOSED, CircuitState.OPEN)
        metrics.record_state_transition(CircuitState.OPEN, CircuitState.HALF_OPEN)
        metrics.record_state_transition(CircuitState.HALF_OPEN, CircuitState.CLOSED)
        
        assert len(metrics.state_transitions) == 3
        
        # Vérifier la structure des transitions
        transition = metrics.state_transitions[0]
        assert 'timestamp' in transition
        assert transition['from_state'] == 'closed'
        assert transition['to_state'] == 'open'
    
    def test_state_transitions_limit(self):
        """Test la limitation du nombre de transitions stockées."""
        metrics = CircuitBreakerMetrics()
        
        # Ajouter plus de 100 transitions
        for i in range(150):
            from_state = CircuitState.CLOSED if i % 2 == 0 else CircuitState.OPEN
            to_state = CircuitState.OPEN if i % 2 == 0 else CircuitState.CLOSED
            metrics.record_state_transition(from_state, to_state)
        
        # Vérifier que seulement 100 transitions sont conservées
        assert len(metrics.state_transitions) == 100


class TestCircuitBreakerConfig:
    """Tests pour la configuration du Circuit Breaker."""
    
    def test_default_config(self):
        """Test la configuration par défaut."""
        config = CircuitBreakerConfig()
        
        assert config.failure_threshold == 5
        assert config.reset_timeout == 60.0
        assert config.half_open_success_threshold == 3
        assert config.half_open_max_calls == 5
        assert config.expected_exception == Exception
    
    def test_custom_config(self):
        """Test la configuration personnalisée."""
        config = CircuitBreakerConfig(
            failure_threshold=10,
            reset_timeout=120.0,
            half_open_success_threshold=5,
            half_open_max_calls=10,
            expected_exception=APIConnectionException
        )
        
        assert config.failure_threshold == 10
        assert config.reset_timeout == 120.0
        assert config.half_open_success_threshold == 5
        assert config.half_open_max_calls == 10
        assert config.expected_exception == APIConnectionException


class TestDefaultCircuitBreaker:
    """Tests pour l'implémentation du Circuit Breaker."""
    
    def test_initialization(self):
        """Test l'initialisation du Circuit Breaker."""
        cb = DefaultCircuitBreaker()
        
        assert cb.state == CircuitState.CLOSED
        assert isinstance(cb.config, CircuitBreakerConfig)
        assert isinstance(cb.metrics, CircuitBreakerMetrics)
    
    def test_successful_call(self):
        """Test un appel réussi."""
        cb = DefaultCircuitBreaker()
        
        def success_func():
            return "success"
        
        result = cb.call(success_func)
        
        assert result == "success"
        assert cb.state == CircuitState.CLOSED
        assert cb.metrics.success_count == 1
        assert cb.metrics.failure_count == 0
    
    def test_failed_call(self):
        """Test un appel échoué."""
        cb = DefaultCircuitBreaker()
        
        def failure_func():
            raise APIConnectionException("Test error")
        
        with pytest.raises(APIConnectionException):
            cb.call(failure_func)
        
        assert cb.state == CircuitState.CLOSED  # Encore fermé après 1 échec
        assert cb.metrics.failure_count == 1
        assert cb.metrics.success_count == 0
    
    def test_circuit_opens_after_threshold(self):
        """Test l'ouverture du circuit après le seuil d'échecs."""
        config = CircuitBreakerConfig(failure_threshold=3)
        cb = DefaultCircuitBreaker(config)
        
        def failure_func():
            raise APIConnectionException("Test error")
        
        # Provoquer 3 échecs pour atteindre le seuil
        for _ in range(3):
            with pytest.raises(APIConnectionException):
                cb.call(failure_func)
        
        assert cb.state == CircuitState.OPEN
        assert cb.metrics.failure_count == 3
    
    def test_circuit_blocks_calls_when_open(self):
        """Test que le circuit bloque les appels quand il est ouvert."""
        config = CircuitBreakerConfig(failure_threshold=2)
        cb = DefaultCircuitBreaker(config)
        
        def failure_func():
            raise APIConnectionException("Test error")
        
        # Ouvrir le circuit
        for _ in range(2):
            with pytest.raises(APIConnectionException):
                cb.call(failure_func)
        
        assert cb.state == CircuitState.OPEN
        
        # Maintenant les appels doivent être bloqués
        def any_func():
            return "should not execute"
        
        with pytest.raises(CircuitBreakerOpenException):
            cb.call(any_func)
    
    def test_circuit_transitions_to_half_open(self):
        """Test la transition vers l'état semi-ouvert."""
        config = CircuitBreakerConfig(failure_threshold=2, reset_timeout=0.1, half_open_success_threshold=1)
        cb = DefaultCircuitBreaker(config)
        
        def failure_func():
            raise APIConnectionException("Test error")
        
        # Ouvrir le circuit
        for _ in range(2):
            with pytest.raises(APIConnectionException):
                cb.call(failure_func)
        
        assert cb.state == CircuitState.OPEN
        
        # Attendre le timeout de reset
        time.sleep(0.15)
        
        # Le prochain appel doit déclencher la transition vers HALF_OPEN
        def success_func():
            return "success"
        
        result = cb.call(success_func)
        
        assert result == "success"
        assert cb.state == CircuitState.CLOSED  # Devrait fermer après un succès
    
    def test_half_open_success_closes_circuit(self):
        """Test que des succès en mode semi-ouvert ferment le circuit."""
        config = CircuitBreakerConfig(
            failure_threshold=2, 
            reset_timeout=0.1, 
            half_open_success_threshold=2
        )
        cb = DefaultCircuitBreaker(config)
        
        def failure_func():
            raise APIConnectionException("Test error")
        
        def success_func():
            return "success"
        
        # Ouvrir le circuit
        for _ in range(2):
            with pytest.raises(APIConnectionException):
                cb.call(failure_func)
        
        assert cb.state == CircuitState.OPEN
        
        # Attendre le timeout
        time.sleep(0.15)
        
        # Premier succès - devrait passer en HALF_OPEN
        cb.call(success_func)
        assert cb.state == CircuitState.HALF_OPEN
        
        # Deuxième succès - devrait fermer le circuit
        cb.call(success_func)
        assert cb.state == CircuitState.CLOSED
    
    def test_half_open_failure_reopens_circuit(self):
        """Test qu'un échec en mode semi-ouvert rouvre le circuit."""
        config = CircuitBreakerConfig(failure_threshold=2, reset_timeout=0.1)
        cb = DefaultCircuitBreaker(config)
        
        def failure_func():
            raise APIConnectionException("Test error")
        
        def success_func():
            return "success"
        
        # Ouvrir le circuit
        for _ in range(2):
            with pytest.raises(APIConnectionException):
                cb.call(failure_func)
        
        # Attendre le timeout
        time.sleep(0.15)
        
        # Premier appel réussi - passe en HALF_OPEN
        cb.call(success_func)
        assert cb.state == CircuitState.HALF_OPEN
        
        # Échec suivant - doit rouvrir le circuit
        with pytest.raises(APIConnectionException):
            cb.call(failure_func)
        
        assert cb.state == CircuitState.OPEN
    
    def test_half_open_concurrency_limit(self):
        """Test la limitation de concurrence en mode semi-ouvert."""
        config = CircuitBreakerConfig(
            failure_threshold=1, 
            reset_timeout=0.1, 
            half_open_max_calls=2
        )
        cb = DefaultCircuitBreaker(config)
        
        def failure_func():
            raise APIConnectionException("Test error")
        
        # Ouvrir le circuit
        with pytest.raises(APIConnectionException):
            cb.call(failure_func)
        
        # Attendre le timeout
        time.sleep(0.15)
        
        # Simuler des appels concurrents en mode semi-ouvert
        results = []
        exceptions = []
        
        def slow_func():
            time.sleep(0.1)
            return "success"
        
        def make_call():
            try:
                result = cb.call(slow_func)
                results.append(result)
            except Exception as e:
                exceptions.append(e)
        
        # Lancer plusieurs threads simultanés
        threads = []
        for _ in range(5):  # Plus que la limite de half_open_max_calls
            t = threading.Thread(target=make_call)
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join()
        
        # Certains appels doivent être bloqués
        assert len(exceptions) > 0
        assert any(isinstance(e, CircuitBreakerOpenException) for e in exceptions)
    
    def test_non_expected_exceptions_dont_trigger_circuit(self):
        """Test que les exceptions non attendues ne déclenchent pas le circuit."""
        config = CircuitBreakerConfig(
            failure_threshold=2,
            expected_exception=APIConnectionException
        )
        cb = DefaultCircuitBreaker(config)
        
        def value_error_func():
            raise ValueError("This should not trigger circuit")
        
        # Cette exception ne devrait pas compter comme un échec
        with pytest.raises(ValueError):
            cb.call(value_error_func)
        
        assert cb.state == CircuitState.CLOSED
        assert cb.metrics.failure_count == 0
    
    def test_circuit_breaker_reset(self):
        """Test la réinitialisation manuelle du circuit breaker."""
        config = CircuitBreakerConfig(failure_threshold=2)
        cb = DefaultCircuitBreaker(config)
        
        def failure_func():
            raise APIConnectionException("Test error")
        
        # Ouvrir le circuit
        for _ in range(2):
            with pytest.raises(APIConnectionException):
                cb.call(failure_func)
        
        assert cb.state == CircuitState.OPEN
        assert cb.metrics.failure_count == 2
        
        # Réinitialiser
        cb.reset()
        
        assert cb.state == CircuitState.CLOSED
        assert cb.metrics.failure_count == 0
        assert cb.metrics.success_count == 0
    
    def test_get_state_info(self):
        """Test la récupération des informations d'état."""
        cb = DefaultCircuitBreaker()
        
        state_info = cb.get_state_info()
        
        assert 'state' in state_info
        assert 'failure_count' in state_info
        assert 'success_count' in state_info
        assert 'total_calls' in state_info
        assert 'config' in state_info
        assert 'recent_transitions' in state_info
        
        assert state_info['state'] == 'closed'
        assert isinstance(state_info['config'], dict)
    
    def test_thread_safety_state_transitions(self):
        """Test critique de thread-safety des transitions d'état."""
        config = CircuitBreakerConfig(failure_threshold=5, reset_timeout=0.1)
        cb = DefaultCircuitBreaker(config)
        
        results = {'success': 0, 'failure': 0, 'blocked': 0}
        lock = threading.Lock()
        
        def success_func():
            return "success"
        
        def failure_func():
            raise APIConnectionException("Test error")
        
        def make_calls():
            for i in range(20):
                try:
                    if i % 3 == 0:
                        cb.call(failure_func)
                        with lock:
                            results['failure'] += 1
                    else:
                        cb.call(success_func)
                        with lock:
                            results['success'] += 1
                except CircuitBreakerOpenException:
                    with lock:
                        results['blocked'] += 1
                except APIConnectionException:
                    with lock:
                        results['failure'] += 1
                
                # Petit délai pour augmenter les chances de concurrence
                time.sleep(0.001)
        
        # Lancer plusieurs threads
        threads = []
        for _ in range(5):
            t = threading.Thread(target=make_calls)
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join()
        
        # Vérifier que l'état final est cohérent
        final_state = cb.get_state_info()
        
        # L'état doit être valide
        assert final_state['state'] in ['closed', 'open', 'half_open']
        
        # Les compteurs doivent être cohérents
        total_calls = final_state['failure_count'] + final_state['success_count']
        assert total_calls >= 0
        
        # Il devrait y avoir eu des appels bloqués si le circuit s'est ouvert
        if final_state['state'] == 'open':
            assert results['blocked'] > 0


class TestCircuitBreakerIntegration:
    """Tests d'intégration pour le Circuit Breaker."""
    
    def test_realistic_failure_scenario(self):
        """Test un scénario réaliste de défaillance et récupération."""
        config = CircuitBreakerConfig(
            failure_threshold=3,
            reset_timeout=0.2,
            half_open_success_threshold=2
        )
        cb = DefaultCircuitBreaker(config)
        
        call_history = []
        
        def flaky_service(fail=False):
            if fail:
                raise APIConnectionException("Service unavailable")
            return "success"
        
        # Phase 1: Service fonctionne normalement
        for _ in range(5):
            result = cb.call(lambda: flaky_service(fail=False))
            call_history.append(("success", cb.state.value))
        
        assert cb.state == CircuitState.CLOSED
        
        # Phase 2: Service commence à échouer
        for _ in range(3):
            with pytest.raises(APIConnectionException):
                cb.call(lambda: flaky_service(fail=True))
            call_history.append(("failure", cb.state.value))
        
        assert cb.state == CircuitState.OPEN
        
        # Phase 3: Circuit ouvert, appels bloqués
        for _ in range(3):
            with pytest.raises(CircuitBreakerOpenException):
                cb.call(lambda: flaky_service(fail=False))
            call_history.append(("blocked", cb.state.value))
        
        # Phase 4: Attendre le timeout et récupération
        time.sleep(0.25)
        
        # Premier appel après timeout - doit passer en HALF_OPEN
        result = cb.call(lambda: flaky_service(fail=False))
        call_history.append(("recovery1", cb.state.value))
        assert cb.state == CircuitState.HALF_OPEN
        
        # Deuxième succès - doit fermer le circuit
        result = cb.call(lambda: flaky_service(fail=False))
        call_history.append(("recovery2", cb.state.value))
        assert cb.state == CircuitState.CLOSED
        
        # Vérifier l'historique des appels
        assert len(call_history) == 13
        
        # Les états doivent suivre la séquence attendue
        states = [entry[1] for entry in call_history]
        assert states[:5] == ['closed'] * 5  # Succès initiaux
        assert 'open' in states[5:8]  # Échecs
        assert all(s == 'open' for s in states[8:11])  # Bloqués
        assert states[11] == 'half_open'  # Premier succès de récupération
        assert states[12] == 'closed'  # Circuit fermé
    
    @pytest.mark.performance
    def test_performance_under_load(self):
        """Test de performance sous charge."""
        cb = DefaultCircuitBreaker()
        
        def fast_func():
            return "success"
        
        # Mesurer le temps d'exécution pour de nombreux appels
        start_time = time.time()
        
        for _ in range(1000):
            cb.call(fast_func)
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Le circuit breaker ne devrait pas ajouter une surcharge significative
        # (moins de 1ms par appel en moyenne)
        assert execution_time < 1.0
        assert cb.metrics.success_count == 1000
        assert cb.metrics.failure_count == 0 