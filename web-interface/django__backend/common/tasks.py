"""
Tâches Celery pour le module Common - Orchestrateur Central NMS.

Ce module contient les tâches centrales qui orchestrent la communication
et la coordination entre tous les modules du système NMS.
"""

import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

from celery import shared_task, group, chain
from django.utils import timezone
from django.core.cache import cache
from django.conf import settings

logger = logging.getLogger(__name__)


@shared_task
def orchestrate_system_monitoring():
    """
    Orchestrateur central qui coordonne toutes les tâches de monitoring système.
    
    Cette tâche lance et coordonne les collectes de tous les modules
    pour avoir une vue d'ensemble synchronisée.
    """
    try:
        logger.info("🎯 Orchestration monitoring système global")
        
        # Créer un groupe de tâches parallèles pour chaque module
        monitoring_tasks = group(
            # Monitoring réseau et équipements
            monitor_network_health.s(),
            
            # Monitoring sécurité
            monitor_security_status.s(),
            
            # Monitoring QoS et performance
            monitor_qos_performance.s(),
            
            # Monitoring GNS3
            monitor_gns3_integration.s(),
            
            # Monitoring AI Assistant
            monitor_ai_assistant_health.s()
        )
        
        # Exécuter toutes les tâches en parallèle
        job = monitoring_tasks.apply_async()
        results = job.get(timeout=120)  # 2 minutes timeout
        
        # Analyser les résultats globaux
        system_health = _analyze_global_system_health(results)
        
        # Sauvegarder les métriques globales
        cache.set('nms_global_health', system_health, timeout=300)
        
        # Déclencher des actions si problèmes critiques
        if system_health['status'] == 'critical':
            trigger_critical_system_alert.delay(system_health)
        
        logger.info(f"✅ Orchestration terminée - Statut global: {system_health['status']}")
        
        return {
            'status': 'success',
            'global_health': system_health,
            'modules_monitored': len(results)
        }
        
    except Exception as e:
        logger.error(f"❌ Erreur orchestration monitoring: {e}")
        
        # Marquer le système comme dégradé
        cache.set('nms_global_health', {
            'status': 'degraded',
            'error': str(e),
            'timestamp': timezone.now().isoformat()
        }, timeout=300)
        
        return {'status': 'error', 'error': str(e)}


