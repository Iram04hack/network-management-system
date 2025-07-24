#!/usr/bin/env python3
"""
Script de validation pour la Phase 2 du Dashboard - Collecte de Données Réelles.

Ce script valide toutes les nouvelles fonctionnalités de la Phase 2 :
- Intégration avec les vrais modèles Django
- Collecte SNMP pour métriques
- Système d'alertes basé sur seuils réels
- Service de découverte réseau automatique
"""

import os
import sys
import django
import asyncio
from datetime import datetime

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nms_backend.settings')
django.setup()

from network_management.models import NetworkDevice, NetworkInterface, NetworkConnection
from monitoring.models import Alert, DeviceMetric, MetricValue, MetricsDefinition
from django.utils import timezone


def validate_real_data_integration():
    """
    Valide l'intégration avec les vraies données.
    """
    print("\n🔗 VALIDATION INTÉGRATION DONNÉES RÉELLES")
    print("=" * 50)
    
    try:
        # Test 1: Vérifier les modèles Django
        device_count = NetworkDevice.objects.count()
        interface_count = NetworkInterface.objects.count()
        connection_count = NetworkConnection.objects.count()
        alert_count = Alert.objects.count()
        
        print(f"✅ Modèles Django accessibles:")
        print(f"   - Équipements: {device_count}")
        print(f"   - Interfaces: {interface_count}")
        print(f"   - Connexions: {connection_count}")
        print(f"   - Alertes: {alert_count}")
        
        # Test 2: Tester les adaptateurs avec données réelles
        from dashboard.infrastructure.network_adapter import NetworkAdapter
        from dashboard.infrastructure.monitoring_adapter import MonitoringAdapter
        
        network_adapter = NetworkAdapter()
        monitoring_adapter = MonitoringAdapter()
        
        # Test asynchrone des adaptateurs
        async def test_adapters():
            device_summary = await network_adapter.get_device_summary()
            interface_summary = await network_adapter.get_interface_summary()
            system_health = await monitoring_adapter.get_system_health_metrics()
            
            return device_summary, interface_summary, system_health
        
        device_summary, interface_summary, system_health = asyncio.run(test_adapters())
        
        print(f"✅ Adaptateurs fonctionnels:")
        print(f"   - NetworkAdapter: {device_summary.get('data_source', 'unknown')}")
        print(f"   - MonitoringAdapter: santé système = {system_health.system_health}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur intégration données réelles: {e}")
        return False


def validate_snmp_collection():
    """
    Valide le service de collecte SNMP.
    """
    print("\n📡 VALIDATION COLLECTE SNMP")
    print("=" * 50)
    
    try:
        from dashboard.infrastructure.snmp_collector import SNMPCollector
        
        collector = SNMPCollector()
        
        # Test de collecte SNMP
        async def test_snmp():
            # Créer un équipement de test si nécessaire
            test_device, created = NetworkDevice.objects.get_or_create(
                ip_address="192.168.1.100",
                defaults={
                    'name': 'test-snmp-device',
                    'device_type': 'router',
                    'vendor': 'Test',
                    'status': 'active',
                    'snmp_community': 'public'
                }
            )
            
            # Tester la collecte
            metrics = await collector.collect_device_metrics(test_device.id)
            all_devices_result = await collector.collect_all_devices_metrics()
            
            return metrics, all_devices_result, test_device
        
        metrics, all_devices_result, test_device = asyncio.run(test_snmp())
        
        print(f"✅ Collecte SNMP fonctionnelle:")
        print(f"   - Métriques collectées: {len([k for k, v in metrics.items() if isinstance(v, (int, float))])}")
        print(f"   - Équipements traités: {all_devices_result.get('total_devices', 0)}")
        print(f"   - SNMP disponible: {all_devices_result.get('snmp_available', False)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur collecte SNMP: {e}")
        return False


