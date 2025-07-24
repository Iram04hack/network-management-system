"""
Tâches Celery pour le module Network Management.

Ce module contient les tâches asynchrones pour la gestion réseau,
la synchronisation de topologie et la découverte automatique.
"""

import logging
from celery import shared_task
from django.utils import timezone
from django.core.cache import cache
from datetime import timedelta

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def sync_network_topology(self):
    """
    Tâche de synchronisation de la topologie réseau.
    
    Cette tâche synchronise la topologie avec GNS3 et met à jour
    les informations des équipements réseau.
    """
    try:
        logger.info("Démarrage de la synchronisation de topologie réseau")
        
        # Import du service de topologie
        from .services.topology_service import topology_service
        import asyncio
        
        # Créer une nouvelle boucle d'événements pour Celery
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            # Synchroniser avec GNS3
            sync_result = loop.run_until_complete(topology_service.sync_with_gns3())
            
            # Mettre à jour les métriques de synchronisation
            cache_key = "network_topology_sync_metrics"
            current_metrics = cache.get(cache_key, {})
            
            current_metrics.update({
                'last_sync': timezone.now().isoformat(),
                'sync_success': sync_result['success'],
                'devices_synced': sync_result['devices_synced'],
                'interfaces_synced': sync_result['interfaces_synced'],
                'topologies_synced': sync_result['topologies_synced'],
                'gns3_available': sync_result['gns3_available'],
                'error_count': len(sync_result.get('errors', [])),
                'consecutive_failures': 0 if sync_result['success'] else current_metrics.get('consecutive_failures', 0) + 1
            })
            
            # Sauvegarder les métriques (24h)
            cache.set(cache_key, current_metrics, timeout=86400)
            
            if sync_result['success']:
                logger.info(f"Synchronisation de topologie réussie - "
                           f"Équipements: {sync_result['devices_synced']}, "
                           f"Interfaces: {sync_result['interfaces_synced']}")
            else:
                logger.warning(f"Synchronisation de topologie échouée - "
                              f"Erreurs: {sync_result.get('errors', [])}")
                
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"Erreur lors de la synchronisation de topologie: {e}")
        
        # Retry avec backoff exponentiel
        try:
            raise self.retry(countdown=60 * (2 ** self.request.retries))
        except self.MaxRetriesExceededError:
            logger.error("Nombre maximum de tentatives atteint pour la synchronisation de topologie")


@shared_task(bind=True, max_retries=2, default_retry_delay=120)
def discover_network_devices(self, scan_ranges=None):
    """
    Tâche de découverte automatique des équipements réseau.
    
    Args:
        scan_ranges: Liste des plages IP à scanner
    """
    try:
        logger.info("Démarrage de la découverte automatique des équipements réseau")
        
        # Import du service de topologie
        from .services.topology_service import topology_service
        import asyncio
        
        # Plages par défaut si non spécifiées
        if not scan_ranges:
            scan_ranges = [
                '192.168.1.0/24',
                '192.168.0.0/24',
                '10.0.0.0/24'
            ]
        
        # Créer une nouvelle boucle d'événements pour Celery
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            # Lancer la découverte
            discovery_result = loop.run_until_complete(
                topology_service.discover_network_devices(scan_ranges)
            )
            
            # Mettre à jour les métriques de découverte
            cache_key = "network_discovery_metrics"
            current_metrics = cache.get(cache_key, {})
            
            current_metrics.update({
                'last_discovery': timezone.now().isoformat(),
                'discovery_success': discovery_result['success'],
                'devices_discovered': discovery_result['devices_discovered'],
                'devices_updated': discovery_result['devices_updated'],
                'discovery_methods': discovery_result['discovery_methods'],
                'scan_ranges': discovery_result['scan_ranges'],
                'error_count': len(discovery_result.get('errors', []))
            })
            
            # Sauvegarder les métriques (24h)
            cache.set(cache_key, current_metrics, timeout=86400)
            
            logger.info(f"Découverte réseau terminée - "
                       f"Découverts: {discovery_result['devices_discovered']}, "
                       f"Mis à jour: {discovery_result['devices_updated']}")
                
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"Erreur lors de la découverte réseau: {e}")
        
        # Retry avec backoff
        try:
            raise self.retry(countdown=120 * (2 ** self.request.retries))
        except self.MaxRetriesExceededError:
            logger.error("Nombre maximum de tentatives atteint pour la découverte réseau")


