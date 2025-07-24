"""
Tests unitaires pour les repositories du module monitoring.
"""

import unittest
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock
from django.test import TestCase
from django.contrib.auth import get_user_model

from ..models import (
    Alert, 
    MetricsDefinition, 
    DeviceMetric, 
    MetricValue,
    ServiceCheck,
    DeviceServiceCheck,
    CheckResult,
    Dashboard,
    DashboardWidget,
    Notification,
    NotificationChannel
)
from ..infrastructure.repositories import (
    AlertRepository,
    MetricsDefinitionRepository,
    DeviceMetricRepository,
    MetricValueRepository,
    ServiceCheckRepository,
    DeviceServiceCheckRepository,
    CheckResultRepository,
    DashboardRepository,
    NotificationRepository
)

User = get_user_model()


class AlertRepositoryTest(TestCase):
    """Tests pour le repository des alertes."""
    
    def setUp(self):
        """Initialisation des données de test."""
        self.repository = AlertRepository()
        
        # Créer une alerte de test
        self.alert = Alert.objects.create(
            title="Test Alert",
            description="This is a test alert",
            severity="high",
            status="active",
            source_type="metric",
            source_id=1
        )
    
    def test_get_by_id(self):
        """Test de la méthode get_by_id."""
        alert = self.repository.get_by_id(self.alert.id)
        self.assertIsNotNone(alert)
        self.assertEqual(alert.title, "Test Alert")
    
    def test_list_all(self):
        """Test de la méthode list_all."""
        alerts = self.repository.list_all()
        self.assertEqual(len(alerts), 1)
        self.assertEqual(alerts[0].id, self.alert.id)
    
    def test_create(self):
        """Test de la méthode create."""
        new_alert = self.repository.create(
            title="New Alert",
            description="This is a new alert",
            severity="medium",
            status="active",
            source_type="service_check",
            source_id=2
        )
        
        self.assertIsNotNone(new_alert)
        self.assertEqual(new_alert.title, "New Alert")
        self.assertEqual(new_alert.severity, "medium")
        
        # Vérifier que l'alerte a bien été créée en base
        alerts = Alert.objects.all()
        self.assertEqual(len(alerts), 2)
    
    def test_update(self):
        """Test de la méthode update."""
        updated_alert = self.repository.update(
            self.alert.id,
            title="Updated Alert",
            severity="critical"
        )
        
        self.assertEqual(updated_alert.title, "Updated Alert")
        self.assertEqual(updated_alert.severity, "critical")
        self.assertEqual(updated_alert.description, "This is a test alert")  # Non modifié
        
        # Vérifier que l'alerte a bien été mise à jour en base
        alert = Alert.objects.get(id=self.alert.id)
        self.assertEqual(alert.title, "Updated Alert")
    
    def test_update_status(self):
        """Test de la méthode update_status."""
        user = User.objects.create_user(username="testuser", password="password")
        
        updated_alert = self.repository.update_status(
            self.alert.id,
            status="acknowledged",
            user_id=user.id,
            comment="Acknowledging this alert"
        )
        
        self.assertEqual(updated_alert.status, "acknowledged")
        self.assertEqual(updated_alert.acknowledged_by_id, user.id)
        self.assertIsNotNone(updated_alert.acknowledged_at)
        
        # Vérifier que l'alerte a bien été mise à jour en base
        alert = Alert.objects.get(id=self.alert.id)
        self.assertEqual(alert.status, "acknowledged")
    
    def test_delete(self):
        """Test de la méthode delete."""
        result = self.repository.delete(self.alert.id)
        self.assertTrue(result)
        
        # Vérifier que l'alerte a bien été supprimée en base
        with self.assertRaises(Alert.DoesNotExist):
            Alert.objects.get(id=self.alert.id)


