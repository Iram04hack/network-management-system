"""
Tâches Celery pour le monitoring permanent GNS3.

Ce module contient les tâches asynchrones pour la détection
et le monitoring permanent du serveur GNS3.
"""

import logging
from celery import shared_task
from django.utils import timezone
from django.core.cache import cache
from datetime import timedelta

from .infrastructure.gns3_detection_service import get_gns3_server_status

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def monitor_gns3_server(self):
    """
    Tâche de monitoring permanent du serveur GNS3.
    
    Cette tâche s'exécute en arrière-plan pour détecter
    la disponibilité du serveur GNS3 et mettre à jour le cache.
    """
    try:
        logger.info("Démarrage du monitoring GNS3")
        
        # Vérifier le statut du serveur GNS3
        import asyncio
        
        # Créer une nouvelle boucle d'événements pour Celery
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            status = loop.run_until_complete(get_gns3_server_status(force_check=True))
            
            # Mettre à jour les métriques de monitoring
            cache_key = "gns3_monitoring_metrics"
            current_metrics = cache.get(cache_key, {})
            
            current_metrics.update({
                'last_check': timezone.now().isoformat(),
                'is_available': status.is_available,
                'version': status.version,
                'projects_count': status.projects_count,
                'response_time_ms': status.response_time_ms,
                'error_message': status.error_message,
                'consecutive_failures': 0 if status.is_available else current_metrics.get('consecutive_failures', 0) + 1,
                'uptime_percentage': current_metrics.get('uptime_percentage', 100.0)
            })
            
            # Calculer le pourcentage d'uptime (sur les 24 dernières heures)
            if status.is_available:
                current_metrics['last_available'] = timezone.now().isoformat()
            
            # Sauvegarder les métriques (24h)
            cache.set(cache_key, current_metrics, timeout=86400)
            
            if status.is_available:
                logger.info(f"Serveur GNS3 disponible - Version: {status.version}, "
                           f"Projets: {status.projects_count}, "
                           f"Temps de réponse: {status.response_time_ms:.0f}ms")
            else:
                logger.warning(f"Serveur GNS3 indisponible - Erreur: {status.error_message}")
                
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"Erreur lors du monitoring GNS3: {e}")
        
        # Retry avec backoff exponentiel
        try:
            raise self.retry(countdown=60 * (2 ** self.request.retries))
        except self.MaxRetriesExceededError:
            logger.error("Nombre maximum de tentatives atteint pour le monitoring GNS3")


@shared_task
def cleanup_gns3_cache():
    """
    Tâche de nettoyage du cache GNS3.
    
    Nettoie les entrées de cache anciennes et obsolètes.
    """
    try:
        logger.info("Nettoyage du cache GNS3")
        
        # Nettoyer les anciennes métriques (plus de 7 jours)
        cache_patterns = [
            "gns3_server_status_*",
            "gns3_project_*",
            "gns3_node_*",
            "gns3_monitoring_metrics"
        ]
        
        # Django cache ne supporte pas le pattern matching direct
        # donc on utilise une liste de clés connues
        keys_to_clean = [
            f"gns3_server_status_localhost_3080",
            f"gns3_monitoring_metrics_old",
            f"gns3_projects_cache",
            f"gns3_nodes_cache"
        ]
        
        cleaned_count = 0
        for key in keys_to_clean:
            if cache.get(key):
                cache.delete(key)
                cleaned_count += 1
                
        logger.info(f"Nettoyage terminé - {cleaned_count} entrées supprimées")
        
    except Exception as e:
        logger.error(f"Erreur lors du nettoyage du cache GNS3: {e}")