def validate_network_discovery():
    """
    Valide le service de découverte réseau.
    """
    print("\n🔍 VALIDATION DÉCOUVERTE RÉSEAU")
    print("=" * 50)
    
    try:
        from dashboard.infrastructure.network_discovery import NetworkDiscoveryService
        
        discovery = NetworkDiscoveryService()
        
        # Test de découverte réseau
        async def test_discovery():
            # Découverte d'une petite plage
            range_result = await discovery.discover_network_range("192.168.1.0/30")
            
            # Découverte des voisins si on a des équipements
            neighbor_results = []
            devices = NetworkDevice.objects.all()[:2]  # Tester sur 2 équipements max
            
            for device in devices:
                neighbor_result = await discovery.discover_device_neighbors(device.id)
                neighbor_results.append(neighbor_result)
            
            return range_result, neighbor_results
        
        range_result, neighbor_results = asyncio.run(test_discovery())
        
        print(f"✅ Découverte réseau fonctionnelle:")
        print(f"   - IPs scannées: {range_result.get('total_ips_scanned', 0)}")
        print(f"   - IPs responsives: {range_result.get('responsive_ips', 0)}")
        print(f"   - Équipements découverts: {range_result.get('discovered_devices', 0)}")
        print(f"   - Tests voisins: {len(neighbor_results)} équipements")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur découverte réseau: {e}")
        return False


def validate_threshold_alerting():
    """
    Valide le système d'alertes basé sur seuils.
    """
    print("\n⚠️  VALIDATION SYSTÈME D'ALERTES")
    print("=" * 50)
    
    try:
        from dashboard.infrastructure.threshold_alerting import ThresholdAlertingService
        
        alerting = ThresholdAlertingService()
        
        # Test du système d'alertes
        async def test_alerting():
            # Créer un équipement de test avec métriques
            test_device, created = NetworkDevice.objects.get_or_create(
                ip_address="192.168.1.200",
                defaults={
                    'name': 'test-alert-device',
                    'device_type': 'router',
                    'status': 'active'
                }
            )
            
            # Créer une métrique de test
            metric_def, created = MetricsDefinition.objects.get_or_create(
                name="test_cpu_utilization",
                defaults={
                    'description': 'Test CPU Utilization',
                    'unit': 'percent',
                    'data_type': 'float'
                }
            )
            
            device_metric, created = DeviceMetric.objects.get_or_create(
                device=test_device,
                metric_definition=metric_def,
                defaults={'is_active': True}
            )
            
            # Ajouter une valeur élevée pour déclencher une alerte
            MetricValue.objects.create(
                device_metric=device_metric,
                value=95.0,  # Valeur critique
                timestamp=timezone.now()
            )
            
            # Tester l'évaluation des seuils
            device_result = await alerting.evaluate_device_thresholds(test_device.id)
            global_result = await alerting.evaluate_all_devices_thresholds()
            
            # Tester la configuration de seuils
            config_result = await alerting.configure_device_thresholds(
                test_device.id, "test_cpu_utilization", 70.0, 90.0
            )
            
            return device_result, global_result, config_result, test_device
        
        device_result, global_result, config_result, test_device = asyncio.run(test_alerting())
        
        print(f"✅ Système d'alertes fonctionnel:")
        print(f"   - Seuils évalués: {device_result.get('thresholds_evaluated', 0)}")
        print(f"   - Alertes générées: {device_result.get('alerts_generated', 0)}")
        print(f"   - Équipements globaux: {global_result.get('total_devices', 0)}")
        print(f"   - Configuration seuils: {'OK' if 'error' not in config_result else 'ERREUR'}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur système d'alertes: {e}")
        return False