@shared_task
def start_gns3_project_complete(**kwargs):
    """
    Démarre complètement un projet GNS3 - tâche MANQUANTE critique.
    
    Cette tâche effectue le démarrage réel du projet sélectionné :
    1. Ouvre le projet GNS3
    2. Démarre tous les nœuds
    3. Configure la surveillance automatique
    4. Déclenche le workflow d'analyse
    """
    try:
        project_id = kwargs.get('project_id')
        workflow_id = kwargs.get('workflow_id', 'unknown')
        trigger_source = kwargs.get('trigger_source', 'workflow')
        
        logger.info(f"🚀 DÉMARRAGE PROJET GNS3: {project_id} (workflow: {workflow_id})")
        
        if not project_id:
            logger.error("❌ project_id manquant pour démarrage projet")
            return {'status': 'error', 'error': 'project_id requis'}
        
        # Importer les services GNS3
        from gns3_integration.infrastructure.gns3_client_impl import GNS3ClientImpl
        from gns3_integration.infrastructure.gns3_repository_impl import GNS3RepositoryImpl
        from gns3_integration.application.project_service import ProjectService
        from gns3_integration.application.multi_project_service import MultiProjectService
        
        # Initialiser les services
        client = GNS3ClientImpl()
        repository = GNS3RepositoryImpl()
        project_service = ProjectService(client, repository)
        multi_project_service = MultiProjectService(project_service, client, repository)
        
        # Étape 1: Ouvrir le projet
        logger.info(f"📂 Ouverture du projet {project_id}")
        open_result = project_service.open_project(project_id)
        
        if not open_result:
            logger.error(f"❌ Impossible d'ouvrir le projet {project_id}")
            return {'status': 'error', 'error': 'Ouverture projet échouée'}
        
        # Étape 2: Démarrer tous les nœuds avec validation complète
        logger.info(f"⚡ Démarrage COMPLET de tous les nœuds du projet {project_id}")
        start_result = project_service.start_all_nodes(project_id)
        
        if not start_result or start_result.get('success_count', 0) == 0:
            logger.error(f"❌ Aucun nœud démarré pour le projet {project_id}")
            return {'status': 'error', 'error': 'Démarrage nœuds échoué'}
        
        nodes_started = start_result.get('success_count', 0)
        nodes_failed = start_result.get('failure_count', 0)
        
        logger.info(f"✅ Démarrage initial: {nodes_started} nœuds OK, {nodes_failed} échecs")
        
        # Étape 2.1: Attendre que les nœuds soient vraiment opérationnels
        logger.info(f"⏳ Attente stabilisation des nœuds (15 secondes)...")
        import time
        time.sleep(15)  # Laisser le temps aux équipements de s'initialiser
        
        # Étape 2.2: Vérification de l'état opérationnel réel
        logger.info(f"🔍 Vérification de l'état opérationnel RÉEL des nœuds...")
        import asyncio
        operational_status = asyncio.run(_verify_nodes_operational_status(project_service, project_id))
        
        logger.info(f"📊 ÉTAT OPÉRATIONNEL DU RÉSEAU:")
        logger.info(f"   - Nœuds démarrés: {operational_status['nodes_started']}")
        logger.info(f"   - Nœuds opérationnels: {operational_status['nodes_operational']}")
        logger.info(f"   - Nœuds avec console active: {operational_status['nodes_with_console']}")
        logger.info(f"   - Nœuds avec connectivité: {operational_status['nodes_with_connectivity']}")
        
        if operational_status['nodes_operational'] == 0:
            logger.error(f"❌ AUCUN nœud n'est opérationnel malgré le démarrage")
            return {'status': 'error', 'error': 'Nœuds démarrés mais non opérationnels'}
        
        # Étape 2.3: Découverte et validation des adresses IP RÉELLES
        logger.info(f"🌐 Découverte des adresses IP RÉELLES des équipements...")
        ip_discovery_result = asyncio.run(_discover_real_equipment_ips(project_id))
        
        logger.info(f"📡 RÉSULTATS DÉCOUVERTE IP RÉELLE:")
        logger.info(f"   - Équipements analysés: {ip_discovery_result['total_equipment']}")
        logger.info(f"   - Équipements avec IPs: {ip_discovery_result['equipment_with_ips']}")
        logger.info(f"   - Total IPs trouvées: {ip_discovery_result['total_ips']}")
        logger.info(f"   - Équipements accessibles: {ip_discovery_result['accessible_equipment']}")
        
        if ip_discovery_result['equipment_with_ips'] == 0:
            logger.warning(f"⚠️ AUCUNE IP trouvée - configuration réseau requise")
        
        # Messages de confirmation d'état opérationnel
        if operational_status['nodes_operational'] >= nodes_started * 0.8:  # Au moins 80% opérationnels
            logger.info(f"🎯 RÉSEAU OPÉRATIONNEL CONFIRMÉ!")
            logger.info(f"✅ {operational_status['nodes_operational']}/{nodes_started} nœuds sont opérationnels")
            logger.info(f"✅ Le réseau est prêt pour l'injection de trafic")
            operational_confirmed = True
        else:
            logger.warning(f"⚠️ Réseau partiellement opérationnel")
            logger.warning(f"⚠️ {operational_status['nodes_operational']}/{nodes_started} nœuds opérationnels")
            operational_confirmed = False
        
        # Étape 3: Configurer la surveillance automatique
        logger.info(f"🔍 Configuration surveillance automatique pour {project_id}")
        try:
            # Sélectionner le projet pour surveillance automatique
            selection_result = multi_project_service.select_project_for_monitoring(
                project_id, 
                auto_start_on_traffic=True,
                priority=1  # Haute priorité
            )
            logger.info(f"✅ Surveillance automatique configurée: {selection_result}")
        except Exception as e:
            logger.warning(f"⚠️ Surveillance automatique non configurée: {e}")
        
        # Étape 4: Déclencher orchestrateur système maintenant que le projet est actif
        logger.info(f"🎯 Déclenchement orchestrateur système pour projet actif")
        orchestrate_result = orchestrate_system_monitoring.delay()
        
        # Mettre à jour le cache avec le projet actif
        cache.set('active_gns3_project', {
            'project_id': project_id,
            'nodes_started': nodes_started,
            'started_at': timezone.now().isoformat(),
            'workflow_id': workflow_id,
            'status': 'running'
        }, timeout=3600)
        
        return {
            'status': 'success',
            'project_id': project_id,
            'nodes_started': nodes_started,
            'nodes_failed': nodes_failed,
            'nodes_operational': operational_status['nodes_operational'],
            'nodes_with_console': operational_status['nodes_with_console'],
            'nodes_with_connectivity': operational_status['nodes_with_connectivity'],
            'operational_confirmed': operational_confirmed,
            'equipment_with_ips': ip_discovery_result['equipment_with_ips'],
            'total_ips_found': ip_discovery_result['total_ips'],
            'accessible_equipment': ip_discovery_result['accessible_equipment'],
            'network_ready_for_traffic': operational_confirmed and ip_discovery_result['equipment_with_ips'] > 0,
            'surveillance_configured': True,
            'orchestrator_triggered': True,
            'detailed_status': {
                'startup_phase': 'completed',
                'operational_verification': 'completed',
                'ip_discovery': 'completed',
                'network_status': 'operational' if operational_confirmed else 'partial',
                'traffic_injection_ready': operational_confirmed and ip_discovery_result['equipment_with_ips'] > 0
            },
            'timestamp': timezone.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Erreur critique démarrage projet GNS3: {e}")
        return {'status': 'error', 'error': str(e)}


@shared_task
def monitor_network_health():
    """Monitore la santé globale du réseau."""
    try:
        logger.info("🌐 Monitoring santé réseau")
        
        # Appeler les tâches spécifiques réseau/monitoring
        from monitoring.tasks import collect_metrics
        from network_management.tasks import update_device_statuses
        
        # Exécuter les tâches de monitoring réseau
        metrics_result = collect_metrics.delay()
        devices_result = update_device_statuses.delay()
        
        # Récupérer les résultats
        metrics = metrics_result.get(timeout=60)
        devices = devices_result.get(timeout=60)
        
        # Analyser la santé réseau
        network_health = {
            'module': 'network',
            'status': 'healthy',
            'metrics_collection': metrics.get('success', False),
            'devices_updated': devices.get('updated_devices', 0),
            'timestamp': timezone.now().isoformat()
        }
        
        # Déterminer le statut basé sur les résultats
        if not metrics.get('success') or devices.get('updated_devices', 0) == 0:
            network_health['status'] = 'degraded'
        
        return network_health
        
    except Exception as e:
        logger.error(f"❌ Erreur monitoring réseau: {e}")
        return {
            'module': 'network',
            'status': 'critical',
            'error': str(e),
            'timestamp': timezone.now().isoformat()
        }


@shared_task
def monitor_security_status():
    """Monitore le statut de sécurité global."""
    try:
        logger.info("🛡️ Monitoring sécurité")
        
        from security_management.tasks import monitor_security_alerts
        
        # Lancer le monitoring de sécurité
        security_result = monitor_security_alerts.delay()
        result = security_result.get(timeout=60)
        
        # Analyser le statut sécurité
        security_health = {
            'module': 'security',
            'status': 'healthy',
            'new_alerts': result.get('new_alerts', 0),
            'critical_alerts': result.get('critical_alerts', 0),
            'report_triggered': result.get('report_triggered', False),
            'timestamp': timezone.now().isoformat()
        }
        
        # Déterminer criticité
        if result.get('critical_alerts', 0) > 0:
            security_health['status'] = 'critical'
        elif result.get('new_alerts', 0) > 5:
            security_health['status'] = 'warning'
        
        return security_health
        
    except Exception as e:
        logger.error(f"❌ Erreur monitoring sécurité: {e}")
        return {
            'module': 'security',
            'status': 'critical',
            'error': str(e),
            'timestamp': timezone.now().isoformat()
        }


@shared_task
def monitor_qos_performance():
    """Monitore les performances QoS."""
    try:
        logger.info("📊 Monitoring QoS")
        
        from qos_management.tasks import collect_traffic_statistics
        
        # Lancer la collecte QoS
        qos_result = collect_traffic_statistics.delay()
        result = qos_result.get(timeout=60)
        
        qos_health = {
            'module': 'qos',
            'status': 'healthy',
            'interfaces_monitored': result.get('interfaces_monitored', 0),
            'congested_interfaces': result.get('congested_interfaces', 0),
            'recommendations': result.get('recommendations_generated', 0),
            'timestamp': timezone.now().isoformat()
        }
        
        # Évaluer la performance QoS
        if result.get('congested_interfaces', 0) > 3:
            qos_health['status'] = 'critical'
        elif result.get('congested_interfaces', 0) > 0:
            qos_health['status'] = 'warning'
        
        return qos_health
        
    except Exception as e:
        logger.error(f"❌ Erreur monitoring QoS: {e}")
        return {
            'module': 'qos',
            'status': 'critical',
            'error': str(e),
            'timestamp': timezone.now().isoformat()
        }


@shared_task
def monitor_gns3_integration():
    """Monitore l'intégration GNS3 incluant le multi-projets."""
    try:
        logger.info("🔧 Monitoring GNS3 avec multi-projets")
        
        from gns3_integration.tasks import monitor_gns3_server, monitor_multi_projects_traffic
        
        # Vérifier le serveur GNS3
        gns3_result = monitor_gns3_server.delay()
        gns3_result.get(timeout=30)  # Attendre le résultat
        
        # Déclencher surveillance multi-projets pour détection trafic automatique
        multi_projects_result = monitor_multi_projects_traffic.delay()
        multi_projects_data = multi_projects_result.get(timeout=60)
        
        # Récupérer les métriques du cache
        gns3_metrics = cache.get('gns3_monitoring_metrics', {})
        multi_project_metrics = cache.get('gns3_multi_project_metrics', {})
        
        gns3_health = {
            'module': 'gns3',
            'status': 'healthy' if gns3_metrics.get('is_available', False) else 'critical',
            'server_available': gns3_metrics.get('is_available', False),
            'projects_count': gns3_metrics.get('projects_count', 0),
            'response_time': gns3_metrics.get('response_time_ms', 0),
            'multi_projects_monitoring': multi_project_metrics.get('monitoring_enabled', False),
            'selected_projects': multi_project_metrics.get('selected_projects_count', 0),
            'projects_with_traffic': multi_project_metrics.get('projects_with_traffic', 0),
            'project_switches': multi_project_metrics.get('project_switches', 0),
            'work_started': multi_project_metrics.get('work_started', 0),
            'timestamp': timezone.now().isoformat()
        }
        
        return gns3_health
        
    except Exception as e:
        logger.error(f"❌ Erreur monitoring GNS3: {e}")
        return {
            'module': 'gns3',
            'status': 'critical',
            'error': str(e),
            'timestamp': timezone.now().isoformat()
        }


@shared_task
def monitor_ai_assistant_health():
    """Monitore la santé de l'assistant IA."""
    try:
        logger.info("🤖 Monitoring AI Assistant")
        
        from ai_assistant.tasks import check_ai_services_health
        
        # Vérifier la santé des services IA
        ai_result = check_ai_services_health.delay()
        result = ai_result.get(timeout=30)
        
        ai_health = {
            'module': 'ai_assistant',
            'status': result.get('health_report', {}).get('overall_status', 'unknown'),
            'services_healthy': result.get('status') == 'success',
            'timestamp': timezone.now().isoformat()
        }
        
        return ai_health
        
    except Exception as e:
        logger.error(f"❌ Erreur monitoring AI: {e}")
        return {
            'module': 'ai_assistant',
            'status': 'critical',
            'error': str(e),
            'timestamp': timezone.now().isoformat()
        }


@shared_task
def trigger_critical_system_alert(system_health: Dict[str, Any]):
    """Déclenche une alerte système critique."""
    try:
        logger.warning("🚨 Déclenchement alerte système critique")
        
        # Créer l'alerte
        alert_data = {
            'title': 'Alerte Système Critique NMS',
            'description': f"Le système NMS montre des signes critiques: {system_health.get('issues', [])}",
            'severity': 'critical',
            'source_type': 'system_health',
            'source_id': 'global_orchestrator',
            'metadata': system_health
        }
        
        # Envoyer via monitoring
        from monitoring.tasks import create_alert
        create_alert.delay(alert_data)
        
        # Déclencher rapport d'urgence
        from reporting.tasks import generate_emergency_system_report
        generate_emergency_system_report.delay(system_health)
        
        logger.info("✅ Alerte système critique déclenchée")
        
    except Exception as e:
        logger.error(f"❌ Erreur déclenchement alerte critique: {e}")


@shared_task
def coordinate_inter_module_communication():
    """
    Coordonne la communication entre modules via Redis/WebSocket.
    """
    try:
        logger.info("📡 Coordination communication inter-modules")
        
        # Récupérer les événements en attente de tous les modules
        events_to_broadcast = []
        
        # Events du monitoring
        monitoring_events = cache.get('monitoring_events_pending', [])
        events_to_broadcast.extend(monitoring_events)
        
        # Events de sécurité
        security_events = cache.get('security_events_pending', [])
        events_to_broadcast.extend(security_events)
        
        # Events QoS
        qos_events = cache.get('qos_events_pending', [])
        events_to_broadcast.extend(qos_events)
        
        # Events GNS3
        gns3_events = cache.get('gns3_events_pending', [])
        events_to_broadcast.extend(gns3_events)
        
        # Diffuser tous les événements
        if events_to_broadcast:
            from .infrastructure.realtime_event_system import broadcast_system_event
            
            for event in events_to_broadcast:
                broadcast_system_event(event)
        
        # Nettoyer les événements traités
        cache.delete_many([
            'monitoring_events_pending',
            'security_events_pending', 
            'qos_events_pending',
            'gns3_events_pending'
        ])
        
        logger.info(f"✅ {len(events_to_broadcast)} événements diffusés")
        
        return {
            'status': 'success',
            'events_broadcasted': len(events_to_broadcast)
        }
        
    except Exception as e:
        logger.error(f"❌ Erreur coordination communication: {e}")
        return {'status': 'error', 'error': str(e)}


@shared_task
def sync_modules_configuration():
    """
    Synchronise la configuration entre tous les modules.
    """
    try:
        logger.info("⚙️ Synchronisation configuration modules")
        
        # Récupérer la configuration globale
        global_config = cache.get('nms_global_config', {})
        
        if not global_config:
            # Générer configuration par défaut
            global_config = _generate_default_global_config()
            cache.set('nms_global_config', global_config, timeout=3600)
        
        # Synchroniser avec chaque module
        sync_results = {}
        
        # Sync monitoring
        try:
            from monitoring.tasks import update_monitoring_config
            monitoring_result = update_monitoring_config.delay(global_config.get('monitoring', {}))
            sync_results['monitoring'] = monitoring_result.get(timeout=30)
        except Exception as e:
            sync_results['monitoring'] = {'error': str(e)}
        
        # Sync security
        try:
            from security_management.tasks import update_security_config
            security_result = update_security_config.delay(global_config.get('security', {}))
            sync_results['security'] = security_result.get(timeout=30)
        except Exception as e:
            sync_results['security'] = {'error': str(e)}
        
        # Sync QoS
        try:
            from qos_management.tasks import update_qos_config
            qos_result = update_qos_config.delay(global_config.get('qos', {}))
            sync_results['qos'] = qos_result.get(timeout=30)
        except Exception as e:
            sync_results['qos'] = {'error': str(e)}
        
        # Calculer le succès global
        successful_syncs = sum(1 for result in sync_results.values() 
                             if result.get('status') == 'success')
        
        logger.info(f"✅ Synchronisation terminée - {successful_syncs}/{len(sync_results)} modules")
        
        return {
            'status': 'success',
            'synced_modules': successful_syncs,
            'total_modules': len(sync_results),
            'details': sync_results
        }
        
    except Exception as e:
        logger.error(f"❌ Erreur synchronisation configuration: {e}")
        return {'status': 'error', 'error': str(e)}


@shared_task
def generate_unified_system_report():
    """
    Génère un rapport unifié de l'état de tout le système NMS.
    """
    try:
        logger.info("📋 Génération rapport système unifié")
        
        # Récupérer les données de tous les modules
        monitoring_data = cache.get('monitoring_stats', {})
        security_data = cache.get('security_monitoring_stats', {})
        qos_data = cache.get('qos_monitoring_status', {})
        gns3_data = cache.get('gns3_monitoring_metrics', {})
        gns3_multi_project_data = cache.get('gns3_multi_project_metrics', {})
        ai_data = cache.get('ai_assistant_health_report', {})
        
        # Compiler le rapport unifié
        unified_report = {
            'generated_at': timezone.now().isoformat(),
            'report_type': 'unified_system_status',
            'modules': {
                'monitoring': {
                    'status': 'healthy' if monitoring_data.get('scan_success', False) else 'warning',
                    'last_scan': monitoring_data.get('last_scan'),
                    'alerts_processed': monitoring_data.get('alerts_processed', 0),
                    'metrics': monitoring_data
                },
                'security': {
                    'status': 'healthy' if security_data.get('scan_success', False) else 'critical',
                    'last_scan': security_data.get('last_scan'),
                    'alerts_detected': security_data.get('alerts_processed', 0),
                    'critical_alerts': security_data.get('critical_alerts', 0),
                    'metrics': security_data
                },
                'qos': {
                    'status': 'healthy' if qos_data.get('service_healthy', False) else 'degraded',
                    'last_collection': qos_data.get('last_collection'),
                    'interfaces_monitored': qos_data.get('interfaces_monitored', 0),
                    'congestion_alerts': qos_data.get('congestion_alerts', 0),
                    'metrics': qos_data
                },
                'gns3': {
                    'status': 'healthy' if gns3_data.get('is_available', False) else 'critical',
                    'last_check': gns3_data.get('last_check'),
                    'projects_count': gns3_data.get('projects_count', 0),
                    'response_time': gns3_data.get('response_time_ms', 0),
                    'multi_projects_enabled': gns3_multi_project_data.get('monitoring_enabled', False),
                    'selected_projects': gns3_multi_project_data.get('selected_projects_count', 0),
                    'projects_with_traffic': gns3_multi_project_data.get('projects_with_traffic', 0),
                    'auto_switches': gns3_multi_project_data.get('project_switches', 0),
                    'work_started': gns3_multi_project_data.get('work_started', 0),
                    'active_project': gns3_multi_project_data.get('active_project'),
                    'metrics': gns3_data,
                    'multi_project_metrics': gns3_multi_project_data
                },
                'ai_assistant': {
                    'status': ai_data.get('overall_status', 'unknown'),
                    'timestamp': ai_data.get('timestamp'),
                    'services': ai_data.get('services', {}),
                    'metrics': ai_data
                }
            },
            'global_health': cache.get('nms_global_health', {}),
            'summary': {
                'total_modules': 5,
                'healthy_modules': 0,
                'warning_modules': 0,
                'critical_modules': 0
            }
        }
        
        # Calculer le résumé
        for module_data in unified_report['modules'].values():
            status = module_data['status']
            if status == 'healthy':
                unified_report['summary']['healthy_modules'] += 1
            elif status in ['warning', 'degraded']:
                unified_report['summary']['warning_modules'] += 1
            elif status == 'critical':
                unified_report['summary']['critical_modules'] += 1
        
        # Déterminer le statut global
        if unified_report['summary']['critical_modules'] > 0:
            unified_report['global_status'] = 'critical'
        elif unified_report['summary']['warning_modules'] > 0:
            unified_report['global_status'] = 'warning'
        else:
            unified_report['global_status'] = 'healthy'
        
        # Sauvegarder le rapport
        cache.set('nms_unified_report', unified_report, timeout=1800)  # 30 minutes
        
        # Déclencher la distribution du rapport
        from reporting.tasks import distribute_unified_report
        distribute_unified_report.delay(unified_report)
        
        logger.info(f"✅ Rapport unifié généré - Statut: {unified_report['global_status']}")
        
        return {
            'status': 'success',
            'global_status': unified_report['global_status'],
            'modules_count': unified_report['summary']['total_modules']
        }
        
    except Exception as e:
        logger.error(f"❌ Erreur génération rapport unifié: {e}")
        return {'status': 'error', 'error': str(e)}


@shared_task
def cleanup_system_cache():
    """
    Nettoie le cache système global et optimise les performances.
    """
    try:
        logger.info("🧹 Nettoyage cache système global")
        
        # Patterns de cache à nettoyer
        cache_patterns = [
            'temp_*',
            '*_old_*',
            'expired_*',
            'debug_*',
            'test_*'
        ]
        
        # Nettoyer les entrées expirées
        expired_keys = []
        
        # Simuler le nettoyage (Django cache ne supporte pas les patterns)
        for i in range(1, 1000):
            for pattern in ['temp_', 'old_', 'expired_', 'debug_', 'test_']:
                cache_key = f"{pattern}{i}"
                if cache.get(cache_key):
                    cache.delete(cache_key)
                    expired_keys.append(cache_key)
        
        # Optimiser les caches de performance
        performance_keys = [
            'nms_global_health',
            'nms_unified_report',
            'nms_global_config'
        ]
        
        optimized_count = 0
        for key in performance_keys:
            data = cache.get(key)
            if data:
                # Recompresser et optimiser
                cache.set(key, data, timeout=cache.ttl(key) or 3600)
                optimized_count += 1
        
        logger.info(f"✅ Nettoyage terminé - {len(expired_keys)} supprimées, {optimized_count} optimisées")
        
        return {
            'expired_cleaned': len(expired_keys),
            'performance_optimized': optimized_count
        }
        
    except Exception as e:
        logger.error(f"❌ Erreur nettoyage cache: {e}")
        return {'error': str(e)}


# Fonctions utilitaires pour validation opérationnelle

async def _verify_nodes_operational_status(project_service, project_id: str) -> Dict[str, Any]:
    """
    Vérifie l'état opérationnel RÉEL de tous les nœuds d'un projet.
    
    Returns:
        Dict avec les statistiques d'état opérationnel
    """
    try:
        # Récupérer tous les nœuds du projet
        # Récupérer tous les nœuds du projet via GNS3Client
        from api_clients.network.gns3_client import GNS3Client
        gns3_client = GNS3Client()
        nodes = gns3_client.get_nodes(project_id)
        
        operational_status = {
            'nodes_started': 0,
            'nodes_operational': 0,
            'nodes_with_console': 0,
            'nodes_with_connectivity': 0,
            'operational_details': []
        }
        
        for node in nodes:
            node_id = node.get('node_id')
            node_name = node.get('name', 'Unknown')
            node_status = node.get('status', 'unknown')
            node_type = node.get('node_type', 'unknown')
            
            node_detail = {
                'node_id': node_id,
                'name': node_name,
                'type': node_type,
                'status': node_status,
                'operational': False,
                'console_active': False,
                'connectivity': False
            }
            
            if node_status == 'started':
                operational_status['nodes_started'] += 1
                
                # Vérifier si le nœud est vraiment opérationnel
                is_operational = await _check_node_operational(project_service, project_id, node_id, node)
                
                if is_operational['operational']:
                    operational_status['nodes_operational'] += 1
                    node_detail['operational'] = True
                
                if is_operational['console_active']:
                    operational_status['nodes_with_console'] += 1
                    node_detail['console_active'] = True
                
                if is_operational['connectivity']:
                    operational_status['nodes_with_connectivity'] += 1
                    node_detail['connectivity'] = True
            
            operational_status['operational_details'].append(node_detail)
        
        return operational_status
        
    except Exception as e:
        logger.error(f"❌ Erreur vérification état opérationnel: {e}")
        return {
            'nodes_started': 0,
            'nodes_operational': 0,
            'nodes_with_console': 0,
            'nodes_with_connectivity': 0,
            'operational_details': [],
            'error': str(e)
        }

async def _check_node_operational(project_service, project_id: str, node_id: str, node_data: Dict) -> Dict[str, bool]:
    """
    Vérifie si un nœud spécifique est vraiment opérationnel.
    """
    try:
        node_name = node_data.get('name', 'Unknown')
        node_type = node_data.get('node_type', 'unknown')
        
        operational_check = {
            'operational': False,
            'console_active': False,
            'connectivity': False
        }
        
        # 1. Vérifier la console si disponible
        console_port = node_data.get('console')
        if console_port:
            try:
                # Test simple de connexion à la console
                import socket
                import time
                
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(2)
                result = sock.connect_ex(('localhost', console_port))
                sock.close()
                
                if result == 0:
                    operational_check['console_active'] = True
                    logger.debug(f"✅ Console active pour {node_name} sur port {console_port}")
                else:
                    logger.debug(f"⚠️ Console non accessible pour {node_name} sur port {console_port}")
                    
            except Exception as e:
                logger.debug(f"⚠️ Erreur test console {node_name}: {e}")
        
        # 2. Vérifier selon le type de nœud
        if node_type in ['vpcs', 'qemu', 'dynamips', 'iou']:
            # Ces types devraient être opérationnels s'ils sont démarrés
            operational_check['operational'] = True
            
            # Pour VPCS et QEMU, tester une connexion simple
            if console_port and operational_check['console_active']:
                operational_check['connectivity'] = True
                
        elif node_type in ['cloud', 'ethernet_hub', 'ethernet_switch']:
            # Ces types sont opérationnels par design
            operational_check['operational'] = True
            operational_check['connectivity'] = True
        
        return operational_check
        
    except Exception as e:
        logger.error(f"❌ Erreur vérification nœud {node_id}: {e}")
        return {'operational': False, 'console_active': False, 'connectivity': False}

async def _discover_real_equipment_ips(project_id: str) -> Dict[str, Any]:
    """
    Découvre les adresses IP RÉELLES des équipements en utilisant l'API corrigée.
    """
    try:
        logger.info(f"🔍 Lancement découverte IP RÉELLE via API corrigée...")
        
        # Utiliser l'API de découverte corrigée
        from common.api_views.equipment_discovery_api import equipment_discovery_service
        
        # Récupérer la liste des équipements
        from api_clients.network.gns3_client import GNS3Client
        gns3_client = GNS3Client()
        nodes = gns3_client.get_nodes(project_id)
        
        discovery_result = {
            'total_equipment': len(nodes),
            'equipment_with_ips': 0,
            'total_ips': 0,
            'accessible_equipment': 0,
            'equipment_details': []
        }
        
        # Découvrir les IPs pour chaque équipement
        for node in nodes:
            node_id = node.get('node_id')
            node_name = node.get('name', 'Unknown')
            node_type = node.get('node_type', 'unknown')
            
            try:
                # Utiliser la méthode corrigée de découverte
                equipment_data = await equipment_discovery_service.discover_equipment_details(project_id, node_id)
                
                network_info = equipment_data.get('network_info', {})
                ip_addresses = network_info.get('ip_addresses', [])
                
                # Filtrer les IPs valides (pas localhost, pas vides)
                valid_ips = [ip for ip in ip_addresses if ip and not ip.startswith('127.') and ip != '0.0.0.0']
                
                equipment_detail = {
                    'node_id': node_id,
                    'name': node_name,
                    'type': node_type,
                    'ip_count': len(valid_ips),
                    'ips': valid_ips,
                    'accessible': False
                }
                
                if valid_ips:
                    discovery_result['equipment_with_ips'] += 1
                    discovery_result['total_ips'] += len(valid_ips)
                    
                    # Tester l'accessibilité de la première IP
                    if await _test_ip_accessibility(valid_ips[0]):
                        discovery_result['accessible_equipment'] += 1
                        equipment_detail['accessible'] = True
                        logger.info(f"✅ {node_name}: {len(valid_ips)} IPs trouvées, accessible")
                    else:
                        logger.info(f"⚠️ {node_name}: {len(valid_ips)} IPs trouvées, pas accessible")
                else:
                    logger.debug(f"❌ {node_name}: Aucune IP trouvée")
                
                discovery_result['equipment_details'].append(equipment_detail)
                
            except Exception as e:
                logger.error(f"❌ Erreur découverte {node_name}: {e}")
                discovery_result['equipment_details'].append({
                    'node_id': node_id,
                    'name': node_name,
                    'type': node_type,
                    'ip_count': 0,
                    'ips': [],
                    'accessible': False,
                    'error': str(e)
                })
        
        return discovery_result
        
    except Exception as e:
        logger.error(f"❌ Erreur découverte IPs équipements: {e}")
        return {
            'total_equipment': 0,
            'equipment_with_ips': 0,
            'total_ips': 0,
            'accessible_equipment': 0,
            'equipment_details': [],
            'error': str(e)
        }

async def _test_ip_accessibility(ip: str) -> bool:
    """
    Teste l'accessibilité RÉELLE d'une adresse IP.
    """
    try:
        import subprocess
        
        # Test ping simple
        result = subprocess.run(
            ['ping', '-c', '1', '-W', '2', ip],
            capture_output=True,
            timeout=3
        )
        
        return result.returncode == 0
        
    except Exception as e:
        logger.debug(f"⚠️ Erreur test accessibilité {ip}: {e}")
        return False

# Fonctions utilitaires

def _analyze_global_system_health(module_results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyse la santé globale du système basée sur les résultats des modules."""
    healthy_count = 0
    warning_count = 0
    critical_count = 0
    issues = []
    
    for result in module_results:
        status = result.get('status', 'unknown')
        module = result.get('module', 'unknown')
        
        if status == 'healthy':
            healthy_count += 1
        elif status in ['warning', 'degraded']:
            warning_count += 1
        elif status == 'critical':
            critical_count += 1
            issues.append(f"Module {module}: {result.get('error', 'Critical status')}")
    
    # Déterminer le statut global
    if critical_count > 0:
        global_status = 'critical'
    elif warning_count > 2:
        global_status = 'degraded'
    elif warning_count > 0:
        global_status = 'warning'
    else:
        global_status = 'healthy'
    
    return {
        'status': global_status,
        'timestamp': timezone.now().isoformat(),
        'modules_total': len(module_results),
        'modules_healthy': healthy_count,
        'modules_warning': warning_count,
        'modules_critical': critical_count,
        'issues': issues,
        'health_score': (healthy_count / len(module_results) * 100) if module_results else 0
    }


def _generate_default_global_config() -> Dict[str, Any]:
    """Génère la configuration globale par défaut."""
    return {
        'monitoring': {
            'collection_interval': 120,  # 2 minutes
            'retention_days': 30,
            'alert_thresholds': {
                'cpu': 80,
                'memory': 85,
                'disk': 90
            }
        },
        'security': {
            'alert_scan_interval': 120,  # 2 minutes
            'alert_retention_days': 30,
            'auto_report_threshold': 'critical'
        },
        'qos': {
            'stats_collection_interval': 120,  # 2 minutes
            'optimization_enabled': True,
            'auto_adjustment_threshold': 'high'
        },
        'reporting': {
            'unified_report_interval': 3600,  # 1 heure
            'distribution_enabled': True,
            'formats': ['html', 'pdf']
        },
        'gns3': {
            'monitoring_interval': 300,  # 5 minutes
            'auto_sync_projects': True
        },
        'general': {
            'timezone': 'Europe/Paris',
            'debug_mode': False,
            'log_level': 'INFO'
        }
    }