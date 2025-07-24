#!/usr/bin/env python3
"""
Dashboard - Tâches Celery pour le Monitoring Temps Réel
======================================================

Ce module contient les tâches Celery pour le monitoring temps réel
du dashboard, incluant la collecte de métriques, mise à jour des
statistiques et surveillance des systèmes.

Auteur: Claude Code
Date: 2025-07-18
"""

import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from celery import shared_task
from django.utils import timezone
from django.core.cache import cache
from django.db import transaction
import json
import requests
import psutil
from .models import DashboardWidget, NetworkNode, SystemMetrics
from .infrastructure.metrics_collector import MetricsCollector
from .infrastructure.monitoring_adapter import MonitoringAdapter
from .infrastructure.network_discovery import NetworkDiscovery
from .infrastructure.cache_service import CacheService
from .infrastructure.unified_dashboard_service import UnifiedDashboardService
from .infrastructure.threshold_alerting import ThresholdAlerting
from .application.dashboard_service import DashboardService

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def collect_system_metrics(self):
    """
    Collecte les métriques système en temps réel.
    
    Cette tâche collecte :
    - Métriques CPU, RAM, disque
    - Statistiques réseau
    - Métriques des services
    - État des conteneurs Docker
    """
    try:
        logger.info("🔍 Collecte des métriques système")
        
        # Initialiser le collecteur de métriques
        metrics_collector = MetricsCollector()
        
        # Collecter les métriques système
        system_metrics = {
            'timestamp': timezone.now().isoformat(),
            'cpu_percent': psutil.cpu_percent(interval=1),
            'memory_percent': psutil.virtual_memory().percent,
            'disk_percent': psutil.disk_usage('/').percent,
            'network_stats': _get_network_stats(),
            'load_average': psutil.getloadavg(),
            'boot_time': psutil.boot_time()
        }
        
        # Collecter les métriques des services
        service_metrics = metrics_collector.collect_all_metrics()
        
        # Combiner les métriques
        combined_metrics = {
            'system': system_metrics,
            'services': service_metrics,
            'collection_time': timezone.now().isoformat()
        }
        
        # Mettre à jour le cache
        cache_service = CacheService()
        cache_service.set_metrics('system_metrics', combined_metrics, timeout=300)
        
        # Sauvegarder en base de données
        _save_metrics_to_db(combined_metrics)
        
        # Vérifier les seuils et alertes
        _check_threshold_alerts(combined_metrics)
        
        logger.info(f"✅ Métriques système collectées: {len(service_metrics)} services")
        
        return {
            'success': True,
            'metrics_collected': len(service_metrics),
            'timestamp': timezone.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Erreur collecte métriques système: {e}")
        
        # Retry automatique
        if self.request.retries < self.max_retries:
            logger.info(f"🔄 Retry {self.request.retries + 1}/{self.max_retries}")
            raise self.retry(countdown=60, exc=e)
        
        return {
            'success': False,
            'error': str(e),
            'timestamp': timezone.now().isoformat()
        }

@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def update_network_topology(self):
    """
    Met à jour la topologie réseau en temps réel.
    
    Cette tâche :
    - Découvre les nouveaux équipements
    - Met à jour les statuts des nœuds
    - Actualise les connexions réseau
    """
    try:
        logger.info("🌐 Mise à jour de la topologie réseau")
        
        # Initialiser la découverte réseau
        network_discovery = NetworkDiscovery()
        
        # Découvrir les équipements
        discovered_nodes = network_discovery.discover_network_nodes()
        
        # Mettre à jour les nœuds en base
        updated_nodes = 0
        new_nodes = 0
        
        for node_data in discovered_nodes:
            node_id = node_data.get('id')
            
            # Vérifier si le nœud existe
            try:
                node = NetworkNode.objects.get(node_id=node_id)
                
                # Mettre à jour les informations
                node.status = node_data.get('status', 'unknown')
                node.last_seen = timezone.now()
                node.metadata = node_data.get('metadata', {})
                node.save()
                
                updated_nodes += 1
                
            except NetworkNode.DoesNotExist:
                # Créer un nouveau nœud
                NetworkNode.objects.create(
                    node_id=node_id,
                    name=node_data.get('name', 'Unknown'),
                    node_type=node_data.get('type', 'unknown'),
                    status=node_data.get('status', 'unknown'),
                    ip_address=node_data.get('ip_address'),
                    metadata=node_data.get('metadata', {}),
                    last_seen=timezone.now()
                )
                
                new_nodes += 1
        
        # Mettre à jour le cache
        cache_service = CacheService()
        cache_service.set_metrics('network_topology', {
            'nodes': discovered_nodes,
            'updated_at': timezone.now().isoformat(),
            'stats': {
                'total_nodes': len(discovered_nodes),
                'updated_nodes': updated_nodes,
                'new_nodes': new_nodes
            }
        }, timeout=300)
        
        logger.info(f"✅ Topologie réseau mise à jour: {updated_nodes} mis à jour, {new_nodes} nouveaux")
        
        return {
            'success': True,
            'updated_nodes': updated_nodes,
            'new_nodes': new_nodes,
            'total_nodes': len(discovered_nodes),
            'timestamp': timezone.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Erreur mise à jour topologie: {e}")
        
        # Retry automatique
        if self.request.retries < self.max_retries:
            logger.info(f"🔄 Retry {self.request.retries + 1}/{self.max_retries}")
            raise self.retry(countdown=30, exc=e)
        
        return {
            'success': False,
            'error': str(e),
            'timestamp': timezone.now().isoformat()
        }

@shared_task(bind=True, max_retries=3, default_retry_delay=120)
def monitor_gns3_projects(self):
    """
    Surveille les projets GNS3 en temps réel.
    
    Cette tâche :
    - Vérifie l'état des projets GNS3
    - Met à jour les statuts des équipements
    - Collecte les métriques de performance
    """
    try:
        logger.info("🎯 Surveillance des projets GNS3")
        
        # Initialiser l'adaptateur de monitoring
        monitoring_adapter = MonitoringAdapter()
        
        # Obtenir les projets GNS3
        gns3_projects = monitoring_adapter.get_gns3_projects()
        
        project_stats = {
            'total_projects': len(gns3_projects),
            'active_projects': 0,
            'stopped_projects': 0,
            'equipment_stats': {}
        }
        
        for project in gns3_projects:
            project_id = project.get('project_id')
            project_status = project.get('status', 'unknown')
            
            # Compter les projets par statut
            if project_status == 'opened':
                project_stats['active_projects'] += 1
            elif project_status == 'closed':
                project_stats['stopped_projects'] += 1
            
            # Collecter les statistiques des équipements
            if project_status == 'opened':
                equipment_stats = monitoring_adapter.get_project_equipment_stats(project_id)
                project_stats['equipment_stats'][project_id] = equipment_stats
        
        # Mettre à jour le cache
        cache_service = CacheService()
        cache_service.set_metrics('gns3_projects', {
            'projects': gns3_projects,
            'stats': project_stats,
            'updated_at': timezone.now().isoformat()
        }, timeout=300)
        
        logger.info(f"✅ Projets GNS3 surveillés: {project_stats['active_projects']} actifs, {project_stats['stopped_projects']} arrêtés")
        
        return {
            'success': True,
            'project_stats': project_stats,
            'timestamp': timezone.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Erreur surveillance GNS3: {e}")
        
        # Retry automatique
        if self.request.retries < self.max_retries:
            logger.info(f"🔄 Retry {self.request.retries + 1}/{self.max_retries}")
            raise self.retry(countdown=120, exc=e)
        
        return {
            'success': False,
            'error': str(e),
            'timestamp': timezone.now().isoformat()
        }

@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def update_dashboard_widgets(self):
    """
    Met à jour les widgets du dashboard en temps réel.
    
    Cette tâche :
    - Actualise les données des widgets
    - Met à jour les graphiques
    - Calcule les statistiques
    """
    try:
        logger.info("📊 Mise à jour des widgets dashboard")
        
        # Obtenir tous les widgets actifs
        active_widgets = DashboardWidget.objects.filter(is_active=True)
        
        updated_widgets = 0
        dashboard_service = DashboardService()
        
        for widget in active_widgets:
            try:
                # Mettre à jour les données du widget
                widget_data = dashboard_service.get_widget_data(widget.widget_type)
                
                # Mettre à jour les statistiques
                widget.data = widget_data
                widget.last_updated = timezone.now()
                widget.save()
                
                updated_widgets += 1
                
            except Exception as e:
                logger.error(f"❌ Erreur mise à jour widget {widget.name}: {e}")
                continue
        
        # Mettre à jour le cache global des widgets
        cache_service = CacheService()
        cache_service.set_metrics('dashboard_widgets', {
            'widgets': [
                {
                    'name': w.name,
                    'type': w.widget_type,
                    'data': w.data,
                    'last_updated': w.last_updated.isoformat() if w.last_updated else None
                }
                for w in active_widgets
            ],
            'updated_at': timezone.now().isoformat()
        }, timeout=300)
        
        logger.info(f"✅ Widgets dashboard mis à jour: {updated_widgets}/{len(active_widgets)}")
        
        return {
            'success': True,
            'updated_widgets': updated_widgets,
            'total_widgets': len(active_widgets),
            'timestamp': timezone.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Erreur mise à jour widgets: {e}")
        
        # Retry automatique
        if self.request.retries < self.max_retries:
            logger.info(f"🔄 Retry {self.request.retries + 1}/{self.max_retries}")
            raise self.retry(countdown=60, exc=e)
        
        return {
            'success': False,
            'error': str(e),
            'timestamp': timezone.now().isoformat()
        }

@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def cleanup_old_metrics(self):
    """
    Nettoie les anciennes métriques pour optimiser les performances.
    
    Cette tâche :
    - Supprime les métriques anciennes
    - Nettoie le cache
    - Optimise la base de données
    """
    try:
        logger.info("🧹 Nettoyage des anciennes métriques")
        
        # Supprimer les métriques anciennes (plus de 7 jours)
        cutoff_date = timezone.now() - timedelta(days=7)
        
        deleted_metrics = SystemMetrics.objects.filter(
            timestamp__lt=cutoff_date
        ).delete()
        
        # Nettoyer les anciens nœuds réseau (plus de 30 jours sans activité)
        old_nodes_cutoff = timezone.now() - timedelta(days=30)
        
        deleted_nodes = NetworkNode.objects.filter(
            last_seen__lt=old_nodes_cutoff
        ).delete()
        
        # Nettoyer le cache
        cache_service = CacheService()
        cache_service.cleanup_old_entries()
        
        logger.info(f"✅ Nettoyage terminé: {deleted_metrics[0]} métriques, {deleted_nodes[0]} nœuds supprimés")
        
        return {
            'success': True,
            'deleted_metrics': deleted_metrics[0],
            'deleted_nodes': deleted_nodes[0],
            'timestamp': timezone.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Erreur nettoyage métriques: {e}")
        
        # Retry automatique
        if self.request.retries < self.max_retries:
            logger.info(f"🔄 Retry {self.request.retries + 1}/{self.max_retries}")
            raise self.retry(countdown=30, exc=e)
        
        return {
            'success': False,
            'error': str(e),
            'timestamp': timezone.now().isoformat()
        }

# ==========================================
# FONCTIONS UTILITAIRES PRIVÉES
# ==========================================

def _get_network_stats():
    """Obtenir les statistiques réseau"""
    try:
        net_stats = psutil.net_io_counters()
        return {
            'bytes_sent': net_stats.bytes_sent,
            'bytes_recv': net_stats.bytes_recv,
            'packets_sent': net_stats.packets_sent,
            'packets_recv': net_stats.packets_recv,
            'errin': net_stats.errin,
            'errout': net_stats.errout,
            'dropin': net_stats.dropin,
            'dropout': net_stats.dropout
        }
    except Exception as e:
        logger.error(f"❌ Erreur récupération stats réseau: {e}")
        return {}

def _save_metrics_to_db(metrics_data):
    """Sauvegarder les métriques en base de données"""
    try:
        with transaction.atomic():
            SystemMetrics.objects.create(
                timestamp=timezone.now(),
                cpu_percent=metrics_data['system']['cpu_percent'],
                memory_percent=metrics_data['system']['memory_percent'],
                disk_percent=metrics_data['system']['disk_percent'],
                network_stats=metrics_data['system']['network_stats'],
                service_metrics=metrics_data['services'],
                metadata=metrics_data
            )
    except Exception as e:
        logger.error(f"❌ Erreur sauvegarde métriques: {e}")

def _check_threshold_alerts(metrics_data):
    """Vérifier les seuils et générer des alertes"""
    try:
        alerting = ThresholdAlerting()
        
        # Vérifier les seuils système
        system_metrics = metrics_data['system']
        
        # CPU
        if system_metrics['cpu_percent'] > 80:
            alerting.trigger_alert('cpu_high', {
                'value': system_metrics['cpu_percent'],
                'threshold': 80,
                'timestamp': timezone.now().isoformat()
            })
        
        # Mémoire
        if system_metrics['memory_percent'] > 85:
            alerting.trigger_alert('memory_high', {
                'value': system_metrics['memory_percent'],
                'threshold': 85,
                'timestamp': timezone.now().isoformat()
            })
        
        # Disque
        if system_metrics['disk_percent'] > 90:
            alerting.trigger_alert('disk_high', {
                'value': system_metrics['disk_percent'],
                'threshold': 90,
                'timestamp': timezone.now().isoformat()
            })
        
    except Exception as e:
        logger.error(f"❌ Erreur vérification seuils: {e}")

# ==========================================
# TÂCHES PÉRIODIQUES CONFIGURÉES
# ==========================================

# Configuration des tâches périodiques dans settings.py :
# CELERY_BEAT_SCHEDULE = {
#     'collect-system-metrics': {
#         'task': 'dashboard.tasks.collect_system_metrics',
#         'schedule': 30.0,  # Toutes les 30 secondes
#     },
#     'update-network-topology': {
#         'task': 'dashboard.tasks.update_network_topology',
#         'schedule': 60.0,  # Toutes les minutes
#     },
#     'monitor-gns3-projects': {
#         'task': 'dashboard.tasks.monitor_gns3_projects',
#         'schedule': 120.0,  # Toutes les 2 minutes
#     },
#     'update-dashboard-widgets': {
#         'task': 'dashboard.tasks.update_dashboard_widgets',
#         'schedule': 45.0,  # Toutes les 45 secondes
#     },
#     'cleanup-old-metrics': {
#         'task': 'dashboard.tasks.cleanup_old_metrics',
#         'schedule': 3600.0,  # Toutes les heures
#     },
# }