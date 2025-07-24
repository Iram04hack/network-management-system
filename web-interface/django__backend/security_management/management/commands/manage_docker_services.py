"""
Commande Django pour la gestion et maintenance des services Docker de sécurité.

Cette commande effectue :
- La surveillance de santé des services Docker
- La synchronisation des configurations
- Le redémarrage automatique des services défaillants
- La collecte de métriques et diagnostics
"""

import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.conf import settings
from django.core.cache import cache

from ...infrastructure.docker_integration import (
    SuricataDockerAdapter, Fail2BanDockerAdapter, TrafficControlDockerAdapter
)
from ...models import AuditLogModel

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Commande de gestion des services Docker de sécurité.
    
    Usage:
        python manage.py manage_docker_services [options]
    """
    
    help = 'Gère et maintient les services Docker de sécurité (Suricata, Fail2Ban, Traffic Control)'
    
    def __init__(self):
        super().__init__()
        # Initialiser les adaptateurs Docker
        self.docker_services = {
            'suricata': SuricataDockerAdapter(),
            'fail2ban': Fail2BanDockerAdapter(),
            'traffic_control': TrafficControlDockerAdapter()
        }
        
        # Statistiques de gestion
        self.management_stats = {
            'services_checked': 0,
            'services_healthy': 0,
            'services_restarted': 0,
            'configurations_synced': 0,
            'errors_encountered': 0
        }
    
    def add_arguments(self, parser):
        """Ajoute les arguments de la commande."""
        parser.add_argument(
            '--action',
            choices=['status', 'health-check', 'restart', 'sync-config', 'monitor', 'diagnose'],
            default='status',
            help='Action à effectuer (default: status)'
        )
        
        parser.add_argument(
            '--service',
            choices=['suricata', 'fail2ban', 'traffic_control', 'all'],
            default='all',
            help='Service cible (default: all)'
        )
        
        parser.add_argument(
            '--auto-restart',
            action='store_true',
            help='Redémarre automatiquement les services défaillants'
        )
        
        parser.add_argument(
            '--monitor-duration',
            type=int,
            default=60,
            help='Durée de surveillance en secondes (default: 60)'
        )
        
        parser.add_argument(
            '--config-file',
            type=str,
            help='Fichier de configuration à synchroniser'
        )
        
        parser.add_argument(
            '--output-format',
            choices=['text', 'json'],
            default='text',
            help='Format de sortie (default: text)'
        )
        
        parser.add_argument(
            '--export-metrics',
            type=str,
            help='Chemin pour exporter les métriques'
        )
        
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Mode verbeux'
        )
    
    def handle(self, *args, **options):
        """Point d'entrée principal de la commande."""
        try:
            self.verbosity = options.get('verbosity', 1)
            self.verbose = options.get('verbose', False)
            
            start_time = timezone.now()
            
            if self.verbose:
                self.stdout.write(
                    self.style.SUCCESS(f'🐳 Gestion des services Docker - {start_time}')
                )
            
            action = options['action']
            service = options['service']
            
            # Sélectionner les services à traiter
            services_to_process = self._get_services_to_process(service)
            
            # Exécuter l'action demandée
            if action == 'status':
                results = self._check_services_status(services_to_process)
            elif action == 'health-check':
                results = self._perform_health_check(services_to_process)
            elif action == 'restart':
                results = self._restart_services(services_to_process)
            elif action == 'sync-config':
                results = self._sync_configurations(services_to_process, options.get('config_file'))
            elif action == 'monitor':
                results = self._monitor_services(
                    services_to_process, 
                    options['monitor_duration'],
                    options.get('auto_restart', False)
                )
            elif action == 'diagnose':
                results = self._diagnose_services(services_to_process)
            else:
                raise CommandError(f'Action non supportée: {action}')
            
            # Afficher les résultats
            end_time = timezone.now()
            duration = end_time - start_time
            
            self._display_results(results, options['output_format'], duration)
            
            # Exporter les métriques si demandé
            if options.get('export_metrics'):
                self._export_metrics(results, options['export_metrics'])
            
            # Auto-restart si nécessaire
            if options.get('auto_restart') and action != 'restart':
                unhealthy_services = [
                    name for name, data in results.items() 
                    if isinstance(data, dict) and not data.get('healthy', True)
                ]
                if unhealthy_services:
                    self.stdout.write(
                        self.style.WARNING(f'🔄 Redémarrage automatique de {len(unhealthy_services)} services...')
                    )
                    restart_results = self._restart_services(unhealthy_services)
                    results['auto_restart'] = restart_results
            
            # Audit log
            self._log_management_audit(action, service, options)
            
            if self.verbose:
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Gestion terminée en {duration.total_seconds():.2f}s')
                )
            
        except Exception as e:
            logger.error(f"Erreur lors de la gestion des services Docker: {str(e)}")
            raise CommandError(f'Erreur lors de la gestion: {str(e)}')
    
    def _get_services_to_process(self, service_param: str) -> List[str]:
        """Retourne la liste des services à traiter."""
        if service_param == 'all':
            return list(self.docker_services.keys())
        else:
            return [service_param]
    
    def _check_services_status(self, services: List[str]) -> Dict[str, Any]:
        """Vérifie le statut de base des services."""
        results = {}
        
        for service_name in services:
            if service_name not in self.docker_services:
                results[service_name] = {'error': 'Service non reconnu'}
                continue
            
            adapter = self.docker_services[service_name]
            self.management_stats['services_checked'] += 1
            
            try:
                # Test de connexion basique
                is_connected = adapter.test_connection()
                
                # Récupération du statut détaillé
                service_status = {}
                if hasattr(adapter, 'get_service_status'):
                    service_status = adapter.get_service_status()
                
                results[service_name] = {
                    'connected': is_connected,
                    'status': service_status,
                    'last_check': timezone.now().isoformat()
                }
                
                if is_connected:
                    self.management_stats['services_healthy'] += 1
                
                if self.verbose:
                    status_icon = "✅" if is_connected else "❌"
                    self.stdout.write(f"{status_icon} {service_name}: {'Connecté' if is_connected else 'Déconnecté'}")
                
            except Exception as e:
                self.management_stats['errors_encountered'] += 1
                results[service_name] = {
                    'connected': False,
                    'error': str(e),
                    'last_check': timezone.now().isoformat()
                }
                
                if self.verbose:
                    self.stdout.write(
                        self.style.ERROR(f"❌ {service_name}: Erreur - {str(e)}")
                    )
        
        return results
    
    def _perform_health_check(self, services: List[str]) -> Dict[str, Any]:
        """Effectue un contrôle de santé approfondi."""
        results = {}
        
        for service_name in services:
            if service_name not in self.docker_services:
                results[service_name] = {'error': 'Service non reconnu'}
                continue
            
            adapter = self.docker_services[service_name]
            self.management_stats['services_checked'] += 1
            
            try:
                health_check = {
                    'service_name': service_name,
                    'timestamp': timezone.now().isoformat(),
                    'tests': {}
                }
                
                # Test 1: Connexion de base
                connection_test = adapter.test_connection()
                health_check['tests']['connection'] = {
                    'passed': connection_test,
                    'description': 'Test de connexion HTTP'
                }
                
                # Test 2: Statut du service
                if connection_test:
                    try:
                        status = adapter.get_service_status() if hasattr(adapter, 'get_service_status') else {}
                        health_check['tests']['service_status'] = {
                            'passed': bool(status),
                            'description': 'Récupération du statut du service',
                            'data': status
                        }
                    except Exception as e:
                        health_check['tests']['service_status'] = {
                            'passed': False,
                            'description': 'Récupération du statut du service',
                            'error': str(e)
                        }
                    
                    # Test 3: Santé spécifique au service
                    if hasattr(adapter, 'get_health_check'):
                        try:
                            service_health = adapter.get_health_check()
                            health_check['tests']['service_health'] = {
                                'passed': service_health.get('healthy', False),
                                'description': 'Contrôle de santé spécifique',
                                'data': service_health
                            }
                        except Exception as e:
                            health_check['tests']['service_health'] = {
                                'passed': False,
                                'description': 'Contrôle de santé spécifique',
                                'error': str(e)
                            }
                    
                    # Test 4: Temps de réponse
                    start_time = time.time()
                    try:
                        adapter.call_api('/status' if hasattr(adapter, 'call_api') else '/', method='GET')
                        response_time = (time.time() - start_time) * 1000  # en ms
                        health_check['tests']['response_time'] = {
                            'passed': response_time < 5000,  # moins de 5s
                            'description': 'Temps de réponse API',
                            'response_time_ms': response_time
                        }
                    except Exception as e:
                        health_check['tests']['response_time'] = {
                            'passed': False,
                            'description': 'Temps de réponse API',
                            'error': str(e)
                        }
                
                # Calculer le score de santé global
                total_tests = len(health_check['tests'])
                passed_tests = sum(1 for test in health_check['tests'].values() if test['passed'])
                health_score = (passed_tests / total_tests) if total_tests > 0 else 0
                
                health_check['health_score'] = health_score
                health_check['overall_health'] = 'healthy' if health_score >= 0.8 else 'degraded' if health_score >= 0.5 else 'unhealthy'
                
                results[service_name] = health_check
                
                if health_score >= 0.8:
                    self.management_stats['services_healthy'] += 1
                
                if self.verbose:
                    health_icon = "💚" if health_score >= 0.8 else "💛" if health_score >= 0.5 else "❤️"
                    self.stdout.write(
                        f"{health_icon} {service_name}: Score de santé {health_score:.2f} ({health_check['overall_health']})"
                    )
                    
                    for test_name, test_result in health_check['tests'].items():
                        test_icon = "✅" if test_result['passed'] else "❌"
                        self.stdout.write(f"    {test_icon} {test_result['description']}")
                
            except Exception as e:
                self.management_stats['errors_encountered'] += 1
                results[service_name] = {
                    'error': str(e),
                    'timestamp': timezone.now().isoformat(),
                    'overall_health': 'error'
                }
                
                if self.verbose:
                    self.stdout.write(
                        self.style.ERROR(f"❌ {service_name}: Erreur lors du contrôle de santé - {str(e)}")
                    )
        
        return results
    
    def _restart_services(self, services: List[str]) -> Dict[str, Any]:
        """Redémarre les services spécifiés."""
        results = {}
        
        for service_name in services:
            if service_name not in self.docker_services:
                results[service_name] = {'error': 'Service non reconnu'}
                continue
            
            adapter = self.docker_services[service_name]
            
            try:
                if self.verbose:
                    self.stdout.write(f"🔄 Redémarrage de {service_name}...")
                
                # Tentative de redémarrage via l'API du service
                restart_result = {'success': False}
                
                if hasattr(adapter, 'restart_service'):
                    restart_result = adapter.restart_service()
                else:
                    # Fallback: test de reconnexion après un délai
                    time.sleep(2)
                    if adapter.test_connection():
                        restart_result = {'success': True, 'method': 'reconnection_test'}
                
                results[service_name] = {
                    'restarted': restart_result.get('success', False),
                    'timestamp': timezone.now().isoformat(),
                    'details': restart_result
                }
                
                if restart_result.get('success'):
                    self.management_stats['services_restarted'] += 1
                    
                    if self.verbose:
                        self.stdout.write(
                            self.style.SUCCESS(f"✅ {service_name}: Redémarrage réussi")
                        )
                else:
                    if self.verbose:
                        self.stdout.write(
                            self.style.ERROR(f"❌ {service_name}: Échec du redémarrage")
                        )
                
            except Exception as e:
                self.management_stats['errors_encountered'] += 1
                results[service_name] = {
                    'restarted': False,
                    'error': str(e),
                    'timestamp': timezone.now().isoformat()
                }
                
                if self.verbose:
                    self.stdout.write(
                        self.style.ERROR(f"❌ {service_name}: Erreur lors du redémarrage - {str(e)}")
                    )
        
        return results
    
    def _sync_configurations(self, services: List[str], config_file: Optional[str] = None) -> Dict[str, Any]:
        """Synchronise les configurations des services."""
        results = {}
        
        for service_name in services:
            if service_name not in self.docker_services:
                results[service_name] = {'error': 'Service non reconnu'}
                continue
            
            adapter = self.docker_services[service_name]
            
            try:
                if self.verbose:
                    self.stdout.write(f"🔧 Synchronisation de la configuration de {service_name}...")
                
                sync_result = {'synced': False}
                
                # Si un fichier de configuration est fourni
                if config_file:
                    try:
                        with open(config_file, 'r') as f:
                            config_content = f.read()
                        
                        if hasattr(adapter, 'update_configuration'):
                            sync_result = adapter.update_configuration(config_content)
                        elif hasattr(adapter, 'validate_configuration'):
                            # Au minimum, valider la configuration
                            validation = adapter.validate_configuration(config_content)
                            sync_result = {
                                'synced': validation.get('valid', False),
                                'validation': validation
                            }
                    except FileNotFoundError:
                        sync_result = {'synced': False, 'error': 'Fichier de configuration non trouvé'}
                else:
                    # Synchronisation automatique (récupération de la configuration actuelle)
                    if hasattr(adapter, 'get_configuration'):
                        current_config = adapter.get_configuration()
                        sync_result = {
                            'synced': True,
                            'method': 'config_retrieval',
                            'config_retrieved': bool(current_config)
                        }
                
                results[service_name] = {
                    'synchronized': sync_result.get('synced', False),
                    'timestamp': timezone.now().isoformat(),
                    'details': sync_result
                }
                
                if sync_result.get('synced'):
                    self.management_stats['configurations_synced'] += 1
                    
                    if self.verbose:
                        self.stdout.write(
                            self.style.SUCCESS(f"✅ {service_name}: Configuration synchronisée")
                        )
                else:
                    if self.verbose:
                        error_msg = sync_result.get('error', 'Échec de la synchronisation')
                        self.stdout.write(
                            self.style.ERROR(f"❌ {service_name}: {error_msg}")
                        )
                
            except Exception as e:
                self.management_stats['errors_encountered'] += 1
                results[service_name] = {
                    'synchronized': False,
                    'error': str(e),
                    'timestamp': timezone.now().isoformat()
                }
                
                if self.verbose:
                    self.stdout.write(
                        self.style.ERROR(f"❌ {service_name}: Erreur lors de la synchronisation - {str(e)}")
                    )
        
        return results
    
    def _monitor_services(self, services: List[str], duration: int, auto_restart: bool = False) -> Dict[str, Any]:
        """Surveille les services pendant une durée donnée."""
        if self.verbose:
            self.stdout.write(f"👁️  Surveillance des services pendant {duration} secondes...")
        
        monitoring_data = {
            'monitoring_period': {
                'start_time': timezone.now().isoformat(),
                'duration_seconds': duration
            },
            'services': {},
            'events': []
        }
        
        # Initialiser les données de surveillance
        for service_name in services:
            monitoring_data['services'][service_name] = {
                'checks_performed': 0,
                'successful_checks': 0,
                'failed_checks': 0,
                'response_times': [],
                'status_changes': []
            }
        
        start_time = time.time()
        check_interval = min(10, duration // 10)  # Au moins 10 vérifications
        
        while (time.time() - start_time) < duration:
            for service_name in services:
                if service_name not in self.docker_services:
                    continue
                
                adapter = self.docker_services[service_name]
                service_data = monitoring_data['services'][service_name]
                
                try:
                    check_start = time.time()
                    is_healthy = adapter.test_connection()
                    response_time = (time.time() - check_start) * 1000  # en ms
                    
                    service_data['checks_performed'] += 1
                    service_data['response_times'].append(response_time)
                    
                    if is_healthy:
                        service_data['successful_checks'] += 1
                    else:
                        service_data['failed_checks'] += 1
                        
                        # Enregistrer l'événement de panne
                        event = {
                            'timestamp': timezone.now().isoformat(),
                            'service': service_name,
                            'event_type': 'service_down',
                            'details': {'response_time_ms': response_time}
                        }
                        monitoring_data['events'].append(event)
                        
                        if self.verbose:
                            self.stdout.write(
                                self.style.ERROR(f"❌ {service_name}: Service indisponible")
                            )
                        
                        # Auto-restart si activé
                        if auto_restart:
                            if self.verbose:
                                self.stdout.write(f"🔄 Redémarrage automatique de {service_name}...")
                            
                            restart_results = self._restart_services([service_name])
                            if restart_results.get(service_name, {}).get('restarted'):
                                event = {
                                    'timestamp': timezone.now().isoformat(),
                                    'service': service_name,
                                    'event_type': 'auto_restart',
                                    'details': restart_results[service_name]
                                }
                                monitoring_data['events'].append(event)
                                self.management_stats['services_restarted'] += 1
                
                except Exception as e:
                    service_data['checks_performed'] += 1
                    service_data['failed_checks'] += 1
                    
                    event = {
                        'timestamp': timezone.now().isoformat(),
                        'service': service_name,
                        'event_type': 'check_error',
                        'details': {'error': str(e)}
                    }
                    monitoring_data['events'].append(event)
            
            # Affichage périodique du statut
            if self.verbose and int(time.time() - start_time) % 30 == 0:
                elapsed = int(time.time() - start_time)
                remaining = duration - elapsed
                self.stdout.write(f"⏱️  Surveillance en cours... {remaining}s restantes")
            
            time.sleep(check_interval)
        
        # Finaliser les statistiques
        monitoring_data['monitoring_period']['end_time'] = timezone.now().isoformat()
        
        for service_name, service_data in monitoring_data['services'].items():
            if service_data['checks_performed'] > 0:
                service_data['availability'] = service_data['successful_checks'] / service_data['checks_performed']
                
                if service_data['response_times']:
                    service_data['avg_response_time'] = sum(service_data['response_times']) / len(service_data['response_times'])
                    service_data['max_response_time'] = max(service_data['response_times'])
                    service_data['min_response_time'] = min(service_data['response_times'])
        
        if self.verbose:
            self.stdout.write(self.style.SUCCESS("✅ Surveillance terminée"))
            
            # Affichage des statistiques
            for service_name, service_data in monitoring_data['services'].items():
                availability = service_data.get('availability', 0) * 100
                avg_response = service_data.get('avg_response_time', 0)
                
                self.stdout.write(
                    f"📊 {service_name}: Disponibilité {availability:.1f}%, "
                    f"Temps de réponse moyen {avg_response:.1f}ms"
                )
        
        return monitoring_data
    
    def _diagnose_services(self, services: List[str]) -> Dict[str, Any]:
        """Effectue un diagnostic approfondi des services."""
        results = {}
        
        for service_name in services:
            if service_name not in self.docker_services:
                results[service_name] = {'error': 'Service non reconnu'}
                continue
            
            adapter = self.docker_services[service_name]
            
            if self.verbose:
                self.stdout.write(f"🔍 Diagnostic de {service_name}...")
            
            diagnosis = {
                'service_name': service_name,
                'timestamp': timezone.now().isoformat(),
                'connectivity': {},
                'performance': {},
                'configuration': {},
                'logs': {},
                'recommendations': []
            }
            
            try:
                # Test de connectivité
                diagnosis['connectivity']['reachable'] = adapter.test_connection()
                
                if diagnosis['connectivity']['reachable']:
                    # Tests de performance
                    response_times = []
                    for i in range(5):  # 5 tests de ping
                        start_time = time.time()
                        try:
                            adapter.test_connection()
                            response_time = (time.time() - start_time) * 1000
                            response_times.append(response_time)
                        except:
                            pass
                        time.sleep(0.5)
                    
                    if response_times:
                        diagnosis['performance'] = {
                            'avg_response_time': sum(response_times) / len(response_times),
                            'max_response_time': max(response_times),
                            'min_response_time': min(response_times),
                            'response_times': response_times
                        }
                        
                        # Recommandations basées sur la performance
                        avg_time = diagnosis['performance']['avg_response_time']
                        if avg_time > 2000:
                            diagnosis['recommendations'].append("Performance dégradée - temps de réponse élevé")
                        elif avg_time > 1000:
                            diagnosis['recommendations'].append("Performance acceptable mais surveiller")
                    
                    # Test de configuration
                    if hasattr(adapter, 'get_configuration'):
                        try:
                            config = adapter.get_configuration()
                            diagnosis['configuration']['retrievable'] = bool(config)
                            if config:
                                diagnosis['configuration']['size'] = len(str(config))
                        except Exception as e:
                            diagnosis['configuration']['error'] = str(e)
                    
                    # Récupération des logs si disponible
                    if hasattr(adapter, 'get_logs'):
                        try:
                            logs = adapter.get_logs()
                            diagnosis['logs']['retrievable'] = bool(logs)
                            if logs:
                                diagnosis['logs']['recent_entries'] = len(logs)
                        except Exception as e:
                            diagnosis['logs']['error'] = str(e)
                
                else:
                    diagnosis['recommendations'].append("Service non accessible - vérifier l'état du conteneur")
                
                # Recommandations générales
                if not diagnosis['recommendations']:
                    diagnosis['recommendations'].append("Service opérationnel - aucune action requise")
                
                results[service_name] = diagnosis
                
                if self.verbose:
                    reachable = diagnosis['connectivity']['reachable']
                    icon = "✅" if reachable else "❌"
                    self.stdout.write(f"{icon} {service_name}: {'Accessible' if reachable else 'Inaccessible'}")
                    
                    for rec in diagnosis['recommendations']:
                        self.stdout.write(f"    💡 {rec}")
                
            except Exception as e:
                self.management_stats['errors_encountered'] += 1
                results[service_name] = {
                    'error': str(e),
                    'timestamp': timezone.now().isoformat()
                }
                
                if self.verbose:
                    self.stdout.write(
                        self.style.ERROR(f"❌ {service_name}: Erreur lors du diagnostic - {str(e)}")
                    )
        
        return results
    
    def _display_results(self, results: Dict[str, Any], output_format: str, duration: timedelta):
        """Affiche les résultats de la gestion."""
        if output_format == 'json':
            output = {
                'results': results,
                'management_stats': self.management_stats,
                'duration_seconds': duration.total_seconds(),
                'timestamp': timezone.now().isoformat()
            }
            self.stdout.write(json.dumps(output, indent=2, ensure_ascii=False))
        else:
            # Affichage texte formaté
            self.stdout.write(self.style.SUCCESS("\n🐳 RAPPORT DE GESTION DES SERVICES DOCKER"))
            self.stdout.write("=" * 60)
            
            # Résumé des statistiques
            self.stdout.write(f"\n📊 STATISTIQUES")
            self.stdout.write(f"   Durée d'exécution: {duration.total_seconds():.2f}s")
            self.stdout.write(f"   Services vérifiés: {self.management_stats['services_checked']}")
            self.stdout.write(f"   Services sains: {self.management_stats['services_healthy']}")
            self.stdout.write(f"   Services redémarrés: {self.management_stats['services_restarted']}")
            self.stdout.write(f"   Configurations synchronisées: {self.management_stats['configurations_synced']}")
            self.stdout.write(f"   Erreurs rencontrées: {self.management_stats['errors_encountered']}")
            
            # Résultats détaillés
            self.stdout.write(f"\n🔍 RÉSULTATS DÉTAILLÉS")
            for service_name, result in results.items():
                if isinstance(result, dict):
                    if 'error' in result:
                        self.stdout.write(
                            self.style.ERROR(f"   ❌ {service_name}: {result['error']}")
                        )
                    elif 'overall_health' in result:
                        health = result['overall_health']
                        icon = "💚" if health == 'healthy' else "💛" if health == 'degraded' else "❤️"
                        self.stdout.write(f"   {icon} {service_name}: {health}")
                    elif 'connected' in result:
                        icon = "✅" if result['connected'] else "❌"
                        self.stdout.write(f"   {icon} {service_name}: {'Connecté' if result['connected'] else 'Déconnecté'}")
                    else:
                        self.stdout.write(f"   ℹ️  {service_name}: Données disponibles")
            
            self.stdout.write("\n" + "=" * 60)
    
    def _export_metrics(self, results: Dict[str, Any], file_path: str):
        """Exporte les métriques vers un fichier."""
        try:
            metrics_data = {
                'export_timestamp': timezone.now().isoformat(),
                'management_stats': self.management_stats,
                'service_results': results,
                'system_info': {
                    'docker_services_configured': len(self.docker_services),
                    'services_available': list(self.docker_services.keys())
                }
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(metrics_data, f, indent=2, ensure_ascii=False, default=str)
            
            self.stdout.write(
                self.style.SUCCESS(f"📄 Métriques exportées vers: {file_path}")
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"❌ Erreur lors de l'export des métriques: {str(e)}")
            )
    
    def _log_management_audit(self, action: str, service: str, options: Dict[str, Any]):
        """Enregistre l'audit de la gestion."""
        try:
            audit_details = {
                'command': 'manage_docker_services',
                'action': action,
                'target_service': service,
                'options': {k: v for k, v in options.items() if k not in ['verbosity', 'settings']},
                'stats': self.management_stats.copy(),
                'timestamp': timezone.now().isoformat()
            }
            
            AuditLogModel.objects.create(
                action=f'docker_management_{action}',
                target_type='docker_services',
                target_id=0,  # Global management
                user_id=None,  # System command
                ip_address='127.0.0.1',
                user_agent='Django Management Command',
                details=audit_details
            )
            
        except Exception as e:
            if self.verbose:
                self.stdout.write(
                    self.style.WARNING(f"⚠️  Erreur lors de l'audit: {str(e)}")
                )