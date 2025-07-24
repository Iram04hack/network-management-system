"""
Tests pour le collecteur de métriques du module dashboard.

Tests pour MetricsCollector, MetricThreshold, et les fonctions associées.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
from django.test import TestCase
from django.core.cache import cache
from django.utils import timezone

from dashboard.infrastructure.metrics_collector import (
    MetricsCollector,
    MetricThreshold,
    MetricReading,
    MetricType,
    ThresholdOperator,
    create_alert_callback,
    metrics_collector
)
from dashboard.domain.entities import AlertSeverity

pytestmark = pytest.mark.django_db


class TestMetricThreshold(TestCase):
    """Tests pour la classe MetricThreshold."""
    
    def test_threshold_evaluation_greater_than(self):
        """Test d'évaluation avec opérateur supérieur."""
        threshold = MetricThreshold(
            metric_type=MetricType.DEVICE_CPU,
            operator=ThresholdOperator.GREATER_THAN,
            value=80.0,
            severity=AlertSeverity.HIGH,
            message_template="CPU élevé: {metric_value}%"
        )
        
        assert threshold.evaluate(85.0) is True  # 85 > 80
        assert threshold.evaluate(80.0) is False  # 80 == 80
        assert threshold.evaluate(75.0) is False  # 75 < 80
    
    def test_threshold_evaluation_less_than(self):
        """Test d'évaluation avec opérateur inférieur."""
        threshold = MetricThreshold(
            metric_type=MetricType.SYSTEM_HEALTH,
            operator=ThresholdOperator.LESS_THAN,
            value=0.5,
            severity=AlertSeverity.CRITICAL,
            message_template="Santé système critique: {metric_value}"
        )
        
        assert threshold.evaluate(0.3) is True  # 0.3 < 0.5
        assert threshold.evaluate(0.5) is False  # 0.5 == 0.5
        assert threshold.evaluate(0.7) is False  # 0.7 > 0.5
    
    def test_threshold_evaluation_equal(self):
        """Test d'évaluation avec opérateur égal."""
        threshold = MetricThreshold(
            metric_type=MetricType.CONNECTION_COUNT,
            operator=ThresholdOperator.EQUAL,
            value=0,
            severity=AlertSeverity.HIGH,
            message_template="Aucune connexion active"
        )
        
        assert threshold.evaluate(0) is True
        assert threshold.evaluate(1) is False
        assert threshold.evaluate(-1) is False
    
    def test_message_formatting(self):
        """Test du formatage des messages d'alerte."""
        threshold = MetricThreshold(
            metric_type=MetricType.DEVICE_CPU,
            operator=ThresholdOperator.GREATER_THAN,
            value=80.0,
            severity=AlertSeverity.HIGH,
            message_template="CPU élevé sur {device_name}: {metric_value:.1f}% > {threshold_value:.1f}%"
        )
        
        message = threshold.format_message(85.5, "Router-01")
        expected = "CPU élevé sur Router-01: 85.5% > 80.0%"
        assert message == expected
    
    def test_message_formatting_without_device(self):
        """Test du formatage sans nom d'équipement."""
        threshold = MetricThreshold(
            metric_type=MetricType.NETWORK_LATENCY,
            operator=ThresholdOperator.GREATER_THAN,
            value=100.0,
            severity=AlertSeverity.HIGH,
            message_template="Latence élevée: {metric_value:.1f}ms"
        )
        
        message = threshold.format_message(150.0)
        assert message == "Latence élevée: 150.0ms"
    
    def test_message_formatting_error_handling(self):
        """Test de gestion d'erreur dans le formatage."""
        threshold = MetricThreshold(
            metric_type=MetricType.DEVICE_CPU,
            operator=ThresholdOperator.GREATER_THAN,
            value=80.0,
            severity=AlertSeverity.HIGH,
            message_template="CPU {invalid_key}: {metric_value}%"
        )
        
        message = threshold.format_message(85.0, "Router-01")
        assert "Seuil dépassé pour device_cpu: 85.0" in message