class MetricsRepositoryTest(TestCase):
    """Tests pour les repositories liés aux métriques."""
    
    def setUp(self):
        """Initialisation des données de test."""
        self.metrics_definition_repository = MetricsDefinitionRepository()
        self.device_metric_repository = DeviceMetricRepository()
        self.metric_value_repository = MetricValueRepository()
        
        # Créer une définition de métrique
        self.metric_def = MetricsDefinition.objects.create(
            name="CPU Usage",
            description="CPU usage in percentage",
            metric_type="gauge",
            unit="%",
            collection_method="snmp",
            collection_config={"oid": "1.3.6.1.4.1.2021.11.9.0"}
        )
        
        # Créer une métrique d'équipement
        self.device_metric = DeviceMetric.objects.create(
            device_id=1,  # Supposons qu'un équipement avec cet ID existe
            metric=self.metric_def,
            name="Server CPU Usage",
            is_active=True
        )
        
        # Créer quelques valeurs de métrique
        self.metric_value1 = MetricValue.objects.create(
            device_metric=self.device_metric,
            value=45.5,
            timestamp=datetime.now(timezone.utc) - timedelta(hours=1)
        )
        
        self.metric_value2 = MetricValue.objects.create(
            device_metric=self.device_metric,
            value=50.2,
            timestamp=datetime.now(timezone.utc)
        )
    
    def test_metrics_definition_repository(self):
        """Test du repository MetricsDefinitionRepository."""
        # Test get_by_id
        metric_def = self.metrics_definition_repository.get_by_id(self.metric_def.id)
        self.assertEqual(metric_def.name, "CPU Usage")
        
        # Test create_metrics_definition
        new_metric_def = self.metrics_definition_repository.create_metrics_definition(
            name="Memory Usage",
            description="Memory usage in percentage",
            metric_type="gauge",
            unit="%",
            collection_method="snmp",
            collection_config={"oid": "1.3.6.1.4.1.2021.4.5.0"},
            category="memory"
        )
        
        self.assertEqual(new_metric_def.name, "Memory Usage")
        self.assertEqual(new_metric_def.category, "memory")
        
        # Test get_by_collection_method
        snmp_metrics = self.metrics_definition_repository.get_by_collection_method("snmp")
        self.assertEqual(len(snmp_metrics), 2)
        
        # Test get_by_category
        memory_metrics = self.metrics_definition_repository.get_by_category("memory")
        self.assertEqual(len(memory_metrics), 1)
        self.assertEqual(memory_metrics[0].name, "Memory Usage")
    
    def test_device_metric_repository(self):
        """Test du repository DeviceMetricRepository."""
        # Test get_by_id
        device_metric = self.device_metric_repository.get_by_id(self.device_metric.id)
        self.assertEqual(device_metric.name, "Server CPU Usage")
        
        # Test create_device_metric
        new_device_metric = self.device_metric_repository.create_device_metric(
            device_id=1,
            metric_id=self.metric_def.id,
            name="Custom CPU Metric",
            is_active=True
        )
        
        self.assertEqual(new_device_metric.name, "Custom CPU Metric")
        
        # Test get_by_device
        device_metrics = self.device_metric_repository.get_by_device(1)
        self.assertEqual(len(device_metrics), 2)
        
        # Test update_collection_status
        updated_metric = self.device_metric_repository.update_collection_status(
            self.device_metric.id,
            success=True,
            last_value=55.3,
            message="Collection successful"
        )
        
        self.assertEqual(updated_metric.last_value, 55.3)
        self.assertTrue(updated_metric.last_collection_success)
        self.assertEqual(updated_metric.last_collection_message, "Collection successful")
    
    def test_metric_value_repository(self):
        """Test du repository MetricValueRepository."""
        # Test create_metric_value
        new_value = self.metric_value_repository.create_metric_value(
            device_metric_id=self.device_metric.id,
            value=60.1
        )
        
        self.assertEqual(new_value.value, 60.1)
        
        # Test get_values_for_device_metric
        values = self.metric_value_repository.get_values_for_device_metric(
            self.device_metric.id,
            start_time=datetime.now(timezone.utc) - timedelta(hours=2)
        )
        
        self.assertEqual(len(values), 3)
        
        # Test get_latest_value
        latest = self.metric_value_repository.get_latest_value(self.device_metric.id)
        self.assertIsNotNone(latest)
        
        # Test batch_create
        batch_values = [
            {"device_metric_id": self.device_metric.id, "value": 65.2},
            {"device_metric_id": self.device_metric.id, "value": 70.5}
        ]
        
        created_values = self.metric_value_repository.batch_create(batch_values)
        self.assertEqual(len(created_values), 2)
        
        # Vérifier que les valeurs ont bien été créées
        all_values = MetricValue.objects.filter(device_metric_id=self.device_metric.id)
        self.assertEqual(all_values.count(), 5)


