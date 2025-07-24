"""
Tests d'intégration pour les adaptateurs d'infrastructure du module dashboard.

Ces tests vérifient l'intégration entre les adaptateurs et les services externes.
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timedelta
from django.utils import timezone
from django.test import TestCase

from dashboard.infrastructure.monitoring_adapter import MonitoringAdapter
from dashboard.infrastructure.network_adapter import NetworkAdapter
from dashboard.infrastructure.services import (
    DashboardDataServiceImpl,
    NetworkOverviewServiceImpl,
    TopologyVisualizationServiceImpl
)

from monitoring.models import Metric, Alert
from network_management.models import NetworkDevice, NetworkInterface
from security_management.models import SecurityAlert
from qos_management.models import QoSPolicy

pytestmark = pytest.mark.django_db


class TestMonitoringAdapter(TestCase):
    """Tests d'intégration pour MonitoringAdapter."""
    
    def setUp(self):
        """Configuration des données de test."""
        self.adapter = MonitoringAdapter()
        
        # Créer des alertes de test
        self.alert1 = Alert.objects.create(
            metric_name='cpu_usage',
            severity='high',
            message='CPU usage is high',
            status='new',
            timestamp=timezone.now()
        )
        
        self.alert2 = Alert.objects.create(
            metric_name='memory_usage',
            severity='critical',
            message='Memory usage is critical',
            status='acknowledged',
            timestamp=timezone.now() - timedelta(minutes=30)
        )
        
        # Créer des métriques de test
        self.device = NetworkDevice.objects.create(
            name='Test Device',
            hostname='test.example.com',
            ip_address='192.168.1.100',
            device_type='router'
        )
        
        self.metric1 = Metric.objects.create(
            device_id=self.device.id,
            name='cpu_usage',
            value=75.5,
            timestamp=timezone.now()
        )
        
        self.metric2 = Metric.objects.create(
            device_id=self.device.id,
            name='memory_usage',
            value=85.2,
            timestamp=timezone.now() - timedelta(minutes=5)
        )
    
    def test_get_system_alerts_default_params(self):
        """Test de récupération des alertes système avec paramètres par défaut."""
        # Act
        alerts = self.adapter.get_system_alerts()
        
        # Assert
        assert len(alerts) == 2
        assert alerts[0]['id'] == self.alert1.id  # Plus récente en premier
        assert alerts[1]['id'] == self.alert2.id
        
        # Vérifier la structure des données
        for alert in alerts:
            assert 'id' in alert
            assert 'metric_name' in alert
            assert 'severity' in alert
            assert 'message' in alert
            assert 'timestamp' in alert
            assert 'status' in alert
    
    def test_get_system_alerts_with_limit(self):
        """Test de récupération des alertes avec limite."""
        # Act
        alerts = self.adapter.get_system_alerts(limit=1)
        
        # Assert
        assert len(alerts) == 1
        assert alerts[0]['id'] == self.alert1.id
    
    def test_get_system_alerts_with_status_filter(self):
        """Test de récupération des alertes avec filtre de statut."""
        # Act
        alerts = self.adapter.get_system_alerts(status_filter=['new'])
        
        # Assert
        assert len(alerts) == 1
        assert alerts[0]['status'] == 'new'
        assert alerts[0]['id'] == self.alert1.id
    
    def test_get_performance_metrics(self):
        """Test de récupération des métriques de performance."""
        # Act
        metrics = self.adapter.get_performance_metrics()
        
        # Assert
        assert isinstance(metrics, dict)
        assert 'bandwidth_utilization' in metrics
        assert 'response_time_avg' in metrics
        assert 'packet_loss' in metrics
        assert 'latency_avg' in metrics
        
        # Vérifier que les valeurs sont numériques
        for key, value in metrics.items():
            assert isinstance(value, (int, float))
    
    def test_get_device_metrics(self):
        """Test de récupération des métriques d'un équipement."""
        # Act
        metrics = self.adapter.get_device_metrics(self.device.id)
        
        # Assert
        assert isinstance(metrics, dict)
        assert 'cpu_usage' in metrics
        assert 'memory_usage' in metrics
        assert 'interface_status' in metrics
        assert 'uptime' in metrics
        assert 'temperature' in metrics
        assert 'alerts' in metrics
        
        # Vérifier que les alertes sont incluses
        assert isinstance(metrics['alerts'], list)
    
    def test_get_device_metrics_nonexistent_device(self):
        """Test avec un équipement inexistant."""
        # Act
        metrics = self.adapter.get_device_metrics(999)
        
        # Assert
        assert isinstance(metrics, dict)
        # Doit retourner des valeurs par défaut
        assert metrics['cpu_usage'] == 0
        assert metrics['memory_usage'] == 0
        assert metrics['alerts'] == []