@shared_task
def sync_gns3_projects():
    """
    Synchronise les projets GNS3 avec la base de données.
    
    Cette tâche s'exécute périodiquement pour synchroniser
    les projets GNS3 disponibles avec la base de données locale.
    """
    try:
        logger.info("Synchronisation des projets GNS3")
        
        # Vérifier la disponibilité du serveur
        import asyncio
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            status = loop.run_until_complete(get_gns3_server_status())
            
            if not status.is_available:
                logger.warning("Serveur GNS3 indisponible - Synchronisation ignorée")
                return
            
            # Importer les services nécessaires
            from .infrastructure.gns3_client import GNS3Client
            from .infrastructure.gns3_repository import GNS3Repository
            from .application.project_service import ProjectService
            
            # Initialiser les services
            client = GNS3Client(host="localhost", port=3080)
            repository = GNS3Repository()
            project_service = ProjectService(client, repository)
            
            # Récupérer les projets depuis GNS3
            projects = project_service.get_all_projects()
            
            logger.info(f"Synchronisation terminée - {len(projects)} projets trouvés")
            
            # Mettre à jour le cache avec les projets synchronisés
            cache.set("gns3_projects_sync", {
                'timestamp': timezone.now().isoformat(),
                'projects_count': len(projects),
                'projects': [p.to_dict() for p in projects]
            }, timeout=3600)
            
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"Erreur lors de la synchronisation des projets GNS3: {e}")


@shared_task
def monitor_multi_projects_traffic():
    """
    Surveille automatiquement le trafic sur tous les projets GNS3 sélectionnés.
    
    Cette tâche vérifie le trafic réseau sur tous les projets sélectionnés
    et déclenche automatiquement le basculement et le démarrage du travail.
    """
    try:
        logger.info("🚀 Surveillance automatique multi-projets GNS3")
        
        # Importer le service multi-projets
        from .application.multi_project_service import MultiProjectService
        from .application.project_service import ProjectService
        from .infrastructure.gns3_client_impl import GNS3ClientImpl
        from .infrastructure.gns3_repository_impl import GNS3RepositoryImpl
        
        # Initialiser les services
        client = GNS3ClientImpl()
        repository = GNS3RepositoryImpl()
        project_service = ProjectService(client, repository)
        multi_project_service = MultiProjectService(project_service, client, repository)
        
        # Récupérer les projets sélectionnés
        selected_projects = multi_project_service.get_selected_projects()
        
        if not selected_projects:
            logger.debug("✅ Aucun projet sélectionné pour surveillance")
            return {"status": "success", "message": "Aucun projet sélectionné"}
        
        logger.info(f"🔍 Surveillance de {len(selected_projects)} projet(s) sélectionné(s)")
        
        # Variables pour métriques
        projects_with_traffic = 0
        project_switches = 0
        work_started = 0
        
        # Vérifier le trafic pour chaque projet
        for selection in selected_projects:
            if not selection.auto_start_on_traffic:
                continue
                
            try:
                # Détecter le trafic
                traffic_status = multi_project_service.detect_traffic_on_project(selection.project_id)
                
                if traffic_status.has_traffic:
                    projects_with_traffic += 1
                    
                    # Mettre à jour la sélection
                    selection.traffic_detected = True
                    selection.last_traffic = traffic_status.detected_at
                    
                    logger.info(f"🚨 Trafic détecté sur projet {selection.project_name} "
                               f"(niveau: {traffic_status.traffic_level})")
                    
            except Exception as e:
                logger.error(f"❌ Erreur détection trafic projet {selection.project_id}: {e}")
                continue
        
        # Analyser si basculement nécessaire
        current_active = multi_project_service.get_active_project()
        should_switch = False
        target_project = None
        
        if projects_with_traffic > 0:
            # Trouver le projet avec la plus haute priorité ayant du trafic
            projects_with_traffic_sorted = sorted(
                [sel for sel in selected_projects if sel.traffic_detected],
                key=lambda x: x.priority
            )
            
            if projects_with_traffic_sorted:
                best_project = projects_with_traffic_sorted[0]
                
                if not current_active:
                    # Aucun projet actif, activer le meilleur
                    should_switch = True
                    target_project = best_project
                    logger.info(f"🔄 Aucun projet actif, activation de {best_project.project_name}")
                    
                elif current_active.project_id != best_project.project_id:
                    # Vérifier si le projet actuel a encore du trafic
                    current_has_traffic = any(
                        sel.project_id == current_active.project_id and sel.traffic_detected 
                        for sel in selected_projects
                    )
                    
                    if not current_has_traffic or best_project.priority < current_active.priority:
                        should_switch = True
                        target_project = best_project
                        logger.info(f"🔄 Basculement vers projet prioritaire {best_project.project_name}")
        
        # Effectuer le basculement si nécessaire
        if should_switch and target_project:
            try:
                success = multi_project_service.set_active_project(target_project.project_id)
                if success:
                    project_switches += 1
                    
                    # Démarrer le travail automatiquement
                    import asyncio
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    
                    try:
                        # Ouvrir le projet et démarrer les nœuds
                        project_service.open_project(target_project.project_id)
                        start_result = project_service.start_all_nodes(target_project.project_id)
                        
                        if start_result and start_result.get('success_count', 0) > 0:
                            work_started += 1
                            logger.info(f"✅ Travail démarré sur projet {target_project.project_name}: "
                                       f"{start_result.get('success_count', 0)} nœuds démarrés")
                        
                    finally:
                        loop.close()
                        
            except Exception as e:
                logger.error(f"❌ Erreur lors du basculement vers {target_project.project_name}: {e}")
        
        # Mettre à jour les métriques globales
        monitoring_metrics = {
            'last_multi_project_check': timezone.now().isoformat(),
            'selected_projects_count': len(selected_projects),
            'projects_with_traffic': projects_with_traffic,
            'project_switches': project_switches,
            'work_started': work_started,
            'active_project': target_project.project_id if target_project else (current_active.project_id if current_active else None),
            'monitoring_enabled': True
        }
        
        cache.set("gns3_multi_project_metrics", monitoring_metrics, timeout=600)
        
        logger.info(f"✅ Surveillance multi-projets terminée - "
                   f"{projects_with_traffic} avec trafic, {project_switches} basculements")
        
        return {
            'status': 'success',
            'selected_projects': len(selected_projects),
            'projects_with_traffic': projects_with_traffic,
            'project_switches': project_switches,
            'work_started': work_started
        }
        
    except Exception as e:
        logger.error(f"❌ Erreur surveillance multi-projets GNS3: {e}")
        
        # Mettre à jour métriques d'erreur
        cache.set("gns3_multi_project_metrics", {
            'last_multi_project_check': timezone.now().isoformat(),
            'monitoring_enabled': False,
            'error': str(e)
        }, timeout=600)
        
        return {'status': 'error', 'error': str(e)}


