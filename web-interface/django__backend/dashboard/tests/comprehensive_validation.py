#!/usr/bin/env python3
"""
Validation fonctionnelle exhaustive du module Dashboard.

Ce script effectue une validation complète et rigoureuse de toutes les fonctionnalités
des Phases 1 et 2 avec des données réelles exclusivement.
"""

import os
import sys
import django
import asyncio
import requests
import json
from datetime import datetime
from typing import Dict, Any, List, Tuple

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nms_backend.settings')
django.setup()

from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status

from network_management.models import NetworkDevice, NetworkInterface, NetworkConnection
from monitoring.models import Alert, DeviceMetric, MetricValue, MetricsDefinition
from dashboard.infrastructure.network_adapter import NetworkAdapter
from dashboard.infrastructure.monitoring_adapter import MonitoringAdapter
from dashboard.infrastructure.snmp_collector import SNMPCollector
from dashboard.infrastructure.network_discovery import NetworkDiscoveryService
from dashboard.infrastructure.threshold_alerting import ThresholdAlertingService


class ComprehensiveDashboardValidation:
    """
    Classe principale pour la validation exhaustive du Dashboard.
    """
    
    def __init__(self):
        """Initialise la validation."""
        self.results = {
            'functional_tests': {},
            'api_tests': {},
            'integration_tests': {},
            'data_validation': {},
            'performance_tests': {}
        }
        self.api_client = APIClient()
        self.base_url = 'http://localhost:8000'
        
    def run_comprehensive_validation(self) -> Dict[str, Any]:
        """
        Exécute la validation complète du Dashboard.
        
        Returns:
            Résultats détaillés de la validation
        """
        print("🚀 VALIDATION FONCTIONNELLE EXHAUSTIVE DASHBOARD")
        print("=" * 60)
        print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 1. Validation fonctionnelle des adaptateurs
        print("\n📋 1. VALIDATION FONCTIONNELLE DES ADAPTATEURS")
        self.validate_adapters()
        
        # 2. Validation des endpoints API
        print("\n🌐 2. VALIDATION DES ENDPOINTS API")
        self.validate_api_endpoints()
        
        # 3. Validation de l'intégration avec les vrais modèles
        print("\n🔗 3. VALIDATION INTÉGRATION MODÈLES DJANGO")
        self.validate_django_integration()
        
        # 4. Validation des services Phase 2
        print("\n⚡ 4. VALIDATION SERVICES PHASE 2")
        self.validate_phase2_services()
        
        # 5. Validation des données réelles
        print("\n💾 5. VALIDATION DONNÉES RÉELLES")
        self.validate_real_data_usage()
        
        # 6. Tests de performance
        print("\n⚡ 6. TESTS DE PERFORMANCE")
        self.validate_performance()
        
        return self.generate_final_report()
    
    def validate_adapters(self):
        """Valide le fonctionnement des adaptateurs."""
        print("  📡 Test NetworkAdapter...")
        
        try:
            adapter = NetworkAdapter()
            
            # Test get_device_summary avec données réelles
            device_summary = asyncio.run(adapter.get_device_summary())
            self.results['functional_tests']['network_adapter_device_summary'] = {
                'status': 'PASS' if 'total_devices' in device_summary else 'FAIL',
                'data_source': device_summary.get('data_source', 'unknown'),
                'total_devices': device_summary.get('total_devices', 0),
                'has_real_data': device_summary.get('data_source') == 'real_database'
            }
            
            # Test get_interface_summary
            interface_summary = asyncio.run(adapter.get_interface_summary())
            self.results['functional_tests']['network_adapter_interface_summary'] = {
                'status': 'PASS' if 'total_interfaces' in interface_summary else 'FAIL',
                'data_source': interface_summary.get('data_source', 'unknown'),
                'total_interfaces': interface_summary.get('total_interfaces', 0),
                'has_real_data': interface_summary.get('data_source') == 'real_database'
            }
            
            # Test get_topology_data
            topology_data = asyncio.run(adapter.get_topology_data())
            self.results['functional_tests']['network_adapter_topology'] = {
                'status': 'PASS' if 'nodes' in topology_data else 'FAIL',
                'data_source': topology_data.get('data_source', 'unknown'),
                'nodes_count': len(topology_data.get('nodes', [])),
                'connections_count': len(topology_data.get('connections', [])),
                'has_real_data': topology_data.get('data_source') == 'real_database'
            }
            
            print("    ✅ NetworkAdapter validé")
            
        except Exception as e:
            print(f"    ❌ Erreur NetworkAdapter: {e}")
            self.results['functional_tests']['network_adapter_error'] = str(e)
        
        print("  📊 Test MonitoringAdapter...")
        
        try:
            adapter = MonitoringAdapter()
            
            # Test get_system_alerts
            alerts = asyncio.run(adapter.get_system_alerts(limit=5))
            self.results['functional_tests']['monitoring_adapter_alerts'] = {
                'status': 'PASS' if isinstance(alerts, list) else 'FAIL',
                'alerts_count': len(alerts) if isinstance(alerts, list) else 0,
                'has_real_alerts': len(alerts) > 0 if isinstance(alerts, list) else False
            }
            
            # Test get_system_health_metrics
            health = asyncio.run(adapter.get_system_health_metrics())
            self.results['functional_tests']['monitoring_adapter_health'] = {
                'status': 'PASS' if hasattr(health, 'system_health') else 'FAIL',
                'system_health': getattr(health, 'system_health', 0),
                'network_health': getattr(health, 'network_health', 0),
                'security_health': getattr(health, 'security_health', 0)
            }
            
            print("    ✅ MonitoringAdapter validé")
            
        except Exception as e:
            print(f"    ❌ Erreur MonitoringAdapter: {e}")
            self.results['functional_tests']['monitoring_adapter_error'] = str(e)
    
    def validate_api_endpoints(self):
        """Valide tous les endpoints API du Dashboard."""
        endpoints_to_test = [
            ('/api/dashboard/api/data/', 'GET'),
            ('/api/dashboard/api/config/', 'GET'),
            ('/api/dashboard/api/network/overview/', 'GET'),
            ('/api/dashboard/api/network/health/', 'GET'),
            ('/api/dashboard/api/topology/list/', 'GET'),
            ('/api/dashboard/api/topology/data/', 'GET'),
        ]
        
        for endpoint, method in endpoints_to_test:
            print(f"  🌐 Test {method} {endpoint}")
            
            try:
                if method == 'GET':
                    response = self.api_client.get(endpoint)
                else:
                    response = self.api_client.post(endpoint)
                
                endpoint_key = endpoint.replace('/', '_').replace('-', '_')
                self.results['api_tests'][endpoint_key] = {
                    'status': 'PASS' if response.status_code in [200, 201] else 'FAIL',
                    'status_code': response.status_code,
                    'has_data': len(response.data) > 0 if hasattr(response, 'data') else False,
                    'response_time': getattr(response, '_response_time', 'unknown')
                }
                
                if response.status_code in [200, 201]:
                    print(f"    ✅ {endpoint} - Status: {response.status_code}")
                else:
                    print(f"    ❌ {endpoint} - Status: {response.status_code}")
                    
            except Exception as e:
                print(f"    💥 Erreur {endpoint}: {e}")
                endpoint_key = endpoint.replace('/', '_').replace('-', '_')
                self.results['api_tests'][endpoint_key] = {
                    'status': 'ERROR',
                    'error': str(e)
                }
    
    def validate_django_integration(self):
        """Valide l'intégration avec les vrais modèles Django."""
        print("  🔗 Test intégration NetworkDevice...")
        
        try:
            # Compter les équipements réels
            device_count = NetworkDevice.objects.count()
            interface_count = NetworkInterface.objects.count()
            connection_count = NetworkConnection.objects.count()
            
            self.results['integration_tests']['django_models'] = {
                'status': 'PASS',
                'device_count': device_count,
                'interface_count': interface_count,
                'connection_count': connection_count,
                'models_accessible': True
            }
            
            print(f"    ✅ Modèles Django accessibles - {device_count} équipements")
            
        except Exception as e:
            print(f"    ❌ Erreur modèles Django: {e}")
            self.results['integration_tests']['django_models'] = {
                'status': 'FAIL',
                'error': str(e),
                'models_accessible': False
            }
        
        print("  📊 Test intégration Monitoring...")
        
        try:
            # Compter les alertes et métriques réelles
            alert_count = Alert.objects.count()
            metric_count = DeviceMetric.objects.count()
            value_count = MetricValue.objects.count()
            
            self.results['integration_tests']['monitoring_models'] = {
                'status': 'PASS',
                'alert_count': alert_count,
                'metric_count': metric_count,
                'value_count': value_count,
                'monitoring_accessible': True
            }
            
            print(f"    ✅ Monitoring accessible - {alert_count} alertes, {value_count} valeurs")
            
        except Exception as e:
            print(f"    ❌ Erreur monitoring: {e}")
            self.results['integration_tests']['monitoring_models'] = {
                'status': 'FAIL',
                'error': str(e),
                'monitoring_accessible': False
            }
    
    def validate_phase2_services(self):
        """Valide les services de la Phase 2."""
        print("  📡 Test SNMPCollector...")
        
        try:
            collector = SNMPCollector()
            
            # Test de collecte globale
            result = asyncio.run(collector.collect_all_devices_metrics())
            
            self.results['integration_tests']['snmp_collector'] = {
                'status': 'PASS' if 'total_devices' in result else 'FAIL',
                'total_devices': result.get('total_devices', 0),
                'success_count': result.get('success_count', 0),
                'error_count': result.get('error_count', 0),
                'snmp_available': result.get('snmp_available', False)
            }
            
            print(f"    ✅ SNMPCollector - {result.get('total_devices', 0)} équipements traités")
            
        except Exception as e:
            print(f"    ❌ Erreur SNMPCollector: {e}")
            self.results['integration_tests']['snmp_collector'] = {
                'status': 'ERROR',
                'error': str(e)
            }
        
        print("  🔍 Test NetworkDiscovery...")
        
        try:
            discovery = NetworkDiscoveryService()
            
            # Test de découverte sur une petite plage
            result = asyncio.run(discovery.discover_network_range("192.168.1.0/30"))
            
            self.results['integration_tests']['network_discovery'] = {
                'status': 'PASS' if 'total_ips_scanned' in result else 'FAIL',
                'total_ips_scanned': result.get('total_ips_scanned', 0),
                'responsive_ips': result.get('responsive_ips', 0),
                'discovered_devices': result.get('discovered_devices', 0)
            }
            
            print(f"    ✅ NetworkDiscovery - {result.get('total_ips_scanned', 0)} IPs scannées")
            
        except Exception as e:
            print(f"    ❌ Erreur NetworkDiscovery: {e}")
            self.results['integration_tests']['network_discovery'] = {
                'status': 'ERROR',
                'error': str(e)
            }
        
        print("  ⚠️ Test ThresholdAlerting...")
        
        try:
            alerting = ThresholdAlertingService()
            
            # Test d'évaluation globale
            result = asyncio.run(alerting.evaluate_all_devices_thresholds())
            
            self.results['integration_tests']['threshold_alerting'] = {
                'status': 'PASS' if 'total_devices' in result else 'FAIL',
                'total_devices': result.get('total_devices', 0),
                'total_alerts_generated': result.get('total_alerts_generated', 0),
                'devices_with_alerts': result.get('devices_with_alerts', 0)
            }
            
            print(f"    ✅ ThresholdAlerting - {result.get('total_devices', 0)} équipements évalués")
            
        except Exception as e:
            print(f"    ❌ Erreur ThresholdAlerting: {e}")
            self.results['integration_tests']['threshold_alerting'] = {
                'status': 'ERROR',
                'error': str(e)
            }
    
    def validate_real_data_usage(self):
        """Valide l'utilisation exclusive de données réelles."""
        print("  💾 Validation utilisation données réelles...")
        
        real_data_sources = 0
        total_sources = 0
        
        # Vérifier les sources de données des adaptateurs
        for test_name, test_result in self.results['functional_tests'].items():
            if isinstance(test_result, dict) and 'has_real_data' in test_result:
                total_sources += 1
                if test_result['has_real_data']:
                    real_data_sources += 1
        
        real_data_percentage = (real_data_sources / total_sources * 100) if total_sources > 0 else 0
        
        self.results['data_validation']['real_data_usage'] = {
            'status': 'PASS' if real_data_percentage >= 95.0 else 'FAIL',
            'real_data_sources': real_data_sources,
            'total_sources': total_sources,
            'percentage': real_data_percentage,
            'target_achieved': real_data_percentage >= 95.65
        }
        
        print(f"    📊 Données réelles: {real_data_percentage:.1f}% (objectif: 95.65%)")
        
        if real_data_percentage >= 95.65:
            print("    ✅ Objectif 95.65% de données réelles ATTEINT")
        else:
            print("    ⚠️ Objectif 95.65% de données réelles NON ATTEINT")
    
    def validate_performance(self):
        """Valide les performances du Dashboard."""
        print("  ⚡ Test performance des adaptateurs...")
        
        try:
            import time
            
            # Test performance NetworkAdapter
            start_time = time.time()
            adapter = NetworkAdapter()
            asyncio.run(adapter.get_device_summary())
            network_time = time.time() - start_time
            
            # Test performance MonitoringAdapter
            start_time = time.time()
            adapter = MonitoringAdapter()
            asyncio.run(adapter.get_system_health_metrics())
            monitoring_time = time.time() - start_time
            
            self.results['performance_tests']['adapter_performance'] = {
                'status': 'PASS' if network_time < 5.0 and monitoring_time < 5.0 else 'FAIL',
                'network_adapter_time': network_time,
                'monitoring_adapter_time': monitoring_time,
                'performance_acceptable': network_time < 5.0 and monitoring_time < 5.0
            }
            
            print(f"    ⏱️ NetworkAdapter: {network_time:.2f}s")
            print(f"    ⏱️ MonitoringAdapter: {monitoring_time:.2f}s")
            
            if network_time < 5.0 and monitoring_time < 5.0:
                print("    ✅ Performance acceptable")
            else:
                print("    ⚠️ Performance à améliorer")
                
        except Exception as e:
            print(f"    ❌ Erreur test performance: {e}")
            self.results['performance_tests']['adapter_performance'] = {
                'status': 'ERROR',
                'error': str(e)
            }
    
    def generate_final_report(self) -> Dict[str, Any]:
        """Génère le rapport final de validation."""
        print("\n📊 GÉNÉRATION DU RAPPORT FINAL")
        
        # Calculer les statistiques globales
        total_tests = 0
        passed_tests = 0
        failed_tests = 0
        error_tests = 0
        
        for category, tests in self.results.items():
            for test_name, test_result in tests.items():
                if isinstance(test_result, dict) and 'status' in test_result:
                    total_tests += 1
                    if test_result['status'] == 'PASS':
                        passed_tests += 1
                    elif test_result['status'] == 'FAIL':
                        failed_tests += 1
                    elif test_result['status'] == 'ERROR':
                        error_tests += 1
        
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        final_report = {
            'validation_date': datetime.now().isoformat(),
            'summary': {
                'total_tests': total_tests,
                'passed_tests': passed_tests,
                'failed_tests': failed_tests,
                'error_tests': error_tests,
                'success_rate': success_rate
            },
            'detailed_results': self.results,
            'validation_status': 'PASS' if success_rate >= 90.0 else 'FAIL',
            'ready_for_production': success_rate >= 90.0 and failed_tests == 0
        }
        
        return final_report


def main():
    """Fonction principale de validation."""
    validator = ComprehensiveDashboardValidation()
    report = validator.run_comprehensive_validation()
    
    print("\n" + "=" * 60)
    print("📋 RAPPORT FINAL DE VALIDATION")
    print("=" * 60)
    
    summary = report['summary']
    print(f"📊 Total tests: {summary['total_tests']}")
    print(f"✅ Réussis: {summary['passed_tests']}")
    print(f"❌ Échoués: {summary['failed_tests']}")
    print(f"💥 Erreurs: {summary['error_tests']}")
    print(f"📈 Taux de réussite: {summary['success_rate']:.1f}%")
    
    if report['validation_status'] == 'PASS':
        print("\n🎉 VALIDATION EXHAUSTIVE RÉUSSIE!")
        print("✅ Le module Dashboard est prêt pour les tests finaux")
    else:
        print("\n⚠️ VALIDATION INCOMPLÈTE")
        print("❌ Des améliorations sont nécessaires")
    
    # Sauvegarder le rapport
    report_file = f"dashboard_validation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n📄 Rapport détaillé sauvegardé: {report_file}")
    
    return report['validation_status'] == 'PASS'


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