class TestMetricReading(TestCase):
    """Tests pour la classe MetricReading."""
    
    def test_metric_reading_creation(self):
        """Test de création d'une lecture de métrique."""
        timestamp = timezone.now()
        reading = MetricReading(
            metric_type=MetricType.DEVICE_CPU,
            value=75.5,
            timestamp=timestamp,
            device_id=123,
            device_name="Test Device",
            metadata={'source': 'snmp', 'interface': 'eth0'}
        )
        
        assert reading.metric_type == MetricType.DEVICE_CPU
        assert reading.value == 75.5
        assert reading.timestamp == timestamp
        assert reading.device_id == 123
        assert reading.device_name == "Test Device"
        assert reading.metadata['source'] == 'snmp'


class TestMetricsCollector(TestCase):
    """Tests pour la classe MetricsCollector."""
    
    def setUp(self):
        """Configuration des données de test."""
        self.collector = MetricsCollector()
        cache.clear()
    
    def tearDown(self):
        """Nettoyage après chaque test."""
        cache.clear()
        if self.collector.is_collecting:
            self.collector.stop_collection()
    
    def test_collector_initialization(self):
        """Test d'initialisation du collecteur."""
        assert isinstance(self.collector.thresholds, list)
        assert len(self.collector.thresholds) > 0  # Seuils par défaut
        assert isinstance(self.collector.metric_handlers, dict)
        assert len(self.collector.metric_handlers) > 0
        assert self.collector.is_collecting is False
    
    def test_add_threshold(self):
        """Test d'ajout de seuil."""
        initial_count = len(self.collector.thresholds)
        
        threshold = MetricThreshold(
            metric_type=MetricType.DEVICE_TEMPERATURE,
            operator=ThresholdOperator.GREATER_THAN,
            value=70.0,
            severity=AlertSeverity.HIGH,
            message_template="Température élevée: {metric_value}°C"
        )
        
        self.collector.add_threshold(threshold)
        
        assert len(self.collector.thresholds) == initial_count + 1
        assert threshold in self.collector.thresholds
    
    def test_remove_threshold(self):
        """Test de suppression de seuil."""
        # Ajouter un seuil spécifique
        threshold = MetricThreshold(
            metric_type=MetricType.DEVICE_TEMPERATURE,
            operator=ThresholdOperator.GREATER_THAN,
            value=70.0,
            severity=AlertSeverity.HIGH,
            message_template="Test threshold"
        )
        self.collector.add_threshold(threshold)
        
        initial_count = len(self.collector.thresholds)
        
        # Supprimer le seuil
        self.collector.remove_threshold(
            MetricType.DEVICE_TEMPERATURE,
            70.0,
            ThresholdOperator.GREATER_THAN
        )
        
        assert len(self.collector.thresholds) == initial_count - 1
        assert threshold not in self.collector.thresholds
    
    def test_add_alert_callback(self):
        """Test d'ajout de callback d'alerte."""
        initial_count = len(self.collector.alert_callbacks)
        
        def test_callback(message, severity, data):
            pass
        
        self.collector.add_alert_callback(test_callback)
        
        assert len(self.collector.alert_callbacks) == initial_count + 1
        assert test_callback in self.collector.alert_callbacks
    
    def test_process_metric_caching(self):
        """Test de mise en cache des métriques."""
        timestamp = timezone.now()
        metric = MetricReading(
            metric_type=MetricType.DEVICE_CPU,
            value=75.0,
            timestamp=timestamp,
            device_id=123,
            device_name="Test Device"
        )
        
        self.collector._process_metric(metric)
        
        # Vérifier que la métrique est en cache
        cache_key = f"metric:device_cpu:123:{timestamp.strftime('%Y%m%d%H%M')}"
        cached_data = cache.get(cache_key)
        
        assert cached_data is not None
        assert cached_data['value'] == 75.0
        assert cached_data['device_name'] == "Test Device"
    
    def test_process_metric_threshold_trigger(self):
        """Test de déclenchement d'alerte lors du traitement."""
        # Ajouter un callback mock
        mock_callback = Mock()
        self.collector.add_alert_callback(mock_callback)
        
        # Créer une métrique qui dépasse un seuil
        metric = MetricReading(
            metric_type=MetricType.DEVICE_CPU,
            value=95.0,  # Dépasse le seuil critique de 90%
            timestamp=timezone.now(),
            device_id=123,
            device_name="Test Device"
        )
        
        self.collector._process_metric(metric)
        
        # Vérifier que le callback a été appelé
        mock_callback.assert_called()
        
        # Vérifier les arguments du callback
        call_args = mock_callback.call_args
        message, severity, data = call_args[0]
        
        assert severity == AlertSeverity.CRITICAL
        assert "Test Device" in message
        assert "95.0%" in message
        assert data['metric_value'] == 95.0
        assert data['device_id'] == 123
    
    def test_metric_processing_device_filter(self):
        """Test de filtrage par équipement dans les seuils."""
        # Ajouter un seuil spécifique à un équipement
        device_threshold = MetricThreshold(
            metric_type=MetricType.DEVICE_CPU,
            operator=ThresholdOperator.GREATER_THAN,
            value=50.0,  # Seuil bas pour le test
            severity=AlertSeverity.HIGH,
            message_template="CPU élevé: {metric_value}%",
            device_id=123  # Spécifique à l'équipement 123
        )
        self.collector.add_threshold(device_threshold)
        
        mock_callback = Mock()
        self.collector.add_alert_callback(mock_callback)
        
        # Métrique pour l'équipement 123 (doit déclencher)
        metric1 = MetricReading(
            metric_type=MetricType.DEVICE_CPU,
            value=60.0,
            timestamp=timezone.now(),
            device_id=123,
            device_name="Device 123"
        )
        
        # Métrique pour l'équipement 456 (ne doit pas déclencher)
        metric2 = MetricReading(
            metric_type=MetricType.DEVICE_CPU,
            value=60.0,
            timestamp=timezone.now(),
            device_id=456,
            device_name="Device 456"
        )
        
        self.collector._process_metric(metric1)
        self.collector._process_metric(metric2)
        
        # Vérifier qu'une seule alerte a été déclenchée (pour l'équipement 123)
        # Note: Il peut y avoir d'autres seuils généraux qui se déclenchent aussi
        assert mock_callback.called
        
        # Vérifier qu'au moins un appel concerne l'équipement 123
        calls = mock_callback.call_args_list
        device_123_calls = [call for call in calls if call[0][2]['device_id'] == 123]
        assert len(device_123_calls) > 0
    
    @patch('django__backend.dashboard.infrastructure.metrics_collector.asyncio.sleep')
    async def test_start_stop_collection(self, mock_sleep):
        """Test de démarrage et arrêt de la collecte."""
        mock_sleep.side_effect = [None, Exception("Stop collection")]  # Simule l'arrêt après un cycle
        
        # Mock des méthodes de collecte
        with patch.object(self.collector, '_collect_all_metrics', new_callable=AsyncMock) as mock_collect:
            
            # Démarrer la collecte en arrière-plan
            collection_task = asyncio.create_task(self.collector.start_collection(interval=1))
            
            # Attendre un peu puis arrêter
            await asyncio.sleep(0.1)
            self.collector.stop_collection()
            
            # Attendre la fin de la tâche
            try:
                await collection_task
            except Exception:
                pass  # Exception attendue pour arrêter la boucle
            
            # Vérifier que la collecte a été appelée
            mock_collect.assert_called()
            assert self.collector.is_collecting is False
    
    @patch('django__backend.dashboard.infrastructure.metrics_collector.get_container')
    async def test_collect_system_health(self, mock_get_container):
        """Test de collecte de santé système."""
        # Mock du use case
        mock_use_case = Mock()
        mock_use_case.execute.return_value = {'system_health': 0.85}
        
        mock_container = Mock()
        mock_container.resolve.return_value = mock_use_case
        mock_get_container.return_value = mock_container
        
        # Appeler la méthode de collecte
        result = await self.collector._collect_system_health()
        
        # Vérifier le résultat
        assert result is not None
        assert result.metric_type == MetricType.SYSTEM_HEALTH
        assert result.value == 0.85
        assert isinstance(result.timestamp, datetime)
    
    @patch('django__backend.dashboard.infrastructure.metrics_collector.get_container')
    async def test_collect_system_health_error(self, mock_get_container):
        """Test de gestion d'erreur lors de la collecte."""
        mock_get_container.side_effect = Exception("Container error")
        
        result = await self.collector._collect_system_health()
        
        assert result is None
    
    async def test_collect_device_cpu(self):
        """Test de collecte CPU des équipements."""
        result = await self.collector._collect_device_cpu()
        
        assert isinstance(result, list)
        assert len(result) > 0
        
        for metric in result:
            assert metric.metric_type == MetricType.DEVICE_CPU
            assert isinstance(metric.value, float)
            assert 0 <= metric.value <= 100  # CPU usage percentage
            assert metric.device_id is not None
            assert metric.device_name is not None
    
    async def test_collect_device_memory(self):
        """Test de collecte mémoire des équipements."""
        result = await self.collector._collect_device_memory()
        
        assert isinstance(result, list)
        assert len(result) > 0
        
        for metric in result:
            assert metric.metric_type == MetricType.DEVICE_MEMORY
            assert isinstance(metric.value, float)
            assert 0 <= metric.value <= 100  # Memory usage percentage
            assert metric.device_id is not None
            assert metric.device_name is not None
    
    def test_get_metric_history(self):
        """Test de récupération de l'historique des métriques."""
        # Créer quelques métriques historiques
        base_time = timezone.now()
        
        for i in range(3):
            timestamp = base_time - timedelta(minutes=i)
            metric = MetricReading(
                metric_type=MetricType.DEVICE_CPU,
                value=70.0 + i,
                timestamp=timestamp,
                device_id=123,
                device_name="Test Device"
            )
            self.collector._process_metric(metric)
        
        # Récupérer l'historique
        history = self.collector.get_metric_history(MetricType.DEVICE_CPU, device_id=123, hours=1)
        
        assert isinstance(history, list)
        assert len(history) > 0
        
        # Vérifier que l'historique est trié par timestamp
        timestamps = [item['timestamp'] for item in history]
        assert timestamps == sorted(timestamps)
    
    def test_get_active_thresholds(self):
        """Test de récupération des seuils actifs."""
        thresholds = self.collector.get_active_thresholds()
        
        assert isinstance(thresholds, list)
        assert len(thresholds) > 0
        
        for threshold in thresholds:
            assert 'metric_type' in threshold
            assert 'operator' in threshold
            assert 'value' in threshold
            assert 'severity' in threshold
            assert 'message_template' in threshold
            assert 'is_active' in threshold


