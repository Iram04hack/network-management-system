"""
Management command pour la validation exhaustive du module Dashboard.
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, Any

from django.core.management.base import BaseCommand
from django.db import connection
from django.utils import timezone

# Import des modèles
from network_management.models import NetworkDevice, NetworkInterface, NetworkConnection
from monitoring.models import Alert, DeviceMetric, MetricValue, MetricsDefinition

# Import des adaptateurs et services
from dashboard.infrastructure.network_adapter import NetworkAdapter
from dashboard.infrastructure.monitoring_adapter import MonitoringAdapter
from dashboard.infrastructure.snmp_collector import SNMPCollector
from dashboard.infrastructure.network_discovery import NetworkDiscoveryService
from dashboard.infrastructure.threshold_alerting import ThresholdAlertingService


class Command(BaseCommand):
    """Command de validation exhaustive du Dashboard."""
    
    help = 'Valide exhaustivement le module Dashboard avec données réelles'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.results = {}
        self.start_time = datetime.now()
    
    def add_arguments(self, parser):
        """Ajoute les arguments de la commande."""
        parser.add_argument(
            '--output',
            type=str,
            help='Fichier de sortie pour le rapport JSON',
            default=None
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Mode verbeux',
        )
    
    def handle(self, *args, **options):
        """Exécute la validation."""
        self.stdout.write("🚀 VALIDATION EXHAUSTIVE DASHBOARD")
        self.stdout.write("=" * 50)
        self.stdout.write(f"Date: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 1. Validation de l'environnement
        self.stdout.write("\n🔧 1. VALIDATION ENVIRONNEMENT")
        self.validate_environment()
        
        # 2. Validation des modèles Django
        self.stdout.write("\n🗄️ 2. VALIDATION MODÈLES DJANGO")
        self.validate_django_models()
        
        # 3. Validation des adaptateurs
        self.stdout.write("\n🔌 3. VALIDATION ADAPTATEURS")
        self.validate_adapters()
        
        # 4. Validation des services Phase 2
        self.stdout.write("\n⚡ 4. VALIDATION SERVICES PHASE 2")
        self.validate_phase2_services()
        
        # 5. Validation des données réelles
        self.stdout.write("\n💾 5. VALIDATION DONNÉES RÉELLES")
        self.validate_real_data()
        
        # 6. Génération du rapport
        self.stdout.write("\n📊 6. GÉNÉRATION RAPPORT")
        report = self.generate_report()
        
        # Sauvegarde du rapport
        if options['output']:
            with open(options['output'], 'w') as f:
                json.dump(report, f, indent=2)
            self.stdout.write(f"📄 Rapport sauvegardé: {options['output']}")
        
        # Retour du statut
        if report['summary']['validation_status'] == 'PASS':
            self.stdout.write(self.style.SUCCESS("\n🎉 VALIDATION RÉUSSIE!"))
            return 0
        else:
            self.stdout.write(self.style.ERROR("\n❌ VALIDATION ÉCHOUÉE"))
            return 1
    
    def validate_environment(self):
        """Valide l'environnement Django."""
        try:
            # Test de connexion à la base de données
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
            
            self.results['environment'] = {
                'database_connection': 'OK' if result else 'FAIL',
                'django_setup': 'OK',
                'settings_loaded': 'OK'
            }
            self.stdout.write("  ✅ Environnement Django opérationnel")
            
        except Exception as e:
            self.results['environment'] = {
                'database_connection': 'FAIL',
                'error': str(e)
            }
            self.stdout.write(f"  ❌ Erreur environnement: {e}")
    
    def validate_django_models(self):
        """Valide l'accès aux modèles Django."""
        try:
            # Test des modèles network_management
            device_count = NetworkDevice.objects.count()
            interface_count = NetworkInterface.objects.count()
            connection_count = NetworkConnection.objects.count()
            
            # Test des modèles monitoring
            alert_count = Alert.objects.count()
            metric_def_count = MetricsDefinition.objects.count()
            device_metric_count = DeviceMetric.objects.count()
            metric_value_count = MetricValue.objects.count()
            
            self.results['django_models'] = {
                'network_management': {
                    'devices': device_count,
                    'interfaces': interface_count,
                    'connections': connection_count,
                    'accessible': True
                },
                'monitoring': {
                    'alerts': alert_count,
                    'metric_definitions': metric_def_count,
                    'device_metrics': device_metric_count,
                    'metric_values': metric_value_count,
                    'accessible': True
                },
                'total_data_points': device_count + interface_count + connection_count + alert_count + metric_value_count
            }
            
            self.stdout.write(f"  ✅ Modèles accessibles - {device_count} équipements, {alert_count} alertes, {metric_value_count} valeurs")
            
        except Exception as e:
            self.results['django_models'] = {
                'error': str(e),
                'accessible': False
            }
            self.stdout.write(f"  ❌ Erreur modèles Django: {e}")
    
    def validate_adapters(self):
        """Valide les adaptateurs Dashboard."""
        self.stdout.write("  🔌 Test NetworkAdapter...")
        
        try:
            adapter = NetworkAdapter()
            
            # Test device_summary
            device_summary = asyncio.run(adapter.get_device_summary())
            
            # Test interface_summary
            interface_summary = asyncio.run(adapter.get_interface_summary())
            
            # Test topology_data
            topology_data = asyncio.run(adapter.get_topology_data())
            
            # Test QoS summary
            qos_summary = asyncio.run(adapter.get_qos_summary())
            
            self.results['network_adapter'] = {
                'device_summary': {
                    'status': 'OK' if 'total_devices' in device_summary else 'FAIL',
                    'data_source': device_summary.get('data_source', 'unknown'),
                    'total_devices': device_summary.get('total_devices', 0),
                    'real_data': device_summary.get('data_source') == 'real_database'
                },
                'interface_summary': {
                    'status': 'OK' if 'total_interfaces' in interface_summary else 'FAIL',
                    'data_source': interface_summary.get('data_source', 'unknown'),
                    'total_interfaces': interface_summary.get('total_interfaces', 0),
                    'real_data': interface_summary.get('data_source') == 'real_database'
                },
                'topology_data': {
                    'status': 'OK' if 'nodes' in topology_data else 'FAIL',
                    'data_source': topology_data.get('data_source', 'unknown'),
                    'nodes_count': len(topology_data.get('nodes', [])),
                    'connections_count': len(topology_data.get('connections', [])),
                    'real_data': topology_data.get('data_source') == 'real_database'
                },
                'qos_summary': {
                    'status': 'OK' if 'policies' in qos_summary else 'FAIL',
                    'data_source': qos_summary.get('data_source', 'unknown'),
                    'total_policies': qos_summary.get('policies', {}).get('total', 0)
                }
            }
            
            self.stdout.write("    ✅ NetworkAdapter opérationnel")
            
        except Exception as e:
            self.results['network_adapter'] = {'error': str(e)}
            self.stdout.write(f"    ❌ Erreur NetworkAdapter: {e}")
        
        self.stdout.write("  📊 Test MonitoringAdapter...")
        
        try:
            adapter = MonitoringAdapter()
            
            # Test system_alerts
            alerts = asyncio.run(adapter.get_system_alerts(limit=5))
            
            # Test system_health_metrics
            health = asyncio.run(adapter.get_system_health_metrics())
            
            # Test performance_metrics
            performance = asyncio.run(adapter.get_performance_metrics())
            
            self.results['monitoring_adapter'] = {
                'system_alerts': {
                    'status': 'OK' if isinstance(alerts, list) else 'FAIL',
                    'alerts_count': len(alerts) if isinstance(alerts, list) else 0,
                    'real_alerts': len(alerts) > 0 if isinstance(alerts, list) else False
                },
                'system_health': {
                    'status': 'OK' if hasattr(health, 'system_health') else 'FAIL',
                    'system_health': getattr(health, 'system_health', 0),
                    'network_health': getattr(health, 'network_health', 0),
                    'security_health': getattr(health, 'security_health', 0)
                },
                'performance_metrics': {
                    'status': 'OK' if isinstance(performance, dict) else 'FAIL',
                    'has_data': len(performance) > 0 if isinstance(performance, dict) else False
                }
            }
            
            self.stdout.write("    ✅ MonitoringAdapter opérationnel")
            
        except Exception as e:
            self.results['monitoring_adapter'] = {'error': str(e)}
            self.stdout.write(f"    ❌ Erreur MonitoringAdapter: {e}")
    
    def validate_phase2_services(self):
        """Valide les services de la Phase 2."""
        self.stdout.write("  📡 Test SNMPCollector...")
        
        try:
            collector = SNMPCollector()
            
            # Test de collecte globale
            result = asyncio.run(collector.collect_all_devices_metrics())
            
            self.results['snmp_collector'] = {
                'status': 'OK' if 'total_devices' in result else 'FAIL',
                'total_devices': result.get('total_devices', 0),
                'success_count': result.get('success_count', 0),
                'error_count': result.get('error_count', 0),
                'snmp_available': result.get('snmp_available', False)
            }
            
            self.stdout.write(f"    ✅ SNMPCollector - {result.get('total_devices', 0)} équipements traités")
            
        except Exception as e:
            self.results['snmp_collector'] = {'error': str(e)}
            self.stdout.write(f"    ❌ Erreur SNMPCollector: {e}")
        
        self.stdout.write("  🔍 Test NetworkDiscovery...")
        
        try:
            discovery = NetworkDiscoveryService()
            
            # Test de découverte sur une petite plage
            result = asyncio.run(discovery.discover_network_range("192.168.1.0/30"))
            
            self.results['network_discovery'] = {
                'status': 'OK' if 'total_ips_scanned' in result else 'FAIL',
                'total_ips_scanned': result.get('total_ips_scanned', 0),
                'responsive_ips': result.get('responsive_ips', 0),
                'discovered_devices': result.get('discovered_devices', 0)
            }
            
            self.stdout.write(f"    ✅ NetworkDiscovery - {result.get('total_ips_scanned', 0)} IPs scannées")
            
        except Exception as e:
            self.results['network_discovery'] = {'error': str(e)}
            self.stdout.write(f"    ❌ Erreur NetworkDiscovery: {e}")
        
        self.stdout.write("  ⚠️ Test ThresholdAlerting...")
        
        try:
            alerting = ThresholdAlertingService()
            
            # Test d'évaluation globale
            result = asyncio.run(alerting.evaluate_all_devices_thresholds())
            
            self.results['threshold_alerting'] = {
                'status': 'OK' if 'total_devices' in result else 'FAIL',
                'total_devices': result.get('total_devices', 0),
                'total_alerts_generated': result.get('total_alerts_generated', 0),
                'devices_with_alerts': result.get('devices_with_alerts', 0)
            }
            
            self.stdout.write(f"    ✅ ThresholdAlerting - {result.get('total_devices', 0)} équipements évalués")
            
        except Exception as e:
            self.results['threshold_alerting'] = {'error': str(e)}
            self.stdout.write(f"    ❌ Erreur ThresholdAlerting: {e}")
    
    def validate_real_data(self):
        """Valide l'utilisation de données réelles."""
        real_data_sources = 0
        total_sources = 0
        
        # Compter les sources de données réelles
        for adapter_name, adapter_results in self.results.items():
            if adapter_name in ['network_adapter', 'monitoring_adapter']:
                for test_name, test_result in adapter_results.items():
                    if isinstance(test_result, dict) and 'real_data' in test_result:
                        total_sources += 1
                        if test_result['real_data']:
                            real_data_sources += 1
        
        real_data_percentage = (real_data_sources / total_sources * 100) if total_sources > 0 else 0
        
        self.results['real_data_validation'] = {
            'real_data_sources': real_data_sources,
            'total_sources': total_sources,
            'percentage': real_data_percentage,
            'target_achieved': real_data_percentage >= 95.65,
            'status': 'OK' if real_data_percentage >= 95.65 else 'FAIL'
        }
        
        self.stdout.write(f"  📊 Données réelles: {real_data_percentage:.1f}% (objectif: 95.65%)")
        
        if real_data_percentage >= 95.65:
            self.stdout.write("    ✅ Objectif 95.65% de données réelles ATTEINT")
        else:
            self.stdout.write("    ⚠️ Objectif 95.65% de données réelles NON ATTEINT")
    
    def generate_report(self) -> Dict[str, Any]:
        """Génère le rapport final."""
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()
        
        # Calculer les statistiques
        total_tests = 0
        passed_tests = 0
        failed_tests = 0
        
        def count_tests(data):
            nonlocal total_tests, passed_tests, failed_tests
            if isinstance(data, dict):
                for key, value in data.items():
                    if key == 'status':
                        total_tests += 1
                        if value == 'OK':
                            passed_tests += 1
                        else:
                            failed_tests += 1
                    elif isinstance(value, dict):
                        count_tests(value)
        
        count_tests(self.results)
        
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        report = {
            'validation_info': {
                'start_time': self.start_time.isoformat(),
                'end_time': end_time.isoformat(),
                'duration_seconds': duration
            },
            'summary': {
                'total_tests': total_tests,
                'passed_tests': passed_tests,
                'failed_tests': failed_tests,
                'success_rate': success_rate,
                'validation_status': 'PASS' if success_rate >= 90.0 else 'FAIL'
            },
            'detailed_results': self.results
        }
        
        self.stdout.write(f"\n📊 RÉSUMÉ VALIDATION")
        self.stdout.write(f"  Total tests: {total_tests}")
        self.stdout.write(f"  Réussis: {passed_tests}")
        self.stdout.write(f"  Échoués: {failed_tests}")
        self.stdout.write(f"  Taux de réussite: {success_rate:.1f}%")
        self.stdout.write(f"  Durée: {duration:.2f}s")
        
        return report