@shared_task
def sync_all_selected_projects():
    """
    Synchronise tous les projets sélectionnés avec le serveur GNS3.
    
    Cette tâche met à jour les informations de tous les projets
    sélectionnés pour surveillance multi-projets.
    """
    try:
        logger.info("🔄 Synchronisation projets sélectionnés GNS3")
        
        # Importer les services
        from .application.multi_project_service import MultiProjectService
        from .application.project_service import ProjectService
        from .infrastructure.gns3_client_impl import GNS3ClientImpl
        from .infrastructure.gns3_repository_impl import GNS3RepositoryImpl
        
        # Initialiser les services
        client = GNS3ClientImpl()
        repository = GNS3RepositoryImpl()
        project_service = ProjectService(client, repository)
        multi_project_service = MultiProjectService(project_service, client, repository)
        
        # Récupérer les projets sélectionnés
        selected_projects = multi_project_service.get_selected_projects()
        
        if not selected_projects:
            logger.debug("✅ Aucun projet sélectionné à synchroniser")
            return {"status": "success", "message": "Aucun projet sélectionné"}
        
        # Synchroniser chaque projet
        synced_projects = 0
        failed_projects = 0
        
        for selection in selected_projects:
            try:
                # Synchroniser le projet avec GNS3
                project = project_service.sync_project(selection.project_id)
                
                if project:
                    synced_projects += 1
                    # Mettre à jour le nom du projet dans la sélection si changé
                    if selection.project_name != project.name:
                        selection.project_name = project.name
                        
                else:
                    failed_projects += 1
                    logger.warning(f"⚠️ Projet {selection.project_id} non trouvé sur GNS3")
                    
            except Exception as e:
                failed_projects += 1
                logger.error(f"❌ Erreur synchronisation projet {selection.project_id}: {e}")
                continue
        
        # Sauvegarder les métriques de synchronisation
        sync_metrics = {
            'last_sync': timezone.now().isoformat(),
            'total_selected_projects': len(selected_projects),
            'synced_projects': synced_projects,
            'failed_projects': failed_projects,
            'sync_success_rate': (synced_projects / len(selected_projects) * 100) if selected_projects else 0
        }
        
        cache.set("gns3_multi_project_sync_metrics", sync_metrics, timeout=3600)
        
        logger.info(f"✅ Synchronisation terminée - {synced_projects}/{len(selected_projects)} projets synchronisés")
        
        return {
            'status': 'success',
            'synced_projects': synced_projects,
            'failed_projects': failed_projects,
            'total_projects': len(selected_projects)
        }
        
    except Exception as e:
        logger.error(f"❌ Erreur synchronisation projets sélectionnés: {e}")
        return {'status': 'error', 'error': str(e)}