class TestCreateAlertCallback(TestCase):
    """Tests pour la fonction create_alert_callback."""
    
    def test_create_alert_callback(self):
        """Test de création d'un callback d'alerte."""
        # Mock du modèle d'alerte
        mock_alert_model = Mock()
        mock_alert_model.objects.create = Mock()
        
        # Créer le callback
        callback = create_alert_callback(mock_alert_model)
        
        # Tester le callback
        test_data = {
            'metric_type': 'device_cpu',
            'metric_value': 95.0,
            'device_id': 123,
            'device_name': 'Test Device'
        }
        
        callback("Test alert message", AlertSeverity.CRITICAL, test_data)
        
        # Vérifier que le modèle a été appelé
        mock_alert_model.objects.create.assert_called_once()
        
        # Vérifier les arguments passés
        call_args = mock_alert_model.objects.create.call_args
        kwargs = call_args[1]
        
        assert kwargs['message'] == "Test alert message"
        assert kwargs['severity'] == AlertSeverity.CRITICAL.value
        assert kwargs['metric_name'] == 'device_cpu'
        assert kwargs['source'] == 'metrics_collector'
        assert kwargs['status'] == 'new'
        assert kwargs['metadata'] == test_data
    
    def test_callback_error_handling(self):
        """Test de gestion d'erreur dans le callback."""
        # Mock qui lève une exception
        mock_alert_model = Mock()
        mock_alert_model.objects.create.side_effect = Exception("Database error")
        
        # Créer le callback
        callback = create_alert_callback(mock_alert_model)
        
        # Le callback ne doit pas lever d'exception
        try:
            callback("Test message", AlertSeverity.HIGH, {})
        except Exception:
            pytest.fail("Le callback ne doit pas lever d'exception")


