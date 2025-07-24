"""
Tests d'intégration pour la Phase 2 du Dashboard - Collecte de Données Réelles.

Ce fichier teste toutes les nouvelles fonctionnalités de la Phase 2 :
- Intégration avec les vrais modèles Django
- Collecte SNMP pour métriques
- Système d'alertes basé sur seuils réels
- Service de découverte réseau automatique
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from django.test import TestCase, TransactionTestCase
from django.utils import timezone
from datetime import timedelta

from network_management.models import NetworkDevice, NetworkInterface, NetworkConnection
from monitoring.models import Alert, DeviceMetric, MetricValue, MetricsDefinition

from dashboard.infrastructure.network_adapter import NetworkAdapter
from dashboard.infrastructure.monitoring_adapter import MonitoringAdapter
from dashboard.infrastructure.snmp_collector import SNMPCollector, snmp_collector
from dashboard.infrastructure.network_discovery import NetworkDiscoveryService, network_discovery
from dashboard.infrastructure.threshold_alerting import ThresholdAlertingService, threshold_alerting


class TestPhase2RealDataIntegration(TransactionTestCase):
    """
    Tests d'intégration pour vérifier que les adaptateurs utilisent les vraies données.
    """
    
    def setUp(self):
        """Configuration des tests avec données réelles."""
        # Créer des équipements de test
        self.device1 = NetworkDevice.objects.create(
            name="test-router-01",
            ip_address="192.168.1.1",
            device_type="router",
            vendor="Cisco",
            model="ISR4321",
            status="active",
            snmp_community="public"
        )
        
        self.device2 = NetworkDevice.objects.create(
            name="test-switch-01", 
            ip_address="192.168.1.2",
            device_type="switch",
            vendor="Cisco",
            model="C9300-24T",
            status="warning"
        )
        
        # Créer des interfaces
        self.interface1 = NetworkInterface.objects.create(
            device=self.device1,
            name="GigabitEthernet0/0/0",
            status="up",
            speed=1000
        )
        
        self.interface2 = NetworkInterface.objects.create(
            device=self.device2,
            name="GigabitEthernet1/0/1",
            status="up", 
            speed=1000
        )
        
        # Créer une connexion
        self.connection = NetworkConnection.objects.create(
            source_device=self.device1,
            target_device=self.device2,
            source_interface=self.interface1,
            target_interface=self.interface2,
            connection_type="ethernet",
            bandwidth=1000
        )
        
        # Créer des définitions de métriques
        self.cpu_metric_def = MetricsDefinition.objects.create(
            name="cpu_utilization",
            description="CPU Utilization",
            unit="percent",
            data_type="float"
        )
        
        self.memory_metric_def = MetricsDefinition.objects.create(
            name="memory_utilization", 
            description="Memory Utilization",
            unit="percent",
            data_type="float"
        )
        
        # Créer des métriques d'équipement
        self.device_cpu_metric = DeviceMetric.objects.create(
            device=self.device1,
            metric_definition=self.cpu_metric_def,
            is_active=True
        )
        
        self.device_memory_metric = DeviceMetric.objects.create(
            device=self.device1,
            metric_definition=self.memory_metric_def,
            is_active=True
        )
        
        # Créer des valeurs de métriques
        MetricValue.objects.create(
            device_metric=self.device_cpu_metric,
            value=75.5,
            timestamp=timezone.now()
        )
        
        MetricValue.objects.create(
            device_metric=self.device_memory_metric,
            value=82.3,
            timestamp=timezone.now()
        )
        
        # Créer des alertes
        self.alert1 = Alert.objects.create(
            device=self.device1,
            alert_type="threshold",
            severity="warning",
            status="active",
            message="CPU utilization high",
            metric_name="cpu_utilization"
        )
        
        self.alert2 = Alert.objects.create(
            device=self.device2,
            alert_type="network",
            severity="critical", 
            status="active",
            message="Interface down"
        )
    
    def test_network_adapter_real_device_summary(self):
        """Test que NetworkAdapter récupère les vraies données d'équipements."""
        adapter = NetworkAdapter()
        
        # Exécuter la méthode asynchrone
        result = asyncio.run(adapter.get_device_summary())
        
        # Vérifications
        self.assertIn('total_devices', result)
        self.assertEqual(result['total_devices'], 2)
        self.assertIn('device_types', result)
        self.assertIn('router', result['device_types'])
        self.assertIn('switch', result['device_types'])
        self.assertEqual(result['device_types']['router'], 1)
        self.assertEqual(result['device_types']['switch'], 1)
        self.assertIn('status', result)
        self.assertEqual(result['status']['active'], 1)
        self.assertEqual(result['status']['warning'], 1)
        self.assertEqual(result['data_source'], 'real_database')
    
    def test_network_adapter_real_interface_summary(self):
        """Test que NetworkAdapter récupère les vraies données d'interfaces."""
        adapter = NetworkAdapter()
        
        result = asyncio.run(adapter.get_interface_summary())
        
        # Vérifications
        self.assertIn('total_interfaces', result)
        self.assertEqual(result['total_interfaces'], 2)
        self.assertIn('by_speed', result)
        self.assertIn('1Gbps', result['by_speed'])
        self.assertEqual(result['by_speed']['1Gbps'], 2)
        self.assertIn('by_status', result)
        self.assertEqual(result['by_status']['up'], 2)
        self.assertEqual(result['data_source'], 'real_database')
    
    def test_network_adapter_real_topology_data(self):
        """Test que NetworkAdapter récupère les vraies données de topologie."""
        adapter = NetworkAdapter()
        
        result = asyncio.run(adapter.get_topology_data())
        
        # Vérifications
        self.assertIn('nodes', result)
        self.assertIn('connections', result)
        self.assertEqual(len(result['nodes']), 2)
        self.assertEqual(len(result['connections']), 1)
        
        # Vérifier les données des nœuds
        node_names = [node['name'] for node in result['nodes']]
        self.assertIn('test-router-01', node_names)
        self.assertIn('test-switch-01', node_names)
        
        # Vérifier les connexions
        connection = result['connections'][0]
        self.assertIn('source', connection)
        self.assertIn('target', connection)
        self.assertEqual(connection['bandwidth'], 1000)
        self.assertEqual(result['data_source'], 'real_database')
    
    def test_monitoring_adapter_real_system_alerts(self):
        """Test que MonitoringAdapter récupère les vraies alertes."""
        adapter = MonitoringAdapter()
        
        result = asyncio.run(adapter.get_system_alerts(limit=10))
        
        # Vérifications
        self.assertIsInstance(result, list)
        self.assertGreaterEqual(len(result), 2)  # Au moins nos 2 alertes de test
        
        # Vérifier qu'on a nos alertes
        alert_messages = [alert.message for alert in result]
        self.assertIn("CPU utilization high", alert_messages)
        self.assertIn("Interface down", alert_messages)
    
    def test_monitoring_adapter_real_device_metrics(self):
        """Test que MonitoringAdapter récupère les vraies métriques d'équipement."""
        adapter = MonitoringAdapter()
        
        result = asyncio.run(adapter.get_device_metrics(self.device1.id))
        
        # Vérifications
        self.assertIn('cpu_usage', result)
        self.assertIn('memory_usage', result)
        self.assertEqual(result['cpu_usage'], 75.5)
        self.assertEqual(result['memory_usage'], 82.3)
        self.assertEqual(result['data_source'], 'real_database')
        self.assertIn('metrics_count', result)
        self.assertEqual(result['metrics_count'], 2)
    
    def test_monitoring_adapter_real_system_health(self):
        """Test que MonitoringAdapter calcule la santé système depuis les vraies données."""
        adapter = MonitoringAdapter()
        
        result = asyncio.run(adapter.get_system_health_metrics())
        
        # Vérifications
        self.assertIsNotNone(result.system_health)
        self.assertIsNotNone(result.network_health)
        self.assertIsNotNone(result.security_health)
        
        # Les valeurs doivent être entre 0 et 1
        self.assertGreaterEqual(result.system_health, 0.0)
        self.assertLessEqual(result.system_health, 1.0)
        self.assertGreaterEqual(result.network_health, 0.0)
        self.assertLessEqual(result.network_health, 1.0)
        
        # La santé réseau devrait être 0.5 (1 actif sur 2 équipements)
        self.assertEqual(result.network_health, 0.5)