class ServiceCheckRepositoryTest(TestCase):
    """Tests pour les repositories liés aux vérifications de service."""
    
    def setUp(self):
        """Initialisation des données de test."""
        self.service_check_repository = ServiceCheckRepository()
        self.device_service_check_repository = DeviceServiceCheckRepository()
        self.check_result_repository = CheckResultRepository()
        
        # Créer une vérification de service
        self.service_check = ServiceCheck.objects.create(
            name="Ping Check",
            description="Check if host responds to ping",
            check_type="ping",
            check_config={"count": 4, "timeout": 2},
            category="network",
            enabled=True
        )
        
        # Créer une vérification de service d'équipement
        self.device_check = DeviceServiceCheck.objects.create(
            device_id=1,  # Supposons qu'un équipement avec cet ID existe
            service_check=self.service_check,
            name="Server Ping Check",
            check_interval=300,
            is_active=True
        )
        
        # Créer un résultat de vérification
        self.check_result = CheckResult.objects.create(
            device_service_check=self.device_check,
            status="ok",
            execution_time=0.05,
            message="Host is reachable",
            details={"packets_sent": 4, "packets_received": 4},
            timestamp=datetime.now(timezone.utc)
        )
    
    def test_service_check_repository(self):
        """Test du repository ServiceCheckRepository."""
        # Test get_by_id
        service_check = self.service_check_repository.get_by_id(self.service_check.id)
        self.assertEqual(service_check.name, "Ping Check")
        
        # Test create_service_check
        new_service_check = self.service_check_repository.create_service_check(
            name="HTTP Check",
            description="Check if HTTP service is running",
            check_type="http",
            check_config={"url": "http://example.com", "timeout": 5},
            category="web",
            compatible_device_types=["server", "router"],
            enabled=True
        )
        
        self.assertEqual(new_service_check.name, "HTTP Check")
        self.assertEqual(new_service_check.check_type, "http")
        
        # Test get_by_check_type
        ping_checks = self.service_check_repository.get_by_check_type("ping")
        self.assertEqual(len(ping_checks), 1)
        self.assertEqual(ping_checks[0].name, "Ping Check")
        
        # Test get_by_category
        web_checks = self.service_check_repository.get_by_category("web")
        self.assertEqual(len(web_checks), 1)
        self.assertEqual(web_checks[0].name, "HTTP Check")
        
        # Test update_check_config
        updated_check = self.service_check_repository.update_check_config(
            self.service_check.id,
            {"count": 5, "interval": 1}
        )
        
        self.assertEqual(updated_check.check_config["count"], 5)
        self.assertEqual(updated_check.check_config["interval"], 1)
        self.assertEqual(updated_check.check_config["timeout"], 2)  # Valeur conservée
    
    def test_device_service_check_repository(self):
        """Test du repository DeviceServiceCheckRepository."""
        # Test get_by_id
        device_check = self.device_service_check_repository.get_by_id(self.device_check.id)
        self.assertEqual(device_check.name, "Server Ping Check")
        
        # Test create_device_service_check
        new_device_check = self.device_service_check_repository.create_device_service_check(
            device_id=1,
            service_check_id=self.service_check.id,
            name="Custom Ping Check",
            check_interval=600,
            is_active=True
        )
        
        self.assertEqual(new_device_check.name, "Custom Ping Check")
        self.assertEqual(new_device_check.check_interval, 600)
        
        # Test get_by_device
        device_checks = self.device_service_check_repository.get_by_device(1)
        self.assertEqual(len(device_checks), 2)
        
        # Test update_check_status
        updated_check = self.device_service_check_repository.update_check_status(
            self.device_check.id,
            last_status="warning",
            message="High latency detected"
        )
        
        self.assertEqual(updated_check.last_status, "warning")
        self.assertEqual(updated_check.last_message, "High latency detected")
    
    def test_check_result_repository(self):
        """Test du repository CheckResultRepository."""
        # Test get_by_id
        check_result = self.check_result_repository.get_by_id(self.check_result.id)
        self.assertEqual(check_result.status, "ok")
        
        # Test create_check_result
        new_result = self.check_result_repository.create_check_result(
            device_service_check_id=self.device_check.id,
            status="warning",
            execution_time=0.08,
            message="High latency",
            details={"latency": 150}
        )
        
        self.assertEqual(new_result.status, "warning")
        self.assertEqual(new_result.message, "High latency")
        
        # Test get_results_for_device_check
        results = self.check_result_repository.get_results_for_device_check(self.device_check.id)
        self.assertEqual(len(results), 2)
        
        # Test get_latest_result
        latest = self.check_result_repository.get_latest_result(self.device_check.id)
        self.assertIsNotNone(latest)
        self.assertEqual(latest.status, "warning")
        
        # Test get_results_by_status
        warning_results = self.check_result_repository.get_results_by_status("warning")
        self.assertEqual(len(warning_results), 1)
        self.assertEqual(warning_results[0].message, "High latency")


