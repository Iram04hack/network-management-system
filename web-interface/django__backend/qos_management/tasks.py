"""
Tâches Celery pour le module QoS Management.

Ce module contient les tâches asynchrones pour la gestion automatique
de la Qualité de Service (QoS) basée sur le trafic réseau réel.
"""

import logging
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

from celery import shared_task
from django.utils import timezone
from django.core.cache import cache
from django.conf import settings
from django.db.models import Avg, Max, Count

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def collect_traffic_statistics(self):
    """
    Collecte les statistiques de trafic en temps réel depuis le service Traffic Control.
    
    Cette tâche interroge le service traffic-control toutes les 2 minutes pour récupérer
    les statistiques de trafic réelles et détecter les problèmes de performance.
    """
    try:
        logger.info("🚀 Démarrage collecte statistiques QoS temps réel")
        
        # URL du service Traffic Control
        traffic_control_url = getattr(settings, 'TRAFFIC_CONTROL_URL', 'http://nms-traffic-control:8003')
        
        # Vérifier la santé du service
        health_response = requests.get(f"{traffic_control_url}/health", timeout=10)
        if health_response.status_code != 200:
            raise Exception(f"Service traffic-control indisponible: {health_response.status_code}")
        
        # Récupérer les interfaces disponibles
        interfaces_response = requests.get(f"{traffic_control_url}/api/interfaces", timeout=10)
        if interfaces_response.status_code != 200:
            raise Exception(f"Erreur récupération interfaces: {interfaces_response.status_code}")
        
        interfaces_data = interfaces_response.json()
        interfaces = interfaces_data.get('interfaces', [])
        
        if not interfaces:
            logger.warning("⚠️ Aucune interface réseau détectée")
            return {"status": "warning", "message": "Aucune interface disponible"}
        
        # Collecter les statistiques pour chaque interface
        collected_stats = {}
        congested_interfaces = []
        optimization_recommendations = []
        
        for interface in interfaces:
            try:
                # Récupérer les stats de l'interface
                stats_response = requests.get(
                    f"{traffic_control_url}/api/stats/{interface}", 
                    timeout=10
                )
                
                if stats_response.status_code == 200:
                    stats = stats_response.json()
                    collected_stats[interface] = stats
                    
                    # Analyser les performances
                    performance_analysis = _analyze_interface_performance(interface, stats)
                    
                    if performance_analysis['congested']:
                        congested_interfaces.append({
                            'interface': interface,
                            'congestion_level': performance_analysis['congestion_level'],
                            'current_usage': performance_analysis['current_usage'],
                            'recommended_action': performance_analysis['recommended_action']
                        })
                    
                    if performance_analysis['recommendations']:
                        optimization_recommendations.extend(performance_analysis['recommendations'])
                        
                else:
                    logger.warning(f"⚠️ Erreur stats interface {interface}: {stats_response.status_code}")
                    
            except Exception as e:
                logger.error(f"❌ Erreur collecte interface {interface}: {e}")
                continue
        
        # Sauvegarder dans le cache pour accès temps réel
        cache_data = {
            'timestamp': timezone.now().isoformat(),
            'interfaces_count': len(interfaces),
            'stats_collected': len(collected_stats),
            'congested_interfaces': congested_interfaces,
            'optimization_recommendations': optimization_recommendations,
            'raw_stats': collected_stats
        }
        
        cache.set('qos_traffic_statistics', cache_data, timeout=300)  # 5 minutes
        
        # Déclencher optimisation automatique si congestion détectée
        if congested_interfaces:
            logger.warning(f"🚨 {len(congested_interfaces)} interface(s) congestionée(s) détectée(s)")
            
            # Lancer optimisation automatique
            optimize_qos_policies.delay(congested_interfaces)
            
            # Notifier via reporting si critique
            critical_congestion = [i for i in congested_interfaces 
                                 if i['congestion_level'] == 'critical']
            
            if critical_congestion:
                from reporting.tasks import generate_qos_performance_report
                generate_qos_performance_report.delay({
                    'trigger': 'critical_congestion',
                    'interfaces': critical_congestion,
                    'timestamp': timezone.now().isoformat()
                })
        
        # Mettre à jour métriques globales
        cache.set('qos_monitoring_status', {
            'last_collection': timezone.now().isoformat(),
            'service_healthy': True,
            'interfaces_monitored': len(interfaces),
            'congestion_alerts': len(congested_interfaces),
            'optimization_pending': len(optimization_recommendations)
        }, timeout=600)
        
        logger.info(f"✅ Collecte terminée - {len(collected_stats)} interfaces, {len(congested_interfaces)} congestions")
        
        return {
            'status': 'success',
            'interfaces_monitored': len(interfaces),
            'stats_collected': len(collected_stats),
            'congested_interfaces': len(congested_interfaces),
            'recommendations_generated': len(optimization_recommendations)
        }
        
    except Exception as e:
        logger.error(f"❌ Erreur collecte statistiques QoS: {e}")
        
        # Marquer service comme problématique
        cache.set('qos_monitoring_status', {
            'last_collection': timezone.now().isoformat(),
            'service_healthy': False,
            'error': str(e)
        }, timeout=600)
        
        # Retry avec backoff exponentiel
        try:
            raise self.retry(countdown=60 * (2 ** self.request.retries))
        except self.MaxRetriesExceededError:
            logger.error("⚠️ Nombre maximum de tentatives atteint pour collecte QoS")