class TestPhase2SNMPCollection(TestCase):
    """
    Tests pour le service de collecte SNMP.
    """
    
    def setUp(self):
        """Configuration des tests SNMP."""
        self.device = NetworkDevice.objects.create(
            name="snmp-test-device",
            ip_address="192.168.1.100",
            device_type="router",
            vendor="Cisco",
            snmp_community="public",
            status="active"
        )
        
        self.collector = SNMPCollector()
    
    def test_snmp_collector_device_metrics(self):
        """Test de collecte de métriques SNMP pour un équipement."""
        result = asyncio.run(self.collector.collect_device_metrics(self.device.id))
        
        # Vérifications
        self.assertNotIn('error', result)
        self.assertIn('cpu_utilization', result)
        self.assertIn('memory_utilization', result)
        self.assertIn('uptime', result)
        self.assertIn('interface_throughput', result)
        self.assertIn('last_snmp_collection', result)
    
    def test_snmp_collector_all_devices(self):
        """Test de collecte SNMP pour tous les équipements."""
        result = asyncio.run(self.collector.collect_all_devices_metrics())
        
        # Vérifications
        self.assertIn('total_devices', result)
        self.assertIn('success_count', result)
        self.assertIn('error_count', result)
        self.assertIn('snmp_available', result)
        self.assertEqual(result['total_devices'], 1)