class DashboardRepositoryTest(TestCase):
    """Tests pour le repository des tableaux de bord."""
    
    def setUp(self):
        """Initialisation des données de test."""
        self.repository = DashboardRepository()
        self.user = User.objects.create_user(username="testuser", password="password")
        
        # Créer un tableau de bord de test
        self.dashboard = self.repository.create_dashboard(
            title="Test Dashboard",
            description="This is a test dashboard",
            owner_id=self.user.id,
            is_public=True,
            is_default=True
        )
    
    def test_get_by_id(self):
        """Test de la méthode get_by_id."""
        dashboard = self.repository.get_by_id(self.dashboard.id)
        self.assertIsNotNone(dashboard)
        self.assertEqual(dashboard.title, "Test Dashboard")
    
    def test_get_by_uid(self):
        """Test de la méthode get_by_uid."""
        dashboard = self.repository.get_by_uid(self.dashboard.uid)
        self.assertIsNotNone(dashboard)
        self.assertEqual(dashboard.id, self.dashboard.id)
    
    def test_get_by_owner(self):
        """Test de la méthode get_by_owner."""
        dashboards = self.repository.get_by_owner(self.user.id)
        self.assertEqual(len(dashboards), 1)
        self.assertEqual(dashboards[0].id, self.dashboard.id)
    
    def test_get_public_dashboards(self):
        """Test de la méthode get_public_dashboards."""
        dashboards = self.repository.get_public_dashboards()
        self.assertEqual(len(dashboards), 1)
        self.assertEqual(dashboards[0].id, self.dashboard.id)
    
    def test_get_default_dashboard(self):
        """Test de la méthode get_default_dashboard."""
        dashboard = self.repository.get_default_dashboard(self.user.id)
        self.assertIsNotNone(dashboard)
        self.assertEqual(dashboard.id, self.dashboard.id)
    
    def test_add_widget(self):
        """Test de la méthode add_widget."""
        widget = self.repository.add_widget(
            dashboard_id=self.dashboard.id,
            title="CPU Usage",
            widget_type="metric_chart",
            position={"x": 0, "y": 0},
            size={"width": 6, "height": 4},
            data_source={"metric_id": 1},
            config={"chart_type": "line"}
        )
        
        self.assertIsNotNone(widget)
        self.assertEqual(widget.title, "CPU Usage")
        self.assertEqual(widget.widget_type, "metric_chart")
        
        # Vérifier que le widget a bien été créé en base
        widgets = DashboardWidget.objects.filter(dashboard_id=self.dashboard.id)
        self.assertEqual(len(widgets), 1)
    
    def test_remove_widget(self):
        """Test de la méthode remove_widget."""
        # Créer un widget
        widget = self.repository.add_widget(
            dashboard_id=self.dashboard.id,
            title="Memory Usage",
            widget_type="metric_value",
            position={"x": 6, "y": 0},
            size={"width": 3, "height": 2}
        )
        
        # Supprimer le widget
        result = self.repository.remove_widget(widget.id)
        self.assertTrue(result)
        
        # Vérifier que le widget a bien été supprimé en base
        widgets = DashboardWidget.objects.filter(id=widget.id)
        self.assertEqual(len(widgets), 0)
    
    def test_update_widget(self):
        """Test de la méthode update_widget."""
        # Créer un widget
        widget = self.repository.add_widget(
            dashboard_id=self.dashboard.id,
            title="Network Traffic",
            widget_type="metric_chart",
            position={"x": 0, "y": 4},
            size={"width": 12, "height": 6}
        )
        
        # Mettre à jour le widget
        updated_widget = self.repository.update_widget(
            widget_id=widget.id,
            title="Updated Network Traffic",
            position={"x": 0, "y": 6},
            config={"chart_type": "area"}
        )
        
        self.assertEqual(updated_widget.title, "Updated Network Traffic")
        self.assertEqual(updated_widget.position["y"], 6)
        self.assertEqual(updated_widget.config["chart_type"], "area")
        
        # Vérifier que le widget a bien été mis à jour en base
        widget = DashboardWidget.objects.get(id=widget.id)
        self.assertEqual(widget.title, "Updated Network Traffic")