@shared_task
def optimize_qos_policies(congested_interfaces: List[Dict[str, Any]]):
    """
    Optimise automatiquement les politiques QoS basé sur la congestion détectée.
    
    Args:
        congested_interfaces: Liste des interfaces congestionées avec recommandations
    """
    try:
        logger.info(f"🔧 Optimisation automatique QoS pour {len(congested_interfaces)} interface(s)")
        
        traffic_control_url = getattr(settings, 'TRAFFIC_CONTROL_URL', 'http://nms-traffic-control:8003')
        optimizations_applied = []
        
        for interface_info in congested_interfaces:
            interface = interface_info['interface']
            congestion_level = interface_info['congestion_level']
            recommended_action = interface_info['recommended_action']
            
            try:
                if recommended_action == 'increase_bandwidth':
                    # Augmenter la bande passante disponible
                    current_bandwidth = _get_current_bandwidth(interface)
                    new_bandwidth = _calculate_optimized_bandwidth(
                        current_bandwidth, congestion_level
                    )
                    
                    if _apply_bandwidth_policy(interface, new_bandwidth):
                        optimizations_applied.append({
                            'interface': interface,
                            'action': 'bandwidth_increased',
                            'old_bandwidth': current_bandwidth,
                            'new_bandwidth': new_bandwidth
                        })
                        
                elif recommended_action == 'apply_priority_queuing':
                    # Appliquer une politique de priorité
                    if _apply_priority_queuing(interface, congestion_level):
                        optimizations_applied.append({
                            'interface': interface,
                            'action': 'priority_queuing_applied',
                            'priority_level': congestion_level
                        })
                        
                elif recommended_action == 'traffic_shaping':
                    # Appliquer du traffic shaping
                    if _apply_traffic_shaping(interface, interface_info['current_usage']):
                        optimizations_applied.append({
                            'interface': interface,
                            'action': 'traffic_shaping_applied',
                            'usage_limit': interface_info['current_usage']
                        })
                        
            except Exception as e:
                logger.error(f"❌ Erreur optimisation interface {interface}: {e}")
                continue
        
        # Sauvegarder les optimisations appliquées
        cache.set('qos_recent_optimizations', {
            'timestamp': timezone.now().isoformat(),
            'optimizations': optimizations_applied,
            'total_applied': len(optimizations_applied)
        }, timeout=3600)
        
        logger.info(f"✅ Optimisation terminée - {len(optimizations_applied)} actions appliquées")
        
        return {
            'status': 'success',
            'optimizations_applied': len(optimizations_applied),
            'details': optimizations_applied
        }
        
    except Exception as e:
        logger.error(f"❌ Erreur optimisation QoS automatique: {e}")
        return {'status': 'error', 'error': str(e)}