class TestPhase2NetworkDiscovery(TestCase):
    """
    Tests pour le service de découverte réseau.
    """
    
    def setUp(self):
        """Configuration des tests de découverte."""
        self.discovery = NetworkDiscoveryService()
    
    def test_network_discovery_range(self):
        """Test de découverte d'une plage réseau."""
        result = asyncio.run(self.discovery.discover_network_range("192.168.1.0/30"))
        
        # Vérifications
        self.assertIn('network_range', result)
        self.assertIn('total_ips_scanned', result)
        self.assertIn('responsive_ips', result)
        self.assertIn('discovered_devices', result)
        self.assertIn('devices', result)
        self.assertEqual(result['network_range'], "192.168.1.0/30")
        self.assertEqual(result['total_ips_scanned'], 2)  # .1 et .2 dans un /30
    
    def test_device_neighbors_discovery(self):
        """Test de découverte des voisins d'un équipement."""
        device = NetworkDevice.objects.create(
            name="discovery-test",
            ip_address="192.168.1.50",
            device_type="switch",
            status="active"
        )
        
        result = asyncio.run(self.discovery.discover_device_neighbors(device.id))
        
        # Vérifications
        self.assertIn('device_id', result)
        self.assertIn('neighbors_count', result)
        self.assertIn('neighbors', result)
        self.assertEqual(result['device_id'], device.id)
        self.assertGreaterEqual(result['neighbors_count'], 2)