@shared_task
def cleanup_multi_project_cache():
    """
    Nettoie le cache des données multi-projets obsolètes.
    """
    try:
        logger.info("🧹 Nettoyage cache multi-projets GNS3")
        
        # Clés de cache à nettoyer
        cache_keys_to_clean = []
        
        # Nettoyer les statuts de trafic anciens (plus de 1 heure)
        for i in range(1, 1000):  # IDs de projets jusqu'à 1000
            traffic_key = f"gns3_traffic_status_{i}"
            if cache.get(traffic_key):
                cache.delete(traffic_key)
                cache_keys_to_clean.append(traffic_key)
        
        # Nettoyer les données temporaires
        temp_keys = [
            "gns3_temp_project_selection",
            "gns3_temp_traffic_analysis",
            "gns3_temp_switch_decision"
        ]
        
        for key in temp_keys:
            if cache.get(key):
                cache.delete(key)
                cache_keys_to_clean.append(key)
        
        # Optimiser les données de performance fréquemment utilisées
        performance_keys = [
            "gns3_selected_projects",
            "gns3_active_project",
            "gns3_multi_project_metrics"
        ]
        
        optimized_keys = 0
        for key in performance_keys:
            data = cache.get(key)
            if data:
                # Recompresser et optimiser avec timeout approprié
                timeout = 3600 if 'metrics' in key else cache.ttl(key) or 1800
                cache.set(key, data, timeout=timeout)
                optimized_keys += 1
        
        logger.info(f"✅ Nettoyage cache terminé - {len(cache_keys_to_clean)} supprimées, {optimized_keys} optimisées")
        
        return {
            'cache_entries_cleaned': len(cache_keys_to_clean),
            'performance_keys_optimized': optimized_keys
        }
        
    except Exception as e:
        logger.error(f"❌ Erreur nettoyage cache multi-projets: {e}")
        return {'error': str(e)}