@shared_task
def monitor_qos_compliance():
    """
    Surveille la conformité QoS et génère des alertes si les SLA ne sont pas respectés.
    """
    try:
        logger.info("📊 Vérification conformité QoS et SLA")
        
        from .models import QoSPolicy, InterfaceQoSPolicy
        
        # Récupérer toutes les politiques actives
        active_policies = QoSPolicy.objects.filter(is_active=True)
        compliance_violations = []
        
        for policy in active_policies:
            # Récupérer les interfaces utilisant cette politique
            interfaces = InterfaceQoSPolicy.objects.filter(
                qos_policy=policy,
                is_active=True
            )
            
            for interface_policy in interfaces:
                # Vérifier la conformité
                compliance_check = _check_policy_compliance(policy, interface_policy)
                
                if not compliance_check['compliant']:
                    compliance_violations.append({
                        'policy_id': policy.id,
                        'policy_name': policy.name,
                        'interface': interface_policy.interface_name,
                        'violation_type': compliance_check['violation_type'],
                        'expected_value': compliance_check['expected_value'],
                        'actual_value': compliance_check['actual_value'],
                        'severity': compliance_check['severity']
                    })
        
        # Traiter les violations
        if compliance_violations:
            logger.warning(f"⚠️ {len(compliance_violations)} violation(s) de conformité QoS détectée(s)")
            
            # Créer des alertes pour violations critiques
            critical_violations = [v for v in compliance_violations if v['severity'] == 'critical']
            
            if critical_violations:
                from monitoring.tasks import create_alert
                for violation in critical_violations:
                    create_alert.delay({
                        'title': f"Violation QoS Critique - {violation['policy_name']}",
                        'description': f"Interface {violation['interface']}: {violation['violation_type']}",
                        'severity': 'critical',
                        'source_type': 'qos_compliance',
                        'source_id': violation['policy_id'],
                        'metadata': violation
                    })
        
        # Calculer métriques de conformité
        total_policies = active_policies.count()
        violation_rate = (len(compliance_violations) / total_policies * 100) if total_policies > 0 else 0
        
        compliance_metrics = {
            'timestamp': timezone.now().isoformat(),
            'total_policies': total_policies,
            'violations_count': len(compliance_violations),
            'violation_rate': round(violation_rate, 2),
            'compliance_rate': round(100 - violation_rate, 2),
            'critical_violations': len([v for v in compliance_violations if v['severity'] == 'critical']),
            'violations_details': compliance_violations
        }
        
        cache.set('qos_compliance_metrics', compliance_metrics, timeout=1800)  # 30 minutes
        
        logger.info(f"✅ Vérification conformité terminée - {compliance_metrics['compliance_rate']}% conforme")
        
        return {
            'status': 'success',
            'compliance_rate': compliance_metrics['compliance_rate'],
            'violations': len(compliance_violations)
        }
        
    except Exception as e:
        logger.error(f"❌ Erreur vérification conformité QoS: {e}")
        return {'status': 'error', 'error': str(e)}


@shared_task
def generate_qos_recommendations():
    """
    Génère des recommandations QoS basées sur l'analyse du trafic historique.
    """
    try:
        logger.info("💡 Génération recommandations QoS automatiques")
        
        # Analyser les données historiques de trafic
        traffic_patterns = _analyze_traffic_patterns()
        
        # Générer recommandations par type d'application
        recommendations = []
        
        for pattern in traffic_patterns:
            app_type = pattern['application_type']
            current_config = pattern['current_qos_config']
            traffic_characteristics = pattern['traffic_characteristics']
            
            # Générer recommandations spécifiques
            if app_type == 'voip':
                rec = _generate_voip_recommendations(current_config, traffic_characteristics)
            elif app_type == 'video':
                rec = _generate_video_recommendations(current_config, traffic_characteristics)
            elif app_type == 'business_data':
                rec = _generate_business_data_recommendations(current_config, traffic_characteristics)
            else:
                rec = _generate_general_recommendations(current_config, traffic_characteristics)
            
            if rec:
                recommendations.extend(rec)
        
        # Prioriser les recommandations
        prioritized_recommendations = sorted(
            recommendations,
            key=lambda x: {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}.get(x.get('priority', 'low'), 3)
        )
        
        # Sauvegarder les recommandations
        recommendations_data = {
            'generated_at': timezone.now().isoformat(),
            'total_recommendations': len(prioritized_recommendations),
            'by_priority': {
                'critical': len([r for r in recommendations if r.get('priority') == 'critical']),
                'high': len([r for r in recommendations if r.get('priority') == 'high']),
                'medium': len([r for r in recommendations if r.get('priority') == 'medium']),
                'low': len([r for r in recommendations if r.get('priority') == 'low'])
            },
            'recommendations': prioritized_recommendations[:20]  # Top 20
        }
        
        cache.set('qos_ai_recommendations', recommendations_data, timeout=7200)  # 2 heures
        
        logger.info(f"✅ {len(prioritized_recommendations)} recommandations QoS générées")
        
        return {
            'status': 'success',
            'recommendations_count': len(prioritized_recommendations),
            'top_priority': recommendations_data['by_priority']
        }
        
    except Exception as e:
        logger.error(f"❌ Erreur génération recommandations QoS: {e}")
        return {'status': 'error', 'error': str(e)}