@shared_task
def collect_interface_statistics():
    """
    Collecte les statistiques de toutes les interfaces réseau.
    """
    try:
        logger.info("Collecte des statistiques d'interfaces")
        
        # Import des services nécessaires
        from .application.services import InterfaceService
        from .infrastructure.adapters import DjangoInterfaceRepository, DjangoDeviceRepository
        from .models import NetworkInterface
        
        # Initialiser le service
        interface_repository = DjangoInterfaceRepository()
        device_repository = DjangoDeviceRepository()
        interface_service = InterfaceService(interface_repository, device_repository)
        
        # Récupérer toutes les interfaces actives
        interfaces = NetworkInterface.objects.filter(
            device__is_monitored=True,
            status='up'
        ).select_related('device')
        
        stats_collected = 0
        for interface in interfaces:
            try:
                # Collecter les statistiques pour chaque interface
                stats = interface_service.get_interface_statistics(interface.id)
                
                if stats and stats.get('collection_method') == 'snmp_real':
                    stats_collected += 1
                    
                    # Mettre en cache les statistiques
                    cache_key = f"interface_stats_{interface.id}"
                    cache.set(cache_key, stats, timeout=300)  # 5 minutes
                    
            except Exception as e:
                logger.debug(f"Erreur collecte statistiques interface {interface.id}: {e}")
                continue
        
        # Mettre à jour les métriques globales
        cache.set("interface_stats_collection", {
            'last_collection': timezone.now().isoformat(),
            'interfaces_total': interfaces.count(),
            'stats_collected': stats_collected,
            'collection_rate': (stats_collected / interfaces.count() * 100) if interfaces.count() > 0 else 0
        }, timeout=3600)
        
        logger.info(f"Collecte terminée - {stats_collected}/{interfaces.count()} interfaces")
        
    except Exception as e:
        logger.error(f"Erreur lors de la collecte de statistiques: {e}")


@shared_task
def cleanup_old_topology_data():
    """
    Nettoie les anciennes données de topologie.
    """
    try:
        logger.info("Nettoyage des anciennes données de topologie")
        
        from .models import NetworkDevice, NetworkInterface
        from django.utils import timezone
        from datetime import timedelta
        
        # Supprimer les équipements découverts mais non confirmés depuis 7 jours
        old_discovered = NetworkDevice.objects.filter(
            status='discovered',
            discovered_at__lt=timezone.now() - timedelta(days=7)
        )
        
        deleted_devices = old_discovered.count()
        old_discovered.delete()
        
        # Nettoyer les interfaces orphelines
        orphaned_interfaces = NetworkInterface.objects.filter(
            device__isnull=True
        )
        
        deleted_interfaces = orphaned_interfaces.count()
        orphaned_interfaces.delete()
        
        # Nettoyer le cache
        cache_patterns = [
            "interface_stats_*",
            "network_topology_*",
            "device_statistics_*"
        ]
        
        # Nettoyer les entrées de cache anciennes (simulé car Django cache ne supporte pas les patterns)
        cleaned_cache_entries = 0
        for i in range(1, 1000):  # Nettoyer les interfaces jusqu'à ID 1000
            cache_key = f"interface_stats_{i}"
            if cache.get(cache_key):
                cache.delete(cache_key)
                cleaned_cache_entries += 1
        
        logger.info(f"Nettoyage terminé - "
                   f"Équipements supprimés: {deleted_devices}, "
                   f"Interfaces supprimées: {deleted_interfaces}, "
                   f"Entrées cache nettoyées: {cleaned_cache_entries}")
        
    except Exception as e:
        logger.error(f"Erreur lors du nettoyage: {e}")


