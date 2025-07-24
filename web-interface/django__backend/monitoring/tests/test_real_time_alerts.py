"""
Tests pour le système d'alertes temps réel du module monitoring.
"""

import unittest
import asyncio
from unittest.mock import patch, MagicMock, Mock, AsyncMock
from datetime import datetime, timezone, timedelta
from django.test import TestCase, TransactionTestCase
from django.contrib.auth import get_user_model
from channels.testing import WebsocketCommunicator
from channels.db import database_sync_to_async
import json

from ..models import (
    Alert, 
    MetricsDefinition, 
    DeviceMetric, 
    MetricValue,
    ServiceCheck,
    DeviceServiceCheck,
    CheckResult,
    Notification,
    NotificationChannel
)
from ..tasks.metrics_tasks import collect_device_metrics
from ..consumers import MonitoringConsumer
from ..infrastructure.adapters.prometheus_adapter import PrometheusAdapter

User = get_user_model()


class RealTimeAlertsTest(TestCase):
    """
    Tests pour le système d'alertes temps réel.
    """
    
    def setUp(self):
        """
        Initialisation des données de test.
        """
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="password"
        )
        
        # Créer des définitions de métriques avec seuils d'alerte
        self.cpu_metric_def = MetricsDefinition.objects.create(
            name="CPU Usage",
            description="CPU usage percentage",
            metric_type="gauge",
            unit="%",
            collection_method="prometheus",
            collection_config={
                "query": "cpu_usage{instance=\"$instance\"}",
                "thresholds": {
                    "warning": 70.0,
                    "critical": 90.0
                }
            },
            category="system"
        )
        
        self.memory_metric_def = MetricsDefinition.objects.create(
            name="Memory Usage",
            description="Memory usage percentage",
            metric_type="gauge",
            unit="%",
            collection_method="prometheus",
            collection_config={
                "query": "memory_usage{instance=\"$instance\"}",
                "thresholds": {
                    "warning": 80.0,
                    "critical": 95.0
                }
            },
            category="system"
        )
        
        # Créer des métriques d'équipement
        self.device_cpu_metric = DeviceMetric.objects.create(
            device_id=1,
            metric=self.cpu_metric_def,
            name="Server CPU Usage",
            is_active=True
        )
        
        self.device_memory_metric = DeviceMetric.objects.create(
            device_id=1,
            metric=self.memory_metric_def,
            name="Server Memory Usage",
            is_active=True
        )
        
        # Créer un canal de notification
        self.notification_channel = NotificationChannel.objects.create(
            name="Email Alerts",
            channel_type="email",
            config={"smtp_server": "localhost", "port": 587},
            is_active=True
        )
    
    def test_create_alert_from_metric_threshold(self):
        """
        Test de création d'alerte à partir d'un seuil de métrique dépassé.
        """
        # Créer une valeur de métrique dépassant le seuil critique
        high_cpu_value = MetricValue.objects.create(
            device_metric=self.device_cpu_metric,
            value=95.5,  # Dépasse le seuil critique de 90%
            timestamp=datetime.now(timezone.utc)
        )
        
        # Simuler la logique de détection d'alerte
        threshold_config = self.cpu_metric_def.collection_config.get('thresholds', {})
        critical_threshold = threshold_config.get('critical', 100)
        
        if high_cpu_value.value >= critical_threshold:
            alert = Alert.objects.create(
                title=f"Critical CPU Usage - Device {self.device_cpu_metric.device_id}",
                description=f"CPU usage is {high_cpu_value.value}% (threshold: {critical_threshold}%)",
                severity="critical",
                status="active",
                source_type="metric",
                source_id=self.device_cpu_metric.id,
                details={
                    "metric_name": self.cpu_metric_def.name,
                    "current_value": high_cpu_value.value,
                    "threshold": critical_threshold,
                    "device_id": self.device_cpu_metric.device_id,
                    "timestamp": high_cpu_value.timestamp.isoformat()
                }
            )
        
        # Vérifications
        self.assertEqual(Alert.objects.count(), 1)
        created_alert = Alert.objects.first()
        self.assertEqual(created_alert.severity, "critical")
        self.assertEqual(created_alert.status, "active")
        self.assertEqual(created_alert.source_type, "metric")
        self.assertEqual(created_alert.source_id, self.device_cpu_metric.id)
        self.assertIn("95.5%", created_alert.description)
    
    def test_alert_severity_levels(self):
        """
        Test des différents niveaux de sévérité d'alerte.
        """
        threshold_config = self.memory_metric_def.collection_config.get('thresholds', {})
        warning_threshold = threshold_config.get('warning', 80)
        critical_threshold = threshold_config.get('critical', 95)
        
        # Test alerte Warning
        warning_value = MetricValue.objects.create(
            device_metric=self.device_memory_metric,
            value=85.0,  # Entre warning (80) et critical (95)
            timestamp=datetime.now(timezone.utc)
        )
        
        if warning_threshold <= warning_value.value < critical_threshold:
            Alert.objects.create(
                title="Warning Memory Usage",
                severity="warning",
                status="active",
                source_type="metric",
                source_id=self.device_memory_metric.id
            )
        
        # Test alerte Critical
        critical_value = MetricValue.objects.create(
            device_metric=self.device_memory_metric,
            value=97.0,  # Dépasse critical (95)
            timestamp=datetime.now(timezone.utc)
        )
        
        if critical_value.value >= critical_threshold:
            Alert.objects.create(
                title="Critical Memory Usage",
                severity="critical",
                status="active",
                source_type="metric",
                source_id=self.device_memory_metric.id
            )
        
        # Vérifications
        self.assertEqual(Alert.objects.count(), 2)
        
        warning_alert = Alert.objects.filter(severity="warning").first()
        critical_alert = Alert.objects.filter(severity="critical").first()
        
        self.assertIsNotNone(warning_alert)
        self.assertIsNotNone(critical_alert)
        self.assertEqual(warning_alert.title, "Warning Memory Usage")
        self.assertEqual(critical_alert.title, "Critical Memory Usage")
    
    def test_alert_auto_resolution(self):
        """
        Test de résolution automatique d'alerte.
        """
        # Créer une alerte active
        alert = Alert.objects.create(
            title="High CPU Usage",
            severity="warning",
            status="active",
            source_type="metric",
            source_id=self.device_cpu_metric.id
        )
        
        # Créer une nouvelle valeur en dessous du seuil
        normal_value = MetricValue.objects.create(
            device_metric=self.device_cpu_metric,
            value=45.0,  # En dessous du seuil warning (70%)
            timestamp=datetime.now(timezone.utc)
        )
        
        # Simuler la logique de résolution automatique
        threshold_config = self.cpu_metric_def.collection_config.get('thresholds', {})
        warning_threshold = threshold_config.get('warning', 70)
        
        if normal_value.value < warning_threshold:
            alert.status = "resolved"
            alert.resolved_at = datetime.now(timezone.utc)
            alert.details.update({
                "resolution_reason": "Metric returned to normal levels",
                "final_value": normal_value.value,
                "resolution_timestamp": alert.resolved_at.isoformat()
            })
            alert.save()
        
        # Vérifications
        updated_alert = Alert.objects.get(id=alert.id)
        self.assertEqual(updated_alert.status, "resolved")
        self.assertIsNotNone(updated_alert.resolved_at)
        self.assertIn("normal levels", updated_alert.details["resolution_reason"])
    
    def test_alert_notification_creation(self):
        """
        Test de création de notification lors d'une alerte.
        """
        # Créer une alerte critique
        alert = Alert.objects.create(
            title="Critical System Alert",
            description="System requires immediate attention",
            severity="critical",
            status="active",
            source_type="metric",
            source_id=self.device_cpu_metric.id
        )
        
        # Créer une notification pour cette alerte
        notification = Notification.objects.create(
            channel=self.notification_channel,
            subject=f"CRITICAL ALERT: {alert.title}",
            message=f"""
            Alert Details:
            - Title: {alert.title}
            - Severity: {alert.severity.upper()}
            - Description: {alert.description}
            - Created: {alert.created_at.strftime('%Y-%m-%d %H:%M:%S UTC')}
            - Device ID: {self.device_cpu_metric.device_id}
            
            Please investigate immediately.
            """,
            recipients=["admin@example.com", "ops@example.com"],
            user_recipients=[self.user.id],
            status="pending",
            alert_id=alert.id,
            details={
                "alert_severity": alert.severity,
                "alert_source": alert.source_type,
                "notification_type": "alert_creation"
            }
        )
        
        # Vérifications
        self.assertEqual(Notification.objects.count(), 1)
        created_notification = Notification.objects.first()
        self.assertEqual(created_notification.alert_id, alert.id)
        self.assertIn("CRITICAL ALERT", created_notification.subject)
        self.assertEqual(created_notification.status, "pending")
        self.assertEqual(len(created_notification.recipients), 2)
        self.assertIn(self.user.id, created_notification.user_recipients)
    
    @patch('monitoring.infrastructure.adapters.prometheus_adapter.PrometheusAdapter.collect_system_metrics')
    def test_real_time_metric_collection_with_alerts(self, mock_collect):
        """
        Test de collecte de métriques en temps réel avec génération d'alertes.
        """
        # Configuration du mock pour retourner des valeurs critiques
        mock_collect.return_value = {
            'success': True,
            'metrics': {
                'cpu_usage': 92.5,    # Dépasse le seuil critique (90%)
                'memory_usage': 97.8,  # Dépasse le seuil critique (95%)
                'disk_usage': 45.2,
                'network_in': 1024000,
                'network_out': 2048000
            },
            'instance': 'localhost:9100',
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        # Simuler la collecte de métriques
        adapter = PrometheusAdapter()
        result = adapter.collect_system_metrics('localhost:9100')
        
        # Vérifications de la collecte
        self.assertTrue(result['success'])
        metrics = result['metrics']
        
        # Créer les valeurs de métriques
        cpu_value = MetricValue.objects.create(
            device_metric=self.device_cpu_metric,
            value=metrics['cpu_usage'],
            timestamp=datetime.now(timezone.utc)
        )
        
        memory_value = MetricValue.objects.create(
            device_metric=self.device_memory_metric,
            value=metrics['memory_usage'],
            timestamp=datetime.now(timezone.utc)
        )
        
        # Simuler la logique de détection d'alertes
        alerts_created = []
        
        # Vérification CPU
        cpu_thresholds = self.cpu_metric_def.collection_config.get('thresholds', {})
        if cpu_value.value >= cpu_thresholds.get('critical', 100):
            cpu_alert = Alert.objects.create(
                title=f"Critical CPU Usage - {cpu_value.value}%",
                severity="critical",
                status="active",
                source_type="metric",
                source_id=self.device_cpu_metric.id
            )
            alerts_created.append(cpu_alert)
        
        # Vérification Memory
        memory_thresholds = self.memory_metric_def.collection_config.get('thresholds', {})
        if memory_value.value >= memory_thresholds.get('critical', 100):
            memory_alert = Alert.objects.create(
                title=f"Critical Memory Usage - {memory_value.value}%",
                severity="critical",
                status="active",
                source_type="metric",
                source_id=self.device_memory_metric.id
            )
            alerts_created.append(memory_alert)
        
        # Vérifications
        self.assertEqual(len(alerts_created), 2)
        self.assertEqual(Alert.objects.count(), 2)
        
        cpu_alert = Alert.objects.filter(title__contains="CPU").first()
        memory_alert = Alert.objects.filter(title__contains="Memory").first()
        
        self.assertIsNotNone(cpu_alert)
        self.assertIsNotNone(memory_alert)
        self.assertEqual(cpu_alert.severity, "critical")
        self.assertEqual(memory_alert.severity, "critical")


class ServiceCheckAlertsTest(TestCase):
    """
    Tests pour les alertes basées sur les vérifications de service.
    """
    
    def setUp(self):
        """
        Initialisation des données de test.
        """
        # Créer des vérifications de service
        self.ping_check = ServiceCheck.objects.create(
            name="Ping Check",
            description="Check if host responds to ping",
            check_type="ping",
            check_config={"timeout": 5, "count": 3},
            category="network",
            enabled=True
        )
        
        self.http_check = ServiceCheck.objects.create(
            name="HTTP Check",
            description="Check if HTTP service is responding",
            check_type="http",
            check_config={"url": "http://example.com", "timeout": 10},
            category="web",
            enabled=True
        )
        
        # Créer des vérifications d'équipement
        self.device_ping_check = DeviceServiceCheck.objects.create(
            device_id=1,
            service_check=self.ping_check,
            name="Server Ping Check",
            check_interval=60,
            is_active=True
        )
        
        self.device_http_check = DeviceServiceCheck.objects.create(
            device_id=1,
            service_check=self.http_check,
            name="Server HTTP Check",
            check_interval=300,
            is_active=True
        )
    
    def test_service_failure_alert_creation(self):
        """
        Test de création d'alerte lors d'un échec de service.
        """
        # Créer un résultat de vérification en échec
        failed_result = CheckResult.objects.create(
            device_service_check=self.device_ping_check,
            status="critical",
            execution_time=5.0,
            message="Host is not reachable - 100% packet loss",
            details={
                "packets_sent": 3,
                "packets_received": 0,
                "packet_loss": 100,
                "error": "Request timeout"
            },
            timestamp=datetime.now(timezone.utc)
        )
        
        # Simuler la logique de création d'alerte pour échec de service
        if failed_result.status in ["critical", "error"]:
            alert = Alert.objects.create(
                title=f"Service Check Failed - {self.device_ping_check.name}",
                description=f"Service check '{self.ping_check.name}' failed: {failed_result.message}",
                severity="critical" if failed_result.status == "critical" else "warning",
                status="active",
                source_type="service_check",
                source_id=self.device_ping_check.id,
                details={
                    "check_type": self.ping_check.check_type,
                    "check_result_id": failed_result.id,
                    "execution_time": failed_result.execution_time,
                    "device_id": self.device_ping_check.device_id,
                    "failure_details": failed_result.details
                }
            )
        
        # Vérifications
        self.assertEqual(Alert.objects.count(), 1)
        created_alert = Alert.objects.first()
        self.assertEqual(created_alert.severity, "critical")
        self.assertEqual(created_alert.source_type, "service_check")
        self.assertIn("not reachable", created_alert.description)
        self.assertEqual(created_alert.details["check_type"], "ping")
    
    def test_service_recovery_alert_resolution(self):
        """
        Test de résolution d'alerte lors de la récupération d'un service.
        """
        # Créer une alerte existante pour un service en panne
        service_alert = Alert.objects.create(
            title="HTTP Service Down",
            severity="critical",
            status="active",
            source_type="service_check",
            source_id=self.device_http_check.id
        )
        
        # Créer un résultat de vérification réussi
        recovery_result = CheckResult.objects.create(
            device_service_check=self.device_http_check,
            status="ok",
            execution_time=0.85,
            message="HTTP service is responding normally",
            details={
                "http_status": 200,
                "response_time": 0.85,
                "content_length": 1024
            },
            timestamp=datetime.now(timezone.utc)
        )
        
        # Simuler la logique de résolution d'alerte
        if recovery_result.status == "ok":
            service_alert.status = "resolved"
            service_alert.resolved_at = datetime.now(timezone.utc)
            service_alert.details.update({
                "resolution_reason": "Service check returned to normal",
                "recovery_result_id": recovery_result.id,
                "recovery_timestamp": service_alert.resolved_at.isoformat()
            })
            service_alert.save()
        
        # Vérifications
        updated_alert = Alert.objects.get(id=service_alert.id)
        self.assertEqual(updated_alert.status, "resolved")
        self.assertIsNotNone(updated_alert.resolved_at)
        self.assertIn("normal", updated_alert.details["resolution_reason"])
    
    def test_multiple_consecutive_failures(self):
        """
        Test de gestion de multiples échecs consécutifs.
        """
        # Créer plusieurs résultats d'échec consécutifs
        failure_timestamps = [
            datetime.now(timezone.utc) - timedelta(minutes=15),
            datetime.now(timezone.utc) - timedelta(minutes=10),
            datetime.now(timezone.utc) - timedelta(minutes=5),
            datetime.now(timezone.utc)
        ]
        
        failure_results = []
        for i, timestamp in enumerate(failure_timestamps):
            result = CheckResult.objects.create(
                device_service_check=self.device_ping_check,
                status="critical",
                execution_time=5.0,
                message=f"Ping failed - attempt {i+1}",
                details={"attempt": i+1, "packet_loss": 100},
                timestamp=timestamp
            )
            failure_results.append(result)
        
        # Simuler la logique de gestion des échecs multiples
        recent_failures = CheckResult.objects.filter(
            device_service_check=self.device_ping_check,
            status="critical",
            timestamp__gte=datetime.now(timezone.utc) - timedelta(minutes=20)
        ).count()
        
        # Créer une alerte escaladée si plus de 3 échecs
        if recent_failures >= 3:
            escalated_alert = Alert.objects.create(
                title=f"Persistent Service Failure - {self.device_ping_check.name}",
                description=f"Service has failed {recent_failures} consecutive times in the last 20 minutes",
                severity="critical",
                status="active",
                source_type="service_check",
                source_id=self.device_ping_check.id,
                details={
                    "consecutive_failures": recent_failures,
                    "escalation_reason": "Multiple consecutive failures",
                    "time_window": "20 minutes",
                    "requires_immediate_attention": True
                }
            )
        
        # Vérifications
        self.assertEqual(recent_failures, 4)
        self.assertEqual(Alert.objects.count(), 1)
        
        escalated_alert = Alert.objects.first()
        self.assertEqual(escalated_alert.severity, "critical")
        self.assertIn("Persistent", escalated_alert.title)
        self.assertTrue(escalated_alert.details["requires_immediate_attention"])
        self.assertEqual(escalated_alert.details["consecutive_failures"], 4)


class WebSocketAlertsTest(TransactionTestCase):
    """
    Tests pour les alertes en temps réel via WebSocket.
    """
    
    async def test_websocket_alert_notification(self):
        """
        Test de notification d'alerte via WebSocket.
        """
        # Créer un utilisateur
        user = await database_sync_to_async(User.objects.create_user)(
            username="wsuser",
            password="password"
        )
        
        # Simuler une connexion WebSocket
        communicator = WebsocketCommunicator(
            MonitoringConsumer.as_asgi(),
            "/ws/monitoring/"
        )
        
        connected, subprotocol = await communicator.connect()
        self.assertTrue(connected)
        
        # Créer une alerte
        alert_data = {
            'type': 'alert_created',
            'alert': {
                'id': 1,
                'title': 'Critical System Alert',
                'severity': 'critical',
                'status': 'active',
                'created_at': datetime.now(timezone.utc).isoformat(),
                'description': 'System requires immediate attention'
            }
        }
        
        # Envoyer l'alerte via WebSocket
        await communicator.send_json_to(alert_data)
        
        # Vérifier la réception
        response = await communicator.receive_json_from()
        
        # Vérifications
        self.assertEqual(response['type'], 'alert_created')
        self.assertEqual(response['alert']['title'], 'Critical System Alert')
        self.assertEqual(response['alert']['severity'], 'critical')
        
        await communicator.disconnect()
    
    async def test_websocket_metric_update(self):
        """
        Test de mise à jour de métrique via WebSocket.
        """
        communicator = WebsocketCommunicator(
            MonitoringConsumer.as_asgi(),
            "/ws/monitoring/"
        )
        
        connected, subprotocol = await communicator.connect()
        self.assertTrue(connected)
        
        # Simuler une mise à jour de métrique
        metric_update = {
            'type': 'metric_update',
            'metric': {
                'device_id': 1,
                'metric_name': 'CPU Usage',
                'value': 85.5,
                'unit': '%',
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'status': 'warning'  # Dépasse un seuil
            }
        }
        
        # Envoyer la mise à jour
        await communicator.send_json_to(metric_update)
        
        # Vérifier la réception
        response = await communicator.receive_json_from()
        
        # Vérifications
        self.assertEqual(response['type'], 'metric_update')
        self.assertEqual(response['metric']['device_id'], 1)
        self.assertEqual(response['metric']['value'], 85.5)
        self.assertEqual(response['metric']['status'], 'warning')
        
        await communicator.disconnect()


if __name__ == '__main__':
    unittest.main()