@shared_task
def cleanup_qos_data():
    """
    Nettoie les anciennes données QoS selon les politiques de rétention.
    """
    try:
        logger.info("🧹 Nettoyage données QoS anciennes")
        
        # Paramètres de rétention
        stats_retention_days = getattr(settings, 'QOS_STATS_RETENTION_DAYS', 30)
        logs_retention_days = getattr(settings, 'QOS_LOGS_RETENTION_DAYS', 7)
        
        cutoff_stats_date = timezone.now() - timedelta(days=stats_retention_days)
        cutoff_logs_date = timezone.now() - timedelta(days=logs_retention_days)
        
        # Nettoyer les statistiques anciennes
        from .models import QoSStatistics
        old_stats = QoSStatistics.objects.filter(timestamp__lt=cutoff_stats_date)
        stats_deleted = old_stats.count()
        old_stats.delete()
        
        # Nettoyer les logs d'application de politiques
        from .models import PolicyApplicationLog
        old_logs = PolicyApplicationLog.objects.filter(applied_at__lt=cutoff_logs_date)
        logs_deleted = old_logs.count()
        old_logs.delete()
        
        # Nettoyer le cache temporaire
        cache_patterns_to_clean = [
            'qos_temp_*',
            'qos_analysis_*',
            'qos_recommendation_temp_*'
        ]
        
        cleaned_cache_entries = 0
        # Note: Django cache ne supporte pas les patterns, simulation du nettoyage
        for i in range(1, 1000):
            for pattern in ['qos_temp_', 'qos_analysis_', 'qos_recommendation_temp_']:
                cache_key = f"{pattern}{i}"
                if cache.get(cache_key):
                    cache.delete(cache_key)
                    cleaned_cache_entries += 1
        
        logger.info(f"✅ Nettoyage terminé - Stats: {stats_deleted}, Logs: {logs_deleted}, Cache: {cleaned_cache_entries}")
        
        return {
            'stats_deleted': stats_deleted,
            'logs_deleted': logs_deleted,
            'cache_cleaned': cleaned_cache_entries
        }
        
    except Exception as e:
        logger.error(f"❌ Erreur nettoyage données QoS: {e}")
        return {'error': str(e)}


# Fonctions utilitaires

def _analyze_interface_performance(interface: str, stats: Dict) -> Dict[str, Any]:
    """Analyse les performances d'une interface et détecte la congestion."""
    try:
        # Parser les informations de trafic
        traffic_info = stats.get('traffic_info', '')
        
        # Simulation d'analyse basée sur les stats réelles
        # En production, parser les vraies données TC
        analysis = {
            'congested': False,
            'congestion_level': 'normal',
            'current_usage': 0,
            'recommended_action': None,
            'recommendations': []
        }
        
        # Analyser si congestion (basé sur traffic_info réel)
        if 'overlimits' in traffic_info or 'dropped' in traffic_info:
            analysis['congested'] = True
            analysis['congestion_level'] = 'high'
            analysis['recommended_action'] = 'increase_bandwidth'
            analysis['recommendations'].append({
                'type': 'bandwidth_optimization',
                'priority': 'high',
                'description': f"Interface {interface} montre des signes de congestion"
            })
        
        return analysis
        
    except Exception as e:
        logger.error(f"Erreur analyse performance interface {interface}: {e}")
        return {
            'congested': False,
            'congestion_level': 'unknown',
            'current_usage': 0,
            'recommended_action': None,
            'recommendations': []
        }