class TestNetworkAdapter(TestCase):
    """Tests d'intégration pour NetworkAdapter."""
    
    def setUp(self):
        """Configuration des données de test."""
        self.adapter = NetworkAdapter()
        
        # Créer des équipements de test
        self.device1 = NetworkDevice.objects.create(
            name='Router 1',
            hostname='router1.example.com',
            ip_address='192.168.1.1',
            device_type='router',
            status='active'
        )
        
        self.device2 = NetworkDevice.objects.create(
            name='Switch 1',
            hostname='switch1.example.com',
            ip_address='192.168.1.2',
            device_type='switch',
            status='warning'
        )
        
        # Créer des interfaces de test
        self.interface1 = NetworkInterface.objects.create(
            device=self.device1,
            name='eth0',
            interface_type='ethernet',
            status='up'
        )
        
        self.interface2 = NetworkInterface.objects.create(
            device=self.device2,
            name='eth1',
            interface_type='ethernet',
            status='down'
        )
        
        # Créer des politiques QoS de test
        self.qos_policy = QoSPolicy.objects.create(
            name='High Priority',
            description='High priority traffic',
            is_active=True
        )
    
    def test_get_device_summary(self):
        """Test de récupération du résumé des équipements."""
        # Act
        summary = self.adapter.get_device_summary()
        
        # Assert
        assert isinstance(summary, dict)
        assert 'total' in summary
        assert 'status_summary' in summary
        
        assert summary['total'] == 2
        status_summary = summary['status_summary']
        assert status_summary['active'] == 1
        assert status_summary['warning'] == 1
        assert status_summary['critical'] == 0
        assert status_summary['inactive'] == 0
    
    def test_get_interface_summary(self):
        """Test de récupération du résumé des interfaces."""
        # Act
        summary = self.adapter.get_interface_summary()
        
        # Assert
        assert isinstance(summary, dict)
        assert 'total' in summary
        assert 'status_summary' in summary
        
        assert summary['total'] == 2
        status_summary = summary['status_summary']
        assert status_summary['up'] == 1
        assert status_summary['down'] == 1
        assert status_summary['unknown'] == 0
    
    def test_get_qos_summary(self):
        """Test de récupération du résumé QoS."""
        # Act
        summary = self.adapter.get_qos_summary()
        
        # Assert
        assert isinstance(summary, dict)
        assert 'policies' in summary
        assert 'active_policies' in summary
        
        assert summary['policies'] == 1
        assert summary['active_policies'] == 1
    
    def test_get_topology_data(self):
        """Test de récupération des données de topologie."""
        # Act
        topology_data = self.adapter.get_topology_data()
        
        # Assert
        assert isinstance(topology_data, dict)
        # La structure dépend de l'implémentation spécifique


class TestDashboardDataServiceImpl(TestCase):
    """Tests d'intégration pour DashboardDataServiceImpl."""
    
    def setUp(self):
        """Configuration des données de test."""
        self.service = DashboardDataServiceImpl()
        
        # Créer des données de test
        self.device = NetworkDevice.objects.create(
            name='Test Device',
            hostname='test.example.com',
            ip_address='192.168.1.100',
            device_type='router',
            status='active'
        )
        
        self.security_alert = SecurityAlert.objects.create(
            source='test',
            event_type='security',
            message='Test security alert',
            severity='high',
            status='new',
            timestamp=timezone.now()
        )
        
        self.system_alert = Alert.objects.create(
            metric_name='cpu_usage',
            severity='warning',
            message='Test system alert',
            status='new',
            timestamp=timezone.now()
        )
    
    def test_get_dashboard_overview(self):
        """Test de récupération de la vue d'ensemble du dashboard."""
        # Act
        overview = self.service.get_dashboard_overview()
        
        # Assert
        assert isinstance(overview, dict)
        assert 'devices' in overview
        assert 'security_alerts' in overview
        assert 'system_alerts' in overview
        assert 'performance' in overview
        assert 'health_metrics' in overview
        
        # Vérifier les statistiques des équipements
        devices = overview['devices']
        assert devices['total'] == 1
        assert devices['active'] == 1
        
        # Vérifier les alertes
        assert len(overview['security_alerts']) == 1
        assert len(overview['system_alerts']) == 1
    
    def test_get_system_health_metrics(self):
        """Test de récupération des métriques de santé."""
        # Act
        metrics = self.service.get_system_health_metrics()
        
        # Assert
        assert isinstance(metrics, dict)
        assert 'system_health' in metrics
        assert 'network_health' in metrics
        assert 'security_health' in metrics
        
        # Vérifier que les valeurs sont dans la plage [0, 1]
        for key, value in metrics.items():
            assert 0 <= value <= 1, f"{key} doit être entre 0 et 1"