class TestPhase2ThresholdAlerting(TestCase):
    """
    Tests pour le système d'alertes basé sur seuils.
    """
    
    def setUp(self):
        """Configuration des tests d'alertes."""
        self.device = NetworkDevice.objects.create(
            name="threshold-test-device",
            ip_address="192.168.1.200",
            device_type="router",
            status="active"
        )
        
        # Créer une métrique avec valeur élevée
        self.metric_def = MetricsDefinition.objects.create(
            name="cpu_utilization",
            description="CPU Utilization",
            unit="percent"
        )
        
        self.device_metric = DeviceMetric.objects.create(
            device=self.device,
            metric_definition=self.metric_def,
            is_active=True
        )
        
        # Valeur qui dépasse le seuil critique (90%)
        MetricValue.objects.create(
            device_metric=self.device_metric,
            value=95.0,
            timestamp=timezone.now()
        )
        
        self.alerting = ThresholdAlertingService()
    
    def test_threshold_evaluation_creates_alert(self):
        """Test que l'évaluation de seuils crée des alertes."""
        result = asyncio.run(self.alerting.evaluate_device_thresholds(self.device.id))
        
        # Vérifications
        self.assertIn('alerts_generated', result)
        self.assertGreater(result['alerts_generated'], 0)
        self.assertIn('alerts', result)
        
        # Vérifier qu'une alerte a été créée
        alert_created = Alert.objects.filter(
            device=self.device,
            metric_name="cpu_utilization",
            severity="critical"
        ).exists()
        self.assertTrue(alert_created)
    
    def test_threshold_configuration(self):
        """Test de configuration de seuils personnalisés."""
        result = asyncio.run(self.alerting.configure_device_thresholds(
            self.device.id, "cpu_utilization", 60.0, 80.0
        ))
        
        # Vérifications
        self.assertIn('device_id', result)
        self.assertIn('metric_name', result)
        self.assertEqual(result['warning_threshold'], 60.0)
        self.assertEqual(result['critical_threshold'], 80.0)
    
    def test_global_threshold_evaluation(self):
        """Test d'évaluation globale des seuils."""
        result = asyncio.run(self.alerting.evaluate_all_devices_thresholds())
        
        # Vérifications
        self.assertIn('total_devices', result)
        self.assertIn('total_alerts_generated', result)
        self.assertIn('devices_with_alerts', result)
        self.assertEqual(result['total_devices'], 1)


class TestPhase2IntegrationWorkflow(TransactionTestCase):
    """
    Tests d'intégration complets pour valider le workflow Phase 2.
    """
    
    def setUp(self):
        """Configuration pour les tests d'intégration complets."""
        # Créer un environnement de test complet
        self.devices = []
        for i in range(3):
            device = NetworkDevice.objects.create(
                name=f"integration-device-{i+1}",
                ip_address=f"192.168.10.{i+1}",
                device_type="router" if i == 0 else "switch",
                vendor="Cisco",
                status="active",
                snmp_community="public"
            )
            self.devices.append(device)
    
    def test_complete_phase2_workflow(self):
        """Test du workflow complet Phase 2."""
        # 1. Collecte SNMP
        collector = SNMPCollector()
        snmp_result = asyncio.run(collector.collect_all_devices_metrics())
        self.assertEqual(snmp_result['total_devices'], 3)
        
        # 2. Récupération des données réelles via les adaptateurs
        network_adapter = NetworkAdapter()
        device_summary = asyncio.run(network_adapter.get_device_summary())
        self.assertEqual(device_summary['total_devices'], 3)
        self.assertEqual(device_summary['data_source'], 'real_database')
        
        monitoring_adapter = MonitoringAdapter()
        health_metrics = asyncio.run(monitoring_adapter.get_system_health_metrics())
        self.assertIsNotNone(health_metrics.system_health)
        
        # 3. Découverte réseau
        discovery = NetworkDiscoveryService()
        discovery_result = asyncio.run(discovery.discover_network_range("192.168.10.0/29"))
        self.assertGreaterEqual(discovery_result['discovered_devices'], 0)
        
        # 4. Évaluation des seuils
        alerting = ThresholdAlertingService()
        threshold_result = asyncio.run(alerting.evaluate_all_devices_thresholds())
        self.assertEqual(threshold_result['total_devices'], 3)
        
        # Vérifier que tout fonctionne ensemble
        self.assertTrue(True)  # Si on arrive ici, le workflow complet fonctionne
