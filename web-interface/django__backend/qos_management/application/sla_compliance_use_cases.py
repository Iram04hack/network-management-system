"""
Cas d'utilisation pour la gestion des rapports de conformité SLA QoS.

Ce module implémente les cas d'utilisation pour générer et analyser
les rapports de conformité SLA (Service Level Agreement) pour la QoS.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

from ..domain.interfaces import QoSMonitoringService
from ..domain.exceptions import QoSMonitoringException

logger = logging.getLogger(__name__)


class GetSLAComplianceReportUseCase:
    """
    Cas d'utilisation pour obtenir un rapport de conformité SLA pour un équipement.
    """
    
    def __init__(self, qos_monitoring_service: QoSMonitoringService):
        """
        Initialise le cas d'utilisation.
        
        Args:
            qos_monitoring_service: Service de monitoring QoS
        """
        self._qos_monitoring_service = qos_monitoring_service
    
    def execute(self, device_id: int, period: str = "24h") -> Dict[str, Any]:
        """
        Génère un rapport de conformité SLA pour un équipement.
        
        Args:
            device_id: ID de l'équipement
            period: Période sur laquelle calculer la conformité (ex: "24h", "7d")
            
        Returns:
            Rapport de conformité SLA
            
        Raises:
            QoSMonitoringException: Si la génération du rapport échoue
        """
        try:
            # Récupérer le rapport de conformité SLA via le service de monitoring
            compliance_report = self._qos_monitoring_service.get_sla_compliance(device_id, period)
            
            return {
                'success': True,
                'data': compliance_report
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de la génération du rapport SLA pour l'équipement {device_id}: {str(e)}")
            raise QoSMonitoringException(f"Erreur lors de la génération du rapport SLA: {str(e)}")


class GetQoSPerformanceReportUseCase:
    """
    Cas d'utilisation pour obtenir un rapport de performance QoS global.
    """
    
    def __init__(self, qos_monitoring_service: QoSMonitoringService):
        """
        Initialise le cas d'utilisation.
        
        Args:
            qos_monitoring_service: Service de monitoring QoS
        """
        self._qos_monitoring_service = qos_monitoring_service
    
    def execute(self, device_ids: Optional[List[int]] = None, period: str = "7d") -> Dict[str, Any]:
        """
        Génère un rapport de performance QoS global.
        
        Args:
            device_ids: Liste des IDs d'équipements à inclure (optionnel)
            period: Période du rapport (ex: "7d", "30d")
            
        Returns:
            Rapport de performance QoS
            
        Raises:
            QoSMonitoringException: Si la génération du rapport échoue
        """
        try:
            # Récupérer le rapport QoS via le service de monitoring
            qos_report = self._qos_monitoring_service.get_qos_report(device_ids, period)
            
            return {
                'success': True,
                'data': qos_report
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de la génération du rapport QoS: {str(e)}")
            raise QoSMonitoringException(f"Erreur lors de la génération du rapport QoS: {str(e)}")


class AnalyzeSLATrendsUseCase:
    """
    Cas d'utilisation pour analyser les tendances de conformité SLA sur une période.
    """
    
    def __init__(self, qos_monitoring_service: QoSMonitoringService):
        """
        Initialise le cas d'utilisation.
        
        Args:
            qos_monitoring_service: Service de monitoring QoS
        """
        self._qos_monitoring_service = qos_monitoring_service
    
    def execute(self, device_id: int, start_date: str, end_date: str, 
               interval: str = "1d") -> Dict[str, Any]:
        """
        Analyse les tendances de conformité SLA sur une période donnée.
        
        Args:
            device_id: ID de l'équipement
            start_date: Date de début au format ISO (YYYY-MM-DD)
            end_date: Date de fin au format ISO (YYYY-MM-DD)
            interval: Intervalle d'agrégation (ex: "1d", "1h")
            
        Returns:
            Analyse des tendances SLA
            
        Raises:
            QoSMonitoringException: Si l'analyse échoue
        """
        try:
            # Convertir les dates en objets datetime
            try:
                start = datetime.fromisoformat(start_date)
                end = datetime.fromisoformat(end_date)
            except ValueError:
                raise QoSMonitoringException("Format de date invalide. Utilisez le format YYYY-MM-DD.")
            
            # Vérifier que la date de fin est après la date de début
            if end <= start:
                raise QoSMonitoringException("La date de fin doit être postérieure à la date de début.")
            
            # Calculer les périodes pour l'analyse
            periods = self._generate_periods(start, end, interval)
            
            # Récupérer les rapports SLA pour chaque période
            trend_data = []
            
            for period_start, period_end in periods:
                # Calculer la durée de la période au format attendu par le service
                period_duration = self._format_duration(period_end - period_start)
                
                # Récupérer le rapport SLA pour cette période
                period_report = self._qos_monitoring_service.get_sla_compliance(
                    device_id, 
                    period_duration
                )
                
                # Ajouter les données à l'analyse des tendances
                trend_data.append({
                    'period_start': period_start.isoformat(),
                    'period_end': period_end.isoformat(),
                    'overall_compliance': period_report.get('overall_compliance', 0),
                    'service_classes': self._extract_service_class_compliances(
                        period_report.get('service_classes', {})
                    )
                })
            
            # Analyser les tendances
            trend_analysis = self._analyze_trends(trend_data)
            
            return {
                'success': True,
                'device_id': device_id,
                'start_date': start_date,
                'end_date': end_date,
                'interval': interval,
                'trend_data': trend_data,
                'analysis': trend_analysis
            }
            
        except QoSMonitoringException:
            raise
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse des tendances SLA pour l'équipement {device_id}: {str(e)}")
            raise QoSMonitoringException(f"Erreur lors de l'analyse des tendances SLA: {str(e)}")
    
    def _generate_periods(self, start: datetime, end: datetime, 
                        interval: str) -> List[tuple]:
        """
        Génère une liste de périodes entre la date de début et la date de fin.
        
        Args:
            start: Date de début
            end: Date de fin
            interval: Intervalle ("1d", "1h", etc.)
            
        Returns:
            Liste de tuples (début, fin) pour chaque période
        """
        periods = []
        
        # Analyser l'intervalle
        if interval.endswith('d'):
            try:
                days = int(interval[:-1])
                delta = timedelta(days=days)
            except ValueError:
                delta = timedelta(days=1)
        elif interval.endswith('h'):
            try:
                hours = int(interval[:-1])
                delta = timedelta(hours=hours)
            except ValueError:
                delta = timedelta(hours=1)
        else:
            # Par défaut, intervalle d'un jour
            delta = timedelta(days=1)
        
        # Générer les périodes
        current = start
        while current < end:
            next_period = min(current + delta, end)
            periods.append((current, next_period))
            current = next_period
            
        return periods
    
    def _format_duration(self, duration: timedelta) -> str:
        """
        Convertit une durée timedelta en format attendu par le service de monitoring.
        
        Args:
            duration: Durée à convertir
            
        Returns:
            Durée au format attendu (ex: "24h", "7d")
        """
        total_seconds = duration.total_seconds()
        
        # Convertir en jours si plus d'un jour
        if total_seconds >= 86400:  # 60 * 60 * 24
            days = int(total_seconds / 86400)
            return f"{days}d"
        
        # Convertir en heures si moins d'un jour
        hours = int(total_seconds / 3600)
        return f"{hours}h"
    
    def _extract_service_class_compliances(self, service_classes: Dict[str, Any]) -> Dict[str, float]:
        """
        Extrait les taux de conformité par classe de service.
        
        Args:
            service_classes: Dictionnaire des classes de service et leurs métriques
            
        Returns:
            Dictionnaire des taux de conformité par classe de service
        """
        result = {}
        
        for class_name, class_data in service_classes.items():
            result[class_name] = class_data.get('compliance_rate', 0)
            
        return result
    
    def _analyze_trends(self, trend_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyse les tendances dans les données.
        
        Args:
            trend_data: Données de tendances
            
        Returns:
            Analyse des tendances
        """
        if not trend_data:
            return {
                'trend': 'unchanged',
                'improvement': 0,
                'most_improved_class': None,
                'most_degraded_class': None
            }
        
        # Analyser la tendance globale
        start_compliance = trend_data[0]['overall_compliance']
        end_compliance = trend_data[-1]['overall_compliance']
        improvement = end_compliance - start_compliance
        
        trend = 'unchanged'
        if improvement > 0.05:  # 5% d'amélioration
            trend = 'improving'
        elif improvement < -0.05:  # 5% de dégradation
            trend = 'degrading'
            
        # Analyser les tendances par classe de service
        class_improvements = {}
        for class_name in trend_data[0]['service_classes'].keys():
            start_class = trend_data[0]['service_classes'].get(class_name, 0)
            end_class = trend_data[-1]['service_classes'].get(class_name, 0)
            class_improvements[class_name] = end_class - start_class
            
        # Trouver les classes avec la plus grande amélioration et dégradation
        most_improved_class = max(class_improvements.items(), key=lambda x: x[1]) if class_improvements else None
        most_degraded_class = min(class_improvements.items(), key=lambda x: x[1]) if class_improvements else None
        
        return {
            'trend': trend,
            'improvement': improvement,
            'most_improved_class': most_improved_class[0] if most_improved_class else None,
            'most_improved_value': most_improved_class[1] if most_improved_class else 0,
            'most_degraded_class': most_degraded_class[0] if most_degraded_class else None,
            'most_degraded_value': most_degraded_class[1] if most_degraded_class else 0
        } 