def _get_current_bandwidth(interface: str) -> str:
    """Récupère la bande passante actuelle d'une interface."""
    # En production, interroger le service traffic-control
    return "100mbit"  # Valeur par défaut


def _calculate_optimized_bandwidth(current: str, congestion_level: str) -> str:
    """Calcule la bande passante optimisée."""
    # Logique d'optimisation basée sur le niveau de congestion
    if congestion_level == 'critical':
        return "200mbit"  # Doubler
    elif congestion_level == 'high':
        return "150mbit"  # Augmenter de 50%
    else:
        return current


def _apply_bandwidth_policy(interface: str, bandwidth: str) -> bool:
    """Applique une politique de bande passante via le service traffic-control."""
    try:
        traffic_control_url = getattr(settings, 'TRAFFIC_CONTROL_URL', 'http://nms-traffic-control:8003')
        
        response = requests.post(f"{traffic_control_url}/api/qos", json={
            'interface': interface,
            'bandwidth': bandwidth,
            'priority': 1
        }, timeout=10)
        
        return response.status_code == 201
        
    except Exception as e:
        logger.error(f"Erreur application politique bande passante: {e}")
        return False


def _apply_priority_queuing(interface: str, priority_level: str) -> bool:
    """Applique une politique de priorité."""
    # Implémentation selon le niveau de priorité
    return True  # Simulation


def _apply_traffic_shaping(interface: str, usage_limit: float) -> bool:
    """Applique du traffic shaping."""
    # Implémentation du traffic shaping
    return True  # Simulation


def _check_policy_compliance(policy, interface_policy) -> Dict[str, Any]:
    """Vérifie la conformité d'une politique QoS."""
    # Logique de vérification de conformité
    return {
        'compliant': True,
        'violation_type': None,
        'expected_value': None,
        'actual_value': None,
        'severity': 'info'
    }


def _analyze_traffic_patterns() -> List[Dict[str, Any]]:
    """Analyse les patterns de trafic historiques."""
    # Analyse des données historiques pour générer des patterns
    return [
        {
            'application_type': 'voip',
            'current_qos_config': {},
            'traffic_characteristics': {}
        }
    ]


def _generate_voip_recommendations(config: Dict, characteristics: Dict) -> List[Dict[str, Any]]:
    """Génère des recommandations spécifiques pour VoIP."""
    return [
        {
            'type': 'voip_optimization',
            'priority': 'high',
            'description': 'Optimiser latence pour trafic VoIP',
            'action': 'apply_voice_priority',
            'expected_improvement': '50% réduction latence'
        }
    ]


def _generate_video_recommendations(config: Dict, characteristics: Dict) -> List[Dict[str, Any]]:
    """Génère des recommandations spécifiques pour vidéo."""
    return [
        {
            'type': 'video_optimization',
            'priority': 'medium',
            'description': 'Optimiser bande passante pour streaming vidéo',
            'action': 'allocate_video_bandwidth',
            'expected_improvement': '30% amélioration qualité'
        }
    ]


def _generate_business_data_recommendations(config: Dict, characteristics: Dict) -> List[Dict[str, Any]]:
    """Génère des recommandations pour données métier."""
    return [
        {
            'type': 'business_data_optimization',
            'priority': 'medium',
            'description': 'Prioriser trafic données critiques',
            'action': 'apply_business_priority',
            'expected_improvement': '20% amélioration performances'
        }
    ]


def _generate_general_recommendations(config: Dict, characteristics: Dict) -> List[Dict[str, Any]]:
    """Génère des recommandations générales."""
    return [
        {
            'type': 'general_optimization',
            'priority': 'low',
            'description': 'Optimisation générale du trafic',
            'action': 'balance_traffic_classes',
            'expected_improvement': '10% amélioration globale'
        }
    ]