class NotificationRepositoryTest(TestCase):
    """Tests pour le repository des notifications."""
    
    def setUp(self):
        """Initialisation des données de test."""
        self.repository = NotificationRepository()
        self.user = User.objects.create_user(username="testuser", password="password")
        
        # Créer un canal de notification
        self.channel = self.repository.create_notification_channel(
            name="Email Channel",
            channel_type="email",
            config={"from_email": "alerts@example.com"},
            created_by_id=self.user.id,
            is_active=True
        )
        
        # Créer une notification
        self.notification = self.repository.create_notification(
            channel_id=self.channel.id,
            subject="Test Alert",
            message="This is a test alert notification",
            recipients=["user@example.com"],
            user_recipients=[self.user.id],
            status="pending"
        )
    
    def test_create_notification(self):
        """Test de la méthode create_notification."""
        notification = self.repository.create_notification(
            channel_id=self.channel.id,
            subject="New Alert",
            message="This is a new alert notification",
            recipients=["admin@example.com"],
            status="pending"
        )
        
        self.assertIsNotNone(notification)
        self.assertEqual(notification.subject, "New Alert")
        self.assertEqual(notification.recipients, ["admin@example.com"])
    
    def test_update_notification_status(self):
        """Test de la méthode update_notification_status."""
        updated = self.repository.update_notification_status(
            self.notification.id,
            status="sent"
        )
        
        self.assertEqual(updated.status, "sent")
        self.assertIsNotNone(updated.sent_at)
        
        # Mettre à jour avec une erreur
        updated = self.repository.update_notification_status(
            self.notification.id,
            status="error",
            error_message="Failed to send email"
        )
        
        self.assertEqual(updated.status, "error")
        self.assertEqual(updated.details.get("error_message"), "Failed to send email")
    
    def test_mark_as_read(self):
        """Test de la méthode mark_as_read."""
        updated = self.repository.mark_as_read(
            self.notification.id,
            user_id=self.user.id
        )
        
        self.assertIn(self.user.id, updated.read_by)
        
        # Vérifier que la notification a bien été mise à jour en base
        notification = Notification.objects.get(id=self.notification.id)
        self.assertIn(self.user.id, notification.read_by)
    
    def test_get_notifications_for_user(self):
        """Test de la méthode get_notifications_for_user."""
        notifications = self.repository.get_notifications_for_user(
            user_id=self.user.id
        )
        
        self.assertEqual(len(notifications), 1)
        self.assertEqual(notifications[0].id, self.notification.id)
        
        # Tester avec le filtre unread_only après avoir marqué comme lu
        self.repository.mark_as_read(self.notification.id, user_id=self.user.id)
        
        unread_notifications = self.repository.get_notifications_for_user(
            user_id=self.user.id,
            unread_only=True
        )
        
        self.assertEqual(len(unread_notifications), 0)
    
    def test_get_unread_count(self):
        """Test de la méthode get_unread_count."""
        # Créer une deuxième notification
        self.repository.create_notification(
            channel_id=self.channel.id,
            subject="Second Alert",
            message="This is another test alert",
            user_recipients=[self.user.id],
            status="pending"
        )
        
        count = self.repository.get_unread_count(user_id=self.user.id)
        self.assertEqual(count, 2)
        
        # Marquer une notification comme lue
        self.repository.mark_as_read(self.notification.id, user_id=self.user.id)
        
        count = self.repository.get_unread_count(user_id=self.user.id)
        self.assertEqual(count, 1)
    
    def test_create_notification_channel(self):
        """Test de la méthode create_notification_channel."""
        channel = self.repository.create_notification_channel(
            name="Webhook Channel",
            channel_type="webhook",
            config={"url": "https://example.com/webhook"},
            description="Channel for webhook notifications",
            created_by_id=self.user.id,
            is_active=True
        )
        
        self.assertIsNotNone(channel)
        self.assertEqual(channel.name, "Webhook Channel")
        self.assertEqual(channel.channel_type, "webhook")
        self.assertEqual(channel.config["url"], "https://example.com/webhook")
    
    def test_get_active_channels(self):
        """Test de la méthode get_active_channels."""
        # Créer un deuxième canal inactif
        self.repository.create_notification_channel(
            name="Inactive Channel",
            channel_type="sms",
            config={},
            is_active=False
        )
        
        active_channels = self.repository.get_active_channels()
        self.assertEqual(len(active_channels), 1)
        self.assertEqual(active_channels[0].name, "Email Channel")
        
        # Tester avec le filtre par type
        email_channels = self.repository.get_active_channels(channel_type="email")
        self.assertEqual(len(email_channels), 1)
        
        sms_channels = self.repository.get_active_channels(channel_type="sms")
        self.assertEqual(len(sms_channels), 0)
    
    def test_get_channels_for_user(self):
        """Test de la méthode get_channels_for_user."""
        # Créer un canal partagé
        self.repository.create_notification_channel(
            name="Shared Channel",
            channel_type="webhook",
            config={},
            is_shared=True
        )
        
        # Créer un canal pour un autre utilisateur
        other_user = User.objects.create_user(username="otheruser", password="password")
        self.repository.create_notification_channel(
            name="Other User Channel",
            channel_type="email",
            config={},
            created_by_id=other_user.id
        )
        
        channels = self.repository.get_channels_for_user(user_id=self.user.id)
        self.assertEqual(len(channels), 2)  # Le canal de l'utilisateur + le canal partagé
        
        # Vérifier que les noms des canaux sont corrects
        channel_names = [channel.name for channel in channels]
        self.assertIn("Email Channel", channel_names)
        self.assertIn("Shared Channel", channel_names)
        self.assertNotIn("Other User Channel", channel_names)


if __name__ == '__main__':
    unittest.main() 