class TestNetworkOverviewServiceImpl(TestCase):
    """Tests d'intégration pour NetworkOverviewServiceImpl."""
    
    def setUp(self):
        """Configuration des données de test."""
        self.service = NetworkOverviewServiceImpl()
        
        # Créer des données de test
        self.device = NetworkDevice.objects.create(
            name='Test Device',
            hostname='test.example.com',
            ip_address='192.168.1.100',
            device_type='router',
            status='active'
        )
        
        self.interface = NetworkInterface.objects.create(
            device=self.device,
            name='eth0',
            interface_type='ethernet',
            status='up'
        )
        
        self.qos_policy = QoSPolicy.objects.create(
            name='Test Policy',
            description='Test QoS policy',
            is_active=True
        )
        
        self.alert = Alert.objects.create(
            metric_name='network_latency',
            severity='warning',
            message='Network latency alert',
            status='new',
            timestamp=timezone.now(),
            category='network'
        )
    
    def test_get_network_overview(self):
        """Test de récupération de la vue d'ensemble réseau."""
        # Act
        overview = self.service.get_network_overview()
        
        # Assert
        assert isinstance(overview, dict)
        assert 'devices' in overview
        assert 'interfaces' in overview
        assert 'qos' in overview
        assert 'alerts' in overview
        
        # Vérifier les statistiques des équipements
        devices = overview['devices']
        assert devices['total'] == 1
        assert devices['status_summary']['active'] == 1
        
        # Vérifier les statistiques des interfaces
        interfaces = overview['interfaces']
        assert interfaces['total'] == 1
        assert interfaces['status_summary']['up'] == 1
        
        # Vérifier les politiques QoS
        qos = overview['qos']
        assert qos['policies'] == 1
        assert qos['active_policies'] == 1
        
        # Vérifier les alertes
        assert len(overview['alerts']) == 1


class TestTopologyVisualizationServiceImpl(TestCase):
    """Tests d'intégration pour TopologyVisualizationServiceImpl."""
    
    def setUp(self):
        """Configuration des données de test."""
        self.service = TopologyVisualizationServiceImpl()
        
        # Créer des données de test
        self.device = NetworkDevice.objects.create(
            name='Test Device',
            hostname='test.example.com',
            ip_address='192.168.1.100',
            device_type='router',
            status='active'
        )
    
    def test_get_device_health_status(self):
        """Test de récupération du statut de santé d'un équipement."""
        # Act
        status = self.service.get_device_health_status(self.device.id)
        
        # Assert
        assert isinstance(status, str)
        assert status in ['critical', 'warning', 'healthy', 'inactive']
    
    def test_get_device_health_status_nonexistent(self):
        """Test avec un équipement inexistant."""
        # Act
        status = self.service.get_device_health_status(999)
        
        # Assert
        assert status == 'unknown'
    
    def test_get_connection_status(self):
        """Test de récupération du statut d'une connexion."""
        # Act
        status = self.service.get_connection_status(1)
        
        # Assert
        assert isinstance(status, str)
        assert status in ['critical', 'warning', 'healthy', 'unknown']


class TestAdaptersIntegration(TestCase):
    """Tests d'intégration entre les adaptateurs."""
    
    def setUp(self):
        """Configuration des données de test."""
        self.monitoring_adapter = MonitoringAdapter()
        self.network_adapter = NetworkAdapter()
        
        # Créer des données partagées
        self.device = NetworkDevice.objects.create(
            name='Shared Device',
            hostname='shared.example.com',
            ip_address='192.168.1.200',
            device_type='router',
            status='active'
        )
        
        self.metric = Metric.objects.create(
            device_id=self.device.id,
            name='cpu_usage',
            value=80.0,
            timestamp=timezone.now()
        )
    
    def test_adapters_consistency(self):
        """Test de cohérence entre les adaptateurs."""
        # Act
        device_summary = self.network_adapter.get_device_summary()
        device_metrics = self.monitoring_adapter.get_device_metrics(self.device.id)
        
        # Assert
        # Les deux adaptateurs doivent voir le même équipement
        assert device_summary['total'] >= 1
        assert isinstance(device_metrics, dict)
        assert 'cpu_usage' in device_metrics
    
    def test_error_handling_consistency(self):
        """Test de cohérence dans la gestion d'erreurs."""
        # Act & Assert
        # Les deux adaptateurs doivent gérer les erreurs de manière similaire
        network_result = self.network_adapter.get_device_summary()
        monitoring_result = self.monitoring_adapter.get_device_metrics(999)
        
        # Aucune exception ne doit être levée
        assert isinstance(network_result, dict)
        assert isinstance(monitoring_result, dict)