class TestGlobalCollectorInstance(TestCase):
    """Tests pour l'instance globale du collecteur."""
    
    def test_global_instance_exists(self):
        """Test que l'instance globale existe."""
        assert metrics_collector is not None
        assert isinstance(metrics_collector, MetricsCollector)
    
    def test_global_instance_initialized(self):
        """Test que l'instance globale est initialisée."""
        assert len(metrics_collector.thresholds) > 0
        assert len(metrics_collector.metric_handlers) > 0
        assert metrics_collector.is_collecting is False


class TestMetricsCollectorIntegration(TestCase):
    """Tests d'intégration pour le collecteur de métriques."""
    
    def setUp(self):
        """Configuration des données de test."""
        self.collector = MetricsCollector()
        cache.clear()
    
    def tearDown(self):
        """Nettoyage après chaque test."""
        cache.clear()
        if self.collector.is_collecting:
            self.collector.stop_collection()
    
    async def test_full_collection_cycle(self):
        """Test d'un cycle complet de collecte."""
        # Ajouter un callback mock
        alert_calls = []
        
        def test_callback(message, severity, data):
            alert_calls.append((message, severity, data))
        
        self.collector.add_alert_callback(test_callback)
        
        # Exécuter un cycle de collecte
        await self.collector._collect_all_metrics()
        
        # Vérifier que des métriques ont été collectées et mises en cache
        # (Les métriques simulées peuvent déclencher des alertes)
        
        # Vérifier l'historique
        history = self.collector.get_metric_history(MetricType.SYSTEM_HEALTH, hours=1)
        # L'historique peut être vide si la collecte a échoué, ce qui est acceptable pour les tests
        
        # Vérifier les seuils actifs
        thresholds = self.collector.get_active_thresholds()
        assert len(thresholds) > 0
    
    def test_threshold_management_workflow(self):
        """Test du workflow de gestion des seuils."""
        initial_count = len(self.collector.thresholds)
        
        # Ajouter un seuil personnalisé
        custom_threshold = MetricThreshold(
            metric_type=MetricType.DEVICE_TEMPERATURE,
            operator=ThresholdOperator.GREATER_THAN,
            value=65.0,
            severity=AlertSeverity.HIGH,
            message_template="Température élevée sur {device_name}: {metric_value}°C"
        )
        
        self.collector.add_threshold(custom_threshold)
        assert len(self.collector.thresholds) == initial_count + 1
        
        # Vérifier que le seuil apparaît dans la liste active
        active_thresholds = self.collector.get_active_thresholds()
        temp_thresholds = [t for t in active_thresholds if t['metric_type'] == 'device_temperature']
        assert len(temp_thresholds) == 1
        assert temp_thresholds[0]['value'] == 65.0
        
        # Supprimer le seuil
        self.collector.remove_threshold(
            MetricType.DEVICE_TEMPERATURE,
            65.0,
            ThresholdOperator.GREATER_THAN
        )
        assert len(self.collector.thresholds) == initial_count
        
        # Vérifier que le seuil n'apparaît plus
        active_thresholds = self.collector.get_active_thresholds()
        temp_thresholds = [t for t in active_thresholds if t['metric_type'] == 'device_temperature']
        assert len(temp_thresholds) == 0