@shared_task
def update_device_statuses():
    """
    Met à jour les statuts des équipements réseau via SNMP.
    """
    try:
        logger.info("Mise à jour des statuts d'équipements")
        
        from .models import NetworkDevice
        from api_clients.network.snmp_client import SNMPClient
        import asyncio
        
        # Récupérer les équipements avec IP
        devices = NetworkDevice.objects.filter(
            is_monitored=True,
            ip_address__isnull=False
        ).exclude(ip_address='')
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        updated_devices = 0
        
        try:
            for device in devices:
                try:
                    # Test SNMP basique pour vérifier la connectivité
                    snmp_client = SNMPClient(
                        host=str(device.ip_address),
                        community=device.snmp_community or 'public',
                        timeout=3,
                        retries=1
                    )
                    
                    # Test avec sysUpTime
                    result = loop.run_until_complete(
                        asyncio.get_event_loop().run_in_executor(
                            None, snmp_client.get, '1.3.6.1.2.1.1.3.0'
                        )
                    )
                    
                    # Mettre à jour le statut
                    new_status = 'running' if result and 'value' in result else 'stopped'
                    
                    if device.status != new_status:
                        device.status = new_status
                        device.last_seen = timezone.now()
                        device.save()
                        updated_devices += 1
                        
                except Exception as e:
                    # Marquer comme arrêté si SNMP échoue
                    if device.status != 'stopped':
                        device.status = 'stopped'
                        device.save()
                        updated_devices += 1
                    logger.debug(f"SNMP failed for {device.name}: {e}")
                    
        finally:
            loop.close()
        
        logger.info(f"Mise à jour des statuts terminée - {updated_devices} équipements mis à jour")
        
    except ImportError:
        logger.warning("Client SNMP non disponible pour la mise à jour des statuts")
    except Exception as e:
        logger.error(f"Erreur lors de la mise à jour des statuts: {e}")


@shared_task
def generate_topology_health_report():
    """
    Génère un rapport de santé de la topologie réseau.
    """
    try:
        logger.info("Génération du rapport de santé de topologie")
        
        from .services.topology_service import topology_service
        
        # Récupérer le résumé de la topologie
        summary = topology_service.get_topology_summary()
        
        # Analyser la santé
        total_devices = summary.get('devices_total', 0)
        online_devices = summary.get('devices_online', 0)
        managed_devices = summary.get('devices_managed', 0)
        monitored_devices = summary.get('devices_monitored', 0)
        
        # Calculer les métriques
        online_percentage = (online_devices / total_devices * 100) if total_devices > 0 else 0
        managed_percentage = (managed_devices / total_devices * 100) if total_devices > 0 else 0
        monitored_percentage = (monitored_devices / total_devices * 100) if total_devices > 0 else 0
        
        # Générer le rapport
        report = {
            'generated_at': timezone.now().isoformat(),
            'summary': summary,
            'health_metrics': {
                'online_percentage': round(online_percentage, 1),
                'managed_percentage': round(managed_percentage, 1),
                'monitored_percentage': round(monitored_percentage, 1)
            },
            'recommendations': [],
            'alerts': []
        }
        
        # Ajouter des recommandations basées sur les métriques
        if online_percentage < 80:
            report['alerts'].append({
                'level': 'warning',
                'message': f"Seulement {online_percentage:.1f}% des équipements sont en ligne"
            })
            
        if managed_percentage < 60:
            report['recommendations'].append(
                "Augmenter le nombre d'équipements gérés pour améliorer le contrôle réseau"
            )
            
        if monitored_percentage < 70:
            report['recommendations'].append(
                "Activer la surveillance pour plus d'équipements"
            )
            
        if total_devices == 0:
            report['recommendations'].append(
                "Lancer la découverte automatique pour identifier les équipements réseau"
            )
        
        # Sauvegarder le rapport
        cache.set("topology_health_report", report, timeout=3600)
        
        logger.info(f"Rapport de santé généré - "
                   f"Santé globale: {online_percentage:.1f}% en ligne")
        
    except Exception as e:
        logger.error(f"Erreur lors de la génération du rapport de santé: {e}")