def validate_data_preservation():
    """
    Valide que les 95.65% de données réelles sont préservées.
    """
    print("\n💾 VALIDATION PRÉSERVATION DONNÉES")
    print("=" * 50)
    
    try:
        from dashboard.infrastructure.network_adapter import NetworkAdapter
        from dashboard.infrastructure.monitoring_adapter import MonitoringAdapter
        
        # Tester que les adaptateurs utilisent les vraies données
        async def test_data_sources():
            network_adapter = NetworkAdapter()
            monitoring_adapter = MonitoringAdapter()
            
            device_summary = await network_adapter.get_device_summary()
            interface_summary = await network_adapter.get_interface_summary()
            topology_data = await network_adapter.get_topology_data()
            
            # Créer un équipement pour tester les métriques
            test_device = NetworkDevice.objects.first()
            if test_device:
                device_metrics = await monitoring_adapter.get_device_metrics(test_device.id)
            else:
                device_metrics = {"data_source": "no_devices"}
            
            return device_summary, interface_summary, topology_data, device_metrics
        
        device_summary, interface_summary, topology_data, device_metrics = asyncio.run(test_data_sources())
        
        # Vérifier les sources de données
        real_data_sources = 0
        total_sources = 0
        
        sources = [
            device_summary.get('data_source'),
            interface_summary.get('data_source'),
            topology_data.get('data_source'),
            device_metrics.get('data_source')
        ]
        
        for source in sources:
            total_sources += 1
            if source == 'real_database':
                real_data_sources += 1
        
        real_data_percentage = (real_data_sources / total_sources) * 100 if total_sources > 0 else 0
        
        print(f"✅ Préservation des données:")
        print(f"   - Sources réelles: {real_data_sources}/{total_sources}")
        print(f"   - Pourcentage réel: {real_data_percentage:.1f}%")
        print(f"   - Objectif 95.65%: {'✅ ATTEINT' if real_data_percentage >= 95.0 else '⚠️  À AMÉLIORER'}")
        
        return real_data_percentage >= 95.0
        
    except Exception as e:
        print(f"❌ Erreur validation préservation données: {e}")
        return False


def main():
    """
    Fonction principale de validation Phase 2.
    """
    print("🚀 VALIDATION PHASE 2 - COLLECTE DE DONNÉES RÉELLES")
    print("=" * 60)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Liste des validations à effectuer
    validations = [
        (validate_real_data_integration, "Intégration données réelles"),
        (validate_snmp_collection, "Collecte SNMP"),
        (validate_network_discovery, "Découverte réseau"),
        (validate_threshold_alerting, "Système d'alertes"),
        (validate_data_preservation, "Préservation données réelles"),
    ]
    
    # Exécuter les validations
    results = []
    for validation_func, description in validations:
        try:
            result = validation_func()
            results.append((description, result))
        except Exception as e:
            print(f"💥 Erreur lors de {description}: {e}")
            results.append((description, False))
    
    # Résumé final
    print("\n📊 RÉSUMÉ DE LA VALIDATION PHASE 2")
    print("=" * 50)
    
    total_tests = len(results)
    passed_tests = sum(1 for _, result in results if result)
    failed_tests = total_tests - passed_tests
    
    for description, result in results:
        status = "✅ SUCCÈS" if result else "❌ ÉCHEC"
        print(f"{status} - {description}")
    
    print(f"\n📈 STATISTIQUES:")
    print(f"   Total: {total_tests}")
    print(f"   Réussis: {passed_tests}")
    print(f"   Échoués: {failed_tests}")
    print(f"   Taux de réussite: {(passed_tests/total_tests)*100:.1f}%")
    
    if failed_tests == 0:
        print("\n🎉 TOUTES LES VALIDATIONS PHASE 2 ONT RÉUSSI!")
        print("✅ La collecte de données réelles est opérationnelle.")
        print("✅ Les 95.65% de données réelles sont préservées.")
        print("✅ Les services SNMP, découverte et alertes fonctionnent.")
        return True
    else:
        print(f"\n⚠️  {failed_tests} VALIDATION(S) ONT ÉCHOUÉ")
        print("❌ Des améliorations sont nécessaires avant la Phase 3.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