@shared_task
def generate_gns3_health_report():
    """
    Génère un rapport de santé du serveur GNS3 incluant les métriques multi-projets.
    
    Cette tâche analyse les métriques collectées et génère
    un rapport de santé détaillé du serveur GNS3 et des projets multiples.
    """
    try:
        logger.info("📋 Génération du rapport de santé GNS3")
        
        # Récupérer les métriques de monitoring serveur
        server_metrics = cache.get("gns3_monitoring_metrics", {})
        
        # Récupérer les métriques multi-projets
        multi_project_metrics = cache.get("gns3_multi_project_metrics", {})
        sync_metrics = cache.get("gns3_multi_project_sync_metrics", {})
        
        # Analyser la santé du serveur
        server_health = {
            'available': server_metrics.get('is_available', False),
            'response_time_ms': server_metrics.get('response_time_ms', 0),
            'consecutive_failures': server_metrics.get('consecutive_failures', 0),
            'projects_count': server_metrics.get('projects_count', 0),
            'last_check': server_metrics.get('last_check')
        }
        
        # Analyser la santé multi-projets
        multi_project_health = {
            'monitoring_enabled': multi_project_metrics.get('monitoring_enabled', False),
            'selected_projects_count': multi_project_metrics.get('selected_projects_count', 0),
            'projects_with_traffic': multi_project_metrics.get('projects_with_traffic', 0),
            'active_project': multi_project_metrics.get('active_project'),
            'last_check': multi_project_metrics.get('last_multi_project_check'),
            'sync_success_rate': sync_metrics.get('sync_success_rate', 0)
        }
        
        # Compiler le rapport unifié
        report = {
            'generated_at': timezone.now().isoformat(),
            'server_health': server_health,
            'multi_project_health': multi_project_health,
            'overall_status': 'healthy',
            'availability_score': 100,
            'performance_score': 100,
            'recommendations': [],
            'alerts': []
        }
        
        # Calculer les scores
        if not server_health['available']:
            report['overall_status'] = 'critical'
            report['availability_score'] = 0
            report['alerts'].append({
                'level': 'critical',
                'message': 'Serveur GNS3 indisponible'
            })
        else:
            # Réduire le score selon les échecs consécutifs
            failures = server_health['consecutive_failures']
            if failures > 0:
                report['availability_score'] = max(0, 100 - (failures * 10))
                
            if failures > 3:
                report['overall_status'] = 'degraded'
                report['alerts'].append({
                    'level': 'warning',
                    'message': f'Serveur instable: {failures} échecs consécutifs'
                })
        
        # Analyser les performances
        response_time = server_health['response_time_ms']
        if response_time > 2000:
            report['performance_score'] = 50
            report['alerts'].append({
                'level': 'warning',
                'message': f'Temps de réponse élevé: {response_time:.0f}ms'
            })
        elif response_time > 1000:
            report['performance_score'] = 75
        
        # Générer des recommandations
        if server_health['projects_count'] == 0:
            report['recommendations'].append(
                "Aucun projet détecté - Vérifier la configuration GNS3"
            )
        
        if multi_project_health['selected_projects_count'] == 0:
            report['recommendations'].append(
                "Aucun projet sélectionné pour surveillance automatique"
            )
        elif multi_project_health['projects_with_traffic'] == 0:
            report['recommendations'].append(
                "Aucun trafic détecté sur les projets sélectionnés"
            )
        
        if multi_project_health['sync_success_rate'] < 80:
            report['recommendations'].append(
                f"Taux de synchronisation faible: {multi_project_health['sync_success_rate']:.1f}%"
            )
        
        if not multi_project_health['monitoring_enabled']:
            report['recommendations'].append(
                "Surveillance multi-projets désactivée"
            )
        
        # Déterminer le statut global final
        if report['availability_score'] < 50:
            report['overall_status'] = 'critical'
        elif report['availability_score'] < 80 or report['performance_score'] < 70:
            report['overall_status'] = 'degraded'
        elif len(report['alerts']) > 0:
            report['overall_status'] = 'warning'
        
        # Sauvegarder le rapport
        cache.set("gns3_health_report", report, timeout=3600)
        
        logger.info(f"✅ Rapport généré - Statut: {report['overall_status']}, "
                   f"Disponibilité: {report['availability_score']}/100, "
                   f"Performance: {report['performance_score']}/100")
        
        return {
            'status': 'success',
            'overall_status': report['overall_status'],
            'availability_score': report['availability_score'],
            'performance_score': report['performance_score'],
            'alerts_count': len(report['alerts']),
            'recommendations_count': len(report['recommendations'])
        }
        
    except Exception as e:
        logger.error(f"❌ Erreur génération rapport santé GNS3: {e}")
        return {'status': 'error', 'error': str(e)}